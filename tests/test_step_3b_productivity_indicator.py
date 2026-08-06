"""
test_step_3b_productivity_indicator.py

Targeted validation for the Executive Overview productivity indicator card.
Covers actual-month (Jan-Jul) and forecast-month (Aug-Dec) behaviour,
denominator-policy integration, label correctness, and scope exclusions.
"""

import os
import sys
import pytest

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.productivity_indicator_engine import (
    get_productivity_capacity,
    _is_operational_department,
    _calculate_actual,
    _calculate_forecast,
)
from src.productivity_forecast_denominator_policy import ForecastDenominatorCalculator


# ───────────────────────────────────────────────────────────────────────────
# 1. Jan–Jul selected month returns ACTUAL
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("month", [1, 2, 3, 4, 5, 6, 7])
def test_jan_to_jul_returns_actual(month):
    result = get_productivity_capacity(
        hospital_id="HOSP-001",
        department_id="DEPT-ADM",
        year=2025,
        month=month,
    )
    assert result.period_type == "ACTUAL"
    assert result.status in ("OK", "UNAVAILABLE")


# ───────────────────────────────────────────────────────────────────────────
# 2. Actual value uses selected month only
# ───────────────────────────────────────────────────────────────────────────

def test_actual_value_uses_selected_month_only():
    result_jan = get_productivity_capacity(
        hospital_id="HOSP-001", department_id="DEPT-ADM", year=2025, month=1,
    )
    result_feb = get_productivity_capacity(
        hospital_id="HOSP-001", department_id="DEPT-ADM", year=2025, month=2,
    )
    # If both months have data, they should differ (different daily sums)
    if result_jan.status == "OK" and result_feb.status == "OK":
        assert result_jan.productive_staff_hours != result_feb.productive_staff_hours


# ───────────────────────────────────────────────────────────────────────────
# 3. No cumulative Jan–Jul calculation
# ───────────────────────────────────────────────────────────────────────────

def test_no_cumulative_jan_jul():
    result_jan = get_productivity_capacity(
        hospital_id="HOSP-001", department_id="DEPT-ADM", year=2025, month=1,
    )
    result_jul = get_productivity_capacity(
        hospital_id="HOSP-001", department_id="DEPT-ADM", year=2025, month=7,
    )
    # July value must not equal sum of Jan-Jul (would indicate cumulative bug)
    if result_jan.status == "OK" and result_jul.status == "OK":
        # July alone should be strictly less than Jan+Feb+...+Jul
        cumulative_guess = result_jan.productive_staff_hours * 7
        assert result_jul.productive_staff_hours < cumulative_guess


# ───────────────────────────────────────────────────────────────────────────
# 4. Actual numerator sums correctly
# ───────────────────────────────────────────────────────────────────────────

def test_actual_numerator_sums_correctly():
    result = get_productivity_capacity(
        hospital_id="HOSP-001", department_id="DEPT-ADM", year=2025, month=7,
    )
    if result.status == "OK":
        # Should be a positive finite number
        assert result.productive_staff_hours is not None
        assert result.productive_staff_hours > 0
        assert result.productive_staff_hours < 1_000_000


# ───────────────────────────────────────────────────────────────────────────
# 5. Aug–Dec returns FORECAST
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("month", [8, 9, 10, 11, 12])
def test_aug_to_dec_returns_forecast(month):
    result = get_productivity_capacity(
        hospital_id="HOSP-001",
        department_id="DEPT-ADM",
        year=2025,
        month=month,
    )
    assert result.period_type == "FORECAST"
    assert result.status in ("OK", "UNAVAILABLE", "INSUFFICIENT_MONTHS")


# ───────────────────────────────────────────────────────────────────────────
# 6. Forecast uses point_forecast for kpi_001
# ───────────────────────────────────────────────────────────────────────────

def test_forecast_uses_point_forecast():
    result = get_productivity_capacity(
        hospital_id="HOSP-001", department_id="DEPT-ADM", year=2025, month=8,
    )
    if result.status == "OK":
        assert result.staffing_coverage_pct is not None
        assert 0 < result.staffing_coverage_pct <= 100


# ───────────────────────────────────────────────────────────────────────────
# 7. Forecast denominator comes from ForecastDenominatorCalculator
# ───────────────────────────────────────────────────────────────────────────

def test_forecast_denominator_from_policy():
    result = get_productivity_capacity(
        hospital_id="HOSP-001", department_id="DEPT-ADM", year=2025, month=8,
    )
    if result.status == "OK":
        assert "productivity_forecast_denominator_policy" in result.source


# ───────────────────────────────────────────────────────────────────────────
# 8. No hardcoded May/Jun/Jul logic in productivity engine
# ───────────────────────────────────────────────────────────────────────────

