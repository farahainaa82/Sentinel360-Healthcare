"""
Tests for Patient Experience Transformation (Step 2D-4)
"""

import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.patient_experience_transformer import PatientExperienceTransformer, TRANSFORMATION_VERSION, ENGINE_VERSION
from src.patient_experience_daily_builder import PatientExperienceDailyBuilder
from src.run_patient_experience_processing import main, parse_args, _verify_step_2d3_closure
from src.processed_schema_registry import get_processed_schema


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_complaint_df(rows):
    base = {
        "complaint_id": [r.get("complaint_id", f"C{i}") for i, r in enumerate(rows)],
        "hospital_id": [r.get("hospital_id", "HOSP-001") for r in rows],
        "department_id": [r.get("department_id", "DEPT-ED") for r in rows],
        "encounter_id": [r.get("encounter_id", None) for r in rows],
        "complaint_received_date": [r.get("complaint_received_date", "2026-01-15") for r in rows],
        "complaint_channel": [r.get("complaint_channel", "Email") for r in rows],
        "complaint_category": [r.get("complaint_category", "Waiting Time") for r in rows],
        "severity": [r.get("severity", "Medium") for r in rows],
        "description": [r.get("description", None) for r in rows],
        "status": [r.get("status", "Received") for r in rows],
        "resolution_date": [r.get("resolution_date", None) for r in rows],
        "outcome_category": [r.get("outcome_category", None) for r in rows],
        "duplicate_flag": [r.get("duplicate_flag", False) for r in rows],
        "duplicate_of_complaint_id": [r.get("duplicate_of_complaint_id", None) for r in rows],
        "source_system": [r.get("source_system", "demo") for r in rows],
        "created_at": [r.get("created_at", "2026-01-15T00:00:00") for r in rows],
    }
    return pd.DataFrame(base)


def _make_survey_df(rows):
    base = {
        "survey_id": [r.get("survey_id", f"S{i}") for i, r in enumerate(rows)],
        "hospital_id": [r.get("hospital_id", "HOSP-001") for r in rows],
        "department_id": [r.get("department_id", "DEPT-ED") for r in rows],
        "encounter_id": [r.get("encounter_id", None) for r in rows],
        "survey_date": [r.get("survey_date", "2026-01-15") for r in rows],
        "survey_type": [r.get("survey_type", "Outpatient Satisfaction") for r in rows],
        "scale_id": [r.get("scale_id", "SCALE-5PT") for r in rows],
        "score_value": [r.get("score_value", 4.0) for r in rows],
        "response_weight": [r.get("response_weight", 1.0) for r in rows],
        "is_complete": [r.get("is_complete", True) for r in rows],
        "source_system": [r.get("source_system", "demo") for r in rows],
        "created_at": [r.get("created_at", "2026-01-15T00:00:00") for r in rows],
    }
    return pd.DataFrame(base)


def _make_hospital_master():
    return pd.DataFrame({
        "hospital_id": ["HOSP-001", "HOSP-002"],
        "hospital_name": ["General", "Specialist"],
    })


def _make_department_master():
    return pd.DataFrame({
        "department_id": ["DEPT-ED", "DEPT-OPC"],
        "department_name": ["Emergency", "Outpatient"],
        "hospital_id": ["HOSP-001", "HOSP-001"],
    })


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_dirs():
    tmp = tempfile.mkdtemp()
    source_dir = Path(tmp) / "source"
    processed_dir = Path(tmp) / "processed"
    log_dir = Path(tmp) / "log"
    source_dir.mkdir()
    processed_dir.mkdir()
    log_dir.mkdir()

    # Write reference masters
    _make_hospital_master().to_csv(processed_dir / "processed_hospital_master.csv", index=False)
    _make_department_master().to_csv(processed_dir / "processed_department_master.csv", index=False)

    # Write Step 2D-3 closure manifest
    closure = {
        "closure_passed_flag": True,
        "run_status": "Passed",
    }
    with open(log_dir / "step_2d3_closure_manifest.json", "w") as f:
        json.dump(closure, f)

    yield {"source_dir": source_dir, "processed_dir": processed_dir, "log_dir": log_dir, "tmp": tmp}
    shutil.rmtree(tmp)


@pytest.fixture
def transformer(temp_dirs):
    return PatientExperienceTransformer(
        processing_run_id="PROC-TEST-001",
        validation_run_id="VAL-TEST-001",
        source_directory=temp_dirs["source_dir"],
        output_directory=temp_dirs["processed_dir"],
        log_directory=temp_dirs["log_dir"],
        source_type="test",
        collect_lineage=True,
        max_issue_examples=100,
    )


@pytest.fixture
def daily_builder(temp_dirs):
    return PatientExperienceDailyBuilder(
        processing_run_id="PROC-TEST-001",
        validation_run_id="VAL-TEST-001",
        input_directory=temp_dirs["processed_dir"],
        output_directory=temp_dirs["processed_dir"],
        log_directory=temp_dirs["log_dir"],
        source_type="test",
        collect_lineage=True,
        max_issue_examples=100,
    )


# ---------------------------------------------------------------------------
# 1-2. Safe imports
# ---------------------------------------------------------------------------

def test_modules_import_safely():
    import src.patient_experience_transformer as tmod
    import src.patient_experience_daily_builder as dmod
    import src.run_patient_experience_processing as rmod
    assert hasattr(tmod, "PatientExperienceTransformer")
    assert hasattr(dmod, "PatientExperienceDailyBuilder")
    assert hasattr(rmod, "main")


def test_runner_does_not_execute_on_import():
    import src.run_patient_experience_processing as runner
    assert callable(runner.main)
    assert callable(runner.parse_args)


# ---------------------------------------------------------------------------
# 3-6. Missing sources / references block processing
# ---------------------------------------------------------------------------

