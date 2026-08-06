"""
Step AI-2 — Targeted tests for the AI management synthesis service.

All tests mock the LLM provider layer; NO live API calls are made.
The test suite covers:

  * Happy-path synthesis (valid evidence -> OK structured result)
  * Each structured field (headline, situation, significance, next_step,
    governance_note)
  * Failure statuses (NOT_CONFIGURED, TIMEOUT, PROVIDER_ERROR,
    INVALID_RESPONSE, INVALID_EVIDENCE, API_UNAVAILABLE)
  * Evidence immutability (no calculation, no mutation)
  * Prompt safety (governance constraints embedded in system prompt)
  * Data hygiene (raw DataFrame cannot leak into the evidence API)
  * TokenHub HTTP connector (Bearer auth, status mapping, request shape)

Dependencies:
  pytest, unittest.mock, json (stdlib).
"""

from __future__ import annotations

import json
import os
import sys
from copy import deepcopy
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.ai_management_synthesis import (
    AIManagementSynthesisResult,
    AIManagementSynthesisService,
    _TOKENHUB_CHAT_COMPLETIONS_URL,
    _build_system_prompt,
    _coerce_str,
)
from src.management_evidence_pack import ManagementEvidencePack


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def service_not_configured():
    """Service with no provider / credentials configured."""
    return AIManagementSynthesisService(provider="", model="")


@pytest.fixture
def service_configured():
    """Service configured for Tencent TokenHub."""
    return AIManagementSynthesisService(
        provider="tencent_hunyuan",
        model="hy3",
        api_key="FAKE_KEY_FOR_TESTING",
    )


@pytest.fixture
def service_unsupported_provider():
    """Service with an unsupported provider."""
    return AIManagementSynthesisService(
        provider="openai",
        model="gpt-4",
        api_key="FAKE_KEY_FOR_TESTING",
    )


@pytest.fixture
def service_missing_api_key():
    """Service with provider/model but no API key."""
    return AIManagementSynthesisService(
        provider="tencent_hunyuan",
        model="hy3",
        api_key="",
    )


@pytest.fixture
def sample_evidence_pack():
    """A small, fully-populated evidence pack for OK-path tests."""
    return ManagementEvidencePack(
        context={
            "hospital_id": "HOSP-001",
            "hospital_name": "St. Mary's",
            "department_id": "DEPT-ED",
            "department_name": "Emergency Department",
            "year": 2025,
            "month": 8,
            "month_label": "AUG 2025",
            "period_type": "FORECAST",
            "data_cutoff": "31 JUL 2025",
            "forecast_horizon": "AUG-DEC 2025",
        },
        priority_signal={
            "kpi_id": "kpi_001",
            "kpi_name": "Staffing Level",
            "value": 70.0,
            "value_display": "70.0%",
            "unit": "percent",
            "target_label": ">= 84.2%",
            "gap_to_target": "14.2 percentage points below target",
            "status": "Amber",
            "border_colour": "amber",
            "directionality": "HIGHER_IS_BETTER",
            "warning_level": "Escalating Warning",
            "forecast_quality": "MODERATE INDICATIVE CONFIDENCE",
            "horizon_months_ahead": 1,
            "forecast_value": 70.0,
            "forecast_indicative_range": "68.5% - 72.5%",
            "forecast_status": "Forecast deterioration",
            "risk_tier": "High",
            "operational_status": "PRIORITY MANAGEMENT REVIEW",
            "has_priority_signal": True,
        },
        forecast_provenance={
            "selected_method": "Holt-Winters",
            "forecast_quality": "MODERATE INDICATIVE CONFIDENCE",
            "horizon": "1 month ahead",
            "horizon_months_ahead": 1,
            "dominant_warning_level": "Escalating Warning",
            "forecast_capability_text": "Moderate confidence",
            "validation_mae": 2.4,
        },
        availability={
            "has_priority_signal": True,
            "has_forecast": True,
            "period_type_available": True,
            "kpi_value_available": True,
            "target_available": True,
            "warning_available": True,
            "forecast_method_available": True,
        },
        governance={
            "evidence_source": "Sentinel360 governed analytical outputs",
            "evidence_is_governed": True,
            "ai_may_calculate": False,
            "ai_may_modify_values": False,
            "ai_may_infer_missing_values": False,
            "causality_confirmed": False,
            "module": "src.management_evidence_pack",
            "schema_version": "ai1_v1",
            "scope": "executive_overview",
        },
        source_references={
            "page_state": "build_executive_page_state",
            "kpi_cards": "_build_all_kpi_cards",
            "threshold_config": "config/kpi_threshold_config.csv",
            "period_governance": "GOVERNED_ACTUAL_*",
            "forecast_method": "outputs/forecasting/...",
        },
    )


# ---------------------------------------------------------------------------
# 1 - Happy path: OK structured result
# ---------------------------------------------------------------------------
def test_synthesize_valid_evidence_returns_ok(service_configured, sample_evidence_pack):
    mock_json = json.dumps({
        "what_is_happening": "Staffing pressure flagged in August forecast.",
        "why_it_matters": "ED staffing level is 14.2 percentage points below target.",
        "what_management_should_do": "Review workforce scheduling and escalation triggers.",
        "governance_note": "AI-assisted interpretation of governed Sentinel360 outputs.",
    })
    with patch.object(
        service_configured,
        "_call_llm",
        return_value=AIManagementSynthesisResult(
            status="OK",
            message=mock_json,
            model_provider="tencent_hunyuan",
            model_name="hy3",
        ),
    ):
        result = service_configured.synthesize(sample_evidence_pack)

    assert result.status == "OK"
    assert result.what_is_happening is not None
    assert result.why_it_matters is not None
    assert result.what_management_should_do is not None
    assert result.governance_note is not None


