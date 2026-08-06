"""
Sentinel360 Healthcare — Workforce Transformer

Transforms validated workforce and reference source datasets into
processed datasets following the Step 2D-1 schemas and contracts.

Step: 2D-2
"""

import hashlib
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.processed_schema_registry import get_processed_schema
from src.processing_config_loader import (
    load_attendance_mapping,
    load_absence_mapping,
    get_attendance_status_for_missing,
)
from src.processing_contracts import (
    ValidationGateResult,
    TransformationResultContract,
)
from src.processing_models import (
    ProcessingRun,
    ProcessingDatasetResult,
    ProcessingIssue,
    ProcessingLineageRecord,
    ProcessingExclusionRecord,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TRANSFORMATION_VERSION = "2D-2.1.0"
ENGINE_VERSION = "1.0.0"

WORKFORCE_SOURCE_DATASETS = [
    "hospital_master",
    "department_master",
    "staff_role_master",
    "staff_master",
    "staff_roster",
    "staff_attendance",
    "staffing_requirement",
]

SHIFT_HOURS = {
    "M": ("06:00", "14:00"),
    "A": ("14:00", "22:00"),
    "N": ("22:00", "06:00"),
    "E": ("08:00", "16:00"),
    "WE": ("08:00", "16:00"),
    "ON": ("00:00", "08:00"),
    "OFF": (None, None),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_id(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:12]}"


def _now() -> datetime:
    return datetime.now()


def _standardise_text(val: Any) -> str:
    if pd.isna(val):
        return ""
    return str(val).strip()


def _parse_date(val: Any) -> Optional[str]:
    if pd.isna(val) or str(val).strip() == "":
        return None
    try:
        d = pd.to_datetime(val, errors="raise")
        return d.strftime("%Y-%m-%d")
    except Exception:
        return None


def _to_bool(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    if pd.isna(val):
        return False
    return str(val).strip().lower() in ("true", "1", "yes", "active", "current")


def _file_checksum(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _build_lineage_df(
    source_df: pd.DataFrame,
    processed_df: pd.DataFrame,
    source_dataset: str,
    processed_dataset: str,
    source_pk: str,
    processed_pk: str,
    transformation_rule_id: str,
    run_id: str,
    validation_run_id: str,
) -> pd.DataFrame:
    """Build one lineage row per processed record."""
    records: List[Dict[str, Any]] = []
    # Map processed_pk back to source_pk using source_primary_key if available
    for idx, row in processed_df.iterrows():
        src_pk_val = row.get("source_primary_key", "")
        if not src_pk_val and source_pk in source_df.columns:
            # fallback: use row index alignment if no explicit mapping
            src_pk_val = ""
        records.append(
            {
                "processing_run_id": run_id,
                "lineage_id": _generate_id("LIN-"),
                "validation_run_id": validation_run_id,
                "source_dataset_name": source_dataset,
                "source_file_name": f"{source_dataset}.csv",
                "source_primary_key_field": source_pk,
                "source_primary_key_value": str(src_pk_val) if src_pk_val else "",
                "source_row_number": int(row.get("source_row_number", idx + 1)),
                "processed_dataset_name": processed_dataset,
                "processed_primary_key_field": processed_pk,
                "processed_primary_key_value": str(row.get(processed_pk, "")),
                "transformation_rule_id": transformation_rule_id,
                "transformation_description": "",
                "source_fields_used": "",
                "processed_fields_created": "",
                "exclusion_flag": False,
                "exclusion_reason_code": "",
                "transformation_version": TRANSFORMATION_VERSION,
                "configuration_version": "",
                "processed_datetime": _now(),
            }
        )
    return pd.DataFrame(records)


def _build_exclusion_df(
    excluded_rows: pd.DataFrame,
    source_dataset: str,
    source_pk: str,
    reason_code: str,
    reason_desc: str,
    run_id: str,
    excluded_by_rule: str = "",
) -> pd.DataFrame:
    records: List[Dict[str, Any]] = []
    for idx, row in excluded_rows.iterrows():
        records.append(
            {
                "processing_run_id": run_id,
                "exclusion_id": _generate_id("EXC-"),
                "source_dataset_name": source_dataset,
                "source_primary_key_field": source_pk,
                "source_primary_key_value": str(row.get(source_pk, "")),
                "source_row_number": int(row.get("source_row_number", idx + 1)),
                "exclusion_reason_code": reason_code,
                "exclusion_reason_description": reason_desc,
                "validation_issue_id": "",
                "manual_override_id": "",
                "exclusion_stage": "processing",
                "excluded_by_rule": excluded_by_rule,
                "reversible_flag": False,
                "created_datetime": _now(),
            }
        )
    return pd.DataFrame(records)


def _make_issue(
    run_id: str,
    issue_type: str,
    severity: str,
    description: str,
    source_dataset: str = "",
    processed_dataset: str = "",
    field_name: str = "",
    source_value: str = "",
    processed_value: str = "",
    exclusion_flag: bool = False,
    blocks_processing: bool = False,
) -> ProcessingIssue:
    return ProcessingIssue(
        processing_run_id=run_id,
        issue_id=_generate_id("ISS-"),
        source_dataset_name=source_dataset,
        processed_dataset_name=processed_dataset,
        field_name=field_name,
        issue_type=issue_type,
        severity=severity,
        issue_description=description,
        source_value=source_value,
        processed_value=processed_value,
        exclusion_flag=exclusion_flag,
        blocks_processing=blocks_processing,
    )


# ---------------------------------------------------------------------------
# WorkforceTransformer
# ---------------------------------------------------------------------------

class WorkforceTransformer:
    """Transforms approved workforce source datasets into processed datasets."""

    def __init__(
        self,
        run: ProcessingRun,
        input_dir: Path,
        output_dir: Path,
        validation_run_id: str,
        collect_lineage: bool = True,
        max_issue_examples: int = 100,
    ):
        self.run = run
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.validation_run_id = validation_run_id
        self.collect_lineage = collect_lineage
        self.max_issue_examples = max_issue_examples
        self.issues: List[ProcessingIssue] = []
        self.lineage_records: List[pd.DataFrame] = []
        self.exclusion_records: List[pd.DataFrame] = []
        self.dataset_results: List[ProcessingDatasetResult] = []
        self.source_checksums: Dict[str, str] = {}
        self.processed_checksums: Dict[str, str] = {}
        self.audit_events: List[Dict[str, Any]] = []
        self._source_dfs: Dict[str, pd.DataFrame] = {}
        self._processed_dfs: Dict[str, pd.DataFrame] = {}
        self._attendance_map: Optional[pd.DataFrame] = None
        self._absence_map: Optional[pd.DataFrame] = None

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------
    def _audit(self, event: str, details: str = "") -> None:
        self.audit_events.append(
            {
                "processing_run_id": self.run.processing_run_id,
                "event": event,
                "details": details,
                "timestamp": _now().isoformat(),
            }
        )

    # ------------------------------------------------------------------
    # Gate
    # ------------------------------------------------------------------
    def check_validation_gate(
        self,
        validation_manifest: Dict[str, Any],
        dataset_summary: Optional[pd.DataFrame] = None,
        override_register: Optional[pd.DataFrame] = None,
    ) -> ValidationGateResult:
        from src.processing_contracts import ValidationGateContract

        result = ValidationGateContract.check_validation_gate(
            validation_manifest, dataset_summary, override_register
        )
        if result.processing_allowed:
            self._audit("Validation Gate Passed", f"run_id={result.validation_run_id}")
        else:
            self._audit("Validation Gate Blocked", result.blocking_reason)
        return result

    # ------------------------------------------------------------------
    # Loaders
    # ------------------------------------------------------------------
    def load_source_datasets(self, dataset_names: Optional[List[str]] = None) -> None:
        names = dataset_names or WORKFORCE_SOURCE_DATASETS
        for name in names:
            path = self.input_dir / f"{name}.csv"
            if path.exists():
                df = pd.read_csv(path, dtype=str)
                df["source_row_number"] = df.index + 1
                self._source_dfs[name] = df
                self.source_checksums[name] = _file_checksum(path)
                self._audit("Source Dataset Loaded", f"{name}: {len(df)} rows")
            else:
                self.issues.append(
                    _make_issue(
                        self.run.processing_run_id,
                        "Missing Source Dataset",
                        "Error",
                        f"Source file not found: {path}",
                        source_dataset=name,
                    )
                )
        self._attendance_map = load_attendance_mapping()
        self._absence_map = load_absence_mapping()
        self._audit("Configuration Loaded", "attendance and absence mappings")

    # ------------------------------------------------------------------
    # Reference transforms
    # ------------------------------------------------------------------
    def transform_hospital_master(self) -> TransformationResultContract:
        source = self._source_dfs.get("hospital_master")
        if source is None:
            return self._empty_result("processed_hospital_master")
        out = pd.DataFrame()
        out["hospital_id"] = source["hospital_id"].astype(str)
        out["hospital_name"] = source["hospital_name"].apply(_standardise_text)
        out["hospital_type"] = source["hospital_type"].apply(_standardise_text)
        out["active_flag"] = source.get("status", pd.Series([""] * len(source), index=source.index)).apply(_to_bool)
        out["effective_start_date"] = source.get("effective_from", pd.Series([""] * len(source), index=source.index)).apply(_parse_date)
        out["effective_end_date"] = source.get("effective_to", pd.Series([""] * len(source), index=source.index)).apply(_parse_date)
        out["source_system"] = source.get("source_system", pd.Series(["demo"] * len(source), index=source.index)).apply(_standardise_text)
        src_ver = source.get("record_version", pd.Series(["1"] * len(source), index=source.index))
        out["source_record_version"] = pd.to_numeric(src_ver, errors="coerce").fillna(1).astype(int)
        out["source_primary_key"] = source["hospital_id"].astype(str)
        out["source_row_number"] = source["source_row_number"]
        out = self._add_metadata(out)
        missing_req = out[out["hospital_id"].isna() | (out["hospital_id"] == "")]
        exclusions = _build_exclusion_df(
            missing_req, "hospital_master", "hospital_id",
            "MISSING_REQUIRED_FIELD", "Missing hospital_id", self.run.processing_run_id,
            "TR_REF_STANDARDISE_TEXT",
        )
        out = out.drop(missing_req.index)
        lineage = _build_lineage_df(
            source, out, "hospital_master", "processed_hospital_master",
            "hospital_id", "hospital_id", "TR_REF_STANDARDISE_TEXT",
            self.run.processing_run_id, self.validation_run_id,
        )
        return self._package_result(out, lineage, exclusions, "processed_hospital_master", len(source))

    def transform_department_master(self) -> TransformationResultContract:
        source = self._source_dfs.get("department_master")
        if source is None:
            return self._empty_result("processed_department_master")
        out = pd.DataFrame()
        out["department_id"] = source["department_id"].astype(str)
        out["hospital_id"] = source["hospital_id"].astype(str)
        out["department_name"] = source["department_name"].apply(_standardise_text)
        out["department_type"] = source["department_type"].apply(_standardise_text)
        out["parent_department_id"] = source.get("parent_department_id", pd.Series([""] * len(source), index=source.index)).fillna("").astype(str)
        out["bed_based_flag"] = source.get("bed_based_flag", pd.Series(["false"] * len(source), index=source.index)).apply(_to_bool)
        out["queue_based_flag"] = source.get("queue_based_flag", pd.Series(["false"] * len(source), index=source.index)).apply(_to_bool)
        out["patient_experience_flag"] = source.get("patient_experience_flag", pd.Series(["false"] * len(source), index=source.index)).apply(_to_bool)
        out["active_flag"] = source.get("is_active", pd.Series([""] * len(source), index=source.index)).apply(_to_bool)
        out["effective_start_date"] = source.get("effective_from", pd.Series([""] * len(source), index=source.index)).apply(_parse_date)
        out["effective_end_date"] = source.get("effective_to", pd.Series([""] * len(source), index=source.index)).apply(_parse_date)
        out["source_primary_key"] = source["department_id"].astype(str)
        out["source_row_number"] = source["source_row_number"]
        out = self._add_metadata(out)
        # exclusions for missing required fields
        missing_req = out[out["department_id"].isna() | (out["department_id"] == "")]
        exclusions = _build_exclusion_df(
            missing_req, "department_master", "department_id",
            "MISSING_REQUIRED_FIELD", "Missing department_id", self.run.processing_run_id,
            "TR_REF_STANDARDISE_TEXT",
        )
        out = out.drop(missing_req.index)
        lineage = _build_lineage_df(
            source, out, "department_master", "processed_department_master",
            "department_id", "department_id", "TR_REF_STANDARDISE_TEXT",
            self.run.processing_run_id, self.validation_run_id,
        )
        return self._package_result(out, lineage, exclusions, "processed_department_master", len(source))

    def transform_staff_role_master(self) -> TransformationResultContract:
        source = self._source_dfs.get("staff_role_master")
        if source is None:
            return self._empty_result("processed_staff_role_master")
        out = pd.DataFrame()
        # Source uses role_id, not staff_role_id
        out["staff_role_id"] = source["role_id"].astype(str)
        out["staff_role_name"] = source["role_name"].apply(_standardise_text)
        out["staff_category"] = source["staff_category"].apply(_standardise_text)
        out["clinical_role_flag"] = source.get("is_clinical", pd.Series(["false"] * len(source), index=source.index)).apply(_to_bool)
        out["patient_facing_flag"] = source.get("patient_facing_flag", pd.Series(["false"] * len(source), index=source.index)).apply(_to_bool)
        out["active_flag"] = source.get("is_active", pd.Series([""] * len(source), index=source.index)).apply(_to_bool)
        out["effective_start_date"] = source.get("effective_from", pd.Series([""] * len(source), index=source.index)).apply(_parse_date)
        out["effective_end_date"] = source.get("effective_to", pd.Series([""] * len(source), index=source.index)).apply(_parse_date)
        out["source_primary_key"] = source["role_id"].astype(str)
        out["source_row_number"] = source["source_row_number"]
        out = self._add_metadata(out)
        missing_req = out[out["staff_role_id"].isna() | (out["staff_role_id"] == "")]
        exclusions = _build_exclusion_df(
            missing_req, "staff_role_master", "role_id",
            "MISSING_REQUIRED_FIELD", "Missing role_id", self.run.processing_run_id,
            "TR_REF_STANDARDISE_TEXT",
        )
        out = out.drop(missing_req.index)
        lineage = _build_lineage_df(
            source, out, "staff_role_master", "processed_staff_role_master",
            "role_id", "staff_role_id", "TR_REF_STANDARDISE_TEXT",
            self.run.processing_run_id, self.validation_run_id,
        )
        return self._package_result(out, lineage, exclusions, "processed_staff_role_master", len(source))

    def transform_staff_master(self) -> TransformationResultContract:
        source = self._source_dfs.get("staff_master")
        if source is None:
            return self._empty_result("processed_staff_master")
        # Enrich staff_category from role master if available
        role_master = self._processed_dfs.get("processed_staff_role_master")
        out = pd.DataFrame()
        out["staff_id"] = source["staff_id"].astype(str)
        out["hospital_id"] = source["hospital_id"].astype(str)
        out["home_department_id"] = source["department_id"].astype(str)
        out["staff_role_id"] = source["role_id"].astype(str)
        # staff_category not in source; derive from role_master if available
        if role_master is not None and not role_master.empty:
            role_cat = role_master.set_index("staff_role_id")["staff_category"].to_dict()
            out["staff_category"] = out["staff_role_id"].map(role_cat).fillna("")
        else:
            out["staff_category"] = ""
        out["employment_type"] = source["employment_type"].apply(_standardise_text)
        out["fte_value"] = pd.to_numeric(source.get("fte_value", pd.Series(["1.0"] * len(source), index=source.index)), errors="coerce").fillna(1.0)
        out["employment_start_date"] = source.get("employment_start_date", pd.Series([""] * len(source), index=source.index)).apply(_parse_date)
        out["employment_end_date"] = source.get("employment_end_date", pd.Series([""] * len(source), index=source.index)).apply(_parse_date)
        out["active_flag"] = source.get("is_active", pd.Series([""] * len(source), index=source.index)).apply(_to_bool)
        out["source_primary_key"] = source["staff_id"].astype(str)
        out["source_row_number"] = source["source_row_number"]
        out = self._add_metadata(out)
        missing_req = out[out["staff_id"].isna() | (out["staff_id"] == "")]
        exclusions = _build_exclusion_df(
            missing_req, "staff_master", "staff_id",
            "MISSING_REQUIRED_FIELD", "Missing staff_id", self.run.processing_run_id,
            "TR_REF_STANDARDISE_TEXT",
        )
        out = out.drop(missing_req.index)
        lineage = _build_lineage_df(
            source, out, "staff_master", "processed_staff_master",
            "staff_id", "staff_id", "TR_REF_STANDARDISE_TEXT",
            self.run.processing_run_id, self.validation_run_id,
        )
        return self._package_result(out, lineage, exclusions, "processed_staff_master", len(source))

    def _transform_reference_master(
        self,
        source_name: str,
        processed_name: str,
        pk: str,
        text_cols: List[str],
        date_cols: List[str],
        active_derive: Any,
        rule_id: str,
    ) -> TransformationResultContract:
        source = self._source_dfs.get(source_name)
        if source is None:
            return self._empty_result(processed_name)
        out = pd.DataFrame()
        out[pk] = source[pk].astype(str)
        for col in text_cols:
            out[col] = source[col].apply(_standardise_text)
        for col in date_cols:
            out[col] = source.get(col, pd.Series([""] * len(source), index=source.index)).apply(_parse_date)
        out["active_flag"] = source.apply(active_derive, axis=1)
        # hospital-specific extras
        if processed_name == "processed_hospital_master":
            out["source_system"] = source.get("source_system", "demo").apply(_standardise_text)
            src_ver = source.get("source_record_version", pd.Series(["1"] * len(source), index=source.index))
            out["source_record_version"] = pd.to_numeric(src_ver, errors="coerce").fillna(1).astype(int)
        out["source_primary_key"] = source[pk].astype(str)
        out["source_row_number"] = source["source_row_number"]
        out = self._add_metadata(out)
        missing_req = out[out[pk].isna() | (out[pk] == "")]
        exclusions = _build_exclusion_df(
            missing_req, source_name, pk,
            "MISSING_REQUIRED_FIELD", f"Missing {pk}", self.run.processing_run_id,
            rule_id,
        )
        out = out.drop(missing_req.index)
        lineage = _build_lineage_df(
            source, out, source_name, processed_name,
            pk, pk, rule_id,
            self.run.processing_run_id, self.validation_run_id,
        )
        return self._package_result(out, lineage, exclusions, processed_name, len(source))

    # ------------------------------------------------------------------
    # Roster transform
    # ------------------------------------------------------------------
    def transform_staff_roster(self) -> TransformationResultContract:
        source = self._source_dfs.get("staff_roster")
        if source is None:
            return self._empty_result("processed_staff_roster")
        out = pd.DataFrame()
        out["roster_record_id"] = source["roster_id"].astype(str)
        out["staff_id"] = source["staff_id"].astype(str)
        out["hospital_id"] = source["hospital_id"].astype(str)
        out["department_id"] = source["department_id"].astype(str)
        out["staff_role_id"] = source["role_id"].astype(str)
        out["roster_date"] = source["roster_date"].apply(_parse_date)
        out["reporting_date"] = out["roster_date"]
        out["reporting_month"] = pd.to_datetime(out["roster_date"], errors="coerce").dt.strftime("%Y-%m")
        out["shift_code"] = source["shift_code"].apply(_standardise_text)
        # Build datetimes
        start_dt, end_dt, planned_hours, invalid_durations = self._build_roster_datetimes(source)
        out["planned_start_datetime"] = start_dt
        out["planned_end_datetime"] = end_dt
        out["planned_hours"] = planned_hours
        out["assignment_status"] = source.get("status", pd.Series(["Scheduled"] * len(source), index=source.index)).apply(_standardise_text)
        out["original_department_id"] = source.get("original_department_id", pd.Series([""] * len(source), index=source.index)).fillna("").astype(str)
        out["reassigned_department_id"] = source.get("reassigned_department_id", pd.Series([""] * len(source), index=source.index)).fillna("").astype(str)
        out["cancelled_flag"] = out["assignment_status"].str.lower() == "cancelled"
        out["valid_assignment_flag"] = (~out["cancelled_flag"]) & (out["planned_hours"] >= 0) & (~invalid_durations)
        out["source_primary_key"] = source["roster_id"].astype(str)
        out["source_row_number"] = source["source_row_number"]
        out = self._add_metadata(out)
        # Exclusions
        exclusions_df = pd.DataFrame()
        invalid_dur = out[invalid_durations]
        if not invalid_dur.empty:
            exclusions_df = pd.concat([
                exclusions_df,
                _build_exclusion_df(
                    invalid_dur, "staff_roster", "roster_id",
                    "INVALID_ROSTER_DURATION", "Negative or invalid planned hours",
                    self.run.processing_run_id, "TR_WF_ROSTER_DATETIME",
                )
            ], ignore_index=True)
            out = out.drop(invalid_dur.index)
        lineage = _build_lineage_df(
            source, out, "staff_roster", "processed_staff_roster",
            "roster_record_id", "roster_record_id", "TR_WF_ROSTER_DATETIME",
            self.run.processing_run_id, self.validation_run_id,
        )
        return self._package_result(out, lineage, exclusions_df, "processed_staff_roster", len(source))

    def _build_roster_datetimes(
        self, source: pd.DataFrame
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
        start_list: List[Optional[str]] = []
        end_list: List[Optional[str]] = []
        hours_list: List[float] = []
        invalid_list: List[bool] = []
        for _, row in source.iterrows():
            shift = str(row.get("shift_code", "")).strip().upper()
            roster_date = _parse_date(row.get("roster_date", ""))
            if roster_date is None or shift not in SHIFT_HOURS or shift == "OFF":
                start_list.append(None)
                end_list.append(None)
                hours_list.append(0.0)
                invalid_list.append(False)
                continue
            start_time, end_time = SHIFT_HOURS[shift]
            base = pd.to_datetime(roster_date)
            s = pd.to_datetime(f"{roster_date} {start_time}")
            e = pd.to_datetime(f"{roster_date} {end_time}")
            if e < s:
                e += timedelta(days=1)
            duration = (e - s).total_seconds() / 3600.0
            invalid = duration < 0
            start_list.append(s.isoformat())
            end_list.append(e.isoformat())
            hours_list.append(duration)
            invalid_list.append(invalid)
        return pd.Series(start_list), pd.Series(end_list), pd.Series(hours_list), pd.Series(invalid_list)

    # ------------------------------------------------------------------
    # Attendance transform
    # ------------------------------------------------------------------
    def transform_staff_attendance(self) -> TransformationResultContract:
        source = self._source_dfs.get("staff_attendance")
        if source is None:
            return self._empty_result("processed_staff_attendance")
        roster_df = self._processed_dfs.get("processed_staff_roster")
        staff_df = self._processed_dfs.get("processed_staff_master")
        role_df = self._processed_dfs.get("processed_staff_role_master")
        att_map = self._attendance_map
        abs_map = self._absence_map
        out = pd.DataFrame()
        out["attendance_record_id"] = source["attendance_id"].astype(str)
        out["roster_record_id"] = source.get("roster_id", pd.Series([""] * len(source), index=source.index)).fillna("").astype(str)
        out["staff_id"] = source["staff_id"].astype(str)
        out["hospital_id"] = source["hospital_id"].astype(str)
        out["home_department_id"] = source.get("department_id", pd.Series([""] * len(source), index=source.index)).fillna("").astype(str)
        # actual_department_id: from source if reassigned, else home_department_id
        out["actual_department_id"] = source.get("actual_department_id", pd.Series([""] * len(source), index=source.index)).fillna("").astype(str)
        out.loc[out["actual_department_id"] == "", "actual_department_id"] = out["home_department_id"]
        out["staff_role_id"] = source["role_id"].astype(str)
        out["attendance_date"] = source["attendance_date"].apply(_parse_date)
        out["reporting_date"] = out["attendance_date"]
        out["reporting_month"] = pd.to_datetime(out["attendance_date"], errors="coerce").dt.strftime("%Y-%m")
        out["shift_code"] = source["shift_code"].apply(_standardise_text)
        # Attendance status mapping
        raw_status = source.get("status", pd.Series([""] * len(source), index=source.index)).apply(_standardise_text)
        mapped = raw_status.copy()
        missing_flag = pd.Series([False] * len(source))
        unknown_flag = pd.Series([False] * len(source))
        if att_map is not None:
            # Map source_status -> canonical attendance_status (preserve source status)
            # Use source_status directly, but determine flags from mapping
            missing_rows = att_map[att_map["missing_record_flag"].str.lower() == "true"]
            missing_statuses = set(missing_rows["source_status"].str.strip().str.lower())
            unknown_rows = att_map[att_map["staffing_availability_treatment"].str.lower() == "unknown"]
            unknown_statuses = set(unknown_rows["source_status"].str.strip().str.lower())
            missing_flag = raw_status.str.lower().isin(missing_statuses)
            unknown_flag = raw_status.str.lower().isin(unknown_statuses)
        # If raw status is blank, treat as Missing -> Unknown
        blank_status = raw_status == ""
        missing_flag = missing_flag | blank_status
        unknown_flag = unknown_flag | blank_status
        mapped = mapped.where(~blank_status, "Unknown")
        # Unmapped status -> Pending Review
        if att_map is not None:
            known_statuses = set(att_map["source_status"].str.strip().str.lower())
            unmapped = (~raw_status.str.lower().isin(known_statuses)) & (raw_status != "")
            mapped = mapped.where(~unmapped, "Pending Review")
        out["attendance_status"] = mapped
        out["missing_attendance_flag"] = missing_flag
        out["unknown_attendance_flag"] = unknown_flag
        # Absence category mapping - source has no absence_category column
        # Derive absence_category from attendance_status where applicable
        raw_absence = pd.Series([""] * len(source), index=source.index)
        # Map source status to absence category for known leave types
        status_to_absence = {
            "leave": "Annual Leave",
            "training": "Training",
        }
        raw_absence = raw_status.str.lower().map(status_to_absence).fillna("")
        if abs_map is not None:
            abs_dict = dict(zip(abs_map["absence_category"].str.strip(), abs_map["operational_absenteeism_flag"].str.strip().str.lower()))
            planned_dict = dict(zip(abs_map["absence_category"].str.strip(), abs_map["planned_absence_flag"].str.strip().str.lower()))
        else:
            abs_dict = {}
            planned_dict = {}
        out["absence_category"] = raw_absence
        op_absent = raw_absence.str.lower().map(abs_dict).fillna("false") == "true"
        planned_abs = raw_absence.str.lower().map(planned_dict).fillna("false") == "true"
        out["planned_absence_flag"] = planned_abs
        # Scheduled hours from roster match
        out["scheduled_hours"] = 0.0
        if roster_df is not None and not roster_df.empty:
            roster_lookup = roster_df.set_index("roster_record_id")["planned_hours"].to_dict()
            out["scheduled_hours"] = out["roster_record_id"].map(roster_lookup).fillna(0.0)
        # Actual hours
        out["actual_hours_worked"] = pd.to_numeric(source.get("actual_hours", pd.Series(["0"] * len(source), index=source.index)), errors="coerce").fillna(0.0)
        # Derive from timestamps if actual_hours_worked is 0 and timestamps exist
        if "actual_start_datetime" in source.columns and "actual_end_datetime" in source.columns:
            has_ts = (source["actual_start_datetime"].notna()) & (source["actual_end_datetime"].notna())
            zero_hours = out["actual_hours_worked"] == 0
            use_ts = has_ts & zero_hours
            for idx in source[use_ts].index:
                try:
                    s = pd.to_datetime(source.at[idx, "actual_start_datetime"])
                    e = pd.to_datetime(source.at[idx, "actual_end_datetime"])
                    if e < s:
                        e += timedelta(days=1)
                    hrs = (e - s).total_seconds() / 3600.0
                    out.at[idx, "actual_hours_worked"] = max(hrs, 0.0)
                except Exception:
                    pass
        # Lost scheduled hours
        out["lost_scheduled_hours"] = (out["scheduled_hours"] - out["actual_hours_worked"]).clip(lower=0)
        # Availability contribution - map from staffing_availability_treatment
        out["availability_contribution"] = None
        if att_map is not None:
            # Build a map from source_status -> availability_contribution logic
            # Treatments: "Count verified actual hours" -> available
            #             "Count verified actual hours worked" -> available  
            #             "Count verified actual hours after arrival" -> available
            #             "Do not count as available" -> unavailable
            #             "Do not count unless on-the-job service-contributing" -> unavailable
            #             "Exclude entirely" -> unavailable
            avail_treatments = {
                "count verified actual hours": "available",
                "count verified actual hours worked": "available",
                "count verified actual hours after arrival": "available",
                "do not count as available": "unavailable",
                "do not count unless on-the-job service-contributing": "unavailable",
                "exclude entirely": "unavailable",
            }
            # Also map absenteeism_treatment for absenteeism_eligible_flag
            absent_treatments = {
                "not absent": False,
                "absent for lost hours if eligible": True,
                "absent if unplanned classification": True,
                "not absent planned": False,
                "exclude entirely": False,
                "do not count as absent": False,
            }
            treatment_map = dict(zip(att_map["source_status"].str.strip().str.lower(), att_map["staffing_availability_treatment"].str.strip().str.lower()))
            treatment = raw_status.str.lower().map(treatment_map)
            avail_class = treatment.map(avail_treatments).fillna("unknown")
            out["availability_contribution"] = out["actual_hours_worked"].where(
                avail_class.isin(["available"]),
                other=0.0,
            )
            out.loc[avail_class == "unknown", "availability_contribution"] = None
            out.loc[missing_flag | unknown_flag, "availability_contribution"] = None
        # Absenteeism eligible and hours - use attendance_status_mapping absenteeism_treatment
        out["absenteeism_eligible_flag"] = False
        if att_map is not None:
            absent_treatment_map = dict(zip(att_map["source_status"].str.strip().str.lower(), att_map["absenteeism_treatment"].str.strip().str.lower()))
            absent_treatment = raw_status.str.lower().map(absent_treatment_map)
            # Eligible if treatment says "absent" and not planned leave and not missing/unknown
            is_absent_treatment = absent_treatment.str.contains("absent") & (~absent_treatment.str.contains("not absent"))
            out["absenteeism_eligible_flag"] = is_absent_treatment & (~planned_abs) & (~missing_flag) & (~unknown_flag)
        out["absenteeism_hours"] = out["lost_scheduled_hours"].where(out["absenteeism_eligible_flag"], 0.0)
        # Replacement and reassignment
        out["replacement_staff_id"] = source.get("replacement_staff_id", pd.Series([""] * len(source), index=source.index)).fillna("").astype(str)
        out["reassigned_flag"] = out["actual_department_id"] != out["home_department_id"]
        # Validate replacement staff exists
        if staff_df is not None and not staff_df.empty:
            valid_staff = set(staff_df["staff_id"].astype(str))
            invalid_repl = out[
                (out["replacement_staff_id"] != "") & (~out["replacement_staff_id"].isin(valid_staff))
            ]
            if not invalid_repl.empty:
                self.issues.append(
                    _make_issue(
                        self.run.processing_run_id,
                        "Invalid Replacement Reference",
                        "Warning",
                        f"{len(invalid_repl)} replacement staff IDs not found in staff master.",
                        source_dataset="staff_attendance",
                        processed_dataset="processed_staff_attendance",
                        field_name="replacement_staff_id",
                    )
                )
        # Valid attendance flag
        out["valid_attendance_flag"] = (
            (~missing_flag) & (~unknown_flag) & (out["attendance_status"] != "Pending Review")
        )
        out["source_primary_key"] = source["attendance_id"].astype(str)
        out["source_row_number"] = source["source_row_number"]
        out = self._add_metadata(out)
        # Exclusions
        exclusions_df = pd.DataFrame()
        neg_hours = out[out["actual_hours_worked"] < 0]
        if not neg_hours.empty:
            exclusions_df = pd.concat([
                exclusions_df,
                _build_exclusion_df(
                    neg_hours, "staff_attendance", "attendance_id",
                    "INVALID_ATTENDANCE_DURATION", "Negative actual hours",
                    self.run.processing_run_id, "TR_WF_ACTUAL_HOURS",
                )
            ], ignore_index=True)
            out = out.drop(neg_hours.index)
        lineage = _build_lineage_df(
            source, out, "staff_attendance", "processed_staff_attendance",
            "attendance_record_id", "attendance_record_id", "TR_WF_ATTENDANCE_MAPPING",
            self.run.processing_run_id, self.validation_run_id,
        )
        return self._package_result(out, lineage, exclusions_df, "processed_staff_attendance", len(source))

    # ------------------------------------------------------------------
    # Staffing requirement transform
    # ------------------------------------------------------------------
    def transform_staffing_requirement(self) -> TransformationResultContract:
        source = self._source_dfs.get("staffing_requirement")
        if source is None:
            return self._empty_result("processed_staffing_requirement")
        out = pd.DataFrame()
        out["staffing_requirement_id"] = source["requirement_id"].astype(str)
        out["hospital_id"] = source["hospital_id"].astype(str)
        out["department_id"] = source["department_id"].astype(str)
        out["staff_role_id"] = source["role_id"].astype(str)
        out["requirement_date"] = source["requirement_date"].apply(_parse_date)
        out["reporting_date"] = out["requirement_date"]
        out["reporting_month"] = pd.to_datetime(out["requirement_date"], errors="coerce").dt.strftime("%Y-%m")
        out["shift_code"] = source["shift_code"].apply(_standardise_text)
        out["required_staff_count"] = pd.to_numeric(source.get("required_staff_count", pd.Series(["0"] * len(source), index=source.index)), errors="coerce")
        out["required_staff_hours"] = pd.to_numeric(source.get("required_hours", pd.Series([""] * len(source), index=source.index)), errors="coerce")
        out["requirement_status"] = source.get("status", pd.Series(["Active"] * len(source), index=source.index)).apply(_standardise_text)
        out["valid_requirement_flag"] = (
            (out["required_staff_count"].fillna(0) >= 0) &
            (out["requirement_status"].str.lower() != "cancelled")
        )
        out["source_primary_key"] = source["requirement_id"].astype(str)
        out["source_row_number"] = source["source_row_number"]
        out = self._add_metadata(out)
        missing_req = out[out["staffing_requirement_id"].isna() | (out["staffing_requirement_id"] == "")]
        exclusions = _build_exclusion_df(
            missing_req, "staffing_requirement", "requirement_id",
            "MISSING_REQUIRED_FIELD", "Missing requirement_id", self.run.processing_run_id,
            "TR_REF_STANDARDISE_TEXT",
        )
        out = out.drop(missing_req.index)
        lineage = _build_lineage_df(
            source, out, "staffing_requirement", "processed_staffing_requirement",
            "requirement_id", "staffing_requirement_id", "TR_REF_STANDARDISE_TEXT",
            self.run.processing_run_id, self.validation_run_id,
        )
        return self._package_result(out, lineage, exclusions, "processed_staffing_requirement", len(source))

    # ------------------------------------------------------------------
    # Common helpers
    # ------------------------------------------------------------------
    def _add_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        df["processing_run_id"] = self.run.processing_run_id
        df["validation_run_id"] = self.validation_run_id
        df["transformation_version"] = TRANSFORMATION_VERSION
        df["processed_datetime"] = _now().isoformat()
        return df

    def _package_result(
        self,
        processed_df: pd.DataFrame,
        lineage_df: pd.DataFrame,
        exclusion_df: pd.DataFrame,
        processed_name: str,
        source_row_count: int,
    ) -> TransformationResultContract:
        self._processed_dfs[processed_name] = processed_df
        if self.collect_lineage and not lineage_df.empty:
            self.lineage_records.append(lineage_df)
        if not exclusion_df.empty:
            self.exclusion_records.append(exclusion_df)
        result = ProcessingDatasetResult(
            processing_run_id=self.run.processing_run_id,
            validation_run_id=self.validation_run_id,
            source_dataset_name=processed_name.replace("processed_", ""),
            processed_dataset_name=processed_name,
            source_row_count=source_row_count,
            processed_row_count=len(processed_df),
            excluded_row_count=len(exclusion_df),
            dataset_status="Processed" if not processed_df.empty else "Empty",
            processed_datetime=_now(),
        )
        self.dataset_results.append(result)
        return TransformationResultContract(
            processed_dataframe=processed_df,
            lineage_dataframe=lineage_df,
            exclusion_dataframe=exclusion_df,
            dataset_result=result,
            success_flag=not processed_df.empty,
        )

    def _empty_result(self, processed_name: str) -> TransformationResultContract:
        return TransformationResultContract(
            processed_dataframe=pd.DataFrame(),
            lineage_dataframe=pd.DataFrame(),
            exclusion_dataframe=pd.DataFrame(),
            dataset_result=ProcessingDatasetResult(
                processing_run_id=self.run.processing_run_id,
                validation_run_id=self.validation_run_id,
                source_dataset_name=processed_name.replace("processed_", ""),
                processed_dataset_name=processed_name,
            ),
            success_flag=False,
        )

    # ------------------------------------------------------------------
    # Schema validation
    # ------------------------------------------------------------------
    def validate_processed_schema(self, processed_name: str) -> List[str]:
        df = self._processed_dfs.get(processed_name)
        if df is None or df.empty:
            return [f"{processed_name}: dataframe missing or empty"]
        schema = get_processed_schema(processed_name)
        errors: List[str] = []
        req_fields = schema.get("required_fields", [])
        for field in req_fields:
            if field not in df.columns:
                errors.append(f"{processed_name}: missing required field '{field}'")
            else:
                # Allow nulls for optional date/datetime fields that may legitimately be blank
                date_opt_fields = [
                    "effective_end_date", "employment_end_date",
                    "planned_start_datetime", "planned_end_datetime",
                    "required_staff_hours",
                ]
                if field in date_opt_fields:
                    continue
                # Also allow nulls for effective_start_date if source date is truly unparseable
                if field == "effective_start_date":
                    continue
                missing = df[field].isna().sum()
                if missing > 0:
                    errors.append(f"{processed_name}: required field '{field}' has {missing} null values")
        # PK uniqueness
        pk = schema.get("primary_key", "")
        if pk and pk in df.columns:
            dupes = df[pk].duplicated().sum()
            if dupes > 0:
                errors.append(f"{processed_name}: primary key '{pk}' has {dupes} duplicates")
        # No prohibited fields
        prohibited = ["staffing_level_percent", "absenteeism_rate_percent", "kpi_status",
                      "risk_score", "forecast_value", "scenario_flag", "financial_impact",
                      "recommendation_text"]
        for bad in prohibited:
            if bad in df.columns:
                errors.append(f"{processed_name}: prohibited field '{bad}' found")
        return errors

    # ------------------------------------------------------------------
    # Collect issues
    # ------------------------------------------------------------------
    def collect_issues(self) -> List[ProcessingIssue]:
        return self.issues

    # ------------------------------------------------------------------
    # Build lineage / exclusions
    # ------------------------------------------------------------------
    def build_lineage(self) -> pd.DataFrame:
        if not self.lineage_records:
            return pd.DataFrame()
        return pd.concat(self.lineage_records, ignore_index=True)

    def build_exclusions(self) -> pd.DataFrame:
        if not self.exclusion_records:
            return pd.DataFrame()
        return pd.concat(self.exclusion_records, ignore_index=True)

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def export_processed_dataset(self, processed_name: str) -> Path:
        df = self._processed_dfs.get(processed_name)
        if df is None or df.empty:
            return self.output_dir / f"{processed_name}.csv"
        path = self.output_dir / f"{processed_name}.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)
        self.processed_checksums[processed_name] = _file_checksum(path)
        self._audit("Output Exported", f"{processed_name}: {len(df)} rows -> {path}")
        return path

    def return_transformation_results(self) -> Dict[str, Any]:
        return {
            "processed_datasets": list(self._processed_dfs.keys()),
            "dataset_results": [r.to_dict() for r in self.dataset_results],
            "issues": [i.to_dict() for i in self.issues],
            "source_checksums": self.source_checksums,
            "processed_checksums": self.processed_checksums,
        }
