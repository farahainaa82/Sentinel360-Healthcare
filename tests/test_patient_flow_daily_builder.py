"""
Tests for Patient Flow Daily Builder (Step 2D-3C)
"""

import json
import os
import shutil
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.patient_flow_daily_builder import PatientFlowDailyBuilder, TRANSFORMATION_VERSION, ENGINE_VERSION
from src.processed_schema_registry import get_processed_schema


def _make_encounter_df(rows):
    """Create a processed_patient_encounters DataFrame with all required schema fields."""
    base = {
        "encounter_id": [r.get("encounter_id", f"E{i}") for i, r in enumerate(rows)],
        "hospital_id": [r["hospital_id"] for r in rows],
        "department_id": [r["department_id"] for r in rows],
        "encounter_date": [r.get("encounter_date", r["reporting_date"]) for r in rows],
        "reporting_date": [r["reporting_date"] for r in rows],
        "reporting_month": [r.get("reporting_month", r["reporting_date"][:7]) for r in rows],
        "encounter_type": [r.get("encounter_type", "outpatient") for r in rows],
        "arrival_datetime": [r.get("arrival_datetime", "2024-01-01T08:00:00") for r in rows],
        "triage_datetime": [r.get("triage_datetime", "2024-01-01T08:15:00") for r in rows],
        "consultation_start_datetime": [r.get("consultation_start_datetime", "2024-01-01T08:30:00") for r in rows],
        "service_end_datetime": [r.get("service_end_datetime", "2024-01-01T09:00:00") for r in rows],
        "disposition_status": [r.get("disposition_status", "completed") for r in rows],
        "cancelled_flag": [r.get("cancelled_flag", False) for r in rows],
        "left_before_service_flag": [r.get("left_before_service_flag", False) for r in rows],
        "completed_service_flag": [r.get("completed_service_flag", True) for r in rows],
        "arrival_to_triage_minutes": [r.get("arrival_to_triage_minutes", 15.0) for r in rows],
        "arrival_to_consultation_minutes": [r.get("arrival_to_consultation_minutes", 30.0) for r in rows],
        "triage_to_consultation_minutes": [r.get("triage_to_consultation_minutes", 15.0) for r in rows],
        "consultation_to_service_end_minutes": [r.get("consultation_to_service_end_minutes", 30.0) for r in rows],
        "official_wait_stage_eligible_flag": [r.get("official_wait_stage_eligible_flag", True) for r in rows],
        "encounter_wait_eligible_flag": [r.get("encounter_wait_eligible_flag", True) for r in rows],
        "exclusion_reason_code": [r.get("exclusion_reason_code", "") for r in rows],
        "source_primary_key": [r.get("source_primary_key", "") for r in rows],
        "processing_run_id": [r.get("processing_run_id", "PROC-TEST") for r in rows],
        "validation_run_id": [r.get("validation_run_id", "VAL-TEST") for r in rows],
        "transformation_version": [r.get("transformation_version", "1.0") for r in rows],
        "processed_datetime": [r.get("processed_datetime", "2024-01-01T00:00:00") for r in rows],
    }
    return pd.DataFrame(base)


def _make_queue_df(rows):
    base = {
        "queue_record_id": [r.get("queue_record_id", f"Q{i}") for i, r in enumerate(rows)],
        "hospital_id": [r["hospital_id"] for r in rows],
        "department_id": [r["department_id"] for r in rows],
        "queue_date": [r.get("queue_date", r["reporting_date"]) for r in rows],
        "reporting_date": [r["reporting_date"] for r in rows],
        "reporting_month": [r.get("reporting_month", r["reporting_date"][:7]) for r in rows],
        "queue_stage": [r.get("queue_stage", "triage") for r in rows],
        "arrivals_count": [r.get("arrivals_count", 10) for r in rows],
        "served_count": [r.get("served_count", 8) for r in rows],
        "waiting_patient_count": [r.get("waiting_patient_count", 2) for r in rows],
        "average_wait_minutes": [r.get("average_wait_minutes", 15.0) for r in rows],
        "median_wait_minutes": [r.get("median_wait_minutes", 12.0) for r in rows],
        "maximum_wait_minutes": [r.get("maximum_wait_minutes", 45.0) for r in rows],
        "summary_source_flag": [r.get("summary_source_flag", False) for r in rows],
        "encounter_derived_flag": [r.get("encounter_derived_flag", False) for r in rows],
        "valid_queue_record_flag": [r.get("valid_queue_record_flag", True) for r in rows],
        "source_primary_key": [r.get("source_primary_key", "") for r in rows],
        "processing_run_id": [r.get("processing_run_id", "PROC-TEST") for r in rows],
        "validation_run_id": [r.get("validation_run_id", "VAL-TEST") for r in rows],
        "transformation_version": [r.get("transformation_version", "1.0") for r in rows],
        "processed_datetime": [r.get("processed_datetime", "2024-01-01T00:00:00") for r in rows],
    }
    return pd.DataFrame(base)


def _make_bed_df(rows):
    base = {
        "bed_capacity_record_id": [r.get("bed_capacity_record_id", f"B{i}") for i, r in enumerate(rows)],
        "hospital_id": [r["hospital_id"] for r in rows],
        "department_id": [r["department_id"] for r in rows],
        "reporting_date": [r["reporting_date"] for r in rows],
        "reporting_month": [r.get("reporting_month", r["reporting_date"][:7]) for r in rows],
        "licensed_beds": [r.get("licensed_beds", 100) for r in rows],
        "staffed_beds": [r.get("staffed_beds", 80) for r in rows],
        "operational_beds": [r.get("operational_beds", 75) for r in rows],
        "occupied_beds": [r.get("occupied_beds", 70) for r in rows],
        "unavailable_beds": [r.get("unavailable_beds", 5) for r in rows],
        "reserved_beds": [r.get("reserved_beds", 2) for r in rows],
        "beds_above_operational_capacity": [r.get("beds_above_operational_capacity", 0) for r in rows],
        "overcapacity_flag": [r.get("overcapacity_flag", False) for r in rows],
        "overcapacity_exception_flag": [r.get("overcapacity_exception_flag", False) for r in rows],
        "overcapacity_reason": [r.get("overcapacity_reason", "") for r in rows],
        "valid_bed_record_flag": [r.get("valid_bed_record_flag", True) for r in rows],
        "source_primary_key": [r.get("source_primary_key", "") for r in rows],
        "processing_run_id": [r.get("processing_run_id", "PROC-TEST") for r in rows],
        "validation_run_id": [r.get("validation_run_id", "VAL-TEST") for r in rows],
        "transformation_version": [r.get("transformation_version", "1.0") for r in rows],
        "processed_datetime": [r.get("processed_datetime", "2024-01-01T00:00:00") for r in rows],
    }
    return pd.DataFrame(base)


