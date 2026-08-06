"""
Tests for Patient Experience KPI Engine (Step 2A-4)

Covers:
- Architecture and scope
- Patient Complaint Rate (kpi_005)
- Patient Satisfaction Score (kpi_006)
- Thresholds, confidence, outputs, immutability
"""

import sys
from pathlib import Path
import tempfile
import shutil

import pandas as pd
import pytest

# Ensure src/ is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from patient_experience_kpi_engine import PatientExperienceKPIEngine, PatientExperienceKPIEngineResult
# CalculationStatus is not in analytical_contracts; use string literals directly


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def project_root():
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def engine(project_root):
    return PatientExperienceKPIEngine(project_root=project_root)


@pytest.fixture
def sample_operational_df():
    return pd.DataFrame({
        "operational_daily_id": ["OP_001", "OP_002", "OP_003", "OP_004"],
        "hospital_id": ["H_001", "H_001", "H_002", "H_002"],
        "department_id": ["DEPT_001", "DEPT_001", "DEPT_002", "DEPT_002"],
        "reporting_date": ["2026-07-01", "2026-07-02", "2026-07-01", "2026-07-02"],
        "reporting_month": [7, 7, 7, 7],
        "reporting_year": [2026, 2026, 2026, 2026],
        "complaint_valid_record_count": [2.0, 0.0, 5.0, None],
        "encounter_record_count": [100.0, 100.0, 50.0, 80.0],
        "survey_score_weighted_sum": [120.0, 80.0, None, 200.0],
        "survey_valid_score_record_count": [30.0, 20.0, 10.0, 0.0],
    })


@pytest.fixture
def sample_complaints_df():
    return pd.DataFrame({
        "complaint_id": ["C_001", "C_002", "C_003", "C_004"],
        "hospital_id": ["H_001", "H_001", "H_002", "H_002"],
        "department_id": ["DEPT_001", "DEPT_001", "DEPT_002", "DEPT_002"],
        "complaint_date": ["2026-07-01", "2026-07-01", "2026-07-01", "2026-07-02"],
        "complaint_count_eligible_flag": [True, True, True, False],
        "complaint_duplicate_flag": [False, False, False, False],
        "complaint_record_valid_flag": [True, True, True, True],
        "exclusion_reason_code": [None, None, None, "DUPLICATE"],
    })


@pytest.fixture
def sample_surveys_df():
    return pd.DataFrame({
        "survey_id": ["S_001", "S_002", "S_003"],
        "hospital_id": ["H_001", "H_001", "H_002"],
        "department_id": ["DEPT_001", "DEPT_001", "DEPT_002"],
        "survey_date": ["2026-07-01", "2026-07-01", "2026-07-02"],
        "satisfaction_score_numeric": [4.0, 3.0, 5.0],
        "response_count": [10, 20, 5],
        "survey_score_eligible_flag": [True, True, True],
        "exclusion_reason_code": [None, None, None],
    })


# ---------------------------------------------------------------------------
# Architecture
# ---------------------------------------------------------------------------

def test_safe_import():
    from patient_experience_kpi_engine import PatientExperienceKPIEngine
    assert PatientExperienceKPIEngine is not None


def test_no_automatic_execution(project_root):
    engine = PatientExperienceKPIEngine(project_root=project_root)
    assert engine.operational_df is None


def test_only_kpi_005_and_006_supported():
    assert PatientExperienceKPIEngine.SUPPORTED_KPI_IDS == {"kpi_005", "kpi_006"}


def test_no_workforce_kpi_calculated(engine):
    assert "kpi_001" not in engine.SUPPORTED_KPI_IDS
    assert "kpi_002" not in engine.SUPPORTED_KPI_IDS


def test_no_patient_flow_kpi_calculated(engine):
    assert "kpi_003" not in engine.SUPPORTED_KPI_IDS
    assert "kpi_004" not in engine.SUPPORTED_KPI_IDS


# ---------------------------------------------------------------------------
# Complaint Rate (kpi_005)
# ---------------------------------------------------------------------------

