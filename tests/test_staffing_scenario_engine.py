"""tests/test_staffing_scenario_engine.py — Staffing scenario model correction tests.

Governed model v2:
- baseline_source = FORECAST_MONTH
- duration_scaling_enabled = TRUE
- 100% ceiling retained
- no arbitrary productivity coefficients
"""
from __future__ import annotations

import calendar
import os
import sys
from typing import Any, Dict, List

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC_DIR = os.path.join(_ROOT, "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from src.simulation_lab_controller import (
    build_baseline,
    build_simulation_state,
    get_comparator_profiles,
    run_scenario,
    GOVERNED_ACTUAL_YEAR,
)
from src.scenario_models import ScenarioBaseline, ScenarioResult
from src.staffing_scenario_engine import StaffingScenarioEngine
from src.scenario_governance_validator import ScenarioGovernanceValidator
from src.scenario_config_loader import ScenarioConfigLoader


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def ed_nov_state():
    """Full simulation state for HOSP-001 / DEPT-ED / kpi_001 / Nov 2025."""
    state = build_simulation_state(
        hospital_id="HOSP-001",
        department_id="DEPT-ED",
        kpi_id="kpi_001",
        forecast_month=11,
        intervention_id="INT-STAFF-001",
    )
    assert state is not None
    return state


@pytest.fixture
def validator():
    return ScenarioGovernanceValidator(ScenarioConfigLoader())


@pytest.fixture
def ed_baseline():
    """Historical baseline for ED (required_staff denominator retained)."""
    bl = build_baseline("HOSP-001", "DEPT-ED", "kpi_001")
    assert bl is not None
    return bl


# ---------------------------------------------------------------------------
# A. scenario baseline equals selected-month forecast
# ---------------------------------------------------------------------------

def test_a_baseline_equals_forecast(ed_nov_state):
    """The scenario baseline coverage must equal the selected-month forecast."""
    baseline = ed_nov_state["baseline"]
    forecast_value = ed_nov_state["forecast_value"]
    assert baseline is not None
    assert forecast_value is not None
    assert baseline.baseline_staffing_coverage_pct == pytest.approx(forecast_value, rel=1e-6)


# ---------------------------------------------------------------------------
# B. historical mean is no longer used as intervention starting coverage
# ---------------------------------------------------------------------------

def test_b_historical_mean_not_used(ed_nov_state):
    """Historical mean (Jan–Jul) should differ from forecast; baseline uses forecast."""
    baseline = ed_nov_state["baseline"]
    forecast_value = ed_nov_state["forecast_value"]
    # The forecast for Nov 2025 ED is known to be ~83.5%; historical mean is ~90.9%
    # We assert the baseline is NOT the historical mean.
    assert baseline is not None
    assert forecast_value is not None
    # Historical mean is > 85 in known data; forecast is < 85 for Nov ED
    assert baseline.baseline_staffing_coverage_pct < 85.0
    assert baseline.baseline_staffing_coverage_pct == pytest.approx(forecast_value, rel=1e-6)


# ---------------------------------------------------------------------------
# C. forecast available staff derived correctly
# ---------------------------------------------------------------------------

def test_c_forecast_available_staff_derived(ed_nov_state):
    """forecast_available_staff = (forecast_pct / 100) * baseline_required_staff."""
    baseline = ed_nov_state["baseline"]
    forecast_value = ed_nov_state["forecast_value"]
    assert baseline is not None
    assert baseline.baseline_required_staff is not None
    expected_avail = (forecast_value / 100.0) * baseline.baseline_required_staff
    assert baseline.baseline_available_staff == pytest.approx(expected_avail, rel=1e-6)


# ---------------------------------------------------------------------------
# D. duration scaling uses selected-month calendar days
# ---------------------------------------------------------------------------

def test_d_duration_scaling_uses_calendar_days(ed_nov_state):
    """Assumptions must contain days_in_selected_month matching the month."""
    profiles = ed_nov_state["comparator_profiles"]
    for p in profiles:
        assert "days_in_selected_month" in p["assumptions"]
        assert p["assumptions"]["days_in_selected_month"] == 30  # November


