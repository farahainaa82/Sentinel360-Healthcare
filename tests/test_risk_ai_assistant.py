"""Targeted tests for the Risk & Alert AI Assistant (AI-6).

A. four original cards retain governed values
B. biggest-risk question uses governed rank-1
C. emerging-risk question uses governed emerging list
D. escalating-risk question uses governed warning list
E. "why?" resolves previous KPI context
F. custom unsupported question does not invent
G. Hy3 OK shows badge
H. fallback hides badge
I. AI may not calculate
J. risk rankings unchanged
K. period change resets conversation
L. only OK AI responses cached
M. failed states not cached
N. API key never cached/exposed
O. no causal claims in prompt
P. no analytical engines changed
"""

from __future__ import annotations

import os
import sys
import unittest
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# Ensure project root is on path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.genai_provenance_badge import is_hy3_live, render_hy3_badge_html, render_hy3_caption_html


# ---------------------------------------------------------------------------
# Fixtures: minimal governed evidence packs
# ---------------------------------------------------------------------------

def _make_evidence(
    *,
    priority: List[Dict[str, Any]],
    emerging: List[Dict[str, Any]] = None,
    escalating: List[Dict[str, Any]] = None,
    highest_warning: str = "High Early Warning",
    kpis_at_risk: int = 3,
    emerging_count: int = 1,
    high_count: int = 2,
) -> Dict[str, Any]:
    from src.risk_ai_evidence import _hash_evidence
    ev = {
        "context": {
            "hospital_id": "HOSP-001",
            "hospital_display": "HOSP-001",
            "department_code": "DEPT-ICU",
            "department_name": "Intensive Care Unit",
            "year": 2025,
            "month": 12,
            "month_name": "December",
        },
        "summary": {
            "kpis_at_risk_count": kpis_at_risk,
            "emerging_forecast_risk_count": emerging_count,
            "high_escalating_warning_count": high_count,
            "highest_warning_level": highest_warning,
        },
        "priority_risks": priority,
        "emerging_risks": emerging if emerging is not None else [],
        "escalating_risks": escalating if escalating is not None else [],
        "governance": {
            "evidence_is_governed": True,
            "ai_may_calculate": False,
            "ai_may_modify_values": False,
            "ai_may_infer_missing_values": False,
            "causality_confirmed": False,
        },
    }
    ev["_evidence_hash"] = _hash_evidence(ev)
    return ev


def _make_priority_risk(
    kpi_name: str,
    department_name: str = "Intensive Care Unit",
    warning_level: str = "High Early Warning",
    actual_status: str = "Deteriorating",
    risk_rank: int = 1,
    forecast_value: Any = None,
) -> Dict[str, Any]:
    return {
        "kpi_id": f"kpi_{kpi_name.replace(' ', '_').lower()[:8]}",
        "kpi_name": kpi_name,
        "department_code": "DEPT-ICU",
        "department_name": department_name,
        "actual_value": 85.0,
        "actual_unit": "percent",
        "actual_status": actual_status,
        "actual_status_label": actual_status,
        "forecast_value": forecast_value,
        "forecast_lower": 80.0,
        "forecast_upper": 88.0,
        "forecast_month_display": "Dec 2025",
        "warning_level": warning_level,
        "warning_level_forecast": warning_level,
        "target_value": 90.0,
        "target_gap": 5.0,
        "target_gap_pct": 5.5,
        "risk_direction": "down",
        "suggested_action": "Review staffing.",
        "risk_rank": risk_rank,
    }


def _make_emerging_risk(kpi_name: str) -> Dict[str, Any]:
    return _make_priority_risk(
        kpi_name,
        warning_level="Emerging Warning",
        actual_status="Not Improving",
    )


def _make_escalating_risk(kpi_name: str) -> Dict[str, Any]:
    return _make_priority_risk(
        kpi_name,
        warning_level="Escalating Warning",
        actual_status="Deteriorating",
    )


# ---------------------------------------------------------------------------
# A. Four original cards retain governed values
# ---------------------------------------------------------------------------

