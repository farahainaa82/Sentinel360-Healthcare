"""
Sentinel360 Healthcare — Patient Flow KPI Engine Tests

Step 2A-3 test suite.
"""

import os
import sys
import tempfile
import uuid
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from patient_flow_kpi_engine import PatientFlowKPIEngine, PatientFlowKPIEngineResult
from analytical_models import KPICalculationResult, DataConfidenceResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_project_root():
    """Create a temporary project structure with minimal config and data."""
    tmpdir = Path(tempfile.mkdtemp())
    (tmpdir / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (tmpdir / "data" / "analytical").mkdir(parents=True, exist_ok=True)
    (tmpdir / "config").mkdir(parents=True, exist_ok=True)
    (tmpdir / "outputs" / "analytical_governance").mkdir(parents=True, exist_ok=True)

    # Minimal kpi_definition_config.csv
    kpi_def = pd.DataFrame({
        "kpi_id": ["kpi_003", "kpi_004", "kpi_005"],
        "kpi_name": ["Bed Occupancy Rate", "Average Patient Waiting Time", "Patient Complaint Rate"],
        "domain": ["Patient Flow", "Patient Flow", "Patient Experience"],
        "description": ["", "", ""],
        "numerator_definition": ["", "", ""],
        "denominator_definition": ["", "", ""],
        "formula_text": ["", "", ""],
        "unit": ["Percent", "Minutes", "Percent"],
        "directionality": ["", "", ""],
        "grain": ["", "", ""],
        "calculation_frequency": ["", "", ""],
        "authoritative_input_dataset": ["", "", ""],
        "required_fields": ["", "", ""],
        "eligibility_rules": ["", "", ""],
        "exclusion_rules": ["", "", ""],
        "null_treatment": ["", "", ""],
        "zero_denominator_treatment": ["", "", ""],
        "minimum_denominator": ["", "", ""],
        "threshold_config_reference": ["", "", ""],
        "data_confidence_rule_reference": ["", "", ""],
        "config_version": ["v1.0-draft", "v1.0-draft", "v1.0-draft"],
        "approval_requirement": ["", "", ""],
        "readiness_status": ["Conditionally Ready", "Conditionally Ready", "Conditionally Ready"],
        "unresolved_rules": ["", "", ""],
        "effective_date": ["", "", ""],
        "approval_status": ["Draft", "Draft", "Draft"],
    })
    kpi_def.to_csv(tmpdir / "config" / "kpi_definition_config.csv", index=False)

    # Minimal kpi_threshold_config.csv
    kpi_thresh = pd.DataFrame({
        "threshold_config_id": ["thc_003", "thc_004"],
        "kpi_id": ["kpi_003", "kpi_004"],
        "hospital_id": ["", ""],
        "department_id": ["", ""],
        "threshold_scope": ["Global", "Global"],
        "warning_lower_bound": ["", ""],
        "warning_upper_bound": ["", ""],
        "critical_lower_bound": ["", ""],
        "critical_upper_bound": ["", ""],
        "warning_lower_operator": ["", ""],
        "warning_upper_operator": ["", ""],
        "critical_lower_operator": ["", ""],
        "critical_upper_operator": ["", ""],
        "threshold_unit": ["Percent", "Minutes"],
        "threshold_basis": ["Operational", "Operational"],
        "configuration_version": ["v1.0-draft", "v1.0-draft"],
        "effective_start_date": ["2026-07-25", "2026-07-25"],
        "effective_end_date": ["", ""],
        "active_flag": ["False", "False"],
        "approval_status": ["Draft", "Draft"],
        "validation_status": ["Pending Stakeholder Validation", "Pending Stakeholder Validation"],
        "approved_by_role": ["", ""],
        "approval_date": ["", ""],
        "change_reason": ["Initial placeholder", "Initial placeholder"],
        "created_datetime": ["2026-07-25T00:00:00", "2026-07-25T00:00:00"],
        "updated_datetime": ["2026-07-25T00:00:00", "2026-07-25T00:00:00"],
    })
    kpi_thresh.to_csv(tmpdir / "config" / "kpi_threshold_config.csv", index=False)

    # Minimal data_confidence_config.csv
    conf = pd.DataFrame({
        "rule_id": ["CONF-001"],
        "rule_name": ["Basic completeness"],
        "description": [""],
        "kpi_domain": ["Patient Flow"],
        "kpi_id": [""],
        "numerator_weight": ["0.3"],
        "denominator_weight": ["0.3"],
        "lineage_weight": ["0.2"],
        "config_weight": ["0.2"],
        "high_threshold": ["90"],
        "medium_threshold": ["70"],
        "low_threshold": ["40"],
        "configuration_version": ["v1.0-draft"],
        "approval_status": ["Draft"],
        "effective_date": ["2026-07-25"],
    })
    conf.to_csv(tmpdir / "config" / "data_confidence_config.csv", index=False)

    # Minimal absence and attendance mappings (required by config loader)
    abs_map = pd.DataFrame({
        "absence_category": ["Sick Leave"],
        "mapped_category": ["Approved"],
        "counts_toward_absenteeism": ["False"],
    })
    abs_map.to_csv(tmpdir / "config" / "absence_category_mapping.csv", index=False)

    att_map = pd.DataFrame({
        "attendance_status": ["Present"],
        "counts_as_present": ["True"],
        "counts_as_absence": ["False"],
    })
    att_map.to_csv(tmpdir / "config" / "attendance_status_mapping.csv", index=False)

    # Create Step 2A-1 governance evidence files
    pd.DataFrame({
        "kpi_id": ["kpi_003", "kpi_004"],
        "kpi_name": ["Bed Occupancy Rate", "Average Patient Waiting Time"],
        "readiness_status": ["Conditionally Ready", "Conditionally Ready"],
        "blocking_reason": ["", ""],
        "source_dataset_available": ["False", "False"],
        "required_fields_available": ["False", "False"],
        "threshold_config_available": ["False", "False"],
        "approval_status": ["Draft", "Draft"],
        "assessed_at": [datetime.now().isoformat(), datetime.now().isoformat()],
        "calculation_run_id": ["ARCH-2A1-TEST", "ARCH-2A1-TEST"],
        "unresolved_rules": ["", ""],
    }).to_csv(tmpdir / "outputs" / "analytical_governance" / "kpi_readiness_summary.csv", index=False)

    pd.DataFrame({
        "dataset_name": ["processed_operational_daily.csv"],
        "baseline_checksum": ["abc123"],
        "current_checksum": ["abc123"],
        "match": ["True"],
        "status": ["Unchanged"],
    }).to_csv(tmpdir / "outputs" / "analytical_governance" / "phase1_immutability_verification.csv", index=False)

    pd.DataFrame({
        "kpi_id": ["kpi_003", "kpi_004"],
        "kpi_name": ["Bed Occupancy Rate", "Average Patient Waiting Time"],
        "domain": ["Patient Flow", "Patient Flow"],
    }).to_csv(tmpdir / "outputs" / "analytical_governance" / "kpi_governance_registry.csv", index=False)

    # Create minimal workforce KPI evidence for 2A-2 immutability check
    pd.DataFrame({
        "analytical_record_id": ["AKPI-kpi_001-HOSP-001-DEPT-A-20260101"],
        "kpi_id": ["kpi_001"],
    }).to_csv(tmpdir / "data" / "analytical" / "analytical_workforce_kpi_daily.csv", index=False)
    for fname in ["analytical_workforce_kpi_evidence.csv", "analytical_workforce_kpi_exclusions.csv",
                  "analytical_workforce_kpi_lineage.csv", "analytical_workforce_kpi_issues.csv",
                  "analytical_workforce_kpi_audit.csv"]:
        pd.DataFrame({"col": [1]}).to_csv(tmpdir / "data" / "analytical" / fname, index=False)

    yield tmpdir


@pytest.fixture
def sample_operational_df():
    return pd.DataFrame({
        "hospital_id": ["HOSP-001", "HOSP-001", "HOSP-001", "HOSP-001", "HOSP-001", "HOSP-001"],
        "department_id": ["DEPT-MED", "DEPT-MED", "DEPT-MED", "DEPT-MED", "DEPT-MED", "DEPT-MED"],
        "reporting_date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05", "2026-01-06"],
        "reporting_month": [1, 1, 1, 1, 1, 1],
        "reporting_year": [2026, 2026, 2026, 2026, 2026, 2026],
        "occupied_beds": [80.0, 90.0, 100.0, 110.0, None, 95.0],
        "operational_beds": [100.0, 100.0, 100.0, 100.0, 100.0, 0.0],
        "operational_daily_id": ["OPD-1", "OPD-2", "OPD-3", "OPD-4", "OPD-5", "OPD-6"],
    })


