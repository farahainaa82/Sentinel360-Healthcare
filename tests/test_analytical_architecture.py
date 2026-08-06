"""
Sentinel360 Healthcare — Analytical Architecture Tests

Tests for Step 2A-1: Analytical Architecture and KPI Governance.
No actual KPI calculation is performed.

Step: 2A-1
"""

import json
import os
import shutil
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Ensure src is on path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from analytical_config_loader import AnalyticalConfigLoader, APPROVED_KPI_NAMES
from analytical_governance_validator import AnalyticalGovernanceValidator, AUTHORITATIVE_SOURCE_FIELDS
from analytical_models import KPIDefinition, AnalyticalIssue
from analytical_schema_registry import validate_schema_completeness, list_analytical_schemas
from kpi_registry import KPIRegistry, build_registry_from_config
from run_analytical_architecture_validation import run_closure


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_config_dir():
    tmp = Path(tempfile.mkdtemp())
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def temp_processed_dir():
    tmp = Path(tempfile.mkdtemp())
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def temp_output_dir():
    tmp = Path(tempfile.mkdtemp())
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def valid_kpi_definition_df():
    return pd.DataFrame({
        "kpi_id": ["KPI-001", "KPI-002", "KPI-003", "KPI-004", "KPI-005", "KPI-006"],
        "kpi_name": [
            "Staffing Level",
            "Staff Absenteeism Rate",
            "Bed Occupancy Rate",
            "Average Patient Waiting Time",
            "Patient Complaint Rate",
            "Patient Satisfaction Score",
        ],
        "domain": ["Workforce", "Workforce", "Patient Flow", "Patient Flow", "Patient Experience", "Patient Experience"],
        "description": ["D1", "D2", "D3", "D4", "D5", "D6"],
        "numerator_field": ["present_staff_count", "unapproved_absence_count", "occupied_beds", "wait_minutes", "complaint_count", "score_sum"],
        "denominator_field": ["planned_staff_count", "planned_staff_count", "operational_beds", "eligible_encounters", "encounter_count", "valid_responses"],
        "formula_text": ["N/D*100", "N/D*100", "N/D*100", "N/D", "N/D*1000", "N/D"],
        "unit": ["percentage", "percentage", "percentage", "minutes", "rate_per_1000", "score"],
        "directionality": ["higher_is_better", "lower_is_better", "neutral", "lower_is_better", "lower_is_better", "higher_is_better"],
        "grain": ["hospital-department-date", "hospital-department-date", "hospital-department-date", "hospital-department-date", "hospital-department-date", "hospital-department-date"],
        "calculation_frequency": ["daily", "daily", "daily", "daily", "daily", "daily"],
        "source_dataset": ["processed_operational_daily", "processed_operational_daily", "processed_operational_daily", "processed_patient_encounters", "processed_operational_daily", "processed_operational_daily"],
        "required_fields": ["planned_staff_count,present_staff_count", "planned_staff_count,unapproved_absence_count", "occupied_beds,operational_beds", "arrival_to_consultation_minutes,official_wait_stage_eligible_flag", "complaint_valid_record_count,encounter_record_count", "survey_score_weighted_sum,survey_valid_score_record_count"],
        "eligibility_rules": ["", "", "", "official_wait_stage_eligible_flag=True", "", ""],
        "exclusion_rules": ["", "", "", "negative_wait_minutes", "", ""],
        "null_treatment": ["exclude", "exclude", "exclude", "exclude", "exclude", "exclude"],
        "zero_denominator_treatment": ["null", "null", "null", "null", "null", "null"],
        "minimum_denominator": [1, 1, 1, 1, 1, 1],
        "threshold_config_reference": ["THR-001", "THR-002", "THR-003", "THR-004", "THR-005", "THR-006"],
        "data_confidence_rule_reference": ["DC-001", "DC-002", "DC-003", "DC-004", "DC-005", "DC-006"],
        "config_version": ["1.0", "1.0", "1.0", "1.0", "1.0", "1.0"],
        "approval_requirement": ["required", "required", "required", "required", "required", "required"],
        "effective_date": ["2026-01-01", "2026-01-01", "2026-01-01", "2026-01-01", "2026-01-01", "2026-01-01"],
        "approval_status": ["Approved", "Approved", "Approved", "Approved", "Approved", "Approved"],
    })


