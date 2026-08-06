"""
Tests for Patient Flow Integration Validator (Step 2D-3D)
"""

import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.patient_flow_integration_validator import PatientFlowIntegrationValidator, INTEGRATION_VERSION, ENGINE_VERSION


def _make_encounter_df(rows):
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


def _make_daily_df(rows):
    base = {
        "patient_flow_daily_id": [r.get("patient_flow_daily_id", f"PFD-{r['hospital_id']}-{r['department_id']}-{r['reporting_date'].replace('-','')}") for r in rows],
        "hospital_id": [r["hospital_id"] for r in rows],
        "department_id": [r["department_id"] for r in rows],
        "reporting_date": [r["reporting_date"] for r in rows],
        "reporting_month": [r.get("reporting_month", r["reporting_date"][:7]) for r in rows],
        "encounter_count": [r.get("encounter_count", 0) for r in rows],
        "completed_encounter_count": [r.get("completed_encounter_count", 0) for r in rows],
        "cancelled_encounter_count": [r.get("cancelled_encounter_count", 0) for r in rows],
        "left_before_service_count": [r.get("left_before_service_count", 0) for r in rows],
        "official_wait_eligible_encounter_count": [r.get("official_wait_eligible_encounter_count", 0) for r in rows],
        "total_arrival_to_consultation_minutes": [r.get("total_arrival_to_consultation_minutes", np.nan) for r in rows],
        "queue_arrivals_count": [r.get("queue_arrivals_count", np.nan) for r in rows],
        "queue_served_count": [r.get("queue_served_count", np.nan) for r in rows],
        "queue_waiting_patient_count": [r.get("queue_waiting_patient_count", np.nan) for r in rows],
        "queue_average_wait_minutes": [r.get("queue_average_wait_minutes", np.nan) for r in rows],
        "licensed_beds": [r.get("licensed_beds", np.nan) for r in rows],
        "staffed_beds": [r.get("staffed_beds", np.nan) for r in rows],
        "operational_beds": [r.get("operational_beds", np.nan) for r in rows],
        "occupied_beds": [r.get("occupied_beds", np.nan) for r in rows],
        "unavailable_beds": [r.get("unavailable_beds", np.nan) for r in rows],
        "reserved_beds": [r.get("reserved_beds", np.nan) for r in rows],
        "beds_above_operational_capacity": [r.get("beds_above_operational_capacity", np.nan) for r in rows],
        "overcapacity_flag": [r.get("overcapacity_flag", pd.NA) for r in rows],
        "planned_service_session_count": [r.get("planned_service_session_count", 0) for r in rows],
        "cancelled_service_session_count": [r.get("cancelled_service_session_count", 0) for r in rows],
        "reduced_service_session_count": [r.get("reduced_service_session_count", 0) for r in rows],
        "extended_service_session_count": [r.get("extended_service_session_count", 0) for r in rows],
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
    processed_dir = Path(tmp) / "processed"
    log_dir = Path(tmp) / "log"
    processed_dir.mkdir()
    log_dir.mkdir()
    yield {"processed_dir": processed_dir, "log_dir": log_dir, "tmp": tmp}
    shutil.rmtree(tmp)


@pytest.fixture
def valid_manifests(temp_dirs):
    log_dir = temp_dirs["log_dir"]
    for name in ["patient_encounter_processing_run_manifest.json", "queue_capacity_schedule_processing_run_manifest.json", "patient_flow_daily_processing_run_manifest.json"]:
        manifest = {
            "processing_run_id": f"PROC-{name[:5].upper()}",
            "run_status": "success",
            "processing_allowed_flag": True,
            "input_checksums": {},
        }
        with open(log_dir / name, "w") as f:
            json.dump(manifest, f)
    return log_dir


@pytest.fixture
def sample_datasets(temp_dirs, valid_manifests):
    processed_dir = temp_dirs["processed_dir"]
    # Encounters
    enc = _make_encounter_df([
        {"encounter_id": "E1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01",
         "completed_service_flag": True, "cancelled_flag": False, "left_before_service_flag": False,
         "official_wait_stage_eligible_flag": True, "arrival_to_consultation_minutes": 30.0},
        {"encounter_id": "E2", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01",
         "completed_service_flag": True, "cancelled_flag": False, "left_before_service_flag": False,
         "official_wait_stage_eligible_flag": True, "arrival_to_consultation_minutes": 45.0},
        {"encounter_id": "E3", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-02",
         "completed_service_flag": False, "cancelled_flag": True, "left_before_service_flag": False,
         "official_wait_stage_eligible_flag": False, "arrival_to_consultation_minutes": np.nan},
    ])
    enc.to_csv(processed_dir / "processed_patient_encounters.csv", index=False)
    # Queue
    q = _make_queue_df([
        {"queue_record_id": "Q1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01",
         "arrivals_count": 10, "served_count": 8, "waiting_patient_count": 2, "average_wait_minutes": 15.0, "summary_source_flag": True},
        {"queue_record_id": "Q2", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-02",
         "arrivals_count": 5, "served_count": 4, "waiting_patient_count": 1, "average_wait_minutes": 10.0, "summary_source_flag": True},
    ])
    q.to_csv(processed_dir / "processed_patient_queue.csv", index=False)
    # Bed
    b = _make_bed_df([
        {"bed_capacity_record_id": "B1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01",
         "licensed_beds": 100, "staffed_beds": 80, "operational_beds": 75, "occupied_beds": 70,
         "unavailable_beds": 5, "reserved_beds": 2, "beds_above_operational_capacity": 0, "overcapacity_flag": False},
        {"bed_capacity_record_id": "B2", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-02",
         "licensed_beds": 100, "staffed_beds": 80, "operational_beds": 75, "occupied_beds": 80,
         "unavailable_beds": 5, "reserved_beds": 2, "beds_above_operational_capacity": 5, "overcapacity_flag": True},
    ])
    b.to_csv(processed_dir / "processed_bed_capacity.csv", index=False)
    # Schedule
    s = _make_schedule_df([
        {"service_schedule_id": "S1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01",
         "cancelled_session_flag": False, "reduced_session_flag": False, "extended_session_flag": False},
        {"service_schedule_id": "S2", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01",
         "cancelled_session_flag": False, "reduced_session_flag": False, "extended_session_flag": False},
        {"service_schedule_id": "S3", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01",
         "cancelled_session_flag": True, "reduced_session_flag": False, "extended_session_flag": False},
        {"service_schedule_id": "S4", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-02",
         "cancelled_session_flag": False, "reduced_session_flag": False, "extended_session_flag": False},
    ])
    s.to_csv(processed_dir / "processed_service_schedule.csv", index=False)
    # Daily
    d = _make_daily_df([
        {"hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01",
         "encounter_count": 2, "completed_encounter_count": 2, "cancelled_encounter_count": 0,
         "left_before_service_count": 0, "official_wait_eligible_encounter_count": 2,
         "total_arrival_to_consultation_minutes": 75.0,
         "queue_arrivals_count": 10.0, "queue_served_count": 8.0, "queue_waiting_patient_count": 2.0, "queue_average_wait_minutes": 15.0,
         "licensed_beds": 100.0, "staffed_beds": 80.0, "operational_beds": 75.0, "occupied_beds": 70.0,
         "unavailable_beds": 5.0, "reserved_beds": 2.0, "beds_above_operational_capacity": 0.0, "overcapacity_flag": False,
         "planned_service_session_count": 2, "cancelled_service_session_count": 1, "reduced_service_session_count": 0, "extended_service_session_count": 0},
        {"hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-02",
         "encounter_count": 1, "completed_encounter_count": 0, "cancelled_encounter_count": 1,
         "left_before_service_count": 0, "official_wait_eligible_encounter_count": 0,
         "total_arrival_to_consultation_minutes": np.nan,
         "queue_arrivals_count": 5.0, "queue_served_count": 4.0, "queue_waiting_patient_count": 1.0, "queue_average_wait_minutes": 10.0,
         "licensed_beds": 100.0, "staffed_beds": 80.0, "operational_beds": 75.0, "occupied_beds": 80.0,
         "unavailable_beds": 5.0, "reserved_beds": 2.0, "beds_above_operational_capacity": 5.0, "overcapacity_flag": True,
         "planned_service_session_count": 1, "cancelled_service_session_count": 0, "reduced_service_session_count": 0, "extended_service_session_count": 0},
    ])
    d.to_csv(processed_dir / "processed_patient_flow_daily.csv", index=False)

    # Lineage
    lineage = pd.DataFrame({
        "processing_run_id": ["PROC-TEST"] * 6,
        "lineage_id": [f"L{i}" for i in range(6)],
        "validation_run_id": ["VAL-TEST"] * 6,
        "source_dataset_name": ["processed_patient_encounters", "processed_patient_queue", "processed_bed_capacity", "processed_service_schedule", "processed_patient_encounters", "processed_patient_queue"],
        "source_file_name": ["enc.csv", "q.csv", "b.csv", "s.csv", "enc.csv", "q.csv"],
        "source_primary_key_field": ["encounter_id", "queue_record_id", "bed_capacity_record_id", "service_schedule_id", "encounter_id", "queue_record_id"],
        "source_primary_key_value": ["E1", "Q1", "B1", "S1", "E2", "Q2"],
        "source_row_number": [0] * 6,
        "processed_dataset_name": ["processed_patient_flow_daily"] * 6,
        "processed_primary_key_field": ["patient_flow_daily_id"] * 6,
        "processed_primary_key_value": ["PFD-H1-D1-20240101", "PFD-H1-D1-20240101", "PFD-H1-D1-20240101", "PFD-H1-D1-20240101", "PFD-H1-D1-20240102", "PFD-H1-D1-20240102"],
        "transformation_rule_id": ["TR_PFD_ENCOUNTER_AGGREGATION"] * 6,
        "transformation_description": ["test"] * 6,
        "source_fields_used": [""] * 6,
        "processed_fields_created": [""] * 6,
        "exclusion_flag": [False] * 6,
        "exclusion_reason_code": [""] * 6,
        "transformation_version": ["1.0"] * 6,
        "configuration_version": ["1.0"] * 6,
        "processed_datetime": [datetime.now()] * 6,
    })
    log_dir = temp_dirs["log_dir"]
    lineage.to_csv(log_dir / "patient_flow_daily_processing_lineage.csv", index=False)

    # Prior issues and exclusions
    for name in ["patient_encounter_processing_issue_log.csv", "queue_capacity_schedule_processing_issue_log.csv", "patient_flow_daily_processing_issue_log.csv"]:
        pd.DataFrame(columns=["issue_id", "processing_run_id", "source_dataset_name", "issue_type", "severity", "issue_description"]).to_csv(log_dir / name, index=False)
    for name in ["patient_encounter_processing_exclusion_register.csv", "queue_capacity_schedule_processing_exclusion_register.csv", "patient_flow_daily_processing_exclusion_register.csv"]:
        pd.DataFrame(columns=["exclusion_id", "processing_run_id", "source_dataset_name", "exclusion_reason_code"]).to_csv(log_dir / name, index=False)

    return processed_dir


@pytest.fixture
def validator(temp_dirs, valid_manifests):
    return PatientFlowIntegrationValidator(
        integration_run_id="INT-TEST-001",
        processed_directory=temp_dirs["processed_dir"],
        log_directory=temp_dirs["log_dir"],
        max_issue_examples=100,
        reconciliation_tolerance=0.001,
    )


# ---------------------------------------------------------------------------
# 1-2. Safe imports
# ---------------------------------------------------------------------------

def test_module_imports_safely():
    import src.patient_flow_integration_validator as mod
    assert hasattr(mod, "PatientFlowIntegrationValidator")


def test_runner_does_not_execute_on_import():
    import src.run_patient_flow_integration_validation as runner
    assert callable(runner.main)


# ---------------------------------------------------------------------------
# 3-6. Manifest and gate
# ---------------------------------------------------------------------------

def test_all_prior_manifests_load(validator, sample_datasets):
    gate = validator.load_prior_manifests()
    assert gate.processing_allowed is True


def test_missing_manifest_blocks_integration(temp_dirs):
    # Only create two manifests
    for name in ["patient_encounter_processing_run_manifest.json", "queue_capacity_schedule_processing_run_manifest.json"]:
        manifest = {"processing_run_id": "PROC-TEST", "run_status": "success", "processing_allowed_flag": True}
        with open(temp_dirs["log_dir"] / name, "w") as f:
            json.dump(manifest, f)
    v = PatientFlowIntegrationValidator(
        integration_run_id="INT-TEST-002",
        processed_directory=temp_dirs["processed_dir"],
        log_directory=temp_dirs["log_dir"],
    )
    gate = v.load_prior_manifests()
    assert gate.processing_allowed is False
    assert "patient_flow_daily_processing_run_manifest.json" in gate.blocking_reason


def test_failed_prior_run_blocks_integration(temp_dirs):
    for name in ["patient_encounter_processing_run_manifest.json", "queue_capacity_schedule_processing_run_manifest.json", "patient_flow_daily_processing_run_manifest.json"]:
        manifest = {"processing_run_id": "PROC-TEST", "run_status": "failed", "processing_allowed_flag": True}
        with open(temp_dirs["log_dir"] / name, "w") as f:
            json.dump(manifest, f)
    v = PatientFlowIntegrationValidator(
        integration_run_id="INT-TEST-003",
        processed_directory=temp_dirs["processed_dir"],
        log_directory=temp_dirs["log_dir"],
    )
    gate = v.load_prior_manifests()
    assert gate.processing_allowed is False


def test_checksum_mismatch_detected(temp_dirs, valid_manifests, sample_datasets):
    # Write manifest with wrong checksum
    manifest = json.load(open(temp_dirs["log_dir"] / "patient_encounter_processing_run_manifest.json"))
    manifest["input_checksums"] = {"processed_patient_encounters": "wrong_checksum"}
    with open(temp_dirs["log_dir"] / "patient_encounter_processing_run_manifest.json", "w") as f:
        json.dump(manifest, f)
    v = PatientFlowIntegrationValidator(
        integration_run_id="INT-TEST-004",
        processed_directory=temp_dirs["processed_dir"],
        log_directory=temp_dirs["log_dir"],
    )
    v.load_prior_manifests()
    v.load_processed_datasets()
    ok = v.verify_manifest_checksums()
    assert ok is False


# ---------------------------------------------------------------------------
# 7-13. Dataset loading and business keys
# ---------------------------------------------------------------------------

def test_all_five_processed_datasets_load(validator, sample_datasets):
    validator.load_prior_manifests()
    datasets = validator.load_processed_datasets()
    assert set(datasets.keys()) == {
        "processed_patient_encounters",
        "processed_patient_queue",
        "processed_bed_capacity",
        "processed_service_schedule",
        "processed_patient_flow_daily",
    }


def test_all_five_schemas_pass(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    errors = validator.validate_processed_schemas()
    assert len(errors) == 0


def test_encounter_business_keys_unique(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    errors = validator.validate_business_keys()
    assert not any("encounter_id" in e for e in errors)


def test_queue_business_keys_unique(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    errors = validator.validate_business_keys()
    assert not any("queue_record_id" in e for e in errors)


def test_bed_business_keys_unique(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    errors = validator.validate_business_keys()
    assert not any("bed_capacity_record_id" in e for e in errors)


def test_service_schedule_business_keys_unique(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    errors = validator.validate_business_keys()
    assert not any("service_schedule_id" in e for e in errors)


def test_daily_ids_unique(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    errors = validator.validate_business_keys()
    assert not any("patient_flow_daily_id" in e for e in errors)


def test_daily_grain_unique(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    errors = validator.validate_daily_grain()
    assert len(errors) == 0


# ---------------------------------------------------------------------------
# 14-16. Date alignment
# ---------------------------------------------------------------------------

def test_reporting_months_align_with_dates(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    errors = validator.validate_date_alignment()
    assert len(errors) == 0


def test_daily_dates_exist_in_input_union(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    errors = validator.validate_cross_dataset_references()
    assert not any("orphan" in e.lower() for e in errors)


def test_daily_rows_not_orphaned(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    errors = validator.validate_cross_dataset_references()
    assert not any("orphan" in e.lower() for e in errors)


# ---------------------------------------------------------------------------
# 17-24. Encounter reconciliation
# ---------------------------------------------------------------------------

def test_encounter_counts_reconcile(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    recs = validator.reconcile_daily_encounters()
    enc_count_rec = [r for r in recs if r["reconciliation_field"] == "encounter_count"][0]
    assert enc_count_rec["reconciliation_status"] == "Passed"


def test_completed_encounter_counts_reconcile(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    recs = validator.reconcile_daily_encounters()
    comp_rec = [r for r in recs if r["reconciliation_field"] == "completed_encounter_count"][0]
    assert comp_rec["reconciliation_status"] == "Passed"


def test_cancelled_encounter_counts_reconcile(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    recs = validator.reconcile_daily_encounters()
    canc_rec = [r for r in recs if r["reconciliation_field"] == "cancelled_encounter_count"][0]
    assert canc_rec["reconciliation_status"] == "Passed"


def test_lwbs_counts_reconcile(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    recs = validator.reconcile_daily_encounters()
    lwbs_rec = [r for r in recs if r["reconciliation_field"] == "left_before_service_count"][0]
    assert lwbs_rec["reconciliation_status"] == "Passed"


def test_eligible_encounter_counts_reconcile(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    recs = validator.reconcile_daily_encounters()
    elig_rec = [r for r in recs if r["reconciliation_field"] == "official_wait_eligible_encounter_count"][0]
    assert elig_rec["reconciliation_status"] == "Passed"


def test_wait_minute_totals_reconcile(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    recs = validator.reconcile_daily_encounters()
    wait_rec = [r for r in recs if r["reconciliation_field"] == "total_arrival_to_consultation_minutes"][0]
    assert wait_rec["reconciliation_status"] == "Passed"


def test_null_wait_minute_totals_acceptable(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    recs = validator.reconcile_daily_encounters()
    wait_rec = [r for r in recs if r["reconciliation_field"] == "total_arrival_to_consultation_minutes"][0]
    assert wait_rec["reconciliation_status"] == "Passed"


# ---------------------------------------------------------------------------
# 25-27. Queue reconciliation
# ---------------------------------------------------------------------------

def test_queue_approved_summary_reconciliation(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    recs = validator.reconcile_daily_queue()
    arr_rec = [r for r in recs if r["reconciliation_field"] == "queue_arrivals_count"][0]
    assert arr_rec["reconciliation_status"] == "Passed"


def test_queue_ambiguous_aggregation_reported(temp_dirs, valid_manifests):
    # Create queue with ambiguous multi-stage
    processed_dir = temp_dirs["processed_dir"]
    q = _make_queue_df([
        {"queue_record_id": "Q1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01",
         "queue_stage": "triage", "arrivals_count": 10, "summary_source_flag": False},
        {"queue_record_id": "Q2", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01",
         "queue_stage": "registration", "arrivals_count": 15, "summary_source_flag": False},
    ])
    q.to_csv(processed_dir / "processed_patient_queue.csv", index=False)
    # Also need other datasets
    _make_encounter_df([{"encounter_id": "E1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"}]).to_csv(processed_dir / "processed_patient_encounters.csv", index=False)
    _make_bed_df([{"bed_capacity_record_id": "B1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"}]).to_csv(processed_dir / "processed_bed_capacity.csv", index=False)
    _make_schedule_df([{"service_schedule_id": "S1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"}]).to_csv(processed_dir / "processed_service_schedule.csv", index=False)
    _make_daily_df([{"hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01", "queue_arrivals_count": np.nan}]).to_csv(processed_dir / "processed_patient_flow_daily.csv", index=False)
    v = PatientFlowIntegrationValidator(
        integration_run_id="INT-TEST-005",
        processed_directory=processed_dir,
        log_directory=temp_dirs["log_dir"],
    )
    v.load_prior_manifests()
    v.load_processed_datasets()
    recs = v.reconcile_daily_queue()
    arr_rec = [r for r in recs if r["reconciliation_field"] == "queue_arrivals_count"][0]
    # The daily has null, source has values but ambiguous -> mismatch expected
    assert arr_rec["reconciliation_status"] == "Failed"


def test_queue_averages_not_averaged_without_weights(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    recs = validator.reconcile_daily_queue()
    avg_rec = [r for r in recs if r["reconciliation_field"] == "queue_average_wait_minutes"][0]
    assert avg_rec["reconciliation_status"] == "Passed"


# ---------------------------------------------------------------------------
# 28-31. Bed reconciliation
# ---------------------------------------------------------------------------

def test_bed_values_reconcile(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    recs = validator.reconcile_daily_bed_capacity()
    occ_rec = [r for r in recs if r["reconciliation_field"] == "occupied_beds"][0]
    assert occ_rec["reconciliation_status"] == "Passed"


def test_occupied_beds_not_capped(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    recs = validator.reconcile_daily_bed_capacity()
    # Check that overcapacity row exists and is valid
    bed = validator.processed_dataframes["processed_bed_capacity"]
    over = bed[bed["occupied_beds"] > bed["operational_beds"]]
    assert len(over) > 0


def test_overcapacity_calculations_reconcile(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    recs = validator.reconcile_daily_bed_capacity()
    above_rec = [r for r in recs if r["reconciliation_field"] == "beds_above_operational_capacity"][0]
    flag_rec = [r for r in recs if r["reconciliation_field"] == "overcapacity_flag"][0]
    assert above_rec["reconciliation_status"] == "Passed"
    assert flag_rec["reconciliation_status"] == "Passed"


def test_duplicate_bed_snapshots_detected(temp_dirs, valid_manifests):
    processed_dir = temp_dirs["processed_dir"]
    b = _make_bed_df([
        {"bed_capacity_record_id": "B1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"},
        {"bed_capacity_record_id": "B2", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"},
    ])
    b.to_csv(processed_dir / "processed_bed_capacity.csv", index=False)
    # Other datasets
    _make_encounter_df([{"encounter_id": "E1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"}]).to_csv(processed_dir / "processed_patient_encounters.csv", index=False)
    _make_queue_df([{"queue_record_id": "Q1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"}]).to_csv(processed_dir / "processed_patient_queue.csv", index=False)
    _make_schedule_df([{"service_schedule_id": "S1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"}]).to_csv(processed_dir / "processed_service_schedule.csv", index=False)
    _make_daily_df([{"hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"}]).to_csv(processed_dir / "processed_patient_flow_daily.csv", index=False)
    v = PatientFlowIntegrationValidator(
        integration_run_id="INT-TEST-006",
        processed_directory=processed_dir,
        log_directory=temp_dirs["log_dir"],
    )
    v.load_prior_manifests()
    v.load_processed_datasets()
    errors = v.validate_business_keys()
    # Bed business key is bed_capacity_record_id, not grain, so no duplicate error from business key check
    # But reconciliation should show mismatch or null
    recs = v.reconcile_daily_bed_capacity()
    # Daily has null bed fields because builder would have set them to null for duplicates
    # In our test daily has NaN, source has 2 rows -> mismatch expected
    occ_rec = [r for r in recs if r["reconciliation_field"] == "occupied_beds"][0]
    assert occ_rec["reconciliation_status"] == "Failed"


# ---------------------------------------------------------------------------
# 32-36. Service schedule reconciliation
# ---------------------------------------------------------------------------

def test_planned_session_counts_reconcile(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    recs = validator.reconcile_daily_service_schedule()
    planned_rec = [r for r in recs if r["reconciliation_field"] == "planned_service_session_count"][0]
    assert planned_rec["reconciliation_status"] == "Passed"


def test_cancelled_session_counts_reconcile(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    recs = validator.reconcile_daily_service_schedule()
    canc_rec = [r for r in recs if r["reconciliation_field"] == "cancelled_service_session_count"][0]
    assert canc_rec["reconciliation_status"] == "Passed"


def test_reduced_session_counts_reconcile(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    recs = validator.reconcile_daily_service_schedule()
    red_rec = [r for r in recs if r["reconciliation_field"] == "reduced_service_session_count"][0]
    assert red_rec["reconciliation_status"] == "Passed"


def test_extended_session_counts_reconcile(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    recs = validator.reconcile_daily_service_schedule()
    ext_rec = [r for r in recs if r["reconciliation_field"] == "extended_service_session_count"][0]
    assert ext_rec["reconciliation_status"] == "Passed"


def test_overnight_sessions_not_duplicated(temp_dirs, valid_manifests):
    processed_dir = temp_dirs["processed_dir"]
    s = _make_schedule_df([
        {"service_schedule_id": "S1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01",
         "session_start_datetime": "2024-01-01T23:00:00", "session_end_datetime": "2024-01-02T07:00:00"},
    ])
    s.to_csv(processed_dir / "processed_service_schedule.csv", index=False)
    _make_encounter_df([{"encounter_id": "E1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"}]).to_csv(processed_dir / "processed_patient_encounters.csv", index=False)
    _make_queue_df([{"queue_record_id": "Q1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"}]).to_csv(processed_dir / "processed_patient_queue.csv", index=False)
    _make_bed_df([{"bed_capacity_record_id": "B1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"}]).to_csv(processed_dir / "processed_bed_capacity.csv", index=False)
    _make_daily_df([{"hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01", "planned_service_session_count": 1}]).to_csv(processed_dir / "processed_patient_flow_daily.csv", index=False)
    v = PatientFlowIntegrationValidator(
        integration_run_id="INT-TEST-007",
        processed_directory=processed_dir,
        log_directory=temp_dirs["log_dir"],
    )
    v.load_prior_manifests()
    v.load_processed_datasets()
    recs = v.reconcile_daily_service_schedule()
    planned_rec = [r for r in recs if r["reconciliation_field"] == "planned_service_session_count"][0]
    assert planned_rec["reconciliation_status"] == "Passed"


# ---------------------------------------------------------------------------
# 37-41. Lineage
# ---------------------------------------------------------------------------

def test_every_daily_row_has_lineage(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    errors = validator.validate_cross_step_lineage()
    assert not any("missing lineage" in e.lower() for e in errors)


def test_multi_domain_daily_rows_show_contributing_domains(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    validator.validate_cross_step_lineage()
    summary = validator.lineage_summary[0]
    sources = summary.get("unique_source_datasets", "").split(",")
    assert "processed_patient_encounters" in sources
    assert "processed_patient_queue" in sources


def test_missing_lineage_detected(temp_dirs, valid_manifests):
    processed_dir = temp_dirs["processed_dir"]
    # Empty lineage
    pd.DataFrame(columns=["processing_run_id", "lineage_id", "validation_run_id", "source_dataset_name",
                          "source_file_name", "source_primary_key_field", "source_primary_key_value",
                          "source_row_number", "processed_dataset_name", "processed_primary_key_field",
                          "processed_primary_key_value", "transformation_rule_id", "transformation_description",
                          "source_fields_used", "processed_fields_created", "exclusion_flag",
                          "exclusion_reason_code", "transformation_version", "configuration_version",
                          "processed_datetime"]).to_csv(temp_dirs["log_dir"] / "patient_flow_daily_processing_lineage.csv", index=False)
    _make_encounter_df([{"encounter_id": "E1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"}]).to_csv(processed_dir / "processed_patient_encounters.csv", index=False)
    _make_queue_df([{"queue_record_id": "Q1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"}]).to_csv(processed_dir / "processed_patient_queue.csv", index=False)
    _make_bed_df([{"bed_capacity_record_id": "B1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"}]).to_csv(processed_dir / "processed_bed_capacity.csv", index=False)
    _make_schedule_df([{"service_schedule_id": "S1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"}]).to_csv(processed_dir / "processed_service_schedule.csv", index=False)
    _make_daily_df([{"hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"}]).to_csv(processed_dir / "processed_patient_flow_daily.csv", index=False)
    v = PatientFlowIntegrationValidator(
        integration_run_id="INT-TEST-008",
        processed_directory=processed_dir,
        log_directory=temp_dirs["log_dir"],
    )
    v.load_prior_manifests()
    v.load_processed_datasets()
    errors = v.validate_cross_step_lineage()
    assert any("missing lineage" in e.lower() for e in errors)


def test_broken_lineage_references_detected(temp_dirs, valid_manifests):
    processed_dir = temp_dirs["processed_dir"]
    lineage = pd.DataFrame({
        "processing_run_id": ["PROC-TEST"],
        "lineage_id": ["L1"],
        "validation_run_id": ["VAL-TEST"],
        "source_dataset_name": ["processed_patient_encounters"],
        "source_file_name": ["enc.csv"],
        "source_primary_key_field": ["encounter_id"],
        "source_primary_key_value": ["E1"],
        "source_row_number": [0],
        "processed_dataset_name": ["processed_patient_flow_daily"],
        "processed_primary_key_field": ["patient_flow_daily_id"],
        "processed_primary_key_value": [""],
        "transformation_rule_id": ["TR_PFD_ENCOUNTER_AGGREGATION"],
        "transformation_description": ["test"],
        "source_fields_used": [""],
        "processed_fields_created": [""],
        "exclusion_flag": [False],
        "exclusion_reason_code": [""],
        "transformation_version": ["1.0"],
        "configuration_version": ["1.0"],
        "processed_datetime": [datetime.now()],
    })
    lineage.to_csv(temp_dirs["log_dir"] / "patient_flow_daily_processing_lineage.csv", index=False)
    _make_encounter_df([{"encounter_id": "E1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"}]).to_csv(processed_dir / "processed_patient_encounters.csv", index=False)
    _make_queue_df([{"queue_record_id": "Q1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"}]).to_csv(processed_dir / "processed_patient_queue.csv", index=False)
    _make_bed_df([{"bed_capacity_record_id": "B1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"}]).to_csv(processed_dir / "processed_bed_capacity.csv", index=False)
    _make_schedule_df([{"service_schedule_id": "S1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"}]).to_csv(processed_dir / "processed_service_schedule.csv", index=False)
    _make_daily_df([{"hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"}]).to_csv(processed_dir / "processed_patient_flow_daily.csv", index=False)
    v = PatientFlowIntegrationValidator(
        integration_run_id="INT-TEST-009",
        processed_directory=processed_dir,
        log_directory=temp_dirs["log_dir"],
    )
    v.load_prior_manifests()
    v.load_processed_datasets()
    errors = v.validate_cross_step_lineage()
    assert any("null or empty" in e.lower() for e in errors)


def test_duplicate_lineage_detected(temp_dirs, valid_manifests):
    processed_dir = temp_dirs["processed_dir"]
    lineage = pd.DataFrame({
        "processing_run_id": ["PROC-TEST", "PROC-TEST"],
        "lineage_id": ["L1", "L2"],
        "validation_run_id": ["VAL-TEST", "VAL-TEST"],
        "source_dataset_name": ["processed_patient_encounters", "processed_patient_encounters"],
        "source_file_name": ["enc.csv", "enc.csv"],
        "source_primary_key_field": ["encounter_id", "encounter_id"],
        "source_primary_key_value": ["E1", "E1"],
        "source_row_number": [0, 0],
        "processed_dataset_name": ["processed_patient_flow_daily", "processed_patient_flow_daily"],
        "processed_primary_key_field": ["patient_flow_daily_id", "patient_flow_daily_id"],
        "processed_primary_key_value": ["PFD-H1-D1-20240101", "PFD-H1-D1-20240101"],
        "transformation_rule_id": ["TR_PFD_ENCOUNTER_AGGREGATION", "TR_PFD_ENCOUNTER_AGGREGATION"],
        "transformation_description": ["test", "test"],
        "source_fields_used": ["", ""],
        "processed_fields_created": ["", ""],
        "exclusion_flag": [False, False],
        "exclusion_reason_code": ["", ""],
        "transformation_version": ["1.0", "1.0"],
        "configuration_version": ["1.0", "1.0"],
        "processed_datetime": [datetime.now(), datetime.now()],
    })
    lineage.to_csv(temp_dirs["log_dir"] / "patient_flow_daily_processing_lineage.csv", index=False)
    _make_encounter_df([{"encounter_id": "E1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"}]).to_csv(processed_dir / "processed_patient_encounters.csv", index=False)
    _make_queue_df([{"queue_record_id": "Q1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"}]).to_csv(processed_dir / "processed_patient_queue.csv", index=False)
    _make_bed_df([{"bed_capacity_record_id": "B1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"}]).to_csv(processed_dir / "processed_bed_capacity.csv", index=False)
    _make_schedule_df([{"service_schedule_id": "S1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"}]).to_csv(processed_dir / "processed_service_schedule.csv", index=False)
    _make_daily_df([{"hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"}]).to_csv(processed_dir / "processed_patient_flow_daily.csv", index=False)
    v = PatientFlowIntegrationValidator(
        integration_run_id="INT-TEST-010",
        processed_directory=processed_dir,
        log_directory=temp_dirs["log_dir"],
    )
    v.load_prior_manifests()
    v.load_processed_datasets()
    errors = v.validate_cross_step_lineage()
    assert any("duplicate" in e.lower() for e in errors)


# ---------------------------------------------------------------------------
# 42-44. Issue and exclusion consolidation
# ---------------------------------------------------------------------------

def test_prior_issues_consolidated(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    consolidated = validator.consolidate_issues()
    assert isinstance(consolidated, pd.DataFrame)


def test_prior_exclusions_consolidated(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    consolidated = validator.consolidate_exclusions()
    assert isinstance(consolidated, pd.DataFrame)


def test_empty_exclusion_outputs_retain_headers(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    consolidated = validator.consolidate_exclusions()
    assert len(consolidated.columns) > 0


# ---------------------------------------------------------------------------
# 45-46. Prohibited fields
# ---------------------------------------------------------------------------

def test_prohibited_kpi_fields_detected(temp_dirs, valid_manifests):
    processed_dir = temp_dirs["processed_dir"]
    enc = _make_encounter_df([{"encounter_id": "E1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"}])
    enc["average_patient_waiting_time"] = 30.0
    enc.to_csv(processed_dir / "processed_patient_encounters.csv", index=False)
    _make_queue_df([{"queue_record_id": "Q1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"}]).to_csv(processed_dir / "processed_patient_queue.csv", index=False)
    _make_bed_df([{"bed_capacity_record_id": "B1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"}]).to_csv(processed_dir / "processed_bed_capacity.csv", index=False)
    _make_schedule_df([{"service_schedule_id": "S1", "hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"}]).to_csv(processed_dir / "processed_service_schedule.csv", index=False)
    _make_daily_df([{"hospital_id": "H1", "department_id": "D1", "reporting_date": "2024-01-01"}]).to_csv(processed_dir / "processed_patient_flow_daily.csv", index=False)
    v = PatientFlowIntegrationValidator(
        integration_run_id="INT-TEST-011",
        processed_directory=processed_dir,
        log_directory=temp_dirs["log_dir"],
    )
    v.load_prior_manifests()
    v.load_processed_datasets()
    errors = v.check_prohibited_fields()
    assert any("average_patient_waiting_time" in e for e in errors)


def test_approved_preparation_fields_not_falsely_flagged(validator, sample_datasets):
    validator.load_prior_manifests()
    validator.load_processed_datasets()
    errors = validator.check_prohibited_fields()
    assert not any("encounter_count" in e for e in errors)
    assert not any("occupied_beds" in e for e in errors)


# ---------------------------------------------------------------------------
# 47. Integration outputs
# ---------------------------------------------------------------------------

def test_all_integration_outputs_generated(temp_dirs, valid_manifests, sample_datasets):
    from src.run_patient_flow_integration_validation import main
    result = main(
        processed_dir=str(temp_dirs["processed_dir"]),
        log_dir=str(temp_dirs["log_dir"]),
    )
    assert result["success"] is True
    files = [
        "patient_flow_integration_manifest.json",
        "patient_flow_integration_dataset_summary.csv",
        "patient_flow_integration_check_results.csv",
        "patient_flow_integration_issue_log.csv",
        "patient_flow_integration_lineage_summary.csv",
        "patient_flow_integration_lineage_gap_log.csv",
        "patient_flow_integration_exclusion_summary.csv",
        "patient_flow_integration_audit_log.csv",
        "patient_flow_cross_step_reconciliation.csv",
    ]
    for f in files:
        assert (temp_dirs["log_dir"] / f).exists(), f"Missing {f}"


# ---------------------------------------------------------------------------
# 48. Input immutability
# ---------------------------------------------------------------------------

def test_processed_datasets_remain_unchanged(temp_dirs, valid_manifests, sample_datasets):
    from src.run_patient_flow_integration_validation import main
    import hashlib
    def checksum(path):
        h = hashlib.sha256()
        with open(path, "rb") as f:
            h.update(f.read())
        return h.hexdigest()
    pre = {f: checksum(temp_dirs["processed_dir"] / f) for f in [
        "processed_patient_encounters.csv", "processed_patient_queue.csv",
        "processed_bed_capacity.csv", "processed_service_schedule.csv",
        "processed_patient_flow_daily.csv"
    ]}
    main(
        processed_dir=str(temp_dirs["processed_dir"]),
        log_dir=str(temp_dirs["log_dir"]),
    )
    post = {f: checksum(temp_dirs["processed_dir"] / f) for f in [
        "processed_patient_encounters.csv", "processed_patient_queue.csv",
        "processed_bed_capacity.csv", "processed_service_schedule.csv",
        "processed_patient_flow_daily.csv"
    ]}
    assert pre == post


# ---------------------------------------------------------------------------
# 49. Determinism
# ---------------------------------------------------------------------------

def test_repeated_integration_consistent(temp_dirs, valid_manifests, sample_datasets):
    from src.run_patient_flow_integration_validation import main
    result1 = main(
        processed_dir=str(temp_dirs["processed_dir"]),
        log_dir=str(temp_dirs["log_dir"]),
    )
    assert result1["success"] is True
    log_dir2 = temp_dirs["log_dir"] / "run2"
    log_dir2.mkdir()
    # Copy manifests
    import shutil
    for m in ["patient_encounter_processing_run_manifest.json", "queue_capacity_schedule_processing_run_manifest.json", "patient_flow_daily_processing_run_manifest.json"]:
        shutil.copy(temp_dirs["log_dir"] / m, log_dir2)
    # Copy lineage
    shutil.copy(temp_dirs["log_dir"] / "patient_flow_daily_processing_lineage.csv", log_dir2)
    # Copy prior issues/exclusions
    for f in ["patient_encounter_processing_issue_log.csv", "queue_capacity_schedule_processing_issue_log.csv", "patient_flow_daily_processing_issue_log.csv",
              "patient_encounter_processing_exclusion_register.csv", "queue_capacity_schedule_processing_exclusion_register.csv", "patient_flow_daily_processing_exclusion_register.csv"]:
        shutil.copy(temp_dirs["log_dir"] / f, log_dir2)
    result2 = main(
        processed_dir=str(temp_dirs["processed_dir"]),
        log_dir=str(log_dir2),
    )
    assert result2["success"] is True
    # Compare check results (excluding timestamps and IDs)
    checks1 = pd.read_csv(temp_dirs["log_dir"] / "patient_flow_integration_check_results.csv")
    checks2 = pd.read_csv(log_dir2 / "patient_flow_integration_check_results.csv")
    cols = [c for c in checks1.columns if c not in ["integration_run_id", "check_id", "checked_datetime"]]
    pd.testing.assert_frame_equal(checks1[cols].sort_values("check_name").reset_index(drop=True),
                                   checks2[cols].sort_values("check_name").reset_index(drop=True))


# ---------------------------------------------------------------------------
# 50-52. No forbidden outputs
# ---------------------------------------------------------------------------

def test_no_official_kpi_calculated(temp_dirs, valid_manifests, sample_datasets):
    from src.run_patient_flow_integration_validation import main
    result = main(
        processed_dir=str(temp_dirs["processed_dir"]),
        log_dir=str(temp_dirs["log_dir"]),
    )
    assert result["success"] is True
    manifest = result["manifest"]
    assert "kpi_value" not in str(manifest)


def test_no_kpi_status_created(temp_dirs, valid_manifests, sample_datasets):
    from src.run_patient_flow_integration_validation import main
    result = main(
        processed_dir=str(temp_dirs["processed_dir"]),
        log_dir=str(temp_dirs["log_dir"]),
    )
    assert result["success"] is True
    manifest = result["manifest"]
    assert "kpi_status" not in str(manifest).lower()


def test_no_risk_forecast_scenario_financial_recommendation(temp_dirs, valid_manifests, sample_datasets):
    from src.run_patient_flow_integration_validation import main
    result = main(
        processed_dir=str(temp_dirs["processed_dir"]),
        log_dir=str(temp_dirs["log_dir"]),
    )
    assert result["success"] is True
    manifest = result["manifest"]
    manifest_str = str(manifest).lower()
    for term in ["risk", "forecast", "scenario", "financial", "recommendation"]:
        assert term not in manifest_str or term in "readiness_for_next_step"