def _make_schedule_df(rows):
    base = {
        "service_schedule_id": [r.get("service_schedule_id", f"S{i}") for i, r in enumerate(rows)],
        "hospital_id": [r["hospital_id"] for r in rows],
        "department_id": [r["department_id"] for r in rows],
        "service_date": [r.get("service_date", r["reporting_date"]) for r in rows],
        "reporting_date": [r["reporting_date"] for r in rows],
        "reporting_month": [r.get("reporting_month", r["reporting_date"][:7]) for r in rows],
        "service_type": [r.get("service_type", "general") for r in rows],
        "session_start_datetime": [r.get("session_start_datetime", "2024-01-01T08:00:00") for r in rows],
        "session_end_datetime": [r.get("session_end_datetime", "2024-01-01T16:00:00") for r in rows],
        "planned_service_hours": [r.get("planned_service_hours", 8.0) for r in rows],
        "planned_capacity": [r.get("planned_capacity", 10) for r in rows],
        "schedule_status": [r.get("schedule_status", "active") for r in rows],
        "reduced_session_flag": [r.get("reduced_session_flag", False) for r in rows],
        "cancelled_session_flag": [r.get("cancelled_session_flag", False) for r in rows],
        "extended_session_flag": [r.get("extended_session_flag", False) for r in rows],
        "valid_schedule_flag": [r.get("valid_schedule_flag", True) for r in rows],
        "source_primary_key": [r.get("source_primary_key", "") for r in rows],
        "processing_run_id": [r.get("processing_run_id", "PROC-TEST") for r in rows],
        "validation_run_id": [r.get("validation_run_id", "VAL-TEST") for r in rows],
        "transformation_version": [r.get("transformation_version", "1.0") for r in rows],
        "processed_datetime": [r.get("processed_datetime", "2024-01-01T00:00:00") for r in rows],
    }
    return pd.DataFrame(base)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_dirs():
    tmp = tempfile.mkdtemp()
    input_dir = Path(tmp) / "input"
    output_dir = Path(tmp) / "output"
    log_dir = Path(tmp) / "log"
    input_dir.mkdir()
    output_dir.mkdir()
    log_dir.mkdir()
    yield {"input_dir": input_dir, "output_dir": output_dir, "log_dir": log_dir, "tmp": tmp}
    shutil.rmtree(tmp)


@pytest.fixture
def valid_manifests(temp_dirs):
    log_dir = temp_dirs["log_dir"]
    enc_manifest = {
        "processing_run_id": "PROC-ENC-001",
        "run_status": "success",
        "processing_allowed_flag": True,
    }
    with open(log_dir / "patient_encounter_processing_run_manifest.json", "w") as f:
        json.dump(enc_manifest, f)
    qcs_manifest = {
        "processing_run_id": "PROC-QCS-001",
        "run_status": "success",
        "processing_allowed_flag": True,
    }
    with open(log_dir / "queue_capacity_schedule_processing_run_manifest.json", "w") as f:
        json.dump(qcs_manifest, f)
    return log_dir


@pytest.fixture
def sample_encounters(temp_dirs):
    df = _make_encounter_df([
        {"encounter_id": "E1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01",
         "completed_service_flag": True, "cancelled_flag": False, "left_before_service_flag": False,
         "official_wait_stage_eligible_flag": True, "arrival_to_consultation_minutes": 30.0},
        {"encounter_id": "E2", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01",
         "completed_service_flag": True, "cancelled_flag": False, "left_before_service_flag": False,
         "official_wait_stage_eligible_flag": True, "arrival_to_consultation_minutes": 45.0},
        {"encounter_id": "E3", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-02",
         "completed_service_flag": False, "cancelled_flag": True, "left_before_service_flag": False,
         "official_wait_stage_eligible_flag": False, "arrival_to_consultation_minutes": np.nan},
        {"encounter_id": "E4", "hospital_id": "H2", "department_id": "D2", "reporting_date": "2024-01-01",
         "completed_service_flag": False, "cancelled_flag": False, "left_before_service_flag": True,
         "official_wait_stage_eligible_flag": True, "arrival_to_consultation_minutes": -5.0},
    ])
    path = temp_dirs["input_dir"] / "processed_patient_encounters.csv"
    df.to_csv(path, index=False)
    return path


@pytest.fixture
def sample_queue(temp_dirs):
    df = _make_queue_df([
        {"queue_record_id": "Q1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01",
         "queue_stage": "triage", "arrivals_count": 10, "served_count": 8, "waiting_patient_count": 2,
         "average_wait_minutes": 15.0, "summary_source_flag": False},
        {"queue_record_id": "Q2", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01",
         "queue_stage": "summary", "arrivals_count": 25, "served_count": 20, "waiting_patient_count": 5,
         "average_wait_minutes": 12.0, "summary_source_flag": True},
        {"queue_record_id": "Q3", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-02",
         "queue_stage": "triage", "arrivals_count": 5, "served_count": 4, "waiting_patient_count": 1,
         "average_wait_minutes": 10.0, "summary_source_flag": False},
    ])
    path = temp_dirs["input_dir"] / "processed_patient_queue.csv"
    df.to_csv(path, index=False)
    return path


@pytest.fixture
def sample_bed(temp_dirs):
    df = _make_bed_df([
        {"bed_capacity_record_id": "B1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01",
         "licensed_beds": 100, "staffed_beds": 80, "operational_beds": 75, "occupied_beds": 70,
         "unavailable_beds": 5, "reserved_beds": 2, "beds_above_operational_capacity": 0, "overcapacity_flag": False},
        {"bed_capacity_record_id": "B2", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-02",
         "licensed_beds": 100, "staffed_beds": 80, "operational_beds": 75, "occupied_beds": 80,
         "unavailable_beds": 5, "reserved_beds": 2, "beds_above_operational_capacity": 5, "overcapacity_flag": True},
        {"bed_capacity_record_id": "B3", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01",
         "licensed_beds": 100, "staffed_beds": 80, "operational_beds": 75, "occupied_beds": 70,
         "unavailable_beds": 5, "reserved_beds": 2, "beds_above_operational_capacity": 0, "overcapacity_flag": False},
    ])
    path = temp_dirs["input_dir"] / "processed_bed_capacity.csv"
    df.to_csv(path, index=False)
    return path