def test_complaint_rate_standard_calculation(engine, sample_operational_df):
    engine.operational_df = sample_operational_df
    engine.registry = {"kpi_005": type("obj", (object,), {"kpi_name": "Patient Complaint Rate"})()}
    readiness = {"calculation_readiness": "Provisional but Calculable"}
    row = sample_operational_df.iloc[0]
    result = engine.calculate_complaint_rate(row, readiness)
    assert result.calculation_status == "Calculated"
    assert result.kpi_value == pytest.approx(20.0)  # 2 / 100 * 1000
    assert result.numerator_value == 2.0
    assert result.denominator_value == 100.0
    assert result.unit == "Complaints per 1000 encounters"


def test_complaint_rate_zero_complaints(engine, sample_operational_df):
    engine.operational_df = sample_operational_df
    engine.registry = {"kpi_005": type("obj", (object,), {"kpi_name": "Patient Complaint Rate"})()}
    readiness = {"calculation_readiness": "Provisional but Calculable"}
    row = sample_operational_df.iloc[1]
    result = engine.calculate_complaint_rate(row, readiness)
    assert result.calculation_status == "Calculated"
    assert result.kpi_value == pytest.approx(0.0)
    assert result.numerator_value == 0.0


def test_complaint_rate_zero_denominator(engine, sample_operational_df):
    engine.operational_df = sample_operational_df.copy()
    engine.operational_df.loc[0, "encounter_record_count"] = 0.0
    engine.registry = {"kpi_005": type("obj", (object,), {"kpi_name": "Patient Complaint Rate"})()}
    readiness = {"calculation_readiness": "Provisional but Calculable"}
    row = engine.operational_df.iloc[0]
    result = engine.calculate_complaint_rate(row, readiness)
    assert result.calculation_status == "Zero Denominator"
    assert result.kpi_value is None


def test_complaint_rate_null_denominator(engine, sample_operational_df):
    engine.operational_df = sample_operational_df.copy()
    engine.operational_df.loc[0, "encounter_record_count"] = None
    engine.registry = {"kpi_005": type("obj", (object,), {"kpi_name": "Patient Complaint Rate"})()}
    readiness = {"calculation_readiness": "Provisional but Calculable"}
    row = engine.operational_df.iloc[0]
    result = engine.calculate_complaint_rate(row, readiness)
    assert result.calculation_status == "Insufficient Data"
    assert result.kpi_value is None


def test_complaint_rate_null_complaint_count(engine, sample_operational_df):
    engine.operational_df = sample_operational_df
    engine.registry = {"kpi_005": type("obj", (object,), {"kpi_name": "Patient Complaint Rate"})()}
    readiness = {"calculation_readiness": "Provisional but Calculable"}
    row = sample_operational_df.iloc[3]
    result = engine.calculate_complaint_rate(row, readiness)
    assert result.calculation_status == "Insufficient Data"
    assert result.kpi_value is None


def test_complaint_rate_invalid_complaint_count(engine, sample_operational_df):
    engine.operational_df = sample_operational_df.copy()
    engine.operational_df["complaint_valid_record_count"] = engine.operational_df["complaint_valid_record_count"].astype(object)
    engine.operational_df.loc[0, "complaint_valid_record_count"] = "invalid"
    engine.registry = {"kpi_005": type("obj", (object,), {"kpi_name": "Patient Complaint Rate"})()}
    readiness = {"calculation_readiness": "Provisional but Calculable"}
    row = engine.operational_df.iloc[0]
    result = engine.calculate_complaint_rate(row, readiness)
    assert result.calculation_status == "Invalid Input"
    assert result.kpi_value is None


def test_complaint_rate_provisional_denominator_preserved(engine, sample_operational_df):
    engine.operational_df = sample_operational_df
    engine.registry = {"kpi_005": type("obj", (object,), {"kpi_name": "Patient Complaint Rate"})()}
    readiness = {"calculation_readiness": "Provisional but Calculable"}
    row = sample_operational_df.iloc[0]
    result = engine.calculate_complaint_rate(row, readiness)
    assert result.readiness_status == "Provisional but Calculable"


def test_complaint_rate_deterministic_id(engine, sample_operational_df):
    engine.operational_df = sample_operational_df
    engine.registry = {"kpi_005": type("obj", (object,), {"kpi_name": "Patient Complaint Rate"})()}
    readiness = {"calculation_readiness": "Provisional but Calculable"}
    row = sample_operational_df.iloc[0]
    result = engine.calculate_complaint_rate(row, readiness)
    expected_id = f"AKPI-{result.kpi_id}-{result.hospital_id}-{result.department_id}-20260701"
    assert expected_id == "AKPI-kpi_005-H_001-DEPT_001-20260701"


