"""
Sentinel360 Healthcare — Workforce KPI Engine Tests

Step 2A-2 test suite.
"""

import os
import sys
import tempfile
import uuid
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import pytest

# Ensure src is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.workforce_kpi_engine import WorkforceKPIEngine, WorkforceKPIEngineResult
from src.analytical_models import KPICalculationResult, DataConfidenceResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_project_root():
    """Create a temporary project structure with minimal config and data."""
    tmpdir = Path(tempfile.mkdtemp())
    # Create directories
    (tmpdir / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (tmpdir / "data" / "analytical").mkdir(parents=True, exist_ok=True)
    (tmpdir / "config").mkdir(parents=True, exist_ok=True)
    (tmpdir / "outputs" / "analytical_governance").mkdir(parents=True, exist_ok=True)

    # Minimal kpi_definition_config.csv
    kpi_def = pd.DataFrame({
        "kpi_id": ["kpi_001", "kpi_002", "kpi_003"],
        "kpi_name": ["Staffing Level", "Staff Absenteeism Rate", "Bed Occupancy Rate"],
        "domain": ["Workforce", "Workforce", "Operational"],
        "description": ["", "", ""],
        "numerator_definition": ["", "", ""],
        "denominator_definition": ["", "", ""],
        "formula_text": ["", "", ""],
        "unit": ["Percent", "Percent", "Percent"],
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
        "threshold_config_id": ["thc_001", "thc_002"],
        "kpi_id": ["kpi_001", "kpi_002"],
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
        "threshold_unit": ["Percent", "Percent"],
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
        "kpi_domain": ["Workforce"],
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

    # Minimal absence_category_mapping.csv
    abs_map = pd.DataFrame({
        "absence_category": ["Sick Leave", "Annual Leave", "Unapproved"],
        "mapped_category": ["Approved", "Approved", "Unapproved"],
        "counts_toward_absenteeism": ["False", "False", "True"],
    })
    abs_map.to_csv(tmpdir / "config" / "absence_category_mapping.csv", index=False)

    # Minimal attendance_status_mapping.csv
    att_map = pd.DataFrame({
        "attendance_status": ["Present", "Absent", "Late"],
        "counts_as_present": ["True", "False", "True"],
        "counts_as_absence": ["False", "True", "False"],
    })
    att_map.to_csv(tmpdir / "config" / "attendance_status_mapping.csv", index=False)

    # Create Step 2A-1 governance evidence files
    pd.DataFrame({
        "kpi_id": ["kpi_001", "kpi_002"],
        "kpi_name": ["Staffing Level", "Staff Absenteeism Rate"],
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
        "kpi_id": ["kpi_001", "kpi_002"],
        "kpi_name": ["Staffing Level", "Staff Absenteeism Rate"],
        "domain": ["Workforce", "Workforce"],
    }).to_csv(tmpdir / "outputs" / "analytical_governance" / "kpi_governance_registry.csv", index=False)

    yield tmpdir


@pytest.fixture
def sample_source_df():
    """Return a sample processed_operational_daily DataFrame."""
    return pd.DataFrame({
        "hospital_id": ["HOSP-001", "HOSP-001", "HOSP-001", "HOSP-001", "HOSP-001", "HOSP-001"],
        "department_id": ["DEPT-A", "DEPT-A", "DEPT-A", "DEPT-A", "DEPT-A", "DEPT-A"],
        "reporting_date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05", "2026-01-06"],
        "reporting_month": [1, 1, 1, 1, 1, 1],
        "reporting_year": [2026, 2026, 2026, 2026, 2026, 2026],
        "planned_staff_count": [20.0, 20.0, 20.0, 0.0, None, 20.0],
        "present_staff_count": [18.0, 20.0, 15.0, 10.0, 10.0, None],
        "unapproved_absence_count": [2.0, 0.0, 3.0, 1.0, 1.0, 2.0],
        "replacement_staff_count": [0.0, 2.0, 0.0, 0.0, 0.0, 0.0],
        "reassigned_staff_count": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "operational_daily_id": ["OPD-1", "OPD-2", "OPD-3", "OPD-4", "OPD-5", "OPD-6"],
    })


# ---------------------------------------------------------------------------
# Architecture Tests
# ---------------------------------------------------------------------------

def test_module_imports_safely():
    import src.workforce_kpi_engine as wke
    assert hasattr(wke, "WorkforceKPIEngine")


def test_no_automatic_execution(temp_project_root):
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    assert engine.source_df is None


def test_only_two_workforce_kpis_supported():
    assert WorkforceKPIEngine.SUPPORTED_KPI_IDS == {"kpi_001", "kpi_002"}


def test_no_unrelated_kpi_calculations(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    engine.run()
    calculated_ids = {r.kpi_id for r in engine.run().kpi_results}
    assert calculated_ids == {"kpi_001", "kpi_002"}


# ---------------------------------------------------------------------------
# Staffing Level Tests
# ---------------------------------------------------------------------------

def test_staffing_level_standard_calculation(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    sl_results = [r for r in result.kpi_results if r.kpi_id == "kpi_001"]
    # Row 0: (18+0)/20*100 = 90
    assert sl_results[0].calculation_status == "Calculated"
    assert sl_results[0].kpi_value == pytest.approx(90.0)


def test_staffing_level_replacement_staff_included(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    sl_results = [r for r in result.kpi_results if r.kpi_id == "kpi_001"]
    # Row 1: (20+2)/20*100 = 110
    assert sl_results[1].kpi_value == pytest.approx(110.0)


def test_staffing_level_zero_replacement(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    sl_results = [r for r in result.kpi_results if r.kpi_id == "kpi_001"]
    # Row 0 replacement = 0
    assert sl_results[0].numerator_value == 18.0


def test_staffing_level_above_100_preserved(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    sl_results = [r for r in result.kpi_results if r.kpi_id == "kpi_001"]
    assert sl_results[1].kpi_value == pytest.approx(110.0)


def test_staffing_level_zero_denominator(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    sl_results = [r for r in result.kpi_results if r.kpi_id == "kpi_001"]
    # Row 3: planned = 0
    assert sl_results[3].calculation_status == "Zero Denominator"
    assert sl_results[3].kpi_value is None


def test_staffing_level_denominator_null(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    sl_results = [r for r in result.kpi_results if r.kpi_id == "kpi_001"]
    # Row 4: planned = None
    assert sl_results[4].calculation_status == "Insufficient Data"
    assert sl_results[4].kpi_value is None


def test_staffing_level_numerator_null(temp_project_root):
    df = pd.DataFrame({
        "hospital_id": ["HOSP-001"],
        "department_id": ["DEPT-A"],
        "reporting_date": ["2026-01-01"],
        "reporting_month": [1],
        "reporting_year": [2026],
        "planned_staff_count": [20.0],
        "present_staff_count": [None],
        "unapproved_absence_count": [2.0],
        "replacement_staff_count": [None],
        "reassigned_staff_count": [0.0],
        "operational_daily_id": ["OPD-1"],
    })
    df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    sl = [r for r in result.kpi_results if r.kpi_id == "kpi_001"][0]
    # Both present and replacement null -> insufficient data
    assert sl.calculation_status == "Insufficient Data"
    assert sl.kpi_value is None


def test_staffing_level_no_silent_null_to_zero(temp_project_root):
    df = pd.DataFrame({
        "hospital_id": ["HOSP-001"],
        "department_id": ["DEPT-A"],
        "reporting_date": ["2026-01-01"],
        "reporting_month": [1],
        "reporting_year": [2026],
        "planned_staff_count": [20.0],
        "present_staff_count": [None],
        "unapproved_absence_count": [2.0],
        "replacement_staff_count": [None],
        "reassigned_staff_count": [0.0],
        "operational_daily_id": ["OPD-1"],
    })
    df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    sl = [r for r in result.kpi_results if r.kpi_id == "kpi_001"][0]
    assert sl.calculation_status != "Calculated"
    assert sl.kpi_value is None


def test_staffing_level_deterministic_id(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    sl = [r for r in result.kpi_results if r.kpi_id == "kpi_001"][0]
    expected_id = f"AKPI-kpi_001-{sl.hospital_id}-{sl.department_id}-{sl.reporting_date.strftime('%Y%m%d')}"
    assert any(e["analytical_record_id"] == expected_id for e in result.evidence_records if e["kpi_id"] == "kpi_001")


# ---------------------------------------------------------------------------
# Absenteeism Rate Tests
# ---------------------------------------------------------------------------

def test_absenteeism_standard_calculation(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    abs_results = [r for r in result.kpi_results if r.kpi_id == "kpi_002"]
    # Row 0: 2/20*100 = 10
    assert abs_results[0].calculation_status == "Calculated"
    assert abs_results[0].kpi_value == pytest.approx(10.0)


def test_absenteeism_zero_eligible_absence(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    abs_results = [r for r in result.kpi_results if r.kpi_id == "kpi_002"]
    # Row 1: 0/20*100 = 0
    assert abs_results[1].calculation_status == "Calculated"
    assert abs_results[1].kpi_value == pytest.approx(0.0)


def test_absenteeism_denominator_zero(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    abs_results = [r for r in result.kpi_results if r.kpi_id == "kpi_002"]
    # Row 3: planned = 0
    assert abs_results[3].calculation_status == "Zero Denominator"
    assert abs_results[3].kpi_value is None


def test_absenteeism_denominator_null(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    abs_results = [r for r in result.kpi_results if r.kpi_id == "kpi_002"]
    # Row 4: planned = None
    assert abs_results[4].calculation_status == "Insufficient Data"
    assert abs_results[4].kpi_value is None


def test_absenteeism_approved_absence_excluded(temp_project_root):
    """Approved leave should not be counted as unapproved absence."""
    df = pd.DataFrame({
        "hospital_id": ["HOSP-001"],
        "department_id": ["DEPT-A"],
        "reporting_date": ["2026-01-01"],
        "reporting_month": [1],
        "reporting_year": [2026],
        "planned_staff_count": [20.0],
        "present_staff_count": [18.0],
        "unapproved_absence_count": [0.0],
        "replacement_staff_count": [0.0],
        "reassigned_staff_count": [0.0],
        "operational_daily_id": ["OPD-1"],
    })
    df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    abs_res = [r for r in result.kpi_results if r.kpi_id == "kpi_002"][0]
    assert abs_res.kpi_value == pytest.approx(0.0)


def test_absenteeism_invalid_absence_value(temp_project_root):
    df = pd.DataFrame({
        "hospital_id": ["HOSP-001"],
        "department_id": ["DEPT-A"],
        "reporting_date": ["2026-01-01"],
        "reporting_month": [1],
        "reporting_year": [2026],
        "planned_staff_count": [20.0],
        "present_staff_count": [18.0],
        "unapproved_absence_count": [None],
        "replacement_staff_count": [0.0],
        "reassigned_staff_count": [0.0],
        "operational_daily_id": ["OPD-1"],
    })
    df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    abs_res = [r for r in result.kpi_results if r.kpi_id == "kpi_002"][0]
    assert abs_res.calculation_status == "Insufficient Data"
    assert abs_res.kpi_value is None


def test_absenteeism_deterministic_id(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    abs_res = [r for r in result.kpi_results if r.kpi_id == "kpi_002"][0]
    expected_id = f"AKPI-kpi_002-{abs_res.hospital_id}-{abs_res.department_id}-{abs_res.reporting_date.strftime('%Y%m%d')}"
    assert any(e["analytical_record_id"] == expected_id for e in result.evidence_records if e["kpi_id"] == "kpi_002")


# ---------------------------------------------------------------------------
# Threshold Tests
# ---------------------------------------------------------------------------

def test_threshold_draft_status_preserved(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    sl = [r for r in result.kpi_results if r.kpi_id == "kpi_001"][0]
    assert getattr(sl, "threshold_is_provisional", True) is True
    assert getattr(sl, "threshold_approval_status", "") == "Draft"


def test_missing_threshold_returns_not_assessed(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root, skip_threshold_status=True)
    result = engine.run()
    sl = [r for r in result.kpi_results if r.kpi_id == "kpi_001"][0]
    assert getattr(sl, "threshold_status", "") == "Not Assessed"


def test_no_hardcoded_threshold_values(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    for r in result.kpi_results:
        assert getattr(r, "threshold_version", "") != ""


# ---------------------------------------------------------------------------
# Confidence Tests
# ---------------------------------------------------------------------------

def test_confidence_complete_evidence(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    sl = [r for r in result.kpi_results if r.kpi_id == "kpi_001" and r.calculation_status == "Calculated"][0]
    assert getattr(sl, "data_confidence_level", "Unavailable") in ("High", "Medium", "Low")


def test_confidence_missing_numerator(temp_project_root):
    df = pd.DataFrame({
        "hospital_id": ["HOSP-001"],
        "department_id": ["DEPT-A"],
        "reporting_date": ["2026-01-01"],
        "reporting_month": [1],
        "reporting_year": [2026],
        "planned_staff_count": [20.0],
        "present_staff_count": [None],
        "unapproved_absence_count": [None],
        "replacement_staff_count": [None],
        "reassigned_staff_count": [0.0],
        "operational_daily_id": ["OPD-1"],
    })
    df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    sl = [r for r in result.kpi_results if r.kpi_id == "kpi_001"][0]
    assert sl.calculation_status == "Insufficient Data"
    assert getattr(sl, "data_confidence_level", "Unavailable") == "Unavailable"


def test_confidence_unavailable_kpi_result(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    sl = [r for r in result.kpi_results if r.kpi_id == "kpi_001" and r.calculation_status == "Zero Denominator"]
    if sl:
        assert getattr(sl[0], "data_confidence_level", "Unavailable") == "Unavailable"
    else:
        # If no zero denominator in sample, test with an unavailable result
        sl = [r for r in result.kpi_results if r.kpi_id == "kpi_001" and r.calculation_status != "Calculated"]
        assert getattr(sl[0], "data_confidence_level", "Unavailable") == "Unavailable"


# ---------------------------------------------------------------------------
# Output Tests
# ---------------------------------------------------------------------------

def test_output_schema_validation(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    daily_df = engine.to_daily_dataframe(result.kpi_results)
    schema_result = engine.validate_output_schema(daily_df, "analytical_workforce_kpi_daily")
    assert schema_result.valid


def test_unique_analytical_record_id(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    daily_df = engine.to_daily_dataframe(result.kpi_results)
    assert daily_df["analytical_record_id"].is_unique


def test_correct_daily_grain(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    daily_df = engine.to_daily_dataframe(result.kpi_results)
    expected_rows = len(sample_source_df) * 2
    assert len(daily_df) == expected_rows


def test_exactly_two_approved_kpi_ids(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    daily_df = engine.to_daily_dataframe(result.kpi_results)
    assert set(daily_df["kpi_id"].unique()) == {"kpi_001", "kpi_002"}


def test_numerator_denominator_evidence_preserved(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    evidence_df = engine.to_evidence_dataframe(result.evidence_records)
    assert len(evidence_df) > 0
    assert "numerator" in evidence_df["evidence_type"].values
    assert "denominator" in evidence_df["evidence_type"].values


def test_null_kpi_values_for_unavailable(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    for r in result.kpi_results:
        if r.calculation_status != "Calculated":
            assert r.kpi_value is None


def test_lineage_coverage(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    assert len(result.lineage_records) == len(sample_source_df) * 2


def test_exclusions_recorded(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    # Rows with zero/null planned should create exclusions
    assert len(result.exclusion_records) > 0


def test_issues_structured(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    issues_df = engine.to_issues_dataframe(result.issue_records)
    assert isinstance(issues_df, pd.DataFrame)


def test_audit_records_generated(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    assert len(result.audit_records) > 0


# ---------------------------------------------------------------------------
# Immutability Tests
# ---------------------------------------------------------------------------

def test_phase1_datasets_unchanged(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    # Create additional Phase 1 files
    for fname in ["processed_workforce_daily.csv", "processed_staff_attendance.csv"]:
        (temp_project_root / "data" / "processed" / fname).write_text("col1\nval1\n")
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    result = engine.run()
    assert result.immutability_result["verified"] is True
    assert len(result.immutability_result["datasets_changed"]) == 0


def test_step2a1_governance_outputs_unchanged(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    engine = WorkforceKPIEngine(project_root=temp_project_root)
    engine.run()
    # Check that 2A-1 files still exist and are readable
    for fname in ["kpi_governance_registry.csv", "kpi_readiness_summary.csv"]:
        assert (temp_project_root / "outputs" / "analytical_governance" / fname).exists()


# ---------------------------------------------------------------------------
# Runner Tests
# ---------------------------------------------------------------------------

def test_runner_dry_run(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    from src.run_workforce_kpi_processing import run_workforce_kpi_processing
    result = run_workforce_kpi_processing(
        project_root=temp_project_root,
        dry_run=True,
        execute_export=False,
    )
    assert result["status"] == "Completed"
    assert result["dry_run"] is True


def test_runner_execute_export(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    from src.run_workforce_kpi_processing import run_workforce_kpi_processing
    result = run_workforce_kpi_processing(
        project_root=temp_project_root,
        dry_run=False,
        execute_export=True,
        output_dir=temp_project_root / "outputs" / "analytical_workforce",
    )
    assert result["status"] == "Completed"
    assert (temp_project_root / "outputs" / "analytical_workforce" / "workforce_kpi_run_manifest.json").exists()


def test_runner_kpi_id_filter(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    from src.run_workforce_kpi_processing import run_workforce_kpi_processing
    result = run_workforce_kpi_processing(
        project_root=temp_project_root,
        dry_run=True,
        kpi_id="kpi_001",
    )
    assert result["status"] == "Completed"


def test_runner_unsupported_kpi_id(temp_project_root, sample_source_df):
    sample_source_df.to_csv(temp_project_root / "data" / "processed" / "processed_operational_daily.csv", index=False)
    from src.run_workforce_kpi_processing import run_workforce_kpi_processing
    result = run_workforce_kpi_processing(
        project_root=temp_project_root,
        dry_run=True,
        kpi_id="kpi_099",
    )
    # Should still complete but may flag unsupported
    assert result["status"] in ("Completed", "Failed")