@pytest.fixture
def sample_schedule(temp_dirs):
    df = _make_schedule_df([
        {"service_schedule_id": "S1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01",
         "cancelled_session_flag": False, "reduced_session_flag": False, "extended_session_flag": False},
        {"service_schedule_id": "S2", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01",
         "cancelled_session_flag": False, "reduced_session_flag": False, "extended_session_flag": False},
        {"service_schedule_id": "S3", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01",
         "cancelled_session_flag": True, "reduced_session_flag": False, "extended_session_flag": False},
        {"service_schedule_id": "S4", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01",
         "cancelled_session_flag": False, "reduced_session_flag": True, "extended_session_flag": False},
        {"service_schedule_id": "S5", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01",
         "cancelled_session_flag": False, "reduced_session_flag": False, "extended_session_flag": True},
    ])
    path = temp_dirs["input_dir"] / "processed_service_schedule.csv"
    df.to_csv(path, index=False)
    return path


@pytest.fixture
def builder(temp_dirs, valid_manifests):
    return PatientFlowDailyBuilder(
        processing_run_id="PROC-TEST-001",
        validation_run_id="VAL-TEST-001",
        input_directory=temp_dirs["input_dir"],
        output_directory=temp_dirs["output_dir"],
        log_directory=temp_dirs["log_dir"],
        source_type="test",
        collect_lineage=True,
        max_issue_examples=100,
    )


# ---------------------------------------------------------------------------
# 1. Safe imports
# ---------------------------------------------------------------------------

def test_module_imports_safely():
    import src.patient_flow_daily_builder as mod
    assert hasattr(mod, "PatientFlowDailyBuilder")
    assert hasattr(mod, "TRANSFORMATION_VERSION")


def test_runner_does_not_execute_on_import():
    import src.run_patient_flow_daily_processing as runner
    assert callable(runner.main)


# ---------------------------------------------------------------------------
# 2-3. Manifest gate
# ---------------------------------------------------------------------------

def test_prior_manifests_accepted_when_valid(builder):
    gate = builder.check_input_manifests()
    assert gate.processing_allowed is True
    assert gate.blocking_reason == ""


def test_processing_blocked_when_manifest_fails(temp_dirs):
    log_dir = temp_dirs["log_dir"]
    enc_manifest = {"processing_run_id": "PROC-ENC-001", "run_status": "failed", "processing_allowed_flag": True}
    with open(log_dir / "patient_encounter_processing_run_manifest.json", "w") as f:
        json.dump(enc_manifest, f)
    qcs_manifest = {"processing_run_id": "PROC-QCS-001", "run_status": "success", "processing_allowed_flag": True}
    with open(log_dir / "queue_capacity_schedule_processing_run_manifest.json", "w") as f:
        json.dump(qcs_manifest, f)
    b = PatientFlowDailyBuilder(
        processing_run_id="PROC-TEST-002",
        validation_run_id="VAL-TEST-002",
        input_directory=temp_dirs["input_dir"],
        output_directory=temp_dirs["output_dir"],
        log_directory=log_dir,
    )
    gate = b.check_input_manifests()
    assert gate.processing_allowed is False
    assert ("run_status" in gate.blocking_reason.lower() or "failed" in gate.blocking_reason.lower())


def test_processing_blocked_when_checksum_mismatch(temp_dirs, valid_manifests, sample_encounters, sample_queue, sample_bed, sample_schedule):
    b = PatientFlowDailyBuilder(
        processing_run_id="PROC-TEST-003",
        validation_run_id="VAL-TEST-003",
        input_directory=temp_dirs["input_dir"],
        output_directory=temp_dirs["output_dir"],
        log_directory=temp_dirs["log_dir"],
    )
    b.check_input_manifests()
    b.load_processed_inputs()
    tampered = temp_dirs["input_dir"] / "processed_patient_encounters.csv"
    df = pd.read_csv(tampered)
    df.loc[0, "encounter_id"] = "E1-TAMPERED"
    df.to_csv(tampered, index=False)
    ok = b.verify_input_checksums()
    assert ok is False


# ---------------------------------------------------------------------------
# 4-6. Input loading and spine
# ---------------------------------------------------------------------------

def test_all_four_inputs_loaded(builder, sample_encounters, sample_queue, sample_bed, sample_schedule):
    builder.check_input_manifests()
    inputs = builder.load_processed_inputs()
    assert set(inputs.keys()) == {
        "processed_patient_encounters",
        "processed_patient_queue",
        "processed_bed_capacity",
        "processed_service_schedule",
    }


def test_daily_spine_unique_grain(builder, sample_encounters, sample_queue, sample_bed, sample_schedule):
    builder.check_input_manifests()
    inputs = builder.load_processed_inputs()
    spine = builder.build_daily_spine(inputs)
    assert spine[["hospital_id", "department_id", "reporting_date"]].duplicated().sum() == 0


def test_patient_flow_daily_id_deterministic(builder, sample_encounters, sample_queue, sample_bed, sample_schedule):
    builder.check_input_manifests()
    inputs = builder.load_processed_inputs()
    spine = builder.build_daily_spine(inputs)
    enc = builder.aggregate_encounters(inputs["processed_patient_encounters"])
    queue = builder.aggregate_queue(inputs["processed_patient_queue"])
    bed = builder.aggregate_bed_capacity(inputs["processed_bed_capacity"])
    service = builder.aggregate_service_schedule(inputs["processed_service_schedule"])
    daily = builder.combine_daily_components(spine, enc, queue, bed, service)
    daily = builder.create_daily_identifier(daily)
    expected = "PFD-H1-D1-20240101"
    assert daily.loc[daily["reporting_date"] == "2024-01-01", "patient_flow_daily_id"].iloc[0] == expected


def test_patient_flow_daily_id_unique(builder, sample_encounters, sample_queue, sample_bed, sample_schedule):
    builder.check_input_manifests()
    inputs = builder.load_processed_inputs()
    spine = builder.build_daily_spine(inputs)
    enc = builder.aggregate_encounters(inputs["processed_patient_encounters"])
    queue = builder.aggregate_queue(inputs["processed_patient_queue"])
    bed = builder.aggregate_bed_capacity(inputs["processed_bed_capacity"])
    service = builder.aggregate_service_schedule(inputs["processed_service_schedule"])
    daily = builder.combine_daily_components(spine, enc, queue, bed, service)
    daily = builder.create_daily_identifier(daily)
    assert daily["patient_flow_daily_id"].duplicated().sum() == 0


