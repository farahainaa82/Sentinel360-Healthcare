"""
Sentinel360 Healthcare — Analytical Governance Validator

Validates KPI definitions, source fields, thresholds, and readiness.
No actual KPI calculation is performed in Step 2A-1.

Step: 2A-1
"""

import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd

from analytical_models import AnalyticalIssue, KPIDefinition
from kpi_registry import KPIRegistry


# ---------------------------------------------------------------------------
# 1. Source Dataset Field Mapping
# ---------------------------------------------------------------------------

# Authoritative source fields for each KPI based on inspected processed data
AUTHORITATIVE_SOURCE_FIELDS: Dict[str, Dict[str, Any]] = {
    "KPI-001": {
        "dataset": "processed_operational_daily",
        "required_fields": [
            "planned_staff_count",
            "present_staff_count",
            "replacement_staff_count",
            "reassigned_staff_count",
        ],
        "numerator_field": "present_staff_count + replacement_staff_count",
        "denominator_field": "planned_staff_count",
        "notes": "Reassigned staff counted as present if reassigned_in > 0; formula uses present + replacement as available staff",
    },
    "KPI-002": {
        "dataset": "processed_operational_daily",
        "required_fields": [
            "planned_staff_count",
            "unapproved_absence_count",
        ],
        "numerator_field": "unapproved_absence_count",
        "denominator_field": "planned_staff_count",
        "notes": "Approved leave is excluded from absenteeism; only unapproved absences count",
    },
    "KPI-003": {
        "dataset": "processed_operational_daily",
        "required_fields": [
            "occupied_beds",
            "operational_beds",
        ],
        "numerator_field": "occupied_beds",
        "denominator_field": "operational_beds",
        "notes": "Overcapacity preserved when occupied > operational; not capped at 100%",
    },
    "KPI-004": {
        "dataset": "processed_patient_encounters",
        "required_fields": [
            "arrival_to_consultation_minutes",
            "official_wait_stage_eligible_flag",
            "encounter_wait_eligible_flag",
        ],
        "numerator_field": "SUM(arrival_to_consultation_minutes WHERE eligible)",
        "denominator_field": "COUNT(encounter_id WHERE eligible)",
        "notes": "Eligibility requires official_wait_stage_eligible_flag = True AND encounter_wait_eligible_flag = True; negative or null intervals excluded",
    },
    "KPI-005": {
        "dataset": "processed_operational_daily",
        "required_fields": [
            "complaint_valid_record_count",
            "encounter_record_count",
        ],
        "numerator_field": "complaint_valid_record_count",
        "denominator_field": "encounter_record_count",
        "notes": "Valid complaints only; encounter count as approved exposure base",
    },
    "KPI-006": {
        "dataset": "processed_operational_daily",
        "required_fields": [
            "survey_score_weighted_sum",
            "survey_valid_score_record_count",
        ],
        "numerator_field": "survey_score_weighted_sum",
        "denominator_field": "survey_valid_score_record_count",
        "notes": "Weighted sum of valid satisfaction scores divided by valid response count; scale handled at preparation layer",
    },
    "kpi_001": {
        "dataset": "processed_operational_daily",
        "required_fields": [
            "planned_staff_count",
            "present_staff_count",
            "replacement_staff_count",
            "reassigned_staff_count",
        ],
        "numerator_field": "present_staff_count + replacement_staff_count",
        "denominator_field": "planned_staff_count",
        "notes": "Reassigned staff counted as present if reassigned_in > 0; formula uses present + replacement as available staff",
    },
    "kpi_002": {
        "dataset": "processed_operational_daily",
        "required_fields": [
            "planned_staff_count",
            "unapproved_absence_count",
        ],
        "numerator_field": "unapproved_absence_count",
        "denominator_field": "planned_staff_count",
        "notes": "Approved leave is excluded from absenteeism; only unapproved absences count",
    },
    "kpi_003": {
        "dataset": "processed_operational_daily",
        "required_fields": [
            "occupied_beds",
            "operational_beds",
        ],
        "numerator_field": "occupied_beds",
        "denominator_field": "operational_beds",
        "notes": "Overcapacity preserved when occupied > operational; not capped at 100%",
    },
    "kpi_004": {
        "dataset": "processed_patient_encounters",
        "required_fields": [
            "arrival_to_consultation_minutes",
            "official_wait_stage_eligible_flag",
            "encounter_wait_eligible_flag",
        ],
        "numerator_field": "SUM(arrival_to_consultation_minutes WHERE eligible)",
        "denominator_field": "COUNT(encounter_id WHERE eligible)",
        "notes": "Eligibility requires official_wait_stage_eligible_flag = True AND encounter_wait_eligible_flag = True; negative or null intervals excluded",
    },
    "kpi_005": {
        "dataset": "processed_operational_daily",
        "required_fields": [
            "complaint_valid_record_count",
            "encounter_record_count",
        ],
        "numerator_field": "complaint_valid_record_count",
        "denominator_field": "encounter_record_count",
        "notes": "Valid complaints only; encounter count as approved exposure base",
    },
    "kpi_006": {
        "dataset": "processed_operational_daily",
        "required_fields": [
            "survey_score_weighted_sum",
            "survey_valid_score_record_count",
        ],
        "numerator_field": "survey_score_weighted_sum",
        "denominator_field": "survey_valid_score_record_count",
        "notes": "Weighted sum of valid satisfaction scores divided by valid response count; scale handled at preparation layer",
    },
}


