"""
Step AI-4 — Targeted tests for the AI management page helper.

The helper module (src.ai_management_page_helper) is the only seam between
the Executive Overview page and the AI management synthesis service. It
exposes:

  * build_ai_cache_signature(state)         -> stable hashable key
  * cache_signature_to_str(sig)             -> string form for dict caches
  * run_ai_synthesis_for_state(state, ...)  -> defensive JSON-safe dict
  * build_deterministic_priority_text(...)  -> preserved fallback text
  * build_priority_card_html(...)           -> HTML assembly (AI + fallback)

The verification list from the integration spec is:
  A. Forecast + AI OK                       -> AI-assisted content displayed
  B. Forecast + TIMEOUT                     -> deterministic fallback
  C. Forecast + NOT_CONFIGURED              -> deterministic fallback
  D. Forecast + INVALID_RESPONSE            -> deterministic fallback
  E. Actual period                          -> existing deterministic text
  F. AI success                             -> governance footer displayed
  G. AI failure                             -> no AI badge / no footer
  H. No API key shown anywhere

All tests mock the LLM provider layer; NO live API calls are made.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import src.ai_management_page_helper as helper
from src.ai_management_page_helper import (
    build_ai_cache_signature,
    build_deterministic_priority_text,
    build_priority_card_html,
    cache_signature_to_str,
    run_ai_synthesis_for_state,
)
from src.ai_management_synthesis import AIManagementSynthesisResult


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------
def _make_state(
    *,
    period_type: str = "FORECAST",
    hospital_id: str = "HOSP-001",
    department_id: str = "DEPT-ED",
    selected_year: int = 2025,
    selected_month: int = 8,
    dominant_kpi_id: str = "kpi_001",
    dominant_kpi_name: str = "Staffing Level",
    dominant_status: str = "Amber",
    warning_level: str = "Escalating Warning",
) -> Dict[str, Any]:
    """Build a minimal state dict that satisfies the helper's expectations."""
    return {
        "selected_context": {
            "hospital_id": hospital_id,
            "department_id": department_id,
            "selected_year": selected_year,
            "selected_month": selected_month,
        },
        "period_type": period_type,
        "dominant_kpi_id": dominant_kpi_id,
        "dominant_kpi_name": dominant_kpi_name,
        "dominant_status": dominant_status,
        "dominant_forecast_warning": {"warning_level": warning_level},
    }


def _make_filters(
    *, month: int = 8, year: int = 2025, department_name: str = "Emergency Department"
) -> Dict[str, Any]:
    return {"month": month, "year": year, "department_name": department_name}


def _ok_ai_result() -> Dict[str, Any]:
    return {
        "status": "OK",
        "what_is_happening": (
            "ICU bed occupancy is forecast to reach 104.8% in August, "
            "moving from Amber to Red."
        ),
        "why_it_matters": (
            "Sustained occupancy above 100% signals capacity pressure that "
            "may constrain patient flow and service resilience during the "
            "forecast period."
        ),
        "what_management_should_do": (
            "Review the capacity risk and supporting operational evidence "
            "before confirming intervention priorities."
        ),
        "governance_note": (
            "AI-assisted interpretation of governed Sentinel360 outputs."
        ),
        "model_provider": "tencent_hunyuan",
        "model_name": "hy3",
        "message": None,
        "response_duration_seconds": 4.1,
    }


