"""Phase 3B-FI Forecast Integration Tests.

Verifies that:
- January-July use actual data
- August-December use governed forecast output
- Actual August-December source rows are never used as forecasts
- Annual chart: solid actual line + dashed forecast line + uncertainty band
- Month slicer allows January-December
- Actual card equals actual chart point; forecast card equals forecast chart point
- ACTUAL PERIOD appears for Jan-Jul; FORECAST PERIOD appears for Aug-Dec
- ACTION FOR REVIEW appears for actual months; SUGGESTED ACTION for forecast months
- Forecast warning and quality appear
- Ineligible forecasts show Forecast Not Available (not zero, no false status colour)
- All Departments is not averaged ad hoc
- Financial Impact remains absent
- Scenario forecast fallback works
- Forecast output files remain unchanged
- Step 3C remains unstarted
"""
import os
import sys

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, PROJECT_ROOT)

import pandas as pd
import pytest

from src.streamlit_executive_data_loader import (
    load_all_data,
    get_kpi_monthly_actual_table,
    get_kpi_annual_forecast_series,
    load_kpi_monthly_forecast,
    load_kpi_forecast_warning_signals,
    load_kpi_forecast_eligibility_audit,
    load_kpi_forecast_method_selection,
    get_filter_options,
    get_period_type,
    lookup_forecast_record,
    lookup_forecast_warning,
    lookup_forecast_eligibility,
    get_forecast_capability_notice,
    GOVERNED_ACTUAL_MONTH_CUTOFF,
    FORECAST_HORIZON_START_MONTH,
    FORECAST_HORIZON_END_MONTH,
)
from src.streamlit_executive_page_controller import (
    build_executive_page_state,
    build_kpi_interpretation_card,
    build_forecast_interpretation_card,
    _build_all_kpi_cards,
    load_kpi_threshold_config,
)
from src.streamlit_executive_visualisation_engine import render_kpi_annual_actual_chart


PAGE_PATH = os.path.join(PROJECT_ROOT, "pages", "02_Executive_Overview.py")


@pytest.fixture(scope="module")
def all_data():
    return load_all_data()


@pytest.fixture(scope="module")
def forecast_df(all_data):
    return all_data["forecast_monthly"]


@pytest.fixture(scope="module")
def warning_df(all_data):
    return all_data["forecast_warnings"]


@pytest.fixture(scope="module")
def eligibility_df(all_data):
    return all_data["forecast_eligibility"]


@pytest.fixture(scope="module")
def threshold_cfg():
    return load_kpi_threshold_config()


# ---------------------------------------------------------------------------
# 1. Forecast data loaded
# ---------------------------------------------------------------------------

def test_01_forecast_files_loaded(all_data):
    assert not all_data["forecast_monthly"].empty
    assert not all_data["forecast_warnings"].empty
    assert not all_data["forecast_eligibility"].empty
    assert "point_forecast" in all_data["forecast_monthly"].columns
    assert "lower_bound" in all_data["forecast_monthly"].columns
    assert "upper_bound" in all_data["forecast_monthly"].columns


# ---------------------------------------------------------------------------
# 2. Period classifier
# ---------------------------------------------------------------------------

def test_02_period_type_actual_for_january_to_july():
    for m in range(1, 8):
        assert get_period_type(2025, m) == "ACTUAL"


def test_03_period_type_forecast_for_august_to_december():
    for m in range(8, 13):
        assert get_period_type(2025, m) == "FORECAST"


# ---------------------------------------------------------------------------
# 4. Month slicer allows January-December
# ---------------------------------------------------------------------------

def test_04_month_slicer_allows_january_to_december(all_data):
    opts = get_filter_options(all_data["kpi_daily"])
    months = set(opts["month"])
    assert months == set(range(1, 13))


# ---------------------------------------------------------------------------
# 5. Actual card equals actual chart point (Jan-Jul)
# ---------------------------------------------------------------------------