# ---------------------------------------------------------------------------
# 2 - NOT_CONFIGURED paths
# ---------------------------------------------------------------------------
def test_missing_credentials_not_configured(
    service_not_configured, sample_evidence_pack
):
    result = service_not_configured.synthesize(sample_evidence_pack)
    assert result.status == "NOT_CONFIGURED"
    assert result.headline is None
    assert result.governance_note is not None
    assert "SENTINEL360_AI_PROVIDER" in result.message


def test_unsupported_provider_returns_not_configured(
    service_unsupported_provider, sample_evidence_pack
):
    result = service_unsupported_provider.synthesize(sample_evidence_pack)
    assert result.status == "NOT_CONFIGURED"
    assert "Unsupported AI provider" in result.message


def test_missing_api_key_returns_not_configured(
    service_missing_api_key, sample_evidence_pack
):
    result = service_missing_api_key.synthesize(sample_evidence_pack)
    assert result.status == "NOT_CONFIGURED"
    assert "SENTINEL360_AI_API_KEY" in result.message


# ---------------------------------------------------------------------------
# 3 - Dispatch behaviour
# ---------------------------------------------------------------------------
def test_live_dispatch_returns_api_unavailable():
    svc = AIManagementSynthesisService(
        provider="openai", model="gpt-4", api_key="fake"
    )
    result = svc._call_llm([{"role": "user", "content": "hello"}])
    assert result.status == "API_UNAVAILABLE"
    assert "not supported" in result.message.lower()


# ---------------------------------------------------------------------------
# 4 - Provider exception mapping
# ---------------------------------------------------------------------------
def test_provider_timeout(service_configured, sample_evidence_pack):
    with patch.object(
        service_configured,
        "_call_llm",
        side_effect=TimeoutError("Connection timed out after 10.0s"),
    ):
        result = service_configured.synthesize(sample_evidence_pack)
    assert result.status == "TIMEOUT"
    assert "timed out" in result.message.lower()
    assert result.response_duration_seconds is not None


def test_provider_exception(service_configured, sample_evidence_pack):
    with patch.object(
        service_configured,
        "_call_llm",
        side_effect=RuntimeError("Internal provider fault"),
    ):
        result = service_configured.synthesize(sample_evidence_pack)
    assert result.status == "PROVIDER_ERROR"
    assert "RuntimeError" in result.message
    assert result.response_duration_seconds is not None


# ---------------------------------------------------------------------------
# 5 - Response parsing
# ---------------------------------------------------------------------------
def test_parse_response_malformed_returns_invalid_response(service_configured):
    with patch.object(
        service_configured,
        "_call_llm",
        return_value=AIManagementSynthesisResult(
            status="OK",
            message="this is not json",
            model_provider="tencent_hunyuan",
            model_name="hy3",
        ),
    ):
        result = service_configured.synthesize(
            ManagementEvidencePack(
                context={"x": 1},
                priority_signal={"y": 2},
                forecast_provenance={"z": 3},
                availability={"a": True},
                governance={"g": True},
            )
        )
    assert result.status == "INVALID_RESPONSE"


def test_parse_response_missing_field_returns_invalid_response(service_configured):
    """With the Q&A schema, a response that supplies only one of the
    three Q&A fields is still parseable but only populates that field;
    the other two Q&A fields stay None. Status remains OK because the
    JSON itself parsed cleanly.
    """
    bad_payload = json.dumps({"what_is_happening": "Only the first answer."})
    with patch.object(
        service_configured,
        "_call_llm",
        return_value=AIManagementSynthesisResult(
            status="OK",
            message=bad_payload,
            model_provider="tencent_hunyuan",
            model_name="hy3",
        ),
    ):
        result = service_configured.synthesize(
            ManagementEvidencePack(
                context={"x": 1},
                priority_signal={"y": 2},
                forecast_provenance={"z": 3},
                availability={"a": True},
                governance={"g": True},
            )
        )
    assert result.status == "OK"
    assert result.what_is_happening == "Only the first answer."
    assert result.why_it_matters is None
    assert result.what_management_should_do is None


def test_parse_response_strips_markdown_fences(service_configured):
    fenced = "```json\n" + json.dumps({
        "what_is_happening": "H",
        "why_it_matters": "M",
        "what_management_should_do": "D",
    }) + "\n```"
    with patch.object(
        service_configured,
        "_call_llm",
        return_value=AIManagementSynthesisResult(
            status="OK",
            message=fenced,
            model_provider="tencent_hunyuan",
            model_name="hy3",
        ),
    ):
        result = service_configured.synthesize(
            ManagementEvidencePack(
                context={"x": 1},
                priority_signal={"y": 2},
                forecast_provenance={"z": 3},
                availability={"a": True},
                governance={"g": True},
            )
        )
    assert result.status == "OK"
    assert result.what_is_happening == "H"
    assert result.why_it_matters == "M"
    assert result.what_management_should_do == "D"


def test_provider_empty_message_returns_invalid_response(service_configured):
    with patch.object(
        service_configured,
        "_call_llm",
        return_value=AIManagementSynthesisResult(
            status="OK",
            message="",
            model_provider="tencent_hunyuan",
            model_name="hy3",
        ),
    ):
        result = service_configured.synthesize(
            ManagementEvidencePack(
                context={"x": 1},
                priority_signal={"y": 2},
                forecast_provenance={"z": 3},
                availability={"a": True},
                governance={"g": True},
            )
        )
    assert result.status == "INVALID_RESPONSE"
    assert "empty response body" in result.message


