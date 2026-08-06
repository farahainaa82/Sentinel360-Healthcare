"""
Sentinel360 Healthcare — Analytical Configuration Loader

Loads and validates analytical layer configuration files.
No actual KPI calculation is performed in Step 2A-1.

Step: 2A-1
"""

import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from analytical_models import AnalyticalIssue, ConfigurationProvenance


# ---------------------------------------------------------------------------
# 1. Approved KPI Names
# ---------------------------------------------------------------------------

APPROVED_KPI_NAMES = {
    "Staffing Level",
    "Staff Absenteeism Rate",
    "Bed Occupancy Rate",
    "Average Patient Waiting Time",
    "Patient Complaint Rate",
    "Patient Satisfaction Score",
}


# ---------------------------------------------------------------------------
# 2. Valid Units
# ---------------------------------------------------------------------------

VALID_UNITS = {
    "percentage",
    "ratio",
    "count",
    "minutes",
    "hours",
    "days",
    "score",
    "index",
    "rate_per_1000",
}


# ---------------------------------------------------------------------------
# 3. Valid Directionality
# ---------------------------------------------------------------------------

VALID_DIRECTIONALITY = {
    "higher_is_better",
    "lower_is_better",
    "neutral",
}


# ---------------------------------------------------------------------------
# 4. Valid Grains
# ---------------------------------------------------------------------------

VALID_GRAINS = {
    "hospital-department-date",
    "hospital-department-month",
    "hospital-date",
    "hospital-month",
    "department-date",
    "department-month",
    "date",
    "month",
}


# ---------------------------------------------------------------------------
# 5. Configuration Loader
# ---------------------------------------------------------------------------