# ---------------------------------------------------------------------------
# A. Cache signature tests
# ---------------------------------------------------------------------------
class TestCacheSignature:
    def test_signature_changes_with_hospital(self):
        s1 = _make_state(hospital_id="HOSP-001")
        s2 = _make_state(hospital_id="HOSP-002")
        sig1 = build_ai_cache_signature(s1)
        sig2 = build_ai_cache_signature(s2)
        assert sig1 != sig2
        # Hospital id is in position 0
        assert sig1[0] == "HOSP-001"
        assert sig2[0] == "HOSP-002"

    def test_signature_changes_with_department(self):
        s1 = _make_state(department_id="DEPT-ED")
        s2 = _make_state(department_id="DEPT-ICU")
        sig1 = build_ai_cache_signature(s1)
        sig2 = build_ai_cache_signature(s2)
        assert sig1 != sig2
        assert sig1[1] == "DEPT-ED"
        assert sig2[1] == "DEPT-ICU"

    def test_signature_changes_with_year(self):
        s1 = _make_state(selected_year=2025)
        s2 = _make_state(selected_year=2026)
        sig1 = build_ai_cache_signature(s1)
        sig2 = build_ai_cache_signature(s2)
        assert sig1 != sig2

    def test_signature_changes_with_month(self):
        s1 = _make_state(selected_month=8)
        s2 = _make_state(selected_month=9)
        sig1 = build_ai_cache_signature(s1)
        sig2 = build_ai_cache_signature(s2)
        assert sig1 != sig2

    def test_signature_changes_with_dominant_kpi(self):
        s1 = _make_state(dominant_kpi_id="kpi_001")
        s2 = _make_state(dominant_kpi_id="kpi_007")
        sig1 = build_ai_cache_signature(s1)
        sig2 = build_ai_cache_signature(s2)
        assert sig1 != sig2

    def test_signature_includes_schema_version(self):
        sig = build_ai_cache_signature(_make_state())
        # Schema version is at position 5.
        # Active contract is the executive-Q&A schema ("ai1_qa_v2"), which
        # supersedes the legacy long-form schema ("ai1_v1"). The signature
        # bump ensures stale long-form entries are never reused after the
        # schema change.
        assert sig[5] in ("ai1_qa_v2",)

    def test_signature_includes_payload_hash(self):
        sig = build_ai_cache_signature(_make_state())
        # Last element is the 16-char sha256 prefix
        assert isinstance(sig[6], str)
        assert len(sig[6]) == 16

    def test_signature_to_str_is_stable(self):
        s = _make_state()
        sig = build_ai_cache_signature(s)
        s1 = cache_signature_to_str(sig)
        s2 = cache_signature_to_str(sig)
        assert s1 == s2
        assert "|" in s1

    def test_signature_handles_bad_state_gracefully(self):
        """A state without selected_context should still produce a tuple."""
        sig = build_ai_cache_signature({"period_type": "FORECAST"})
        assert isinstance(sig, tuple)
        assert len(sig) == 7