@pytest.fixture
def valid_kpi_threshold_df():
    return pd.DataFrame({
        "kpi_id": ["KPI-001", "KPI-001", "KPI-002", "KPI-003", "KPI-004", "KPI-005", "KPI-006"],
        "threshold_id": ["T1", "T2", "T3", "T4", "T5", "T6", "T7"],
        "threshold_name": ["Critical Low", "Warning Low", "Critical High", "Critical High", "Critical High", "Critical High", "Critical Low"],
        "threshold_value": [50, 70, 15, 95, 120, 50, 3.0],
        "threshold_direction": ["below", "below", "above", "above", "above", "above", "below"],
        "severity": ["critical", "warning", "critical", "critical", "critical", "critical", "critical"],
        "effective_date": ["2026-01-01"] * 7,
        "expiry_date": ["2026-12-31"] * 7,
        "approved_by": ["admin"] * 7,
        "approval_date": ["2026-01-01"] * 7,
    })


@pytest.fixture
def valid_data_confidence_df():
    return pd.DataFrame({
        "kpi_id": ["KPI-001", "KPI-002", "KPI-003", "KPI-004", "KPI-005", "KPI-006"],
        "confidence_level": ["high", "high", "high", "medium", "high", "high"],
        "completeness_threshold": [0.95, 0.95, 0.95, 0.90, 0.95, 0.95],
        "freshness_threshold_days": [1, 1, 1, 1, 1, 1],
        "validation_rules": ["", "", "", "", "", ""],
    })


@pytest.fixture
def minimal_processed_datasets(temp_processed_dir):
    # Create minimal processed datasets with required fields
    opd = pd.DataFrame({
        "hospital_id": ["H1"],
        "department_id": ["D1"],
        "reporting_date": ["2026-01-01"],
        "planned_staff_count": [10],
        "present_staff_count": [8],
        "unapproved_absence_count": [1],
        "replacement_staff_count": [1],
        "reassigned_staff_count": [0],
        "occupied_beds": [45],
        "operational_beds": [50],
        "complaint_valid_record_count": [2],
        "encounter_record_count": [100],
        "survey_score_weighted_sum": [450],
        "survey_valid_score_record_count": [100],
    })
    opd.to_csv(temp_processed_dir / "processed_operational_daily.csv", index=False)

    enc = pd.DataFrame({
        "encounter_id": ["E1"],
        "hospital_id": ["H1"],
        "department_id": ["D1"],
        "arrival_to_consultation_minutes": [30],
        "official_wait_stage_eligible_flag": [True],
        "encounter_wait_eligible_flag": [True],
    })
    enc.to_csv(temp_processed_dir / "processed_patient_encounters.csv", index=False)

    return temp_processed_dir


# ---------------------------------------------------------------------------
# Configuration Tests
# ---------------------------------------------------------------------------

def test_required_configuration_files_exist(temp_config_dir, valid_kpi_definition_df, valid_kpi_threshold_df, valid_data_confidence_df):
    valid_kpi_definition_df.to_csv(temp_config_dir / "kpi_definition_config.csv", index=False)
    valid_kpi_threshold_df.to_csv(temp_config_dir / "kpi_threshold_config.csv", index=False)
    valid_data_confidence_df.to_csv(temp_config_dir / "data_confidence_config.csv", index=False)

    loader = AnalyticalConfigLoader(temp_config_dir)
    df = loader.load_kpi_definitions()
    assert not df.empty
    df2 = loader.load_kpi_thresholds()
    assert not df2.empty
    df3 = loader.load_data_confidence_rules()
    assert not df3.empty