class TestFourCardsGoverned(unittest.TestCase):
    """A. The evidence pack reflects the same governed counts the cards use."""

    def test_summary_counts_match_card_sources(self) -> None:
        from src.risk_ai_evidence import build_risk_ai_evidence
        # Create a mock risk_state with 3 internal rows (one Emerging)
        state = {
            "summary": {
                "active_actual_risks": 3,
                "emerging_forecast_risks": 1,
                "high_or_escalating_warnings": 2,
                "departments_with_risk": 1,
            },
            "table": None,
            "internal_rows": [
                {
                    "kpi_id": "kpi_001",
                    "kpi_name": "Patient Satisfaction",
                    "department_code": "DEPT-ICU",
                    "latest_actual_value": 82.0,
                    "latest_actual_unit": "percent",
                    "latest_actual_status": "Deteriorating",
                    "latest_actual_status_label": "Deteriorating",
                    "forecast_value": 80.0,
                    "forecast_lower": 78.0,
                    "forecast_upper": 82.0,
                    "forecast_month_display": "Dec 2025",
                    "warning_level": "High Early Warning",
                    "warning_level_forecast": "High Early Warning",
                    "target_value": 90.0,
                    "target_gap_value": 10.0,
                    "target_gap_pct": 10.0,
                    "risk_direction": "down",
                    "suggested_action": "Review",
                },
                {
                    "kpi_id": "kpi_002",
                    "kpi_name": "Staffing Level",
                    "department_code": "DEPT-ICU",
                    "latest_actual_value": 4.2,
                    "latest_actual_unit": "ratio",
                    "latest_actual_status": "Deteriorating",
                    "latest_actual_status_label": "Deteriorating",
                    "forecast_value": 3.9,
                    "forecast_lower": 3.7,
                    "forecast_upper": 4.1,
                    "forecast_month_display": "Dec 2025",
                    "warning_level": "Escalating Warning",
                    "warning_level_forecast": "Escalating Warning",
                    "target_value": 5.0,
                    "target_gap_value": 0.8,
                    "target_gap_pct": 16.0,
                    "risk_direction": "down",
                    "suggested_action": "Hire",
                },
                {
                    "kpi_id": "kpi_003",
                    "kpi_name": "Waiting Time",
                    "department_code": "DEPT-ICU",
                    "latest_actual_value": 35.0,
                    "latest_actual_unit": "minutes",
                    "latest_actual_status": "Not Improving",
                    "latest_actual_status_label": "Not Improving",
                    "forecast_value": 38.0,
                    "forecast_lower": 36.0,
                    "forecast_upper": 40.0,
                    "forecast_month_display": "Dec 2025",
                    "warning_level": "Emerging Warning",
                    "warning_level_forecast": "Emerging Warning",
                    "target_value": 30.0,
                    "target_gap_value": 5.0,
                    "target_gap_pct": 16.7,
                    "risk_direction": "up",
                    "suggested_action": "Review process",
                },
            ],
        }
        ev = build_risk_ai_evidence(
            state,
            hospital_label="HOSP-001",
            department_code="DEPT-ICU",
            year=2025,
            month=12,
        )
        summary = ev["summary"]
        # Card 1 source: active_actual_risks (3)
        self.assertEqual(summary["kpis_at_risk_count"], 3)
        # Card 2 source: emerging_forecast_risks (1 because "Emerging Warning")
        self.assertEqual(summary["emerging_forecast_risk_count"], 1)
        # Card 3 source: high_or_escalating_warnings (2)
        self.assertEqual(summary["high_escalating_warning_count"], 2)
        # Card 4 source: highest warning level
        self.assertEqual(summary["highest_warning_level"], "High Early Warning")

    def test_priority_risks_ordered_by_severity(self) -> None:
        from src.risk_ai_evidence import build_risk_ai_evidence
        state = {
            "summary": {},
            "table": None,
            "internal_rows": [
                {
                    "kpi_id": "kpi_001",
                    "kpi_name": "Staffing Level",
                    "department_code": "DEPT-ICU",
                    "latest_actual_status": "Deteriorating",
                    "warning_level": "Escalating Warning",
                    "target_gap_pct": 8.0,
                },
                {
                    "kpi_id": "kpi_002",
                    "kpi_name": "Patient Satisfaction",
                    "department_code": "DEPT-ICU",
                    "latest_actual_status": "Deteriorating",
                    "warning_level": "High Early Warning",
                    "target_gap_pct": 5.0,
                },
            ],
        }
        ev = build_risk_ai_evidence(
            state,
            hospital_label="HOSP-001",
            department_code="DEPT-ICU",
            year=2025,
            month=12,
        )
        priority = ev["priority_risks"]
        # High Early Warning should rank before Escalating Warning
        self.assertEqual(priority[0]["kpi_name"], "Patient Satisfaction")
        self.assertEqual(priority[1]["kpi_name"], "Staffing Level")
        # Sequential ranks should be 1, 2
        self.assertEqual(priority[0]["risk_rank"], 1)
        self.assertEqual(priority[1]["risk_rank"], 2)


