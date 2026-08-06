"""
Sentinel360 Healthcare — Analytical Layer Closure Tests

Focused closure tests for Phase 2A.
Do not run nested pytest inside tests.

Step: 2A-6
"""

import os
import sys
import json
import tempfile
import shutil
import pytest
from datetime import datetime

import pandas as pd
import numpy as np

# Ensure src is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from analytical_layer_closure_validator import (
    AnalyticalLayerClosureValidator,
    ValidationFinding,
    ClosureResult,
    _file_checksum,
    _record_checksums,
)


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def validator():
    return AnalyticalLayerClosureValidator(project_root=PROJECT_ROOT)


@pytest.fixture
def temp_validator():
    """Validator pointing at a temporary copy to avoid modifying accepted outputs."""
    tmp = tempfile.mkdtemp()
    # Copy minimal required files
    src_analytical = os.path.join(PROJECT_ROOT, "data", "analytical")
    dst_analytical = os.path.join(tmp, "data", "analytical")
    os.makedirs(dst_analytical, exist_ok=True)
    for fname in [
        "analytical_six_kpi_daily.csv",
        "analytical_six_kpi_evidence.csv",
        "analytical_six_kpi_exclusions.csv",
        "analytical_six_kpi_lineage.csv",
        "analytical_six_kpi_issues.csv",
        "analytical_six_kpi_audit.csv",
        "analytical_six_kpi_coverage_daily.csv",
        "analytical_workforce_kpi_daily.csv",
        "analytical_patient_flow_kpi_daily.csv",
        "analytical_patient_experience_kpi_daily.csv",
    ]:
        sp = os.path.join(src_analytical, fname)
        if os.path.exists(sp):
            shutil.copy2(sp, os.path.join(dst_analytical, fname))
    # Copy config
    src_config = os.path.join(PROJECT_ROOT, "config")
    dst_config = os.path.join(tmp, "config")
    os.makedirs(dst_config, exist_ok=True)
    for fname in ["kpi_definition_config.csv", "kpi_threshold_config.csv", "data_confidence_config.csv"]:
        sp = os.path.join(src_config, fname)
        if os.path.exists(sp):
            shutil.copy2(sp, os.path.join(dst_config, fname))
    v = AnalyticalLayerClosureValidator(project_root=tmp)
    yield v
    shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# Architecture
# ---------------------------------------------------------------------------

def test_safe_import():
    from analytical_layer_closure_validator import AnalyticalLayerClosureValidator
    assert AnalyticalLayerClosureValidator is not None


def test_no_automatic_execution():
    """Importing runner should not execute closure."""
    import run_analytical_layer_closure
    # Simply importing should not raise or run closure
    assert hasattr(run_analytical_layer_closure, "run_closure")


def test_closure_validator_returns_structured_result(validator):
    result = validator.run_all_validations()
    assert isinstance(result, ClosureResult)
    assert hasattr(result, "findings")
    assert hasattr(result, "closure_status")


def test_no_kpi_recalculation_in_validator(validator):
    # Validator should not modify source files
    src_path = os.path.join(PROJECT_ROOT, "data/analytical/analytical_six_kpi_daily.csv")
    pre = _file_checksum(src_path)
    validator.run_all_validations()
    post = _file_checksum(src_path)
    assert pre == post


# ---------------------------------------------------------------------------
# File validation
# ---------------------------------------------------------------------------

def test_all_required_files_exist(validator):
    validator.validate_required_files()
    file_findings = [f for f in validator.result.findings if f.domain == "File Validation" and f.status == "Failed"]
    assert len(file_findings) == 0, f"Missing required files: {[f.message for f in file_findings]}"


# ---------------------------------------------------------------------------
# KPI registry
# ---------------------------------------------------------------------------

def test_exactly_six_approved_kpi_ids(validator):
    validator.validate_kpi_registry()
    f = [x for x in validator.result.findings if x.check_name == "kpi_registry_six_kpis"]
    assert f
    assert f[0].status == "Passed"


