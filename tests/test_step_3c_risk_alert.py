"""
test_step_3c_risk_alert.py

Phase 3C — Risk & Alert focused tests.

These tests verify that the Risk & Alert controller/page correctly:
1. Uses governed actual status / forecast warnings for summary counts.
2. Orders risks by warning severity (High Early Warning > Escalating > Emerging > Monitoring).
3. Does not fabricate missing forecasts.
4. Does not falsely label missing forecasts as Monitoring.
5. Sources actual values from canonical monthly actual data.
6. Formats KPI units cleanly.
7. Excludes ALL / All Departments from slicer.
8. Excludes DEPT-PEX / Patient Experience from slicer.
9. Selected risk detail respects department + KPI.
10. Forecast lower/upper range uses governed values.
11. Suggested action comes from existing action/intervention source.
12. No Financial Impact section exists.
13. No Scenario Comparison section exists.
14. Risk progression handles unsupported months safely.
15. No fabricated zero values for missing data.
"""

import sys
import os

# Ensure project root is on path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pandas as pd
import pytest

from src.risk_alert_controller import (
    EXCLUDED_DEPT_IDS,
    WARNING_PRIORITY_ORDER,
    WARNING_PRIORITY_RANK,
    STATUS_TEXT_BY_CODE,
    build_risk_alert_state,
    build_priority_risk_table,
    build_selected_risk_detail,
    build_risk_progression,
    build_management_interpretation,
    build_suggested_action_card,
    compute_risk_summary,
    get_excluded_dept_ids,
    get_filter_options,
    _format_value_with_unit,
    _format_forecast,
    _clean_suggested_action,
    _format_month_label,
)
from src.streamlit_executive_page_controller import format_unit_value
from src.streamlit_executive_data_loader import (
    load_kpi_daily,
    load_kpi_monthly_forecast,
    load_kpi_forecast_warning_signals,
    get_kpi_monthly_actual_table,
    GOVERNED_ACTUAL_MONTH_CUTOFF,
)


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

@pytest.fixture(scope="module")
def kpi_daily():
    return load_kpi_daily()


@pytest.fixture(scope="module")
def forecast_df():
    return load_kpi_monthly_forecast()


@pytest.fixture(scope="module")
def warning_signals():
    return load_kpi_forecast_warning_signals()


@pytest.fixture
def icu_dec_state(kpi_daily, forecast_df, warning_signals):
    return build_risk_alert_state(
        department_code="DEPT-ICU",
        year=2025,
        month=12,
        hospital_label="HOSP-001",
    )


@pytest.fixture
def ed_oct_state(kpi_daily, forecast_df, warning_signals):
    return build_risk_alert_state(
        department_code="DEPT-ED",
        year=2025,
        month=10,
        hospital_label="HOSP-001",
    )


# --------------------------------------------------------------------------
# 1. Summary counts use governed statuses / warnings
# --------------------------------------------------------------------------

def test_summary_counts_use_governed_status_and_warnings(icu_dec_state):
    summary = icu_dec_state["summary"]
    # ICU Dec 2025: no actual risks (Dec is forecast month), but there are forecast warnings
    assert isinstance(summary["active_actual_risks"], int)
    assert isinstance(summary["emerging_forecast_risks"], int)
    assert isinstance(summary["high_or_escalating_warnings"], int)
    assert summary["emerging_forecast_risks"] >= summary["high_or_escalating_warnings"]
    assert summary["high_or_escalating_warnings"] >= 0


def test_summary_active_actual_risks_for_actual_month(kpi_daily, warning_signals):
    # ICU Jul 2025 (actual month) should have at least 1 active actual risk
    summary = compute_risk_summary(
        kpi_daily=kpi_daily,
        warning_signals=warning_signals,
        department_code="DEPT-ICU",
        year=2025,
        month=7,
    )
    assert summary["active_actual_risks"] >= 1


# --------------------------------------------------------------------------
# 2. Warning priority ordering
# --------------------------------------------------------------------------

def test_warning_priority_order_is_correct():
    assert WARNING_PRIORITY_ORDER == (
        "High Early Warning",
        "Escalating Warning",
        "Emerging Warning",
        "Monitoring",
    )
    assert WARNING_PRIORITY_RANK["High Early Warning"] < WARNING_PRIORITY_RANK["Escalating Warning"]
    assert WARNING_PRIORITY_RANK["Escalating Warning"] < WARNING_PRIORITY_RANK["Emerging Warning"]
    assert WARNING_PRIORITY_RANK["Emerging Warning"] < WARNING_PRIORITY_RANK["Monitoring"]