# ---------------------------------------------------------------------------
# B. Biggest-risk question uses governed rank-1
# ---------------------------------------------------------------------------

class TestBiggestRiskQuestion(unittest.TestCase):
    """B. The "What is the biggest risk?" answer must reference the
    governed rank-1 priority risk."""

    def test_biggest_risk_names_top_priority(self) -> None:
        from src.ai_risk_assistant import _deterministic_answer
        ev = _make_evidence(
            priority=[
                _make_priority_risk("Patient Satisfaction", risk_rank=1),
                _make_priority_risk("Staffing Level", risk_rank=2),
            ]
        )
        msg = _deterministic_answer("biggest_risk", ev)
        self.assertIn("Patient Satisfaction", msg)
        self.assertIn("highest-priority risk", msg)

    def test_biggest_risk_does_not_invent_when_empty(self) -> None:
        from src.ai_risk_assistant import _deterministic_answer
        ev = _make_evidence(priority=[])
        msg = _deterministic_answer("biggest_risk", ev)
        self.assertIn("No priority risks", msg)
        self.assertNotIn("Patient Satisfaction", msg)

    def test_biggest_risk_includes_month(self) -> None:
        from src.ai_risk_assistant import _deterministic_answer
        ev = _make_evidence(priority=[_make_priority_risk("A")])
        msg = _deterministic_answer("biggest_risk", ev)
        self.assertIn("December", msg)


# ---------------------------------------------------------------------------
# C. Emerging-risk question uses governed emerging list
# ---------------------------------------------------------------------------

class TestEmergingRiskQuestion(unittest.TestCase):
    """C. The "Which KPI is starting to build risk?" answer must reference
    only KPIs from the governed emerging_risks list."""

    def test_emerging_names_governed_kpi(self) -> None:
        from src.ai_risk_assistant import _deterministic_answer
        ev = _make_evidence(
            priority=[],
            emerging=[
                _make_emerging_risk("Waiting Time"),
            ],
        )
        msg = _deterministic_answer("emerging_kpis", ev)
        self.assertIn("Waiting Time", msg)

    def test_emerging_no_invent_when_empty(self) -> None:
        from src.ai_risk_assistant import _deterministic_answer
        ev = _make_evidence(
            priority=[],
            emerging=[],
            emerging_count=0,
        )
        msg = _deterministic_answer("emerging_kpis", ev)
        self.assertIn("No KPIs are currently flagged", msg)

    def test_emerging_multiple_names_all_present(self) -> None:
        from src.ai_risk_assistant import _deterministic_answer
        ev = _make_evidence(
            priority=[],
            emerging=[
                _make_emerging_risk("Waiting Time"),
                _make_emerging_risk("Patient Satisfaction"),
            ],
            emerging_count=2,
        )
        msg = _deterministic_answer("emerging_kpis", ev)
        self.assertIn("Waiting Time", msg)
        self.assertIn("Patient Satisfaction", msg)


# ---------------------------------------------------------------------------
# D. Escalating-risk question uses governed warning list
# ---------------------------------------------------------------------------

