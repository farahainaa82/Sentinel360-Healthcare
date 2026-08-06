"""Connected Signal targeted tests: management-interpretation rendering fix.

Covers the bug where the Connected Signal card was rendering the entire AI
result object (Python dict representation) instead of the inner message
string, plus the new state-specific Hy3 wording requirements.

The contract under test:

  * dict AI result  -- extract ``message`` only, never stringify the dict.
  * dataclass AI result -- extract ``message`` only, never stringify the obj.
  * The "status" field, the dict braces, the field names, and any Python
    ``repr`` are never visible in the card body.
  * The Hy3 badge and provenance caption only appear when the synthesis
    status is "OK" (live Tencent Hy3).
  * The deterministic fallback hides the Hy3 badge and the provenance
    caption.
  * CONTINUES / PARTIAL / NOT_CONTINUING wording is management-specific
    and contains the actual KPI chain labels.
  * No causal language is used.
  * The governance footer text remains unchanged.
"""
from __future__ import annotations

import unittest
from dataclasses import dataclass
from typing import Any, Dict, Optional


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_html(ai_interpretation: Any) -> str:
    """Invoke the Connected Signal card builder with a minimal valid result.

    The builder accepts a dict result shape and the AI interpretation can
    be a dict, a dataclass, a plain string, or None.
    """
    from src.connected_signal_engine import build_connected_signal_card_html

    result: Dict[str, Any] = {
        "primary_chain": {
            "chain_kpi_ids": ["kpi_002", "kpi_001", "kpi_004", "kpi_006"],
            "chain_kpi_names": [
                "Staff Absenteeism Rate",
                "Staffing Level",
                "Patient Waiting Time",
                "Patient Satisfaction",
            ],
            "trend_directions": {
                "kpi_002": "UP",
                "kpi_001": "DOWN",
                "kpi_004": "UP",
                "kpi_006": "DOWN",
            },
            "edges": [{"correlation": 0.91}],
            "average_abs_r": 0.91,
        },
        "governance": {"causality_confirmed": False, "warning_level": "watch", "confidence": "moderate"},
        "forecast_continuation": {
            "continuation_status": "NOT_CONTINUING",
            "selected_forecast_month": 8,
        },
        "actual_period_start": "2025-01",
        "actual_period_end": "2025-07",
        "is_forecast_period": True,
        "selected_forecast_year": 2025,
        "selected_forecast_month": 8,
    }
    return build_connected_signal_card_html(
        result,
        period_badge_html='<span class="period-badge">Aug 2025</span>',
        ai_interpretation=ai_interpretation,
    )


@dataclass
class _AIResultObject:
    """Dataclass-style AI synthesis result (mirror of the real one)."""

    status: str
    message: str
    model_provider: str = "tencent_hy3"
    model_name: str = "hy3"


# ---------------------------------------------------------------------------
# A. dict AI result renders only message
# ---------------------------------------------------------------------------

class TestDictAIRendersOnlyMessage(unittest.TestCase):
    """A. dict-shaped AI result must render ONLY the inner message string."""

    def test_dict_message_appears_verbatim(self) -> None:
        msg = "Historically, KPI A moved together with KPI B and KPI C. The August forecast does not show the full pattern continuing."
        html = _build_html({"status": "OK", "message": msg})
        self.assertIn(msg, html)

    def test_dict_does_not_render_status_field_visible(self) -> None:
        html = _build_html({"status": "OK", "message": "A clean management sentence."})
        # The literal "status" field label should not appear as a visible
        # line in the card body.
        self.assertNotIn("'status'", html)
        self.assertNotIn('"status"', html)

    def test_dict_does_not_render_message_field_label(self) -> None:
        html = _build_html({"status": "OK", "message": "A clean management sentence."})
        # The literal "message" key should not appear as visible text.
        self.assertNotIn("'message'", html)
        self.assertNotIn('"message"', html)

    def test_dict_braces_never_visible(self) -> None:
        html = _build_html({"status": "OK", "message": "A clean management sentence."})
        self.assertNotIn("{", html)
        self.assertNotIn("}", html)

    def test_dict_does_not_render_str_repr(self) -> None:
        html = _build_html({"status": "OK", "message": "A clean management sentence."})
        # The full dict repr must not appear anywhere.
        self.assertNotIn("{'status': 'OK', 'message':", html)
        self.assertNotIn('{"status": "OK", "message":', html)


# ---------------------------------------------------------------------------
# B. dataclass AI result renders only message
# ---------------------------------------------------------------------------