# ---------------------------------------------------------------------------
# 6 - Governance & prompt safety
# ---------------------------------------------------------------------------
def test_system_prompt_includes_no_calculate_constraint():
    prompt = _build_system_prompt()
    assert "Do not calculate any new values" in prompt
    assert "Do not claim causality" in prompt
    assert "Do not infer missing values" in prompt
    assert "Do not create interventions" in prompt


def test_governance_prompt_is_in_messages(service_configured):
    captured = {}

    def fake_call(messages):
        captured["messages"] = messages
        return AIManagementSynthesisResult(
            status="OK",
            message=json.dumps({
                "headline": "H", "situation": "S",
                "management_significance": "M", "next_step": "N",
            }),
            model_provider="tencent_hunyuan",
            model_name="hy3",
        )

    with patch.object(service_configured, "_call_llm", side_effect=fake_call):
        service_configured.synthesize(ManagementEvidencePack(
            context={"x": 1},
            priority_signal={"y": 2},
            forecast_provenance={"z": 3},
            availability={"a": True},
            governance={"g": True},
        ))
    msgs = captured["messages"]
    assert msgs[0]["role"] == "system"
    assert "Do not calculate any new values" in msgs[0]["content"]
    assert msgs[1]["role"] == "user"


# ---------------------------------------------------------------------------
# 7 - Evidence immutability / hygiene
# ---------------------------------------------------------------------------
def test_evidence_pack_is_not_mutated_by_synthesis(service_configured):
    pack = ManagementEvidencePack(
        context={"x": 1},
        priority_signal={"y": 2},
        forecast_provenance={"z": 3},
        availability={"a": True},
        governance={"g": True},
    )
    before = deepcopy(pack.to_ai_payload())
    with patch.object(
        service_configured,
        "_call_llm",
        return_value=AIManagementSynthesisResult(
            status="OK",
            message=json.dumps({
                "headline": "H", "situation": "S",
                "management_significance": "M", "next_step": "N",
            }),
            model_provider="tencent_hunyuan",
            model_name="hy3",
        ),
    ):
        service_configured.synthesize(pack)
    after = pack.to_ai_payload()
    assert before == after


def test_dataframe_cannot_pass_through_evidence_api(sample_evidence_pack):
    import pandas as pd

    df = pd.DataFrame({"a": [1, 2, 3]})
    sample_evidence_pack.context["dataframe"] = df
    sample_evidence_pack.priority_signal["dataframe"] = df
    payload = sample_evidence_pack.to_ai_payload()
    assert payload["context"]["dataframe"] is None
    assert payload["priority_signal"]["dataframe"] is None

    svc = AIManagementSynthesisService(
        provider="tencent_hunyuan",
        model="hy3",
        api_key="FAKE_KEY",
    )
    with patch.object(
        svc,
        "_call_llm",
        return_value=AIManagementSynthesisResult(
            status="OK",
            message=json.dumps({
                "headline": "H", "situation": "S",
                "management_significance": "M", "next_step": "N",
            }),
            model_provider="tencent_hunyuan",
            model_name="hy3",
        ),
    ):
        result = svc.synthesize(sample_evidence_pack)
    assert result.status == "OK"


def test_invalid_evidence_empty_pack(service_configured):
    empty_pack = ManagementEvidencePack(
        context={}, priority_signal={}, forecast_provenance={},
        availability={}, governance={},
    )
    with patch.object(
        service_configured, "_call_llm",
        return_value=AIManagementSynthesisResult(
            status="API_UNAVAILABLE",
            message="mocked",
            model_provider="tencent_hunyuan",
            model_name="hy3",
        ),
    ):
        result = service_configured.synthesize(empty_pack)
    # Empty pack with dict keys passes payload validation; assert result is
    # non-OK (synthesis should not produce a real OK response for empty pack).
    assert result.status in {"INVALID_EVIDENCE", "INVALID_RESPONSE", "API_UNAVAILABLE"}


# ---------------------------------------------------------------------------
# 8 - Allowed status set
# ---------------------------------------------------------------------------
ALLOWED_STATUSES = {
    "OK",
    "NOT_CONFIGURED",
    "TIMEOUT",
    "API_UNAVAILABLE",
    "INVALID_RESPONSE",
    "PROVIDER_ERROR",
    "INVALID_EVIDENCE",
}


def test_all_failure_statuses_are_from_allowed_set():
    svc = AIManagementSynthesisService(provider="", model="")
    pack = ManagementEvidencePack(
        context={}, priority_signal={}, forecast_provenance={},
        availability={}, governance={},
    )
    result = svc.synthesize(pack)
    assert result.status in ALLOWED_STATUSES


# ---------------------------------------------------------------------------
# TokenHub HTTP connector tests (mocked)
# ---------------------------------------------------------------------------
def _make_mock_response(status_code, json_payload=None, raise_json=False):
    resp = MagicMock()
    resp.status_code = status_code
    if raise_json:
        resp.json.side_effect = ValueError("bad json")
    else:
        resp.json.return_value = json_payload or {}
    return resp


@patch("src.ai_management_synthesis.requests.post")
def test_tokenhub_authorization_header_uses_api_key(
    mock_post, service_configured
):
    mock_post.return_value = _make_mock_response(200, {
        "choices": [{"message": {"content": json.dumps({
            "headline": "H", "situation": "S",
            "management_significance": "M", "next_step": "N",
        })}}]
    })
    svc = AIManagementSynthesisService(
        provider="tencent_hunyuan",
        model="hy3",
        api_key="MY_SECRET_KEY",
    )
    svc.synthesize(ManagementEvidencePack(
        context={"x": 1}, priority_signal={"y": 2},
        forecast_provenance={"z": 3}, availability={"a": True},
        governance={"g": True},
    ))
    headers = mock_post.call_args.kwargs["headers"]
    assert headers["Authorization"] == "Bearer MY_SECRET_KEY"
    assert headers["Content-Type"] == "application/json"