# ---------------------------------------------------------------------------
# B-D + F-H. AI synthesis wrapper tests (status mapping + safety)
# ---------------------------------------------------------------------------
class TestRunAISynthesis:
    def _patch_pack_and_service(self, result):
        """Patch both the evidence-pack builder and the service constructor."""
        pack = MagicMock()
        patcher_pack = patch.object(
            helper.ManagementEvidencePack, "from_executive_state", return_value=pack
        )
        svc_instance = MagicMock()
        svc_instance.synthesize.return_value = result
        patcher_svc = patch.object(
            helper, "AIManagementSynthesisService", return_value=svc_instance
        )
        return pack, svc_instance, patcher_pack, patcher_svc

    # --- A: Forecast + AI OK ---------------------------------------------------
    def test_forecast_ai_ok_returns_qa_ok_status(self, monkeypatch):
        monkeypatch.setenv("SENTINEL360_AI_PROVIDER", "tencent_hunyuan")
        monkeypatch.setenv("SENTINEL360_AI_MODEL", "hy3")
        monkeypatch.setenv("SENTINEL360_AI_API_KEY", "FAKE_KEY")
        ok_result = AIManagementSynthesisResult(
            status="OK",
            what_is_happening="WIH",
            why_it_matters="WIM",
            what_management_should_do="WMSD",
            governance_note="GN",
        )
        _, _, pp, ps = self._patch_pack_and_service(ok_result)
        with pp, ps:
            out = run_ai_synthesis_for_state(_make_state(period_type="FORECAST"))
        assert out["status"] == "OK"
        assert out["what_is_happening"] == "WIH"
        assert out["why_it_matters"] == "WIM"
        assert out["what_management_should_do"] == "WMSD"
        assert out["governance_note"] == "GN"

    # --- B: Forecast + TIMEOUT ------------------------------------------------
    def test_forecast_ai_timeout_returns_timeout_status(self, monkeypatch):
        monkeypatch.setenv("SENTINEL360_AI_PROVIDER", "tencent_hunyuan")
        monkeypatch.setenv("SENTINEL360_AI_MODEL", "hy3")
        monkeypatch.setenv("SENTINEL360_AI_API_KEY", "FAKE_KEY")
        timeout_result = AIManagementSynthesisResult(
            status="TIMEOUT",
            message="timeout",
        )
        _, _, pp, ps = self._patch_pack_and_service(timeout_result)
        with pp, ps:
            out = run_ai_synthesis_for_state(_make_state(period_type="FORECAST"))
        assert out["status"] == "TIMEOUT"

    # --- C: Forecast + NOT_CONFIGURED ----------------------------------------
    def test_forecast_ai_not_configured_when_no_api_key(self, monkeypatch):
        monkeypatch.delenv("SENTINEL360_AI_API_KEY", raising=False)
        monkeypatch.setenv("SENTINEL360_AI_PROVIDER", "tencent_hunyuan")
        monkeypatch.setenv("SENTINEL360_AI_MODEL", "hy3")
        # No need to mock anything — the service should bail with NOT_CONFIGURED
        # before the LLM is called.
        out = run_ai_synthesis_for_state(_make_state(period_type="FORECAST"))
        assert out["status"] == "NOT_CONFIGURED"

    # --- D: Forecast + INVALID_RESPONSE --------------------------------------
    def test_forecast_ai_invalid_response(self, monkeypatch):
        monkeypatch.setenv("SENTINEL360_AI_PROVIDER", "tencent_hunyuan")
        monkeypatch.setenv("SENTINEL360_AI_MODEL", "hy3")
        monkeypatch.setenv("SENTINEL360_AI_API_KEY", "FAKE_KEY")
        invalid_result = AIManagementSynthesisResult(
            status="INVALID_RESPONSE",
            message="TokenHub returned empty choices.",
        )
        _, _, pp, ps = self._patch_pack_and_service(invalid_result)
        with pp, ps:
            out = run_ai_synthesis_for_state(_make_state(period_type="FORECAST"))
        assert out["status"] == "INVALID_RESPONSE"

    # --- PROVIDER_ERROR (any unexpected exception) ----------------------------
    def test_ai_provider_error_when_service_raises(self, monkeypatch):
        monkeypatch.setenv("SENTINEL360_AI_PROVIDER", "tencent_hunyuan")
        monkeypatch.setenv("SENTINEL360_AI_MODEL", "hy3")
        monkeypatch.setenv("SENTINEL360_AI_API_KEY", "FAKE_KEY")
        pack = MagicMock()
        with patch.object(
            helper.ManagementEvidencePack, "from_executive_state", return_value=pack
        ):
            svc_instance = MagicMock()
            svc_instance.synthesize.side_effect = RuntimeError("boom")
            with patch.object(helper, "AIManagementSynthesisService", return_value=svc_instance):
                out = run_ai_synthesis_for_state(_make_state(period_type="FORECAST"))
        # The helper wraps the entire call in a defensive try/except, so any
        # exception (including the service raising RuntimeError) is caught at
        # the helper level and converted to API_UNAVAILABLE. The service's
        # own internal PROVIDER_ERROR mapping is exercised in
        # test_ai_management_synthesis.py; here we just verify the helper
        # never lets an exception escape.
        assert out["status"] == "API_UNAVAILABLE"
        assert "boom" in out["message"]

    # --- Helper never raises --------------------------------------------------
    def test_helper_does_not_raise_on_bad_state(self, monkeypatch):
        monkeypatch.setenv("SENTINEL360_AI_PROVIDER", "tencent_hunyuan")
        monkeypatch.setenv("SENTINEL360_AI_MODEL", "hy3")
        monkeypatch.setenv("SENTINEL360_AI_API_KEY", "FAKE_KEY")
        # Pass a totally empty state — helper must not raise.
        out = run_ai_synthesis_for_state({})
        assert isinstance(out, dict)
        assert out["status"] != "OK"
        # Must not contain any credential-like field
        assert "api_key" not in out
        assert "authorization" not in out

    # --- H: No API key shown anywhere -----------------------------------------
    def test_result_dict_has_no_api_key(self, monkeypatch):
        monkeypatch.setenv("SENTINEL360_AI_PROVIDER", "tencent_hunyuan")
        monkeypatch.setenv("SENTINEL360_AI_MODEL", "hy3")
        monkeypatch.setenv("SENTINEL360_AI_API_KEY", "FAKE_KEY")
        ok_result = AIManagementSynthesisResult(
            status="OK", what_is_happening="S"
        )
        _, _, pp, ps = self._patch_pack_and_service(ok_result)
        with pp, ps:
            out = run_ai_synthesis_for_state(_make_state())
        forbidden = (
            "api_key", "apikey", "api-key", "authorization", "auth",
            "token", "secret", "password", "credential", "bearer",
        )
        for f in forbidden:
            assert f not in out, f"forbidden key {f!r} present in result"

    def test_result_dict_scrubs_credential_fields(self, monkeypatch):
        monkeypatch.setenv("SENTINEL360_AI_PROVIDER", "tencent_hunyuan")
        monkeypatch.setenv("SENTINEL360_AI_MODEL", "hy3")
        monkeypatch.setenv("SENTINEL360_AI_API_KEY", "FAKE_KEY")
        # Build a result whose to_dict() contains a credential-like field.
        result = MagicMock()
        result.to_dict.return_value = {
            "status": "OK",
            "what_is_happening": "h",
            "why_it_matters": "m",
            "what_management_should_do": "d",
            "api_key": "sk-leaked",
            "authorization": "Bearer leaked",
        }
        pack = MagicMock()
        with patch.object(
            helper.ManagementEvidencePack, "from_executive_state", return_value=pack
        ):
            svc_instance = MagicMock()
            svc_instance.synthesize.return_value = result
            with patch.object(helper, "AIManagementSynthesisService", return_value=svc_instance):
                out = run_ai_synthesis_for_state(_make_state())
        # The credential-like keys must not appear in the output dict at all
        # (helper scrubs them rather than letting them pass through).
        assert "api_key" not in out
        assert "authorization" not in out
        # The Q&A fields themselves remain.
        assert out["what_is_happening"] == "h"
        assert out["why_it_matters"] == "m"
        assert out["what_management_should_do"] == "d"