class TestDataclassAIRendersOnlyMessage(unittest.TestCase):
    """B. dataclass / object AI result must render ONLY ``.message``."""

    def test_dataclass_message_appears_verbatim(self) -> None:
        msg = "Historically, KPI A moved together with KPI B. The August forecast continues to reflect the same pattern."
        html = _build_html(_AIResultObject(status="OK", message=msg))
        self.assertIn(msg, html)

    def test_dataclass_does_not_leak_object_repr(self) -> None:
        html = _build_html(_AIResultObject(status="OK", message="A clean sentence."))
        # The full object repr must not appear.
        self.assertNotIn("_AIResultObject(", html)
        self.assertNotIn("AIResultObject(", html)

    def test_dataclass_does_not_leak_attribute_names(self) -> None:
        html = _build_html(_AIResultObject(status="OK", message="A clean sentence."))
        self.assertNotIn("model_provider", html)
        self.assertNotIn("model_name", html)


# ---------------------------------------------------------------------------
# C. status field is never visibly rendered
# ---------------------------------------------------------------------------

class TestStatusFieldNeverVisible(unittest.TestCase):
    """C. The synthesis status value is never rendered into the body."""

    def test_ok_status_not_in_body(self) -> None:
        html = _build_html({"status": "OK", "message": "Sentence body."})
        # The literal token "OK" should not appear as a standalone status
        # badge in the management interpretation area.  (We do allow the
        # word "OK" in any other context; the test only checks the
        # structural fields of the AI result are gone.)
        self.assertNotIn("'status': 'OK'", html)
        self.assertNotIn('"status": "OK"', html)

    def test_error_status_not_in_body(self) -> None:
        html = _build_html({"status": "AI_ERROR", "message": "Sentence body."})
        self.assertNotIn("AI_ERROR", html)

    def test_fallback_status_not_in_body(self) -> None:
        html = _build_html({"status": "FALLBACK_NO_API_KEY", "message": "Sentence body."})
        self.assertNotIn("FALLBACK_NO_API_KEY", html)


# ---------------------------------------------------------------------------
# D. Python dict braces / field names are never visible
# ---------------------------------------------------------------------------

class TestDictBracesNeverVisible(unittest.TestCase):
    """D. Card must never expose Python/JSON structural characters."""

    def test_braces_absent_for_ok(self) -> None:
        html = _build_html({"status": "OK", "message": "Sentence."})
        self.assertNotIn("{", html)
        self.assertNotIn("}", html)

    def test_colon_key_value_pairs_absent(self) -> None:
        html = _build_html({"status": "OK", "message": "Sentence."})
        # The AI result contains a colon, but a colon like `'status':`
        # should never appear.  We allow normal English colons.
        self.assertNotIn("'status':", html)
        self.assertNotIn('"status":', html)
        self.assertNotIn("'message':", html)
        self.assertNotIn('"message":', html)


# ---------------------------------------------------------------------------
# E. OK shows badge + caption
# ---------------------------------------------------------------------------

class TestOKShowsBadgeAndCaption(unittest.TestCase):
    """E. When status == OK, the Hy3 badge and the provenance caption
    must both be present in the rendered card."""

    def test_dict_ok_shows_badge(self) -> None:
        html = _build_html({"status": "OK", "message": "Sentence."})
        self.assertIn("AI-ASSISTED", html)
        self.assertIn("Tencent Hy3", html)

    def test_dict_ok_shows_provenance_caption(self) -> None:
        html = _build_html({"status": "OK", "message": "Sentence."})
        self.assertIn("Generated from governed Sentinel360", html)
        self.assertIn("connected-signal evidence", html)

    def test_dataclass_ok_shows_badge(self) -> None:
        html = _build_html(_AIResultObject(status="OK", message="Sentence."))
        self.assertIn("AI-ASSISTED", html)
        self.assertIn("Tencent Hy3", html)


# ---------------------------------------------------------------------------
# F. Fallback hides badge + caption
# ---------------------------------------------------------------------------

class TestFallbackHidesBadgeAndCaption(unittest.TestCase):
    """F. When status != OK, no Hy3 badge and no provenance caption."""

    def test_not_configured_hides_badge(self) -> None:
        html = _build_html({"status": "AI_NOT_CONFIGURED", "message": "Sentence."})
        self.assertNotIn("AI-ASSISTED", html)
        self.assertNotIn("Tencent Hy3", html)

    def test_not_configured_hides_provenance_caption(self) -> None:
        html = _build_html({"status": "AI_NOT_CONFIGURED", "message": "Sentence."})
        self.assertNotIn("Generated from governed Sentinel360", html)

    def test_bare_string_fallback_hides_badge(self) -> None:
        # A plain string is treated as deterministic fallback.
        html = _build_html("Just a deterministic sentence.")
        self.assertNotIn("AI-ASSISTED", html)
        self.assertNotIn("Tencent Hy3", html)

    def test_none_hides_badge(self) -> None:
        html = _build_html(None)
        self.assertNotIn("AI-ASSISTED", html)
        self.assertNotIn("Tencent Hy3", html)

    def test_ai_error_hides_badge(self) -> None:
        html = _build_html({"status": "AI_ERROR", "message": "Sentence."})
        self.assertNotIn("AI-ASSISTED", html)