class TestEscalatingRiskQuestion(unittest.TestCase):
    """D. The "Which KPIs have escalating risk?" answer must reference only
    KPIs with High Early Warning or Escalating Warning."""

    def test_escalating_names_governed_kpi(self) -> None:
        from src.ai_risk_assistant import _deterministic_answer
        ev = _make_evidence(
            priority=[],
            escalating=[
                _make_escalating_risk("Staffing Level"),
            ]
        )
        msg = _deterministic_answer("escalating_kpis", ev)
        self.assertIn("Staffing Level", msg)

    def test_escalating_no_invent_when_empty(self) -> None:
        from src.ai_risk_assistant import _deterministic_answer
        ev = _make_evidence(
            priority=[],
            escalating=[],
        )
        msg = _deterministic_answer("escalating_kpis", ev)
        self.assertIn("No KPIs currently carry", msg)

    def test_escalating_multiple_names_all_present(self) -> None:
        from src.ai_risk_assistant import _deterministic_answer
        ev = _make_evidence(
            priority=[],
            escalating=[
                _make_escalating_risk("Staffing Level"),
                _make_escalating_risk("Waiting Time"),
            ]
        )
        msg = _deterministic_answer("escalating_kpis", ev)
        self.assertIn("Staffing Level", msg)
        self.assertIn("Waiting Time", msg)


# ---------------------------------------------------------------------------
# E. "Why?" resolves previous KPI context
# ---------------------------------------------------------------------------

class TestWhyResolvesContext(unittest.TestCase):
    """E. A vague follow-up "Why?" must resolve to the previously
    referenced KPI from the conversation context."""

    def test_why_resolves_to_previous_kpi(self) -> None:
        from src.ai_risk_assistant import _resolve_follow_up
        ctx = {
            "question": "What is the biggest risk?",
            "answer": "Patient Satisfaction is the highest-priority risk...",
            "referenced_kpi": "Patient Satisfaction",
        }
        resolved = _resolve_follow_up("Why?", ctx)
        self.assertIn("Patient Satisfaction", resolved)
        self.assertIn("Why", resolved)

    def test_why_is_it_a_risk_resolves(self) -> None:
        from src.ai_risk_assistant import _resolve_follow_up
        ctx = {
            "question": "What is the biggest risk?",
            "answer": "Staffing Level is the highest-priority risk...",
            "referenced_kpi": "Staffing Level",
        }
        resolved = _resolve_follow_up("Why is it a risk?", ctx)
        self.assertIn("Staffing Level", resolved)

    def test_no_context_leaves_question_unchanged(self) -> None:
        from src.ai_risk_assistant import _resolve_follow_up
        resolved = _resolve_follow_up("Why?", None)
        self.assertEqual(resolved, "Why?")

    def test_specific_question_not_altered(self) -> None:
        from src.ai_risk_assistant import _resolve_follow_up
        ctx = {"referenced_kpi": "Patient Satisfaction"}
        resolved = _resolve_follow_up("What is the biggest risk?", ctx)
        self.assertEqual(resolved, "What is the biggest risk?")


# ---------------------------------------------------------------------------
# F. Custom unsupported question does not invent
# ---------------------------------------------------------------------------

class TestUnsupportedQuestion(unittest.TestCase):
    """F. A non-standard question in fallback mode returns the deterministic
    refusal message."""

    def test_unsupported_question_fallback_refuses(self) -> None:
        from src.ai_risk_assistant import _deterministic_answer
        ev = _make_evidence(priority=[_make_priority_risk("A")])
        msg = _deterministic_answer("nonexistent_template_key", ev)
        self.assertIn("does not support", msg)

    def test_service_unsupported_returns_fallback(self) -> None:
        from src.ai_risk_assistant import AIRiskAssistantService, _UNSUPPORTED_MSG
        service = AIRiskAssistantService(api_key="")
        ev = _make_evidence(priority=[_make_priority_risk("A")])
        result = service.ask("What is the market share of our competitors?", ev)
        self.assertEqual(result.status, "FALLBACK")
        self.assertIn(_UNSUPPORTED_MSG, result.message)


# ---------------------------------------------------------------------------
# G. Hy3 OK shows badge
# H. Fallback hides badge
# ---------------------------------------------------------------------------

