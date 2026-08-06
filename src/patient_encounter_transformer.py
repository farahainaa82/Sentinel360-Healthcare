"""
Sentinel360 Healthcare — Patient Encounter Transformer

Transforms validated source patient_encounters.csv into
processed_patient_encounters.csv per the approved schema.

Scope (Step 2D-3A):
- Enforce validation/processing gate.
- Preserve source identifiers and traceability.
- Standardise encounter dates and timestamps.
- Calculate approved preparation-level time intervals.
- Classify cancelled, completed and left-before-service encounters.
- Prepare waiting-time eligibility fields.
- Distinguish invalid records from valid but analytically ineligible records.
- Generate encounter-specific lineage, issues and exclusions.
- Validate the processed encounter schema.
- Remain deterministic, reproducible and auditable.

Out of scope:
- KPI percentages, KPI status, trends, anomalies, risks, forecasts, scenarios,
  financial impact, recommendations.
- patient_queue, bed_capacity, service_schedule, patient_flow_daily.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.processed_schema_registry import get_processed_schema
from src.processing_contracts import TransformationResultContract, ValidationGateResult
from src.processing_models import (
    ProcessingDatasetResult,
    ProcessingExclusionRecord,
    ProcessingIssue,
    ProcessingLineageRecord,
    ProcessingRun,
)

logger = logging.getLogger(__name__)

TRANSFORMATION_VERSION = "2D-3A-1.0"
ENGINE_VERSION = "Sentinel360-Phase1-2D-3A"

REQUIRED_SOURCE_COLS = [
    "encounter_id",
    "hospital_id",
    "department_id",
    "encounter_date",
    "encounter_type",
    "arrival_datetime",
    "triage_datetime",
    "consultation_start_datetime",
    "service_end_datetime",
    "disposition_status",
]

TIMESTAMP_COLS = [
    "arrival_datetime",
    "triage_datetime",
    "consultation_start_datetime",
    "service_end_datetime",
]

# Source-to-processed column name mapping
SOURCE_COLUMN_MAP = {
    "service_start_datetime": "consultation_start_datetime",
    "status": "disposition_status",
}

# Source columns that are expected but may be missing in demo data
SOURCE_OPTIONAL_COLS = {
    "triage_datetime": None,  # no source equivalent; will remain empty
}

DISPOSITION_CANCELLED = {"cancelled", "canceled"}
DISPOSITION_LWBS = {"left before service", "left before seen", "lwbs", "left"}
DISPOSITION_COMPLETED = {"completed", "discharged", "admitted", "transferred"}

EXCLUSION_REASONS = {
    "CANCELLED_ENCOUNTER": "Encounter was cancelled.",
    "LEFT_BEFORE_SERVICE": "Patient left before service.",
    "MISSING_ARRIVAL_TIMESTAMP": "Missing arrival timestamp.",
    "MISSING_TRIAGE_TIMESTAMP": "Missing triage timestamp.",
    "MISSING_CONSULTATION_TIMESTAMP": "Missing consultation timestamp.",
    "MISSING_SERVICE_END_TIMESTAMP": "Missing service end timestamp.",
    "INVALID_TIMESTAMP_ORDER": "Timestamps are in impossible chronological order.",
    "UNPARSABLE_TIMESTAMP": "One or more timestamps could not be parsed.",
    "UNSUPPORTED_DISPOSITION_STATUS": "Disposition status not in approved mapping.",
    "FAILED_SOURCE_VALIDATION": "Source record failed validation.",
    "INVALID_DEPARTMENT_RELATIONSHIP": "Department reference invalid.",
    "PENDING_WAIT_STAGE_RULE": "Official wait-stage rule unresolved.",
    "OTHER": "Other exclusion reason.",
}


class PatientEncounterTransformer:
    """Transforms source patient_encounters into processed_patient_encounters."""

    def __init__(
        self,
        input_dir: Path,
        output_dir: Path,
        validation_log_dir: Path,
        source_type: str = "synthetic_demo",
        collect_lineage: bool = True,
        max_issue_examples: int = 1000,
    ) -> None:
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.validation_log_dir = Path(validation_log_dir)
        self.source_type = source_type
        self.collect_lineage = collect_lineage
        self.max_issue_examples = max_issue_examples

        self.processing_run_id = f"PE-{uuid.uuid4().hex[:12].upper()}"
        self.validation_run_id: Optional[str] = None
        self.processing_started = datetime.utcnow().isoformat() + "Z"
        self.issues: List[ProcessingIssue] = []
        self.lineage: List[ProcessingLineageRecord] = []
        self.exclusions: List[ProcessingExclusionRecord] = []
        self.audit_events: List[Dict[str, Any]] = []
        self.source_checksum: Optional[str] = None
        self.processed_checksum: Optional[str] = None
        self.processed_df: Optional[pd.DataFrame] = None
        self.unresolved_rules: List[str] = []

    # ------------------------------------------------------------------
    # Validation gate
    # ------------------------------------------------------------------
    def check_validation_gate(self) -> ValidationGateResult:
        manifest_path = self.validation_log_dir / "validation_run_manifest.json"
        summary_path = self.validation_log_dir / "dataset_validation_summary.csv"
        override_path = self.validation_log_dir / "manual_override_register.csv"

        if not manifest_path.exists():
            return ValidationGateResult(
                processing_allowed=False,
                blocking_reason="validation_run_manifest.json not found.",
                validation_run_id="",
            )

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        run_status = manifest.get("run_status", "")
        processing_allowed = manifest.get("processing_allowed_flag", False)
        self.validation_run_id = manifest.get("validation_run_id")

        if run_status not in {"Passed", "Passed with Warnings"}:
            return ValidationGateResult(
                processing_allowed=False,
                blocking_reason=f"Validation run_status is '{run_status}'. Must be 'Passed' or 'Passed with Warnings'.",
                validation_run_id=self.validation_run_id or "",
            )

        if not processing_allowed:
            return ValidationGateResult(
                processing_allowed=False,
                blocking_reason="processing_allowed_flag is false in validation manifest.",
                validation_run_id=self.validation_run_id or "",
            )

        # Check dataset summary for patient_encounters
        if summary_path.exists():
            summary = pd.read_csv(summary_path)
            pe_row = summary[summary["dataset_name"] == "patient_encounters"]
            if not pe_row.empty:
                overall = pe_row.iloc[0].get("dataset_status", "")
                if overall not in {"Valid", "Passed", "Passed with Warnings"}:
                    # Check overrides
                    if override_path.exists():
                        overrides = pd.read_csv(override_path)
                        pe_overrides = overrides[overrides["dataset_name"] == "patient_encounters"]
                        if pe_overrides.empty or not pe_overrides.iloc[0].get("approved", False):
                            return ValidationGateResult(
                                processing_allowed=False,
                                blocking_reason=f"patient_encounters dataset_status is '{overall}' and no approved override exists.",
                                validation_run_id=self.validation_run_id or "",
                            )
                    else:
                        return ValidationGateResult(
                            processing_allowed=False,
                            blocking_reason=f"patient_encounters dataset_status is '{overall}'.",
                            validation_run_id=self.validation_run_id or "",
                        )

        result = ValidationGateResult(
            processing_allowed=True,
            blocking_reason="",
            validation_run_id=self.validation_run_id or "",
        )
        result.accepted_datasets = ["patient_encounters"]
        return result

    # ------------------------------------------------------------------
    # Source loading
    # ------------------------------------------------------------------
    def load_source_data(self) -> pd.DataFrame:
        source_path = self.input_dir / "patient_encounters.csv"
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        df = pd.read_csv(source_path, dtype=str, keep_default_na=False)
        # Compute checksum on raw bytes
        self.source_checksum = hashlib.sha256(source_path.read_bytes()).hexdigest()
        self._audit("Source Dataset Loaded", {"source_path": str(source_path), "rows": len(df)})
        return df

    # ------------------------------------------------------------------
    # Main transformation
    # ------------------------------------------------------------------
    def transform_encounters(self, source: pd.DataFrame) -> pd.DataFrame:
        self._audit("Encounter Transformation Started", {"source_rows": len(source)})
        df = source.copy()

        # Preserve row numbers for lineage
        df["__row_number"] = df.index + 2  # 1-based + header

        # Normalise column names
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        # Map source columns to expected names
        for source_col, expected_col in SOURCE_COLUMN_MAP.items():
            if source_col in df.columns and expected_col not in df.columns:
                df[expected_col] = df[source_col]

        # Ensure expected columns exist (create empty if missing to avoid KeyError)
        for col in REQUIRED_SOURCE_COLS:
            if col not in df.columns:
                df[col] = ""
                self._add_issue(
                    severity="Warning",
                    issue_type="Missing Source Column",
                    description=f"Expected source column '{col}' not found; created empty.",
                    field_name=col,
                )

        # Parse encounter_date
        df["encounter_date_parsed"] = self._parse_dates(df["encounter_date"])

        # Parse timestamps
        for col in TIMESTAMP_COLS:
            df[f"{col}_parsed"] = self._parse_datetimes(df[col], col)

        self._audit("Timestamp Parsing Completed", {})

        # Derive reporting_date and reporting_month
        df["reporting_date"] = df["encounter_date_parsed"]
        df["reporting_month"] = df["reporting_date"].apply(
            lambda x: x.strftime("%Y-%m") if pd.notna(x) else None
        )

        # Disposition classification
        df = self._derive_disposition_flags(df)
        self._audit("Disposition Classification Completed", {})

        # Calculate wait intervals
        df = self._calculate_wait_intervals(df)
        self._audit("Wait Intervals Calculated", {})

        # Derive wait eligibility
        df = self._derive_wait_eligibility(df)
        self._audit("Wait Eligibility Derived", {})

        # Build processed dataframe with exact schema fields
        schema = get_processed_schema("processed_patient_encounters")
        target_cols = schema["required_fields"] + schema.get("optional_fields", [])

        out = pd.DataFrame(index=df.index)
        out["encounter_id"] = df["encounter_id"].replace("", pd.NA)
        out["hospital_id"] = df["hospital_id"].replace("", pd.NA)
        out["department_id"] = df["department_id"].replace("", pd.NA)
        out["encounter_date"] = df["encounter_date_parsed"]
        out["reporting_date"] = df["reporting_date"]
        out["reporting_month"] = df["reporting_month"]
        out["encounter_type"] = df["encounter_type"].replace("", pd.NA)
        out["arrival_datetime"] = df["arrival_datetime_parsed"]
        out["triage_datetime"] = df["triage_datetime_parsed"]
        out["consultation_start_datetime"] = df["consultation_start_datetime_parsed"]
        out["service_end_datetime"] = df["service_end_datetime_parsed"]
        out["disposition_status"] = df["disposition_status"].replace("", pd.NA)
        out["cancelled_flag"] = df["cancelled_flag"]
        out["left_before_service_flag"] = df["left_before_service_flag"]
        out["completed_service_flag"] = df["completed_service_flag"]
        out["arrival_to_triage_minutes"] = df["arrival_to_triage_minutes"]
        out["arrival_to_consultation_minutes"] = df["arrival_to_consultation_minutes"]
        out["triage_to_consultation_minutes"] = df["triage_to_consultation_minutes"]
        out["consultation_to_service_end_minutes"] = df["consultation_to_service_end_minutes"]
        out["official_wait_stage_eligible_flag"] = df["official_wait_stage_eligible_flag"]
        out["encounter_wait_eligible_flag"] = df["encounter_wait_eligible_flag"]
        out["exclusion_reason_code"] = df["exclusion_reason_code"]
        out["source_primary_key"] = df["encounter_id"]
        out["source_row_number"] = df["__row_number"]
        out["processing_run_id"] = self.processing_run_id
        out["validation_run_id"] = self.validation_run_id
        out["transformation_version"] = TRANSFORMATION_VERSION
        out["processed_datetime"] = datetime.utcnow().isoformat() + "Z"

        # Reorder exactly to schema
        out = out[[c for c in target_cols if c in out.columns]]

        self.processed_df = out
        return out

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------
    def _parse_dates(self, series: pd.Series) -> pd.Series:
        """Parse date-only values; return NaT for empty/unparseable."""
        cleaned = series.replace("", pd.NA).replace("NaT", pd.NA)
        parsed = pd.to_datetime(cleaned, errors="coerce", format="%Y-%m-%d")
        # Also try without strict format
        mask = parsed.isna() & cleaned.notna()
        if mask.any():
            parsed.loc[mask] = pd.to_datetime(cleaned.loc[mask], errors="coerce")
        return parsed

    def _parse_datetimes(self, series: pd.Series, field_name: str) -> pd.Series:
        """Parse full datetimes; return NaT for empty/unparseable. Record issues."""
        cleaned = series.replace("", pd.NA).replace("NaT", pd.NA)
        parsed = pd.to_datetime(cleaned, errors="coerce")
        # Record unparseable examples
        unparseable = cleaned.notna() & parsed.isna()
        if unparseable.any():
            examples = cleaned[unparseable].head(self.max_issue_examples).tolist()
            self._add_issue(
                severity="Error",
                issue_type="Unparsable Timestamp",
                description=f"Could not parse {field_name} for {unparseable.sum()} records. Examples: {examples[:5]}",
                field_name=field_name,
                evidence=json.dumps(examples[:5]),
            )
        return parsed

    # ------------------------------------------------------------------
    # Disposition flags
    # ------------------------------------------------------------------
    def _derive_disposition_flags(self, df: pd.DataFrame) -> pd.DataFrame:
        disp = df["disposition_status"].astype(str).str.strip().str.lower()

        df["cancelled_flag"] = disp.isin(DISPOSITION_CANCELLED)
        df["left_before_service_flag"] = disp.isin(DISPOSITION_LWBS)
        df["completed_service_flag"] = disp.isin(DISPOSITION_COMPLETED)

        # Unsupported disposition
        known = DISPOSITION_CANCELLED | DISPOSITION_LWBS | DISPOSITION_COMPLETED
        unsupported = ~disp.isin(known) & (disp != "") & disp.notna()
        if unsupported.any():
            examples = df.loc[unsupported, "disposition_status"].head(5).tolist()
            self._add_issue(
                severity="Warning",
                issue_type="Unsupported Disposition Status",
                description=f"Unsupported disposition_status values found: {examples}",
                field_name="disposition_status",
                evidence=json.dumps(examples),
            )
            # Mark as unsupported but do not guess
            df.loc[unsupported, "completed_service_flag"] = False

        return df

    # ------------------------------------------------------------------
    # Wait intervals
    # ------------------------------------------------------------------
    def _calculate_wait_intervals(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in TIMESTAMP_COLS:
            df[col] = df[f"{col}_parsed"]

        def _diff_minutes(end: pd.Series, start: pd.Series) -> pd.Series:
            diff = (end - start).dt.total_seconds() / 60.0
            return diff

        df["arrival_to_triage_minutes"] = _diff_minutes(df["triage_datetime"], df["arrival_datetime"])
        df["arrival_to_consultation_minutes"] = _diff_minutes(df["consultation_start_datetime"], df["arrival_datetime"])
        df["triage_to_consultation_minutes"] = _diff_minutes(df["consultation_start_datetime"], df["triage_datetime"])
        df["consultation_to_service_end_minutes"] = _diff_minutes(df["service_end_datetime"], df["consultation_start_datetime"])

        # Detect negative intervals and null them
        interval_cols = [
            "arrival_to_triage_minutes",
            "arrival_to_consultation_minutes",
            "triage_to_consultation_minutes",
            "consultation_to_service_end_minutes",
        ]
        for col in interval_cols:
            negative = df[col] < 0
            if negative.any():
                self._add_issue(
                    severity="Error",
                    issue_type="Invalid Wait Interval",
                    description=f"Negative values detected in {col} ({negative.sum()} records).",
                    field_name=col,
                    evidence=json.dumps(df.loc[negative, col].head(5).tolist()),
                )
                df.loc[negative, col] = pd.NA

        return df

    # ------------------------------------------------------------------
    # Wait eligibility
    # ------------------------------------------------------------------
    def _derive_wait_eligibility(self, df: pd.DataFrame) -> pd.DataFrame:
        # Default flags
        df["official_wait_stage_eligible_flag"] = False
        df["encounter_wait_eligible_flag"] = False
        df["exclusion_reason_code"] = None

        # Conditions for eligibility (preparation-level, not KPI)
        has_arrival = df["arrival_datetime"].notna()
        has_triage = df["triage_datetime"].notna()
        has_consultation = df["consultation_start_datetime"].notna()
        has_service_end = df["service_end_datetime"].notna()

        # Invalid timestamp order detection
        invalid_order = pd.Series(False, index=df.index)
        for earlier, later in [
            ("arrival_datetime", "triage_datetime"),
            ("arrival_datetime", "consultation_start_datetime"),
            ("triage_datetime", "consultation_start_datetime"),
            ("consultation_start_datetime", "service_end_datetime"),
        ]:
            mask = df[earlier].notna() & df[later].notna() & (df[later] < df[earlier])
            invalid_order |= mask

        if invalid_order.any():
            self._add_issue(
                severity="Error",
                issue_type="Invalid Timestamp Order",
                description=f"Impossible timestamp order in {invalid_order.sum()} records.",
                field_name="timestamp_order",
                evidence="",
            )
            df.loc[invalid_order, "exclusion_reason_code"] = "INVALID_TIMESTAMP_ORDER"
            df.loc[invalid_order, "encounter_wait_eligible_flag"] = False
            df.loc[invalid_order, "official_wait_stage_eligible_flag"] = False

        # Cancelled
        cancelled = df["cancelled_flag"] == True
        df.loc[cancelled, "exclusion_reason_code"] = "CANCELLED_ENCOUNTER"
        df.loc[cancelled, "encounter_wait_eligible_flag"] = False
        df.loc[cancelled, "official_wait_stage_eligible_flag"] = False

        # Left before service
        lwbs = df["left_before_service_flag"] == True
        df.loc[lwbs, "exclusion_reason_code"] = "LEFT_BEFORE_SERVICE"
        df.loc[lwbs, "encounter_wait_eligible_flag"] = False
        df.loc[lwbs, "official_wait_stage_eligible_flag"] = False

        # Completed with missing required timestamps
        completed = df["completed_service_flag"] == True
        missing_required = completed & (~has_arrival | ~has_consultation)
        if missing_required.any():
            df.loc[missing_required & ~has_arrival, "exclusion_reason_code"] = "MISSING_ARRIVAL_TIMESTAMP"
            df.loc[missing_required & has_arrival & ~has_consultation, "exclusion_reason_code"] = "MISSING_CONSULTATION_TIMESTAMP"
            df.loc[missing_required, "encounter_wait_eligible_flag"] = False
            df.loc[missing_required, "official_wait_stage_eligible_flag"] = False

        # Eligible completed: arrival + consultation present, no invalid order, not cancelled/LWBS
        eligible = (
            completed
            & has_arrival
            & has_consultation
            & ~invalid_order
            & ~cancelled
            & ~lwbs
        )
        df.loc[eligible, "encounter_wait_eligible_flag"] = True
        # Official wait stage: require triage as well (adjust if rule changes)
        official_eligible = eligible & has_triage
        df.loc[official_eligible, "official_wait_stage_eligible_flag"] = True

        # Missing service end for completed is noted but does not block encounter-level eligibility
        missing_end = completed & ~has_service_end & eligible
        if missing_end.any():
            self._add_issue(
                severity="Warning",
                issue_type="Missing Required Timestamp",
                description=f"Completed encounters missing service_end_datetime ({missing_end.sum()} records).",
                field_name="service_end_datetime",
            )

        # Unresolved rule placeholder
        if not self.unresolved_rules:
            # If official wait-stage definition is not fully documented, flag it
            self.unresolved_rules.append(
                "Official wait-stage definition may require clinical review for encounters without triage."
            )

        return df

    # ------------------------------------------------------------------
    # Schema validation
    # ------------------------------------------------------------------
    def validate_processed_schema(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        schema = get_processed_schema("processed_patient_encounters")
        required = schema.get("required_fields", [])
        errors: List[str] = []

        # Field presence and order
        target_fields = schema["required_fields"] + schema.get("optional_fields", [])
        missing = [c for c in target_fields if c not in df.columns]
        if missing:
            errors.append(f"Missing columns: {missing}")

        extra = [c for c in df.columns if c not in target_fields]
        if extra:
            errors.append(f"Extra columns: {extra}")

        # Required-field completeness (skip optional timestamp/interval fields)
        optional_nullable = {
            "triage_datetime", "consultation_start_datetime", "service_end_datetime",
            "arrival_to_triage_minutes", "arrival_to_consultation_minutes",
            "triage_to_consultation_minutes", "consultation_to_service_end_minutes",
            "exclusion_reason_code",
        }
        for col in required:
            if col in df.columns and col not in optional_nullable:
                nulls = df[col].isna().sum() + (df[col] == "").sum()
                if nulls > 0:
                    errors.append(f"Required column '{col}' has {nulls} null/empty values.")

        # Primary-key uniqueness
        pk = schema.get("primary_key", ["encounter_id"])
        if all(c in df.columns for c in pk):
            dups = df.duplicated(subset=pk).sum()
            if dups > 0:
                errors.append(f"Primary key {pk} has {dups} duplicate rows.")

        # Date/datetime parseability
        for col in ["encounter_date", "reporting_date"]:
            if col in df.columns:
                non_null = df[col].notna()
                if non_null.any() and not pd.api.types.is_datetime64_any_dtype(df[col]):
                    errors.append(f"Column '{col}' is not datetime type.")

        for col in TIMESTAMP_COLS:
            if col in df.columns:
                if not pd.api.types.is_datetime64_any_dtype(df[col]):
                    errors.append(f"Column '{col}' is not datetime type.")

        # Boolean consistency
        for col in ["cancelled_flag", "left_before_service_flag", "completed_service_flag",
                    "official_wait_stage_eligible_flag", "encounter_wait_eligible_flag"]:
            if col in df.columns:
                if df[col].dtype != bool:
                    errors.append(f"Column '{col}' is not bool dtype (found {df[col].dtype}).")

        # No prohibited fields
        prohibited = ["waiting_time_kpi", "average_waiting_time", "kpi_status", "risk_score",
                      "forecast", "scenario_result", "financial_result", "recommendation",
                      "patient_name", "clinical_notes", "diagnosis", "direct_personal_identifier"]
        for bad in prohibited:
            if bad in df.columns:
                errors.append(f"Prohibited column '{bad}' found in output.")

        return len(errors) == 0, errors

    # ------------------------------------------------------------------
    # Lineage
    # ------------------------------------------------------------------
    def build_lineage(self, source: pd.DataFrame, processed: pd.DataFrame) -> List[ProcessingLineageRecord]:
        if not self.collect_lineage:
            return []

        records: List[ProcessingLineageRecord] = []
        source_cols = list(source.columns)
        now = datetime.utcnow().isoformat() + "Z"

        # Build efficiently using lists
        for idx in processed.index:
            encounter_id = processed.at[idx, "encounter_id"]
            row_num = source.at[idx, "__row_number"] if "__row_number" in source.columns else idx + 2
            exclusion_code = processed.at[idx, "exclusion_reason_code"]
            exclusion_flag = pd.notna(exclusion_code) and exclusion_code != ""

            record = ProcessingLineageRecord(
                processing_run_id=self.processing_run_id,
                lineage_id=f"LIN-{uuid.uuid4().hex[:12].upper()}",
                validation_run_id=self.validation_run_id or "",
                source_dataset_name="patient_encounters",
                source_file_name="patient_encounters.csv",
                source_primary_key_field="encounter_id",
                source_primary_key_value=str(encounter_id) if pd.notna(encounter_id) else "",
                source_row_number=int(row_num),
                processed_dataset_name="processed_patient_encounters",
                processed_primary_key_field="encounter_id",
                processed_primary_key_value=str(encounter_id) if pd.notna(encounter_id) else "",
                transformation_rule_id="TR_PF_TIMESTAMP_PARSE",
                transformation_description="Parsed encounter dates and timestamps; derived disposition flags, wait intervals and eligibility.",
                source_fields_used=",".join(source_cols),
                processed_fields_created=",".join(processed.columns.tolist()),
                exclusion_flag=exclusion_flag,
                exclusion_reason_code=exclusion_code if pd.notna(exclusion_code) else "",
                transformation_version=TRANSFORMATION_VERSION,
                configuration_version="",
                processed_datetime=datetime.now(),
            )
            records.append(record)

        self.lineage = records
        return records

    # ------------------------------------------------------------------
    # Exclusions
    # ------------------------------------------------------------------
    def build_exclusions(self, processed: pd.DataFrame) -> List[ProcessingExclusionRecord]:
        records: List[ProcessingExclusionRecord] = []
        now = datetime.utcnow().isoformat() + "Z"

        mask = processed["exclusion_reason_code"].notna() & (processed["exclusion_reason_code"] != "")
        for idx in processed[mask].index:
            reason_code = processed.at[idx, "exclusion_reason_code"]
            encounter_id = processed.at[idx, "encounter_id"]
            record = ProcessingExclusionRecord(
                processing_run_id=self.processing_run_id,
                exclusion_id=f"EXC-{uuid.uuid4().hex[:12].upper()}",
                source_dataset_name="patient_encounters",
                source_primary_key_field="encounter_id",
                source_primary_key_value=str(encounter_id) if pd.notna(encounter_id) else "",
                source_row_number=idx + 2,
                exclusion_reason_code=reason_code,
                exclusion_reason_description=EXCLUSION_REASONS.get(reason_code, reason_code),
                validation_issue_id="",
                manual_override_id="",
                exclusion_stage="transformation",
                excluded_by_rule="PatientEncounterTransformer",
                reversible_flag=False,
                created_datetime=datetime.now(),
            )
            records.append(record)

        self.exclusions = records
        return records

    # ------------------------------------------------------------------
    # Issues
    # ------------------------------------------------------------------
    def collect_issues(self) -> List[ProcessingIssue]:
        return self.issues

    def _add_issue(
        self,
        severity: str,
        issue_type: str,
        description: str,
        field_name: str = "",
        evidence: str = "",
    ) -> None:
        if len(self.issues) >= self.max_issue_examples:
            return
        issue = ProcessingIssue(
            processing_run_id=self.processing_run_id,
            issue_id=f"ISS-{uuid.uuid4().hex[:12].upper()}",
            source_dataset_name="patient_encounters",
            processed_dataset_name="processed_patient_encounters",
            severity=severity,
            issue_type=issue_type,
            issue_description=description,
            field_name=field_name,
            source_value=evidence,
            created_datetime=datetime.now(),
        )
        self.issues.append(issue)

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------
    def _audit(self, event: str, details: Dict[str, Any]) -> None:
        self.audit_events.append({
            "processing_run_id": self.processing_run_id,
            "event": event,
            "details": json.dumps(details),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        })

    # ------------------------------------------------------------------
    # Result
    # ------------------------------------------------------------------
    def return_transformation_result(
        self, df: pd.DataFrame, schema_passed: bool, schema_errors: List[str]
    ) -> TransformationResultContract:
        return TransformationResultContract(
            success=schema_passed,
            dataset_name="processed_patient_encounters",
            record_count=len(df),
            schema_errors=schema_errors,
            issues=self.issues,
            lineage=self.lineage,
            exclusions=self.exclusions,
        )
