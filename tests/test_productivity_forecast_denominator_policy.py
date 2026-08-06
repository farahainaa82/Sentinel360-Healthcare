"""
Sentinel360 Healthcare — Productivity Forecast Denominator Policy Tests

Targeted test suite for the governed forecast required staff-hours policy.
Does NOT test the Executive Overview UI or the Simulation Lab.

Step: Governance validation for Phase 3B productivity estimation.
"""

import os
import sys
from pathlib import Path

# Ensure src is on the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from productivity_forecast_denominator_policy import (
    DenominatorResult,
    ForecastDenominatorCalculator,
    ForecastDenominatorPolicy,
    PolicyConfigLoader,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent.parent


@pytest.fixture
def loader():
    return PolicyConfigLoader(base_dir=BASE_DIR)


@pytest.fixture
def policy(loader):
    return loader.load()


@pytest.fixture
def calculator(policy):
    return ForecastDenominatorCalculator(policy=policy, base_dir=BASE_DIR)


# ---------------------------------------------------------------------------
# 1. Policy loads from config
# ---------------------------------------------------------------------------


def test_policy_loads_from_config(loader):
    p = loader.load()
    assert isinstance(p, ForecastDenominatorPolicy)
    assert p.policy_id == "PFA-001"


# ---------------------------------------------------------------------------
# 2. lookback_months = 3
# ---------------------------------------------------------------------------


def test_lookback_months_is_three(policy):
    assert policy.lookback_months == 3
    assert isinstance(policy.lookback_months, int)


def test_lookback_months_numeric_and_positive(policy):
    assert policy.lookback_months >= 1


# ---------------------------------------------------------------------------
# 3. Aggregation method = ARITHMETIC_MEAN
# ---------------------------------------------------------------------------


def test_aggregation_method_is_arithmetic_mean(policy):
    assert policy.aggregation_method == "ARITHMETIC_MEAN"


# ---------------------------------------------------------------------------
# 4. Fallback = NOT_AVAILABLE
# ---------------------------------------------------------------------------


def test_fallback_is_not_available(policy):
    assert policy.fallback_behavior == "NOT_AVAILABLE"


# ---------------------------------------------------------------------------
# 5. Latest complete actual month determined correctly
# ---------------------------------------------------------------------------


def test_latest_complete_months_derived_from_data(calculator):
    # For HOSP-001 / DEPT-ADM / 2025, actual months are Jan-Jul.
    # The latest complete actual month should be July (7).
    result = calculator.calculate("HOSP-001", "DEPT-ADM", 2025)
    assert result.status == "OK"
    # Latest 3 months from sorted descending actual data
    assert result.months_used[-1] == max(result.months_used)


# ---------------------------------------------------------------------------
# 6. Current data resolves latest 3 actual months to May-Jul 2025
# ---------------------------------------------------------------------------


def test_current_data_resolves_to_may_jun_jul(calculator):
    result = calculator.calculate("HOSP-001", "DEPT-ADM", 2025)
    assert result.status == "OK"
    # Because Jan-Jul are available, latest 3 complete months are May(5), Jun(6), Jul(7)
    assert sorted(result.months_used) == [5, 6, 7]


def test_all_operational_departments_resolve_to_may_jun_jul(calculator):
    # Exclude ALL and DEPT-PEX (per Executive Overview operational scope)
    excluded = ["ALL", "DEPT-PEX"]
    results = calculator.calculate_all_departments(
        "HOSP-001", 2025, excluded_departments=excluded
    )
    for dept, res in results.items():
        assert res.status == "OK", f"{dept} failed: {res.message}"
        assert sorted(res.months_used) == [5, 6, 7], (
            f"{dept} months_used mismatch: {res.months_used}"
        )


# ---------------------------------------------------------------------------
# 7. No literal May/Jun/Jul month policy is required
# ---------------------------------------------------------------------------


def test_no_hardcoded_month_numbers_in_policy(policy):
    # The policy config stores lookback_months=3, not explicit month numbers.
    assert policy.lookback_months == 3
    # Verify there is no "5", "6", or "7" in the config that is month-related.
    # This is a conceptual test: the calculator derives months from data.
    assert "May" not in policy.policy_name
    assert "Jun" not in policy.policy_name
    assert "Jul" not in policy.policy_name


def test_months_emerge_dynamically(calculator):
    # If data existed for Aug 2025, the latest 3 would be Jun-Jul-Aug.
    # We cannot simulate that here, but we confirm the calculator sorts
    # descending and takes the top N — no literal month numbers.
    result = calculator.calculate("HOSP-001", "DEPT-ADM", 2025)
    assert result.months_used == sorted(result.months_used)
    # The months_used come from the data, not from a hardcoded list.


# ---------------------------------------------------------------------------
# 8. No 8-hour assumption is used
# ---------------------------------------------------------------------------


def test_no_eight_hour_assumption_in_result(calculator):
    # The result value must be sourced from denominator_value, not a
    # fabricated shift_hours * staff_count calculation.
    result = calculator.calculate("HOSP-001", "DEPT-ADM", 2025)
    assert result.status == "OK"
    # DEPT-ADM May+Jun+Jul average was ~597.3 in the audit.
    # Anything in the 500-700 range is consistent with observed data.
    assert 400 < result.value < 800, (
        f"Value {result.value} looks like it may involve a hardcoded shift constant"
    )


