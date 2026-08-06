"""
Sentinel360 Healthcare — Trend and Statistical Signal Engine

Governed trend analysis without approved performance thresholds.
Does not recalculate KPIs or assign Green/Amber/Red.

Step: 2B-1
"""

import os
import json
import hashlib
import uuid
import logging
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

from trend_analytical_models import (
    PeriodComparisonResult,
    RollingStatisticResult,
    StatisticalSignalResult,
    SustainedMovementResult,
    TrendEvidenceRecord,
    TrendLineageRecord,
    TrendIssueRecord,
    TrendAuditRecord,
    TrendRunManifest,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Safe CSV loader
# ---------------------------------------------------------------------------

def _safe_read_csv(path: str) -> Optional[pd.DataFrame]:
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=True)
        if df.empty:
            return None
        return df
    except pd.errors.EmptyDataError:
        return None
    except Exception:
        return None


def _file_checksum(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# TrendStatisticalSignalEngine
# ---------------------------------------------------------------------------

class TrendStatisticalSignalEngine:
    """
    Governed engine for trend and statistical-signal analysis.
    """

    SIX_KPIS = ["kpi_001", "kpi_002", "kpi_003", "kpi_004", "kpi_005", "kpi_006"]

    KPI_DIRECTIONALITY: Dict[str, str] = {
        "kpi_001": "higher_is_better",
        "kpi_002": "lower_is_better",
        "kpi_003": "context_sensitive",
        "kpi_004": "lower_is_better",
        "kpi_005": "lower_is_better",
        "kpi_006": "higher_is_better",
    }

    COMPARISON_TYPES = [
        "Previous Available Day",
        "Previous Calendar Day",
        "Previous Week",
        "Previous Month",
        "Same Period Previous Month",
        "Rolling 7-Day Average",
        "Rolling 14-Day Average",
        "Rolling 30-Day Average",
        "Rolling 3-Month Average",
        "Baseline Period Average",
    ]

    def __init__(
        self,
        project_root: str,
        trend_run_id: Optional[str] = None,
        skip_zscore: bool = False,
        skip_mad: bool = False,
        skip_slope: bool = False,
        skip_volatility: bool = False,
        skip_confidence: bool = False,
    ):
        self.project_root = os.path.abspath(project_root)
        self.trend_run_id = trend_run_id or f"TREND-{uuid.uuid4().hex[:12].upper()}"
        self.skip_zscore = skip_zscore
        self.skip_mad = skip_mad
        self.skip_slope = skip_slope
        self.skip_volatility = skip_volatility
        self.skip_confidence = skip_confidence
        self._data_cache: Dict[str, Optional[pd.DataFrame]] = {}
        self.issues: List[TrendIssueRecord] = []
        self.audit: List[TrendAuditRecord] = []
        self.evidence: List[TrendEvidenceRecord] = []
        self.lineage: List[TrendLineageRecord] = []
        self.period_comparisons: List[PeriodComparisonResult] = []
        self.rolling_statistics: List[RollingStatisticResult] = []
        self.signals: List[StatisticalSignalResult] = []
        self.sustained_movements: List[SustainedMovementResult] = []

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _path(self, rel: str) -> str:
        return os.path.join(self.project_root, rel)

    def _load(self, rel: str) -> Optional[pd.DataFrame]:
        if rel not in self._data_cache:
            self._data_cache[rel] = _safe_read_csv(self._path(rel))
        return self._data_cache[rel]

    def _add_issue(self, severity: str, issue_type: str, message: str, kpi_id: str = "", hospital_id: str = "", department_id: str = "", reporting_date: Optional[date] = None, source_record_id: str = "") -> None:
        self.issues.append(TrendIssueRecord(
            trend_issue_id=f"TISS-{uuid.uuid4().hex[:12].upper()}",
            severity=severity,
            issue_type=issue_type,
            hospital_id=hospital_id,
            department_id=department_id,
            kpi_id=kpi_id,
            reporting_date=reporting_date,
            message=message,
            source_record_id=source_record_id,
            trend_run_id=self.trend_run_id,
        ))

    def _add_audit(self, event_type: str, event_status: str, kpi_id: str = "", details: str = "") -> None:
        self.audit.append(TrendAuditRecord(
            audit_id=f"TAUD-{uuid.uuid4().hex[:12].upper()}",
            event_type=event_type,
            event_status=event_status,
            kpi_id=kpi_id,
            trend_run_id=self.trend_run_id,
            event_time=datetime.now(),
            details=details,
        ))

    def _add_evidence(self, result_record_id: str, result_type: str, kpi_id: str, evidence_role: str, source_analytical_record_id: str, source_reporting_date: Optional[date], source_kpi_value: Optional[float], observation_included: bool, exclusion_reason: str = "") -> None:
        self.evidence.append(TrendEvidenceRecord(
            trend_evidence_id=f"TEV-{uuid.uuid4().hex[:12].upper()}",
            result_record_id=result_record_id,
            result_type=result_type,
            kpi_id=kpi_id,
            evidence_role=evidence_role,
            source_analytical_record_id=source_analytical_record_id,
            source_reporting_date=source_reporting_date,
            source_kpi_value=source_kpi_value,
            observation_included=observation_included,
            exclusion_reason=exclusion_reason,
            trend_run_id=self.trend_run_id,
        ))

    def _add_lineage(self, result_record_id: str, result_type: str, kpi_id: str, source_analytical_dataset: str, source_analytical_record_id: str, source_integration_run_id: str, transformation_name: str) -> None:
        self.lineage.append(TrendLineageRecord(
            trend_lineage_id=f"TLIN-{uuid.uuid4().hex[:12].upper()}",
            result_record_id=result_record_id,
            result_type=result_type,
            kpi_id=kpi_id,
            source_analytical_dataset=source_analytical_dataset,
            source_analytical_record_id=source_analytical_record_id,
            source_integration_run_id=source_integration_run_id,
            transformation_name=transformation_name,
            configuration_version="v1.0-draft",
            trend_run_id=self.trend_run_id,
            created_at=datetime.now(),
        ))

    # -----------------------------------------------------------------------
    # 1. Load and validate
    # -----------------------------------------------------------------------

    def load_accepted_input(self) -> Optional[pd.DataFrame]:
        df = self._load("data/analytical/analytical_six_kpi_daily.csv")
        if df is None:
            self._add_issue("Blocking", "LoadError", "Cannot load analytical_six_kpi_daily.csv")
            return None
        # Parse dates and numeric
        df["reporting_date"] = pd.to_datetime(df["reporting_date"], errors="coerce").dt.date
        df["kpi_value"] = pd.to_numeric(df["kpi_value"], errors="coerce")
        df["reporting_month"] = pd.to_numeric(df["reporting_month"], errors="coerce")
        df["reporting_year"] = pd.to_numeric(df["reporting_year"], errors="coerce")
        # Sort deterministically
        df = df.sort_values(["hospital_id", "department_id", "kpi_id", "reporting_date"]).reset_index(drop=True)
        self._add_audit("load", "Success", details=f"Loaded {len(df)} rows from analytical_six_kpi_daily.csv")
        return df

    def validate_phase_2a_acceptance(self) -> bool:
        closure_path = self._path("data/analytical/analytical_phase_2a_closure_snapshot.csv")
        if not os.path.exists(closure_path):
            self._add_issue("Warning", "ClosureCheck", "Phase 2A closure snapshot not found; proceeding with caution.")
            return True
        self._add_audit("closure_check", "Success", details="Phase 2A closure snapshot found")
        return True

    def validate_kpi_set(self, df: pd.DataFrame) -> bool:
        found = set(df["kpi_id"].dropna().unique().tolist())
        expected = set(self.SIX_KPIS)
        unknown = found - expected
        if unknown:
            self._add_issue("Blocking", "KPIValidation", f"Unknown KPIs in input: {unknown}")
            return False
        self._add_audit("kpi_validation", "Success", details=f"KPIs validated: {found}")
        return True

    # -----------------------------------------------------------------------
    # 2. Prepare time series per grain
    # -----------------------------------------------------------------------

    def prepare_time_series(self, df: pd.DataFrame) -> Dict[Tuple[str, str, str], pd.DataFrame]:
        series_map: Dict[Tuple[str, str, str], pd.DataFrame] = {}
        for (hosp, dept, kpi), sub in df.groupby(["hospital_id", "department_id", "kpi_id"]):
            sub = sub.sort_values("reporting_date").reset_index(drop=True)
            series_map[(hosp, dept, kpi)] = sub
        return series_map

    # -----------------------------------------------------------------------
    # 3. Period comparisons
    # -----------------------------------------------------------------------

    def build_period_comparisons(self, df: pd.DataFrame) -> None:
        series_map = self.prepare_time_series(df)
        for (hosp, dept, kpi), sub in series_map.items():
            self._process_grain_comparisons(hosp, dept, kpi, sub)
        self._add_audit("period_comparison", "Success", details=f"Generated {len(self.period_comparisons)} period comparisons")

    def _process_grain_comparisons(self, hosp: str, dept: str, kpi: str, sub: pd.DataFrame) -> None:
        calc_mask = sub["calculation_status"] == "Calculated"
        calc_sub = sub[calc_mask].copy()
        kpi_name = str(sub["kpi_name"].iloc[0]) if not sub.empty else ""
        domain = str(sub["domain"].iloc[0]) if not sub.empty else ""
        unit = str(sub["unit"].iloc[0]) if not sub.empty else ""
        source_dataset = str(sub["source_analytical_dataset"].iloc[0]) if not sub.empty else ""

        for idx, row in sub.iterrows():
            curr_date = row["reporting_date"]
            curr_val = row["kpi_value"] if row["calculation_status"] == "Calculated" else None
            curr_is_calc = row["calculation_status"] == "Calculated"
            curr_conf = str(row.get("data_confidence_level", ""))

            comparisons_to_build = [
                "Previous Available Day",
                "Previous Calendar Day",
                "Previous Week",
                "Previous Month",
                "Rolling 7-Day Average",
                "Rolling 14-Day Average",
                "Rolling 30-Day Average",
                "Baseline Period Average",
            ]

            curr_record_id = str(row["analytical_record_id"])
            curr_calc_status = str(row["calculation_status"])
            curr_integration_run_id = str(row.get("integration_run_id", ""))
            for comp_type in comparisons_to_build:
                self._build_single_comparison(
                    hosp, dept, kpi, kpi_name, domain, unit, source_dataset,
                    sub, calc_sub, curr_date, curr_val, curr_is_calc, curr_conf,
                    curr_record_id, curr_calc_status, curr_integration_run_id,
                    comp_type,
                )

    def _build_single_comparison(self, hosp, dept, kpi, kpi_name, domain, unit, source_dataset, sub, calc_sub, curr_date, curr_val, curr_is_calc, curr_conf, curr_record_id, curr_calc_status, curr_integration_run_id, comp_type):
        comp_val = None
        comp_date = None
        comp_record_id = ""
        obs_used = 0
        coverage_pct = None
        history_status = ""
        calc_status = "Not Calculated"
        abs_change = None
        pct_change = None
        pct_status = ""
        math_dir = "Unavailable"
        biz_interp = "Unavailable"
        interp_status = ""
        interp_reason = ""
        trend_conf = "Unavailable"
        trend_conf_reason = ""

        if not curr_is_calc:
            calc_status = "Current Value Unavailable"
            history_status = "Unavailable"
            trend_conf = "Unavailable"
            trend_conf_reason = "Current KPI value is not calculated"
        else:
            # Determine comparison value
            if comp_type == "Previous Available Day":
                prior = calc_sub[calc_sub["reporting_date"] < curr_date]
                if not prior.empty:
                    prior_row = prior.iloc[-1]
                    comp_val = prior_row["kpi_value"]
                    comp_date = prior_row["reporting_date"]
                    comp_record_id = prior_row["analytical_record_id"]
                    obs_used = 1
                    history_status = "Complete"
                else:
                    calc_status = "Comparison Value Unavailable"
                    history_status = "Insufficient"
            elif comp_type == "Previous Calendar Day":
                target = curr_date - timedelta(days=1)
                prior = sub[sub["reporting_date"] == target]
                if not prior.empty:
                    pr = prior.iloc[0]
                    if pr["calculation_status"] == "Calculated":
                        comp_val = pr["kpi_value"]
                        comp_date = pr["reporting_date"]
                        comp_record_id = pr["analytical_record_id"]
                        obs_used = 1
                        history_status = "Complete"
                    else:
                        calc_status = "Comparison Value Unavailable"
                        history_status = "Unavailable"
                else:
                    calc_status = "Comparison Value Unavailable"
                    history_status = "Missing"
            elif comp_type == "Previous Week":
                target = curr_date - timedelta(days=7)
                prior = sub[sub["reporting_date"] == target]
                if not prior.empty:
                    pr = prior.iloc[0]
                    if pr["calculation_status"] == "Calculated":
                        comp_val = pr["kpi_value"]
                        comp_date = pr["reporting_date"]
                        comp_record_id = pr["analytical_record_id"]
                        obs_used = 1
                        history_status = "Complete"
                    else:
                        calc_status = "Comparison Value Unavailable"
                        history_status = "Unavailable"
                else:
                    calc_status = "Comparison Value Unavailable"
                    history_status = "Missing"
            elif comp_type == "Previous Month":
                target = curr_date - timedelta(days=30)
                # Find nearest within +/- 3 days
                window = sub[sub["reporting_date"].between(target - timedelta(days=3), target + timedelta(days=3))]
                calc_window = window[window["calculation_status"] == "Calculated"]
                if not calc_window.empty:
                    pr = calc_window.iloc[-1]
                    comp_val = pr["kpi_value"]
                    comp_date = pr["reporting_date"]
                    comp_record_id = pr["analytical_record_id"]
                    obs_used = 1
                    history_status = "Complete"
                else:
                    calc_status = "Comparison Value Unavailable"
                    history_status = "Missing"
            elif comp_type.startswith("Rolling") and "Average" in comp_type:
                window_days = self._extract_window_days(comp_type)
                if window_days:
                    window_start = curr_date - timedelta(days=window_days - 1)
                    window_sub = calc_sub[calc_sub["reporting_date"].between(window_start, curr_date)]
                    if not window_sub.empty:
                        comp_val = float(window_sub["kpi_value"].mean())
                        obs_used = len(window_sub)
                        expected = window_days
                        coverage_pct = (obs_used / expected) * 100 if expected > 0 else None
                        history_status = "Complete" if coverage_pct and coverage_pct >= 50 else "Partial"
                    else:
                        calc_status = "Comparison Value Unavailable"
                        history_status = "Insufficient"
                else:
                    calc_status = "Invalid Input"
            elif comp_type == "Baseline Period Average":
                baseline = calc_sub[calc_sub["reporting_date"] < curr_date]
                if not baseline.empty:
                    comp_val = float(baseline["kpi_value"].mean())
                    obs_used = len(baseline)
                    history_status = "Complete"
                else:
                    calc_status = "Comparison Value Unavailable"
                    history_status = "Insufficient"

            # Calculate changes
            if curr_is_calc and comp_val is not None:
                abs_change = curr_val - comp_val
                if comp_val != 0:
                    pct_change = (abs_change / abs(comp_val)) * 100.0
                    pct_status = "Calculated"
                else:
                    pct_change = None
                    pct_status = "Zero Comparison Value"
                calc_status = "Calculated"

                # Mathematical direction
                tolerance = 1e-9
                if abs_change is not None and abs(abs_change) <= tolerance:
                    math_dir = "Stable"
                elif abs_change is not None and abs_change > tolerance:
                    math_dir = "Increasing"
                elif abs_change is not None and abs_change < -tolerance:
                    math_dir = "Decreasing"

                # Business interpretation
                directionality = self.KPI_DIRECTIONALITY.get(kpi, "unknown")
                if directionality == "higher_is_better":
                    if math_dir == "Increasing":
                        biz_interp = "Improvement"
                    elif math_dir == "Decreasing":
                        biz_interp = "Deterioration"
                    else:
                        biz_interp = "Stable"
                elif directionality == "lower_is_better":
                    if math_dir == "Increasing":
                        biz_interp = "Deterioration"
                    elif math_dir == "Decreasing":
                        biz_interp = "Improvement"
                    else:
                        biz_interp = "Stable"
                elif directionality == "context_sensitive":
                    biz_interp = "Context Review"
                    interp_reason = "kpi_003 Bed Occupancy Rate requires context-sensitive interpretation"
                else:
                    biz_interp = "Context Review"

                interp_status = "Provisional"
                interp_reason = interp_reason or "Trend interpretation is provisional pending stakeholder-approved thresholds"

                # Confidence
                trend_conf, trend_conf_reason = self._evaluate_trend_confidence(obs_used, coverage_pct or 100.0, curr_conf)
            elif curr_is_calc and comp_val is None:
                calc_status = calc_status if calc_status != "Not Calculated" else "Comparison Value Unavailable"
                math_dir = "Insufficient History"
                biz_interp = "Insufficient History"
                trend_conf = "Unavailable"
                trend_conf_reason = "Comparison value unavailable"

        # Build record ID
        date_str = str(curr_date).replace("-", "")
        comp_slug = comp_type.replace(" ", "_").replace("-", "_")
        rec_id = f"TCMP-{kpi}-{hosp}-{dept}-DAILY-{date_str}-{comp_slug}"

        pcr = PeriodComparisonResult(
            comparison_record_id=rec_id,
            hospital_id=hosp,
            department_id=dept,
            kpi_id=kpi,
            kpi_name=kpi_name,
            domain=domain,
            unit=unit,
            period_type="Daily",
            comparison_type=comp_type,
            current_period_start=curr_date,
            current_period_end=curr_date,
            comparison_period_start=comp_date,
            comparison_period_end=comp_date,
            current_value=curr_val,
            comparison_value=comp_val,
            absolute_change=abs_change,
            percentage_change=pct_change,
            percentage_change_status=pct_status,
            mathematical_trend_direction=math_dir,
            business_movement_interpretation=biz_interp,
            interpretation_status=interp_status,
            interpretation_reason=interp_reason,
            calculation_status=calc_status,
            history_status=history_status,
            observations_used=obs_used,
            coverage_percentage=coverage_pct,
            source_data_confidence=curr_conf,
            trend_confidence_level=trend_conf,
            trend_confidence_reason=trend_conf_reason,
            configuration_version="v1.0-draft",
            trend_run_id=self.trend_run_id,
            calculated_at=datetime.now(),
        )
        self.period_comparisons.append(pcr)

        # Evidence
        self._add_evidence(rec_id, "period_comparison", kpi, "current", curr_record_id, curr_date, curr_val, curr_is_calc, "" if curr_is_calc else curr_calc_status)
        if comp_record_id:
            self._add_evidence(rec_id, "period_comparison", kpi, "comparison", comp_record_id, comp_date, comp_val, True, "")
        # Lineage
        self._add_lineage(rec_id, "period_comparison", kpi, source_dataset, curr_record_id, curr_integration_run_id, f"period_comparison_{comp_type}")

    def _extract_window_days(self, comp_type: str) -> Optional[int]:
        mapping = {
            "Rolling 7-Day Average": 7,
            "Rolling 14-Day Average": 14,
            "Rolling 30-Day Average": 30,
            "Rolling 3-Month Average": 90,
        }
        return mapping.get(comp_type)

    def _evaluate_trend_confidence(self, obs_used: int, coverage_pct: float, source_conf: str) -> Tuple[str, str]:
        if self.skip_confidence:
            return "Unavailable", "Confidence evaluation skipped"
        if obs_used >= 15 and coverage_pct >= 75 and source_conf == "High":
            return "High", "Sufficient history and coverage with high source confidence"
        elif obs_used >= 8 and coverage_pct >= 50:
            return "Medium", "Sufficient minimum history with partial coverage"
        elif obs_used >= 4 and coverage_pct >= 25:
            return "Low", "Minimum history barely met or sparse observations"
        else:
            return "Unavailable", "History or coverage below minimum thresholds"

    # -----------------------------------------------------------------------
    # 4. Rolling statistics
    # -----------------------------------------------------------------------

    def calculate_rolling_statistics(self, df: pd.DataFrame) -> None:
        windows = [7, 14, 30]
        series_map = self.prepare_time_series(df)
        for (hosp, dept, kpi), sub in series_map.items():
            calc_sub = sub[sub["calculation_status"] == "Calculated"].copy()
            if calc_sub.empty:
                continue
            calc_sub = calc_sub.sort_values("reporting_date").reset_index(drop=True)
            for w in windows:
                self._process_rolling_window(hosp, dept, kpi, sub, calc_sub, w)
        self._add_audit("rolling_statistics", "Success", details=f"Generated {len(self.rolling_statistics)} rolling statistics")

    def _process_rolling_window(self, hosp: str, dept: str, kpi: str, sub: pd.DataFrame, calc_sub: pd.DataFrame, window: int) -> None:
        for idx, row in calc_sub.iterrows():
            curr_date = row["reporting_date"]
            window_start = curr_date - timedelta(days=window - 1)
            window_sub = calc_sub[calc_sub["reporting_date"].between(window_start, curr_date)]
            valid_count = len(window_sub)
            expected = window
            coverage = (valid_count / expected) * 100.0 if expected > 0 else 0.0

            # Minimum history rules
            min_req = {7: 4, 14: 7, 30: 15}.get(window, 4)
            if valid_count < min_req:
                calc_status = "Insufficient History"
                history_status = "Insufficient"
            else:
                calc_status = "Calculated"
                history_status = "Complete" if coverage >= 75 else "Partial"

            if valid_count > 0:
                vals = window_sub["kpi_value"].astype(float)
                rmean = float(vals.mean())
                rmedian = float(vals.median())
                rmin = float(vals.min())
                rmax = float(vals.max())
                rstd = float(vals.std(ddof=0)) if valid_count > 1 else 0.0
            else:
                rmean = rmedian = rmin = rmax = rstd = None

            rec_id = f"TROLL-{kpi}-{hosp}-{dept}-{str(curr_date).replace('-', '')}-{window}"
            self.rolling_statistics.append(RollingStatisticResult(
                rolling_record_id=rec_id,
                hospital_id=hosp,
                department_id=dept,
                kpi_id=kpi,
                reporting_date=curr_date,
                rolling_window=window,
                rolling_mean=rmean,
                rolling_median=rmedian,
                rolling_minimum=rmin,
                rolling_maximum=rmax,
                rolling_standard_deviation=rstd,
                rolling_valid_observation_count=valid_count,
                rolling_expected_observation_count=expected,
                rolling_coverage_percentage=coverage,
                calculation_status=calc_status,
                history_status=history_status,
                trend_run_id=self.trend_run_id,
                calculated_at=datetime.now(),
            ))

    # -----------------------------------------------------------------------
    # 5. Statistical signals
    # -----------------------------------------------------------------------

    def generate_signal_candidates(self, df: pd.DataFrame) -> None:
        series_map = self.prepare_time_series(df)
        for (hosp, dept, kpi), sub in series_map.items():
            calc_sub = sub[sub["calculation_status"] == "Calculated"].copy()
            if calc_sub.empty:
                continue
            calc_sub = calc_sub.sort_values("reporting_date").reset_index(drop=True)
            vals = calc_sub["kpi_value"].astype(float).values
            dates = calc_sub["reporting_date"].values
            record_ids = calc_sub["analytical_record_id"].values
            n = len(vals)

            for i in range(n):
                curr_val = vals[i]
                curr_date = dates[i]
                curr_rec_id = record_ids[i]

                # Z-score
                if not self.skip_zscore:
                    self._calc_zscore(hosp, dept, kpi, calc_sub, i, curr_val, curr_date, curr_rec_id, vals, dates, record_ids)
                # MAD
                if not self.skip_mad:
                    self._calc_mad(hosp, dept, kpi, calc_sub, i, curr_val, curr_date, curr_rec_id, vals, dates, record_ids)
                # Slope
                if not self.skip_slope:
                    self._calc_slope(hosp, dept, kpi, calc_sub, i, curr_val, curr_date, curr_rec_id, vals, dates, record_ids)
                # Volatility
                if not self.skip_volatility:
                    self._calc_volatility(hosp, dept, kpi, calc_sub, i, curr_val, curr_date, curr_rec_id, vals, dates, record_ids)

        self._add_audit("signals", "Success", details=f"Generated {len(self.signals)} statistical signals")

    def _calc_zscore(self, hosp, dept, kpi, calc_sub, i, curr_val, curr_date, curr_rec_id, vals, dates, record_ids):
        history_window = 30
        min_obs = 8
        sensitivity = 2.0
        start_idx = max(0, i - history_window)
        hist_vals = vals[start_idx:i]
        obs_used = len(hist_vals)
        if obs_used < min_obs:
            return
        mean = float(np.mean(hist_vals))
        std = float(np.std(hist_vals, ddof=0))
        if std == 0:
            self._add_signal(hosp, dept, kpi, curr_date, "z_score", "Zero Historical Variance", 0.0, "none", "none", "Zero Historical Variance", obs_used, history_window, "Complete", "Low", sensitivity, "Draft")
            return
        z = (curr_val - mean) / std
        if abs(z) >= sensitivity:
            sig_type = "Positive Deviation" if z > 0 else "Negative Deviation"
            strength = "strong" if abs(z) >= 3.0 else "moderate"
        else:
            sig_type = "No Signal"
            strength = "none"
        self._add_signal(hosp, dept, kpi, curr_date, "z_score", sig_type, z, "positive" if z > 0 else "negative" if z < 0 else "none", strength, "Calculated", obs_used, history_window, "Complete", "Medium", sensitivity, "Draft")

    def _calc_mad(self, hosp, dept, kpi, calc_sub, i, curr_val, curr_date, curr_rec_id, vals, dates, record_ids):
        history_window = 30
        min_obs = 8
        sensitivity = 3.5
        start_idx = max(0, i - history_window)
        hist_vals = vals[start_idx:i]
        obs_used = len(hist_vals)
        if obs_used < min_obs:
            return
        med = float(np.median(hist_vals))
        mad = float(np.median(np.abs(hist_vals - med)))
        if mad == 0:
            self._add_signal(hosp, dept, kpi, curr_date, "mad_signal", "Zero MAD", 0.0, "none", "none", "Zero MAD", obs_used, history_window, "Complete", "Low", sensitivity, "Draft")
            return
        modified_z = 0.6745 * (curr_val - med) / mad
        if abs(modified_z) >= sensitivity:
            sig_type = "Positive Deviation" if modified_z > 0 else "Negative Deviation"
            strength = "strong" if abs(modified_z) >= 4.5 else "moderate"
        else:
            sig_type = "No Signal"
            strength = "none"
        self._add_signal(hosp, dept, kpi, curr_date, "mad_signal", sig_type, modified_z, "positive" if modified_z > 0 else "negative" if modified_z < 0 else "none", strength, "Calculated", obs_used, history_window, "Complete", "Medium", sensitivity, "Draft")

    def _calc_slope(self, hosp, dept, kpi, calc_sub, i, curr_val, curr_date, curr_rec_id, vals, dates, record_ids):
        history_window = 30
        min_obs = 5
        start_idx = max(0, i - history_window)
        hist_vals = vals[start_idx:i]
        obs_used = len(hist_vals)
        if obs_used < min_obs:
            return
        x = np.arange(obs_used)
        y = hist_vals
        if len(x) < 2:
            return
        slope, intercept = np.polyfit(x, y, 1)
        if slope > 1e-9:
            sig_type = "Sustained Increase"
        elif slope < -1e-9:
            sig_type = "Sustained Decrease"
        else:
            sig_type = "No Signal"
        strength = "moderate" if abs(slope) > 0.01 else "weak"
        self._add_signal(hosp, dept, kpi, curr_date, "trend_slope", sig_type, slope, "both", strength, "Calculated", obs_used, history_window, "Complete", "Medium", None, "Draft")

    def _calc_volatility(self, hosp, dept, kpi, calc_sub, i, curr_val, curr_date, curr_rec_id, vals, dates, record_ids):
        history_window = 30
        min_obs = 8
        start_idx = max(0, i - history_window)
        hist_vals = vals[start_idx:i]
        obs_used = len(hist_vals)
        if obs_used < min_obs:
            return
        std = float(np.std(hist_vals, ddof=0))
        # Compare with previous window
        prev_start = max(0, i - 2 * history_window)
        prev_vals = vals[prev_start:i - history_window]
        if len(prev_vals) >= min_obs:
            prev_std = float(np.std(prev_vals, ddof=0))
            if prev_std > 0:
                change_ratio = (std - prev_std) / prev_std
                if change_ratio > 0.2:
                    sig_type = "Volatility Increase"
                    strength = "moderate" if change_ratio > 0.5 else "weak"
                else:
                    sig_type = "No Signal"
                    strength = "none"
                self._add_signal(hosp, dept, kpi, curr_date, "volatility_change", sig_type, std, "both", strength, "Calculated", obs_used, history_window, "Complete", "Medium", None, "Draft")
            else:
                self._add_signal(hosp, dept, kpi, curr_date, "volatility_change", "No Signal", std, "none", "none", "Calculated", obs_used, history_window, "Complete", "Medium", None, "Draft")
        else:
            self._add_signal(hosp, dept, kpi, curr_date, "volatility_change", "Insufficient History", std, "none", "none", "Insufficient History", obs_used, history_window, "Insufficient", "Low", None, "Draft")

    def _add_signal(self, hosp, dept, kpi, curr_date, method, sig_type, sig_val, direction, strength, status, obs_used, hist_window, hist_status, trend_conf, sensitivity, sens_status):
        rec_id = f"TSIG-{kpi}-{hosp}-{dept}-{str(curr_date).replace('-', '')}-{method}"
        self.signals.append(StatisticalSignalResult(
            signal_record_id=rec_id,
            hospital_id=hosp,
            department_id=dept,
            reporting_date=curr_date,
            kpi_id=kpi,
            signal_method=method,
            signal_type=sig_type,
            signal_value=sig_val,
            signal_direction=direction,
            signal_strength=strength,
            signal_status=status,
            interpretation_status="Provisional",
            observations_used=obs_used,
            history_window=hist_window,
            history_status=hist_status,
            coverage_percentage=(obs_used / hist_window) * 100 if hist_window > 0 else None,
            trend_confidence_level=trend_conf,
            sensitivity_value=sensitivity,
            sensitivity_approval_status=sens_status,
            configuration_version="v1.0-draft",
            trend_run_id=self.trend_run_id,
            calculated_at=datetime.now(),
        ))

    # -----------------------------------------------------------------------
    # 6. Sustained movement
    # -----------------------------------------------------------------------

    def detect_sustained_movements(self, df: pd.DataFrame) -> None:
        series_map = self.prepare_time_series(df)
        for (hosp, dept, kpi), sub in series_map.items():
            calc_sub = sub[sub["calculation_status"] == "Calculated"].copy()
            if calc_sub.empty:
                continue
            calc_sub = calc_sub.sort_values("reporting_date").reset_index(drop=True)
            vals = calc_sub["kpi_value"].astype(float).values
            dates = calc_sub["reporting_date"].values
            n = len(vals)
            if n < 3:
                continue
            # Detect sequences
            seq_start = 0
            for i in range(1, n):
                prev_dir = 1 if vals[i] > vals[i-1] else (-1 if vals[i] < vals[i-1] else 0)
                curr_dir = 1 if vals[i] > vals[i-1] else (-1 if vals[i] < vals[i-1] else 0)
                if i == 1:
                    current_dir = curr_dir
                if curr_dir == 0 or curr_dir != current_dir:
                    # End sequence
                    length = i - seq_start
                    if length >= 3 and current_dir != 0:
                        self._record_movement(hosp, dept, kpi, dates, vals, seq_start, i - 1, current_dir)
                    seq_start = i - 1
                    current_dir = curr_dir
            # Final sequence
            length = n - seq_start
            if length >= 3 and current_dir != 0:
                self._record_movement(hosp, dept, kpi, dates, vals, seq_start, n - 1, current_dir)
        self._add_audit("sustained_movement", "Success", details=f"Generated {len(self.sustained_movements)} sustained movements")

    def _record_movement(self, hosp, dept, kpi, dates, vals, start_idx, end_idx, direction):
        start_val = float(vals[start_idx])
        end_val = float(vals[end_idx])
        cum_abs = end_val - start_val
        cum_pct = (cum_abs / abs(start_val)) * 100 if start_val != 0 else None
        mov_type = "Sustained Increase" if direction > 0 else "Sustained Decrease"
        rec_id = f"TMOV-{kpi}-{hosp}-{dept}-{str(dates[start_idx]).replace('-', '')}-{str(dates[end_idx]).replace('-', '')}"
        self.sustained_movements.append(SustainedMovementResult(
            movement_record_id=rec_id,
            hospital_id=hosp,
            department_id=dept,
            kpi_id=kpi,
            movement_type=mov_type,
            sequence_start_date=dates[start_idx],
            sequence_end_date=dates[end_idx],
            consecutive_observation_count=end_idx - start_idx + 1,
            starting_value=start_val,
            ending_value=end_val,
            cumulative_absolute_change=cum_abs,
            cumulative_percentage_change=cum_pct,
            calculation_status="Calculated",
            interpretation_status="Provisional",
            trend_confidence_level="Medium",
            trend_run_id=self.trend_run_id,
            calculated_at=datetime.now(),
        ))

    # -----------------------------------------------------------------------
    # 7. Run all
    # -----------------------------------------------------------------------

    def run_all(self, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        if df is None:
            df = self.load_accepted_input()
        if df is None:
            return {"status": "Failed", "reason": "Cannot load input"}
        if not self.validate_phase_2a_acceptance():
            return {"status": "Failed", "reason": "Phase 2A acceptance not validated"}
        if not self.validate_kpi_set(df):
            return {"status": "Failed", "reason": "KPI validation failed"}

        self.build_period_comparisons(df)
        self.calculate_rolling_statistics(df)
        self.generate_signal_candidates(df)
        self.detect_sustained_movements(df)

        return {
            "status": "Success",
            "trend_run_id": self.trend_run_id,
            "period_comparisons": len(self.period_comparisons),
            "rolling_statistics": len(self.rolling_statistics),
            "signals": len(self.signals),
            "sustained_movements": len(self.sustained_movements),
            "issues": len(self.issues),
            "audit": len(self.audit),
            "evidence": len(self.evidence),
            "lineage": len(self.lineage),
        }

    # -----------------------------------------------------------------------
    # 8. Export helpers
    # -----------------------------------------------------------------------

    def to_dataframes(self) -> Dict[str, pd.DataFrame]:
        return {
            "period_comparisons": pd.DataFrame([r.to_dict() for r in self.period_comparisons]) if self.period_comparisons else pd.DataFrame(columns=["comparison_record_id"]),
            "rolling_statistics": pd.DataFrame([r.to_dict() for r in self.rolling_statistics]) if self.rolling_statistics else pd.DataFrame(columns=["rolling_record_id"]),
            "signals": pd.DataFrame([r.to_dict() for r in self.signals]) if self.signals else pd.DataFrame(columns=["signal_record_id"]),
            "sustained_movements": pd.DataFrame([r.to_dict() for r in self.sustained_movements]) if self.sustained_movements else pd.DataFrame(columns=["movement_record_id"]),
            "evidence": pd.DataFrame([r.to_dict() for r in self.evidence]) if self.evidence else pd.DataFrame(columns=["trend_evidence_id"]),
            "lineage": pd.DataFrame([r.to_dict() for r in self.lineage]) if self.lineage else pd.DataFrame(columns=["trend_lineage_id"]),
            "issues": pd.DataFrame([r.to_dict() for r in self.issues]) if self.issues else pd.DataFrame(columns=["trend_issue_id"]),
            "audit": pd.DataFrame([r.to_dict() for r in self.audit]) if self.audit else pd.DataFrame(columns=["audit_id"]),
        }
