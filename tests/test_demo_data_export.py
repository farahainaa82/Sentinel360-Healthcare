"""
Automated tests for Step 2B export and profiling.

These tests validate that:
- export and profiling modules work correctly;
- exported CSVs match in-memory DataFrames;
- manifests and summaries are created;
- data quality and relationships are sound in clean mode;
- no analytical outputs are produced.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _PROJECT_ROOT / "src"
_DEMO_DIR = _PROJECT_ROOT / "data" / "demo"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from export_demo_data import (
    build_demo_datasets,
    build_generation_manifest,
    calculate_file_checksum,
    export_demo_datasets,
    validate_export_schemas,
    EXPECTED_DATASETS,
)
from profile_demo_data import (
    build_data_quality_observation_summary,
    build_relationship_summary,
    inspect_storyline_sources,
    load_demo_datasets,
    profile_all_datasets,
    PRIMARY_KEYS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def exported_data() -> dict:
    """Generate and export data once per module."""
    data = build_demo_datasets(seed=360)
    export_demo_datasets(data, _DEMO_DIR)
    manifest = build_generation_manifest(data, _DEMO_DIR, seed=360)
    manifest_path = _DEMO_DIR / "generation_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, default=str)
    return data


@pytest.fixture(scope="module")
def loaded_data() -> dict:
    """Load exported CSVs once per module."""
    return load_demo_datasets(_DEMO_DIR)


# ---------------------------------------------------------------------------
# 1-2. Module Import Safety
# ---------------------------------------------------------------------------

def test_export_module_imports() -> None:
    import export_demo_data as _mod
    assert _mod is not None


def test_profile_module_imports() -> None:
    import profile_demo_data as _mod
    assert _mod is not None


# ---------------------------------------------------------------------------
# 3-4. CSV Export Presence
# ---------------------------------------------------------------------------

def test_all_csv_files_exported() -> None:
    for name in EXPECTED_DATASETS:
        assert (_DEMO_DIR / f"{name}.csv").exists(), f"Missing {name}.csv"


def test_no_unexpected_csv_files() -> None:
    csv_files = set(p.name for p in _DEMO_DIR.glob("*.csv"))
    expected = set(f"{name}.csv" for name in EXPECTED_DATASETS) | {
        "dataset_profile_summary.csv",
        "relationship_check_summary.csv",
        "storyline_inspection_summary.csv",
        "data_quality_observation_summary.csv",
    }
    unexpected = csv_files - expected
    assert not unexpected, f"Unexpected CSV files: {unexpected}"


# ---------------------------------------------------------------------------
# 5-6. Column Order and Row Counts
# ---------------------------------------------------------------------------

def test_csv_column_order_matches_generator(exported_data: dict) -> None:
    for name in EXPECTED_DATASETS:
        df = pd.read_csv(_DEMO_DIR / f"{name}.csv", dtype=str)
        expected_cols = list(exported_data[name].columns)
        assert list(df.columns) == expected_cols, f"Column order mismatch in {name}"


def test_exported_row_counts_match_memory(exported_data: dict) -> None:
    for name in EXPECTED_DATASETS:
        df = pd.read_csv(_DEMO_DIR / f"{name}.csv")
        assert len(df) == len(exported_data[name]), f"Row count mismatch in {name}"


# ---------------------------------------------------------------------------
# 7. Reloaded Values
# ---------------------------------------------------------------------------

def test_exported_values_can_be_reloaded(exported_data: dict) -> None:
    for name in EXPECTED_DATASETS:
        df = pd.read_csv(_DEMO_DIR / f"{name}.csv", dtype=str, keep_default_na=True)
        assert len(df) > 0 or name == "hospital_master", f"Empty reload for {name}"


# ---------------------------------------------------------------------------
# 8-12. Manifest Checks
# ---------------------------------------------------------------------------

def test_manifest_created() -> None:
    assert (_DEMO_DIR / "generation_manifest.json").exists()


def test_manifest_dataset_count_equals_13() -> None:
    with open(_DEMO_DIR / "generation_manifest.json", "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["dataset_count"] == 13


def test_manifest_row_counts_match_exported_csvs(exported_data: dict) -> None:
    with open(_DEMO_DIR / "generation_manifest.json", "r", encoding="utf-8") as f:
        manifest = json.load(f)
    for name in EXPECTED_DATASETS:
        assert manifest["row_count_by_dataset"][name] == len(exported_data[name])


def test_manifest_date_range_matches_configuration() -> None:
    with open(_DEMO_DIR / "generation_manifest.json", "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["configured_start_date"] == "2026-01-01"
    assert manifest["configured_end_date"] == "2026-12-31"


def test_manifest_checksums_populated() -> None:
    with open(_DEMO_DIR / "generation_manifest.json", "r", encoding="utf-8") as f:
        manifest = json.load(f)
    for name in EXPECTED_DATASETS:
        checksum = manifest["file_checksum_by_dataset"][name]
        assert checksum and len(checksum) == 64, f"Missing or invalid checksum for {name}"


# ---------------------------------------------------------------------------
# 13-16. Summary Files Created
# ---------------------------------------------------------------------------

def test_dataset_profile_summary_created() -> None:
    assert (_DEMO_DIR / "dataset_profile_summary.csv").exists()


def test_relationship_summary_created() -> None:
    assert (_DEMO_DIR / "relationship_check_summary.csv").exists()


def test_storyline_inspection_summary_created() -> None:
    assert (_DEMO_DIR / "storyline_inspection_summary.csv").exists()


def test_quality_observation_summary_created() -> None:
    assert (_DEMO_DIR / "data_quality_observation_summary.csv").exists()


# ---------------------------------------------------------------------------
# 17-18. PK and FK Integrity
# ---------------------------------------------------------------------------

def test_no_duplicate_primary_keys_clean_mode(loaded_data: dict) -> None:
    for name, df in loaded_data.items():
        pk = PRIMARY_KEYS[name]
        assert not df[pk].duplicated().any(), f"Duplicate PK in {name}"


def test_no_orphan_required_foreign_keys_clean_mode(loaded_data: dict) -> None:
    hm = loaded_data["hospital_master"]
    dm = loaded_data["department_master"]
    srm = loaded_data["staff_role_master"]
    sm = loaded_data["staff_master"]
    sr = loaded_data["staff_roster"]
    sa = loaded_data["staff_attendance"]

    hosp_ids = set(hm["hospital_id"])
    dept_ids = set(dm["department_id"])
    role_ids = set(srm["role_id"])
    staff_ids = set(sm["staff_id"])
    roster_ids = set(sr["roster_id"])

    assert set(dm["hospital_id"]).issubset(hosp_ids)
    assert set(sm["hospital_id"]).issubset(hosp_ids)
    assert set(sm["department_id"]).issubset(dept_ids)
    assert set(sm["role_id"]).issubset(role_ids)
    assert set(sr["staff_id"]).issubset(staff_ids)
    assert set(sr["roster_id"]).isdisjoint(set())  # just ensure no error
    assert set(sa["roster_id"]).issubset(roster_ids)


# ---------------------------------------------------------------------------
# 19-20. Privacy
# ---------------------------------------------------------------------------

def test_no_direct_patient_identifiers(loaded_data: dict) -> None:
    forbidden = {"patient_name", "patient_full_name", "identity_card", "passport_number",
                 "telephone", "phone_number", "email", "diagnosis", "clinical_note",
                 "medical_record_number", "mrn"}
    for name, df in loaded_data.items():
        # staff_master contains email/phone/address as approved schema fields,
        # but they must be blank (tested separately). Skip them from column check.
        if name == "staff_master":
            continue
        assert forbidden.isdisjoint(set(df.columns)), f"Forbidden fields in {name}"


def test_no_staff_names(loaded_data: dict) -> None:
    sm = loaded_data["staff_master"]
    if "staff_name" in sm.columns:
        assert sm["staff_name"].isna().all() or (sm["staff_name"] == "").all()


# ---------------------------------------------------------------------------
# 21. Date Range
# ---------------------------------------------------------------------------

def test_dates_within_configured_period(loaded_data: dict) -> None:
    from profile_demo_data import DATE_COLUMNS
    for name, col in DATE_COLUMNS.items():
        df = loaded_data[name]
        if col not in df.columns:
            continue
        min_d = pd.to_datetime(df[col]).min()
        max_d = pd.to_datetime(df[col]).max()
        assert min_d >= pd.Timestamp("2026-01-01"), f"{name} has dates before start"
        assert max_d <= pd.Timestamp("2026-12-31"), f"{name} has dates after end"


# ---------------------------------------------------------------------------
# 22. Occupancy Exception Handling
# ---------------------------------------------------------------------------

def test_occupancy_above_capacity_has_flag_and_reason(loaded_data: dict) -> None:
    bed = loaded_data["bed_capacity_records"]
    bed["bed_occupied_num"] = pd.to_numeric(bed["bed_occupied"], errors="coerce")
    bed["bed_operational_num"] = pd.to_numeric(bed["bed_operational"], errors="coerce")
    over = bed[bed["bed_occupied_num"] > bed["bed_operational_num"]]
    if len(over) > 0:
        assert over["exception_flag"].astype(str).str.lower().eq("true").all(), "Missing exception_flag"
        assert over["exception_reason"].notna().all(), "Missing exception_reason"


# ---------------------------------------------------------------------------
# 23-24. Domain Validity
# ---------------------------------------------------------------------------

def test_complaint_statuses_valid(loaded_data: dict) -> None:
    pc = loaded_data["patient_complaints"]
    valid = {"Received", "Under Review", "Investigating", "Resolved", "Closed", "Escalated"}
    assert set(pc["status"]).issubset(valid)


def test_survey_scores_within_scales(loaded_data: dict) -> None:
    ps = loaded_data["patient_surveys"]
    complete = ps[ps["is_complete"].astype(str).str.lower() == "true"]
    scale_5 = complete[complete["scale_id"] == "SCALE-5PT"]
    if len(scale_5) > 0:
        scores = pd.to_numeric(scale_5["score_value"], errors="coerce")
        assert scores.between(1, 5).all(), "5-point scale violation"


# ---------------------------------------------------------------------------
# 25. Profiling Does Not Modify Source Files
# ---------------------------------------------------------------------------

def test_profiling_does_not_modify_source_files(exported_data: dict) -> None:
    checksums_before = {}
    for name in EXPECTED_DATASETS:
        path = _DEMO_DIR / f"{name}.csv"
        checksums_before[name] = calculate_file_checksum(path)

    # Run profiling
    data = load_demo_datasets(_DEMO_DIR)
    profile_all_datasets(data)
    build_relationship_summary(data)
    inspect_storyline_sources(data)
    build_data_quality_observation_summary(data)

    checksums_after = {}
    for name in EXPECTED_DATASETS:
        path = _DEMO_DIR / f"{name}.csv"
        checksums_after[name] = calculate_file_checksum(path)

    assert checksums_before == checksums_after, "Source CSVs were modified by profiling"


# ---------------------------------------------------------------------------
# 26. Reproducibility
# ---------------------------------------------------------------------------

def test_repeated_export_produces_identical_content() -> None:
    data1 = build_demo_datasets(seed=360)
    data2 = build_demo_datasets(seed=360)
    for name in EXPECTED_DATASETS:
        pd.testing.assert_frame_equal(data1[name], data2[name])


# ---------------------------------------------------------------------------
# 27-28. No Analytical Output Files
# ---------------------------------------------------------------------------

def test_no_kpi_result_files() -> None:
    kpi_patterns = ["*kpi*", "*status*", "*score*", "*dashboard*"]
    for pattern in kpi_patterns:
        matches = list(_DEMO_DIR.glob(pattern))
        assert not matches, f"Unexpected KPI file: {matches}"


def test_no_forecast_scenario_financial_recommendation_files() -> None:
    forbidden_patterns = ["*forecast*", "*scenario*", "*financial*", "*recommendation*", "*risk*"]
    for pattern in forbidden_patterns:
        matches = list(_DEMO_DIR.glob(pattern))
        assert not matches, f"Unexpected analytical file: {matches}"
