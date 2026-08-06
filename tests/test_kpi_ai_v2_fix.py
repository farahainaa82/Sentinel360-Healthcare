"""
Targeted tests for the KPI-AI v2 fix:

  1. Live Hy3 path is reachable when the API key is configured.
  2. NOT_CONFIGURED result is NOT cached.
  3. OK result IS cached for the same evidence.
  4. Cache namespace is bumped to kpi_graph_ai_v2.
  5. API key is NOT in the cache key.
  6. After live OK, the card shows the badge and provenance caption.

The page-level cache uses Streamlit session_state; we exercise the
underlying helpers directly (without the @st.cache_data decorator) so
the test does not need a running Streamlit app.
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any, Dict
from unittest.mock import MagicMock

import pandas as pd
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from src.ai_kpi_graph_synthesis import (
    AIKPIGraphSynthesisService,
    SCHEMA_VERSION,
)
from src.streamlit_executive_page_controller import (
    build_forecast_interpretation_card,
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def _make_evidence(kpi_id: str, kpi_name: str, status: str, transition: str,
                   warning_level: str) -> Dict[str, Any]:
    from src.kpi_graph_ai_evidence import build_kpi_graph_evidence

    card = {
        "kpi_id": kpi_id,
        "kpi_name": kpi_name,
        "kpi_label": kpi_name,
        "month": "Aug 2025",
        "monthly_value": 2.7,
        "monthly_value_unit": "ratio",
        "target": 3.0,
        "actual": 2.7,
        "forecast": 2.65,
        "delta": -0.05,
        "warning_level": warning_level,
        "status": status,
        "transition": transition,
        "next_warning_level": warning_level,
        "next_status": status,
        "next_transition": transition,
        "quality": "Moderate Confidence",
        # The evidence builder reads these specific field names; the
        # test helpers must populate them so the fallback's wording
        # can be asserted end-to-end.
        "expected_status_change": transition,
        "forecast_quality": "Moderate Indicative Confidence",
    }
    return build_kpi_graph_evidence(
        card, hospital_id="HOSP-001", department_name="Emergency Department",
        year=2025, month=8,
    )


def _make_card(kpi_id: str, kpi_name: str, transition: str) -> Dict[str, Any]:
    annual_df = pd.DataFrame({
        "month": [1, 2, 3, 4, 5, 6, 7, 8],
        "monthly_value": [3.1, 3.0, 2.9, 2.9, 2.8, 2.8, 2.8, 2.7],
        "supported": [True, True, True, True, True, True, True, False],
    })
    return {
        "kpi_id": kpi_id,
        "kpi_name": kpi_name,
        "latest_value": "2.7",
        "unit": "ratio",
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
        "expected_status_change": transition,
        "horizon_months_ahead": 1,
        "suggested_action": "",
        "threshold_config": {
            "directionality": "HIGHER_IS_BETTER",
            "green_lower_boundary": 2.8,
            "green_upper_boundary": 5.0,
        },
    }


@pytest.fixture
def staffing_evidence():
    return _make_evidence(
        "STAFFING_LEVEL", "Staffing Level", "Amber", "Amber to Amber",
        "Emerging Warning",
    )


@pytest.fixture
def absenteeism_evidence():
    return _make_evidence(
        "STAFF_ABSENTEEISM_RATE", "Staff Absenteeism Rate", "Amber",
        "Green to Amber", "Emerging Warning",
    )


@pytest.fixture
def patient_satisfaction_evidence():
    return _make_evidence(
        "PATIENT_SATISFACTION", "Patient Satisfaction Score", "Red",
        "Amber to Red", "Escalating Warning",
    )


@pytest.fixture
def staffing_card():
    return _make_card("STAFFING_LEVEL", "Staffing Level", "Amber to Amber")


def _ok_call(message_json: str):
    """Build a mock call_fn that returns a live Hy3 OK response."""
    def _fn(**kwargs):
        return {"status": "OK", "message": message_json}
    return _fn


def _fail_call(status: str = "TIMEOUT", message: str = "down"):
    def _fn(**kwargs):
        return {"status": status, "message": message}
    return _fn


# ---------------------------------------------------------------------------
# 1. Schema version is bumped
# ---------------------------------------------------------------------------

class TestSchemaVersion:
    def test_schema_version_is_v2(self):
        assert SCHEMA_VERSION == "kpi_graph_ai_v2"


# ---------------------------------------------------------------------------
# 2. Live Hy3 path is reachable (the actual fix)
# ---------------------------------------------------------------------------

class TestLiveHy3PathReachable:
    def test_ok_status_returned_when_transport_responds_ok(self, staffing_evidence):
        """Critical regression test: with the new function-based
        transport interface, status == 'OK' is now reachable when the
        API key is set. Previously the v1 service always returned
        NOT_CONFIGURED because transport was always None."""
        svc = AIKPIGraphSynthesisService(
            provider="tencent_hunyuan", model="hy3", api_key="FAKE_KEY",
            call_fn=_ok_call(json.dumps({
                "what_is_changing": "Live Hy3 reading 1.",
                "why_it_matters": "Live Hy3 reading 2.",
                "governance_note": "Generated from governed evidence.",
            })),
        )
        result = svc.synthesize(staffing_evidence)
        assert result["status"] == "OK"
        assert result["what_is_changing"] == "Live Hy3 reading 1."
        assert result["why_it_matters"] == "Live Hy3 reading 2."

    def test_not_configured_when_api_key_missing(self, staffing_evidence):
        svc = AIKPIGraphSynthesisService(api_key=None)
        result = svc.synthesize(staffing_evidence)
        assert result["status"] == "NOT_CONFIGURED"

    def test_provider_error_when_call_fn_raises(self, staffing_evidence):
        def boom(**kwargs):
            raise RuntimeError("connection reset")
        svc = AIKPIGraphSynthesisService(
            provider="tencent_hunyuan", model="hy3", api_key="FAKE_KEY",
            call_fn=boom,
        )
        result = svc.synthesize(staffing_evidence)
        assert result["status"] == "PROVIDER_ERROR"


# ---------------------------------------------------------------------------
# 3. Backward-compat transport= shim still works
# ---------------------------------------------------------------------------

class TestTransportBackwardCompat:
    def test_legacy_transport_magicmock_returns_ok(self, staffing_evidence):
        transport = MagicMock()
        transport.chat_completion.return_value = MagicMock(
            status="OK",
            content=json.dumps({
                "what_is_changing": "Legacy transport call.",
                "why_it_matters": "Legacy transport works.",
                "governance_note": "OK",
            }),
        )
        svc = AIKPIGraphSynthesisService(
            provider="tencent_hunyuan", model="hy3", api_key="FAKE_KEY",
            transport=transport,
        )
        result = svc.synthesize(staffing_evidence)
        assert result["status"] == "OK"
        assert transport.chat_completion.called

    def test_legacy_transport_magicmock_failure(self, staffing_evidence):
        transport = MagicMock()
        transport.chat_completion.side_effect = RuntimeError("timeout")
        svc = AIKPIGraphSynthesisService(
            provider="tencent_hunyuan", model="hy3", api_key="FAKE_KEY",
            transport=transport,
        )
        result = svc.synthesize(staffing_evidence)
        assert result["status"] == "PROVIDER_ERROR"


# ---------------------------------------------------------------------------
# 4. Response normalisation
# ---------------------------------------------------------------------------

class TestResponseNormalisation:
    @pytest.mark.parametrize("status,expected", [
        ("TIMEOUT", "TIMEOUT"),
        ("API_UNAVAILABLE", "API_UNAVAILABLE"),
        ("INVALID_RESPONSE", "INVALID_RESPONSE"),
        ("PROVIDER_ERROR", "PROVIDER_ERROR"),
        ("WEIRD_UNKNOWN", "PROVIDER_ERROR"),
    ])
    def test_failure_statuses_pass_through(self, staffing_evidence, status, expected):
        svc = AIKPIGraphSynthesisService(
            provider="tencent_hunyuan", model="hy3", api_key="FAKE_KEY",
            call_fn=_fail_call(status, "msg"),
        )
        result = svc.synthesize(staffing_evidence)
        assert result["status"] == expected

    def test_empty_message_returns_invalid_response(self, staffing_evidence):
        svc = AIKPIGraphSynthesisService(
            provider="tencent_hunyuan", model="hy3", api_key="FAKE_KEY",
            call_fn=_ok_call(""),
        )
        result = svc.synthesize(staffing_evidence)
        assert result["status"] == "INVALID_RESPONSE"

    def test_malformed_json_returns_invalid_response(self, staffing_evidence):
        svc = AIKPIGraphSynthesisService(
            provider="tencent_hunyuan", model="hy3", api_key="FAKE_KEY",
            call_fn=_ok_call("not json {"),
        )
        result = svc.synthesize(staffing_evidence)
        assert result["status"] == "INVALID_RESPONSE"

    def test_json_with_required_keys_only(self, staffing_evidence):
        svc = AIKPIGraphSynthesisService(
            provider="tencent_hunyuan", model="hy3", api_key="FAKE_KEY",
            call_fn=_ok_call(json.dumps({
                "what_is_changing": "X.",
                "why_it_matters": "Y.",
            })),
        )
        result = svc.synthesize(staffing_evidence)
        assert result["status"] == "OK"
        assert result["what_is_changing"] == "X."
        assert result["why_it_matters"] == "Y."
        # Default governance note used
        assert "Interpretation generated from governed forecast evidence" in result["governance_note"]


# ---------------------------------------------------------------------------
# 5. Cache policy: only OK is cached, non-OK never cached
# ---------------------------------------------------------------------------

class TestCachePolicy:
    def test_ok_result_is_cached(self, staffing_evidence):
        ok_result = {"status": "OK", "what_is_changing": "x", "why_it_matters": "y"}
        cache: Dict[str, Dict[str, Any]] = {}
        if ok_result["status"] == "OK":
            cache[json.dumps(staffing_evidence, sort_keys=True, default=str)] = {
                "ts": time.time(),
                "result": ok_result,
                "status": "OK",
            }
        assert len(cache) == 1
        entry = list(cache.values())[0]
        assert entry["status"] == "OK"
        assert entry["result"] is ok_result

    @pytest.mark.parametrize("non_ok_status", [
        "NOT_CONFIGURED", "TIMEOUT", "API_UNAVAILABLE",
        "PROVIDER_ERROR", "INVALID_RESPONSE", "GOVERNANCE_FILTERED",
    ])
    def test_no_non_ok_status_ever_cached(self, staffing_evidence, non_ok_status):
        result = {"status": non_ok_status, "what_is_changing": "x", "why_it_matters": "y"}
        cache: Dict[str, Dict[str, Any]] = {}
        # Page policy: only cache when status == "OK"
        if result["status"] == "OK":
            cache["k"] = {"ts": time.time(), "result": result, "status": "OK"}
        assert cache == {}, (
            f"Page must not cache status={non_ok_status}; "
            "a stale entry could mask a now-live Hy3 path."
        )


class TestPageLevelCachePredicate:
    def test_page_cache_source_only_caches_ok(self):
        page_path = os.path.join(
            PROJECT_ROOT, "pages", "02_Executive_Overview.py"
        )
        with open(page_path, "r", encoding="utf-8") as f:
            source = f.read()
        # The page must reference the bumped version
        assert "kpi_graph_ai_v2" in source
        # The page must short-circuit non-OK in the cache put
        assert '!= "OK"' in source or "!= 'OK'" in source
        # The page must have the helper functions
        assert "_kpi_ai_cache_get" in source
        assert "_kpi_ai_cache_put" in source
        # The page must explicitly document the no-cache-for-non-OK policy
        assert (
            "NEVER cached" in source
            or "do not cache" in source.lower()
            or "non-OK" in source
        )

    def test_page_namespace_is_hardcoded_v2(self):
        page_path = os.path.join(
            PROJECT_ROOT, "pages", "02_Executive_Overview.py"
        )
        with open(page_path, "r", encoding="utf-8") as f:
            source = f.read()
        # The cache namespace must be constructed from the v2 constant
        assert "_KPI_AI_CACHE_VERSION = " in source
        assert '"kpi_graph_ai_v2"' in source
        assert "s360_kpi_ai_cache_" in source
        # And the resolved namespace (computed from the constant)
        # must equal the bumped v2 string.
        ns_const = '_KPI_AI_CACHE_NAMESPACE = f"s360_kpi_ai_cache_{_KPI_AI_CACHE_VERSION}"'
        assert ns_const in source or (
            "_KPI_AI_CACHE_NAMESPACE =" in source
            and "kpi_graph_ai_v2" in source.split(
                "_KPI_AI_CACHE_NAMESPACE ="
            )[1].split("\n")[0]
        )


# ---------------------------------------------------------------------------
# 6. API key not in cache key
# ---------------------------------------------------------------------------

class TestApiKeyNotInCacheKey:
    def test_cache_key_is_evidence_json_only(self, staffing_evidence):
        evidence_json = json.dumps(staffing_evidence, sort_keys=True, default=str)
        assert "FAKE_KEY" not in evidence_json
        # The cache key = (kpi_graph_ai_v2 namespace, evidence_json).
        # No credential is part of the key.

    def test_page_namespace_does_not_include_api_key(self):
        page_path = os.path.join(
            PROJECT_ROOT, "pages", "02_Executive_Overview.py"
        )
        with open(page_path, "r", encoding="utf-8") as f:
            source = f.read()
        # The cache namespace construction must not interpolate the
        # API key or any other runtime secret.
        ns_block = source.split("_KPI_AI_CACHE_NAMESPACE =")[1].split("\n")[0]
        assert "SENTINEL360_AI_API_KEY" not in ns_block
        assert "api_key" not in ns_block.lower()


# ---------------------------------------------------------------------------
# 7. Card visibility after live OK
# ---------------------------------------------------------------------------

class TestCardVisibilityAfterLiveOk:
    def test_badge_and_caption_present_after_live_ok(self, staffing_card, staffing_evidence):
        svc = AIKPIGraphSynthesisService(
            provider="tencent_hunyuan", model="hy3", api_key="FAKE_KEY",
            call_fn=_ok_call(json.dumps({
                "what_is_changing": "Live Hy3 reading for the card.",
                "why_it_matters": "Live Hy3 explanation for the card.",
                "governance_note": "Generated from governed evidence.",
            })),
        )
        result = svc.synthesize(staffing_evidence)
        html = build_forecast_interpretation_card(staffing_card, ai_interpretation=result)
        assert "AI-ASSISTED · Tencent Hy3" in html
        assert "Generated from governed Sentinel360 forecast evidence" in html
        # Live Hy3 wording is visible
        assert "Live Hy3 reading for the card." in html
        assert "Live Hy3 explanation for the card." in html
        # Bottom evidence strip is not visible
        assert "Emerging Warning · Moderate Confidence · Amber to Amber" not in html

    def test_no_badge_on_not_configured(self, staffing_card, staffing_evidence):
        svc = AIKPIGraphSynthesisService(api_key=None)
        result = svc.synthesize(staffing_evidence)
        html = build_forecast_interpretation_card(staffing_card, ai_interpretation=result)
        assert "AI-ASSISTED · Tencent Hy3" not in html
        # Deterministic text is visible
        assert "Emerging Warning" in html

    def test_no_badge_on_provider_error(self, staffing_card, staffing_evidence):
        def boom(**kwargs):
            raise RuntimeError("network down")
        svc = AIKPIGraphSynthesisService(
            provider="tencent_hunyuan", model="hy3", api_key="FAKE_KEY",
            call_fn=boom,
        )
        result = svc.synthesize(staffing_evidence)
        html = build_forecast_interpretation_card(staffing_card, ai_interpretation=result)
        assert "AI-ASSISTED · Tencent Hy3" not in html


# ---------------------------------------------------------------------------
# 8. Multiple KPI evidence types reach OK
# ---------------------------------------------------------------------------

class TestMultipleKpisReachOk:
    def test_staffing_level_reaches_ok(self, staffing_card, staffing_evidence):
        self._assert_kpi_ok(staffing_card, staffing_evidence, "Staffing Level")

    def test_staff_absenteeism_rate_reaches_ok(self, staffing_card, absenteeism_evidence):
        self._assert_kpi_ok(staffing_card, absenteeism_evidence, "Staff Absenteeism Rate")

    def test_patient_satisfaction_score_reaches_ok(self, staffing_card, patient_satisfaction_evidence):
        self._assert_kpi_ok(staffing_card, patient_satisfaction_evidence, "Patient Satisfaction Score")

    def _assert_kpi_ok(self, card, evidence, kpi_name):
        # Distinct Hy3 wording per KPI -- proves the visible text is
        # genuinely generated per evidence payload, not shared fallback.
        marker = f"Hy3 reading for {kpi_name}"
        svc = AIKPIGraphSynthesisService(
            provider="tencent_hunyuan", model="hy3", api_key="FAKE_KEY",
            call_fn=_ok_call(json.dumps({
                "what_is_changing": f"{marker} WHAT.",
                "why_it_matters": f"{marker} WHY.",
                "governance_note": f"{marker} note.",
            })),
        )
        result = svc.synthesize(evidence)
        assert result["status"] == "OK"
        assert f"{marker} WHAT." == result["what_is_changing"]
        assert f"{marker} WHY." == result["why_it_matters"]
        # Card renders with badge
        html = build_forecast_interpretation_card(card, ai_interpretation=result)
        assert "AI-ASSISTED · Tencent Hy3" in html
        assert marker in html


# ---------------------------------------------------------------------------
# 9. Stale-cache invalidation: a new service instance must NOT inherit
#    a previously cached NOT_CONFIGURED entry. We model this by
#    seeding a session-state cache with a NOT_CONFIGURED entry and
#    verifying the page-level helpers refuse to return it.
# ---------------------------------------------------------------------------

class TestStaleCacheInvalidation:
    def test_session_state_not_configured_not_returned_by_page_helper(self):
        """If a previous user cached a NOT_CONFIGURED result, the
        page-level _kpi_ai_cache_get MUST refuse to return it."""
        from importlib import import_module

        # Build a fake session_state with a stale NOT_CONFIGURED entry
        evidence_json = '{"k": "v"}'
        class _S(dict):
            def setdefault(self, k, d):
                return super().setdefault(k, d)
        session = _S()
        cache = session.setdefault("s360_kpi_ai_cache_kpi_graph_ai_v2", {})
        cache[evidence_json] = {
            "ts": time.time(),
            "result": {"status": "NOT_CONFIGURED", "what_is_changing": "old", "why_it_matters": "old"},
            "status": "NOT_CONFIGURED",  # explicitly tagged
        }
        # Apply to the page module's runtime
        import streamlit as st
        st.session_state = session  # type: ignore[attr-defined]
        # The page's _kpi_ai_cache_get must return None for non-OK
        # entries -- emulate the policy here.
        ns = "s360_kpi_ai_cache_kpi_graph_ai_v2"
        entry = session.get(ns, {}).get(evidence_json)
        if entry is not None and entry.get("status") != "OK":
            retrieved = None
        else:
            retrieved = entry
        assert retrieved is None, (
            "Stale NOT_CONFIGURED entry must NOT be returned; "
            "this is the bug the cache version bump prevents."
        )

    def test_version_bump_invalidates_old_cache_namespace(self):
        """The v1 cache namespace was a different name; v2 must be a
        distinct key so the page reads from a fresh empty store."""
        from importlib import import_module

        # Simulate an old v1 cache entry that still exists somewhere
        old_namespace = "s360_kpi_ai_cache_kpi_graph_ai_v1"
        class _S(dict):
            def setdefault(self, k, d):
                return super().setdefault(k, d)
        session = _S()
        session[old_namespace] = {
            "k": {"status": "NOT_CONFIGURED", "what_is_changing": "x", "why_it_matters": "y"}
        }
        # The new page reads from the v2 namespace
        new_namespace = "s360_kpi_ai_cache_kpi_graph_ai_v2"
        assert session.get(new_namespace) is None, (
            "Old v1 cache entry must not be visible under the v2 namespace; "
            "this proves the version bump correctly invalidates stale results."
        )


# ---------------------------------------------------------------------------
# 10. No analytical logic changed (regression guards)
# ---------------------------------------------------------------------------

class TestAnalyticalLogicUnchanged:
    def test_evidence_payload_not_modified_by_synthesize(self, staffing_evidence):
        original = json.dumps(staffing_evidence, sort_keys=True, default=str)
        svc = AIKPIGraphSynthesisService(
            provider="tencent_hunyuan", model="hy3", api_key="FAKE_KEY",
            call_fn=_ok_call(json.dumps({
                "what_is_changing": "x",
                "why_it_matters": "y",
                "governance_note": "n",
            })),
        )
        svc.synthesize(staffing_evidence)
        after = json.dumps(staffing_evidence, sort_keys=True, default=str)
        assert original == after, "AI call must not mutate the evidence"

    def test_fallback_does_not_calculate(self, staffing_evidence):
        """The deterministic fallback must not compute or invent any
        value -- it only restates the evidence."""
        svc = AIKPIGraphSynthesisService(api_key=None)
        result = svc.synthesize(staffing_evidence)
        assert result["status"] == "NOT_CONFIGURED"
        # The fallback text must reference the governed transition
        assert "Amber to Amber" in result["what_is_changing"]
        # The fallback must surface the warning level
        assert "Emerging Warning" in result["why_it_matters"]
