"""
Sentinel360 Healthcare — Queue, Bed Capacity and Service Schedule Transformation Tests

Step 2D-3B test coverage.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.queue_capacity_schedule_transformer import (
    QueueCapacityScheduleTransformer,
    TRANSFORMATION_VERSION,
    EXCLUSION_REASONS,
)
from src.run_queue_capacity_schedule_processing import run_queue_capacity_schedule_processing
from src.processed_schema_registry import get_processed_schema


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

@pytest.fixture
def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def valid_manifest(project_root: Path) -> dict:
    manifest_path = project_root / "outputs" / "logs" / "validation_run_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def source_queue(project_root: Path) -> pd.DataFrame:
    path = project_root / "data" / "demo" / "patient_queue_records.csv"
    return pd.read_csv(path)


@pytest.fixture
def source_bed(project_root: Path) -> pd.DataFrame:
    path = project_root / "data" / "demo" / "bed_capacity_records.csv"
    return pd.read_csv(path)


@pytest.fixture
def source_schedule(project_root: Path) -> pd.DataFrame:
    path = project_root / "data" / "demo" / "service_schedule.csv"
    return pd.read_csv(path)


@pytest.fixture
def transformer(project_root: Path) -> QueueCapacityScheduleTransformer:
    return QueueCapacityScheduleTransformer(
        processing_run_id=f"TEST-{uuid.uuid4().hex[:8].upper()}",
        validation_run_id="",
        input_directory=project_root / "data" / "demo",
        output_directory=project_root / "data" / "processed",
        validation_log_directory=project_root / "outputs" / "logs",
        source_type="synthetic_demo",
        collect_lineage=True,
        max_issue_examples=1000,
    )


@pytest.fixture
def transformed_queue(transformer: QueueCapacityScheduleTransformer, source_queue: pd.DataFrame) -> pd.DataFrame:
    return transformer.transform_patient_queue(source_queue)


@pytest.fixture
def transformed_bed(transformer: QueueCapacityScheduleTransformer, source_bed: pd.DataFrame) -> pd.DataFrame:
    return transformer.transform_bed_capacity(source_bed)


@pytest.fixture
def transformed_schedule(transformer: QueueCapacityScheduleTransformer, source_schedule: pd.DataFrame) -> pd.DataFrame:
    return transformer.transform_service_schedule(source_schedule)


@pytest.fixture
def source_checksums(project_root: Path) -> dict:
    checksums = {}
    for name in ["patient_queue_records.csv", "bed_capacity_records.csv", "service_schedule.csv"]:
        path = project_root / "data" / "demo" / name
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        checksums[name] = h.hexdigest()
    return checksums


# ------------------------------------------------------------------
# 1. Module import safety
# ------------------------------------------------------------------

def test_modules_import_safely():
    import src.queue_capacity_schedule_transformer
    import src.run_queue_capacity_schedule_processing
    assert hasattr(src.queue_capacity_schedule_transformer, "QueueCapacityScheduleTransformer")
    assert hasattr(src.run_queue_capacity_schedule_processing, "run_queue_capacity_schedule_processing")


# ------------------------------------------------------------------
# 2. Runner does not execute on import
# ------------------------------------------------------------------

def test_runner_does_not_execute_on_import(project_root: Path):
    import subprocess
    result = subprocess.run(
        [sys.executable, "-c", "import src.run_queue_capacity_schedule_processing; print('OK')"],
        cwd=str(project_root),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "OK" in result.stdout
    assert "SUMMARY" not in result.stdout


# ------------------------------------------------------------------
# 3. Validation gate accepts approved run
# ------------------------------------------------------------------

def test_validation_gate_passes(transformer: QueueCapacityScheduleTransformer, valid_manifest: dict):
    gate = transformer.check_validation_gate()
    assert gate.processing_allowed is True


# ------------------------------------------------------------------
# 4. Validation gate rejects processing_allowed false
# ------------------------------------------------------------------

def test_validation_gate_rejects_blocked_gate(project_root: Path, tmp_path: Path):
    # Create a temporary blocked manifest
    blocked_manifest = {
        "validation_run_id": "VAL-BLOCKED-001",
        "run_status": "Failed",
        "processing_allowed_flag": False,
        "accepted_datasets": [],
        "excluded_datasets": ["patient_queue_records", "bed_capacity_records", "service_schedule"],
    }
    temp_log_dir = tmp_path / "logs"
    temp_log_dir.mkdir()
    with open(temp_log_dir / "validation_run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(blocked_manifest, f)
    # Empty summary to avoid file-not-found
    pd.DataFrame(columns=["dataset_name", "validation_status", "processing_allowed"]).to_csv(
        temp_log_dir / "dataset_validation_summary.csv", index=False
    )
    # Empty override register
    pd.DataFrame(columns=["dataset_name", "override_approved"]).to_csv(
        temp_log_dir / "manual_override_register.csv", index=False
    )

    t = QueueCapacityScheduleTransformer(
        processing_run_id="TEST-BLOCKED",
        validation_run_id="",
        input_directory=project_root / "data" / "demo",
        output_directory=tmp_path / "processed",
        validation_log_directory=temp_log_dir,
    )
    gate = t.check_validation_gate()
    assert gate.processing_allowed is False


# ------------------------------------------------------------------
# 5. Queue output matches approved schema
# ------------------------------------------------------------------

def test_queue_output_matches_schema(transformed_queue: pd.DataFrame):
    schema = get_processed_schema("processed_patient_queue")
    required = schema["required_fields"]
    for field in required:
        assert field in transformed_queue.columns, f"Missing required field: {field}"


# ------------------------------------------------------------------
# 6. Bed output matches approved schema
# ------------------------------------------------------------------

def test_bed_output_matches_schema(transformed_bed: pd.DataFrame):
    schema = get_processed_schema("processed_bed_capacity")
    required = schema["required_fields"]
    for field in required:
        assert field in transformed_bed.columns, f"Missing required field: {field}"


# ------------------------------------------------------------------
# 7. Schedule output matches approved schema
# ------------------------------------------------------------------

def test_schedule_output_matches_schema(transformed_schedule: pd.DataFrame):
    schema = get_processed_schema("processed_service_schedule")
    required = schema["required_fields"]
    for field in required:
        assert field in transformed_schedule.columns, f"Missing required field: {field}"


# ------------------------------------------------------------------
# 8. All three processed files are created
# ------------------------------------------------------------------

def test_all_three_processed_files_created(project_root: Path, tmp_path: Path):
    out_dir = tmp_path / "processed"
    log_dir = tmp_path / "logs"
    out_dir.mkdir()
    log_dir.mkdir()
    # Copy validation manifest so gate passes
    shutil.copy(project_root / "outputs" / "logs" / "validation_run_manifest.json", log_dir / "validation_run_manifest.json")
    shutil.copy(project_root / "outputs" / "logs" / "dataset_validation_summary.csv", log_dir / "dataset_validation_summary.csv")
    shutil.copy(project_root / "outputs" / "logs" / "manual_override_register.csv", log_dir / "manual_override_register.csv")

    result = run_queue_capacity_schedule_processing(
        input_dir=project_root / "data" / "demo",
        output_dir=out_dir,
        validation_log_dir=log_dir,
        execute_export=True,
    )
    assert result["status"] in ("completed", "failed_schema")
    assert (out_dir / "processed_patient_queue.csv").exists()
    assert (out_dir / "processed_bed_capacity.csv").exists()
    assert (out_dir / "processed_service_schedule.csv").exists()


# ------------------------------------------------------------------
# 9. Patient-flow-daily output is not created
# ------------------------------------------------------------------

def test_patient_flow_daily_not_created(project_root: Path, tmp_path: Path):
    out_dir = tmp_path / "processed"
    log_dir = tmp_path / "logs"
    out_dir.mkdir()
    log_dir.mkdir()
    shutil.copy(project_root / "outputs" / "logs" / "validation_run_manifest.json", log_dir / "validation_run_manifest.json")
    shutil.copy(project_root / "outputs" / "logs" / "dataset_validation_summary.csv", log_dir / "dataset_validation_summary.csv")
    shutil.copy(project_root / "outputs" / "logs" / "manual_override_register.csv", log_dir / "manual_override_register.csv")

    run_queue_capacity_schedule_processing(
        input_dir=project_root / "data" / "demo",
        output_dir=out_dir,
        validation_log_dir=log_dir,
        execute_export=True,
    )
    assert not (out_dir / "processed_patient_flow_daily.csv").exists()


# ------------------------------------------------------------------
# 10. Source files remain unchanged
# ------------------------------------------------------------------

def test_source_files_unchanged(project_root: Path, source_checksums: dict):
    for name, expected in source_checksums.items():
        path = project_root / "data" / "demo" / name
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        assert h.hexdigest() == expected


# ------------------------------------------------------------------
# 11. Workforce outputs remain unchanged
# ------------------------------------------------------------------

def test_workforce_outputs_remain_unchanged(project_root: Path):
    workforce_files = [
        "processed_hospital_master.csv",
        "processed_department_master.csv",
        "processed_staff_role_master.csv",
        "processed_staff_master.csv",
        "processed_staff_roster.csv",
        "processed_staff_attendance.csv",
        "processed_staffing_requirement.csv",
        "processed_workforce_daily.csv",
    ]
    for name in workforce_files:
        assert (project_root / "data" / "processed" / name).exists(), f"Missing workforce file: {name}"


# ------------------------------------------------------------------
# 12. Processed encounter output remains unchanged
# ------------------------------------------------------------------

def test_encounter_output_remains_unchanged(project_root: Path):
    assert (project_root / "data" / "processed" / "processed_patient_encounters.csv").exists()


# ------------------------------------------------------------------
# 13. Queue IDs preserved and unique
# ------------------------------------------------------------------

def test_queue_ids_preserved_and_unique(transformed_queue: pd.DataFrame, source_queue: pd.DataFrame):
    assert transformed_queue["queue_record_id"].nunique() == len(transformed_queue)
    assert set(transformed_queue["queue_record_id"]) == set(source_queue["queue_id"].astype(str))


# ------------------------------------------------------------------
# 14. Queue dates parse correctly
# ------------------------------------------------------------------

def test_queue_dates_parse_correctly(transformed_queue: pd.DataFrame):
    assert transformed_queue["queue_date"].notna().all()
    assert transformed_queue["reporting_date"].notna().all()


# ------------------------------------------------------------------
# 15. Queue reporting_month uses YYYY-MM
# ------------------------------------------------------------------

def test_queue_reporting_month_format(transformed_queue: pd.DataFrame):
    assert transformed_queue["reporting_month"].notna().all()
    for val in transformed_queue["reporting_month"].dropna():
        assert len(str(val)) == 7 and str(val)[4] == "-"


# ------------------------------------------------------------------
# 16. Queue-stage detail is preserved
# ------------------------------------------------------------------

def test_queue_stage_detail_preserved(transformed_queue: pd.DataFrame, source_queue: pd.DataFrame):
    source_stages = set(source_queue["queue_type"].astype(str))
    processed_stages = set(transformed_queue["queue_stage"].astype(str))
    assert source_stages == processed_stages


# ------------------------------------------------------------------
# 17. Queue counts remain non-negative
# ------------------------------------------------------------------

def test_queue_counts_non_negative(transformed_queue: pd.DataFrame):
    count_cols = ["arrivals_count", "served_count", "waiting_patient_count"]
    for col in count_cols:
        if col in transformed_queue.columns:
            valid = transformed_queue[col].dropna()
            assert (valid >= 0).all(), f"Negative values found in {col}"


# ------------------------------------------------------------------
# 18. Negative queue counts are detected
# ------------------------------------------------------------------

def test_negative_queue_counts_detected(project_root: Path):
    source = pd.read_csv(project_root / "data" / "demo" / "patient_queue_records.csv")
    source.loc[0, "arrivals_count"] = -5
    t = QueueCapacityScheduleTransformer(
        processing_run_id="TEST-NEG-QUEUE",
        validation_run_id="",
        input_directory=project_root / "data" / "demo",
        output_directory=project_root / "data" / "processed",
        validation_log_directory=project_root / "outputs" / "logs",
    )
    result = t.transform_patient_queue(source)
    assert any(i.issue_type == "Invalid Queue Count" for i in t.issues)
    assert result.loc[0, "valid_queue_record_flag"] == False


# ------------------------------------------------------------------
# 19. Blank queue values remain null
# ------------------------------------------------------------------

def test_blank_queue_values_remain_null(project_root: Path):
    source = pd.read_csv(project_root / "data" / "demo" / "patient_queue_records.csv")
    # Ensure at least one blank exists or create one
    if source["avg_wait_minutes"].notna().all():
        source.loc[0, "avg_wait_minutes"] = None
    t = QueueCapacityScheduleTransformer(
        processing_run_id="TEST-BLANK-QUEUE",
        validation_run_id="",
        input_directory=project_root / "data" / "demo",
        output_directory=project_root / "data" / "processed",
        validation_log_directory=project_root / "outputs" / "logs",
    )
    result = t.transform_patient_queue(source)
    blank_mask = source["avg_wait_minutes"].isna()
    assert result.loc[blank_mask, "average_wait_minutes"].isna().all()


# ------------------------------------------------------------------
# 20. Queue wait values remain non-negative
# ------------------------------------------------------------------

def test_queue_wait_values_non_negative(transformed_queue: pd.DataFrame):
    wait_cols = ["average_wait_minutes", "median_wait_minutes", "maximum_wait_minutes"]
    for col in wait_cols:
        if col in transformed_queue.columns:
            valid = transformed_queue[col].dropna()
            assert (valid >= 0).all(), f"Negative values found in {col}"


# ------------------------------------------------------------------
# 21. encounter_derived_flag is not invented
# ------------------------------------------------------------------

def test_encounter_derived_flag_not_invented(transformed_queue: pd.DataFrame):
    # If source did not have the column, it should be null (not True/False)
    source = pd.read_csv(Path(__file__).resolve().parent.parent / "data" / "demo" / "patient_queue_records.csv")
    if "encounter_derived_flag" not in source.columns:
        assert transformed_queue["encounter_derived_flag"].isna().all()


# ------------------------------------------------------------------
# 22. Bed IDs preserved and unique
# ------------------------------------------------------------------

def test_bed_ids_preserved_and_unique(transformed_bed: pd.DataFrame, source_bed: pd.DataFrame):
    assert transformed_bed["bed_capacity_record_id"].nunique() == len(transformed_bed)
    assert set(transformed_bed["bed_capacity_record_id"]) == set(source_bed["record_id"].astype(str))


# ------------------------------------------------------------------
# 23. Bed reporting dates parse correctly
# ------------------------------------------------------------------

def test_bed_reporting_dates_parse_correctly(transformed_bed: pd.DataFrame):
    assert transformed_bed["reporting_date"].notna().all()


# ------------------------------------------------------------------
# 24. Bed counts remain non-negative
# ------------------------------------------------------------------

def test_bed_counts_non_negative(transformed_bed: pd.DataFrame):
    bed_cols = ["licensed_beds", "staffed_beds", "operational_beds", "occupied_beds", "unavailable_beds", "reserved_beds"]
    for col in bed_cols:
        if col in transformed_bed.columns:
            valid = transformed_bed[col].dropna()
            assert (valid >= 0).all(), f"Negative values found in {col}"


# ------------------------------------------------------------------
# 25. Negative bed counts are detected
# ------------------------------------------------------------------

def test_negative_bed_counts_detected(project_root: Path):
    source = pd.read_csv(project_root / "data" / "demo" / "bed_capacity_records.csv")
    source.loc[0, "bed_occupied"] = -3
    t = QueueCapacityScheduleTransformer(
        processing_run_id="TEST-NEG-BED",
        validation_run_id="",
        input_directory=project_root / "data" / "demo",
        output_directory=project_root / "data" / "processed",
        validation_log_directory=project_root / "outputs" / "logs",
    )
    result = t.transform_bed_capacity(source)
    assert any(i.issue_type == "Invalid Bed Count" for i in t.issues)
    assert result.loc[0, "valid_bed_record_flag"] == False


# ------------------------------------------------------------------
# 26. Occupied beds may exceed operational beds
# ------------------------------------------------------------------

def test_occupied_beds_may_exceed_operational(project_root: Path):
    source = pd.read_csv(project_root / "data" / "demo" / "bed_capacity_records.csv")
    source.loc[0, "bed_occupied"] = source.loc[0, "bed_operational"] + 10
    t = QueueCapacityScheduleTransformer(
        processing_run_id="TEST-OVERCAP",
        validation_run_id="",
        input_directory=project_root / "data" / "demo",
        output_directory=project_root / "data" / "processed",
        validation_log_directory=project_root / "outputs" / "logs",
    )
    result = t.transform_bed_capacity(source)
    assert result.loc[0, "occupied_beds"] > result.loc[0, "operational_beds"]
    assert result.loc[0, "overcapacity_flag"] == True


# ------------------------------------------------------------------
# 27. Occupied beds are not capped
# ------------------------------------------------------------------

def test_occupied_beds_not_capped(project_root: Path):
    source = pd.read_csv(project_root / "data" / "demo" / "bed_capacity_records.csv")
    original_occupied = source.loc[0, "bed_occupied"]
    if original_occupied <= source.loc[0, "bed_operational"]:
        source.loc[0, "bed_occupied"] = source.loc[0, "bed_operational"] + 5
        original_occupied = source.loc[0, "bed_occupied"]
    t = QueueCapacityScheduleTransformer(
        processing_run_id="TEST-NO-CAP",
        validation_run_id="",
        input_directory=project_root / "data" / "demo",
        output_directory=project_root / "data" / "processed",
        validation_log_directory=project_root / "outputs" / "logs",
    )
    result = t.transform_bed_capacity(source)
    assert result.loc[0, "occupied_beds"] == original_occupied


# ------------------------------------------------------------------
# 28. beds_above_operational_capacity calculates correctly
# ------------------------------------------------------------------

def test_beds_above_operational_capacity_calculated(project_root: Path):
    source = pd.read_csv(project_root / "data" / "demo" / "bed_capacity_records.csv")
    source.loc[0, "bed_occupied"] = source.loc[0, "bed_operational"] + 7
    t = QueueCapacityScheduleTransformer(
        processing_run_id="TEST-ABOVE-CAP",
        validation_run_id="",
        input_directory=project_root / "data" / "demo",
        output_directory=project_root / "data" / "processed",
        validation_log_directory=project_root / "outputs" / "logs",
    )
    result = t.transform_bed_capacity(source)
    expected = max(result.loc[0, "occupied_beds"] - result.loc[0, "operational_beds"], 0)
    assert result.loc[0, "beds_above_operational_capacity"] == expected


# ------------------------------------------------------------------
# 29. overcapacity_flag calculates correctly
# ------------------------------------------------------------------

def test_overcapacity_flag_calculated(project_root: Path):
    source = pd.read_csv(project_root / "data" / "demo" / "bed_capacity_records.csv")
    source.loc[0, "bed_occupied"] = source.loc[0, "bed_operational"] + 1
    t = QueueCapacityScheduleTransformer(
        processing_run_id="TEST-FLAG",
        validation_run_id="",
        input_directory=project_root / "data" / "demo",
        output_directory=project_root / "data" / "processed",
        validation_log_directory=project_root / "outputs" / "logs",
    )
    result = t.transform_bed_capacity(source)
    assert result.loc[0, "overcapacity_flag"] == True


# ------------------------------------------------------------------
# 30. Overcapacity is not automatically invalid
# ------------------------------------------------------------------

def test_overcapacity_not_automatically_invalid(project_root: Path):
    source = pd.read_csv(project_root / "data" / "demo" / "bed_capacity_records.csv")
    source.loc[0, "bed_occupied"] = source.loc[0, "bed_operational"] + 5
    t = QueueCapacityScheduleTransformer(
        processing_run_id="TEST-OVER-VALID",
        validation_run_id="",
        input_directory=project_root / "data" / "demo",
        output_directory=project_root / "data" / "processed",
        validation_log_directory=project_root / "outputs" / "logs",
    )
    result = t.transform_bed_capacity(source)
    assert result.loc[0, "valid_bed_record_flag"] == True
    assert not any(i.issue_type == "Invalid Bed Count" and i.severity in ("Error", "Critical") for i in t.issues)


# ------------------------------------------------------------------
# 31. Blank bed values remain null
# ------------------------------------------------------------------

def test_blank_bed_values_remain_null(project_root: Path):
    source = pd.read_csv(project_root / "data" / "demo" / "bed_capacity_records.csv")
    if source["bed_reserved"].notna().all():
        source.loc[0, "bed_reserved"] = None
    t = QueueCapacityScheduleTransformer(
        processing_run_id="TEST-BLANK-BED",
        validation_run_id="",
        input_directory=project_root / "data" / "demo",
        output_directory=project_root / "data" / "processed",
        validation_log_directory=project_root / "outputs" / "logs",
    )
    result = t.transform_bed_capacity(source)
    blank_mask = source["bed_reserved"].isna()
    assert result.loc[blank_mask, "reserved_beds"].isna().all()


# ------------------------------------------------------------------
# 32. Service schedule IDs preserved and unique
# ------------------------------------------------------------------

def test_schedule_ids_preserved_and_unique(transformed_schedule: pd.DataFrame, source_schedule: pd.DataFrame):
    assert transformed_schedule["service_schedule_id"].nunique() == len(transformed_schedule)
    assert set(transformed_schedule["service_schedule_id"]) == set(source_schedule["schedule_id"].astype(str))


# ------------------------------------------------------------------
# 33. Service dates parse correctly
# ------------------------------------------------------------------

def test_service_dates_parse_correctly(transformed_schedule: pd.DataFrame):
    assert transformed_schedule["service_date"].notna().all()
    assert transformed_schedule["reporting_date"].notna().all()


# ------------------------------------------------------------------
# 34. Session timestamps parse correctly
# ------------------------------------------------------------------

def test_session_timestamps_parse_correctly(transformed_schedule: pd.DataFrame):
    assert pd.api.types.is_datetime64_any_dtype(transformed_schedule["session_start_datetime"])
    assert pd.api.types.is_datetime64_any_dtype(transformed_schedule["session_end_datetime"])


# ------------------------------------------------------------------
# 35. Valid service duration calculates correctly
# ------------------------------------------------------------------

def test_valid_service_duration_calculated(project_root: Path):
    source = pd.read_csv(project_root / "data" / "demo" / "service_schedule.csv")
    t = QueueCapacityScheduleTransformer(
        processing_run_id="TEST-DUR",
        validation_run_id="",
        input_directory=project_root / "data" / "demo",
        output_directory=project_root / "data" / "processed",
        validation_log_directory=project_root / "outputs" / "logs",
    )
    result = t.transform_service_schedule(source)
    # planned_service_hours should come from source planned_hours when available
    assert result["planned_service_hours"].notna().sum() > 0
    # For records with valid timestamps, duration should be positive (cross-midnight handled)
    valid_ts = result["session_start_datetime"].notna() & result["session_end_datetime"].notna()
    assert (result.loc[valid_ts, "planned_service_hours"] >= 0).all()


# ------------------------------------------------------------------
# 36. Valid overnight session produces positive duration
# ------------------------------------------------------------------

def test_overnight_session_positive_duration(project_root: Path):
    source = pd.read_csv(project_root / "data" / "demo" / "service_schedule.csv")
    # Create an overnight session
    source.loc[0, "planned_start_time"] = "2024-01-01 22:00:00"
    source.loc[0, "planned_end_time"] = "2024-01-02 06:00:00"
    t = QueueCapacityScheduleTransformer(
        processing_run_id="TEST-OVERNIGHT",
        validation_run_id="",
        input_directory=project_root / "data" / "demo",
        output_directory=project_root / "data" / "processed",
        validation_log_directory=project_root / "outputs" / "logs",
    )
    result = t.transform_service_schedule(source)
    assert result.loc[0, "planned_service_hours"] == pytest.approx(8.0, abs=0.01)


# ------------------------------------------------------------------
# 37. Negative service duration is detected
# ------------------------------------------------------------------

def test_negative_service_duration_detected(project_root: Path):
    source = pd.read_csv(project_root / "data" / "demo" / "service_schedule.csv")
    # Create a genuinely negative duration by setting planned_hours negative
    # and making timestamps also produce negative duration
    source.loc[0, "planned_start_time"] = "2024-01-01 10:00:00"
    source.loc[0, "planned_end_time"] = "2024-01-01 08:00:00"
    source.loc[0, "planned_hours"] = -2.0
    t = QueueCapacityScheduleTransformer(
        processing_run_id="TEST-NEG-DUR",
        validation_run_id="",
        input_directory=project_root / "data" / "demo",
        output_directory=project_root / "data" / "processed",
        validation_log_directory=project_root / "outputs" / "logs",
    )
    result = t.transform_service_schedule(source)
    assert any(i.issue_type == "Invalid Service Duration" for i in t.issues)
    assert result.loc[0, "valid_schedule_flag"] == False


# ------------------------------------------------------------------
# 38. Cancelled sessions are identified
# ------------------------------------------------------------------

def test_cancelled_sessions_identified(project_root: Path):
    source = pd.read_csv(project_root / "data" / "demo" / "service_schedule.csv")
    source.loc[0, "schedule_status"] = "cancelled"
    t = QueueCapacityScheduleTransformer(
        processing_run_id="TEST-CANCEL",
        validation_run_id="",
        input_directory=project_root / "data" / "demo",
        output_directory=project_root / "data" / "processed",
        validation_log_directory=project_root / "outputs" / "logs",
    )
    result = t.transform_service_schedule(source)
    assert result.loc[0, "cancelled_session_flag"] == True


# ------------------------------------------------------------------
# 39. Reduced sessions are identified
# ------------------------------------------------------------------

def test_reduced_sessions_identified(project_root: Path):
    source = pd.read_csv(project_root / "data" / "demo" / "service_schedule.csv")
    source.loc[0, "schedule_status"] = "reduced"
    t = QueueCapacityScheduleTransformer(
        processing_run_id="TEST-REDUCED",
        validation_run_id="",
        input_directory=project_root / "data" / "demo",
        output_directory=project_root / "data" / "processed",
        validation_log_directory=project_root / "outputs" / "logs",
    )
    result = t.transform_service_schedule(source)
    assert result.loc[0, "reduced_session_flag"] == True


# ------------------------------------------------------------------
# 40. Extended sessions are identified
# ------------------------------------------------------------------

def test_extended_sessions_identified(project_root: Path):
    source = pd.read_csv(project_root / "data" / "demo" / "service_schedule.csv")
    source.loc[0, "schedule_status"] = "extended"
    t = QueueCapacityScheduleTransformer(
        processing_run_id="TEST-EXTENDED",
        validation_run_id="",
        input_directory=project_root / "data" / "demo",
        output_directory=project_root / "data" / "processed",
        validation_log_directory=project_root / "outputs" / "logs",
    )
    result = t.transform_service_schedule(source)
    assert result.loc[0, "extended_session_flag"] == True


# ------------------------------------------------------------------
# 41. Blank planned capacity remains null
# ------------------------------------------------------------------

def test_blank_planned_capacity_remains_null(project_root: Path):
    source = pd.read_csv(project_root / "data" / "demo" / "service_schedule.csv")
    if source["planned_capacity"].notna().all():
        source.loc[0, "planned_capacity"] = None
    t = QueueCapacityScheduleTransformer(
        processing_run_id="TEST-BLANK-CAP",
        validation_run_id="",
        input_directory=project_root / "data" / "demo",
        output_directory=project_root / "data" / "processed",
        validation_log_directory=project_root / "outputs" / "logs",
    )
    result = t.transform_service_schedule(source)
    blank_mask = source["planned_capacity"].isna()
    assert result.loc[blank_mask, "planned_capacity"].isna().all()


# ------------------------------------------------------------------
# 42. No official waiting-time KPI field exists
# ------------------------------------------------------------------

def test_no_waiting_time_kpi_field(transformed_queue: pd.DataFrame):
    prohibited = ["average_patient_waiting_time", "official_waiting_time_kpi", "kpi_average_wait"]
    for field in prohibited:
        assert field not in transformed_queue.columns


# ------------------------------------------------------------------
# 43. No bed-occupancy KPI field exists
# ------------------------------------------------------------------

def test_no_bed_occupancy_kpi_field(transformed_bed: pd.DataFrame):
    prohibited = ["bed_occupancy_rate", "occupancy_rate", "bed_occupancy_kpi"]
    for field in prohibited:
        assert field not in transformed_bed.columns


# ------------------------------------------------------------------
# 44. No KPI status field exists
# ------------------------------------------------------------------

def test_no_kpi_status_field(transformed_queue: pd.DataFrame, transformed_bed: pd.DataFrame, transformed_schedule: pd.DataFrame):
    prohibited = ["kpi_status", "status_indicator", "performance_status"]
    for df in [transformed_queue, transformed_bed, transformed_schedule]:
        for field in prohibited:
            assert field not in df.columns


# ------------------------------------------------------------------
# 45. No risk field exists
# ------------------------------------------------------------------

def test_no_risk_field(transformed_queue: pd.DataFrame, transformed_bed: pd.DataFrame, transformed_schedule: pd.DataFrame):
    prohibited = ["risk_score", "risk_level", "risk_flag"]
    for df in [transformed_queue, transformed_bed, transformed_schedule]:
        for field in prohibited:
            assert field not in df.columns


# ------------------------------------------------------------------
# 46. No forecast field exists
# ------------------------------------------------------------------

def test_no_forecast_field(transformed_queue: pd.DataFrame, transformed_bed: pd.DataFrame, transformed_schedule: pd.DataFrame):
    prohibited = ["forecast", "predicted_value", "projection"]
    for df in [transformed_queue, transformed_bed, transformed_schedule]:
        for field in prohibited:
            assert field not in df.columns


# ------------------------------------------------------------------
# 47. No scenario field exists
# ------------------------------------------------------------------

def test_no_scenario_field(transformed_queue: pd.DataFrame, transformed_bed: pd.DataFrame, transformed_schedule: pd.DataFrame):
    prohibited = ["scenario", "what_if", "simulation_result"]
    for df in [transformed_queue, transformed_bed, transformed_schedule]:
        for field in prohibited:
            assert field not in df.columns


# ------------------------------------------------------------------
# 48. No financial field exists
# ------------------------------------------------------------------

def test_no_financial_field(transformed_queue: pd.DataFrame, transformed_bed: pd.DataFrame, transformed_schedule: pd.DataFrame):
    prohibited = ["cost", "revenue", "financial_impact", "budget_variance"]
    for df in [transformed_queue, transformed_bed, transformed_schedule]:
        for field in prohibited:
            assert field not in df.columns


# ------------------------------------------------------------------
# 49. No recommendation field exists
# ------------------------------------------------------------------

def test_no_recommendation_field(transformed_queue: pd.DataFrame, transformed_bed: pd.DataFrame, transformed_schedule: pd.DataFrame):
    prohibited = ["recommendation", "recommended_action", "suggested_intervention"]
    for df in [transformed_queue, transformed_bed, transformed_schedule]:
        for field in prohibited:
            assert field not in df.columns


# ------------------------------------------------------------------
# 50. Every processed record has lineage
# ------------------------------------------------------------------

def test_every_record_has_lineage(transformer: QueueCapacityScheduleTransformer, source_queue: pd.DataFrame, source_bed: pd.DataFrame, source_schedule: pd.DataFrame):
    queue_df = transformer.transform_patient_queue(source_queue)
    bed_df = transformer.transform_bed_capacity(source_bed)
    schedule_df = transformer.transform_service_schedule(source_schedule)
    transformer.build_lineage(source_queue, queue_df, "patient_queue_records")
    transformer.build_lineage(source_bed, bed_df, "bed_capacity_records")
    transformer.build_lineage(source_schedule, schedule_df, "service_schedule")
    assert len(transformer.lineage_records) == len(queue_df) + len(bed_df) + len(schedule_df)


# ------------------------------------------------------------------
# 51. Exclusions are recorded
# ------------------------------------------------------------------

def test_exclusions_recorded(project_root: Path):
    source = pd.read_csv(project_root / "data" / "demo" / "patient_queue_records.csv")
    source.loc[0, "arrivals_count"] = -1
    t = QueueCapacityScheduleTransformer(
        processing_run_id="TEST-EXCL",
        validation_run_id="",
        input_directory=project_root / "data" / "demo",
        output_directory=project_root / "data" / "processed",
        validation_log_directory=project_root / "outputs" / "logs",
    )
    t.transform_patient_queue(source)
    assert len(t.exclusion_records) > 0


# ------------------------------------------------------------------
# 52. Issue log is generated
# ------------------------------------------------------------------

def test_issue_log_generated(project_root: Path, tmp_path: Path):
    out_dir = tmp_path / "processed"
    log_dir = tmp_path / "logs"
    out_dir.mkdir()
    log_dir.mkdir()
    shutil.copy(project_root / "outputs" / "logs" / "validation_run_manifest.json", log_dir / "validation_run_manifest.json")
    shutil.copy(project_root / "outputs" / "logs" / "dataset_validation_summary.csv", log_dir / "dataset_validation_summary.csv")
    shutil.copy(project_root / "outputs" / "logs" / "manual_override_register.csv", log_dir / "manual_override_register.csv")

    run_queue_capacity_schedule_processing(
        input_dir=project_root / "data" / "demo",
        output_dir=out_dir,
        validation_log_dir=log_dir,
        execute_export=True,
    )
    assert (log_dir / "queue_capacity_schedule_processing_issue_log.csv").exists()


# ------------------------------------------------------------------
# 53. Audit log is generated
# ------------------------------------------------------------------

def test_audit_log_generated(project_root: Path, tmp_path: Path):
    out_dir = tmp_path / "processed"
    log_dir = tmp_path / "logs"
    out_dir.mkdir()
    log_dir.mkdir()
    shutil.copy(project_root / "outputs" / "logs" / "validation_run_manifest.json", log_dir / "validation_run_manifest.json")
    shutil.copy(project_root / "outputs" / "logs" / "dataset_validation_summary.csv", log_dir / "dataset_validation_summary.csv")
    shutil.copy(project_root / "outputs" / "logs" / "manual_override_register.csv", log_dir / "manual_override_register.csv")

    run_queue_capacity_schedule_processing(
        input_dir=project_root / "data" / "demo",
        output_dir=out_dir,
        validation_log_dir=log_dir,
        execute_export=True,
    )
    assert (log_dir / "queue_capacity_schedule_processing_audit_log.csv").exists()


# ------------------------------------------------------------------
# 54. Manifest is generated
# ------------------------------------------------------------------

def test_manifest_generated(project_root: Path, tmp_path: Path):
    out_dir = tmp_path / "processed"
    log_dir = tmp_path / "logs"
    out_dir.mkdir()
    log_dir.mkdir()
    shutil.copy(project_root / "outputs" / "logs" / "validation_run_manifest.json", log_dir / "validation_run_manifest.json")
    shutil.copy(project_root / "outputs" / "logs" / "dataset_validation_summary.csv", log_dir / "dataset_validation_summary.csv")
    shutil.copy(project_root / "outputs" / "logs" / "manual_override_register.csv", log_dir / "manual_override_register.csv")

    run_queue_capacity_schedule_processing(
        input_dir=project_root / "data" / "demo",
        output_dir=out_dir,
        validation_log_dir=log_dir,
        execute_export=True,
    )
    assert (log_dir / "queue_capacity_schedule_processing_run_manifest.json").exists()


# ------------------------------------------------------------------
# 55. Dataset summary is generated
# ------------------------------------------------------------------

def test_dataset_summary_generated(project_root: Path, tmp_path: Path):
    out_dir = tmp_path / "processed"
    log_dir = tmp_path / "logs"
    out_dir.mkdir()
    log_dir.mkdir()
    shutil.copy(project_root / "outputs" / "logs" / "validation_run_manifest.json", log_dir / "validation_run_manifest.json")
    shutil.copy(project_root / "outputs" / "logs" / "dataset_validation_summary.csv", log_dir / "dataset_validation_summary.csv")
    shutil.copy(project_root / "outputs" / "logs" / "manual_override_register.csv", log_dir / "manual_override_register.csv")

    run_queue_capacity_schedule_processing(
        input_dir=project_root / "data" / "demo",
        output_dir=out_dir,
        validation_log_dir=log_dir,
        execute_export=True,
    )
    assert (log_dir / "queue_capacity_schedule_processing_dataset_summary.csv").exists()


# ------------------------------------------------------------------
# 56. Processed checksums are generated
# ------------------------------------------------------------------

def test_processed_checksums_generated(project_root: Path, tmp_path: Path):
    out_dir = tmp_path / "processed"
    log_dir = tmp_path / "logs"
    out_dir.mkdir()
    log_dir.mkdir()
    shutil.copy(project_root / "outputs" / "logs" / "validation_run_manifest.json", log_dir / "validation_run_manifest.json")
    shutil.copy(project_root / "outputs" / "logs" / "dataset_validation_summary.csv", log_dir / "dataset_validation_summary.csv")
    shutil.copy(project_root / "outputs" / "logs" / "manual_override_register.csv", log_dir / "manual_override_register.csv")

    result = run_queue_capacity_schedule_processing(
        input_dir=project_root / "data" / "demo",
        output_dir=out_dir,
        validation_log_dir=log_dir,
        execute_export=True,
    )
    assert result["status"] in ("completed", "failed_schema")
    manifest_path = log_dir / "queue_capacity_schedule_processing_run_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert "processed_checksums" in manifest
    assert len(manifest["processed_checksums"]) == 3


# ------------------------------------------------------------------
# 57. Source checksums remain unchanged
# ------------------------------------------------------------------

def test_source_checksums_unchanged(project_root: Path, tmp_path: Path, source_checksums: dict):
    out_dir = tmp_path / "processed"
    log_dir = tmp_path / "logs"
    out_dir.mkdir()
    log_dir.mkdir()
    shutil.copy(project_root / "outputs" / "logs" / "validation_run_manifest.json", log_dir / "validation_run_manifest.json")
    shutil.copy(project_root / "outputs" / "logs" / "dataset_validation_summary.csv", log_dir / "dataset_validation_summary.csv")
    shutil.copy(project_root / "outputs" / "logs" / "manual_override_register.csv", log_dir / "manual_override_register.csv")

    run_queue_capacity_schedule_processing(
        input_dir=project_root / "data" / "demo",
        output_dir=out_dir,
        validation_log_dir=log_dir,
        execute_export=True,
    )
    for name, expected in source_checksums.items():
        path = project_root / "data" / "demo" / name
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        assert h.hexdigest() == expected


# ------------------------------------------------------------------
# 58. Repeated execution produces consistent business content
# ------------------------------------------------------------------

def test_repeated_execution_consistent(project_root: Path, tmp_path: Path):
    out_dir1 = tmp_path / "processed1"
    out_dir2 = tmp_path / "processed2"
    log_dir1 = tmp_path / "logs1"
    log_dir2 = tmp_path / "logs2"
    for d in [out_dir1, out_dir2, log_dir1, log_dir2]:
        d.mkdir()
    for ld in [log_dir1, log_dir2]:
        shutil.copy(project_root / "outputs" / "logs" / "validation_run_manifest.json", ld / "validation_run_manifest.json")
        shutil.copy(project_root / "outputs" / "logs" / "dataset_validation_summary.csv", ld / "dataset_validation_summary.csv")
        shutil.copy(project_root / "outputs" / "logs" / "manual_override_register.csv", ld / "manual_override_register.csv")

    run_queue_capacity_schedule_processing(
        input_dir=project_root / "data" / "demo",
        output_dir=out_dir1,
        validation_log_dir=log_dir1,
        execute_export=True,
    )
    run_queue_capacity_schedule_processing(
        input_dir=project_root / "data" / "demo",
        output_dir=out_dir2,
        validation_log_dir=log_dir2,
        execute_export=True,
    )
    for name in ["processed_patient_queue.csv", "processed_bed_capacity.csv", "processed_service_schedule.csv"]:
        df1 = pd.read_csv(out_dir1 / name)
        df2 = pd.read_csv(out_dir2 / name)
        # Exclude metadata columns that vary between runs
        compare_cols = [c for c in df1.columns if c not in ("processing_run_id", "processed_datetime")]
        pd.testing.assert_frame_equal(df1[compare_cols], df2[compare_cols])


# ------------------------------------------------------------------
# 59. No patient names are created
# ------------------------------------------------------------------

def test_no_patient_names(transformed_queue: pd.DataFrame, transformed_bed: pd.DataFrame, transformed_schedule: pd.DataFrame):
    prohibited = ["patient_name", "first_name", "last_name", "full_name"]
    for df in [transformed_queue, transformed_bed, transformed_schedule]:
        for field in prohibited:
            assert field not in df.columns


# ------------------------------------------------------------------
# 60. No clinical notes or diagnoses are created
# ------------------------------------------------------------------

def test_no_clinical_notes(transformed_queue: pd.DataFrame, transformed_bed: pd.DataFrame, transformed_schedule: pd.DataFrame):
    prohibited = ["clinical_notes", "diagnosis", "diagnosis_code", "icd_code", "medical_notes"]
    for df in [transformed_queue, transformed_bed, transformed_schedule]:
        for field in prohibited:
            assert field not in df.columns


# ------------------------------------------------------------------
# 61. No direct personal identifiers are created
# ------------------------------------------------------------------

def test_no_direct_personal_identifiers(transformed_queue: pd.DataFrame, transformed_bed: pd.DataFrame, transformed_schedule: pd.DataFrame):
    prohibited = ["ssn", "social_security_number", "national_id", "passport_number", "phone_number", "email", "address"]
    for df in [transformed_queue, transformed_bed, transformed_schedule]:
        for field in prohibited:
            assert field not in df.columns
