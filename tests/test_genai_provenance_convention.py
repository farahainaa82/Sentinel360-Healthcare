"""
Tests for the unified GenAI provenance convention.

Covers the shared helper module ``src/genai_provenance_badge`` plus
the Connected Signal card builder integration. The shared helper is
the single source of truth for the "AI-ASSISTED · Tencent Hy3" badge
and its associated provenance caption. Both the KPI graph
interpretation card and the Connected Signal card MUST render the
badge using these helpers so the styling stays identical.

Scenarios:
  A. live Hy3 OK on KPI card
     - AI badge visible
     - forecast provenance caption visible
     - no bottom evidence footer
  B. Hy3 failure on KPI card
     - AI badge hidden
     - provenance hidden
     - deterministic text visible
     - no bottom evidence footer
  C. live Hy3 OK on Connected Signal
     - AI badge visible under MANAGEMENT INTERPRETATION
     - connected-signal provenance caption visible
     - governance footer retained
  D. Hy3 failure on Connected Signal
     - AI badge hidden
     - provenance caption hidden
     - deterministic interpretation visible
     - governance footer retained
  E. no supported Connected Signal chain
     - existing clean no-signal state remains unchanged
     - no misleading AI badge
"""

from __future__ import annotations

import os
import sys

import pytest

# Ensure project root is on path so src/ imports work as a package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