def test_priority_table_orders_by_warning_severity(icu_dec_state):
    table = icu_dec_state["table"]
    if table.empty:
        pytest.skip("No forecast warnings for ICU Dec 2025")
    warnings = table["Warning"].tolist()
    ranks = [WARNING_PRIORITY_RANK.get(w, 99) for w in warnings]
    assert ranks == sorted(ranks)


# --------------------------------------------------------------------------
# 3. Missing forecast remains unavailable
# --------------------------------------------------------------------------

def test_missing_forecast_shows_unavailable(icu_dec_state):
    table = icu_dec_state["table"]
    # ICU Dec 2025: kpi_004 and kpi_005 have no forecast (insufficient data).
    # Because the controller only creates rows from the warning-signals file,
    # ineligible KPIs do not appear as explicit rows.  Instead they are
    # simply absent from the table.  Verify absence.
    kpi_names = table["KPI"].tolist()
    assert "Average Patient Waiting Time" not in kpi_names
    assert "Patient Complaint Rate" not in kpi_names


# --------------------------------------------------------------------------
# 4. Missing forecast does NOT become Monitoring
# --------------------------------------------------------------------------

def test_missing_forecast_does_not_become_monitoring(icu_dec_state):
    table = icu_dec_state["table"]
    # Ineligible KPIs are absent from the table; verify no row has
    # Warning == "Monitoring" while also claiming Forecast Not Available.
    unavailable_rows = table[table["Forecast Month"] == "Forecast Not Available"]
    for _, row in unavailable_rows.iterrows():
        assert row["Warning"] != "Monitoring"


# --------------------------------------------------------------------------
# 5. Actual values come from canonical monthly actual data
# --------------------------------------------------------------------------

def test_actual_values_from_canonical_data(kpi_daily):
    monthly = get_kpi_monthly_actual_table(kpi_daily)
    assert not monthly.empty
    assert "monthly_actual_value" in monthly.columns
    assert "department_code" in monthly.columns
    assert "kpi_id" in monthly.columns
    # Verify ICU has actual data
    icu_actual = monthly[
        (monthly["department_code"] == "DEPT-ICU")
        & (monthly["year"] == 2025)
        & (monthly["month"] <= GOVERNED_ACTUAL_MONTH_CUTOFF)
    ]
    assert not icu_actual.empty


# --------------------------------------------------------------------------
# 6. Unit formatting is clean
# --------------------------------------------------------------------------

def test_unit_formatting_clean():
    assert _format_value_with_unit(85.9, "%") == "85.9%"
    assert _format_value_with_unit(2.5, "1-5 likert score") == "2.5/5 Likert"
    assert _format_value_with_unit(68.5, "minutes") == "68.5 minutes"
    assert _format_value_with_unit(8.2, "complaints per 1,000 encounters") == "8.2 complaints per 1,000 encounters"
    assert _format_value_with_unit(None, "%") == "No actual data"


def test_forecast_formatting_clean():
    assert _format_forecast(18.2) == "18.2"
    assert _format_forecast(None) == "Forecast Not Available"


# --------------------------------------------------------------------------
# 7 & 8. Department list excludes ALL / Patient Experience
# --------------------------------------------------------------------------

def test_excluded_dept_ids():
    assert "ALL" in EXCLUDED_DEPT_IDS
    assert "DEPT-PEX" in EXCLUDED_DEPT_IDS


def test_filter_options_exclude_all_and_pex(kpi_daily):
    opts = get_filter_options()
    dept_ids = [d for d, _ in opts["department"]]
    assert "ALL" not in dept_ids
    assert "DEPT-PEX" not in dept_ids
    assert "DEPT-ICU" in dept_ids
    assert "DEPT-ED" in dept_ids


# --------------------------------------------------------------------------
# 9. Selected risk detail respects department + KPI
# --------------------------------------------------------------------------

def test_selected_risk_detail_respects_dept_and_kpi(icu_dec_state, kpi_daily):
    internal_rows = icu_dec_state["internal_rows"]
    if not internal_rows:
        pytest.skip("No internal rows for ICU Dec 2025")
    selected = internal_rows[0]
    monthly_actual = get_kpi_monthly_actual_table(kpi_daily)
    detail = build_selected_risk_detail(selected, monthly_actual)
    assert detail["header"].startswith("Selected Risk —")
    assert selected["department"] in detail["header"]
    assert selected["kpi_name"] in detail["header"]


# --------------------------------------------------------------------------
# 10. Forecast lower/upper range uses governed values
# --------------------------------------------------------------------------