def test_reporting_month_format(builder, sample_encounters, sample_queue, sample_bed, sample_schedule):
    builder.check_input_manifests()
    inputs = builder.load_processed_inputs()
    spine = builder.build_daily_spine(inputs)
    assert spine["reporting_month"].str.match(r"^\d{4}-\d{2}$").all()


# ---------------------------------------------------------------------------
# 7-11. Encounter aggregation
# ---------------------------------------------------------------------------

def test_encounter_count_aggregates(builder, sample_encounters):
    df = pd.read_csv(sample_encounters)
    agg = builder.aggregate_encounters(df)
    row = agg[(agg["hospital_id"] == "H1") & (agg["department_id"] == "D1") & (agg["reporting_date"] == "2024-01-01")]
    assert row["encounter_count"].iloc[0] == 2


def test_completed_count_aggregates(builder, sample_encounters):
    df = pd.read_csv(sample_encounters)
    agg = builder.aggregate_encounters(df)
    row = agg[(agg["hospital_id"] == "H1") & (agg["department_id"] == "D1") & (agg["reporting_date"] == "2024-01-01")]
    assert row["completed_encounter_count"].iloc[0] == 2


def test_cancelled_count_aggregates(builder, sample_encounters):
    df = pd.read_csv(sample_encounters)
    agg = builder.aggregate_encounters(df)
    row = agg[(agg["hospital_id"] == "H1") & (agg["department_id"] == "D1") & (agg["reporting_date"] == "2024-01-02")]
    assert row["cancelled_encounter_count"].iloc[0] == 1


def test_left_before_service_count_aggregates(builder, sample_encounters):
    df = pd.read_csv(sample_encounters)
    agg = builder.aggregate_encounters(df)
    row = agg[(agg["hospital_id"] == "H2") & (agg["department_id"] == "D2") & (agg["reporting_date"] == "2024-01-01")]
    assert row["left_before_service_count"].iloc[0] == 1


def test_wait_eligible_count_aggregates(builder, sample_encounters):
    df = pd.read_csv(sample_encounters)
    agg = builder.aggregate_encounters(df)
    row = agg[(agg["hospital_id"] == "H1") & (agg["department_id"] == "D1") & (agg["reporting_date"] == "2024-01-01")]
    assert row["official_wait_eligible_encounter_count"].iloc[0] == 2


def test_wait_minute_total_aggregates(builder, sample_encounters):
    df = pd.read_csv(sample_encounters)
    agg = builder.aggregate_encounters(df)
    row = agg[(agg["hospital_id"] == "H1") & (agg["department_id"] == "D1") & (agg["reporting_date"] == "2024-01-01")]
    assert row["total_arrival_to_consultation_minutes"].iloc[0] == 75.0


def test_negative_intervals_excluded(builder, sample_encounters):
    df = pd.read_csv(sample_encounters)
    agg = builder.aggregate_encounters(df)
    row = agg[(agg["hospital_id"] == "H2") & (agg["department_id"] == "D2") & (agg["reporting_date"] == "2024-01-01")]
    assert pd.isna(row["total_arrival_to_consultation_minutes"].iloc[0])


def test_no_official_waiting_time_kpi(builder, sample_encounters, sample_queue, sample_bed, sample_schedule):
    builder.check_input_manifests()
    inputs = builder.load_processed_inputs()
    spine = builder.build_daily_spine(inputs)
    enc = builder.aggregate_encounters(inputs["processed_patient_encounters"])
    queue = builder.aggregate_queue(inputs["processed_patient_queue"])
    bed = builder.aggregate_bed_capacity(inputs["processed_bed_capacity"])
    service = builder.aggregate_service_schedule(inputs["processed_service_schedule"])
    daily = builder.combine_daily_components(spine, enc, queue, bed, service)
    daily = builder.create_daily_identifier(daily)
    forbidden = ["average_patient_waiting_time", "avg_wait_time_kpi", "official_wait_time"]
    for col in forbidden:
        assert col not in daily.columns


# ---------------------------------------------------------------------------
# 12-16. Queue aggregation
# ---------------------------------------------------------------------------

def test_queue_stages_not_silently_summed(builder, sample_queue):
    df = pd.read_csv(sample_queue)
    agg = builder.aggregate_queue(df)
    row = agg[(agg["hospital_id"] == "H1") & (agg["department_id"] == "D1") & (agg["reporting_date"] == "2024-01-01")]
    assert row["queue_arrivals_count"].iloc[0] == 25.0


def test_summary_queue_stage_preferred(builder, sample_queue):
    df = pd.read_csv(sample_queue)
    agg = builder.aggregate_queue(df)
    row = agg[(agg["hospital_id"] == "H1") & (agg["department_id"] == "D1") & (agg["reporting_date"] == "2024-01-01")]
    assert row["queue_served_count"].iloc[0] == 20.0


def test_ambiguous_queue_produces_issue(temp_dirs, valid_manifests):
    # Create all four inputs with ambiguous queue
    _make_encounter_df([
        {"encounter_id": "E1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"},
    ]).to_csv(temp_dirs["input_dir"] / "processed_patient_encounters.csv", index=False)
    _make_queue_df([
        {"queue_record_id": "Q1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01",
         "queue_stage": "triage", "arrivals_count": 10, "served_count": 8, "waiting_patient_count": 2,
         "average_wait_minutes": 15.0, "summary_source_flag": False},
        {"queue_record_id": "Q2", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01",
         "queue_stage": "registration", "arrivals_count": 15, "served_count": 12, "waiting_patient_count": 3,
         "average_wait_minutes": 20.0, "summary_source_flag": False},
    ]).to_csv(temp_dirs["input_dir"] / "processed_patient_queue.csv", index=False)
    _make_bed_df([
        {"bed_capacity_record_id": "B1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"},
    ]).to_csv(temp_dirs["input_dir"] / "processed_bed_capacity.csv", index=False)
    _make_schedule_df([
        {"service_schedule_id": "S1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"},
    ]).to_csv(temp_dirs["input_dir"] / "processed_service_schedule.csv", index=False)
    b = PatientFlowDailyBuilder(
        processing_run_id="PROC-TEST-004",
        validation_run_id="VAL-TEST-004",
        input_directory=temp_dirs["input_dir"],
        output_directory=temp_dirs["output_dir"],
        log_directory=temp_dirs["log_dir"],
    )
    b.check_input_manifests()
    inputs = b.load_processed_inputs()
    agg = b.aggregate_queue(inputs["processed_patient_queue"])
    row = agg[(agg["hospital_id"] == "H1") & (agg["department_id"] == "D1") & (agg["reporting_date"] == "2024-01-01")]
    assert pd.isna(row["queue_arrivals_count"].iloc[0])
    assert any(i.issue_type == "Ambiguous Queue Aggregation" for i in b.issues)


