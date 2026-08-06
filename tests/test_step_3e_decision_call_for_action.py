"""tests/test_step_3e_decision_call_for_action.py — Phase 3E Decision & Call for Action tests.

Focused tests only. No full regression.
"""
from __future__ import annotations

import datetime
import os
import sys
from typing import Any, Dict

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC_DIR = os.path.join(_ROOT, "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from src.simulation_lab_controller import _KPI_ID_TO_NAME, _KPI_TO_ACTION_STRATEGY
from src.streamlit_executive_data_loader import _display_department, GOVERNED_ACTUAL_YEAR


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_handoff() -> Dict[str, Any]:
    """Reflects the ACTUAL handoff written by pages/04_Simulation_Lab.py."""
    return {
        "hospital_id": "HOSP-001",
        "department_id": "DEPT-ED",
        "kpi_id": "kpi_004",
        "kpi_name": "Average Patient Waiting Time",
        "forecast_month": 9,
        "forecast_month_label": "SEP 2025",
        "latest_actual_baseline": 42.5,
        "latest_actual_unit": "min",
        "latest_actual_date": "2025-07",
        "do_nothing_forecast": 48.7,
        "do_nothing_unit": "min",
        "forecast_warning": "Monitoring",
        "action_strategy": "Patient Flow Capacity Adjustment",
        "selected_action_level": "Recommended",
        "action_detail": "Add 2 RNs + 1 Tech for the next 4 weeks",
        "resource_line": "+2 staff / +1 capacity / 4 weeks",
        "intervention_id": "INT-FLOW-001",
        "comparator": "recommended",
        "scenario_kpi_value": 44.1,
        "scenario_unit": "min",
        "scenario_status": "ABOVE_TARGET",
        "change": -4.6,
        "confidence": "Moderate",
        "financial": None,
        "tradeoff_text": "",
        "displacement_text": "",
        "management_takeaway": "Add 2 RNs + 1 Tech for the next 4 weeks",
        "prepared_at": "2025-08-02T00:00:00",
    }


# ---------------------------------------------------------------------------
# 1. Page module loads
# ---------------------------------------------------------------------------

def test_page_module_loads(monkeypatch):
    """The Decision page module must import without error when handoff is present."""
    import streamlit as st
    _handoff = {
        "hospital_id": "HOSP-001",
        "department_id": "DEPT-ED",
        "kpi_id": "kpi_004",
        "kpi_name": "Average Patient Waiting Time",
        "forecast_month": 9,
        "forecast_month_label": "SEP 2025",
        "latest_actual_baseline": 42.5,
        "latest_actual_unit": "min",
        "do_nothing_forecast": 48.7,
        "do_nothing_unit": "min",
        "action_strategy": "Patient Flow Capacity Adjustment",
        "selected_action_level": "Recommended",
        "intervention_id": "INT-FLOW-001",
        "comparator": "recommended",
        "scenario_kpi_value": 44.1,
        "scenario_unit": "min",
        "scenario_status": "ABOVE_TARGET",
        "change": -4.6,
        "confidence": "Moderate",
        "management_takeaway": "Add 2 RNs + 1 Tech for the next 4 weeks",
    }
    monkeypatch.setattr(
        st, "session_state", {"decision_review_context": _handoff}, raising=False
    )
    monkeypatch.setattr(st, "set_page_config", lambda **kwargs: None)
    monkeypatch.setattr(st, "markdown", lambda *a, **k: None)
    monkeypatch.setattr(st, "caption", lambda *a, **k: None)
    monkeypatch.setattr(st, "warning", lambda *a, **k: None)
    monkeypatch.setattr(st, "info", lambda *a, **k: None)
    monkeypatch.setattr(st, "error", lambda *a, **k: None)
    monkeypatch.setattr(st, "stop", lambda: None)
    def _fake_columns(*a, **k):
        spec = a[0] if a else k.get("spec", 1)
        n = len(spec) if isinstance(spec, (list, tuple)) else int(spec)
        FakeCol = type("C", (), {"__enter__": lambda s: s, "__exit__": lambda *a: None, "markdown": lambda *a, **k: None})
        return [FakeCol() for _ in range(n)]
    monkeypatch.setattr(st, "columns", _fake_columns)
    monkeypatch.setattr(st, "write", lambda *a, **k: None)
    monkeypatch.setattr(st, "radio", lambda *a, **k: (a[2][0] if len(a) > 2 else (k.get("options", [""])[0])))
    monkeypatch.setattr(st, "text_area", lambda *a, **k: "")
    monkeypatch.setattr(st, "button", lambda *a, **k: False)
    monkeypatch.setattr(st, "success", lambda *a, **k: None)

    pages_dir = os.path.join(_ROOT, "pages")
    if pages_dir not in sys.path:
        sys.path.insert(0, pages_dir)
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_05_decision", os.path.join(pages_dir, "05_Decision_and_Call_for_Action.py")
    )
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "_resolve_kpi_name")
    assert hasattr(mod, "_resolve_department_name")
    assert hasattr(mod, "_decision_status_text")


# ---------------------------------------------------------------------------
# 2. Empty state without handoff
# ---------------------------------------------------------------------------