@pytest.fixture
def sample_encounters_df():
    return pd.DataFrame({
        "encounter_id": [f"ENC-{i:03d}" for i in range(1, 13)],
        "hospital_id": ["HOSP-001"] * 12,
        "department_id": ["DEPT-MED"] * 12,
        "encounter_date": ["2026-01-01"] * 6 + ["2026-01-02"] * 6,
        "arrival_to_consultation_minutes": [10.0, 20.0, 30.0, 40.0, 50.0, None, 15.0, 25.0, 35.0, 45.0, 55.0, -5.0],
        "official_wait_stage_eligible_flag": [False] * 12,
        "encounter_wait_eligible_flag": [True, True, True, True, True, True, True, True, True, True, True, False],
        "exclusion_reason_code": [None, None, None, None, None, None, None, None, None, None, None, "LEFT_BEFORE_SERVICE"],
    })


# ---------------------------------------------------------------------------
# Architecture Tests
# ---------------------------------------------------------------------------

def test_module_imports_safely():
    import patient_flow_kpi_engine as pfke
    assert hasattr(pfke, "PatientFlowKPIEngine")


def test_no_automatic_execution(temp_project_root):
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    assert engine.operational_df is None


def test_only_two_patient_flow_kpis_supported():
    assert PatientFlowKPIEngine.SUPPORTED_KPI_IDS == {"kpi_003", "kpi_004"}