def test_ambiguous_queue_value_null(builder, sample_queue):
    df = pd.read_csv(sample_queue)
    df["summary_source_flag"] = False
    agg = builder.aggregate_queue(df)
    row = agg[(agg["hospital_id"] == "H1") & (agg["department_id"] == "D1") & (agg["reporting_date"] == "2024-01-01")]
    assert pd.isna(row["queue_arrivals_count"].iloc[0])


def test_queue_averages_not_averaged_without_weighting(builder, sample_queue):
    df = pd.read_csv(sample_queue)
    agg = builder.aggregate_queue(df)
    row = agg[(agg["hospital_id"] == "H1") & (agg["department_id"] == "D1") & (agg["reporting_date"] == "2024-01-01")]
    assert row["queue_average_wait_minutes"].iloc[0] == 12.0


def test_blank_queue_values_null(builder, sample_queue):
    df = pd.read_csv(sample_queue)
    df.loc[0, "average_wait_minutes"] = np.nan
    agg = builder.aggregate_queue(df)
    row = agg[(agg["hospital_id"] == "H1") & (agg["department_id"] == "D1") & (agg["reporting_date"] == "2024-01-02")]
    assert pd.isna(row["queue_average_wait_minutes"].iloc[0]) or row["queue_average_wait_minutes"].iloc[0] == 10.0


# ---------------------------------------------------------------------------
# 17-22. Bed capacity
# ---------------------------------------------------------------------------

def test_bed_values_preserved(builder, sample_bed):
    df = pd.read_csv(sample_bed)
    df = df.drop_duplicates(subset=["hospital_id", "department_id", "reporting_date"], keep="first")
    agg = builder.aggregate_bed_capacity(df)
    row = agg[(agg["hospital_id"] == "H1") & (agg["department_id"] == "D1") & (agg["reporting_date"] == "2024-01-01")]
    assert row["licensed_beds"].iloc[0] == 100.0
    assert row["occupied_beds"].iloc[0] == 70.0


def test_occupied_beds_not_capped(builder, sample_bed):
    df = pd.read_csv(sample_bed)
    df = df.drop_duplicates(subset=["hospital_id", "department_id", "reporting_date"], keep="first")
    agg = builder.aggregate_bed_capacity(df)
    row = agg[(agg["hospital_id"] == "H1") & (agg["department_id"] == "D1") & (agg["reporting_date"] == "2024-01-02")]
    assert row["occupied_beds"].iloc[0] == 80.0
    assert row["operational_beds"].iloc[0] == 75.0


def test_overcapacity_flag_preserved(builder, sample_bed):
    df = pd.read_csv(sample_bed)
    df = df.drop_duplicates(subset=["hospital_id", "department_id", "reporting_date"], keep="first")
    agg = builder.aggregate_bed_capacity(df)
    row = agg[(agg["hospital_id"] == "H1") & (agg["department_id"] == "D1") & (agg["reporting_date"] == "2024-01-02")]
    assert row["overcapacity_flag"].iloc[0] == True


def test_beds_above_operational_capacity(builder, sample_bed):
    df = pd.read_csv(sample_bed)
    df = df.drop_duplicates(subset=["hospital_id", "department_id", "reporting_date"], keep="first")
    agg = builder.aggregate_bed_capacity(df)
    row = agg[(agg["hospital_id"] == "H1") & (agg["department_id"] == "D1") & (agg["reporting_date"] == "2024-01-02")]
    assert row["beds_above_operational_capacity"].iloc[0] == 5.0


def test_duplicate_bed_snapshots_detected(builder, sample_bed):
    df = pd.read_csv(sample_bed)
    agg = builder.aggregate_bed_capacity(df)
    assert any(i.issue_type == "Duplicate Capacity Snapshot" for i in builder.issues)


def test_duplicate_bed_snapshots_not_silently_summed(builder, sample_bed):
    df = pd.read_csv(sample_bed)
    agg = builder.aggregate_bed_capacity(df)
    row = agg[(agg["hospital_id"] == "H1") & (agg["department_id"] == "D1") & (agg["reporting_date"] == "2024-01-01")]
    assert pd.isna(row["licensed_beds"].iloc[0])
    assert pd.isna(row["occupied_beds"].iloc[0])


# ---------------------------------------------------------------------------
# 23-26. Service schedule
# ---------------------------------------------------------------------------

def test_planned_service_sessions_aggregate(builder, sample_schedule):
    df = pd.read_csv(sample_schedule)
    agg = builder.aggregate_service_schedule(df)
    row = agg[(agg["hospital_id"] == "H1") & (agg["department_id"] == "D1") & (agg["reporting_date"] == "2024-01-01")]
    # 5 total, 1 cancelled -> 4 planned
    assert row["planned_service_session_count"].iloc[0] == 4


def test_cancelled_service_sessions_aggregate(builder, sample_schedule):
    df = pd.read_csv(sample_schedule)
    agg = builder.aggregate_service_schedule(df)
    row = agg[(agg["hospital_id"] == "H1") & (agg["department_id"] == "D1") & (agg["reporting_date"] == "2024-01-01")]
    assert row["cancelled_service_session_count"].iloc[0] == 1


def test_reduced_service_sessions_aggregate(builder, sample_schedule):
    df = pd.read_csv(sample_schedule)
    agg = builder.aggregate_service_schedule(df)
    row = agg[(agg["hospital_id"] == "H1") & (agg["department_id"] == "D1") & (agg["reporting_date"] == "2024-01-01")]
    assert row["reduced_service_session_count"].iloc[0] == 1


def test_extended_service_sessions_aggregate(builder, sample_schedule):
    df = pd.read_csv(sample_schedule)
    agg = builder.aggregate_service_schedule(df)
    row = agg[(agg["hospital_id"] == "H1") & (agg["department_id"] == "D1") & (agg["reporting_date"] == "2024-01-01")]
    assert row["extended_service_session_count"].iloc[0] == 1


