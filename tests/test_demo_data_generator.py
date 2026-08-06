"""
Automated tests for SyntheticHospitalDataGenerator.

These tests validate generator mechanics, reproducibility, schema compliance,
cross-dataset consistency, and defect-injection behaviour.

They do NOT test KPI outputs, threshold logic, or analytical engines.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Ensure src/ is on the path when running from project root or tests/
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _PROJECT_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from demo_data_generator import SyntheticHospitalDataGenerator
from demo_generation_config import GeneratorConfig, get_default_config


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def default_data() -> dict:
    """Generate default dataset collection once per module."""
    gen = SyntheticHospitalDataGenerator(seed=360)
    return gen.generate_all()


@pytest.fixture(scope="module")
def alt_seed_data() -> dict:
    """Generate dataset with a different seed."""
    gen = SyntheticHospitalDataGenerator(seed=999)
    return gen.generate_all()


@pytest.fixture
def defect_config() -> GeneratorConfig:
    """Return a config with all defect switches enabled."""
    cfg = get_default_config()
    for key in cfg.defects:
        cfg.defects[key] = True
    return cfg


# ---------------------------------------------------------------------------
# 1. Generator Initialisation
# ---------------------------------------------------------------------------

def test_generator_initialisation() -> None:
    gen = SyntheticHospitalDataGenerator()
    assert gen.seed == 360
    assert gen.config is not None
    gen2 = SyntheticHospitalDataGenerator(seed=123)
    assert gen2.seed == 123


# ---------------------------------------------------------------------------
# 2. Deterministic Output from Same Seed
# ---------------------------------------------------------------------------

def test_deterministic_output_same_seed() -> None:
    gen1 = SyntheticHospitalDataGenerator(seed=360)
    data1 = gen1.generate_all()
    gen2 = SyntheticHospitalDataGenerator(seed=360)
    data2 = gen2.generate_all()
    for name in data1:
        pd.testing.assert_frame_equal(data1[name], data2[name])


# ---------------------------------------------------------------------------
# 3. Different Output from Different Seed
# ---------------------------------------------------------------------------

def test_different_output_different_seed(default_data: dict, alt_seed_data: dict) -> None:
    # At least one dataset should differ in row count or values
    diffs = 0
    for name in default_data:
        if not default_data[name].equals(alt_seed_data[name]):
            diffs += 1
    assert diffs > 0, "Expected at least one dataset to differ between seeds"


# ---------------------------------------------------------------------------
# 4. All 13 Datasets Returned
# ---------------------------------------------------------------------------

def test_all_datasets_returned(default_data: dict) -> None:
    expected = {
        "hospital_master", "department_master", "staff_role_master", "staff_master",
        "staff_roster", "staff_attendance", "staffing_requirement", "patient_encounters",
        "patient_queue_records", "bed_capacity_records", "patient_complaints",
        "patient_surveys", "service_schedule",
    }
    assert set(default_data.keys()) == expected
    for name in expected:
        assert isinstance(default_data[name], pd.DataFrame)


# ---------------------------------------------------------------------------
# 5. Required Columns Exist
# ---------------------------------------------------------------------------

def test_required_columns_exist(default_data: dict) -> None:
    expected_cols = {
        "hospital_master": ["hospital_id", "hospital_name", "status"],
        "department_master": ["department_id", "hospital_id", "department_name", "is_active"],
        "staff_role_master": ["role_id", "role_name", "staff_category", "is_clinical"],
        "staff_master": ["staff_id", "hospital_id", "department_id", "role_id", "employment_type", "fte_value"],
        "staff_roster": ["roster_id", "staff_id", "roster_date", "shift_code", "planned_hours"],
        "staff_attendance": ["attendance_id", "staff_id", "roster_id", "status", "actual_hours"],
        "staffing_requirement": ["requirement_id", "department_id", "role_id", "required_staff_count", "required_hours"],
        "patient_encounters": ["encounter_id", "department_id", "arrival_datetime", "status"],
        "patient_queue_records": ["queue_id", "department_id", "queue_date", "arrivals_count", "avg_wait_minutes"],
        "bed_capacity_records": ["record_id", "department_id", "record_date", "bed_licensed", "bed_occupied", "occupancy_rate"],
        "patient_complaints": ["complaint_id", "department_id", "complaint_received_date", "status"],
        "patient_surveys": ["survey_id", "department_id", "survey_date", "score_value", "scale_id"],
        "service_schedule": ["schedule_id", "department_id", "service_date", "planned_hours", "schedule_status"],
    }
    for ds, cols in expected_cols.items():
        for col in cols:
            assert col in default_data[ds].columns, f"Missing column {col} in {ds}"


# ---------------------------------------------------------------------------
# 6. Primary Keys Are Unique
# ---------------------------------------------------------------------------

def test_primary_keys_unique(default_data: dict) -> None:
    pk_map = {
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
    for ds, pk in pk_map.items():
        assert not default_data[ds][pk].duplicated().any(), f"Duplicate PK in {ds}"


# ---------------------------------------------------------------------------
# 7. Foreign Keys Are Valid
# ---------------------------------------------------------------------------

def test_foreign_keys_valid(default_data: dict) -> None:
    hosp_ids = set(default_data["hospital_master"]["hospital_id"])
    dept_ids = set(default_data["department_master"]["department_id"])
    role_ids = set(default_data["staff_role_master"]["role_id"])
    staff_ids = set(default_data["staff_master"]["staff_id"])
    roster_ids = set(default_data["staff_roster"]["roster_id"])

    # hospital_id references
    for ds in ["department_master", "staff_master"]:
        assert set(default_data[ds]["hospital_id"]).issubset(hosp_ids)

    # department_id references
    for ds in ["staff_master", "staff_roster", "staff_attendance", "staffing_requirement",
               "service_schedule", "patient_encounters", "patient_queue_records",
               "bed_capacity_records", "patient_complaints", "patient_surveys"]:
        assert set(default_data[ds]["department_id"]).issubset(dept_ids), f"Invalid dept ref in {ds}"

    # role_id references
    for ds in ["staff_master", "staff_roster", "staff_attendance", "staffing_requirement"]:
        assert set(default_data[ds]["role_id"]).issubset(role_ids), f"Invalid role ref in {ds}"

    # staff_id references
    for ds in ["staff_roster", "staff_attendance"]:
        assert set(default_data[ds]["staff_id"]).issubset(staff_ids), f"Invalid staff ref in {ds}"

    # roster_id references in attendance
    assert set(default_data["staff_attendance"]["roster_id"]).issubset(roster_ids)


# ---------------------------------------------------------------------------
# 8. Date Range Is Respected
# ---------------------------------------------------------------------------

def test_date_range_respected(default_data: dict) -> None:
    cfg = get_default_config()
    date_cols = {
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
    for ds, col in date_cols.items():
        df = default_data[ds]
        assert df[col].min() >= cfg.start_date, f"{ds} has dates before start"
        assert df[col].max() <= cfg.end_date, f"{ds} has dates after end"


# ---------------------------------------------------------------------------
# 9. No Direct Patient Identifiers Exist
# ---------------------------------------------------------------------------

def test_no_patient_identifiers(default_data: dict) -> None:
    enc = default_data["patient_encounters"]
    # patient_id should be synthetic token, not a real name or IC
    assert enc["patient_id"].notna().all()
    for val in enc["patient_id"].head(20):
        assert str(val).startswith("PAT-")
    # No name, phone, email, IC, address columns in encounters
    forbidden = {"patient_name", "phone", "email", "ic_number", "address", "mrn"}
    assert forbidden.isdisjoint(set(enc.columns))


# ---------------------------------------------------------------------------
# 10. No Staff Names Exist
# ---------------------------------------------------------------------------

def test_no_staff_names(default_data: dict) -> None:
    staff = default_data["staff_master"]
    pii_cols = ["staff_name", "email", "phone_number", "ic_number", "address"]
    for col in pii_cols:
        if col in staff.columns:
            assert staff[col].isna().all(), f"PII column {col} should be null"


# ---------------------------------------------------------------------------
# 11. Non-Negative Numeric Fields
# ---------------------------------------------------------------------------

def test_non_negative_numeric_fields(default_data: dict) -> None:
    checks = {
        "staffing_requirement": ["required_staff_count", "required_hours"],
        "patient_queue_records": ["arrivals_count", "served_count", "waiting_count"],
        "bed_capacity_records": ["bed_licensed", "bed_staffed", "bed_operational", "bed_occupied", "bed_unavailable", "bed_reserved"],
        "service_schedule": ["planned_capacity", "planned_hours"],
        "staff_roster": ["planned_hours"],
    }
    for ds, cols in checks.items():
        for col in cols:
            assert (default_data[ds][col] >= 0).all(), f"Negative values in {ds}.{col}"


# ---------------------------------------------------------------------------
# 12. Timestamp Ordering
# ---------------------------------------------------------------------------

def test_timestamp_ordering(default_data: dict) -> None:
    enc = default_data["patient_encounters"]
    completed = enc[enc["status"] == "Completed"]
    assert (completed["service_start_datetime"] >= completed["arrival_datetime"]).all()
    assert (completed["service_end_datetime"] >= completed["service_start_datetime"]).all()


# ---------------------------------------------------------------------------
# 13. Attendance-Roster Reconciliation
# ---------------------------------------------------------------------------

def test_attendance_roster_reconciliation(default_data: dict) -> None:
    roster = default_data["staff_roster"]
    attendance = default_data["staff_attendance"]
    # Every attendance roster_id should exist in roster
    assert set(attendance["roster_id"]).issubset(set(roster["roster_id"]))
    # Counts should match (1:1 in normal generation)
    assert len(attendance) == len(roster)


# ---------------------------------------------------------------------------
# 14. Bed Records Restricted to Valid Departments
# ---------------------------------------------------------------------------

def test_bed_records_valid_departments(default_data: dict) -> None:
    bed = default_data["bed_capacity_records"]
    dept = default_data["department_master"]
    bed_dept_ids = set(dept[dept["bed_licensed"] > 0]["department_id"])
    assert set(bed["department_id"]).issubset(bed_dept_ids)


# ---------------------------------------------------------------------------
# 15. Survey Scores Within Declared Scales
# ---------------------------------------------------------------------------

def test_survey_scores_within_scales(default_data: dict) -> None:
    surv = default_data["patient_surveys"]
    complete = surv[surv["is_complete"] == True]
    for scale_id in complete["scale_id"].unique():
        subset = complete[complete["scale_id"] == scale_id]
        if scale_id == "SCALE-5PT":
            assert subset["score_value"].between(1, 5).all()
        elif scale_id == "SCALE-10PT":
            assert subset["score_value"].between(1, 10).all()


# ---------------------------------------------------------------------------
# 16. Complaint Statuses Valid
# ---------------------------------------------------------------------------

def test_complaint_statuses_valid(default_data: dict) -> None:
    comp = default_data["patient_complaints"]
    valid = {"Received", "Under Review", "Investigating", "Resolved", "Closed", "Escalated"}
    assert set(comp["status"]).issubset(valid)


# ---------------------------------------------------------------------------
# 17. Clean Mode Produces No Intentional Defects
# ---------------------------------------------------------------------------

def test_clean_mode_no_defects(default_data: dict) -> None:
    # In clean mode, occupied > operational must have exception_flag=True and reason
    bed = default_data["bed_capacity_records"]
    over = bed[bed["bed_occupied"] > bed["bed_operational"]]
    if len(over) > 0:
        assert over["exception_flag"].all(), "Over-capacity records missing exception_flag"
        assert over["exception_reason"].notna().all(), "Over-capacity records missing exception_reason"
    # No duplicate primary keys
    for ds in ["hospital_master", "department_master", "staff_role_master", "staff_master",
               "staff_roster", "staff_attendance", "staffing_requirement", "patient_encounters",
               "patient_queue_records", "bed_capacity_records", "patient_complaints",
               "patient_surveys", "service_schedule"]:
        pk_col = {
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
        }[ds]
        assert not default_data[ds][pk_col].duplicated().any(), f"Unexpected duplicate PK in clean {ds}"


# ---------------------------------------------------------------------------
# 18. Defect Mode Produces Requested Reproducible Defect
# ---------------------------------------------------------------------------

def test_defect_mode_injects_defects(defect_config: GeneratorConfig) -> None:
    gen = SyntheticHospitalDataGenerator(config=defect_config, seed=360)
    data = gen.generate_all()
    # Check specific defects were injected
    if defect_config.defects.get("unknown_hospital_reference"):
        assert "HOSP-UNKNOWN" in data["department_master"]["hospital_id"].values
    if defect_config.defects.get("missing_required_values"):
        assert data["staff_master"]["employment_type"].isna().any()
    if defect_config.defects.get("invalid_complaint_status"):
        assert "Unknown Status" in data["patient_complaints"]["status"].values
    if defect_config.defects.get("invalid_survey_scale"):
        assert (data["patient_surveys"]["score_value"] > 10).any() or (data["patient_surveys"]["score_value"] > 5).any()


# ---------------------------------------------------------------------------
# 19. Occupancy Source Conditions May Exceed Operational Capacity
# ---------------------------------------------------------------------------

def test_occupancy_may_exceed_operational(default_data: dict) -> None:
    bed = default_data["bed_capacity_records"]
    # The generator should naturally produce some over-capacity conditions
    # during pressure periods. Verify the schema allows it.
    over = bed[bed["bed_occupied"] > bed["bed_operational"]]
    # With the default storyline, we expect at least some over-capacity days
    assert len(over) > 0, "Expected at least some over-capacity records in default storyline"
    # Occupancy rate should reflect >100 when over capacity
    assert (over["occupancy_rate"] > 100).any()


# ---------------------------------------------------------------------------
# 20. generate_all() Does Not Write Files Automatically
# ---------------------------------------------------------------------------

def test_generate_all_does_not_write_files(tmp_path: Path) -> None:
    cfg = get_default_config()
    cfg.output_dir = tmp_path
    gen = SyntheticHospitalDataGenerator(config=cfg, seed=360)
    _ = gen.generate_all()
    # No CSV files should exist in the output directory
    csv_files = list(tmp_path.glob("*.csv"))
    assert len(csv_files) == 0, f"Unexpected CSV files written: {csv_files}"