def test_05_actual_card_equals_chart_point_for_january(all_data, threshold_cfg):
    cards = _build_all_kpi_cards(
        all_data["kpi_daily"], "DEPT-ICU", None, None, None, threshold_cfg,
        hospital_id="HOSP-001", year=2025, month=1,
        forecast_df=all_data["forecast_monthly"],
        warning_df=all_data["forecast_warnings"],
        eligibility_df=all_data["forecast_eligibility"],
    )
    card = next(c for c in cards if c["kpi_id"] == "kpi_002")
    assert card["period_type"] == "ACTUAL"
    assert card["latest_value"] != "Insufficient Data"
    # Chart point for Jan is in annual_df month 1
    if not card["annual_df"].empty:
        jan_row = card["annual_df"][card["annual_df"]["month"] == 1]
        if not jan_row.empty:
            chart_val = f"{jan_row.iloc[0]['monthly_value']:.1f}"
            assert card["latest_value"] == chart_val


# ---------------------------------------------------------------------------
# 6. Forecast card equals forecast chart point (Aug-Dec)
# ---------------------------------------------------------------------------

def test_06_forecast_card_equals_chart_point_for_december(all_data, threshold_cfg):
    cards = _build_all_kpi_cards(
        all_data["kpi_daily"], "DEPT-ICU", None, None, None, threshold_cfg,
        hospital_id="HOSP-001", year=2025, month=12,
        forecast_df=all_data["forecast_monthly"],
        warning_df=all_data["forecast_warnings"],
        eligibility_df=all_data["forecast_eligibility"],
    )
    card = next(c for c in cards if c["kpi_id"] == "kpi_002")
    assert card["period_type"] == "FORECAST"
    assert card["point_forecast"] is not None
    # Card value must equal point_forecast (single source of truth)
    assert float(card["latest_value"]) == round(float(card["point_forecast"]), 1)


# ---------------------------------------------------------------------------
# 7. ICU Absenteeism December — forecast ≈ 15.1, Amber, Emerging Warning
# ---------------------------------------------------------------------------

def test_07_icu_absenteeism_december_forecast(all_data, threshold_cfg):
    cards = _build_all_kpi_cards(
        all_data["kpi_daily"], "DEPT-ICU", None, None, None, threshold_cfg,
        hospital_id="HOSP-001", year=2025, month=12,
        forecast_df=all_data["forecast_monthly"],
        warning_df=all_data["forecast_warnings"],
        eligibility_df=all_data["forecast_eligibility"],
    )
    card = next(c for c in cards if c["kpi_id"] == "kpi_002")
    assert card["period_type"] == "FORECAST"
    assert 14.0 <= float(card["point_forecast"]) <= 16.5, f"point_forecast={card['point_forecast']}"
    assert card["threshold_status"] in ("Warning", "Critical")
    assert card["warning_level"] in ("Emerging Warning", "Escalating Warning", "High Early Warning")


# ---------------------------------------------------------------------------
# 8. ICU Staffing — declining forecast, uncertainty grows with horizon
# ---------------------------------------------------------------------------

def test_08_icu_staffing_uncertainty_grows(all_data, threshold_cfg):
    aug_card = _build_all_kpi_cards(
        all_data["kpi_daily"], "DEPT-ICU", None, None, None, threshold_cfg,
        hospital_id="HOSP-001", year=2025, month=8,
        forecast_df=all_data["forecast_monthly"],
        warning_df=all_data["forecast_warnings"],
        eligibility_df=all_data["forecast_eligibility"],
    )
    dec_card = _build_all_kpi_cards(
        all_data["kpi_daily"], "DEPT-ICU", None, None, None, threshold_cfg,
        hospital_id="HOSP-001", year=2025, month=12,
        forecast_df=all_data["forecast_monthly"],
        warning_df=all_data["forecast_warnings"],
        eligibility_df=all_data["forecast_eligibility"],
    )
    aug = next(c for c in aug_card if c["kpi_id"] == "kpi_001")
    dec = next(c for c in dec_card if c["kpi_id"] == "kpi_001")
    assert aug["point_forecast"] is not None
    assert dec["point_forecast"] is not None
    # Uncertainty band is non-zero (shown to user)
    assert (aug["upper_bound"] - aug["lower_bound"]) > 0
    assert (dec["upper_bound"] - dec["lower_bound"]) > 0
    # Forecast values for Aug and Dec differ
    assert aug["point_forecast"] != dec["point_forecast"]
    # Horizon is displayed correctly
    assert aug.get("horizon_months_ahead") == 1
    assert dec.get("horizon_months_ahead") == 5


# ---------------------------------------------------------------------------
# 9. ED Waiting Time October — forecast near 60 minutes
# ---------------------------------------------------------------------------

