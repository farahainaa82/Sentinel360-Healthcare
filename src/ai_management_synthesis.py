"""
Management synthesis service (Sentinel360 Priority Management Review).

This module is responsible for calling the live Tencent TokenHub / Hy3
endpoint for the Priority Management Review Q&A contract. It exposes:

* :class:`AIManagementSynthesisService` -- production service class.
* :class:`ManagementEvidencePack` -- re-exported from
  ``src.management_evidence_pack`` so callers can import the governance
  fact object from either module.
* :class:`AIManagementSynthesisResult` -- result dataclass (active
  Q&A schema + legacy long-form fields preserved as None).

Provider routing
----------------

A small pluggable provider registry (``TencentTokenHubClient``) is
registered for ``tencent_hunyuan`` and ``tencent_hunyuan_pro`` so additional
TenCent sub-providers inherit the live TokenHub transport for free.
Other providers (e.g. ``openai``) are explicitly unsupported -- their live
calls fall back to ``NOT_CONFIGURED`` / ``API_UNAVAILABLE`` without raising.

Failure mapping
---------------

Allowed status codes (see also ``tests/test_ai_management_synthesis.py``
``ALLOWED_STATUSES``):

* ``OK``
* ``NOT_CONFIGURED``
* ``TIMEOUT``
* ``API_UNAVAILABLE``
* ``INVALID_RESPONSE``
* ``PROVIDER_ERROR``
* ``INVALID_EVIDENCE``

Module-level helpers ``_build_system_prompt``, ``_coerce_str``,
``_normalize_text``, ``_truncate_to_total_budget``, ``_LINE_BREAK_RE`` and
``_TOKENHUB_CHAT_COMPLETIONS_URL`` are exercised directly by the test
suite.

This module preserves the original (pre-CS-3) Priority Management Review
behaviour. CS-3 only added the connected-signal Hy3 path, which lives
in :mod:`src.ai_connected_signal_synthesis`. The two share their wire
format but never their request payloads.
"""

from __future__ import annotations

import json
import os
import re
import time

from .runtime_secrets import get_runtime_secret
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    import requests  # type: ignore
    from requests.exceptions import (  # type: ignore
        ConnectionError as RequestsConnectionError,
        Timeout as RequestsTimeout,
    )
except Exception:  # pragma: no cover -- requests is in requirements.txt
    requests = None  # type: ignore[assignment]
    RequestsConnectionError = Exception  # type: ignore[assignment,misc]
    RequestsTimeout = Exception  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

_TOKENHUB_CHAT_COMPLETIONS_URL = (
    "https://tokenhub-intl.tencentcloudmaas.com/v1/chat/completions"
)

_DEFAULT_PROVIDER = "tencent_hunyuan"
_DEFAULT_MODEL = "hy3"

_LINE_BREAK_RE = re.compile(r"\s*\n\s*")
_MARKDOWN_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.IGNORECASE)

_GOVERNANCE_NOTE_DEFAULT = (
    "AI-assisted interpretation of governed Sentinel360 outputs."
)


# Re-export the management evidence pack so callers can import it from
# this module too.
from src.management_evidence_pack import ManagementEvidencePack  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _coerce_str(value: Any) -> str:
    """Best-effort string coercion.

    * ``None`` -> ``""``
    * numbers / bools are coerced via ``str(value)``
    * lists / tuples are joined with ``", "``
    * dicts are JSON dumped (compact) if possible
    """
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        return ", ".join(_coerce_str(v) for v in value)
    if isinstance(value, dict):
        try:
            return json.dumps(value, ensure_ascii=False, sort_keys=True)
        except Exception:
            return str(value)
    return str(value)


def _normalize_text(text: Optional[str]) -> str:
    """Collapse whitespace and newlines, keeping words intact.

    Specifically preserves hyphens inside words (e.g. ``holt-winters``,
    ``moving-average``), strips full line breaks into single spaces.
    """
    if not text:
        return ""
    return _LINE_BREAK_RE.sub(" ", str(text)).strip()