class AnalyticalConfigLoader:
    """Loads and validates analytical configuration files."""

    def __init__(self, config_dir: Path):
        self.config_dir = Path(config_dir)
        self.issues: List[AnalyticalIssue] = []
        self.provenance: List[ConfigurationProvenance] = []
        self.kpi_definitions: Optional[pd.DataFrame] = None
        self.kpi_thresholds: Optional[pd.DataFrame] = None
        self.data_confidence: Optional[pd.DataFrame] = None

    # -- Loading -----------------------------------------------------------

    def load_kpi_definitions(self) -> pd.DataFrame:
        path = self.config_dir / "kpi_definition_config.csv"
        if not path.exists():
            self._add_issue("Error", "KPI definition config missing", str(path))
            return pd.DataFrame()
        df = pd.read_csv(path)
        self.kpi_definitions = df
        self._record_provenance(path, df)
        return df

    def load_kpi_thresholds(self) -> pd.DataFrame:
        path = self.config_dir / "kpi_threshold_config.csv"
        if not path.exists():
            self._add_issue("Error", "KPI threshold config missing", str(path))
            return pd.DataFrame()
        df = pd.read_csv(path)
        self.kpi_thresholds = df
        self._record_provenance(path, df)
        return df

    def load_data_confidence_rules(self) -> pd.DataFrame:
        path = self.config_dir / "data_confidence_config.csv"
        if not path.exists():
            self._add_issue("Error", "Data confidence config missing", str(path))
            return pd.DataFrame()
        df = pd.read_csv(path)
        self.data_confidence = df
        self._record_provenance(path, df)
        return df

    # -- Validation --------------------------------------------------------

    def validate_configuration(self) -> Dict[str, Any]:
        """Run all configuration validations and return structured results."""
        results = {
            "kpi_definitions_valid": False,
            "kpi_thresholds_valid": False,
            "data_confidence_valid": False,
            "overall_valid": False,
            "issues": [],
        }

        if self.kpi_definitions is not None and not self.kpi_definitions.empty:
            results["kpi_definitions_valid"] = self._validate_kpi_definitions()

        if self.kpi_thresholds is not None and not self.kpi_thresholds.empty:
            results["kpi_thresholds_valid"] = self._validate_kpi_thresholds()

        if self.data_confidence is not None and not self.data_confidence.empty:
            results["data_confidence_valid"] = self._validate_data_confidence()

        results["overall_valid"] = (
            results["kpi_definitions_valid"]
            and results["kpi_thresholds_valid"]
            and results["data_confidence_valid"]
        )
        results["issues"] = [i.to_dict() for i in self.issues]
        return results

    def _validate_kpi_definitions(self) -> bool:
        df = self.kpi_definitions
        if df is None or df.empty:
            return False

        required_cols = ["kpi_id", "kpi_name", "domain", "numerator_field", "denominator_field", "unit", "directionality", "grain", "effective_date", "approval_status"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            self._add_issue("Error", "KPI definition missing columns", f"{missing}")
            return False

        # Unique KPI IDs
        if df["kpi_id"].duplicated().any():
            dups = df[df["kpi_id"].duplicated(False)]["kpi_id"].unique().tolist()
            self._add_issue("Error", "Duplicate KPI IDs", f"{dups}")

        # Approved names only
        unapproved = df[~df["kpi_name"].isin(APPROVED_KPI_NAMES)]["kpi_name"].unique().tolist()
        if unapproved:
            self._add_issue("Error", "Unapproved KPI names", f"{unapproved}")

        # Valid units
        invalid_units = df[~df["unit"].isin(VALID_UNITS)]["unit"].unique().tolist()
        if invalid_units:
            self._add_issue("Error", "Invalid units", f"{invalid_units}")

        # Valid directionality
        invalid_dir = df[~df["directionality"].isin(VALID_DIRECTIONALITY)]["directionality"].unique().tolist()
        if invalid_dir:
            self._add_issue("Error", "Invalid directionality", f"{invalid_dir}")

        # Valid grain
        invalid_grain = df[~df["grain"].isin(VALID_GRAINS)]["grain"].unique().tolist()
        if invalid_grain:
            self._add_issue("Error", "Invalid grain", f"{invalid_grain}")

        # Minimum denominator validity
        if "minimum_denominator" in df.columns:
            bad_min = df[pd.to_numeric(df["minimum_denominator"], errors="coerce") < 0]["kpi_id"].tolist()
            if bad_min:
                self._add_issue("Error", "Negative minimum denominator", f"{bad_min}")

        # Approval status
        if "approval_status" in df.columns:
            unapproved_status = df[~df["approval_status"].isin(["Approved", "approved"])]["kpi_id"].tolist()
            if unapproved_status:
                self._add_issue("Warning", "Unapproved KPI definitions", f"{unapproved_status}")

        # Effective date parsing
        if "effective_date" in df.columns:
            try:
                pd.to_datetime(df["effective_date"], errors="raise")
            except Exception as e:
                self._add_issue("Error", "Invalid effective_date values", str(e))

        return not any(i.issue_type == "Error" for i in self.issues)

    def _validate_kpi_thresholds(self) -> bool:
        df = self.kpi_thresholds
        if df is None or df.empty:
            return False

        required_cols = ["kpi_id", "threshold_id", "threshold_name", "threshold_value", "threshold_direction", "severity", "effective_date"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            self._add_issue("Error", "KPI threshold config missing columns", f"{missing}")
            return False

        # Threshold ordering: for same kpi_id + threshold_direction, values should be ordered
        for (kpi_id, direction), group in df.groupby(["kpi_id", "threshold_direction"]):
            vals = pd.to_numeric(group["threshold_value"], errors="coerce").dropna().tolist()
            if len(vals) > 1 and direction in ("above", "below"):
                # For "above", higher values should have higher severity or be consistent
                # For "below", lower values should have higher severity
                # We only flag exact duplicates as conflicts
                dup_vals = group[group.duplicated(subset=["threshold_value"], keep=False)]
                if not dup_vals.empty:
                    self._add_issue("Warning", "Duplicate threshold values", f"{kpi_id} {direction}")

        # All kpi_ids in thresholds must exist in definitions
        if self.kpi_definitions is not None and not self.kpi_definitions.empty:
            unknown_kpis = set(df["kpi_id"]) - set(self.kpi_definitions["kpi_id"])
            if unknown_kpis:
                self._add_issue("Error", "Thresholds reference unknown KPIs", f"{unknown_kpis}")

        return not any(i.issue_type == "Error" for i in self.issues if i.source_dataset == "kpi_threshold_config")

    def _validate_data_confidence(self) -> bool:
        df = self.data_confidence
        if df is None or df.empty:
            return False

        required_cols = ["kpi_id", "confidence_level", "completeness_threshold", "freshness_threshold_days"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            self._add_issue("Error", "Data confidence config missing columns", f"{missing}")
            return False

        valid_levels = {"high", "medium", "low", "insufficient"}
        invalid = df[~df["confidence_level"].isin(valid_levels)]["confidence_level"].unique().tolist()
        if invalid:
            self._add_issue("Error", "Invalid confidence levels", f"{invalid}")

        return not any(i.issue_type == "Error" for i in self.issues if i.source_dataset == "data_confidence_config")

    # -- Helpers -----------------------------------------------------------

    def _add_issue(self, issue_type: str, description: str, detail: str = "") -> None:
        issue = AnalyticalIssue(
            issue_id=str(uuid.uuid4())[:8],
            issue_type=issue_type,
            severity=issue_type,
            issue_description=f"{description}: {detail}" if detail else description,
            source_dataset="",
            kpi_id="",
            field_name="",
            created_at=datetime.now(),
        )
        self.issues.append(issue)

    def _record_provenance(self, path: Path, df: pd.DataFrame) -> None:
        with open(path, "rb") as fh:
            checksum = hashlib.sha256(fh.read()).hexdigest()
        prov = ConfigurationProvenance(
            config_file=str(path.name),
            config_version="",
            loaded_at=datetime.now(),
            checksum=checksum,
            row_count=len(df),
            validated=False,
        )
        self.provenance.append(prov)

    def get_provenance(self) -> List[ConfigurationProvenance]:
        return self.provenance

    def get_issues(self) -> List[AnalyticalIssue]:
        return self.issues