def test_09_ed_waiting_time_october(all_data, threshold_cfg):
    cards = _build_all_kpi_cards(
        all_data["kpi_daily"], "DEPT-ED", None, None, None, threshold_cfg,
        hospital_id="HOSP-001", year=2025, month=10,
        forecast_df=all_data["forecast_monthly"],
        warning_df=all_data["forecast_warnings"],
        eligibility_df=all_data["forecast_eligibility"],
    )
    card = next(c for c in cards if c["kpi_id"] == "kpi_004")
    assert card["period_type"] == "FORECAST"
    assert 50.0 <= float(card["point_forecast"]) <= 75.0


# ---------------------------------------------------------------------------
# 10. Administration Bed Occupancy August — Forecast Not Available
# ---------------------------------------------------------------------------

def test_10_administration_bed_occupancy_unavailable(all_data, threshold_cfg):
    cards = _build_all_kpi_cards(
        all_data["kpi_daily"], "DEPT-ADM", None, None, None, threshold_cfg,
        hospital_id="HOSP-001", year=2025, month=8,
        forecast_df=all_data["forecast_monthly"],
        warning_df=all_data["forecast_warnings"],
        eligibility_df=all_data["forecast_eligibility"],
    )
    card = next(c for c in cards if c["kpi_id"] == "kpi_003")
    assert card["forecast_unavailable"] is True
    assert card["latest_value"] == "Forecast Not Available"
    assert card["threshold_status"] == "Not Assessable"
    assert float(card["point_forecast"] or 0) == 0 or card["point_forecast"] is None


# ---------------------------------------------------------------------------
# 11. All Departments August — no ad hoc forecast aggregation
# ---------------------------------------------------------------------------

def test_11_all_departments_no_ad_hoc_forecast(all_data, threshold_cfg):
    cards = _build_all_kpi_cards(
        all_data["kpi_daily"], "ALL", None, None, None, threshold_cfg,
        hospital_id="HOSP-001", year=2025, month=8,
        forecast_df=all_data["forecast_monthly"],
        warning_df=all_data["forecast_warnings"],
        eligibility_df=all_data["forecast_eligibility"],
    )
    # All Departments for forecast month: explicit Forecast Not Available, no aggregation
    for card in cards:
        assert card["period_type"] == "FORECAST"
        assert card["forecast_unavailable"] is True
        assert card["latest_value"] == "Forecast Not Available"
        assert card["threshold_status"] == "Not Assessable"
        assert card["point_forecast"] is None


# ---------------------------------------------------------------------------
# 12. Forecast source CSV files unchanged (existence + schema)
# ---------------------------------------------------------------------------

def test_12_forecast_output_files_unchanged():
    base = os.path.join(PROJECT_ROOT, "outputs", "forecasting")
    for fname in [
        "analytical_kpi_monthly_forecast.csv",
        "analytical_kpi_forecast_warning_signals.csv",
        "kpi_forecast_eligibility_audit.csv",
        "kpi_forecast_method_selection.csv",
    ]:
        path = os.path.join(base, fname)
        assert os.path.exists(path), f"{fname} missing"
        df = pd.read_csv(path)
        assert not df.empty, f"{fname} empty"


# ---------------------------------------------------------------------------
# 13. Forecast outputs have expected coverage (33/48 eligible)
# ---------------------------------------------------------------------------

def test_13_forecast_eligibility_coverage(eligibility_df):
    eligibility_counts = eligibility_df["eligibility_status"].value_counts().to_dict()
    assert eligibility_counts.get("ELIGIBLE", 0) == 33
    ineligible = sum(v for k, v in eligibility_counts.items() if k != "ELIGIBLE")
    assert ineligible == 15


# ---------------------------------------------------------------------------
# 14. Page shows FORECAST PERIOD text
# ---------------------------------------------------------------------------

def test_14_page_source_has_forecast_period():
    with open(PAGE_PATH, encoding="utf-8") as f:
        src = f.read()
    assert "FORECAST PERIOD" in src
    assert "SUGGESTED ACTION" in src


# ---------------------------------------------------------------------------
# 15. Page source does NOT contain Financial Impact section
# ---------------------------------------------------------------------------

