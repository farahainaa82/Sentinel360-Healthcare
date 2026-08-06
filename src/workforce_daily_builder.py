"""
Sentinel360 Healthcare — Workforce Daily Builder

Builds processed_workforce_daily.csv from processed roster, attendance,
and staffing requirement datasets.

Grain: one row per hospital_id + department_id + staff_role_id + reporting_date.

Step: 2D-2
"""

import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from src.processing_models import ProcessingRun, ProcessingDatasetResult

TRANSFORMATION_VERSION = "2D-2.1.0"


def _now() -> datetime:
    return datetime.now()


def _build_daily_id(row: pd.Series) -> str:
    """Deterministic workforce_daily_id from grain columns."""
    key = f"{row['hospital_id']}:{row['department_id']}:{row['staff_role_id']}:{row['reporting_date']}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def build_workforce_daily(
    roster_df: pd.DataFrame,
    attendance_df: pd.DataFrame,
    requirement_df: pd.DataFrame,
    run: ProcessingRun,
    validation_run_id: str,
) -> pd.DataFrame:
    """Aggregate workforce data to daily grain.

    Returns a DataFrame conforming to processed_workforce_daily schema.
    """
    # Build grain from all contributing datasets
    grains: List[pd.DataFrame] = []
    if not roster_df.empty and {"hospital_id", "department_id", "staff_role_id", "reporting_date"}.issubset(roster_df.columns):
        grains.append(roster_df[["hospital_id", "department_id", "staff_role_id", "reporting_date"]].copy())
    if not attendance_df.empty and {"hospital_id", "actual_department_id", "staff_role_id", "reporting_date"}.issubset(attendance_df.columns):
        att_grain = attendance_df[["hospital_id", "actual_department_id", "staff_role_id", "reporting_date"]].copy()
        att_grain = att_grain.rename(columns={"actual_department_id": "department_id"})
        grains.append(att_grain)
    if not requirement_df.empty and {"hospital_id", "department_id", "staff_role_id", "reporting_date"}.issubset(requirement_df.columns):
        grains.append(requirement_df[["hospital_id", "department_id", "staff_role_id", "reporting_date"]].copy())

    if not grains:
        return pd.DataFrame()

    grain = pd.concat(grains, ignore_index=True)
    grain = grain.drop_duplicates()
    grain["reporting_date"] = pd.to_datetime(grain["reporting_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    grain = grain.dropna(subset=["hospital_id", "department_id", "staff_role_id", "reporting_date"])

    # Roster aggregations
    if not roster_df.empty:
        roster_df = roster_df.copy()
        roster_df["reporting_date"] = pd.to_datetime(roster_df["reporting_date"], errors="coerce").dt.strftime("%Y-%m-%d")
        valid_roster = roster_df[roster_df["valid_assignment_flag"] == True]
        roster_agg = valid_roster.groupby(["hospital_id", "department_id", "staff_role_id", "reporting_date"]).agg(
            rostered_staff_count=("staff_id", "nunique"),
            rostered_hours=("planned_hours", "sum"),
        ).reset_index()
        grain = grain.merge(roster_agg, on=["hospital_id", "department_id", "staff_role_id", "reporting_date"], how="left")
    else:
        grain["rostered_staff_count"] = 0
        grain["rostered_hours"] = 0.0

    # Staffing requirement aggregations
    if not requirement_df.empty:
        req_df = requirement_df.copy()
        req_df["reporting_date"] = pd.to_datetime(req_df["reporting_date"], errors="coerce").dt.strftime("%Y-%m-%d")
        valid_req = req_df[req_df["valid_requirement_flag"] == True]
        req_agg = valid_req.groupby(["hospital_id", "department_id", "staff_role_id", "reporting_date"]).agg(
            required_staff_count=("required_staff_count", "sum"),
            required_staff_hours=("required_staff_hours", "sum"),
        ).reset_index()
        grain = grain.merge(req_agg, on=["hospital_id", "department_id", "staff_role_id", "reporting_date"], how="left")
    else:
        grain["required_staff_count"] = 0
        grain["required_staff_hours"] = None

    # Attendance aggregations
    if not attendance_df.empty:
        att_df = attendance_df.copy()
        att_df["reporting_date"] = pd.to_datetime(att_df["reporting_date"], errors="coerce").dt.strftime("%Y-%m-%d")
        att_df = att_df.rename(columns={"actual_department_id": "department_id"})
        # Verified available
        avail = att_df[att_df["availability_contribution"].notna() & (att_df["availability_contribution"] > 0)]
        avail_agg = avail.groupby(["hospital_id", "department_id", "staff_role_id", "reporting_date"]).agg(
            verified_available_staff_count=("staff_id", "nunique"),
            verified_available_hours=("availability_contribution", "sum"),
        ).reset_index()
        grain = grain.merge(avail_agg, on=["hospital_id", "department_id", "staff_role_id", "reporting_date"], how="left")
        # Absent events
        absent = att_df[att_df["absenteeism_eligible_flag"] == True]
        absent_agg = absent.groupby(["hospital_id", "department_id", "staff_role_id", "reporting_date"]).agg(
            absent_event_count=("attendance_record_id", "count"),
            absent_hours=("absenteeism_hours", "sum"),
        ).reset_index()
        grain = grain.merge(absent_agg, on=["hospital_id", "department_id", "staff_role_id", "reporting_date"], how="left")
        # Planned leave
        planned = att_df[att_df["planned_absence_flag"] == True]
        planned_agg = planned.groupby(["hospital_id", "department_id", "staff_role_id", "reporting_date"]).agg(
            planned_leave_event_count=("attendance_record_id", "count"),
            planned_leave_hours=("lost_scheduled_hours", "sum"),
        ).reset_index()
        grain = grain.merge(planned_agg, on=["hospital_id", "department_id", "staff_role_id", "reporting_date"], how="left")
        # Partial attendance
        partial = att_df[att_df["attendance_status"].str.lower() == "partial"]
        partial_agg = partial.groupby(["hospital_id", "department_id", "staff_role_id", "reporting_date"]).agg(
            partial_attendance_event_count=("attendance_record_id", "count"),
        ).reset_index()
        grain = grain.merge(partial_agg, on=["hospital_id", "department_id", "staff_role_id", "reporting_date"], how="left")
        # Late attendance
        late = att_df[att_df["attendance_status"].str.lower() == "late"]
        late_agg = late.groupby(["hospital_id", "department_id", "staff_role_id", "reporting_date"]).agg(
            late_attendance_event_count=("attendance_record_id", "count"),
        ).reset_index()
        grain = grain.merge(late_agg, on=["hospital_id", "department_id", "staff_role_id", "reporting_date"], how="left")
        # Reassignments
        reassigned_in = att_df[att_df["reassigned_flag"] == True]
        reassigned_out = att_df[(att_df["reassigned_flag"] == True) & (att_df["home_department_id"] != att_df["department_id"])]
        # Simplification: count reassigned_in as records with reassigned_flag=True
        reass_in_agg = reassigned_in.groupby(["hospital_id", "department_id", "staff_role_id", "reporting_date"]).agg(
            reassigned_in_count=("attendance_record_id", "count"),
        ).reset_index()
        grain = grain.merge(reass_in_agg, on=["hospital_id", "department_id", "staff_role_id", "reporting_date"], how="left")
        reass_out_agg = reassigned_out.groupby(["hospital_id", "department_id", "staff_role_id", "reporting_date"]).agg(
            reassigned_out_count=("attendance_record_id", "count"),
        ).reset_index()
        grain = grain.merge(reass_out_agg, on=["hospital_id", "department_id", "staff_role_id", "reporting_date"], how="left")
        # Replacement staff
        repl = att_df[att_df["replacement_staff_id"] != ""]
        repl_agg = repl.groupby(["hospital_id", "department_id", "staff_role_id", "reporting_date"]).agg(
            replacement_staff_count=("replacement_staff_id", "nunique"),
        ).reset_index()
        grain = grain.merge(repl_agg, on=["hospital_id", "department_id", "staff_role_id", "reporting_date"], how="left")
        # Missing attendance
        missing = att_df[att_df["missing_attendance_flag"] == True]
        missing_agg = missing.groupby(["hospital_id", "department_id", "staff_role_id", "reporting_date"]).agg(
            missing_attendance_count=("attendance_record_id", "count"),
        ).reset_index()
        grain = grain.merge(missing_agg, on=["hospital_id", "department_id", "staff_role_id", "reporting_date"], how="left")
        # Unknown attendance
        unknown = att_df[att_df["unknown_attendance_flag"] == True]
        unknown_agg = unknown.groupby(["hospital_id", "department_id", "staff_role_id", "reporting_date"]).agg(
            unknown_attendance_count=("attendance_record_id", "count"),
        ).reset_index()
        grain = grain.merge(unknown_agg, on=["hospital_id", "department_id", "staff_role_id", "reporting_date"], how="left")
        # Eligible and excluded counts
        eligible = att_df[att_df["valid_attendance_flag"] == True]
        eligible_agg = eligible.groupby(["hospital_id", "department_id", "staff_role_id", "reporting_date"]).agg(
            eligible_record_count=("attendance_record_id", "count"),
        ).reset_index()
        grain = grain.merge(eligible_agg, on=["hospital_id", "department_id", "staff_role_id", "reporting_date"], how="left")
        excluded = att_df[att_df["valid_attendance_flag"] == False]
        excluded_agg = excluded.groupby(["hospital_id", "department_id", "staff_role_id", "reporting_date"]).agg(
            excluded_record_count=("attendance_record_id", "count"),
        ).reset_index()
        grain = grain.merge(excluded_agg, on=["hospital_id", "department_id", "staff_role_id", "reporting_date"], how="left")
    else:
        grain["verified_available_staff_count"] = 0
        grain["verified_available_hours"] = 0.0
        grain["absent_event_count"] = 0
        grain["absent_hours"] = 0.0
        grain["planned_leave_event_count"] = 0
        grain["planned_leave_hours"] = 0.0
        grain["partial_attendance_event_count"] = 0
        grain["late_attendance_event_count"] = 0
        grain["reassigned_in_count"] = 0
        grain["reassigned_out_count"] = 0
        grain["replacement_staff_count"] = 0
        grain["missing_attendance_count"] = 0
        grain["unknown_attendance_count"] = 0
        grain["eligible_record_count"] = 0
        grain["excluded_record_count"] = 0

    # Fill nulls for counts
    count_cols = [
        "rostered_staff_count", "rostered_hours",
        "required_staff_count", "required_staff_hours",
        "verified_available_staff_count", "verified_available_hours",
        "absent_event_count", "absent_hours",
        "planned_leave_event_count", "planned_leave_hours",
        "partial_attendance_event_count", "late_attendance_event_count",
        "reassigned_in_count", "reassigned_out_count",
        "replacement_staff_count",
        "missing_attendance_count", "unknown_attendance_count",
        "eligible_record_count", "excluded_record_count",
    ]
    for col in count_cols:
        if col in grain.columns:
            if col == "required_staff_hours":
                # Keep null rather than zero for unresolved hours
                continue
            grain[col] = grain[col].fillna(0)

    # Data completeness count
    grain["data_completeness_count"] = (
        grain["eligible_record_count"].fillna(0) + grain["excluded_record_count"].fillna(0)
    )

    # Reporting month
    grain["reporting_month"] = pd.to_datetime(grain["reporting_date"], errors="coerce").dt.strftime("%Y-%m")

    # Deterministic ID
    grain["workforce_daily_id"] = grain.apply(_build_daily_id, axis=1)

    # Metadata
    grain["processing_run_id"] = run.processing_run_id
    grain["validation_run_id"] = validation_run_id
    grain["transformation_version"] = TRANSFORMATION_VERSION
    grain["processed_datetime"] = _now().isoformat()

    # Reorder columns to match schema
    schema_order = [
        "workforce_daily_id", "hospital_id", "department_id", "staff_role_id",
        "reporting_date", "reporting_month", "rostered_staff_count", "rostered_hours",
        "required_staff_count", "required_staff_hours", "verified_available_staff_count",
        "verified_available_hours", "absent_event_count", "absent_hours",
        "planned_leave_event_count", "planned_leave_hours", "partial_attendance_event_count",
        "late_attendance_event_count", "reassigned_in_count", "reassigned_out_count",
        "replacement_staff_count", "missing_attendance_count", "unknown_attendance_count",
        "eligible_record_count", "excluded_record_count", "data_completeness_count",
        "processing_run_id", "validation_run_id", "transformation_version", "processed_datetime",
    ]
    present = [c for c in schema_order if c in grain.columns]
    grain = grain[present]
    return grain