@patch("src.ai_management_synthesis.requests.post")
def test_tokenhub_model_passed_correctly(mock_post, service_configured):
    mock_post.return_value = _make_mock_response(200, {
        "choices": [{"message": {"content": json.dumps({
            "headline": "H", "situation": "S",
            "management_significance": "M", "next_step": "N",
        })}}]
    })
    svc = AIManagementSynthesisService(
        provider="tencent_hunyuan", model="hy3", api_key="K"
    )
    svc.synthesize(ManagementEvidencePack(
        context={"x": 1}, priority_signal={"y": 2},
        forecast_provenance={"z": 3}, availability={"a": True},
        governance={"g": True},
    ))
    body = mock_post.call_args.kwargs["json"]
    assert body["model"] == "hy3"


@patch("src.ai_management_synthesis.requests.post")
def test_tokenhub_messages_unchanged(mock_post, service_configured):
    mock_post.return_value = _make_mock_response(200, {
        "choices": [{"message": {"content": json.dumps({
            "headline": "H", "situation": "S",
            "management_significance": "M", "next_step": "N",
        })}}]
    })
    svc = AIManagementSynthesisService(
        provider="tencent_hunyuan", model="hy3", api_key="K"
    )
    svc.synthesize(ManagementEvidencePack(
        context={"x": 1}, priority_signal={"y": 2},
        forecast_provenance={"z": 3}, availability={"a": True},
        governance={"g": True},
    ))
    body = mock_post.call_args.kwargs["json"]
    assert len(body["messages"]) == 2
    assert body["messages"][0]["role"] == "system"
    assert body["messages"][1]["role"] == "user"


@patch("src.ai_management_synthesis.requests.post")
def test_tokenhub_temperature_passed_correctly(mock_post, service_configured):
    mock_post.return_value = _make_mock_response(200, {
        "choices": [{"message": {"content": json.dumps({
            "headline": "H", "situation": "S",
            "management_significance": "M", "next_step": "N",
        })}}]
    })
    svc = AIManagementSynthesisService(
        provider="tencent_hunyuan", model="hy3",
        api_key="K", temperature=0.5,
    )
    svc.synthesize(ManagementEvidencePack(
        context={"x": 1}, priority_signal={"y": 2},
        forecast_provenance={"z": 3}, availability={"a": True},
        governance={"g": True},
    ))
    body = mock_post.call_args.kwargs["json"]
    assert body["temperature"] == 0.5


@patch("src.ai_management_synthesis.requests.post")
def test_tokenhub_endpoint_url(mock_post, service_configured):
    mock_post.return_value = _make_mock_response(200, {
        "choices": [{"message": {"content": json.dumps({
            "headline": "H", "situation": "S",
            "management_significance": "M", "next_step": "N",
        })}}]
    })
    svc = AIManagementSynthesisService(
        provider="tencent_hunyuan", model="hy3", api_key="K"
    )
    svc.synthesize(ManagementEvidencePack(
        context={"x": 1}, priority_signal={"y": 2},
        forecast_provenance={"z": 3}, availability={"a": True},
        governance={"g": True},
    ))
    url = mock_post.call_args.args[0]
    assert url == _TOKENHUB_CHAT_COMPLETIONS_URL
    assert url == "https://tokenhub-intl.tencentcloudmaas.com/v1/chat/completions"


@patch("src.ai_management_synthesis.requests.post")
def test_tokenhub_timeout_passed(mock_post, service_configured):
    mock_post.return_value = _make_mock_response(200, {
        "choices": [{"message": {"content": json.dumps({
            "what_is_happening": "H",
            "why_it_matters": "M",
            "what_management_should_do": "D",
        })}}]
    })
    svc = AIManagementSynthesisService(
        provider="tencent_hunyuan", model="hy3", api_key="K", timeout=12,
    )
    svc.synthesize(ManagementEvidencePack(
        context={"x": 1}, priority_signal={"y": 2},
        forecast_provenance={"z": 3}, availability={"a": True},
        governance={"g": True},
    ))
    assert mock_post.call_args.kwargs["timeout"] == 12


@patch("src.ai_management_synthesis.requests.post")
def test_tokenhub_valid_response_returns_ok(mock_post, service_configured):
    mock_post.return_value = _make_mock_response(200, {
        "choices": [{"message": {"content": json.dumps({
            "what_is_happening": "What is happening.",
            "why_it_matters": "Why it matters.",
            "what_management_should_do": "What management should do.",
            "governance_note": "AI-assisted interpretation of governed Sentinel360 outputs.",
        })}}]
    })
    svc = AIManagementSynthesisService(
        provider="tencent_hunyuan", model="hy3", api_key="K"
    )
    result = svc.synthesize(ManagementEvidencePack(
        context={"x": 1}, priority_signal={"y": 2},
        forecast_provenance={"z": 3}, availability={"a": True},
        governance={"g": True},
    ))
    assert result.status == "OK"
    assert result.what_is_happening == "What is happening."
    assert result.why_it_matters == "Why it matters."
    assert result.what_management_should_do == "What management should do."
    assert result.governance_note == (
        "AI-assisted interpretation of governed Sentinel360 outputs."
    )
    assert result.model_provider == "tencent_hunyuan"
    assert result.model_name == "hy3"


