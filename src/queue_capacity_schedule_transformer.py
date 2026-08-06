"""
Sentinel360 Healthcare — Queue, Bed Capacity and Service Schedule Transformer

Transforms patient_queue_records, bed_capacity_records and service_schedule
into processed_patient_queue, processed_bed_capacity and processed_service_schedule.

Step: 2D-3B
"""

import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

from src.processed_schema_registry import get_processed_schema
from src.processing_contracts import ValidationGateResult, TransformationResultContract
from src.processing_models import (
    ProcessingIssue,
    ProcessingLineageRecord,
    ProcessingExclusionRecord,
    ProcessingDatasetResult,
)


TRANSFORMATION_VERSION = "2D-3B-1.0.0"
ENGINE_VERSION = "1.0.0"

SOURCE_DATASETS = {
    "patient_queue_records": {
        "source_file": "patient_queue_records.csv",
        "processed_name": "processed_patient_queue",
        "primary_key": "queue_record_id",
        "source_primary_key": "queue_id",
        "transformation_rule_id": "TR_PF_QUEUE_STANDARDISATION",
        "transformation_description": "Standardise queue stage definitions and counts.",
        "column_map": {
            "queue_id": "queue_record_id",
            "queue_type": "queue_stage",
            "waiting_count": "waiting_patient_count",
            "avg_wait_minutes": "average_wait_minutes",
        },
    },
    "bed_capacity_records": {
        "source_file": "bed_capacity_records.csv",
        "processed_name": "processed_bed_capacity",
        "primary_key": "bed_capacity_record_id",
        "source_primary_key": "record_id",
        "transformation_rule_id": "TR_PF_BED_STANDARDISATION",
        "transformation_description": "Standardise bed capacity fields and exception flags.",
        "column_map": {
            "record_id": "bed_capacity_record_id",
            "record_date": "reporting_date",
            "bed_licensed": "licensed_beds",
            "bed_staffed": "staffed_beds",
            "bed_operational": "operational_beds",
            "bed_occupied": "occupied_beds",
            "bed_unavailable": "unavailable_beds",
            "bed_reserved": "reserved_beds",
            "exception_flag": "overcapacity_exception_flag",
            "exception_reason": "overcapacity_reason",
        },
    },
        "service_schedule": {
        "source_file": "service_schedule.csv",
        "processed_name": "processed_service_schedule",
        "primary_key": "service_schedule_id",
        "source_primary_key": "schedule_id",
        "transformation_rule_id": "TR_PF_SCHEDULE_STANDARDISATION",
        "transformation_description": "Standardise service schedule fields and session flags.",
        "column_map": {
            "schedule_id": "service_schedule_id",
            "planned_start_time": "session_start_datetime",
            "planned_end_time": "session_end_datetime",
            "planned_hours": "planned_service_hours",
            "shift_code": "service_type",
        },
    },
}

EXCLUSION_REASONS: Dict[str, str] = {
    "NEGATIVE_QUEUE_COUNT": "Negative queue count detected.",
    "NEGATIVE_WAIT_VALUE": "Negative wait value detected.",
    "MISSING_QUEUE_STAGE": "Missing mandatory queue stage.",
    "UNSUPPORTED_QUEUE_STAGE": "Queue stage value not in approved categorical list.",
    "NEGATIVE_BED_COUNT": "Negative bed count detected.",
    "INVALID_CAPACITY_RELATIONSHIP": "Invalid capacity relationship detected.",
    "INVALID_SERVICE_DURATION": "Invalid or negative service duration detected.",
    "UNPARSABLE_SERVICE_TIMESTAMP": "Unparseable service session timestamp.",
    "MISSING_SERVICE_TIMESTAMP": "Missing mandatory service session timestamp.",
    "MISSING_MANDATORY_KEY": "Missing mandatory primary key or relationship field.",
    "INVALID_HOSPITAL_DEPARTMENT": "Invalid hospital or department relationship.",
}


