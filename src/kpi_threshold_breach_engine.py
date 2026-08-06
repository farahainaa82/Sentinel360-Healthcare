"""
Sentinel360 Healthcare — Step 2B-2 Threshold Classification and Breach Engine
"""

import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from threshold_breach_models import (
    BreachEventResult,
    BreachType,
    IssueCategory,
    IssueSeverity,
    OperationalUseStatus,
    ReviewDueStatus,
    ThresholdClassificationResult,
    ThresholdState,
    WatchIssueResult,
)


class KPIThresholdBreachEngine:
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.engine_run_id = f"THBREACH-{uuid.uuid4().hex[:16].upper()}"
        self.processed_at = datetime.now().isoformat()
        self.classifications: List[ThresholdClassificationResult] = []
        self.breaches: List[BreachEventResult] = []
        self.issues: List[WatchIssueResult] = []
        self.df_daily: Optional[pd.DataFrame] = None
        self.df_thresholds: Optional[pd.DataFrame] = None
        self.df_breach_rules: Optional[pd.DataFrame] = None

    def _generate_id(self, prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4().hex[:16].upper()}"

    def load_inputs(self) -> None:
        daily_path = self.project_root / "data" / "analytical" / "analytical_six_kpi_daily.csv"
        self.df_daily = pd.read_csv(daily_path)
        self.df_daily["kpi_value"] = pd.to_numeric(self.df_daily["kpi_value"], errors="coerce")
        self.df_daily["reporting_date"] = pd.to_datetime(self.df_daily["reporting_date"]).dt.strftime("%Y-%m-%d")

        thresh_path = self.project_root / "config" / "kpi_threshold_config.csv"
        self.df_thresholds = pd.read_csv(thresh_path)

        rules_path = self.project_root / "config" / "threshold_breach_rule_config.csv"
        self.df_breach_rules = pd.read_csv(rules_path)

    def validate_prerequisites(self) -> Tuple[bool, List[str]]:
        issues: List[str] = []
        if self.df_daily is None or self.df_daily.empty:
            issues.append("Daily KPI data missing.")
        if self.df_thresholds is None or self.df_thresholds.empty:
            issues.append("Active threshold config missing.")
        if self.df_breach_rules is None or self.df_breach_rules.empty:
            issues.append("Breach rule config missing.")
        if self.df_thresholds is not None:
            missing = set(self.df_daily["kpi_id"].unique()) - set(self.df_thresholds["kpi_id"].unique())
            if missing:
                issues.append(f"Missing active thresholds for: {missing}")
        return len(issues) == 0, issues

    def _classify_vectorised(self, values: np.ndarray, row: pd.Series) -> np.ndarray:
        direction = row["directionality"]
        statuses = np.full(len(values), ThresholdState.NOT_ASSESSED.value, dtype=object)

        if direction == "Higher is better":
            lr = row.get("lower_red_boundary")
            gl = row.get("green_lower_boundary")
            gu = row.get("green_upper_boundary")
            if pd.notna(lr) and pd.notna(gl) and pd.notna(gu):
                statuses = np.where(values < lr, ThresholdState.RED.value, statuses)
                statuses = np.where((values >= lr) & (values < gl), ThresholdState.AMBER.value, statuses)
                statuses = np.where(values >= gl, ThresholdState.GREEN.value, statuses)

        elif direction == "Lower is better":
            gl = row.get("green_lower_boundary")
            gu = row.get("green_upper_boundary")
            ur = row.get("upper_red_boundary")
            if pd.notna(gl) and pd.notna(gu) and pd.notna(ur):
                statuses = np.where(values <= gu, ThresholdState.GREEN.value, statuses)
                statuses = np.where((values > gu) & (values < ur), ThresholdState.AMBER.value, statuses)
                statuses = np.where(values >= ur, ThresholdState.RED.value, statuses)

        elif direction == "Context-sensitive":
            lr = row.get("lower_red_boundary")
            gl = row.get("green_lower_boundary")
            gu = row.get("green_upper_boundary")
            ur = row.get("upper_red_boundary")
            if pd.notna(lr) and pd.notna(gl) and pd.notna(gu) and pd.notna(ur):
                statuses = np.where(values < lr, ThresholdState.LOW_UTILISATION.value, statuses)
                statuses = np.where((values >= lr) & (values < gl), ThresholdState.LOWER_AMBER.value, statuses)
                statuses = np.where((values >= gl) & (values <= gu), ThresholdState.NORMAL_OPERATING_BAND.value, statuses)
                statuses = np.where((values > gu) & (values < ur), ThresholdState.UPPER_AMBER.value, statuses)
                statuses = np.where(values >= ur, ThresholdState.CRITICAL_CAPACITY_PRESSURE.value, statuses)

        return statuses

    def classify_all_records(self) -> pd.DataFrame:
        if self.df_daily is None or self.df_thresholds is None:
            raise ValueError("Inputs not loaded.")

        df = self.df_daily.copy()
        df = df.merge(self.df_thresholds, on="kpi_id", how="left", suffixes=("", "_thresh"))

        # Handle missing thresholds
        missing_thresh = df["directionality"].isna()
        if missing_thresh.any():
            for _, row in df[missing_thresh].iterrows():
                self.issues.append(WatchIssueResult(
                    issue_record_id=self._generate_id("ISS"),
                    hospital_id=row["hospital_id"],
                    department_id=row["department_id"],
                    reporting_date=row["reporting_date"],
                    kpi_id=row["kpi_id"],
                    issue_category=IssueCategory.MISSING_ACTIVE_THRESHOLD.value,
                    issue_severity=IssueSeverity.BLOCKING.value,
                    issue_description=f"No active threshold for {row['kpi_id']}",
                    engine_run_id=self.engine_run_id,
                    processed_at=self.processed_at,
                ))

        # Classify calculated records
        calc_mask = df["calculation_status"] == "Calculated"
        unavail_mask = df["calculation_status"] != "Calculated"

        # Initialize all as Unavailable or Not Assessed
        df["threshold_state"] = ThresholdState.UNAVAILABLE.value
        df.loc[calc_mask & df["kpi_value"].isna(), "threshold_state"] = ThresholdState.NOT_ASSESSED.value

        # Vectorised classification per KPI
        for _, thresh in self.df_thresholds.iterrows():
            kpi_id = thresh["kpi_id"]
            sub_mask = calc_mask & (df["kpi_id"] == kpi_id) & df["kpi_value"].notna()
            if sub_mask.any():
                values = df.loc[sub_mask, "kpi_value"].values
                states = self._classify_vectorised(values, thresh)
                df.loc[sub_mask, "threshold_state"] = states

        # Preserve threshold metadata
        meta_cols = [
            "threshold_version", "approval_status", "threshold_is_provisional",
            "lower_red_boundary", "lower_amber_boundary", "green_lower_boundary",
            "green_upper_boundary", "upper_amber_boundary", "upper_red_boundary",
            "boundary_inclusivity_rule", "decision_record_id", "effective_date",
            "required_review_date", "unit_thresh",
        ]
        for col in meta_cols:
            if col in df.columns:
                df[col] = df[col].fillna("") if col not in ("threshold_is_provisional",) else df[col].fillna(False)

        # Review due status
        current_date = datetime(2026, 7, 27).date()
        df["review_due_status"] = ReviewDueStatus.NOT_APPLICABLE.value
        for idx, row in df.iterrows():
            review_date = row.get("required_review_date")
            if pd.notna(review_date) and review_date != "":
                try:
                    rd = datetime.strptime(str(review_date), "%Y-%m-%d").date()
                    days_until = (rd - current_date).days
                    if days_until < 0:
                        df.at[idx, "review_due_status"] = ReviewDueStatus.OVERDUE.value
                    elif days_until <= 30:
                        df.at[idx, "review_due_status"] = ReviewDueStatus.DUE_SOON.value
                    else:
                        df.at[idx, "review_due_status"] = ReviewDueStatus.NOT_YET_DUE.value
                except (ValueError, TypeError):
                    pass

        # Operational use status
        df["operational_use_status"] = OperationalUseStatus.FULLY_OPERATIONAL.value
        df.loc[df["threshold_is_provisional"] == True, "operational_use_status"] = OperationalUseStatus.PROTOTYPE_USE_WITH_CONDITIONS.value

        # Build classification results
        for _, row in df.iterrows():
            self.classifications.append(ThresholdClassificationResult(
                classification_record_id=self._generate_id("CLS"),
                integration_record_id=str(row.get("integration_record_id", "")),
                hospital_id=str(row.get("hospital_id", "")),
                department_id=str(row.get("department_id", "")),
                reporting_date=str(row.get("reporting_date", "")),
                kpi_id=str(row.get("kpi_id", "")),
                kpi_name=str(row.get("kpi_name", "")),
                kpi_value=row.get("kpi_value") if pd.notna(row.get("kpi_value")) else None,
                kpi_unit=str(row.get("unit", row.get("unit_thresh", ""))),
                calculation_status=str(row.get("calculation_status", "")),
                threshold_state=str(row.get("threshold_state", "")),
                threshold_version=str(row.get("threshold_version", "")),
                threshold_source="config/kpi_threshold_config.csv",
                approval_status=str(row.get("approval_status", "")),
                threshold_is_provisional=bool(row.get("threshold_is_provisional", False)),
                lower_red_boundary=row.get("lower_red_boundary") if pd.notna(row.get("lower_red_boundary")) else None,
                lower_amber_boundary=row.get("lower_amber_boundary") if pd.notna(row.get("lower_amber_boundary")) else None,
                green_lower_boundary=row.get("green_lower_boundary") if pd.notna(row.get("green_lower_boundary")) else None,
                green_upper_boundary=row.get("green_upper_boundary") if pd.notna(row.get("green_upper_boundary")) else None,
                upper_amber_boundary=row.get("upper_amber_boundary") if pd.notna(row.get("upper_amber_boundary")) else None,
                upper_red_boundary=row.get("upper_red_boundary") if pd.notna(row.get("upper_red_boundary")) else None,
                boundary_inclusivity_rule=str(row.get("boundary_inclusivity_rule", "")),
                decision_record_id=str(row.get("decision_record_id", "")),
                effective_date=str(row.get("effective_date", "")),
                required_review_date=str(row.get("required_review_date", "")) if pd.notna(row.get("required_review_date")) else None,
                engine_run_id=self.engine_run_id,
                processed_at=self.processed_at,
            ))

        return df

    def detect_breaches(self, df_classified: pd.DataFrame) -> pd.DataFrame:
        df = df_classified.copy()

        # Map threshold state to breach type
        def _map_breach(state: str, is_provisional: bool) -> Tuple[str, bool]:
            if state == ThresholdState.UNAVAILABLE.value:
                return BreachType.UNAVAILABLE.value, False
            if state == ThresholdState.NOT_ASSESSED.value:
                return BreachType.NOT_ASSESSED.value, False
            if state in (ThresholdState.AMBER.value, ThresholdState.LOWER_AMBER.value, ThresholdState.UPPER_AMBER.value):
                bt = BreachType.AMBER_CONDITION.value
                return bt, True
            if state == ThresholdState.RED.value:
                bt = BreachType.RED_BREACH.value
                return bt, True
            if state == ThresholdState.CRITICAL_CAPACITY_PRESSURE.value:
                bt = BreachType.CRITICAL_CAPACITY_BREACH.value
                return bt, True
            if state == ThresholdState.LOW_UTILISATION.value:
                bt = BreachType.LOW_UTILISATION_CONDITION.value
                return bt, True
            return BreachType.NO_BREACH.value, False

        breach_info = df.apply(lambda r: _map_breach(r["threshold_state"], r.get("threshold_is_provisional", False)), axis=1)
        df["breach_type"] = [b[0] for b in breach_info]
        df["breach_flag"] = [b[1] for b in breach_info]

        # Provisional breach marker: only override if there is an actual breach
        prov_mask = df["threshold_is_provisional"] == True
        df.loc[prov_mask & df["breach_flag"], "breach_type"] = BreachType.PROVISIONAL_BREACH.value

        # Ensure non-provisional records with actual breaches keep their specific breach type
        non_prov_mask = df["threshold_is_provisional"] != True
        for state, btype in [
            (ThresholdState.AMBER.value, BreachType.AMBER_CONDITION.value),
            (ThresholdState.LOWER_AMBER.value, BreachType.AMBER_CONDITION.value),
            (ThresholdState.UPPER_AMBER.value, BreachType.AMBER_CONDITION.value),
            (ThresholdState.RED.value, BreachType.RED_BREACH.value),
            (ThresholdState.CRITICAL_CAPACITY_PRESSURE.value, BreachType.CRITICAL_CAPACITY_BREACH.value),
            (ThresholdState.LOW_UTILISATION.value, BreachType.LOW_UTILISATION_CONDITION.value),
        ]:
            df.loc[non_prov_mask & (df["threshold_state"] == state), "breach_type"] = btype

        # Build breach results
        for _, row in df.iterrows():
            self.breaches.append(BreachEventResult(
                breach_record_id=self._generate_id("BRH"),
                classification_record_id="",  # linked later
                integration_record_id=str(row.get("integration_record_id", "")),
                hospital_id=str(row.get("hospital_id", "")),
                department_id=str(row.get("department_id", "")),
                reporting_date=str(row.get("reporting_date", "")),
                kpi_id=str(row.get("kpi_id", "")),
                kpi_name=str(row.get("kpi_name", "")),
                kpi_value=row.get("kpi_value") if pd.notna(row.get("kpi_value")) else None,
                threshold_state=str(row.get("threshold_state", "")),
                breach_type=str(row.get("breach_type", "")),
                breach_flag=bool(row.get("breach_flag", False)),
                threshold_version=str(row.get("threshold_version", "")),
                approval_status=str(row.get("approval_status", "")),
                threshold_is_provisional=bool(row.get("threshold_is_provisional", False)),
                operational_use_status=str(row.get("operational_use_status", "")),
                governance_warning="" if not bool(row.get("threshold_is_provisional", False)) else "Provisional threshold in use.",
                engine_run_id=self.engine_run_id,
                processed_at=self.processed_at,
            ))

        return df

    def to_classification_dataframe(self) -> pd.DataFrame:
        if not self.classifications:
            return pd.DataFrame()
        rows = []
        for c in self.classifications:
            rows.append({
                "classification_record_id": c.classification_record_id,
                "integration_record_id": c.integration_record_id,
                "hospital_id": c.hospital_id,
                "department_id": c.department_id,
                "reporting_date": c.reporting_date,
                "kpi_id": c.kpi_id,
                "kpi_name": c.kpi_name,
                "kpi_value": c.kpi_value,
                "kpi_unit": c.kpi_unit,
                "calculation_status": c.calculation_status,
                "threshold_state": c.threshold_state,
                "threshold_version": c.threshold_version,
                "threshold_source": c.threshold_source,
                "approval_status": c.approval_status,
                "threshold_is_provisional": c.threshold_is_provisional,
                "lower_red_boundary": c.lower_red_boundary,
                "lower_amber_boundary": c.lower_amber_boundary,
                "green_lower_boundary": c.green_lower_boundary,
                "green_upper_boundary": c.green_upper_boundary,
                "upper_amber_boundary": c.upper_amber_boundary,
                "upper_red_boundary": c.upper_red_boundary,
                "boundary_inclusivity_rule": c.boundary_inclusivity_rule,
                "decision_record_id": c.decision_record_id,
                "effective_date": c.effective_date,
                "required_review_date": c.required_review_date,
                "review_due_status": "",  # populated in classify_all_records
                "operational_use_status": "",
                "engine_run_id": c.engine_run_id,
                "processed_at": c.processed_at,
            })
        return pd.DataFrame(rows)

    def to_breach_dataframe(self) -> pd.DataFrame:
        if not self.breaches:
            return pd.DataFrame()
        rows = []
        for b in self.breaches:
            rows.append({
                "breach_record_id": b.breach_record_id,
                "integration_record_id": b.integration_record_id,
                "hospital_id": b.hospital_id,
                "department_id": b.department_id,
                "reporting_date": b.reporting_date,
                "kpi_id": b.kpi_id,
                "kpi_name": b.kpi_name,
                "kpi_value": b.kpi_value,
                "threshold_state": b.threshold_state,
                "breach_type": b.breach_type,
                "breach_flag": b.breach_flag,
                "threshold_version": b.threshold_version,
                "approval_status": b.approval_status,
                "threshold_is_provisional": b.threshold_is_provisional,
                "operational_use_status": b.operational_use_status,
                "governance_warning": b.governance_warning,
                "engine_run_id": b.engine_run_id,
                "processed_at": b.processed_at,
            })
        return pd.DataFrame(rows)

    def to_issue_dataframe(self) -> pd.DataFrame:
        if not self.issues:
            return pd.DataFrame()
        rows = []
        for i in self.issues:
            rows.append({
                "issue_record_id": i.issue_record_id,
                "hospital_id": i.hospital_id,
                "department_id": i.department_id,
                "reporting_date": i.reporting_date,
                "kpi_id": i.kpi_id,
                "issue_category": i.issue_category,
                "issue_severity": i.issue_severity,
                "issue_description": i.issue_description,
                "engine_run_id": i.engine_run_id,
                "processed_at": i.processed_at,
            })
        return pd.DataFrame(rows)
