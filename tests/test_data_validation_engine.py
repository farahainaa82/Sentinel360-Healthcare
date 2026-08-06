"""
Sentinel360 Healthcare — Data Validation Engine Tests

Tests for Step 2C: validation engine, registries, and runner.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Ensure src is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import validation_config_loader as vcl
from src.data_validation_engine import DataValidationEngine
from src.run_data_validation import export_validation_outputs, main, parse_args
from src.validation_models import ValidationRun


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def clean_demo_dir():
    """Return path to clean demo data."""
    return Path("data/demo")


@pytest.fixture
def temp_dir():
    """Provide a temporary directory."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture
def engine_for_clean(clean_demo_dir):
    """Build an engine pointed at clean demo data."""
    schema = vcl.load_dataset_schema_registry()
    rels = vcl.load_relationship_registry()
    rules = vcl.load_validation_rule_registry()
    return DataValidationEngine(
        input_directory=clean_demo_dir,
        schema_registry=schema,
        relationship_registry=rels,
        validation_rules=rules,
        source_type="synthetic_demo",
        collect_record_level_issues=True,
        maximum_record_level_examples=50,
    )


# ---------------------------------------------------------------------------
# 1. modules import safely
# ---------------------------------------------------------------------------

def test_modules_import_safely():
    import src.validation_models
    import src.validation_config_loader
    import src.data_validation_engine
    import src.run_data_validation
    assert src.validation_models is not None
    assert src.validation_config_loader is not None
    assert src.data_validation_engine is not None
    assert src.run_data_validation is not None


# ---------------------------------------------------------------------------
# 2. schema registry contains all 13 datasets
# ---------------------------------------------------------------------------

def test_schema_registry_contains_all_datasets():
    registry = vcl.load_dataset_schema_registry()
    assert len(registry) == 13
    for ds in vcl.DATASET_NAMES:
        assert ds in registry


# ---------------------------------------------------------------------------
# 3. relationship registry is valid
# ---------------------------------------------------------------------------

def test_relationship_registry_valid():
    rels = vcl.load_relationship_registry()
    assert len(rels) > 0
    for rel in rels:
        assert "child_dataset" in rel
        assert "parent_dataset" in rel
        assert "mandatory" in rel


# ---------------------------------------------------------------------------
# 4. validation rules have unique test IDs
# ---------------------------------------------------------------------------

def test_validation_rules_unique_test_ids():
    rules = vcl.load_validation_rule_registry()
    ids = [r["test_id"] for r in rules]
    assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# 5. clean demo data validates successfully
# ---------------------------------------------------------------------------

def test_clean_demo_validates(engine_for_clean):
    result = engine_for_clean.run_validation()
    assert result.validation_run.run_status in ("Passed", "Passed with Warnings")


# ---------------------------------------------------------------------------
# 6. clean demo data has no blocking issues
# ---------------------------------------------------------------------------

def test_clean_demo_no_blocking_issues(engine_for_clean):
    result = engine_for_clean.run_validation()
    open_blocking = [i for i in result.issues if i.blocks_processing and i.issue_status == "Open"]
    # Privacy issues on staff_master approved fields should not be blocking
    assert len(open_blocking) == 0


# ---------------------------------------------------------------------------
# 7. all 13 dataset results are returned
# ---------------------------------------------------------------------------

def test_all_dataset_results_returned(engine_for_clean):
    result = engine_for_clean.run_validation()
    assert len(result.dataset_results) == 13
    for ds in vcl.DATASET_NAMES:
        assert ds in result.dataset_results


# ---------------------------------------------------------------------------
# 8. missing mandatory file becomes Blocked
# ---------------------------------------------------------------------------

def test_missing_mandatory_file_blocked(temp_dir):
    # Copy only 12 datasets, omit hospital_master
    for f in Path("data/demo").glob("*.csv"):
        if f.stem != "hospital_master":
            shutil.copy(f, temp_dir / f.name)
    engine = DataValidationEngine(
        input_directory=temp_dir,
        schema_registry=vcl.load_dataset_schema_registry(),
        relationship_registry=vcl.load_relationship_registry(),
        validation_rules=vcl.load_validation_rule_registry(),
        source_type="test",
    )
    result = engine.run_validation()
    assert result.dataset_results["hospital_master"].dataset_status == "Blocked"


# ---------------------------------------------------------------------------
# 9. unreadable or malformed file becomes Blocked
# ---------------------------------------------------------------------------

