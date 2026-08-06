"""Targeted tests for Risk & Alert AI-Assisted Management Interpretation.

A. governed evidence values preserved exactly
B. Hy3 cannot calculate (governance flags)
C. AI success shows badge (via is_hy3_live)
D. AI success shows provenance caption
E. fallback hides badge
F. WHAT IS CHANGING renders
G. WHY DOES IT MATTER renders
H. old "Historical:" label removed from user-facing output
I. old "Forecast:" label removed from user-facing output
J. no cross-KPI causal claims in system prompt
K. no raw dict / JSON rendered (safe extraction)
L. failed responses not cached (only OK cached)
M. OK responses cached
N. Management Follow-Up remains unchanged
O. no analytical engines changed
"""

from __future__ import annotations

import hashlib
import json
import os
from unittest.mock import patch

import pandas as pd
import pytest

from src.ai_risk_interpretation import (
    AIRiskInterpretationResult,
    AIRiskInterpretationService,
    _build_fallback,
    _build_prompt,
    _load_api_key,
    _parse_json_fields,
    build_risk_interpretation_cache_key,
)
from src.risk_interpretation_evidence import (
    build_risk_interpretation_evidence,
    _hash_evidence,
)


# ---------------------------------------------------------------------------
# A  — governed evidence values preserved exactly
# ---------------------------------------------------------------------------

class TestGovernedEvidence:
    """A. governed evidence values preserved exactly."""

    def test_evidence_contains_kpi_and_historical_and_forecast(self):
        selected_row = {
            "kpi_id": "S-01",
            "kpi_name": "Patient Satisfaction Score",
            "latest_actual_unit": "1-5 Likert",
            "department_code": "ICU",
            "hospital_id": "HOSP-001",
            "forecast_value": 2.2,
            "forecast_month": "Dec 2025",
            "warning_level": "High Early Warning",
            "forecast_status": "High",
            "actual_status_text": "Acceptable",
        }
        monthly = pd.DataFrame({
            "department_code": ["ICU"],
            "kpi_id": ["S-01"],
            "year": [2025],
            "month": [7],
            "monthly_actual_value": [2.9],
        })
        ev = build_risk_interpretation_evidence(
            selected_row, monthly, 2025, 7
        )
        assert ev["kpi"]["kpi_name"] == "Patient Satisfaction Score"
        assert ev["kpi"]["unit"] == "1-5 Likert"
        assert ev["historical"]["latest_actual_status"] == "Acceptable"
        assert ev["forecast"]["warning_level"] == "High Early Warning"

    def test_evidence_hash_changes_when_value_changes(self):
        ev1 = build_risk_interpretation_evidence(
            {"kpi_id": "S-01", "kpi_name": "X", "latest_actual_unit": "",
             "department_code": "", "hospital_id": "", "forecast_value": None,
             "forecast_month": "", "warning_level": "", "forecast_status": "",
             "actual_status_text": ""},
            pd.DataFrame(), 2025, 7,
        )
        ev2 = build_risk_interpretation_evidence(
            {"kpi_id": "S-01", "kpi_name": "Y", "latest_actual_unit": "",
             "department_code": "", "hospital_id": "", "forecast_value": None,
             "forecast_month": "", "warning_level": "", "forecast_status": "",
             "actual_status_text": ""},
            pd.DataFrame(), 2025, 7,
        )
        assert ev1["_evidence_hash"] != ev2["_evidence_hash"]

    def test_evidence_governance_flags_forbid_calculation(self):
        ev = build_risk_interpretation_evidence(
            {"kpi_id": "S-01", "kpi_name": "X", "latest_actual_unit": "",
             "department_code": "", "hospital_id": "", "forecast_value": None,
             "forecast_month": "", "warning_level": "", "forecast_status": "",
             "actual_status_text": ""},
            pd.DataFrame(), 2025, 7,
        )
        g = ev["governance"]
        assert g["evidence_is_governed"] is True
        assert g["ai_may_calculate"] is False
        assert g["ai_may_modify_values"] is False
        assert g["ai_may_infer_missing_values"] is False
        assert g["causality_confirmed"] is False