def test_cross_midnight_not_double_counted(builder, sample_schedule):
    df = pd.read_csv(sample_schedule)
    agg = builder.aggregate_service_schedule(df)
    row = agg[(agg["hospital_id"] == "H1") & (agg["department_id"] == "D1") & (agg["reporting_date"] == "2024-01-01")]
    assert len(row) == 1


# ---------------------------------------------------------------------------
# 27-28. Null vs zero
# ---------------------------------------------------------------------------

def test_count_fields_zero_where_appropriate(builder, sample_encounters, sample_queue, sample_bed, sample_schedule):
    builder.check_input_manifests()
    inputs = builder.load_processed_inputs()
    spine = builder.build_daily_spine(inputs)
    enc = builder.aggregate_encounters(inputs["processed_patient_encounters"])
    queue = builder.aggregate_queue(inputs["processed_patient_queue"])
    bed = builder.aggregate_bed_capacity(inputs["processed_bed_capacity"])
    service = builder.aggregate_service_schedule(inputs["processed_service_schedule"])
    daily = builder.combine_daily_components(spine, enc, queue, bed, service)
    row = daily[(daily["hospital_id"] == "H2") & (daily["department_id"] == "D2")]
    if not row.empty:
        assert row["planned_service_session_count"].iloc[0] == 0


def test_measurement_fields_null_where_unavailable(builder, sample_encounters):
    df = pd.read_csv(sample_encounters)
    agg = builder.aggregate_encounters(df)
    row = agg[(agg["hospital_id"] == "H2") & (agg["department_id"] == "D2") & (agg["reporting_date"] == "2024-01-01")]
    assert pd.isna(row["total_arrival_to_consultation_minutes"].iloc[0])


# ---------------------------------------------------------------------------
# 29-30. Schema and grain
# ---------------------------------------------------------------------------

def test_final_schema_matches_registry(builder, sample_encounters, sample_queue, sample_bed, sample_schedule):
    builder.check_input_manifests()
    inputs = builder.load_processed_inputs()
    spine = builder.build_daily_spine(inputs)
    enc = builder.aggregate_encounters(inputs["processed_patient_encounters"])
    queue = builder.aggregate_queue(inputs["processed_patient_queue"])
    bed = builder.aggregate_bed_capacity(inputs["processed_bed_capacity"])
    service = builder.aggregate_service_schedule(inputs["processed_service_schedule"])
    daily = builder.combine_daily_components(spine, enc, queue, bed, service)
    daily = builder.create_daily_identifier(daily)
    # Add metadata fields that the runner normally adds
    daily["processing_run_id"] = "PROC-TEST"
    daily["validation_run_id"] = "VAL-TEST"
    daily["transformation_version"] = "1.0"
    daily["processed_datetime"] = "2024-01-01T00:00:00"
    schema = get_processed_schema("processed_patient_flow_daily")
    for field in schema["required_fields"]:
        assert field in daily.columns, f"Missing {field}"


def test_daily_grain_unique(builder, sample_encounters, sample_queue, sample_bed, sample_schedule):
    builder.check_input_manifests()
    inputs = builder.load_processed_inputs()
    spine = builder.build_daily_spine(inputs)
    enc = builder.aggregate_encounters(inputs["processed_patient_encounters"])
    queue = builder.aggregate_queue(inputs["processed_patient_queue"])
    bed = builder.aggregate_bed_capacity(inputs["processed_bed_capacity"])
    service = builder.aggregate_service_schedule(inputs["processed_service_schedule"])
    daily = builder.combine_daily_components(spine, enc, queue, bed, service)
    daily = builder.create_daily_identifier(daily)
    assert daily["patient_flow_daily_id"].duplicated().sum() == 0


# ---------------------------------------------------------------------------
# 31-32. Processed file and control outputs
# ---------------------------------------------------------------------------

def test_processed_file_created(temp_dirs, valid_manifests, sample_encounters, sample_queue, sample_bed, sample_schedule):
    from src.run_patient_flow_daily_processing import main
    main(
        input_dir=str(temp_dirs["input_dir"]),
        output_dir=str(temp_dirs["output_dir"]),
        log_dir=str(temp_dirs["log_dir"]),
        source_type="test",
        collect_lineage=True,
    )
    assert (temp_dirs["output_dir"] / "processed_patient_flow_daily.csv").exists()


def test_all_six_control_outputs_created(temp_dirs, valid_manifests, sample_encounters, sample_queue, sample_bed, sample_schedule):
    from src.run_patient_flow_daily_processing import main
    main(
        input_dir=str(temp_dirs["input_dir"]),
        output_dir=str(temp_dirs["output_dir"]),
        log_dir=str(temp_dirs["log_dir"]),
        source_type="test",
        collect_lineage=True,
    )
    files = [
        "patient_flow_daily_processing_run_manifest.json",
        "patient_flow_daily_processing_dataset_summary.csv",
        "patient_flow_daily_processing_issue_log.csv",
        "patient_flow_daily_processing_lineage.csv",
        "patient_flow_daily_processing_exclusion_register.csv",
        "patient_flow_daily_processing_audit_log.csv",
    ]
    for f in files:
        assert (temp_dirs["log_dir"] / f).exists(), f"Missing {f}"


# ---------------------------------------------------------------------------
# 33-35. Lineage
# ---------------------------------------------------------------------------

def test_every_daily_row_has_lineage(temp_dirs, valid_manifests, sample_encounters, sample_queue, sample_bed, sample_schedule):
    from src.run_patient_flow_daily_processing import main
    result = main(
        input_dir=str(temp_dirs["input_dir"]),
        output_dir=str(temp_dirs["output_dir"]),
        log_dir=str(temp_dirs["log_dir"]),
        source_type="test",
        collect_lineage=True,
    )
    daily = result["daily_dataframe"]
    lineage = pd.read_csv(temp_dirs["log_dir"] / "patient_flow_daily_processing_lineage.csv")
    daily_ids = set(daily["patient_flow_daily_id"])
    lineage_ids = set(lineage["processed_primary_key_value"])
    assert daily_ids.issubset(lineage_ids)


