"""
Profile Demo Data — Sentinel360 Healthcare

Reads the exported synthetic source CSVs, profiles them, checks relationships,
inspects storyline indicators, and produces summary files.

This module does NOT modify source CSV files and does NOT calculate official
KPI values, statuses, forecasts, or recommendations.

Usage:
    python src/profile_demo_data.py
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Ensure src/ is importable
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _PROJECT_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from demo_data_generator import (
    VALID_COMPLAINT_STATUSES,
    VALID_ATTENDANCE_STATUSES,
)
from demo_generation_config import get_default_config

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEMO_DIR: Path = _PROJECT_ROOT / "data" / "demo"

EXPECTED_DATASETS: List[str] = [
    "hospital_master",
    "department_master",
    "staff_role_master",
    "staff_master",
    "staff_roster",
    "staff_attendance",
    "staffing_requirement",
    "patient_encounters",
    "patient_queue_records",
    "bed_capacity_records",
    "patient_complaints",
    "patient_surveys",
    "service_schedule",
]

PRIMARY_KEYS: Dict[str, str] = {
    "hospital_master": "hospital_id",
    "department_master": "department_id",
    "staff_role_master": "role_id",
    "staff_master": "staff_id",
    "staff_roster": "roster_id",
    "staff_attendance": "attendance_id",
    "staffing_requirement": "requirement_id",
    "patient_encounters": "encounter_id",
    "patient_queue_records": "queue_id",
    "bed_capacity_records": "record_id",
    "patient_complaints": "complaint_id",
    "patient_surveys": "survey_id",
    "service_schedule": "schedule_id",
}

DATE_COLUMNS: Dict[str, str] = {
    "staff_roster": "roster_date",
    "staff_attendance": "attendance_date",
    "patient_encounters": "encounter_date",
    "patient_queue_records": "queue_date",
    "bed_capacity_records": "record_date",
    "patient_complaints": "complaint_received_date",
    "patient_surveys": "survey_date",
    "service_schedule": "service_date",
    "staffing_requirement": "requirement_date",
}

# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------


def load_demo_datasets(demo_dir: Path = DEMO_DIR) -> Dict[str, pd.DataFrame]:
    """Load all exported CSV files into DataFrames."""
    data: Dict[str, pd.DataFrame] = {}
    for name in EXPECTED_DATASETS:
        filepath = demo_dir / f"{name}.csv"
        if not filepath.exists():
            raise FileNotFoundError(f"Expected file not found: {filepath}")
        df = pd.read_csv(filepath, dtype=str, keep_default_na=True)
        # Parse known date/datetime columns
        for col in df.columns:
            if "date" in col.lower() or "datetime" in col.lower():
                try:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
                except Exception:
                    pass
            if col in ["is_active", "is_clinical", "is_complete", "exception_flag", "duplicate_flag"]:
                df[col] = df[col].map({"True": True, "False": False, "true": True, "false": False, "1": True, "0": False}).fillna(df[col])
            # Coerce numeric columns for profiling
            numeric_hints = [
                "bed_licensed", "bed_staffed", "bed_operational", "bed_occupied", "bed_unavailable", "bed_reserved",
                "occupancy_rate", "planned_hours", "actual_hours", "required_staff_count", "required_hours",
                "arrivals_count", "served_count", "waiting_count", "avg_wait_minutes", "median_wait_minutes", "max_wait_minutes",
                "planned_capacity", "score_value", "response_weight", "fte_value", "record_version",
            ]
            if col in numeric_hints:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        data[name] = df
    return data


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------


def profile_dataset(name: str, df: pd.DataFrame) -> Dict[str, Any]:
    """Return a profile dictionary for a single dataset."""
    pk = PRIMARY_KEYS.get(name)
    pk_unique = df[pk].nunique(dropna=False) if pk else None
    pk_duplicates = len(df) - pk_unique if pk else None

    date_col = DATE_COLUMNS.get(name)
    earliest = df[date_col].min() if date_col and date_col in df.columns else None
    latest = df[date_col].max() if date_col and date_col in df.columns else None

    required_cols = list(df.columns)
    missing_req = 0
    for col in required_cols:
        missing_req += df[col].isna().sum()

    total_missing = df.isna().sum().sum()

    hosp_count = df["hospital_id"].nunique() if "hospital_id" in df.columns else None
    dept_count = df["department_id"].nunique() if "department_id" in df.columns else None
    src_count = df["source_system"].nunique() if "source_system" in df.columns else None

    upload_count = df["upload_id"].nunique() if "upload_id" in df.columns else None
    ver_count = df["record_version"].nunique() if "record_version" in df.columns else None

    status = "Passed"
    notes = []
    if pk_duplicates and pk_duplicates > 0:
        status = "Failed"
        notes.append(f"Duplicate PKs: {pk_duplicates}")
    if missing_req > 0:
        status = "Passed with Observations" if status != "Failed" else status
        notes.append(f"Missing values in required columns: {missing_req}")

    return {
        "dataset_name": name,
        "file_name": f"{name}.csv",
        "row_count": len(df),
        "column_count": len(df.columns),
        "primary_key": pk,
        "unique_primary_key_count": pk_unique,
        "duplicate_primary_key_count": pk_duplicates,
        "required_column_count": len(required_cols),
        "missing_required_value_count": int(missing_req),
        "total_missing_value_count": int(total_missing),
        "earliest_date": str(earliest) if earliest is not None else None,
        "latest_date": str(latest) if latest is not None else None,
        "hospital_count": hosp_count,
        "department_count": dept_count,
        "source_system_count": src_count,
        "upload_id_count": upload_count,
        "record_version_count": ver_count,
        "profile_status": status,
        "profile_notes": "; ".join(notes) if notes else "No issues observed",
    }


def profile_all_datasets(data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Profile all datasets and return a summary DataFrame."""
    rows = [profile_dataset(name, df) for name, df in data.items()]
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Relationship Checks
# ---------------------------------------------------------------------------