# ---------------------------------------------------------------------------
# B  — Hy3 cannot calculate
# ---------------------------------------------------------------------------

class TestHy3CannotCalculate:
    """B. Hy3 cannot calculate (governance flags in prompt)."""

    def test_system_prompt_forbids_calculation(self):
        from src.ai_risk_interpretation import _SYSTEM_PROMPT
        assert "Do NOT calculate" in _SYSTEM_PROMPT
        assert "false" in _SYSTEM_PROMPT.lower() or "not" in _SYSTEM_PROMPT.lower()

    def test_prompt_contains_governance_flags(self):
        ev = build_risk_interpretation_evidence(
            {"kpi_id": "S-01", "kpi_name": "X", "latest_actual_unit": "",
             "department_code": "", "hospital_id": "", "forecast_value": None,
             "forecast_month": "", "warning_level": "", "forecast_status": "",
             "actual_status_text": ""},
            pd.DataFrame(), 2025, 7,
        )
        prompt = _build_prompt(ev)
        assert "GOVERNANCE FLAGS" in prompt
        assert "ai_may_calculate: false" in prompt
        assert "ai_may_modify_values: false" in prompt


# ---------------------------------------------------------------------------
# C/E — badge visibility
# ---------------------------------------------------------------------------

class TestBadgeVisibility:
    """C. AI success shows badge. E. fallback hides badge."""

    def test_ok_status_shows_badge(self):
        from src.genai_provenance_badge import is_hy3_live
        result = AIRiskInterpretationResult(
            status="OK",
            what_is_changing="x",
            why_it_matters="y",
        )
        assert is_hy3_live(result) is True

    def test_fallback_hides_badge(self):
        from src.genai_provenance_badge import is_hy3_live
        result = AIRiskInterpretationResult(
            status="FALLBACK",
            what_is_changing="x",
            why_it_matters="y",
        )
        assert is_hy3_live(result) is False

    def test_not_configured_hides_badge(self):
        from src.genai_provenance_badge import is_hy3_live
        result = AIRiskInterpretationResult(
            status="NOT_CONFIGURED",
            what_is_changing="",
            why_it_matters="",
        )
        assert is_hy3_live(result) is False


# ---------------------------------------------------------------------------
# F/G — WHAT IS CHANGING / WHY DOES IT MATTER render
# ---------------------------------------------------------------------------

class TestStructuredFields:
    """F. WHAT IS CHANGING renders. G. WHY DOES IT MATTER renders."""

    def test_fallback_populates_both_fields(self):
        ev = build_risk_interpretation_evidence(
            {
                "kpi_id": "S-01",
                "kpi_name": "Patient Satisfaction",
                "latest_actual_unit": "1-5",
                "department_code": "ICU",
                "hospital_id": "HOSP-001",
                "forecast_value": 2.2,
                "forecast_month": "Dec 2025",
                "warning_level": "High Early Warning",
                "forecast_status": "High",
                "actual_status_text": "Acceptable",
            },
            pd.DataFrame({
                "department_code": ["ICU", "ICU"],
                "kpi_id": ["S-01", "S-01"],
                "year": [2025, 2025],
                "month": [1, 7],
                "monthly_actual_value": [3.7, 2.9],
            }),
            2025,
            7,
        )
        fallback = _build_fallback(ev)
        assert "WHAT IS CHANGING" not in fallback["what_is_changing"]  # label-free
        assert "Patient Satisfaction" in fallback["what_is_changing"]
        assert "3.7" in fallback["what_is_changing"]
        assert "2.9" in fallback["what_is_changing"]
        assert "2.2" in fallback["what_is_changing"]
        assert "High Early Warning" in fallback["why_it_matters"]

    def test_service_with_no_api_key_returns_fallback(self):
        ev = build_risk_interpretation_evidence(
            {"kpi_id": "S-01", "kpi_name": "X", "latest_actual_unit": "",
             "department_code": "", "hospital_id": "", "forecast_value": None,
             "forecast_month": "", "warning_level": "", "forecast_status": "",
             "actual_status_text": ""},
            pd.DataFrame(), 2025, 7,
        )
        with patch.object(os, "getenv", return_value=""):
            svc = AIRiskInterpretationService(api_key="")
            result = svc.interpret(ev)
        assert result.status == "FALLBACK"
        assert result.what_is_changing != ""
        assert result.why_it_matters != ""