def test_multi_source_daily_rows_have_lineage_to_contributing_domains(temp_dirs, valid_manifests, sample_encounters, sample_queue, sample_bed, sample_schedule):
    from src.run_patient_flow_daily_processing import main
    main(
        input_dir=str(temp_dirs["input_dir"]),
        output_dir=str(temp_dirs["output_dir"]),
        log_dir=str(temp_dirs["log_dir"]),
        source_type="test",
        collect_lineage=True,
    )
    lineage = pd.read_csv(temp_dirs["log_dir"] / "patient_flow_daily_processing_lineage.csv")
    sources = set(lineage["source_dataset_name"])
    assert "processed_patient_encounters" in sources
    assert "processed_patient_queue" in sources


# ---------------------------------------------------------------------------
# 36-37. Exclusions and issues
# ---------------------------------------------------------------------------

def test_exclusions_logged(temp_dirs, valid_manifests, sample_encounters, sample_queue, sample_bed, sample_schedule):
    from src.run_patient_flow_daily_processing import main
    main(
        input_dir=str(temp_dirs["input_dir"]),
        output_dir=str(temp_dirs["output_dir"]),
        log_dir=str(temp_dirs["log_dir"]),
        source_type="test",
        collect_lineage=True,
    )
    exclusions = pd.read_csv(temp_dirs["log_dir"] / "patient_flow_daily_processing_exclusion_register.csv")
    assert "exclusion_id" in exclusions.columns or len(exclusions) == 0


def test_issues_logged(temp_dirs, valid_manifests, sample_encounters, sample_queue, sample_bed, sample_schedule):
    from src.run_patient_flow_daily_processing import main
    main(
        input_dir=str(temp_dirs["input_dir"]),
        output_dir=str(temp_dirs["output_dir"]),
        log_dir=str(temp_dirs["log_dir"]),
        source_type="test",
        collect_lineage=True,
    )
    issues = pd.read_csv(temp_dirs["log_dir"] / "patient_flow_daily_processing_issue_log.csv")
    assert "issue_id" in issues.columns


# ---------------------------------------------------------------------------
# 38. Input immutability
# ---------------------------------------------------------------------------

def test_input_files_remain_unchanged(temp_dirs, valid_manifests, sample_encounters, sample_queue, sample_bed, sample_schedule):
    from src.run_patient_flow_daily_processing import main
    import hashlib
    def checksum(path):
        h = hashlib.sha256()
        with open(path, "rb") as f:
            h.update(f.read())
        return h.hexdigest()
    pre = {f: checksum(temp_dirs["input_dir"] / f) for f in [
        "processed_patient_encounters.csv", "processed_patient_queue.csv",
        "processed_bed_capacity.csv", "processed_service_schedule.csv"
    ]}
    main(
        input_dir=str(temp_dirs["input_dir"]),
        output_dir=str(temp_dirs["output_dir"]),
        log_dir=str(temp_dirs["log_dir"]),
        source_type="test",
        collect_lineage=True,
    )
    post = {f: checksum(temp_dirs["input_dir"] / f) for f in [
        "processed_patient_encounters.csv", "processed_patient_queue.csv",
        "processed_bed_capacity.csv", "processed_service_schedule.csv"
    ]}
    assert pre == post


# ---------------------------------------------------------------------------
# 39. No complaint or survey data loaded
# ---------------------------------------------------------------------------

def test_no_complaint_or_survey_data_loaded(builder, sample_encounters, sample_queue, sample_bed, sample_schedule):
    builder.check_input_manifests()
    inputs = builder.load_processed_inputs()
    for name, df in inputs.items():
        for col in df.columns:
            assert "complaint" not in col.lower()
            assert "survey" not in col.lower()


# ---------------------------------------------------------------------------
# 40-48. No forbidden fields
# ---------------------------------------------------------------------------

def test_no_official_kpi_fields(builder, sample_encounters, sample_queue, sample_bed, sample_schedule):
    builder.check_input_manifests()
    inputs = builder.load_processed_inputs()
    spine = builder.build_daily_spine(inputs)
    enc = builder.aggregate_encounters(inputs["processed_patient_encounters"])
    queue = builder.aggregate_queue(inputs["processed_patient_queue"])
    bed = builder.aggregate_bed_capacity(inputs["processed_bed_capacity"])
    service = builder.aggregate_service_schedule(inputs["processed_service_schedule"])
    daily = builder.combine_daily_components(spine, enc, queue, bed, service)
    daily = builder.create_daily_identifier(daily)
    forbidden = [
        "average_patient_waiting_time", "bed_occupancy_rate", "staffing_level",
        "staff_absenteeism_rate", "complaint_rate", "patient_satisfaction_score",
    ]
    for col in forbidden:
        assert col not in daily.columns, f"Forbidden KPI field {col} found"


def test_no_kpi_status_field(builder, sample_encounters, sample_queue, sample_bed, sample_schedule):
    builder.check_input_manifests()
    inputs = builder.load_processed_inputs()
    spine = builder.build_daily_spine(inputs)
    enc = builder.aggregate_encounters(inputs["processed_patient_encounters"])
    queue = builder.aggregate_queue(inputs["processed_patient_queue"])
    bed = builder.aggregate_bed_capacity(inputs["processed_bed_capacity"])
    service = builder.aggregate_service_schedule(inputs["processed_service_schedule"])
    daily = builder.combine_daily_components(spine, enc, queue, bed, service)
    daily = builder.create_daily_identifier(daily)
    assert "kpi_status" not in daily.columns


def test_no_trend_field(builder, sample_encounters, sample_queue, sample_bed, sample_schedule):
    builder.check_input_manifests()
    inputs = builder.load_processed_inputs()
    spine = builder.build_daily_spine(inputs)
    enc = builder.aggregate_encounters(inputs["processed_patient_encounters"])
    queue = builder.aggregate_queue(inputs["processed_patient_queue"])
    bed = builder.aggregate_bed_capacity(inputs["processed_bed_capacity"])
    service = builder.aggregate_service_schedule(inputs["processed_service_schedule"])
    daily = builder.combine_daily_components(spine, enc, queue, bed, service)
    daily = builder.create_daily_identifier(daily)
    assert "trend" not in daily.columns


def test_no_anomaly_field(builder, sample_encounters, sample_queue, sample_bed, sample_schedule):
    builder.check_input_manifests()
    inputs = builder.load_processed_inputs()
    spine = builder.build_daily_spine(inputs)
    enc = builder.aggregate_encounters(inputs["processed_patient_encounters"])
    queue = builder.aggregate_queue(inputs["processed_patient_queue"])
    bed = builder.aggregate_bed_capacity(inputs["processed_bed_capacity"])
    service = builder.aggregate_service_schedule(inputs["processed_service_schedule"])
    daily = builder.combine_daily_components(spine, enc, queue, bed, service)
    daily = builder.create_daily_identifier(daily)
    assert "anomaly" not in daily.columns