def test_unreadable_file_blocked(temp_dir):
    # Copy all but corrupt one file
    for f in Path("data/demo").glob("*.csv"):
        shutil.copy(f, temp_dir / f.name)
    # Overwrite with binary garbage
    (temp_dir / "hospital_master.csv").write_bytes(b"\x00\x01\x02\xff")
    engine = DataValidationEngine(
        input_directory=temp_dir,
        schema_registry=vcl.load_dataset_schema_registry(),
        relationship_registry=vcl.load_relationship_registry(),
        validation_rules=vcl.load_validation_rule_registry(),
        source_type="test",
    )
    result = engine.run_validation()
    # File is unreadable as UTF-8 text
    assert result.dataset_results["hospital_master"].dataset_status == "Blocked"


# ---------------------------------------------------------------------------
# 10. missing required column blocks the dataset
# ---------------------------------------------------------------------------

def test_missing_required_column_blocks(temp_dir):
    df = pd.read_csv(Path("data/demo/hospital_master.csv"), dtype=str)
    df = df.drop(columns=["hospital_name"])
    df.to_csv(temp_dir / "hospital_master.csv", index=False)
    # Copy rest
    for f in Path("data/demo").glob("*.csv"):
        if f.stem != "hospital_master":
            shutil.copy(f, temp_dir / f.name)
    engine = DataValidationEngine(
        input_directory=temp_dir,
        schema_registry=vcl.load_dataset_schema_registry(),
        relationship_registry=vcl.load_relationship_registry(),
        validation_rules=vcl.load_validation_rule_registry(),
        source_type="test",
    )
    result = engine.run_validation()
    assert result.dataset_results["hospital_master"].dataset_status == "Blocked"


# ---------------------------------------------------------------------------
# 11. unexpected harmless column creates Warning
# ---------------------------------------------------------------------------

def test_unexpected_column_warning(temp_dir):
    df = pd.read_csv(Path("data/demo/hospital_master.csv"), dtype=str)
    df["extra_harmless_column"] = "x"
    df.to_csv(temp_dir / "hospital_master.csv", index=False)
    for f in Path("data/demo").glob("*.csv"):
        if f.stem != "hospital_master":
            shutil.copy(f, temp_dir / f.name)
    engine = DataValidationEngine(
        input_directory=temp_dir,
        schema_registry=vcl.load_dataset_schema_registry(),
        relationship_registry=vcl.load_relationship_registry(),
        validation_rules=vcl.load_validation_rule_registry(),
        source_type="test",
    )
    result = engine.run_validation()
    warnings = [i for i in result.issues if i.dataset_name == "hospital_master" and i.issue_type == "UNEXPECTED_COLUMN" and i.severity == "Warning"]
    assert len(warnings) >= 1


# ---------------------------------------------------------------------------
# 12. prohibited identifier column becomes Critical
# ---------------------------------------------------------------------------

def test_prohibited_identifier_column_critical(temp_dir):
    df = pd.read_csv(Path("data/demo/hospital_master.csv"), dtype=str)
    df["patient_name"] = "secret"
    df.to_csv(temp_dir / "hospital_master.csv", index=False)
    for f in Path("data/demo").glob("*.csv"):
        if f.stem != "hospital_master":
            shutil.copy(f, temp_dir / f.name)
    engine = DataValidationEngine(
        input_directory=temp_dir,
        schema_registry=vcl.load_dataset_schema_registry(),
        relationship_registry=vcl.load_relationship_registry(),
        validation_rules=vcl.load_validation_rule_registry(),
        source_type="test",
    )
    result = engine.run_validation()
    crits = [i for i in result.issues if i.dataset_name == "hospital_master" and i.issue_type == "UNEXPECTED_COLUMN" and i.severity == "Critical"]
    assert len(crits) >= 1


# ---------------------------------------------------------------------------
# 13. null primary key becomes Critical
# ---------------------------------------------------------------------------

def test_null_primary_key_critical(temp_dir):
    df = pd.read_csv(Path("data/demo/hospital_master.csv"), dtype=str)
    df.loc[0, "hospital_id"] = ""
    df.to_csv(temp_dir / "hospital_master.csv", index=False)
    for f in Path("data/demo").glob("*.csv"):
        if f.stem != "hospital_master":
            shutil.copy(f, temp_dir / f.name)
    engine = DataValidationEngine(
        input_directory=temp_dir,
        schema_registry=vcl.load_dataset_schema_registry(),
        relationship_registry=vcl.load_relationship_registry(),
        validation_rules=vcl.load_validation_rule_registry(),
        source_type="test",
    )
    result = engine.run_validation()
    pk_issues = [i for i in result.issues if i.dataset_name == "hospital_master" and i.issue_type == "PRIMARY_KEY_MISSING"]
    assert len(pk_issues) >= 1
    assert pk_issues[0].severity == "Critical"