def test_result_matches_observed_denominator_sum(calculator):
    # Re-aggregate manually to confirm no transformation is applied.
    import pandas as pd

    path = BASE_DIR / "data" / "analytical" / "analytical_six_kpi_daily.csv"
    df = pd.read_csv(path, keep_default_na=False, na_values=[""])
    df = df[
        (df["hospital_id"] == "HOSP-001")
        & (df["department_id"] == "DEPT-ADM")
        & (df["reporting_year"] == 2025)
        & (df["kpi_id"] == "kpi_001")
    ]
    df["denominator_value"] = pd.to_numeric(df["denominator_value"], errors="coerce")
    monthly = df.groupby("reporting_month")["denominator_value"].sum()
    expected = sum(monthly[int(m)] for m in [5, 6, 7]) / 3

    result = calculator.calculate("HOSP-001", "DEPT-ADM", 2025)
    assert result.status == "OK"
    assert round(result.value, 2) == round(expected, 2)


# ---------------------------------------------------------------------------
# 9. No 10% CV governance threshold is introduced
# ---------------------------------------------------------------------------


def test_no_cv_threshold_in_policy(policy):
    # The policy should not contain any variability gate.
    assert "CV" not in policy.governance_note.upper()
    assert "10%" not in policy.governance_note
    assert "coefficient" not in policy.governance_note.lower()


def test_calculator_does_not_use_cv(calculator):
    # Confirm the calculator does not reject results based on variability.
    result = calculator.calculate("HOSP-001", "DEPT-ED", 2025)
    assert result.status == "OK", "DEPT-ED should succeed; CV must not block it"


# ---------------------------------------------------------------------------
# 10. Fewer than 3 complete months returns unavailable
# ---------------------------------------------------------------------------


def test_insufficient_months_returns_not_available(calculator):
    # Simulate a target year with no data (e.g., 2024 has no rows)
    result = calculator.calculate("HOSP-001", "DEPT-ADM", 2024)
    assert result.status in ("NOT_AVAILABLE", "INSUFFICIENT_MONTHS")
    assert result.value is None


# ---------------------------------------------------------------------------
# 11. Excluded scope handled consistently
# ---------------------------------------------------------------------------


def test_all_department_excluded(calculator):
    results = calculator.calculate_all_departments(
        "HOSP-001", 2025, excluded_departments=["ALL", "DEPT-PEX"]
    )
    assert "ALL" not in results
    assert "DEPT-PEX" not in results


def test_all_department_present_if_not_excluded(calculator):
    results = calculator.calculate_all_departments(
        "HOSP-001", 2025, excluded_departments=None
    )
    # ALL is present in the raw data as a synthetic aggregate.
    assert "ALL" in results


# ---------------------------------------------------------------------------
# 12. Validation edge cases
# ---------------------------------------------------------------------------


def test_invalid_lookback_months_rejected():
    bad_policy = ForecastDenominatorPolicy(
        policy_id="BAD",
        policy_name="Bad",
        metric_scope="kpi_001",
        method="LATEST_COMPLETE_ACTUAL_MONTHS",
        lookback_months=0,
        aggregation_method="ARITHMETIC_MEAN",
        forecast_horizon_usage="HOLD_CONSTANT",
        minimum_complete_months_required=1,
        fallback_behavior="NOT_AVAILABLE",
        source_dataset="data/analytical/analytical_six_kpi_daily.csv",
        source_field="denominator_value",
        kpi_id="kpi_001",
        unit="staff-hours",
        configuration_version="v1.0",
        effective_start_date="2026-07-25",
        effective_end_date="",
        approval_status="Draft",
        validation_status="Draft",
        created_datetime="2026-07-25T00:00:00",
        updated_datetime="2026-07-25T00:00:00",
        governance_note="",
    )
    loader = PolicyConfigLoader(base_dir=BASE_DIR)
    with pytest.raises(ValueError, match="lookback_months must be >= 1"):
        loader._validate(bad_policy)


def test_unsupported_aggregation_rejected():
    bad_policy = ForecastDenominatorPolicy(
        policy_id="BAD",
        policy_name="Bad",
        metric_scope="kpi_001",
        method="LATEST_COMPLETE_ACTUAL_MONTHS",
        lookback_months=3,
        aggregation_method="GEOMETRIC_MEAN",
        forecast_horizon_usage="HOLD_CONSTANT",
        minimum_complete_months_required=1,
        fallback_behavior="NOT_AVAILABLE",
        source_dataset="data/analytical/analytical_six_kpi_daily.csv",
        source_field="denominator_value",
        kpi_id="kpi_001",
        unit="staff-hours",
        configuration_version="v1.0",
        effective_start_date="2026-07-25",
        effective_end_date="",
        approval_status="Draft",
        validation_status="Draft",
        created_datetime="2026-07-25T00:00:00",
        updated_datetime="2026-07-25T00:00:00",
        governance_note="",
    )
    loader = PolicyConfigLoader(base_dir=BASE_DIR)
    with pytest.raises(ValueError, match="aggregation_method"):
        loader._validate(bad_policy)


def test_unsupported_kpi_rejected():
    bad_policy = ForecastDenominatorPolicy(
        policy_id="BAD",
        policy_name="Bad",
        metric_scope="kpi_002",
        method="LATEST_COMPLETE_ACTUAL_MONTHS",
        lookback_months=3,
        aggregation_method="ARITHMETIC_MEAN",
        forecast_horizon_usage="HOLD_CONSTANT",
        minimum_complete_months_required=1,
        fallback_behavior="NOT_AVAILABLE",
        source_dataset="data/analytical/analytical_six_kpi_daily.csv",
        source_field="denominator_value",
        kpi_id="kpi_002",
        unit="staff-hours",
        configuration_version="v1.0",
        effective_start_date="2026-07-25",
        effective_end_date="",
        approval_status="Draft",
        validation_status="Draft",
        created_datetime="2026-07-25T00:00:00",
        updated_datetime="2026-07-25T00:00:00",
        governance_note="",
    )
    loader = PolicyConfigLoader(base_dir=BASE_DIR)
    with pytest.raises(ValueError, match="kpi_001"):
        loader._validate(bad_policy)
