"""
Sentinel360 Healthcare — Patient Flow Daily Builder

Builds processed_patient_flow_daily.csv from the four processed inputs:
- processed_patient_encounters
- processed_patient_queue
- processed_bed_capacity
- processed_service_schedule

Step: 2D-3C
"""

import hashlib
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

from src.processed_schema_registry import get_processed_schema
from src.processing_contracts import ValidationGateResult
from src.processing_models import (
    ProcessingDatasetResult,
    ProcessingExclusionRecord,
    ProcessingIssue,
    ProcessingLineageRecord,
)

TRANSFORMATION_VERSION = "2D-3C-1.0.0"
ENGINE_VERSION = "Sentinel360-Phase1-2D-3C"

INPUT_DATASETS = {
    "processed_patient_encounters": {
        "file_name": "processed_patient_encounters.csv",
        "primary_key": "encounter_id",
        "grain_keys": ["hospital_id", "department_id", "reporting_date"],
    },
    "processed_patient_queue": {
        "file_name": "processed_patient_queue.csv",
        "primary_key": "queue_record_id",
        "grain_keys": ["hospital_id", "department_id", "reporting_date"],
    },
    "processed_bed_capacity": {
        "file_name": "processed_bed_capacity.csv",
        "primary_key": "bed_capacity_record_id",
        "grain_keys": ["hospital_id", "department_id", "reporting_date"],
    },
    "processed_service_schedule": {
        "file_name": "processed_service_schedule.csv",
        "primary_key": "service_schedule_id",
        "grain_keys": ["hospital_id", "department_id", "reporting_date"],
    },
}