# ---------------------------------------------------------------------------
# 14. duplicate primary key blocks the dataset
# ---------------------------------------------------------------------------

def test_duplicate_primary_key_blocks(temp_dir):
    df = pd.read_csv(Path("data/demo/hospital_master.csv"), dtype=str)
    # Duplicate the first row
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    df.to_csv(temp_dir / "hospital_master.csv", index=False)
    for f in Path("data/demo").glob("*.csv"):
        if f.stem != "hospital_master":
            shutil.copy(f, temp_dir / f.name)
    engine = DataValidationEngine(
        input_directory=temp_dir,
        schema_registry=vcl.load_dataset_schema_registry(),
        relationship_registry=vcl.load_relationship_registry(),
        validation_rules=vcl.load_validation_rule_registry(),
        source_type="test",
    )
    result = engine.run_validation()
    dup_issues = [i for i in result.issues if i.dataset_name == "hospital_master" and i.issue_type == "PRIMARY_KEY_DUPLICATE"]
    assert len(dup_issues) >= 1
    assert result.dataset_results["hospital_master"].dataset_status == "Blocked"


# ---------------------------------------------------------------------------
# 15. invalid foreign key is detected
# ---------------------------------------------------------------------------

def test_invalid_foreign_key_detected(temp_dir):
    df = pd.read_csv(Path("data/demo/department_master.csv"), dtype=str)
    df.loc[0, "hospital_id"] = "HOSP-INVALID"
    df.to_csv(temp_dir / "department_master.csv", index=False)
    for f in Path("data/demo").glob("*.csv"):
        if f.stem != "department_master":
            shutil.copy(f, temp_dir / f.name)
    engine = DataValidationEngine(
        input_directory=temp_dir,
        schema_registry=vcl.load_dataset_schema_registry(),
        relationship_registry=vcl.load_relationship_registry(),
        validation_rules=vcl.load_validation_rule_registry(),
        source_type="test",
    )
    result = engine.run_validation()
    orphan_issues = [i for i in result.issues if i.dataset_name == "department_master" and i.issue_type == "ORPHAN_FOREIGN_KEY"]
    assert len(orphan_issues) >= 1


# ---------------------------------------------------------------------------
# 16. optional null foreign key is not treated as orphan
# ---------------------------------------------------------------------------

def test_optional_null_fk_not_orphan(temp_dir):
    df = pd.read_csv(Path("data/demo/patient_complaints.csv"), dtype=str)
    # encounter_id is optional; ensure some are null
    assert df["encounter_id"].isna().sum() > 0 or (df["encounter_id"] == "").sum() > 0
    # Copy all files
    for f in Path("data/demo").glob("*.csv"):
        shutil.copy(f, temp_dir / f.name)
    engine = DataValidationEngine(
        input_directory=temp_dir,
        schema_registry=vcl.load_dataset_schema_registry(),
        relationship_registry=vcl.load_relationship_registry(),
        validation_rules=vcl.load_validation_rule_registry(),
        source_type="test",
    )
    result = engine.run_validation()
    # No orphan issue should be raised for null encounter_id in complaints
    null_orphan_issues = [i for i in result.issues if i.dataset_name == "patient_complaints" and i.field_name == "encounter_id" and i.issue_type == "ORPHAN_FOREIGN_KEY"]
    assert len(null_orphan_issues) == 0


# ---------------------------------------------------------------------------
# 17. invalid date is detected
# ---------------------------------------------------------------------------

def test_invalid_date_detected(temp_dir):
    df = pd.read_csv(Path("data/demo/hospital_master.csv"), dtype=str)
    df.loc[0, "effective_from"] = "not-a-date"
    df.to_csv(temp_dir / "hospital_master.csv", index=False)
    for f in Path("data/demo").glob("*.csv"):
        if f.stem != "hospital_master":
            shutil.copy(f, temp_dir / f.name)
    engine = DataValidationEngine(
        input_directory=temp_dir,
        schema_registry=vcl.load_dataset_schema_registry(),
        relationship_registry=vcl.load_relationship_registry(),
        validation_rules=vcl.load_validation_rule_registry(),
        source_type="test",
    )
    result = engine.run_validation()
    date_issues = [i for i in result.issues if i.dataset_name == "hospital_master" and i.issue_type == "INVALID_DATE"]
    assert len(date_issues) >= 1