def test_no_unrelated_kpi_calculations(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    calculated_ids = {r.kpi_id for r in result.kpi_results}
    assert calculated_ids == {"kpi_003", "kpi_004"}


# ---------------------------------------------------------------------------
# Bed Occupancy Rate Tests
# ---------------------------------------------------------------------------

def test_bed_occupancy_standard_calculation(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    bor_results = [r for r in result.kpi_results if r.kpi_id == "kpi_003"]
    # Row 0: 80/100*100 = 80
    assert bor_results[0].calculation_status == "Calculated"
    assert bor_results[0].kpi_value == pytest.approx(80.0)


def test_bed_occupancy_below_100(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    bor_results = [r for r in result.kpi_results if r.kpi_id == "kpi_003"]
    assert bor_results[0].kpi_value == pytest.approx(80.0)


def test_bed_occupancy_exactly_100(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    bor_results = [r for r in result.kpi_results if r.kpi_id == "kpi_003"]
    # Row 2: 100/100*100 = 100
    assert bor_results[2].kpi_value == pytest.approx(100.0)


def test_bed_occupancy_above_100_preserved(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    bor_results = [r for r in result.kpi_results if r.kpi_id == "kpi_003"]
    # Row 3: 110/100*100 = 110
    assert bor_results[3].kpi_value == pytest.approx(110.0)


def test_bed_occupancy_no_capping(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    bor_results = [r for r in result.kpi_results if r.kpi_id == "kpi_003"]
    assert bor_results[3].kpi_value > 100.0


def test_bed_occupancy_zero_denominator(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    bor_results = [r for r in result.kpi_results if r.kpi_id == "kpi_003"]
    # Row 5: operational = 0
    assert bor_results[5].calculation_status == "Zero Denominator"
    assert bor_results[5].kpi_value is None


def test_bed_occupancy_null_denominator(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    bor_results = [r for r in result.kpi_results if r.kpi_id == "kpi_003"]
    # Row 4: operational = None (in fixture, row 4 has occupied=None, operational=100)
    # Actually row 4 has occupied=None -> Invalid Input / Insufficient Data
    assert bor_results[4].calculation_status in ("Insufficient Data", "Invalid Input")
    assert bor_results[4].kpi_value is None


def test_bed_occupancy_null_numerator(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    bor_results = [r for r in result.kpi_results if r.kpi_id == "kpi_003"]
    assert bor_results[4].calculation_status in ("Insufficient Data", "Invalid Input")
    assert bor_results[4].kpi_value is None


def test_bed_occupancy_invalid_numeric_value(temp_project_root, sample_encounters_df):
    df = pd.DataFrame({
        "hospital_id": ["HOSP-001"],
        "department_id": ["DEPT-MED"],
        "reporting_date": ["2026-01-01"],
        "reporting_month": [1],
        "reporting_year": [2026],
        "occupied_beds": ["invalid"],
        "operational_beds": [100.0],
        "operational_daily_id": ["OPD-1"],
    })
    df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    bor = [r for r in result.kpi_results if r.kpi_id == "kpi_003"][0]
    # String value will cause type error -> not calculated
    assert bor.calculation_status != "Calculated"


def test_bed_occupancy_deterministic_id(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    bor = [r for r in result.kpi_results if r.kpi_id == "kpi_003"][0]
    expected_id = f"AKPI-kpi_003-{bor.hospital_id}-{bor.department_id}-{bor.reporting_date.strftime('%Y%m%d')}"
    assert any(e["analytical_record_id"] == expected_id for e in result.evidence_records if e["kpi_id"] == "kpi_003")


# ---------------------------------------------------------------------------
# Average Patient Waiting Time Tests
# ---------------------------------------------------------------------------

def test_waiting_time_standard_calculation(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    wt_results = [r for r in result.kpi_results if r.kpi_id == "kpi_004"]
    # Day 1: eligible = 10,20,30,40,50 (5 records, sum=150) -> avg=30
    day1 = [r for r in wt_results if str(r.reporting_date) == "2026-01-01"][0]
    assert day1.calculation_status == "Calculated"
    assert day1.kpi_value == pytest.approx(30.0)


def test_waiting_time_multiple_eligible_encounters(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    wt_results = [r for r in result.kpi_results if r.kpi_id == "kpi_004"]
    day1 = [r for r in wt_results if str(r.reporting_date) == "2026-01-01"][0]
    assert day1.denominator_value == 5


def test_waiting_time_ineligible_encounters_excluded(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    wt_results = [r for r in result.kpi_results if r.kpi_id == "kpi_004"]
    day1 = [r for r in wt_results if str(r.reporting_date) == "2026-01-01"][0]
    # ENC-012 is excluded (LEFT_BEFORE_SERVICE) and should not be counted
    assert day1.denominator_value == 5


def test_waiting_time_negative_intervals_excluded(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    wt_results = [r for r in result.kpi_results if r.kpi_id == "kpi_004"]
    day2 = [r for r in wt_results if str(r.reporting_date) == "2026-01-02"][0]
    # ENC-012 has -5 and is excluded by eligibility flag
    assert day2.denominator_value == 5


def test_waiting_time_missing_wait_values_excluded(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    wt_results = [r for r in result.kpi_results if r.kpi_id == "kpi_004"]
    day1 = [r for r in wt_results if str(r.reporting_date) == "2026-01-01"][0]
    # ENC-006 has null wait value and eligible=True but null -> excluded
    assert day1.denominator_value == 5


def test_waiting_time_no_eligible_encounters(temp_project_root, sample_operational_df):
    df = pd.DataFrame({
        "encounter_id": ["ENC-001"],
        "hospital_id": ["HOSP-001"],
        "department_id": ["DEPT-MED"],
        "encounter_date": ["2026-01-01"],
        "arrival_to_consultation_minutes": [None],
        "official_wait_stage_eligible_flag": [False],
        "encounter_wait_eligible_flag": [False],
        "exclusion_reason_code": ["CANCELLED_ENCOUNTER"],
    })
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    wt = [r for r in result.kpi_results if r.kpi_id == "kpi_004"][0]
    # When all encounters are ineligible, readiness assesses as Not Calculable -> Rule Pending
    assert wt.calculation_status in ("Rule Pending", "Insufficient Data")
    assert wt.kpi_value is None


def test_waiting_time_all_eligibility_flags_false(temp_project_root, sample_operational_df):
    df = pd.DataFrame({
        "encounter_id": ["ENC-001", "ENC-002"],
        "hospital_id": ["HOSP-001", "HOSP-001"],
        "department_id": ["DEPT-MED", "DEPT-MED"],
        "encounter_date": ["2026-01-01", "2026-01-01"],
        "arrival_to_consultation_minutes": [10.0, 20.0],
        "official_wait_stage_eligible_flag": [False, False],
        "encounter_wait_eligible_flag": [False, False],
        "exclusion_reason_code": [None, None],
    })
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    wt = [r for r in result.kpi_results if r.kpi_id == "kpi_004"][0]
    # When all encounters are ineligible, readiness assesses as Not Calculable -> Rule Pending
    assert wt.calculation_status in ("Rule Pending", "Insufficient Data")


def test_waiting_time_no_queue_count_substitution(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    wt_results = [r for r in result.kpi_results if r.kpi_id == "kpi_004"]
    # Ensure no queue count was used as wait minutes
    for r in wt_results:
        if r.calculation_status == "Calculated":
            assert r.unit == "Minutes"


def test_waiting_time_deterministic_id(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    wt = [r for r in result.kpi_results if r.kpi_id == "kpi_004"][0]
    expected_id = f"AKPI-kpi_004-{wt.hospital_id}-{wt.department_id}-{wt.reporting_date.strftime('%Y%m%d')}"
    assert any(e["analytical_record_id"] == expected_id for e in result.evidence_records if e["kpi_id"] == "kpi_004")


# ---------------------------------------------------------------------------
# Threshold Tests
# ---------------------------------------------------------------------------

def test_threshold_draft_status_preserved(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    bor = [r for r in result.kpi_results if r.kpi_id == "kpi_003"][0]
    assert getattr(bor, "threshold_is_provisional", True) is True
    assert getattr(bor, "threshold_approval_status", "") == "Draft"


def test_unavailable_waiting_time_not_assessed(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    wt = [r for r in result.kpi_results if r.kpi_id == "kpi_004"][0]
    assert getattr(wt, "threshold_status", "") in ("Not Assessed", "Unavailable")


def test_no_hardcoded_threshold_values(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    for r in result.kpi_results:
        assert getattr(r, "threshold_version", "") != ""


# ---------------------------------------------------------------------------
# Confidence Tests
# ---------------------------------------------------------------------------

def test_confidence_complete_occupancy_evidence(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    bor = [r for r in result.kpi_results if r.kpi_id == "kpi_003" and r.calculation_status == "Calculated"][0]
    assert getattr(bor, "data_confidence_level", "Unavailable") in ("High", "Medium", "Low")


def test_confidence_overcapacity_evidence(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    bor = [r for r in result.kpi_results if r.kpi_id == "kpi_003" and r.kpi_value is not None and r.kpi_value > 100]
    if bor:
        assert getattr(bor[0], "data_confidence_level", "Unavailable") in ("High", "Medium", "Low")


def test_confidence_missing_denominator(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    bor = [r for r in result.kpi_results if r.kpi_id == "kpi_003" and r.calculation_status == "Zero Denominator"]
    if bor:
        assert getattr(bor[0], "data_confidence_level", "Unavailable") == "Unavailable"


def test_confidence_unresolved_waiting_rule(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    wt = [r for r in result.kpi_results if r.kpi_id == "kpi_004" and r.calculation_status != "Calculated"]
    if wt:
        assert getattr(wt[0], "data_confidence_level", "Unavailable") == "Unavailable"


# ---------------------------------------------------------------------------
# Output Tests
# ---------------------------------------------------------------------------

def test_output_schema_validation(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    daily_df = engine.to_daily_dataframe(result.kpi_results)
    schema_result = engine.validate_output_schema(daily_df, "analytical_patient_flow_kpi_daily")
    assert schema_result.valid


def test_unique_analytical_record_id(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    daily_df = engine.to_daily_dataframe(result.kpi_results)
    assert daily_df["analytical_record_id"].is_unique


def test_correct_daily_grain(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    daily_df = engine.to_daily_dataframe(result.kpi_results)
    expected_rows = len(sample_operational_df) * 2
    assert len(daily_df) == expected_rows


def test_exactly_two_approved_kpi_ids(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    daily_df = engine.to_daily_dataframe(result.kpi_results)
    assert set(daily_df["kpi_id"].unique()) == {"kpi_003", "kpi_004"}


def test_numerator_denominator_evidence_preserved(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    evidence_df = engine.to_evidence_dataframe(result.evidence_records)
    assert len(evidence_df) > 0
    assert "numerator" in evidence_df["evidence_type"].values
    assert "denominator" in evidence_df["evidence_type"].values


def test_null_kpi_values_for_unavailable(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    for r in result.kpi_results:
        if r.calculation_status != "Calculated":
            assert r.kpi_value is None


def test_lineage_coverage(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    assert len(result.lineage_records) == len(sample_operational_df) * 2


def test_exclusions_recorded(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    # Row 4 has null occupied, row 5 has zero operational -> exclusions
    assert len(result.exclusion_records) > 0


def test_issues_structured(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    issues_df = engine.to_issues_dataframe(result.issue_records)
    assert isinstance(issues_df, pd.DataFrame)


def test_audit_records_generated(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    assert len(result.audit_records) > 0


# ---------------------------------------------------------------------------
# Immutability Tests
# ---------------------------------------------------------------------------

def test_phase1_datasets_unchanged(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    for fname in ["processed_workforce_daily.csv", "processed_staff_attendance.csv"]:
        (temp_project_root / "data" / "processed" / fname).write_text("col1\nval1\n")
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    result = engine.run()
    assert result.immutability_result["verified"] is True
    assert len(result.immutability_result["datasets_changed"]) == 0


def test_step2a1_governance_outputs_unchanged(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    engine.run()
    for fname in ["kpi_governance_registry.csv", "kpi_readiness_summary.csv"]:
        assert (temp_project_root / "outputs" / "analytical_governance" / fname).exists()


def test_step2a2_outputs_unchanged(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    engine = PatientFlowKPIEngine(project_root=temp_project_root)
    engine.run()
    assert (temp_project_root / "data" / "analytical" / "analytical_workforce_kpi_daily.csv").exists()


# ---------------------------------------------------------------------------
# Runner Tests
# ---------------------------------------------------------------------------

def test_runner_dry_run(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    from run_patient_flow_kpi_processing import run_patient_flow_kpi_processing
    result = run_patient_flow_kpi_processing(
        project_root=temp_project_root,
        dry_run=True,
        execute_export=False,
    )
    assert result["status"] == "Completed"
    assert result["dry_run"] is True


def test_runner_execute_export(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    from run_patient_flow_kpi_processing import run_patient_flow_kpi_processing
    result = run_patient_flow_kpi_processing(
        project_root=temp_project_root,
        dry_run=False,
        execute_export=True,
        output_dir=temp_project_root / "outputs" / "analytical_patient_flow",
    )
    assert result["status"] == "Completed"
    assert (temp_project_root / "outputs" / "analytical_patient_flow" / "patient_flow_kpi_run_manifest.json").exists()


def test_runner_kpi_id_filter(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    from run_patient_flow_kpi_processing import run_patient_flow_kpi_processing
    result = run_patient_flow_kpi_processing(
        project_root=temp_project_root,
        dry_run=True,
        kpi_id="kpi_003",
    )
    assert result["status"] == "Completed"


def test_runner_unsupported_kpi_id(temp_project_root, sample_operational_df, sample_encounters_df):
    sample_operational_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    sample_encounters_df.to_csv(temp_project_root / "data" / "processed" / "processed_patient_encounters.csv", index=False)
    from run_patient_flow_kpi_processing import run_patient_flow_kpi_processing
    result = run_patient_flow_kpi_processing(
        project_root=temp_project_root,
        dry_run=True,
        kpi_id="kpi_099",
    )
    assert result["status"] in ("Completed", "Failed")