# ---------------------------------------------------------------------------
# Satisfaction Score (kpi_006)
# ---------------------------------------------------------------------------

def test_satisfaction_score_standard_calculation(engine, sample_operational_df):
    engine.operational_df = sample_operational_df
    engine.registry = {"kpi_006": type("obj", (object,), {"kpi_name": "Patient Satisfaction Score"})()}
    readiness = {"calculation_readiness": "Calculable"}
    row = sample_operational_df.iloc[0]
    result = engine.calculate_satisfaction_score(row, readiness)
    assert result.calculation_status == "Calculated"
    assert result.kpi_value == pytest.approx(4.0)  # 120 / 30
    assert result.numerator_value == 120.0
    assert result.denominator_value == 30.0
    assert result.unit == "Score (1-5 scale)"


def test_satisfaction_score_multiple_rows_weighted():
    """Weighted score = sum(score * response) / sum(response)"""
    weighted_sum = 4.0 * 10 + 3.0 * 20  # 40 + 60 = 100
    valid_count = 10 + 20  # 30
    expected = weighted_sum / valid_count  # 3.333...
    assert expected == pytest.approx(3.333, abs=0.01)


def test_satisfaction_score_zero_responses(engine, sample_operational_df):
    engine.operational_df = sample_operational_df
    engine.registry = {"kpi_006": type("obj", (object,), {"kpi_name": "Patient Satisfaction Score"})()}
    readiness = {"calculation_readiness": "Calculable"}
    row = sample_operational_df.iloc[3]
    result = engine.calculate_satisfaction_score(row, readiness)
    assert result.calculation_status == "Zero Denominator"
    assert result.kpi_value is None


def test_satisfaction_score_null_response_count(engine, sample_operational_df):
    engine.operational_df = sample_operational_df.copy()
    engine.operational_df.loc[0, "survey_valid_score_record_count"] = None
    engine.registry = {"kpi_006": type("obj", (object,), {"kpi_name": "Patient Satisfaction Score"})()}
    readiness = {"calculation_readiness": "Calculable"}
    row = engine.operational_df.iloc[0]
    result = engine.calculate_satisfaction_score(row, readiness)
    assert result.calculation_status == "Insufficient Data"
    assert result.kpi_value is None


def test_satisfaction_score_null_weighted_sum(engine, sample_operational_df):
    engine.operational_df = sample_operational_df
    engine.registry = {"kpi_006": type("obj", (object,), {"kpi_name": "Patient Satisfaction Score"})()}
    readiness = {"calculation_readiness": "Calculable"}
    row = sample_operational_df.iloc[2]
    result = engine.calculate_satisfaction_score(row, readiness)
    assert result.calculation_status == "Insufficient Data"
    assert result.kpi_value is None


def test_satisfaction_score_invalid_score(engine, sample_operational_df):
    engine.operational_df = sample_operational_df.copy()
    engine.operational_df["survey_score_weighted_sum"] = engine.operational_df["survey_score_weighted_sum"].astype(object)
    engine.operational_df.loc[0, "survey_score_weighted_sum"] = "invalid"
    engine.registry = {"kpi_006": type("obj", (object,), {"kpi_name": "Patient Satisfaction Score"})()}
    readiness = {"calculation_readiness": "Calculable"}
    row = engine.operational_df.iloc[0]
    result = engine.calculate_satisfaction_score(row, readiness)
    assert result.calculation_status == "Invalid Input"
    assert result.kpi_value is None


def test_satisfaction_score_deterministic_id(engine, sample_operational_df):
    engine.operational_df = sample_operational_df
    engine.registry = {"kpi_006": type("obj", (object,), {"kpi_name": "Patient Satisfaction Score"})()}
    readiness = {"calculation_readiness": "Calculable"}
    row = sample_operational_df.iloc[0]
    result = engine.calculate_satisfaction_score(row, readiness)
    expected_id = f"AKPI-{result.kpi_id}-{result.hospital_id}-{result.department_id}-20260701"
    assert expected_id == "AKPI-kpi_006-H_001-DEPT_001-20260701"


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------