# ---------------------------------------------------------------------------
# 18. invalid timestamp order is detected
# ---------------------------------------------------------------------------

def test_invalid_timestamp_order_detected(temp_dir):
    df = pd.read_csv(Path("data/demo/patient_encounters.csv"), dtype=str)
    df.loc[0, "service_end_datetime"] = df.loc[0, "arrival_datetime"]
    # Make end before start by using same value (start >= end)
    df.to_csv(temp_dir / "patient_encounters.csv", index=False)
    for f in Path("data/demo").glob("*.csv"):
        if f.stem != "patient_encounters":
            shutil.copy(f, temp_dir / f.name)
    engine = DataValidationEngine(
        input_directory=temp_dir,
        schema_registry=vcl.load_dataset_schema_registry(),
        relationship_registry=vcl.load_relationship_registry(),
        validation_rules=vcl.load_validation_rule_registry(),
        source_type="test",
    )
    result = engine.run_validation()
    order_issues = [i for i in result.issues if i.dataset_name == "patient_encounters" and i.issue_type == "DATETIME_ORDER"]
    assert len(order_issues) >= 1


# ---------------------------------------------------------------------------
# 19. negative numeric value is detected
# ---------------------------------------------------------------------------

def test_negative_numeric_detected(temp_dir):
    df = pd.read_csv(Path("data/demo/patient_queue_records.csv"), dtype=str)
    df.loc[0, "arrivals_count"] = "-5"
    df.to_csv(temp_dir / "patient_queue_records.csv", index=False)
    for f in Path("data/demo").glob("*.csv"):
        if f.stem != "patient_queue_records":
            shutil.copy(f, temp_dir / f.name)
    engine = DataValidationEngine(
        input_directory=temp_dir,
        schema_registry=vcl.load_dataset_schema_registry(),
        relationship_registry=vcl.load_relationship_registry(),
        validation_rules=vcl.load_validation_rule_registry(),
        source_type="test",
    )
    result = engine.run_validation()
    neg_issues = [i for i in result.issues if i.dataset_name == "patient_queue_records" and i.issue_type == "NEGATIVE_VALUE"]
    assert len(neg_issues) >= 1


# ---------------------------------------------------------------------------
# 20. survey score outside scale is detected
# ---------------------------------------------------------------------------

def test_survey_score_outside_scale_detected(temp_dir):
    df = pd.read_csv(Path("data/demo/patient_surveys.csv"), dtype=str)
    # Find a SCALE-5PT record and set score to 10
    mask = df["scale_id"] == "SCALE-5PT"
    if mask.any():
        df.loc[mask.idxmax(), "score_value"] = "10.0"
    df.to_csv(temp_dir / "patient_surveys.csv", index=False)
    for f in Path("data/demo").glob("*.csv"):
        if f.stem != "patient_surveys":
            shutil.copy(f, temp_dir / f.name)
    engine = DataValidationEngine(
        input_directory=temp_dir,
        schema_registry=vcl.load_dataset_schema_registry(),
        relationship_registry=vcl.load_relationship_registry(),
        validation_rules=vcl.load_validation_rule_registry(),
        source_type="test",
    )
    result = engine.run_validation()
    scale_issues = [i for i in result.issues if i.dataset_name == "patient_surveys" and i.issue_type == "SURVEY_SCALE"]
    assert len(scale_issues) >= 1


# ---------------------------------------------------------------------------
# 21. invalid survey scale is detected
# ---------------------------------------------------------------------------

def test_invalid_survey_scale_detected(temp_dir):
    df = pd.read_csv(Path("data/demo/patient_surveys.csv"), dtype=str)
    df.loc[0, "scale_id"] = "INVALID-SCALE"
    df.to_csv(temp_dir / "patient_surveys.csv", index=False)
    for f in Path("data/demo").glob("*.csv"):
        if f.stem != "patient_surveys":
            shutil.copy(f, temp_dir / f.name)
    engine = DataValidationEngine(
        input_directory=temp_dir,
        schema_registry=vcl.load_dataset_schema_registry(),
        relationship_registry=vcl.load_relationship_registry(),
        validation_rules=vcl.load_validation_rule_registry(),
        source_type="test",
    )
    result = engine.run_validation()
    domain_issues = [i for i in result.issues if i.dataset_name == "patient_surveys" and i.issue_type == "INVALID_DOMAIN" and i.field_name == "scale_id"]
    assert len(domain_issues) >= 1