# ---------------------------------------------------------------------------
# E. Deterministic text builder (preserved logic)
# ---------------------------------------------------------------------------
class TestDeterministicText:
    def test_forecast_with_priority(self):
        s = _make_state(period_type="FORECAST", dominant_status="Amber")
        f = _make_filters(month=8, year=2025, department_name="Emergency Department")
        out = build_deterministic_priority_text(s, f)
        assert out["period_badge_class"] == "forecast"
        assert "Forward Risk" in out["period_badge_text"]
        assert "Action to Consider" in out["period_badge_text"]
        assert "Operational pressure is forecast" in out["overall_situation"]
        assert "Aug 2025" in out["overall_situation"]
        assert "Staffing Level" in out["overall_situation"]
        assert "most significant forecast risk" in out["highest_priority_alert"]
        # Warning level is lowercased by the existing page logic.
        assert "escalating warning" in out["highest_priority_alert"].lower()

    def test_forecast_no_priority(self):
        s = _make_state(period_type="FORECAST", dominant_kpi_id="", dominant_status="")
        f = _make_filters(month=8, year=2025, department_name="Emergency Department")
        out = build_deterministic_priority_text(s, f)
        assert "remain within acceptable" in out["overall_situation"]
        assert "No priority operational concern" in out["highest_priority_alert"]

    def test_actual_with_priority(self):
        s = _make_state(period_type="ACTUAL", dominant_status="Red")
        f = _make_filters(month=7, year=2025, department_name="ICU")
        out = build_deterministic_priority_text(s, f)
        assert out["period_badge_class"] == "actual"
        assert "Past Performance" in out["period_badge_text"]
        assert "Review" in out["period_badge_text"]
        assert "Operational pressure was recorded" in out["overall_situation"]
        assert "Jul 2025" in out["overall_situation"]
        # The existing deterministic text does NOT include the department name
        # in the priority branch (only in the no-priority branch). The page
        # logic is preserved verbatim.
        assert "ICU" not in out["overall_situation"]
        assert "(Red)" in out["highest_priority_alert"]

    def test_actual_no_priority(self):
        s = _make_state(period_type="ACTUAL", dominant_kpi_id="", dominant_status="")
        f = _make_filters(month=7, year=2025, department_name="ICU")
        out = build_deterministic_priority_text(s, f)
        assert "performance remained within acceptable" in out["overall_situation"]
        assert "No priority operational concern" in out["highest_priority_alert"]