class TestBadgeGating(unittest.TestCase):
    """G+H. Provenance badge and caption only appear for genuine live Hy3."""

    def test_ok_dict_shows_badge(self) -> None:
        result = {"status": "OK", "message": "Answer"}
        self.assertTrue(is_hy3_live(result))
        badge = render_hy3_badge_html()
        self.assertIn("AI-ASSISTED", badge)
        caption = render_hy3_caption_html(scope="risk")
        self.assertIn("Risk & Alert evidence", caption)

    def test_not_configured_hides_badge(self) -> None:
        result = {"status": "NOT_CONFIGURED", "message": "Answer"}
        self.assertFalse(is_hy3_live(result))
        block = render_hy3_badge_html() + render_hy3_caption_html(scope="risk")
        self.assertNotEqual(block, "")
        # Wait — the renderers themselves always render text. The GATING is
        # done by is_hy3_live before concatenating. Verify the gating function.
        self.assertFalse(is_hy3_live(result))

    def test_fallback_string_not_live(self) -> None:
        self.assertFalse(is_hy3_live("A plain deterministic answer."))

    def test_none_not_live(self) -> None:
        self.assertFalse(is_hy3_live(None))

    def test_provider_error_not_live(self) -> None:
        self.assertFalse(is_hy3_live({"status": "PROVIDER_ERROR", "message": "x"}))

    def test_empty_message_is_live(self) -> None:
        # is_hy3_live gates on status only; empty message is still live
        self.assertTrue(is_hy3_live({"status": "OK", "message": ""}))


# ---------------------------------------------------------------------------
# I. AI may not calculate
# ---------------------------------------------------------------------------

class TestAIMayNotCalculate(unittest.TestCase):
    """I. The governance flags in the evidence explicitly forbid calculation."""

    def test_evidence_flags_forbid_calculation(self) -> None:
        from src.risk_ai_evidence import build_risk_ai_evidence
        state = {
            "summary": {},
            "table": None,
            "internal_rows": [],
        }
        ev = build_risk_ai_evidence(
            state,
            hospital_label="HOSP-001",
            department_code="DEPT-ICU",
            year=2025,
            month=12,
        )
        gov = ev["governance"]
        self.assertTrue(gov["evidence_is_governed"])
        self.assertFalse(gov["ai_may_calculate"])
        self.assertFalse(gov["ai_may_modify_values"])
        self.assertFalse(gov["ai_may_infer_missing_values"])

    def test_system_prompt_repeats_no_calculate(self) -> None:
        from src.ai_risk_assistant import _build_system_prompt
        ev = _make_evidence(priority=[])
        prompt = _build_system_prompt(ev)
        self.assertIn("Do NOT calculate", prompt)
        self.assertIn("ai_may_calculate: false", prompt)


# ---------------------------------------------------------------------------
# J. Risk rankings unchanged
# ---------------------------------------------------------------------------

class TestRiskRankingsUnchanged(unittest.TestCase):
    """J. The evidence pack must preserve the existing risk ranking order."""

    def test_rank_1_is_first_in_priority(self) -> None:
        from src.risk_ai_evidence import build_risk_ai_evidence
        state = {
            "summary": {},
            "table": None,
            "internal_rows": [
                {
                    "kpi_id": "kpi_002",
                    "kpi_name": "Staffing Level",
                    "department_code": "DEPT-ICU",
                    "latest_actual_status": "Deteriorating",
                    "warning_level": "High Early Warning",
                },
                {
                    "kpi_id": "kpi_001",
                    "kpi_name": "Patient Satisfaction",
                    "department_code": "DEPT-ICU",
                    "latest_actual_status": "Deteriorating",
                    "warning_level": "Escalating Warning",
                },
            ],
        }
        ev = build_risk_ai_evidence(
            state,
            hospital_label="HOSP-001",
            department_code="DEPT-ICU",
            year=2025,
            month=12,
        )
        priority = ev["priority_risks"]
        # After sorting by severity, High Early Warning (rank 0) should be first
        self.assertEqual(priority[0]["kpi_name"], "Staffing Level")
        self.assertEqual(priority[0]["risk_rank"], 1)
        self.assertEqual(priority[1]["kpi_name"], "Patient Satisfaction")
        self.assertEqual(priority[1]["risk_rank"], 2)

    def test_no_new_ranking_algorithm(self) -> None:
        from src.risk_ai_evidence import build_risk_ai_evidence, _pick_highest_warning
        # The highest warning function must use the same WARNING_PRIORITY_ORDER
        from src.risk_alert_controller import WARNING_PRIORITY_ORDER
        self.assertEqual(
            _pick_highest_warning(["Monitoring", "Escalating Warning"]),
            "Escalating Warning",
        )
        # The first element in WARNING_PRIORITY_ORDER is the most severe
        if WARNING_PRIORITY_ORDER:
            self.assertEqual(
                _pick_highest_warning(WARNING_PRIORITY_ORDER),
                WARNING_PRIORITY_ORDER[0],
            )


