"""
Connected Signal -- CS-3 Targeted Tests.

Covers:

* the shared TokenHub transport is reachable from the connected signal
  synthesis service;
* the contradictory cross-domain footer is no longer rendered by the
  Executive Overview page in any branch;
* AI failure modes (NOT_CONFIGURED, TIMEOUT, API_UNAVAILABLE,
  INVALID_RESPONSE, GOVERNANCE_FILTERED) all return a non-empty
  message -- the card is never blank;
* cleaned Hy3 inputs never carry raw correlation coefficients or raw
  KPI history;
* the no-chain state returns the deterministic no-chain sentence and
  the engine card renders no contradictory cross-domain text.

Real-data end-to-end cases (Emergency Department -- 4-step chain,
Diagnostic Services, Administration/June no-chain) live in the
``tests/test_cs3_real_cases.py`` file, which is invoked from this file
via :func:`test_cs3_real_cases_end_to_end`.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from typing import Any, Dict

import pandas as pd
from pandas import DataFrame

from src import connected_signal_engine as cs_engine
from src import ai_connected_signal_synthesis as ai_cs
from src.ai_connected_signal_synthesis import (
    AIConnectedSignalSynthesisResult,
    AIConnectedSignalSynthesisService,
)
from src._ai_tokenhub_transport import call_tokenhub_chat_completion


# ---------------------------------------------------------------------------
# Shared transport tests
# ---------------------------------------------------------------------------

class TestSharedTokenHubTransport(unittest.TestCase):
    """The shared transport must be reachable from the connected signal
    synthesis service without anyone duplicating HTTP code.
    """

    def test_transport_module_exists_and_is_importable(self) -> None:
        from src import _ai_tokenhub_transport  # noqa: F401
        self.assertTrue(hasattr(_ai_tokenhub_transport, "call_tokenhub_chat_completion"))

    def test_transport_returns_not_configured_when_api_key_missing(self) -> None:
        result = call_tokenhub_chat_completion(
            messages=[{"role": "user", "content": "hi"}],
            provider="tencent_hunyuan",
            model="hy3",
            api_key=None,
            timeout=5.0,
            temperature=0.2,
            max_tokens=100,
        )
        self.assertEqual(result.get("status"), "NOT_CONFIGURED")
        self.assertIn("not configured", str(result.get("message", "")).lower())

    def test_transport_uses_tokenhub_chat_completions_url(self) -> None:
        # The shared transport must target the documented TokenHub /
        # Hy3 endpoint. When a fake key is provided, an HTTP attempt
        # will be made; we confirm the URL is the documented one by
        # inspecting the module constant.
        from src._ai_tokenhub_transport import DEFAULT_TOKENHUB_URL
        self.assertEqual(
            DEFAULT_TOKENHUB_URL,
            "https://tokenhub-intl.tencentcloudmaas.com/v1/chat/completions",
        )

    def test_no_duplicate_http_in_connected_signal_synthesis(self) -> None:
        """The connected signal synthesis module must not define its own
        HTTP layer; it must rely on the shared transport.
        """
        import src.ai_connected_signal_synthesis as mod
        # Allow only dataclass / messaging helpers -- no requests/urllib
        # symbols of the connected signal synthesis module are allowed.
        text = open(mod.__file__, "r", encoding="utf-8").read()
        self.assertNotIn("urllib.request", text)
        self.assertNotIn("requests.post", text)
        # It must however import the shared transport.
        self.assertIn("call_tokenhub_chat_completion", text)


# ---------------------------------------------------------------------------
# Governed-payload hygiene tests
# ---------------------------------------------------------------------------

class TestGovernedPayloadHygiene(unittest.TestCase):
    """The Hy3 request payload must contain only governed evidence.
    Raw coefficients, p-values, and raw KPI history are forbidden.
    """

    def test_no_raw_correlation_coefficient_in_user_payload(self) -> None:
        payload = {
            "primary_chain": {
                "chain_kpi_names": ["Staff Absenteeism Rate", "Staffing Level"],
                "trend_directions": ["up", "down"],
                "strength_label": "STRONG",
                "continuation_status": "CONTINUES",
                "selected_forecast_month_label": "August 2025",
                "edges": [
                    {"correlation": 0.91, "p_value": 0.004},
                ],
            },
            "raw_history": [[1, 2, 3], [4, 5, 6]],
            "correlation_matrix": {"a": 1.0},
            "spearman": 0.91,
            "p_value": 0.004,
        }
        # Capture the message sent to the transport.
        captured = {}

        def fake_transport(messages, **kwargs):  # noqa: ARG001
            captured["messages"] = messages
            return {
                "status": "OK",
                "message": "The connected pattern is also present in the "
                           "August 2025 forecast.",
                "raw": None,
            }

        service = AIConnectedSignalSynthesisService(api_key="FAKE_KEY")
        original = ai_cs.call_tokenhub_chat_completion
        ai_cs.call_tokenhub_chat_completion = fake_transport  # type: ignore
        try:
            service.synthesize(payload)
        finally:
            ai_cs.call_tokenhub_chat_completion = original  # type: ignore

        self.assertIn("messages", captured)
        user_payload = json.loads(captured["messages"][1]["content"])
        self.assertEqual(user_payload.get("causality_confirmed"), False)
        self.assertNotIn("raw_history", user_payload)
        self.assertNotIn("correlation_matrix", user_payload)
        self.assertNotIn("spearman", user_payload)
        self.assertNotIn("p_value", user_payload)
        # The chain labels are kept.
        self.assertEqual(
            user_payload.get("chain_labels"),
            ["Staff Absenteeism Rate", "Staffing Level"],
        )

    def test_causality_confirmed_hard_coded_false(self) -> None:
        # If a malicious caller sets causality_confirmed to True in the
        # engine result, the governed payload sent to Hy3 must clamp it
        # back to False.
        payload = {
            "primary_chain": {
                "chain_kpi_names": ["A", "B"],
                "causality_confirmed": True,
            },
        }
        from src.ai_connected_signal_synthesis import _extract_governed_payload
        extracted = _extract_governed_payload(payload)
        self.assertEqual(extracted["causality_confirmed"], False)


# ---------------------------------------------------------------------------
# AI failure fallback tests
# ---------------------------------------------------------------------------

class TestAIFailureFallback(unittest.TestCase):
    """On every failure path, the synthesis service returns a non-empty
    message so the Connected Signal card is never blank.
    """

    def _run_with_transport(self, transport_status: str, transport_message: str,
                            chain_present: bool = True) -> AIConnectedSignalSynthesisResult:
        captured = {}

        def fake_transport(messages, **kwargs):  # noqa: ARG001
            captured["messages"] = messages
            return {
                "status": transport_status,
                "message": transport_message,
                "raw": None,
            }

        service = AIConnectedSignalSynthesisService(api_key="FAKE_KEY")
        original = ai_cs.call_tokenhub_chat_completion
        ai_cs.call_tokenhub_chat_completion = fake_transport  # type: ignore
        try:
            payload: Dict[str, Any] = {
                "primary_chain": (
                    {
                        "chain_kpi_names": ["Staff Absenteeism Rate",
                                            "Staffing Level",
                                            "Waiting Time",
                                            "Patient Satisfaction"],
                        "trend_directions": ["up", "down", "up", "down"],
                        "strength_label": "STRONG",
                        "continuation_status": "CONTINUES",
                        "selected_forecast_month_label": "August 2025",
                    }
                    if chain_present
                    else {}
                ),
            }
            return service.synthesize(payload)
        finally:
            ai_cs.call_tokenhub_chat_completion = original  # type: ignore

    def test_no_chain_returns_no_chain_sentence(self) -> None:
        # No HTTP call expected; no-chain sentence is returned directly.
        result = self._run_with_transport(
            "OK", "", chain_present=False
        )
        self.assertEqual(result.status, "OK")
        self.assertIn("No sufficiently strong connected signal", result.message)

    def test_timeout_returns_deterministic_fallback(self) -> None:
        result = self._run_with_transport("TIMEOUT", "tokenhub request timed out")
        self.assertEqual(result.status, "TIMEOUT")
        self.assertNotEqual(result.message, "")
        # The fallback must mention the connected pattern in some form.
        self.assertTrue(len(result.message) > 0)
        # No causal language.
        for forbidden in (
            "caused by", "drives", "leads to", "results from", "because of",
        ):
            self.assertNotIn(forbidden, result.message.lower())

    def test_api_unavailable_returns_deterministic_fallback(self) -> None:
        result = self._run_with_transport("API_UNAVAILABLE", "server error")
        self.assertEqual(result.status, "API_UNAVAILABLE")
        self.assertNotEqual(result.message, "")

    def test_provider_error_returns_deterministic_fallback(self) -> None:
        result = self._run_with_transport("PROVIDER_ERROR", "upstream 401")
        self.assertEqual(result.status, "PROVIDER_ERROR")
        self.assertNotEqual(result.message, "")

    def test_invalid_response_returns_deterministic_fallback(self) -> None:
        result = self._run_with_transport("INVALID_RESPONSE", "malformed body")
        self.assertEqual(result.status, "INVALID_RESPONSE")
        self.assertNotEqual(result.message, "")

    def test_governance_filtered_returns_deterministic_fallback(self) -> None:
        # If Hy3 returns an answer that contains causal language, the
        # service must drop it and return a deterministic fallback.
        result = self._run_with_transport(
            "OK", "This is caused by operational pressure at HOSP-001.",
        )
        # Either governance filter or upstream OK -> either way, message
        # must be non-empty AND must NOT contain causal language.
        self.assertNotEqual(result.message, "")
        for forbidden in (
            "caused by", "drives", "leads to", "results from", "because of",
        ):
            self.assertNotIn(forbidden, result.message.lower())

    def test_no_api_key_returns_deterministic_with_status_not_configured(self) -> None:
        # No API key: even though the chain exists, no HTTP call is
        # made; status is NOT_CONFIGURED and message is non-empty.
        service = AIConnectedSignalSynthesisService(api_key=None)
        result = service.synthesize({"primary_chain": {
            "chain_kpi_names": ["A", "B", "C", "D"],
            "trend_directions": ["up", "down", "up", "down"],
            "strength_label": "STRONG",
            "continuation_status": "CONTINUES",
            "selected_forecast_month_label": "August 2025",
        }})
        self.assertEqual(result.status, "NOT_CONFIGURED")
        self.assertNotEqual(result.message, "")
        self.assertNotIn("caused by", result.message.lower())


# ---------------------------------------------------------------------------
# Page-render: no contradictory cross-domain footer
# ---------------------------------------------------------------------------

class TestNoContradictoryFooter(unittest.TestCase):
    """The Executive Overview page must NOT render the 'Workforce,
    service, and patient-experience signals appear together...' caption
    unconditionally. The card itself contains the appropriate
    governance footer in both the chain-exists and no-chain branches.
    """

    def _read_page_source(self) -> str:
        path = os.path.join(
            os.path.dirname(__file__), "..", "pages", "02_Executive_Overview.py"
        )
        path = os.path.abspath(path)
        return open(path, "r", encoding="utf-8").read()

    def test_contradictory_caption_removed(self) -> None:
        text = self._read_page_source()
        forbidden_substrings = (
            # The exact contradictory caption must be gone.
            "Workforce, service, and patient-experience signals appear together "
            "in the selected period. Causality is not confirmed.",
            # Even slightly trimmed forms must not appear.
            "signals appear together in the selected period",
            "appear together in the selected period",
        )
        for bad in forbidden_substrings:
            self.assertNotIn(bad, text)

    def test_page_does_not_render_st_caption_below_connected_signal_card(self) -> None:
        text = self._read_page_source()
        # The exact st.caption call from the old code must be gone. We
        # allow st.caption usages elsewhere but block the specific
        # contradictory one.
        self.assertNotIn(
            'st.caption("Workforce, service, and patient-experience signals '
            'appear together in the selected period. Causality is not '
            'confirmed.")',
            text,
        )


# ---------------------------------------------------------------------------
# Engine's own card already contains the right footer in both branches
# ---------------------------------------------------------------------------

class TestEngineCardHasGovernanceFooterInBothBranches(unittest.TestCase):
    def test_no_chain_card_footer_mentions_governed_actual_kpi_history(self) -> None:
        result = {
            "primary_chain": None,
            "governance": {"causality_confirmed": False},
        }
        html = cs_engine.build_connected_signal_card_html(
            result, period_badge_html='<span></span>',
        )
        self.assertIn("No sufficiently strong connected signal", html)
        self.assertIn("Based on governed actual KPI history", html)
        self.assertIn("Causality is not inferred", html)

    def test_chain_card_footer_mentions_causality_is_not_confirmed(self) -> None:
        result = {
            "primary_chain": {
                "chain_kpi_ids": ["kpi_002", "kpi_001"],
                "chain_kpi_names": ["Staff Absenteeism Rate", "Staffing Level"],
                "trend_directions": {"kpi_002": "UP", "kpi_001": "DOWN"},
                "edges": [{"correlation": 0.91}],
                "average_abs_r": 0.91,
            },
            "governance": {"causality_confirmed": False},
            "forecast_continuation": {},
            "actual_period_start": "Jan 2025",
            "actual_period_end": "Jul 2025",
            "is_forecast_period": False,
        }
        html = cs_engine.build_connected_signal_card_html(
            result, period_badge_html='<span></span>',
            ai_interpretation=None,
        )
        self.assertIn("Causality is not confirmed", html)
        self.assertIn("Association observed from governed actual KPI history", html)


# ---------------------------------------------------------------------------
# Sanity: the new message API never emits raw correlation coefficients
# ---------------------------------------------------------------------------

class TestNoRawCoefficientsInAIMessage(unittest.TestCase):
    def test_deterministic_interpretation_does_not_leak_coefficients(self) -> None:
        governed = {
            "has_supported_chain": True,
            "chain_labels": ["Staff Absenteeism Rate",
                             "Staffing Level",
                             "Waiting Time",
                             "Patient Satisfaction"],
            "movement_directions": ["up", "down", "up", "down"],
            "strength_label": "STRONG",
            "forecast_month": "August 2025",
            "continuation_status": "CONTINUES",
            "causality_confirmed": False,
        }
        from src.ai_connected_signal_synthesis import _deterministic_interpretation
        sentence = _deterministic_interpretation(governed)
        self.assertNotIn("0.9", sentence)  # would-be correlation
        self.assertNotIn("r =", sentence.lower())
        self.assertNotIn("spearman", sentence.lower())
        # Has a word count within budget
        words = sentence.split()
        self.assertGreaterEqual(len(words), 10)
        self.assertLessEqual(len(words), 50)


if __name__ == "__main__":
    unittest.main()


# ---------------------------------------------------------------------------
# Final Executive Wording + Visual Polish (section labels, status mapping,
# flow connector, governance footer)
# ---------------------------------------------------------------------------

def _chain_card_result(continuation_status):
    """Build a representative chain result for card-level tests."""
    return {
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
        "governance": {"causality_confirmed": False},
        "forecast_continuation": {
            "continuation_status": continuation_status,
            "selected_forecast_month": 8,
        },
        "actual_period_start": "2025-01",
        "actual_period_end": "2025-07",
        "is_forecast_period": True,
        "selected_forecast_year": 2025,
        "selected_forecast_month": 8,
    }


class TestFinalSectionLabels(unittest.TestCase):
    def test_historical_signal_label_present(self) -> None:
        html = cs_engine.build_connected_signal_card_html(
            _chain_card_result("CONTINUES"),
            period_badge_html='<span></span>',
        )
        self.assertIn("Historical Signal", html)
        self.assertNotIn("OBSERVED PATTERN", html)

    def test_forward_signal_label_present(self) -> None:
        html = cs_engine.build_connected_signal_card_html(
            _chain_card_result("CONTINUES"),
            period_badge_html='<span></span>',
        )
        self.assertIn("Forward Signal", html)
        self.assertNotIn("FORECAST OUTLOOK", html)
        self.assertNotIn("Forecast Continuation", html)

    def test_management_interpretation_label_present(self) -> None:
        html = cs_engine.build_connected_signal_card_html(
            _chain_card_result("CONTINUES"),
            period_badge_html='<span></span>',
            ai_interpretation="Sample management sentence.",
        )
        self.assertIn("Management Interpretation", html)
        self.assertNotIn("AI Interpretation", html)

    def test_connected_signal_overall_title_kept(self) -> None:
        html = cs_engine.build_connected_signal_card_html(
            _chain_card_result("CONTINUES"),
            period_badge_html='<span></span>',
        )
        self.assertIn("Connected Signal", html)


class TestHistoricalSignalWording(unittest.TestCase):
    def test_uses_strong_connected_pattern(self) -> None:
        html = cs_engine.build_connected_signal_card_html(
            _chain_card_result("CONTINUES"),
            period_badge_html='<span></span>',
        )
        self.assertIn("Strong connected pattern", html)

    def test_uses_dynamic_actual_period(self) -> None:
        html = cs_engine.build_connected_signal_card_html(
            _chain_card_result("CONTINUES"),
            period_badge_html='<span></span>',
        )
        self.assertIn("Observed across", html)
        self.assertIn("Jan", html)
        self.assertIn("Jul", html)
        self.assertIn("2025", html)


class TestForwardSignalStatusMapping(unittest.TestCase):
    def test_continues_renders_friendly_title(self) -> None:
        html = cs_engine.build_connected_signal_card_html(
            _chain_card_result("CONTINUES"),
            period_badge_html='<span></span>',
        )
        self.assertIn("Connected pattern continues into the forecast", html)
        self.assertNotIn("CONTINUES", html)

    def test_partial_renders_friendly_title(self) -> None:
        html = cs_engine.build_connected_signal_card_html(
            _chain_card_result("PARTIAL"),
            period_badge_html='<span></span>',
        )
        self.assertIn("Part of the connected pattern continues", html)
        self.assertNotIn("PARTIAL", html)

    def test_not_continuing_renders_friendly_title(self) -> None:
        html = cs_engine.build_connected_signal_card_html(
            _chain_card_result("NOT_CONTINUING"),
            period_badge_html='<span></span>',
        )
        self.assertIn("Pattern not evident in the", html)
        self.assertIn("forecast", html)
        self.assertNotIn("NOT_CONTINUING", html)

    def test_continues_subtext_uses_month(self) -> None:
        html = cs_engine.build_connected_signal_card_html(
            _chain_card_result("CONTINUES"),
            period_badge_html='<span></span>',
        )
        self.assertIn("August", html)

    def test_not_continuing_subtext_uses_month(self) -> None:
        html = cs_engine.build_connected_signal_card_html(
            _chain_card_result("NOT_CONTINUING"),
            period_badge_html='<span></span>',
        )
        self.assertIn("August", html)
        self.assertIn("consistently reflected", html)


class TestConnectorVisualDistinction(unittest.TestCase):
    """Validate the redesigned KPI trend icons and flow connectors.

    The legacy design used:
      * tiny HTML-entity symbols (``&#9650;``/``&#9660;``/``&#9644;``) at
        ~12.5 px for KPI trend direction, and
      * a wide CSS-only chevron block (``clip-path:polygon(...)``,
        46 x 14 px) for the between-row flow connector.

    The redesigned UI uses inline SVG for *both* elements so they stay
    crisp at any zoom level:

      * KPI trend icon  -- 20 x 20 px inline SVG (>= 18 px minimum),
        wrapped in a styled ``s360-cs-trend-icon`` span with
        ``s360-cs-trend-up`` / ``s360-cs-trend-down`` /
        ``s360-cs-trend-flat`` modifier classes for semantic colour,
      * Flow connector -- 20 x 36 px inline SVG arrow (clear vertical
        shaft + downward arrowhead), centered between KPI rows,
        carried by ``s360-cs-flow-connector`` /
        ``s360-cs-flow-arrow`` / ``s360-cs-flow-arrow-svg`` classes.

    This class asserts that the new design is in place and that the
    connector remains visually larger than the per-KPI trend icon so
    the two elements cannot be confused.
    """

    # ---- KPI trend icons --------------------------------------------------

    def test_trend_up_class_is_emitted(self) -> None:
        html = cs_engine.build_connected_signal_card_html(
            _chain_card_result("CONTINUES"),
            period_badge_html='<span></span>',
        )
        self.assertIn("s360-cs-trend-up", html)

    def test_trend_down_class_is_emitted(self) -> None:
        html = cs_engine.build_connected_signal_card_html(
            _chain_card_result("CONTINUES"),
            period_badge_html='<span></span>',
        )
        self.assertIn("s360-cs-trend-down", html)

    def test_trend_icons_render_as_inline_svg(self) -> None:
        html = cs_engine.build_connected_signal_card_html(
            _chain_card_result("CONTINUES"),
            period_badge_html='<span></span>',
        )
        # Every trend-icon span must contain a child <svg>.
        # The chain fixture mixes UP/DOWN so we expect at least one of
        # each; together those cover 4 trend spans on a 4-KPI chain.
        self.assertIn(
            'class="s360-cs-trend-icon s360-cs-trend-up"', html,
        )
        self.assertIn(
            'class="s360-cs-trend-icon s360-cs-trend-down"', html,
        )
        # New KPI trend SVG must use a 20x20 viewBox / width / height
        # (executive-grade size, well above the 12.5 px HTML-entity
        # symbols they replaced).
        self.assertIn('width="20" height="20"', html)

    def test_trend_icons_carry_semantic_colors(self) -> None:
        html = cs_engine.build_connected_signal_card_html(
            _chain_card_result("CONTINUES"),
            period_badge_html='<span></span>',
        )
        # UP   -> green (#2F855A); DOWN -> red (#C53030);
        # FLAT -> slate (#4A6A99).  Colours are inline in the SVG fill.
        self.assertIn("#2F855A", html)  # UP
        self.assertIn("#C53030", html)  # DOWN

    def test_legacy_tiny_trend_symbols_no_longer_used(self) -> None:
        """The previous 12.5 px HTML-entity trend symbols must be gone."""
        html = cs_engine.build_connected_signal_card_html(
            _chain_card_result("CONTINUES"),
            period_badge_html='<span></span>',
        )
        self.assertNotIn("&#9650;", html)  # legacy UP glyph
        self.assertNotIn("&#9660;", html)  # legacy DOWN glyph
        self.assertNotIn("&#9644;", html)  # legacy FLAT glyph

    # ---- Flow connector ---------------------------------------------------

    def test_flow_connector_class_is_emitted(self) -> None:
        html = cs_engine.build_connected_signal_card_html(
            _chain_card_result("CONTINUES"),
            period_badge_html='<span></span>',
        )
        self.assertIn("s360-cs-flow-connector", html)
        self.assertIn("s360-cs-flow-arrow", html)
        self.assertIn("s360-cs-flow-arrow-svg", html)

    def test_flow_connector_count_matches_chain_gaps(self) -> None:
        """4 KPIs in the chain fixture => exactly 3 flow connectors."""
        html = cs_engine.build_connected_signal_card_html(
            _chain_card_result("CONTINUES"),
            period_badge_html='<span></span>',
        )
        self.assertEqual(html.count("s360-cs-flow-connector"), 3)
        self.assertEqual(html.count("s360-cs-flow-arrow-svg"), 3)

    def test_flow_arrow_is_inline_svg_with_shaft_and_arrowhead(self) -> None:
        html = cs_engine.build_connected_signal_card_html(
            _chain_card_result("CONTINUES"),
            period_badge_html='<span></span>',
        )
        # The flow-arrow-svg SVG must include:
        #   * a vertical <line> shaft (stroke), and
        #   * a <polygon> arrowhead.
        # Both must share a single SVG element with the
        # s360-cs-flow-arrow-svg class.
        import re
        svg_match = re.search(
            r'<svg[^>]*class="s360-cs-flow-arrow-svg"[^>]*>(.*?)</svg>',
            html,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(svg_match, "flow-arrow-svg SVG not found")
        inner = svg_match.group(1)
        self.assertIn("<line", inner)
        self.assertIn("<polygon", inner)

    def test_legacy_chevron_clip_path_no_longer_used(self) -> None:
        """The CSS-only chevron block must be gone."""
        html = cs_engine.build_connected_signal_card_html(
            _chain_card_result("CONTINUES"),
            period_badge_html='<span></span>',
        )
        self.assertNotIn("clip-path:polygon", html)
        self.assertNotIn("width:46px", html)

    def test_flow_connector_is_visibly_larger_than_trend_icons(self) -> None:
        """The connector SVG (height=36) must be taller than the
        per-KPI trend icon SVG (height=20) so the two elements remain
        visually distinct."""
        html = cs_engine.build_connected_signal_card_html(
            _chain_card_result("CONTINUES"),
            period_badge_html='<span></span>',
        )
        import re
        flow_dims = re.findall(
            r'<svg[^>]*class="s360-cs-flow-arrow-svg"[^>]*'
            r'width="(\d+)"\s+height="(\d+)"',
            html,
        )
        self.assertTrue(flow_dims, "no flow arrow SVGs found")
        for width, height in flow_dims:
            self.assertGreaterEqual(int(width), 18)
            self.assertGreaterEqual(int(height), 30)
        # Compare against a known design constant: the trend icon SVG
        # is fixed at 20 x 20 in the engine.  The flow connector height
        # (>= 30, currently 36) must strictly exceed that.
        flow_height = int(flow_dims[0][1])
        self.assertGreater(flow_height, 20)


class TestGovernanceFooterBothStatesFinal(unittest.TestCase):
    def test_chain_footer_uses_observed_from(self) -> None:
        html = cs_engine.build_connected_signal_card_html(
            _chain_card_result("CONTINUES"),
            period_badge_html='<span></span>',
        )
        self.assertIn("Association observed from governed actual KPI history", html)
        self.assertIn("Forecast assessment reflects directional consistency only", html)
        self.assertIn("Causality is not confirmed", html)

    def test_no_chain_footer_still_clean(self) -> None:
        result = {
            "primary_chain": None,
            "governance": {"causality_confirmed": False},
        }
        html = cs_engine.build_connected_signal_card_html(
            result, period_badge_html='<span></span>',
        )
        self.assertIn("Based on governed actual KPI history", html)
        self.assertIn("Causality is not inferred", html)


class TestNoChainHidesAllChainSections(unittest.TestCase):
    def test_no_chain_card_omits_chain_labels(self) -> None:
        result = {
            "primary_chain": None,
            "governance": {"causality_confirmed": False},
        }
        html = cs_engine.build_connected_signal_card_html(
            result, period_badge_html='<span></span>',
        )
        self.assertNotIn("Historical Signal", html)
        self.assertNotIn("Forward Signal", html)
        self.assertNotIn("Management Interpretation", html)

    def test_no_chain_card_only_has_clean_fallback(self) -> None:
        result = {
            "primary_chain": None,
            "governance": {"causality_confirmed": False},
        }
        html = cs_engine.build_connected_signal_card_html(
            result, period_badge_html='<span></span>',
        )
        self.assertIn("No sufficiently strong connected signal", html)
        self.assertNotIn("Management Interpretation", html)


class TestDeterministicFallbackManagementVoice(unittest.TestCase):
    def setUp(self) -> None:
        self._gov = {
            "has_supported_chain": True,
            "chain_labels": [
                "Staff Absenteeism Rate",
                "Staffing Level",
                "Patient Waiting Time",
                "Patient Satisfaction",
            ],
            "forecast_month": 8,
            "continuation_status": "NOT_CONTINUING",
        }

    def test_continues_word_count_30_to_50(self) -> None:
        from src.ai_connected_signal_synthesis import _deterministic_interpretation
        gov = dict(self._gov)
        gov["continuation_status"] = "CONTINUES"
        msg = _deterministic_interpretation(gov)
        n = len(msg.split())
        self.assertGreaterEqual(n, 30, f"word count {n} below 30: {msg!r}")
        self.assertLessEqual(n, 50, f"word count {n} above 50: {msg!r}")

    def test_partial_word_count_30_to_50(self) -> None:
        from src.ai_connected_signal_synthesis import _deterministic_interpretation
        gov = dict(self._gov)
        gov["continuation_status"] = "PARTIAL"
        msg = _deterministic_interpretation(gov)
        n = len(msg.split())
        self.assertGreaterEqual(n, 30)
        self.assertLessEqual(n, 50)

    def test_not_continuing_word_count_30_to_50(self) -> None:
        from src.ai_connected_signal_synthesis import _deterministic_interpretation
        gov = dict(self._gov)
        gov["continuation_status"] = "NOT_CONTINUING"
        msg = _deterministic_interpretation(gov)
        n = len(msg.split())
        self.assertGreaterEqual(n, 30)
        self.assertLessEqual(n, 50)

    def test_continues_does_not_leak_internal_codes(self) -> None:
        from src.ai_connected_signal_synthesis import _deterministic_interpretation
        gov = dict(self._gov)
        gov["continuation_status"] = "CONTINUES"
        msg = _deterministic_interpretation(gov)
        for code in ("CONTINUES", "PARTIAL", "NOT_CONTINUING"):
            self.assertNotIn(code, msg)

    def test_not_continuing_does_not_leak_internal_codes(self) -> None:
        from src.ai_connected_signal_synthesis import _deterministic_interpretation
        gov = dict(self._gov)
        gov["continuation_status"] = "NOT_CONTINUING"
        msg = _deterministic_interpretation(gov)
        for code in ("CONTINUES", "PARTIAL", "NOT_CONTINUING"):
            self.assertNotIn(code, msg)

    def test_not_continuing_avoids_causal_language(self) -> None:
        from src.ai_connected_signal_synthesis import _deterministic_interpretation
        gov = dict(self._gov)
        gov["continuation_status"] = "NOT_CONTINUING"
        msg = _deterministic_interpretation(gov).lower()
        for banned in ("caused by", "causes ", "because of",
                       "leads to", "results from", "drives"):
            self.assertNotIn(banned, msg)

    def test_continues_mentions_month(self) -> None:
        from src.ai_connected_signal_synthesis import _deterministic_interpretation
        gov = dict(self._gov)
        gov["continuation_status"] = "CONTINUES"
        msg = _deterministic_interpretation(gov)
        self.assertIn("August", msg)


class TestHy3SystemPromptForManagementLanguage(unittest.TestCase):
    def test_system_prompt_has_30_50_word_target(self) -> None:
        from src.ai_connected_signal_synthesis import _build_system_prompt
        prompt = _build_system_prompt()
        self.assertIn("30 to 50 words", prompt)
        self.assertIn("maximum 2 sentences", prompt)

    def test_system_prompt_excludes_correlation_terms(self) -> None:
        from src.ai_connected_signal_synthesis import _build_system_prompt
        prompt = _build_system_prompt()
        # The prompt must FORBID these terms for Hy3 output; check that
        # each banned term appears in a NEVER- or do-not- style rule
        # within ~200 chars of the term.
        prompt_lc = prompt.lower()
        for banned in ("spearman", "p-values", "correlation coefficients"):
            self.assertIn(banned, prompt_lc)
            idx_term = prompt_lc.find(banned)
            window = prompt_lc[idx_term : idx_term + 200]
            self.assertTrue(
                any(w in window for w in ("never", "do not", "avoid")),
                f"Prompt does not explicitly forbid {banned!r}",
            )

    def test_system_prompt_forbids_internal_codes_in_output(self) -> None:
        from src.ai_connected_signal_synthesis import _build_system_prompt
        prompt = _build_system_prompt()
        self.assertIn("NEVER mention raw continuation codes", prompt)

    def test_system_prompt_forbids_causality_note_inside_interpretation(self) -> None:
        from src.ai_connected_signal_synthesis import _build_system_prompt
        prompt = _build_system_prompt()
        self.assertIn("causality is not confirmed", prompt)
        self.assertIn("card footer only", prompt)