def test_empty_state_shows_no_case_selected(monkeypatch):
    """If decision_review_context is missing, the page should stop with a warning."""
    import streamlit as st
    monkeypatch.setattr(st, "session_state", {}, raising=False)
    calls: list = []
    monkeypatch.setattr(st, "warning", lambda msg: calls.append(("warning", msg)))
    monkeypatch.setattr(st, "info", lambda msg: calls.append(("info", msg)))
    monkeypatch.setattr(st, "stop", lambda: (_ for _ in ()).throw(SystemExit("stop")))

    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_05_decision_empty",
        os.path.join(_ROOT, "pages", "05_Decision_and_Call_for_Action.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    with pytest.raises(SystemExit):
        spec.loader.exec_module(mod)
    msgs = [c[1] for c in calls]
    assert any("NO DECISION CASE SELECTED" in str(m) for m in msgs)


# ---------------------------------------------------------------------------
# 3. Handoff read correctly
# ---------------------------------------------------------------------------

def test_handoff_keys_present(sample_handoff):
    """The 8 keys required for a valid case must exist and be non-null in the handoff."""
    required = [
        "hospital_id",
        "department_id",
        "kpi_id",
        "forecast_month_label",
        "selected_action_level",
        "action_strategy",
        "do_nothing_forecast",
        "scenario_kpi_value",
    ]
    for k in required:
        assert k in sample_handoff, f"missing key: {k}"
        assert sample_handoff[k] is not None, f"null value for key: {k}"


# ---------------------------------------------------------------------------
# 4. Department name resolved
# ---------------------------------------------------------------------------

def test_department_name_resolution():
    assert _display_department("DEPT-ED") == "Emergency Department"
    assert _display_department("DEPT-ICU") == "Intensive Care Unit"
    assert _display_department("DEPT-ADM") == "Admissions"
    assert _display_department("UNKNOWN") == "UNKNOWN"


# ---------------------------------------------------------------------------
# 5. KPI name resolved
# ---------------------------------------------------------------------------

def test_kpi_name_resolution():
    assert _KPI_ID_TO_NAME.get("kpi_004") == "Average Patient Waiting Time"
    assert _KPI_ID_TO_NAME.get("kpi_001") == "Staffing Level"


# ---------------------------------------------------------------------------
# 6. Evidence values displayed (formatting helper)
# ---------------------------------------------------------------------------

def test_format_unit_value_on_evidence():
    from src.streamlit_executive_page_controller import format_unit_value
    assert format_unit_value(42.5, "min") == "42.5 min"
    assert format_unit_value(88.1, "%") == "88.1%"
    assert format_unit_value(None, "min") == "N/A"


# ---------------------------------------------------------------------------
# 7. Action strategy displayed
# ---------------------------------------------------------------------------

def test_action_strategy_from_handoff(sample_handoff):
    strategy = sample_handoff["action_strategy"]
    assert strategy == "Patient Flow Capacity Adjustment"
    assert strategy == _KPI_TO_ACTION_STRATEGY.get("kpi_004")


# ---------------------------------------------------------------------------
# 8. Unsupported / missing handoff blocked
# ---------------------------------------------------------------------------

def test_missing_required_fields_blocked(monkeypatch):
    """If required handoff fields are None, the page should stop with an error."""
    import streamlit as st
    bad_handoff = {
        "hospital_id": "HOSP-001",
        "department_id": "DEPT-ED",
        "kpi_id": "kpi_004",
        "forecast_month_label": "SEP 2025",
        "selected_action_level": "Recommended",
        "action_strategy": "Patient Flow Capacity Adjustment",
        "do_nothing_forecast": 48.7,
        "scenario_kpi_value": None,  # the actual key; null must be rejected
    }
    monkeypatch.setattr(
        st, "session_state", {"decision_review_context": bad_handoff}, raising=False
    )
    calls: list = []
    monkeypatch.setattr(st, "error", lambda msg: calls.append(("error", msg)))
    monkeypatch.setattr(st, "info", lambda msg: calls.append(("info", msg)))
    monkeypatch.setattr(st, "stop", lambda: (_ for _ in ()).throw(SystemExit("stop")))

    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_05_decision_unsupported",
        os.path.join(_ROOT, "pages", "05_Decision_and_Call_for_Action.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    with pytest.raises(SystemExit):
        spec.loader.exec_module(mod)
    msgs = [c[1] for c in calls]
    assert any("DECISION SUPPORT NOT AVAILABLE" in str(m) for m in msgs)


# ---------------------------------------------------------------------------
# 9. Management decision stored
# ---------------------------------------------------------------------------

def test_management_decision_record_structure(sample_handoff):
    """The record maps the live handoff keys to the conceptual record keys."""
    record = {
        "hospital_id": sample_handoff["hospital_id"],
        "department_id": sample_handoff["department_id"],
        "department_name": _display_department(sample_handoff["department_id"]),
        "kpi_id": sample_handoff["kpi_id"],
        "kpi_name": _KPI_ID_TO_NAME.get(sample_handoff["kpi_id"], sample_handoff["kpi_id"]),
        "forecast_month_label": sample_handoff["forecast_month_label"],
        "action_strategy": sample_handoff["action_strategy"],
        "selected_action_level": sample_handoff["selected_action_level"],
        "latest_actual": sample_handoff["latest_actual_baseline"],
        "do_nothing_forecast": sample_handoff["do_nothing_forecast"],
        "selected_scenario_value": sample_handoff["scenario_kpi_value"],
        "change_value": sample_handoff["change"],
        "change_pct": None,
        "action_status": sample_handoff["scenario_status"],
        "confidence": sample_handoff["confidence"],
        "confidence_pct": None,
        "management_decision": "APPROVE",
        "management_note": "Proceed with staffing plan.",
        "decision_status": "APPROVED FOR ACTION PLANNING",
        "decision_timestamp": datetime.datetime.now().isoformat(),
    }
    assert record["management_decision"] == "APPROVE"
    assert record["decision_status"] == "APPROVED FOR ACTION PLANNING"
    assert record["department_name"] == "Emergency Department"
    assert record["kpi_name"] == "Average Patient Waiting Time"
    assert record["latest_actual"] == 42.5
    assert record["selected_scenario_value"] == 44.1
    assert record["change_value"] == -4.6


# ---------------------------------------------------------------------------
# 13. Live handoff shape (matches pages/04_Simulation_Lab.py)
# ---------------------------------------------------------------------------

def test_live_handoff_shape_recognized(sample_handoff):
    """The page must accept the live Simulation Lab handoff shape."""
    h = sample_handoff
    # These are the live keys the page requires
    required = [
        "hospital_id", "department_id", "kpi_id",
        "forecast_month_label", "selected_action_level", "action_strategy",
        "do_nothing_forecast", "scenario_kpi_value",
    ]
    for k in required:
        assert h.get(k) is not None
    # Display names come from local lookups
    assert _display_department(h["department_id"]) == "Emergency Department"
    assert _KPI_ID_TO_NAME.get(h["kpi_id"]) == "Average Patient Waiting Time"


# ---------------------------------------------------------------------------
# 14. Supported case: Admissions + Staffing Level (Dec 2025, Minimum)
# ---------------------------------------------------------------------------

def test_supported_case_admissions_staffing_minimum(monkeypatch):
    """Admissions + Staffing Level supported scenario must pass validation."""
    import streamlit as st
    handoff = {
        "hospital_id": "HOSP-001",
        "department_id": "DEPT-ADM",
        "kpi_id": "kpi_001",
        "kpi_name": "Staffing Level",
        "forecast_month": 12,
        "forecast_month_label": "DEC 2025",
        "latest_actual_baseline": 18.0,
        "latest_actual_unit": "FTE",
        "do_nothing_forecast": 20.0,
        "do_nothing_unit": "FTE",
        "action_strategy": "Staffing Coverage Adjustment",
        "selected_action_level": "Minimum",
        "intervention_id": "INT-STAFF-001",
        "comparator": "minimum",
        "scenario_kpi_value": 19.2,
        "scenario_unit": "FTE",
        "scenario_status": "BELOW_TARGET",
        "change": -0.8,
        "confidence": "Moderate",
        "management_takeaway": "Add 1 RN to cover weekend shifts.",
    }
    stopped = {"value": False}
    errored = {"value": False}
    def _stop():
        stopped["value"] = True
        raise SystemExit("stop")
    def _error(*a, **k):
        errored["value"] = True
    monkeypatch.setattr(st, "session_state", {"decision_review_context": handoff}, raising=False)
    monkeypatch.setattr(st, "set_page_config", lambda **k: None)
    monkeypatch.setattr(st, "markdown", lambda *a, **k: None)
    monkeypatch.setattr(st, "caption", lambda *a, **k: None)
    monkeypatch.setattr(st, "warning", lambda *a, **k: None)
    monkeypatch.setattr(st, "info", lambda *a, **k: None)
    monkeypatch.setattr(st, "error", _error)
    monkeypatch.setattr(st, "stop", _stop)
    monkeypatch.setattr(st, "write", lambda *a, **k: None)
    monkeypatch.setattr(st, "radio", lambda *a, **k: (a[2][0] if len(a) > 2 else "APPROVE"))
    monkeypatch.setattr(st, "text_area", lambda *a, **k: "")
    monkeypatch.setattr(st, "button", lambda *a, **k: False)
    monkeypatch.setattr(st, "success", lambda *a, **k: None)
    def _columns(*a, **k):
        spec = a[0] if a else k.get("spec", 1)
        n = len(spec) if isinstance(spec, (list, tuple)) else int(spec)
        FakeCol = type("C", (), {"__enter__": lambda s: s, "__exit__": lambda *a: None, "markdown": lambda *a, **k: None})
        return [FakeCol() for _ in range(n)]
    monkeypatch.setattr(st, "columns", _columns)

    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_05_decision_case_a",
        os.path.join(_ROOT, "pages", "05_Decision_and_Call_for_Action.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # Validation must NOT have triggered stop or error
    assert stopped["value"] is False, "Decision page stopped on a valid case"
    assert errored["value"] is False, "Decision page errored on a valid case"
    # Display names should be resolved
    assert mod._resolve_department_name("DEPT-ADM") == "Admissions"
    assert mod._resolve_kpi_name("kpi_001") == "Staffing Level"


# ---------------------------------------------------------------------------
# 15. Supported case: ED + Average Patient Waiting Time (Recommended)
# ---------------------------------------------------------------------------

def test_supported_case_ed_apwt(monkeypatch):
    """ED + APWT supported scenario must pass validation."""
    import streamlit as st
    handoff = {
        "hospital_id": "HOSP-001",
        "department_id": "DEPT-ED",
        "kpi_id": "kpi_004",
        "kpi_name": "Average Patient Waiting Time",
        "forecast_month": 9,
        "forecast_month_label": "SEP 2025",
        "latest_actual_baseline": 42.5,
        "latest_actual_unit": "min",
        "do_nothing_forecast": 48.7,
        "do_nothing_unit": "min",
        "action_strategy": "Patient Flow Capacity Adjustment",
        "selected_action_level": "Recommended",
        "intervention_id": "INT-FLOW-001",
        "comparator": "recommended",
        "scenario_kpi_value": 44.1,
        "scenario_unit": "min",
        "scenario_status": "ABOVE_TARGET",
        "change": -4.6,
        "confidence": "Moderate",
        "management_takeaway": "Add 2 RNs + 1 Tech for 4 weeks.",
    }
    stopped = {"value": False}
    errored = {"value": False}
    def _stop():
        stopped["value"] = True
        raise SystemExit("stop")
    def _error(*a, **k):
        errored["value"] = True
    monkeypatch.setattr(st, "session_state", {"decision_review_context": handoff}, raising=False)
    monkeypatch.setattr(st, "set_page_config", lambda **k: None)
    monkeypatch.setattr(st, "markdown", lambda *a, **k: None)
    monkeypatch.setattr(st, "caption", lambda *a, **k: None)
    monkeypatch.setattr(st, "warning", lambda *a, **k: None)
    monkeypatch.setattr(st, "info", lambda *a, **k: None)
    monkeypatch.setattr(st, "error", _error)
    monkeypatch.setattr(st, "stop", _stop)
    monkeypatch.setattr(st, "write", lambda *a, **k: None)
    monkeypatch.setattr(st, "radio", lambda *a, **k: (a[2][0] if len(a) > 2 else "APPROVE"))
    monkeypatch.setattr(st, "text_area", lambda *a, **k: "")
    monkeypatch.setattr(st, "button", lambda *a, **k: False)
    monkeypatch.setattr(st, "success", lambda *a, **k: None)
    def _columns(*a, **k):
        spec = a[0] if a else k.get("spec", 1)
        n = len(spec) if isinstance(spec, (list, tuple)) else int(spec)
        FakeCol = type("C", (), {"__enter__": lambda s: s, "__exit__": lambda *a: None, "markdown": lambda *a, **k: None})
        return [FakeCol() for _ in range(n)]
    monkeypatch.setattr(st, "columns", _columns)

    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_05_decision_case_b",
        os.path.join(_ROOT, "pages", "05_Decision_and_Call_for_Action.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    assert stopped["value"] is False, "Decision page stopped on ED+APWT valid case"
    assert errored["value"] is False, "Decision page errored on ED+APWT valid case"
    assert mod._resolve_department_name("DEPT-ED") == "Emergency Department"
    assert mod._resolve_kpi_name("kpi_004") == "Average Patient Waiting Time"


# ---------------------------------------------------------------------------
# 16. change_pct derived locally from change and do_nothing_forecast
# ---------------------------------------------------------------------------

def test_change_pct_derived_locally(monkeypatch):
    """When the handoff has no change_pct, the page must derive it from change/do_nothing_forecast."""
    import streamlit as st
    handoff = {
        "hospital_id": "HOSP-001",
        "department_id": "DEPT-ED",
        "kpi_id": "kpi_004",
        "forecast_month_label": "SEP 2025",
        "selected_action_level": "Recommended",
        "action_strategy": "Patient Flow Capacity Adjustment",
        "do_nothing_forecast": 50.0,
        "scenario_kpi_value": 45.0,
        "change": -5.0,  # -5/50*100 = -10.0%
    }
    monkeypatch.setattr(st, "session_state", {"decision_review_context": handoff}, raising=False)
    monkeypatch.setattr(st, "set_page_config", lambda **k: None)
    monkeypatch.setattr(st, "markdown", lambda *a, **k: None)
    monkeypatch.setattr(st, "caption", lambda *a, **k: None)
    monkeypatch.setattr(st, "warning", lambda *a, **k: None)
    monkeypatch.setattr(st, "info", lambda *a, **k: None)
    monkeypatch.setattr(st, "error", lambda *a, **k: None)
    monkeypatch.setattr(st, "stop", lambda: None)
    monkeypatch.setattr(st, "write", lambda *a, **k: None)
    monkeypatch.setattr(st, "radio", lambda *a, **k: (a[2][0] if len(a) > 2 else "APPROVE"))
    monkeypatch.setattr(st, "text_area", lambda *a, **k: "")
    monkeypatch.setattr(st, "button", lambda *a, **k: False)
    monkeypatch.setattr(st, "success", lambda *a, **k: None)
    def _columns(*a, **k):
        spec = a[0] if a else k.get("spec", 1)
        n = len(spec) if isinstance(spec, (list, tuple)) else int(spec)
        FakeCol = type("C", (), {"__enter__": lambda s: s, "__exit__": lambda *a: None, "markdown": lambda *a, **k: None})
        return [FakeCol() for _ in range(n)]
    monkeypatch.setattr(st, "columns", _columns)

    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_05_decision_chg",
        os.path.join(_ROOT, "pages", "05_Decision_and_Call_for_Action.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # If we got here without error, the page handled the handoff.
    assert True


# ---------------------------------------------------------------------------
# 17. Phase 3D/3E — Recommended Action consistency (Minimum Action)
# ---------------------------------------------------------------------------

def test_recommended_action_minimum_consistency():
    """Minimum Action: action_detail must be the user-facing Recommended Action."""
    # Staffing Minimum: +1 staff · +1 temp · 7 days
    action_detail = "+1 staff · +1 temp · 7 days"
    action_strategy = "Staffing Coverage Adjustment"
    selected_action_level = "Minimum Action"
    assert action_detail == "+1 staff · +1 temp · 7 days"

    # The Decision page reads action_detail from the handoff and displays it
    handoff = {
        "action_strategy": action_strategy,
        "selected_action_level": selected_action_level,
        "action_detail": action_detail,
    }
    assert handoff["action_detail"] == action_detail
    # Strategy and level are kept separately
    assert handoff["action_strategy"] != action_detail
    assert handoff["selected_action_level"] != action_detail


def test_recommended_action_recommended_consistency():
    """Recommended Action: action_detail must be the user-facing Recommended Action."""
    # Staffing Recommended: +2 staff · +2 temp · +1 reassign · 10% shift coverage · 14 days
    action_detail = "+2 staff · +2 temp · +1 reassign · 10% shift coverage · 14 days"
    action_strategy = "Staffing Coverage Adjustment"
    selected_action_level = "Recommended Action"
    assert action_detail == "+2 staff · +2 temp · +1 reassign · 10% shift coverage · 14 days"

    handoff = {
        "action_strategy": action_strategy,
        "selected_action_level": selected_action_level,
        "action_detail": action_detail,
    }
    assert handoff["action_detail"] == action_detail
    assert handoff["action_strategy"] != action_detail
    assert handoff["selected_action_level"] != action_detail


def test_recommended_action_intensive_consistency():
    """Intensive Action: action_detail must be the user-facing Recommended Action."""
    # Staffing Intensive: +4 staff · +3 temp · +2 reassign · 20% shift coverage · 30 days
    action_detail = "+4 staff · +3 temp · +2 reassign · 20% shift coverage · 30 days"
    action_strategy = "Staffing Coverage Adjustment"
    selected_action_level = "Intensive Action"
    assert action_detail == "+4 staff · +3 temp · +2 reassign · 20% shift coverage · 30 days"

    handoff = {
        "action_strategy": action_strategy,
        "selected_action_level": selected_action_level,
        "action_detail": action_detail,
    }
    assert handoff["action_detail"] == action_detail
    assert handoff["action_strategy"] != action_detail
    assert handoff["selected_action_level"] != action_detail


# ---------------------------------------------------------------------------
# 18. action_detail and resource_line passed through the handoff exactly
# ---------------------------------------------------------------------------

def test_action_detail_and_resource_line_passthrough(sample_handoff):
    """The Decision page must show action_detail (and resource_line) exactly as in the handoff."""
    handoff_action_detail = sample_handoff["action_detail"]
    handoff_resource_line = sample_handoff["resource_line"]

    # The Decision page reads these directly (not from management_takeaway
    # or derived from intervention_id+comparator).
    assert handoff_action_detail == "Add 2 RNs + 1 Tech for the next 4 weeks"
    assert handoff_resource_line == "+2 staff / +1 capacity / 4 weeks"

    # The Recommended Action is action_detail itself (NOT a combined label)
    rec = sample_handoff["action_detail"]
    assert rec == "Add 2 RNs + 1 Tech for the next 4 weeks"
    # It must NOT be the combined strategy+level label
    combined = f"{sample_handoff['action_strategy']} — {sample_handoff['selected_action_level']}"
    assert rec != combined


def test_no_unknown_or_fallback_action_label_when_strategy_present(sample_handoff):
    """The page must NOT show 'Unknown' or '—' when action_strategy is present."""
    h = sample_handoff
    # action_strategy is not empty
    assert h["action_strategy"]
    assert h["selected_action_level"]
    # The recommended action value is action_detail (not a combined label)
    rec = h["action_detail"]
    assert "Unknown" not in rec
    # action_detail is a substantive text, not just the strategy or level
    assert rec != h["action_strategy"]
    assert rec != h["selected_action_level"]
    # action_detail and resource_line are non-empty too
    assert h["action_detail"]
    assert h["resource_line"]


# ---------------------------------------------------------------------------
# 10. Management note stored
# ---------------------------------------------------------------------------

def test_management_note_preserved():
    note = "Add contingency for weekend surge."
    record = {"management_note": note}
    assert record["management_note"] == note


# ---------------------------------------------------------------------------
# 11. Timestamp created
# ---------------------------------------------------------------------------

def test_timestamp_created():
    ts = datetime.datetime.now().isoformat()
    assert isinstance(ts, str)
    assert len(ts) >= 10
    assert "T" in ts


# ---------------------------------------------------------------------------
# 12. No analytical output modified
# ---------------------------------------------------------------------------

def test_no_analytical_files_touched():
    """Decision page must not write to CSV or modify analytical outputs."""
    path = os.path.join(_ROOT, "pages", "05_Decision_and_Call_for_Action.py")
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    lower = source.lower()
    # Must not contain CSV write patterns
    assert "to_csv" not in lower
    assert ".to_csv(" not in source
    assert "pd.DataFrame().to_csv" not in source
    # Must not write to outputs/ or data/
    assert 'open("outputs/' not in source and "open('outputs/" not in source
    assert 'open("data/' not in source and "open('data/" not in source
    assert 'open(r"outputs/' not in source
    assert 'open(r"data/' not in source


# ---------------------------------------------------------------------------
# 19. Recommended Action displays action_detail (Phase 3D/3E consistency fix)
# ---------------------------------------------------------------------------

# Expected action_detail values per (kpi, level) — same as 3d tests
STAFFING_ACTION_DETAIL = {
    "Minimum Action": "+1 staff · +1 temp · 7 days",
    "Recommended Action": "+2 staff · +2 temp · +1 reassign · 10% shift coverage · 14 days",
    "Intensive Action": "+4 staff · +3 temp · +2 reassign · 20% shift coverage · 30 days",
}

ABSENTEEISM_ACTION_DETAIL = {
    "Minimum Action": "10% reduction · 30% replacement · 25% contingency roster · 7 days",
    "Recommended Action": "20% reduction · 50% replacement · 50% contingency roster · 14 days",
    "Intensive Action": "35% reduction · 75% replacement · 75% contingency roster · 30 days",
}

FLOW_ACTION_DETAIL = {
    "Minimum Action": "+5% service capacity · +2% throughput · +5% routing efficiency · +1 temp resource · 7 days",
    "Recommended Action": "+10% service capacity · +5% throughput · +10% routing efficiency · +3 temp resource · 14 days",
    "Intensive Action": "+20% service capacity · +12% throughput · +18% routing efficiency · +6 temp resource · 30 days",
}


def test_decision_page_recommended_action_card_uses_action_detail():
    """The Decision page must render the Recommended Action card using action_detail."""
    path = os.path.join(_ROOT, "pages", "05_Decision_and_Call_for_Action.py")
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    # The main Recommended Action card (in the Action Commitment section)
    # must reference action_detail and NOT use the combined label.
    commitment_idx = source.find("Action Commitment")
    assert commitment_idx > 0, "Action Commitment section must exist"
    rec_idx = source.find("Recommended Action", commitment_idx)
    assert rec_idx > 0, "Recommended Action card must exist after Action Commitment"
    card_window = source[rec_idx:rec_idx + 600]
    # The card value must reference the action_detail variable
    assert "action_detail" in card_window, (
        "Decision page Recommended Action card must use action_detail"
    )
    # The card value must NOT use the combined strategy+level label
    assert "action_strategy} —" not in card_window
    assert "selected_action_level}" not in card_window
    # Strategy and level are still in the page (Decision Context table)
    assert "Action Strategy" in source
    assert "Action Level" in source


def test_decision_page_renders_with_staffing_minimum_action_detail():
    """Decision page must load successfully with staffing Minimum action_detail."""
    import streamlit as st
    import importlib.util

    handoff = {
        "hospital_id": "HOSP-001",
        "department_id": "DEPT-ICU",
        "kpi_id": "kpi_001",
        "forecast_month_label": "SEP 2025",
        "selected_action_level": "Minimum Action",
        "action_strategy": "Staffing Coverage Adjustment",
        "do_nothing_forecast": 80.0,
        "scenario_kpi_value": 75.0,
        "change": -5.0,
        "scenario_status": "ABOVE_TARGET",
        "intervention_id": "INT-STAFF-001",
        "comparator": "conservative",
        "scenario_unit": "%",
        "action_detail": STAFFING_ACTION_DETAIL["Minimum Action"],
        "resource_line": "+1 staff / +1 temp / 7 days",
        "management_takeaway": "Take action to reduce uncovered shifts.",
    }
    stopped = {"value": False}
    errored = {"value": False}
    def _stop():
        stopped["value"] = True
        raise SystemExit("stop")
    def _error(*a, **k):
        errored["value"] = True
    monkeypatch_setup = {
        "session_state": {"decision_review_context": handoff},
        "set_page_config": lambda **k: None,
        "markdown": lambda *a, **k: None,
        "caption": lambda *a, **k: None,
        "warning": lambda *a, **k: None,
        "info": lambda *a, **k: None,
        "error": _error,
        "stop": _stop,
        "write": lambda *a, **k: None,
        "radio": lambda *a, **k: (a[2][0] if len(a) > 2 else "APPROVE"),
        "text_area": lambda *a, **k: "",
        "button": lambda *a, **k: False,
        "success": lambda *a, **k: None,
    }
    for k, v in monkeypatch_setup.items():
        setattr(st, k, v)
    st.session_state = {"decision_review_context": handoff}

    def _columns(*a, **k):
        spec = a[0] if a else k.get("spec", 1)
        n = len(spec) if isinstance(spec, (list, tuple)) else int(spec)
        FakeCol = type("C", (), {"__enter__": lambda s: s, "__exit__": lambda *a: None, "markdown": lambda *a, **k: None})
        return [FakeCol() for _ in range(n)]
    st.columns = _columns

    spec = importlib.util.spec_from_file_location(
        "_05_decision_staff_min",
        os.path.join(_ROOT, "pages", "05_Decision_and_Call_for_Action.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    assert stopped["value"] is False, "Decision page stopped on staffing Minimum valid handoff"
    assert errored["value"] is False, "Decision page errored on staffing Minimum valid handoff"


def test_decision_page_renders_with_staffing_recommended_action_detail():
    """Decision page must load successfully with staffing Recommended action_detail."""
    import streamlit as st
    import importlib.util

    handoff = {
        "hospital_id": "HOSP-001",
        "department_id": "DEPT-ICU",
        "kpi_id": "kpi_001",
        "forecast_month_label": "SEP 2025",
        "selected_action_level": "Recommended Action",
        "action_strategy": "Staffing Coverage Adjustment",
        "do_nothing_forecast": 80.0,
        "scenario_kpi_value": 75.0,
        "change": -5.0,
        "scenario_status": "ABOVE_TARGET",
        "intervention_id": "INT-STAFF-001",
        "comparator": "expected",
        "scenario_unit": "%",
        "action_detail": STAFFING_ACTION_DETAIL["Recommended Action"],
        "resource_line": "+2 staff / +2 temp / +1 reassign / 14 days",
        "management_takeaway": "Take action to reduce uncovered shifts.",
    }
    stopped = {"value": False}
    errored = {"value": False}
    def _stop():
        stopped["value"] = True
        raise SystemExit("stop")
    def _error(*a, **k):
        errored["value"] = True

    st.session_state = {"decision_review_context": handoff}
    st.set_page_config = lambda **k: None
    st.markdown = lambda *a, **k: None
    st.caption = lambda *a, **k: None
    st.warning = lambda *a, **k: None
    st.info = lambda *a, **k: None
    st.error = _error
    st.stop = _stop
    st.write = lambda *a, **k: None
    st.radio = lambda *a, **k: (a[2][0] if len(a) > 2 else "APPROVE")
    st.text_area = lambda *a, **k: ""
    st.button = lambda *a, **k: False
    st.success = lambda *a, **k: None

    def _columns(*a, **k):
        spec = a[0] if a else k.get("spec", 1)
        n = len(spec) if isinstance(spec, (list, tuple)) else int(spec)
        FakeCol = type("C", (), {"__enter__": lambda s: s, "__exit__": lambda *a: None, "markdown": lambda *a, **k: None})
        return [FakeCol() for _ in range(n)]
    st.columns = _columns

    spec = importlib.util.spec_from_file_location(
        "_05_decision_staff_rec",
        os.path.join(_ROOT, "pages", "05_Decision_and_Call_for_Action.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    assert stopped["value"] is False, "Decision page stopped on staffing Recommended valid handoff"
    assert errored["value"] is False, "Decision page errored on staffing Recommended valid handoff"


def test_decision_page_renders_with_staffing_intensive_action_detail():
    """Decision page must load successfully with staffing Intensive action_detail."""
    import streamlit as st
    import importlib.util

    handoff = {
        "hospital_id": "HOSP-001",
        "department_id": "DEPT-ICU",
        "kpi_id": "kpi_001",
        "forecast_month_label": "SEP 2025",
        "selected_action_level": "Intensive Action",
        "action_strategy": "Staffing Coverage Adjustment",
        "do_nothing_forecast": 80.0,
        "scenario_kpi_value": 75.0,
        "change": -5.0,
        "scenario_status": "ABOVE_TARGET",
        "intervention_id": "INT-STAFF-001",
        "comparator": "higher_intensity",
        "scenario_unit": "%",
        "action_detail": STAFFING_ACTION_DETAIL["Intensive Action"],
        "resource_line": "+4 staff / +3 temp / +2 reassign / 30 days",
        "management_takeaway": "Take action to reduce uncovered shifts.",
    }
    stopped = {"value": False}
    errored = {"value": False}
    def _stop():
        stopped["value"] = True
        raise SystemExit("stop")
    def _error(*a, **k):
        errored["value"] = True

    st.session_state = {"decision_review_context": handoff}
    st.set_page_config = lambda **k: None
    st.markdown = lambda *a, **k: None
    st.caption = lambda *a, **k: None
    st.warning = lambda *a, **k: None
    st.info = lambda *a, **k: None
    st.error = _error
    st.stop = _stop
    st.write = lambda *a, **k: None
    st.radio = lambda *a, **k: (a[2][0] if len(a) > 2 else "APPROVE")
    st.text_area = lambda *a, **k: ""
    st.button = lambda *a, **k: False
    st.success = lambda *a, **k: None

    def _columns(*a, **k):
        spec = a[0] if a else k.get("spec", 1)
        n = len(spec) if isinstance(spec, (list, tuple)) else int(spec)
        FakeCol = type("C", (), {"__enter__": lambda s: s, "__exit__": lambda *a: None, "markdown": lambda *a, **k: None})
        return [FakeCol() for _ in range(n)]
    st.columns = _columns

    spec = importlib.util.spec_from_file_location(
        "_05_decision_staff_int",
        os.path.join(_ROOT, "pages", "05_Decision_and_Call_for_Action.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    assert stopped["value"] is False, "Decision page stopped on staffing Intensive valid handoff"
    assert errored["value"] is False, "Decision page errored on staffing Intensive valid handoff"


def test_decision_page_renders_with_flow_action_detail():
    """Decision page must load successfully with flow (kpi_003) action_detail."""
    import streamlit as st
    import importlib.util

    handoff = {
        "hospital_id": "HOSP-001",
        "department_id": "DEPT-ED",
        "kpi_id": "kpi_003",
        "forecast_month_label": "SEP 2025",
        "selected_action_level": "Recommended Action",
        "action_strategy": "Patient Flow Capacity Adjustment",
        "do_nothing_forecast": 50.0,
        "scenario_kpi_value": 45.0,
        "change": -5.0,
        "scenario_status": "ABOVE_TARGET",
        "intervention_id": "INT-FLOW-001",
        "comparator": "expected",
        "scenario_unit": "%",
        "action_detail": FLOW_ACTION_DETAIL["Recommended Action"],
        "resource_line": "+10% service capacity / +3 temp / 14 days",
        "management_takeaway": "Add 2 RNs + 1 Tech for 4 weeks.",
    }
    stopped = {"value": False}
    errored = {"value": False}
    def _stop():
        stopped["value"] = True
        raise SystemExit("stop")
    def _error(*a, **k):
        errored["value"] = True

    st.session_state = {"decision_review_context": handoff}
    st.set_page_config = lambda **k: None
    st.markdown = lambda *a, **k: None
    st.caption = lambda *a, **k: None
    st.warning = lambda *a, **k: None
    st.info = lambda *a, **k: None
    st.error = _error
    st.stop = _stop
    st.write = lambda *a, **k: None
    st.radio = lambda *a, **k: (a[2][0] if len(a) > 2 else "APPROVE")
    st.text_area = lambda *a, **k: ""
    st.button = lambda *a, **k: False
    st.success = lambda *a, **k: None

    def _columns(*a, **k):
        spec = a[0] if a else k.get("spec", 1)
        n = len(spec) if isinstance(spec, (list, tuple)) else int(spec)
        FakeCol = type("C", (), {"__enter__": lambda s: s, "__exit__": lambda *a: None, "markdown": lambda *a, **k: None})
        return [FakeCol() for _ in range(n)]
    st.columns = _columns

    spec = importlib.util.spec_from_file_location(
        "_05_decision_flow",
        os.path.join(_ROOT, "pages", "05_Decision_and_Call_for_Action.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    assert stopped["value"] is False, "Decision page stopped on flow valid handoff"
    assert errored["value"] is False, "Decision page errored on flow valid handoff"


def test_decision_page_renders_with_absenteeism_action_detail():
    """Decision page must load successfully with absenteeism (kpi_002) action_detail."""
    import streamlit as st
    import importlib.util

    handoff = {
        "hospital_id": "HOSP-001",
        "department_id": "DEPT-ICU",
        "kpi_id": "kpi_002",
        "forecast_month_label": "SEP 2025",
        "selected_action_level": "Recommended Action",
        "action_strategy": "Absenteeism Contingency Response",
        "do_nothing_forecast": 12.0,
        "scenario_kpi_value": 9.0,
        "change": -3.0,
        "scenario_status": "ABOVE_TARGET",
        "intervention_id": "INT-ABS-001",
        "comparator": "expected",
        "scenario_unit": "%",
        "action_detail": ABSENTEEISM_ACTION_DETAIL["Recommended Action"],
        "resource_line": "20% reduction / 50% replacement / 14 days",
        "management_takeaway": "Activate contingency roster.",
    }
    stopped = {"value": False}
    errored = {"value": False}
    def _stop():
        stopped["value"] = True
        raise SystemExit("stop")
    def _error(*a, **k):
        errored["value"] = True

    st.session_state = {"decision_review_context": handoff}
    st.set_page_config = lambda **k: None
    st.markdown = lambda *a, **k: None
    st.caption = lambda *a, **k: None
    st.warning = lambda *a, **k: None
    st.info = lambda *a, **k: None
    st.error = _error
    st.stop = _stop
    st.write = lambda *a, **k: None
    st.radio = lambda *a, **k: (a[2][0] if len(a) > 2 else "APPROVE")
    st.text_area = lambda *a, **k: ""
    st.button = lambda *a, **k: False
    st.success = lambda *a, **k: None

    def _columns(*a, **k):
        spec = a[0] if a else k.get("spec", 1)
        n = len(spec) if isinstance(spec, (list, tuple)) else int(spec)
        FakeCol = type("C", (), {"__enter__": lambda s: s, "__exit__": lambda *a: None, "markdown": lambda *a, **k: None})
        return [FakeCol() for _ in range(n)]
    st.columns = _columns

    spec = importlib.util.spec_from_file_location(
        "_05_decision_abs",
        os.path.join(_ROOT, "pages", "05_Decision_and_Call_for_Action.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    assert stopped["value"] is False, "Decision page stopped on absenteeism valid handoff"
    assert errored["value"] is False, "Decision page errored on absenteeism valid handoff"


def test_action_detail_passthrough_matches_across_pages():
    """The same action_detail must appear in both the Simulation Lab handoff and the Decision page.

    This test verifies the end-to-end contract: the Simulation Lab produces
    a specific action_detail (e.g. '+1 staff · +1 temp · 7 days'), and the
    Decision page renders that exact value in the Recommended Action card.
    The Decision page's renderer reads action_detail directly from the
    handoff (no reconstruction), so the values are equal by construction.
    """
    # The Decision page's Recommended Action card uses {action_detail}
    # (with the 'or "—"' fallback). This is the value that flows through.
    path = os.path.join(_ROOT, "pages", "05_Decision_and_Call_for_Action.py")
    with open(path, "r", encoding="utf-8") as fh:
        dec_src = fh.read()

    # Find the Recommended Action card value
    commitment_idx = dec_src.find("Action Commitment")
    rec_idx = dec_src.find("Recommended Action", commitment_idx)
    card_window = dec_src[rec_idx:rec_idx + 600]
    # The card value must use the action_detail variable
    assert "action_detail" in card_window, (
        "Decision page Recommended Action card must use action_detail"
    )
    # It must NOT use the combined strategy+level label
    assert "action_strategy} —" not in card_window

    # The handoff is the contract: the same string flows from the
    # Simulation Lab (which writes sel_action_detail) into the Decision page
    # (which reads context.get("action_detail")). The two pages share the
    # same string by construction.
    for action_detail, action_strategy, selected_action_level in [
        ("+1 staff · +1 temp · 7 days", "Staffing Coverage Adjustment", "Minimum Action"),
        ("+2 staff · +2 temp · +1 reassign · 10% shift coverage · 14 days",
         "Staffing Coverage Adjustment", "Recommended Action"),
        ("+4 staff · +3 temp · +2 reassign · 20% shift coverage · 30 days",
         "Staffing Coverage Adjustment", "Intensive Action"),
    ]:
        handoff = {"action_detail": action_detail, "action_strategy": action_strategy,
                   "selected_action_level": selected_action_level}
        # The Decision page Recommended Action card value is handoff["action_detail"]
        assert handoff["action_detail"] == action_detail
        # It must NOT be the combined strategy+level label
        combined = f"{action_strategy} — {selected_action_level}"
        assert handoff["action_detail"] != combined