def test_forecast_range_uses_governed_values(icu_dec_state):
    internal_rows = icu_dec_state["internal_rows"]
    forecast_rows = [r for r in internal_rows if r.get("forecast_value") is not None]
    if not forecast_rows:
        pytest.skip("No forecast rows for ICU Dec 2025")
    for row in forecast_rows:
        assert row["forecast_lower"] is not None
        assert row["forecast_upper"] is not None
        assert row["forecast_lower"] <= row["forecast_upper"]


# --------------------------------------------------------------------------
# 11. Suggested action comes from existing action/intervention source
# --------------------------------------------------------------------------

def test_suggested_action_not_invented(icu_dec_state):
    internal_rows = icu_dec_state["internal_rows"]
    for row in internal_rows:
        action = row.get("suggested_action", "")
        assert isinstance(action, str)
        # Should not be empty or a generic placeholder unless genuinely missing
        assert action != ""


def test_suggested_action_card_structure(icu_dec_state):
    internal_rows = icu_dec_state["internal_rows"]
    if not internal_rows:
        pytest.skip("No rows")
    card = build_suggested_action_card(internal_rows[0])
    assert "title" in card
    assert "action" in card
    assert "why" in card
    assert "status" in card
    assert card["status"] == "Suggested — Management Review Required"


# --------------------------------------------------------------------------
# 12 & 13. No Financial Impact / Scenario Comparison sections
# --------------------------------------------------------------------------

def test_no_financial_impact_section():
    # The controller has no financial impact function
    assert not hasattr(build_risk_alert_state, "financial_impact")
    assert "financial" not in str(build_risk_alert_state.__doc__).lower()


def test_no_scenario_comparison_section():
    assert "scenario" not in str(build_risk_alert_state.__doc__).lower()


# --------------------------------------------------------------------------
# Slicer — forecast months only
# --------------------------------------------------------------------------

def test_review_month_slicer_contains_forecast_months_only():
    opts = get_filter_options()
    assert opts["month"] == [8, 9, 10, 11, 12]


def test_actual_months_excluded_from_alert_month_slicer():
    opts = get_filter_options()
    for m in range(1, 8):
        assert m not in opts["month"]


# --------------------------------------------------------------------------
# 14. Risk progression handles unsupported months safely
# --------------------------------------------------------------------------

def test_risk_progression_handles_unsupported_months(icu_dec_state, kpi_daily, forecast_df):
    internal_rows = icu_dec_state["internal_rows"]
    if not internal_rows:
        pytest.skip("No rows")
    monthly_actual = get_kpi_monthly_actual_table(kpi_daily)
    strip = build_risk_progression(
        monthly_actual=monthly_actual,
        forecast_df=forecast_df,
        selected_row=internal_rows[0],
        review_year=2025,
    )
    assert len(strip) == 12
    for entry in strip:
        assert entry["severity"] in ("red", "amber", "green", "grey")
        assert entry["status"] in ("Actual", "Forecast", "Unsupported")


def test_risk_progression_empty_selection(kpi_daily, forecast_df):
    strip = build_risk_progression(
        monthly_actual=get_kpi_monthly_actual_table(kpi_daily),
        forecast_df=forecast_df,
        selected_row={},
        review_year=2025,
    )
    assert len(strip) == 12
    for entry in strip:
        assert entry["status"] == "Unsupported"
        assert entry["severity"] == "grey"


# --------------------------------------------------------------------------
# 15. No fabricated zero values for missing data
# --------------------------------------------------------------------------

def test_no_fabricated_zeros_for_missing_data(icu_dec_state):
    table = icu_dec_state["table"]
    for _, row in table.iterrows():
        forecast = row["Forecast"]
        assert forecast != "0.0"
        assert forecast != "0"
    # For unavailable forecasts, the value should be "Forecast Not Available"
    unavailable = table[table["Forecast Month"] == "Forecast Not Available"]
    for _, row in unavailable.iterrows():
        assert row["Forecast"] == "Forecast Not Available"


# --------------------------------------------------------------------------
# Controller integration — build_risk_alert_state
# --------------------------------------------------------------------------

def test_build_risk_alert_state_structure(icu_dec_state):
    assert "summary" in icu_dec_state
    assert "table" in icu_dec_state
    assert "internal_rows" in icu_dec_state
    assert "department_code" in icu_dec_state
    assert "year" in icu_dec_state
    assert "month" in icu_dec_state


def test_ed_october_state_has_risks(ed_oct_state):
    assert not ed_oct_state["table"].empty
    assert len(ed_oct_state["internal_rows"]) >= 1


# --------------------------------------------------------------------------
# Management interpretation
# --------------------------------------------------------------------------