def test_configuration_schema_validation(temp_config_dir, valid_kpi_definition_df):
    valid_kpi_definition_df.to_csv(temp_config_dir / "kpi_definition_config.csv", index=False)
    loader = AnalyticalConfigLoader(temp_config_dir)
    loader.load_kpi_definitions()
    result = loader.validate_configuration()
    assert result["kpi_definitions_valid"] is True


def test_duplicate_kpi_ids_detected(temp_config_dir):
    df = pd.DataFrame({
        "kpi_id": ["KPI-001", "KPI-001"],
        "kpi_name": ["Staffing Level", "Staffing Level"],
        "domain": ["Workforce", "Workforce"],
        "numerator_field": ["a", "a"],
        "denominator_field": ["b", "b"],
        "unit": ["percentage", "percentage"],
        "directionality": ["higher_is_better", "higher_is_better"],
        "grain": ["hospital-department-date", "hospital-department-date"],
        "effective_date": ["2026-01-01", "2026-01-01"],
        "approval_status": ["Approved", "Approved"],
    })
    df.to_csv(temp_config_dir / "kpi_definition_config.csv", index=False)
    loader = AnalyticalConfigLoader(temp_config_dir)
    loader.load_kpi_definitions()
    result = loader.validate_configuration()
    assert result["kpi_definitions_valid"] is False
    issue_descs = [i.issue_description for i in loader.get_issues()]
    assert any("Duplicate KPI IDs" in d for d in issue_descs)


def test_unapproved_kpi_names_rejected(temp_config_dir):
    df = pd.DataFrame({
        "kpi_id": ["KPI-999"],
        "kpi_name": ["Unauthorized KPI"],
        "domain": ["Test"],
        "numerator_field": ["a"],
        "denominator_field": ["b"],
        "unit": ["percentage"],
        "directionality": ["higher_is_better"],
        "grain": ["hospital-department-date"],
        "effective_date": ["2026-01-01"],
        "approval_status": ["Approved"],
    })
    df.to_csv(temp_config_dir / "kpi_definition_config.csv", index=False)
    loader = AnalyticalConfigLoader(temp_config_dir)
    loader.load_kpi_definitions()
    result = loader.validate_configuration()
    assert result["kpi_definitions_valid"] is False
    issue_descs = [i.issue_description for i in loader.get_issues()]
    assert any("Unapproved KPI names" in d for d in issue_descs)


def test_invalid_unit_detected(temp_config_dir):
    df = pd.DataFrame({
        "kpi_id": ["KPI-001"],
        "kpi_name": ["Staffing Level"],
        "domain": ["Workforce"],
        "numerator_field": ["a"],
        "denominator_field": ["b"],
        "unit": ["invalid_unit"],
        "directionality": ["higher_is_better"],
        "grain": ["hospital-department-date"],
        "effective_date": ["2026-01-01"],
        "approval_status": ["Approved"],
    })
    df.to_csv(temp_config_dir / "kpi_definition_config.csv", index=False)
    loader = AnalyticalConfigLoader(temp_config_dir)
    loader.load_kpi_definitions()
    result = loader.validate_configuration()
    assert result["kpi_definitions_valid"] is False
    issue_descs = [i.issue_description for i in loader.get_issues()]
    assert any("Invalid units" in d for d in issue_descs)


def test_invalid_directionality_detected(temp_config_dir):
    df = pd.DataFrame({
        "kpi_id": ["KPI-001"],
        "kpi_name": ["Staffing Level"],
        "domain": ["Workforce"],
        "numerator_field": ["a"],
        "denominator_field": ["b"],
        "unit": ["percentage"],
        "directionality": ["up_is_good"],
        "grain": ["hospital-department-date"],
        "effective_date": ["2026-01-01"],
        "approval_status": ["Approved"],
    })
    df.to_csv(temp_config_dir / "kpi_definition_config.csv", index=False)
    loader = AnalyticalConfigLoader(temp_config_dir)
    loader.load_kpi_definitions()
    result = loader.validate_configuration()
    assert result["kpi_definitions_valid"] is False
    issue_descs = [i.issue_description for i in loader.get_issues()]
    assert any("Invalid directionality" in d for d in issue_descs)