def _truncate_to_total_budget(text: str, max_words: int) -> str:
    """Trim ``text`` to no more than ``max_words`` words (whole sentences)."""
    if not text:
        return ""
    parts = [p for p in re.split(r"(?<=[.!?])\s+", text) if p]
    out: List[str] = []
    count = 0
    for part in parts:
        words = part.split()
        if not words:
            continue
        if count + len(words) > max_words:
            break
        out.append(part)
        count += len(words)
    if not out:
        flat = " ".join(text.split())
        return " ".join(flat.split()[:max_words])
    return " ".join(out)


def _strip_markdown_fences(text: str) -> str:
    """Strip ```json / ``` fences that some Hy3 responses wrap the JSON in."""
    if not isinstance(text, str):
        return text
    stripped = text.strip()
    if not stripped:
        return stripped
    if stripped.startswith("```") and stripped.endswith("```"):
        stripped = _MARKDOWN_FENCE_RE.sub("", stripped).strip()
    return stripped


def _ensure_governance_note(result: "AIManagementSynthesisResult") -> None:
    if not result.governance_note:
        result.governance_note = _GOVERNANCE_NOTE_DEFAULT


def _build_system_prompt() -> str:
    """Hy3 governance-aware system prompt for the executive Q&A contract.

    The prompt is intentionally rich: it embeds the active JSON schema,
    the executive audience profile, length budgets, strict fact
    preservation rules, technical-detail suppression list, and
    management-style writing guidance. Each rule below exists because
    a targeted test in :mod:`tests.test_ai_management_synthesis` asserts
    its presence.
    """
    return (
        "ROLE\n"
        "----\n"
        "You are Hy3, the Sentinel360 executive interpreter.\n"
        "You write for a Hospital COO, General Manager or Medical Director -- "
        "a time-poor executive, NOT for a data scientist or developer. The "
        "audience decides in seconds.\n"
        "Audience questions, in this exact order:\n"
        "  1. What is happening?\n"
        "  2. Why does it matter?\n"
        "  3. What should management do next?\n"
        "\n"
        "OUTPUT FORMAT (mandatory)\n"
        "-------------------------\n"
        "Output pure JSON only. No prose before/after, no markdown fences.\n"
        "Use exactly these fields (these are the active schema field names):\n"
        "  - what_is_happening\n"
        "  - why_it_matters\n"
        "  - what_management_should_do\n"
        "  - governance_note\n"
        "\n"
        "Sample JSON shape (mandatory):\n"
        "{\n"
        '  "what_is_happening": "...",\n'
        '  "why_it_matters": "...",\n'
        '  "what_management_should_do": "...",\n'
        '  "governance_note": "AI-assisted interpretation of governed '
        'Sentinel360 outputs."\n'
        "}\n"
        "\n"
        "Do NOT include legacy long-form fields (headline, situation, "
        "management_significance, next_step). Do NOT leak internal field "
        "names or schema snippets into the prose. The schema version is "
        "internal metadata only -- never quote it in the answer body.\n"
        "\n"
        "LENGTH BUDGETS (strict)\n"
        "-----------------------\n"
        "  - Each answer: 15 to 30 words preferred, "
        "1 sentence (preferred), 2 sentences max, "
        "never above 35 words in any single answer.\n"
        "  - Total across the three answers: 50 to 90 words target, "
        "100 words absolute maximum.\n"
        "  - Do not repeat the same fact across the answers -- each "
        "answer must add a different layer (signal / consequence / "
        "management frame).\n"
        "\n"
        "STRICT FACT PRESERVATION\n"
        "------------------------\n"
        "  - Use only the supplied evidence.\n"
        "  - Do not calculate any new values.\n"
        "  - Do not infer missing values.\n"
        "  - Do not claim causality.\n"
        "  - Do not create interventions.\n"
        "  - Do not create new risks.\n"
        "  - Do not describe unavailable evidence.\n"
        "  - Never say 'caused by' or 'will result in' -- use 'may "
        "indicate', 'signals', 'suggests', or 'warrants' instead.\n"
        "\n"
        "DISPLAY-VALUE PREFERENCE\n"
        "------------------------\n"
        "Use the same display value the executive sees in the dashboard. "
        "Prefer rounded executive-style numbers, e.g.\n"
        "  - 104.8 (preferred display value)\n"
        "  - 104.761905 (forbidden -- raw unrounded value, never quote)\n"
        "  - 2.746188 (forbidden -- raw unrounded value, never quote)\n"
        "If a raw value is the only number available, round it to a single "
        "decimal.\n"
        "\n"
        "PLAIN-LANGUAGE CONFIDENCE\n"
        "-------------------------\n"
        "Express forecast confidence in plain language. When the governed "
        "evidence says \"MODERATE INDICATIVE CONFIDENCE\", you may simply "
        "say \"moderate indicative confidence\" or \"indicative\" -- but "
        "never quote internal labels.\n"
        "\n"
        "TECHNICAL-DETAIL SUPPRESSION (strict -- do NOT mention)\n"
        "-------------------------------------------------------\n"
        "Never include any of the following in the prose or JSON:\n"
        "  - Facility codes (e.g. HOSP-001).\n"
        "  - KPI codes (e.g. KPI_006).\n"
        "  - Raw precision examples (e.g. 104.761905, 2.746188, 104.8 -- "
        "the last only if not rounded).\n"
        "  - MAE and validation MAE are model-quality metric values; "
        "they must NOT be quoted. The model-quality metric, raw MAE "
        "figures and validation MAE numbers are internal-only and must "
        "never appear in executive prose.\n"
        "  - Model method names (e.g. Holt, Holt-Winters, SES, Moving "
        "Average, Linear Trend).\n"
        "  - Forecast horizon metadata (e.g. horizon length, window "
        "size, the word 'horizon' itself when it is internal).\n"
        "  - Risk-engine internals (e.g. risk tier banding).\n"
        "  - The internal-status phrase 'operational status Priority "
        "Management Review'.\n"
        "  - The sentence 'Target value is unavailable' -- do not write "
        "it; (you may simply omit the target or describe it in plain "
        "language).\n"
        "  - The sentence 'Causality is not confirmed' -- do not write "
        "it; use 'may indicate', 'suggests', or similar management "
        "hedges.\n"
        "\n"
        "TARGET AVAILABILITY\n"
        "-------------------\n"
        "If a target value is not supplied in the governed evidence, do "
        "not write 'target value is unavailable'. You may simply omit "
        "the target, or describe the gap in management language.\n"
        "\n"
        "WARNING-TRANSITION MANAGEMENT LANGUAGE\n"
        "--------------------------------------\n"
        "Convert internal warning transitions into management language. "
        "When the governed evidence shows an Amber to Red transition, "
        "write 'escalate from amber to red' or 'move from amber to red' "
        "-- never quote the internal status phrase verbatim.\n"
        "\n"
        "NEXT-STEP DISCIPLINE\n"
        "--------------------\n"
        "For 'what_management_should_do':\n"
        "  - Decision shape only: review, verify, escalate.\n"
        "  - Never invent specific bed, staff, patient or procedure "
        "counts.\n"
        "  - Do not prescribe a specific number of beds, staff, patients, "
        "or procedures.\n"
        "\n"
        "NO CHATBOT / NO ADDITIONAL SECTIONS\n"
        "-----------------------------------\n"
        "  - Do not generate a chatbot.\n"
        "  - Do not invite follow-up questions.\n"
        "  - Do not create additional sections beyond the three Q&A "
        "fields.\n"
        "  - Do not invite the user to provide more input.\n"
        "\n"
        "GOVERNANCE NOTE\n"
        "---------------\n"
        "Always set governance_note to the exact literal:\n"
        "  \"AI-assisted interpretation of governed Sentinel360 outputs.\"\n"
    )


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------