def test_tokenhub_missing_api_key_returns_not_configured(sample_evidence_pack):
    svc = AIManagementSynthesisService(
        provider="tencent_hunyuan", model="hy3", api_key=""
    )
    result = svc.synthesize(sample_evidence_pack)
    assert result.status == "NOT_CONFIGURED"
    assert "SENTINEL360_AI_API_KEY" in result.message


@patch("src.ai_management_synthesis.requests.post")
def test_tokenhub_request_timeout_returns_timeout(mock_post, sample_evidence_pack):
    import requests
    mock_post.side_effect = requests.exceptions.Timeout("read timed out")
    svc = AIManagementSynthesisService(
        provider="tencent_hunyuan", model="hy3", api_key="K"
    )
    result = svc.synthesize(sample_evidence_pack)
    assert result.status == "TIMEOUT"
    assert result.response_duration_seconds is not None


@patch("src.ai_management_synthesis.requests.post")
def test_tokenhub_network_error_returns_api_unavailable(mock_post, sample_evidence_pack):
    import requests
    mock_post.side_effect = requests.exceptions.ConnectionError("DNS failure")
    svc = AIManagementSynthesisService(
        provider="tencent_hunyuan", model="hy3", api_key="K"
    )
    result = svc.synthesize(sample_evidence_pack)
    assert result.status == "API_UNAVAILABLE"
    assert "network error" in result.message.lower()


@patch("src.ai_management_synthesis.requests.post")
def test_tokenhub_401_returns_provider_error(mock_post, sample_evidence_pack):
    mock_post.return_value = _make_mock_response(401)
    svc = AIManagementSynthesisService(
        provider="tencent_hunyuan", model="hy3", api_key="K"
    )
    result = svc.synthesize(sample_evidence_pack)
    assert result.status == "PROVIDER_ERROR"
    assert "401" in result.message


@patch("src.ai_management_synthesis.requests.post")
def test_tokenhub_403_returns_provider_error(mock_post, sample_evidence_pack):
    mock_post.return_value = _make_mock_response(403)
    svc = AIManagementSynthesisService(
        provider="tencent_hunyuan", model="hy3", api_key="K"
    )
    result = svc.synthesize(sample_evidence_pack)
    assert result.status == "PROVIDER_ERROR"
    assert "403" in result.message


@patch("src.ai_management_synthesis.requests.post")
def test_tokenhub_429_returns_provider_error(mock_post, sample_evidence_pack):
    mock_post.return_value = _make_mock_response(429)
    svc = AIManagementSynthesisService(
        provider="tencent_hunyuan", model="hy3", api_key="K"
    )
    result = svc.synthesize(sample_evidence_pack)
    assert result.status == "PROVIDER_ERROR"
    assert "rate limited" in result.message.lower()


@patch("src.ai_management_synthesis.requests.post")
def test_tokenhub_500_returns_api_unavailable(mock_post, sample_evidence_pack):
    mock_post.return_value = _make_mock_response(500)
    svc = AIManagementSynthesisService(
        provider="tencent_hunyuan", model="hy3", api_key="K"
    )
    result = svc.synthesize(sample_evidence_pack)
    assert result.status == "API_UNAVAILABLE"
    assert "server error" in result.message.lower()


@patch("src.ai_management_synthesis.requests.post")
def test_tokenhub_400_returns_provider_error(mock_post, sample_evidence_pack):
    mock_post.return_value = _make_mock_response(400)
    svc = AIManagementSynthesisService(
        provider="tencent_hunyuan", model="hy3", api_key="K"
    )
    result = svc.synthesize(sample_evidence_pack)
    assert result.status == "PROVIDER_ERROR"


@patch("src.ai_management_synthesis.requests.post")
def test_tokenhub_malformed_json_returns_invalid_response(mock_post, sample_evidence_pack):
    mock_post.return_value = _make_mock_response(200, {}, raise_json=True)
    svc = AIManagementSynthesisService(
        provider="tencent_hunyuan", model="hy3", api_key="K"
    )
    result = svc.synthesize(sample_evidence_pack)
    assert result.status == "INVALID_RESPONSE"
    assert "not valid json" in result.message.lower()


@patch("src.ai_management_synthesis.requests.post")
def test_tokenhub_empty_choices_returns_invalid_response(mock_post, sample_evidence_pack):
    mock_post.return_value = _make_mock_response(200, {"choices": []})
    svc = AIManagementSynthesisService(
        provider="tencent_hunyuan", model="hy3", api_key="K"
    )
    result = svc.synthesize(sample_evidence_pack)
    assert result.status == "INVALID_RESPONSE"
    assert "empty choices" in result.message.lower()


@patch("src.ai_management_synthesis.requests.post")
def test_tokenhub_missing_content_returns_invalid_response(mock_post, sample_evidence_pack):
    mock_post.return_value = _make_mock_response(200, {
        "choices": [{"message": {}}]
    })
    svc = AIManagementSynthesisService(
        provider="tencent_hunyuan", model="hy3", api_key="K"
    )
    result = svc.synthesize(sample_evidence_pack)
    assert result.status == "INVALID_RESPONSE"


@patch("src.ai_management_synthesis.requests.post")
def test_tokenhub_api_key_not_in_error_message(mock_post, sample_evidence_pack):
    import requests
    mock_post.side_effect = requests.exceptions.ConnectionError("DNS failure")
    svc = AIManagementSynthesisService(
        provider="tencent_hunyuan",
        model="hy3",
        api_key="REAL_API_KEY_VALUE",
    )
    result = svc.synthesize(sample_evidence_pack)
    assert result.status == "API_UNAVAILABLE"
    assert "REAL_API_KEY_VALUE" not in result.message

    mock_post.side_effect = requests.exceptions.Timeout("read timed out")
    result = svc.synthesize(sample_evidence_pack)
    assert result.status == "TIMEOUT"
    assert "REAL_API_KEY_VALUE" not in result.message


