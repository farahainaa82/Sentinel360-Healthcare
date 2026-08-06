"""
Sentinel360 Healthcare — Patient Flow Integration Validator

Integration and assurance layer for the complete patient-flow processing chain.
Verifies all five processed datasets, cross-step lineage, reconciliation,
and prohibited-field compliance.

Step: 2D-3D
"""

import hashlib
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd
import numpy as np

from src.processed_schema_registry import get_processed_schema
from src.processing_contracts import ValidationGateResult
from src.processing_models import ProcessingIssue, ProcessingExclusionRecord

INTEGRATION_VERSION = "2D-3D-1.0.0"
ENGINE_VERSION = "Sentinel360-Phase1-2D-3D"

PROCESSED_DATASETS = {
    "processed_patient_encounters": {
        "file_name": "processed_patient_encounters.csv",
        "primary_key": "encounter_id",
        "grain_keys": ["hospital_id", "department_id", "reporting_date"],
        "manifest_name": "patient_encounter_processing_run_manifest.json",
    },
    "processed_patient_queue": {
        "file_name": "processed_patient_queue.csv",
        "primary_key": "queue_record_id",
        "grain_keys": ["hospital_id", "department_id", "reporting_date"],
        "manifest_name": "queue_capacity_schedule_processing_run_manifest.json",
    },
    "processed_bed_capacity": {
        "file_name": "processed_bed_capacity.csv",
        "primary_key": "bed_capacity_record_id",
        "grain_keys": ["hospital_id", "department_id", "reporting_date"],
        "manifest_name": "queue_capacity_schedule_processing_run_manifest.json",
    },
    "processed_service_schedule": {
        "file_name": "processed_service_schedule.csv",
        "primary_key": "service_schedule_id",
        "grain_keys": ["hospital_id", "department_id", "reporting_date"],
        "manifest_name": "queue_capacity_schedule_processing_run_manifest.json",
    },
    "processed_patient_flow_daily": {
        "file_name": "processed_patient_flow_daily.csv",
        "primary_key": "patient_flow_daily_id",
        "grain_keys": ["hospital_id", "department_id", "reporting_date"],
        "manifest_name": "patient_flow_daily_processing_run_manifest.json",
    },
}

PRIOR_MANIFESTS = [
    "patient_encounter_processing_run_manifest.json",
    "queue_capacity_schedule_processing_run_manifest.json",
    "patient_flow_daily_processing_run_manifest.json",
]

PROHIBITED_FIELD_PATTERNS = [
    "kpi_value", "kpi_status", "trend", "anomaly_score", "risk_score",
    "forecast", "scenario", "financial_impact", "recommendation",
    "management_decision", "action_tracking", "outcome_review",
    "average_patient_waiting_time", "bed_occupancy_rate", "staffing_level",
    "staff_absenteeism_rate", "complaint_rate", "patient_satisfaction_score",
]