def _check_fk(
    child_df: pd.DataFrame,
    child_field: str,
    parent_df: pd.DataFrame,
    parent_field: str,
    allow_null: bool = True,
) -> Dict[str, Any]:
    """Check foreign-key relationship and return summary dict."""
    child_values = child_df[child_field]
    populated = child_values.notna()
    parent_values = set(parent_df[parent_field].dropna().unique())
    valid = child_values[populated].isin(parent_values).sum()
    orphan = populated.sum() - valid
    null_count = (~populated).sum()

    if orphan > 0:
        rel_status = "Failed"
    elif null_count > 0 and allow_null:
        rel_status = "Passed with Optional Nulls"
    else:
        rel_status = "Passed"

    return {
        "child_dataset": child_df.name if hasattr(child_df, "name") else "",
        "child_field": child_field,
        "parent_dataset": parent_df.name if hasattr(parent_df, "name") else "",
        "parent_field": parent_field,
        "populated_child_values": int(populated.sum()),
        "valid_reference_count": int(valid),
        "orphan_reference_count": int(orphan),
        "null_reference_count": int(null_count),
        "relationship_status": rel_status,
        "notes": "Orphan references detected" if orphan > 0 else "",
    }


def build_relationship_summary(data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build relationship check summary across all datasets."""
    checks: List[Dict[str, Any]] = []
    hm = data["hospital_master"]
    dm = data["department_master"]
    srm = data["staff_role_master"]
    sm = data["staff_master"]
    sr = data["staff_roster"]
    sa = data["staff_attendance"]
    stf_req = data["staffing_requirement"]
    pe = data["patient_encounters"]
    pq = data["patient_queue_records"]
    bc = data["bed_capacity_records"]
    pc = data["patient_complaints"]
    ps = data["patient_surveys"]
    ss = data["service_schedule"]

    def add_check(child_df, child_field, parent_df, parent_field, allow_null=True):
        result = _check_fk(child_df, child_field, parent_df, parent_field, allow_null)
        result["relationship_id"] = f"REL-{len(checks)+1:03d}"
        checks.append(result)

    add_check(dm, "hospital_id", hm, "hospital_id", allow_null=False)
    add_check(sm, "hospital_id", hm, "hospital_id", allow_null=False)
    add_check(sm, "department_id", dm, "department_id", allow_null=False)
    add_check(sm, "role_id", srm, "role_id", allow_null=False)
    add_check(sr, "hospital_id", hm, "hospital_id", allow_null=False)
    add_check(sr, "department_id", dm, "department_id", allow_null=False)
    add_check(sr, "staff_id", sm, "staff_id", allow_null=False)
    add_check(sr, "role_id", srm, "role_id", allow_null=False)
    add_check(sa, "hospital_id", hm, "hospital_id", allow_null=False)
    add_check(sa, "department_id", dm, "department_id", allow_null=False)
    add_check(sa, "staff_id", sm, "staff_id", allow_null=False)
    add_check(sa, "role_id", srm, "role_id", allow_null=False)
    add_check(sa, "roster_id", sr, "roster_id", allow_null=False)
    add_check(sa, "replacement_staff_id", sm, "staff_id", allow_null=True)
    add_check(stf_req, "hospital_id", hm, "hospital_id", allow_null=False)
    add_check(stf_req, "department_id", dm, "department_id", allow_null=False)
    add_check(stf_req, "role_id", srm, "role_id", allow_null=False)
    add_check(pe, "hospital_id", hm, "hospital_id", allow_null=False)
    add_check(pe, "department_id", dm, "department_id", allow_null=False)
    add_check(pq, "hospital_id", hm, "hospital_id", allow_null=False)
    add_check(pq, "department_id", dm, "department_id", allow_null=False)
    add_check(bc, "hospital_id", hm, "hospital_id", allow_null=False)
    add_check(bc, "department_id", dm, "department_id", allow_null=False)
    add_check(pc, "hospital_id", hm, "hospital_id", allow_null=False)
    add_check(pc, "department_id", dm, "department_id", allow_null=False)
    add_check(pc, "encounter_id", pe, "encounter_id", allow_null=True)
    add_check(ps, "hospital_id", hm, "hospital_id", allow_null=False)
    add_check(ps, "department_id", dm, "department_id", allow_null=False)
    add_check(ps, "encounter_id", pe, "encounter_id", allow_null=True)
    add_check(ss, "hospital_id", hm, "hospital_id", allow_null=False)
    add_check(ss, "department_id", dm, "department_id", allow_null=False)

    return pd.DataFrame(checks)


# ---------------------------------------------------------------------------
# Storyline Inspection
# ---------------------------------------------------------------------------


def inspect_storyline_sources(data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Inspect source-level indicators by month to verify the operational storyline.
    These are descriptive inspections, not official KPI outputs.
    """
    sr = data["staff_roster"]
    sa = data["staff_attendance"]
    pe = data["patient_encounters"]
    pq = data["patient_queue_records"]
    bc = data["bed_capacity_records"]
    pc = data["patient_complaints"]
    ps = data["patient_surveys"]
    ss = data["service_schedule"]

    # Month extraction helper
    def to_month(series):
        return series.dt.to_period("M").dt.to_timestamp()

    # Rostered hours by month
    sr["month"] = to_month(sr["roster_date"])
    rostered = sr.groupby("month")["planned_hours"].sum().reset_index(name="rostered_hours")

    # Attendance hours by month
    sa["month"] = to_month(sa["attendance_date"])
    attendance_hours = sa.groupby("month")["actual_hours"].sum().reset_index(name="verified_attendance_hours")
    absent_events = (
        sa[sa["status"] == "Absent"]
        .groupby("month")
        .size()
        .reset_index(name="absent_event_count")
    )
    partial_events = (
        sa[sa["status"] == "Partial"]
        .groupby("month")
        .size()
        .reset_index(name="partial_attendance_count")
    )

    # Encounters by month
    pe["month"] = to_month(pe["encounter_date"])
    encounters = pe.groupby("month").size().reset_index(name="encounter_count")

    # Wait minutes by month (descriptive)
    completed = pe[pe["status"] == "Completed"].copy()
    completed["wait_minutes"] = (completed["service_start_datetime"] - completed["arrival_datetime"]).dt.total_seconds() / 60.0
    wait_min = completed.groupby("month")["wait_minutes"].mean().reset_index(name="descriptive_wait_minutes")

    # Queue records by month
    pq["month"] = to_month(pq["queue_date"])
    queue_wait = pq.groupby("month")["avg_wait_minutes"].mean().reset_index(name="queue_avg_wait_minutes")

    # Bed capacity by month
    bc["month"] = to_month(bc["record_date"])
    bed_stats = bc.groupby("month").agg(
        occupied_bed_count=("bed_occupied", "sum"),
        operational_bed_count=("bed_operational", "sum"),
    ).reset_index()

    # Complaints by month
    pc["month"] = to_month(pc["complaint_received_date"])
    complaints = pc.groupby("month").size().reset_index(name="complaint_count")

    # Surveys by month
    ps["month"] = to_month(ps["survey_date"])
    survey_stats = ps.groupby("month").agg(
        survey_response_count=("survey_id", "count"),
        descriptive_normalised_satisfaction=("score_value", "mean"),
    ).reset_index()

    # Service schedule by month
    ss["month"] = to_month(ss["service_date"])
    reduced = (
        ss[ss["schedule_status"] == "Reduced"]
        .groupby("month")
        .size()
        .reset_index(name="reduced_service_session_count")
    )
    cancelled = (
        ss[ss["schedule_status"] == "Cancelled"]
        .groupby("month")
        .size()
        .reset_index(name="cancelled_service_session_count")
    )

    # Merge all
    months = pd.DataFrame({"month": pd.date_range("2026-01-01", "2026-12-01", freq="MS")})
    merged = months
    for df in [rostered, attendance_hours, absent_events, partial_events, encounters, wait_min, queue_wait, bed_stats, complaints, survey_stats, reduced, cancelled]:
        merged = merged.merge(df, on="month", how="left")

    # Add storyline phase
    config = get_default_config()
    merged["storyline_phase"] = merged["month"].apply(lambda d: config.get_phase_for_date(d.date())["phase_name"])
    merged["inspection_notes"] = "Descriptive source-level inspection only; not an official KPI output."

    # Reorder columns
    cols = [
        "month", "storyline_phase", "rostered_hours", "verified_attendance_hours",
        "absent_event_count", "partial_attendance_count", "encounter_count",
        "descriptive_wait_minutes", "queue_avg_wait_minutes",
        "occupied_bed_count", "operational_bed_count",
        "complaint_count", "survey_response_count", "descriptive_normalised_satisfaction",
        "reduced_service_session_count", "cancelled_service_session_count",
        "inspection_notes",
    ]
    for c in cols:
        if c not in merged.columns:
            merged[c] = np.nan
    return merged[cols]


# ---------------------------------------------------------------------------
# Data Quality Observations
# ---------------------------------------------------------------------------


def build_data_quality_observation_summary(data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build data-quality observation summary (profiling only, not full validation)."""
    observations: List[Dict[str, Any]] = []
    counter = 1

    def add_obs(
        dataset_name: str,
        obs_type: str,
        severity: str,
        record_count: int,
        expected_in_clean: bool,
        status: str,
        explanation: str,
        requires_step2c: bool = True,
    ) -> None:
        nonlocal counter
        observations.append({
            "observation_id": f"OBS-{counter:03d}",
            "dataset_name": dataset_name,
            "observation_type": obs_type,
            "severity": severity,
            "record_count": record_count,
            "expected_in_clean_mode": expected_in_clean,
            "observation_status": status,
            "explanation": explanation,
            "requires_step_2c_validation": requires_step2c,
        })
        counter += 1

    # Duplicate PKs
    for name, df in data.items():
        pk = PRIMARY_KEYS[name]
        dup_count = df[pk].duplicated().sum()
        add_obs(
            name,
            "Duplicate Primary Keys",
            "Critical" if dup_count > 0 else "Information",
            int(dup_count),
            False,
            "Failed" if dup_count > 0 else "Not Observed",
            f"Duplicate {pk} count: {dup_count}",
        )

    # Missing mandatory values (spot check on key fields)
    mandatory_checks = {
        "staff_master": ["staff_id", "hospital_id", "department_id", "role_id"],
        "patient_encounters": ["encounter_id", "hospital_id", "department_id", "arrival_datetime"],
        "staff_attendance": ["attendance_id", "staff_id", "roster_id"],
    }
    for ds, cols in mandatory_checks.items():
        df = data[ds]
        for col in cols:
            null_count = df[col].isna().sum()
            add_obs(
                ds,
                f"Missing Mandatory Value: {col}",
                "Error" if null_count > 0 else "Information",
                int(null_count),
                False,
                "Failed" if null_count > 0 else "Not Observed",
                f"Null count in {col}: {null_count}",
            )

    # Negative values
    neg_checks = {
        "staffing_requirement": ["required_staff_count", "required_hours"],
        "patient_queue_records": ["arrivals_count", "served_count", "waiting_count"],
        "bed_capacity_records": ["bed_licensed", "bed_staffed", "bed_operational", "bed_occupied"],
        "service_schedule": ["planned_capacity", "planned_hours"],
    }
    for ds, cols in neg_checks.items():
        df = data[ds]
        for col in cols:
            neg = (pd.to_numeric(df[col], errors="coerce") < 0).sum()
            add_obs(
                ds,
                f"Negative Value: {col}",
                "Error" if neg > 0 else "Information",
                int(neg),
                False,
                "Failed" if neg > 0 else "Not Observed",
                f"Negative count in {col}: {neg}",
            )

    # Invalid date ordering (encounters)
    enc = data["patient_encounters"]
    completed = enc[enc["status"] == "Completed"]
    if len(completed) > 0:
        invalid = (completed["service_start_datetime"] < completed["arrival_datetime"]).sum()
        add_obs(
            "patient_encounters",
            "Invalid Date Ordering (service_start < arrival)",
            "Error" if invalid > 0 else "Information",
            int(invalid),
            False,
            "Failed" if invalid > 0 else "Not Observed",
            f"Invalid timestamp order count: {invalid}",
        )

    # Occupied above operational
    bed = data["bed_capacity_records"]
    over = bed[pd.to_numeric(bed["bed_occupied"], errors="coerce") > pd.to_numeric(bed["bed_operational"], errors="coerce")]
    over_count = len(over)
    add_obs(
        "bed_capacity_records",
        "Occupied Beds Above Operational Beds",
        "Warning",
        over_count,
        True,
        "Expected" if over_count > 0 else "Not Observed",
        "Occupancy may exceed 100% during pressure periods; exception flag and reason should be present.",
    )

    # Occupied above operational without exception flag
    if over_count > 0:
        no_flag = over[over["exception_flag"] != True]
        add_obs(
            "bed_capacity_records",
            "Over-Capacity Without Exception Flag",
            "Error" if len(no_flag) > 0 else "Information",
            int(len(no_flag)),
            False,
            "Failed" if len(no_flag) > 0 else "Not Observed",
            f"Records with occupied > operational but exception_flag != True: {len(no_flag)}",
        )

    # Occupied above operational without reason
    if over_count > 0:
        no_reason = over[over["exception_reason"].isna() | (over["exception_reason"] == "")]
        add_obs(
            "bed_capacity_records",
            "Over-Capacity Without Exception Reason",
            "Error" if len(no_reason) > 0 else "Information",
            int(len(no_reason)),
            False,
            "Failed" if len(no_reason) > 0 else "Not Observed",
            f"Records with occupied > operational but missing exception_reason: {len(no_reason)}",
        )

    # Operational above licensed
    op_above_lic = (pd.to_numeric(bed["bed_operational"], errors="coerce") > pd.to_numeric(bed["bed_licensed"], errors="coerce")).sum()
    add_obs(
        "bed_capacity_records",
        "Operational Beds Above Licensed Beds",
        "Warning" if op_above_lic > 0 else "Information",
        int(op_above_lic),
        False,
        "Observed" if op_above_lic > 0 else "Not Observed",
        "Operational beds should not normally exceed licensed beds.",
    )

    # Invalid queue counts (served > arrivals)
    pq = data["patient_queue_records"]
    invalid_queue = (pd.to_numeric(pq["served_count"], errors="coerce") > pd.to_numeric(pq["arrivals_count"], errors="coerce")).sum()
    add_obs(
        "patient_queue_records",
        "Served Count Greater Than Arrivals",
        "Error" if invalid_queue > 0 else "Information",
        int(invalid_queue),
        False,
        "Failed" if invalid_queue > 0 else "Not Observed",
        f"served_count > arrivals_count in {invalid_queue} rows",
    )

    # Survey scores outside scale
    ps = data["patient_surveys"]
    complete = ps[ps["is_complete"] == True]
    scale_5 = complete[complete["scale_id"] == "SCALE-5PT"]
    out_of_scale_5 = (pd.to_numeric(scale_5["score_value"], errors="coerce") < 1) | (pd.to_numeric(scale_5["score_value"], errors="coerce") > 5)
    add_obs(
        "patient_surveys",
        "Survey Score Outside 5-Point Scale",
        "Error" if out_of_scale_5.sum() > 0 else "Information",
        int(out_of_scale_5.sum()),
        False,
        "Failed" if out_of_scale_5.sum() > 0 else "Not Observed",
        f"Scores outside [1,5] for SCALE-5PT: {out_of_scale_5.sum()}",
    )

    # Invalid complaint status
    pc = data["patient_complaints"]
    invalid_status = (~pc["status"].isin(VALID_COMPLAINT_STATUSES)).sum()
    add_obs(
        "patient_complaints",
        "Invalid Complaint Status",
        "Error" if invalid_status > 0 else "Information",
        int(invalid_status),
        False,
        "Failed" if invalid_status > 0 else "Not Observed",
        f"Unrecognised complaint statuses: {invalid_status}",
    )

    # Records outside configured date range
    config = get_default_config()
    for ds, col in DATE_COLUMNS.items():
        df = data[ds]
        if col not in df.columns:
            continue
        min_d = df[col].min()
        max_d = df[col].max()
        outside = ((df[col] < pd.Timestamp(config.start_date)) | (df[col] > pd.Timestamp(config.end_date))).sum()
        add_obs(
            ds,
            "Records Outside Configured Date Range",
            "Error" if outside > 0 else "Information",
            int(outside),
            False,
            "Failed" if outside > 0 else "Not Observed",
            f"Date range: {min_d} to {max_d}; configured: {config.start_date} to {config.end_date}",
        )

    # Unexpected direct identifiers
    forbidden_fields = {
        "patient_name", "patient_full_name", "identity_card", "ic_number",
        "passport_number", "address", "telephone", "phone_number", "email",
        "diagnosis", "clinical_note", "medical_record_number", "mrn",
    }
    for name, df in data.items():
        # staff_master contains email/phone/address as approved schema fields,
        # but they must be blank (tested separately). Exclude from this check.
        if name == "staff_master":
            continue
        found = forbidden_fields.intersection(set(df.columns))
        if found:
            add_obs(
                name,
                "Unexpected Direct Identifier Fields",
                "Critical",
                len(found),
                False,
                "Failed",
                f"Forbidden fields present: {found}",
            )
        else:
            add_obs(
                name,
                "Unexpected Direct Identifier Fields",
                "Information",
                0,
                False,
                "Not Observed",
                "No forbidden identifier fields found.",
            )

    # Staff names check
    sm = data["staff_master"]
    name_populated = sm["staff_name"].notna().sum() if "staff_name" in sm.columns else 0
    add_obs(
        "staff_master",
        "Staff Names Populated",
        "Critical" if name_populated > 0 else "Information",
        int(name_populated),
        False,
        "Failed" if name_populated > 0 else "Not Observed",
        f"staff_name populated count: {name_populated}",
    )

    return pd.DataFrame(observations)


# ---------------------------------------------------------------------------
# Export Profile Results
# ---------------------------------------------------------------------------


def export_profile_results(
    data: Dict[str, pd.DataFrame],
    output_dir: Path = DEMO_DIR,
) -> Dict[str, Path]:
    """Run all profiling functions and write summary CSVs."""
    print("[profile_demo_data] Profiling datasets...")
    profile_df = profile_all_datasets(data)
    profile_path = output_dir / "dataset_profile_summary.csv"
    profile_df.to_csv(profile_path, index=False)
    print(f"[profile_demo_data] Profile summary: {profile_path}")

    print("[profile_demo_data] Checking relationships...")
    rel_df = build_relationship_summary(data)
    rel_path = output_dir / "relationship_check_summary.csv"
    rel_df.to_csv(rel_path, index=False)
    print(f"[profile_demo_data] Relationship summary: {rel_path}")

    print("[profile_demo_data] Inspecting storyline...")
    story_df = inspect_storyline_sources(data)
    story_path = output_dir / "storyline_inspection_summary.csv"
    story_df.to_csv(story_path, index=False)
    print(f"[profile_demo_data] Storyline summary: {story_path}")

    print("[profile_demo_data] Building quality observations...")
    qual_df = build_data_quality_observation_summary(data)
    qual_path = output_dir / "data_quality_observation_summary.csv"
    qual_df.to_csv(qual_path, index=False)
    print(f"[profile_demo_data] Quality observations: {qual_path}")

    return {
        "dataset_profile_summary": profile_path,
        "relationship_check_summary": rel_path,
        "storyline_inspection_summary": story_path,
        "data_quality_observation_summary": qual_path,
    }


def main(output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Full profiling pipeline."""
    out = output_dir or DEMO_DIR
    print("[profile_demo_data] Loading demo datasets...")
    data = load_demo_datasets(out)
    paths = export_profile_results(data, out)
    print("[profile_demo_data] Profiling complete.")
    return {
        "status": "success",
        "output_directory": str(out.resolve()),
        "summary_files": {k: str(v.resolve()) for k, v in paths.items()},
    }


if __name__ == "__main__":
    main()