# ---------------------------------------------------------------------------
# F + G + A. Card HTML assembly — Q&A AI vs deterministic paths
# ---------------------------------------------------------------------------
class TestCardHTML:
    def _det_args(self, **overrides):
        args = dict(
            period_badge_text="Forward Risk \u2014 Action to Consider",
            period_badge_class="forecast",
            overall_situation="Aug 2025 is forecast to operate under elevated staffing pressure.",
            highest_priority_alert="Staffing Level is the most significant forecast risk.",
        )
        args.update(overrides)
        return args

    def _qa_args(self, **overrides):
        return self._det_args(
            what_is_happening=overrides.pop(
                "what_is_happening",
                "ICU bed occupancy is forecast to reach 104.8% in August, "
                "moving from Amber to Red.",
            ),
            why_it_matters=overrides.pop(
                "why_it_matters",
                "Sustained occupancy above 100% signals capacity pressure "
                "that may constrain patient flow.",
            ),
            what_management_should_do=overrides.pop(
                "what_management_should_do",
                "Review the supporting capacity evidence before confirming "
                "intervention priorities.",
            ),
            show_ai_pill=True,
            show_governance_footer=True,
            **overrides,
        )

    # --- Q&A AI path ------------------------------------------------------------
    def test_qa_path_includes_ai_pill(self):
        html = build_priority_card_html(**self._qa_args())
        assert "s360-ai-pill" in html
        assert "AI-ASSISTED" in html

    def test_qa_path_includes_governance_footer(self):
        html = build_priority_card_html(**self._qa_args())
        assert "s360-ai-governance" in html
        assert "AI-assisted interpretation of governed Sentinel360 outputs." in html

    def test_qa_path_renders_three_qa_rows(self):
        html = build_priority_card_html(**self._qa_args())
        # Exactly three row containers
        assert html.count("s360-ai-qa-row") == 3
        # Exactly three labels present and uppercase
        assert "WHAT IS HAPPENING?" in html
        assert "WHY DOES IT MATTER?" in html
        assert "WHAT SHOULD MANAGEMENT DO NEXT?" in html
        # Exactly three answer bodies present
        assert "ICU bed occupancy is forecast" in html
        assert "Sustained occupancy above 100%" in html
        assert "Review the supporting capacity evidence" in html

    def test_qa_path_replaces_legacy_long_form_rows(self):
        """The AI path renders Q&A rows; it does NOT render the legacy
        'Overall Situation' / 'Highest-Priority Alert' rows."""
        html = build_priority_card_html(**self._qa_args())
        assert "Highest-Priority Alert" not in html
        assert "Overall Situation" not in html
        assert "Management Significance" not in html

    def test_qa_path_does_not_render_legacy_long_form_ai_fields(self):
        """The legacy long-form AI fields are no longer accepted by the
        card builder; their content must not appear in the rendered HTML
        regardless of how the test is constructed (we simply do not pass
        them in)."""
        html = build_priority_card_html(**self._qa_args())
        assert "ai_headline" not in html.lower()
        assert "management_significance" not in html.lower()

    def test_qa_path_label_classes_present(self):
        html = build_priority_card_html(**self._qa_args())
        # Class hook for visual styling (uppercase + muted blue/grey).
        assert "s360-ai-qa-label" in html
        assert "s360-ai-qa-answer" in html

    def test_qa_path_qa_block_outer_wrapper(self):
        html = build_priority_card_html(**self._qa_args())
        assert html.count("<div class=\"s360-ai-qa\">") == 1

    def test_qa_path_label_is_uppercase(self):
        html = build_priority_card_html(**self._qa_args())
        # The rendered label text must be uppercase.
        assert "WHAT IS HAPPENING?" in html
        assert "WHY DOES IT MATTER?" in html
        assert "WHAT SHOULD MANAGEMENT DO NEXT?" in html

    # --- Deterministic path ----------------------------------------------------
    def test_deterministic_path_uses_highest_priority_alert(self):
        html = build_priority_card_html(
            **self._det_args(
                what_is_happening=None,
                why_it_matters=None,
                what_management_should_do=None,
                show_ai_pill=False,
                show_governance_footer=False,
            )
        )
        assert "Highest-Priority Alert" in html
        assert "Staffing Level is the most significant forecast risk." in html

    def test_deterministic_path_no_ai_pill(self):
        html = build_priority_card_html(
            **self._det_args(
                what_is_happening=None,
                why_it_matters=None,
                what_management_should_do=None,
                show_ai_pill=False,
                show_governance_footer=False,
            )
        )
        assert "s360-ai-pill" not in html
        assert "AI-ASSISTED" not in html

    def test_deterministic_path_no_governance_footer(self):
        html = build_priority_card_html(
            **self._det_args(
                what_is_happening=None,
                why_it_matters=None,
                what_management_should_do=None,
                show_ai_pill=False,
                show_governance_footer=False,
            )
        )
        assert "s360-ai-governance" not in html
        assert "AI-assisted interpretation" not in html

    def test_deterministic_path_does_not_render_qa_rows(self):
        html = build_priority_card_html(
            **self._det_args(
                what_is_happening=None,
                why_it_matters=None,
                what_management_should_do=None,
                show_ai_pill=False,
                show_governance_footer=False,
            )
        )
        assert "s360-ai-qa-row" not in html
        assert "WHAT IS HAPPENING?" not in html

    # --- Shared properties ----------------------------------------------------
    def test_card_html_always_includes_period_badge(self):
        html = build_priority_card_html(**self._det_args())
        assert "s360-pm-status-badge forecast" in html
        assert "Forward Risk" in html

    def test_card_html_actual_badge(self):
        html = build_priority_card_html(
            **self._det_args(
                period_badge_text="Past Performance \u2014 Review",
                period_badge_class="actual",
                overall_situation="x",
                highest_priority_alert="y",
            )
        )
        assert "s360-pm-status-badge actual" in html
        assert "Past Performance" in html

    def test_card_html_escapes_html_special_chars(self):
        html = build_priority_card_html(
            **self._det_args(
                overall_situation="<script>alert('xss')</script> & more",
                highest_priority_alert="alert with <b>bold</b>",
            )
        )
        assert "<script>" not in html
        assert "&lt;script&gt;" in html
        assert "&amp;" in html
        # The deterministic fallback alert with <b> tags should also be escaped
        assert "<b>bold</b>" not in html

    def test_card_html_escapes_ai_text(self):
        html = build_priority_card_html(
            **self._qa_args(
                what_is_happening="<img src=x onerror=alert(1)>",
                why_it_matters="<b>bad</b>",
                what_management_should_do="<i>step</i>",
            )
        )
        assert "<img" not in html
        assert "<b>bad</b>" not in html
        assert "<i>step</i>" not in html
        assert "&lt;img" in html
        assert "&lt;b&gt;bad&lt;/b&gt;" in html

    def test_card_html_always_includes_priority_card_wrapper(self):
        html = build_priority_card_html(**self._det_args())
        assert html.startswith('<div class="s360-priority-card">')
        assert html.endswith("</div>")
        assert "Priority Management Review" in html