class PatientFlowIntegrationValidator:
    """Integration validator for patient-flow processing chain."""

    def __init__(
        self,
        integration_run_id: str,
        processed_directory: Path,
        log_directory: Path,
        max_issue_examples: int = 1000,
        reconciliation_tolerance: float = 0.001,
    ):
        self.integration_run_id = integration_run_id
        self.processed_directory = processed_directory
        self.log_directory = log_directory
        self.max_issue_examples = max_issue_examples
        self.reconciliation_tolerance = reconciliation_tolerance
        self.issues: List[ProcessingIssue] = []
        self.check_results: List[Dict[str, Any]] = []
        self.reconciliation_records: List[Dict[str, Any]] = []
        self.lineage_summary: List[Dict[str, Any]] = []
        self.lineage_gaps: List[Dict[str, Any]] = []
        self.exclusion_summary: List[Dict[str, Any]] = []
        self.audit_events: List[Dict[str, Any]] = []
        self.dataset_checksums: Dict[str, str] = {}
        self.prior_manifests: Dict[str, Dict[str, Any]] = {}
        self.processed_dataframes: Dict[str, pd.DataFrame] = {}

    # -----------------------------------------------------------------------
    # Integration Gate
    # -----------------------------------------------------------------------

    def load_prior_manifests(self) -> ValidationGateResult:
        """Load and verify all three prior processing manifests."""
        all_passed = True
        blocking_reasons = []

        for manifest_name in PRIOR_MANIFESTS:
            manifest_path = self.log_directory / manifest_name
            if not manifest_path.exists():
                all_passed = False
                blocking_reasons.append(f"{manifest_name} not found.")
                continue
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
            except Exception as e:
                all_passed = False
                blocking_reasons.append(f"{manifest_name} unreadable: {e}")
                continue

            self.prior_manifests[manifest_name] = manifest
            run_status = manifest.get("run_status", "")
            if run_status not in ("success", "Completed"):
                all_passed = False
                blocking_reasons.append(f"{manifest_name} run_status was '{run_status}'.")
                continue

            proc_allowed = manifest.get("processing_allowed_flag", True)
            if proc_allowed is False:
                all_passed = False
                blocking_reasons.append(f"{manifest_name} processing_allowed_flag was False.")
                continue

        if all_passed:
            result = ValidationGateResult(
                processing_allowed=True,
                blocking_reason="",
                validation_run_id="",
            )
            self._audit("Prior Manifests Verified", "All passed")
        else:
            result = ValidationGateResult(
                processing_allowed=False,
                blocking_reason="; ".join(blocking_reasons),
                validation_run_id="",
            )
            self._audit("Prior Manifests Verified", f"Blocked — {'; '.join(blocking_reasons)}")

        return result

    def verify_prior_run_statuses(self) -> List[str]:
        """Verify prior run statuses from loaded manifests."""
        errors = []
        for name, manifest in self.prior_manifests.items():
            run_status = manifest.get("run_status", "")
            if run_status not in ("success", "Completed"):
                errors.append(f"{name}: run_status = '{run_status}'")
        self._audit("Prior Run Statuses Checked", f"{len(errors)} failures")
        return errors

    # -----------------------------------------------------------------------
    # Dataset Loading
    # -----------------------------------------------------------------------

    def load_processed_datasets(self) -> Dict[str, pd.DataFrame]:
        """Load all five processed datasets."""
        loaded: Dict[str, pd.DataFrame] = {}
        for ds_name, config in PROCESSED_DATASETS.items():
            file_path = self.processed_directory / config["file_name"]
            if not file_path.exists():
                raise FileNotFoundError(f"Processed dataset not found: {file_path}")
            df = pd.read_csv(file_path)
            loaded[ds_name] = df
            self.dataset_checksums[ds_name] = self._file_checksum(file_path)
            self._audit(f"{ds_name} Loaded", f"{len(df)} rows")
        self.processed_dataframes = loaded
        return loaded

    def verify_manifest_checksums(self) -> bool:
        """Verify that dataset checksums match prior manifest checksums where available."""
        all_match = True
        for ds_name, config in PROCESSED_DATASETS.items():
            manifest_name = config["manifest_name"]
            manifest = self.prior_manifests.get(manifest_name, {})
            input_checksums = manifest.get("input_checksums", {})
            expected = input_checksums.get(ds_name)
            if expected is None:
                continue
            actual = self.dataset_checksums.get(ds_name)
            if actual != expected:
                all_match = False
                self._add_issue(
                    source_dataset_name=ds_name,
                    issue_type="Checksum Mismatch",
                    severity="Critical",
                    description=f"Checksum mismatch for {ds_name}: expected {expected}, got {actual}",
                )
        self._audit("Manifest Checksums Verified", f"Match: {all_match}")
        return all_match

    # -----------------------------------------------------------------------
    # Schema Validation
    # -----------------------------------------------------------------------

    def validate_processed_schemas(self) -> List[str]:
        """Validate all five processed datasets against schema registry."""
        errors = []
        for ds_name, df in self.processed_dataframes.items():
            schema = get_processed_schema(ds_name)
            if schema is None:
                errors.append(f"Schema not found for {ds_name}")
                continue
            required = schema.get("required_fields", [])
            for field in required:
                if field not in df.columns:
                    errors.append(f"Missing required field '{field}' in {ds_name}")
        if errors:
            for err in errors:
                self._add_issue(
                    source_dataset_name="",
                    issue_type="Schema Mismatch",
                    severity="Error",
                    description=err,
                )
        self._audit("Processed Schemas Validated", f"Errors: {len(errors)}")
        return errors

    # -----------------------------------------------------------------------
    # Business Key Integrity
    # -----------------------------------------------------------------------

    def validate_business_keys(self) -> List[str]:
        """Validate business key uniqueness for all datasets."""
        errors = []
        for ds_name, config in PROCESSED_DATASETS.items():
            df = self.processed_dataframes[ds_name]
            pk = config["primary_key"]
            if pk in df.columns:
                dups = df[pk].duplicated().sum()
                if dups > 0:
                    errors.append(f"{ds_name}: {dups} duplicate {pk}")
                    self._add_issue(
                        source_dataset_name=ds_name,
                        issue_type="Duplicate Business Key",
                        severity="Error",
                        description=f"{dups} duplicate {pk} in {ds_name}",
                    )

        # Daily grain uniqueness
        daily = self.processed_dataframes["processed_patient_flow_daily"]
        grain_dups = daily[["hospital_id", "department_id", "reporting_date"]].duplicated().sum()
        if grain_dups > 0:
            errors.append(f"processed_patient_flow_daily: {grain_dups} duplicate daily grains")
            self._add_issue(
                source_dataset_name="processed_patient_flow_daily",
                issue_type="Invalid Daily Grain",
                severity="Critical",
                description=f"{grain_dups} duplicate daily grains",
            )

        # Daily ID deterministic check
        expected_id = (
            "PFD-" + daily["hospital_id"].astype(str) + "-"
            + daily["department_id"].astype(str) + "-"
            + daily["reporting_date"].astype(str).str.replace("-", "", regex=False)
        )
        if not (daily["patient_flow_daily_id"] == expected_id).all():
            errors.append("processed_patient_flow_daily: patient_flow_daily_id is not deterministic")
            self._add_issue(
                source_dataset_name="processed_patient_flow_daily",
                issue_type="Invalid Daily Grain",
                severity="Error",
                description="patient_flow_daily_id is not deterministic",
            )

        self._audit("Business Keys Validated", f"Errors: {len(errors)}")
        return errors

    # -----------------------------------------------------------------------
    # Cross-Dataset References
    # -----------------------------------------------------------------------

    def validate_cross_dataset_references(self) -> List[str]:
        """Validate cross-dataset hospital/dept consistency and orphan checks."""
        errors = []
        enc = self.processed_dataframes["processed_patient_encounters"]
        q = self.processed_dataframes["processed_patient_queue"]
        b = self.processed_dataframes["processed_bed_capacity"]
        s = self.processed_dataframes["processed_service_schedule"]
        d = self.processed_dataframes["processed_patient_flow_daily"]

        # Hospital consistency
        all_hospitals = set(enc["hospital_id"].unique()) | set(q["hospital_id"].unique()) | set(b["hospital_id"].unique()) | set(s["hospital_id"].unique())
        daily_hospitals = set(d["hospital_id"].unique())
        if daily_hospitals != all_hospitals:
            errors.append("Hospital IDs are not consistent across datasets")

        # Department union check
        all_depts = set(enc["department_id"].unique()) | set(q["department_id"].unique()) | set(b["department_id"].unique()) | set(s["department_id"].unique())
        daily_depts = set(d["department_id"].unique())
        orphan_depts = daily_depts - all_depts
        if orphan_depts:
            errors.append(f"Daily departments not found in inputs: {orphan_depts}")
            self._add_issue(
                source_dataset_name="processed_patient_flow_daily",
                issue_type="Orphan Daily Row",
                severity="Error",
                description=f"Departments {orphan_depts} not in any input",
            )

        # Orphan daily rows
        enc_grain = set(tuple(x) for x in enc[["hospital_id","department_id","reporting_date"]].drop_duplicates().values)
        q_grain = set(tuple(x) for x in q[["hospital_id","department_id","reporting_date"]].drop_duplicates().values)
        b_grain = set(tuple(x) for x in b[["hospital_id","department_id","reporting_date"]].drop_duplicates().values)
        s_grain = set(tuple(x) for x in s[["hospital_id","department_id","reporting_date"]].drop_duplicates().values)
        all_grains = enc_grain | q_grain | b_grain | s_grain
        daily_grain = set(tuple(x) for x in d[["hospital_id","department_id","reporting_date"]].values)
        orphans = daily_grain - all_grains
        if orphans:
            errors.append(f"{len(orphans)} orphan daily rows")
            self._add_issue(
                source_dataset_name="processed_patient_flow_daily",
                issue_type="Orphan Daily Row",
                severity="Error",
                description=f"{len(orphans)} daily rows with no source in any input dataset",
            )

        self._audit("Cross-Dataset References Validated", f"Errors: {len(errors)}")
        return errors

    # -----------------------------------------------------------------------
    # Date Alignment
    # -----------------------------------------------------------------------

    def validate_date_alignment(self) -> List[str]:
        """Validate date and month alignment across datasets."""
        errors = []
        for ds_name, df in self.processed_dataframes.items():
            if "reporting_date" not in df.columns or "reporting_month" not in df.columns:
                continue
            df = df.copy()
            df["parsed_date"] = pd.to_datetime(df["reporting_date"], errors="coerce")
            df["expected_month"] = df["parsed_date"].dt.strftime("%Y-%m")
            mismatches = (df["reporting_month"] != df["expected_month"]).sum()
            if mismatches > 0:
                errors.append(f"{ds_name}: {mismatches} reporting_month mismatches")
                self._add_issue(
                    source_dataset_name=ds_name,
                    issue_type="Date Alignment Failure",
                    severity="Error",
                    description=f"{mismatches} reporting_month mismatches in {ds_name}",
                )

        self._audit("Date Alignment Validated", f"Errors: {len(errors)}")
        return errors

    # -----------------------------------------------------------------------
    # Reconciliation
    # -----------------------------------------------------------------------

    def reconcile_daily_encounters(self) -> List[Dict[str, Any]]:
        """Reconcile encounter fields between daily and source."""
        enc = self.processed_dataframes["processed_patient_encounters"].copy()
        daily = self.processed_dataframes["processed_patient_flow_daily"].copy()
        enc["reporting_date"] = pd.to_datetime(enc["reporting_date"], errors="coerce").dt.strftime("%Y-%m-%d")

        bool_cols = ["completed_service_flag", "cancelled_flag", "left_before_service_flag", "official_wait_stage_eligible_flag"]
        for col in bool_cols:
            if col in enc.columns:
                enc[col] = enc[col].fillna(False).astype(bool)

        enc_agg = enc.groupby(["hospital_id", "department_id", "reporting_date"], as_index=False).agg(
            encounter_count_src=("encounter_id", "size"),
            completed_encounter_count_src=("completed_service_flag", "sum"),
            cancelled_encounter_count_src=("cancelled_flag", "sum"),
            left_before_service_count_src=("left_before_service_flag", "sum"),
            official_wait_eligible_encounter_count_src=("official_wait_stage_eligible_flag", "sum"),
        )

        # Wait-minute total
        if "arrival_to_consultation_minutes" in enc.columns:
            enc["arrival_to_consultation_minutes"] = pd.to_numeric(enc["arrival_to_consultation_minutes"], errors="coerce")
            eligible = enc[
                enc["official_wait_stage_eligible_flag"].eq(True)
                & enc["arrival_to_consultation_minutes"].notna()
                & enc["arrival_to_consultation_minutes"].ge(0)
            ]
            wait_sum = eligible.groupby(["hospital_id", "department_id", "reporting_date"], as_index=False)["arrival_to_consultation_minutes"].sum()
            wait_sum = wait_sum.rename(columns={"arrival_to_consultation_minutes": "total_arrival_to_consultation_minutes_src"})
            enc_agg = enc_agg.merge(wait_sum, on=["hospital_id", "department_id", "reporting_date"], how="left")
        else:
            enc_agg["total_arrival_to_consultation_minutes_src"] = np.nan

        merged = daily.merge(enc_agg, on=["hospital_id", "department_id", "reporting_date"], how="left")
        merged["encounter_count_src"] = merged["encounter_count_src"].fillna(0).astype(int)

        records = []
        for field, src_field in [
            ("encounter_count", "encounter_count_src"),
            ("completed_encounter_count", "completed_encounter_count_src"),
            ("cancelled_encounter_count", "cancelled_encounter_count_src"),
            ("left_before_service_count", "left_before_service_count_src"),
            ("official_wait_eligible_encounter_count", "official_wait_eligible_encounter_count_src"),
        ]:
            mismatches = merged[field].fillna(0).astype(int) != merged[src_field].fillna(0).astype(int)
            count = mismatches.sum()
            status = "Passed" if count == 0 else "Failed"
            records.append({
                "integration_run_id": self.integration_run_id,
                "patient_flow_daily_id": "",
                "hospital_id": "",
                "department_id": "",
                "reporting_date": "",
                "reconciliation_domain": "encounter",
                "reconciliation_field": field,
                "source_calculated_value": "",
                "daily_stored_value": "",
                "difference_value": "",
                "reconciliation_status": status,
                "issue_id": "",
                "checked_datetime": datetime.now(),
            })
            self._add_check("Reconciliation", "processed_patient_flow_daily", f"encounter_{field}", "match", str(count), status, count)

        # Wait-minute reconciliation
        wait_mismatches = 0
        for idx, row in merged.iterrows():
            daily_val = row["total_arrival_to_consultation_minutes"]
            src_val = row["total_arrival_to_consultation_minutes_src"]
            if pd.isna(daily_val) and pd.isna(src_val):
                continue
            if pd.isna(daily_val) or pd.isna(src_val):
                wait_mismatches += 1
                continue
            if abs(daily_val - src_val) > self.reconciliation_tolerance:
                wait_mismatches += 1

        status = "Passed" if wait_mismatches == 0 else "Failed"
        records.append({
            "integration_run_id": self.integration_run_id,
            "patient_flow_daily_id": "",
            "hospital_id": "",
            "department_id": "",
            "reporting_date": "",
            "reconciliation_domain": "encounter",
            "reconciliation_field": "total_arrival_to_consultation_minutes",
            "source_calculated_value": "",
            "daily_stored_value": "",
            "difference_value": "",
            "reconciliation_status": status,
            "issue_id": "",
            "checked_datetime": datetime.now(),
        })
        self._add_check("Reconciliation", "processed_patient_flow_daily", "encounter_wait_minutes", "match", str(wait_mismatches), status, wait_mismatches)

        self.reconciliation_records.extend(records)
        self._audit("Encounter Reconciliation Completed", f"Mismatches: {sum(1 for r in records if r['reconciliation_status'] == 'Failed')}")
        return records

    def reconcile_daily_queue(self) -> List[Dict[str, Any]]:
        """Reconcile queue fields between daily and source."""
        q = self.processed_dataframes["processed_patient_queue"].copy()
        daily = self.processed_dataframes["processed_patient_flow_daily"].copy()
        q["reporting_date"] = pd.to_datetime(q["reporting_date"], errors="coerce").dt.strftime("%Y-%m-%d")

        merged = daily.merge(q, on=["hospital_id", "department_id", "reporting_date"], how="left", suffixes=("", "_src"))

        records = []
        for field, src_field in [
            ("queue_arrivals_count", "arrivals_count"),
            ("queue_served_count", "served_count"),
            ("queue_waiting_patient_count", "waiting_patient_count"),
            ("queue_average_wait_minutes", "average_wait_minutes"),
        ]:
            mismatches = 0
            for idx, row in merged.iterrows():
                daily_val = row[field]
                src_val = row[src_field]
                if pd.isna(daily_val) and pd.isna(src_val):
                    continue
                if pd.isna(daily_val) or pd.isna(src_val):
                    mismatches += 1
                    continue
                if field == "queue_average_wait_minutes":
                    if abs(daily_val - src_val) > self.reconciliation_tolerance:
                        mismatches += 1
                else:
                    if daily_val != src_val:
                        mismatches += 1

            status = "Passed" if mismatches == 0 else "Failed"
            records.append({
                "integration_run_id": self.integration_run_id,
                "patient_flow_daily_id": "",
                "hospital_id": "",
                "department_id": "",
                "reporting_date": "",
                "reconciliation_domain": "queue",
                "reconciliation_field": field,
                "source_calculated_value": "",
                "daily_stored_value": "",
                "difference_value": "",
                "reconciliation_status": status,
                "issue_id": "",
                "checked_datetime": datetime.now(),
            })
            self._add_check("Reconciliation", "processed_patient_flow_daily", f"queue_{field}", "match", str(mismatches), status, mismatches)

        self.reconciliation_records.extend(records)
        self._audit("Queue Reconciliation Completed", f"Mismatches: {sum(1 for r in records if r['reconciliation_status'] == 'Failed')}")
        return records

    def reconcile_daily_bed_capacity(self) -> List[Dict[str, Any]]:
        """Reconcile bed-capacity fields between daily and source."""
        b = self.processed_dataframes["processed_bed_capacity"].copy()
        daily = self.processed_dataframes["processed_patient_flow_daily"].copy()
        b["reporting_date"] = pd.to_datetime(b["reporting_date"], errors="coerce").dt.strftime("%Y-%m-%d")

        merged = daily.merge(b, on=["hospital_id", "department_id", "reporting_date"], how="left", suffixes=("", "_src"))

        records = []
        for field in ["licensed_beds", "staffed_beds", "operational_beds", "occupied_beds", "unavailable_beds", "reserved_beds"]:
            mismatches = 0
            for idx, row in merged.iterrows():
                daily_val = row[field]
                src_val = row[field + "_src"]
                if pd.isna(daily_val) and pd.isna(src_val):
                    continue
                if pd.isna(daily_val) or pd.isna(src_val):
                    mismatches += 1
                    continue
                if abs(daily_val - src_val) > self.reconciliation_tolerance:
                    mismatches += 1

            status = "Passed" if mismatches == 0 else "Failed"
            records.append({
                "integration_run_id": self.integration_run_id,
                "patient_flow_daily_id": "",
                "hospital_id": "",
                "department_id": "",
                "reporting_date": "",
                "reconciliation_domain": "bed",
                "reconciliation_field": field,
                "source_calculated_value": "",
                "daily_stored_value": "",
                "difference_value": "",
                "reconciliation_status": status,
                "issue_id": "",
                "checked_datetime": datetime.now(),
            })
            self._add_check("Reconciliation", "processed_patient_flow_daily", f"bed_{field}", "match", str(mismatches), status, mismatches)

        # Verify beds_above_operational_capacity
        merged["calc_beds_above"] = (merged["occupied_beds_src"] - merged["operational_beds_src"]).clip(lower=0)
        above_mismatches = 0
        for idx, row in merged.iterrows():
            daily_val = row["beds_above_operational_capacity"]
            src_val = row["calc_beds_above"]
            if pd.isna(daily_val) and pd.isna(src_val):
                continue
            if pd.isna(daily_val) or pd.isna(src_val):
                above_mismatches += 1
                continue
            if abs(daily_val - src_val) > self.reconciliation_tolerance:
                above_mismatches += 1

        status = "Passed" if above_mismatches == 0 else "Failed"
        records.append({
            "integration_run_id": self.integration_run_id,
            "patient_flow_daily_id": "",
            "hospital_id": "",
            "department_id": "",
            "reporting_date": "",
            "reconciliation_domain": "bed",
            "reconciliation_field": "beds_above_operational_capacity",
            "source_calculated_value": "",
            "daily_stored_value": "",
            "difference_value": "",
            "reconciliation_status": status,
            "issue_id": "",
            "checked_datetime": datetime.now(),
        })
        self._add_check("Reconciliation", "processed_patient_flow_daily", "bed_beds_above_operational_capacity", "match", str(above_mismatches), status, above_mismatches)

        # Verify overcapacity_flag
        merged["calc_overcapacity"] = np.where(
            merged["occupied_beds_src"].notna() & merged["operational_beds_src"].notna(),
            merged["occupied_beds_src"] > merged["operational_beds_src"],
            np.nan
        )
        flag_mismatches = 0
        for idx, row in merged.iterrows():
            daily_val = row["overcapacity_flag"]
            src_val = row["calc_overcapacity"]
            if pd.isna(daily_val) and pd.isna(src_val):
                continue
            if pd.isna(daily_val) or pd.isna(src_val):
                flag_mismatches += 1
                continue
            if bool(daily_val) != bool(src_val):
                flag_mismatches += 1

        status = "Passed" if flag_mismatches == 0 else "Failed"
        records.append({
            "integration_run_id": self.integration_run_id,
            "patient_flow_daily_id": "",
            "hospital_id": "",
            "department_id": "",
            "reporting_date": "",
            "reconciliation_domain": "bed",
            "reconciliation_field": "overcapacity_flag",
            "source_calculated_value": "",
            "daily_stored_value": "",
            "difference_value": "",
            "reconciliation_status": status,
            "issue_id": "",
            "checked_datetime": datetime.now(),
        })
        self._add_check("Reconciliation", "processed_patient_flow_daily", "bed_overcapacity_flag", "match", str(flag_mismatches), status, flag_mismatches)

        self.reconciliation_records.extend(records)
        self._audit("Bed Reconciliation Completed", f"Mismatches: {sum(1 for r in records if r['reconciliation_status'] == 'Failed')}")
        return records

    def reconcile_daily_service_schedule(self) -> List[Dict[str, Any]]:
        """Reconcile service-schedule fields between daily and source."""
        s = self.processed_dataframes["processed_service_schedule"].copy()
        daily = self.processed_dataframes["processed_patient_flow_daily"].copy()
        s["reporting_date"] = pd.to_datetime(s["reporting_date"], errors="coerce").dt.strftime("%Y-%m-%d")

        for col in ["cancelled_session_flag", "reduced_session_flag", "extended_session_flag"]:
            if col in s.columns:
                s[col] = s[col].fillna(False).astype(bool)
            else:
                s[col] = False

        planned = s[~s["cancelled_session_flag"]].groupby(["hospital_id", "department_id", "reporting_date"], as_index=False).size().rename(columns={"size": "planned_src"})
        cancelled = s[s["cancelled_session_flag"]].groupby(["hospital_id", "department_id", "reporting_date"], as_index=False).size().rename(columns={"size": "cancelled_src"})
        reduced = s[s["reduced_session_flag"]].groupby(["hospital_id", "department_id", "reporting_date"], as_index=False).size().rename(columns={"size": "reduced_src"})
        extended = s[s["extended_session_flag"]].groupby(["hospital_id", "department_id", "reporting_date"], as_index=False).size().rename(columns={"size": "extended_src"})

        merged = daily.merge(planned, on=["hospital_id", "department_id", "reporting_date"], how="left")
        merged = merged.merge(cancelled, on=["hospital_id", "department_id", "reporting_date"], how="left")
        merged = merged.merge(reduced, on=["hospital_id", "department_id", "reporting_date"], how="left")
        merged = merged.merge(extended, on=["hospital_id", "department_id", "reporting_date"], how="left")
        merged = merged.fillna(0)

        records = []
        for field, src_field in [
            ("planned_service_session_count", "planned_src"),
            ("cancelled_service_session_count", "cancelled_src"),
            ("reduced_service_session_count", "reduced_src"),
            ("extended_service_session_count", "extended_src"),
        ]:
            mismatches = (merged[field].astype(int) != merged[src_field].astype(int)).sum()
            status = "Passed" if mismatches == 0 else "Failed"
            records.append({
                "integration_run_id": self.integration_run_id,
                "patient_flow_daily_id": "",
                "hospital_id": "",
                "department_id": "",
                "reporting_date": "",
                "reconciliation_domain": "service",
                "reconciliation_field": field,
                "source_calculated_value": "",
                "daily_stored_value": "",
                "difference_value": "",
                "reconciliation_status": status,
                "issue_id": "",
                "checked_datetime": datetime.now(),
            })
            self._add_check("Reconciliation", "processed_patient_flow_daily", f"service_{field}", "match", str(mismatches), status, mismatches)

        self.reconciliation_records.extend(records)
        self._audit("Service Reconciliation Completed", f"Mismatches: {sum(1 for r in records if r['reconciliation_status'] == 'Failed')}")
        return records

    # -----------------------------------------------------------------------
    # Daily Grain
    # -----------------------------------------------------------------------

    def validate_daily_grain(self) -> List[str]:
        """Validate daily grain uniqueness and identifier consistency."""
        errors = []
        daily = self.processed_dataframes["processed_patient_flow_daily"]
        if daily["patient_flow_daily_id"].duplicated().sum() > 0:
            errors.append("Duplicate patient_flow_daily_id values")
        if daily[["hospital_id", "department_id", "reporting_date"]].duplicated().sum() > 0:
            errors.append("Duplicate daily grain combinations")
        self._audit("Daily Grain Validated", f"Errors: {len(errors)}")
        return errors

    # -----------------------------------------------------------------------
    # Cross-Step Lineage
    # -----------------------------------------------------------------------

    def validate_cross_step_lineage(self) -> List[str]:
        """Validate lineage coverage and integrity."""
        errors = []
        daily = self.processed_dataframes["processed_patient_flow_daily"]
        lineage_path = self.log_directory / "patient_flow_daily_processing_lineage.csv"
        if not lineage_path.exists():
            errors.append("Daily lineage file not found")
            self._add_issue(
                source_dataset_name="",
                issue_type="Missing Lineage",
                severity="Critical",
                description="patient_flow_daily_processing_lineage.csv not found",
            )
            self._audit("Lineage Validated", "Failed: file missing")
            return errors

        lineage = pd.read_csv(lineage_path)
        daily_ids = set(daily["patient_flow_daily_id"])
        lineage_ids = set(lineage["processed_primary_key_value"])

        missing_ids = daily_ids - lineage_ids
        if missing_ids:
            errors.append(f"{len(missing_ids)} daily rows missing lineage")
            self._add_issue(
                source_dataset_name="processed_patient_flow_daily",
                issue_type="Missing Lineage",
                severity="Error",
                description=f"{len(missing_ids)} daily rows missing lineage",
            )

        # Broken references
        broken = lineage["processed_primary_key_value"].isna().sum()
        # Also detect empty strings
        empty_str = (lineage["processed_primary_key_value"].astype(str).str.strip() == "").sum()
        broken_total = int(broken) + int(empty_str)
        if broken_total > 0:
            errors.append(f"{broken_total} lineage records with null or empty processed_primary_key_value")
            self._add_issue(
                source_dataset_name="",
                issue_type="Broken Lineage Reference",
                severity="Error",
                description=f"{broken_total} lineage records with null or empty processed_primary_key_value",
            )

        # Duplicate lineage
        dup_lineage = lineage.duplicated(subset=["processing_run_id", "source_dataset_name", "processed_primary_key_value"]).sum()
        if dup_lineage > 0:
            errors.append(f"{dup_lineage} duplicate lineage records")
            self._add_issue(
                source_dataset_name="",
                issue_type="Duplicate Lineage",
                severity="Warning",
                description=f"{dup_lineage} duplicate lineage records",
            )

        # Lineage summary
        coverage_pct = len(lineage_ids) / len(daily_ids) * 100 if daily_ids else 0
        self.lineage_summary.append({
            "processed_dataset_name": "processed_patient_flow_daily",
            "processed_record_count": len(daily),
            "records_with_lineage": len(lineage_ids),
            "records_without_lineage": len(missing_ids),
            "lineage_coverage_percentage": round(coverage_pct, 2),
            "unique_source_datasets": ",".join(lineage["source_dataset_name"].unique().tolist()) if not lineage.empty else "",
            "unique_transformation_rules": ",".join(lineage["transformation_rule_id"].unique().tolist()) if not lineage.empty else "",
            "broken_reference_count": broken,
            "duplicate_lineage_count": dup_lineage,
            "status": "Passed" if not missing_ids and not broken else "Failed",
        })

        self._audit("Lineage Validated", f"Coverage: {coverage_pct:.1f}%, Missing: {len(missing_ids)}, Broken: {broken}, Duplicates: {dup_lineage}")
        return errors

    def detect_lineage_gaps(self) -> List[Dict[str, Any]]:
        """Detect and report lineage gaps."""
        daily = self.processed_dataframes["processed_patient_flow_daily"]
        lineage_path = self.log_directory / "patient_flow_daily_processing_lineage.csv"
        gaps = []
        if lineage_path.exists():
            lineage = pd.read_csv(lineage_path)
            daily_ids = set(daily["patient_flow_daily_id"])
            lineage_ids = set(lineage["processed_primary_key_value"])
            missing = daily_ids - lineage_ids
            for daily_id in missing:
                gaps.append({
                    "integration_run_id": self.integration_run_id,
                    "processed_dataset_name": "processed_patient_flow_daily",
                    "processed_primary_key_value": daily_id,
                    "gap_type": "Missing Lineage",
                    "description": "Daily row has no lineage record",
                    "detected_datetime": datetime.now(),
                })
        self.lineage_gaps = gaps
        self._audit("Lineage Gaps Detected", f"{len(gaps)} gaps")
        return gaps

    # -----------------------------------------------------------------------
    # Issue Consolidation
    # -----------------------------------------------------------------------

    def consolidate_issues(self) -> pd.DataFrame:
        """Consolidate issues from all three prior steps."""
        issue_files = [
            "patient_encounter_processing_issue_log.csv",
            "queue_capacity_schedule_processing_issue_log.csv",
            "patient_flow_daily_processing_issue_log.csv",
        ]
        parts = []
        for f in issue_files:
            path = self.log_directory / f
            if path.exists():
                df = pd.read_csv(path)
                parts.append(df)
        if parts:
            consolidated = pd.concat(parts, ignore_index=True)
        else:
            consolidated = pd.DataFrame(columns=["issue_id", "processing_run_id", "source_dataset_name", "issue_type", "severity", "issue_description"])
        self._audit("Issues Consolidated", f"{len(consolidated)} total issues")
        return consolidated

    # -----------------------------------------------------------------------
    # Exclusion Consolidation
    # -----------------------------------------------------------------------

    def consolidate_exclusions(self) -> pd.DataFrame:
        """Consolidate exclusion records from all three prior steps."""
        exclusion_files = [
            "patient_encounter_processing_exclusion_register.csv",
            "queue_capacity_schedule_processing_exclusion_register.csv",
            "patient_flow_daily_processing_exclusion_register.csv",
        ]
        parts = []
        for f in exclusion_files:
            path = self.log_directory / f
            if path.exists():
                df = pd.read_csv(path)
                parts.append(df)
        if parts:
            consolidated = pd.concat(parts, ignore_index=True)
        else:
            consolidated = pd.DataFrame(columns=["exclusion_id", "processing_run_id", "source_dataset_name", "exclusion_reason_code"])
        self._audit("Exclusions Consolidated", f"{len(consolidated)} total exclusions")
        return consolidated

    # -----------------------------------------------------------------------
    # Prohibited Field Check
    # -----------------------------------------------------------------------

    def check_prohibited_fields(self) -> List[str]:
        """Check that no prohibited analytical fields exist across datasets."""
        errors = []
        for ds_name, df in self.processed_dataframes.items():
            for col in df.columns:
                col_lower = col.lower()
                for pattern in PROHIBITED_FIELD_PATTERNS:
                    if pattern == col_lower:
                        errors.append(f"{ds_name}: prohibited field '{col}'")
                        self._add_issue(
                            source_dataset_name=ds_name,
                            issue_type="Prohibited Analytical Field",
                            severity="Error",
                            description=f"Prohibited field '{col}' found in {ds_name}",
                        )
        self._audit("Prohibited Fields Checked", f"Violations: {len(errors)}")
        return errors

    # -----------------------------------------------------------------------
    # Integration Summary
    # -----------------------------------------------------------------------

    def build_integration_summary(self) -> Dict[str, Any]:
        """Build the integration summary."""
        issue_counts = {}
        for i in self.issues:
            issue_counts[i.severity] = issue_counts.get(i.severity, 0) + 1

        return {
            "integration_run_id": self.integration_run_id,
            "integration_started_datetime": self.audit_events[0]["timestamp"] if self.audit_events else datetime.now().isoformat(),
            "integration_completed_datetime": datetime.now().isoformat(),
            "engine_version": ENGINE_VERSION,
            "integration_version": INTEGRATION_VERSION,
            "prior_processing_run_ids": {k: v.get("processing_run_id", "") for k, v in self.prior_manifests.items()},
            "validation_run_ids": {k: v.get("validation_run_id", "") for k, v in self.prior_manifests.items()},
            "processed_datasets_checked": list(PROCESSED_DATASETS.keys()),
            "processed_dataset_row_counts": {k: len(v) for k, v in self.processed_dataframes.items()},
            "manifest_verification_results": "Passed" if all(v.get("run_status") in ("success", "Completed") for v in self.prior_manifests.values()) else "Failed",
            "checksum_verification_results": "Passed",  # Updated during run
            "schema_results": "Passed" if not any(i.issue_type == "Schema Mismatch" for i in self.issues) else "Failed",
            "business_key_results": "Passed" if not any(i.issue_type == "Duplicate Business Key" for i in self.issues) else "Failed",
            "daily_grain_result": "Passed" if not any(i.issue_type == "Invalid Daily Grain" for i in self.issues) else "Failed",
            "reconciliation_results": "Passed" if not any(r["reconciliation_status"] == "Failed" for r in self.reconciliation_records) else "Failed",
            "lineage_results": "Passed" if not any(i.issue_type in ("Missing Lineage", "Broken Lineage Reference") for i in self.issues) else "Failed",
            "issue_counts_by_severity": issue_counts,
            "exclusion_counts": 0,  # Updated during run
            "prohibited_field_check": "Passed" if not any(i.issue_type == "Prohibited Analytical Field" for i in self.issues) else "Failed",
            "run_status": "Passed" if not any(i.severity in ("Error", "Critical") for i in self.issues) else "Failed",
            "integration_passed_flag": not any(i.severity in ("Error", "Critical") for i in self.issues),
            "output_files": [],
            "unresolved_rules": ["Pending Review"],
            "known_limitations": [
                "Queue aggregation relies on explicit summary_source_flag.",
                "Duplicate bed snapshots are not resolved.",
            ],
            "readiness_for_next_step": "Step 2D-3E will run cumulative regression testing, verify final patient-flow processing acceptance criteria and formally close Step 2D-3. Step 2D-3E will not calculate official KPI values or KPI status.",
        }

    def return_integration_result(self) -> Dict[str, Any]:
        """Return the full integration result."""
        return {
            "success": True,
            "integration_run_id": self.integration_run_id,
            "issues": self.issues,
            "check_results": self.check_results,
            "reconciliation_records": self.reconciliation_records,
            "lineage_summary": self.lineage_summary,
            "lineage_gaps": self.lineage_gaps,
            "exclusion_summary": self.exclusion_summary,
            "audit_events": self.audit_events,
            "dataset_checksums": self.dataset_checksums,
        }

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _file_checksum(self, file_path: Path) -> str:
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def _audit(self, event: str, detail: str) -> None:
        self.audit_events.append({
            "integration_run_id": self.integration_run_id,
            "event": event,
            "detail": detail,
            "timestamp": datetime.now().isoformat(),
        })

    def _add_issue(
        self,
        source_dataset_name: str,
        issue_type: str,
        severity: str,
        description: str,
    ) -> None:
        issue = ProcessingIssue(
            processing_run_id=self.integration_run_id,
            issue_id=str(uuid.uuid4()),
            source_dataset_name=source_dataset_name,
            processed_dataset_name="",
            source_primary_key="",
            source_row_number=0,
            field_name="",
            issue_type=issue_type,
            severity=severity,
            issue_description=description,
            source_value="",
            processed_value="",
            resolution_action="",
            exclusion_flag=False,
            blocks_processing=severity in ("Error", "Critical"),
        )
        self.issues.append(issue)

    def _add_check(
        self,
        category: str,
        dataset_name: str,
        check_name: str,
        expected: str,
        actual: str,
        status: str,
        affected_count: int,
    ) -> None:
        self.check_results.append({
            "integration_run_id": self.integration_run_id,
            "check_id": str(uuid.uuid4()),
            "check_category": category,
            "dataset_name": dataset_name,
            "check_name": check_name,
            "expected_result": expected,
            "actual_result": actual,
            "status": status,
            "severity": "Warning" if status == "Failed" else "Information",
            "affected_record_count": affected_count,
            "evidence_reference": "",
            "checked_datetime": datetime.now(),
        })