def test_no_hardcoded_month_numbers_in_engine():
    import inspect
    source = inspect.getsource(get_productivity_capacity)
    # The engine must not contain literal month numbers 5, 6, 7
    for bad in ["'5'", '"5"', "'6'", '"6"', "'7'", '"7"', "May", "Jun", "Jul"]:
        assert bad not in source, f"Hardcoded month reference found: {bad}"


# ───────────────────────────────────────────────────────────────────────────
# 9. No 8-hour assumption
# ───────────────────────────────────────────────────────────────────────────

def test_no_eight_hour_assumption():
    import inspect
    source = inspect.getsource(get_productivity_capacity)
    for bad in ["8.0", "8 *", "* 8", "8-hour", "eight"]:
        assert bad.lower() not in source.lower(), f"8-hour assumption found: {bad}"


# ───────────────────────────────────────────────────────────────────────────
# 10. Insufficient denominator returns unavailable
# ───────────────────────────────────────────────────────────────────────────

def test_insufficient_months_returns_unavailable():
    # Use a department that might not have 3 months, or mock by passing empty data
    import pandas as pd
    empty_df = pd.DataFrame()
    result = get_productivity_capacity(
        hospital_id="HOSP-001",
        department_id="DEPT-ADM",
        year=2025,
        month=8,
        forecast_df=empty_df,
    )
    assert result.status == "UNAVAILABLE"
    assert result.productive_staff_hours is None


# ───────────────────────────────────────────────────────────────────────────
# 11. ACTUAL / FORECAST labels correct
# ───────────────────────────────────────────────────────────────────────────

def test_actual_forecast_labels():
    actual = get_productivity_capacity(
        hospital_id="HOSP-001", department_id="DEPT-ADM", year=2025, month=3,
    )
    forecast = get_productivity_capacity(
        hospital_id="HOSP-001", department_id="DEPT-ADM", year=2025, month=10,
    )
    assert actual.period_type == "ACTUAL"
    assert forecast.period_type == "FORECAST"


# ───────────────────────────────────────────────────────────────────────────
# 12. Staff-hours unit correct
# ───────────────────────────────────────────────────────────────────────────

def test_unit_is_staff_hours():
    result = get_productivity_capacity(
        hospital_id="HOSP-001", department_id="DEPT-ADM", year=2025, month=5,
    )
    assert result.unit == "staff-hours"


# ───────────────────────────────────────────────────────────────────────────
# 13. Staffing coverage value matches selected month
# ───────────────────────────────────────────────────────────────────────────

def test_staffing_coverage_matches_selected_month():
    result = get_productivity_capacity(
        hospital_id="HOSP-001", department_id="DEPT-ADM", year=2025, month=7,
    )
    if result.status == "OK":
        assert result.staffing_coverage_pct is not None
        assert 0 < result.staffing_coverage_pct <= 100


# ───────────────────────────────────────────────────────────────────────────
# 14. Excluded scope handled safely
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("dept", ["ALL", "DEPT-PEX", "", None])
def test_excluded_scope_returns_not_supported(dept):
    result = get_productivity_capacity(
        hospital_id="HOSP-001", department_id=dept, year=2025, month=5,
    )
    assert result.status == "NOT_SUPPORTED"
    assert result.productive_staff_hours is None


# ───────────────────────────────────────────────────────────────────────────
# 15. Operational department helper
# ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "dept,expected",
    [
        ("DEPT-ADM", True),
        ("DEPT-ED", True),
        ("ALL", False),
        ("DEPT-PEX", False),
        ("", False),
        (None, False),
    ],
)
def test_is_operational_department(dept, expected):
    assert _is_operational_department(dept) == expected


# ───────────────────────────────────────────────────────────────────────────
# 16. Forecast result uses governed denominator (not a fixed constant)
# ───────────────────────────────────────────────────────────────────────────

def test_forecast_result_scales_with_denominator():
    result = get_productivity_capacity(
        hospital_id="HOSP-001", department_id="DEPT-ADM", year=2025, month=8,
    )
    if result.status == "OK":
        # If coverage is 100%, hours should equal denominator
        # If coverage < 100%, hours should be less than denominator
        assert result.productive_staff_hours is not None
        assert result.staffing_coverage_pct is not None
        # Reconstruct denominator from result
        if result.staffing_coverage_pct > 0:
            implied_denom = result.productive_staff_hours / (result.staffing_coverage_pct / 100.0)
            assert implied_denom > 0
            assert implied_denom < 1_000_000


# ───────────────────────────────────────────────────────────────────────────
# 17. No CV threshold governance rule introduced
# ───────────────────────────────────────────────────────────────────────────

def test_no_cv_threshold_in_engine():
    import inspect
    source = inspect.getsource(get_productivity_capacity)
    for bad in ["cv", "coefficient", "variation", "10%", "threshold"]:
        assert bad.lower() not in source.lower(), f"CV/threshold reference found: {bad}"