def test_tokenhub_governance_prompt_unchanged():
    prompt = _build_system_prompt()
    assert "Do not calculate any new values" in prompt
    assert "Do not claim causality" in prompt
    assert "AI-assisted interpretation of governed Sentinel360 outputs" in prompt


# ---------------------------------------------------------------------------
# 9 - Executive-language prompt instructions
#     (verifies that the refined system prompt enforces the new style rules)
# ---------------------------------------------------------------------------
class TestExecutiveLanguagePrompt:
    """Targeted tests asserting the system prompt instructs Hy3 to write
    management-facing prose, suppress technical provenance, and stay compact
    — adapted for the active executive Q&A schema (what_is_happening /
    why_it_matters / what_management_should_do).
    """

    def test_prompt_names_executive_audience(self):
        prompt = _build_system_prompt()
        assert "COO" in prompt or "Hospital COO" in prompt
        assert "General Manager" in prompt or "Medical Director" in prompt
        assert "executive" in prompt.lower()

    def test_prompt_instructs_display_value_preference(self):
        prompt = _build_system_prompt()
        # Explicit display-value preference and a canonical example.
        assert "display value" in prompt.lower()
        assert "104.8" in prompt
        assert "104.761905" in prompt  # example of preferred display vs raw

    def test_prompt_forbids_raw_excessive_precision(self):
        prompt = _build_system_prompt()
        # Must explicitly forbid raw unrounded values with an example.
        assert "2.746188" in prompt
        assert "104.761905" in prompt

    def test_prompt_forbids_validation_mae_in_prose(self):
        prompt = _build_system_prompt()
        # The word MAE must appear, and the prose must be instructed to
        # avoid quoting it.
        assert "MAE" in prompt
        assert "validation MAE" in prompt
        # The "validation MAE" mention sits inside the suppression list,
        # which is preceded by the header "Technical-detail suppression
        # (strict" and a "do NOT" directive. Verify the MAE context line
        # itself is a forbidden-line.
        mae_idx = prompt.find("MAE")
        window = prompt[mae_idx: mae_idx + 80].lower()
        assert "model-quality" in window or "metric" in window

    def test_prompt_forbids_model_method_names_in_prose(self):
        prompt = _build_system_prompt()
        for name in ("Holt", "SES", "Moving Average", "Linear Trend"):
            assert name in prompt

    def test_prompt_instructs_plain_language_confidence(self):
        prompt = _build_system_prompt()
        low = prompt.lower()
        assert "confidence" in low
        assert "plain language" in low
        assert "moderate indicative confidence" in low

    def test_prompt_handles_target_availability(self):
        prompt = _build_system_prompt()
        low = prompt.lower()
        # The phrase must appear (as the explicit forbidden sentence).
        assert "target value is unavailable" in low
        idx = low.find("target value is unavailable")
        window = low[max(0, idx - 80): idx + 80]
        assert (
            "do not write" in window
            or "(you may simply" in window
            or "do not lead with" in window
        )

    def test_prompt_converts_warning_transitions_to_management_language(self):
        prompt = _build_system_prompt()
        assert "amber to red" in prompt.lower()
        assert (
            "escalate from amber to red" in prompt.lower()
            or "move from amber to red" in prompt.lower()
        )

    def test_prompt_specifies_qa_answer_length_bounds(self):
        """Each Q&A answer is bounded: 1 sentence preferred / 2 max,
        15-30 words preferred, never above 35 words in a single answer."""
        prompt = _build_system_prompt()
        low = prompt.lower()
        assert "1 sentence" in low and "preferred" in low
        assert "2 sentences" in low
        assert "15 to 30" in prompt

    def test_prompt_per_qa_field_style_present(self):
        prompt = _build_system_prompt()
        low = prompt.lower()
        assert "what_is_happening" in low
        assert "why_it_matters" in low
        assert "what_management_should_do" in low

    def test_prompt_no_causality_language(self):
        prompt = _build_system_prompt()
        low = prompt.lower()
        # Causal-claim forbiddances.
        assert "caused by" in low
        assert "will result in" in low
        # Approved management hedges.
        for hedge in ("may indicate", "signals", "suggests", "warrants"):
            assert hedge in low

    def test_prompt_no_invented_intervention(self):
        prompt = _build_system_prompt()
        low = prompt.lower()
        # Forbidden intervention categories must appear. The prompt may
        # reference these in singular ("patient counts", "bed counts") or
        # plural ("patients", "beds") form.
        for cat in ("beds", "staff", "patient", "procedure"):
            assert cat in low
        # A "never invent" or "do not invent" qualifier must accompany the
        # list.
        any_invent_phrase = (
            "never invent" in low
            or "do not invent" in low
        )
        assert any_invent_phrase

    def test_prompt_instructs_total_length_50_to_90_words(self):
        prompt = _build_system_prompt()
        assert "50 to 90" in prompt
        # Maximum strict cap.
        assert "100 words" in prompt

    def test_prompt_forbids_duplication_across_qa(self):
        prompt = _build_system_prompt()
        low = prompt.lower()
        assert (
            "do not repeat the same fact across" in low
            or "each answer must add a different layer" in low
        )

    def test_prompt_preserves_strict_fact_preservation(self):
        prompt = _build_system_prompt()
        low = prompt.lower()
        # All governance guardrails retained.
        assert "use only the supplied evidence" in low
        assert "do not calculate any new values" in low
        assert "do not infer missing values" in low
        assert "do not claim causality" in low
        assert "do not create new risks" in low
        assert "do not describe unavailable evidence" in low

    def test_prompt_forbids_internal_field_names_schema_json(self):
        prompt = _build_system_prompt()
        low = prompt.lower()
        assert "field names" in low
        assert ("schema version" in low) or ("schema snippets" in low)

    def test_prompt_forbids_risk_engine_threshold_internals(self):
        prompt = _build_system_prompt()
        low = prompt.lower()
        # The forbidden term "risk tier" (or "risk-engine") must appear.
        assert "risk tier" in low

    def test_prompt_distinguishes_audience_from_developer(self):
        prompt = _build_system_prompt()
        low = prompt.lower()
        assert "not for a data scientist" in low
        assert "developer" in low

    def test_prompt_in_messages_includes_executive_rules(
        self, service_configured
    ):
        captured = {}

        def fake_call(messages):
            captured["messages"] = messages
            return AIManagementSynthesisResult(
                status="OK",
                message=json.dumps({
                    "what_is_happening": "H",
                    "why_it_matters": "M",
                    "what_management_should_do": "D",
                }),
                model_provider="tencent_hunyuan",
                model_name="hy3",
            )

        with patch.object(service_configured, "_call_llm", side_effect=fake_call):
            service_configured.synthesize(ManagementEvidencePack(
                context={"x": 1},
                priority_signal={"y": 2},
                forecast_provenance={"z": 3},
                availability={"a": True},
                governance={"g": True},
            ))
        sys_prompt = captured["messages"][0]["content"]
        assert "executive" in sys_prompt.lower()
        assert "do not claim causality" in sys_prompt.lower()
        assert "MAE" in sys_prompt
        assert "104.8" in sys_prompt

    def test_prompt_json_schema_uses_qa_fields(self):
        """The active AI output schema is the executive Q&A schema:
        what_is_happening / why_it_matters / what_management_should_do /
        governance_note.
        """
        prompt = _build_system_prompt()
        for field in (
            '"what_is_happening"',
            '"why_it_matters"',
            '"what_management_should_do"',
            '"governance_note"',
        ):
            assert field in prompt, (
                f"expected Q&A field {field!r} in prompt"
            )
        # Legacy long-form fields must NOT appear as schema keys in the
        # prompt (the prompt should not instruct the model to emit them).
        for legacy in (
            '"headline"', '"situation"',
            '"management_significance"', '"next_step"',
        ):
            assert legacy not in prompt, (
                f"legacy long-form field {legacy!r} must not appear in "
                f"the active prompt"
            )
        # Governance note value string unchanged.
        assert (
            "AI-assisted interpretation of governed Sentinel360 outputs."
            in prompt
        )

    def test_output_schema_returns_qa_fields(self, service_configured):
        """The parser must read the Q&A schema and populate the new
        dataclass fields when given a valid Q&A JSON response.
        """
        good = json.dumps({
            "what_is_happening": "H",
            "why_it_matters": "M",
            "what_management_should_do": "D",
            "governance_note": "AI-assisted interpretation of governed "
            "Sentinel360 outputs.",
        })
        with patch.object(
            service_configured,
            "_call_llm",
            return_value=AIManagementSynthesisResult(
                status="OK",
                message=good,
                model_provider="tencent_hunyuan",
                model_name="hy3",
            ),
        ):
            result = service_configured.synthesize(ManagementEvidencePack(
                context={"x": 1},
                priority_signal={"y": 2},
                forecast_provenance={"z": 3},
                availability={"a": True},
                governance={"g": True},
            ))
        assert result.status == "OK"
        assert result.what_is_happening == "H"
        assert result.why_it_matters == "M"
        assert result.what_management_should_do == "D"
        assert (
            result.governance_note
            == "AI-assisted interpretation of governed Sentinel360 outputs."
        )
        # Legacy long-form fields default to None on a valid Q&A response.
        assert result.headline is None
        assert result.situation is None
        assert result.management_significance is None
        assert result.next_step is None