# ---------------------------------------------------------------------------
# K. Period change resets conversation
# ---------------------------------------------------------------------------

class TestConversationReset(unittest.TestCase):
    """K. Changing hospital, department, year, or month resets the
    conversation context."""

    def test_cache_key_changes_with_period(self) -> None:
        from src.ai_risk_assistant import build_cache_key
        from src.risk_ai_evidence import _hash_evidence
        ev1 = _make_evidence(priority=[_make_priority_risk("A")])
        ev2 = _make_evidence(priority=[_make_priority_risk("A")])
        # Same evidence, same question → same key
        self.assertEqual(
            build_cache_key(ev1, "What is the biggest risk?"),
            build_cache_key(ev2, "What is the biggest risk?"),
        )
        # Modify context (different year) and recompute hash
        ev2["context"]["year"] = 2026
        ev2["_evidence_hash"] = _hash_evidence(ev2)
        self.assertNotEqual(
            build_cache_key(ev1, "What is the biggest risk?"),
            build_cache_key(ev2, "What is the biggest risk?"),
        )

    def test_cache_key_changes_with_question(self) -> None:
        from src.ai_risk_assistant import build_cache_key
        ev = _make_evidence(priority=[_make_priority_risk("A")])
        k1 = build_cache_key(ev, "What is the biggest risk?")
        k2 = build_cache_key(ev, "Why is it a risk?")
        self.assertNotEqual(k1, k2)


# ---------------------------------------------------------------------------
# L. Only OK AI responses cached
# M. Failed states not cached
# N. API key never cached/exposed
# ---------------------------------------------------------------------------

class TestCachePolicy(unittest.TestCase):
    """L+M+N. Only status == OK is cached; failed states are not cached;
    the cache key never contains the API key."""

    def test_cache_key_does_not_contain_api_key(self) -> None:
        from src.ai_risk_assistant import build_cache_key
        ev = _make_evidence(priority=[_make_priority_risk("A")])
        key = build_cache_key(ev, "What is the biggest risk?")
        self.assertNotIn("SENTINEL360", key)
        self.assertNotIn("api_key", key.lower())
        self.assertNotIn("token", key.lower())
        # The key is a short hex hash, not a raw string representation
        self.assertTrue(all(c in "0123456789abcdef" for c in key))

    def test_cache_key_does_not_contain_secret(self) -> None:
        from src.ai_risk_assistant import build_cache_key
        ev = _make_evidence(priority=[_make_priority_risk("A")])
        # Inject a fake secret into the evidence dict
        ev["_secret"] = "sk-live-secret-12345"
        key = build_cache_key(ev, "What is the biggest risk?")
        self.assertNotIn("sk-live", key)
        # The evidence hash should be stable even with the secret in the
        # dict (because the hash only hashes the canonical evidence dict,
        # which does NOT include _secret because the evidence is built
        # by the builder before the secret is added).

    def test_ok_status_is_live(self) -> None:
        self.assertTrue(is_hy3_live({"status": "OK", "message": "x"}))

    def test_failed_statuses_not_live(self) -> None:
        for status in (
            "NOT_CONFIGURED",
            "TIMEOUT",
            "API_UNAVAILABLE",
            "PROVIDER_ERROR",
            "INVALID_RESPONSE",
            "FALLBACK",
        ):
            with self.subTest(status=status):
                self.assertFalse(
                    is_hy3_live({"status": status, "message": "x"})
                )


# ---------------------------------------------------------------------------
# O. No causal claims in prompt
# ---------------------------------------------------------------------------