# ---------------------------------------------------------------------------
# End-to-end synthesis path (status -> render-plan behaviour) for clarity.
# Verifies the executive-Q&A contract end to end.
# ---------------------------------------------------------------------------
from src.ai_management_page_helper import build_render_plan


class TestRenderPlanContract:
    """Verify the contract: given an AI result dict and a forecast flag,
    the page-level code should produce an AI-path or fallback-path HTML.
    Mirrors the exact branch in pages/02_Executive_Overview.py.

    The active contract is the executive Q&A schema. The legacy long-form
    fields are intentionally NOT consulted."""

    @staticmethod
    def _should_use_ai_path(is_forecast: bool, ai_result: Dict[str, Any]) -> bool:
        return (
            is_forecast
            and isinstance(ai_result, dict)
            and ai_result.get("status") == "OK"
            and (
                ai_result.get("what_is_happening")
                or ai_result.get("why_it_matters")
                or ai_result.get("what_management_should_do")
            )
        )

    def test_forecast_ai_ok_takes_ai_path(self):
        assert self._should_use_ai_path(True, _ok_ai_result())

    def test_forecast_ai_timeout_falls_back(self):
        result = {"status": "TIMEOUT", "message": "t"}
        assert not self._should_use_ai_path(True, result)

    def test_forecast_ai_not_configured_falls_back(self):
        result = {"status": "NOT_CONFIGURED", "message": "x"}
        assert not self._should_use_ai_path(True, result)

    def test_forecast_ai_invalid_response_falls_back(self):
        result = {"status": "INVALID_RESPONSE", "message": "x"}
        assert not self._should_use_ai_path(True, result)

    def test_forecast_ai_provider_error_falls_back(self):
        result = {"status": "PROVIDER_ERROR", "message": "x"}
        assert not self._should_use_ai_path(True, result)

    def test_actual_period_never_takes_ai_path(self):
        assert not self._should_use_ai_path(False, _ok_ai_result())

    def test_forecast_ai_ok_with_no_content_falls_back(self):
        """An OK status with all-None structured fields is treated as failure."""
        result = {
            "status": "OK",
            "what_is_happening": None,
            "why_it_matters": None,
            "what_management_should_do": None,
        }
        assert not self._should_use_ai_path(True, result)

    # --- Render-plan helper directly -----------------------------------------
    def test_render_plan_qa_mode_produces_three_questions(self):
        plan = build_render_plan(
            is_forecast=True,
            ai_status="OK",
            ai_payload=_ok_ai_result(),
        )
        assert plan["mode"] == "ai"
        assert plan["show_ai_pill"] is True
        assert plan["show_governance_footer"] is True
        assert len(plan["questions"]) == 3
        labels = [q["label"] for q in plan["questions"]]
        assert labels[0] == "WHAT IS HAPPENING?"
        assert labels[1] == "WHY DOES IT MATTER?"
        assert labels[2] == "WHAT SHOULD MANAGEMENT DO NEXT?"

    def test_render_plan_qa_mode_answers_from_qa_payload(self):
        plan = build_render_plan(
            is_forecast=True,
            ai_status="OK",
            ai_payload=_ok_ai_result(),
        )
        answers = {q["label"]: q["answer"] for q in plan["questions"]}
        assert (
            "ICU bed occupancy is forecast to reach 104.8%"
            in answers["WHAT IS HAPPENING?"]
        )
        assert (
            "Sustained occupancy above 100% signals"
            in answers["WHY DOES IT MATTER?"]
        )
        assert (
            "Review the capacity risk and supporting operational evidence"
            in answers["WHAT SHOULD MANAGEMENT DO NEXT?"]
        )

    def test_render_plan_fallback_mode_is_deterministic(self):
        plan = build_render_plan(
            is_forecast=False,
            ai_status="OK",
            ai_payload=_ok_ai_result(),
        )
        assert plan["mode"] == "deterministic"
        assert plan["show_ai_pill"] is False
        assert plan["show_governance_footer"] is False
        assert plan["questions"] == []

    def test_render_plan_fallback_on_non_ok_status(self):
        plan = build_render_plan(
            is_forecast=True,
            ai_status="TIMEOUT",
            ai_payload={"status": "TIMEOUT"},
        )
        assert plan["mode"] == "deterministic"
        assert plan["show_ai_pill"] is False
        assert plan["show_governance_footer"] is False

    def test_render_plan_fallback_on_api_unavailable(self):
        plan = build_render_plan(
            is_forecast=True,
            ai_status="API_UNAVAILABLE",
            ai_payload={"status": "API_UNAVAILABLE"},
        )
        assert plan["mode"] == "deterministic"
        assert plan["show_ai_pill"] is False

    def test_render_plan_qa_mode_uses_default_governance_note_if_missing(self):
        plan = build_render_plan(
            is_forecast=True,
            ai_status="OK",
            ai_payload={
                "status": "OK",
                "what_is_happening": "H",
                "why_it_matters": "M",
                "what_management_should_do": "D",
            },
        )
        assert plan["governance_note"] == (
            "AI-assisted interpretation of governed Sentinel360 outputs."
        )