def test_evidence_kpi_005(engine, sample_operational_df):
    engine.operational_df = sample_operational_df
    engine.registry = {"kpi_005": type("obj", (object,), {"kpi_name": "Patient Complaint Rate"})()}
    readiness = {"calculation_readiness": "Provisional but Calculable"}
    row = sample_operational_df.iloc[0]
    result = engine.calculate_complaint_rate(row, readiness)
    evidence = engine.build_evidence(result, row)
    types = [e["evidence_type"] for e in evidence]
    assert "numerator" in types
    assert "denominator" in types
    assert "multiplier" in types


def test_evidence_kpi_006(engine, sample_operational_df):
    engine.operational_df = sample_operational_df
    engine.registry = {"kpi_006": type("obj", (object,), {"kpi_name": "Patient Satisfaction Score"})()}
    readiness = {"calculation_readiness": "Calculable"}
    row = sample_operational_df.iloc[0]
    result = engine.calculate_satisfaction_score(row, readiness)
    evidence = engine.build_evidence(result, row)
    types = [e["evidence_type"] for e in evidence]
    assert "numerator" in types
    assert "denominator" in types
    assert "scale" in types
    assert "weighting_method" in types


# ---------------------------------------------------------------------------
# Exclusions
# ---------------------------------------------------------------------------

def test_exclusions_complaint(engine, sample_operational_df, sample_complaints_df):
    engine.operational_df = sample_operational_df
    engine.complaints_df = sample_complaints_df
    engine.registry = {"kpi_005": type("obj", (object,), {"kpi_name": "Patient Complaint Rate"})()}
    readiness = {"calculation_readiness": "Provisional but Calculable"}
    row = sample_operational_df.iloc[3]  # H_002, DEPT_002, 2026-07-02
    result = engine.calculate_complaint_rate(row, readiness)
    result.calculation_status = "Calculated"  # Force for exclusion test
    exclusions = engine.build_exclusions(result)
    assert len(exclusions) == 1
    assert exclusions[0]["reason_code"] == "DUPLICATE"


def test_exclusions_survey(engine, sample_operational_df, sample_surveys_df):
    engine.operational_df = sample_operational_df
    engine.surveys_df = sample_surveys_df
    engine.registry = {"kpi_006": type("obj", (object,), {"kpi_name": "Patient Satisfaction Score"})()}
    readiness = {"calculation_readiness": "Calculable"}
    row = sample_operational_df.iloc[0]
    result = engine.calculate_satisfaction_score(row, readiness)
    exclusions = engine.build_exclusions(result)
    # No excluded surveys in fixture
    assert len(exclusions) == 0


# ---------------------------------------------------------------------------
# Lineage
# ---------------------------------------------------------------------------

def test_lineage_kpi_005(engine, sample_operational_df):
    engine.operational_df = sample_operational_df
    engine.complaints_df = pd.DataFrame()
    engine.registry = {"kpi_005": type("obj", (object,), {"kpi_name": "Patient Complaint Rate"})()}
    row = sample_operational_df.iloc[0]
    result = engine.calculate_complaint_rate(row, {"calculation_readiness": "Provisional but Calculable"})
    lineage = engine.build_lineage(result, row)
    assert len(lineage) == 2
    assert lineage[0]["source_dataset"] == "processed_operational_daily.csv"
    assert lineage[1]["source_dataset"] == "processed_patient_complaints.csv"


def test_lineage_kpi_006(engine, sample_operational_df):
    engine.operational_df = sample_operational_df
    engine.surveys_df = pd.DataFrame()
    engine.registry = {"kpi_006": type("obj", (object,), {"kpi_name": "Patient Satisfaction Score"})()}
    row = sample_operational_df.iloc[0]
    result = engine.calculate_satisfaction_score(row, {"calculation_readiness": "Calculable"})
    lineage = engine.build_lineage(result, row)
    assert len(lineage) == 2
    assert lineage[0]["source_dataset"] == "processed_operational_daily.csv"
    assert lineage[1]["source_dataset"] == "processed_patient_surveys.csv"


# ---------------------------------------------------------------------------
# Issues
# ---------------------------------------------------------------------------

def test_issue_zero_denominator(engine, sample_operational_df):
    engine.operational_df = sample_operational_df.copy()
    engine.operational_df.loc[0, "encounter_record_count"] = 0.0
    engine.registry = {"kpi_005": type("obj", (object,), {"kpi_name": "Patient Complaint Rate"})()}
    row = engine.operational_df.iloc[0]
    result = engine.calculate_complaint_rate(row, {"calculation_readiness": "Provisional but Calculable"})
    issues = engine.collect_issues(result, row)
    assert any(i["issue_type"] == "ZERO_DENOMINATOR" for i in issues)