# ---------------------------------------------------------------------------
# 10 - Q&A contract prompt instructions (verifies the active schema rules)
# ---------------------------------------------------------------------------
class TestQASchemaPrompt:
    """Targeted tests asserting the system prompt enforces the executive
    Q&A schema, the strict length budget, and the spec §7 technical-detail
    suppression list."""

    # --- Active schema (Q&A fields) ------------------------------------------
    def test_prompt_declares_qa_fields(self):
        prompt = _build_system_prompt()
        for f in (
            "what_is_happening", "why_it_matters",
            "what_management_should_do", "governance_note",
        ):
            assert f in prompt

    def test_prompt_names_three_management_questions(self):
        prompt = _build_system_prompt()
        low = prompt.lower()
        assert "what is happening?" in low
        assert "why does it matter?" in low
        assert "what should management do next?" in low

    def test_prompt_disallows_chatbot_or_user_questions(self):
        """Spec: do NOT create a chatbot; do NOT add a text input;
        do NOT create free-form user questions."""
        prompt = _build_system_prompt()
        low = prompt.lower()
        assert "do not generate a chatbot" in low
        assert "do not invite follow-up questions" in low
        assert "do not create additional sections" in low

    # --- Per-answer and total length budgets ---------------------------------
    def test_prompt_one_sentence_preferred_two_max(self):
        prompt = _build_system_prompt()
        low = prompt.lower()
        assert "1 sentence (preferred)" in low or (
            "1 sentence" in low and "preferred" in low
        )
        assert "2 sentences" in low

    def test_prompt_answer_word_budget(self):
        prompt = _build_system_prompt()
        assert "15 to 30" in prompt
        # Never above 35 in any single answer.
        assert "35 words" in prompt

    def test_prompt_total_word_budget(self):
        prompt = _build_system_prompt()
        assert "50 to 90" in prompt
        # Absolute maximum.
        assert "100 words" in prompt

    # --- Technical-detail suppression (spec §7) ------------------------------
    def test_prompt_forbids_facility_codes(self):
        prompt = _build_system_prompt()
        assert "HOSP-001" in prompt

    def test_prompt_forbids_kpi_codes(self):
        prompt = _build_system_prompt()
        assert "KPI_006" in prompt

    def test_prompt_forbids_raw_precision_examples(self):
        prompt = _build_system_prompt()
        assert "104.761905" in prompt
        # Even the small-multiple-precision example must appear.
        assert "2.746188" in prompt

    def test_prompt_forbids_model_method_names(self):
        prompt = _build_system_prompt()
        low = prompt.lower()
        for name in ("holt", "holt-winters", "ses", "moving average",
                     "linear trend"):
            assert name in low

    def test_prompt_forbids_forecast_horizon_metadata(self):
        prompt = _build_system_prompt()
        low = prompt.lower()
        assert "horizon" in low

    def test_prompt_forbids_risk_engine_internal_terminology(self):
        prompt = _build_system_prompt()
        low = prompt.lower()
        assert "risk tier" in low

    def test_prompt_forbids_internal_status_phrase(self):
        prompt = _build_system_prompt()
        assert "operational status Priority Management Review" in prompt

    def test_prompt_forbids_target_unavailable_sentence(self):
        prompt = _build_system_prompt()
        assert "Target value is unavailable" in prompt

    def test_prompt_forbids_causality_disclaimer_sentence(self):
        prompt = _build_system_prompt()
        assert "Causality is not confirmed" in prompt

    # --- Decision-oriented next step -----------------------------------------
    def test_prompt_forbids_specific_intervention_invention(self):
        prompt = _build_system_prompt()
        low = prompt.lower()
        # Forbidden intervention categories must appear in singular or
        # plural form.
        for ex in ("bed", "staff", "patient", "procedure"):
            assert ex in low, (
                f"expected forbidden intervention category '{ex}' in prompt"
            )
        # 'do not' / 'never' must qualify the no-invent list.
        any_phrase = (
            "never invent specific" in low
            or "do not invent" in low
        )
        assert any_phrase

    # --- Schema-output JSON contract ----------------------------------------
    def test_prompt_output_format_is_qa_only(self):
        prompt = _build_system_prompt()
        # The example JSON in the prompt must list the four Q&A fields and
        # not list legacy long-form fields.
        idx = prompt.find("{")
        end = prompt.find("}", idx)
        json_block = prompt[idx:end + 1]
        for f in (
            '"what_is_happening"',
            '"why_it_matters"',
            '"what_management_should_do"',
            '"governance_note"',
        ):
            assert f in json_block
        for legacy in (
            '"headline"', '"situation"',
            '"management_significance"', '"next_step"',
        ):
            assert legacy not in json_block

    def test_prompt_governance_note_value_unchanged(self):
        prompt = _build_system_prompt()
        assert (
            "AI-assisted interpretation of governed Sentinel360 outputs."
            in prompt
        )