def test_invalid_grain_detected(temp_config_dir):
    df = pd.DataFrame({
        "kpi_id": ["KPI-001"],
        "kpi_name": ["Staffing Level"],
        "domain": ["Workforce"],
        "numerator_field": ["a"],
        "denominator_field": ["b"],
        "unit": ["percentage"],
        "directionality": ["higher_is_better"],
        "grain": ["invalid_grain"],
        "effective_date": ["2026-01-01"],
        "approval_status": ["Approved"],
    })
    df.to_csv(temp_config_dir / "kpi_definition_config.csv", index=False)
    loader = AnalyticalConfigLoader(temp_config_dir)
    loader.load_kpi_definitions()
    result = loader.validate_configuration()
    assert result["kpi_definitions_valid"] is False
    issue_descs = [i.issue_description for i in loader.get_issues()]
    assert any("Invalid grain" in d for d in issue_descs)


def test_negative_minimum_denominator_detected(temp_config_dir):
    df = pd.DataFrame({
        "kpi_id": ["KPI-001"],
        "kpi_name": ["Staffing Level"],
        "domain": ["Workforce"],
        "numerator_field": ["a"],
        "denominator_field": ["b"],
        "unit": ["percentage"],
        "directionality": ["higher_is_better"],
        "grain": ["hospital-department-date"],
        "minimum_denominator": [-1],
        "effective_date": ["2026-01-01"],
        "approval_status": ["Approved"],
    })
    df.to_csv(temp_config_dir / "kpi_definition_config.csv", index=False)
    loader = AnalyticalConfigLoader(temp_config_dir)
    loader.load_kpi_definitions()
    result = loader.validate_configuration()
    assert result["kpi_definitions_valid"] is False
    issue_descs = [i.issue_description for i in loader.get_issues()]
    assert any("Negative minimum denominator" in d for d in issue_descs)


# ---------------------------------------------------------------------------
# KPI Registry Tests
# ---------------------------------------------------------------------------

def test_kpi_registry_has_exactly_six_kpis(valid_kpi_definition_df):
    registry = KPIRegistry(build_registry_from_config(valid_kpi_definition_df))
    completeness = registry.validate_completeness()
    assert completeness["valid"] is True
    assert completeness["total_registered"] == 6
    assert len(completeness["missing"]) == 0
    assert len(completeness["extra"]) == 0


def test_kpi_registry_missing_kpi_detected(valid_kpi_definition_df):
    df = valid_kpi_definition_df[valid_kpi_definition_df["kpi_id"] != "KPI-006"]
    registry = KPIRegistry(build_registry_from_config(df))
    completeness = registry.validate_completeness()
    assert completeness["valid"] is False
    assert "Patient Satisfaction Score" in completeness["missing"]


def test_kpi_registry_extra_kpi_detected(valid_kpi_definition_df):
    extra = pd.DataFrame({
        "kpi_id": ["KPI-999"],
        "kpi_name": ["Extra KPI"],
        "domain": ["Test"],
        "numerator_field": ["a"],
        "denominator_field": ["b"],
        "unit": ["percentage"],
        "directionality": ["higher_is_better"],
        "grain": ["hospital-department-date"],
        "effective_date": ["2026-01-01"],
        "approval_status": ["Approved"],
    })
    df = pd.concat([valid_kpi_definition_df, extra], ignore_index=True)
    registry = KPIRegistry(build_registry_from_config(df))
    completeness = registry.validate_completeness()
    assert completeness["valid"] is False
    assert "Extra KPI" in completeness["extra"]


def test_kpi_registry_returns_correct_kpi(valid_kpi_definition_df):
    registry = KPIRegistry(build_registry_from_config(valid_kpi_definition_df))
    kpi = registry.get_kpi("KPI-001")
    assert kpi is not None
    assert kpi.kpi_name == "Staffing Level"