def test_issue_provisional_denominator(engine, sample_operational_df):
    engine.operational_df = sample_operational_df
    engine.registry = {"kpi_005": type("obj", (object,), {"kpi_name": "Patient Complaint Rate"})()}
    row = sample_operational_df.iloc[0]
    result = engine.calculate_complaint_rate(row, {"calculation_readiness": "Provisional but Calculable"})
    issues = engine.collect_issues(result, row)
    assert any(i["issue_type"] == "PROVISIONAL_DENOMINATOR" for i in issues)


# ---------------------------------------------------------------------------
# Formula verification
# ---------------------------------------------------------------------------

def test_formula_verification_passes(engine, sample_operational_df):
    engine.operational_df = sample_operational_df
    engine.registry = {
        "kpi_005": type("obj", (object,), {"kpi_name": "Patient Complaint Rate"})(),
        "kpi_006": type("obj", (object,), {"kpi_name": "Patient Satisfaction Score"})(),
    }
    results = []
    for _, row in sample_operational_df.iterrows():
        r005 = engine.calculate_complaint_rate(row, {"calculation_readiness": "Provisional but Calculable"})
        results.append(r005)
        r006 = engine.calculate_satisfaction_score(row, {"calculation_readiness": "Calculable"})
        results.append(r006)
    fv = engine.verify_formulas(results)
    assert fv["verification_status"] == "Passed"
    assert fv["mismatches"] == 0


def test_end_to_end_dry_run(project_root):
    engine = PatientExperienceKPIEngine(project_root=project_root)
    result = engine.run()
    assert isinstance(result, PatientExperienceKPIEngineResult)
    kpi_ids = {r.kpi_id for r in result.kpi_results}
    assert kpi_ids == {"kpi_005", "kpi_006"}
    assert result.formula_verification["verification_status"] == "Passed"


def test_end_to_end_only_two_kpis(project_root):
    engine = PatientExperienceKPIEngine(project_root=project_root)
    result = engine.run()
    kpi_ids = {r.kpi_id for r in result.kpi_results}
    assert "kpi_001" not in kpi_ids
    assert "kpi_002" not in kpi_ids
    assert "kpi_003" not in kpi_ids
    assert "kpi_004" not in kpi_ids


# ---------------------------------------------------------------------------
# Complaint denominator readiness
# ---------------------------------------------------------------------------

def test_complaint_denominator_readiness(project_root):
    engine = PatientExperienceKPIEngine(project_root=project_root)
    engine.load_inputs()
    readiness = engine.assess_complaint_denominator_readiness()
    assert readiness["denominator_definition"] == "encounter_record_count"
    assert readiness["provisional_status"] is True
    assert readiness["calculation_readiness"] == "Provisional but Calculable"


# ---------------------------------------------------------------------------
# Satisfaction weighting readiness
# ---------------------------------------------------------------------------

def test_satisfaction_weighting_readiness(project_root):
    engine = PatientExperienceKPIEngine(project_root=project_root)
    engine.load_inputs()
    readiness = engine.assess_satisfaction_weighting_readiness()
    assert readiness["score_scale"] == "1-5"
    assert readiness["weighted_calculation_supported"] is True
    assert readiness["calculation_readiness"] == "Calculable"


# ---------------------------------------------------------------------------
# Thresholds and confidence
# ---------------------------------------------------------------------------

def test_threshold_provisional_preserved(engine, sample_operational_df):
    engine.operational_df = sample_operational_df
    engine.registry = {"kpi_005": type("obj", (object,), {"kpi_name": "Patient Complaint Rate"})()}
    row = sample_operational_df.iloc[0]
    result = engine.calculate_complaint_rate(row, {"calculation_readiness": "Provisional but Calculable"})
    assert result.threshold_approval_status == "Draft"
    assert result.threshold_is_provisional is True


