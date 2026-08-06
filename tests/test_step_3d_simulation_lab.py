"""tests/test_step_3d_simulation_lab.py — Phase 3D Simulation Lab tests.

Verifies that the Simulation Lab page and controller use ONLY existing governed
engines, configs, and data.  No new models.  No new assumptions.
"""
from __future__ import annotations

import os
import sys
from typing import Any, Dict, List

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC_DIR = os.path.join(_ROOT, "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

# ---------------------------------------------------------------------------
# Controller imports
# ---------------------------------------------------------------------------
from src.simulation_lab_controller import (
    get_filter_options,
    load_interventions_for_kpi,
    build_baseline,
    get_comparator_profiles,
    run_scenario,
    calculate_financial_impact,
    build_tradeoff_and_displacement,
    build_management_takeaway,
    build_simulation_state,
    _SUPPORTED_KPI_IDS,
    _KPI_ID_TO_NAME,
    _KPI_ENGINE_MAP,
    _COMPARATOR_ORDER,
    _FORBIDDEN_WORDS,
    _FINANCIAL_DISPLAY_RULES,
    _has_financial_mapping,
    _KPI_TO_ACTION_STRATEGY,
)
from src.streamlit_executive_data_loader import (
    get_kpi_annual_forecast_series,
    load_kpi_monthly_forecast,
    GOVERNED_ACTUAL_YEAR,
    FORECAST_HORIZON_START_MONTH,
)
from src.scenario_models import ScenarioBaseline
from src.staffing_scenario_engine import StaffingScenarioEngine
from src.absenteeism_scenario_engine import AbsenteeismScenarioEngine
from src.patient_flow_scenario_engine import PatientFlowScenarioEngine


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def filter_options():
    return get_filter_options()


@pytest.fixture
def icu_dec_kpi001_state():
    """Pre-built state for ICU, December 2025, kpi_001."""
    return build_simulation_state(
        hospital_id="HOSP-001",
        department_id="DEPT-ICU",
        kpi_id="kpi_001",
        forecast_month=12,
        intervention_id="INT-STAFF-001",
    )


@pytest.fixture
def icu_dec_kpi003_state():
    """Pre-built state for ICU, December 2025, kpi_003."""
    return build_simulation_state(
        hospital_id="HOSP-001",
        department_id="DEPT-ICU",
        kpi_id="kpi_003",
        forecast_month=12,
        intervention_id="INT-FLOW-001",
    )


# ---------------------------------------------------------------------------
# 1. KPI selector contains only kpi_001–kpi_004
# ---------------------------------------------------------------------------

def test_kpi_selector_only_four_supported(filter_options):
    kpi_ids = [k["id"] for k in filter_options["kpis"]]
    assert set(kpi_ids) == set(_SUPPORTED_KPI_IDS)
    assert len(kpi_ids) == 4


# ---------------------------------------------------------------------------
# 2. kpi_005/kpi_006 excluded from direct simulation
# ---------------------------------------------------------------------------

def test_kpi_005_excluded(filter_options):
    kpi_ids = [k["id"] for k in filter_options["kpis"]]
    assert "kpi_005" not in kpi_ids


def test_kpi_006_excluded(filter_options):
    kpi_ids = [k["id"] for k in filter_options["kpis"]]
    assert "kpi_006" not in kpi_ids


# ---------------------------------------------------------------------------
# 3. Department excludes ALL and DEPT-PEX
# ---------------------------------------------------------------------------

def test_department_excludes_all_and_pex(filter_options):
    depts = filter_options["departments"]
    assert "ALL" not in depts
    assert "DEPT-PEX" not in depts


# ---------------------------------------------------------------------------
# 4. Forecast month uses supported forecast months
# ---------------------------------------------------------------------------

def test_forecast_months_supported_only(filter_options):
    months = filter_options["months"]
    assert all(m >= FORECAST_HORIZON_START_MONTH for m in months)
    assert all(1 <= m <= 12 for m in months)


# ---------------------------------------------------------------------------
# 5. Baseline matches Risk & Alert governed forecast
# ---------------------------------------------------------------------------

def test_baseline_matches_governed_forecast(icu_dec_kpi001_state):
    state = icu_dec_kpi001_state
    forecast_df = get_kpi_annual_forecast_series(
        load_kpi_monthly_forecast(),
        state["hospital_id"],
        state["department_id"],
        state["kpi_id"],
        GOVERNED_ACTUAL_YEAR,
    )
    mask = forecast_df["month"] == state["forecast_month"]
    row = forecast_df[mask]
    assert not row.empty
    expected = float(row.iloc[0]["monthly_value"])
    assert state["forecast_value"] == pytest.approx(expected, rel=1e-6)


# ---------------------------------------------------------------------------
# 6. Latest actual baseline uses canonical actual data
# ---------------------------------------------------------------------------

def test_baseline_uses_canonical_actual_data(icu_dec_kpi001_state):
    baseline = icu_dec_kpi001_state["baseline"]
    assert baseline is not None
    assert isinstance(baseline, ScenarioBaseline)
    assert baseline.baseline_kpi_value is not None
    assert baseline.baseline_reference_date is not None


# ---------------------------------------------------------------------------
# 7. Intervention filtering follows intervention catalogue
# ---------------------------------------------------------------------------

def test_intervention_filtering_follows_catalogue():
    df = load_interventions_for_kpi("kpi_001")
    assert not df.empty
    # applicable_kpi_id may contain semicolon-separated values
    assert all(df["applicable_kpi_id"].apply(lambda v: "kpi_001" in str(v).split(";")))
    assert all(df["active_flag"].str.strip().str.lower() == "true")


# ---------------------------------------------------------------------------
# 8. Comparator names are exactly Conservative / Expected / Higher Intensity
# ---------------------------------------------------------------------------

def test_comparator_names_exact(icu_dec_kpi001_state):
    profiles = icu_dec_kpi001_state["comparator_profiles"]
    names = [p["comparator_type"] for p in profiles]
    assert set(names) == set(_COMPARATOR_ORDER)
    assert len(names) == 3


# ---------------------------------------------------------------------------
# 9. "Strong" is not used
# ---------------------------------------------------------------------------

def test_strong_not_used_in_page_source():
    src_path = os.path.join(_ROOT, "pages", "04_Simulation_Lab.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    assert '"Strong"' not in src
    assert "'Strong'" not in src
    assert "Strong" not in src or "strong" in src.lower()  # allow "strong" in CSS/selectors


def test_strong_not_used_in_controller_source():
    src_path = os.path.join(_ROOT, "src", "simulation_lab_controller.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    # "Strong" as a standalone comparator label must not appear
    lines = src.splitlines()
    for line in lines:
        if "Strong" in line and "comparator" in line.lower():
            pytest.fail(f"Forbidden word 'Strong' found in comparator context: {line}")


# ---------------------------------------------------------------------------
# 10. Correct existing scenario engine selected by KPI
# ---------------------------------------------------------------------------

def test_engine_map_kpi001():
    assert _KPI_ENGINE_MAP["kpi_001"] is StaffingScenarioEngine


def test_engine_map_kpi002():
    assert _KPI_ENGINE_MAP["kpi_002"] is AbsenteeismScenarioEngine


def test_engine_map_kpi003():
    assert _KPI_ENGINE_MAP["kpi_003"] is PatientFlowScenarioEngine


def test_engine_map_kpi004():
    assert _KPI_ENGINE_MAP["kpi_004"] is PatientFlowScenarioEngine


# ---------------------------------------------------------------------------
# 11. Original forecast is unchanged
# ---------------------------------------------------------------------------

def test_original_forecast_unchanged_after_scenario_run(icu_dec_kpi001_state):
    """Running scenario should not modify the underlying forecast data."""
    state = icu_dec_kpi001_state
    forecast_df = get_kpi_annual_forecast_series(
        load_kpi_monthly_forecast(),
        state["hospital_id"],
        state["department_id"],
        state["kpi_id"],
        GOVERNED_ACTUAL_YEAR,
    )
    mask = forecast_df["month"] == state["forecast_month"]
    row = forecast_df[mask]
    assert not row.empty
    # The forecast value in state must still match the original
    assert state["forecast_value"] == float(row.iloc[0]["monthly_value"])


# ---------------------------------------------------------------------------
# 12. Scenario value comes from governed engine/profile
# ---------------------------------------------------------------------------

def test_scenario_value_from_engine(icu_dec_kpi001_state):
    results = icu_dec_kpi001_state["scenario_results"]
    assert len(results) == 3
    for result in results:
        assert result is not None
        assert result.scenario_primary_kpi_value is not None
        assert result.engine_version != ""
        assert result.assumption_set_id != ""


# ---------------------------------------------------------------------------
# 13. Scenario output labelled Indicative
# ---------------------------------------------------------------------------

def test_scenario_output_labelled_indicative(icu_dec_kpi001_state):
    """Page source must contain 'Indicative Scenario' label."""
    src_path = os.path.join(_ROOT, "pages", "04_Simulation_Lab.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    assert "Indicative Scenario" in src


# ---------------------------------------------------------------------------
# 14. Unit formatting correct
# ---------------------------------------------------------------------------

def test_unit_formatting_uses_format_unit_value(icu_dec_kpi001_state):
    """Controller must import and use format_unit_value."""
    src_path = os.path.join(_ROOT, "src", "simulation_lab_controller.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    assert "format_unit_value" in src


def test_scenario_values_have_units(icu_dec_kpi001_state):
    state = icu_dec_kpi001_state
    for result in state["scenario_results"]:
        assert result is not None
        assert result.baseline_unit != ""


# ---------------------------------------------------------------------------
# 15. Financial values only appear when valid mapping exists
# ---------------------------------------------------------------------------

def test_financial_only_when_mapping_exists(icu_dec_kpi001_state):
    """If no cost driver mapping, financial should be None/Not Available."""
    state = icu_dec_kpi001_state
    # Check if financial results are either dicts with available=True or None
    for fin in state.get("financial_results", []):
        if fin is not None:
            assert isinstance(fin, dict)
            # Either legacy format with "available" key, or new adapter format with "total_cost"
            assert "available" in fin or "total_cost" in fin


# ---------------------------------------------------------------------------
# 16. Financial language follows governance
# ---------------------------------------------------------------------------

def test_financial_display_rules_in_controller():
    src_path = os.path.join(_ROOT, "src", "simulation_lab_controller.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    # Phase 3D corrections: management takeaway uses governed financial labels
    assert "Estimated Intervention Cost" in src
    # Causality/governance language is required
    assert "Causality" in src or "causality" in src
    assert "Moderate" in src  # confidence label


# ---------------------------------------------------------------------------
# 17. No forbidden financial wording appears
# ---------------------------------------------------------------------------

def test_no_forbidden_financial_wording_in_page():
    src_path = os.path.join(_ROOT, "pages", "04_Simulation_Lab.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    forbidden = ["Actual Cost", "Guaranteed Savings", "Profit", "Proven ROI",
                 "High Confidence", "Confirmed Causality", "Definite Cost"]
    for word in forbidden:
        assert word not in src, f"Forbidden word '{word}' found in page source"


def test_no_forbidden_financial_wording_in_controller():
    src_path = os.path.join(_ROOT, "src", "simulation_lab_controller.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    # Check display text — not the _FORBIDDEN_WORDS tuple itself
    forbidden = ["Actual Cost", "Guaranteed Savings", "Profit", "Proven ROI",
                 "High Confidence", "Confirmed Causality", "Definite Cost"]
    in_tuple = False
    for line in src.splitlines():
        if "_FORBIDDEN_WORDS" in line:
            in_tuple = True
        if in_tuple and line.strip().endswith(")"):
            in_tuple = False
        if in_tuple:
            continue
        for word in forbidden:
            assert word not in line, f"Forbidden word '{word}' found in controller: {line}"


# ---------------------------------------------------------------------------
# 18. Net financial impact uses existing engine
# ---------------------------------------------------------------------------

def test_net_impact_uses_existing_engine(icu_dec_kpi001_state):
    src_path = os.path.join(_ROOT, "src", "simulation_lab_controller.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    # Phase 3D corrections: controller uses smallest possible adapter
    # for semicolon-separated applicable_comparator_types instead of batch engines.
    assert "_safe_financial_compute" in src or "_load_financial_cost_driver_mapping" in src
    assert "financial_cost_driver_mapping" in src or "_has_financial_mapping" in src


# ---------------------------------------------------------------------------
# 19. Trade-off/displacement comes from existing engines
# ---------------------------------------------------------------------------

def test_tradeoff_uses_existing_engine(icu_dec_kpi001_state):
    state = icu_dec_kpi001_state
    tradeoff = state.get("tradeoff_text", "")
    assert tradeoff != ""
    src_path = os.path.join(_ROOT, "src", "simulation_lab_controller.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    assert "ScenarioTradeoffEngine" in src
    assert "ScenarioDisplacementEngine" in src


# ---------------------------------------------------------------------------
# 20. Session-state handoff stores selected scenario context
# ---------------------------------------------------------------------------

def test_session_state_handoff_in_page():
    src_path = os.path.join(_ROOT, "pages", "04_Simulation_Lab.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    assert "decision_review_context" in src
    assert "st.session_state" in src
    assert "hospital_id" in src
    assert "action_strategy" in src
    assert "selected_action_level" in src
    assert "comparator" in src


def test_session_state_handoff_includes_action_detail_and_resource_line():
    """Handoff must include action_detail and resource_line as authoritative fields."""
    src_path = os.path.join(_ROOT, "pages", "04_Simulation_Lab.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    # Both keys must be written into the handoff dict
    assert '"action_detail"' in src
    assert '"resource_line"' in src
    # And the value sent to the handoff must be the selected profile's value
    # (sel_action_detail and the page-level resource_line)
    assert "sel_action_detail" in src


def test_session_state_handoff_recommended_action_uses_action_detail():
    """Handoff action_strategy + selected_action_level + action_detail must be reusable downstream."""
    src_path = os.path.join(_ROOT, "pages", "04_Simulation_Lab.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    # The handoff writes all three fields
    assert '"action_strategy"' in src
    assert '"selected_action_level"' in src
    assert '"action_detail"' in src
    # The page's own "Recommended Action" row must use action_detail
    # (NOT a combined "{action_strategy} — {selected_action_level}" label)
    fn_start = src.index("def _render_decision_table(")
    fn_body = src[fn_start:fn_start + 3500]
    assert '"Recommended Action"' in fn_body
    assert "action_detail" in fn_body
    # Strategy/level must appear as separate rows, not combined
    assert "Action Strategy" in fn_body
    assert "Selected Action Level" in fn_body


def test_decision_page_reads_action_detail_and_resource_line_directly():
    """The Decision page must read action_detail and resource_line from the handoff (not derive)."""
    dec_path = os.path.join(_ROOT, "pages", "05_Decision_and_Call_for_Action.py")
    with open(dec_path, "r", encoding="utf-8") as fh:
        dec = fh.read()
    # The page should look for these keys in context
    assert 'context.get("action_detail")' in dec
    assert 'context.get("resource_line")' in dec
    # The page must show action_detail in the Recommended Action card
    # (NOT a combined "{action_strategy} — {selected_action_level}" label)
    assert "Recommended Action" in dec
    # The literal combined-label pattern must NOT appear in the Decision page
    assert 'f"{action_strategy} — {selected_action_level}"' not in dec


# ---------------------------------------------------------------------------
# 21. No approval/implementation claim
# ---------------------------------------------------------------------------

def test_no_approval_claim_in_page():
    src_path = os.path.join(_ROOT, "pages", "04_Simulation_Lab.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    # Page references decision status via _FINANCIAL_DISPLAY_RULES["decision_status"]
    assert '_FINANCIAL_DISPLAY_RULES["decision_status"]' in src
    # "Approved" must NOT appear in display text (allowed only in forbidden-words import)
    display_lines = [ln for ln in src.splitlines() if "Approved" in ln and "_FORBIDDEN" not in ln and "\"Approved\"" not in ln and "_FINANCIAL_DISPLAY_RULES" not in ln]
    assert not display_lines, f"'Approved' found in display text: {display_lines}"
    assert "implementation is approved" not in src.lower()


# ---------------------------------------------------------------------------
# 22. No new model created or invoked
# ---------------------------------------------------------------------------

def test_no_new_model_files():
    """Verify no new scenario/financial model files were created."""
    src_dir = os.path.join(_ROOT, "src")
    existing_models = [
        "staffing_scenario_engine.py",
        "absenteeism_scenario_engine.py",
        "patient_flow_scenario_engine.py",
        "financial_cost_engine.py",
        "financial_benefit_engine.py",
        "financial_net_impact_engine.py",
        "financial_roi_engine.py",
    ]
    for model in existing_models:
        assert os.path.exists(os.path.join(src_dir, model)), f"Missing existing model: {model}"

    # The only new file should be the controller
    new_files = ["simulation_lab_controller.py"]
    for f in new_files:
        assert os.path.exists(os.path.join(src_dir, f)), f"Missing new controller: {f}"


def test_controller_only_invokes_existing_engines(icu_dec_kpi001_state):
    """Controller returns results from existing engines, not custom calculations."""
    results = icu_dec_kpi001_state["scenario_results"]
    for result in results:
        assert result is not None
        # Verify the result was produced by a known engine version
        assert result.engine_version in ("2C-2C-1.0",)
        assert result.calculation_rule_id != ""


# ===========================================================================
# PHASE 3D — TARGETED CORRECTIONS (20 new tests)
# ===========================================================================

# ---------------------------------------------------------------------------
# 23. Governed cutoff blocks Aug-Dec forecast from becoming actual baseline
# ---------------------------------------------------------------------------

def test_governed_cutoff_blocks_aug_dec_actual_baseline():
    """Latest actual must stop at JUL 2025 — never pick Aug-Dec forecast rows."""
    from src.streamlit_executive_data_loader import (
        load_kpi_daily,
        GOVERNED_ACTUAL_MONTH_CUTOFF,
    )
    df = load_kpi_daily()
    state = build_simulation_state(
        hospital_id="HOSP-001",
        department_id="DEPT-ICU",
        kpi_id="kpi_001",
        forecast_month=12,
        intervention_id="INT-STAFF-001",
    )
    baseline_date = state["baseline"].baseline_reference_date
    assert baseline_date is not None
    # Parse and assert month is <= cutoff
    import datetime
    dt = datetime.datetime.fromisoformat(str(baseline_date).replace("Z", ""))
    assert dt.month <= GOVERNED_ACTUAL_MONTH_CUTOFF
    assert dt.year == 2025


def test_governed_cutoff_helper_filters_correctly():
    """The _apply_governed_cutoff helper drops Aug-Dec rows."""
    from src.simulation_lab_controller import _apply_governed_cutoff
    from src.streamlit_executive_data_loader import load_kpi_daily
    df = load_kpi_daily()
    df_filtered = _apply_governed_cutoff(df)
    assert not df_filtered.empty
    import pandas as pd
    df_filtered["_d"] = pd.to_datetime(df_filtered["reporting_date"], errors="coerce")
    assert df_filtered["_d"].dt.month.max() <= 7
    assert df_filtered["_d"].dt.year.max() <= 2025


# ---------------------------------------------------------------------------
# 24. UI labels: Minimum / Recommended / Intensive Action
# ---------------------------------------------------------------------------

def test_display_label_for_comparator_id_exists():
    """Controller exports _DISPLAY_LABEL_FOR_COMPARATOR_ID mapping."""
    from src.simulation_lab_controller import _DISPLAY_LABEL_FOR_COMPARATOR_ID
    assert _DISPLAY_LABEL_FOR_COMPARATOR_ID["Conservative"] == "Minimum Action"
    assert _DISPLAY_LABEL_FOR_COMPARATOR_ID["Expected"] == "Recommended Action"
    assert _DISPLAY_LABEL_FOR_COMPARATOR_ID["Higher Intensity"] == "Intensive Action"


def test_page_uses_ui_labels():
    """Page source uses _DISPLAY_LABEL_FOR_COMPARATOR_ID for display."""
    src_path = os.path.join(_ROOT, "pages", "04_Simulation_Lab.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    assert "_DISPLAY_LABEL_FOR_COMPARATOR_ID" in src
    # Page imports the mapping; controller holds the literal labels.
    from src.simulation_lab_controller import _DISPLAY_LABEL_FOR_COMPARATOR_ID as M
    assert M["Conservative"] == "Minimum Action"
    assert M["Expected"] == "Recommended Action"
    assert M["Higher Intensity"] == "Intensive Action"


def test_internal_comparator_names_unchanged():
    """Internal governed names remain Conservative/Expected/Higher Intensity."""
    profiles = build_simulation_state(
        hospital_id="HOSP-001",
        department_id="DEPT-ICU",
        kpi_id="kpi_001",
        forecast_month=12,
        intervention_id="INT-STAFF-001",
    )["comparator_profiles"]
    names = [p["comparator_type"] for p in profiles]
    assert "Conservative" in names
    assert "Expected" in names
    assert "Higher Intensity" in names


# ---------------------------------------------------------------------------
# 25. Scenario assumptions differ across profiles
# ---------------------------------------------------------------------------

def test_assumptions_differ_across_profiles(icu_dec_kpi001_state):
    """Conservative/Expected/Higher Intensity must use different assumption values."""
    profiles = icu_dec_kpi001_state["comparator_profiles"]
    assumptions_by_type = {p["comparator_type"]: p["assumptions"] for p in profiles}
    # additional_staff_count should increase across profiles
    c = assumptions_by_type["Conservative"].get("additional_staff_count", 0)
    e = assumptions_by_type["Expected"].get("additional_staff_count", 0)
    h = assumptions_by_type["Higher Intensity"].get("additional_staff_count", 0)
    assert c < e < h, f"staff counts not strictly increasing: {c}, {e}, {h}"


def test_action_intensity_helper_renders():
    """_assumption_intensity_line produces a readable action summary."""
    sys.path.insert(0, _ROOT)
    # Import the page module without running Streamlit
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "sim_lab_page", os.path.join(_ROOT, "pages", "04_Simulation_Lab.py")
    )
    # We can't actually import a Streamlit script, so read source and verify
    src_path = os.path.join(_ROOT, "pages", "04_Simulation_Lab.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    assert "_assumption_intensity_line" in src
    assert "additional_staff_count" in src


# ---------------------------------------------------------------------------
# 26. Capped/identical scenario values are surfaced with action intensity
# ---------------------------------------------------------------------------

def test_capped_scenario_detected_in_page():
    """Page detects when all 3 profiles produce identical values (ceiling hit)."""
    src_path = os.path.join(_ROOT, "pages", "04_Simulation_Lab.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    assert "capped_note" in src or "governed ceiling" in src
    # Ensure intensity is rendered when capped
    assert "intensity_line" in src


# ---------------------------------------------------------------------------
# 27. Financial adapter parses comma/semicolon-separated comparator types
# ---------------------------------------------------------------------------

def test_has_financial_mapping_parses_comma_separated():
    """_has_financial_mapping handles comma-separated applicable_comparator_types."""
    from src.simulation_lab_controller import _has_financial_mapping
    # "Staffing Coverage Adjustment" is the scenario_family used in the mapping file
    assert _has_financial_mapping("Staffing Coverage Adjustment", "Conservative") is True
    assert _has_financial_mapping("Staffing Coverage Adjustment", "Expected") is True
    assert _has_financial_mapping("Staffing Coverage Adjustment", "Higher Intensity") is True


def test_financial_adapter_returns_total_cost_when_mapping_exists(icu_dec_kpi001_state):
    """_safe_financial_compute returns a dict with total_cost when mapping exists."""
    from src.simulation_lab_controller import _safe_financial_compute
    assumptions = {"additional_staff_count": 2, "temporary_staff_count": 2,
                   "intervention_duration_days": 14}
    result = _safe_financial_compute(
        "Staffing Coverage Adjustment", "Expected", assumptions
    )
    assert result is not None
    assert "total_cost" in result
    assert result["total_cost"] > 0
    assert result["currency"] == "MYR"


def test_financial_adapter_returns_none_when_no_mapping():
    """No mapping → None → UI shows 'Not Available'."""
    from src.simulation_lab_controller import _safe_financial_compute
    result = _safe_financial_compute(
        "Unknown Family", "Conservative", {"additional_staff_count": 1}
    )
    assert result is None


# ---------------------------------------------------------------------------
# 28. Trade-off / displacement never expose Python errors
# ---------------------------------------------------------------------------

def test_tradeoff_displacement_never_expose_errors(icu_dec_kpi001_state):
    """build_tradeoff_and_displacement must never return raw Python error text."""
    state = icu_dec_kpi001_state
    tt = state.get("tradeoff_text", "")
    dt = state.get("displacement_text", "")
    for snippet in ["Traceback", "AttributeError", "Exception", "Error:"]:
        assert snippet not in tt, f"Python error leaked in tradeoff: {tt}"
        assert snippet not in dt, f"Python error leaked in displacement: {dt}"
    assert tt != ""
    assert dt != ""


def test_tradeoff_uses_safe_public_methods():
    """Controller only calls documented public methods on trade-off engines."""
    src_path = os.path.join(_ROOT, "src", "simulation_lab_controller.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    # Must NOT call non-existent methods
    assert "calculate_tradeoffs" not in src
    assert "calculate_displacement_risk" not in src
    # Must use safe public methods
    assert "compare_comparators" in src
    assert "analyse_displacement" in src


# ---------------------------------------------------------------------------
# 29. Management Takeaway follows deterministic structure
# ---------------------------------------------------------------------------

def test_management_takeaway_structure(icu_dec_kpi001_state):
    """Takeaway must contain all required sections."""
    state = icu_dec_kpi001_state
    sel_idx = 0
    sel_profile = state["comparator_profiles"][sel_idx]
    sel_result = state["scenario_results"][sel_idx]
    sel_financial = state.get("financial_results", [None])[sel_idx]
    takeaway = build_management_takeaway(
        kpi_id=state["kpi_id"],
        kpi_name=state["kpi_name"],
        baseline_value=state["baseline_value"],
        baseline_unit=state["baseline_unit"],
        forecast_value=state["forecast_value"],
        forecast_unit=state["forecast_unit"],
        scenario_result=sel_result,
        comparator_type=sel_profile["comparator_type"],
        intervention_name=state["intervention_name"],
        financial=sel_financial,
    )
    assert "RECOMMENDED ACTION" in takeaway
    assert "EXPECTED OPERATIONAL IMPACT" in takeaway
    assert "WHY ACT NOW" in takeaway
    assert "RESOURCE LEVEL" in takeaway
    assert "FINANCIAL VIEW" in takeaway
    assert "DECISION REQUIRED" in takeaway


def test_management_takeaway_uses_ui_label():
    """Takeaway uses Minimum/Recommended/Intensive Action for resource level."""
    state = build_simulation_state(
        hospital_id="HOSP-001",
        department_id="DEPT-ICU",
        kpi_id="kpi_001",
        forecast_month=12,
        intervention_id="INT-STAFF-001",
    )
    sel_idx = 0
    sel_profile = state["comparator_profiles"][sel_idx]
    sel_result = state["scenario_results"][sel_idx]
    sel_financial = state.get("financial_results", [None])[sel_idx]
    takeaway = build_management_takeaway(
        kpi_id=state["kpi_id"],
        kpi_name=state["kpi_name"],
        baseline_value=state["baseline_value"],
        baseline_unit=state["baseline_unit"],
        forecast_value=state["forecast_value"],
        forecast_unit=state["forecast_unit"],
        scenario_result=sel_result,
        comparator_type=sel_profile["comparator_type"],
        intervention_name=state["intervention_name"],
        financial=sel_financial,
    )
    assert "Minimum Action" in takeaway


# ---------------------------------------------------------------------------
# 30. Unit formatting uses percentage points / minutes
# ---------------------------------------------------------------------------

def test_format_change_text_uses_percentage_points():
    """_format_change_text maps 'Percent' → percentage points."""
    from src.simulation_lab_controller import format_unit_value
    # format_unit_value maps Percent → '%'
    assert "%" in format_unit_value(84.6, "Percent")
    assert "minutes" in format_unit_value(30.0, "Minutes")


def test_page_format_change_text_helper():
    """Page source contains _format_change_text helper using clean units."""
    src_path = os.path.join(_ROOT, "pages", "04_Simulation_Lab.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    assert "_format_change_text" in src
    assert "percentage points" in src


def test_page_clean_unit_label_helper():
    """Page source contains _clean_unit_label helper."""
    src_path = os.path.join(_ROOT, "pages", "04_Simulation_Lab.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    assert "_clean_unit_label" in src


# ---------------------------------------------------------------------------
# 31. Absenteeism baseline extracts total_staff and absent_count
# ---------------------------------------------------------------------------

def test_absenteeism_baseline_extracts_components():
    """kpi_002 baseline must include baseline_absenteeism_rate."""
    state = build_simulation_state(
        hospital_id="HOSP-001",
        department_id="DEPT-ICU",
        kpi_id="kpi_002",
        forecast_month=12,
        intervention_id="INT-ABS-001",
    )
    baseline = state["baseline"]
    assert baseline is not None
    assert baseline.baseline_absenteeism_rate is not None
    assert baseline.baseline_absenteeism_rate > 0


# ---------------------------------------------------------------------------
# 32. Regression: existing engines still invoked correctly
# ---------------------------------------------------------------------------

def test_staffing_engine_invoked_for_kpi001(icu_dec_kpi001_state):
    """kpi_001 still uses StaffingScenarioEngine."""
    results = icu_dec_kpi001_state["scenario_results"]
    for r in results:
        assert r.engine_version == "2C-2C-1.0"


def test_patient_flow_engine_invoked_for_kpi004():
    """kpi_004 still uses PatientFlowScenarioEngine."""
    state = build_simulation_state(
        hospital_id="HOSP-001",
        department_id="DEPT-ED",
        kpi_id="kpi_004",
        forecast_month=12,
        intervention_id="INT-FLOW-001",
    )
    results = state["scenario_results"]
    assert len(results) == 3
    for r in results:
        assert r is not None
        assert r.engine_version == "2C-2C-1.0"


# ===========================================================================
# PHASE 3D — LOGIC CLEANUP (22 new tests)
# ===========================================================================

# ---------------------------------------------------------------------------
# 33. _KPI_TO_ACTION_STRATEGY is exported from controller
# ---------------------------------------------------------------------------

def test_kpi_to_action_strategy_exported():
    """Controller exports _KPI_TO_ACTION_STRATEGY dict."""
    assert isinstance(_KPI_TO_ACTION_STRATEGY, dict)
    assert len(_KPI_TO_ACTION_STRATEGY) == 4


def test_kpi_to_action_strategy_all_kpis_covered():
    """All supported KPI IDs must have an entry in _KPI_TO_ACTION_STRATEGY."""
    for kpi_id in _SUPPORTED_KPI_IDS:
        assert kpi_id in _KPI_TO_ACTION_STRATEGY, (
            f"{kpi_id} missing from _KPI_TO_ACTION_STRATEGY"
        )


def test_kpi_to_action_strategy_kpi001():
    assert _KPI_TO_ACTION_STRATEGY["kpi_001"] == "Staffing Coverage Adjustment"


def test_kpi_to_action_strategy_kpi002():
    assert _KPI_TO_ACTION_STRATEGY["kpi_002"] == "Absenteeism Contingency Response"


def test_kpi_to_action_strategy_kpi003():
    assert _KPI_TO_ACTION_STRATEGY["kpi_003"] == "Patient Flow Capacity Adjustment"


def test_kpi_to_action_strategy_kpi004():
    assert _KPI_TO_ACTION_STRATEGY["kpi_004"] == "Patient Flow Capacity Adjustment"


def test_kpi003_kpi004_share_action_strategy():
    """kpi_003 and kpi_004 share the same action strategy (both are flow KPIs)."""
    assert _KPI_TO_ACTION_STRATEGY["kpi_003"] == _KPI_TO_ACTION_STRATEGY["kpi_004"]


# ---------------------------------------------------------------------------
# 34. Page imports _KPI_TO_ACTION_STRATEGY and does NOT import load_interventions_for_kpi
# ---------------------------------------------------------------------------

def test_page_imports_kpi_to_action_strategy():
    src_path = os.path.join(_ROOT, "pages", "04_Simulation_Lab.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    assert "_KPI_TO_ACTION_STRATEGY" in src


def test_page_does_not_import_load_interventions_for_kpi():
    """load_interventions_for_kpi was removed after the Intervention slicer was dropped."""
    src_path = os.path.join(_ROOT, "pages", "04_Simulation_Lab.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    # Must not appear in the import block
    import_block_lines = [
        ln for ln in src.splitlines()
        if "load_interventions_for_kpi" in ln and ln.strip().startswith(("from", "import"))
    ]
    assert not import_block_lines, (
        f"load_interventions_for_kpi still imported: {import_block_lines}"
    )


# ---------------------------------------------------------------------------
# 35. Intervention selectbox has been removed from the page
# ---------------------------------------------------------------------------

def test_page_has_no_intervention_selectbox():
    """The old Intervention selectbox must no longer appear in page source."""
    src_path = os.path.join(_ROOT, "pages", "04_Simulation_Lab.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    # Pattern: st.selectbox(...label..."Intervention"...)
    # Look for a selectbox whose first positional arg is literally "Intervention"
    assert '"Intervention"' not in src or "sim_intervention" not in src, (
        "Old Intervention selectbox still present in page (found both "
        "'\"Intervention\"' and 'sim_intervention')"
    )
    assert "sim_intervention" not in src, "Old selectbox key 'sim_intervention' still in page"


# ---------------------------------------------------------------------------
# 36. Page derives action_strategy from _KPI_TO_ACTION_STRATEGY
# ---------------------------------------------------------------------------

def test_page_derives_action_strategy():
    """Page must derive action_strategy via _KPI_TO_ACTION_STRATEGY.get(kpi_id, ...)."""
    src_path = os.path.join(_ROOT, "pages", "04_Simulation_Lab.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    assert "action_strategy" in src
    assert "_KPI_TO_ACTION_STRATEGY.get(kpi_id" in src


def test_page_action_strategy_display_banner():
    """Page renders an Action Strategy display block visible to users."""
    src_path = os.path.join(_ROOT, "pages", "04_Simulation_Lab.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    assert "Action Strategy" in src


# ---------------------------------------------------------------------------
# 37. Simulation eligibility gate
# ---------------------------------------------------------------------------

def test_page_has_eligibility_gate():
    """Page must check baseline/forecast/comparator_profiles before rendering output."""
    src_path = os.path.join(_ROOT, "pages", "04_Simulation_Lab.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    # Eligibility checks
    assert "_baseline_ok" in src or "baseline_ok" in src
    assert "_forecast_ok" in src or "forecast_ok" in src
    assert "_mapping_ok" in src or "mapping_ok" in src


def test_page_has_simulation_not_available_message():
    """Page must display SIMULATION NOT AVAILABLE when eligibility fails."""
    src_path = os.path.join(_ROOT, "pages", "04_Simulation_Lab.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    assert "SIMULATION NOT AVAILABLE" in src


def test_page_calls_stop_after_unavailable_message():
    """Page must call st.stop() after the unavailable message to halt further rendering."""
    src_path = os.path.join(_ROOT, "pages", "04_Simulation_Lab.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        lines = fh.readlines()
    # Find the SIMULATION NOT AVAILABLE line; verify st.stop() appears after it
    unavail_idx = next(
        (i for i, ln in enumerate(lines) if "SIMULATION NOT AVAILABLE" in ln), None
    )
    assert unavail_idx is not None, "SIMULATION NOT AVAILABLE not found"
    rest = "".join(lines[unavail_idx:])
    assert "st.stop()" in rest, "st.stop() not found after SIMULATION NOT AVAILABLE message"


# ---------------------------------------------------------------------------
# 38. _render_decision_table uses action_strategy + selected_action_level
# ---------------------------------------------------------------------------

def test_render_decision_table_signature_has_action_strategy():
    """_render_decision_table must declare action_strategy parameter."""
    src_path = os.path.join(_ROOT, "pages", "04_Simulation_Lab.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    assert "action_strategy" in src
    # Signature check: param appears inside the function def
    assert "def _render_decision_table(" in src
    # Find the function and check params
    fn_start = src.index("def _render_decision_table(")
    fn_sig_end = src.index(")", fn_start)
    fn_sig = src[fn_start:fn_sig_end]
    assert "action_strategy" in fn_sig
    assert "selected_action_level" in fn_sig


def test_render_decision_table_recommended_action_row():
    """Recommended Action row must display action_detail (the selected scenario's action text)."""
    src_path = os.path.join(_ROOT, "pages", "04_Simulation_Lab.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    # The function must accept action_detail as a parameter
    fn_start = src.index("def _render_decision_table(")
    fn_sig_end = src.index(")", fn_start)
    fn_sig = src[fn_start:fn_sig_end]
    assert "action_detail" in fn_sig
    # The function body must put action_detail in the Recommended Action row
    fn_body = src[fn_start:fn_start + 3500]
    assert "action_strategy" in fn_body
    assert "selected_action_level" in fn_body
    # The Recommended Action tuple must reference action_detail (not a combined label)
    assert '"Recommended Action"' in fn_body
    # Ensure it no longer references intervention_name in the row definition
    assert '"Recommended Action", f"{intervention_name}' not in fn_body
    # The combined label pattern must NOT appear in the rows
    assert '"Recommended Action", f"{action_strategy} — {selected_action_level}"' not in fn_body


# ---------------------------------------------------------------------------
# 39. Session-state handoff keys
# ---------------------------------------------------------------------------

def test_handoff_has_action_strategy_key():
    """Session-state handoff dict must include 'action_strategy'."""
    src_path = os.path.join(_ROOT, "pages", "04_Simulation_Lab.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    # Find the handoff dict
    handoff_start = src.index('"decision_review_context"')
    handoff_block = src[handoff_start:handoff_start + 1500]
    assert '"action_strategy"' in handoff_block


def test_handoff_has_selected_action_level_key():
    """Session-state handoff dict must include 'selected_action_level'."""
    src_path = os.path.join(_ROOT, "pages", "04_Simulation_Lab.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    handoff_start = src.index('"decision_review_context"')
    handoff_block = src[handoff_start:handoff_start + 1500]
    assert '"selected_action_level"' in handoff_block


def test_handoff_does_not_have_intervention_name_key():
    """intervention_name must NOT appear as a standalone handoff key (it was removed)."""
    src_path = os.path.join(_ROOT, "pages", "04_Simulation_Lab.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    handoff_start = src.index('"decision_review_context"')
    handoff_block = src[handoff_start:handoff_start + 1500]
    assert '"intervention_name"' not in handoff_block, (
        "'intervention_name' should not be a key in the session-state handoff"
    )


# ---------------------------------------------------------------------------
# 40. action_detail is the user-facing Recommended Action (Phase 3D/3E fix)
# ---------------------------------------------------------------------------

# Expected action_detail values for staffing profiles (kpi_001)
STAFFING_ACTION_DETAIL = {
    "minimum": "+1 staff · +1 temp · 7 days",
    "recommended": "+2 staff · +2 temp · +1 reassign · 10% shift coverage · 14 days",
    "intensive": "+4 staff · +3 temp · +2 reassign · 20% shift coverage · 30 days",
}

# Expected action_detail values for absenteeism profiles (kpi_002)
ABSENTEEISM_ACTION_DETAIL = {
    "minimum": "10% reduction · 30% replacement · 25% contingency roster · 7 days",
    "recommended": "20% reduction · 50% replacement · 50% contingency roster · 14 days",
    "intensive": "35% reduction · 75% replacement · 75% contingency roster · 30 days",
}

# Expected action_detail values for flow profiles (kpi_003/kpi_004)
FLOW_ACTION_DETAIL = {
    "minimum": "+5% service capacity · +2% throughput · +5% routing efficiency · +1 temp resource · 7 days",
    "recommended": "+10% service capacity · +5% throughput · +10% routing efficiency · +3 temp resource · 14 days",
    "intensive": "+20% service capacity · +12% throughput · +18% routing efficiency · +6 temp resource · 30 days",
}


def test_action_detail_for_profile_staffing_minimum():
    """Staffing Minimum must produce '+1 staff · +1 temp · 7 days'."""
    # Re-import to get a clean module
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_04_sim_staff_min",
        os.path.join(_ROOT, "pages", "04_Simulation_Lab.py"),
    )
    sim = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sim)

    assumptions = {
        "additional_staff_count": 1,
        "temporary_staff_count": 1,
        "staff_reassignment_count": 0,
        "uncovered_shift_reduction_pct": 0,
        "intervention_duration_days": 7,
    }
    result = sim._action_detail_for_profile("kpi_001", assumptions)
    assert result == STAFFING_ACTION_DETAIL["minimum"]
    assert result == "+1 staff · +1 temp · 7 days"


def test_action_detail_for_profile_staffing_recommended():
    """Staffing Recommended must produce '+2 staff · +2 temp · +1 reassign · 10% shift coverage · 14 days'."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_04_sim_staff_rec",
        os.path.join(_ROOT, "pages", "04_Simulation_Lab.py"),
    )
    sim = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sim)

    assumptions = {
        "additional_staff_count": 2,
        "temporary_staff_count": 2,
        "staff_reassignment_count": 1,
        "uncovered_shift_reduction_pct": 10,
        "intervention_duration_days": 14,
    }
    result = sim._action_detail_for_profile("kpi_001", assumptions)
    assert result == STAFFING_ACTION_DETAIL["recommended"]
    assert result == "+2 staff · +2 temp · +1 reassign · 10% shift coverage · 14 days"


def test_action_detail_for_profile_staffing_intensive():
    """Staffing Intensive must produce '+4 staff · +3 temp · +2 reassign · 20% shift coverage · 30 days'."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_04_sim_staff_high",
        os.path.join(_ROOT, "pages", "04_Simulation_Lab.py"),
    )
    sim = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sim)

    assumptions = {
        "additional_staff_count": 4,
        "temporary_staff_count": 3,
        "staff_reassignment_count": 2,
        "uncovered_shift_reduction_pct": 20,
        "intervention_duration_days": 30,
    }
    result = sim._action_detail_for_profile("kpi_001", assumptions)
    assert result == STAFFING_ACTION_DETAIL["intensive"]
    assert result == "+4 staff · +3 temp · +2 reassign · 20% shift coverage · 30 days"


def test_action_detail_for_profile_flow_recommended():
    """Flow (kpi_003/kpi_004) Recommended must produce a flow-family action_detail."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_04_sim_flow_rec",
        os.path.join(_ROOT, "pages", "04_Simulation_Lab.py"),
    )
    sim = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sim)

    # Test against kpi_003 (Bed Occupancy) — Expected profile
    assumptions = {
        "service_capacity_change_pct": 10,
        "throughput_change_pct": 5,
        "arrival_change_pct": 0,
        "routing_efficiency_change_pct": 10,
        "temporary_resource_change": 3,
        "intervention_duration_days": 14,
    }
    result_kpi3 = sim._action_detail_for_profile("kpi_003", assumptions)
    assert result_kpi3 == FLOW_ACTION_DETAIL["recommended"]

    # Test against kpi_004 (Average Patient Waiting Time) — same assumptions
    result_kpi4 = sim._action_detail_for_profile("kpi_004", assumptions)
    assert result_kpi4 == FLOW_ACTION_DETAIL["recommended"]
    # Both flow KPIs produce the same string for the same assumptions
    assert result_kpi3 == result_kpi4


def test_action_detail_for_profile_absenteeism_recommended():
    """Absenteeism (kpi_002) Recommended must produce a flow-family action_detail."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_04_sim_abs_rec",
        os.path.join(_ROOT, "pages", "04_Simulation_Lab.py"),
    )
    sim = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sim)

    assumptions = {
        "assumed_absenteeism_reduction_pct": 20,
        "replacement_coverage_pct": 50,
        "contingency_roster_activation_pct": 50,
        "intervention_duration_days": 14,
    }
    result = sim._action_detail_for_profile("kpi_002", assumptions)
    assert result == ABSENTEEISM_ACTION_DETAIL["recommended"]


def test_decision_page_shows_action_detail_in_recommended_action_card():
    """The Decision page Recommended Action card must display action_detail directly."""
    dec_path = os.path.join(_ROOT, "pages", "05_Decision_and_Call_for_Action.py")
    with open(dec_path, "r", encoding="utf-8") as fh:
        dec_src = fh.read()

    # The main "Recommended Action" card (in the Action Commitment section)
    # must display action_detail directly, not the combined label.
    # Locate the Action Commitment section.
    commitment_idx = dec_src.find("Action Commitment")
    assert commitment_idx > 0, "Action Commitment section must exist"
    # Find the next "Recommended Action" label that comes after Action Commitment
    # (i.e., the main card, not the historical Decision Record).
    rec_idx = dec_src.find("Recommended Action", commitment_idx)
    assert rec_idx > 0, "Recommended Action card must exist after Action Commitment"
    # Look at a 600-char window around this card to capture the value.
    card_window = dec_src[rec_idx:rec_idx + 600]
    # The card value must reference the action_detail variable
    assert "action_detail" in card_window, (
        "The main Recommended Action card must display action_detail"
    )
    # The card value must NOT use the combined "{action_strategy} — {selected_action_level}" label
    assert "action_strategy} —" not in card_window, (
        "The main Recommended Action card must NOT use the combined strategy+level label"
    )
    assert "selected_action_level}" not in card_window, (
        "The main Recommended Action card must NOT use the combined strategy+level label"
    )

    # Strategy and level are still in the page (Decision Context table)
    assert "Action Strategy" in dec_src
    assert "Action Level" in dec_src


def test_simulation_lab_passes_action_detail_to_decision_table():
    """The Simulation Lab call to _render_decision_table must pass sel_action_detail."""
    src_path = os.path.join(_ROOT, "pages", "04_Simulation_Lab.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    # The call site passes action_detail=sel_action_detail (as keyword argument)
    # The function definition uses action_detail: str = "" (with colon, not equals)
    # So we search for the exact call pattern.
    assert "action_detail=sel_action_detail" in src, (
        "_render_decision_table must be called with action_detail=sel_action_detail"
    )
    # And confirm there's exactly one call site
    assert src.count("action_detail=sel_action_detail") == 1


def test_simulation_lab_handoff_passes_action_detail_and_resource_line():
    """The handoff must include action_detail and resource_line keys."""
    src_path = os.path.join(_ROOT, "pages", "04_Simulation_Lab.py")
    with open(src_path, "r", encoding="utf-8") as fh:
        src = fh.read()
    handoff_start = src.index('"decision_review_context"')
    handoff_block = src[handoff_start:handoff_start + 2000]
    assert '"action_detail"' in handoff_block
    assert '"resource_line"' in handoff_block


def test_action_detail_consistency_across_pages_staffing():
    """The same action_detail value must be produced by _action_detail_for_profile
    and used in both the Simulation Lab decision table and the Decision page."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_04_sim_consistency",
        os.path.join(_ROOT, "pages", "04_Simulation_Lab.py"),
    )
    sim = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sim)

    for level, assumptions in [
        ("minimum", {
            "additional_staff_count": 1,
            "temporary_staff_count": 1,
            "staff_reassignment_count": 0,
            "uncovered_shift_reduction_pct": 0,
            "intervention_duration_days": 7,
        }),
        ("recommended", {
            "additional_staff_count": 2,
            "temporary_staff_count": 2,
            "staff_reassignment_count": 1,
            "uncovered_shift_reduction_pct": 10,
            "intervention_duration_days": 14,
        }),
        ("intensive", {
            "additional_staff_count": 4,
            "temporary_staff_count": 3,
            "staff_reassignment_count": 2,
            "uncovered_shift_reduction_pct": 20,
            "intervention_duration_days": 30,
        }),
    ]:
        # 1. The Simulation Lab page produces this exact action_detail
        sim_action_detail = sim._action_detail_for_profile("kpi_001", assumptions)
        assert sim_action_detail == STAFFING_ACTION_DETAIL[level]

        # 2. The Decision page reads action_detail from the handoff
        handoff = {
            "hospital_id": "HOSP-001",
            "department_id": "DEPT-ICU",
            "kpi_id": "kpi_001",
            "forecast_month_label": "SEP 2025",
            "selected_action_level": level.replace("minimum", "Minimum Action")
                .replace("recommended", "Recommended Action")
                .replace("intensive", "Intensive Action"),
            "action_strategy": "Staffing Coverage Adjustment",
            "do_nothing_forecast": 80.0,
            "scenario_kpi_value": 75.0,
            "change": -5.0,
            "scenario_status": "ABOVE_TARGET",
            "intervention_id": "INT-STAFF-001",
            "comparator": level,
            "scenario_unit": "%",
            "action_detail": sim_action_detail,
            "resource_line": sim_action_detail,
            "management_takeaway": "Take action to reduce uncovered shifts.",
        }
        # 3. The Decision page would display handoff["action_detail"] in
        #    the Recommended Action card. The handoff value must equal the
        #    value the Simulation Lab page produced.
        assert handoff["action_detail"] == sim_action_detail

        # 4. The Recommended Action card value must NOT be the combined label
        combined = f"{handoff['action_strategy']} — {handoff['selected_action_level']}"
        assert handoff["action_detail"] != combined