# ---------------------------------------------------------------------------
# Source Field Availability Tests
# ---------------------------------------------------------------------------

def test_source_fields_available(temp_config_dir, temp_processed_dir, valid_kpi_definition_df, valid_kpi_threshold_df, minimal_processed_datasets):
    valid_kpi_definition_df.to_csv(temp_config_dir / "kpi_definition_config.csv", index=False)
    valid_kpi_threshold_df.to_csv(temp_config_dir / "kpi_threshold_config.csv", index=False)

    loader = AnalyticalConfigLoader(temp_config_dir)
    loader.load_kpi_definitions()
    loader.load_kpi_thresholds()
    registry = KPIRegistry(build_registry_from_config(loader.kpi_definitions))
    validator = AnalyticalGovernanceValidator(registry, temp_processed_dir, temp_config_dir)
    valid = validator.validate_source_field_availability()
    assert valid is True


def test_missing_source_dataset_detected(temp_config_dir, temp_processed_dir, valid_kpi_definition_df, valid_kpi_threshold_df):
    valid_kpi_definition_df.to_csv(temp_config_dir / "kpi_definition_config.csv", index=False)
    valid_kpi_threshold_df.to_csv(temp_config_dir / "kpi_threshold_config.csv", index=False)

    loader = AnalyticalConfigLoader(temp_config_dir)
    loader.load_kpi_definitions()
    registry = KPIRegistry(build_registry_from_config(loader.kpi_definitions))
    validator = AnalyticalGovernanceValidator(registry, temp_processed_dir, temp_config_dir)
    valid = validator.validate_source_field_availability()
    assert valid is False
    issue_descs = [i.issue_description for i in validator.get_issues()]
    assert any("Source dataset missing" in d for d in issue_descs)


def test_missing_source_field_detected(temp_config_dir, temp_processed_dir, valid_kpi_definition_df, valid_kpi_threshold_df):
    # Create operational daily with missing required field
    opd = pd.DataFrame({
        "hospital_id": ["H1"],
        "department_id": ["D1"],
        "reporting_date": ["2026-01-01"],
        "planned_staff_count": [10],
        # missing present_staff_count
    })
    opd.to_csv(temp_processed_dir / "processed_operational_daily.csv", index=False)

    valid_kpi_definition_df.to_csv(temp_config_dir / "kpi_definition_config.csv", index=False)
    valid_kpi_threshold_df.to_csv(temp_config_dir / "kpi_threshold_config.csv", index=False)

    loader = AnalyticalConfigLoader(temp_config_dir)
    loader.load_kpi_definitions()
    registry = KPIRegistry(build_registry_from_config(loader.kpi_definitions))
    validator = AnalyticalGovernanceValidator(registry, temp_processed_dir, temp_config_dir)
    valid = validator.validate_source_field_availability()
    assert valid is False
    issue_descs = [i.issue_description for i in validator.get_issues()]
    assert any("Missing source fields" in d for d in issue_descs)


# ---------------------------------------------------------------------------
# Threshold Validation Tests
# ---------------------------------------------------------------------------

def test_threshold_configuration_valid(temp_config_dir, temp_processed_dir, valid_kpi_definition_df, valid_kpi_threshold_df, minimal_processed_datasets):
    valid_kpi_definition_df.to_csv(temp_config_dir / "kpi_definition_config.csv", index=False)
    valid_kpi_threshold_df.to_csv(temp_config_dir / "kpi_threshold_config.csv", index=False)

    loader = AnalyticalConfigLoader(temp_config_dir)
    loader.load_kpi_definitions()
    registry = KPIRegistry(build_registry_from_config(loader.kpi_definitions))
    validator = AnalyticalGovernanceValidator(registry, temp_processed_dir, temp_config_dir)
    valid = validator.validate_threshold_configuration()
    assert valid is True