def test_missing_complaint_source_blocks_processing(temp_dirs):
    _make_survey_df([{"survey_id": "S1"}]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    result = main(
        project_root=str(Path(temp_dirs["tmp"])),
        source_dir="source",
        processed_dir="processed",
        log_dir="log",
        execute_export=False,
        dry_run=True,
    )
    assert result["success"] is False
    assert "patient_complaints" in result.get("blocking_reason", "").lower() or "missing source" in result.get("blocking_reason", "").lower()


def test_missing_survey_source_blocks_processing(temp_dirs):
    _make_complaint_df([{"complaint_id": "C1"}]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    result = main(
        project_root=str(Path(temp_dirs["tmp"])),
        source_dir="source",
        processed_dir="processed",
        log_dir="log",
        execute_export=False,
        dry_run=True,
    )
    assert result["success"] is False
    assert "patient_surveys" in result.get("blocking_reason", "").lower() or "missing source" in result.get("blocking_reason", "").lower()


def test_missing_hospital_reference_blocks_processing(temp_dirs):
    os.remove(temp_dirs["processed_dir"] / "processed_hospital_master.csv")
    _make_complaint_df([{"complaint_id": "C1"}]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1"}]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    result = main(
        project_root=str(Path(temp_dirs["tmp"])),
        source_dir="source",
        processed_dir="processed",
        log_dir="log",
        execute_export=False,
        dry_run=True,
    )
    assert result["success"] is False


def test_missing_department_reference_blocks_processing(temp_dirs):
    os.remove(temp_dirs["processed_dir"] / "processed_department_master.csv")
    _make_complaint_df([{"complaint_id": "C1"}]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1"}]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    result = main(
        project_root=str(Path(temp_dirs["tmp"])),
        source_dir="source",
        processed_dir="processed",
        log_dir="log",
        execute_export=False,
        dry_run=True,
    )
    assert result["success"] is False


# ---------------------------------------------------------------------------
# 7-10. ID preservation and duplication
# ---------------------------------------------------------------------------

def test_complaint_ids_preserved(transformer, temp_dirs):
    _make_complaint_df([{"complaint_id": "C-ABC-123"}]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1"}]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, _ = transformer.load_source_data()
    result = transformer.transform_complaints(complaints)
    assert result.loc[0, "complaint_id"] == "C-ABC-123"


def test_survey_ids_preserved(transformer, temp_dirs):
    _make_complaint_df([{"complaint_id": "C1"}]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S-XYZ-999"}]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    _, surveys = transformer.load_source_data()
    result = transformer.transform_surveys(surveys)
    assert result.loc[0, "survey_id"] == "S-XYZ-999"


def test_duplicate_complaint_ids_detected(transformer, temp_dirs):
    _make_complaint_df([
        {"complaint_id": "C1"},
        {"complaint_id": "C1"},
    ]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1"}]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, _ = transformer.load_source_data()
    transformer.transform_complaints(complaints)
    assert any(i.issue_type == "Duplicate Primary Key" for i in transformer.issues)
    assert any(i.blocks_processing for i in transformer.issues if i.issue_type == "Duplicate Primary Key")


def test_duplicate_survey_ids_detected(transformer, temp_dirs):
    _make_complaint_df([{"complaint_id": "C1"}]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([
        {"survey_id": "S1"},
        {"survey_id": "S1"},
    ]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    _, surveys = transformer.load_source_data()
    transformer.transform_surveys(surveys)
    assert any(i.issue_type == "Duplicate Primary Key" for i in transformer.issues)
    assert any(i.blocks_processing for i in transformer.issues if i.issue_type == "Duplicate Primary Key")


# ---------------------------------------------------------------------------
# 11-14. Date parsing
# ---------------------------------------------------------------------------

def test_complaint_dates_parse_correctly(transformer, temp_dirs):
    _make_complaint_df([{"complaint_id": "C1", "complaint_received_date": "2026-06-15"}]).to_csv(
        temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1"}]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, _ = transformer.load_source_data()
    result = transformer.transform_complaints(complaints)
    assert str(result.loc[0, "complaint_date"]) == "2026-06-15"
    assert result.loc[0, "complaint_date_valid_flag"] == True


def test_invalid_complaint_dates_logged(transformer, temp_dirs):
    _make_complaint_df([{"complaint_id": "C1", "complaint_received_date": "not-a-date"}]).to_csv(
        temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1"}]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, _ = transformer.load_source_data()
    transformer.transform_complaints(complaints)
    assert any(i.issue_type == "Invalid Date" for i in transformer.issues)


def test_survey_dates_parse_correctly(transformer, temp_dirs):
    _make_complaint_df([{"complaint_id": "C1"}]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1", "survey_date": "2026-08-20"}]).to_csv(
        temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    _, surveys = transformer.load_source_data()
    result = transformer.transform_surveys(surveys)
    assert str(result.loc[0, "survey_date"]) == "2026-08-20"
    assert result.loc[0, "survey_date_valid_flag"] == True


def test_invalid_survey_dates_logged(transformer, temp_dirs):
    _make_complaint_df([{"complaint_id": "C1"}]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1", "survey_date": "bad-date"}]).to_csv(
        temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    _, surveys = transformer.load_source_data()
    transformer.transform_surveys(surveys)
    assert any(i.issue_type == "Invalid Date" for i in transformer.issues)


# ---------------------------------------------------------------------------
# 15-21. Complaint fields preserved / not inferred
# ---------------------------------------------------------------------------

def test_complaint_channels_preserved(transformer, temp_dirs):
    _make_complaint_df([{"complaint_id": "C1", "complaint_channel": "Walk-In"}]).to_csv(
        temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1"}]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, _ = transformer.load_source_data()
    result = transformer.transform_complaints(complaints)
    assert result.loc[0, "complaint_channel"] == "Walk-In"


def test_unsupported_complaint_channels_preserved(transformer, temp_dirs):
    _make_complaint_df([{"complaint_id": "C1", "complaint_channel": "Carrier Pigeon"}]).to_csv(
        temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1"}]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, _ = transformer.load_source_data()
    result = transformer.transform_complaints(complaints)
    assert result.loc[0, "complaint_channel"] == "Carrier Pigeon"
    assert result.loc[0, "complaint_channel_supported_flag"] == False
    assert any(i.issue_type == "Unsupported Channel" for i in transformer.issues)


def test_complaint_categories_preserved(transformer, temp_dirs):
    _make_complaint_df([{"complaint_id": "C1", "complaint_category": "Billing"}]).to_csv(
        temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1"}]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, _ = transformer.load_source_data()
    result = transformer.transform_complaints(complaints)
    assert result.loc[0, "complaint_category"] == "Billing"


def test_unsupported_complaint_categories_preserved(transformer, temp_dirs):
    _make_complaint_df([{"complaint_id": "C1", "complaint_category": "Parking"}]).to_csv(
        temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1"}]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, _ = transformer.load_source_data()
    result = transformer.transform_complaints(complaints)
    assert result.loc[0, "complaint_category"] == "Parking"
    assert result.loc[0, "complaint_category_supported_flag"] == False
    assert any(i.issue_type == "Unsupported Category" for i in transformer.issues)


def test_complaint_severity_preserved(transformer, temp_dirs):
    _make_complaint_df([{"complaint_id": "C1", "severity": "Critical"}]).to_csv(
        temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1"}]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, _ = transformer.load_source_data()
    result = transformer.transform_complaints(complaints)
    assert result.loc[0, "complaint_severity"] == "Critical"


def test_complaint_severity_not_inferred_from_text(transformer, temp_dirs):
    _make_complaint_df([{"complaint_id": "C1", "severity": "Low", "description": "Terrible disaster"}]).to_csv(
        temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1"}]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, _ = transformer.load_source_data()
    result = transformer.transform_complaints(complaints)
    assert result.loc[0, "complaint_severity"] == "Low"


def test_resolution_status_not_inferred(transformer, temp_dirs):
    _make_complaint_df([{"complaint_id": "C1", "status": "Received", "resolution_date": None}]).to_csv(
        temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1"}]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, _ = transformer.load_source_data()
    result = transformer.transform_complaints(complaints)
    assert result.loc[0, "complaint_resolved_source_flag"] == False
    assert result.loc[0, "complaint_open_source_flag"] == True


def test_resolution_date_before_complaint_detected(transformer, temp_dirs):
    _make_complaint_df([{
        "complaint_id": "C1",
        "complaint_received_date": "2026-06-15",
        "resolution_date": "2026-06-10",
    }]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1"}]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, _ = transformer.load_source_data()
    transformer.transform_complaints(complaints)
    assert any(i.issue_type == "Resolution Before Complaint" for i in transformer.issues)


# ---------------------------------------------------------------------------
# 23-29. Survey score handling
# ---------------------------------------------------------------------------

def test_survey_score_source_preserved(transformer, temp_dirs):
    _make_complaint_df([{"complaint_id": "C1"}]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1", "score_value": 3.5}]).to_csv(
        temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    _, surveys = transformer.load_source_data()
    result = transformer.transform_surveys(surveys)
    assert float(result.loc[0, "satisfaction_score_numeric"]) == 3.5


def test_valid_survey_scores_pass(transformer, temp_dirs):
    _make_complaint_df([{"complaint_id": "C1"}]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1", "score_value": 4.0, "scale_id": "SCALE-5PT"}]).to_csv(
        temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    _, surveys = transformer.load_source_data()
    result = transformer.transform_surveys(surveys)
    assert result.loc[0, "satisfaction_score_valid_flag"] == True


def test_invalid_survey_scores_detected(transformer, temp_dirs):
    _make_complaint_df([{"complaint_id": "C1"}]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1", "score_value": 99.0, "scale_id": "SCALE-5PT"}]).to_csv(
        temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    _, surveys = transformer.load_source_data()
    transformer.transform_surveys(surveys)
    assert any(i.issue_type == "Impossible Score" for i in transformer.issues)


def test_unknown_survey_scale_flagged(transformer, temp_dirs):
    _make_complaint_df([{"complaint_id": "C1"}]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1", "scale_id": "SCALE-UNKNOWN"}]).to_csv(
        temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    _, surveys = transformer.load_source_data()
    transformer.transform_surveys(surveys)
    assert any(i.issue_type == "Unknown Survey Scale" for i in transformer.issues)


def test_multiple_survey_scales_flagged(transformer, temp_dirs):
    _make_complaint_df([{"complaint_id": "C1"}]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([
        {"survey_id": "S1", "scale_id": "SCALE-5PT"},
        {"survey_id": "S2", "scale_id": "SCALE-10PT"},
    ]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    _, surveys = transformer.load_source_data()
    transformer.transform_surveys(surveys)
    assert any(i.issue_type == "Mixed Survey Scales" for i in transformer.issues)


def test_negative_response_counts_detected(transformer, temp_dirs):
    _make_complaint_df([{"complaint_id": "C1"}]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1", "response_weight": -2.0}]).to_csv(
        temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    _, surveys = transformer.load_source_data()
    transformer.transform_surveys(surveys)
    assert any(i.issue_type == "Negative Response Count" for i in transformer.issues)


def test_missing_response_counts_remain_null(transformer, temp_dirs):
    _make_complaint_df([{"complaint_id": "C1"}]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    df = _make_survey_df([{"survey_id": "S1"}])
    df["response_weight"] = np.nan
    df.to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    _, surveys = transformer.load_source_data()
    result = transformer.transform_surveys(surveys)
    assert pd.isna(result.loc[0, "response_count"])


def test_missing_response_count_not_replaced_with_one(transformer, temp_dirs):
    _make_complaint_df([{"complaint_id": "C1"}]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    df = _make_survey_df([{"survey_id": "S1"}])
    df["response_weight"] = np.nan
    df.to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    _, surveys = transformer.load_source_data()
    result = transformer.transform_surveys(surveys)
    assert result.loc[0, "response_count"] != 1.0
    assert pd.isna(result.loc[0, "response_count"])


# ---------------------------------------------------------------------------
# 31-33. Reference validation
# ---------------------------------------------------------------------------

def test_hospital_references_validated(transformer, temp_dirs):
    _make_complaint_df([{"complaint_id": "C1", "hospital_id": "HOSP-001"}]).to_csv(
        temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1"}]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, _ = transformer.load_source_data()
    result = transformer.transform_complaints(complaints)
    assert result.loc[0, "hospital_ref_valid_flag"] == True


def test_department_references_validated(transformer, temp_dirs):
    _make_complaint_df([{"complaint_id": "C1", "department_id": "DEPT-ED"}]).to_csv(
        temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1"}]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, _ = transformer.load_source_data()
    result = transformer.transform_complaints(complaints)
    assert result.loc[0, "department_ref_valid_flag"] == True


def test_orphan_references_detected(transformer, temp_dirs):
    _make_complaint_df([{"complaint_id": "C1", "hospital_id": "UNKNOWN-HOSP"}]).to_csv(
        temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1"}]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, _ = transformer.load_source_data()
    transformer.transform_complaints(complaints)
    assert any(i.issue_type == "Invalid Hospital Reference" for i in transformer.issues)


# ---------------------------------------------------------------------------
# 34-36. Schema passes
# ---------------------------------------------------------------------------

def test_processed_complaint_schema_passes(transformer, temp_dirs):
    _make_complaint_df([{"complaint_id": "C1"}]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1"}]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, _ = transformer.load_source_data()
    result = transformer.transform_complaints(complaints)
    errors = transformer.validate_processed_complaint_schema(result)
    assert errors == []


def test_processed_survey_schema_passes(transformer, temp_dirs):
    _make_complaint_df([{"complaint_id": "C1"}]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1"}]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    _, surveys = transformer.load_source_data()
    result = transformer.transform_surveys(surveys)
    errors = transformer.validate_processed_survey_schema(result)
    assert errors == []


def test_daily_schema_passes(temp_dirs, transformer, daily_builder):
    _make_complaint_df([
        {"complaint_id": "C1", "complaint_received_date": "2026-01-15"},
    ]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([
        {"survey_id": "S1", "survey_date": "2026-01-15"},
    ]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, surveys = transformer.load_source_data()
    c_df = transformer.transform_complaints(complaints)
    s_df = transformer.transform_surveys(surveys)
    daily_builder.set_processed_complaints(c_df)
    daily_builder.set_processed_surveys(s_df)
    spine = daily_builder.build_daily_spine()
    ca = daily_builder.aggregate_complaints(spine)
    sa = daily_builder.aggregate_surveys(spine)
    daily = daily_builder.combine_daily_components(spine, ca, sa)
    daily = daily_builder.create_daily_identifier(daily)
    daily["processing_run_id"] = "PROC-TEST"
    daily["processed_datetime"] = datetime.now()
    daily["transformation_version"] = "1.0"
    errors = daily_builder.validate_daily_schema(daily)
    assert errors == []


# ---------------------------------------------------------------------------
# 37-39. Daily identifiers and grain
# ---------------------------------------------------------------------------

def test_daily_ids_are_deterministic(temp_dirs, transformer, daily_builder):
    _make_complaint_df([
        {"complaint_id": "C1", "complaint_received_date": "2026-01-15"},
    ]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([
        {"survey_id": "S1", "survey_date": "2026-01-15"},
    ]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, surveys = transformer.load_source_data()
    c_df = transformer.transform_complaints(complaints)
    s_df = transformer.transform_surveys(surveys)
    daily_builder.set_processed_complaints(c_df)
    daily_builder.set_processed_surveys(s_df)
    spine = daily_builder.build_daily_spine()
    ca = daily_builder.aggregate_complaints(spine)
    sa = daily_builder.aggregate_surveys(spine)
    daily = daily_builder.combine_daily_components(spine, ca, sa)
    daily = daily_builder.create_daily_identifier(daily)
    assert daily.loc[0, "patient_experience_daily_id"] == "PEX-HOSP-001-DEPT-ED-20260115"


def test_daily_ids_are_unique(temp_dirs, transformer, daily_builder):
    _make_complaint_df([
        {"complaint_id": "C1", "complaint_received_date": "2026-01-15"},
    ]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([
        {"survey_id": "S1", "survey_date": "2026-01-15"},
    ]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, surveys = transformer.load_source_data()
    c_df = transformer.transform_complaints(complaints)
    s_df = transformer.transform_surveys(surveys)
    daily_builder.set_processed_complaints(c_df)
    daily_builder.set_processed_surveys(s_df)
    spine = daily_builder.build_daily_spine()
    ca = daily_builder.aggregate_complaints(spine)
    sa = daily_builder.aggregate_surveys(spine)
    daily = daily_builder.combine_daily_components(spine, ca, sa)
    daily = daily_builder.create_daily_identifier(daily)
    assert daily["patient_experience_daily_id"].duplicated().sum() == 0


def test_hospital_department_date_grain_is_unique(temp_dirs, transformer, daily_builder):
    _make_complaint_df([
        {"complaint_id": "C1", "complaint_received_date": "2026-01-15"},
    ]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([
        {"survey_id": "S1", "survey_date": "2026-01-15"},
    ]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, surveys = transformer.load_source_data()
    c_df = transformer.transform_complaints(complaints)
    s_df = transformer.transform_surveys(surveys)
    daily_builder.set_processed_complaints(c_df)
    daily_builder.set_processed_surveys(s_df)
    spine = daily_builder.build_daily_spine()
    ca = daily_builder.aggregate_complaints(spine)
    sa = daily_builder.aggregate_surveys(spine)
    daily = daily_builder.combine_daily_components(spine, ca, sa)
    daily = daily_builder.create_daily_identifier(daily)
    grain_dups = daily.duplicated(subset=["hospital_id", "department_id", "reporting_date"]).sum()
    assert grain_dups == 0


# ---------------------------------------------------------------------------
# 40-42. Daily row types
# ---------------------------------------------------------------------------

def test_complaint_only_daily_rows_supported(temp_dirs, transformer, daily_builder):
    _make_complaint_df([
        {"complaint_id": "C1", "complaint_received_date": "2026-01-15"},
    ]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, surveys = transformer.load_source_data()
    c_df = transformer.transform_complaints(complaints)
    s_df = transformer.transform_surveys(surveys)
    daily_builder.set_processed_complaints(c_df)
    daily_builder.set_processed_surveys(s_df)
    spine = daily_builder.build_daily_spine()
    ca = daily_builder.aggregate_complaints(spine)
    sa = daily_builder.aggregate_surveys(spine)
    daily = daily_builder.combine_daily_components(spine, ca, sa)
    daily = daily_builder.create_daily_identifier(daily)
    assert daily.loc[0, "complaint_source_present_flag"] == True
    assert daily.loc[0, "survey_source_present_flag"] == False


def test_survey_only_daily_rows_supported(temp_dirs, transformer, daily_builder):
    _make_complaint_df([]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([
        {"survey_id": "S1", "survey_date": "2026-01-15"},
    ]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, surveys = transformer.load_source_data()
    c_df = transformer.transform_complaints(complaints)
    s_df = transformer.transform_surveys(surveys)
    daily_builder.set_processed_complaints(c_df)
    daily_builder.set_processed_surveys(s_df)
    spine = daily_builder.build_daily_spine()
    ca = daily_builder.aggregate_complaints(spine)
    sa = daily_builder.aggregate_surveys(spine)
    daily = daily_builder.combine_daily_components(spine, ca, sa)
    daily = daily_builder.create_daily_identifier(daily)
    assert daily.loc[0, "complaint_source_present_flag"] == False
    assert daily.loc[0, "survey_source_present_flag"] == True


def test_combined_daily_rows_supported(temp_dirs, transformer, daily_builder):
    _make_complaint_df([
        {"complaint_id": "C1", "complaint_received_date": "2026-01-15"},
    ]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([
        {"survey_id": "S1", "survey_date": "2026-01-15"},
    ]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, surveys = transformer.load_source_data()
    c_df = transformer.transform_complaints(complaints)
    s_df = transformer.transform_surveys(surveys)
    daily_builder.set_processed_complaints(c_df)
    daily_builder.set_processed_surveys(s_df)
    spine = daily_builder.build_daily_spine()
    ca = daily_builder.aggregate_complaints(spine)
    sa = daily_builder.aggregate_surveys(spine)
    daily = daily_builder.combine_daily_components(spine, ca, sa)
    daily = daily_builder.create_daily_identifier(daily)
    assert daily.loc[0, "complaint_source_present_flag"] == True
    assert daily.loc[0, "survey_source_present_flag"] == True


# ---------------------------------------------------------------------------
# 43-47. Aggregation correctness
# ---------------------------------------------------------------------------

def test_complaint_counts_aggregate_correctly(temp_dirs, transformer, daily_builder):
    _make_complaint_df([
        {"complaint_id": "C1", "complaint_received_date": "2026-01-15"},
        {"complaint_id": "C2", "complaint_received_date": "2026-01-15"},
        {"complaint_id": "C3", "complaint_received_date": "2026-01-15"},
    ]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, surveys = transformer.load_source_data()
    c_df = transformer.transform_complaints(complaints)
    s_df = transformer.transform_surveys(surveys)
    daily_builder.set_processed_complaints(c_df)
    daily_builder.set_processed_surveys(s_df)
    spine = daily_builder.build_daily_spine()
    ca = daily_builder.aggregate_complaints(spine)
    sa = daily_builder.aggregate_surveys(spine)
    daily = daily_builder.combine_daily_components(spine, ca, sa)
    daily = daily_builder.create_daily_identifier(daily)
    assert daily.loc[0, "complaint_record_count"] == 3


def test_severity_counts_aggregate_correctly(temp_dirs, transformer, daily_builder):
    _make_complaint_df([
        {"complaint_id": "C1", "complaint_received_date": "2026-01-15", "severity": "High"},
        {"complaint_id": "C2", "complaint_received_date": "2026-01-15", "severity": "Medium"},
        {"complaint_id": "C3", "complaint_received_date": "2026-01-15", "severity": "Low"},
        {"complaint_id": "C4", "complaint_received_date": "2026-01-15", "severity": "High"},
    ]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, surveys = transformer.load_source_data()
    c_df = transformer.transform_complaints(complaints)
    s_df = transformer.transform_surveys(surveys)
    daily_builder.set_processed_complaints(c_df)
    daily_builder.set_processed_surveys(s_df)
    spine = daily_builder.build_daily_spine()
    ca = daily_builder.aggregate_complaints(spine)
    sa = daily_builder.aggregate_surveys(spine)
    daily = daily_builder.combine_daily_components(spine, ca, sa)
    daily = daily_builder.create_daily_identifier(daily)
    assert daily.loc[0, "complaint_high_severity_count"] == 2
    assert daily.loc[0, "complaint_medium_severity_count"] == 1
    assert daily.loc[0, "complaint_low_severity_count"] == 1


def test_survey_record_counts_aggregate_correctly(temp_dirs, transformer, daily_builder):
    _make_complaint_df([]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([
        {"survey_id": "S1", "survey_date": "2026-01-15"},
        {"survey_id": "S2", "survey_date": "2026-01-15"},
    ]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, surveys = transformer.load_source_data()
    c_df = transformer.transform_complaints(complaints)
    s_df = transformer.transform_surveys(surveys)
    daily_builder.set_processed_complaints(c_df)
    daily_builder.set_processed_surveys(s_df)
    spine = daily_builder.build_daily_spine()
    ca = daily_builder.aggregate_complaints(spine)
    sa = daily_builder.aggregate_surveys(spine)
    daily = daily_builder.combine_daily_components(spine, ca, sa)
    daily = daily_builder.create_daily_identifier(daily)
    assert daily.loc[0, "survey_record_count"] == 2


def test_response_counts_aggregate_correctly(temp_dirs, transformer, daily_builder):
    _make_complaint_df([]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([
        {"survey_id": "S1", "survey_date": "2026-01-15", "response_weight": 2.0},
        {"survey_id": "S2", "survey_date": "2026-01-15", "response_weight": 3.0},
    ]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, surveys = transformer.load_source_data()
    c_df = transformer.transform_complaints(complaints)
    s_df = transformer.transform_surveys(surveys)
    daily_builder.set_processed_complaints(c_df)
    daily_builder.set_processed_surveys(s_df)
    spine = daily_builder.build_daily_spine()
    ca = daily_builder.aggregate_complaints(spine)
    sa = daily_builder.aggregate_surveys(spine)
    daily = daily_builder.combine_daily_components(spine, ca, sa)
    daily = daily_builder.create_daily_identifier(daily)
    assert daily.loc[0, "survey_response_count_total"] == 5


def test_score_sums_aggregate_correctly(temp_dirs, transformer, daily_builder):
    _make_complaint_df([]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([
        {"survey_id": "S1", "survey_date": "2026-01-15", "score_value": 3.0, "response_weight": 1.0},
        {"survey_id": "S2", "survey_date": "2026-01-15", "score_value": 4.0, "response_weight": 1.0},
    ]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, surveys = transformer.load_source_data()
    c_df = transformer.transform_complaints(complaints)
    s_df = transformer.transform_surveys(surveys)
    daily_builder.set_processed_complaints(c_df)
    daily_builder.set_processed_surveys(s_df)
    spine = daily_builder.build_daily_spine()
    ca = daily_builder.aggregate_complaints(spine)
    sa = daily_builder.aggregate_surveys(spine)
    daily = daily_builder.combine_daily_components(spine, ca, sa)
    daily = daily_builder.create_daily_identifier(daily)
    assert daily.loc[0, "survey_score_sum"] == 7.0


# ---------------------------------------------------------------------------
# 48-57. No forbidden KPI / analytical outputs
# ---------------------------------------------------------------------------

def test_no_official_complaint_rate_calculated(temp_dirs, transformer, daily_builder):
    _make_complaint_df([
        {"complaint_id": "C1", "complaint_received_date": "2026-01-15"},
    ]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, surveys = transformer.load_source_data()
    c_df = transformer.transform_complaints(complaints)
    s_df = transformer.transform_surveys(surveys)
    daily_builder.set_processed_complaints(c_df)
    daily_builder.set_processed_surveys(s_df)
    spine = daily_builder.build_daily_spine()
    ca = daily_builder.aggregate_complaints(spine)
    sa = daily_builder.aggregate_surveys(spine)
    daily = daily_builder.combine_daily_components(spine, ca, sa)
    assert "complaint_rate" not in daily.columns
    assert "official_complaint_rate" not in daily.columns


def test_no_official_satisfaction_kpi_calculated(temp_dirs, transformer, daily_builder):
    _make_complaint_df([]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([
        {"survey_id": "S1", "survey_date": "2026-01-15", "score_value": 4.0},
    ]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, surveys = transformer.load_source_data()
    c_df = transformer.transform_complaints(complaints)
    s_df = transformer.transform_surveys(surveys)
    daily_builder.set_processed_complaints(c_df)
    daily_builder.set_processed_surveys(s_df)
    spine = daily_builder.build_daily_spine()
    ca = daily_builder.aggregate_complaints(spine)
    sa = daily_builder.aggregate_surveys(spine)
    daily = daily_builder.combine_daily_components(spine, ca, sa)
    assert "patient_satisfaction_score" not in daily.columns
    assert "average_satisfaction_score" not in daily.columns


def test_no_kpi_status_created(temp_dirs, transformer, daily_builder):
    daily = _build_simple_daily(temp_dirs, transformer, daily_builder)
    assert "kpi_status" not in daily.columns


def test_no_trend_field_created(temp_dirs, transformer, daily_builder):
    daily = _build_simple_daily(temp_dirs, transformer, daily_builder)
    assert "trend" not in daily.columns


def test_no_anomaly_field_created(temp_dirs, transformer, daily_builder):
    daily = _build_simple_daily(temp_dirs, transformer, daily_builder)
    assert "anomaly" not in daily.columns


def test_no_risk_field_created(temp_dirs, transformer, daily_builder):
    daily = _build_simple_daily(temp_dirs, transformer, daily_builder)
    assert "risk" not in daily.columns


def test_no_forecast_field_created(temp_dirs, transformer, daily_builder):
    daily = _build_simple_daily(temp_dirs, transformer, daily_builder)
    assert "forecast" not in daily.columns


def test_no_scenario_field_created(temp_dirs, transformer, daily_builder):
    daily = _build_simple_daily(temp_dirs, transformer, daily_builder)
    assert "scenario" not in daily.columns


def test_no_financial_impact_field_created(temp_dirs, transformer, daily_builder):
    daily = _build_simple_daily(temp_dirs, transformer, daily_builder)
    assert "financial" not in daily.columns


def test_no_recommendation_field_created(temp_dirs, transformer, daily_builder):
    daily = _build_simple_daily(temp_dirs, transformer, daily_builder)
    assert "recommendation" not in daily.columns


def _build_simple_daily(temp_dirs, transformer, daily_builder):
    _make_complaint_df([
        {"complaint_id": "C1", "complaint_received_date": "2026-01-15"},
    ]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([
        {"survey_id": "S1", "survey_date": "2026-01-15"},
    ]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, surveys = transformer.load_source_data()
    c_df = transformer.transform_complaints(complaints)
    s_df = transformer.transform_surveys(surveys)
    daily_builder.set_processed_complaints(c_df)
    daily_builder.set_processed_surveys(s_df)
    spine = daily_builder.build_daily_spine()
    ca = daily_builder.aggregate_complaints(spine)
    sa = daily_builder.aggregate_surveys(spine)
    daily = daily_builder.combine_daily_components(spine, ca, sa)
    return daily


# ---------------------------------------------------------------------------
# 58-60. Lineage coverage
# ---------------------------------------------------------------------------

def test_record_lineage_covers_complaint_outputs(transformer, temp_dirs):
    _make_complaint_df([{"complaint_id": "C1"}]).to_csv(
        temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, _ = transformer.load_source_data()
    c_df = transformer.transform_complaints(complaints)
    transformer.build_record_lineage(complaints, c_df, "patient_complaints", "processed_patient_complaints", "complaint_id")
    lineage_ids = {r["output_record_id"] for r in transformer.lineage_records}
    assert "C1" in lineage_ids


def test_record_lineage_covers_survey_outputs(transformer, temp_dirs):
    _make_complaint_df([]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1"}]).to_csv(
        temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    _, surveys = transformer.load_source_data()
    s_df = transformer.transform_surveys(surveys)
    transformer.build_record_lineage(surveys, s_df, "patient_surveys", "processed_patient_surveys", "survey_id")
    lineage_ids = {r["output_record_id"] for r in transformer.lineage_records}
    assert "S1" in lineage_ids


def test_daily_lineage_covers_all_daily_output_rows(temp_dirs, transformer, daily_builder):
    _make_complaint_df([
        {"complaint_id": "C1", "complaint_received_date": "2026-01-15"},
    ]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([
        {"survey_id": "S1", "survey_date": "2026-01-15"},
    ]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, surveys = transformer.load_source_data()
    c_df = transformer.transform_complaints(complaints)
    s_df = transformer.transform_surveys(surveys)
    daily_builder.set_processed_complaints(c_df)
    daily_builder.set_processed_surveys(s_df)
    spine = daily_builder.build_daily_spine()
    ca = daily_builder.aggregate_complaints(spine)
    sa = daily_builder.aggregate_surveys(spine)
    daily = daily_builder.combine_daily_components(spine, ca, sa)
    daily = daily_builder.create_daily_identifier(daily)
    daily["processing_run_id"] = "PROC-TEST"
    daily["processed_datetime"] = datetime.now()
    daily["transformation_version"] = "1.0"
    daily_builder.build_daily_lineage(daily, c_df, s_df)
    daily_ids = set(daily["patient_experience_daily_id"])
    lineage_daily_ids = {r["output_record_id"] for r in daily_builder.lineage_records}
    assert daily_ids.issubset(lineage_daily_ids)


# ---------------------------------------------------------------------------
# 61. Excluded records logged
# ---------------------------------------------------------------------------

def test_excluded_records_logged(transformer, temp_dirs):
    _make_complaint_df([
        {"complaint_id": "C1", "complaint_received_date": "bad-date"},
    ]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    complaints, _ = transformer.load_source_data()
    c_df = transformer.transform_complaints(complaints)
    transformer.build_exclusions(c_df, "complaint_id", "processed_patient_complaints", "patient_complaints.csv")
    assert len(transformer.exclusion_records) > 0
    assert transformer.exclusion_records[0]["exclusion_reason_code"] == "INVALID_DATE"


# ---------------------------------------------------------------------------
# 62-64. Source / prior immutability
# ---------------------------------------------------------------------------

def test_source_checksums_verified(temp_dirs):
    _make_complaint_df([{"complaint_id": "C1"}]).to_csv(
        temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1"}]).to_csv(
        temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    result = main(
        project_root=str(Path(temp_dirs["tmp"])),
        source_dir="source",
        processed_dir="processed",
        log_dir="log",
        execute_export=True,
        dry_run=False,
    )
    assert result["success"] is True
    manifest_path = temp_dirs["log_dir"] / "patient_experience_processing_run_manifest.json"
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    assert manifest.get("inputs_unchanged", False) is True


def test_source_files_remain_unchanged(temp_dirs):
    _make_complaint_df([{"complaint_id": "C1"}]).to_csv(
        temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1"}]).to_csv(
        temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    pre_c = _file_checksum(temp_dirs["source_dir"] / "patient_complaints.csv")
    pre_s = _file_checksum(temp_dirs["source_dir"] / "patient_surveys.csv")
    main(
        project_root=str(Path(temp_dirs["tmp"])),
        source_dir="source",
        processed_dir="processed",
        log_dir="log",
        execute_export=True,
        dry_run=False,
    )
    post_c = _file_checksum(temp_dirs["source_dir"] / "patient_complaints.csv")
    post_s = _file_checksum(temp_dirs["source_dir"] / "patient_surveys.csv")
    assert pre_c == post_c
    assert pre_s == post_s


def test_prior_processed_datasets_remain_unchanged(temp_dirs):
    # Create a dummy prior processed file
    prior_file = temp_dirs["processed_dir"] / "processed_patient_flow_daily.csv"
    prior_file.write_text("dummy")
    prior_checksum = _file_checksum(prior_file)
    _make_complaint_df([{"complaint_id": "C1"}]).to_csv(
        temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1"}]).to_csv(
        temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    main(
        project_root=str(Path(temp_dirs["tmp"])),
        source_dir="source",
        processed_dir="processed",
        log_dir="log",
        execute_export=True,
        dry_run=False,
    )
    post_checksum = _file_checksum(prior_file)
    assert prior_checksum == post_checksum


def _file_checksum(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


# ---------------------------------------------------------------------------
# 65. Deterministic repeated processing
# ---------------------------------------------------------------------------

def test_repeated_processing_gives_deterministic_business_results(temp_dirs):
    _make_complaint_df([
        {"complaint_id": "C1", "complaint_received_date": "2026-01-15"},
        {"complaint_id": "C2", "complaint_received_date": "2026-01-15"},
    ]).to_csv(temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([
        {"survey_id": "S1", "survey_date": "2026-01-15"},
    ]).to_csv(temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    result1 = main(
        project_root=str(Path(temp_dirs["tmp"])),
        source_dir="source",
        processed_dir="processed",
        log_dir="log",
        execute_export=True,
        dry_run=False,
    )
    log2 = temp_dirs["log_dir"] / "run2"
    log2.mkdir()
    shutil.copy(temp_dirs["log_dir"] / "step_2d3_closure_manifest.json", log2)
    result2 = main(
        project_root=str(Path(temp_dirs["tmp"])),
        source_dir="source",
        processed_dir="processed",
        log_dir=str(log2),
        execute_export=True,
        dry_run=False,
    )
    assert result1["success"] and result2["success"]
    d1 = result1["daily_dataframe"].sort_values("patient_experience_daily_id").reset_index(drop=True)
    d2 = result2["daily_dataframe"].sort_values("patient_experience_daily_id").reset_index(drop=True)
    cols = [c for c in d1.columns if c not in ["processing_run_id", "processed_datetime"]]
    pd.testing.assert_frame_equal(d1[cols], d2[cols])


# ---------------------------------------------------------------------------
# 66-73. Control outputs created
# ---------------------------------------------------------------------------

def test_manifest_is_created(temp_dirs):
    _make_complaint_df([{"complaint_id": "C1"}]).to_csv(
        temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1"}]).to_csv(
        temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    main(
        project_root=str(Path(temp_dirs["tmp"])),
        source_dir="source",
        processed_dir="processed",
        log_dir="log",
        execute_export=True,
        dry_run=False,
    )
    assert (temp_dirs["log_dir"] / "patient_experience_processing_run_manifest.json").exists()


def test_dataset_summary_created(temp_dirs):
    _make_complaint_df([{"complaint_id": "C1"}]).to_csv(
        temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1"}]).to_csv(
        temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    main(
        project_root=str(Path(temp_dirs["tmp"])),
        source_dir="source",
        processed_dir="processed",
        log_dir="log",
        execute_export=True,
        dry_run=False,
    )
    assert (temp_dirs["log_dir"] / "patient_experience_processing_dataset_summary.csv").exists()


def test_issue_log_created(temp_dirs):
    _make_complaint_df([{"complaint_id": "C1"}]).to_csv(
        temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1"}]).to_csv(
        temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    main(
        project_root=str(Path(temp_dirs["tmp"])),
        source_dir="source",
        processed_dir="processed",
        log_dir="log",
        execute_export=True,
        dry_run=False,
    )
    assert (temp_dirs["log_dir"] / "patient_experience_processing_issue_log.csv").exists()


def test_record_issue_log_created(temp_dirs):
    _make_complaint_df([{"complaint_id": "C1"}]).to_csv(
        temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1"}]).to_csv(
        temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    main(
        project_root=str(Path(temp_dirs["tmp"])),
        source_dir="source",
        processed_dir="processed",
        log_dir="log",
        execute_export=True,
        dry_run=False,
    )
    assert (temp_dirs["log_dir"] / "patient_experience_processing_record_issue_log.csv").exists()


def test_lineage_output_created(temp_dirs):
    _make_complaint_df([{"complaint_id": "C1"}]).to_csv(
        temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1"}]).to_csv(
        temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    main(
        project_root=str(Path(temp_dirs["tmp"])),
        source_dir="source",
        processed_dir="processed",
        log_dir="log",
        execute_export=True,
        dry_run=False,
    )
    assert (temp_dirs["log_dir"] / "patient_experience_processing_lineage.csv").exists()


def test_exclusion_register_created(temp_dirs):
    _make_complaint_df([{"complaint_id": "C1"}]).to_csv(
        temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1"}]).to_csv(
        temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    main(
        project_root=str(Path(temp_dirs["tmp"])),
        source_dir="source",
        processed_dir="processed",
        log_dir="log",
        execute_export=True,
        dry_run=False,
    )
    assert (temp_dirs["log_dir"] / "patient_experience_processing_exclusion_register.csv").exists()


def test_audit_log_created(temp_dirs):
    _make_complaint_df([{"complaint_id": "C1"}]).to_csv(
        temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1"}]).to_csv(
        temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    main(
        project_root=str(Path(temp_dirs["tmp"])),
        source_dir="source",
        processed_dir="processed",
        log_dir="log",
        execute_export=True,
        dry_run=False,
    )
    assert (temp_dirs["log_dir"] / "patient_experience_processing_audit_log.csv").exists()


def test_relationship_summary_created(temp_dirs):
    _make_complaint_df([{"complaint_id": "C1"}]).to_csv(
        temp_dirs["source_dir"] / "patient_complaints.csv", index=False)
    _make_survey_df([{"survey_id": "S1"}]).to_csv(
        temp_dirs["source_dir"] / "patient_surveys.csv", index=False)
    main(
        project_root=str(Path(temp_dirs["tmp"])),
        source_dir="source",
        processed_dir="processed",
        log_dir="log",
        execute_export=True,
        dry_run=False,
    )
    assert (temp_dirs["log_dir"] / "patient_experience_processing_relationship_summary.csv").exists()