# ---------------------------------------------------------------------------
# 22. invalid complaint status is detected
# ---------------------------------------------------------------------------

def test_invalid_complaint_status_detected(temp_dir):
    df = pd.read_csv(Path("data/demo/patient_complaints.csv"), dtype=str)
    df.loc[0, "status"] = "InvalidStatus"
    df.to_csv(temp_dir / "patient_complaints.csv", index=False)
    for f in Path("data/demo").glob("*.csv"):
        if f.stem != "patient_complaints":
            shutil.copy(f, temp_dir / f.name)
    engine = DataValidationEngine(
        input_directory=temp_dir,
        schema_registry=vcl.load_dataset_schema_registry(),
        relationship_registry=vcl.load_relationship_registry(),
        validation_rules=vcl.load_validation_rule_registry(),
        source_type="test",
    )
    result = engine.run_validation()
    domain_issues = [i for i in result.issues if i.dataset_name == "patient_complaints" and i.issue_type == "INVALID_DOMAIN" and i.field_name == "status"]
    assert len(domain_issues) >= 1


# ---------------------------------------------------------------------------
# 23. attendance without staff reference is detected
# ---------------------------------------------------------------------------

def test_attendance_without_staff_reference_detected(temp_dir):
    df = pd.read_csv(Path("data/demo/staff_attendance.csv"), dtype=str)
    df.loc[0, "staff_id"] = ""
    df.to_csv(temp_dir / "staff_attendance.csv", index=False)
    for f in Path("data/demo").glob("*.csv"):
        if f.stem != "staff_attendance":
            shutil.copy(f, temp_dir / f.name)
    engine = DataValidationEngine(
        input_directory=temp_dir,
        schema_registry=vcl.load_dataset_schema_registry(),
        relationship_registry=vcl.load_relationship_registry(),
        validation_rules=vcl.load_validation_rule_registry(),
        source_type="test",
    )
    result = engine.run_validation()
    missing_issues = [i for i in result.issues if i.dataset_name == "staff_attendance" and i.field_name == "staff_id" and i.issue_type == "REQUIRED_VALUE_MISSING"]
    assert len(missing_issues) >= 1


# ---------------------------------------------------------------------------
# 24. attendance without roster is detected according to rule
# ---------------------------------------------------------------------------

def test_attendance_without_roster_detected(temp_dir):
    df = pd.read_csv(Path("data/demo/staff_attendance.csv"), dtype=str)
    df.loc[0, "roster_id"] = "ROSTER-NONEXISTENT"
    df.to_csv(temp_dir / "staff_attendance.csv", index=False)
    for f in Path("data/demo").glob("*.csv"):
        if f.stem != "staff_attendance":
            shutil.copy(f, temp_dir / f.name)
    engine = DataValidationEngine(
        input_directory=temp_dir,
        schema_registry=vcl.load_dataset_schema_registry(),
        relationship_registry=vcl.load_relationship_registry(),
        validation_rules=vcl.load_validation_rule_registry(),
        source_type="test",
    )
    result = engine.run_validation()
    roster_issues = [i for i in result.issues if i.dataset_name == "staff_attendance" and i.issue_type == "ATTENDANCE_ROSTER"]
    assert len(roster_issues) >= 1


# ---------------------------------------------------------------------------
# 25. missing attendance is not imputed
# ---------------------------------------------------------------------------

def test_missing_attendance_not_imputed(temp_dir):
    df = pd.read_csv(Path("data/demo/staff_attendance.csv"), dtype=str)
    # Blank some statuses
    df.loc[0, "status"] = ""
    df.to_csv(temp_dir / "staff_attendance.csv", index=False)
    for f in Path("data/demo").glob("*.csv"):
        if f.stem != "staff_attendance":
            shutil.copy(f, temp_dir / f.name)
    engine = DataValidationEngine(
        input_directory=temp_dir,
        schema_registry=vcl.load_dataset_schema_registry(),
        relationship_registry=vcl.load_relationship_registry(),
        validation_rules=vcl.load_validation_rule_registry(),
        source_type="test",
    )
    result = engine.run_validation()
    missing_issues = [i for i in result.issues if i.dataset_name == "staff_attendance" and i.field_name == "status" and i.issue_type == "REQUIRED_VALUE_MISSING"]
    assert len(missing_issues) >= 1
    # Ensure no imputation happened (source file unchanged)
    reloaded = pd.read_csv(temp_dir / "staff_attendance.csv", dtype=str)
    assert pd.isna(reloaded.loc[0, "status"]) or reloaded.loc[0, "status"] == ""