def test_threshold_references_unknown_kpi(temp_config_dir, temp_processed_dir, valid_kpi_definition_df):
    thr = pd.DataFrame({
        "kpi_id": ["KPI-999"],
        "threshold_id": ["T1"],
        "threshold_name": ["Test"],
        "threshold_value": [50],
        "threshold_direction": ["above"],
        "severity": ["critical"],
        "effective_date": ["2026-01-01"],
    })
    valid_kpi_definition_df.to_csv(temp_config_dir / "kpi_definition_config.csv", index=False)
    thr.to_csv(temp_config_dir / "kpi_threshold_config.csv", index=False)

    loader = AnalyticalConfigLoader(temp_config_dir)
    loader.load_kpi_definitions()
    registry = KPIRegistry(build_registry_from_config(loader.kpi_definitions))
    validator = AnalyticalGovernanceValidator(registry, temp_processed_dir, temp_config_dir)
    valid = validator.validate_threshold_configuration()
    assert valid is False
    issue_descs = [i.issue_description for i in validator.get_issues()]
    assert any("Thresholds reference unknown KPIs" in d for d in issue_descs)


# ---------------------------------------------------------------------------
# Readiness Tests
# ---------------------------------------------------------------------------

def test_readiness_all_ready(temp_config_dir, temp_processed_dir, valid_kpi_definition_df, valid_kpi_threshold_df, minimal_processed_datasets):
    valid_kpi_definition_df.to_csv(temp_config_dir / "kpi_definition_config.csv", index=False)
    valid_kpi_threshold_df.to_csv(temp_config_dir / "kpi_threshold_config.csv", index=False)

    loader = AnalyticalConfigLoader(temp_config_dir)
    loader.load_kpi_definitions()
    registry = KPIRegistry(build_registry_from_config(loader.kpi_definitions))
    validator = AnalyticalGovernanceValidator(registry, temp_processed_dir, temp_config_dir)
    validator.validate_all()
    readiness = validator.get_readiness()
    for kpi_id, status in readiness.items():
        assert status in ("Ready", "Conditionally Ready"), f"{kpi_id} is {status}"


def test_blocked_kpi_has_reason(temp_config_dir, temp_processed_dir, valid_kpi_definition_df, valid_kpi_threshold_df):
    # No processed datasets - all should be blocked
    valid_kpi_definition_df.to_csv(temp_config_dir / "kpi_definition_config.csv", index=False)
    valid_kpi_threshold_df.to_csv(temp_config_dir / "kpi_threshold_config.csv", index=False)

    loader = AnalyticalConfigLoader(temp_config_dir)
    loader.load_kpi_definitions()
    registry = KPIRegistry(build_registry_from_config(loader.kpi_definitions))
    validator = AnalyticalGovernanceValidator(registry, temp_processed_dir, temp_config_dir)
    validator.validate_all()
    readiness = validator.get_readiness()
    blocked = {k: v for k, v in readiness.items() if v == "Blocked"}
    assert len(blocked) > 0
    issue_descs = [i.issue_description for i in validator.get_issues()]
    assert len(issue_descs) > 0


# ---------------------------------------------------------------------------
# Schema Tests
# ---------------------------------------------------------------------------

def test_analytical_schemas_defined():
    result = validate_schema_completeness()
    assert result["valid"] is True
    assert result["registered_count"] == 9


def test_analytical_kpi_daily_schema_has_required_fields():
    from analytical_schema_registry import get_analytical_schema
    schema = get_analytical_schema("analytical_kpi_daily")
    assert "analytical_record_id" in schema["required_fields"]
    assert "kpi_id" in schema["required_fields"]
    assert "kpi_value" in schema["required_fields"]


# ---------------------------------------------------------------------------
# Calculation Prevention Tests
# ---------------------------------------------------------------------------

def test_no_kpi_calculations_performed(temp_config_dir, temp_processed_dir, valid_kpi_definition_df, valid_kpi_threshold_df, minimal_processed_datasets):
    valid_kpi_definition_df.to_csv(temp_config_dir / "kpi_definition_config.csv", index=False)
    valid_kpi_threshold_df.to_csv(temp_config_dir / "kpi_threshold_config.csv", index=False)

    loader = AnalyticalConfigLoader(temp_config_dir)
    loader.load_kpi_definitions()
    registry = KPIRegistry(build_registry_from_config(loader.kpi_definitions))
    validator = AnalyticalGovernanceValidator(registry, temp_processed_dir, temp_config_dir)
    assert validator.validate_no_calculations_performed() is True


