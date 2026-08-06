"""
Sentinel360 Healthcare — Patient Experience Transformer

Transforms patient complaint and patient survey source datasets into
controlled preparation-level processed datasets.

Step: 2D-4
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


TRANSFORMATION_VERSION = "2D-4.0"
ENGINE_VERSION = "2D-4.0"

SUPPORTED_COMPLAINT_CHANNELS: Set[str] = {
    "Formal Letter", "Third Party", "Online Portal", "Email", "Social Media", "Walk-In", "Phone"
}
SUPPORTED_COMPLAINT_CATEGORIES: Set[str] = {
    "Facilities", "Waiting Time", "Staff Behaviour", "Other", "Clinical Care", "Safety", "Communication", "Billing"
}
SUPPORTED_COMPLAINT_SEVERITIES: Set[str] = {"Low", "Medium", "High", "Critical"}

SUPPORTED_SURVEY_TYPES: Set[str] = {"Outpatient Satisfaction"}

KNOWN_SURVEY_SCALES: Dict[str, Tuple[int, int]] = {
    "SCALE-5PT": (1, 5),
}

RESOLVED_STATUSES: Set[str] = {"Resolved", "Closed"}
OPEN_STATUSES: Set[str] = {"Escalated", "Received", "Investigating", "Under Review"}

INPUT_DATASETS = {
    "patient_complaints": "patient_complaints.csv",
    "patient_surveys": "patient_surveys.csv",
}


class Issue:
    def __init__(
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
        exclusion_flag: bool,
        blocks_processing: bool = False,
    ):
        self.source_dataset_name = source_dataset_name
        self.processed_dataset_name = processed_dataset_name
        self.source_primary_key = source_primary_key
        self.source_row_number = source_row_number
        self.field_name = field_name
        self.issue_type = issue_type
        self.severity = severity
        self.issue_description = issue_description
        self.source_value = source_value
        self.exclusion_flag = exclusion_flag
        self.blocks_processing = blocks_processing

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_dataset_name": self.source_dataset_name,
            "processed_dataset_name": self.processed_dataset_name,
            "source_primary_key": self.source_primary_key,
            "source_row_number": self.source_row_number,
            "field_name": self.field_name,
            "issue_type": self.issue_type,
            "severity": self.severity,
            "issue_description": self.issue_description,
            "source_value": self.source_value,
            "exclusion_flag": self.exclusion_flag,
            "blocks_processing": self.blocks_processing,
        }


class PatientExperienceTransformer:
    """Transforms complaint and survey sources into processed datasets."""

    def __init__(
        self,
        processing_run_id: str,
        validation_run_id: str,
        source_directory: Path,
        output_directory: Path,
        log_directory: Path,
        source_type: str = "processed_synthetic_demo",
        collect_lineage: bool = True,
        max_issue_examples: int = 1000,
    ):
        self.processing_run_id = processing_run_id
        self.validation_run_id = validation_run_id
        self.source_directory = Path(source_directory)
        self.output_directory = Path(output_directory)
        self.log_directory = Path(log_directory)
        self.source_type = source_type
        self.collect_lineage = collect_lineage
        self.max_issue_examples = max_issue_examples

        self.issues: List[Issue] = []
        self.lineage_records: List[Dict[str, Any]] = []
        self.exclusion_records: List[Dict[str, Any]] = []
        self.audit_events: List[Dict[str, Any]] = []
        self.source_checksums: Dict[str, str] = {}
        self.input_record_counts: Dict[str, int] = {}

        self.processed_complaints: Optional[pd.DataFrame] = None
        self.processed_surveys: Optional[pd.DataFrame] = None

        self.hospital_ids: Optional[Set[str]] = None
        self.department_ids: Optional[Set[str]] = None

    # ------------------------------------------------------------------
    # Audit helper
    # ------------------------------------------------------------------
    def _audit(self, event: str, detail: str) -> None:
        self.audit_events.append({
            "processing_run_id": self.processing_run_id,
            "event": event,
            "detail": detail,
            "timestamp": datetime.now().isoformat(),
        })

    # ------------------------------------------------------------------
    # Issue helper
    # ------------------------------------------------------------------
    def _add_issue(self, **kwargs: Any) -> None:
        if len(self.issues) < self.max_issue_examples:
            self.issues.append(Issue(**kwargs))

    # ------------------------------------------------------------------
    # Checksum
    # ------------------------------------------------------------------
    def _file_checksum(self, path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def verify_source_checksums(self) -> Dict[str, str]:
        for key, filename in INPUT_DATASETS.items():
            path = self.source_directory / filename
            if path.exists():
                self.source_checksums[key] = self._file_checksum(path)
        return self.source_checksums

    # ------------------------------------------------------------------
    # Load source
    # ------------------------------------------------------------------
    def load_source_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        complaints_path = self.source_directory / INPUT_DATASETS["patient_complaints"]
        surveys_path = self.source_directory / INPUT_DATASETS["patient_surveys"]

        if not complaints_path.exists():
            raise FileNotFoundError(f"Missing source: {complaints_path}")
        if not surveys_path.exists():
            raise FileNotFoundError(f"Missing source: {surveys_path}")

        complaints = pd.read_csv(complaints_path, dtype=str, keep_default_na=True)
        surveys = pd.read_csv(surveys_path, dtype=str, keep_default_na=True)

        complaints["source_row_number"] = range(1, len(complaints) + 1)
        surveys["source_row_number"] = range(1, len(surveys) + 1)

        complaints["source_checksum"] = self.source_checksums.get("patient_complaints", "")
        surveys["source_checksum"] = self.source_checksums.get("patient_surveys", "")

        self.input_record_counts["patient_complaints"] = len(complaints)
        self.input_record_counts["patient_surveys"] = len(surveys)

        self._audit("Source Loaded", f"complaints={len(complaints)}, surveys={len(surveys)}")
        return complaints, surveys

    def inspect_source_columns(self, complaints: pd.DataFrame, surveys: pd.DataFrame) -> Dict[str, Any]:
        return {
            "complaint_columns": list(complaints.columns),
            "survey_columns": list(surveys.columns),
            "complaint_rows": len(complaints),
            "survey_rows": len(surveys),
        }

    # ------------------------------------------------------------------
    # Reference masters
    # ------------------------------------------------------------------
    def _load_reference_masters(self) -> None:
        hosp_path = self.output_directory / "processed_hospital_master.csv"
        dept_path = self.output_directory / "processed_department_master.csv"

        if hosp_path.exists():
            hosp = pd.read_csv(hosp_path, dtype=str)
            self.hospital_ids = set(hosp["hospital_id"].dropna().unique())
        else:
            self.hospital_ids = set()
            self._add_issue(
                source_dataset_name="",
                processed_dataset_name="",
                source_primary_key="",
                source_row_number=0,
                field_name="processed_hospital_master",
                issue_type="Missing Reference",
                severity="Critical",
                issue_description="processed_hospital_master.csv not found.",
                source_value="",
                exclusion_flag=False,
                blocks_processing=True,
            )

        if dept_path.exists():
            dept = pd.read_csv(dept_path, dtype=str)
            self.department_ids = set(dept["department_id"].dropna().unique())
        else:
            self.department_ids = set()
            self._add_issue(
                source_dataset_name="",
                processed_dataset_name="",
                source_primary_key="",
                source_row_number=0,
                field_name="processed_department_master",
                issue_type="Missing Reference",
                severity="Critical",
                issue_description="processed_department_master.csv not found.",
                source_value="",
                exclusion_flag=False,
                blocks_processing=True,
            )

    def validate_hospital_references(self, df: pd.DataFrame, pk_col: str, dataset_name: str) -> pd.DataFrame:
        if self.hospital_ids is None:
            self._load_reference_masters()

        df["hospital_ref_valid_flag"] = df["hospital_id"].isin(self.hospital_ids)
        invalid = df[~df["hospital_ref_valid_flag"]]
        for _, row in invalid.iterrows():
            self._add_issue(
                source_dataset_name=dataset_name,
                processed_dataset_name=dataset_name.replace("patient_", "processed_"),
                source_primary_key=str(row.get(pk_col, "")),
                source_row_number=int(row.get("source_row_number", 0)),
                field_name="hospital_id",
                issue_type="Invalid Hospital Reference",
                severity="Error",
                issue_description=f"hospital_id '{row.get('hospital_id')}' not found in processed_hospital_master.",
                source_value=str(row.get("hospital_id", "")),
                exclusion_flag=True,
            )
        return df

    def validate_department_references(self, df: pd.DataFrame, pk_col: str, dataset_name: str) -> pd.DataFrame:
        if self.department_ids is None:
            self._load_reference_masters()

        df["department_ref_valid_flag"] = df["department_id"].isin(self.department_ids)
        invalid = df[~df["department_ref_valid_flag"]]
        for _, row in invalid.iterrows():
            self._add_issue(
                source_dataset_name=dataset_name,
                processed_dataset_name=dataset_name.replace("patient_", "processed_"),
                source_primary_key=str(row.get(pk_col, "")),
                source_row_number=int(row.get("source_row_number", 0)),
                field_name="department_id",
                issue_type="Invalid Department Reference",
                severity="Error",
                issue_value=str(row.get("department_id", "")),
                issue_description=f"department_id '{row.get('department_id')}' not found in processed_department_master.",
                source_value=str(row.get("department_id", "")),
                exclusion_flag=True,
            )
        return df

    # ------------------------------------------------------------------
    # Date parsing
    # ------------------------------------------------------------------
    def parse_complaint_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        df["complaint_date"] = pd.to_datetime(df["complaint_received_date"], errors="coerce").dt.date
        df["complaint_date_valid_flag"] = df["complaint_date"].notna()
        df["complaint_year"] = pd.to_datetime(df["complaint_received_date"], errors="coerce").dt.year
        df["complaint_month"] = pd.to_datetime(df["complaint_received_date"], errors="coerce").dt.month

        invalid = df[~df["complaint_date_valid_flag"]]
        for _, row in invalid.iterrows():
            self._add_issue(
                source_dataset_name="patient_complaints",
                processed_dataset_name="processed_patient_complaints",
                source_primary_key=str(row.get("complaint_id", "")),
                source_row_number=int(row.get("source_row_number", 0)),
                field_name="complaint_received_date",
                issue_type="Invalid Date",
                severity="Error",
                issue_description=f"Cannot parse complaint date: '{row.get('complaint_received_date')}'.",
                source_value=str(row.get("complaint_received_date", "")),
                exclusion_flag=True,
            )
        return df

    def parse_survey_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        df["survey_date"] = pd.to_datetime(df["survey_date"], errors="coerce").dt.date
        df["survey_date_valid_flag"] = df["survey_date"].notna()
        df["survey_year"] = pd.to_datetime(df["survey_date"], errors="coerce").dt.year
        df["survey_month"] = pd.to_datetime(df["survey_date"], errors="coerce").dt.month

        invalid = df[~df["survey_date_valid_flag"]]
        for _, row in invalid.iterrows():
            self._add_issue(
                source_dataset_name="patient_surveys",
                processed_dataset_name="processed_patient_surveys",
                source_primary_key=str(row.get("survey_id", "")),
                source_row_number=int(row.get("source_row_number", 0)),
                field_name="survey_date",
                issue_type="Invalid Date",
                severity="Error",
                issue_description=f"Cannot parse survey date: '{row.get('survey_date')}'.",
                source_value=str(row.get("survey_date", "")),
                exclusion_flag=True,
            )
        return df

    # ------------------------------------------------------------------
    # Identifier validation
    # ------------------------------------------------------------------
    def validate_complaint_identifiers(self, df: pd.DataFrame) -> pd.DataFrame:
        dups = df[df["complaint_id"].duplicated(keep=False)]
        for _, row in dups.iterrows():
            self._add_issue(
                source_dataset_name="patient_complaints",
                processed_dataset_name="processed_patient_complaints",
                source_primary_key=str(row.get("complaint_id", "")),
                source_row_number=int(row.get("source_row_number", 0)),
                field_name="complaint_id",
                issue_type="Duplicate Primary Key",
                severity="Error",
                issue_description=f"Duplicate complaint_id: '{row.get('complaint_id')}'.",
                source_value=str(row.get("complaint_id", "")),
                exclusion_flag=True,
                blocks_processing=True,
            )
        return df

    def validate_survey_identifiers(self, df: pd.DataFrame) -> pd.DataFrame:
        dups = df[df["survey_id"].duplicated(keep=False)]
        for _, row in dups.iterrows():
            self._add_issue(
                source_dataset_name="patient_surveys",
                processed_dataset_name="processed_patient_surveys",
                source_primary_key=str(row.get("survey_id", "")),
                source_row_number=int(row.get("source_row_number", 0)),
                field_name="survey_id",
                issue_type="Duplicate Primary Key",
                severity="Error",
                issue_description=f"Duplicate survey_id: '{row.get('survey_id')}'.",
                source_value=str(row.get("survey_id", "")),
                exclusion_flag=True,
                blocks_processing=True,
            )
        return df

    # ------------------------------------------------------------------
    # Classification / preservation helpers
    # ------------------------------------------------------------------
    def classify_complaint_channels(self, df: pd.DataFrame) -> pd.DataFrame:
        df["complaint_channel"] = df["complaint_channel"].fillna("").astype(str)
        df["complaint_channel_supported_flag"] = df["complaint_channel"].isin(SUPPORTED_COMPLAINT_CHANNELS)
        unsupported = df[~df["complaint_channel_supported_flag"] & (df["complaint_channel"] != "")]
        for _, row in unsupported.iterrows():
            self._add_issue(
                source_dataset_name="patient_complaints",
                processed_dataset_name="processed_patient_complaints",
                source_primary_key=str(row.get("complaint_id", "")),
                source_row_number=int(row.get("source_row_number", 0)),
                field_name="complaint_channel",
                issue_type="Unsupported Channel",
                severity="Information",
                issue_description=f"Unsupported complaint channel preserved: '{row.get('complaint_channel')}'.",
                source_value=str(row.get("complaint_channel", "")),
                exclusion_flag=False,
            )
        return df

    def classify_complaint_categories(self, df: pd.DataFrame) -> pd.DataFrame:
        df["complaint_category"] = df["complaint_category"].fillna("").astype(str)
        df["complaint_category_supported_flag"] = df["complaint_category"].isin(SUPPORTED_COMPLAINT_CATEGORIES)
        unsupported = df[~df["complaint_category_supported_flag"] & (df["complaint_category"] != "")]
        for _, row in unsupported.iterrows():
            self._add_issue(
                source_dataset_name="patient_complaints",
                processed_dataset_name="processed_patient_complaints",
                source_primary_key=str(row.get("complaint_id", "")),
                source_row_number=int(row.get("source_row_number", 0)),
                field_name="complaint_category",
                issue_type="Unsupported Category",
                severity="Information",
                issue_description=f"Unsupported complaint category preserved: '{row.get('complaint_category')}'.",
                source_value=str(row.get("complaint_category", "")),
                exclusion_flag=False,
            )
        return df

    def classify_complaint_severity(self, df: pd.DataFrame) -> pd.DataFrame:
        df["complaint_severity"] = df["severity"].fillna("").astype(str)
        df["complaint_severity_supported_flag"] = df["complaint_severity"].isin(SUPPORTED_COMPLAINT_SEVERITIES)
        unsupported = df[~df["complaint_severity_supported_flag"] & (df["complaint_severity"] != "")]
        for _, row in unsupported.iterrows():
            self._add_issue(
                source_dataset_name="patient_complaints",
                processed_dataset_name="processed_patient_complaints",
                source_primary_key=str(row.get("complaint_id", "")),
                source_row_number=int(row.get("source_row_number", 0)),
                field_name="severity",
                issue_type="Unsupported Severity",
                severity="Information",
                issue_description=f"Unsupported complaint severity preserved: '{row.get('severity')}'.",
                source_value=str(row.get("severity", "")),
                exclusion_flag=False,
            )
        missing = df[df["complaint_severity"] == ""]
        for _, row in missing.iterrows():
            self._add_issue(
                source_dataset_name="patient_complaints",
                processed_dataset_name="processed_patient_complaints",
                source_primary_key=str(row.get("complaint_id", "")),
                source_row_number=int(row.get("source_row_number", 0)),
                field_name="severity",
                issue_type="Missing Severity",
                severity="Warning",
                issue_description="Missing complaint severity.",
                source_value="",
                exclusion_flag=False,
            )
        return df

    # ------------------------------------------------------------------
    # Survey validation
    # ------------------------------------------------------------------
    def validate_survey_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        df["score_value"] = pd.to_numeric(df["score_value"], errors="coerce")
        df["satisfaction_score_numeric"] = df["score_value"]
        df["satisfaction_score_source"] = df["score_value"].astype(str).replace("nan", "")

        df["satisfaction_scale_min"] = np.nan
        df["satisfaction_scale_max"] = np.nan
        df["satisfaction_score_valid_flag"] = False
        df["unresolved_scale_flag"] = False

        for scale_id, (smin, smax) in KNOWN_SURVEY_SCALES.items():
            mask = df["scale_id"] == scale_id
            df.loc[mask, "satisfaction_scale_min"] = smin
            df.loc[mask, "satisfaction_scale_max"] = smax
            df.loc[mask, "satisfaction_score_valid_flag"] = (
                df.loc[mask, "score_value"].notna() &
                (df.loc[mask, "score_value"] >= smin) &
                (df.loc[mask, "score_value"] <= smax)
            )

        unknown_scale_mask = ~df["scale_id"].isin(KNOWN_SURVEY_SCALES.keys()) & df["scale_id"].notna()
        if unknown_scale_mask.any():
            df.loc[unknown_scale_mask, "unresolved_scale_flag"] = True
            for _, row in df[unknown_scale_mask].iterrows():
                self._add_issue(
                    source_dataset_name="patient_surveys",
                    processed_dataset_name="processed_patient_surveys",
                    source_primary_key=str(row.get("survey_id", "")),
                    source_row_number=int(row.get("source_row_number", 0)),
                    field_name="scale_id",
                    issue_type="Unknown Survey Scale",
                    severity="Warning",
                    issue_description=f"Unknown survey scale '{row.get('scale_id')}' — score preserved but not normalised.",
                    source_value=str(row.get("scale_id", "")),
                    exclusion_flag=False,
                )

        # Multiple scales check
        unique_scales = df["scale_id"].dropna().unique()
        if len(unique_scales) > 1:
            self._add_issue(
                source_dataset_name="patient_surveys",
                processed_dataset_name="processed_patient_surveys",
                source_primary_key="",
                source_row_number=0,
                field_name="scale_id",
                issue_type="Mixed Survey Scales",
                severity="Warning",
                issue_description=f"Multiple survey scales detected: {list(unique_scales)}.",
                source_value=str(list(unique_scales)),
                exclusion_flag=False,
            )

        # Invalid scores against known scale
        known_mask = df["scale_id"].isin(KNOWN_SURVEY_SCALES.keys())
        invalid_scores = known_mask & df["score_value"].notna() & ~df["satisfaction_score_valid_flag"]
        for _, row in df[invalid_scores].iterrows():
            self._add_issue(
                source_dataset_name="patient_surveys",
                processed_dataset_name="processed_patient_surveys",
                source_primary_key=str(row.get("survey_id", "")),
                source_row_number=int(row.get("source_row_number", 0)),
                field_name="score_value",
                issue_type="Impossible Score",
                severity="Error",
                issue_description=f"Score {row.get('score_value')} outside known scale for {row.get('scale_id')}.",
                source_value=str(row.get("score_value", "")),
                exclusion_flag=True,
            )

        df["satisfaction_score_normalised_flag"] = False
        return df

    def validate_response_counts(self, df: pd.DataFrame) -> pd.DataFrame:
        df["response_count"] = pd.to_numeric(df["response_weight"], errors="coerce")
        df["survey_response_present_flag"] = df["is_complete"].astype(str).str.lower().isin(["true", "1", "yes"])

        negative_mask = df["response_count"] < 0
        for _, row in df[negative_mask].iterrows():
            self._add_issue(
                source_dataset_name="patient_surveys",
                processed_dataset_name="processed_patient_surveys",
                source_primary_key=str(row.get("survey_id", "")),
                source_row_number=int(row.get("source_row_number", 0)),
                field_name="response_weight",
                issue_type="Negative Response Count",
                severity="Error",
                issue_description=f"Negative response_weight: {row.get('response_weight')}.",
                source_value=str(row.get("response_weight", "")),
                exclusion_flag=True,
            )

        missing_mask = df["response_count"].isna()
        for _, row in df[missing_mask].iterrows():
            self._add_issue(
                source_dataset_name="patient_surveys",
                processed_dataset_name="processed_patient_surveys",
                source_primary_key=str(row.get("survey_id", "")),
                source_row_number=int(row.get("source_row_number", 0)),
                field_name="response_weight",
                issue_type="Missing Response Count",
                severity="Warning",
                issue_description="Missing response_weight — not replaced with one.",
                source_value="",
                exclusion_flag=False,
            )
        return df

    # ------------------------------------------------------------------
    # Flag derivation
    # ------------------------------------------------------------------
    def derive_complaint_flags(self, df: pd.DataFrame) -> pd.DataFrame:
        df["complaint_text_present_flag"] = df["description"].notna() & (df["description"].astype(str).str.strip() != "")
        df["complaint_status_source"] = df["status"].fillna("").astype(str)

        # Resolution date parsing
        df["resolution_date"] = pd.to_datetime(df["resolution_date"], errors="coerce").dt.date
        df["resolution_date_valid_flag"] = df["resolution_date"].notna()

        # Detect resolution date before complaint date
        comp_dt = pd.to_datetime(df["complaint_received_date"], errors="coerce")
        res_dt = pd.to_datetime(df["resolution_date"], errors="coerce")
        invalid_res = (res_dt.notna() & comp_dt.notna() & (res_dt < comp_dt))
        for _, row in df[invalid_res].iterrows():
            self._add_issue(
                source_dataset_name="patient_complaints",
                processed_dataset_name="processed_patient_complaints",
                source_primary_key=str(row.get("complaint_id", "")),
                source_row_number=int(row.get("source_row_number", 0)),
                field_name="resolution_date",
                issue_type="Resolution Before Complaint",
                severity="Warning",
                issue_description="Resolution date is earlier than complaint date.",
                source_value=str(row.get("resolution_date", "")),
                exclusion_flag=False,
            )

        df["complaint_resolved_source_flag"] = df["complaint_status_source"].isin(RESOLVED_STATUSES)
        df["complaint_open_source_flag"] = df["complaint_status_source"].isin(OPEN_STATUSES)

        # Valid record: has valid date, hospital, department, no duplicate ID
        df["complaint_record_valid_flag"] = (
            df["complaint_date_valid_flag"] &
            df["hospital_id"].notna() & (df["hospital_id"].astype(str).str.strip() != "") &
            df["department_id"].notna() & (df["department_id"].astype(str).str.strip() != "") &
            df["hospital_ref_valid_flag"] &
            df["department_ref_valid_flag"]
        )

        # Exclusion conditions
        df["exclusion_reason_code"] = ""
        df.loc[~df["complaint_date_valid_flag"], "exclusion_reason_code"] = "INVALID_DATE"
        df.loc[
            df["hospital_id"].isna() | (df["hospital_id"].astype(str).str.strip() == ""),
            "exclusion_reason_code"
        ] = "MISSING_HOSPITAL"
        df.loc[
            (~df["hospital_ref_valid_flag"]) & (df["exclusion_reason_code"] == ""),
            "exclusion_reason_code"
        ] = "INVALID_HOSPITAL"
        df.loc[
            df["department_id"].isna() | (df["department_id"].astype(str).str.strip() == ""),
            "exclusion_reason_code"
        ] = "MISSING_DEPARTMENT"
        df.loc[
            (~df["department_ref_valid_flag"]) & (df["exclusion_reason_code"] == ""),
            "exclusion_reason_code"
        ] = "INVALID_DEPARTMENT"

        df["complaint_count_eligible_flag"] = (
            df["complaint_record_valid_flag"] & (df["exclusion_reason_code"] == "")
        )
        df["complaint_daily_aggregation_eligible_flag"] = df["complaint_count_eligible_flag"]

        unresolved = (
            (~df["complaint_category_supported_flag"]) |
            (~df["complaint_channel_supported_flag"]) |
            (~df["complaint_severity_supported_flag"])
        )
        df["unresolved_rule_flag"] = unresolved
        return df

    def derive_survey_flags(self, df: pd.DataFrame) -> pd.DataFrame:
        df["survey_channel"] = np.nan  # Not present in source
        df["survey_type"] = df["survey_type"].fillna("").astype(str)
        df["survey_type_supported_flag"] = df["survey_type"].isin(SUPPORTED_SURVEY_TYPES)
        df["survey_channel_supported_flag"] = False

        unsupported = df[~df["survey_type_supported_flag"] & (df["survey_type"] != "")]
        for _, row in unsupported.iterrows():
            self._add_issue(
                source_dataset_name="patient_surveys",
                processed_dataset_name="processed_patient_surveys",
                source_primary_key=str(row.get("survey_id", "")),
                source_row_number=int(row.get("source_row_number", 0)),
                field_name="survey_type",
                issue_type="Unsupported Survey Type",
                severity="Information",
                issue_description=f"Unsupported survey type preserved: '{row.get('survey_type')}'.",
                source_value=str(row.get("survey_type", "")),
                exclusion_flag=False,
            )

        # Valid record
        df["survey_record_valid_flag"] = (
            df["survey_date_valid_flag"] &
            df["hospital_id"].notna() & (df["hospital_id"].astype(str).str.strip() != "") &
            df["department_id"].notna() & (df["department_id"].astype(str).str.strip() != "") &
            df["hospital_ref_valid_flag"] &
            df["department_ref_valid_flag"]
        )

        # Exclusion conditions
        df["exclusion_reason_code"] = ""
        df.loc[~df["survey_date_valid_flag"], "exclusion_reason_code"] = "INVALID_DATE"
        df.loc[
            df["hospital_id"].isna() | (df["hospital_id"].astype(str).str.strip() == ""),
            "exclusion_reason_code"
        ] = "MISSING_HOSPITAL"
        df.loc[
            (~df["hospital_ref_valid_flag"]) & (df["exclusion_reason_code"] == ""),
            "exclusion_reason_code"
        ] = "INVALID_HOSPITAL"
        df.loc[
            df["department_id"].isna() | (df["department_id"].astype(str).str.strip() == ""),
            "exclusion_reason_code"
        ] = "MISSING_DEPARTMENT"
        df.loc[
            (~df["department_ref_valid_flag"]) & (df["exclusion_reason_code"] == ""),
            "exclusion_reason_code"
        ] = "INVALID_DEPARTMENT"
        df.loc[
            (df["response_count"] < 0) & (df["exclusion_reason_code"] == ""),
            "exclusion_reason_code"
        ] = "NEGATIVE_RESPONSE_COUNT"
        df.loc[
            (~df["satisfaction_score_valid_flag"]) &
            df["satisfaction_score_numeric"].notna() &
            (df["exclusion_reason_code"] == ""),
            "exclusion_reason_code"
        ] = "INVALID_SCORE"

        df["survey_aggregation_eligible_flag"] = (
            df["survey_record_valid_flag"] & (df["exclusion_reason_code"] == "")
        )
        df["survey_score_eligible_flag"] = (
            df["survey_aggregation_eligible_flag"] & df["satisfaction_score_valid_flag"]
        )
        df["survey_response_count_eligible_flag"] = (
            df["survey_aggregation_eligible_flag"] & df["response_count"].notna() & (df["response_count"] >= 0)
        )

        unresolved = (
            (~df["survey_type_supported_flag"]) |
            df["unresolved_scale_flag"]
        )
        df["unresolved_rule_flag"] = unresolved
        return df

    # ------------------------------------------------------------------
    # Exclusions
    # ------------------------------------------------------------------
    def build_exclusions(self, df: pd.DataFrame, pk_col: str, dataset_name: str, source_name: str) -> pd.DataFrame:
        excluded = df[df["exclusion_reason_code"] != ""]
        records = []
        for _, row in excluded.iterrows():
            records.append({
                "exclusion_id": f"EXC-{uuid.uuid4().hex[:12].upper()}",
                "dataset_name": dataset_name,
                "source_record_id": str(row.get(pk_col, "")),
                "exclusion_reason_code": row.get("exclusion_reason_code", ""),
                "exclusion_reason": self._exclusion_reason_text(row.get("exclusion_reason_code", "")),
                "severity": "Error",
                "source_file": source_name,
                "source_row_number": int(row.get("source_row_number", 0)),
                "processing_run_id": self.processing_run_id,
                "excluded_datetime": datetime.now().isoformat(),
            })
        self.exclusion_records.extend(records)
        return pd.DataFrame(records) if records else pd.DataFrame(columns=[
            "exclusion_id", "dataset_name", "source_record_id", "exclusion_reason_code",
            "exclusion_reason", "severity", "source_file", "source_row_number",
            "processing_run_id", "excluded_datetime",
        ])

    @staticmethod
    def _exclusion_reason_text(code: str) -> str:
        mapping = {
            "INVALID_DATE": "Required date is invalid.",
            "MISSING_HOSPITAL": "Required hospital ID is missing.",
            "INVALID_HOSPITAL": "Hospital reference is invalid.",
            "MISSING_DEPARTMENT": "Required department ID is missing.",
            "INVALID_DEPARTMENT": "Department reference is invalid.",
            "NEGATIVE_RESPONSE_COUNT": "Negative response count.",
            "INVALID_SCORE": "Impossible score against known scale.",
            "DUPLICATE_KEY": "Duplicate primary key cannot be resolved.",
        }
        return mapping.get(code, code)

    # ------------------------------------------------------------------
    # Lineage
    # ------------------------------------------------------------------
    def build_record_lineage(
        self,
        source_df: pd.DataFrame,
        processed_df: pd.DataFrame,
        source_dataset: str,
        processed_dataset: str,
        pk_col: str,
    ) -> pd.DataFrame:
        if not self.collect_lineage:
            return pd.DataFrame()

        records = []
        for _, row in processed_df.iterrows():
            records.append({
                "lineage_id": f"LIN-{uuid.uuid4().hex[:12].upper()}",
                "processing_run_id": self.processing_run_id,
                "output_dataset": processed_dataset,
                "output_record_id": str(row.get(pk_col, "")),
                "source_dataset": source_dataset,
                "source_record_id": str(row.get("source_record_id", row.get(pk_col, ""))),
                "source_file": row.get("source_file", ""),
                "source_row_number": int(row.get("source_row_number", 0)),
                "transformation_name": "patient_experience_transform",
                "transformation_version": TRANSFORMATION_VERSION,
                "lineage_datetime": datetime.now().isoformat(),
            })
        self.lineage_records.extend(records)
        return pd.DataFrame(records)

    # ------------------------------------------------------------------
    # Schema validation
    # ------------------------------------------------------------------
    def validate_processed_complaint_schema(self, df: pd.DataFrame) -> List[str]:
        schema = get_processed_schema("processed_patient_complaints")
        if schema is None:
            return ["Schema not found for processed_patient_complaints"]
        errors = []
        for field in schema["required_fields"]:
            if field not in df.columns:
                errors.append(f"Missing required field: {field}")
        return errors

    def validate_processed_survey_schema(self, df: pd.DataFrame) -> List[str]:
        schema = get_processed_schema("processed_patient_surveys")
        if schema is None:
            return ["Schema not found for processed_patient_surveys"]
        errors = []
        for field in schema["required_fields"]:
            if field not in df.columns:
                errors.append(f"Missing required field: {field}")
        return errors

    # ------------------------------------------------------------------
    # Main transforms
    # ------------------------------------------------------------------
    def transform_complaints(self, complaints: pd.DataFrame) -> pd.DataFrame:
        df = complaints.copy()
        df["source_file"] = INPUT_DATASETS["patient_complaints"]
        df["source_record_id"] = df["complaint_id"]

        # Identifiers
        df = self.validate_complaint_identifiers(df)
        dup_blocks = any(i.blocks_processing for i in self.issues if i.issue_type == "Duplicate Primary Key")
        if dup_blocks:
            self._audit("Complaint Transform", "Blocked by duplicate IDs")
            return df

        # References
        df = self.validate_hospital_references(df, "complaint_id", "patient_complaints")
        df = self.validate_department_references(df, "complaint_id", "patient_complaints")

        # Dates
        df = self.parse_complaint_dates(df)

        # Classification
        df = self.classify_complaint_channels(df)
        df = self.classify_complaint_categories(df)
        df = self.classify_complaint_severity(df)

        # Flags
        df = self.derive_complaint_flags(df)

        # Metadata
        df["processing_run_id"] = self.processing_run_id
        df["processed_datetime"] = datetime.now()
        df["transformation_version"] = TRANSFORMATION_VERSION
        df["complaint_subcategory"] = np.nan

        # Reorder to schema
        schema = get_processed_schema("processed_patient_complaints")
        all_fields = schema["required_fields"] + schema.get("optional_fields", [])
        for col in all_fields:
            if col not in df.columns:
                df[col] = np.nan
        df = df[[c for c in all_fields if c in df.columns]]

        self.processed_complaints = df
        self._audit("Complaint Transform", f"{len(df)} rows processed")
        return df

    def transform_surveys(self, surveys: pd.DataFrame) -> pd.DataFrame:
        df = surveys.copy()
        df["source_file"] = INPUT_DATASETS["patient_surveys"]
        df["source_record_id"] = df["survey_id"]

        # Identifiers
        df = self.validate_survey_identifiers(df)
        dup_blocks = any(i.blocks_processing for i in self.issues if i.issue_type == "Duplicate Primary Key")
        if dup_blocks:
            self._audit("Survey Transform", "Blocked by duplicate IDs")
            return df

        # References
        df = self.validate_hospital_references(df, "survey_id", "patient_surveys")
        df = self.validate_department_references(df, "survey_id", "patient_surveys")

        # Dates
        df = self.parse_survey_dates(df)

        # Scores and counts
        df = self.validate_survey_scores(df)
        df = self.validate_response_counts(df)

        # Flags
        df = self.derive_survey_flags(df)

        # Metadata
        df["processing_run_id"] = self.processing_run_id
        df["processed_datetime"] = datetime.now()
        df["transformation_version"] = TRANSFORMATION_VERSION

        # Reorder to schema
        schema = get_processed_schema("processed_patient_surveys")
        all_fields = schema["required_fields"] + schema.get("optional_fields", [])
        for col in all_fields:
            if col not in df.columns:
                df[col] = np.nan
        df = df[[c for c in all_fields if c in df.columns]]

        self.processed_surveys = df
        self._audit("Survey Transform", f"{len(df)} rows processed")
        return df

    # ------------------------------------------------------------------
    # Collect issues
    # ------------------------------------------------------------------
    def collect_issues(self) -> pd.DataFrame:
        cols = [
            "source_dataset_name", "processed_dataset_name", "source_primary_key",
            "source_row_number", "field_name", "issue_type", "severity",
            "issue_description", "source_value", "exclusion_flag", "blocks_processing",
        ]
        if not self.issues:
            return pd.DataFrame(columns=cols)
        return pd.DataFrame([i.to_dict() for i in self.issues])

    # ------------------------------------------------------------------
    # Return results
    # ------------------------------------------------------------------
    def return_transformation_results(self) -> Dict[str, Any]:
        return {
            "processing_run_id": self.processing_run_id,
            "complaint_row_count": len(self.processed_complaints) if self.processed_complaints is not None else 0,
            "survey_row_count": len(self.processed_surveys) if self.processed_surveys is not None else 0,
            "issue_count": len(self.issues),
            "exclusion_count": len(self.exclusion_records),
            "lineage_count": len(self.lineage_records),
        }