# ---------------------------------------------------------------------------
# 26. reassigned staff without destination is detected
# ---------------------------------------------------------------------------

def test_reassigned_staff_without_destination_detected(temp_dir):
    df = pd.read_csv(Path("data/demo/staff_attendance.csv"), dtype=str)
    # Find a row and set status to Reassigned with blank department_id
    mask = df["status"] != ""
    if mask.any():
        idx = mask.idxmax()
        df.loc[idx, "status"] = "Reassigned"
        df.loc[idx, "department_id"] = ""
    df.to_csv(temp_dir / "staff_attendance.csv", index=False)
    for f in Path("data/demo").glob("*.csv"):
        if f.stem != "staff_attendance":
            shutil.copy(f, temp_dir / f.name)
    engine = DataValidationEngine(
        input_directory=temp_dir,
        schema_registry=vcl.load_dataset_schema_registry(),
        relationship_registry=vcl.load_relationship_registry(),
        validation_rules=vcl.load_validation_rule_registry(),
        source_type="test",
    )
    result = engine.run_validation()
    reassign_issues = [i for i in result.issues if i.dataset_name == "staff_attendance" and i.issue_type == "ATTENDANCE_REASSIGN"]
    assert len(reassign_issues) >= 1


# ---------------------------------------------------------------------------
# 27. replacement staff invalid reference is detected
# ---------------------------------------------------------------------------

def test_replacement_staff_invalid_reference_detected(temp_dir):
    df = pd.read_csv(Path("data/demo/staff_attendance.csv"), dtype=str)
    # Set a replacement_staff_id to invalid value
    mask = df["replacement_staff_id"].isna() | (df["replacement_staff_id"] == "")
    # Find a row with blank replacement and set it
    if mask.any():
        idx = mask.idxmax()
        df.loc[idx, "replacement_staff_id"] = "STAFF-INVALID"
    df.to_csv(temp_dir / "staff_attendance.csv", index=False)
    for f in Path("data/demo").glob("*.csv"):
        if f.stem != "staff_attendance":
            shutil.copy(f, temp_dir / f.name)
    engine = DataValidationEngine(
        input_directory=temp_dir,
        schema_registry=vcl.load_dataset_schema_registry(),
        relationship_registry=vcl.load_relationship_registry(),
        validation_rules=vcl.load_validation_rule_registry(),
        source_type="test",
    )
    result = engine.run_validation()
    repl_issues = [i for i in result.issues if i.dataset_name == "staff_attendance" and i.issue_type == "INVALID_REPLACEMENT_STAFF"]
    assert len(repl_issues) >= 1


# ---------------------------------------------------------------------------
# 28. occupied beds above operational with exception metadata is accepted
# ---------------------------------------------------------------------------

def test_occupied_above_operational_with_exception_accepted(temp_dir):
    df = pd.read_csv(Path("data/demo/bed_capacity_records.csv"), dtype=str)
    # Find a row and make occupied > operational with exception metadata
    df.loc[0, "bed_occupied"] = "999"
    df.loc[0, "exception_flag"] = "True"
    df.loc[0, "exception_reason"] = "Surge capacity activated"
    df.to_csv(temp_dir / "bed_capacity_records.csv", index=False)
    for f in Path("data/demo").glob("*.csv"):
        if f.stem != "bed_capacity_records":
            shutil.copy(f, temp_dir / f.name)
    engine = DataValidationEngine(
        input_directory=temp_dir,
        schema_registry=vcl.load_dataset_schema_registry(),
        relationship_registry=vcl.load_relationship_registry(),
        validation_rules=vcl.load_validation_rule_registry(),
        source_type="test",
    )
    result = engine.run_validation()
    # Should NOT have BED_EXCEPTION because exception_flag is True and reason is populated
    exc_issues = [i for i in result.issues if i.dataset_name == "bed_capacity_records" and i.issue_type == "BED_EXCEPTION"]
    assert len(exc_issues) == 0


# ---------------------------------------------------------------------------
# 29. occupied beds above operational without exception reason is detected
# ---------------------------------------------------------------------------

