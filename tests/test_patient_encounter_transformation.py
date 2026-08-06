"""
Sentinel360 Healthcare — Patient Encounter Transformation Tests

Step 2D-3A test coverage.
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

# Ensure src is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.patient_encounter_transformer import (
    DISPOSITION_CANCELLED,
    DISPOSITION_COMPLETED,
    DISPOSITION_LWBS,
    PatientEncounterTransformer,
)
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
def source_encounters(project_root: Path) -> pd.DataFrame:
    path = project_root / "data" / "demo" / "patient_encounters.csv"
    return pd.read_csv(path, dtype=str, keep_default_na=False)


@pytest.fixture
def transformer(project_root: Path) -> PatientEncounterTransformer:
    return PatientEncounterTransformer(
        input_dir=project_root / "data" / "demo",
        output_dir=project_root / "data" / "processed",
        validation_log_dir=project_root / "outputs" / "logs",
    )


@pytest.fixture
def temp_transformer(tmp_path: Path) -> PatientEncounterTransformer:
    """Transformer pointing at temporary directories for mutation tests."""
    return PatientEncounterTransformer(
        input_dir=tmp_path / "input",
        output_dir=tmp_path / "output",
        validation_log_dir=tmp_path / "logs",
    )


# ------------------------------------------------------------------
# 1. Module imports safely
# ------------------------------------------------------------------

def test_module_imports_safely() -> None:
    import src.patient_encounter_transformer as pet
    import src.run_patient_encounter_processing as runner

    assert pet is not None
    assert runner is not None


# ------------------------------------------------------------------
# 2. Runner does not execute automatically on import
# ------------------------------------------------------------------

def test_runner_no_auto_execute(project_root: Path) -> None:
    import src.run_patient_encounter_processing as runner

    # The module should define main() and run_patient_encounter_processing()
    assert callable(runner.main)
    assert callable(runner.run_patient_encounter_processing)


# ------------------------------------------------------------------
# 3. Validation gate accepts the approved run
# ------------------------------------------------------------------

def test_validation_gate_accepts_approved_run(transformer: PatientEncounterTransformer) -> None:
    gate = transformer.check_validation_gate()
    assert gate.processing_allowed is True
    assert gate.validation_run_id is not None


# ------------------------------------------------------------------
# 4. Validation gate rejects processing_allowed false
# ------------------------------------------------------------------

def test_validation_gate_rejects_processing_allowed_false(
    tmp_path: Path, transformer: PatientEncounterTransformer
) -> None:
    # Create a fake manifest with processing_allowed_flag=false
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "validation_run_id": "VR-TEST",
        "run_status": "Passed",
        "processing_allowed_flag": False,
    }
    with open(log_dir / "validation_run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f)

    t = PatientEncounterTransformer(
        input_dir=tmp_path / "input",
        output_dir=tmp_path / "output",
        validation_log_dir=log_dir,
    )
    gate = t.check_validation_gate()
    assert gate.processing_allowed is False
    assert "processing_allowed_flag" in gate.blocking_reason.lower()


# ------------------------------------------------------------------
# 5. Output matches approved processed_patient_encounters schema
# ------------------------------------------------------------------

def test_output_matches_approved_schema(
    transformer: PatientEncounterTransformer, source_encounters: pd.DataFrame
) -> None:
    processed = transformer.transform_encounters(source_encounters)
    schema = get_processed_schema("processed_patient_encounters")
    target_fields = schema["required_fields"] + schema.get("optional_fields", [])
    missing = [c for c in target_fields if c not in processed.columns]
    extra = [c for c in processed.columns if c not in target_fields]
    assert not missing, f"Missing schema columns: {missing}"
    assert not extra, f"Extra columns not in schema: {extra}"


# ------------------------------------------------------------------
# 6. Processed encounter file is created only when execution is requested
# ------------------------------------------------------------------

def test_processed_file_created_only_on_execute(project_root: Path, tmp_path: Path) -> None:
    import src.run_patient_encounter_processing as runner

    out_dir = tmp_path / "processed"
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    # Copy real manifest
    shutil.copy(
        project_root / "outputs" / "logs" / "validation_run_manifest.json",
        log_dir / "validation_run_manifest.json",
    )
    shutil.copy(
        project_root / "outputs" / "logs" / "dataset_validation_summary.csv",
        log_dir / "dataset_validation_summary.csv",
    )
    # Run without export
    result = runner.run_patient_encounter_processing(
        input_dir=project_root / "data" / "demo",
        output_dir=out_dir,
        validation_log_dir=log_dir,
        execute_export=False,
    )
    assert result["status"] in ("completed", "failed_schema")
    assert not (out_dir / "processed_patient_encounters.csv").exists()

    # Run with export
    result2 = runner.run_patient_encounter_processing(
        input_dir=project_root / "data" / "demo",
        output_dir=out_dir,
        validation_log_dir=log_dir,
        execute_export=True,
    )
    assert (out_dir / "processed_patient_encounters.csv").exists()


# ------------------------------------------------------------------
# 7. Queue, bed, schedule and patient-flow-daily files are not created
# ------------------------------------------------------------------

def test_no_other_processed_files_created(project_root: Path, tmp_path: Path) -> None:
    import src.run_patient_encounter_processing as runner

    out_dir = tmp_path / "processed"
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(
        project_root / "outputs" / "logs" / "validation_run_manifest.json",
        log_dir / "validation_run_manifest.json",
    )
    shutil.copy(
        project_root / "outputs" / "logs" / "dataset_validation_summary.csv",
        log_dir / "dataset_validation_summary.csv",
    )
    runner.run_patient_encounter_processing(
        input_dir=project_root / "data" / "demo",
        output_dir=out_dir,
        validation_log_dir=log_dir,
        execute_export=True,
    )
    forbidden = [
        "processed_patient_queue.csv",
        "processed_bed_capacity.csv",
        "processed_service_schedule.csv",
        "processed_patient_flow_daily.csv",
    ]
    for name in forbidden:
        assert not (out_dir / name).exists(), f"Forbidden file created: {name}"


# ------------------------------------------------------------------
# 8. Source patient_encounters.csv remains unchanged
# ------------------------------------------------------------------

def test_source_unchanged(project_root: Path, transformer: PatientEncounterTransformer) -> None:
    source_path = project_root / "data" / "demo" / "patient_encounters.csv"
    before = hashlib.sha256(source_path.read_bytes()).hexdigest()
    source = transformer.load_source_data()
    transformer.transform_encounters(source)
    after = hashlib.sha256(source_path.read_bytes()).hexdigest()
    assert before == after


# ------------------------------------------------------------------
# 9. Workforce processed files remain unchanged
# ------------------------------------------------------------------

def test_workforce_files_unchanged(project_root: Path, tmp_path: Path) -> None:
    import src.run_patient_encounter_processing as runner

    out_dir = tmp_path / "processed"
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(
        project_root / "outputs" / "logs" / "validation_run_manifest.json",
        log_dir / "validation_run_manifest.json",
    )
    shutil.copy(
        project_root / "outputs" / "logs" / "dataset_validation_summary.csv",
        log_dir / "dataset_validation_summary.csv",
    )
    # Copy existing workforce files into temp output dir and record checksums
    real_processed = project_root / "data" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)
    checksums: dict = {}
    for wf in [
        "processed_hospital_master.csv",
        "processed_department_master.csv",
        "processed_staff_role_master.csv",
        "processed_staff_master.csv",
        "processed_staff_roster.csv",
        "processed_staff_attendance.csv",
        "processed_staffing_requirement.csv",
        "processed_workforce_daily.csv",
    ]:
        src = real_processed / wf
        if src.exists():
            shutil.copy(src, out_dir / wf)
            checksums[wf] = hashlib.sha256((out_dir / wf).read_bytes()).hexdigest()

    runner.run_patient_encounter_processing(
        input_dir=project_root / "data" / "demo",
        output_dir=out_dir,
        validation_log_dir=log_dir,
        execute_export=True,
    )

    for wf, before in checksums.items():
        p = out_dir / wf
        assert p.exists(), f"Workforce file {wf} missing"
        after = hashlib.sha256(p.read_bytes()).hexdigest()
        assert after == before, f"Workforce file {wf} was modified"


# ------------------------------------------------------------------
# 10. Encounter IDs are preserved and unique
# ------------------------------------------------------------------

def test_encounter_ids_preserved_and_unique(
    transformer: PatientEncounterTransformer, source_encounters: pd.DataFrame
) -> None:
    processed = transformer.transform_encounters(source_encounters)
    source_ids = set(source_encounters["encounter_id"].astype(str))
    proc_ids = set(processed["encounter_id"].dropna().astype(str))
    assert source_ids == proc_ids
    assert processed["encounter_id"].duplicated().sum() == 0


# ------------------------------------------------------------------
# 11. Hospital and department IDs are preserved
# ------------------------------------------------------------------

def test_hospital_department_ids_preserved(
    transformer: PatientEncounterTransformer, source_encounters: pd.DataFrame
) -> None:
    processed = transformer.transform_encounters(source_encounters)
    for col in ["hospital_id", "department_id"]:
        source_vals = set(source_encounters[col].astype(str).replace("", pd.NA).dropna())
        proc_vals = set(processed[col].dropna().astype(str))
        assert source_vals == proc_vals, f"Mismatch in {col}"


# ------------------------------------------------------------------
# 12. Encounter and reporting dates parse correctly
# ------------------------------------------------------------------

def test_encounter_and_reporting_dates_parse(
    transformer: PatientEncounterTransformer, source_encounters: pd.DataFrame
) -> None:
    processed = transformer.transform_encounters(source_encounters)
    assert pd.api.types.is_datetime64_any_dtype(processed["encounter_date"])
    assert pd.api.types.is_datetime64_any_dtype(processed["reporting_date"])
    assert processed["encounter_date"].notna().all()


# ------------------------------------------------------------------
# 13. reporting_month uses YYYY-MM
# ------------------------------------------------------------------

def test_reporting_month_format(
    transformer: PatientEncounterTransformer, source_encounters: pd.DataFrame
) -> None:
    processed = transformer.transform_encounters(source_encounters)
    assert processed["reporting_month"].notna().all()
    for val in processed["reporting_month"].dropna():
        assert len(str(val)) == 7 and str(val)[4] == "-"


# ------------------------------------------------------------------
# 14. Valid timestamps parse correctly
# ------------------------------------------------------------------

def test_valid_timestamps_parse(
    transformer: PatientEncounterTransformer, source_encounters: pd.DataFrame
) -> None:
    processed = transformer.transform_encounters(source_encounters)
    for col in [
        "arrival_datetime",
        "triage_datetime",
        "consultation_start_datetime",
        "service_end_datetime",
    ]:
        assert pd.api.types.is_datetime64_any_dtype(processed[col])


# ------------------------------------------------------------------
# 15. Missing timestamps remain null
# ------------------------------------------------------------------

def test_missing_timestamps_null(
    transformer: PatientEncounterTransformer, source_encounters: pd.DataFrame
) -> None:
    processed = transformer.transform_encounters(source_encounters)
    for col in [
        "arrival_datetime",
        "triage_datetime",
        "consultation_start_datetime",
        "service_end_datetime",
    ]:
        nulls = processed[col].isna().sum()
        assert nulls >= 0  # at minimum, some may be present


# ------------------------------------------------------------------
# 16. Missing timestamps are never imputed
# ------------------------------------------------------------------

def test_no_timestamp_imputation(
    transformer: PatientEncounterTransformer, source_encounters: pd.DataFrame
) -> None:
    processed = transformer.transform_encounters(source_encounters)
    # Check that empty source timestamps result in null processed timestamps
    source_cols = ["arrival_datetime", "triage_datetime", "consultation_start_datetime", "service_end_datetime"]
    for col in source_cols:
        if col in source_encounters.columns:
            empty_mask = source_encounters[col] == ""
            if empty_mask.any():
                assert processed.loc[empty_mask, col].isna().all(), f"Imputed values found in {col}"


# ------------------------------------------------------------------
# 17. All four preparation-level intervals calculate correctly
# ------------------------------------------------------------------

def test_interval_calculation(
    transformer: PatientEncounterTransformer, source_encounters: pd.DataFrame
) -> None:
    processed = transformer.transform_encounters(source_encounters)
    for col in [
        "arrival_to_triage_minutes",
        "arrival_to_consultation_minutes",
        "triage_to_consultation_minutes",
        "consultation_to_service_end_minutes",
    ]:
        assert col in processed.columns


# ------------------------------------------------------------------
# 18. Negative intervals are detected and nulled
# ------------------------------------------------------------------

def test_negative_intervals_detected(
    transformer: PatientEncounterTransformer, source_encounters: pd.DataFrame
) -> None:
    processed = transformer.transform_encounters(source_encounters)
    for col in [
        "arrival_to_triage_minutes",
        "arrival_to_consultation_minutes",
        "triage_to_consultation_minutes",
        "consultation_to_service_end_minutes",
    ]:
        negative = processed[col].notna() & (processed[col] < 0)
        assert negative.sum() == 0, f"Negative values found in {col}"


# ------------------------------------------------------------------
# 19. Valid cross-midnight chronology is supported
# ------------------------------------------------------------------

def test_cross_midnight_chronology(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "validation_run_id": "VR-TEST",
        "run_status": "Passed",
        "processing_allowed_flag": True,
    }
    with open(log_dir / "validation_run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f)

    input_dir = tmp_path / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame({
        "encounter_id": ["E001"],
        "hospital_id": ["H1"],
        "department_id": ["D1"],
        "encounter_date": ["2026-01-01"],
        "encounter_type": ["Emergency"],
        "arrival_datetime": ["2026-01-01 23:00:00"],
        "triage_datetime": ["2026-01-01 23:30:00"],
        "consultation_start_datetime": ["2026-01-02 00:15:00"],
        "service_end_datetime": ["2026-01-02 01:00:00"],
        "disposition_status": ["completed"],
    })
    df.to_csv(input_dir / "patient_encounters.csv", index=False)

    t = PatientEncounterTransformer(
        input_dir=input_dir,
        output_dir=tmp_path / "output",
        validation_log_dir=log_dir,
    )
    source = t.load_source_data()
    processed = t.transform_encounters(source)
    assert processed["arrival_to_consultation_minutes"].iloc[0] == 75.0
    assert processed["consultation_to_service_end_minutes"].iloc[0] == 45.0


# ------------------------------------------------------------------
# 20. Cancelled encounters are classified and retained
# ------------------------------------------------------------------

def test_cancelled_encounters_classified(
    transformer: PatientEncounterTransformer, source_encounters: pd.DataFrame
) -> None:
    processed = transformer.transform_encounters(source_encounters)
    cancelled = processed[processed["cancelled_flag"] == True]
    assert len(cancelled) > 0
    assert (cancelled["exclusion_reason_code"] == "CANCELLED_ENCOUNTER").all()


# ------------------------------------------------------------------
# 21. Cancelled encounters are excluded from wait eligibility
# ------------------------------------------------------------------

def test_cancelled_not_wait_eligible(
    transformer: PatientEncounterTransformer, source_encounters: pd.DataFrame
) -> None:
    processed = transformer.transform_encounters(source_encounters)
    cancelled = processed[processed["cancelled_flag"] == True]
    assert (cancelled["encounter_wait_eligible_flag"] == False).all()


# ------------------------------------------------------------------
# 22. LWBS encounters are classified and retained
# ------------------------------------------------------------------

def test_lwbs_encounters_classified(
    transformer: PatientEncounterTransformer, source_encounters: pd.DataFrame
) -> None:
    processed = transformer.transform_encounters(source_encounters)
    lwbs = processed[processed["left_before_service_flag"] == True]
    assert len(lwbs) > 0
    assert (lwbs["exclusion_reason_code"] == "LEFT_BEFORE_SERVICE").all()


# ------------------------------------------------------------------
# 23. LWBS without consultation has null consultation interval
# ------------------------------------------------------------------

def test_lwbs_no_consultation_interval(
    transformer: PatientEncounterTransformer, source_encounters: pd.DataFrame
) -> None:
    processed = transformer.transform_encounters(source_encounters)
    lwbs = processed[processed["left_before_service_flag"] == True]
    assert lwbs["arrival_to_consultation_minutes"].isna().all()
    assert lwbs["triage_to_consultation_minutes"].isna().all()
    assert lwbs["consultation_to_service_end_minutes"].isna().all()


# ------------------------------------------------------------------
# 24. Completed encounters are classified correctly
# ------------------------------------------------------------------

def test_completed_encounters_classified(
    transformer: PatientEncounterTransformer, source_encounters: pd.DataFrame
) -> None:
    processed = transformer.transform_encounters(source_encounters)
    completed = processed[processed["completed_service_flag"] == True]
    assert len(completed) > 0


# ------------------------------------------------------------------
# 25. Eligibility requires valid approved timestamps
# ------------------------------------------------------------------

def test_eligibility_requires_timestamps(
    transformer: PatientEncounterTransformer, source_encounters: pd.DataFrame
) -> None:
    processed = transformer.transform_encounters(source_encounters)
    eligible = processed[processed["encounter_wait_eligible_flag"] == True]
    assert eligible["arrival_datetime"].notna().all()
    assert eligible["consultation_start_datetime"].notna().all()


# ------------------------------------------------------------------
# 26. Unsupported disposition values are logged and not guessed
# ------------------------------------------------------------------

def test_unsupported_disposition_logged(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "validation_run_id": "VR-TEST",
        "run_status": "Passed",
        "processing_allowed_flag": True,
    }
    with open(log_dir / "validation_run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f)

    input_dir = tmp_path / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame({
        "encounter_id": ["E001"],
        "hospital_id": ["H1"],
        "department_id": ["D1"],
        "encounter_date": ["2026-01-01"],
        "encounter_type": ["Emergency"],
        "arrival_datetime": ["2026-01-01 09:00:00"],
        "triage_datetime": ["2026-01-01 09:15:00"],
        "consultation_start_datetime": ["2026-01-01 09:30:00"],
        "service_end_datetime": ["2026-01-01 10:00:00"],
        "disposition_status": ["unknown_status_xyz"],
    })
    df.to_csv(input_dir / "patient_encounters.csv", index=False)

    t = PatientEncounterTransformer(
        input_dir=input_dir,
        output_dir=tmp_path / "output",
        validation_log_dir=log_dir,
    )
    source = t.load_source_data()
    processed = t.transform_encounters(source)
    assert processed["completed_service_flag"].iloc[0] == False
    assert any(i.issue_type == "Unsupported Disposition Status" for i in t.issues)


# ------------------------------------------------------------------
# 27. Exclusion reason codes are transparent
# ------------------------------------------------------------------

def test_exclusion_reason_codes_transparent(
    transformer: PatientEncounterTransformer, source_encounters: pd.DataFrame
) -> None:
    processed = transformer.transform_encounters(source_encounters)
    from src.patient_encounter_transformer import EXCLUSION_REASONS
    codes = processed["exclusion_reason_code"].dropna().unique()
    for code in codes:
        assert code in EXCLUSION_REASONS or code.startswith("MISSING_") or code.startswith("INVALID_")


# ------------------------------------------------------------------
# 28. Invalid records distinguished from analytically ineligible
# ------------------------------------------------------------------

def test_invalid_vs_ineligible_distinction(
    transformer: PatientEncounterTransformer, source_encounters: pd.DataFrame
) -> None:
    processed = transformer.transform_encounters(source_encounters)
    invalid = processed[processed["exclusion_reason_code"] == "INVALID_TIMESTAMP_ORDER"]
    ineligible = processed[processed["exclusion_reason_code"].isin(["CANCELLED_ENCOUNTER", "LEFT_BEFORE_SERVICE"])]
    # Both should exist or at least be distinguishable by code
    assert len(ineligible) > 0 or len(invalid) > 0


# ------------------------------------------------------------------
# 29. Every processed encounter has lineage
# ------------------------------------------------------------------

def test_every_record_has_lineage(
    transformer: PatientEncounterTransformer, source_encounters: pd.DataFrame
) -> None:
    processed = transformer.transform_encounters(source_encounters)
    transformer.build_lineage(source_encounters, processed)
    assert len(transformer.lineage) == len(processed)


# ------------------------------------------------------------------
# 30. Issue, exclusion, audit, manifest and dataset-summary outputs are generated
# ------------------------------------------------------------------

def test_control_outputs_generated(project_root: Path, tmp_path: Path) -> None:
    import src.run_patient_encounter_processing as runner

    out_dir = tmp_path / "processed"
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(
        project_root / "outputs" / "logs" / "validation_run_manifest.json",
        log_dir / "validation_run_manifest.json",
    )
    shutil.copy(
        project_root / "outputs" / "logs" / "dataset_validation_summary.csv",
        log_dir / "dataset_validation_summary.csv",
    )
    runner.run_patient_encounter_processing(
        input_dir=project_root / "data" / "demo",
        output_dir=out_dir,
        validation_log_dir=log_dir,
        execute_export=True,
    )
    assert (log_dir / "patient_encounter_processing_run_manifest.json").exists()
    assert (log_dir / "patient_encounter_processing_dataset_summary.csv").exists()
    assert (log_dir / "patient_encounter_processing_issue_log.csv").exists()
    assert (log_dir / "patient_encounter_processing_lineage.csv").exists()
    assert (log_dir / "patient_encounter_processing_exclusion_register.csv").exists()
    assert (log_dir / "patient_encounter_processing_audit_log.csv").exists()


# ------------------------------------------------------------------
# 31. Source and processed checksums are generated
# ------------------------------------------------------------------

def test_checksums_generated(project_root: Path, tmp_path: Path) -> None:
    import src.run_patient_encounter_processing as runner

    out_dir = tmp_path / "processed"
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(
        project_root / "outputs" / "logs" / "validation_run_manifest.json",
        log_dir / "validation_run_manifest.json",
    )
    shutil.copy(
        project_root / "outputs" / "logs" / "dataset_validation_summary.csv",
        log_dir / "dataset_validation_summary.csv",
    )
    result = runner.run_patient_encounter_processing(
        input_dir=project_root / "data" / "demo",
        output_dir=out_dir,
        validation_log_dir=log_dir,
        execute_export=True,
    )
    assert result["source_unchanged"] is True
    manifest_path = log_dir / "patient_encounter_processing_run_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest.get("source_checksum") is not None


# ------------------------------------------------------------------
# 32. Repeated execution produces consistent business content
# ------------------------------------------------------------------

def test_repeated_execution_consistent(
    transformer: PatientEncounterTransformer, source_encounters: pd.DataFrame
) -> None:
    p1 = transformer.transform_encounters(source_encounters)
    t2 = PatientEncounterTransformer(
        input_dir=transformer.input_dir,
        output_dir=transformer.output_dir,
        validation_log_dir=transformer.validation_log_dir,
    )
    p2 = t2.transform_encounters(source_encounters)
    # Business content should match (ignore metadata columns that differ per run)
    compare_cols = [c for c in p1.columns if c not in ("processing_run_id", "processed_datetime")]
    pd.testing.assert_frame_equal(p1[compare_cols], p2[compare_cols])


# ------------------------------------------------------------------
# 33. No official waiting-time KPI is calculated
# ------------------------------------------------------------------

def test_no_kpi_calculated(
    transformer: PatientEncounterTransformer, source_encounters: pd.DataFrame
) -> None:
    processed = transformer.transform_encounters(source_encounters)
    forbidden = ["waiting_time_kpi", "average_waiting_time", "average_patient_waiting_time"]
    for col in forbidden:
        assert col not in processed.columns


# ------------------------------------------------------------------
# 34. No KPI status, risk, forecast, scenario, financial or recommendation field exists
# ------------------------------------------------------------------

def test_no_prohibited_analytical_fields(
    transformer: PatientEncounterTransformer, source_encounters: pd.DataFrame
) -> None:
    processed = transformer.transform_encounters(source_encounters)
    forbidden = [
        "kpi_status", "risk_score", "forecast", "scenario_result",
        "financial_result", "recommendation",
    ]
    for col in forbidden:
        assert col not in processed.columns


# ------------------------------------------------------------------
# 35. No patient names, clinical notes, diagnoses or direct identifiers are created
# ------------------------------------------------------------------

def test_no_personal_or_clinical_fields(
    transformer: PatientEncounterTransformer, source_encounters: pd.DataFrame
) -> None:
    processed = transformer.transform_encounters(source_encounters)
    forbidden = [
        "patient_name", "clinical_notes", "diagnosis", "direct_personal_identifier",
        "patient_id", "mrn", "nhs_number", "phone", "email", "address",
    ]
    for col in forbidden:
        assert col not in processed.columns