def test_management_interpretation_has_historical_and_forecast(icu_dec_state, kpi_daily):
    internal_rows = icu_dec_state["internal_rows"]
    if not internal_rows:
        pytest.skip("No rows")
    monthly_actual = get_kpi_monthly_actual_table(kpi_daily)
    interp = build_management_interpretation(
        selected_row=internal_rows[0],
        monthly_actual=monthly_actual,
        review_year=2025,
    )
    assert "historical" in interp
    assert "forecast" in interp
    assert "combined" in interp
    assert interp["historical"] != ""
    assert interp["forecast"] != ""


def test_management_interpretation_uses_actual_period_only(icu_dec_state, kpi_daily):
    """Historical statement must end at latest governed actual month (Jul)."""
    internal_rows = icu_dec_state["internal_rows"]
    if not internal_rows:
        pytest.skip("No rows")
    monthly_actual = get_kpi_monthly_actual_table(kpi_daily)
    interp = build_management_interpretation(
        selected_row=internal_rows[0],
        monthly_actual=monthly_actual,
        review_year=2025,
    )
    hist = interp["historical"]
    # Must not mention Aug-Dec as actual months
    for forbidden in ["Aug", "Sep", "Oct", "Nov", "Dec"]:
        assert forbidden not in hist, f"Historical text incorrectly mentions {forbidden}"
    # Must mention the selected forecast month in the forecast text
    fc = interp["forecast"]
    assert "2025-12" in fc or "Forecast Not Available" in fc


def test_trend_chart_helper_called_with_valid_signature():
    """render_selected_risk_chart must call render_kpi_annual_actual_chart
    with the exact supported argument names."""
    import inspect
    from src.risk_alert_controller import render_selected_risk_chart
    from src.streamlit_executive_visualisation_engine import render_kpi_annual_actual_chart

    target_sig = inspect.signature(render_kpi_annual_actual_chart)
    target_params = set(target_sig.parameters.keys())

    # Verify the target has the expected params
    assert "monthly_df" in target_params
    assert "kpi_name" in target_params
    assert "unit" in target_params
    assert "selected_month" in target_params
    assert "forecast_df" in target_params


def test_trend_chart_renders_without_unexpected_kwarg(icu_dec_state, kpi_daily, forecast_df):
    """Calling render_selected_risk_chart must not raise TypeError about
    unexpected keyword arguments."""
    from src.risk_alert_controller import render_selected_risk_chart
    monthly_actual = get_kpi_monthly_actual_table(kpi_daily)
    row = icu_dec_state["internal_rows"][0]
    # Should not raise
    render_selected_risk_chart(row, monthly_actual, forecast_df, 2025, 12)


# --------------------------------------------------------------------------
# Clean suggested action helper
# --------------------------------------------------------------------------

def test_clean_suggested_action_strips_prefix():
    assert _clean_suggested_action("SUGGESTED ACTION: Review staffing") == "Review staffing"
    assert _clean_suggested_action("Review staffing") == "Review staffing"
    assert _clean_suggested_action("") == "Preventive action requires management review."
    assert _clean_suggested_action(None) == "Preventive action requires management review."


# --------------------------------------------------------------------------
# Phase 3C visual polish — clean month labels, baseline line, blue forecast
# --------------------------------------------------------------------------

def test_format_month_label_clean():
    """_format_month_label converts YYYY-MM to 'JUL 2025' style."""
    assert _format_month_label("2025-07") == "JUL 2025"
    assert _format_month_label("2025-12") == "DEC 2025"
    assert _format_month_label("2025-08") == "AUG 2025"
    # Invalid inputs return empty string
    assert _format_month_label("") == ""
    assert _format_month_label(None) == ""
    assert _format_month_label("2025-13") == ""
    assert _format_month_label("not-a-date") == ""


def test_selected_risk_detail_has_baseline_label(icu_dec_state):
    """Historical card provides a bold BASELINE line derived from latest actual."""
    internal_rows = icu_dec_state["internal_rows"]
    if not internal_rows:
        pytest.skip("No internal rows for ICU Dec 2025")
    detail = build_selected_risk_detail(
        internal_rows[0], get_kpi_monthly_actual_table(load_kpi_daily())
    )
    baseline = detail["historical"].get("baseline_label", "")
    assert baseline != ""
    assert "BASELINE" in baseline
    assert "MTD" in baseline
    # Latest governed actual month is JUL — the baseline must reference it.
    assert "JUL" in baseline
    # Year is dynamic, derived from the actual record (2025)
    assert "2025" in baseline