def test_occupied_above_operational_without_exception_reason_detected(temp_dir):
    df = pd.read_csv(Path("data/demo/bed_capacity_records.csv"), dtype=str)
    df.loc[0, "bed_occupied"] = "999"
    df.loc[0, "exception_flag"] = "True"
    df.loc[0, "exception_reason"] = ""
    df.to_csv(temp_dir / "bed_capacity_records.csv", index=False)
    for f in Path("data/demo").glob("*.csv"):
        if f.stem != "bed_capacity_records":
            shutil.copy(f, temp_dir / f.name)
    engine = DataValidationEngine(
        input_directory=temp_dir,
        schema_registry=vcl.load_dataset_schema_registry(),
        relationship_registry=vcl.load_relationship_registry(),
        validation_rules=vcl.load_validation_rule_registry(),
        source_type="test",
    )
    result = engine.run_validation()
    exc_issues = [i for i in result.issues if i.dataset_name == "bed_capacity_records" and i.issue_type == "BED_EXCEPTION"]
    assert len(exc_issues) >= 1


# ---------------------------------------------------------------------------
# 30. operational beds above licensed beds is detected
# ---------------------------------------------------------------------------

def test_operational_above_licensed_detected(temp_dir):
    df = pd.read_csv(Path("data/demo/bed_capacity_records.csv"), dtype=str)
    df.loc[0, "bed_operational"] = "999"
    df.loc[0, "bed_licensed"] = "10"
    df.to_csv(temp_dir / "bed_capacity_records.csv", index=False)
    for f in Path("data/demo").glob("*.csv"):
        if f.stem != "bed_capacity_records":
            shutil.copy(f, temp_dir / f.name)
    engine = DataValidationEngine(
        input_directory=temp_dir,
        schema_registry=vcl.load_dataset_schema_registry(),
        relationship_registry=vcl.load_relationship_registry(),
        validation_rules=vcl.load_validation_rule_registry(),
        source_type="test",
    )
    result = engine.run_validation()
    logic_issues = [i for i in result.issues if i.dataset_name == "bed_capacity_records" and i.issue_type == "BED_LOGIC"]
    assert len(logic_issues) >= 1


# ---------------------------------------------------------------------------
# 31. queue counts inconsistent are detected
# ---------------------------------------------------------------------------

def test_queue_counts_inconsistent_detected(temp_dir):
    df = pd.read_csv(Path("data/demo/patient_queue_records.csv"), dtype=str)
    df.loc[0, "served_count"] = "999"
    df.loc[0, "arrivals_count"] = "10"
    df.to_csv(temp_dir / "patient_queue_records.csv", index=False)
    for f in Path("data/demo").glob("*.csv"):
        if f.stem != "patient_queue_records":
            shutil.copy(f, temp_dir / f.name)
    engine = DataValidationEngine(
        input_directory=temp_dir,
        schema_registry=vcl.load_dataset_schema_registry(),
        relationship_registry=vcl.load_relationship_registry(),
        validation_rules=vcl.load_validation_rule_registry(),
        source_type="test",
    )
    result = engine.run_validation()
    queue_issues = [i for i in result.issues if i.dataset_name == "patient_queue_records" and i.issue_type == "QUEUE_LOGIC"]
    assert len(queue_issues) >= 1


# ---------------------------------------------------------------------------
# 32. clean source files remain unchanged after validation
# ---------------------------------------------------------------------------

def test_source_files_unchanged(engine_for_clean, temp_dir):
    # Compute checksums before
    before_checksums = {}
    for f in Path("data/demo").glob("*.csv"):
        before_checksums[f.name] = hashlib.sha256(f.read_bytes()).hexdigest()
    # Run validation
    result = engine_for_clean.run_validation()
    # Compute checksums after
    after_checksums = {}
    for f in Path("data/demo").glob("*.csv"):
        after_checksums[f.name] = hashlib.sha256(f.read_bytes()).hexdigest()
    for name in before_checksums:
        assert before_checksums[name] == after_checksums[name], f"Source file {name} was modified"


# ---------------------------------------------------------------------------
# 33. validation outputs are generated
# ---------------------------------------------------------------------------

def test_validation_outputs_generated(engine_for_clean, temp_dir):
    result = engine_for_clean.run_validation()
    files = export_validation_outputs(result, temp_dir)
    assert len(files) == 7
    for name, path in files.items():
        assert path.exists(), f"Output file {name} not found"


# ---------------------------------------------------------------------------
# 34. empty manual override register is created
# ---------------------------------------------------------------------------