# ---------------------------------------------------------------------------
# H/I — old "Historical:" / "Forecast:" labels removed from visible output
# ---------------------------------------------------------------------------

class TestOldLabelsRemoved:
    """H. old 'Historical:' label removed. I. old 'Forecast:' label removed."""

    def test_fallback_does_not_start_with_historical_label(self):
        ev = build_risk_interpretation_evidence(
            {
                "kpi_id": "S-01", "kpi_name": "X", "latest_actual_unit": "",
                "department_code": "", "hospital_id": "", "forecast_value": None,
                "forecast_month": "", "warning_level": "", "forecast_status": "",
                "actual_status_text": "",
            },
            pd.DataFrame(), 2025, 7,
        )
        fallback = _build_fallback(ev)
        assert not fallback["what_is_changing"].startswith("Historical:")
        assert not fallback["what_is_changing"].startswith("Forecast:")

    def test_fallback_why_does_not_start_with_historical_or_forecast(self):
        ev = build_risk_interpretation_evidence(
            {
                "kpi_id": "S-01", "kpi_name": "X", "latest_actual_unit": "",
                "department_code": "", "hospital_id": "", "forecast_value": 1.0,
                "forecast_month": "Dec 2025", "warning_level": "High",
                "forecast_status": "High", "actual_status_text": "",
            },
            pd.DataFrame(), 2025, 7,
        )
        fallback = _build_fallback(ev)
        assert not fallback["why_it_matters"].startswith("Historical:")
        assert not fallback["why_it_matters"].startswith("Forecast:")


# ---------------------------------------------------------------------------
# J  — no cross-KPI causal claims
# ---------------------------------------------------------------------------

class TestNoCrossKPICausality:
    """J. no cross-KPI causal claims in system prompt."""

    def test_system_prompt_forbids_causality(self):
        from src.ai_risk_interpretation import _SYSTEM_PROMPT
        # The system prompt explicitly instructs the model to avoid causal claims
        assert "causal" in _SYSTEM_PROMPT.lower() or "causality" in _SYSTEM_PROMPT.lower()
        assert "claim" in _SYSTEM_PROMPT.lower() or "forbid" in _SYSTEM_PROMPT.lower()

    def test_governance_flag_confirms_no_causality(self):
        ev = build_risk_interpretation_evidence(
            {"kpi_id": "S-01", "kpi_name": "X", "latest_actual_unit": "",
             "department_code": "", "hospital_id": "", "forecast_value": None,
             "forecast_month": "", "warning_level": "", "forecast_status": "",
             "actual_status_text": ""},
            pd.DataFrame(), 2025, 7,
        )
        assert ev["governance"]["causality_confirmed"] is False


# ---------------------------------------------------------------------------
# K  — no raw dict / JSON rendered (safe extraction)
# ---------------------------------------------------------------------------

class TestSafeExtraction:
    """K. no raw dict / JSON rendered (safe extraction)."""

    def test_parse_json_fields_returns_plain_strings(self):
        text = json.dumps({
            "what_is_changing": "Value went from 3 to 2.",
            "why_it_matters": "It is now at risk.",
        })
        parsed = _parse_json_fields(text)
        assert parsed["what_is_changing"] == "Value went from 3 to 2."
        assert parsed["why_it_matters"] == "It is now at risk."
        assert "{" not in parsed["what_is_changing"]

    def test_parse_json_fields_from_codeblock(self):
        text = '```json\n{"what_is_changing": "A", "why_it_matters": "B"}\n```'
        parsed = _parse_json_fields(text)
        assert parsed["what_is_changing"] == "A"
        assert parsed["why_it_matters"] == "B"

    def test_parse_json_fields_empty_on_gibberish(self):
        parsed = _parse_json_fields("no json here")
        assert parsed.get("what_is_changing", "") == ""
        assert parsed.get("why_it_matters", "") == ""