class PatientFlowDailyBuilder:
    """Builder for daily patient-flow preparation dataset."""

    def __init__(
        self,
        processing_run_id: str,
        validation_run_id: str,
        input_directory: Path,
        output_directory: Path,
        log_directory: Path,
        source_type: str = "processed_synthetic_demo",
        collect_lineage: bool = True,
        max_issue_examples: int = 1000,
    ):
        self.processing_run_id = processing_run_id
        self.validation_run_id = validation_run_id
        self.input_directory = input_directory
        self.output_directory = output_directory
        self.log_directory = log_directory
        self.source_type = source_type
        self.collect_lineage = collect_lineage
        self.max_issue_examples = max_issue_examples
        self.issues: List[ProcessingIssue] = []
        self.lineage_records: List[ProcessingLineageRecord] = []
        self.exclusion_records: List[ProcessingExclusionRecord] = []
        self.audit_events: List[Dict[str, Any]] = []
        self.dataset_results: List[ProcessingDatasetResult] = []
        self.input_checksums: Dict[str, str] = {}
        self.input_record_counts: Dict[str, int] = {}
        self.prior_run_ids: Dict[str, str] = {}

    def check_input_manifests(self) -> ValidationGateResult:
        """Evaluate whether processing is permitted based on prior run manifests."""
        manifest_files = {
            "patient_encounter": self.log_directory / "patient_encounter_processing_run_manifest.json",
            "queue_capacity_schedule": self.log_directory / "queue_capacity_schedule_processing_run_manifest.json",
        }

        all_passed = True
        blocking_reasons = []

        for name, manifest_path in manifest_files.items():
            if not manifest_path.exists():
                all_passed = False
                blocking_reasons.append(f"{name} processing manifest not found.")
                continue

            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
            except Exception as e:
                all_passed = False
                blocking_reasons.append(f"{name} manifest unreadable: {e}")
                continue

            run_status = manifest.get("run_status", "")
            if run_status not in ("success", "Completed"):
                all_passed = False
                blocking_reasons.append(f"{name} run_status was '{run_status}', not 'success'.")
                continue

            proc_allowed = manifest.get("processing_allowed_flag", True)
            if proc_allowed is False:
                all_passed = False
                blocking_reasons.append(f"{name} processing_allowed_flag was False.")
                continue

            self.prior_run_ids[name] = manifest.get("processing_run_id", "")

        if all_passed:
            result = ValidationGateResult(
                processing_allowed=True,
                blocking_reason="",
                validation_run_id=self.validation_run_id,
            )
            self._audit("Input Manifests Verified", "All prior manifests passed")
        else:
            result = ValidationGateResult(
                processing_allowed=False,
                blocking_reason="; ".join(blocking_reasons),
                validation_run_id=self.validation_run_id,
            )
            self._audit("Input Manifests Verified", f"Blocked — {'; '.join(blocking_reasons)}")

        return result

    def load_processed_inputs(self) -> Dict[str, pd.DataFrame]:
        """Load the four processed datasets from input directory."""
        loaded: Dict[str, pd.DataFrame] = {}
        for ds_name, config in INPUT_DATASETS.items():
            file_path = self.input_directory / config["file_name"]
            if not file_path.exists():
                raise FileNotFoundError(f"Processed input not found: {file_path}")
            df = pd.read_csv(file_path)
            loaded[ds_name] = df
            self.input_checksums[ds_name] = self._file_checksum(file_path)
            self.input_record_counts[ds_name] = len(df)
            self._audit(f"{ds_name} Loaded", f"{len(df)} rows")
        return loaded

    def verify_input_checksums(self) -> bool:
        """Re-verify that processed input files have not changed since loading."""
        for ds_name, config in INPUT_DATASETS.items():
            file_path = self.input_directory / config["file_name"]
            if not file_path.exists():
                self._audit("Input Checksum Verification", f"{ds_name} missing")
                return False
            current = self._file_checksum(file_path)
            expected = self.input_checksums.get(ds_name)
            if expected is None:
                continue
            if current != expected:
                self._add_issue(
                    source_dataset_name=ds_name,
                    processed_dataset_name="processed_patient_flow_daily",
                    source_primary_key="",
                    source_row_number=0,
                    field_name="",
                    issue_type="Input Manifest Mismatch",
                    severity="Critical",
                    issue_description=f"Checksum mismatch for {ds_name}: expected {expected}, got {current}",
                    source_value="",
                    exclusion_flag=False,
                    blocks_processing=True,
                )
                self._audit("Input Checksum Verification", f"{ds_name} checksum mismatch")
                return False
        self._audit("Input Checksums Confirmed", "All match")
        return True

    def validate_input_schemas(self, inputs: Dict[str, pd.DataFrame]) -> List[str]:
        """Validate that each processed input conforms to its schema."""
        errors = []
        for ds_name, df in inputs.items():
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
                    processed_dataset_name="processed_patient_flow_daily",
                    source_primary_key="",
                    source_row_number=0,
                    field_name="",
                    issue_type="Input Schema Failure",
                    severity="Error",
                    issue_description=err,
                    source_value="",
                    exclusion_flag=False,
                    blocks_processing=True,
                )
            self._audit("Input Schema Validation", f"Failed: {len(errors)} errors")
        else:
            self._audit("Input Schemas Validated", "All passed")
        return errors

    def build_daily_spine(self, inputs: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Create daily spine from union of valid grain keys across all inputs."""
        grain_cols = ["hospital_id", "department_id", "reporting_date"]
        parts = []
        for ds_name, df in inputs.items():
            if not all(c in df.columns for c in grain_cols):
                continue
            sub = df[grain_cols].copy()
            sub["reporting_date"] = pd.to_datetime(sub["reporting_date"], errors="coerce").dt.strftime("%Y-%m-%d")
            sub = sub.dropna(subset=grain_cols)
            sub = sub.drop_duplicates()
            parts.append(sub)

        if not parts:
            spine = pd.DataFrame(columns=grain_cols)
        else:
            spine = pd.concat(parts, ignore_index=True).drop_duplicates()

        spine["reporting_month"] = pd.to_datetime(spine["reporting_date"], errors="coerce").dt.strftime("%Y-%m")
        spine = spine.dropna(subset=grain_cols + ["reporting_month"])

        self._audit("Daily Spine Created", f"{len(spine)} rows")
        return spine

    def aggregate_encounters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate encounter preparation fields to daily grain."""
        keys = ["hospital_id", "department_id", "reporting_date"]
        df = df.copy()
        df["reporting_date"] = pd.to_datetime(df["reporting_date"], errors="coerce").dt.strftime("%Y-%m-%d")
        df = df.dropna(subset=keys)

        bool_cols = ["completed_service_flag", "cancelled_flag", "left_before_service_flag", "official_wait_stage_eligible_flag"]
        for col in bool_cols:
            if col in df.columns:
                df[col] = df[col].fillna(False).astype(bool)
            else:
                df[col] = False

        if "arrival_to_consultation_minutes" in df.columns:
            df["arrival_to_consultation_minutes"] = pd.to_numeric(df["arrival_to_consultation_minutes"], errors="coerce")
        else:
            df["arrival_to_consultation_minutes"] = np.nan

        agg = df.groupby(keys, as_index=False).agg(
            encounter_count=("encounter_id", "size"),
            completed_encounter_count=("completed_service_flag", "sum"),
            cancelled_encounter_count=("cancelled_flag", "sum"),
            left_before_service_count=("left_before_service_flag", "sum"),
            official_wait_eligible_encounter_count=("official_wait_stage_eligible_flag", "sum"),
        )

        eligible = df[
            df["official_wait_stage_eligible_flag"].eq(True)
            & df["arrival_to_consultation_minutes"].notna()
            & df["arrival_to_consultation_minutes"].ge(0)
        ]
        wait_sum = eligible.groupby(keys, as_index=False)["arrival_to_consultation_minutes"].sum()
        wait_sum = wait_sum.rename(columns={"arrival_to_consultation_minutes": "total_arrival_to_consultation_minutes"})
        wait_sum = wait_sum[wait_sum["total_arrival_to_consultation_minutes"] > 0]

        agg = agg.merge(wait_sum, on=keys, how="left")
        agg["total_arrival_to_consultation_minutes"] = agg["total_arrival_to_consultation_minutes"].replace({0: np.nan})

        count_cols = [
            "encounter_count", "completed_encounter_count", "cancelled_encounter_count",
            "left_before_service_count", "official_wait_eligible_encounter_count",
        ]
        for col in count_cols:
            agg[col] = agg[col].fillna(0).astype(int)

        self._audit("Encounter Aggregation Completed", f"{len(agg)} daily groups")
        return agg

    def aggregate_queue(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate queue preparation fields to daily grain without double counting."""
        keys = ["hospital_id", "department_id", "reporting_date"]
        df = df.copy()
        df["reporting_date"] = pd.to_datetime(df["reporting_date"], errors="coerce").dt.strftime("%Y-%m-%d")
        df = df.dropna(subset=keys)

        if "summary_source_flag" in df.columns:
            df["summary_source_flag"] = df["summary_source_flag"].map({
                True: True, False: False, "True": True, "False": False, 1: True, 0: False, "1": True, "0": False
            })
            df["summary_source_flag"] = df["summary_source_flag"].astype("boolean")
        else:
            df["summary_source_flag"] = pd.array([pd.NA] * len(df), dtype="boolean")

        result_rows = []
        for grp_keys, grp in df.groupby(keys):
            row = dict(zip(keys, grp_keys))
            if len(grp) == 1:
                rec = grp.iloc[0]
                row["queue_arrivals_count"] = self._safe_numeric(rec, "arrivals_count")
                row["queue_served_count"] = self._safe_numeric(rec, "served_count")
                row["queue_waiting_patient_count"] = self._safe_numeric(rec, "waiting_patient_count")
                row["queue_average_wait_minutes"] = self._safe_numeric(rec, "average_wait_minutes")
            elif grp["summary_source_flag"].eq(True).any():
                summary = grp[grp["summary_source_flag"].eq(True)].iloc[0]
                row["queue_arrivals_count"] = self._safe_numeric(summary, "arrivals_count")
                row["queue_served_count"] = self._safe_numeric(summary, "served_count")
                row["queue_waiting_patient_count"] = self._safe_numeric(summary, "waiting_patient_count")
                row["queue_average_wait_minutes"] = self._safe_numeric(summary, "average_wait_minutes")
            else:
                row["queue_arrivals_count"] = np.nan
                row["queue_served_count"] = np.nan
                row["queue_waiting_patient_count"] = np.nan
                row["queue_average_wait_minutes"] = np.nan
                self._add_issue(
                    source_dataset_name="processed_patient_queue",
                    processed_dataset_name="processed_patient_flow_daily",
                    source_primary_key="",
                    source_row_number=0,
                    field_name="queue_stage",
                    issue_type="Ambiguous Queue Aggregation",
                    severity="Warning",
                    issue_description=f"Multiple queue stages without approved summary for {grp_keys}. Rule: Pending Review.",
                    source_value=",".join(grp["queue_stage"].astype(str).tolist()),
                    exclusion_flag=False,
                    blocks_processing=False,
                )
            result_rows.append(row)

        if not result_rows:
            agg = pd.DataFrame(columns=keys + [
                "queue_arrivals_count", "queue_served_count",
                "queue_waiting_patient_count", "queue_average_wait_minutes"
            ])
        else:
            agg = pd.DataFrame(result_rows)

        self._audit("Queue Aggregation Completed", f"{len(agg)} daily groups")
        return agg

    def aggregate_bed_capacity(self, df: pd.DataFrame) -> pd.DataFrame:
        """Select or aggregate bed-capacity records to daily grain."""
        keys = ["hospital_id", "department_id", "reporting_date"]
        df = df.copy()
        df["reporting_date"] = pd.to_datetime(df["reporting_date"], errors="coerce").dt.strftime("%Y-%m-%d")
        df = df.dropna(subset=keys)

        result_rows = []
        for grp_keys, grp in df.groupby(keys):
            row = dict(zip(keys, grp_keys))
            if len(grp) == 1:
                rec = grp.iloc[0]
                for col in ["licensed_beds", "staffed_beds", "operational_beds", "occupied_beds",
                            "unavailable_beds", "reserved_beds"]:
                    row[col] = self._safe_numeric(rec, col)
                row["beds_above_operational_capacity"] = max(
                    (row.get("occupied_beds", 0) or 0) - (row.get("operational_beds", 0) or 0), 0
                )
                occ = row.get("occupied_beds", np.nan)
                op = row.get("operational_beds", np.nan)
                if pd.notna(occ) and pd.notna(op):
                    row["overcapacity_flag"] = bool(occ > op)
                else:
                    row["overcapacity_flag"] = pd.NA
            else:
                for col in ["licensed_beds", "staffed_beds", "operational_beds", "occupied_beds",
                            "unavailable_beds", "reserved_beds", "beds_above_operational_capacity", "overcapacity_flag"]:
                    row[col] = np.nan
                self._add_issue(
                    source_dataset_name="processed_bed_capacity",
                    processed_dataset_name="processed_patient_flow_daily",
                    source_primary_key="",
                    source_row_number=0,
                    field_name="bed_capacity_record_id",
                    issue_type="Duplicate Capacity Snapshot",
                    severity="Warning",
                    issue_description=f"Duplicate bed snapshots for {grp_keys} without approved selection rule. Fields set to null.",
                    source_value=str(len(grp)),
                    exclusion_flag=False,
                    blocks_processing=False,
                )
            result_rows.append(row)

        if not result_rows:
            agg = pd.DataFrame(columns=keys + [
                "licensed_beds", "staffed_beds", "operational_beds", "occupied_beds",
                "unavailable_beds", "reserved_beds", "beds_above_operational_capacity", "overcapacity_flag"
            ])
        else:
            agg = pd.DataFrame(result_rows)

        self._audit("Bed Aggregation Completed", f"{len(agg)} daily groups")
        return agg

    def aggregate_service_schedule(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate service-schedule preparation fields to daily grain."""
        keys = ["hospital_id", "department_id", "reporting_date"]
        df = df.copy()
        df["reporting_date"] = pd.to_datetime(df["reporting_date"], errors="coerce").dt.strftime("%Y-%m-%d")
        df = df.dropna(subset=keys)

        for col in ["cancelled_session_flag", "reduced_session_flag", "extended_session_flag"]:
            if col in df.columns:
                df[col] = df[col].fillna(False).astype(bool)
            else:
                df[col] = False

        planned = df[~df["cancelled_session_flag"]].copy()
        planned_agg = planned.groupby(keys, as_index=False).size().rename(columns={"size": "planned_service_session_count"})

        cancelled_agg = df[df["cancelled_session_flag"]].groupby(keys, as_index=False).size().rename(columns={"size": "cancelled_service_session_count"})
        reduced_agg = df[df["reduced_session_flag"]].groupby(keys, as_index=False).size().rename(columns={"size": "reduced_service_session_count"})
        extended_agg = df[df["extended_session_flag"]].groupby(keys, as_index=False).size().rename(columns={"size": "extended_service_session_count"})

        agg = planned_agg.merge(cancelled_agg, on=keys, how="outer")
        agg = agg.merge(reduced_agg, on=keys, how="outer")
        agg = agg.merge(extended_agg, on=keys, how="outer")
        agg = agg.fillna(0)
        for col in ["planned_service_session_count", "cancelled_service_session_count",
                    "reduced_service_session_count", "extended_service_session_count"]:
            agg[col] = agg[col].astype(int)

        self._audit("Service Aggregation Completed", f"{len(agg)} daily groups")
        return agg

    def combine_daily_components(
        self,
        spine: pd.DataFrame,
        encounters: pd.DataFrame,
        queue: pd.DataFrame,
        bed: pd.DataFrame,
        service: pd.DataFrame,
    ) -> pd.DataFrame:
        """Merge all daily components onto the spine."""
        keys = ["hospital_id", "department_id", "reporting_date"]
        daily = spine.copy()

        daily = daily.merge(encounters, on=keys, how="left")
        daily = daily.merge(queue, on=keys, how="left")
        daily = daily.merge(bed, on=keys, how="left")
        daily = daily.merge(service, on=keys, how="left")

        count_cols = [
            "encounter_count", "completed_encounter_count", "cancelled_encounter_count",
            "left_before_service_count", "official_wait_eligible_encounter_count",
            "planned_service_session_count", "cancelled_service_session_count",
            "reduced_service_session_count", "extended_service_session_count",
        ]
        for col in count_cols:
            if col in daily.columns:
                daily[col] = daily[col].fillna(0).astype(int)
            else:
                daily[col] = 0

        self._audit("Daily Components Combined", f"{len(daily)} rows")
        return daily

    def create_daily_identifier(self, daily: pd.DataFrame) -> pd.DataFrame:
        """Create deterministic patient_flow_daily_id."""
        daily = daily.copy()
        daily["patient_flow_daily_id"] = (
            "PFD-" + daily["hospital_id"].astype(str) + "-"
            + daily["department_id"].astype(str) + "-"
            + daily["reporting_date"].astype(str).str.replace("-", "", regex=False)
        )
        self._audit("Daily Identifiers Created", f"{len(daily)} IDs")
        return daily

    def validate_daily_schema(self, daily: pd.DataFrame) -> List[str]:
        """Validate final daily dataframe against schema registry."""
        schema = get_processed_schema("processed_patient_flow_daily")
        if schema is None:
            return ["Schema not found for processed_patient_flow_daily"]

        errors = []
        required = schema.get("required_fields", [])
        for field in required:
            if field not in daily.columns:
                errors.append(f"Missing required field '{field}'")

        for field in schema.get("numeric_fields", []):
            if field in daily.columns:
                if not pd.api.types.is_numeric_dtype(daily[field]):
                    errors.append(f"Field '{field}' is not numeric")

        for field in schema.get("boolean_fields", []):
            if field in daily.columns:
                if not (pd.api.types.is_bool_dtype(daily[field]) or pd.api.types.is_object_dtype(daily[field])):
                    errors.append(f"Field '{field}' is not boolean")

        if errors:
            for err in errors:
                self._add_issue(
                    source_dataset_name="",
                    processed_dataset_name="processed_patient_flow_daily",
                    source_primary_key="",
                    source_row_number=0,
                    field_name="",
                    issue_type="Processed Schema Failure",
                    severity="Error",
                    issue_description=err,
                    source_value="",
                    exclusion_flag=False,
                    blocks_processing=True,
                )
            self._audit("Processed Schema Validated", f"Failed: {len(errors)} errors")
        else:
            self._audit("Processed Schema Validated", "Passed")
        return errors

    def build_lineage(
        self,
        inputs: Dict[str, pd.DataFrame],
        daily: pd.DataFrame,
    ) -> pd.DataFrame:
        """Build lineage records for every daily row from contributing domains."""
        if not self.collect_lineage:
            return pd.DataFrame()

        keys = ["hospital_id", "department_id", "reporting_date"]
        records = []

        for idx, row in daily.iterrows():
            daily_id = row["patient_flow_daily_id"]
            hosp = row["hospital_id"]
            dept = row["department_id"]
            rep_date = row["reporting_date"]

            for ds_name, df in inputs.items():
                if not all(k in df.columns for k in keys):
                    continue
                df_sub = df.copy()
                df_sub["reporting_date"] = pd.to_datetime(df_sub["reporting_date"], errors="coerce").dt.strftime("%Y-%m-%d")
                contributors = df_sub[
                    df_sub["hospital_id"].eq(hosp)
                    & df_sub["department_id"].eq(dept)
                    & df_sub["reporting_date"].eq(rep_date)
                ]
                if contributors.empty:
                    continue

                pk_field = INPUT_DATASETS[ds_name]["primary_key"]
                pk_values = contributors[pk_field].astype(str).tolist() if pk_field in contributors.columns else []

                rule_map = {
                    "processed_patient_encounters": "TR_PFD_ENCOUNTER_AGGREGATION",
                    "processed_patient_queue": "TR_PFD_QUEUE_AGGREGATION",
                    "processed_bed_capacity": "TR_PFD_BED_SELECTION",
                    "processed_service_schedule": "TR_PFD_SERVICE_AGGREGATION",
                }

                lineage_id = str(uuid.uuid4())
                rec = ProcessingLineageRecord(
                    processing_run_id=self.processing_run_id,
                    lineage_id=lineage_id,
                    validation_run_id=self.validation_run_id,
                    source_dataset_name=ds_name,
                    source_file_name=INPUT_DATASETS[ds_name]["file_name"],
                    source_primary_key_field=pk_field,
                    source_primary_key_value=";".join(pk_values[:10]) + (";..." if len(pk_values) > 10 else ""),
                    source_row_number=0,
                    processed_dataset_name="processed_patient_flow_daily",
                    processed_primary_key_field="patient_flow_daily_id",
                    processed_primary_key_value=str(daily_id),
                    transformation_rule_id=rule_map.get(ds_name, "TR_PFD_DAILY_SPINE"),
                    transformation_description=f"Daily aggregation from {ds_name}",
                    source_fields_used=",".join(contributors.columns.tolist()),
                    processed_fields_created=",".join(daily.columns.tolist()),
                    exclusion_flag=False,
                    exclusion_reason_code="",
                    transformation_version=TRANSFORMATION_VERSION,
                    configuration_version=ENGINE_VERSION,
                    processed_datetime=datetime.now(),
                )
                records.append(rec)
                self.lineage_records.append(rec)

        if not records:
            df = pd.DataFrame(columns=list(ProcessingLineageRecord.to_dict(ProcessingLineageRecord()).keys()))
        else:
            df = pd.DataFrame([r.to_dict() for r in records])
        self._audit("Lineage Generated", f"{len(df)} records")
        return df

    def build_exclusions(self) -> pd.DataFrame:
        """Return exclusion register as DataFrame."""
        if not self.exclusion_records:
            # Use a dummy instance to get column names
            dummy = ProcessingExclusionRecord(
                processing_run_id="",
                exclusion_id="",
                source_dataset_name="",
                source_primary_key_field="",
                source_primary_key_value="",
                source_row_number=0,
                exclusion_reason_code="",
                exclusion_reason_description="",
                validation_issue_id="",
                manual_override_id="",
                exclusion_stage="",
                excluded_by_rule="",
                reversible_flag=False,
                created_datetime=datetime.now(),
            )
            return pd.DataFrame(columns=list(dummy.to_dict().keys()))
        df = pd.DataFrame([r.to_dict() for r in self.exclusion_records])
        self._audit("Exclusion Register Generated", f"{len(df)} records")
        return df

    def collect_issues(self) -> pd.DataFrame:
        """Return issues as DataFrame."""
        if not self.issues:
            dummy = ProcessingIssue(
                processing_run_id="",
                issue_id="",
                source_dataset_name="",
                processed_dataset_name="",
                source_primary_key="",
                source_row_number=0,
                field_name="",
                issue_type="",
                severity="",
                issue_description="",
                source_value="",
                processed_value="",
                resolution_action="",
                exclusion_flag=False,
                blocks_processing=False,
            )
            return pd.DataFrame(columns=list(dummy.to_dict().keys()))
        df = pd.DataFrame([i.to_dict() for i in self.issues])
        self._audit("Issues Collected", f"{len(df)} issues")
        return df

    def return_build_result(
        self,
        daily_df: pd.DataFrame,
    ) -> Dict[str, Any]:
        """Return the full build result."""
        dataset_result = ProcessingDatasetResult(
            processing_run_id=self.processing_run_id,
            validation_run_id=self.validation_run_id,
            source_dataset_name="combined_processed_inputs",
            processed_dataset_name="processed_patient_flow_daily",
            source_row_count=sum(self.input_record_counts.values()),
            processed_row_count=len(daily_df),
            excluded_row_count=len(self.exclusion_records),
            transformed_field_count=len(daily_df.columns),
            warning_count=sum(1 for i in self.issues if i.severity == "Warning"),
            error_count=sum(1 for i in self.issues if i.severity == "Error"),
            dataset_status="Processed",
            output_file_name="processed_patient_flow_daily.csv",
            transformation_version=TRANSFORMATION_VERSION,
            processed_datetime=datetime.now(),
        )
        self.dataset_results.append(dataset_result)

        return {
            "daily_dataframe": daily_df,
            "issues": self.issues,
            "lineage_records": self.lineage_records,
            "exclusion_records": self.exclusion_records,
            "audit_events": self.audit_events,
            "dataset_results": self.dataset_results,
            "dataset_result": dataset_result,
            "input_checksums": self.input_checksums,
            "success_flag": True,
        }

    def _file_checksum(self, file_path: Path) -> str:
        """Compute SHA-256 checksum of a file."""
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def _audit(self, event: str, detail: str) -> None:
        """Add an audit event."""
        self.audit_events.append({
            "processing_run_id": self.processing_run_id,
            "event": event,
            "detail": detail,
            "timestamp": datetime.now().isoformat(),
        })

    def _add_issue(
        self,
        source_dataset_name: str,
        processed_dataset_name: str,
        source_primary_key: str,
        source_row_number: int,
        field_name: str,
        issue_type: str,
        severity: str,
        issue_description: str,
        source_value: str,
        exclusion_flag: bool = False,
        blocks_processing: bool = False,
    ) -> None:
        """Add a single ProcessingIssue."""
        issue = ProcessingIssue(
            processing_run_id=self.processing_run_id,
            issue_id=str(uuid.uuid4()),
            source_dataset_name=source_dataset_name,
            processed_dataset_name=processed_dataset_name,
            source_primary_key=source_primary_key,
            source_row_number=source_row_number,
            field_name=field_name,
            issue_type=issue_type,
            severity=severity,
            issue_description=issue_description,
            source_value=str(source_value) if source_value is not None else "",
            processed_value="",
            resolution_action="",
            exclusion_flag=exclusion_flag,
            blocks_processing=blocks_processing,
        )
        self.issues.append(issue)

    def _safe_numeric(self, row: Any, col: str) -> Any:
        """Safely extract a numeric value from a row."""
        val = row.get(col, np.nan) if hasattr(row, "get") else getattr(row, col, np.nan)
        if pd.isna(val):
            return np.nan
        try:
            return float(val)
        except (ValueError, TypeError):
            return np.nan