# ---------------------------------------------------------------------------
# I. New Q&A contract verifications (spec §13)
# ---------------------------------------------------------------------------
class TestQASchemaContract:
    """Spec §13 — twelve explicit verifications on the executive Q&A schema."""

    def test_01_ai_output_has_three_qa_fields(self):
        plan = build_render_plan(
            is_forecast=True,
            ai_status="OK",
            ai_payload=_ok_ai_result(),
        )
        answers = {q["label"] for q in plan["questions"]}
        assert {
            "WHAT IS HAPPENING?",
            "WHY DOES IT MATTER?",
            "WHAT SHOULD MANAGEMENT DO NEXT?",
        } == answers

    def test_02_no_old_long_form_field_required(self):
        """An AI result with only the three Q&A fields (no legacy fields)
        still renders the AI path. Legacy fields are not required."""
        payload = {
            "status": "OK",
            "what_is_happening": "H",
            "why_it_matters": "M",
            "what_management_should_do": "D",
            # Legacy long-form fields absent (or None) — should be ignored.
            "headline": None,
            "situation": None,
            "management_significance": None,
            "next_step": None,
        }
        plan = build_render_plan(
            is_forecast=True, ai_status="OK", ai_payload=payload
        )
        assert plan["mode"] == "ai"
        assert self._legacy_does_not_render(plan) is None
        # Specifically: the Q&A rows contain only the Q&A answers, never
        # the legacy long-form text.
        labels_and_answers = {
            q["label"]: q["answer"] for q in plan["questions"]
        }
        assert set(labels_and_answers.keys()) == {
            "WHAT IS HAPPENING?",
            "WHY DOES IT MATTER?",
            "WHAT SHOULD MANAGEMENT DO NEXT?",
        }

    @staticmethod
    def _legacy_does_not_render(plan):
        """The render plan must not surface legacy long-form labels."""
        legacy_labels = {"Headline", "Situation",
                         "Management Significance", "Next Step"}
        plan_labels = {q["label"] for q in plan["questions"]}
        assert plan_labels.isdisjoint(legacy_labels), plan_labels
        return None

    def test_03_each_answer_stays_compact(self):
        """The fixture answers are intentionally compact (1-2 sentences,
        each well under 35 words). Assert the word-count budget."""
        payload = _ok_ai_result()
        for key in ("what_is_happening", "why_it_matters",
                    "what_management_should_do"):
            text = payload[key]
            wc = len(text.split())
            assert wc <= 35, f"{key} has {wc} words (max 35)"

    def test_04_technical_model_terms_prohibited_in_prompt(self):
        """Spec §7: explicitly forbidden in the AI prompt: Holt, MAE, SES,
        Moving Average, Linear Trend, HOSP-001, KPI_006, raw 2.746188,
        forecast horizon metadata, risk tier, schema version, internal
        field names, "operational status Priority Management Review",
        "target unavailable", "causality is not confirmed"."""
        from src.ai_management_synthesis import _build_system_prompt
        prompt = _build_system_prompt()
        # The prompt must contain explicit suppression guidance mentioning
        # each forbidden exemplar somewhere in its body.
        for exemplar in (
            "HOSP-001",
            "KPI_006",
            "2.746188",
            "MAE",
            "Holt",
            "SES",
            "Moving Average",
            "Linear Trend",
            "horizon",
            "schema version",
            "field names",
            "risk tier",
            "operational status Priority Management Review",
            "Target value is unavailable",
            "causality is not confirmed",
        ):
            assert exemplar.lower() in prompt.lower(), (
                f"prompt must mention forbidden exemplar '{exemplar}'"
            )

    def test_05_raw_precision_prohibited_in_prompt(self):
        from src.ai_management_synthesis import _build_system_prompt
        prompt = _build_system_prompt()
        # Raw precision must be flagged for suppression.
        assert (
            "raw unrounded" in prompt.lower()
            or "excessive decimal precision" in prompt.lower()
        )
        assert "104.761905" in prompt

    def test_06_kpi_ids_internal_identifiers_discouraged(self):
        from src.ai_management_synthesis import _build_system_prompt
        prompt = _build_system_prompt()
        # The prompt must explicitly discourage the use of internal
        # identifier codes.
        low = prompt.lower()
        assert "kpi_006" in low
        assert "internal identifiers" in low or "coded labels" in low or "kpi id" in low

    def test_07_forecast_ai_success_renders_three_qa_rows(self):
        """End-to-end: FORECAST + status OK + Q&A fields -> 3 Q&A rows."""
        plan = build_render_plan(
            is_forecast=True,
            ai_status="OK",
            ai_payload=_ok_ai_result(),
        )
        assert plan["mode"] == "ai"
        assert len(plan["questions"]) == 3

    def test_08_ai_failure_falls_back(self):
        plan = build_render_plan(
            is_forecast=True,
            ai_status="API_UNAVAILABLE",
            ai_payload={"status": "API_UNAVAILABLE"},
        )
        assert plan["mode"] == "deterministic"
        assert plan["show_ai_pill"] is False
        assert plan["show_governance_footer"] is False

    def test_09_actual_remains_deterministic(self):
        plan = build_render_plan(
            is_forecast=False,
            ai_status="OK",
            ai_payload=_ok_ai_result(),
        )
        assert plan["mode"] == "deterministic"
        assert len(plan["questions"]) == 0

    def test_10_ai_badge_and_footer_only_on_success(self):
        ai_plan = build_render_plan(
            is_forecast=True, ai_status="OK", ai_payload=_ok_ai_result()
        )
        assert ai_plan["show_ai_pill"] is True
        assert ai_plan["show_governance_footer"] is True
        det_plan = build_render_plan(
            is_forecast=True, ai_status="TIMEOUT", ai_payload={"status": "TIMEOUT"}
        )
        assert det_plan["show_ai_pill"] is False
        assert det_plan["show_governance_footer"] is False

    def test_11_cache_version_changes(self):
        """The active cache schema version must be ``ai1_qa_v2`` (a bump
        from the legacy ``ai1_v1`` long-form schema) so stale long-form
        entries are not reused."""
        from src.ai_management_page_helper import _AI_CACHE_SCHEMA_VERSION
        assert _AI_CACHE_SCHEMA_VERSION == "ai1_qa_v2"

    def test_12_no_analytical_logic_changes(self):
        """Sanity: the helper still builds the deterministic text from the
        same state fields the page already provides, with no recomputation."""
        s = _make_state(period_type="FORECAST", dominant_status="Amber")
        f = _make_filters(month=8, year=2025,
                           department_name="Emergency Department")
        out = build_deterministic_priority_text(s, f)
        # The deterministic text branches are unchanged.
        assert "Operational pressure is forecast" in out["overall_situation"]
        assert "most significant forecast risk" in out["highest_priority_alert"]