def test_confidence_not_fabricated(engine, sample_operational_df):
    engine.operational_df = sample_operational_df
    engine.registry = {"kpi_005": type("obj", (object,), {"kpi_name": "Patient Complaint Rate"})()}
    row = sample_operational_df.iloc[0]
    result = engine.calculate_complaint_rate(row, {"calculation_readiness": "Provisional but Calculable"})
    assert result.data_confidence_level in ("Unavailable", "Medium", "High", "Low")


# ---------------------------------------------------------------------------
# Output DataFrames
# ---------------------------------------------------------------------------

def test_daily_dataframe_schema(engine, sample_operational_df):
    engine.operational_df = sample_operational_df
    engine.registry = {
        "kpi_005": type("obj", (object,), {"kpi_name": "Patient Complaint Rate"})(),
        "kpi_006": type("obj", (object,), {"kpi_name": "Patient Satisfaction Score"})(),
    }
    results = []
    for _, row in sample_operational_df.iterrows():
        results.append(engine.calculate_complaint_rate(row, {"calculation_readiness": "Provisional but Calculable"}))
        results.append(engine.calculate_satisfaction_score(row, {"calculation_readiness": "Calculable"}))
    df = engine.to_daily_dataframe(results)
    assert "analytical_record_id" in df.columns
    assert "kpi_id" in df.columns
    assert "calculation_status" in df.columns
    assert df["kpi_id"].nunique() == 2


def test_unique_ids(engine, sample_operational_df):
    engine.operational_df = sample_operational_df
    engine.registry = {
        "kpi_005": type("obj", (object,), {"kpi_name": "Patient Complaint Rate"})(),
        "kpi_006": type("obj", (object,), {"kpi_name": "Patient Satisfaction Score"})(),
    }
    results = []
    for _, row in sample_operational_df.iterrows():
        results.append(engine.calculate_complaint_rate(row, {"calculation_readiness": "Provisional but Calculable"}))
        results.append(engine.calculate_satisfaction_score(row, {"calculation_readiness": "Calculable"}))
    df = engine.to_daily_dataframe(results)
    assert df["analytical_record_id"].is_unique


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------

def test_immutability_verification(project_root):
    engine = PatientExperienceKPIEngine(project_root=project_root)
    baseline = {}
    for f in ["data/processed/processed_operational_daily.csv"]:
        p = project_root / f
        if p.exists():
            import hashlib
            baseline[f] = hashlib.sha256(p.read_bytes()).hexdigest()
    result = engine.verify_immutability(baseline)
    assert result["verified"] is True
    assert result["datasets_unchanged"] == len(baseline)


# ---------------------------------------------------------------------------
# End-to-end dry run
# ---------------------------------------------------------------------------

def test_end_to_end_dry_run(project_root):
    engine = PatientExperienceKPIEngine(project_root=project_root)
    result = engine.run()
    assert isinstance(result, PatientExperienceKPIEngineResult)
    kpi_ids = {r.kpi_id for r in result.kpi_results}
    assert kpi_ids == {"kpi_005", "kpi_006"}
    assert result.formula_verification["verification_status"] == "Passed"


def test_end_to_end_only_two_kpis(project_root):
    engine = PatientExperienceKPIEngine(project_root=project_root)
    result = engine.run()
    kpi_ids = {r.kpi_id for r in result.kpi_results}
    assert "kpi_001" not in kpi_ids
    assert "kpi_002" not in kpi_ids
    assert "kpi_003" not in kpi_ids
    assert "kpi_004" not in kpi_ids


# ---------------------------------------------------------------------------
# Complaint denominator readiness
# ---------------------------------------------------------------------------

def test_complaint_denominator_readiness(project_root):
    engine = PatientExperienceKPIEngine(project_root=project_root)
    engine.load_inputs()
    readiness = engine.assess_complaint_denominator_readiness()
    assert readiness["denominator_definition"] == "encounter_record_count"
    assert readiness["provisional_status"] is True
    assert readiness["calculation_readiness"] == "Provisional but Calculable"


# ---------------------------------------------------------------------------
# Satisfaction weighting readiness
# ---------------------------------------------------------------------------

def test_satisfaction_weighting_readiness(project_root):
    engine = PatientExperienceKPIEngine(project_root=project_root)
    engine.load_inputs()
    readiness = engine.assess_satisfaction_weighting_readiness()
    assert readiness["score_scale"] == "1-5"
    assert readiness["weighted_calculation_supported"] is True
    assert readiness["calculation_readiness"] == "Calculable"