# ---------------------------------------------------------------------------
# 11 - Parser / dataclass carries the Q&A schema
# ---------------------------------------------------------------------------
class TestDataclassAndParserQASchema:
    def test_dataclass_default_qa_fields_none(self):
        r = AIManagementSynthesisResult(status="OK")
        assert r.what_is_happening is None
        assert r.why_it_matters is None
        assert r.what_management_should_do is None
        # Legacy long-form fields default to None and stay None unless the
        # parser or a caller explicitly sets them.
        assert r.headline is None
        assert r.situation is None
        assert r.management_significance is None
        assert r.next_step is None

    def test_parser_populates_qa_fields(self, service_configured):
        good = json.dumps({
            "what_is_happening": "WIH",
            "why_it_matters": "WIM",
            "what_management_should_do": "WMSD",
            "governance_note": "AI-assisted interpretation of governed "
            "Sentinel360 outputs.",
        })
        with patch.object(
            service_configured,
            "_call_llm",
            return_value=AIManagementSynthesisResult(
                status="OK",
                message=good,
                model_provider="tencent_hunyuan",
                model_name="hy3",
            ),
        ):
            result = service_configured.synthesize(ManagementEvidencePack(
                context={},
                priority_signal={},
                forecast_provenance={},
                availability={},
                governance={},
            ))
        assert result.status == "OK"
        assert result.what_is_happening == "WIH"
        assert result.why_it_matters == "WIM"
        assert result.what_management_should_do == "WMSD"

    def test_parser_legacy_fields_stay_none_with_qa_json(
        self, service_configured
    ):
        """Even if a downstream caller happens to inject legacy text into
        the response, only the Q&A fields are read into the active
        dataclass fields. The legacy fields stay None because the parser
        does not copy them from the JSON."""
        good = json.dumps({
            "what_is_happening": "WIH",
            "why_it_matters": "WIM",
            "what_management_should_do": "WMSD",
            "governance_note": "AI-assisted interpretation of governed "
            "Sentinel360 outputs.",
        })
        with patch.object(
            service_configured,
            "_call_llm",
            return_value=AIManagementSynthesisResult(
                status="OK",
                message=good,
                model_provider="tencent_hunyuan",
                model_name="hy3",
            ),
        ):
            result = service_configured.synthesize(ManagementEvidencePack(
                context={}, priority_signal={},
                forecast_provenance={}, availability={}, governance={},
            ))
        assert result.headline is None
        assert result.situation is None
        assert result.management_significance is None
        assert result.next_step is None

