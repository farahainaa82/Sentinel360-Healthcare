"""
Sentinel360 Healthcare — Data Validation Engine

Reusable, deterministic validation engine for source datasets.
Does not modify source data, calculate KPIs, or generate analytical outputs.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

from src.validation_models import (
    DatasetValidationResult,
    ManualOverrideRecord,
    RecordValidationIssue,
    RelationshipValidationResult,
    ValidationAuditEvent,
    ValidationIssue,
    ValidationRun,
)
from src import validation_config_loader as vcl

ENGINE_VERSION = "1.0.0"
CONFIG_VERSION = "1.0.0"


class ValidationResult:
    """Container for all outputs of a validation run."""

    def __init__(self, validation_run: ValidationRun):
        self.validation_run = validation_run
        self.dataset_results: Dict[str, DatasetValidationResult] = {}
        self.issues: List[ValidationIssue] = []
        self.record_issues: List[RecordValidationIssue] = []
        self.relationship_results: List[RelationshipValidationResult] = []
        self.manual_overrides: List[ManualOverrideRecord] = []
        self.audit_events: List[ValidationAuditEvent] = []
        self.source_checksums: Dict[str, str] = {}


class DataValidationEngine:
    """
    Reusable validation engine for Sentinel360 Healthcare datasets.

    Parameters
    ----------
    input_directory : Path
        Directory containing source CSV files.
    schema_registry : dict
        Loaded dataset schema definitions.
    relationship_registry : list
        Loaded foreign-key relationship definitions.
    validation_rules : list
        Loaded validation-rule metadata.
    source_type : str
        Descriptor for the source (e.g. 'synthetic_demo').
    validation_run_id : str, optional
        Explicit run identifier. Auto-generated if omitted.
    collect_record_level_issues : bool
        Whether to capture representative record-level issues.
    maximum_record_level_examples : int
        Maximum record-level examples per issue type per dataset.
    """

    def __init__(
        self,
        input_directory: Path,
        schema_registry: Dict[str, Dict[str, Any]],
        relationship_registry: List[Dict[str, Any]],
        validation_rules: List[Dict[str, Any]],
        source_type: str,
        validation_run_id: Optional[str] = None,
        collect_record_level_issues: bool = True,
        maximum_record_level_examples: int = 100,
    ) -> None:
        self.input_directory = Path(input_directory)
        self.schema_registry = schema_registry
        self.relationship_registry = relationship_registry
        self.validation_rules = validation_rules
        self.source_type = source_type
        self.validation_run_id = validation_run_id or f"VAL-{uuid.uuid4().hex[:12].upper()}"
        self.collect_record_level_issues = collect_record_level_issues
        self.maximum_record_level_examples = maximum_record_level_examples
        self.issues: List[ValidationIssue] = []
        self.record_issues: List[RecordValidationIssue] = []
        self._issue_counter = 0
        self._record_issue_counter = 0
        self._audit_counter = 0

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def run_validation(self) -> ValidationResult:
        """Execute the full validation pipeline and return results."""
        started = datetime.now()
        run = ValidationRun(
            validation_run_id=self.validation_run_id,
            validation_started_datetime=started,
            input_directory=str(self.input_directory),
            source_type=self.source_type,
            dataset_count_expected=len(vcl.DATASET_NAMES),
            validation_engine_version=ENGINE_VERSION,
            configuration_version=CONFIG_VERSION,
            created_by="system",
        )
        result = ValidationResult(run)

        self._add_audit_event(result, "Validation Started", "Validation run initiated.")
        self._add_audit_event(result, "Registry Loaded", "Schema, relationship and rule registries loaded.")

        # Discover source files and compute checksums
        discovered = self._discover_files()
        run.dataset_count_found = len(discovered)

        # Load all datasets first for cross-dataset checks
        loaded_data: Dict[str, pd.DataFrame] = {}
        for ds_name in vcl.DATASET_NAMES:
            file_path = self.input_directory / f"{ds_name}.csv"
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path, dtype=str, keep_default_na=True)
                    loaded_data[ds_name] = df
                    result.source_checksums[ds_name] = self._file_checksum(file_path)
                except Exception:
                    loaded_data[ds_name] = pd.DataFrame()
            else:
                loaded_data[ds_name] = pd.DataFrame()

        # Validate each dataset
        for ds_name in vcl.DATASET_NAMES:
            file_path = self.input_directory / f"{ds_name}.csv"
            ds_result = self._validate_dataset(ds_name, file_path, loaded_data, result)
            result.dataset_results[ds_name] = ds_result
            self._add_audit_event(result, "Dataset Validation Completed", f"Validation completed for {ds_name}.", dataset_name=ds_name)

        # Relationship validation
        self._validate_all_relationships(loaded_data, result)
        self._add_audit_event(result, "Relationship Validation Completed", "All referential-integrity checks completed.")

        # Configuration readiness
        config_issues = self._validate_config_readiness()
        for iss in config_issues:
            result.issues.append(iss)
            run.information_issue_count += 1

        # Privacy / unexpected CSV check
        self._validate_unexpected_files(discovered, result)

        # Determine statuses
        for ds_name, ds_result in result.dataset_results.items():
            ds_result.dataset_status = self._determine_dataset_status(ds_result)
            ds_result.processing_allowed_flag = ds_result.dataset_status in (
                "Valid", "Valid with Warnings", "Pending Review"
            )

        run.run_status = self._determine_run_status(result.dataset_results)
        run.blocking_issue_count = sum(1 for i in result.issues if i.blocks_processing and i.issue_status == "Open")
        run.critical_issue_count = sum(1 for i in result.issues if i.severity == "Critical")
        run.error_issue_count = sum(1 for i in result.issues if i.severity == "Error")
        run.warning_issue_count = sum(1 for i in result.issues if i.severity == "Warning")
        run.information_issue_count += sum(1 for i in result.issues if i.severity == "Information")
        run.validation_completed_datetime = datetime.now()

        self._add_audit_event(result, "Validation Completed", f"Run status: {run.run_status}")
        return result

    # -----------------------------------------------------------------------
    # File-level validation
    # -----------------------------------------------------------------------

    def _discover_files(self) -> List[Path]:
        """Return all CSV files in the input directory."""
        if not self.input_directory.exists():
            return []
        return sorted(self.input_directory.glob("*.csv"))

    def _file_checksum(self, file_path: Path) -> str:
        """Compute SHA-256 checksum of a file."""
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def _validate_dataset(
        self,
        ds_name: str,
        file_path: Path,
        loaded_data: Dict[str, pd.DataFrame],
        result: ValidationResult,
    ) -> DatasetValidationResult:
        """Run all validations for a single dataset."""
        ds_started = datetime.now()
        ds_result = DatasetValidationResult(
            validation_run_id=self.validation_run_id,
            dataset_name=ds_name,
            file_name=file_path.name,
            validation_started_datetime=ds_started,
        )

        schema = self.schema_registry.get(ds_name, {})
        required_cols = schema.get("required_columns", [])
        expected_col_count = len(schema.get("columns", []))
        ds_result.expected_column_count = expected_col_count

        # File presence
        if not file_path.exists():
            self._add_issue(result, ds_result, "FILE_MISSING", ds_name, "", "Critical",
                            True, False, f"Required file {file_path.name} is missing.",
                            "File not found", "", "File must exist", 0)
            ds_result.file_found_flag = False
            ds_result.file_readable_flag = False
            ds_result.validation_completed_datetime = datetime.now()
            return ds_result

        ds_result.file_found_flag = True

        # File readability
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw = f.read()
            ds_result.file_readable_flag = True
        except Exception as exc:
            self._add_issue(result, ds_result, "FILE_UNREADABLE", ds_name, "", "Critical",
                            True, False, f"File {file_path.name} is not readable.",
                            "Read error", str(exc), "File must be readable", 0)
            ds_result.validation_completed_datetime = datetime.now()
            return ds_result

        # Empty file check
        if len(raw.strip()) == 0:
            if ds_name not in vcl.ALLOWED_EMPTY_DATASETS:
                self._add_issue(result, ds_result, "FILE_EMPTY", ds_name, "", "Error",
                                True, False, f"File {file_path.name} is empty.",
                                "No content", "", "File must contain data", 0)
            ds_result.validation_completed_datetime = datetime.now()
            return ds_result

        # Load DataFrame (re-use loaded_data if available)
        df = loaded_data.get(ds_name, pd.DataFrame())
        if df.empty and not file_path.exists():
            ds_result.validation_completed_datetime = datetime.now()
            return ds_result

        ds_result.row_count = len(df)
        ds_result.column_count = len(df.columns)

        # Schema validation
        self._validate_schema(df, ds_name, schema, result, ds_result)

        # Data-type validation
        self._validate_data_types(df, ds_name, schema, result, ds_result)

        # Completeness
        self._validate_completeness(df, ds_name, schema, result, ds_result)

        # Primary keys
        self._validate_primary_keys(df, ds_name, schema, result, ds_result)

        # Dates and datetimes ordering/range
        self._validate_dates_and_datetimes(df, ds_name, schema, result, ds_result)

        # Numeric ranges
        self._validate_numeric_ranges(df, ds_name, schema, result, ds_result)

        # Dataset-specific validations
        if ds_name == "bed_capacity_records":
            self._validate_bed_capacity(df, ds_name, result, ds_result)
        if ds_name == "staff_attendance":
            self._validate_attendance(df, ds_name, loaded_data, result, ds_result)
        if ds_name == "patient_queue_records":
            self._validate_queue_consistency(df, ds_name, result, ds_result)
        if ds_name == "patient_encounters":
            self._validate_encounter_consistency(df, ds_name, result, ds_result)
        if ds_name == "patient_complaints":
            self._validate_complaint_consistency(df, ds_name, result, ds_result)
        if ds_name == "patient_surveys":
            self._validate_survey_consistency(df, ds_name, result, ds_result)

        # Privacy
        self._validate_privacy(df, ds_name, result, ds_result)

        ds_result.validation_completed_datetime = datetime.now()
        return ds_result

    def _validate_schema(
        self,
        df: pd.DataFrame,
        ds_name: str,
        schema: Dict[str, Any],
        result: ValidationResult,
        ds_result: DatasetValidationResult,
    ) -> None:
        """Validate column presence and detect unexpected columns."""
        expected_cols = schema.get("columns", [])
        required_cols = schema.get("required_columns", [])
        actual_cols = list(df.columns)

        # Duplicate column names
        seen = set()
        dupes = []
        for c in actual_cols:
            if c in seen:
                dupes.append(c)
            seen.add(c)
        if dupes:
            self._add_issue(result, ds_result, "DUPLICATE_COLUMNS", ds_name, "", "Error",
                            True, False, "Duplicate column names detected.",
                            "Duplicate column names", str(list(set(dupes))), "Column names must be unique", len(set(dupes)))

        # Missing required columns
        missing_required = [c for c in required_cols if c not in actual_cols]
        if missing_required:
            ds_result.missing_required_column_count = len(missing_required)
            for c in missing_required:
                self._add_issue(result, ds_result, "COLUMN_MISSING", ds_name, c, "Critical",
                                True, False, f"Required column {c} is missing.",
                                "Column not found", "", "Column must exist", 0)

        # Unexpected columns
        unexpected = [c for c in actual_cols if c not in expected_cols]
        if unexpected:
            ds_result.unexpected_column_count = len(unexpected)
            for c in unexpected:
                # Check if it resembles a prohibited identifier
                lower_c = c.lower()
                is_prohibited = any(p.lower() in lower_c for p in vcl.PROHIBITED_FIELD_FRAGMENTS)
                sev = "Critical" if is_prohibited else "Warning"
                blocks = is_prohibited
                self._add_issue(result, ds_result, "UNEXPECTED_COLUMN", ds_name, c, sev,
                                blocks, not blocks, f"Unexpected column {c} detected.",
                                "Column not in schema", c, "Column should match approved schema", 0)

    def _validate_data_types(
        self,
        df: pd.DataFrame,
        ds_name: str,
        schema: Dict[str, Any],
        result: ValidationResult,
        ds_result: DatasetValidationResult,
    ) -> None:
        """Validate parseability of dates, datetimes, numerics, booleans."""
        # Dates
        for field in schema.get("date_fields", []):
            if field not in df.columns:
                continue
            invalid_mask = ~df[field].isna() & ~self._is_valid_date_series(df[field])
            count = int(invalid_mask.sum())
            if count:
                ds_result.invalid_date_count += count
                self._add_issue(result, ds_result, "INVALID_DATE", ds_name, field, "Error",
                                True, False, f"Field {field} contains invalid dates.",
                                "Unparseable date", "", "Must be a valid date", count)
                self._add_record_issues(result, ds_name, field, invalid_mask, df, schema,
                                        "INVALID_DATE", "Error", True, f"Invalid date in {field}")

        # Datetimes
        for field in schema.get("datetime_fields", []):
            if field not in df.columns:
                continue
            invalid_mask = ~df[field].isna() & ~self._is_valid_datetime_series(df[field])
            count = int(invalid_mask.sum())
            if count:
                ds_result.invalid_datetime_count += count
                self._add_issue(result, ds_result, "INVALID_DATETIME", ds_name, field, "Error",
                                True, False, f"Field {field} contains invalid datetimes.",
                                "Unparseable datetime", "", "Must be a valid datetime", count)
                self._add_record_issues(result, ds_name, field, invalid_mask, df, schema,
                                        "INVALID_DATETIME", "Error", True, f"Invalid datetime in {field}")

        # Numerics
        for field in schema.get("numeric_fields", []):
            if field not in df.columns:
                continue
            invalid_mask = ~df[field].isna() & ~self._is_valid_numeric_series(df[field])
            count = int(invalid_mask.sum())
            if count:
                ds_result.invalid_numeric_count += count
                self._add_issue(result, ds_result, "INVALID_NUMERIC", ds_name, field, "Error",
                                True, False, f"Field {field} contains invalid numeric values.",
                                "Unparseable number", "", "Must be a valid number", count)
                self._add_record_issues(result, ds_name, field, invalid_mask, df, schema,
                                        "INVALID_NUMERIC", "Error", True, f"Invalid numeric in {field}")

        # Booleans
        for field in schema.get("boolean_fields", []):
            if field not in df.columns:
                continue
            invalid_mask = ~df[field].isna() & ~self._is_valid_boolean_series(df[field])
            count = int(invalid_mask.sum())
            if count:
                ds_result.invalid_data_type_count += count
                self._add_issue(result, ds_result, "INVALID_BOOLEAN", ds_name, field, "Error",
                                True, False, f"Field {field} contains invalid boolean values.",
                                "Unparseable boolean", "", "Must be True/False/1/0", count)
                self._add_record_issues(result, ds_name, field, invalid_mask, df, schema,
                                        "INVALID_BOOLEAN", "Error", True, f"Invalid boolean in {field}")

        # Categorical / domain values
        domain_map = schema.get("domain_values", {})
        for field, allowed in domain_map.items():
            if field not in df.columns:
                continue
            invalid_mask = ~df[field].isna() & ~df[field].isin(allowed)
            count = int(invalid_mask.sum())
            if count:
                ds_result.invalid_domain_value_count += count
                self._add_issue(result, ds_result, "INVALID_DOMAIN", ds_name, field, "Error",
                                True, False, f"Field {field} contains values outside approved domain.",
                                "Value not in domain", "", f"Must be one of {allowed}", count)
                self._add_record_issues(result, ds_name, field, invalid_mask, df, schema,
                                        "INVALID_DOMAIN", "Error", True, f"Invalid domain value in {field}")

    def _validate_completeness(
        self,
        df: pd.DataFrame,
        ds_name: str,
        schema: Dict[str, Any],
        result: ValidationResult,
        ds_result: DatasetValidationResult,
    ) -> None:
        """Validate required fields are not missing or blank."""
        required_cols = schema.get("required_columns", [])
        pk = schema.get("primary_key", "")
        for col in required_cols:
            if col not in df.columns:
                continue
            # Null or blank (after stripping)
            is_blank = df[col].isna() | (df[col].astype(str).str.strip() == "")
            count = int(is_blank.sum())
            if count:
                ds_result.missing_required_value_count += count
                sev = "Critical" if col == pk else "Error"
                blocks = True
                self._add_issue(result, ds_result, "REQUIRED_VALUE_MISSING", ds_name, col, sev,
                                blocks, False, f"Required field {col} has missing or blank value.",
                                "Null or blank", "", "Value must be present", count)
                self._add_record_issues(result, ds_name, col, is_blank, df, schema,
                                        "REQUIRED_VALUE_MISSING", sev, blocks,
                                        f"Missing required value in {col}")

    def _validate_primary_keys(
        self,
        df: pd.DataFrame,
        ds_name: str,
        schema: Dict[str, Any],
        result: ValidationResult,
        ds_result: DatasetValidationResult,
    ) -> None:
        """Validate primary-key constraints."""
        pk = schema.get("primary_key", "")
        if not pk or pk not in df.columns:
            return

        # Null or blank
        is_blank = df[pk].isna() | (df[pk].astype(str).str.strip() == "")
        blank_count = int(is_blank.sum())
        if blank_count:
            ds_result.missing_required_value_count += blank_count
            self._add_issue(result, ds_result, "PRIMARY_KEY_MISSING", ds_name, pk, "Critical",
                            True, False, "Primary key value is null or blank.",
                            "Null or blank PK", "", "PK must be populated", blank_count)
            self._add_record_issues(result, ds_name, pk, is_blank, df, schema,
                                    "PRIMARY_KEY_MISSING", "Critical", True, "Blank primary key")

        # Duplicate PKs
        non_blank = df[~is_blank]
        if not non_blank.empty:
            dupes = non_blank[pk].duplicated(keep=False)
            dup_count = int(dupes.sum())
            if dup_count:
                ds_result.duplicate_primary_key_count = dup_count
                self._add_issue(result, ds_result, "PRIMARY_KEY_DUPLICATE", ds_name, pk, "Critical",
                                True, False, "Primary key value is duplicated.",
                                "Duplicate PK", "", "PK must be unique", dup_count)
                self._add_record_issues(result, ds_name, pk, dupes.reindex(df.index, fill_value=False), df, schema,
                                        "PRIMARY_KEY_DUPLICATE", "Critical", True, "Duplicate primary key")

        # Leading/trailing whitespace
        has_ws = df[pk].astype(str).str.strip() != df[pk].astype(str)
        ws_count = int(has_ws.sum())
        if ws_count:
            self._add_issue(result, ds_result, "PRIMARY_KEY_WHITESPACE", ds_name, pk, "Warning",
                            False, True, "Primary key contains leading or trailing whitespace.",
                            "Whitespace detected", "", "PK should not have extra whitespace", ws_count)

        # Float-like PK where string expected
        float_like = df[pk].astype(str).str.match(r"^\d+\.0+$")
        fl_count = int(float_like.sum())
        if fl_count:
            self._add_issue(result, ds_result, "PRIMARY_KEY_FLOAT", ds_name, pk, "Warning",
                            False, True, "Primary key appears as floating-point value.",
                            "Float-like string", "", "PK should be string identifier", fl_count)

    def _validate_all_relationships(
        self,
        loaded_data: Dict[str, pd.DataFrame],
        result: ValidationResult,
    ) -> None:
        """Validate all foreign-key relationships."""
        for rel in self.relationship_registry:
            child_ds = rel["child_dataset"]
            child_field = rel["child_field"]
            parent_ds = rel["parent_dataset"]
            parent_field = rel["parent_field"]
            mandatory = rel["mandatory"]

            child_df = loaded_data.get(child_ds, pd.DataFrame())
            parent_df = loaded_data.get(parent_ds, pd.DataFrame())

            if child_df.empty or parent_df.empty:
                status = "Not Checked" if child_df.empty else "Orphans Detected"
                rvr = RelationshipValidationResult(
                    validation_run_id=self.validation_run_id,
                    relationship_id=rel["relationship_id"],
                    child_dataset=child_ds,
                    child_field=child_field,
                    parent_dataset=parent_ds,
                    parent_field=parent_field,
                    relationship_status=status,
                    blocks_processing=False,
                    notes="Parent or child dataset not available."
                )
                result.relationship_results.append(rvr)
                continue

            if child_field not in child_df.columns or parent_field not in parent_df.columns:
                status = "Not Checked"
                rvr = RelationshipValidationResult(
                    validation_run_id=self.validation_run_id,
                    relationship_id=rel["relationship_id"],
                    child_dataset=child_ds,
                    child_field=child_field,
                    parent_dataset=parent_ds,
                    parent_field=parent_field,
                    relationship_status=status,
                    blocks_processing=False,
                    notes="Field not found in schema."
                )
                result.relationship_results.append(rvr)
                continue

            child_values = child_df[child_field]
            parent_values = set(parent_df[parent_field].dropna().astype(str))

            populated = child_values.notna() & (child_values.astype(str).str.strip() != "")
            null_count = int((~populated).sum())
            populated_count = int(populated.sum())

            populated_values = child_values[populated].astype(str)
            orphan_mask = ~populated_values.isin(parent_values)
            orphan_count = int(orphan_mask.sum())
            valid_count = populated_count - orphan_count

            status = "Valid" if orphan_count == 0 else "Orphans Detected"
            blocks = mandatory and orphan_count > 0

            rvr = RelationshipValidationResult(
                validation_run_id=self.validation_run_id,
                relationship_id=rel["relationship_id"],
                child_dataset=child_ds,
                child_field=child_field,
                parent_dataset=parent_ds,
                parent_field=parent_field,
                populated_child_value_count=populated_count,
                valid_reference_count=valid_count,
                null_reference_count=null_count,
                orphan_reference_count=orphan_count,
                relationship_status=status,
                blocks_processing=blocks,
                notes="",
            )
            result.relationship_results.append(rvr)

            if orphan_count > 0:
                sev = "Critical" if mandatory else "Error"
                ds_res = result.dataset_results.get(child_ds)
                if ds_res is None:
                    ds_res = DatasetValidationResult(validation_run_id=self.validation_run_id, dataset_name=child_ds)
                    result.dataset_results[child_ds] = ds_res
                self._add_issue(result, ds_res,
                                "ORPHAN_FOREIGN_KEY", child_ds, child_field, sev, blocks, not blocks,
                                f"Field {child_field} references {parent_ds}.{parent_field} but {orphan_count} value(s) not found.",
                                "Orphan reference", "", f"Must exist in {parent_ds}.{parent_field}", orphan_count)

    def _validate_dates_and_datetimes(
        self,
        df: pd.DataFrame,
        ds_name: str,
        schema: Dict[str, Any],
        result: ValidationResult,
        ds_result: DatasetValidationResult,
    ) -> None:
        """Validate date/datetime ordering and logical constraints."""
        # Effective dates
        if ds_name in ("hospital_master", "department_master", "staff_role_master"):
            if "effective_from" in df.columns and "effective_to" in df.columns:
                invalid = self._date_order_invalid(df, "effective_from", "effective_to")
                count = int(invalid.sum())
                if count:
                    self._add_issue(result, ds_result, "DATE_ORDER", ds_name, "effective_to", "Error",
                                    True, False, "Effective end date must be after effective start date.",
                                    "Start >= End", "", "End must be after start", count)
                    self._add_record_issues(result, ds_name, "effective_to", invalid, df, schema,
                                            "DATE_ORDER", "Error", True, "Invalid effective date order")

        # Employment dates
        if ds_name == "staff_master":
            if "employment_start_date" in df.columns and "employment_end_date" in df.columns:
                has_end = df["employment_end_date"].notna() & (df["employment_end_date"].astype(str).str.strip() != "")
                invalid = has_end & self._date_order_invalid(df, "employment_start_date", "employment_end_date")
                count = int(invalid.sum())
                if count:
                    self._add_issue(result, ds_result, "DATE_ORDER", ds_name, "employment_end_date", "Error",
                                    True, False, "Employment end date must be after start date.",
                                    "Start >= End", "", "End must be after start", count)

        # Encounter timestamps
        if ds_name == "patient_encounters":
            if "arrival_datetime" in df.columns and "service_start_datetime" in df.columns:
                has_start = df["service_start_datetime"].notna() & (df["service_start_datetime"].astype(str).str.strip() != "")
                invalid = has_start & self._datetime_order_invalid(df, "arrival_datetime", "service_start_datetime")
                count = int(invalid.sum())
                if count:
                    self._add_issue(result, ds_result, "DATETIME_ORDER", ds_name, "service_start_datetime", "Error",
                                    True, False, "Service start must not be before arrival.",
                                    "Arrival > Service Start", "", "Service start must be >= arrival", count)

            if "service_start_datetime" in df.columns and "service_end_datetime" in df.columns:
                has_end = df["service_end_datetime"].notna() & (df["service_end_datetime"].astype(str).str.strip() != "")
                invalid = has_end & self._datetime_order_invalid(df, "service_start_datetime", "service_end_datetime")
                count = int(invalid.sum())
                if count:
                    self._add_issue(result, ds_result, "DATETIME_ORDER", ds_name, "service_end_datetime", "Error",
                                    True, False, "Service end must not be before service start.",
                                    "Start > End", "", "End must be >= start", count)

        # Queue period
        if ds_name == "patient_queue_records":
            if "period_start" in df.columns and "period_end" in df.columns:
                invalid = self._datetime_order_invalid(df, "period_start", "period_end")
                count = int(invalid.sum())
                if count:
                    self._add_issue(result, ds_result, "DATETIME_ORDER", ds_name, "period_end", "Error",
                                    True, False, "Period end must be after period start.",
                                    "Start >= End", "", "End must be after start", count)

        # Service schedule times — overnight shifts are valid; skip strict time-order blocking
        if ds_name == "service_schedule":
            pass

        # Roster planned datetimes
        if ds_name == "staff_roster":
            if "planned_start_datetime" in df.columns and "planned_end_datetime" in df.columns:
                invalid = self._datetime_order_invalid(df, "planned_start_datetime", "planned_end_datetime")
                count = int(invalid.sum())
                if count:
                    self._add_issue(result, ds_result, "DATETIME_ORDER", ds_name, "planned_end_datetime", "Error",
                                    True, False, "Planned end datetime must be after planned start datetime.",
                                    "Start >= End", "", "End must be after start", count)

        # Attendance actual datetimes
        if ds_name == "staff_attendance":
            if "actual_start_datetime" in df.columns and "actual_end_datetime" in df.columns:
                has_both = (df["actual_start_datetime"].notna() & (df["actual_start_datetime"].astype(str).str.strip() != "") &
                            df["actual_end_datetime"].notna() & (df["actual_end_datetime"].astype(str).str.strip() != ""))
                invalid = has_both & self._datetime_order_invalid(df, "actual_start_datetime", "actual_end_datetime")
                count = int(invalid.sum())
                if count:
                    self._add_issue(result, ds_result, "DATETIME_ORDER", ds_name, "actual_end_datetime", "Error",
                                    True, False, "Actual end datetime must be after actual start datetime.",
                                    "Start >= End", "", "End must be after start", count)

    def _validate_numeric_ranges(
        self,
        df: pd.DataFrame,
        ds_name: str,
        schema: Dict[str, Any],
        result: ValidationResult,
        ds_result: DatasetValidationResult,
    ) -> None:
        """Validate non-negative and logical numeric constraints."""
        non_negative_fields = {
            "staff_roster": ["planned_hours"],
            "staff_attendance": ["actual_hours"],
            "staffing_requirement": ["required_staff_count", "required_hours"],
            "patient_queue_records": ["arrivals_count", "served_count", "waiting_count",
                                       "avg_wait_minutes", "median_wait_minutes", "max_wait_minutes"],
            "bed_capacity_records": ["bed_licensed", "bed_staffed", "bed_operational",
                                       "bed_occupied", "bed_unavailable", "bed_reserved"],
            "patient_surveys": ["response_weight"],
            "service_schedule": ["planned_hours", "planned_capacity"],
        }

        for field in non_negative_fields.get(ds_name, []):
            if field not in df.columns:
                continue
            numeric = pd.to_numeric(df[field], errors="coerce")
            negative = numeric < 0
            count = int(negative.sum())
            if count:
                self._add_issue(result, ds_result, "NEGATIVE_VALUE", ds_name, field, "Error",
                                True, False, f"Field {field} contains negative values.",
                                "Value < 0", "", "Must be non-negative", count)
                self._add_record_issues(result, ds_name, field, negative, df, schema,
                                        "NEGATIVE_VALUE", "Error", True, f"Negative value in {field}")

    def _validate_bed_capacity(
        self,
        df: pd.DataFrame,
        ds_name: str,
        result: ValidationResult,
        ds_result: DatasetValidationResult,
    ) -> None:
        """Bed-capacity-specific validation."""
        if df.empty:
            return

        # operational > licensed
        if "bed_operational" in df.columns and "bed_licensed" in df.columns:
            op = pd.to_numeric(df["bed_operational"], errors="coerce")
            lic = pd.to_numeric(df["bed_licensed"], errors="coerce")
            invalid = (op > lic) & op.notna() & lic.notna()
            count = int(invalid.sum())
            if count:
                self._add_issue(result, ds_result, "BED_LOGIC", ds_name, "bed_operational", "Error",
                                True, False, "Operational beds should not normally exceed licensed beds.",
                                "Operational > Licensed", "", "Operational <= Licensed", count)

        # occupied > operational with exception metadata
        if "bed_occupied" in df.columns and "bed_operational" in df.columns:
            occ = pd.to_numeric(df["bed_occupied"], errors="coerce")
            op = pd.to_numeric(df["bed_operational"], errors="coerce")
            over_occ = (occ > op) & occ.notna() & op.notna()
            # When occupied > operational, exception_flag must be True and exception_reason populated
            if "exception_flag" in df.columns and "exception_reason" in df.columns:
                exc_flag = self._parse_boolean_series(df["exception_flag"])
                exc_reason = df["exception_reason"].fillna("").astype(str).str.strip()
                missing_exc = over_occ & (~exc_flag | (exc_reason == ""))
                count = int(missing_exc.sum())
                if count:
                    self._add_issue(result, ds_result, "BED_EXCEPTION", ds_name, "exception_reason", "Error",
                                    True, False, "Occupied beds above operational capacity requires exception reason when exception flag is true.",
                                    "Missing exception metadata", "", "Exception flag and reason required", count)
            # occupied > operational is NOT automatically invalid if metadata present
            # so we don't raise an issue for over_occ itself, only for missing metadata

    def _validate_attendance(
        self,
        df: pd.DataFrame,
        ds_name: str,
        loaded_data: Dict[str, pd.DataFrame],
        result: ValidationResult,
        ds_result: DatasetValidationResult,
    ) -> None:
        """Staff-attendance-specific validation."""
        if df.empty:
            return

        staff_df = loaded_data.get("staff_master", pd.DataFrame())
        roster_df = loaded_data.get("staff_roster", pd.DataFrame())

        # Attendance staff exists (FK check already done, but double-check)
        # Attendance aligns with roster where required
        if "roster_id" in df.columns and not roster_df.empty:
            has_roster = df["roster_id"].notna() & (df["roster_id"].astype(str).str.strip() != "")
            roster_ids = set(roster_df["roster_id"].dropna().astype(str)) if "roster_id" in roster_df.columns else set()
            invalid_roster = has_roster & ~df["roster_id"].astype(str).isin(roster_ids)
            count = int(invalid_roster.sum())
            if count:
                self._add_issue(result, ds_result, "ATTENDANCE_ROSTER", ds_name, "roster_id", "Error",
                                True, False, "Attendance roster_id does not match a valid roster record.",
                                "Invalid roster reference", "", "Must reference valid roster", count)

        # Actual hours do not exceed plausible assignment hours without overtime indication
        # (Not calculating overtime; just checking non-negative already done)

        # Status values valid
        if "status" in df.columns:
            valid_statuses = vcl.CATEGORICAL_FIELDS.get("staff_attendance", {}).get("status", [])
            invalid_status = ~df["status"].isna() & ~df["status"].isin(valid_statuses)
            count = int(invalid_status.sum())
            if count:
                self._add_issue(result, ds_result, "INVALID_DOMAIN", ds_name, "status", "Error",
                                True, False, "Attendance status value not in approved domain.",
                                "Invalid status", "", f"Must be one of {valid_statuses}", count)

        # Missing attendance is not imputed (we check for blank status)
        if "status" in df.columns:
            blank_status = df["status"].isna() | (df["status"].astype(str).str.strip() == "")
            count = int(blank_status.sum())
            if count:
                self._add_issue(result, ds_result, "REQUIRED_VALUE_MISSING", ds_name, "status", "Error",
                                True, False, "Attendance status is missing.",
                                "Blank status", "", "Status must be present", count)

        # Reassigned staff have valid destination department where applicable
        if "status" in df.columns and "department_id" in df.columns:
            is_reassigned = df["status"] == "Reassigned"
            missing_dept = is_reassigned & (df["department_id"].isna() | (df["department_id"].astype(str).str.strip() == ""))
            count = int(missing_dept.sum())
            if count:
                self._add_issue(result, ds_result, "ATTENDANCE_REASSIGN", ds_name, "department_id", "Error",
                                True, False, "Reassigned attendance record missing destination department.",
                                "Missing department", "", "Reassigned staff needs department", count)

        # Replacement staff invalid reference
        if "replacement_staff_id" in df.columns and not staff_df.empty:
            has_repl = df["replacement_staff_id"].notna() & (df["replacement_staff_id"].astype(str).str.strip() != "")
            staff_ids = set(staff_df["staff_id"].dropna().astype(str)) if "staff_id" in staff_df.columns else set()
            invalid_repl = has_repl & ~df["replacement_staff_id"].astype(str).isin(staff_ids)
            count = int(invalid_repl.sum())
            if count:
                self._add_issue(result, ds_result, "INVALID_REPLACEMENT_STAFF", ds_name, "replacement_staff_id", "Error",
                                True, False, "Replacement staff_id references invalid staff.",
                                "Invalid replacement", "", "Must reference valid staff", count)

        # Absent records should not show full actual working hours
        if "status" in df.columns and "actual_hours" in df.columns:
            is_absent = df["status"] == "Absent"
            has_hours = pd.to_numeric(df["actual_hours"], errors="coerce") > 0
            invalid_absent = is_absent & has_hours
            count = int(invalid_absent.sum())
            if count:
                self._add_issue(result, ds_result, "ATTENDANCE_ABSENT_HOURS", ds_name, "actual_hours", "Warning",
                                False, True, "Absent attendance record shows positive actual hours.",
                                "Absent with hours > 0", "", "Absent should have 0 hours", count)

        # Not-scheduled records must not create normal working availability
        if "status" in df.columns and "actual_hours" in df.columns:
            is_not_sched = df["status"] == "Not Scheduled"
            has_hours = pd.to_numeric(df["actual_hours"], errors="coerce") > 0
            invalid_ns = is_not_sched & has_hours
            count = int(invalid_ns.sum())
            if count:
                self._add_issue(result, ds_result, "ATTENDANCE_NOT_SCHEDULED", ds_name, "actual_hours", "Warning",
                                False, True, "Not Scheduled attendance record shows positive actual hours.",
                                "Not Scheduled with hours > 0", "", "Not Scheduled should have 0 hours", count)

    def _validate_queue_consistency(
        self,
        df: pd.DataFrame,
        ds_name: str,
        result: ValidationResult,
        ds_result: DatasetValidationResult,
    ) -> None:
        """Queue-record logical consistency."""
        if df.empty:
            return

        # served_count <= arrivals_count
        if "served_count" in df.columns and "arrivals_count" in df.columns:
            served = pd.to_numeric(df["served_count"], errors="coerce")
            arrivals = pd.to_numeric(df["arrivals_count"], errors="coerce")
            invalid = (served > arrivals) & served.notna() & arrivals.notna()
            count = int(invalid.sum())
            if count:
                self._add_issue(result, ds_result, "QUEUE_LOGIC", ds_name, "served_count", "Warning",
                                False, True, "Served count should not exceed arrivals count.",
                                "Served > Arrivals", "", "Served <= Arrivals", count)

        # max_wait >= avg_wait
        if "max_wait_minutes" in df.columns and "avg_wait_minutes" in df.columns:
            max_wait = pd.to_numeric(df["max_wait_minutes"], errors="coerce")
            avg_wait = pd.to_numeric(df["avg_wait_minutes"], errors="coerce")
            invalid = (max_wait < avg_wait) & max_wait.notna() & avg_wait.notna()
            count = int(invalid.sum())
            if count:
                self._add_issue(result, ds_result, "QUEUE_LOGIC", ds_name, "max_wait_minutes", "Warning",
                                False, True, "Max wait minutes should not be lower than average wait minutes.",
                                "Max < Avg", "", "Max >= Avg", count)

    def _validate_encounter_consistency(
        self,
        df: pd.DataFrame,
        ds_name: str,
        result: ValidationResult,
        ds_result: DatasetValidationResult,
    ) -> None:
        """Encounter logical consistency."""
        if df.empty:
            return

        # Cancelled encounters consistent with required fields
        if "status" in df.columns:
            is_cancelled = df["status"] == "Cancelled"
            # cancellation_reason should be present for cancelled
            if "cancellation_reason" in df.columns:
                missing_reason = is_cancelled & (df["cancellation_reason"].isna() | (df["cancellation_reason"].astype(str).str.strip() == ""))
                count = int(missing_reason.sum())
                if count:
                    self._add_issue(result, ds_result, "ENCOUNTER_CANCEL", ds_name, "cancellation_reason", "Warning",
                                    False, True, "Cancelled encounter missing cancellation reason.",
                                    "Missing reason", "", "Cancelled should have reason", count)

        # Left-before-service encounters do not require service timestamps
        if "status" in df.columns:
            is_left = df["status"] == "Left Before Service"
            # No validation needed - schema permits null service timestamps
            pass

        # Served encounters require valid service timestamps
        if "status" in df.columns:
            is_completed = df["status"] == "Completed"
            if "service_start_datetime" in df.columns:
                missing_start = is_completed & (df["service_start_datetime"].isna() | (df["service_start_datetime"].astype(str).str.strip() == ""))
                count = int(missing_start.sum())
                if count:
                    self._add_issue(result, ds_result, "ENCOUNTER_SERVICE", ds_name, "service_start_datetime", "Error",
                                    True, False, "Completed encounter missing service start timestamp.",
                                    "Missing service start", "", "Completed needs service start", count)

    def _validate_complaint_consistency(
        self,
        df: pd.DataFrame,
        ds_name: str,
        result: ValidationResult,
        ds_result: DatasetValidationResult,
    ) -> None:
        """Complaint logical consistency."""
        if df.empty:
            return

        # Duplicate flag and original reference consistent
        if "duplicate_flag" in df.columns and "duplicate_of_complaint_id" in df.columns:
            is_duplicate = self._parse_boolean_series(df["duplicate_flag"])
            missing_orig = is_duplicate & (df["duplicate_of_complaint_id"].isna() | (df["duplicate_of_complaint_id"].astype(str).str.strip() == ""))
            count = int(missing_orig.sum())
            if count:
                self._add_issue(result, ds_result, "COMPLAINT_DUPLICATE", ds_name, "duplicate_of_complaint_id", "Warning",
                                False, True, "Duplicate complaint missing original reference.",
                                "Missing original ID", "", "Duplicate should reference original", count)

    def _validate_survey_consistency(
        self,
        df: pd.DataFrame,
        ds_name: str,
        result: ValidationResult,
        ds_result: DatasetValidationResult,
    ) -> None:
        """Survey logical consistency."""
        if df.empty:
            return

        # Score within scale
        if "score_value" in df.columns and "scale_id" in df.columns:
            score = pd.to_numeric(df["score_value"], errors="coerce")
            scale = df["scale_id"]

            # Define scale ranges
            scale_min = {"SCALE-5PT": 1.0, "SCALE-10PT": 1.0, "SCALE-NPS": 0.0}
            scale_max = {"SCALE-5PT": 5.0, "SCALE-10PT": 10.0, "SCALE-NPS": 10.0}

            for s_id, s_min in scale_min.items():
                s_max = scale_max[s_id]
                mask = (scale == s_id) & ((score < s_min) | (score > s_max)) & score.notna()
                count = int(mask.sum())
                if count:
                    self._add_issue(result, ds_result, "SURVEY_SCALE", ds_name, "score_value", "Error",
                                    True, False, f"Survey score outside declared scale {s_id} ({s_min}-{s_max}).",
                                    "Score out of range", "", f"Score must be between {s_min} and {s_max}", count)

        # Scale minimum and maximum valid (scale_id already domain-checked)
        # Weight positive where supplied
        if "response_weight" in df.columns:
            weight = pd.to_numeric(df["response_weight"], errors="coerce")
            has_weight = df["response_weight"].notna() & (df["response_weight"].astype(str).str.strip() != "")
            invalid_weight = has_weight & (weight <= 0) & weight.notna()
            count = int(invalid_weight.sum())
            if count:
                self._add_issue(result, ds_result, "SURVEY_WEIGHT", ds_name, "response_weight", "Error",
                                True, False, "Survey response weight must be positive where supplied.",
                                "Weight <= 0", "", "Weight must be > 0", count)

    def _validate_privacy(
        self,
        df: pd.DataFrame,
        ds_name: str,
        result: ValidationResult,
        ds_result: DatasetValidationResult,
    ) -> None:
        """Detect prohibited direct-identifier columns."""
        for col in df.columns:
            lower_col = col.lower()
            for prohibited in vcl.PROHIBITED_FIELD_FRAGMENTS:
                if prohibited.lower() in lower_col:
                    # staff_master has approved schema fields (email, phone_number, ic_number, address, staff_name)
                    # that are kept blank. They are not prohibited in that dataset.
                    if ds_name == "staff_master" and col in ["staff_name", "email", "phone_number", "ic_number", "address"]:
                        continue
                    self._add_issue(result, ds_result, "PROHIBITED_FIELD", ds_name, col, "Critical",
                                    True, False, f"Prohibited direct-identifier column {col} detected.",
                                    "Prohibited field name", col, "Column must not contain direct identifiers", 0)
                    break

    def _validate_config_readiness(self) -> List[ValidationIssue]:
        """Check that required configuration files exist."""
        issues: List[ValidationIssue] = []
        config_dir = Path("config")
        expected_configs = [
            "kpi_definition_config.csv",
            "attendance_status_mapping.csv",
            "absence_category_mapping.csv",
            "kpi_threshold_config.csv",
            "scenario_assumption_config.csv",
            "financial_assumption_config.csv",
        ]
        for cfg in expected_configs:
            cfg_path = config_dir / cfg
            if not cfg_path.exists():
                self._issue_counter += 1
                issues.append(ValidationIssue(
                    validation_run_id=self.validation_run_id,
                    issue_id=f"ISS-{self._issue_counter:06d}",
                    test_id="CONFIG_MISSING",
                    dataset_name="",
                    field_name="",
                    issue_type="CONFIG_MISSING",
                    severity="Warning",
                    issue_outcome="Observed",
                    issue_description=f"Configuration file {cfg} not found.",
                    failure_condition="File missing",
                    observed_value="",
                    expected_rule="Configuration file should exist",
                    affected_record_count=0,
                    blocks_processing=False,
                    manual_override_allowed=True,
                    manual_override_required=False,
                    audit_required=True,
                    issue_status="Open",
                ))
        return issues

    def _validate_unexpected_files(self, discovered: List[Path], result: ValidationResult) -> None:
        """Report unexpected CSV files in input directory."""
        expected_names = {f"{ds}.csv" for ds in vcl.DATASET_NAMES}
        for fp in discovered:
            if fp.name not in expected_names:
                self._issue_counter += 1
                result.issues.append(ValidationIssue(
                    validation_run_id=self.validation_run_id,
                    issue_id=f"ISS-{self._issue_counter:06d}",
                    test_id="UNEXPECTED_FILE",
                    dataset_name="",
                    field_name="",
                    issue_type="UNEXPECTED_FILE",
                    severity="Information",
                    issue_outcome="Observed",
                    issue_description=f"Unexpected source file {fp.name} detected.",
                    failure_condition="File not in approved dataset list",
                    observed_value=fp.name,
                    expected_rule="Only approved datasets should be present",
                    affected_record_count=0,
                    blocks_processing=False,
                    manual_override_allowed=True,
                    manual_override_required=False,
                    audit_required=False,
                    issue_status="Open",
                ))

    # -----------------------------------------------------------------------
    # Status determination
    # -----------------------------------------------------------------------

    def _determine_dataset_status(self, ds_result: DatasetValidationResult) -> str:
        """Determine dataset status from unresolved issues."""
        if not ds_result.file_found_flag or not ds_result.file_readable_flag:
            return "Blocked"
        if ds_result.blocking_issue_count > 0:
            # Check if any critical blocking
            has_critical = any(i.severity == "Critical" and i.blocks_processing for i in self._get_issues_for_dataset(ds_result.dataset_name))
            if has_critical:
                return "Blocked"
            return "Rejected"
        # Check for review-required issues (Pending Review severity not used directly; use error non-blocking)
        has_errors = any(i.severity == "Error" and not i.blocks_processing for i in self._get_issues_for_dataset(ds_result.dataset_name))
        if has_errors:
            return "Pending Review"
        has_warnings = any(i.severity == "Warning" for i in self._get_issues_for_dataset(ds_result.dataset_name))
        if has_warnings:
            return "Valid with Warnings"
        return "Valid"

    def _determine_run_status(self, dataset_results: Dict[str, DatasetValidationResult]) -> str:
        """Determine overall run status."""
        statuses = [r.dataset_status for r in dataset_results.values()]
        if any(s == "Blocked" for s in statuses):
            return "Blocked"
        if any(s == "Rejected" for s in statuses):
            return "Failed"
        if any(s in ("Pending Review", "Valid with Warnings") for s in statuses):
            return "Passed with Warnings"
        return "Passed"

    def _get_issues_for_dataset(self, dataset_name: str) -> List[ValidationIssue]:
        """Return issues for a specific dataset from internal tracking."""
        return [i for i in self.issues if i.dataset_name == dataset_name]

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _add_issue(
        self,
        result: ValidationResult,
        ds_result: DatasetValidationResult,
        issue_type: str,
        dataset_name: str,
        field_name: str,
        severity: str,
        blocks_processing: bool,
        manual_override_allowed: bool,
        description: str,
        failure_condition: str,
        observed_value: str,
        expected_rule: str,
        affected_record_count: int,
    ) -> None:
        """Add a validation issue and update dataset counters."""
        self._issue_counter += 1
        issue = ValidationIssue(
            validation_run_id=self.validation_run_id,
            issue_id=f"ISS-{self._issue_counter:06d}",
            test_id=issue_type,
            dataset_name=dataset_name,
            field_name=field_name,
            issue_type=issue_type,
            severity=severity,
            issue_outcome="Observed",
            issue_description=description,
            failure_condition=failure_condition,
            observed_value=str(observed_value)[:500],
            expected_rule=expected_rule,
            affected_record_count=affected_record_count,
            blocks_processing=blocks_processing,
            manual_override_allowed=manual_override_allowed,
            manual_override_required=False,
            audit_required=True,
            issue_status="Open",
        )
        result.issues.append(issue)
        self.issues.append(issue)
        if blocks_processing:
            ds_result.blocking_issue_count += 1
        if severity == "Warning":
            ds_result.warning_issue_count += 1

    def _add_record_issues(
        self,
        result: ValidationResult,
        dataset_name: str,
        field_name: str,
        mask: pd.Series,
        df: pd.DataFrame,
        schema: Dict[str, Any],
        issue_type: str,
        severity: str,
        blocks_processing: bool,
        description: str,
    ) -> None:
        """Add representative record-level issues up to the configured limit."""
        if not self.collect_record_level_issues:
            return
        pk = schema.get("primary_key", "")
        indices = df[mask].index.tolist()
        limit = self.maximum_record_level_examples
        for idx in indices[:limit]:
            self._record_issue_counter += 1
            pk_value = ""
            if pk and pk in df.columns:
                pk_value = str(df.at[idx, pk]) if idx in df.index else ""
            record_issue = RecordValidationIssue(
                validation_run_id=self.validation_run_id,
                record_issue_id=f"REC-{self._record_issue_counter:08d}",
                issue_id=f"ISS-{self._issue_counter:06d}",
                dataset_name=dataset_name,
                primary_key_field=pk,
                primary_key_value=pk_value,
                row_number=int(idx) + 2,  # 1-based with header
                field_name=field_name,
                observed_value=str(df.at[idx, field_name])[:500] if field_name in df.columns and idx in df.index else "",
                issue_description=description,
                severity=severity,
                blocks_processing=blocks_processing,
                resolution_status="Open",
            )
            result.record_issues.append(record_issue)

    def _add_audit_event(
        self,
        result: ValidationResult,
        event_type: str,
        description: str,
        dataset_name: str = "",
        issue_id: str = "",
    ) -> None:
        """Add an audit event."""
        self._audit_counter += 1
        event = ValidationAuditEvent(
            audit_event_id=f"AUD-{self._audit_counter:06d}",
            validation_run_id=self.validation_run_id,
            event_datetime=datetime.now(),
            event_type=event_type,
            dataset_name=dataset_name,
            issue_id=issue_id,
            user_or_process="system",
            previous_status="",
            new_status="",
            event_description=description,
            source_reference="",
        )
        result.audit_events.append(event)

    # -----------------------------------------------------------------------
    # Type-checking helpers
    # -----------------------------------------------------------------------

    def _is_valid_date_series(self, series: pd.Series) -> pd.Series:
        """Return boolean mask of valid date strings."""
        parsed = pd.to_datetime(series, errors="coerce", format="%Y-%m-%d")
        # Also accept ISO format
        parsed2 = pd.to_datetime(series, errors="coerce")
        valid = parsed.notna() | parsed2.notna()
        # Reject datetimes with time components when expecting pure dates
        # Allow if time is 00:00:00
        for idx in series.index:
            if not valid.at[idx]:
                continue
            val = str(series.at[idx])
            try:
                dt = datetime.strptime(val, "%Y-%m-%d")
                valid.at[idx] = True
            except ValueError:
                try:
                    dt = datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
                    valid.at[idx] = dt.hour == 0 and dt.minute == 0 and dt.second == 0
                except ValueError:
                    valid.at[idx] = False
        return valid

    def _is_valid_datetime_series(self, series: pd.Series) -> pd.Series:
        """Return boolean mask of valid datetime strings."""
        parsed = pd.to_datetime(series, errors="coerce")
        return parsed.notna()

    def _is_valid_numeric_series(self, series: pd.Series) -> pd.Series:
        """Return boolean mask of valid numeric strings."""
        parsed = pd.to_numeric(series, errors="coerce")
        return parsed.notna()

    def _is_valid_boolean_series(self, series: pd.Series) -> pd.Series:
        """Return boolean mask of valid boolean strings."""
        valid_values = {"true", "false", "1", "0", "yes", "no", "t", "f"}
        return series.astype(str).str.strip().str.lower().isin(valid_values)

    def _parse_boolean_series(self, series: pd.Series) -> pd.Series:
        """Parse boolean strings to actual booleans."""
        s = series.astype(str).str.strip().str.lower()
        return s.isin({"true", "1", "yes", "t"})

    def _date_order_invalid(self, df: pd.DataFrame, start_col: str, end_col: str) -> pd.Series:
        """Return mask where start date >= end date."""
        start = pd.to_datetime(df[start_col], errors="coerce")
        end = pd.to_datetime(df[end_col], errors="coerce")
        return (start >= end) & start.notna() & end.notna()

    def _datetime_order_invalid(self, df: pd.DataFrame, start_col: str, end_col: str) -> pd.Series:
        """Return mask where start datetime >= end datetime."""
        start = pd.to_datetime(df[start_col], errors="coerce")
        end = pd.to_datetime(df[end_col], errors="coerce")
        return (start >= end) & start.notna() & end.notna()

    def _time_order_invalid(self, df: pd.DataFrame, start_col: str, end_col: str) -> pd.Series:
        """Return mask where start time >= end time."""
        def parse_time(val):
            if pd.isna(val) or str(val).strip() == "":
                return None
            try:
                return datetime.strptime(str(val).strip(), "%H:%M:%S").time()
            except ValueError:
                try:
                    return datetime.strptime(str(val).strip(), "%H:%M").time()
                except ValueError:
                    return None
        start = df[start_col].apply(parse_time)
        end = df[end_col].apply(parse_time)
        invalid = pd.Series(False, index=df.index)
        for idx in df.index:
            s = start.at[idx]
            e = end.at[idx]
            if s is not None and e is not None:
                invalid.at[idx] = s >= e
        return invalid