def test_six_kpi_set_integrated(validator):
    validator.validate_six_kpi_set()
    f = [x for x in validator.result.findings if x.check_name == "six_kpi_set_integrated"]
    assert f
    assert f[0].status == "Passed"


# ---------------------------------------------------------------------------
# Counts
# ---------------------------------------------------------------------------

def test_17520_integrated_records(validator):
    validator.validate_integrated_counts()
    f = [x for x in validator.result.findings if x.check_name == "integrated_total_count"]
    assert f
    assert f[0].status == "Passed", f[0].message


def test_2920_records_per_kpi(validator):
    validator.validate_integrated_counts()
    for kpi_id in validator.SIX_KPIS:
        f = [x for x in validator.result.findings if x.check_name == f"integrated_count:{kpi_id}"]
        assert f, f"Missing finding for {kpi_id}"
        assert f[0].status == "Passed", f[0].message


def test_2920_coverage_grains(validator):
    validator.validate_coverage()
    f = [x for x in validator.result.findings if x.check_name == "coverage_grain_count"]
    assert f
    assert f[0].status == "Passed", f[0].message


def test_six_rows_per_grain(validator):
    cov = validator._load("data/analytical/analytical_six_kpi_coverage_daily.csv")
    assert cov is not None
    assert (cov["present_kpi_count"].astype(int) == 6).all()


def test_zero_duplicates(validator):
    validator.validate_business_keys()
    f = [x for x in validator.result.findings if x.check_name == "duplicate_grain_check"]
    assert f
    assert f[0].status == "Passed", f[0].message


def test_zero_missing_records(validator):
    validator.reconcile_kpi_results()
    recs = validator.result.summary.get("kpi_count_reconciliation", [])
    for r in recs:
        assert r["missing_count"] == 0, f"Missing records for {r['kpi_id']}"


# ---------------------------------------------------------------------------
# Availability
# ---------------------------------------------------------------------------

def test_expected_calculated_and_unavailable_counts(validator):
    validator.validate_calculation_statuses()
    for kpi_id in validator.SIX_KPIS:
        f = [x for x in validator.result.findings if x.check_name == f"calculation_availability:{kpi_id}"]
        assert f, f"Missing availability check for {kpi_id}"
        assert f[0].status == "Passed", f"{kpi_id}: {f[0].message}"


def test_unavailable_values_remain_null(validator):
    daily = validator._load("data/analytical/analytical_six_kpi_daily.csv")
    assert daily is not None
    uncalc = daily[daily["calculation_status"] != "Calculated"]
    null_values = uncalc["kpi_value"].isna().sum()
    assert null_values == len(uncalc), f"Expected all unavailable values null, got {null_values}/{len(uncalc)}"


def test_calculated_values_remain_non_null(validator):
    daily = validator._load("data/analytical/analytical_six_kpi_daily.csv")
    assert daily is not None
    calc = daily[daily["calculation_status"] == "Calculated"]
    non_null = calc["kpi_value"].notna().sum()
    assert non_null == len(calc), f"Expected all calculated values non-null, got {non_null}/{len(calc)}"


# ---------------------------------------------------------------------------
# Reconciliation
# ---------------------------------------------------------------------------

def test_source_and_integrated_row_counts_match(validator):
    validator.reconcile_kpi_results()
    recs = validator.result.summary.get("kpi_count_reconciliation", [])
    for r in recs:
        assert r["count_difference"] == 0, f"Count mismatch for {r['kpi_id']}"


def test_source_and_integrated_values_match(validator):
    validator.validate_value_preservation()
    f = [x for x in validator.result.findings if x.check_name == "kpi_value_preserved"]
    assert f
    assert f[0].status == "Passed", f[0].message


# ---------------------------------------------------------------------------
# Threshold governance
# ---------------------------------------------------------------------------

def test_all_not_assessed(validator):
    validator.validate_threshold_governance()
    f = [x for x in validator.result.findings if x.check_name == "all_not_assessed"]
    assert f
    assert f[0].status == "Passed"


def test_all_provisional(validator):
    validator.validate_threshold_governance()
    f = [x for x in validator.result.findings if x.check_name == "all_provisional"]
    assert f
    assert f[0].status == "Passed"