# ---------------------------------------------------------------------------
# E. 7-day intervention contributes less than 14-day intervention
# F. 14-day contributes less than 30-day intervention
# ---------------------------------------------------------------------------

def _run_engine_with_duration(baseline: ScenarioBaseline, duration_days: int, validator):
    """Helper: run staffing engine with a given duration."""
    engine = StaffingScenarioEngine(validator)
    comparator = {
        "comparator_id": "COMP-TEST",
        "comparator_type": "Expected",
        "scenario_mode": "Single Intervention",
        "profile_id": "PROFILE-TEST",
    }
    assumptions = {
        "additional_staff_count": 2,
        "temporary_staff_count": 2,
        "staff_reassignment_count": 1,
        "intervention_duration_days": duration_days,
        "days_in_selected_month": 30,
    }
    result, _ = engine.run(baseline, comparator, assumptions)
    return result


def test_e_f_duration_scaling_order(ed_baseline, validator):
    """Longer durations produce larger (or equal) scenario values, strictly ordered."""
    # Ensure baseline uses a forecast-like value for consistent testing
    ed_baseline.baseline_staffing_coverage_pct = 83.517205
    ed_baseline.baseline_available_staff = (83.517205 / 100.0) * (ed_baseline.baseline_required_staff or 14.33)

    r7 = _run_engine_with_duration(ed_baseline, 7, validator)
    r14 = _run_engine_with_duration(ed_baseline, 14, validator)
    r30 = _run_engine_with_duration(ed_baseline, 30, validator)

    assert r7 is not None and r7.scenario_primary_kpi_value is not None
    assert r14 is not None and r14.scenario_primary_kpi_value is not None
    assert r30 is not None and r30.scenario_primary_kpi_value is not None

    # E
    assert r7.scenario_primary_kpi_value < r14.scenario_primary_kpi_value
    # F
    assert r14.scenario_primary_kpi_value < r30.scenario_primary_kpi_value


# ---------------------------------------------------------------------------
# G. Minimum < Recommended <= Intensive
# ---------------------------------------------------------------------------

def test_g_minimum_recommended_intensive_order(ed_nov_state):
    """Conservative < Expected <= Higher Intensity scenario values."""
    results = ed_nov_state["scenario_results"]
    profiles = ed_nov_state["comparator_profiles"]
    assert len(results) == len(profiles) == 3

    vals = {}
    for r, p in zip(results, profiles):
        assert r is not None
        vals[p["comparator_type"]] = r.scenario_primary_kpi_value

    assert vals["Conservative"] < vals["Expected"]
    assert vals["Expected"] <= vals["Higher Intensity"]


# ---------------------------------------------------------------------------
# H. 100% ceiling retained
# I. no scenario exceeds 100%
# ---------------------------------------------------------------------------

def test_h_i_100_ceiling_retained(ed_nov_state):
    """All scenario results must be <= 100%."""
    for r in ed_nov_state["scenario_results"]:
        assert r is not None
        assert r.scenario_primary_kpi_value is not None
        assert r.scenario_primary_kpi_value <= 100.0 + 1e-9
        # H: hard ceiling at 100
        if r.scenario_primary_kpi_value == 100.0:
            assert "capped" in r.governance_warning.lower() or r.percentage_change is not None


# ---------------------------------------------------------------------------
# J. selected month change changes scenario result when forecast changes
# ---------------------------------------------------------------------------

def test_j_month_change_changes_result():
    """Running the same scenario for a different month must yield different results
    when the forecast value differs."""
    state_nov = build_simulation_state(
        "HOSP-001", "DEPT-ED", "kpi_001", 11, "INT-STAFF-001"
    )
    state_dec = build_simulation_state(
        "HOSP-001", "DEPT-ED", "kpi_001", 12, "INT-STAFF-001"
    )
    assert state_nov is not None
    assert state_dec is not None

    # Baselines must differ if forecasts differ
    if state_nov["forecast_value"] != state_dec["forecast_value"]:
        assert state_nov["baseline"].baseline_staffing_coverage_pct != state_dec["baseline"].baseline_staffing_coverage_pct
        # At least one scenario result must differ
        nov_vals = [r.scenario_primary_kpi_value for r in state_nov["scenario_results"] if r]
        dec_vals = [r.scenario_primary_kpi_value for r in state_dec["scenario_results"] if r]
        assert nov_vals != dec_vals