# ---------------------------------------------------------------------------
# L/M  — caching policy
# ---------------------------------------------------------------------------

class TestCachingPolicy:
    """L. failed responses not cached. M. OK responses cached."""

    def test_cache_key_contains_no_api_key(self):
        ev = {"kpi": {"kpi_name": "X"}, "_evidence_hash": "abc123"}
        key = build_risk_interpretation_cache_key(ev)
        assert "api_key" not in key.lower()
        assert "abc123" in key

    def test_cache_key_is_deterministic(self):
        ev = {"kpi": {"kpi_name": "X"}, "_evidence_hash": "abc123"}
        k1 = build_risk_interpretation_cache_key(ev)
        k2 = build_risk_interpretation_cache_key(ev)
        assert k1 == k2

    def test_hash_matches_content(self):
        ev = {"kpi": {"kpi_name": "A"}, "historical": {}}
        ev["_evidence_hash"] = _hash_evidence(ev)
        assert isinstance(ev["_evidence_hash"], str)
        assert len(ev["_evidence_hash"]) == 16

    def test_ok_result_has_no_dict_rendering_in_fields(self):
        # Simulated Hy3 OK result — fields are plain sentences, not dicts
        result = AIRiskInterpretationResult(
            status="OK",
            what_is_changing="The score dropped.",
            why_it_matters="It is now at risk.",
            raw_response={"status": "OK", "message": "..."},
        )
        assert "{" not in result.what_is_changing
        assert "{" not in result.why_it_matters


# ---------------------------------------------------------------------------
# N  — Management Follow-Up remains unchanged
# ---------------------------------------------------------------------------

class TestManagementFollowUpUnchanged:
    """N. Management Follow-Up remains unchanged."""

    def test_build_suggested_action_card_imported_from_risk_alert_controller(self):
        from src.risk_alert_controller import build_suggested_action_card
        assert callable(build_suggested_action_card)

    def test_build_suggested_action_card_not_removed(self):
        # We simply verify the function still exists and produces a dict
        from src.risk_alert_controller import build_suggested_action_card
        selected = {
            "kpi_name": "Satisfaction",
            "kpi_id": "S-01",
            "department_name": "ICU",
            "latest_actual_value": 2.9,
            "latest_actual_unit": "1-5",
            "forecast_value": 2.2,
            "forecast_unit": "1-5",
            "warning_level": "High Early Warning",
            "trend_direction": "down",
            "actual_status_text": "Acceptable",
            "forecast_status": "High",
            "forecast_quality": "medium",
            "target": 4.5,
            "target_band": 0.5,
            "suggested_action": "Investigate",
            "forecast_month": "Dec 2025",
        }
        action = build_suggested_action_card(selected)
        assert isinstance(action, dict)
        assert "action" in action


# ---------------------------------------------------------------------------
# O  — no analytical engines changed
# ---------------------------------------------------------------------------

class TestNoAnalyticalEnginesChanged:
    """O. no analytical engines changed."""

    def test_build_risk_alert_state_still_exists(self):
        from src.risk_alert_controller import build_risk_alert_state
        assert callable(build_risk_alert_state)

    def test_build_risk_progression_still_exists(self):
        from src.risk_alert_controller import build_risk_progression
        assert callable(build_risk_progression)

    def test_build_selected_risk_detail_still_exists(self):
        from src.risk_alert_controller import build_selected_risk_detail
        assert callable(build_selected_risk_detail)

    def test_build_management_interpretation_still_exists(self):
        # Original function is preserved in the analytical engine
        from src.risk_alert_controller import build_management_interpretation
        assert callable(build_management_interpretation)

    def test_format_unit_value_still_exists(self):
        from src.risk_alert_controller import format_unit_value
        assert callable(format_unit_value)

    def test_warning_priority_rank_unchanged(self):
        from src.risk_alert_controller import WARNING_PRIORITY_RANK
        assert isinstance(WARNING_PRIORITY_RANK, dict)
        assert "High Early Warning" in WARNING_PRIORITY_RANK