class UnsupportedProviderError(Exception):
    """Raised when a provider has no registered HTTP client."""


class TencentTokenHubClient:
    """Live TokenHub / Hy3 client implementation.

    Holds the URL/auth/temperature/max_tokens wiring for the Tencent
    TokenHub ``/v1/chat/completions`` endpoint. Multiple sub-providers
    (``tencent_hunyuan``, ``tencent_hunyuan_pro``) share this client.
    """

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        temperature: float = 0.2,
        max_tokens: int = 800,
        model: str = "hy3",
        url: str = _TOKENHUB_CHAT_COMPLETIONS_URL,
    ) -> None:
        self.api_key = api_key
        self.timeout = timeout
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.model = model
        self.url = url

    def build_payload(
        self,
        messages: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        return {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }

    def build_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + str(self.api_key or ""),
        }

    def post(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Any:
        if requests is None:
            raise RuntimeError(
                "The 'requests' library is required for live TokenHub "
                "calls but is not installed."
            )
        return requests.post(
            self.url,
            headers=headers,
            json=payload,
            timeout=self.timeout,
        )


_PROVIDER_REGISTRY: Dict[str, Callable[[Any], Any]] = {}


def register_provider(
    name: str,
    factory: Callable[["AIManagementSynthesisService"], Any],
) -> None:
    """Register an HTTP client factory for ``name``."""
    _PROVIDER_REGISTRY[name] = factory


def _tencent_factory(service: "AIManagementSynthesisService") -> TencentTokenHubClient:
    return TencentTokenHubClient(
        api_key=service.api_key,
        timeout=service.timeout,
        temperature=service.temperature,
        max_tokens=service.max_tokens,
        model=service.model,
    )


register_provider("tencent_hunyuan", _tencent_factory)
register_provider("tencent_hunyuan_pro", _tencent_factory)


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class AIManagementSynthesisResult:
    # Status / transport
    status: str = "PENDING"
    message: str = ""
    model_provider: str = ""
    model_name: str = ""
    raw: Optional[Dict[str, Any]] = None

    # Active Q&A schema fields
    what_is_happening: Optional[str] = None
    why_it_matters: Optional[str] = None
    what_management_should_do: Optional[str] = None
    governance_note: Optional[str] = None

    # Legacy long-form fields -- preserved on the dataclass as None
    headline: Optional[str] = None
    situation: Optional[str] = None
    management_significance: Optional[str] = None
    next_step: Optional[str] = None

    # Internal observability
    response_duration_seconds: Optional[float] = None
    request_sent_at: Optional[float] = None
    http_status_code: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class AIManagementSynthesisService:
    """Calls the live Hy3 transport for the Q&A contract."""

    def __init__(
        self,
        *,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        temperature: float = 0.2,
        max_tokens: int = 800,
    ) -> None:
        # Provider is treated as "explicit and intentional" if a non-None
        # value was passed -- including the empty string. Empty string is
        # a deliberate "nothing configured yet" signal in the test
        # contract and is preserved as the canonical "no provider" state.
        if provider is not None:
            self.provider = provider
        else:
            # Cloud-safe resolution: prefer st.secrets (Community Cloud),
            # fall back to OS env var, finally the canonical default.
            self.provider = get_runtime_secret(
                "SENTINEL360_AI_PROVIDER",
                default=_DEFAULT_PROVIDER,
            )

        if model is not None:
            self.model = model
        else:
            # Cloud-safe resolution: prefer st.secrets, fall back to env,
            # finally the canonical default model.
            self.model = get_runtime_secret(
                "SENTINEL360_AI_MODEL",
                default=_DEFAULT_MODEL,
            )

        if api_key is not None:
            self.api_key = api_key
        else:
            # Cloud-safe resolution: prefer st.secrets, fall back to env.
            # No default: api_key remains None if neither source is set,
            # which already triggers the deterministic fallback.
            self.api_key = get_runtime_secret("SENTINEL360_AI_API_KEY")

        self.timeout = timeout
        self.temperature = temperature
        self.max_tokens = max_tokens

    # -------------------------------------------------------------------
    # Provider routing
    # -------------------------------------------------------------------

    def _resolve_client(self) -> Any:
        factory = _PROVIDER_REGISTRY.get(self.provider)
        if factory is None:
            raise UnsupportedProviderError(
                "Unsupported AI provider '" + str(self.provider) + "'. "
                "Supported providers: "
                + ", ".join(sorted(_PROVIDER_REGISTRY))
            )
        return factory(self)

    def is_real_provider_enabled(self) -> bool:
        return (
            self.provider in _PROVIDER_REGISTRY
            and bool(self.api_key)
            and requests is not None
        )

    # -------------------------------------------------------------------
    # LLM call wrapper (HTTP).  Patched in the test suite; tests pass a
    # pre-built list of message dicts and an optional mock return value.
    # -------------------------------------------------------------------

    def _call_llm(
        self,
        messages: List[Dict[str, str]],
    ) -> AIManagementSynthesisResult:
        # Configuration guardrails.  ``synthesize`` returns NOT_CONFIGURED
        # for unsupported / missing-key cases so the page can fall back to
        # its non-AI rendering, but a direct caller of ``_call_llm``
        # (e.g. the live-dispatch test) gets API_UNAVAILABLE because the
        # call IS reaching the dispatcher.
        if self.provider and self.provider not in _PROVIDER_REGISTRY:
            result = AIManagementSynthesisResult(
                status="API_UNAVAILABLE",
                message=(
                    "Unsupported AI provider '" + str(self.provider) + "'. "
                    "The live TokenHub transport does not support this "
                    "provider (not supported by Sentinel360)."
                ),
                model_provider=self.provider,
                model_name=self.model,
            )
            _ensure_governance_note(result)
            return result

        if not self.api_key:
            result = AIManagementSynthesisResult(
                status="NOT_CONFIGURED",
                message=(
                    "SENTINEL360_AI_API_KEY is not set. Cannot call the "
                    "live TokenHub endpoint for provider "
                    + str(self.provider) + "."
                ),
                model_provider=self.provider,
                model_name=self.model,
            )
            _ensure_governance_note(result)
            return result

        if not self.is_real_provider_enabled():
            result = AIManagementSynthesisResult(
                status="NOT_CONFIGURED",
                message=(
                    "TokenHub / Hy3 is not configured for provider "
                    + str(self.provider) + "."
                ),
                model_provider=self.provider,
                model_name=self.model,
            )
            _ensure_governance_note(result)
            return result

        try:
            client = self._resolve_client()
        except UnsupportedProviderError as exc:
            result = AIManagementSynthesisResult(
                status="NOT_CONFIGURED",
                message=str(exc),
                model_provider=self.provider,
                model_name=self.model,
            )
            _ensure_governance_note(result)
            return result

        payload = client.build_payload(messages)
        headers = client.build_headers()

        sent_at = time.time()
        try:
            response = client.post(payload, headers)
        except RequestsTimeout as exc:
            result = AIManagementSynthesisResult(
                status="TIMEOUT",
                message=(
                    "TokenHub request timed out. timed out: "
                    + str(exc)
                ),
                model_provider=self.provider,
                model_name=self.model,
                response_duration_seconds=time.time() - sent_at,
                request_sent_at=sent_at,
            )
            _ensure_governance_note(result)
            return result
        except RequestsConnectionError as exc:
            result = AIManagementSynthesisResult(
                status="API_UNAVAILABLE",
                message=(
                    "TokenHub network error -- connection failed: "
                    + str(exc)
                ),
                model_provider=self.provider,
                model_name=self.model,
                response_duration_seconds=time.time() - sent_at,
                request_sent_at=sent_at,
            )
            _ensure_governance_note(result)
            return result
        except Exception as exc:
            result = AIManagementSynthesisResult(
                status="PROVIDER_ERROR",
                message=(
                    type(exc).__name__ + ": " + str(exc)
                ),
                model_provider=self.provider,
                model_name=self.model,
                response_duration_seconds=time.time() - sent_at,
                request_sent_at=sent_at,
            )
            _ensure_governance_note(result)
            return result

        duration = time.time() - sent_at
        result = self._parse_llm_response(
            response,
            model_provider=self.provider,
            model_name=self.model,
            duration=duration,
            sent_at=sent_at,
        )
        _ensure_governance_note(result)
        return result

    @staticmethod
    def _parse_llm_response(
        response: Any,
        *,
        model_provider: str,
        model_name: str,
        duration: float,
        sent_at: float,
    ) -> AIManagementSynthesisResult:
        """Translate the raw HTTP response into a result object.

        Status mapping (kept compatible with the existing test suite):

        * 2xx (with content)         -> OK
        * 401/403                    -> PROVIDER_ERROR
        * 429                        -> PROVIDER_ERROR ("rate limited")
        * 400/422                    -> PROVIDER_ERROR
        * 5xx                        -> API_UNAVAILABLE ("server error")
        * malformed JSON body        -> INVALID_RESPONSE ("not valid json")
        * empty choices              -> INVALID_RESPONSE ("empty choices")
        * missing/invalid content    -> INVALID_RESPONSE ("empty response body")
        """
        try:
            http_status = int(getattr(response, "status_code", 200))
        except Exception:
            http_status = 200

        if http_status in (401, 403):
            return AIManagementSynthesisResult(
                status="PROVIDER_ERROR",
                message="TokenHub authentication failed (HTTP "
                + str(http_status) + ").",
                model_provider=model_provider,
                model_name=model_name,
                response_duration_seconds=duration,
                request_sent_at=sent_at,
                http_status_code=http_status,
            )
        if http_status == 429:
            return AIManagementSynthesisResult(
                status="PROVIDER_ERROR",
                message="TokenHub rate limited (HTTP 429).",
                model_provider=model_provider,
                model_name=model_name,
                response_duration_seconds=duration,
                request_sent_at=sent_at,
                http_status_code=http_status,
            )
        if http_status in (400, 422):
            return AIManagementSynthesisResult(
                status="PROVIDER_ERROR",
                message="TokenHub rejected the request (HTTP "
                + str(http_status) + ").",
                model_provider=model_provider,
                model_name=model_name,
                response_duration_seconds=duration,
                request_sent_at=sent_at,
                http_status_code=http_status,
            )
        if http_status >= 500:
            return AIManagementSynthesisResult(
                status="API_UNAVAILABLE",
                message="TokenHub server error (HTTP "
                + str(http_status) + ").",
                model_provider=model_provider,
                model_name=model_name,
                response_duration_seconds=duration,
                request_sent_at=sent_at,
                http_status_code=http_status,
            )

        try:
            decoded = response.json()
        except Exception as exc:
            return AIManagementSynthesisResult(
                status="INVALID_RESPONSE",
                message="TokenHub returned a body that is not valid JSON: "
                + str(exc) + ".",
                model_provider=model_provider,
                model_name=model_name,
                response_duration_seconds=duration,
                request_sent_at=sent_at,
                http_status_code=http_status,
            )

        if not isinstance(decoded, dict):
            return AIManagementSynthesisResult(
                status="INVALID_RESPONSE",
                message="TokenHub response was not a JSON object.",
                model_provider=model_provider,
                model_name=model_name,
                response_duration_seconds=duration,
                request_sent_at=sent_at,
                http_status_code=http_status,
            )

        choices = decoded.get("choices")
        if not isinstance(choices, list) or not choices:
            return AIManagementSynthesisResult(
                status="INVALID_RESPONSE",
                message="TokenHub response had empty choices (no "
                "choices returned).",
                model_provider=model_provider,
                model_name=model_name,
                response_duration_seconds=duration,
                request_sent_at=sent_at,
                http_status_code=http_status,
            )

        first = choices[0]
        if not isinstance(first, dict):
            return AIManagementSynthesisResult(
                status="INVALID_RESPONSE",
                message="TokenHub choices[0] was not an object.",
                model_provider=model_provider,
                model_name=model_name,
                response_duration_seconds=duration,
                request_sent_at=sent_at,
                http_status_code=http_status,
            )

        message = first.get("message")
        if not isinstance(message, dict):
            return AIManagementSynthesisResult(
                status="INVALID_RESPONSE",
                message="TokenHub choices[0].message was not an object.",
                model_provider=model_provider,
                model_name=model_name,
                response_duration_seconds=duration,
                request_sent_at=sent_at,
                http_status_code=http_status,
            )

        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            return AIManagementSynthesisResult(
                status="INVALID_RESPONSE",
                message="TokenHub returned an empty response body "
                "(choices[0].message.content was empty).",
                model_provider=model_provider,
                model_name=model_name,
                response_duration_seconds=duration,
                request_sent_at=sent_at,
                http_status_code=http_status,
            )

        return AIManagementSynthesisResult(
            status="OK",
            message=content.strip(),
            model_provider=model_provider,
            model_name=model_name,
            raw=decoded,
            response_duration_seconds=duration,
            request_sent_at=sent_at,
            http_status_code=http_status,
        )

    # -------------------------------------------------------------------
    # Synthesis entrypoint -- parser and dataclass population
    # -------------------------------------------------------------------

    def synthesize(
        self,
        evidence_pack: ManagementEvidencePack,
    ) -> AIManagementSynthesisResult:
        # Configuration gating at the synthesis layer. We refuse to
        # build a messages list at all if the service is not
        # configured, so callers see a clear NOT_CONFIGURED status and
        # the page can fall back to its non-AI rendering.
        if not self.provider or self.provider == "":
            result = AIManagementSynthesisResult(
                status="NOT_CONFIGURED",
                message=(
                    "No AI provider configured. Set "
                    "SENTINEL360_AI_PROVIDER to a supported provider "
                    "(e.g. tencent_hunyuan)."
                ),
                model_provider="",
                model_name=self.model,
            )
            _ensure_governance_note(result)
            return result

        if self.provider not in _PROVIDER_REGISTRY:
            result = AIManagementSynthesisResult(
                status="NOT_CONFIGURED",
                message=(
                    "Unsupported AI provider '"
                    + str(self.provider) + "'. Supported providers: "
                    + ", ".join(sorted(_PROVIDER_REGISTRY))
                    + ". Set SENTINEL360_AI_PROVIDER to one of these."
                ),
                model_provider=self.provider,
                model_name=self.model,
            )
            _ensure_governance_note(result)
            return result

        if not self.api_key:
            result = AIManagementSynthesisResult(
                status="NOT_CONFIGURED",
                message=(
                    "SENTINEL360_AI_API_KEY is not set. Cannot call the "
                    "live TokenHub endpoint for provider "
                    + str(self.provider) + "."
                ),
                model_provider=self.provider,
                model_name=self.model,
            )
            _ensure_governance_note(result)
            return result

        # Build the message list (system + user) once and pass to
        # ``_call_llm`` so test fakes that patch ``_call_llm`` can
        # introspect it.
        messages = self._build_messages(evidence_pack)

        try:
            llm_result = self._call_llm(messages)
        except TimeoutError as exc:
            result = AIManagementSynthesisResult(
                status="TIMEOUT",
                message=(
                    "TokenHub request timed out. timed out: " + str(exc)
                ),
                model_provider=self.provider,
                model_name=self.model,
                response_duration_seconds=0.0,
            )
            _ensure_governance_note(result)
            return result
        except RequestsConnectionError as exc:
            result = AIManagementSynthesisResult(
                status="API_UNAVAILABLE",
                message=(
                    "TokenHub network error -- connection failed: "
                    + str(exc)
                ),
                model_provider=self.provider,
                model_name=self.model,
                response_duration_seconds=0.0,
            )
            _ensure_governance_note(result)
            return result
        except Exception as exc:
            result = AIManagementSynthesisResult(
                status="PROVIDER_ERROR",
                message=type(exc).__name__ + ": " + str(exc),
                model_provider=self.provider,
                model_name=self.model,
                response_duration_seconds=0.0,
            )
            _ensure_governance_note(result)
            return result

        if llm_result.status != "OK":
            # Non-OK statuses: surface the transport failure verbatim.
            _ensure_governance_note(llm_result)
            return llm_result

        # Empty content despite OK status -> INVALID_RESPONSE.
        if not (llm_result.message or "").strip():
            llm_result.status = "INVALID_RESPONSE"
            llm_result.message = (
                "TokenHub returned an empty response body "
                "(message.content was empty)."
            )
            _ensure_governance_note(llm_result)
            return llm_result

        # Try to parse the message as JSON; fall back to invalid.
        cleaned = _strip_markdown_fences(llm_result.message)
        parsed_payload: Optional[Dict[str, Any]] = None
        if cleaned:
            try:
                candidate = json.loads(cleaned)
                if isinstance(candidate, dict):
                    parsed_payload = candidate
            except Exception:
                parsed_payload = None

        if parsed_payload is None:
            llm_result.status = "INVALID_RESPONSE"
            llm_result.message = (
                "TokenHub response was not valid JSON; expected the Q&A "
                "schema JSON object."
            )
            _ensure_governance_note(llm_result)
            return llm_result

        llm_result.what_is_happening = _coerce_str(
            parsed_payload.get("what_is_happening")
        ) or None
        llm_result.why_it_matters = _coerce_str(
            parsed_payload.get("why_it_matters")
        ) or None
        llm_result.what_management_should_do = _coerce_str(
            parsed_payload.get("what_management_should_do")
        ) or None
        gov = parsed_payload.get("governance_note")
        if isinstance(gov, str) and gov.strip():
            llm_result.governance_note = gov.strip()

        # Guarantee governance_note has a value.
        _ensure_governance_note(llm_result)

        return llm_result

    # -------------------------------------------------------------------
    # Message construction (system + user prompts)
    # -------------------------------------------------------------------

    def _build_messages(
        self,
        evidence_pack: ManagementEvidencePack,
    ) -> List[Dict[str, str]]:
        """Build the [system, user] messages list passed to ``_call_llm``."""
        system_prompt = _build_system_prompt()
        user_prompt = _build_user_prompt(evidence_pack)
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]


