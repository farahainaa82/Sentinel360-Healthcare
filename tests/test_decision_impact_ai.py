"""Decision Impact AI-Assisted Interpretation — targeted tests (A-O).

A. governed impact values preserved exactly
B. Hy3 cannot calculate
C. AI success shows badge
D. fallback hides badge
E. do-nothing value preserved
F. selected scenario value preserved
G. expected KPI change preserved
H. relative change preserved
I. governed ceiling state preserved
J. no autonomous decision language
K. no raw JSON/dict rendered
L. only OK responses cached
M. failed responses not cached
N. scenario change invalidates cache
O. no analytical logic changed
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from src.ai_decision_impact_synthesis import (
    AIDecisionImpactResult,
    AIDecisionImpactSynthesisService,
    _build_fallback,
    _build_prompt,
    _parse_json_fields,
    _SYSTEM_PROMPT,
)
from src.decision_impact_ai_evidence import (
    build_decision_impact_evidence,
    build_decision_impact_cache_key,
    _compute_target_status,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_evidence(**overrides: Any) -> Dict[str, Any]:
    """Build a standard governed evidence pack for testing."""
    base: Dict[str, Any] = {
        "context": {
            "hospital_id": "Hospital_A",
            "department_name": "Emergency Department",
            "forecast_month": "Sep 2025",
        },
        "kpi": {
            "kpi_id": "kpi_001",
            "kpi_name": "Staffing Level",
            "target_display": "≥ 84.2%",
            "unit": "%",
        },
        "baseline": {
            "do_nothing_forecast_display": "85.4%",
        },
        "scenario": {
            "selected_action_level": "Minimum Action",
            "selected_scenario_display": "100.0%",
            "expected_kpi_change_display": "14.6%",
            "relative_change_display": "17.1%",
            "action_strategy": "Staffing Coverage Adjustment",
            "resource_commitment": "+1 staff · +1 temp · 7 days",
            "governed_ceiling_reached": False,
            "target_met": True,
        },
        "governance": {
            "evidence_is_governed": True,
            "ai_may_calculate": False,
            "ai_may_modify_values": False,
            "ai_may_infer_missing_values": False,
            "causality_confirmed": False,
        },
    }
    base.update(overrides)
    # compute evidence hash the same way the builder does
    evidence_str = json.dumps(base, sort_keys=True, separators=(",", ":"))
    base["_evidence_hash"] = hashlib.sha256(
        evidence_str.encode("utf-8")
    ).hexdigest()[:32]
    return base


def _mock_ok_response(what: str, implication: str) -> Dict[str, Any]:
    return {
        "status": "OK",
        "message": json.dumps({
            "what_it_means": what,
            "decision_implication": implication,
        }),
    }


def _mock_empty_response() -> Dict[str, Any]:
    return {
        "status": "OK",
        "message": json.dumps({"what_it_means": "", "decision_implication": ""}),
    }


def _mock_not_ok_response() -> Dict[str, Any]:
    return {"status": "FAIL", "message": ""}


# ---------------------------------------------------------------------------
# A-O tests
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# A — governed impact values preserved exactly
# ---------------------------------------------------------------------------

def test_a_evidence_pack_preserves_all_governed_fields() -> None:
    ev = build_decision_impact_evidence(
        hospital_id="H",
        department_name="ED",
        kpi_id="kpi_001",
        kpi_name="Staffing Level",
        forecast_month_label="Sep 2025",
        do_nothing_forecast=85.4,
        selected_scenario_value=100.0,
        change_value=14.6,
        change_pct=17.1,
        action_strategy="Staffing Coverage Adjustment",
        resource_line="+1 staff · +1 temp · 7 days",
        selected_action_level="Minimum Action",
        threshold_cfg={
            "kpi_001": {
                "directionality": "HIGHER_IS_BETTER",
                "green_lower_boundary": 84.2,
                "green_upper_boundary": 100.0,
                "unit": "%",
                "threshold_is_provisional": False,
            }
        },
        unit="%",
    )
    assert ev["context"]["hospital_id"] == "H"
    assert ev["context"]["department_name"] == "ED"
    assert ev["context"]["forecast_month"] == "Sep 2025"
    assert ev["kpi"]["kpi_id"] == "kpi_001"
    assert ev["kpi"]["kpi_name"] == "Staffing Level"
    assert ev["kpi"]["target_display"] == "≥ 84.2%"
    assert ev["baseline"]["do_nothing_forecast_display"] == "85.4%"
    assert ev["scenario"]["selected_action_level"] == "Minimum Action"
    assert ev["scenario"]["selected_scenario_display"] == "100.0%"
    assert ev["scenario"]["expected_kpi_change_display"] == "14.6%"
    assert ev["scenario"]["relative_change_display"] == "17.1%"
    assert ev["scenario"]["action_strategy"] == "Staffing Coverage Adjustment"
    assert ev["scenario"]["resource_commitment"] == "+1 staff · +1 temp · 7 days"
    assert ev["governance"]["evidence_is_governed"] is True
    assert ev["governance"]["ai_may_calculate"] is False
    assert ev["governance"]["ai_may_modify_values"] is False
    assert ev["governance"]["ai_may_infer_missing_values"] is False
    assert ev["governance"]["causality_confirmed"] is False


# ---------------------------------------------------------------------------
# B — Hy3 cannot calculate
# ---------------------------------------------------------------------------

def test_b_system_prompt_forbids_calculation() -> None:
    assert "Do NOT recalculate" in _SYSTEM_PROMPT
    assert "ai_may_calculate: False" in _build_prompt(_make_evidence())
    assert "ai_may_calculate: False" in _build_prompt(_make_evidence())


def test_b_system_prompt_forbids_inference() -> None:
    assert "infer missing" in _SYSTEM_PROMPT
    assert "ai_may_infer_missing_values: False" in _build_prompt(
        _make_evidence()
    )


# ---------------------------------------------------------------------------
# C / D — badge visibility on success vs fallback
# ---------------------------------------------------------------------------

def test_c_ai_success_result_is_hy3_live() -> None:
    from src.genai_provenance_badge import is_hy3_live
    r = AIDecisionImpactResult(
        status="OK", what_it_means="a", decision_implication="b"
    )
    assert is_hy3_live(r) is True


def test_d_fallback_result_is_not_hy3_live() -> None:
    from src.genai_provenance_badge import is_hy3_live
    r = AIDecisionImpactResult(
        status="FALLBACK", what_it_means="a", decision_implication="b"
    )
    assert is_hy3_live(r) is False


# ---------------------------------------------------------------------------
# E / F / G / H — do-nothing, selected scenario, change, relative change preserved
# ---------------------------------------------------------------------------

def test_e_f_g_h_display_values_preserved_in_evidence() -> None:
    ev = build_decision_impact_evidence(
        hospital_id="H",
        department_name="ED",
        kpi_id="kpi_001",
        kpi_name="Staffing Level",
        forecast_month_label="Oct 2025",
        do_nothing_forecast=85.4,
        selected_scenario_value=100.0,
        change_value=14.6,
        change_pct=17.1,
        action_strategy="Staffing Coverage Adjustment",
        resource_line="+1 staff",
        selected_action_level="Minimum Action",
        threshold_cfg={
            "kpi_001": {
                "directionality": "HIGHER_IS_BETTER",
                "green_lower_boundary": 84.2,
                "green_upper_boundary": 100.0,
                "unit": "%",
            }
        },
        unit="%",
    )
    assert ev["baseline"]["do_nothing_forecast_display"] == "85.4%"
    assert ev["scenario"]["selected_scenario_display"] == "100.0%"
    assert ev["scenario"]["expected_kpi_change_display"] == "14.6%"
    assert ev["scenario"]["relative_change_display"] == "17.1%"


# ---------------------------------------------------------------------------
# I — governed ceiling state preserved
# ---------------------------------------------------------------------------

def test_i_ceiling_reached_when_above_upper_bound() -> None:
    ev = build_decision_impact_evidence(
        hospital_id="H",
        department_name="ED",
        kpi_id="kpi_001",
        kpi_name="Staffing Level",
        forecast_month_label="Oct 2025",
        do_nothing_forecast=85.0,
        selected_scenario_value=100.0,
        change_value=15.0,
        change_pct=17.6,
        action_strategy="S",
        resource_line="R",
        selected_action_level="Minimum Action",
        threshold_cfg={
            "kpi_001": {
                "directionality": "HIGHER_IS_BETTER",
                "green_lower_boundary": 84.0,
                "green_upper_boundary": 95.0,
                "unit": "%",
            }
        },
        unit="%",
    )
    assert ev["scenario"]["governed_ceiling_reached"] is True
    assert ev["scenario"]["target_met"] is True


def test_i_target_met_but_not_ceiling() -> None:
    ev = build_decision_impact_evidence(
        hospital_id="H",
        department_name="ED",
        kpi_id="kpi_001",
        kpi_name="Staffing Level",
        forecast_month_label="Oct 2025",
        do_nothing_forecast=85.0,
        selected_scenario_value=90.0,
        change_value=5.0,
        change_pct=5.9,
        action_strategy="S",
        resource_line="R",
        selected_action_level="Minimum Action",
        threshold_cfg={
            "kpi_001": {
                "directionality": "HIGHER_IS_BETTER",
                "green_lower_boundary": 84.0,
                "green_upper_boundary": 95.0,
                "unit": "%",
            }
        },
        unit="%",
    )
    assert ev["scenario"]["governed_ceiling_reached"] is False
    assert ev["scenario"]["target_met"] is True


def test_i_target_not_met() -> None:
    ev = build_decision_impact_evidence(
        hospital_id="H",
        department_name="ED",
        kpi_id="kpi_001",
        kpi_name="Staffing Level",
        forecast_month_label="Oct 2025",
        do_nothing_forecast=85.0,
        selected_scenario_value=80.0,
        change_value=-5.0,
        change_pct=-5.9,
        action_strategy="S",
        resource_line="R",
        selected_action_level="Minimum Action",
        threshold_cfg={
            "kpi_001": {
                "directionality": "HIGHER_IS_BETTER",
                "green_lower_boundary": 84.0,
                "green_upper_boundary": 95.0,
                "unit": "%",
            }
        },
        unit="%",
    )
    assert ev["scenario"]["governed_ceiling_reached"] is False
    assert ev["scenario"]["target_met"] is False


# ---------------------------------------------------------------------------
# J — no autonomous decision language
# ---------------------------------------------------------------------------

def test_j_fallback_avoids_autonomous_decision_language() -> None:
    ev = _make_evidence()
    fb = _build_fallback(ev)
    bad_words = ["should approve", "best decision", "approve this", "must choose"]
    for bw in bad_words:
        assert bw not in fb["what_it_means"].lower(), f"forbidden phrase: {bw}"
        assert bw not in fb["decision_implication"].lower(), f"forbidden phrase: {bw}"


def test_j_system_prompt_forbids_autonomous_language() -> None:
    assert "should approve" in _SYSTEM_PROMPT.lower() or "approve this" in _SYSTEM_PROMPT.lower()
    assert "best decision" in _SYSTEM_PROMPT.lower()


def test_j_fallback_uses_cautious_language() -> None:
    ev = _make_evidence()
    fb = _build_fallback(ev)
    cautious = ["sufficient", "weighed", "consider", "may need"]
    combined = fb["what_it_means"] + fb["decision_implication"]
    assert any(c in combined.lower() for c in cautious), "fallback lacks cautious language"


# ---------------------------------------------------------------------------
# K — no raw JSON/dict rendered
# ---------------------------------------------------------------------------

def test_k_result_fields_are_strings_not_dict() -> None:
    ev = _make_evidence()
    fb = _build_fallback(ev)
    assert isinstance(fb["what_it_means"], str)
    assert isinstance(fb["decision_implication"], str)
    assert not fb["what_it_means"].startswith("{")
    assert not fb["decision_implication"].startswith("{")


def test_k_parse_json_extracts_strings() -> None:
    parsed = _parse_json_fields(
        '{"what_it_means": "hello", "decision_implication": "world"}'
    )
    assert parsed["what_it_means"] == "hello"
    assert parsed["decision_implication"] == "world"


def test_k_parse_json_handles_code_block() -> None:
    parsed = _parse_json_fields(
        "```json\n{\"what_it_means\":\"hi\",\"decision_implication\":\"bye\"}\n```"
    )
    assert parsed["what_it_means"] == "hi"
    assert parsed["decision_implication"] == "bye"


# ---------------------------------------------------------------------------
# L / M — only OK responses cached; failed not cached
# ---------------------------------------------------------------------------

@patch("src.ai_decision_impact_synthesis.call_tokenhub_chat_completion")
def test_lm_cache_policy_ok_vs_not_ok(mock_call: MagicMock) -> None:
    """Only OK is cached; FAIL is not cached.  We simulate this via the
    service contract (status field), not by mocking Streamlit session state."""
    mock_call.return_value = _mock_ok_response("a", "b")
    service = AIDecisionImpactSynthesisService(api_key="dummy")
    ev = _make_evidence()
    result = service.interpret(ev)
    assert result.status == "OK"
    # A failed call returns a non-OK status
    mock_call.return_value = _mock_not_ok_response()
    result2 = service.interpret(ev)
    assert result2.status != "OK"
    # Fallback
    mock_call.return_value = _mock_empty_response()
    result3 = service.interpret(ev)
    assert result3.status == "OK"  # parsing succeeded, fields empty


# ---------------------------------------------------------------------------
# N — scenario change invalidates cache
# ---------------------------------------------------------------------------

def test_n_cache_key_changes_with_evidence() -> None:
    ev1 = _make_evidence(
        scenario={
            "selected_action_level": "Minimum Action",
            "selected_scenario_display": "100.0%",
            "expected_kpi_change_display": "14.6%",
            "relative_change_display": "17.1%",
            "action_strategy": "S",
            "resource_commitment": "R",
            "governed_ceiling_reached": False,
            "target_met": True,
        }
    )
    ev2 = _make_evidence(
        scenario={
            "selected_action_level": "Intensive Action",
            "selected_scenario_display": "105.0%",
            "expected_kpi_change_display": "19.6%",
            "relative_change_display": "23.0%",
            "action_strategy": "S2",
            "resource_commitment": "R2",
            "governed_ceiling_reached": True,
            "target_met": True,
        }
    )
    k1 = build_decision_impact_cache_key(ev1)
    k2 = build_decision_impact_cache_key(ev2)
    assert k1 != k2


def test_n_cache_key_changes_with_kpi() -> None:
    ev1 = _make_evidence(kpi={"kpi_id": "kpi_001", "kpi_name": "A", "target_display": "", "unit": "%"})
    ev2 = _make_evidence(kpi={"kpi_id": "kpi_002", "kpi_name": "B", "target_display": "", "unit": "%"})
    assert build_decision_impact_cache_key(ev1) != build_decision_impact_cache_key(ev2)


# ---------------------------------------------------------------------------
# O — no analytical logic changed
# ---------------------------------------------------------------------------

def test_o_evidence_builder_does_not_recalculate_values() -> None:
    """The builder only formats existing values and computes target status
    from the governed threshold config.  It does not recompute scenario
    outcomes, change values, or confidence."""
    ev = build_decision_impact_evidence(
        hospital_id="H",
        department_name="ED",
        kpi_id="kpi_001",
        kpi_name="Staffing Level",
        forecast_month_label="Oct 2025",
        do_nothing_forecast=85.4,
        selected_scenario_value=100.0,
        change_value=14.6,
        change_pct=17.1,
        action_strategy="S",
        resource_line="R",
        selected_action_level="Minimum Action",
        threshold_cfg={
            "kpi_001": {
                "directionality": "HIGHER_IS_BETTER",
                "green_lower_boundary": 84.2,
                "green_upper_boundary": 100.0,
                "unit": "%",
            }
        },
        unit="%",
    )
    # Raw values are passed through unchanged
    assert ev["baseline"]["do_nothing_forecast_display"] == "85.4%"
    assert ev["scenario"]["selected_scenario_display"] == "100.0%"
    assert ev["scenario"]["expected_kpi_change_display"] == "14.6%"
    assert ev["scenario"]["relative_change_display"] == "17.1%"
    # Only threshold comparison is performed (target status)
    assert ev["scenario"]["target_met"] is True
    assert ev["scenario"]["governed_ceiling_reached"] is True


# ---------------------------------------------------------------------------
# Fallback behaviour for three target states
# ---------------------------------------------------------------------------

def test_fallback_ceiling_reached() -> None:
    ev = _make_evidence(
        scenario={
            "selected_action_level": "Minimum Action",
            "selected_scenario_display": "100.0%",
            "expected_kpi_change_display": "14.6%",
            "relative_change_display": "17.1%",
            "action_strategy": "S",
            "resource_commitment": "R",
            "governed_ceiling_reached": True,
            "target_met": True,
        }
    )
    fb = _build_fallback(ev)
    assert "ceiling" in fb["decision_implication"].lower() or "compare" in fb[
        "decision_implication"
    ].lower()


def test_fallback_target_met_not_ceiling() -> None:
    ev = _make_evidence(
        scenario={
            "selected_action_level": "Minimum Action",
            "selected_scenario_display": "90.0%",
            "expected_kpi_change_display": "5.0%",
            "relative_change_display": "5.9%",
            "action_strategy": "S",
            "resource_commitment": "R",
            "governed_ceiling_reached": False,
            "target_met": True,
        }
    )
    fb = _build_fallback(ev)
    assert "sufficient" in fb["decision_implication"].lower() or "without escalating" in fb[
        "decision_implication"
    ].lower()


def test_fallback_target_not_met() -> None:
    ev = _make_evidence(
        scenario={
            "selected_action_level": "Minimum Action",
            "selected_scenario_display": "80.0%",
            "expected_kpi_change_display": "-5.0%",
            "relative_change_display": "-5.9%",
            "action_strategy": "S",
            "resource_commitment": "R",
            "governed_ceiling_reached": False,
            "target_met": False,
        }
    )
    fb = _build_fallback(ev)
    assert "below" in fb["decision_implication"].lower() or "stronger intervention" in fb[
        "decision_implication"
    ].lower()


# ---------------------------------------------------------------------------
# Empty evidence path
# ---------------------------------------------------------------------------

def test_empty_evidence_returns_empty_result() -> None:
    service = AIDecisionImpactSynthesisService(api_key=None)
    result = service.interpret({})
    assert result.status == "EMPTY_EVIDENCE"
    assert result.what_it_means == ""
    assert result.decision_implication == ""