from src import connected_signal_engine
from src.connected_signal_engine import build_connected_signal_card_html
from src.genai_provenance_badge import (
    BADGE_LABEL,
    CS_PROVENANCE_CAPTION,
    KPI_PROVENANCE_CAPTION,
    is_hy3_live,
    render_hy3_badge_html,
    render_hy3_caption_html,
    render_hy3_provenance_html,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def chain_result() -> dict:
    """Minimal Connected Signal result with a supported chain."""
    return {
        "primary_chain": {
            "chain_kpi_ids": ["PATIENT_SATISFACTION", "WAIT_TIME_MIN"],
            "chain_kpi_names": ["Patient Satisfaction", "Wait Time"],
            "trend_directions": {
                "PATIENT_SATISFACTION": "UP",
                "WAIT_TIME_MIN": "DOWN",
            },
            "average_abs_r": 0.85,
            "edges": [
                {
                    "from_kpi": "PATIENT_SATISFACTION",
                    "to_kpi": "WAIT_TIME_MIN",
                    "spearman_r": -0.9,
                    "p_value": 0.01,
                    "n_observations": 7,
                }
            ],
        },
        "forecast_continuation": {
            "continuation_status": "CONTINUES",
        },
        "is_forecast_period": True,
        "actual_period_start": "Jan 2025",
        "actual_period_end": "Jul 2025",
        "selected_forecast_year": 2025,
        "selected_forecast_month": 8,
    }


@pytest.fixture
def no_chain_result() -> dict:
    """Connected Signal result with no supported chain (clean state)."""
    return {
        "primary_chain": None,
        "forecast_continuation": None,
        "is_forecast_period": False,
        "actual_period_start": "Jan 2025",
        "actual_period_end": "Jul 2025",
        "selected_forecast_year": 2025,
        "selected_forecast_month": 8,
    }


def _ok_ai_result(message: str = "Live Hy3 sentence for management.") -> dict:
    return {"status": "OK", "message": message}


def _fallback_ai_result(message: str = "Deterministic fallback sentence.") -> dict:
    return {"status": "NOT_CONFIGURED", "message": message}


# ---------------------------------------------------------------------------
# 1. Shared helper -- gate logic
# ---------------------------------------------------------------------------

class TestIsHy3Live:
    def test_none_returns_false(self):
        assert is_hy3_live(None) is False

    def test_dict_with_status_ok_returns_true(self):
        assert is_hy3_live({"status": "OK", "message": "x"}) is True

    def test_dict_with_status_not_configured_returns_false(self):
        assert is_hy3_live({"status": "NOT_CONFIGURED"}) is False

    def test_dict_with_status_timeout_returns_false(self):
        assert is_hy3_live({"status": "TIMEOUT"}) is False

    def test_dict_with_status_api_unavailable_returns_false(self):
        assert is_hy3_live({"status": "API_UNAVAILABLE"}) is False

    def test_dict_with_status_invalid_response_returns_false(self):
        assert is_hy3_live({"status": "INVALID_RESPONSE"}) is False

    def test_dict_with_status_provider_error_returns_false(self):
        assert is_hy3_live({"status": "PROVIDER_ERROR"}) is False

    def test_dict_with_status_governance_filtered_returns_false(self):
        assert is_hy3_live({"status": "GOVERNANCE_FILTERED"}) is False

    def test_empty_dict_returns_false(self):
        assert is_hy3_live({}) is False

    def test_dict_with_non_string_status_returns_false(self):
        assert is_hy3_live({"status": 200}) is False

    def test_object_with_status_attribute_ok_returns_true(self):
        class _R:
            status = "OK"
            message = "hi"
        assert is_hy3_live(_R()) is True

    def test_object_with_status_attribute_not_ok_returns_false(self):
        class _R:
            status = "TIMEOUT"
        assert is_hy3_live(_R()) is False

    def test_status_lowercase_ok_treated_as_ok(self):
        # The gate is case-insensitive on the literal "OK" string.
        assert is_hy3_live({"status": "ok"}) is True
        assert is_hy3_live({"status": " Ok "}) is True


# ---------------------------------------------------------------------------
# 2. Shared helper -- badge + caption renderers
# ---------------------------------------------------------------------------

class TestRenderHy3Badge:
    def test_badge_label_present(self):
        html = render_hy3_badge_html()
        assert "AI-ASSISTED" in html
        assert "Tencent Hy3" in html

    def test_badge_exact_wording(self):
        assert BADGE_LABEL == "AI-ASSISTED · Tencent Hy3"
        assert BADGE_LABEL in render_hy3_badge_html()

    def test_badge_has_sparkle_svg(self):
        html = render_hy3_badge_html()
        assert "<svg" in html
        assert "M8 0 L9.2 6.8" in html  # 4-point sparkle path

    def test_badge_pill_styling(self):
        html = render_hy3_badge_html()
        # Rounded pill: background + border-radius + small font
        assert "background:#E6EBF2" in html
        assert "border-radius:10px" in html
        assert "font-size:9px" in html
        assert "text-transform:uppercase" in html
        assert "font-weight:700" in html


class TestRenderHy3Caption:
    def test_kpi_caption_default(self):
        html = render_hy3_caption_html()
        assert "Generated from governed Sentinel360 forecast evidence" in html
        assert KPI_PROVENANCE_CAPTION in html

    def test_cs_caption(self):
        html = render_hy3_caption_html(scope="cs")
        assert "Generated from governed Sentinel360 connected-signal evidence" in html
        assert CS_PROVENANCE_CAPTION in html

    def test_caption_is_muted(self):
        html = render_hy3_caption_html()
        # Muted styling: grey + italic + small font
        assert "color:#9AA5B5" in html
        assert "font-style:italic" in html
        assert "font-size:10px" in html


class TestRenderHy3Provenance:
    def test_combined_renders_on_ok(self):
        html = render_hy3_provenance_html({"status": "OK"})
        assert "AI-ASSISTED · Tencent Hy3" in html
        assert "Generated from governed Sentinel360 forecast evidence" in html

    def test_combined_renders_on_ok_with_cs_scope(self):
        html = render_hy3_provenance_html({"status": "OK"}, scope="cs")
        assert "AI-ASSISTED · Tencent Hy3" in html
        assert "Generated from governed Sentinel360 connected-signal evidence" in html

    def test_combined_empty_on_fallback(self):
        html = render_hy3_provenance_html({"status": "NOT_CONFIGURED"})
        assert html == ""
        html2 = render_hy3_provenance_html({"status": "NOT_CONFIGURED"}, scope="cs")
        assert html2 == ""

    def test_combined_empty_on_none(self):
        assert render_hy3_provenance_html(None) == ""


# ---------------------------------------------------------------------------
# 3. Connected Signal -- live Hy3 OK
# ---------------------------------------------------------------------------

class TestConnectedSignalHy3Success:
    def test_badge_visible_under_management_interpretation(self, chain_result):
        html = build_connected_signal_card_html(
            chain_result,
            period_badge_html='<span>Aug 2025</span>',
            ai_interpretation=_ok_ai_result(),
        )
        assert "AI-ASSISTED · Tencent Hy3" in html

    def test_connected_signal_provenance_caption_visible(self, chain_result):
        html = build_connected_signal_card_html(
            chain_result,
            period_badge_html='<span>Aug 2025</span>',
            ai_interpretation=_ok_ai_result(),
        )
        assert "Generated from governed Sentinel360 connected-signal evidence" in html

    def test_kpi_provenance_caption_not_used(self, chain_result):
        """Connected Signal must use the CS caption, NOT the KPI caption."""
        html = build_connected_signal_card_html(
            chain_result,
            period_badge_html='<span>Aug 2025</span>',
            ai_interpretation=_ok_ai_result(),
        )
        assert "Generated from governed Sentinel360 forecast evidence" not in html

    def test_governance_footer_retained(self, chain_result):
        html = build_connected_signal_card_html(
            chain_result,
            period_badge_html='<span>Aug 2025</span>',
            ai_interpretation=_ok_ai_result(),
        )
        assert "Association observed from governed actual KPI history." in html
        assert "Forecast assessment reflects directional consistency only." in html
        assert "Causality is not confirmed." in html

    def test_badge_sits_before_interpretation(self, chain_result):
        """Badge must sit between MANAGEMENT INTERPRETATION label and the message text."""
        html = build_connected_signal_card_html(
            chain_result,
            period_badge_html='<span>Aug 2025</span>',
            ai_interpretation=_ok_ai_result("Live Hy3 sentence for management."),
        )
        pos_label = html.find("Management Interpretation")
        pos_badge = html.find("AI-ASSISTED · Tencent Hy3")
        pos_message = html.find("Live Hy3 sentence for management.")
        assert -1 < pos_label < pos_badge < pos_message

    def test_message_appears(self, chain_result):
        html = build_connected_signal_card_html(
            chain_result,
            period_badge_html='<span>Aug 2025</span>',
            ai_interpretation=_ok_ai_result("Live Hy3 sentence for management."),
        )
        assert "Live Hy3 sentence for management." in html

    def test_historical_signal_unchanged(self, chain_result):
        """Governed sections above management interpretation stay intact."""
        html = build_connected_signal_card_html(
            chain_result,
            period_badge_html='<span>Aug 2025</span>',
            ai_interpretation=_ok_ai_result(),
        )
        assert "Historical Signal" in html
        assert "Strong connected pattern" in html

    def test_uses_shared_badge_helper(self, chain_result):
        """Badge must use the shared styling -- substring of the helper output."""
        expected = render_hy3_badge_html()
        html = build_connected_signal_card_html(
            chain_result,
            period_badge_html='<span>Aug 2025</span>',
            ai_interpretation=_ok_ai_result(),
        )
        # The CS card should embed the shared badge verbatim.
        assert expected in html

    def test_sparkle_icon_present(self, chain_result):
        html = build_connected_signal_card_html(
            chain_result,
            period_badge_html='<span>Aug 2025</span>',
            ai_interpretation=_ok_ai_result(),
        )
        # The badge block must include the 4-point sparkle SVG.
        assert "M8 0 L9.2 6.8" in html


# ---------------------------------------------------------------------------
# 4. Connected Signal -- Hy3 failure (deterministic fallback)
# ---------------------------------------------------------------------------

class TestConnectedSignalHy3Failure:
    def test_badge_hidden_on_not_configured(self, chain_result):
        html = build_connected_signal_card_html(
            chain_result,
            period_badge_html='<span>Aug 2025</span>',
            ai_interpretation=_fallback_ai_result("Deterministic fallback sentence."),
        )
        assert "AI-ASSISTED · Tencent Hy3" not in html

    def test_provenance_caption_hidden_on_not_configured(self, chain_result):
        html = build_connected_signal_card_html(
            chain_result,
            period_badge_html='<span>Aug 2025</span>',
            ai_interpretation=_fallback_ai_result("Deterministic fallback sentence."),
        )
        assert "Generated from governed Sentinel360 connected-signal evidence" not in html
        assert "Generated from governed Sentinel360 forecast evidence" not in html

    def test_fallback_message_still_shown(self, chain_result):
        html = build_connected_signal_card_html(
            chain_result,
            period_badge_html='<span>Aug 2025</span>',
            ai_interpretation=_fallback_ai_result("Deterministic fallback sentence."),
        )
        assert "Deterministic fallback sentence." in html

    def test_governance_footer_retained_on_fallback(self, chain_result):
        html = build_connected_signal_card_html(
            chain_result,
            period_badge_html='<span>Aug 2025</span>',
            ai_interpretation=_fallback_ai_result("Deterministic fallback sentence."),
        )
        assert "Association observed from governed actual KPI history." in html
        assert "Causality is not confirmed." in html

    def test_badge_hidden_on_timeout_status(self, chain_result):
        html = build_connected_signal_card_html(
            chain_result,
            period_badge_html='<span>Aug 2025</span>',
            ai_interpretation={"status": "TIMEOUT", "message": "Timed out."},
        )
        assert "AI-ASSISTED · Tencent Hy3" not in html
        assert "Timed out." in html

    def test_badge_hidden_on_api_unavailable(self, chain_result):
        html = build_connected_signal_card_html(
            chain_result,
            period_badge_html='<span>Aug 2025</span>',
            ai_interpretation={"status": "API_UNAVAILABLE", "message": "Down."},
        )
        assert "AI-ASSISTED · Tencent Hy3" not in html

    def test_badge_hidden_on_invalid_response(self, chain_result):
        html = build_connected_signal_card_html(
            chain_result,
            period_badge_html='<span>Aug 2025</span>',
            ai_interpretation={"status": "INVALID_RESPONSE", "message": "Bad."},
        )
        assert "AI-ASSISTED · Tencent Hy3" not in html

    def test_badge_hidden_on_provider_error(self, chain_result):
        html = build_connected_signal_card_html(
            chain_result,
            period_badge_html='<span>Aug 2025</span>',
            ai_interpretation={"status": "PROVIDER_ERROR", "message": "Err."},
        )
        assert "AI-ASSISTED · Tencent Hy3" not in html

    def test_badge_hidden_on_governance_filtered(self, chain_result):
        html = build_connected_signal_card_html(
            chain_result,
            period_badge_html='<span>Aug 2025</span>',
            ai_interpretation={"status": "GOVERNANCE_FILTERED", "message": "Filtered."},
        )
        assert "AI-ASSISTED · Tencent Hy3" not in html

    def test_legacy_string_input_treated_as_fallback(self, chain_result):
        """A bare string (legacy cache value) is treated as deterministic
        fallback text and never labelled as AI-generated."""
        html = build_connected_signal_card_html(
            chain_result,
            period_badge_html='<span>Aug 2025</span>',
            ai_interpretation="Plain string from legacy cache.",
        )
        assert "AI-ASSISTED · Tencent Hy3" not in html
        assert "Plain string from legacy cache." in html

    def test_none_input_renders_no_interpretation_block(self, chain_result):
        html = build_connected_signal_card_html(
            chain_result,
            period_badge_html='<span>Aug 2025</span>',
            ai_interpretation=None,
        )
        # No badge, no caption, no Management Interpretation block
        # (the card itself still shows Historical Signal etc.)
        assert "AI-ASSISTED · Tencent Hy3" not in html
        assert "Management Interpretation" not in html


# ---------------------------------------------------------------------------
# 5. Connected Signal -- no supported chain (E)
# ---------------------------------------------------------------------------

class TestConnectedSignalNoChain:
    def test_no_chain_state_unchanged(self, no_chain_result):
        """Existing clean no-signal state must remain unchanged."""
        html = build_connected_signal_card_html(
            no_chain_result,
            period_badge_html='<span>Jul 2025</span>',
            ai_interpretation=_ok_ai_result(),  # even with Hy3 OK, no chain = no badge
        )
        assert "No sufficiently strong connected signal detected" in html
        assert "Causality is not inferred" in html

    def test_no_chain_never_shows_badge(self, no_chain_result):
        """Even when Hy3 is OK, the no-chain state must not display the
        AI badge -- there is no chain to interpret."""
        html = build_connected_signal_card_html(
            no_chain_result,
            period_badge_html='<span>Jul 2025</span>',
            ai_interpretation=_ok_ai_result(),
        )
        assert "AI-ASSISTED · Tencent Hy3" not in html
        assert "Generated from governed Sentinel360 connected-signal evidence" not in html

    def test_no_chain_with_none_ai(self, no_chain_result):
        html = build_connected_signal_card_html(
            no_chain_result,
            period_badge_html='<span>Jul 2025</span>',
            ai_interpretation=None,
        )
        assert "AI-ASSISTED · Tencent Hy3" not in html


# ---------------------------------------------------------------------------
# 6. Dataclass + dict interop (service returns dataclass, page passes dict)
# ---------------------------------------------------------------------------

class TestIsHy3LiveDataclassInterop:
    def test_dataclass_status_ok(self):
        """The ``synthesize()`` service returns a dataclass; the gate
        must accept that shape too."""
        from src.ai_connected_signal_synthesis import AIConnectedSignalSynthesisResult

        res = AIConnectedSignalSynthesisResult(status="OK", message="m")
        assert is_hy3_live(res) is True

        res_fb = AIConnectedSignalSynthesisResult(status="NOT_CONFIGURED", message="m")
        assert is_hy3_live(res_fb) is False


# ---------------------------------------------------------------------------
# 7. Cross-card consistency -- KPI + CS use the same shared badge
# ---------------------------------------------------------------------------

class TestCrossCardBadgeConsistency:
    def test_kpi_and_cs_badge_use_same_html(self, chain_result):
        """KPI interpretation card and Connected Signal card must use the
        exact same shared badge HTML. This is the cross-card consistency
        requirement."""
        from src.streamlit_executive_page_controller import build_forecast_interpretation_card

        expected = render_hy3_badge_html()

        # KPI card with live Hy3 OK
        kpi_card = {
            "kpi_id": "PATIENT_SATISFACTION",
            "kpi_name": "Patient Satisfaction",
            "unit": "Score (1-5)",
            "threshold_status": "Warning",
            "warning_level": "Emerging Warning",
            "forecast_quality": "Moderate Confidence",
            "point_forecast": 2.7,
            "expected_status_change": "Green to Amber",
            "latest_value": 2.7,
        }
        kpi_html = build_forecast_interpretation_card(
            kpi_card,
            ai_interpretation={
                "status": "OK",
                "what_is_changing": "Live Hy3 WHAT.",
                "why_it_matters": "Live Hy3 WHY.",
            },
        )
        assert expected in kpi_html

        # CS card with live Hy3 OK
        cs_html = build_connected_signal_card_html(
            chain_result,
            period_badge_html='<span>Aug 2025</span>',
            ai_interpretation=_ok_ai_result(),
        )
        assert expected in cs_html

    def test_kpi_and_cs_caption_wording_differ_by_scope(self, chain_result):
        """KPI caption = forecast evidence; CS caption = connected-signal evidence."""
        from src.streamlit_executive_page_controller import build_forecast_interpretation_card

        kpi_card = {
            "kpi_id": "PATIENT_SATISFACTION",
            "kpi_name": "Patient Satisfaction",
            "unit": "Score (1-5)",
            "threshold_status": "Warning",
            "warning_level": "Emerging Warning",
            "forecast_quality": "Moderate Confidence",
            "point_forecast": 2.7,
            "expected_status_change": "Green to Amber",
            "latest_value": 2.7,
        }
        kpi_html = build_forecast_interpretation_card(
            kpi_card,
            ai_interpretation={
                "status": "OK",
                "what_is_changing": "x",
                "why_it_matters": "y",
            },
        )
        cs_html = build_connected_signal_card_html(
            chain_result,
            period_badge_html='<span>Aug 2025</span>',
            ai_interpretation=_ok_ai_result(),
        )
        # KPI caption wording
        assert "Generated from governed Sentinel360 forecast evidence" in kpi_html
        assert "Generated from governed Sentinel360 connected-signal evidence" not in kpi_html
        # CS caption wording
        assert "Generated from governed Sentinel360 connected-signal evidence" in cs_html
        assert "Generated from governed Sentinel360 forecast evidence" not in cs_html


# ---------------------------------------------------------------------------
# 8. Layer ordering on KPI card (badge before WHAT; caption after WHY)
# ---------------------------------------------------------------------------

class TestKpiCardLayerOrdering:
    def test_badge_before_what_caption_after_why_no_footer(self):
        from src.streamlit_executive_page_controller import build_forecast_interpretation_card

        card = {
            "kpi_id": "PATIENT_SATISFACTION",
            "kpi_name": "Patient Satisfaction",
            "unit": "Score (1-5)",
            "threshold_status": "Warning",
            "warning_level": "Emerging Warning",
            "forecast_quality": "Moderate Confidence",
            "point_forecast": 2.7,
            "expected_status_change": "Green to Amber",
            "latest_value": 2.7,
        }
        html = build_forecast_interpretation_card(
            card,
            ai_interpretation={
                "status": "OK",
                "what_is_changing": "WHAT.",
                "why_it_matters": "WHY.",
            },
        )
        pos_badge = html.find("AI-ASSISTED · Tencent Hy3")
        pos_what = html.find("WHAT IS CHANGING?")
        pos_why = html.find("WHY DOES IT MATTER?")
        pos_caption = html.find("Generated from governed Sentinel360 forecast evidence")
        assert -1 < pos_badge < pos_what < pos_why < pos_caption
        # Bottom evidence strip removed
        assert "Emerging Warning · Moderate Confidence · Green to Amber" not in html