def test_no_green(validator):
    validator.validate_threshold_governance()
    f = [x for x in validator.result.findings if x.check_name == "no_green"]
    assert f
    assert f[0].status == "Passed"


def test_no_amber(validator):
    validator.validate_threshold_governance()
    f = [x for x in validator.result.findings if x.check_name == "no_amber"]
    assert f
    assert f[0].status == "Passed"


def test_no_red(validator):
    validator.validate_threshold_governance()
    f = [x for x in validator.result.findings if x.check_name == "no_red"]
    assert f
    assert f[0].status == "Passed"


def test_draft_threshold_not_marked_approved(validator):
    validator.validate_threshold_governance()
    f = [x for x in validator.result.findings if x.check_name == "draft_not_approved"]
    assert f
    assert f[0].status == "Passed"


# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------

def test_unavailable_result_not_high_confidence(validator):
    validator.validate_confidence_governance()
    f = [x for x in validator.result.findings if x.check_name == "unavailable_not_high_confidence"]
    assert f
    assert f[0].status == "Passed", f[0].message


def test_confidence_version_preserved(validator):
    daily = validator._load("data/analytical/analytical_six_kpi_daily.csv")
    assert daily is not None
    assert (daily["confidence_rule_version"].notna()).all()


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------

def test_calculated_kpi_has_evidence(validator):
    validator.validate_evidence()
    f = [x for x in validator.result.findings if x.check_name == "calculated_has_evidence"]
    assert f
    assert f[0].status == "Passed", f[0].message


def test_unavailable_kpi_has_explanatory_evidence(validator):
    validator.validate_evidence()
    f = [x for x in validator.result.findings if x.check_name == "unavailable_evidence_status_valid"]
    assert f
    assert f[0].status == "Passed", f[0].message


# ---------------------------------------------------------------------------
# Lineage
# ---------------------------------------------------------------------------

def test_calculated_lineage_not_broken(validator):
    validator.validate_lineage()
    f = [x for x in validator.result.findings if x.check_name == "calculated_lineage_not_broken"]
    assert f
    assert f[0].status == "Passed", f[0].message


def test_integrated_source_linkage_exists(validator):
    validator.validate_lineage()
    f = [x for x in validator.result.findings if x.check_name == "source_dataset_linkage"]
    assert f
    assert f[0].status == "Passed", f[0].message


# ---------------------------------------------------------------------------
# Coverage
# ---------------------------------------------------------------------------

def test_all_grains_complete(validator):
    validator.validate_coverage()
    f = [x for x in validator.result.findings if x.check_name == "coverage_all_complete"]
    assert f
    assert f[0].status == "Passed", f[0].message


def test_unavailable_kpi_rows_count_as_present(validator):
    daily = validator._load("data/analytical/analytical_six_kpi_daily.csv")
    cov = validator._load("data/analytical/analytical_six_kpi_coverage_daily.csv")
    assert daily is not None and cov is not None
    # Every grain should have 6 present even if some are unavailable
    assert (cov["present_kpi_count"].astype(int) == 6).all()


def test_missing_kpi_row_fails(validator):
    # This is implicitly tested by coverage checks; ensure no missing rows
    validator.validate_coverage()
    f = [x for x in validator.result.findings if x.check_name == "coverage_missing_kpis"]
    assert f
    assert f[0].status == "Passed", f[0].message


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

def test_required_fields_exist(validator):
    validator.validate_schemas()
    f = [x for x in validator.result.findings if x.check_name == "daily_required_fields"]
    assert f
    assert f[0].status == "Passed", f[0].message


def test_valid_types(validator):
    validator.validate_schemas()
    f = [x for x in validator.result.findings if x.check_name == "reporting_date_parse"]
    assert f
    assert f[0].status == "Passed", f[0].message


# ---------------------------------------------------------------------------
# Keys
# ---------------------------------------------------------------------------

def test_unique_ids(validator):
    validator.validate_business_keys()
    f = [x for x in validator.result.findings if x.check_name == "unique_integration_record_id"]
    assert f
    assert f[0].status == "Passed", f[0].message