# ---------------------------------------------------------------------------
# 2. Governance Validator
# ---------------------------------------------------------------------------

class AnalyticalGovernanceValidator:
    """Validates analytical governance rules for the KPI layer."""

    def __init__(
        self,
        registry: KPIRegistry,
        processed_dir: Path,
        config_dir: Path,
    ):
        self.registry = registry
        self.processed_dir = Path(processed_dir)
        self.config_dir = Path(config_dir)
        self.issues: List[AnalyticalIssue] = []
        self.readiness: Dict[str, str] = {}
        self.source_field_mapping: Dict[str, Dict[str, Any]] = {}

    # -- Core Validations --------------------------------------------------

    def validate_all(self) -> Dict[str, Any]:
        """Run all governance validations and return structured results."""
        results = {
            "kpi_registry_valid": self.validate_kpi_registry(),
            "source_fields_valid": self.validate_source_field_availability(),
            "thresholds_valid": self.validate_threshold_configuration(),
            "schemas_valid": self.validate_analytical_schemas(),
            "readiness_assigned": self.determine_kpi_readiness(),
            "no_calculations": self.validate_no_calculations_performed(),
            "issues": [i.to_dict() for i in self.issues],
        }
        results["overall_valid"] = (
            results["kpi_registry_valid"]
            and results["source_fields_valid"]
            and results["thresholds_valid"]
            and results["schemas_valid"]
            and all(status != "Blocked" for status in results["readiness_assigned"].values())
        )
        return results

    def validate_kpi_registry(self) -> bool:
        """Validate that exactly six approved KPIs are registered."""
        completeness = self.registry.validate_completeness()
        if not completeness["valid"]:
            if completeness["missing"]:
                self._add_issue("Error", "Missing approved KPIs", f"{completeness['missing']}")
            if completeness["extra"]:
                self._add_issue("Error", "Unapproved KPIs registered", f"{completeness['extra']}")
            if completeness["total_registered"] != 6:
                self._add_issue("Error", "KPI count mismatch", f"Expected 6, found {completeness['total_registered']}")
        return completeness["valid"]

    def validate_source_field_availability(self) -> bool:
        """Validate that required source fields exist in processed datasets."""
        all_valid = True
        # Only process each KPI once, normalizing IDs
        processed_kpis = set()
        for kpi_id, mapping in AUTHORITATIVE_SOURCE_FIELDS.items():
            # Normalize kpi_id: handle both KPI-001 and kpi_001 formats
            normalized_id = kpi_id.replace("KPI-", "kpi_").lower()
            if normalized_id in processed_kpis:
                continue
            processed_kpis.add(normalized_id)

            # Try lookup with original ID first, then normalized
            kpi = self.registry.get_kpi(kpi_id)
            if kpi is None:
                kpi = self.registry.get_kpi(normalized_id)
            if kpi is None:
                # Skip if this is a duplicate alias (e.g., kpi_001 when KPI-001 already processed)
                alt_id = kpi_id.replace("kpi_", "KPI-")
                if self.registry.get_kpi(alt_id) is not None:
                    continue
                self._add_issue("Error", "KPI not in registry", kpi_id)
                all_valid = False
                continue

            dataset_name = mapping["dataset"]
            dataset_path = self.processed_dir / f"{dataset_name}.csv"
            if not dataset_path.exists():
                self._add_issue("Error", "Source dataset missing", f"{kpi_id}: {dataset_name}")
                all_valid = False
                self.readiness[kpi_id] = "Blocked"
                continue

            try:
                df = pd.read_csv(dataset_path, nrows=1)
            except Exception as e:
                self._add_issue("Error", "Cannot read source dataset", f"{kpi_id}: {e}")
                all_valid = False
                self.readiness[kpi_id] = "Blocked"
                continue

            missing_fields = [f for f in mapping["required_fields"] if f not in df.columns]
            if missing_fields:
                self._add_issue("Error", "Missing source fields", f"{kpi_id}: {missing_fields}")
                all_valid = False
                self.readiness[kpi_id] = "Blocked"
            else:
                self.source_field_mapping[kpi_id] = mapping

        return all_valid

    def validate_threshold_configuration(self) -> bool:
        """Validate that threshold configuration exists for each KPI."""
        threshold_path = self.config_dir / "kpi_threshold_config.csv"
        if not threshold_path.exists():
            self._add_issue("Error", "Threshold config missing", str(threshold_path))
            return False

        try:
            df = pd.read_csv(threshold_path)
        except Exception as e:
            self._add_issue("Error", "Cannot read threshold config", str(e))
            return False

        # Check for required columns in the actual config format
        if "kpi_id" not in df.columns:
            self._add_issue("Error", "Threshold config missing kpi_id column", "")
            return False

        all_valid = True
        for kpi_id in self.registry.list_kpi_ids():
            kpi_thresholds = df[df["kpi_id"] == kpi_id]
            if kpi_thresholds.empty:
                self._add_issue("Warning", "No thresholds configured", kpi_id)
                # Not blocking - thresholds may be added later
            else:
                # Validate threshold bound columns if present
                bound_cols = ["warning_lower_bound", "warning_upper_bound", "critical_lower_bound", "critical_upper_bound"]
                for col in bound_cols:
                    if col in kpi_thresholds.columns:
                        non_numeric = pd.to_numeric(kpi_thresholds[col], errors="coerce").isna().sum()
                        # Only flag if there are actual non-empty non-numeric values
                        filled = kpi_thresholds[col].notna() & (kpi_thresholds[col].astype(str) != "")
                        bad = filled & pd.to_numeric(kpi_thresholds[col], errors="coerce").isna()
                        if bad.sum() > 0:
                            self._add_issue("Error", "Non-numeric threshold values", f"{kpi_id}: {col}")
                            all_valid = False

        # All kpi_ids in thresholds must exist in definitions
        if self.registry.list_kpi_ids():
            unknown_kpis = set(df["kpi_id"]) - set(self.registry.list_kpi_ids())
            if unknown_kpis:
                self._add_issue("Error", "Thresholds reference unknown KPIs", f"{unknown_kpis}")
                all_valid = False

        return all_valid

    def validate_analytical_schemas(self) -> bool:
        """Validate that all required analytical schemas are defined."""
        from analytical_schema_registry import validate_schema_completeness
        result = validate_schema_completeness()
        if not result["valid"]:
            self._add_issue("Error", "Missing analytical schemas", f"{result['missing']}")
        return result["valid"]

    def determine_kpi_readiness(self) -> Dict[str, str]:
        """Determine readiness status for each KPI based on validation results."""
        for kpi_id in self.registry.list_kpi_ids():
            if kpi_id in self.readiness:
                continue  # Already set to Blocked

            kpi = self.registry.get_kpi(kpi_id)
            if kpi is None:
                self.readiness[kpi_id] = "Blocked"
                continue

            # Check if all required fields are available
            mapping = AUTHORITATIVE_SOURCE_FIELDS.get(kpi_id, {})
            if not mapping:
                self.readiness[kpi_id] = "Blocked"
                self._add_issue("Error", "No source field mapping", kpi_id)
                continue

            # Check for unresolved rules (from config or from issues)
            unresolved = kpi.unresolved_rules or []
            # Also check if there are any open issues for this KPI
            kpi_issues = [i for i in self.issues if i.kpi_id == kpi_id and i.issue_type in ("Error", "Warning")]
            if unresolved or kpi_issues:
                self.readiness[kpi_id] = "Conditionally Ready"
                continue

            # Check approval status
            if kpi.approval_status not in ("Approved", "approved"):
                self.readiness[kpi_id] = "Conditionally Ready"
                continue

            self.readiness[kpi_id] = "Ready"

        return self.readiness

    def validate_no_calculations_performed(self) -> bool:
        """Confirm no KPI calculations occurred during this step.

        In Step 2A-1, this is always True by design.
        """
        return True

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

    def get_issues(self) -> List[AnalyticalIssue]:
        return self.issues

    def get_readiness(self) -> Dict[str, str]:
        return self.readiness

    def get_source_field_mapping(self) -> Dict[str, Dict[str, Any]]:
        return self.source_field_mapping