# ---------------------------------------------------------------------------
# J. Active dataclass contract — verifies the parser emits Q&A fields
# ---------------------------------------------------------------------------
class TestDataclassQASchema:
    def test_dataclass_accepts_qa_fields(self):
        r = AIManagementSynthesisResult(
            status="OK",
            what_is_happening="H",
            why_it_matters="M",
            what_management_should_do="D",
            governance_note="G",
        )
        assert r.what_is_happening == "H"
        assert r.why_it_matters == "M"
        assert r.what_management_should_do == "D"
        assert r.governance_note == "G"

    def test_dataclass_legacy_long_form_fields_default_to_none(self):
        """Backward-compat: legacy fields remain on the dataclass, default
        to None, and are not surfaced anywhere in the active contract."""
        r = AIManagementSynthesisResult(status="OK")
        assert r.headline is None
        assert r.situation is None
        assert r.management_significance is None
        assert r.next_step is None

    def test_dataclass_legacy_fields_can_be_set_explicitly(self):
        """If a downstream tool pre-populates the legacy fields, the
        dataclass still accepts them — but the helper / render plan never
        sets or renders them in the active contract."""
        r = AIManagementSynthesisResult(
            status="OK",
            headline="H", situation="S",
            management_significance="M", next_step="N",
            what_is_happening="W", why_it_matters="W",
            what_management_should_do="W",
        )
        plan = build_render_plan(is_forecast=True, ai_status="OK",
                                 ai_payload=r.__dict__)
        labels = {q["label"] for q in plan["questions"]}
        # Legacy labels must not appear.
        assert "Headline" not in labels
        assert "Situation" not in labels
        assert "Management Significance" not in labels
        assert "Next Step" not in labels
        # Q&A labels must appear.
        assert "WHAT IS HAPPENING?" in labels