def test_no_analytical_result_csv_generated(temp_config_dir, temp_processed_dir, temp_output_dir, valid_kpi_definition_df, valid_kpi_threshold_df, minimal_processed_datasets):
    valid_kpi_definition_df.to_csv(temp_config_dir / "kpi_definition_config.csv", index=False)
    valid_kpi_threshold_df.to_csv(temp_config_dir / "kpi_threshold_config.csv", index=False)

    result = run_closure(
        project_root=temp_processed_dir.parent,
        processed_dir=temp_processed_dir,
        config_dir=temp_config_dir,
        output_dir=temp_output_dir,
        log_dir=temp_output_dir,
        dry_run=False,
        execute_export=True,
    )
    # Check no analytical_kpi_daily.csv was generated
    assert not (temp_output_dir / "analytical_kpi_daily.csv").exists()
    assert not (temp_output_dir / "analytical_kpi_monthly.csv").exists()


# ---------------------------------------------------------------------------
# Phase 1 Immutability Tests
# ---------------------------------------------------------------------------

def test_phase1_processed_datasets_unchanged(temp_config_dir, temp_processed_dir, temp_output_dir, valid_kpi_definition_df, valid_kpi_threshold_df, minimal_processed_datasets):
    valid_kpi_definition_df.to_csv(temp_config_dir / "kpi_definition_config.csv", index=False)
    valid_kpi_threshold_df.to_csv(temp_config_dir / "kpi_threshold_config.csv", index=False)

    result = run_closure(
        project_root=temp_processed_dir.parent,
        processed_dir=temp_processed_dir,
        config_dir=temp_config_dir,
        output_dir=temp_output_dir,
        log_dir=temp_output_dir,
        dry_run=False,
        execute_export=True,
    )
    assert result["phase1_immutability_verified"] is True
    assert len(result["phase1_datasets_changed"]) == 0


# ---------------------------------------------------------------------------
# Runner Integration Tests
# ---------------------------------------------------------------------------

def test_runner_returns_structured_result(temp_config_dir, temp_processed_dir, temp_output_dir, valid_kpi_definition_df, valid_kpi_threshold_df, minimal_processed_datasets):
    valid_kpi_definition_df.to_csv(temp_config_dir / "kpi_definition_config.csv", index=False)
    valid_kpi_threshold_df.to_csv(temp_config_dir / "kpi_threshold_config.csv", index=False)

    result = run_closure(
        project_root=temp_processed_dir.parent,
        processed_dir=temp_processed_dir,
        config_dir=temp_config_dir,
        output_dir=temp_output_dir,
        log_dir=temp_output_dir,
        dry_run=False,
        execute_export=True,
    )
    assert "calculation_run_id" in result
    assert "status" in result
    assert "kpi_count" in result
    assert "readiness_summary" in result
    assert "phase1_immutability_verified" in result


def test_runner_generates_governance_outputs(temp_config_dir, temp_processed_dir, temp_output_dir, valid_kpi_definition_df, valid_kpi_threshold_df, minimal_processed_datasets):
    valid_kpi_definition_df.to_csv(temp_config_dir / "kpi_definition_config.csv", index=False)
    valid_kpi_threshold_df.to_csv(temp_config_dir / "kpi_threshold_config.csv", index=False)

    run_closure(
        project_root=temp_processed_dir.parent,
        processed_dir=temp_processed_dir,
        config_dir=temp_config_dir,
        output_dir=temp_output_dir,
        log_dir=temp_output_dir,
        dry_run=False,
        execute_export=True,
    )
    assert (temp_output_dir / "analytical_architecture_manifest.json").exists()
    assert (temp_output_dir / "kpi_governance_registry.csv").exists()
    assert (temp_output_dir / "kpi_readiness_summary.csv").exists()
    assert (temp_output_dir / "kpi_source_field_mapping.csv").exists()
    assert (temp_output_dir / "kpi_configuration_validation.csv").exists()
    assert (temp_output_dir / "kpi_threshold_validation.csv").exists()
    assert (temp_output_dir / "analytical_schema_summary.csv").exists()
    assert (temp_output_dir / "analytical_governance_issue_log.csv").exists()
    assert (temp_output_dir / "analytical_governance_audit_log.csv").exists()
    assert (temp_output_dir / "phase1_immutability_verification.csv").exists()