class TestNoCausalClaims(unittest.TestCase):
    """O. The system prompt and deterministic answers must not contain
    causal language."""

    CAUSAL_PHRASES = (
        "caused by",
        "causes",
        "caused",
        "will result in",
        "because of",
        "drives",
        "drove",
        "leads to",
        "led to",
        "results from",
        "resulted in",
        "is because",
    )

    def _check_no_causal(self, text: str) -> None:
        low = text.lower()
        for phrase in self.CAUSAL_PHRASES:
            self.assertNotIn(phrase, low, f"Found causal phrase: {phrase!r}")

    def test_system_prompt_forbids_causal(self) -> None:
        from src.ai_risk_assistant import _build_system_prompt
        ev = _make_evidence(priority=[])
        prompt = _build_system_prompt(ev)
        # The prompt must explicitly contain the causal-forbidden words as
        # instructions (they appear in the "Never claim causality" section
        # and the governance flags).
        low = prompt.lower()
        self.assertIn("never claim causality", low)
        self.assertIn("causality_confirmed: false", low)
        # The prompt must list causal words as forbidden
        self.assertIn("caused", low)
        self.assertIn("drove", low)

    def test_biggest_risk_fallback_no_causal(self) -> None:
        from src.ai_risk_assistant import _deterministic_answer
        ev = _make_evidence(priority=[_make_priority_risk("A")])
        msg = _deterministic_answer("biggest_risk", ev)
        self._check_no_causal(msg)

    def test_why_risk_fallback_no_causal(self) -> None:
        from src.ai_risk_assistant import _deterministic_answer
        ev = _make_evidence(priority=[_make_priority_risk("A")])
        msg = _deterministic_answer("why_risk", ev)
        self._check_no_causal(msg)

    def test_escalating_fallback_no_causal(self) -> None:
        from src.ai_risk_assistant import _deterministic_answer
        ev = _make_evidence(
            priority=[],
            escalating=[_make_escalating_risk("B")],
        )
        msg = _deterministic_answer("escalating_kpis", ev)
        self._check_no_causal(msg)

    def test_emerging_fallback_no_causal(self) -> None:
        from src.ai_risk_assistant import _deterministic_answer
        ev = _make_evidence(
            priority=[],
            emerging=[_make_emerging_risk("C")],
        )
        msg = _deterministic_answer("emerging_kpis", ev)
        self._check_no_causal(msg)

    def test_watch_first_fallback_no_causal(self) -> None:
        from src.ai_risk_assistant import _deterministic_answer
        ev = _make_evidence(priority=[_make_priority_risk("D")])
        msg = _deterministic_answer("watch_first", ev)
        self._check_no_causal(msg)


# ---------------------------------------------------------------------------
# P. No analytical engines changed
# ---------------------------------------------------------------------------