class QueueCapacityScheduleTransformer:
    """Transformer for queue, bed capacity and service schedule datasets."""

    def __init__(
        self,
        processing_run_id: str,
        validation_run_id: str,
        input_directory: Path,
        output_directory: Path,
        validation_log_directory: Path,
        source_type: str = "synthetic_demo",
        collect_lineage: bool = True,
        max_issue_examples: int = 1000,
    ):
        self.processing_run_id = processing_run_id
        self.validation_run_id = validation_run_id
        self.input_directory = input_directory
        self.output_directory = output_directory
        self.validation_log_directory = validation_log_directory
        self.source_type = source_type
        self.collect_lineage = collect_lineage
        self.max_issue_examples = max_issue_examples
        self.issues: List[ProcessingIssue] = []
        self.lineage_records: List[ProcessingLineageRecord] = []
        self.exclusion_records: List[ProcessingExclusionRecord] = []
        self.audit_events: List[Dict[str, Any]] = []
        self.dataset_results: List[ProcessingDatasetResult] = []
        self.source_checksums: Dict[str, str] = {}
        self.processed_checksums: Dict[str, str] = {}

    # -----------------------------------------------------------------------
    # Validation Gate
    # -----------------------------------------------------------------------

    def check_validation_gate(self) -> ValidationGateResult:
        """Evaluate whether processing is permitted based on validation outputs."""
        manifest_path = self.validation_log_directory / "validation_run_manifest.json"
        summary_path = self.validation_log_directory / "dataset_validation_summary.csv"
        override_path = self.validation_log_directory / "manual_override_register.csv"

        if not manifest_path.exists():
            result = ValidationGateResult(
                processing_allowed=False,
                blocking_reason="Validation run manifest not found.",
                validation_run_id="",
            )
            self._audit("Validation Gate Checked", "Blocked — manifest missing")
            return result

        import json
        with open(manifest_path, "r", encoding="utf-8") as f:
            validation_manifest = json.load(f)

        dataset_summary = None
        if summary_path.exists():
            dataset_summary = pd.read_csv(summary_path)

        override_register = None
        if override_path.exists():
            override_register = pd.read_csv(override_path)

        from src.processing_contracts import ValidationGateContract
        result = ValidationGateContract.check_validation_gate(
            validation_manifest=validation_manifest,
            dataset_summary=dataset_summary,
            override_register=override_register,
        )

        # Additional dataset-specific checks for our three sources
        if result.processing_allowed and dataset_summary is not None:
            required_datasets = ["patient_queue_records", "bed_capacity_records", "service_schedule"]
            accepted = set(result.accepted_datasets)
            excluded = []
            for ds in required_datasets:
                if ds not in accepted:
                    # Check for approved override
                    if override_register is not None and not override_register.empty:
                        ds_overrides = override_register[override_register.get("dataset_name", pd.Series([], dtype=str)) == ds]
                        if not ds_overrides.empty and ds_overrides.get("override_approved", pd.Series([], dtype=bool)).any():
                            continue
                    excluded.append(ds)
            if excluded:
                result.processing_allowed = False
                result.blocking_reason = f"Required datasets excluded or not validated: {', '.join(excluded)}"
                result.excluded_datasets = excluded

        status = "Passed" if result.processing_allowed else "Blocked"
        self._audit("Validation Gate Checked", f"{status} — {result.blocking_reason or 'No blocking reason'}")
        return result

    # -----------------------------------------------------------------------
    # Source Loading
    # -----------------------------------------------------------------------

    def load_source_datasets(self) -> Dict[str, pd.DataFrame]:
        """Load the three source datasets from input directory."""
        loaded: Dict[str, pd.DataFrame] = {}
        for ds_name, config in SOURCE_DATASETS.items():
            file_path = self.input_directory / config["source_file"]
            if not file_path.exists():
                raise FileNotFoundError(f"Source file not found: {file_path}")
            df = pd.read_csv(file_path)
            loaded[ds_name] = df
            self.source_checksums[ds_name] = self._file_checksum(file_path)
            self._audit(f"{ds_name.replace('_', ' ').title()} Source Loaded", f"{len(df)} rows")
        return loaded

    # -----------------------------------------------------------------------
    # Transformations
    # -----------------------------------------------------------------------

    def transform_patient_queue(self, source_df: pd.DataFrame) -> pd.DataFrame:
        """Transform patient_queue_records into processed_patient_queue."""
        schema = get_processed_schema("processed_patient_queue")
        if schema is None:
            raise ValueError("Schema not found for processed_patient_queue")

        df = source_df.copy()
        self._add_audit("Queue Transformation Started", f"{len(df)} source rows")

        # Apply column mapping
        col_map = SOURCE_DATASETS["patient_queue_records"]["column_map"]
        for src_col, proc_col in col_map.items():
            if src_col in df.columns:
                df[proc_col] = df[src_col]

        # Preserve identifiers
        df["queue_record_id"] = df["queue_record_id"].astype(str)
        df["hospital_id"] = df["hospital_id"].astype(str)
        df["department_id"] = df["department_id"].astype(str)

        # Parse queue_date
        df["queue_date"] = pd.to_datetime(df["queue_date"], errors="coerce").dt.date
        df["reporting_date"] = df["queue_date"]
        df["reporting_month"] = pd.to_datetime(df["queue_date"], errors="coerce").dt.strftime("%Y-%m")

        # Preserve queue_stage
        df["queue_stage"] = df["queue_stage"].astype(str)

        # Preserve counts and wait values — do not replace blank with zero
        numeric_cols = ["arrivals_count", "served_count", "waiting_patient_count",
                        "average_wait_minutes", "median_wait_minutes", "maximum_wait_minutes"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            else:
                df[col] = np.nan

        # Derive flags from source metadata if present; otherwise null
        if "summary_source_flag" in df.columns:
            df["summary_source_flag"] = df["summary_source_flag"].map({True: True, False: False, "True": True, "False": False, 1: True, 0: False, "1": True, "0": False})
            df["summary_source_flag"] = df["summary_source_flag"].astype("boolean")
        else:
            df["summary_source_flag"] = pd.array([pd.NA] * len(df), dtype="boolean")

        if "encounter_derived_flag" in df.columns:
            df["encounter_derived_flag"] = df["encounter_derived_flag"].map({True: True, False: False, "True": True, "False": False, 1: True, 0: False, "1": True, "0": False})
            df["encounter_derived_flag"] = df["encounter_derived_flag"].astype("boolean")
        else:
            df["encounter_derived_flag"] = pd.array([pd.NA] * len(df), dtype="boolean")

        # Derive valid_queue_record_flag
        df["valid_queue_record_flag"] = True

        # Exclusion logic
        exclusion_mask = pd.Series(False, index=df.index)

        # Negative counts
        count_cols = ["arrivals_count", "served_count", "waiting_patient_count"]
        for col in count_cols:
            if col in df.columns:
                neg_mask = df[col] < 0
                if neg_mask.any():
                    exclusion_mask |= neg_mask
                    self._add_issues_from_mask(
                        df, neg_mask, "patient_queue_records", "processed_patient_queue",
                        "Invalid Queue Count", "Warning", "Negative queue count detected.", col,
                        "NEGATIVE_QUEUE_COUNT",
                    )

        # Negative wait values
        wait_cols = ["average_wait_minutes", "median_wait_minutes", "maximum_wait_minutes"]
        for col in wait_cols:
            if col in df.columns:
                neg_mask = df[col] < 0
                if neg_mask.any():
                    exclusion_mask |= neg_mask
                    self._add_issues_from_mask(
                        df, neg_mask, "patient_queue_records", "processed_patient_queue",
                        "Invalid Wait Value", "Warning", "Negative wait value detected.", col,
                        "NEGATIVE_WAIT_VALUE",
                    )

        # Missing queue stage
        missing_stage = df["queue_stage"].isna() | (df["queue_stage"].astype(str).str.strip() == "")
        if missing_stage.any():
            exclusion_mask |= missing_stage
            self._add_issues_from_mask(
                df, missing_stage, "patient_queue_records", "processed_patient_queue",
                "Missing Queue Stage", "Error", "Missing mandatory queue stage.", "queue_stage",
                "MISSING_QUEUE_STAGE",
            )

        # Unsupported queue stage
        approved_stages = schema.get("categorical_fields", {}).get("queue_stage", [])
        if approved_stages:
            unsupported = df["queue_stage"].notna() & ~df["queue_stage"].isin(approved_stages)
            if unsupported.any():
                # Log as issue but do not exclude — preserve detail
                self._add_issues_from_mask(
                    df, unsupported, "patient_queue_records", "processed_patient_queue",
                    "Unsupported Queue Stage", "Information", "Queue stage outside approved categorical list.", "queue_stage",
                    None,
                )

        # Missing mandatory key
        missing_key = df["queue_record_id"].isna() | (df["queue_record_id"].astype(str).str.strip() == "")
        if missing_key.any():
            exclusion_mask |= missing_key
            self._add_issues_from_mask(
                df, missing_key, "patient_queue_records", "processed_patient_queue",
                "Missing Mandatory Key", "Critical", "Missing mandatory primary key.", "queue_record_id",
                "MISSING_MANDATORY_KEY",
            )

        # Build exclusions
        self._build_exclusions_from_mask(
            df, exclusion_mask, "patient_queue_records", "queue_record_id",
            "NEGATIVE_QUEUE_COUNT", "Queue record excluded due to negative count or missing key."
        )

        # Mark invalid records
        df.loc[exclusion_mask, "valid_queue_record_flag"] = False

        # Add metadata
        df["source_primary_key"] = df["queue_record_id"]
        df["processing_run_id"] = self.processing_run_id
        df["validation_run_id"] = self.validation_run_id
        df["transformation_version"] = TRANSFORMATION_VERSION
        df["processed_datetime"] = datetime.now()

        # Reorder to schema
        all_fields = schema["required_fields"] + schema.get("optional_fields", [])
        for col in all_fields:
            if col not in df.columns:
                df[col] = np.nan
        df = df[[c for c in all_fields if c in df.columns]]

        self._add_audit("Queue Transformation Completed", f"{len(df)} rows, {exclusion_mask.sum()} excluded")
        return df

    def transform_bed_capacity(self, source_df: pd.DataFrame) -> pd.DataFrame:
        """Transform bed_capacity_records into processed_bed_capacity."""
        schema = get_processed_schema("processed_bed_capacity")
        if schema is None:
            raise ValueError("Schema not found for processed_bed_capacity")

        df = source_df.copy()
        self._add_audit("Bed Capacity Transformation Started", f"{len(df)} source rows")

        # Apply column mapping
        col_map = SOURCE_DATASETS["bed_capacity_records"]["column_map"]
        for src_col, proc_col in col_map.items():
            if src_col in df.columns:
                df[proc_col] = df[src_col]

        # Preserve identifiers
        df["bed_capacity_record_id"] = df["bed_capacity_record_id"].astype(str)
        df["hospital_id"] = df["hospital_id"].astype(str)
        df["department_id"] = df["department_id"].astype(str)

        # Parse reporting_date
        df["reporting_date"] = pd.to_datetime(df["reporting_date"], errors="coerce").dt.date
        df["reporting_month"] = pd.to_datetime(df["reporting_date"], errors="coerce").dt.strftime("%Y-%m")

        # Preserve bed counts — do not replace blank with zero
        bed_cols = ["licensed_beds", "staffed_beds", "operational_beds", "occupied_beds", "unavailable_beds", "reserved_beds"]
        for col in bed_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            else:
                df[col] = np.nan

        # Calculate overcapacity metrics
        df["beds_above_operational_capacity"] = (df["occupied_beds"] - df["operational_beds"]).clip(lower=0)
        df["overcapacity_flag"] = df["occupied_beds"] > df["operational_beds"]

        # Preserve overcapacity_exception_flag and overcapacity_reason from source if present
        if "overcapacity_exception_flag" in df.columns:
            df["overcapacity_exception_flag"] = df["overcapacity_exception_flag"].map({True: True, False: False, "True": True, "False": False, 1: True, 0: False})
        else:
            df["overcapacity_exception_flag"] = np.nan

        if "overcapacity_reason" in df.columns:
            df["overcapacity_reason"] = df["overcapacity_reason"].astype(str).replace("nan", np.nan).replace("None", np.nan)
        else:
            df["overcapacity_reason"] = np.nan

        # Derive valid_bed_record_flag
        df["valid_bed_record_flag"] = True

        # Exclusion logic
        exclusion_mask = pd.Series(False, index=df.index)

        # Negative bed counts
        for col in bed_cols:
            if col in df.columns:
                neg_mask = df[col] < 0
                if neg_mask.any():
                    exclusion_mask |= neg_mask
                    self._add_issues_from_mask(
                        df, neg_mask, "bed_capacity_records", "processed_bed_capacity",
                        "Invalid Bed Count", "Warning", f"Negative bed count in {col}.", col,
                        "NEGATIVE_BED_COUNT",
                    )

        # Missing mandatory key
        missing_key = df["bed_capacity_record_id"].isna() | (df["bed_capacity_record_id"].astype(str).str.strip() == "")
        if missing_key.any():
            exclusion_mask |= missing_key
            self._add_issues_from_mask(
                df, missing_key, "bed_capacity_records", "processed_bed_capacity",
                "Missing Mandatory Key", "Critical", "Missing mandatory primary key.", "bed_capacity_record_id",
                "MISSING_MANDATORY_KEY",
            )

        # Build exclusions
        self._build_exclusions_from_mask(
            df, exclusion_mask, "bed_capacity_records", "bed_capacity_record_id",
            "NEGATIVE_BED_COUNT", "Bed capacity record excluded due to negative count or missing key."
        )

        # Mark invalid records
        df.loc[exclusion_mask, "valid_bed_record_flag"] = False

        # Add metadata
        df["source_primary_key"] = df["bed_capacity_record_id"]
        df["processing_run_id"] = self.processing_run_id
        df["validation_run_id"] = self.validation_run_id
        df["transformation_version"] = TRANSFORMATION_VERSION
        df["processed_datetime"] = datetime.now()

        # Reorder to schema
        all_fields = schema["required_fields"] + schema.get("optional_fields", [])
        for col in all_fields:
            if col not in df.columns:
                df[col] = np.nan
        df = df[[c for c in all_fields if c in df.columns]]

        self._add_audit("Bed Capacity Transformation Completed", f"{len(df)} rows, {exclusion_mask.sum()} excluded")
        return df

    def transform_service_schedule(self, source_df: pd.DataFrame) -> pd.DataFrame:
        """Transform service_schedule into processed_service_schedule."""
        schema = get_processed_schema("processed_service_schedule")
        if schema is None:
            raise ValueError("Schema not found for processed_service_schedule")

        df = source_df.copy()
        self._add_audit("Service Schedule Transformation Started", f"{len(df)} source rows")

        # Apply column mapping
        col_map = SOURCE_DATASETS["service_schedule"]["column_map"]
        for src_col, proc_col in col_map.items():
            if src_col in df.columns:
                df[proc_col] = df[src_col]

        # Preserve identifiers
        df["service_schedule_id"] = df["service_schedule_id"].astype(str)
        df["hospital_id"] = df["hospital_id"].astype(str)
        df["department_id"] = df["department_id"].astype(str)

        # Parse service_date
        df["service_date"] = pd.to_datetime(df["service_date"], errors="coerce").dt.date
        df["reporting_date"] = df["service_date"]
        df["reporting_month"] = pd.to_datetime(df["service_date"], errors="coerce").dt.strftime("%Y-%m")

        # Preserve service_type
        df["service_type"] = df["service_type"].astype(str)

        # Parse session timestamps
        df["session_start_datetime"] = pd.to_datetime(df["session_start_datetime"], errors="coerce")
        df["session_end_datetime"] = pd.to_datetime(df["session_end_datetime"], errors="coerce")

        # Calculate planned_service_hours
        # Handle cross-midnight: if end time < start time, add one day to end
        start_dt = df["session_start_datetime"].copy()
        end_dt = df["session_end_datetime"].copy()
        # For records where only time is provided (same date), add a day if end < start
        cross_midnight = (end_dt < start_dt) & start_dt.notna() & end_dt.notna()
        end_dt.loc[cross_midnight] = end_dt.loc[cross_midnight] + pd.Timedelta(days=1)
        duration = (end_dt - start_dt).dt.total_seconds() / 3600.0

        # Use source planned_hours if available and valid; otherwise calculate from timestamps
        if "planned_hours" in df.columns:
            df["planned_service_hours"] = pd.to_numeric(df["planned_hours"], errors="coerce")
            # For records where planned_hours is missing but timestamps are valid, use calculated duration
            missing_planned = df["planned_service_hours"].isna() & start_dt.notna() & end_dt.notna() & (duration >= 0)
            df.loc[missing_planned, "planned_service_hours"] = duration.loc[missing_planned]
        else:
            df["planned_service_hours"] = duration.where(
                start_dt.notna() & end_dt.notna() & (duration >= 0),
                np.nan,
            )

        # Preserve planned_capacity — do not replace blank with zero
        if "planned_capacity" in df.columns:
            df["planned_capacity"] = pd.to_numeric(df["planned_capacity"], errors="coerce")
        else:
            df["planned_capacity"] = np.nan

        # Preserve schedule_status
        df["schedule_status"] = df["schedule_status"].astype(str)

        # Derive flags from schedule_status
        df["cancelled_session_flag"] = df["schedule_status"].str.lower() == "cancelled"
        df["reduced_session_flag"] = df["schedule_status"].str.lower() == "reduced"
        df["extended_session_flag"] = df["schedule_status"].str.lower() == "extended"

        # Derive valid_schedule_flag
        df["valid_schedule_flag"] = True

        # Exclusion logic
        exclusion_mask = pd.Series(False, index=df.index)

        # Invalid negative duration (from timestamps or planned_hours)
        invalid_duration = df["session_start_datetime"].notna() & df["session_end_datetime"].notna() & (duration < 0)
        if invalid_duration.any():
            exclusion_mask |= invalid_duration
            self._add_issues_from_mask(
                df, invalid_duration, "service_schedule", "processed_service_schedule",
                "Invalid Service Duration", "Error", "Negative service duration detected.", "planned_service_hours",
                "INVALID_SERVICE_DURATION",
            )

        # Negative planned_service_hours
        neg_hours = df["planned_service_hours"] < 0
        if neg_hours.any():
            exclusion_mask |= neg_hours
            self._add_issues_from_mask(
                df, neg_hours, "service_schedule", "processed_service_schedule",
                "Invalid Service Duration", "Error", "Negative planned service hours detected.", "planned_service_hours",
                "INVALID_SERVICE_DURATION",
            )

        # Missing mandatory timestamps when not cancelled
        missing_ts = (
            df["session_start_datetime"].isna() | df["session_end_datetime"].isna()
        ) & (~df["cancelled_session_flag"])
        if missing_ts.any():
            exclusion_mask |= missing_ts
            self._add_issues_from_mask(
                df, missing_ts, "service_schedule", "processed_service_schedule",
                "Missing Service Timestamp", "Error", "Missing mandatory session timestamp for non-cancelled session.", "session_start_datetime",
                "MISSING_SERVICE_TIMESTAMP",
            )

        # Missing mandatory key
        missing_key = df["service_schedule_id"].isna() | (df["service_schedule_id"].astype(str).str.strip() == "")
        if missing_key.any():
            exclusion_mask |= missing_key
            self._add_issues_from_mask(
                df, missing_key, "service_schedule", "processed_service_schedule",
                "Missing Mandatory Key", "Critical", "Missing mandatory primary key.", "service_schedule_id",
                "MISSING_MANDATORY_KEY",
            )

        # Unsupported schedule status
        approved_statuses = schema.get("categorical_fields", {}).get("schedule_status", [])
        if approved_statuses:
            unsupported = df["schedule_status"].notna() & ~df["schedule_status"].isin(approved_statuses)
            if unsupported.any():
                self._add_issues_from_mask(
                    df, unsupported, "service_schedule", "processed_service_schedule",
                    "Unsupported Schedule Status", "Information", "Schedule status outside approved categorical list.", "schedule_status",
                    None,
                )

        # Build exclusions
        self._build_exclusions_from_mask(
            df, exclusion_mask, "service_schedule", "service_schedule_id",
            "INVALID_SERVICE_DURATION", "Service schedule record excluded due to invalid duration or missing key."
        )

        # Mark invalid records
        df.loc[exclusion_mask, "valid_schedule_flag"] = False

        # Add metadata
        df["source_primary_key"] = df["service_schedule_id"]
        df["processing_run_id"] = self.processing_run_id
        df["validation_run_id"] = self.validation_run_id
        df["transformation_version"] = TRANSFORMATION_VERSION
        df["processed_datetime"] = datetime.now()

        # Reorder to schema
        all_fields = schema["required_fields"] + schema.get("optional_fields", [])
        for col in all_fields:
            if col not in df.columns:
                df[col] = np.nan
        df = df[[c for c in all_fields if c in df.columns]]

        self._add_audit("Service Schedule Transformation Completed", f"{len(df)} rows, {exclusion_mask.sum()} excluded")
        return df

    # -----------------------------------------------------------------------
    # Schema Validation
    # -----------------------------------------------------------------------

    def validate_processed_schema(self, processed_df: pd.DataFrame, dataset_name: str) -> List[str]:
        """Validate that a processed dataframe conforms to its schema."""
        schema = get_processed_schema(dataset_name)
        if schema is None:
            return [f"Schema not found for {dataset_name}"]

        errors: List[str] = []
        required_fields = schema.get("required_fields", [])
        for field in required_fields:
            if field not in processed_df.columns:
                errors.append(f"Missing required field '{field}' in {dataset_name}")

        # Type checks
        for field in schema.get("date_fields", []):
            if field in processed_df.columns and not pd.api.types.is_datetime64_any_dtype(processed_df[field]):
                # Allow object dtype for date fields (Python date objects)
                pass

        for field in schema.get("numeric_fields", []):
            if field in processed_df.columns:
                if not pd.api.types.is_numeric_dtype(processed_df[field]):
                    errors.append(f"Field '{field}' in {dataset_name} is not numeric")

        for field in schema.get("boolean_fields", []):
            if field in processed_df.columns:
                if not (pd.api.types.is_bool_dtype(processed_df[field]) or pd.api.types.is_object_dtype(processed_df[field])):
                    errors.append(f"Field '{field}' in {dataset_name} is not boolean")

        return errors

    # -----------------------------------------------------------------------
    # Lineage
    # -----------------------------------------------------------------------

    def build_lineage(
        self,
        source_df: pd.DataFrame,
        processed_df: pd.DataFrame,
        dataset_name: str,
    ) -> pd.DataFrame:
        """Build lineage records linking source to processed."""
        if not self.collect_lineage:
            return pd.DataFrame()

        config = SOURCE_DATASETS[dataset_name]
        source_pk = config["primary_key"]
        processed_pk = config["primary_key"]
        rule_id = config["transformation_rule_id"]
        description = config["transformation_description"]

        records = []
        for idx, row in processed_df.iterrows():
            source_value = row.get(source_pk, "")
            lineage_id = str(uuid.uuid4())
            record = ProcessingLineageRecord(
                processing_run_id=self.processing_run_id,
                lineage_id=lineage_id,
                validation_run_id=self.validation_run_id,
                source_dataset_name=dataset_name,
                source_file_name=config["source_file"],
                source_primary_key_field=source_pk,
                source_primary_key_value=str(source_value),
                source_row_number=int(idx) + 2,  # 1-based with header
                processed_dataset_name=config["processed_name"],
                processed_primary_key_field=processed_pk,
                processed_primary_key_value=str(source_value),
                transformation_rule_id=rule_id,
                transformation_description=description,
                source_fields_used=",".join(source_df.columns.tolist()),
                processed_fields_created=",".join(processed_df.columns.tolist()),
                exclusion_flag=not row.get("valid_queue_record_flag", True) if "valid_queue_record_flag" in row else (
                    not row.get("valid_bed_record_flag", True) if "valid_bed_record_flag" in row else (
                        not row.get("valid_schedule_flag", True) if "valid_schedule_flag" in row else False
                    )
                ),
                exclusion_reason_code=row.get("exclusion_reason_code", ""),
                transformation_version=TRANSFORMATION_VERSION,
                configuration_version=ENGINE_VERSION,
                processed_datetime=datetime.now(),
            )
            records.append(record)
            self.lineage_records.append(record)

        df = pd.DataFrame([r.to_dict() for r in records])
        self._add_audit(f"Lineage Built for {dataset_name}", f"{len(df)} records")
        return df

    # -----------------------------------------------------------------------
    # Exclusions
    # -----------------------------------------------------------------------

    def build_exclusions(self) -> pd.DataFrame:
        """Return exclusion register as DataFrame."""
        if not self.exclusion_records:
            return pd.DataFrame(columns=[
                "processing_run_id", "exclusion_id", "source_dataset_name",
                "source_primary_key_field", "source_primary_key_value", "source_row_number",
                "exclusion_reason_code", "exclusion_reason_description", "validation_issue_id",
                "manual_override_id", "exclusion_stage", "excluded_by_rule",
                "reversible_flag", "created_datetime",
            ])
        df = pd.DataFrame([r.to_dict() for r in self.exclusion_records])
        self._add_audit("Exclusion Register Built", f"{len(df)} records")
        return df

    # -----------------------------------------------------------------------
    # Issues
    # -----------------------------------------------------------------------

    def collect_issues(self) -> pd.DataFrame:
        """Return issues as DataFrame."""
        if not self.issues:
            return pd.DataFrame(columns=[
                "processing_run_id", "issue_id", "source_dataset_name",
                "processed_dataset_name", "source_primary_key", "source_row_number",
                "field_name", "issue_type", "severity", "issue_description",
                "source_value", "processed_value", "resolution_action",
                "exclusion_flag", "blocks_processing", "created_datetime",
            ])
        df = pd.DataFrame([i.to_dict() for i in self.issues])
        self._add_audit("Issues Collected", f"{len(df)} issues")
        return df

    # -----------------------------------------------------------------------
    # Transformation Results
    # -----------------------------------------------------------------------

    def return_transformation_results(
        self,
        queue_df: pd.DataFrame,
        bed_df: pd.DataFrame,
        schedule_df: pd.DataFrame,
    ) -> Dict[str, TransformationResultContract]:
        """Return transformation results for all three datasets."""
        results = {}
        for name, df in [
            ("patient_queue_records", queue_df),
            ("bed_capacity_records", bed_df),
            ("service_schedule", schedule_df),
        ]:
            config = SOURCE_DATASETS[name]
            dataset_result = ProcessingDatasetResult(
                processing_run_id=self.processing_run_id,
                validation_run_id=self.validation_run_id,
                source_dataset_name=name,
                processed_dataset_name=config["processed_name"],
                source_row_count=len(df),
                processed_row_count=len(df),
                excluded_row_count=0,
                transformed_field_count=len(df.columns),
                warning_count=sum(1 for i in self.issues if i.source_dataset_name == name and i.severity == "Warning"),
                error_count=sum(1 for i in self.issues if i.source_dataset_name == name and i.severity == "Error"),
                dataset_status="Processed",
                output_file_name=f"{config['processed_name']}.csv",
                transformation_version=TRANSFORMATION_VERSION,
                processed_datetime=datetime.now(),
            )
            self.dataset_results.append(dataset_result)
            results[name] = TransformationResultContract(
                processed_dataframe=df,
                issues=[i for i in self.issues if i.source_dataset_name == name],
                dataset_result=dataset_result,
                success_flag=True,
            )
        return results

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

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

    def _add_audit(self, event: str, detail: str) -> None:
        """Alias for _audit."""
        self._audit(event, detail)

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

    def _add_issues_from_mask(
        self,
        df: pd.DataFrame,
        mask: pd.Series,
        source_dataset_name: str,
        processed_dataset_name: str,
        issue_type: str,
        severity: str,
        issue_description: str,
        field_name: str,
        exclusion_reason_code: Optional[str],
    ) -> None:
        """Add issues for rows matching a boolean mask."""
        pk_field = SOURCE_DATASETS[source_dataset_name]["primary_key"]
        affected = df[mask]
        for idx, row in affected.head(self.max_issue_examples).iterrows():
            self._add_issue(
                source_dataset_name=source_dataset_name,
                processed_dataset_name=processed_dataset_name,
                source_primary_key=str(row.get(pk_field, "")),
                source_row_number=int(idx) + 2,
                field_name=field_name,
                issue_type=issue_type,
                severity=severity,
                issue_description=issue_description,
                source_value=str(row.get(field_name, "")),
                exclusion_flag=exclusion_reason_code is not None,
            )

    def _build_exclusions_from_mask(
        self,
        df: pd.DataFrame,
        mask: pd.Series,
        source_dataset_name: str,
        source_primary_key_field: str,
        exclusion_reason_code: str,
        exclusion_reason_description: str,
    ) -> None:
        """Build exclusion records for rows matching a boolean mask."""
        affected = df[mask]
        for idx, row in affected.iterrows():
            exclusion = ProcessingExclusionRecord(
                processing_run_id=self.processing_run_id,
                exclusion_id=str(uuid.uuid4()),
                source_dataset_name=source_dataset_name,
                source_primary_key_field=source_primary_key_field,
                source_primary_key_value=str(row.get(source_primary_key_field, "")),
                source_row_number=int(idx) + 2,
                exclusion_reason_code=exclusion_reason_code,
                exclusion_reason_description=exclusion_reason_description,
                validation_issue_id="",
                manual_override_id="",
                exclusion_stage="Transformation",
                excluded_by_rule=TRANSFORMATION_VERSION,
                reversible_flag=False,
            )
            self.exclusion_records.append(exclusion)