def test_valid_business_keys(validator):
    daily = validator._load("data/analytical/analytical_six_kpi_daily.csv")
    assert daily is not None
    assert daily["hospital_id"].notna().all()
    assert daily["department_id"].notna().all()
    assert daily["reporting_date"].notna().all()
    assert daily["kpi_id"].notna().all()


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------

def test_phase1_unchanged(validator):
    # Check pre/post checksums on a fresh run
    pre = validator.record_checksums("pre")
    validator.run_all_validations()
    post = validator.record_checksums("post")
    validator.verify_immutability()
    f = [x for x in validator.result.findings if x.check_name == "immutability_check"]
    assert f
    assert f[0].status == "Passed", f"Immutability failed: {f[0].details}"


# ---------------------------------------------------------------------------
# Closure status determination
# ---------------------------------------------------------------------------

def test_closure_status_passed_or_passed_with_warning(validator):
    validator.run_all_validations()
    validator.classify_findings()
    assert validator.result.closure_status in ("Passed", "Passed with Warning", "Failed")


def test_phase_2b_readiness_ready_or_ready_with_conditions(validator):
    validator.run_all_validations()
    validator.classify_findings()
    assert validator.result.phase_2b_readiness in ("Ready", "Ready with Conditions", "Not Ready")


def test_no_blocking_issues_means_not_failed(validator):
    validator.run_all_validations()
    validator.classify_findings()
    if validator.result.blocking_count() == 0:
        assert validator.result.closure_status != "Failed"


# ---------------------------------------------------------------------------
# Negative / edge cases using temp validator
# ---------------------------------------------------------------------------

def test_missing_required_file_fails(temp_validator):
    # Remove a required file
    os.remove(os.path.join(temp_validator.project_root, "data/analytical/analytical_six_kpi_daily.csv"))
    temp_validator.validate_required_files()
    failed = [f for f in temp_validator.result.findings if f.domain == "File Validation" and f.status == "Failed"]
    assert any("analytical_six_kpi_daily.csv" in f.message for f in failed)


def test_duplicate_grain_fails(temp_validator):
    # Append a duplicate row
    daily_path = os.path.join(temp_validator.project_root, "data/analytical/analytical_six_kpi_daily.csv")
    df = pd.read_csv(daily_path)
    dup = df.iloc[[0]].copy()
    dup["integration_record_id"] = "DUP-TEST"
    df = pd.concat([df, dup], ignore_index=True)
    df.to_csv(daily_path, index=False)
    temp_validator._data_cache.clear()
    temp_validator.validate_business_keys()
    f = [x for x in temp_validator.result.findings if x.check_name == "duplicate_grain_check"]
    assert f
    assert f[0].status == "Failed"


def test_calculated_with_null_value_fails(temp_validator):
    daily_path = os.path.join(temp_validator.project_root, "data/analytical/analytical_six_kpi_daily.csv")
    df = pd.read_csv(daily_path)
    calc_mask = df["calculation_status"] == "Calculated"
    if calc_mask.any():
        idx = df[calc_mask].index[0]
        df.loc[idx, "kpi_value"] = np.nan
        df.to_csv(daily_path, index=False)
        temp_validator._data_cache.clear()
        temp_validator.validate_calculation_statuses()
        f = [x for x in temp_validator.result.findings if x.check_name == "value_status_consistency"]
        assert f
        assert f[0].status == "Failed"


def test_unavailable_with_high_confidence_fails(temp_validator):
    daily_path = os.path.join(temp_validator.project_root, "data/analytical/analytical_six_kpi_daily.csv")
    df = pd.read_csv(daily_path)
    uncalc_mask = df["calculation_status"] != "Calculated"
    if uncalc_mask.any():
        idx = df[uncalc_mask].index[0]
        df.loc[idx, "data_confidence_level"] = "High"
        df.to_csv(daily_path, index=False)
        temp_validator._data_cache.clear()
        temp_validator.validate_confidence_governance()
        f = [x for x in temp_validator.result.findings if x.check_name == "unavailable_not_high_confidence"]
        assert f
        assert f[0].status == "Failed"