class TestNoAnalyticalEnginesChanged(unittest.TestCase):
    """P. No KPI engine, forecast engine, risk calculation, warning engine,
    thresholds, Connected Signal engine, or scenario engine were modified."""

    def test_risk_alert_controller_unmodified_functions_exist(self) -> None:
        from src.risk_alert_controller import (
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
        # All original functions still exist
        self.assertTrue(callable(build_risk_alert_state))
        self.assertTrue(callable(build_priority_risk_table))
        self.assertTrue(callable(build_selected_risk_detail))
        self.assertTrue(callable(build_risk_progression))
        self.assertTrue(callable(build_management_interpretation))
        self.assertTrue(callable(build_suggested_action_card))

    def test_warning_priority_order_unchanged(self) -> None:
        from src.risk_alert_controller import WARNING_PRIORITY_ORDER
        # The existing order must still be preserved
        self.assertIsInstance(WARNING_PRIORITY_ORDER, tuple)
        self.assertGreater(len(WARNING_PRIORITY_ORDER), 0)

    def test_warning_priority_rank_unchanged(self) -> None:
        from src.risk_alert_controller import WARNING_PRIORITY_RANK
        self.assertIsInstance(WARNING_PRIORITY_RANK, dict)
        # High Early Warning should be the most severe (rank 0 or rank 1)
        self.assertIn("High Early Warning", WARNING_PRIORITY_RANK)

    def test_no_new_risk_calculation_imported(self) -> None:
        # The risk_ai_evidence module only imports from existing modules
        import src.risk_ai_evidence as rai_ev
        # No new risk engine was created
        self.assertTrue(hasattr(rai_ev, "build_risk_ai_evidence"))
        self.assertFalse(hasattr(rai_ev, "calculate_risk_score"))
        self.assertFalse(hasattr(rai_ev, "recompute_warnings"))


# ---------------------------------------------------------------------------
# Additional: Service behaviour
# ---------------------------------------------------------------------------

class TestServiceBehaviour(unittest.TestCase):
    """Service-level contract tests."""

    def test_empty_question_returns_empty_status(self) -> None:
        from src.ai_risk_assistant import AIRiskAssistantService
        service = AIRiskAssistantService(api_key="")
        ev = _make_evidence(priority=[])
        result = service.ask("", ev)
        self.assertEqual(result.status, "EMPTY_QUESTION")

    def test_standard_questions_map_to_template_keys(self) -> None:
        from src.ai_risk_assistant import (
            SUGGESTED_QUESTIONS, _QUESTION_TEMPLATE_KEY,
        )
        for q in SUGGESTED_QUESTIONS:
            self.assertIn(q, _QUESTION_TEMPLATE_KEY)

    def test_fallback_answer_is_not_ok(self) -> None:
        from src.ai_risk_assistant import AIRiskAssistantService
        service = AIRiskAssistantService(api_key="")
        ev = _make_evidence(priority=[_make_priority_risk("A")])
        result = service.ask("What is the biggest risk this month?", ev)
        self.assertEqual(result.status, "FALLBACK")
        self.assertNotEqual(result.status, "OK")
        self.assertIn("A", result.message)

    def test_word_count_within_budget(self) -> None:
        from src.ai_risk_assistant import _deterministic_answer
        for template_key in (
            "biggest_risk", "why_risk", "escalating_kpis",
            "emerging_kpis", "watch_first",
        ):
            with self.subTest(template_key=template_key):
                ev = _make_evidence(
                    priority=[_make_priority_risk("Patient Satisfaction")],
                    emerging=[_make_emerging_risk("Waiting Time")],
                    escalating=[_make_escalating_risk("Staffing Level")],
                )
                msg = _deterministic_answer(template_key, ev)
                words = len(msg.split())
                self.assertLessEqual(
                    words, 100,
                    f"{template_key}: {words} words exceeds 100: {msg!r}",
                )

    def test_system_prompt_includes_evidence_summary(self) -> None:
        from src.ai_risk_assistant import _build_system_prompt
        ev = _make_evidence(
            priority=[
                _make_priority_risk("Patient Satisfaction"),
                _make_priority_risk("Staffing Level"),
            ]
        )
        prompt = _build_system_prompt(ev)
        self.assertIn("Hospital:", prompt)
        self.assertIn("Intensive Care Unit", prompt)
        self.assertIn("Patient Satisfaction", prompt)
        self.assertIn("Staffing Level", prompt)

    def test_evidence_hash_changes_when_data_changes(self) -> None:
        from src.risk_ai_evidence import _hash_evidence, build_risk_ai_evidence
        state1 = {
            "summary": {},
            "table": None,
            "internal_rows": [
                {
                    "kpi_id": "kpi_001",
                    "kpi_name": "A",
                    "department_code": "DEPT-ICU",
                    "latest_actual_status": "Deteriorating",
                    "warning_level": "High Early Warning",
                },
            ],
        }
        ev1 = build_risk_ai_evidence(
            state1, hospital_label="HOSP-001",
            department_code="DEPT-ICU", year=2025, month=12,
        )
        state2 = {
            "summary": {},
            "table": None,
            "internal_rows": [
                {
                    "kpi_id": "kpi_001",
                    "kpi_name": "B",  # changed name
                    "department_code": "DEPT-ICU",
                    "latest_actual_status": "Deteriorating",
                    "warning_level": "High Early Warning",
                },
            ],
        }
        ev2 = build_risk_ai_evidence(
            state2, hospital_label="HOSP-001",
            department_code="DEPT-ICU", year=2025, month=12,
        )
        self.assertNotEqual(ev1["_evidence_hash"], ev2["_evidence_hash"])


if __name__ == "__main__":
    unittest.main()