def test_empty_manual_override_register_created(engine_for_clean, temp_dir):
    result = engine_for_clean.run_validation()
    files = export_validation_outputs(result, temp_dir)
    mo_path = files["manual_override_register.csv"]
    assert mo_path.exists()
    df = pd.read_csv(mo_path)
    # Should have headers even when empty
    assert len(df.columns) > 0


# ---------------------------------------------------------------------------
# 35. audit events are generated
# ---------------------------------------------------------------------------

def test_audit_events_generated(engine_for_clean):
    result = engine_for_clean.run_validation()
    assert len(result.audit_events) > 0
    event_types = {e.event_type for e in result.audit_events}
    assert "Validation Started" in event_types
    assert "Validation Completed" in event_types


# ---------------------------------------------------------------------------
# 36. repeated validation gives consistent issue counts
# ---------------------------------------------------------------------------

def test_repeated_validation_consistent(engine_for_clean):
    result1 = engine_for_clean.run_validation()
    result2 = engine_for_clean.run_validation()
    assert len(result1.issues) == len(result2.issues)
    assert len(result1.record_issues) == len(result2.record_issues)


# ---------------------------------------------------------------------------
# 37. record-level issue examples respect the configured maximum
# ---------------------------------------------------------------------------

def test_record_level_respects_maximum(clean_demo_dir, temp_dir):
    # Create a dataset with many invalid records
    df = pd.read_csv(Path("data/demo/hospital_master.csv"), dtype=str)
    # Duplicate to create many rows with same PK (will trigger many record issues)
    df_large = pd.concat([df] * 5, ignore_index=True)
    df_large.to_csv(temp_dir / "hospital_master.csv", index=False)
    for f in Path("data/demo").glob("*.csv"):
        if f.stem != "hospital_master":
            shutil.copy(f, temp_dir / f.name)
    engine = DataValidationEngine(
        input_directory=temp_dir,
        schema_registry=vcl.load_dataset_schema_registry(),
        relationship_registry=vcl.load_relationship_registry(),
        validation_rules=vcl.load_validation_rule_registry(),
        source_type="test",
        maximum_record_level_examples=10,
    )
    result = engine.run_validation()
    pk_issues = [ri for ri in result.record_issues if ri.dataset_name == "hospital_master" and ri.issue_description == "Duplicate primary key"]
    assert len(pk_issues) <= 10


# ---------------------------------------------------------------------------
# 38. engine does not create processed datasets
# ---------------------------------------------------------------------------

def test_engine_does_not_create_processed_datasets(engine_for_clean, temp_dir):
    result = engine_for_clean.run_validation()
    export_validation_outputs(result, temp_dir)
    # Check no processed/ directory created
    assert not (temp_dir / "processed").exists()
    # Check no analytical CSVs created
    for f in temp_dir.iterdir():
        assert f.suffix in (".csv", ".json")


# ---------------------------------------------------------------------------
# 39. engine does not calculate KPI values
# ---------------------------------------------------------------------------

def test_engine_does_not_calculate_kpis(engine_for_clean):
    result = engine_for_clean.run_validation()
    # No KPI-related issues should exist
    kpi_issues = [i for i in result.issues if "kpi" in i.issue_description.lower()]
    assert len(kpi_issues) == 0


# ---------------------------------------------------------------------------
# 40. engine does not generate forecast, risk, scenario, financial or recommendation outputs
# ---------------------------------------------------------------------------

def test_engine_no_analytical_outputs(engine_for_clean, temp_dir):
    result = engine_for_clean.run_validation()
    files = export_validation_outputs(result, temp_dir)
    for name in files:
        content = files[name].read_text(encoding="utf-8").lower()
        assert "forecast" not in content or "forecast" in name.lower()
        assert "risk score" not in content
        assert "scenario" not in content or "scenario" in name.lower()
        assert "financial impact" not in content
        assert "recommendation" not in content


# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------

def test_parse_args_defaults():
    args = parse_args([])
    assert args.input_dir == "data/demo"
    assert args.source_type == "synthetic_demo"
    assert args.output_dir == "outputs/logs"
    assert args.collect_record_issues is True
    assert args.max_record_examples == 100


def test_parse_args_custom():
    args = parse_args(["--input-dir", "data/uploaded", "--source-type", "uploaded", "--max-record-examples", "50"])
    assert args.input_dir == "data/uploaded"
    assert args.source_type == "uploaded"
    assert args.max_record_examples == 50
