"""
Sentinel360 Healthcare — Step 2B-2 Watch-Condition Engine
"""

import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from threshold_breach_models import (
    BreachType,
    DailySummaryResult,
    OperationalUseStatus,
    ReviewDueStatus,
    ThresholdState,
    TrendInterpretation,
    WatchConditionResult,
    WatchConditionType,
    WatchIssueResult,
    WatchSeverity,
)


class KPIWatchConditionEngine:
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.engine_run_id = f"THWATCH-{uuid.uuid4().hex[:16].upper()}"
        self.processed_at = datetime.now().isoformat()
        self.watches: List[WatchConditionResult] = []
        self.summaries: List[DailySummaryResult] = []
        self.issues: List[WatchIssueResult] = []
        self.df_classified: Optional[pd.DataFrame] = None
        self.df_trends: Optional[pd.DataFrame] = None
        self.df_sustained: Optional[pd.DataFrame] = None
        self.df_watch_rules: Optional[pd.DataFrame] = None
        self.df_provisional: Optional[pd.DataFrame] = None

    def _generate_id(self, prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4().hex[:16].upper()}"

    def load_inputs(self) -> None:
        trends_path = self.project_root / "data" / "analytical" / "analytical_kpi_trend_signals.csv"
        self.df_trends = pd.read_csv(trends_path)
        self.df_trends["reporting_date"] = pd.to_datetime(self.df_trends["reporting_date"]).dt.strftime("%Y-%m-%d")

        sustained_path = self.project_root / "data" / "analytical" / "analytical_kpi_sustained_movements.csv"
        self.df_sustained = pd.read_csv(sustained_path)

        rules_path = self.project_root / "config" / "watch_condition_rule_config.csv"
        self.df_watch_rules = pd.read_csv(rules_path)

        prov_path = self.project_root / "config" / "provisional_threshold_handling_config.csv"
        self.df_provisional = pd.read_csv(prov_path)

    def validate_prerequisites(self) -> Tuple[bool, List[str]]:
        issues: List[str] = []
        if self.df_trends is None or self.df_trends.empty:
            issues.append("Trend signals missing.")
        if self.df_watch_rules is None or self.df_watch_rules.empty:
            issues.append("Watch rule config missing.")
        return len(issues) == 0, issues

    def set_classified_data(self, df: pd.DataFrame) -> None:
        self.df_classified = df.copy()
        self.df_classified["reporting_date"] = pd.to_datetime(self.df_classified["reporting_date"]).dt.strftime("%Y-%m-%d")

    def _get_trend_for_record(self, hospital_id: str, department_id: str, kpi_id: str, reporting_date: str) -> Optional[Dict[str, Any]]:
        if self.df_trends is None:
            return None
        sub = self.df_trends[
            (self.df_trends["hospital_id"] == hospital_id) &
            (self.df_trends["department_id"] == department_id) &
            (self.df_trends["kpi_id"] == kpi_id) &
            (self.df_trends["reporting_date"] == reporting_date)
        ]
        if sub.empty:
            return None
        # Prefer trend_slope signal
        slope = sub[sub["signal_method"] == "trend_slope"]
        if not slope.empty:
            row = slope.iloc[0]
        else:
            row = sub.iloc[0]
        return {
            "signal_type": row.get("signal_type", ""),
            "signal_direction": row.get("signal_direction", ""),
            "signal_strength": row.get("signal_strength", ""),
            "trend_confidence_level": row.get("trend_confidence_level", ""),
            "signal_record_id": row.get("signal_record_id", ""),
        }

    def _get_sustained_for_record(self, hospital_id: str, department_id: str, kpi_id: str, reporting_date: str) -> Optional[Dict[str, Any]]:
        if self.df_sustained is None:
            return None
        sub = self.df_sustained[
            (self.df_sustained["hospital_id"] == hospital_id) &
            (self.df_sustained["department_id"] == department_id) &
            (self.df_sustained["kpi_id"] == kpi_id)
        ]
        if sub.empty:
            return None
        # Find movement that covers this date
        date_obj = datetime.strptime(reporting_date, "%Y-%m-%d")
        for _, row in sub.iterrows():
            start = datetime.strptime(row["sequence_start_date"], "%Y-%m-%d")
            end = datetime.strptime(row["sequence_end_date"], "%Y-%m-%d")
            if start <= date_obj <= end:
                return {
                    "movement_type": row.get("movement_type", ""),
                    "consecutive_observation_count": row.get("consecutive_observation_count", 0),
                    "movement_record_id": row.get("movement_record_id", ""),
                }
        return None

    def _interpret_trend(self, signal_type: str, directionality: str) -> str:
        st = str(signal_type).lower()
        if "increase" in st:
            if directionality == "Higher is better":
                return TrendInterpretation.IMPROVING.value
            elif directionality == "Lower is better":
                return TrendInterpretation.DETERIORATING.value
            else:
                return TrendInterpretation.VOLATILE.value
        elif "decrease" in st:
            if directionality == "Higher is better":
                return TrendInterpretation.DETERIORATING.value
            elif directionality == "Lower is better":
                return TrendInterpretation.IMPROVING.value
            else:
                return TrendInterpretation.VOLATILE.value
        elif "no signal" in st:
            return TrendInterpretation.STABLE.value
        return TrendInterpretation.INSUFFICIENT_EVIDENCE.value

    def _is_deteriorating(self, interpretation: str) -> bool:
        return interpretation == TrendInterpretation.DETERIORATING.value

    def _is_improving(self, interpretation: str) -> bool:
        return interpretation == TrendInterpretation.IMPROVING.value

    def _calc_persistence(self, group: pd.DataFrame, window: int, qualifying_statuses: List[str]) -> Tuple[int, int, int]:
        """Returns (persistence_count, qualifying_count, total_available)"""
        group = group.sort_values("reporting_date")
        available = group[group["calculation_status"] == "Calculated"]
        total_available = len(available)
        if total_available == 0:
            return 0, 0, 0
        # Take last window available periods
        recent = available.tail(window)
        qualifying = recent[recent["threshold_state"].isin(qualifying_statuses)]
        return len(qualifying), len(recent), total_available

    def _calc_approaching_distance(self, value: float, state: str, row: pd.Series) -> Tuple[Optional[float], str, bool]:
        direction = row["directionality"]
        if state != ThresholdState.GREEN.value and state != ThresholdState.NORMAL_OPERATING_BAND.value:
            return None, "", False

        if direction == "Higher is better":
            gl = row.get("green_lower_boundary")
            if pd.notna(gl) and pd.notna(value):
                dist = value - gl
                # If within 10% of range or 5 absolute units
                range_val = row.get("green_upper_boundary", 100) - row.get("lower_red_boundary", 0)
                threshold_dist = max(range_val * 0.1, 5.0) if pd.notna(range_val) else 5.0
                flag = 0 <= dist < threshold_dist
                return dist, "absolute", flag

        elif direction == "Lower is better":
            gu = row.get("green_upper_boundary")
            if pd.notna(gu) and pd.notna(value):
                dist = gu - value
                range_val = row.get("upper_red_boundary", 100) - row.get("green_lower_boundary", 0)
                threshold_dist = max(range_val * 0.1, 5.0) if pd.notna(range_val) else 5.0
                flag = 0 <= dist < threshold_dist
                return dist, "absolute", flag

        elif direction == "Context-sensitive":
            gl = row.get("green_lower_boundary")
            gu = row.get("green_upper_boundary")
            if pd.notna(gl) and pd.notna(gu) and pd.notna(value):
                dist_lower = value - gl
                dist_upper = gu - value
                if dist_lower <= dist_upper:
                    return dist_lower, "absolute", 0 <= dist_lower < 5.0
                else:
                    return dist_upper, "absolute", 0 <= dist_upper < 5.0

        return None, "", False

    def _check_escalation(self, group: pd.DataFrame) -> bool:
        group = group.sort_values("reporting_date")
        available = group[group["calculation_status"] == "Calculated"]
        if len(available) < 3:
            return False
        recent = available.tail(3)
        states = recent["threshold_state"].tolist()
        # Define severity order
        severity = {
            ThresholdState.GREEN.value: 0,
            ThresholdState.NORMAL_OPERATING_BAND.value: 0,
            ThresholdState.LOW_UTILISATION.value: 1,
            ThresholdState.LOWER_AMBER.value: 2,
            ThresholdState.UPPER_AMBER.value: 2,
            ThresholdState.AMBER.value: 2,
            ThresholdState.RED.value: 3,
            ThresholdState.CRITICAL_CAPACITY_PRESSURE.value: 3,
        }
        sevs = [severity.get(s, -1) for s in states]
        # Check strictly worsening over 3 periods
        return sevs[0] < sevs[1] < sevs[2]

    def _check_recovery(self, group: pd.DataFrame) -> bool:
        group = group.sort_values("reporting_date")
        available = group[group["calculation_status"] == "Calculated"]
        if len(available) < 2:
            return False
        recent = available.tail(2)
        states = recent["threshold_state"].tolist()
        # Red -> Amber or Amber -> Green or Critical -> Amber
        recovery_pairs = [
            (ThresholdState.RED.value, ThresholdState.AMBER.value),
            (ThresholdState.AMBER.value, ThresholdState.GREEN.value),
            (ThresholdState.CRITICAL_CAPACITY_PRESSURE.value, ThresholdState.UPPER_AMBER.value),
            (ThresholdState.CRITICAL_CAPACITY_PRESSURE.value, ThresholdState.NORMAL_OPERATING_BAND.value),
            (ThresholdState.LOW_UTILISATION.value, ThresholdState.LOWER_AMBER.value),
            (ThresholdState.LOW_UTILISATION.value, ThresholdState.NORMAL_OPERATING_BAND.value),
        ]
        return (states[0], states[1]) in recovery_pairs

    def evaluate_watch_conditions(self) -> pd.DataFrame:
        if self.df_classified is None:
            raise ValueError("Classified data not set.")

        df = self.df_classified.copy()
        current_date = datetime(2026, 7, 27).date()

        # Pre-compute persistence per group
        groups = df.groupby(["hospital_id", "department_id", "kpi_id"])

        # Merge trend signals (one per record)
        trend_map: Dict[Tuple[str, str, str, str], Dict[str, Any]] = {}
        if self.df_trends is not None:
            for _, t in self.df_trends.iterrows():
                key = (t["hospital_id"], t["department_id"], t["kpi_id"], t["reporting_date"])
                if key not in trend_map:
                    trend_map[key] = {}
                if t.get("signal_method") == "trend_slope":
                    trend_map[key] = {
                        "signal_type": t.get("signal_type", ""),
                        "signal_direction": t.get("signal_direction", ""),
                        "signal_strength": t.get("signal_strength", ""),
                        "trend_confidence_level": t.get("trend_confidence_level", ""),
                        "signal_record_id": t.get("signal_record_id", ""),
                    }

        # Pre-compute sustained movement per record
        sustained_map: Dict[Tuple[str, str, str, str], Dict[str, Any]] = {}
        if self.df_sustained is not None:
            for _, s in self.df_sustained.iterrows():
                start = datetime.strptime(s["sequence_start_date"], "%Y-%m-%d")
                end = datetime.strptime(s["sequence_end_date"], "%Y-%m-%d")
                hid, did, kpi = s["hospital_id"], s["department_id"], s["kpi_id"]
                d = start
                while d <= end:
                    key = (hid, did, kpi, d.strftime("%Y-%m-%d"))
                    sustained_map[key] = {
                        "movement_type": s.get("movement_type", ""),
                        "consecutive_observation_count": s.get("consecutive_observation_count", 0),
                        "movement_record_id": s.get("movement_record_id", ""),
                    }
                    d += timedelta(days=1)

        watch_records = []
        for (hosp, dept, kpi), group in groups:
            group = group.sort_values("reporting_date")
            for _, row in group.iterrows():
                watch = self._evaluate_single_record(
                    row, group, trend_map, sustained_map, current_date
                )
                if watch:
                    watch_records.append(watch)

        if watch_records:
            self.watches = watch_records
            return pd.DataFrame([self._watch_to_dict(w) for w in watch_records])
        return pd.DataFrame()

    def _evaluate_single_record(self, row: pd.Series, group: pd.DataFrame,
                                 trend_map: Dict, sustained_map: Dict,
                                 current_date: datetime.date) -> Optional[WatchConditionResult]:
        hosp = row["hospital_id"]
        dept = row["department_id"]
        kpi = row["kpi_id"]
        date = str(row["reporting_date"])
        state = str(row.get("threshold_state", ""))
        calc_status = str(row.get("calculation_status", ""))
        direction = str(row.get("directionality", ""))
        is_provisional = bool(row.get("threshold_is_provisional", False))
        review_date_str = row.get("required_review_date")

        # Get trend
        trend_key = (hosp, dept, kpi, date)
        trend = trend_map.get(trend_key, {})
        signal_type = trend.get("signal_type", "")
        trend_confidence = trend.get("trend_confidence_level", "")
        trend_interp = self._interpret_trend(signal_type, direction) if signal_type else TrendInterpretation.INSUFFICIENT_EVIDENCE.value
        is_deteriorating = self._is_deteriorating(trend_interp)
        is_improving = self._is_improving(trend_interp)

        # Get sustained movement
        sustained = sustained_map.get(trend_key, {})
        sustained_flag = bool(sustained)
        sustained_periods = sustained.get("consecutive_observation_count", 0) if sustained else 0
        sustained_movement_type = sustained.get("movement_type", "") if sustained else ""

        # Persistence
        amber_count, _, _ = self._calc_persistence(group, 3, [
            ThresholdState.AMBER.value, ThresholdState.LOWER_AMBER.value, ThresholdState.UPPER_AMBER.value
        ])
        red_count, _, _ = self._calc_persistence(group, 3, [
            ThresholdState.RED.value, ThresholdState.CRITICAL_CAPACITY_PRESSURE.value
        ])
        repeated_amber = amber_count >= 2
        repeated_red = red_count >= 2

        # Approaching threshold
        dist_val, dist_type, approaching = None, "", False
        if calc_status == "Calculated" and pd.notna(row.get("kpi_value")):
            dist_val, dist_type, approaching = self._calc_approaching_distance(
                row["kpi_value"], state, row
            )

        # Escalation and recovery
        escalating = self._check_escalation(group)
        recovery = self._check_recovery(group)

        # Review due status
        review_due = ReviewDueStatus.NOT_APPLICABLE.value
        if pd.notna(review_date_str) and str(review_date_str) != "":
            try:
                rd = datetime.strptime(str(review_date_str), "%Y-%m-%d").date()
                days_until = (rd - current_date).days
                if days_until < 0:
                    review_due = ReviewDueStatus.OVERDUE.value
                elif days_until <= 30:
                    review_due = ReviewDueStatus.DUE_SOON.value
                else:
                    review_due = ReviewDueStatus.NOT_YET_DUE.value
            except (ValueError, TypeError):
                pass

        # Determine watch conditions and severity
        watch_types: List[str] = []
        severity = WatchSeverity.NONE.value

        # Base breach
        breach_flag = state in (
            ThresholdState.AMBER.value, ThresholdState.RED.value,
            ThresholdState.LOWER_AMBER.value, ThresholdState.UPPER_AMBER.value,
            ThresholdState.CRITICAL_CAPACITY_PRESSURE.value, ThresholdState.LOW_UTILISATION.value
        )
        breach_type = BreachType.NO_BREACH.value
        if state in (ThresholdState.AMBER.value, ThresholdState.LOWER_AMBER.value, ThresholdState.UPPER_AMBER.value):
            breach_type = BreachType.AMBER_CONDITION.value
        elif state == ThresholdState.RED.value:
            breach_type = BreachType.RED_BREACH.value
        elif state == ThresholdState.CRITICAL_CAPACITY_PRESSURE.value:
            breach_type = BreachType.CRITICAL_CAPACITY_BREACH.value
        elif state == ThresholdState.LOW_UTILISATION.value:
            breach_type = BreachType.LOW_UTILISATION_CONDITION.value
        elif state == ThresholdState.UNAVAILABLE.value:
            breach_type = BreachType.UNAVAILABLE.value
        elif state == ThresholdState.NOT_ASSESSED.value:
            breach_type = BreachType.NOT_ASSESSED.value

        if is_provisional and breach_flag:
            breach_type = BreachType.PROVISIONAL_BREACH.value

        # Watch logic
        if calc_status != "Calculated":
            watch_types.append(WatchConditionType.NONE.value)
        else:
            if repeated_red:
                watch_types.append(WatchConditionType.REPEATED_RED.value)
                severity = self._max_severity(severity, WatchSeverity.HIGH.value)
            elif repeated_amber:
                watch_types.append(WatchConditionType.REPEATED_AMBER.value)
                severity = self._max_severity(severity, WatchSeverity.MODERATE.value)

            if approaching:
                watch_types.append(WatchConditionType.APPROACHING_THRESHOLD.value)
                severity = self._max_severity(severity, WatchSeverity.LOW.value)

            if is_deteriorating and trend_confidence in ("Medium", "High"):
                if state in (ThresholdState.AMBER.value, ThresholdState.LOWER_AMBER.value, ThresholdState.UPPER_AMBER.value):
                    watch_types.append(WatchConditionType.AMBER_PLUS_DETERIORATING_TREND.value)
                    severity = self._max_severity(severity, WatchSeverity.HIGH.value)
                else:
                    watch_types.append(WatchConditionType.DETERIORATING_TREND.value)
                    severity = self._max_severity(severity, WatchSeverity.LOW.value)

            if sustained_flag and is_deteriorating and sustained_periods >= 3:
                watch_types.append(WatchConditionType.SUSTAINED_DETERIORATION.value)
                severity = self._max_severity(severity, WatchSeverity.MODERATE.value)

            if escalating:
                watch_types.append(WatchConditionType.ESCALATING_SEVERITY.value)
                severity = self._max_severity(severity, WatchSeverity.HIGH.value)

            if recovery and not is_deteriorating:
                watch_types.append(WatchConditionType.RECOVERY_WATCH.value)
                severity = self._max_severity(severity, WatchSeverity.INFORMATIONAL.value)

            if is_provisional and breach_flag:
                watch_types.append(WatchConditionType.PROVISIONAL_WATCH.value)
                severity = self._max_severity(severity, WatchSeverity.MODERATE.value)

            if review_due in (ReviewDueStatus.DUE_SOON.value, ReviewDueStatus.OVERDUE.value) and is_provisional:
                watch_types.append(WatchConditionType.REVIEW_DUE_GOVERNANCE_WATCH.value)
                severity = self._max_severity(severity, WatchSeverity.INFORMATIONAL.value)

            # Severity boosts for critical states
            if state == ThresholdState.CRITICAL_CAPACITY_PRESSURE.value:
                severity = self._max_severity(severity, WatchSeverity.CRITICAL.value)
            elif state == ThresholdState.RED.value and is_deteriorating and sustained_flag:
                severity = self._max_severity(severity, WatchSeverity.CRITICAL.value)
            elif state == ThresholdState.RED.value:
                severity = self._max_severity(severity, WatchSeverity.HIGH.value)

            if not watch_types:
                watch_types.append(WatchConditionType.NONE.value)

        watch_type_str = "; ".join(watch_types) if watch_types else WatchConditionType.NONE.value
        watch_flag = any(wt != WatchConditionType.NONE.value for wt in watch_types)

        # Governance
        op_status = OperationalUseStatus.FULLY_OPERATIONAL.value
        gov_warning = ""
        if is_provisional:
            op_status = OperationalUseStatus.PROTOTYPE_USE_WITH_CONDITIONS.value
            prov_cfg = self.df_provisional[self.df_provisional["kpi_id"] == kpi]
            if not prov_cfg.empty:
                gov_warning = str(prov_cfg.iloc[0].get("governance_warning_template", "Provisional threshold."))

        # Summary
        watch_summary = f"{state}"
        if watch_flag:
            watch_summary += f" | Watch: {watch_type_str}"
        if is_deteriorating:
            watch_summary += " | Deteriorating"

        return WatchConditionResult(
            watch_record_id=self._generate_id("WCH"),
            classification_record_id="",
            integration_record_id=str(row.get("integration_record_id", "")),
            hospital_id=hosp,
            department_id=dept,
            reporting_date=date,
            kpi_id=kpi,
            kpi_name=str(row.get("kpi_name", "")),
            kpi_value=row.get("kpi_value") if pd.notna(row.get("kpi_value")) else None,
            kpi_unit=str(row.get("unit", row.get("unit_thresh", ""))),
            calculation_status=calc_status,
            threshold_state=state,
            breach_type=breach_type,
            breach_flag=breach_flag,
            threshold_version=str(row.get("threshold_version", "")),
            threshold_source="config/kpi_threshold_config.csv",
            approval_status=str(row.get("approval_status", "")),
            threshold_is_provisional=is_provisional,
            watch_condition_flag=watch_flag,
            watch_condition_type=watch_type_str,
            watch_severity=severity,
            watch_rule_id="WC-MULTI",
            watch_rule_version="v1.0-draft",
            watch_summary=watch_summary,
            persistence_count=amber_count if repeated_amber else (red_count if repeated_red else 0),
            qualifying_observation_count=3,
            observation_window=3,
            repeated_amber_flag=repeated_amber,
            repeated_red_flag=repeated_red,
            trend_direction=signal_type,
            operational_trend_interpretation=trend_interp,
            trend_confidence=trend_confidence,
            sustained_movement_flag=sustained_flag,
            statistical_signal_flag=bool(signal_type and signal_type != "No Signal"),
            boundary_reference=str(row.get("green_lower_boundary", row.get("green_upper_boundary", ""))),
            distance_to_boundary=dist_val,
            distance_measure_type=dist_type,
            approaching_threshold_flag=approaching,
            operational_use_status=op_status,
            governance_warning=gov_warning,
            required_review_date=str(review_date_str) if pd.notna(review_date_str) else None,
            review_due_status=review_due,
            source_kpi_record_id=str(row.get("analytical_record_id", "")),
            source_threshold_record_id=str(row.get("decision_record_id", "")),
            source_trend_record_id=trend.get("signal_record_id", ""),
            evidence_record_id=self._generate_id("EVD"),
            lineage_record_id=self._generate_id("LIN"),
            engine_run_id=self.engine_run_id,
            processed_at=self.processed_at,
            issue_flag=False,
        )

    def _max_severity(self, current: str, candidate: str) -> str:
        order = [WatchSeverity.NONE.value, WatchSeverity.INFORMATIONAL.value,
                 WatchSeverity.LOW.value, WatchSeverity.MODERATE.value,
                 WatchSeverity.HIGH.value, WatchSeverity.CRITICAL.value]
        try:
            ci = order.index(current)
        except ValueError:
            ci = -1
        try:
            ni = order.index(candidate)
        except ValueError:
            ni = -1
        return order[max(ci, ni)]

    def _watch_to_dict(self, w: WatchConditionResult) -> Dict[str, Any]:
        return {
            "watch_record_id": w.watch_record_id,
            "integration_record_id": w.integration_record_id,
            "hospital_id": w.hospital_id,
            "department_id": w.department_id,
            "reporting_date": w.reporting_date,
            "kpi_id": w.kpi_id,
            "kpi_name": w.kpi_name,
            "kpi_value": w.kpi_value,
            "kpi_unit": w.kpi_unit,
            "calculation_status": w.calculation_status,
            "threshold_state": w.threshold_state,
            "breach_type": w.breach_type,
            "breach_flag": w.breach_flag,
            "threshold_version": w.threshold_version,
            "threshold_source": w.threshold_source,
            "approval_status": w.approval_status,
            "threshold_is_provisional": w.threshold_is_provisional,
            "watch_condition_flag": w.watch_condition_flag,
            "watch_condition_type": w.watch_condition_type,
            "watch_severity": w.watch_severity,
            "watch_rule_id": w.watch_rule_id,
            "watch_rule_version": w.watch_rule_version,
            "watch_summary": w.watch_summary,
            "persistence_count": w.persistence_count,
            "qualifying_observation_count": w.qualifying_observation_count,
            "observation_window": w.observation_window,
            "repeated_amber_flag": w.repeated_amber_flag,
            "repeated_red_flag": w.repeated_red_flag,
            "trend_direction": w.trend_direction,
            "operational_trend_interpretation": w.operational_trend_interpretation,
            "trend_confidence": w.trend_confidence,
            "sustained_movement_flag": w.sustained_movement_flag,
            "statistical_signal_flag": w.statistical_signal_flag,
            "boundary_reference": w.boundary_reference,
            "distance_to_boundary": w.distance_to_boundary,
            "distance_measure_type": w.distance_measure_type,
            "approaching_threshold_flag": w.approaching_threshold_flag,
            "operational_use_status": w.operational_use_status,
            "governance_warning": w.governance_warning,
            "required_review_date": w.required_review_date,
            "review_due_status": w.review_due_status,
            "source_kpi_record_id": w.source_kpi_record_id,
            "source_threshold_record_id": w.source_threshold_record_id,
            "source_trend_record_id": w.source_trend_record_id,
            "evidence_record_id": w.evidence_record_id,
            "lineage_record_id": w.lineage_record_id,
            "engine_run_id": w.engine_run_id,
            "processed_at": w.processed_at,
            "issue_flag": w.issue_flag,
        }

    def generate_daily_summary(self, df_watches: pd.DataFrame) -> pd.DataFrame:
        if df_watches.empty:
            return pd.DataFrame()

        summary_rows = []
        for (hosp, dept, date), group in df_watches.groupby(["hospital_id", "department_id", "reporting_date"]):
            calc_mask = group["calculation_status"] == "Calculated"
            calc_group = group[calc_mask]

            green_count = len(calc_group[calc_group["threshold_state"].isin([ThresholdState.GREEN.value, ThresholdState.NORMAL_OPERATING_BAND.value])])
            amber_count = len(calc_group[calc_group["threshold_state"].isin([ThresholdState.AMBER.value, ThresholdState.LOWER_AMBER.value, ThresholdState.UPPER_AMBER.value])])
            red_count = len(calc_group[calc_group["threshold_state"].isin([ThresholdState.RED.value])])
            ccp_count = len(calc_group[calc_group["threshold_state"] == ThresholdState.CRITICAL_CAPACITY_PRESSURE.value])
            low_util_count = len(calc_group[calc_group["threshold_state"] == ThresholdState.LOW_UTILISATION.value])
            watch_count = len(calc_group[calc_group["watch_condition_flag"] == True])
            high_watch = len(calc_group[calc_group["watch_severity"] == WatchSeverity.HIGH.value])
            critical_watch = len(calc_group[calc_group["watch_severity"] == WatchSeverity.CRITICAL.value])
            prov_watch = len(calc_group[(calc_group["watch_condition_flag"] == True) & (calc_group["threshold_is_provisional"] == True)])
            unavailable_count = len(group[group["calculation_status"] != "Calculated"])

            sevs = calc_group["watch_severity"].unique()
            max_sev = WatchSeverity.NONE.value
            for s in [WatchSeverity.CRITICAL.value, WatchSeverity.HIGH.value, WatchSeverity.MODERATE.value,
                      WatchSeverity.LOW.value, WatchSeverity.INFORMATIONAL.value]:
                if s in sevs:
                    max_sev = s
                    break

            summary_rows.append({
                "summary_record_id": self._generate_id("SUM"),
                "hospital_id": hosp,
                "department_id": dept,
                "reporting_date": date,
                "kpi_count": len(group["kpi_id"].unique()),
                "calculated_kpi_count": len(calc_group),
                "green_count": green_count,
                "amber_count": amber_count,
                "red_count": red_count,
                "critical_capacity_pressure_count": ccp_count,
                "low_utilisation_count": low_util_count,
                "watch_condition_count": watch_count,
                "high_watch_count": high_watch,
                "critical_watch_count": critical_watch,
                "provisional_watch_count": prov_watch,
                "unavailable_count": unavailable_count,
                "max_observed_watch_severity": max_sev,
                "summary_status": "Complete",
                "engine_run_id": self.engine_run_id,
                "processed_at": self.processed_at,
            })

        return pd.DataFrame(summary_rows)

    def to_watch_dataframe(self) -> pd.DataFrame:
        if not self.watches:
            return pd.DataFrame()
        return pd.DataFrame([self._watch_to_dict(w) for w in self.watches])

    def to_summary_dataframe(self) -> pd.DataFrame:
        if not self.summaries:
            return pd.DataFrame()
        rows = []
        for s in self.summaries:
            rows.append({
                "summary_record_id": s.summary_record_id,
                "hospital_id": s.hospital_id,
                "department_id": s.department_id,
                "reporting_date": s.reporting_date,
                "kpi_count": s.kpi_count,
                "calculated_kpi_count": s.calculated_kpi_count,
                "green_count": s.green_count,
                "amber_count": s.amber_count,
                "red_count": s.red_count,
                "critical_capacity_pressure_count": s.critical_capacity_pressure_count,
                "low_utilisation_count": s.low_utilisation_count,
                "watch_condition_count": s.watch_condition_count,
                "high_watch_count": s.high_watch_count,
                "critical_watch_count": s.critical_watch_count,
                "provisional_watch_count": s.provisional_watch_count,
                "unavailable_count": s.unavailable_count,
                "max_observed_watch_severity": s.max_observed_watch_severity,
                "summary_status": s.summary_status,
                "engine_run_id": s.engine_run_id,
                "processed_at": s.processed_at,
            })
        return pd.DataFrame(rows)
