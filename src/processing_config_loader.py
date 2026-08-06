"""
Sentinel360 Healthcare — Processing Configuration Loader

Loads processing-related configuration from approved CSV files.
Handles attendance status mapping, absence category mapping,
configuration versioning, and effective-dated rule selection.

Step: 2D-1
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


def _config_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "config"


def load_attendance_mapping() -> pd.DataFrame:
    """Load the approved attendance status mapping from config.

    Returns a DataFrame with columns including:
    source_status, staffing_availability_treatment, absenteeism_treatment,
    department_attribution_rule, requires_actual_hours, missing_record_flag.
    """
    path = _config_dir() / "attendance_status_mapping.csv"
    if not path.exists():
        raise FileNotFoundError(f"Attendance mapping not found: {path}")
    df = pd.read_csv(path, dtype=str)
    required_cols = ["source_status", "staffing_availability_treatment", "absenteeism_treatment"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Attendance mapping missing required columns: {missing}")
    # Validate uniqueness of source_status
    dupes = df["source_status"][df["source_status"].duplicated()].unique().tolist()
    if dupes:
        raise ValueError(f"Duplicate source_status values in attendance mapping: {dupes}")
    return df


def load_absence_mapping() -> pd.DataFrame:
    """Load the approved absence category mapping from config.

    Returns a DataFrame with columns including:
    absence_category, planned_absence_flag, operational_absenteeism_flag,
    staffing_unavailable_flag, include_in_absenteeism_numerator.
    """
    path = _config_dir() / "absence_category_mapping.csv"
    if not path.exists():
        raise FileNotFoundError(f"Absence mapping not found: {path}")
    df = pd.read_csv(path, dtype=str)
    required_cols = ["absence_category", "planned_absence_flag", "operational_absenteeism_flag"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Absence mapping missing required columns: {missing}")
    dupes = df["absence_category"][df["absence_category"].duplicated()].unique().tolist()
    if dupes:
        raise ValueError(f"Duplicate absence_category values in absence mapping: {dupes}")
    return df


def get_attendance_status_for_missing() -> str:
    """Return the standardised status for a missing attendance record.

    Per approved rules, missing attendance must remain Unknown.
    """
    df = load_attendance_mapping()
    missing_row = df[df["missing_record_flag"] == "true"]
    if missing_row.empty:
        return "Unknown"
    # Prefer explicit Unknown mapping if present; otherwise accept Missing
    unknown_row = missing_row[missing_row["source_status"].str.lower() == "unknown"]
    if not unknown_row.empty:
        return str(unknown_row.iloc[0]["source_status"])
    return str(missing_row.iloc[0]["source_status"])


def is_missing_classified_as_present() -> bool:
    """Return True if the mapping incorrectly classifies Missing as Present."""
    df = load_attendance_mapping()
    missing_rows = df[df["missing_record_flag"] == "true"]
    if missing_rows.empty:
        return False
    return any(missing_rows["source_status"].str.lower() == "present")


def is_missing_classified_as_absent() -> bool:
    """Return True if the mapping incorrectly classifies Missing as Absent."""
    df = load_attendance_mapping()
    missing_rows = df[df["missing_record_flag"] == "true"]
    if missing_rows.empty:
        return False
    return any(missing_rows["source_status"].str.lower() == "absent")


def select_effective_configuration(
    df: pd.DataFrame,
    as_of_date: Optional[datetime] = None,
) -> pd.DataFrame:
    """Filter a configuration DataFrame to the rules effective at the given date.

    If as_of_date is None, uses the current UTC datetime.
    Expects columns: effective_start_date, effective_end_date, active_flag.
    """
    if as_of_date is None:
        as_of_date = datetime.utcnow()

    if "effective_start_date" not in df.columns:
        raise ValueError("Configuration DataFrame missing effective_start_date")

    df = df.copy()
    df["effective_start_date"] = pd.to_datetime(df["effective_start_date"], errors="coerce")
    if "effective_end_date" in df.columns:
        df["effective_end_date"] = pd.to_datetime(df["effective_end_date"], errors="coerce")
    else:
        df["effective_end_date"] = pd.NaT

    mask = (
        (df["effective_start_date"] <= as_of_date)
        & (df["effective_end_date"].isna() | (df["effective_end_date"] >= as_of_date))
    )
    if "active_flag" in df.columns:
        mask = mask & (df["active_flag"].astype(str).str.lower() == "true")

    return df[mask].copy()


def validate_processing_configuration() -> List[str]:
    """Validate processing configuration and return a list of error messages."""
    errors: List[str] = []

    # Attendance mapping
    try:
        att_df = load_attendance_mapping()
        if "source_status" not in att_df.columns:
            errors.append("Attendance mapping missing source_status column")
        else:
            # Missing must remain Unknown
            missing_rows = att_df[att_df["missing_record_flag"] == "true"]
            if missing_rows.empty:
                errors.append("Attendance mapping has no rule for missing records")
            else:
                statuses = set(missing_rows["source_status"].str.strip().str.lower())
                if "present" in statuses:
                    errors.append("Attendance mapping classifies missing record as Present")
                if "absent" in statuses:
                    errors.append("Attendance mapping classifies missing record as Absent")
                if not (statuses & {"unknown", "missing"}):
                    errors.append(f"Missing attendance classified as unexpected status: {statuses}")
    except Exception as exc:
        errors.append(f"Attendance mapping error: {exc}")

    # Absence mapping
    try:
        abs_df = load_absence_mapping()
        if "absence_category" not in abs_df.columns:
            errors.append("Absence mapping missing absence_category column")
    except Exception as exc:
        errors.append(f"Absence mapping error: {exc}")

    return errors


def get_transformation_configuration_version() -> str:
    """Return the current transformation configuration version string.

    Derived from the most recent effective configuration record.
    """
    try:
        df = load_attendance_mapping()
        effective = select_effective_configuration(df)
        if not effective.empty and "configuration_version" in effective.columns:
            return str(effective.iloc[0]["configuration_version"])
    except Exception:
        pass
    return "v1.0-draft"