# ---------------------------------------------------------------------------
# G. NOT_CONTINUING wording is management-specific
# ---------------------------------------------------------------------------

class TestNotContinuingWording(unittest.TestCase):
    """G. NOT_CONTINUING fallback must use management-specific language."""

    def setUp(self) -> None:
        from src.ai_connected_signal_synthesis import _deterministic_interpretation
        self._msg = _deterministic_interpretation({
            "chain_labels": [
                "Staff Absenteeism Rate",
                "Staffing Level",
                "Patient Waiting Time",
                "Patient Satisfaction",
            ],
            "forecast_month": 8,
            "continuation_status": "NOT_CONTINUING",
        })

    def test_message_mentions_month(self) -> None:
        self.assertIn("August", self._msg)

    def test_message_mentions_chain_kpis(self) -> None:
        for kpi in (
            "Staff Absenteeism Rate",
            "Staffing Level",
            "Patient Waiting Time",
            "Patient Satisfaction",
        ):
            self.assertIn(kpi, self._msg)

    def test_message_uses_connected_pattern_phrase(self) -> None:
        low = self._msg.lower()
        self.assertIn("moved together", low)

    def test_message_does_not_continue_phrase(self) -> None:
        # NOT_CONTINUING must not say "continues to reflect the same pattern"
        low = self._msg.lower()
        self.assertNotIn("continues to reflect the same pattern", low)

    def test_message_does_not_leak_status_code(self) -> None:
        self.assertNotIn("NOT_CONTINUING", self._msg)

    def test_message_guides_to_treat_as_separate_signals(self) -> None:
        # Management should be guided to treat the KPIs as separate
        # emerging signals rather than a sustained connected risk.
        low = self._msg.lower()
        self.assertTrue(
            "separate" in low or "individually" in low,
            f"NOT_CONTINUING wording should guide management to treat "
            f"KPIs separately; got: {self._msg!r}",
        )


# ---------------------------------------------------------------------------
# H. CONTINUES wording is management-specific
# ---------------------------------------------------------------------------

class TestContinuesWording(unittest.TestCase):
    """H. CONTINUES fallback must use management-specific language."""

    def setUp(self) -> None:
        from src.ai_connected_signal_synthesis import _deterministic_interpretation
        self._msg = _deterministic_interpretation({
            "chain_labels": [
                "Staff Absenteeism Rate",
                "Staffing Level",
                "Patient Waiting Time",
                "Patient Satisfaction",
            ],
            "forecast_month": 8,
            "continuation_status": "CONTINUES",
        })

    def test_message_mentions_month(self) -> None:
        self.assertIn("August", self._msg)

    def test_message_mentions_chain_kpis(self) -> None:
        for kpi in (
            "Staff Absenteeism Rate",
            "Staffing Level",
            "Patient Waiting Time",
            "Patient Satisfaction",
        ):
            self.assertIn(kpi, self._msg)

    def test_message_indicates_pattern_continues(self) -> None:
        low = self._msg.lower()
        self.assertIn("continues to reflect the same pattern", low)

    def test_message_does_not_leak_status_code(self) -> None:
        self.assertNotIn("CONTINUES", self._msg)

    def test_message_signals_sustained_connected_risk(self) -> None:
        # CONTINUES should signal a sustained connected operational signal.
        low = self._msg.lower()
        self.assertIn("sustained connected operational signal", low)


# ---------------------------------------------------------------------------
# I. PARTIAL wording is management-specific
# ---------------------------------------------------------------------------

class TestPartialWording(unittest.TestCase):
    """I. PARTIAL fallback must use management-specific language."""

    def setUp(self) -> None:
        from src.ai_connected_signal_synthesis import _deterministic_interpretation
        self._msg = _deterministic_interpretation({
            "chain_labels": [
                "Staff Absenteeism Rate",
                "Staffing Level",
                "Patient Waiting Time",
                "Patient Satisfaction",
            ],
            "forecast_month": 8,
            "continuation_status": "PARTIAL",
        })

    def test_message_mentions_month(self) -> None:
        self.assertIn("August", self._msg)

    def test_message_indicates_partial_continuation(self) -> None:
        low = self._msg.lower()
        self.assertIn("part of that sequence continuing", low)

    def test_message_guides_to_review_individually(self) -> None:
        low = self._msg.lower()
        self.assertIn("review the affected kpis individually", low)

    def test_message_does_not_leak_status_code(self) -> None:
        self.assertNotIn("PARTIAL", self._msg)

    def test_message_does_not_claim_full_continuation(self) -> None:
        # PARTIAL must not say the full sequence is continuing.
        low = self._msg.lower()
        self.assertNotIn("continues to reflect the same pattern", low)


