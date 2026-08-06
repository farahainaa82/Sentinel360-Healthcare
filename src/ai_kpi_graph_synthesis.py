"""
Hy3 KPI graph interpretation synthesis service.

Produces concise management interpretation of governed KPI forecast
evidence. Does NOT calculate, modify, or invent values.

The live TokenHub / Hy3 HTTP transport is shared with the connected-signal
synthesis service via :mod:`src._ai_tokenhub_transport`. The single
authoritative entry point is :func:`call_tokenhub_chat_completion`;
both services use it the same way so the wire format, error mapping,
and response normalisation are guaranteed identical.

KPI-AI v2: the v1 implementation imported a non-existent
``AITokenHubTransport`` class (and a non-existent ``AIResponse`` class)
from the transport module. The silent ``ImportError`` fallback left
``self.transport = None`` and the gate returned ``NOT_CONFIGURED`` for
every call -- so the live Hy3 path was never reached. v2 uses
``call_tokenhub_chat_completion`` directly, matching the working
connected-signal service.

Result schema (always returned, even on fallback):

    {
        "what_is_changing": str,
        "why_it_matters": str,
        "governance_note": str,
        "status": str  # "OK" on live Hy3 success,
                       # NOT_CONFIGURED / TIMEOUT / API_UNAVAILABLE /
                       # PROVIDER_ERROR / INVALID_RESPONSE on fallback
    }
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from .runtime_secrets import get_runtime_secret
from src._ai_tokenhub_transport import call_tokenhub_chat_completion


_DEFAULT_PROVIDER = "tencent_hunyuan"
_DEFAULT_MODEL = "hy3"
_DEFAULT_TIMEOUT = 45.0
_DEFAULT_TEMPERATURE = 0.2
_DEFAULT_MAX_TOKENS = 200
_DEFAULT_TOKENHUB_URL = (
    "https://tokenhub-intl.tencentcloudmaas.com/v1/chat/completions"
)

# Cache schema version. Bump this whenever the evidence shape, prompt
# contract, or transport contract changes, so previously cached
# non-OK results cannot mask a now-live Hy3 path.
_AI_SCHEMA_VERSION = "kpi_graph_ai_v2"


class AIKPIGraphSynthesisService:
    """Synthesize concise management interpretation for a single KPI graph."""

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = _DEFAULT_TIMEOUT,
        temperature: float = _DEFAULT_TEMPERATURE,
        max_tokens: int = _DEFAULT_MAX_TOKENS,
        tokenhub_url: str = _DEFAULT_TOKENHUB_URL,
        call_fn: Any = None,
        # Backward-compat shim: old v1 tests passed ``transport``
        # (a MagicMock exposing ``.chat_completion(...)`` returning
        # a response with ``.status`` and ``.content``). We keep
        # that test seam working so the new live-Hy3 path does not
        # invalidate the existing targeted tests. Production code
        # only uses ``call_fn`` (which is None and resolves to the
        # shared ``call_tokenhub_chat_completion``).
        transport: Any = None,
    ):
        # Provider / model / api_key are resolved via the shared
        # runtime-secret helper (st.secrets -> os.getenv -> default).
        # ``call_fn`` is an optional test seam: pass in a mock to
        # substitute for ``call_tokenhub_chat_completion`` without
        # patching the transport module.
        self.provider = (
            provider
            if provider is not None
            else get_runtime_secret(
                "SENTINEL360_AI_PROVIDER", default=_DEFAULT_PROVIDER
            )
        )
        self.model = (
            model
            if model is not None
            else get_runtime_secret(
                "SENTINEL360_AI_MODEL", default=_DEFAULT_MODEL
            )
        )
        self.api_key = (
            api_key
            if api_key is not None
            else get_runtime_secret("SENTINEL360_AI_API_KEY")
        )
        self.timeout = float(timeout)
        self.temperature = float(temperature)
        self.max_tokens = int(max_tokens)
        self.tokenhub_url = tokenhub_url
        # Resolve the live-call function:
        #   * Production: ``call_tokenhub_chat_completion`` (shared
        #     with the connected-signal service).
        #   * New test seam: ``call_fn=fn``.
        #   * Legacy test seam: ``transport=mock`` -- adapt the old
        #     class-based mock interface to the new function-based
        #     interface so the existing targeted tests keep working.
        if call_fn is not None:
            self._call_fn = call_fn
        elif transport is not None:
            self._call_fn = self._adapt_transport_mock(transport)
        else:
            self._call_fn = call_tokenhub_chat_completion

    @staticmethod
    def _adapt_transport_mock(transport: Any) -> Any:
        """Adapt the v1 class-based transport mock to the v2
        function-based interface. ``transport.chat_completion(...)``
        is treated as the live call and the response object is
        normalised to ``{"status": ..., "message": ...}``.
        """
        def _call(**kwargs):
            response = transport.chat_completion(**kwargs)
            if isinstance(response, dict):
                return response
            return {
                "status": getattr(response, "status", ""),
                "message": getattr(response, "content", ""),
            }
        return _call

    # -------------------------------------------------------------------
    # Public entry point
    # -------------------------------------------------------------------

    def synthesize(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Return a dict with ``what_is_changing``, ``why_it_matters``,
        ``governance_note``, and ``status``."""
        # If the API key is missing the live path is unreachable, so
        # we fall back deterministically rather than failing the render.
        if not self.api_key:
            return self._deterministic_fallback(evidence, status="NOT_CONFIGURED")

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(evidence)

        try:
            response = self._call_fn(
                provider=self.provider,
                model=self.model,
                api_key=self.api_key,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout,
                tokenhub_url=self.tokenhub_url,
            )
        except Exception:  # pragma: no cover - defensive
            return self._deterministic_fallback(evidence, status="PROVIDER_ERROR")

        # Normalise the response shape. The transport function
        # returns a dict with ``status`` and ``message`` (or ``raw``).
        response_status = (
            (response.get("status") or "").upper()
            if isinstance(response, dict)
            else ""
        )
        if response_status == "OK":
            content = response.get("message") or ""
            return self._parse_response(content, evidence)
        # Pass through known failure statuses. Unknown statuses become
        # PROVIDER_ERROR to keep the contract stable.
        fallback_status = (
            response_status
            if response_status in {
                "TIMEOUT", "API_UNAVAILABLE", "INVALID_RESPONSE", "PROVIDER_ERROR",
            }
            else "PROVIDER_ERROR"
        )
        return self._deterministic_fallback(evidence, status=fallback_status)

    # -------------------------------------------------------------------
    # Prompt construction
    # -------------------------------------------------------------------

    @staticmethod
    def _build_system_prompt() -> str:
        return (
            "You are a concise healthcare operations analyst. "
            "You interpret governed KPI forecast evidence and return a brief "
            "management reading in plain English.\n\n"
            "STRICT RULES:\n"
            "1. Do NOT calculate, derive, or invent any values. The evidence "
            "already contains every number you need. If a value is missing, "
            "say so explicitly.\n"
            "2. You must NEVER claim causality. Use neutral language such as "
            "'is associated with' or 'coincides with' rather than 'causes'.\n"
            "3. You must NEVER give clinical advice or speak about individual "
            "patients.\n"
            "4. You may only describe a single KPI. You must NEVER describe, "
            "compare, or infer relationships between multiple KPIs.\n\n"
            "RESPONSE FORMAT:\n"
            "Return ONLY a JSON object with exactly three string keys: "
            "'what_is_changing', 'why_it_matters', 'governance_note'. "
            "'what_is_changing' is 15-25 words describing the forecast change. "
            "'why_it_matters' is 15-25 words explaining why this matters for "
            "operational management. "
            "'governance_note' is a short statement reminding the reader that "
            "this interpretation is generated from governed forecast evidence "
            "and does not introduce new measurements or causality claims. "
            "Return ONLY the JSON object -- no commentary, no markdown fences."
        )

    # Backward-compat alias used by targeted tests.
    def _system_prompt(self) -> str:
        return self._build_system_prompt()

    @staticmethod
    def _build_user_prompt(evidence: Dict[str, Any]) -> str:
        # We pass only governed evidence fields the model is allowed
        # to read; no secrets, no API keys, no internal identifiers.
        return (
            "Given the following governed KPI forecast evidence, produce the "
            "JSON interpretation as instructed.\n\n"
            f"EVIDENCE:\n{json.dumps(evidence, sort_keys=True, default=str)}"
        )

    # Backward-compat helper used by targeted tests: combine the
    # system prompt and the user prompt into a single string. We
    # intentionally do NOT prepend a duplicate summary of the KPI
    # name or the forecast value here -- the evidence JSON already
    # contains those fields exactly once, and the targeted tests
    # assert that those values are not repeated excessively.
    def _build_prompt(self, evidence: Dict[str, Any]) -> str:
        return self._build_system_prompt() + "\n\n" + self._build_user_prompt(evidence)

    # -------------------------------------------------------------------
    # Response parsing
    # -------------------------------------------------------------------

    @staticmethod
    def _extract_json_block(text: str) -> str:
        """Find the first balanced JSON object in ``text``.

        Hy3 sometimes wraps its reply in a code fence or adds a brief
        preamble; we still want the JSON payload underneath. We do a
        brace-counting scan from the first ``{`` to the matching ``}``.
        """
        if not text:
            return ""
        start = text.find("{")
        if start < 0:
            return ""
        depth = 0
        in_string = False
        escape = False
        for i in range(start, len(text)):
            ch = text[i]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                continue
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
        return ""

    @classmethod
    def _parse_response(
        cls, content: str, evidence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse the assistant's content as JSON and return the standard
        schema. If the JSON is missing, malformed, or missing required
        keys, fall back deterministically with ``status=INVALID_RESPONSE``.
        """
        if not content or not content.strip():
            return cls._deterministic_fallback(evidence, status="INVALID_RESPONSE")
        json_text = cls._extract_json_block(content)
        if not json_text:
            return cls._deterministic_fallback(evidence, status="INVALID_RESPONSE")
        try:
            parsed = json.loads(json_text)
        except (ValueError, TypeError):
            return cls._deterministic_fallback(evidence, status="INVALID_RESPONSE")
        if not isinstance(parsed, dict):
            return cls._deterministic_fallback(evidence, status="INVALID_RESPONSE")
        what = str(parsed.get("what_is_changing", "")).strip()
        # Be tolerant of common LLM typos on the why-it-matters key.
        why = (
            str(parsed.get("why_it_matters", "")).strip()
            or str(parsed.get("why_it_matter", "")).strip()
        )
        note = str(parsed.get("governance_note", "")).strip()
        if not what or not why:
            return cls._deterministic_fallback(evidence, status="INVALID_RESPONSE")
        return {
            "what_is_changing": what,
            "why_it_matters": why,
            "governance_note": note or "Interpretation generated from governed forecast evidence.",
            "status": "OK",
        }

    # -------------------------------------------------------------------
    # Deterministic fallback
    # -------------------------------------------------------------------

    @staticmethod
    def _deterministic_fallback(
        evidence: Dict[str, Any], status: str = "NOT_CONFIGURED"
    ) -> Dict[str, Any]:
        """Build a deterministic, governed interpretation without calling
        any external service. Mirrors the visible behavior of the
        controller's local fallback so the UI never blanks out.
        """
        forecast = evidence.get("forecast", {}) if isinstance(evidence, dict) else {}
        change = (
            forecast.get("expected_status_change", "no change")
            if isinstance(forecast, dict)
            else "no change"
        )
        warning_level = (
            forecast.get("warning_level", "Monitoring")
            if isinstance(forecast, dict)
            else "Monitoring"
        )
        transition_text = (
            forecast.get("confidence_label", "Moderate Confidence")
            if isinstance(forecast, dict)
            else "Moderate Confidence"
        )
        forecast_month = (
            forecast.get("month", "the next period")
            if isinstance(forecast, dict)
            else "the next period"
        )
        what = (
            f"The {forecast_month} forecast indicates performance is "
            f"expected to move from {change}."
        )
        why = (
            f"Current {warning_level} is acknowledged; {transition_text} "
            "supports continued monitoring without immediate action."
        )
        note = (
            "Deterministic summary produced from governed evidence; "
            "live AI interpretation was not available for this period."
        )
        return {
            "what_is_changing": what,
            "why_it_matters": why,
            "governance_note": note,
            "status": status,
        }


# Public exports
SCHEMA_VERSION = _AI_SCHEMA_VERSION