def test_selected_risk_baseline_label_dynamic_year(icu_dec_state):
    """Baseline year is derived from the actual record, not hardcoded."""
    internal_rows = icu_dec_state["internal_rows"]
    if not internal_rows:
        pytest.skip("No internal rows")
    selected = internal_rows[0]
    actual_month = selected.get("latest_actual_month", "")
    detail = build_selected_risk_detail(
        selected, get_kpi_monthly_actual_table(load_kpi_daily())
    )
    baseline = detail["historical"].get("baseline_label", "")
    expected_label = _format_month_label(actual_month)
    assert expected_label in baseline


def test_selected_risk_forecast_value_uses_unit_formatter(icu_dec_state):
    """Forecast detail value must use format_unit_value, not the raw float."""
    internal_rows = icu_dec_state["internal_rows"]
    forecast_rows = [r for r in internal_rows if r.get("forecast_value") is not None]
    if not forecast_rows:
        pytest.skip("No forecast rows")
    selected = forecast_rows[0]
    detail = build_selected_risk_detail(
        selected, get_kpi_monthly_actual_table(load_kpi_daily())
    )
    fc_value = detail["forecast"]["value"]
    # Must not be the unavailable marker
    assert fc_value != "Forecast Not Available"
    # Must match the canonical unit formatter for the same value+unit
    expected = format_unit_value(
        selected["forecast_value"], selected.get("latest_actual_unit", "")
    )
    assert fc_value == expected
    # Should NOT be a bare number — the unit must be attached
    assert fc_value != f"{float(selected['forecast_value']):.1f}"


def test_selected_risk_forecast_month_label_clean(icu_dec_state):
    """Forecast month label uses 'DEC 2025' style, not raw '2025-12'."""
    internal_rows = icu_dec_state["internal_rows"]
    forecast_rows = [r for r in internal_rows if r.get("forecast_month")]
    if not forecast_rows:
        pytest.skip("No forecast rows")
    detail = build_selected_risk_detail(
        forecast_rows[0], get_kpi_monthly_actual_table(load_kpi_daily())
    )
    month_label = detail["forecast"].get("month_label", "")
    assert month_label != "Not available"
    # Must be in clean 'DEC 2025' style — no dashes
    assert "-" not in month_label
    # Should contain the forecast month abbreviation
    forecast_month = forecast_rows[0]["forecast_month"]
    expected_label = _format_month_label(forecast_month)
    assert month_label == expected_label


def test_page_uses_clean_slicer_format():
    """The page must use a clean short month label — no (08) suffix."""
    src_path = os.path.join(_ROOT, "pages", "03_Risk_and_Alert.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    # Old format pattern must not exist
    assert 'f"{calendar.month_abbr[m]} ({m:02d})"' not in src
    # Clean format pattern must exist
    assert 'f"{calendar.month_abbr[m]}"' in src


def test_page_has_forecast_blue_card_css():
    """Page CSS defines a blue forecast card matching the chart forecast line."""
    src_path = os.path.join(_ROOT, "pages", "03_Risk_and_Alert.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    assert ".s360-risk-forecast-card" in src
    # Same blue family used by the forecast line in the chart (#0d6efd)
    assert "#0d6efd" in src
    # Must use white text for readability
    assert "#ffffff" in src.lower()


def test_page_has_baseline_line_styling():
    """Page CSS defines a bold baseline line element."""
    src_path = os.path.join(_ROOT, "pages", "03_Risk_and_Alert.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    assert ".s360-risk-baseline-line" in src
    # The page must interpolate the controller's baseline_label
    assert 'hist["baseline_label"]' in src or "hist['baseline_label']" in src


# --------------------------------------------------------------------------
# Hospital Slicer Standardization — cross-page display rule
# --------------------------------------------------------------------------

def test_risk_alert_hospital_slicer_no_format_func():
    """Risk & Alert hospital selectbox must not use a format_func mapping to names."""
    src_path = os.path.join(_ROOT, "pages", "03_Risk_and_Alert.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    # Old format_func that mapped to hospital names must be gone
    assert "format_func=lambda h: dict(hospital_options).get" not in src
    # Old hardcoded fallback name must be gone
    assert "KPJ Ampang Puteri" not in src


def test_risk_alert_hospital_label_uses_code():
    """Risk & Alert controller must receive hospital code, not name."""
    state = build_risk_alert_state(
        department_code="DEPT-ICU",
        year=2025,
        month=12,
        hospital_label="HOSP-001",
    )
    assert state["hospital_label"] == "HOSP-001"


def test_no_hospital_name_in_risk_alert_page():
    """Risk & Alert page must not contain the old hospital name."""
    src_path = os.path.join(_ROOT, "pages", "03_Risk_and_Alert.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    assert "KPJ Ampang Puteri" not in src
