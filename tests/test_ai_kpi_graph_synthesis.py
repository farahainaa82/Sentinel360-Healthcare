"""
Step AI-5 — Targeted tests for KPI graph AI interpretation.

Covers:
  A. governed forecast header always renders
  B. header remains when Hy3 fails
  C. evidence payload preserves values exactly
  D. Hy3 receives no raw DataFrames
  E. AI may not calculate
  F. valid Hy3 result produces WHAT IS CHANGING
  G. valid Hy3 result produces WHY DOES IT MATTERS
  H. AI success displays AI-ASSISTED
  I. AI failure uses deterministic fallback
  J. AI failure does not display AI-ASSISTED
  K. evidence strip remains deterministic
  L. status transition preserved exactly
  M. no cross-KPI causal inference allowed
  N. actual period avoids unnecessary AI call
  O. cache changes when KPI evidence changes
  P. API key not cached/exposed
  Q. header content is not duplicated unnecessarily by prompt guidance

Dependencies: pytest, unittest.mock, pandas, json (stdlib).
"""

from __future__ import annotations

import json
import os
import sys
from copy import deepcopy
from unittest.mock import MagicMock

import pandas as pd
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.ai_kpi_graph_synthesis import AIKPIGraphSynthesisService
from src.kpi_graph_ai_evidence import build_kpi_graph_evidence, _map_quality_to_confidence
from src.streamlit_executive_page_controller import (
    build_forecast_interpretation_card,
    build_kpi_interpretation_card,
    _map_quality_to_confidence_label,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_card():
    """A realistic forecast KPI card."""
    annual_df = pd.DataFrame({
        "month": [1, 2, 3, 4, 5, 6, 7, 8],
        "monthly_value": [3.1, 3.0, 2.9, 2.9, 2.8, 2.8, 2.8, 2.7],
        "supported": [True, True, True, True, True, True, True, False],
    })
    return {
        "kpi_id": "kpi_006",
        "kpi_name": "Patient Satisfaction Score",
        "latest_value": "2.7",
        "unit": "1-5 Likert",
        "threshold_status": "Warning",
        "border_colour": "orange",
        "period_type": "FORECAST",
        "annual_df": annual_df,
        "point_forecast": 2.7,
        "lower_bound": 2.5,
        "upper_bound": 2.9,
        "forecast_quality": "Moderate Indicative Confidence",
        "warning_level": "Emerging Warning",
        "warning_reason": "",
        "expected_status_change": "Green to Amber",
        "horizon_months_ahead": 1,
        "suggested_action": "",
        "threshold_config": {
            "directionality": "HIGHER_IS_BETTER",
            "green_lower_boundary": 2.8,
            "green_upper_boundary": 5.0,
        },
    }


@pytest.fixture
def unavailable_card():
    """A forecast KPI card where forecast is unavailable."""
    return {
        "kpi_id": "kpi_099",
        "kpi_name": "Staff Turnover Rate",
        "latest_value": "N/A",
        "unit": "%",
        "threshold_status": "Monitoring",
        "border_colour": "grey",
        "period_type": "FORECAST",
        "annual_df": pd.DataFrame(),
        "forecast_unavailable": True,
        "forecast_limitation": "Insufficient monthly observations.",
    }


@pytest.fixture
def actual_card():
    """An actual-period KPI card."""
    return {
        "kpi_id": "kpi_006",
        "kpi_name": "Patient Satisfaction Score",
        "latest_value": "2.9",
        "unit": "1-5 Likert",
        "threshold_status": "Green",
        "border_colour": "green",
        "period_type": "ACTUAL",
        "annual_df": pd.DataFrame(),
    }


@pytest.fixture
def sample_evidence(sample_card):
    """Evidence derived from sample_card."""
    return build_kpi_graph_evidence(
        sample_card,
        hospital_id="H001",
        department_name="Emergency",
        year=2025,
        month=8,
    )


@pytest.fixture
def service_not_configured():
    return AIKPIGraphSynthesisService(provider="", model="", api_key="")


@pytest.fixture
def service_configured():
    return AIKPIGraphSynthesisService(
        provider="tencent_hunyuan",
        model="hy3",
        api_key="FAKE_KEY_FOR_TESTING",
    )


# ---------------------------------------------------------------------------
# A. Governed forecast header always renders
# ---------------------------------------------------------------------------

class TestGovernedHeaderAlwaysRenders:
    def test_forecast_header_contains_kpi_name(self, sample_card):
        html = build_forecast_interpretation_card(sample_card)
        assert "Patient Satisfaction Score" in html

    def test_forecast_header_contains_value(self, sample_card):
        html = build_forecast_interpretation_card(sample_card)
        assert "2.7" in html

    def test_forecast_header_contains_status(self, sample_card):
        html = build_forecast_interpretation_card(sample_card)
        assert "Warning" in html

    def test_forecast_header_contains_forecast_label(self, sample_card):
        html = build_forecast_interpretation_card(sample_card)
        assert "FORECAST" in html


# ---------------------------------------------------------------------------
# B. Header remains when Hy3 fails
# ---------------------------------------------------------------------------

class TestHeaderRemainsWhenHy3Fails:
    def test_header_present_on_not_configured(self, sample_card, service_not_configured, sample_evidence):
        ai = service_not_configured.synthesize(sample_evidence)
        html = build_forecast_interpretation_card(sample_card, ai_interpretation=ai)
        assert "Patient Satisfaction Score" in html
        assert "2.7" in html
        assert "Warning" in html

    def test_header_present_on_provider_error(self, sample_card, service_configured, sample_evidence):
        transport = MagicMock()
        transport.chat_completion.side_effect = RuntimeError("timeout")
        svc = AIKPIGraphSynthesisService(
            provider="tencent_hunyuan", model="hy3", api_key="FAKE_KEY", transport=transport
        )
        ai = svc.synthesize(sample_evidence)
        html = build_forecast_interpretation_card(sample_card, ai_interpretation=ai)
        assert "Patient Satisfaction Score" in html
        assert ai["status"] == "PROVIDER_ERROR"


# ---------------------------------------------------------------------------
# C. Evidence payload preserves values exactly
# ---------------------------------------------------------------------------

class TestEvidencePreservesValues:
    def test_kpi_name_preserved(self, sample_evidence):
        assert sample_evidence["kpi"]["kpi_name"] == "Patient Satisfaction Score"

    def test_forecast_display_preserved(self, sample_evidence):
        assert sample_evidence["forecast"]["forecast_display"] == "2.7"

    def test_warning_level_preserved(self, sample_evidence):
        assert sample_evidence["forecast"]["warning_level"] == "Emerging Warning"

    def test_status_change_preserved(self, sample_evidence):
        assert sample_evidence["forecast"]["expected_status_change"] == "Green to Amber"

    def test_context_preserved(self, sample_evidence):
        assert sample_evidence["context"]["hospital_id"] == "H001"
        assert sample_evidence["context"]["department_name"] == "Emergency"
        assert sample_evidence["context"]["selected_year"] == 2025
        assert sample_evidence["context"]["selected_month"] == 8

    def test_threshold_config_included(self, sample_evidence):
        assert "target" in sample_evidence
        assert sample_evidence["target"]["directionality"] == "HIGHER_IS_BETTER"


# ---------------------------------------------------------------------------
# D. Hy3 receives no raw DataFrames
# ---------------------------------------------------------------------------

class TestNoRawDataFrames:
    def test_evidence_is_json_serializable(self, sample_evidence):
        try:
            json.dumps(sample_evidence, default=str)
        except TypeError as exc:
            pytest.fail(f"Evidence not JSON serializable: {exc}")

    def test_annual_df_not_in_evidence(self, sample_evidence):
        assert "annual_df" not in sample_evidence
        assert "trend_df" not in sample_evidence


# ---------------------------------------------------------------------------
# E. AI may not calculate
# ---------------------------------------------------------------------------

class TestAiMayNotCalculate:
    def test_governance_flags_set(self, sample_evidence):
        gov = sample_evidence["governance"]
        assert gov["evidence_is_governed"] is True
        assert gov["ai_may_calculate"] is False
        assert gov["ai_may_modify_values"] is False
        assert gov["ai_may_infer_missing_values"] is False
        assert gov["causality_confirmed"] is False

    def test_system_prompt_forbids_calculation(self, service_configured):
        prompt = service_configured._system_prompt()
        assert "Do NOT calculate" in prompt or "not calculate" in prompt.lower()


# ---------------------------------------------------------------------------
# F + G. Valid Hy3 result produces WHAT IS CHANGING and WHY DOES IT MATTER
# ---------------------------------------------------------------------------

class TestValidHy3Result:
    def test_what_is_changing_present(self, sample_evidence):
        transport = MagicMock()
        transport.chat_completion.return_value = MagicMock(
            status="OK",
            content=json.dumps({
                "what_is_changing": "The August outlook shows further deterioration.",
                "why_it_matters": "The decline signals emerging pressure.",
                "governance_note": "AI-assisted interpretation.",
            }),
        )
        svc = AIKPIGraphSynthesisService(
            provider="tencent_hunyuan", model="hy3", api_key="FAKE_KEY", transport=transport
        )
        result = svc.synthesize(sample_evidence)
        assert result["status"] == "OK"
        assert "deterioration" in result["what_is_changing"]

    def test_why_it_matters_present(self, sample_evidence):
        transport = MagicMock()
        transport.chat_completion.return_value = MagicMock(
            status="OK",
            content=json.dumps({
                "what_is_changing": "The August outlook shows further deterioration.",
                "why_it_matters": "The decline signals emerging pressure.",
                "governance_note": "AI-assisted interpretation.",
            }),
        )
        svc = AIKPIGraphSynthesisService(
            provider="tencent_hunyuan", model="hy3", api_key="FAKE_KEY", transport=transport
        )
        result = svc.synthesize(sample_evidence)
        assert "pressure" in result["why_it_matters"]

    def test_html_shows_what_is_changing(self, sample_card, sample_evidence):
        transport = MagicMock()
        transport.chat_completion.return_value = MagicMock(
            status="OK",
            content=json.dumps({
                "what_is_changing": "The August outlook shows further deterioration.",
                "why_it_matters": "The decline signals emerging pressure.",
                "governance_note": "AI-assisted interpretation.",
            }),
        )
        svc = AIKPIGraphSynthesisService(
            provider="tencent_hunyuan", model="hy3", api_key="FAKE_KEY", transport=transport
        )
        ai = svc.synthesize(sample_evidence)
        html = build_forecast_interpretation_card(sample_card, ai_interpretation=ai)
        assert "WHAT IS CHANGING?" in html
        assert "deterioration" in html

    def test_html_shows_why_it_matters(self, sample_card, sample_evidence):
        transport = MagicMock()
        transport.chat_completion.return_value = MagicMock(
            status="OK",
            content=json.dumps({
                "what_is_changing": "The August outlook shows further deterioration.",
                "why_it_matters": "The decline signals emerging pressure.",
                "governance_note": "AI-assisted interpretation.",
            }),
        )
        svc = AIKPIGraphSynthesisService(
            provider="tencent_hunyuan", model="hy3", api_key="FAKE_KEY", transport=transport
        )
        ai = svc.synthesize(sample_evidence)
        html = build_forecast_interpretation_card(sample_card, ai_interpretation=ai)
        assert "WHY DOES IT MATTER?" in html
        assert "pressure" in html


# ---------------------------------------------------------------------------
# H. AI success displays AI-ASSISTED
# ---------------------------------------------------------------------------

class TestAiAssistedBadge:
    def test_badge_shown_on_ok(self, sample_card, sample_evidence):
        transport = MagicMock()
        transport.chat_completion.return_value = MagicMock(
            status="OK",
            content=json.dumps({
                "what_is_changing": "X.",
                "why_it_matters": "Y.",
                "governance_note": "Z.",
            }),
        )
        svc = AIKPIGraphSynthesisService(
            provider="tencent_hunyuan", model="hy3", api_key="FAKE_KEY", transport=transport
        )
        ai = svc.synthesize(sample_evidence)
        html = build_forecast_interpretation_card(sample_card, ai_interpretation=ai)
        assert "AI-ASSISTED" in html


# ---------------------------------------------------------------------------
# I. AI failure uses deterministic fallback
# ---------------------------------------------------------------------------

class TestAiFailureFallback:
    def test_fallback_produces_what_is_changing(self, sample_card, service_not_configured, sample_evidence):
        ai = service_not_configured.synthesize(sample_evidence)
        html = build_forecast_interpretation_card(sample_card, ai_interpretation=ai)
        assert "WHAT IS CHANGING?" in html
        assert ai["status"] == "NOT_CONFIGURED"

    def test_fallback_produces_why_it_matters(self, sample_card, service_not_configured, sample_evidence):
        ai = service_not_configured.synthesize(sample_evidence)
        html = build_forecast_interpretation_card(sample_card, ai_interpretation=ai)
        assert "WHY DOES IT MATTER?" in html

    def test_fallback_mentions_warning(self, sample_card, service_not_configured, sample_evidence):
        ai = service_not_configured.synthesize(sample_evidence)
        assert "Emerging Warning" in ai["why_it_matters"]

    def test_fallback_mentions_status_change(self, sample_card, service_not_configured, sample_evidence):
        ai = service_not_configured.synthesize(sample_evidence)
        assert "Green to Amber" in ai["what_is_changing"]


# ---------------------------------------------------------------------------
# J. AI failure does not display AI-ASSISTED
# ---------------------------------------------------------------------------

class TestNoBadgeOnFailure:
    def test_no_badge_on_not_configured(self, sample_card, service_not_configured, sample_evidence):
        ai = service_not_configured.synthesize(sample_evidence)
        html = build_forecast_interpretation_card(sample_card, ai_interpretation=ai)
        assert "AI-ASSISTED" not in html

    def test_no_badge_on_provider_error(self, sample_card, sample_evidence):
        transport = MagicMock()
        transport.chat_completion.side_effect = RuntimeError("boom")
        svc = AIKPIGraphSynthesisService(
            provider="tencent_hunyuan", model="hy3", api_key="FAKE_KEY", transport=transport
        )
        ai = svc.synthesize(sample_evidence)
        html = build_forecast_interpretation_card(sample_card, ai_interpretation=ai)
        assert "AI-ASSISTED" not in html
        assert ai["status"] == "PROVIDER_ERROR"


# ---------------------------------------------------------------------------
# K. Evidence strip removed from visible card (UI-only removal)
#
# The bottom "warning_level · confidence · transition" strip is no
# longer rendered in the visible card. The underlying fields
# (warning_level, confidence, status transition) are still produced
# by the analytics layer and remain part of the governed evidence /
# AI evidence pack, but they are intentionally hidden from the
# end-user presentation to keep one consistent Hy3 provenance
# convention across Executive Overview.
# ---------------------------------------------------------------------------

class TestEvidenceStrip:
    def test_strip_removed_on_success(self, sample_card, sample_evidence):
        transport = MagicMock()
        transport.chat_completion.return_value = MagicMock(
            status="OK",
            content=json.dumps({
                "what_is_changing": "X.",
                "why_it_matters": "Y.",
                "governance_note": "Z.",
            }),
        )
        svc = AIKPIGraphSynthesisService(transport=transport)
        ai = svc.synthesize(sample_evidence)
        html = build_forecast_interpretation_card(sample_card, ai_interpretation=ai)
        # The combined "Emerging Warning · Moderate Confidence · Green to Amber"
        # string is the bottom evidence strip and must no longer appear.
        assert "Emerging Warning · Moderate Confidence · Green to Amber" not in html

    def test_strip_removed_on_failure(self, sample_card, service_not_configured, sample_evidence):
        ai = service_not_configured.synthesize(sample_evidence)
        html = build_forecast_interpretation_card(sample_card, ai_interpretation=ai)
        assert "Emerging Warning · Moderate Confidence · Green to Amber" not in html

    def test_underlying_fields_still_in_evidence(self, sample_evidence):
        """Underlying analytics fields must remain available in evidence
        even though the visible strip is gone."""
        # The governed evidence pack still carries warning_level, the
        # transition text, and the confidence label -- they just
        # aren't surfaced in the visible card anymore.
        assert sample_evidence["forecast"]["warning_level"] == "Emerging Warning"
        assert sample_evidence["forecast"]["expected_status_change"] == "Green to Amber"
        assert sample_evidence["forecast"]["confidence_label"] == "Moderate Confidence"


# ---------------------------------------------------------------------------
# L. Status transition preserved exactly
# ---------------------------------------------------------------------------

class TestStatusTransitionPreserved:
    def test_transition_in_evidence(self, sample_evidence):
        assert sample_evidence["forecast"]["expected_status_change"] == "Green to Amber"

    def test_transition_in_html(self, sample_card):
        html = build_forecast_interpretation_card(sample_card)
        assert "Green to Amber" in html

    def test_transition_not_modified_by_ai(self, sample_card, sample_evidence):
        """The AI may NOT change the underlying transition. Even when
        Hy3 returns its own WHAT/WHY strings, the governed evidence
        pack must still carry the original transition text -- that is
        the part tests / future use rely on."""
        transport = MagicMock()
        transport.chat_completion.return_value = MagicMock(
            status="OK",
            content=json.dumps({
                "what_is_changing": "X.",
                "why_it_matters": "Y.",
                "governance_note": "Z.",
            }),
        )
        svc = AIKPIGraphSynthesisService(
            provider="tencent_hunyuan", model="hy3", api_key="FAKE_KEY", transport=transport
        )
        svc.synthesize(sample_evidence)
        # The governed evidence is untouched by the AI call -- the
        # transition text remains the original "Green to Amber".
        assert sample_evidence["forecast"]["expected_status_change"] == "Green to Amber"


# ---------------------------------------------------------------------------
# M. No cross-KPI causal inference allowed
# ---------------------------------------------------------------------------

class TestNoCrossKpiCausality:
    def test_prompt_mentions_single_kpi_only(self, service_configured, sample_evidence):
        prompt = service_configured._build_prompt(sample_evidence)
        assert "cross" not in prompt.lower()
        assert "causing" not in prompt.lower()

    def test_system_prompt_forbids_causality(self, service_configured):
        prompt = service_configured._system_prompt()
        assert "causality" in prompt.lower() or "causal" in prompt.lower()


# ---------------------------------------------------------------------------
# N. Actual period avoids unnecessary AI call
# ---------------------------------------------------------------------------

class TestActualPeriodAvoidsAi:
    def test_actual_card_no_ai_section(self, actual_card):
        html = build_kpi_interpretation_card(actual_card, {})
        assert "WHAT IS CHANGING" not in html
        assert "AI-ASSISTED" not in html

    def test_forecast_card_has_ai_section(self, sample_card):
        html = build_forecast_interpretation_card(sample_card)
        assert "WHAT IS CHANGING?" in html


# ---------------------------------------------------------------------------
# O. Cache changes when KPI evidence changes
# ---------------------------------------------------------------------------

class TestCacheChangesWithEvidence:
    def test_evidence_hash_changes_when_kpi_changes(self, sample_card):
        ev1 = build_kpi_graph_evidence(sample_card, "H001", "ER", 2025, 8)
        ev2 = build_kpi_graph_evidence(sample_card, "H001", "ER", 2025, 9)
        j1 = json.dumps(ev1, sort_keys=True, default=str)
        j2 = json.dumps(ev2, sort_keys=True, default=str)
        assert j1 != j2

    def test_evidence_hash_changes_when_value_changes(self, sample_card):
        ev1 = build_kpi_graph_evidence(sample_card, "H001", "ER", 2025, 8)
        card2 = deepcopy(sample_card)
        card2["latest_value"] = "2.9"
        ev2 = build_kpi_graph_evidence(card2, "H001", "ER", 2025, 8)
        j1 = json.dumps(ev1, sort_keys=True, default=str)
        j2 = json.dumps(ev2, sort_keys=True, default=str)
        assert j1 != j2


# ---------------------------------------------------------------------------
# P. API key not cached / exposed
# ---------------------------------------------------------------------------

class TestApiKeyNotCached:
    def test_api_key_not_in_evidence(self, sample_evidence):
        evidence_json = json.dumps(sample_evidence, sort_keys=True, default=str)
        assert "FAKE_KEY" not in evidence_json
        assert "api_key" not in evidence_json.lower()

    def test_api_key_not_in_prompt(self, service_configured, sample_evidence):
        prompt = service_configured._build_prompt(sample_evidence)
        assert "FAKE_KEY" not in prompt


# ---------------------------------------------------------------------------
# Q. Header content is not duplicated unnecessarily by prompt guidance
# ---------------------------------------------------------------------------

class TestHeaderNotDuplicatedInPrompt:
    def test_prompt_does_not_repeat_kpi_name_excessively(self, service_configured, sample_evidence):
        prompt = service_configured._build_prompt(sample_evidence)
        count = prompt.count("Patient Satisfaction Score")
        assert count <= 1, f"KPI name repeated {count} times in prompt"

    def test_prompt_does_not_repeat_forecast_value_excessively(self, service_configured, sample_evidence):
        prompt = service_configured._build_prompt(sample_evidence)
        count = prompt.count("2.7")
        assert count <= 1, f"Forecast value repeated {count} times in prompt"


# ---------------------------------------------------------------------------
# Additional: Unavailable forecast handling
# ---------------------------------------------------------------------------

class TestUnavailableForecast:
    def test_unavailable_no_ai_section(self, unavailable_card):
        html = build_forecast_interpretation_card(unavailable_card)
        assert "Forecast Not Available" in html
        assert "WHAT IS CHANGING" not in html

    def test_unavailable_no_ai_badge(self, unavailable_card):
        html = build_forecast_interpretation_card(unavailable_card)
        assert "AI-ASSISTED" not in html


# ---------------------------------------------------------------------------
# Additional: Confidence label mapping
# ---------------------------------------------------------------------------

class TestConfidenceLabelMapping:
    def test_high_quality(self):
        assert _map_quality_to_confidence("High Confidence") == "High Confidence"
        assert _map_quality_to_confidence_label("High Indicative") == "High Confidence"

    def test_moderate_quality(self):
        assert _map_quality_to_confidence("Moderate Indicative Confidence") == "Moderate Confidence"
        assert _map_quality_to_confidence_label("Moderate Indicative") == "Moderate Confidence"

    def test_low_quality(self):
        assert _map_quality_to_confidence("Low Confidence") == "Low Confidence"
        assert _map_quality_to_confidence_label("Low Indicative") == "Low Confidence"

    def test_empty_defaults_moderate(self):
        assert _map_quality_to_confidence("") == "Moderate Confidence"
        assert _map_quality_to_confidence_label("") == "Moderate Confidence"


# ---------------------------------------------------------------------------
# R. AI provenance visibility (Tencent Hy3 badge + caption)
# ---------------------------------------------------------------------------

def _ok_ai_interpretation():
    """Return a canned OK AI interpretation dict."""
    return {
        "what_is_changing": "The August outlook shows further deterioration.",
        "why_it_matters": "The decline signals emerging pressure.",
        "governance_note": "AI-assisted interpretation.",
        "status": "OK",
    }


class TestAiProvenanceVisibility:
    """Verify judge-visible Hy3 provenance: badge wording + provenance caption."""

    def test_badge_includes_tencent_hy3_on_success(self, sample_card):
        html = build_forecast_interpretation_card(sample_card, ai_interpretation=_ok_ai_interpretation())
        assert "Tencent Hy3" in html

    def test_badge_includes_ai_assisted_prefix_on_success(self, sample_card):
        html = build_forecast_interpretation_card(sample_card, ai_interpretation=_ok_ai_interpretation())
        assert "AI-ASSISTED" in html
        assert "AI-ASSISTED · Tencent Hy3" in html

    def test_badge_uses_pill_styling(self, sample_card):
        html = build_forecast_interpretation_card(sample_card, ai_interpretation=_ok_ai_interpretation())
        assert "border-radius:10px" in html

    def test_badge_includes_sparkle_icon(self, sample_card):
        html = build_forecast_interpretation_card(sample_card, ai_interpretation=_ok_ai_interpretation())
        assert "<svg" in html and "sparkle" not in html  # SVG present, not emoji

    def test_provenance_caption_on_success(self, sample_card):
        html = build_forecast_interpretation_card(sample_card, ai_interpretation=_ok_ai_interpretation())
        assert "Generated from governed Sentinel360 forecast evidence" in html

    def test_provenance_caption_styled_muted(self, sample_card):
        html = build_forecast_interpretation_card(sample_card, ai_interpretation=_ok_ai_interpretation())
        assert "font-style:italic" in html
        assert "#9AA5B5" in html

    def test_no_badge_on_not_configured(self, sample_card, service_not_configured, sample_evidence):
        ai = service_not_configured.synthesize(sample_evidence)
        html = build_forecast_interpretation_card(sample_card, ai_interpretation=ai)
        assert "Tencent Hy3" not in html
        assert "AI-ASSISTED" not in html

    def test_no_badge_on_provider_error(self, sample_card, sample_evidence):
        transport = MagicMock()
        transport.chat_completion.side_effect = RuntimeError("timeout")
        svc = AIKPIGraphSynthesisService(
            provider="tencent_hunyuan", model="hy3", api_key="FAKE_KEY", transport=transport
        )
        ai = svc.synthesize(sample_evidence)
        html = build_forecast_interpretation_card(sample_card, ai_interpretation=ai)
        assert "Tencent Hy3" not in html

    def test_no_provenance_caption_on_failure(self, sample_card, service_not_configured, sample_evidence):
        ai = service_not_configured.synthesize(sample_evidence)
        html = build_forecast_interpretation_card(sample_card, ai_interpretation=ai)
        assert "Generated from governed Sentinel360 forecast evidence" not in html

    def test_no_provenance_caption_when_ai_none(self, sample_card):
        html = build_forecast_interpretation_card(sample_card, ai_interpretation=None)
        assert "Generated from governed Sentinel360 forecast evidence" not in html
        assert "Tencent Hy3" not in html

    def test_governed_header_unchanged_on_success(self, sample_card):
        html = build_forecast_interpretation_card(sample_card, ai_interpretation=_ok_ai_interpretation())
        assert "FORECAST" in html
        assert "Patient Satisfaction Score" in html
        assert "2.7" in html
        assert "Warning" in html

    def test_evidence_strip_removed_on_success(self, sample_card):
        """The bottom evidence strip is no longer rendered in the visible card."""
        html = build_forecast_interpretation_card(sample_card, ai_interpretation=_ok_ai_interpretation())
        assert "Emerging Warning · Moderate Confidence · Green to Amber" not in html

    def test_layer_ordering_on_success(self, sample_card):
        """Badge must sit before WHAT IS CHANGING; provenance must sit after WHY DOES IT MATTER; no bottom strip."""
        html = build_forecast_interpretation_card(sample_card, ai_interpretation=_ok_ai_interpretation())
        pos_badge = html.find("AI-ASSISTED · Tencent Hy3")
        pos_what = html.find("WHAT IS CHANGING?")
        pos_why = html.find("WHY DOES IT MATTER?")
        pos_caption = html.find("Generated from governed Sentinel360 forecast evidence")
        # All four must exist and be in the right order; the bottom
        # evidence strip is intentionally absent from the visible card.
        assert -1 < pos_badge < pos_what < pos_why < pos_caption
        assert "Emerging Warning · Moderate Confidence · Green to Amber" not in html