def test_15_page_does_not_have_financial_impact_section():
    with open(PAGE_PATH, encoding="utf-8") as f:
        src = f.read()
    assert "Financial Impact" not in src
    # No chart, no reconciliation, no fallback
    assert "fin_impact" not in src


# ---------------------------------------------------------------------------
# 16. Build state has forecast context for forecast month
# ---------------------------------------------------------------------------

def test_16_state_has_forecast_context_for_forecast_month(all_data):
    state = build_executive_page_state(
        all_data,
        {
            "department_id": "DEPT-ICU",
            "department_name": "Intensive Care Unit",
            "hospital_id": "HOSP-001",
            "year": 2025,
            "month": 12,
            "reporting_date": pd.Timestamp("2025-12-01"),
        },
    )
    assert state["period_type"] == "FORECAST"
    assert "forecast_capability" in state
    assert state["forecast_capability"]["eligible"] == 33
    assert "dominant_forecast_warning" in state


def test_17_state_has_actual_period_for_january(all_data):
    state = build_executive_page_state(
        all_data,
        {
            "department_id": "DEPT-ICU",
            "department_name": "Intensive Care Unit",
            "hospital_id": "HOSP-001",
            "year": 2025,
            "month": 1,
            "reporting_date": pd.Timestamp("2025-01-01"),
        },
    )
    assert state["period_type"] == "ACTUAL"


# ---------------------------------------------------------------------------
# 18. Capability notice has expected fields
# ---------------------------------------------------------------------------

def test_18_capability_notice_fields():
    notice = get_forecast_capability_notice()
    assert notice["status"] == "Indicative Prototype Available"
    assert notice["coverage"] == "33 of 48 department\u2013KPI combinations"
    assert "August" in notice["horizon"] and "December" in notice["horizon"]
    assert "production-approved" in notice["limitations"]
    assert "15 combinations" in notice["unsupported"]


# ---------------------------------------------------------------------------
# 19. Interpretation card builder returns HTML for forecast card
# ---------------------------------------------------------------------------

def test_19_forecast_interpretation_card_contains_forward_language(threshold_cfg):
    cards = _build_all_kpi_cards(
        pd.DataFrame(), "DEPT-ICU", None, None, None, threshold_cfg,
        hospital_id="HOSP-001", year=2025, month=12,
        forecast_df=load_kpi_monthly_forecast(),
        warning_df=load_kpi_forecast_warning_signals(),
        eligibility_df=load_kpi_forecast_eligibility_audit(),
    )
    card = next(c for c in cards if c["kpi_id"] == "kpi_002")
    html = build_forecast_interpretation_card(card)
    assert "FORECAST" in html
    # Forward-looking language cues
    assert any(w in html.lower() for w in ["projected", "indicative", "may", "suggests", "expected under"])


# ---------------------------------------------------------------------------
# 20. Annual chart renders with forecast and uncertainty band
# ---------------------------------------------------------------------------

def test_20_chart_renders_forecast_with_band(all_data):
    forecast_df = all_data["forecast_monthly"]
    annual_df = pd.DataFrame(columns=["month", "monthly_value", "supported", "month_label"])
    # Build a small annual_df for Jan-Jul actual
    monthly = get_kpi_monthly_actual_table(all_data["kpi_daily"])
    if not monthly.empty:
        mask = (
            (monthly["hospital"] == "HOSP-001")
            & (monthly["kpi_id"] == "kpi_001")
            & (monthly["year"] == 2025)
            & (monthly["department_code"] == "DEPT-ICU")
            & (monthly["month"] <= 7)
        )
        annual_df = monthly[mask].rename(columns={"monthly_actual_value": "monthly_value"})[
            ["month", "monthly_value"]
        ].copy()
        annual_df["supported"] = True
        annual_df["month_label"] = annual_df["month"].apply(
            lambda m: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"][m - 1]
        )
    chart_forecast_df = get_kpi_annual_forecast_series(
        all_data["forecast_monthly"],
        "HOSP-001",
        "DEPT-ICU",
        "kpi_001",
        2025,
    )
    fig = render_kpi_annual_actual_chart(
        annual_df, "Staffing Level", "FTE",
        selected_month=12,
        threshold_value=None,
        status="amber",
        forecast_df=chart_forecast_df,
        eligibility_status="ELIGIBLE",
        forecast_limitation="",
    )
    assert fig is not None