# ---------------------------------------------------------------------------
# J. no causal language in the main interpretation
# ---------------------------------------------------------------------------

class TestNoCausalLanguage(unittest.TestCase):
    """J. The management interpretation never uses causal language."""

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

    def _check(self, status: str) -> None:
        from src.ai_connected_signal_synthesis import _deterministic_interpretation
        msg = _deterministic_interpretation({
            "chain_labels": [
                "Staff Absenteeism Rate",
                "Staffing Level",
                "Patient Waiting Time",
                "Patient Satisfaction",
            ],
            "forecast_month": 8,
            "continuation_status": status,
        }).lower()
        for phrase in self.CAUSAL_PHRASES:
            self.assertNotIn(
                phrase,
                msg,
                f"Causal phrase {phrase!r} found in {status!r} wording: {msg!r}",
            )

    def test_continues_no_causal(self) -> None:
        self._check("CONTINUES")

    def test_partial_no_causal(self) -> None:
        self._check("PARTIAL")

    def test_not_continuing_no_causal(self) -> None:
        self._check("NOT_CONTINUING")

    def test_system_prompt_forbids_causal(self) -> None:
        from src.ai_connected_signal_synthesis import _build_system_prompt
        prompt = _build_system_prompt().lower()
        # The system prompt must explicitly forbid the full causal phrase
        # set, including the new "caused", "drove", "led to", "resulted in".
        for phrase in ("caused", "drove", "led to", "resulted in"):
            self.assertIn(phrase, prompt)


# ---------------------------------------------------------------------------
# K. governance footer remains unchanged
# ---------------------------------------------------------------------------

class TestGovernanceFooterUnchanged(unittest.TestCase):
    """K. The governance footer text must be preserved verbatim."""

    FOOTER_PHRASE = (
        "Association observed from governed actual KPI history."
    )

    def test_footer_present_in_ok_card(self) -> None:
        html = _build_html({"status": "OK", "message": "Sentence."})
        self.assertIn("Causality is not confirmed.", html)
        self.assertIn(self.FOOTER_PHRASE, html)

    def test_footer_present_in_fallback_card(self) -> None:
        html = _build_html({"status": "AI_NOT_CONFIGURED", "message": "Sentence."})
        self.assertIn("Causality is not confirmed.", html)
        self.assertIn(self.FOOTER_PHRASE, html)

    def test_footer_present_with_bare_string(self) -> None:
        html = _build_html("Sentence.")
        self.assertIn("Causality is not confirmed.", html)

    def test_footer_present_with_dataclass(self) -> None:
        html = _build_html(_AIResultObject(status="OK", message="Sentence."))
        self.assertIn("Causality is not confirmed.", html)


# ---------------------------------------------------------------------------
# Helper: extraction directly verified
# ---------------------------------------------------------------------------

class TestExtractionHelper(unittest.TestCase):
    """Direct unit tests on the new extraction helper."""

    def test_extraction_dict(self) -> None:
        from src.connected_signal_engine import _extract_ai_message
        result = {"status": "OK", "message": "Body sentence."}
        self.assertEqual(_extract_ai_message(result), "Body sentence.")

    def test_extraction_dataclass(self) -> None:
        from src.connected_signal_engine import _extract_ai_message
        result = _AIResultObject(status="OK", message="Body sentence.")
        self.assertEqual(_extract_ai_message(result), "Body sentence.")

    def test_extraction_string(self) -> None:
        from src.connected_signal_engine import _extract_ai_message
        self.assertEqual(_extract_ai_message("Body sentence."), "Body sentence.")

    def test_extraction_none_returns_empty(self) -> None:
        from src.connected_signal_engine import _extract_ai_message
        self.assertEqual(_extract_ai_message(None), "")

    def test_extraction_dict_without_message_returns_empty(self) -> None:
        from src.connected_signal_engine import _extract_ai_message
        self.assertEqual(_extract_ai_message({"status": "OK"}), "")

    def test_extraction_unknown_shape_returns_empty(self) -> None:
        from src.connected_signal_engine import _extract_ai_message
        # An object without a ``message`` attribute must not be stringified.
        class _Opaque:
            pass
        self.assertEqual(_extract_ai_message(_Opaque()), "")

    def test_extraction_never_returns_dict_repr(self) -> None:
        from src.connected_signal_engine import _extract_ai_message
        result = {"status": "OK", "message": "Body."}
        out = _extract_ai_message(result)
        self.assertNotIn("{", out)
        self.assertNotIn("}", out)
        self.assertNotIn("'status'", out)


if __name__ == "__main__":
    unittest.main()