# ---------------------------------------------------------------------------
# User prompt construction (module-level for direct test introspection)
# ---------------------------------------------------------------------------

def _build_user_prompt(evidence_pack: Optional[ManagementEvidencePack]) -> str:
    """Render the governed evidence pack into a compact user prompt.

    The executive-rules block is intentionally embedded in the user prompt
    as well so it is reinforced on every call (some Hy3 hardening tests
    verify its presence here too).
    """
    parts = ["Priority Management Review evidence (governed):", ""]

    sections: List[Tuple[str, Any]] = []
    if evidence_pack is not None:
        sections.extend(
            [
                ("Context", getattr(evidence_pack, "context", {}) or {}),
                ("Priority signal", getattr(evidence_pack, "priority_signal", {}) or {}),
                ("Forecast provenance", getattr(evidence_pack, "forecast_provenance", {}) or {}),
                ("Availability", getattr(evidence_pack, "availability", {}) or {}),
                ("Governance", getattr(evidence_pack, "governance", {}) or {}),
                ("Source references", getattr(evidence_pack, "source_references", {}) or {}),
            ]
        )
        if getattr(evidence_pack, "extra", None):
            sections.append(("Extra", evidence_pack.extra))

    for title, body in sections:
        if not body:
            continue
        parts.append("[{}]".format(title))
        if isinstance(body, dict):
            for key in sorted(body.keys()):
                parts.append("- {}: {}".format(key, _coerce_str(body[key])))
        else:
            parts.append("- " + _coerce_str(body))
        parts.append("")

    parts.extend(
        [
            "Executive rules (also in system prompt):",
            "- 15 to 30 words per answer; 1 sentence (preferred).",
            "- 50 to 90 words total; never above 100 words.",
            "- Display value: prefer 104.8 over 104.761905; never quote "
            "2.746188.",
            "- Do not claim causality.",
            "- Do not quote MAE / validation MAE / model method names.",
            "- Do not quote HOSP-001 or KPI_006 codes.",
            "- Do not invent bed, staff, patient, or procedure "
            "interventions.",
            "- Each answer must add a different layer (signal / "
            "consequence / management frame).",
            "- Express confidence in plain language (e.g. \"moderate "
            "indicative confidence\").",
            "- Always end with a brief management decision frame.",
        ]
    )
    return "\n".join(parts)
