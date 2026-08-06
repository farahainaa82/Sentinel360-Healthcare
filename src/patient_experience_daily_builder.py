"""
Sentinel360 Healthcare — Patient Experience Daily Builder

Builds daily patient-experience preparation aggregates from
processed complaints and processed surveys.

Step: 2D-4
"""

import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd
import numpy as np

from src.processed_schema_registry import get_processed_schema


TRANSFORMATION_VERSION = "2D-4.0"
ENGINE_VERSION = "2D-4.0"


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


class PatientExperienceDailyBuilder:
    """Builds daily patient-experience aggregates."""

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
        self.input_directory = Path(input_directory)
        self.output_directory = Path(output_directory)
        self.log_directory = Path(log_directory)
        self.source_type = source_type
        self.collect_lineage = collect_lineage
        self.max_issue_examples = max_issue_examples

        self.issues: List[Issue] = []
        self.lineage_records: List[Dict[str, Any]] = []
        self.exclusion_records: List[Dict[str, Any]] = []
        self.audit_events: List[Dict[str, Any]] = []
        self.input_checksums: Dict[str, str] = {}
        self.input_record_counts: Dict[str, int] = {}

        self.complaints: Optional[pd.DataFrame] = None
        self.surveys: Optional[pd.DataFrame] = None
        self.daily: Optional[pd.DataFrame] = None

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

    def verify_input_checksums(self) -> bool:
        for filename in ["processed_patient_complaints.csv", "processed_patient_surveys.csv"]:
            path = self.input_directory / filename
            if not path.exists():
                return False
            current = self._file_checksum(path)
            if filename not in self.input_checksums:
                self.input_checksums[filename] = current
            elif self.input_checksums[filename] != current:
                return False
        return True

    # ------------------------------------------------------------------
    # Load inputs
    # ------------------------------------------------------------------
    def load_processed_complaints(self) -> pd.DataFrame:
        path = self.input_directory / "processed_patient_complaints.csv"
        if not path.exists():
            raise FileNotFoundError(f"Missing input: {path}")
        df = pd.read_csv(path, dtype=str, keep_default_na=True)
        self.input_record_counts["processed_patient_complaints"] = len(df)
        self.input_checksums["processed_patient_complaints.csv"] = self._file_checksum(path)
        self.complaints = df
        return df

    def set_processed_complaints(self, df: pd.DataFrame) -> pd.DataFrame:
        self.input_record_counts["processed_patient_complaints"] = len(df)
        self.complaints = df.copy()
        return self.complaints

    def load_processed_surveys(self) -> pd.DataFrame:
        path = self.input_directory / "processed_patient_surveys.csv"
        if not path.exists():
            raise FileNotFoundError(f"Missing input: {path}")
        df = pd.read_csv(path, dtype=str, keep_default_na=True)
        self.input_record_counts["processed_patient_surveys"] = len(df)
        self.input_checksums["processed_patient_surveys.csv"] = self._file_checksum(path)
        self.surveys = df
        return df

    def set_processed_surveys(self, df: pd.DataFrame) -> pd.DataFrame:
        self.input_record_counts["processed_patient_surveys"] = len(df)
        self.surveys = df.copy()
        return self.surveys

    # ------------------------------------------------------------------
    # Daily spine
    # ------------------------------------------------------------------
    def build_daily_spine(self) -> pd.DataFrame:
        if self.complaints is None or self.surveys is None:
            raise ValueError("Load complaints and surveys first.")

        c_elig = self.complaints[self.complaints["complaint_daily_aggregation_eligible_flag"].astype(str) == "True"].copy()
        s_elig = self.surveys[self.surveys["survey_aggregation_eligible_flag"].astype(str) == "True"].copy()

        c_dates = c_elig[["hospital_id", "department_id", "complaint_date"]].dropna().rename(columns={"complaint_date": "reporting_date"})
        s_dates = s_elig[["hospital_id", "department_id", "survey_date"]].dropna().rename(columns={"survey_date": "reporting_date"})

        spine = pd.concat([c_dates, s_dates], ignore_index=True).drop_duplicates()
        spine["reporting_date"] = pd.to_datetime(spine["reporting_date"], errors="coerce").dt.date
        spine = spine.dropna(subset=["hospital_id", "department_id", "reporting_date"])
        spine = spine.drop_duplicates()

        self._audit("Daily Spine", f"{len(spine)} unique hospital-department-date grains")
        return spine

    # ------------------------------------------------------------------
    # Aggregations
    # ------------------------------------------------------------------
    def aggregate_complaints(self, spine: pd.DataFrame) -> pd.DataFrame:
        if self.complaints is None:
            raise ValueError("Load complaints first.")

        df = self.complaints.copy()
        df["complaint_date"] = pd.to_datetime(df["complaint_date"], errors="coerce").dt.date

        # High severity
        df["is_high"] = df["complaint_severity"] == "High"
        df["is_medium"] = df["complaint_severity"] == "Medium"
        df["is_low"] = df["complaint_severity"] == "Low"
        df["is_open"] = df["complaint_open_source_flag"].astype(str) == "True"
        df["is_resolved"] = df["complaint_resolved_source_flag"].astype(str) == "True"
        df["is_valid"] = df["complaint_count_eligible_flag"].astype(str) == "True"
        df["is_excluded"] = df["exclusion_reason_code"].astype(str) != ""

        agg = df.groupby(["hospital_id", "department_id", "complaint_date"], as_index=False).agg(
            complaint_record_count=("complaint_id", "count"),
            complaint_valid_record_count=("is_valid", "sum"),
            complaint_excluded_record_count=("is_excluded", "sum"),
            complaint_high_severity_count=("is_high", "sum"),
            complaint_medium_severity_count=("is_medium", "sum"),
            complaint_low_severity_count=("is_low", "sum"),
            complaint_open_source_count=("is_open", "sum"),
            complaint_resolved_source_count=("is_resolved", "sum"),
            complaint_channel_distinct_count=("complaint_channel", "nunique"),
            complaint_category_distinct_count=("complaint_category", "nunique"),
        )
        agg = agg.rename(columns={"complaint_date": "reporting_date"})

        # Ensure numeric
        for col in agg.columns:
            if col not in ["hospital_id", "department_id", "reporting_date"]:
                agg[col] = pd.to_numeric(agg[col], errors="coerce").fillna(0).astype(int)

        self._audit("Complaint Aggregate", f"{len(agg)} daily complaint rows")
        return agg

    def aggregate_surveys(self, spine: pd.DataFrame) -> pd.DataFrame:
        if self.surveys is None:
            raise ValueError("Load surveys first.")

        df = self.surveys.copy()
        df["survey_date"] = pd.to_datetime(df["survey_date"], errors="coerce").dt.date
        df["response_count"] = pd.to_numeric(df["response_count"], errors="coerce")
        df["satisfaction_score_numeric"] = pd.to_numeric(df["satisfaction_score_numeric"], errors="coerce")
        df["is_valid_score"] = (
            (df["survey_score_eligible_flag"].astype(str) == "True") &
            df["satisfaction_score_numeric"].notna()
        )
        df["is_invalid_score"] = (
            df["satisfaction_score_numeric"].notna() &
            (df["satisfaction_score_valid_flag"].astype(str) == "False")
        )
        df["is_eligible"] = df["survey_aggregation_eligible_flag"].astype(str) == "True"

        agg = df.groupby(["hospital_id", "department_id", "survey_date"], as_index=False).agg(
            survey_record_count=("survey_id", "count"),
            survey_response_count_total=("response_count", "sum"),
            survey_valid_score_record_count=("is_valid_score", "sum"),
            survey_invalid_score_record_count=("is_invalid_score", "sum"),
            survey_score_sum=("satisfaction_score_numeric", "sum"),
            survey_score_weighted_sum=("satisfaction_score_numeric", lambda x: (x * df.loc[x.index, "response_count"]).sum()),
            survey_score_min=("satisfaction_score_numeric", "min"),
            survey_score_max=("satisfaction_score_numeric", "max"),
            survey_score_source_scale_count=("survey_id", "count"),
        )
        agg = agg.rename(columns={"survey_date": "reporting_date"})

        # Convert numeric columns
        for col in agg.columns:
            if col not in ["hospital_id", "department_id", "reporting_date"]:
                if col in ["survey_score_min", "survey_score_max"]:
                    agg[col] = pd.to_numeric(agg[col], errors="coerce")
                else:
                    agg[col] = pd.to_numeric(agg[col], errors="coerce").fillna(0).astype(int)

        self._audit("Survey Aggregate", f"{len(agg)} daily survey rows")
        return agg

    # ------------------------------------------------------------------
    # Combine
    # ------------------------------------------------------------------
    def combine_daily_components(
        self,
        spine: pd.DataFrame,
        complaint_agg: pd.DataFrame,
        survey_agg: pd.DataFrame,
    ) -> pd.DataFrame:
        daily = spine.copy()
        daily = daily.merge(
            complaint_agg,
            on=["hospital_id", "department_id", "reporting_date"],
            how="left",
            suffixes=("", "_c"),
        )
        daily = daily.merge(
            survey_agg,
            on=["hospital_id", "department_id", "reporting_date"],
            how="left",
            suffixes=("", "_s"),
        )

        # Fill complaint counts with 0 where no complaints
        complaint_cols = [
            "complaint_record_count", "complaint_valid_record_count",
            "complaint_excluded_record_count", "complaint_high_severity_count",
            "complaint_medium_severity_count", "complaint_low_severity_count",
            "complaint_open_source_count", "complaint_resolved_source_count",
            "complaint_channel_distinct_count", "complaint_category_distinct_count",
        ]
        for col in complaint_cols:
            if col in daily.columns:
                daily[col] = pd.to_numeric(daily[col], errors="coerce").fillna(0).astype(int)

        # Fill survey counts with 0 where no surveys
        survey_cols = [
            "survey_record_count", "survey_response_count_total",
            "survey_valid_score_record_count", "survey_invalid_score_record_count",
            "survey_score_sum", "survey_score_weighted_sum",
            "survey_score_source_scale_count",
        ]
        for col in survey_cols:
            if col in daily.columns:
                if col in ["survey_score_min", "survey_score_max"]:
                    daily[col] = pd.to_numeric(daily[col], errors="coerce")
                else:
                    daily[col] = pd.to_numeric(daily[col], errors="coerce").fillna(0)

        if "survey_score_min" in daily.columns:
            daily["survey_score_min"] = pd.to_numeric(daily["survey_score_min"], errors="coerce")
        if "survey_score_max" in daily.columns:
            daily["survey_score_max"] = pd.to_numeric(daily["survey_score_max"], errors="coerce")

        # Flags
        daily["complaint_source_present_flag"] = daily["complaint_record_count"] > 0
        daily["survey_source_present_flag"] = daily["survey_record_count"] > 0
        daily["complaint_count_available_flag"] = daily["complaint_source_present_flag"]
        daily["survey_score_available_flag"] = daily["survey_valid_score_record_count"] > 0
        daily["survey_response_count_available_flag"] = daily["survey_response_count_total"] > 0
        daily["patient_experience_data_complete_flag"] = (
            daily["complaint_source_present_flag"] | daily["survey_source_present_flag"]
        )
        daily["unresolved_rule_flag"] = False

        # Date parts
        daily["reporting_date"] = pd.to_datetime(daily["reporting_date"], errors="coerce")
        daily["reporting_month"] = daily["reporting_date"].dt.month
        daily["reporting_year"] = daily["reporting_date"].dt.year
        daily["reporting_date"] = daily["reporting_date"].dt.date

        self._audit("Daily Combined", f"{len(daily)} rows")
        return daily

    # ------------------------------------------------------------------
    # Daily identifier
    # ------------------------------------------------------------------
    def create_daily_identifier(self, daily: pd.DataFrame) -> pd.DataFrame:
        daily["patient_experience_daily_id"] = daily.apply(
            lambda r: f"PEX-{r['hospital_id']}-{r['department_id']}-{pd.to_datetime(r['reporting_date']).strftime('%Y%m%d')}",
            axis=1,
        )
        return daily

    # ------------------------------------------------------------------
    # Grain validation
    # ------------------------------------------------------------------
    def validate_daily_grain(self, daily: pd.DataFrame) -> Tuple[bool, int]:
        dup_count = daily["patient_experience_daily_id"].duplicated().sum()
        if dup_count > 0:
            self._add_issue(
                source_dataset_name="",
                processed_dataset_name="processed_patient_experience_daily",
                source_primary_key="",
                source_row_number=0,
                field_name="patient_experience_daily_id",
                issue_type="Duplicate Daily Identifier",
                severity="Critical",
                issue_description=f"{dup_count} duplicate patient_experience_daily_id values found.",
                source_value="",
                exclusion_flag=False,
                blocks_processing=True,
            )
            return False, dup_count

        # Also verify hospital-department-date grain uniqueness
        grain_dups = daily.duplicated(subset=["hospital_id", "department_id", "reporting_date"]).sum()
        if grain_dups > 0:
            self._add_issue(
                source_dataset_name="",
                processed_dataset_name="processed_patient_experience_daily",
                source_primary_key="",
                source_row_number=0,
                field_name="grain",
                issue_type="Duplicate Daily Grain",
                severity="Critical",
                issue_description=f"{grain_dups} duplicate hospital-department-date grains found.",
                source_value="",
                exclusion_flag=False,
                blocks_processing=True,
            )
            return False, grain_dups

        return True, 0

    # ------------------------------------------------------------------
    # Schema validation
    # ------------------------------------------------------------------
    def validate_daily_schema(self, daily: pd.DataFrame) -> List[str]:
        schema = get_processed_schema("processed_patient_experience_daily")
        if schema is None:
            return ["Schema not found for processed_patient_experience_daily"]
        errors = []
        for field in schema["required_fields"]:
            if field not in daily.columns:
                errors.append(f"Missing required field: {field}")
        return errors

    # ------------------------------------------------------------------
    # Daily lineage
    # ------------------------------------------------------------------
    def build_daily_lineage(
        self,
        daily: pd.DataFrame,
        complaints: pd.DataFrame,
        surveys: pd.DataFrame,
    ) -> pd.DataFrame:
        if not self.collect_lineage:
            return pd.DataFrame()

        records = []
        c_elig = complaints[complaints["complaint_daily_aggregation_eligible_flag"].astype(str) == "True"].copy()
        s_elig = surveys[surveys["survey_aggregation_eligible_flag"].astype(str) == "True"].copy()

        c_elig["complaint_date"] = pd.to_datetime(c_elig["complaint_date"], errors="coerce")
        s_elig["survey_date"] = pd.to_datetime(s_elig["survey_date"], errors="coerce")

        for _, drow in daily.iterrows():
            daily_id = drow["patient_experience_daily_id"]
            hid = drow["hospital_id"]
            did = drow["department_id"]
            rdate = pd.to_datetime(drow["reporting_date"]).date()

            # Complaint lineage
            c_match = c_elig[
                (c_elig["hospital_id"] == hid) &
                (c_elig["department_id"] == did) &
                (c_elig["complaint_date"].dt.date == rdate)
            ]
            for _, crow in c_match.iterrows():
                records.append({
                    "lineage_id": f"LIN-{uuid.uuid4().hex[:12].upper()}",
                    "processing_run_id": self.processing_run_id,
                    "output_dataset": "processed_patient_experience_daily",
                    "output_record_id": str(daily_id),
                    "source_dataset": "processed_patient_complaints",
                    "source_record_id": str(crow.get("complaint_id", "")),
                    "source_file": str(crow.get("source_file", "")),
                    "source_row_number": int(crow.get("source_row_number", 0)),
                    "transformation_name": "patient_experience_daily_build",
                    "transformation_version": TRANSFORMATION_VERSION,
                    "lineage_datetime": datetime.now().isoformat(),
                })

            # Survey lineage
            s_match = s_elig[
                (s_elig["hospital_id"] == hid) &
                (s_elig["department_id"] == did) &
                (s_elig["survey_date"].dt.date == rdate)
            ]
            for _, srow in s_match.iterrows():
                records.append({
                    "lineage_id": f"LIN-{uuid.uuid4().hex[:12].upper()}",
                    "processing_run_id": self.processing_run_id,
                    "output_dataset": "processed_patient_experience_daily",
                    "output_record_id": str(daily_id),
                    "source_dataset": "processed_patient_surveys",
                    "source_record_id": str(srow.get("survey_id", "")),
                    "source_file": str(srow.get("source_file", "")),
                    "source_row_number": int(srow.get("source_row_number", 0)),
                    "transformation_name": "patient_experience_daily_build",
                    "transformation_version": TRANSFORMATION_VERSION,
                    "lineage_datetime": datetime.now().isoformat(),
                })

        self.lineage_records.extend(records)
        return pd.DataFrame(records)

    # ------------------------------------------------------------------
    # Exclusions
    # ------------------------------------------------------------------
    def build_daily_exclusions(self) -> pd.DataFrame:
        return pd.DataFrame(columns=[
            "exclusion_id", "dataset_name", "source_record_id",
            "exclusion_reason_code", "exclusion_reason", "severity",
            "source_file", "source_row_number", "processing_run_id", "excluded_datetime",
        ])

    # ------------------------------------------------------------------
    # Issues / result
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

    def return_daily_result(self) -> Dict[str, Any]:
        return {
            "processing_run_id": self.processing_run_id,
            "daily_row_count": len(self.daily) if self.daily is not None else 0,
            "issue_count": len(self.issues),
            "exclusion_count": len(self.exclusion_records),
            "lineage_count": len(self.lineage_records),
        }
