"""
Sentinel360 Healthcare — Operational Daily Builder

Phase 1, Step 2D-5: Build processed_operational_daily.csv from
approved preparation-level daily datasets.

Rules:
- Union daily spine from workforce, patient-flow, patient-experience.
- Do not calculate official KPI values or status.
- Preserve null when absence means unknown.
- Distinguish zero from missing.
- Create lineage for every output row.
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
from src.processing_models import ProcessingIssue

BUILDER_VERSION = "2D-5-1.0.0"
TRANSFORMATION_NAME = "operational_daily_builder"

# Mapping from operational daily field -> (source_dataset, source_field, aggregation)
# aggregation: "sum", "first", "flag_or", None
WORKFORCE_FIELD_MAP = {
    "planned_staff_count": ("workforce", "rostered_staff_count", "sum"),
    "available_staff_count": ("workforce", "verified_available_staff_count", "sum"),
    "present_staff_count": ("workforce", "verified_available_staff_count", "sum"),
    "absent_staff_count": ("workforce", "absent_event_count", "sum"),
    "approved_leave_count": ("workforce", "planned_leave_event_count", "sum"),
    "unapproved_absence_count": ("workforce", "absent_event_count", "sum"),
    "reassigned_staff_count": ("workforce", "reassigned_in_count", "sum"),
    "replacement_staff_count": ("workforce", "replacement_staff_count", "sum"),
}

PATIENT_FLOW_FIELD_MAP = {
    "encounter_record_count": ("patient_flow", "encounter_count", "first"),
    "completed_encounter_count": ("patient_flow", "completed_encounter_count", "first"),
    "cancelled_encounter_count": ("patient_flow", "cancelled_encounter_count", "first"),
    "lwbs_encounter_count": ("patient_flow", "left_before_service_count", "first"),
    "queue_record_count": ("patient_flow", "queue_arrivals_count", "first"),
    "queue_count_total": ("patient_flow", "queue_arrivals_count", "first"),
    "occupied_beds": ("patient_flow", "occupied_beds", "first"),
    "operational_beds": ("patient_flow", "operational_beds", "first"),
    "licensed_beds": ("patient_flow", "licensed_beds", "first"),
    "overcapacity_count": ("patient_flow", "beds_above_operational_capacity", "first"),
    "scheduled_session_count": ("patient_flow", "planned_service_session_count", "first"),
    "cancelled_session_count": ("patient_flow", "cancelled_service_session_count", "first"),
    "reduced_session_count": ("patient_flow", "reduced_service_session_count", "first"),
    "extended_session_count": ("patient_flow", "extended_service_session_count", "first"),
}

PATIENT_EXPERIENCE_FIELD_MAP = {
    "complaint_record_count": ("patient_experience", "complaint_record_count", "first"),
    "complaint_valid_record_count": ("patient_experience", "complaint_valid_record_count", "first"),
    "complaint_high_severity_count": ("patient_experience", "complaint_high_severity_count", "first"),
    "complaint_medium_severity_count": ("patient_experience", "complaint_medium_severity_count", "first"),
    "complaint_low_severity_count": ("patient_experience", "complaint_low_severity_count", "first"),
    "complaint_open_source_count": ("patient_experience", "complaint_open_source_count", "first"),
    "complaint_resolved_source_count": ("patient_experience", "complaint_resolved_source_count", "first"),
    "survey_record_count": ("patient_experience", "survey_record_count", "first"),
    "survey_response_count_total": ("patient_experience", "survey_response_count_total", "first"),
    "survey_valid_score_record_count": ("patient_experience", "survey_valid_score_record_count", "first"),
    "survey_score_sum": ("patient_experience", "survey_score_sum", "first"),
    "survey_score_weighted_sum": ("patient_experience", "survey_score_weighted_sum", "first"),
}

ALL_FIELD_MAPS = {**WORKFORCE_FIELD_MAP, **PATIENT_FLOW_FIELD_MAP, **PATIENT_EXPERIENCE_FIELD_MAP}


class OperationalDailyBuilder:
    """Build processed_operational_daily from three domain daily datasets."""

    def __init__(
        self,
        project_root: Path,
        processed_dir: Path,
        processing_run_id: str = "",
        transformation_version: str = BUILDER_VERSION,
    ):
        self.project_root = Path(project_root)
        self.processed_dir = Path(processed_dir)
        self.processing_run_id = processing_run_id or f"PROC-OPD-{uuid.uuid4().hex[:12].upper()}"
        self.transformation_version = transformation_version
        self.processed_datetime = datetime.now()
        self.issues: List[ProcessingIssue] = []
        self.exclusions: List[Dict[str, Any]] = []
        self.lineage: List[Dict[str, Any]] = []
        self.workforce_df: Optional[pd.DataFrame] = None
        self.patient_flow_df: Optional[pd.DataFrame] = None
        self.patient_experience_df: Optional[pd.DataFrame] = None
        self.operational_daily_df: Optional[pd.DataFrame] = None
        self.checksums: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # Load inputs
    # ------------------------------------------------------------------
    def load_workforce_daily(self) -> Optional[pd.DataFrame]:
        fpath = self.processed_dir / "processed_workforce_daily.csv"
        if not fpath.exists():
            self._add_issue("Critical", "Missing workforce daily", f"Missing workforce daily: {fpath}")
            return None
        df = pd.read_csv(fpath, dtype=str, keep_default_na=False)
        # Aggregate from staff_role grain to hospital-department-date grain
        numeric_cols = ["rostered_staff_count", "verified_available_staff_count", "absent_event_count",
                        "planned_leave_event_count", "reassigned_in_count", "replacement_staff_count"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        agg_dict = {c: "sum" for c in numeric_cols if c in df.columns}
        if "reporting_month" in df.columns:
            agg_dict["reporting_month"] = "first"
        grain = ["hospital_id", "department_id", "reporting_date"]
        if agg_dict:
            df_agg = df.groupby(grain, as_index=False).agg(agg_dict)
        else:
            df_agg = df.groupby(grain, as_index=False).first()
            df_agg = df_agg[grain]
        # Preserve workforce_daily_id for lineage when no aggregation occurred
        if "workforce_daily_id" in df.columns and not agg_dict:
            id_map = df.groupby(grain, as_index=False)["workforce_daily_id"].first()
            df_agg = df_agg.merge(id_map, on=grain, how="left")
        df_agg["workforce_source_present_flag"] = True
        df_agg["workforce_data_complete_flag"] = True
        df_agg["staffing_requirement_available_flag"] = False
        if "required_staff_count" in df.columns:
            req = df.groupby(grain, as_index=False)["required_staff_count"].sum()
            df_agg = df_agg.merge(req, on=grain, how="left")
            df_agg["staffing_requirement_available_flag"] = pd.to_numeric(df_agg["required_staff_count"], errors="coerce") > 0
        self.workforce_df = df_agg
        self.checksums["processed_workforce_daily.csv"] = self._file_checksum(fpath)
        return df_agg

    def load_patient_flow_daily(self) -> Optional[pd.DataFrame]:
        fpath = self.processed_dir / "processed_patient_flow_daily.csv"
        if not fpath.exists():
            self._add_issue("Critical", "Missing patient flow daily", f"Missing patient flow daily: {fpath}")
            return None
        df = pd.read_csv(fpath, dtype=str, keep_default_na=False)
        df["patient_flow_source_present_flag"] = True
        df["patient_flow_data_complete_flag"] = True
        self.patient_flow_df = df
        self.checksums["processed_patient_flow_daily.csv"] = self._file_checksum(fpath)
        return df

    def load_patient_experience_daily(self) -> Optional[pd.DataFrame]:
        fpath = self.processed_dir / "processed_patient_experience_daily.csv"
        if not fpath.exists():
            self._add_issue("Critical", "Missing patient experience daily", f"Missing patient experience daily: {fpath}")
            return None
        df = pd.read_csv(fpath, dtype=str, keep_default_na=False)
        df["patient_experience_source_present_flag"] = True
        df["patient_experience_data_complete_flag"] = df.get("patient_experience_data_complete_flag", True)
        self.patient_experience_df = df
        self.checksums["processed_patient_experience_daily.csv"] = self._file_checksum(fpath)
        return df

    def verify_input_checksums(self, expected: Dict[str, str]) -> Dict[str, Any]:
        results = {}
        for fname, expected_chksum in expected.items():
            actual = self.checksums.get(fname)
            if actual is None:
                results[fname] = {"status": "Not loaded", "match": False}
            elif actual != expected_chksum:
                results[fname] = {"status": "Mismatch", "match": False, "expected": expected_chksum, "actual": actual}
                self._add_issue("Error", "Input checksum mismatch", fname)
            else:
                results[fname] = {"status": "Match", "match": True}
        return results

    def validate_input_schemas(self) -> Dict[str, Any]:
        results = {}
        for ds_name, df in [
            ("processed_workforce_daily", self.workforce_df),
            ("processed_patient_flow_daily", self.patient_flow_df),
            ("processed_patient_experience_daily", self.patient_experience_df),
        ]:
            if df is None:
                results[ds_name] = {"status": "Not loaded"}
                continue
            schema = get_processed_schema(ds_name)
            if schema is None:
                results[ds_name] = {"status": "No schema"}
                continue
            missing = [f for f in schema.required_fields if f not in df.columns]
            results[ds_name] = {"status": "Passed" if not missing else "Failed", "missing": missing}
            if missing:
                self._add_issue("Error", "Input schema missing fields", f"{ds_name}: {missing}")
        return results

    # ------------------------------------------------------------------
    # Build spine
    # ------------------------------------------------------------------
    def build_operational_daily_spine(self) -> pd.DataFrame:
        grain = ["hospital_id", "department_id", "reporting_date"]
        keys = []
        for df in [self.workforce_df, self.patient_flow_df, self.patient_experience_df]:
            if df is not None and all(c in df.columns for c in grain):
                keys.append(df[grain].drop_duplicates())
        if not keys:
            self._add_issue("Critical", "No daily keys available", "All domain daily datasets missing or empty")
            return pd.DataFrame(columns=grain)
        spine = pd.concat(keys, ignore_index=True).drop_duplicates()
        spine["reporting_date_dt"] = pd.to_datetime(spine["reporting_date"], errors="coerce")
        spine["reporting_month"] = spine["reporting_date_dt"].dt.month
        spine["reporting_year"] = spine["reporting_date_dt"].dt.year
        spine = spine.drop(columns=["reporting_date_dt"])
        return spine

    # ------------------------------------------------------------------
    # Merge fields
    # ------------------------------------------------------------------
    def _merge_domain_fields(
        self,
        spine: pd.DataFrame,
        domain_df: Optional[pd.DataFrame],
        field_map: Dict[str, Tuple[str, str, str]],
        prefix: str,
    ) -> pd.DataFrame:
        if domain_df is None:
            for out_field in field_map:
                spine[out_field] = np.nan
            spine[f"{prefix}_missing_flag"] = True
            return spine
        grain = ["hospital_id", "department_id", "reporting_date"]
        merge_cols = list(grain)
        # Select only needed columns
        needed = [c for c in grain]
        for out_field, (src_domain, src_field, agg) in field_map.items():
            if src_field in domain_df.columns:
                needed.append(src_field)
        # Deduplicate needed list preserving order
        seen = set()
        needed_unique = []
        for c in needed:
            if c not in seen:
                seen.add(c)
                needed_unique.append(c)
        sub = domain_df[needed_unique].copy()
        # Rename source fields to output fields for direct merge
        rename_map = {}
        for out_field, (src_domain, src_field, agg) in field_map.items():
            if src_field in sub.columns and src_field != out_field:
                # Avoid collision: rename to output field
                rename_map[src_field] = out_field
        if rename_map:
            sub = sub.rename(columns=rename_map)
        spine = spine.merge(sub, on=grain, how="left")
        spine[f"{prefix}_missing_flag"] = False
        return spine

    def merge_workforce_fields(self, spine: pd.DataFrame) -> pd.DataFrame:
        return self._merge_domain_fields(spine, self.workforce_df, WORKFORCE_FIELD_MAP, "workforce")

    def merge_patient_flow_fields(self, spine: pd.DataFrame) -> pd.DataFrame:
        return self._merge_domain_fields(spine, self.patient_flow_df, PATIENT_FLOW_FIELD_MAP, "patient_flow")

    def merge_patient_experience_fields(self, spine: pd.DataFrame) -> pd.DataFrame:
        return self._merge_domain_fields(spine, self.patient_experience_df, PATIENT_EXPERIENCE_FIELD_MAP, "patient_experience")

    # ------------------------------------------------------------------
    # Domain presence and completeness flags
    # ------------------------------------------------------------------
    def derive_domain_presence_flags(self, df: pd.DataFrame) -> pd.DataFrame:
        df["workforce_missing_flag"] = df.get("workforce_missing_flag", True)
        df["patient_flow_missing_flag"] = df.get("patient_flow_missing_flag", True)
        df["patient_experience_missing_flag"] = df.get("patient_experience_missing_flag", True)
        # Override if any field from that domain is non-null
        wf_fields = [f for f in WORKFORCE_FIELD_MAP if f in df.columns]
        if wf_fields:
            df["workforce_missing_flag"] = df[wf_fields].notna().sum(axis=1) == 0
        pf_fields = [f for f in PATIENT_FLOW_FIELD_MAP if f in df.columns]
        if pf_fields:
            df["patient_flow_missing_flag"] = df[pf_fields].notna().sum(axis=1) == 0
        pe_fields = [f for f in PATIENT_EXPERIENCE_FIELD_MAP if f in df.columns]
        if pe_fields:
            df["patient_experience_missing_flag"] = df[pe_fields].notna().sum(axis=1) == 0
        return df

    def derive_completeness_flags(self, df: pd.DataFrame) -> pd.DataFrame:
        df["operational_data_complete_flag"] = (
            ~df["workforce_missing_flag"] & ~df["patient_flow_missing_flag"] & ~df["patient_experience_missing_flag"]
        )
        df["partial_domain_record_flag"] = (
            df["workforce_missing_flag"] | df["patient_flow_missing_flag"] | df["patient_experience_missing_flag"]
        )
        df["cross_domain_reference_valid_flag"] = True
        df["cross_domain_date_valid_flag"] = True
        df["unresolved_rule_flag"] = False
        return df

    # ------------------------------------------------------------------
    # Identifier
    # ------------------------------------------------------------------
    def create_operational_daily_identifier(self, df: pd.DataFrame) -> pd.DataFrame:
        def _make_id(row):
            date_str = str(row["reporting_date"]).replace("-", "")
            return f"OPD-{row['hospital_id']}-{row['department_id']}-{date_str}"
        df["operational_daily_id"] = df.apply(_make_id, axis=1)
        return df

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def validate_daily_grain(self, df: pd.DataFrame) -> Dict[str, Any]:
        grain = ["hospital_id", "department_id", "reporting_date"]
        dups = df[grain].duplicated().sum()
        status = "Passed" if dups == 0 else "Failed"
        if dups > 0:
            self._add_issue("Error", "Duplicate operational daily grain", f"{dups} duplicates")
        return {"status": status, "duplicates": int(dups)}

    def validate_processed_schema(self, df: pd.DataFrame) -> Dict[str, Any]:
        schema = get_processed_schema("processed_operational_daily")
        if schema is None:
            self._add_issue("Critical", "Operational daily schema not found", "")
            return {"status": "No schema"}
        missing = [f for f in schema.get("required_fields", []) if f not in df.columns]
        if missing:
            self._add_issue("Error", "Operational daily missing required fields", str(missing))
        return {"status": "Passed" if not missing else "Failed", "missing_required": missing}

    # ------------------------------------------------------------------
    # Lineage
    # ------------------------------------------------------------------
    def build_lineage(self, df: pd.DataFrame) -> pd.DataFrame:
        grain = ["hospital_id", "department_id", "reporting_date"]
        lineage_rows = []
        for _, row in df.iterrows():
            opd_id = row["operational_daily_id"]
            for domain_df, domain_name, source_pk in [
                (self.workforce_df, "processed_workforce_daily", "workforce_daily_id"),
                (self.patient_flow_df, "processed_patient_flow_daily", "patient_flow_daily_id"),
                (self.patient_experience_df, "processed_patient_experience_daily", "patient_experience_daily_id"),
            ]:
                if domain_df is None:
                    continue
                match = domain_df
                for c in grain:
                    match = match[match[c] == row[c]]
                if match.empty:
                    continue
                for _, src_row in match.iterrows():
                    lineage_rows.append({
                        "lineage_id": f"LN-{uuid.uuid4().hex[:12].upper()}",
                        "processing_run_id": self.processing_run_id,
                        "output_dataset": "processed_operational_daily",
                        "output_record_id": opd_id,
                        "source_dataset": domain_name,
                        "source_record_id": src_row.get(source_pk, ""),
                        "source_file": f"{domain_name}.csv",
                        "transformation_name": TRANSFORMATION_NAME,
                        "transformation_version": self.transformation_version,
                        "lineage_datetime": self.processed_datetime.isoformat(),
                    })
        lineage_df = pd.DataFrame(lineage_rows)
        self.lineage = lineage_df
        return lineage_df

    # ------------------------------------------------------------------
    # Exclusions
    # ------------------------------------------------------------------
    def build_exclusions(self) -> pd.DataFrame:
        if not self.exclusions:
            return pd.DataFrame(columns=[
                "exclusion_id", "processing_run_id", "source_dataset_name",
                "source_primary_key_field", "source_primary_key_value",
                "exclusion_reason_code", "exclusion_reason_description",
                "created_datetime",
            ])
        return pd.DataFrame(self.exclusions)

    # ------------------------------------------------------------------
    # Issues
    # ------------------------------------------------------------------
    def _add_issue(self, severity: str, category: str, message: str) -> None:
        self.issues.append(
            ProcessingIssue(
                processing_run_id=self.processing_run_id,
                issue_id=str(uuid.uuid4())[:8],
                issue_type=category,
                severity=severity,
                issue_description=message,
            )
        )

    def collect_issues(self) -> pd.DataFrame:
        if not self.issues:
            return pd.DataFrame(columns=[
                "issue_id", "severity", "category", "message",
                "dataset_name", "field_name", "rule_id",
            ])
        rows = []
        for issue in self.issues:
            rows.append({
                "issue_id": issue.issue_id,
                "severity": issue.severity,
                "category": issue.issue_type,
                "message": issue.issue_description,
                "dataset_name": issue.source_dataset_name or issue.processed_dataset_name,
                "field_name": issue.field_name,
                "rule_id": "",
            })
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Result
    # ------------------------------------------------------------------
    def return_build_result(self) -> Dict[str, Any]:
        return {
            "processing_run_id": self.processing_run_id,
            "transformation_version": self.transformation_version,
            "processed_datetime": self.processed_datetime.isoformat(),
            "row_count": len(self.operational_daily_df) if self.operational_daily_df is not None else 0,
            "checksums": self.checksums,
            "issue_count": len(self.issues),
            "lineage_count": len(self.lineage) if isinstance(self.lineage, pd.DataFrame) else 0,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _file_checksum(self, fpath: Path) -> str:
        h = hashlib.sha256()
        with open(fpath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