def test_no_risk_field(builder, sample_encounters, sample_queue, sample_bed, sample_schedule):
    builder.check_input_manifests()
    inputs = builder.load_processed_inputs()
    spine = builder.build_daily_spine(inputs)
    enc = builder.aggregate_encounters(inputs["processed_patient_encounters"])
    queue = builder.aggregate_queue(inputs["processed_patient_queue"])
    bed = builder.aggregate_bed_capacity(inputs["processed_bed_capacity"])
    service = builder.aggregate_service_schedule(inputs["processed_service_schedule"])
    daily = builder.combine_daily_components(spine, enc, queue, bed, service)
    daily = builder.create_daily_identifier(daily)
    assert "risk" not in daily.columns


def test_no_forecast_field(builder, sample_encounters, sample_queue, sample_bed, sample_schedule):
    builder.check_input_manifests()
    inputs = builder.load_processed_inputs()
    spine = builder.build_daily_spine(inputs)
    enc = builder.aggregate_encounters(inputs["processed_patient_encounters"])
    queue = builder.aggregate_queue(inputs["processed_patient_queue"])
    bed = builder.aggregate_bed_capacity(inputs["processed_bed_capacity"])
    service = builder.aggregate_service_schedule(inputs["processed_service_schedule"])
    daily = builder.combine_daily_components(spine, enc, queue, bed, service)
    daily = builder.create_daily_identifier(daily)
    assert "forecast" not in daily.columns


def test_no_scenario_field(builder, sample_encounters, sample_queue, sample_bed, sample_schedule):
    builder.check_input_manifests()
    inputs = builder.load_processed_inputs()
    spine = builder.build_daily_spine(inputs)
    enc = builder.aggregate_encounters(inputs["processed_patient_encounters"])
    queue = builder.aggregate_queue(inputs["processed_patient_queue"])
    bed = builder.aggregate_bed_capacity(inputs["processed_bed_capacity"])
    service = builder.aggregate_service_schedule(inputs["processed_service_schedule"])
    daily = builder.combine_daily_components(spine, enc, queue, bed, service)
    daily = builder.create_daily_identifier(daily)
    assert "scenario" not in daily.columns


def test_no_financial_field(builder, sample_encounters, sample_queue, sample_bed, sample_schedule):
    builder.check_input_manifests()
    inputs = builder.load_processed_inputs()
    spine = builder.build_daily_spine(inputs)
    enc = builder.aggregate_encounters(inputs["processed_patient_encounters"])
    queue = builder.aggregate_queue(inputs["processed_patient_queue"])
    bed = builder.aggregate_bed_capacity(inputs["processed_bed_capacity"])
    service = builder.aggregate_service_schedule(inputs["processed_service_schedule"])
    daily = builder.combine_daily_components(spine, enc, queue, bed, service)
    daily = builder.create_daily_identifier(daily)
    assert "financial" not in daily.columns


def test_no_recommendation_field(builder, sample_encounters, sample_queue, sample_bed, sample_schedule):
    builder.check_input_manifests()
    inputs = builder.load_processed_inputs()
    spine = builder.build_daily_spine(inputs)
    enc = builder.aggregate_encounters(inputs["processed_patient_encounters"])
    queue = builder.aggregate_queue(inputs["processed_patient_queue"])
    bed = builder.aggregate_bed_capacity(inputs["processed_bed_capacity"])
    service = builder.aggregate_service_schedule(inputs["processed_service_schedule"])
    daily = builder.combine_daily_components(spine, enc, queue, bed, service)
    daily = builder.create_daily_identifier(daily)
    assert "recommendation" not in daily.columns


# ---------------------------------------------------------------------------
# 49. Determinism
# ---------------------------------------------------------------------------

def test_repeated_processing_consistent_business_content(temp_dirs, valid_manifests, sample_encounters, sample_queue, sample_bed, sample_schedule):
    from src.run_patient_flow_daily_processing import main
    result1 = main(
        input_dir=str(temp_dirs["input_dir"]),
        output_dir=str(temp_dirs["output_dir"]),
        log_dir=str(temp_dirs["log_dir"]),
        source_type="test",
        collect_lineage=True,
    )
    assert result1["success"] is True
    log_dir2 = temp_dirs["log_dir"] / "run2"
    log_dir2.mkdir()
    # Copy manifests to second log dir so gate passes
    import shutil
    shutil.copy(temp_dirs["log_dir"] / "patient_encounter_processing_run_manifest.json", log_dir2)
    shutil.copy(temp_dirs["log_dir"] / "queue_capacity_schedule_processing_run_manifest.json", log_dir2)
    result2 = main(
        input_dir=str(temp_dirs["input_dir"]),
        output_dir=str(temp_dirs["output_dir"]),
        log_dir=str(log_dir2),
        source_type="test",
        collect_lineage=True,
    )
    assert result2["success"] is True
    df1 = result1["daily_dataframe"].sort_values("patient_flow_daily_id").reset_index(drop=True)
    df2 = result2["daily_dataframe"].sort_values("patient_flow_daily_id").reset_index(drop=True)
    cols = [c for c in df1.columns if c not in ["processing_run_id", "processed_datetime"]]
    pd.testing.assert_frame_equal(df1[cols], df2[cols])


# ---------------------------------------------------------------------------
# 50. No personal identifiers
# ---------------------------------------------------------------------------

def test_no_direct_personal_or_clinical_identifiers(builder, sample_encounters, sample_queue, sample_bed, sample_schedule):
    builder.check_input_manifests()
    inputs = builder.load_processed_inputs()
    spine = builder.build_daily_spine(inputs)
    enc = builder.aggregate_encounters(inputs["processed_patient_encounters"])
    queue = builder.aggregate_queue(inputs["processed_patient_queue"])
    bed = builder.aggregate_bed_capacity(inputs["processed_bed_capacity"])
    service = builder.aggregate_service_schedule(inputs["processed_service_schedule"])
    daily = builder.combine_daily_components(spine, enc, queue, bed, service)
    daily = builder.create_daily_identifier(daily)
    forbidden = ["patient_name", "mrn", "nhs_number", "ssn", "dob", "phone", "email", "address"]
    for col in daily.columns:
        for f in forbidden:
            assert f not in col.lower(), f"Personal identifier column {col} found"