def test_runner_manifest_contains_kpi_ids(temp_config_dir, temp_processed_dir, temp_output_dir, valid_kpi_definition_df, valid_kpi_threshold_df, minimal_processed_datasets):
    valid_kpi_definition_df.to_csv(temp_config_dir / "kpi_definition_config.csv", index=False)
    valid_kpi_threshold_df.to_csv(temp_config_dir / "kpi_threshold_config.csv", index=False)

    run_closure(
        project_root=temp_processed_dir.parent,
        processed_dir=temp_processed_dir,
        config_dir=temp_config_dir,
        output_dir=temp_output_dir,
        log_dir=temp_output_dir,
        dry_run=False,
        execute_export=True,
    )
    with open(temp_output_dir / "analytical_architecture_manifest.json") as f:
        manifest = json.load(f)
    assert len(manifest["kpi_ids"]) == 6
    assert "KPI-001" in manifest["kpi_ids"]


def test_configuration_provenance_recorded(temp_config_dir, temp_processed_dir, temp_output_dir, valid_kpi_definition_df, valid_kpi_threshold_df, minimal_processed_datasets):
    valid_kpi_definition_df.to_csv(temp_config_dir / "kpi_definition_config.csv", index=False)
    valid_kpi_threshold_df.to_csv(temp_config_dir / "kpi_threshold_config.csv", index=False)

    from analytical_config_loader import AnalyticalConfigLoader
    loader = AnalyticalConfigLoader(temp_config_dir)
    loader.load_kpi_definitions()
    loader.load_kpi_thresholds()
    prov = loader.get_provenance()
    assert len(prov) == 2
    assert all(p.checksum for p in prov)


# ---------------------------------------------------------------------------
# Determinism Tests
# ---------------------------------------------------------------------------

def test_registry_output_is_deterministic(valid_kpi_definition_df):
    reg1 = build_registry_from_config(valid_kpi_definition_df)
    reg2 = build_registry_from_config(valid_kpi_definition_df)
    assert sorted(reg1.keys()) == sorted(reg2.keys())
    for kpi_id in reg1:
        assert reg1[kpi_id].kpi_name == reg2[kpi_id].kpi_name


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------

def test_empty_config_returns_empty_registry():
    registry = build_registry_from_config(pd.DataFrame())
    assert len(registry) == 0


def test_kpi_with_unresolved_rules_is_conditionally_ready(temp_config_dir, temp_processed_dir, valid_kpi_definition_df, valid_kpi_threshold_df, minimal_processed_datasets):
    # Add unresolved rule to one KPI
    df = valid_kpi_definition_df.copy()
    df.loc[df["kpi_id"] == "KPI-001", "unresolved_rules"] = "staff_role_mapping_pending"
    df.to_csv(temp_config_dir / "kpi_definition_config.csv", index=False)
    valid_kpi_threshold_df.to_csv(temp_config_dir / "kpi_threshold_config.csv", index=False)

    loader = AnalyticalConfigLoader(temp_config_dir)
    loader.load_kpi_definitions()
    registry = KPIRegistry(build_registry_from_config(loader.kpi_definitions))
    validator = AnalyticalGovernanceValidator(registry, temp_processed_dir, temp_config_dir)
    validator.validate_all()
    readiness = validator.get_readiness()
    assert readiness["KPI-001"] == "Conditionally Ready"