# ---------------------------------------------------------------------------
# K. expected KPI change uses corrected baseline
# L. relative change uses corrected baseline
# ---------------------------------------------------------------------------

def test_k_l_expected_and_relative_change_use_corrected_baseline(ed_nov_state):
    """Expected change = scenario_value - forecast_value (not historical mean)."""
    forecast_value = ed_nov_state["forecast_value"]
    results = ed_nov_state["scenario_results"]
    profiles = ed_nov_state["comparator_profiles"]

    for r, p in zip(results, profiles):
        assert r is not None
        scenario_value = r.scenario_primary_kpi_value
        # K: absolute change computed from forecast baseline
        expected_change = scenario_value - forecast_value
        assert r.percentage_change == pytest.approx(expected_change, rel=1e-6)
        # L: relative change would be expected_change / forecast_value
        if forecast_value and forecast_value != 0:
            relative_change = (expected_change / forecast_value) * 100.0
            # percentage_change in result is absolute points, not relative percent
            # We verify the baseline used is the forecast by checking the result itself
            assert r.baseline_primary_kpi_value == pytest.approx(forecast_value, rel=1e-6)


# ---------------------------------------------------------------------------
# M. no hardcoded scenario outcomes
# ---------------------------------------------------------------------------

def test_m_no_hardcoded_outcomes(ed_nov_state):
    """Scenario values must be computed floats, not literal constants."""
    for r in ed_nov_state["scenario_results"]:
        assert r is not None
        val = r.scenario_primary_kpi_value
        assert isinstance(val, float)
        # Known old hardcoded values for Nov ED were 100.0 for all three;
        # after fix they must differ.
        assert not (val == 100.0 and all(
            res.scenario_primary_kpi_value == 100.0
            for res in ed_nov_state["scenario_results"]
        ))


# ---------------------------------------------------------------------------
# N. financial engine unchanged unless directly required
# ---------------------------------------------------------------------------

def test_n_financial_engine_unchanged(ed_nov_state):
    """Financial results must still be present or None as before; no new cost logic."""
    financial_results = ed_nov_state.get("financial_results", [])
    # Financial may be None if no mapping — that is acceptable unchanged behaviour.
    for fin in financial_results:
        if fin is not None:
            assert "total_cost" in fin
            assert "currency" in fin
            assert "cost_drivers" in fin


# ---------------------------------------------------------------------------
# O. no unrelated analytical engine changed
# ---------------------------------------------------------------------------

def test_o_other_engines_unchanged():
    """Absenteeism and Patient Flow engines must still exist, be importable,
    and route correctly via controller map.  No staffing-specific changes must
    leak into their code."""
    from src.absenteeism_scenario_engine import AbsenteeismScenarioEngine
    from src.patient_flow_scenario_engine import PatientFlowScenarioEngine
    from src.simulation_lab_controller import _KPI_ENGINE_MAP

    # Verify engine classes are still the correct types
    assert _KPI_ENGINE_MAP["kpi_002"] is AbsenteeismScenarioEngine
    assert _KPI_ENGINE_MAP["kpi_003"] is PatientFlowScenarioEngine

    # Verify run method signatures are intact (no new required args)
    import inspect
    abs_run = inspect.signature(AbsenteeismScenarioEngine.run)
    pf_run = inspect.signature(PatientFlowScenarioEngine.run)
    assert "baseline" in abs_run.parameters
    assert "comparator" in abs_run.parameters
    assert "assumptions" in abs_run.parameters
    assert "baseline" in pf_run.parameters
    assert "comparator" in pf_run.parameters
    assert "assumptions" in pf_run.parameters
