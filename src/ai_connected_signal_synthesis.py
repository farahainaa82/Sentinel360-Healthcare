"""
AI Connected Signal Synthesis -- Hy3 interpretation of governed KPI relationships.

Produces a single concise executive sentence interpreting the connected signal
(primary chain, strength, forecast continuation). Does NOT calculate correlation
and does NOT invent interventions.

CS-3 guarantees:

* The live Tencent TokenHub / Hy3 transport is shared with the management
  synthesis service via :mod:`src._ai_tokenhub_transport`. No duplicate
  HTTP / API-key code path.
* Only governed evidence is sent to Hy3 (chain labels, movement
  directions, strength label, selected forecast month, continuation
  status, ``causality_confirmed = False``). Raw correlation coefficients
  and raw KPI history are never included in the request.
* On every outcome (live Hy3 OK / live Hy3 failure / no API key), the
  synthesis function returns *some* single sentence so the Connected
  Signal card never breaks. The sentence is either the (clipped) live
  Hy3 output or a deterministic interpretation derived from the
  continuation status.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field, asdict

from .runtime_secrets import get_runtime_secret
from typing import Any, Dict, List, Optional

from src._ai_tokenhub_transport import (
    DEFAULT_TOKENHUB_URL,
    call_tokenhub_chat_completion,
)


_ENV_PROVIDER = "SENTINEL360_AI_PROVIDER"
_ENV_MODEL = "SENTINEL360_AI_MODEL"
_ENV_API_KEY = "SENTINEL360_AI_API_KEY"

_DEFAULT_TIMEOUT = 45.0
_DEFAULT_TEMPERATURE = 0.2
_DEFAULT_MAX_TOKENS = 200

_AI_SCHEMA_VERSION = "ai_cs_v3"


_ENGLISH_MONTHS = {
    1: "January", 2: "February", 3: "March",
    4: "April", 5: "May", 6: "June",
    7: "July", 8: "August", 9: "September",
    10: "October", 11: "November", 12: "December",
}


# Forbidden causal verbs that Hy3 must NOT use.
_CAUSAL_PHRASES = (
    "caused by",
    "causes ",
    "drives",
    "leads to",
    "lead to",
    "results from",
    "resulting from",
    "because of",
    "is because",
)

_PREFERRED_HEDGES = (
    "associated with",
    "moving together",
    "connected pattern",
    "may indicate",
    "suggests",
)


# ---------------------------------------------------------------------------
# Hy3 system prompt (governance-aware single-sentence contract)
# ---------------------------------------------------------------------------

def _build_system_prompt() -> str:
    """Build the Hy3 governance-aware system prompt for connected signal.

    The interpretation is written specifically for hospital management
    (COO / GM / Medical Director) and must:
      * explain what was observed historically,
      * state whether the selected forecast month continues that pattern,
      * suggest what management should infer from it.
    """
    return (
        "You are a hospital executive management assistant. "
        "You are writing for a COO, General Manager, or Medical Director "
        "who needs a clear management read of a connected operational signal.\n"
        "\n"
        "Task: write a concise English interpretation of a governed "
        "connected-signal pattern in plain management language. "
        "Target 30 to 50 words, maximum 2 sentences.\n"
        "\n"
        "The interpretation must cover, in order:\n"
        "  1. What was observed historically (the connected KPI pattern "
        "and the strength label).\n"
        "  2. Whether the selected forecast month continues that pattern "
        "(based on the supplied continuation_status).\n"
        "  3. What management should infer (e.g. closer monitoring, "
        "review individual KPIs, treat as connected forward risk).\n"
        "\n"
        "Continuation-aware phrasing (use these phrasings directly when "
        "applicable, adapted to the supplied month label):\n"
        "  - CONTINUES: the connected pattern is visible in the forecast.\n"
        "  - PARTIAL: part of the connected pattern is visible, but the "
        "full sequence is not consistently present in the forecast.\n"
        "  - NOT_CONTINUING: the connected pattern is not consistently "
        "reflected in the forecast; the affected KPIs should be monitored "
        "individually rather than treated as one connected forward risk.\n"
        "  - NOT_APPLICABLE or no chain: the dashboard already shows the "
        "no-signal message; do not invent a narrative.\n"
        "\n"
        "Strict governance (non-negotiable):\n"
        "  - Use ONLY the supplied relationship evidence. Do not invent "
        "data, drivers, or interventions.\n"
        "  - Write 1 to 2 sentences. Target 30 to 50 words; never above "
        "60 words.\n"
        "  - Use cautious language such as 'associated with', 'moving "
        "together', 'connected pattern', 'may indicate', 'suggests', "
        "'warrants', 'should be monitored'.\n"
        "  - NEVER use causal language: 'caused by', 'causes', 'will "
        "result in', 'because of', 'drives', 'leads to', 'results from', "
        "'is because'.\n"
        "  - NEVER quote correlation coefficients, p-values, Spearman, "
        "Pearson, or any statistical method name.\n"
        "  - NEVER mention internal identifiers such as 'HOSP-001', "
        "'KPI_006', 'CS_001', or any coded label. Use only the supplied "
        "KPI display names and the supplied month label.\n"
        "  - NEVER mention the relationship schema version, API internals, "
        "model provider, or engine configuration.\n"
        "  - NEVER mention raw continuation codes (CONTINUES, PARTIAL, "
        "NOT_CONTINUING) in the output -- translate them into management "
        "phrasing as described above.\n"
        "  - Do NOT include the phrase 'causality is not confirmed' or any "
        "methodology note inside the main interpretation; this note lives "
        "in the card footer only.\n"
        "  - causality_confirmed is always false in the supplied evidence "
        "-- respect that; do not claim causality.\n"
        "\n"
        "Output format:\n"
        "Plain text. 1 to 2 sentences. No markdown, no JSON, no bullets, "
        "no line breaks, no methodology notes inside the main text.\n"
    )


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class AIConnectedSignalSynthesisResult:
    """Result of the connected-signal AI synthesis."""

    status: str
    message: str
    model_provider: str = ""
    model_name: str = ""
    response_duration_seconds: Optional[float] = None
    source: str = "ai"  # one of "ai" or "deterministic"
    raw: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class AIConnectedSignalSynthesisService:
    """Hy3-based single-sentence synthesis for the Connected Signal card.

    Uses the shared TokenHub transport. On any failure path (no API key,
    timeout, transport error, empty / invalid response, causal-language
    leak) the service falls back to a *deterministic* one-sentence
    interpretation derived from the continuation status, so the analytics
    card is never blank.
    """

    def __init__(
        self,
        *,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = _DEFAULT_TIMEOUT,
        temperature: float = _DEFAULT_TEMPERATURE,
        max_tokens: int = _DEFAULT_MAX_TOKENS,
        tokenhub_url: str = DEFAULT_TOKENHUB_URL,
    ) -> None:
        if provider is not None:
            self.provider = provider
        else:
            # Cloud-safe resolution: prefer st.secrets (Community Cloud),
            # fall back to OS env var, finally the canonical default.
            self.provider = get_runtime_secret(
                "SENTINEL360_AI_PROVIDER",
                default="tencent_hunyuan",
            )

        if model is not None:
            self.model = model
        else:
            # Cloud-safe resolution: prefer st.secrets, fall back to env,
            # finally the canonical default model.
            self.model = get_runtime_secret(
                "SENTINEL360_AI_MODEL",
                default="hy3",
            )

        # No default: api_key remains None if neither st.secrets nor
        # the OS env var is set, which triggers the deterministic
        # fallback in the synthesis service.
        self.api_key = (
            api_key
            if api_key is not None
            else get_runtime_secret("SENTINEL360_AI_API_KEY")
        )
        self.timeout = float(timeout)
        self.temperature = float(temperature)
        self.max_tokens = int(max_tokens)
        self.tokenhub_url = tokenhub_url

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def synthesize(
        self,
        connected_signal_result: Dict[str, Any],
    ) -> AIConnectedSignalSynthesisResult:
        """Produce the single executive sentence for the Connected Signal card.

        Steps:
          1. Extract the governed evidence slice (clean payload).
          2. If no provider / no API key, return NOT_CONFIGURED with a
             non-empty deterministic fallback message so the card is
             never blank.
          3. Build messages, call the shared TokenHub transport.
          4. On any AI failure, return a deterministic fallback that mirrors
             the continuation status. The card is never blank.
          5. On success, enforce single-sentence form, strip causal
             language, and clip the word budget.
        """
        governed = _extract_governed_payload(connected_signal_result)

        # No AI key configured -> NOT_CONFIGURED, but still produce a
        # non-empty deterministic message so the card is never blank.
        if not self.provider or not self.api_key:
            if not governed.get("has_supported_chain"):
                sentence = _deterministic_no_chain_sentence(
                    governed.get("hospital"),
                    governed.get("department"),
                    governed.get("period_label"),
                )
            else:
                sentence = _deterministic_interpretation(governed)
            return AIConnectedSignalSynthesisResult(
                status="NOT_CONFIGURED",
                message=sentence,
                model_provider=self.provider or "",
                model_name=self.model or "",
                source="deterministic",
            )

        # No chain -> synthetic no-chain sentence (no AI call needed).
        if not governed.get("has_supported_chain"):
            sentence = _deterministic_no_chain_sentence(
                governed.get("hospital"),
                governed.get("department"),
                governed.get("period_label"),
            )
            return AIConnectedSignalSynthesisResult(
                status="OK",
                message=sentence,
                model_provider="",
                model_name="",
                source="deterministic",
            )

        # Build messages and call the shared live transport.
        messages = self._build_messages(governed)
        call_status = call_tokenhub_chat_completion(
            messages,
            provider=self.provider,
            model=self.model,
            api_key=self.api_key,
            timeout=self.timeout,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            tokenhub_url=self.tokenhub_url,
        )

        if call_status.get("status") != "OK":
            fallback = _deterministic_interpretation(governed)
            return AIConnectedSignalSynthesisResult(
                status=str(call_status.get("status") or "PROVIDER_ERROR"),
                message=fallback,
                model_provider=self.provider,
                model_name=self.model,
                source="deterministic",
                raw=call_status.get("raw"),
            )

        ai_message = str(call_status.get("message") or "")
        cleaned = _clean_and_enforce_budget(ai_message)
        if not cleaned:
            fallback = _deterministic_interpretation(governed)
            return AIConnectedSignalSynthesisResult(
                status="INVALID_RESPONSE",
                message=fallback,
                model_provider=self.provider,
                model_name=self.model,
                source="deterministic",
                raw=call_status.get("raw"),
            )

        # Reject any causal-language leak -- fall back deterministically.
        if _contains_causal_language(cleaned):
            fallback = _deterministic_interpretation(governed)
            return AIConnectedSignalSynthesisResult(
                status="GOVERNANCE_FILTERED",
                message=fallback,
                model_provider=self.provider,
                model_name=self.model,
                source="deterministic",
                raw=call_status.get("raw"),
            )

        return AIConnectedSignalSynthesisResult(
            status="OK",
            message=cleaned,
            model_provider=self.provider,
            model_name=self.model,
            source="ai",
            raw=call_status.get("raw"),
        )

    # ------------------------------------------------------------------
    # Prompt construction -- only governed evidence, no raw coefficients.
    # ------------------------------------------------------------------

    def _build_messages(self, governed: Dict[str, Any]) -> List[Dict[str, str]]:
        """Build the [system, user] message list for Hy3.

        ``governed`` is the cleansed payload from
        :func:`_extract_governed_payload`. It contains only:
            - chain labels (KPI display names)
            - movement directions (up / down arrows in prose)
            - strength label
            - selected forecast month
            - continuation status
            - causality_confirmed (False)
        Raw correlation coefficients, raw KPI history, hospital codes,
        and KPI codes are stripped before transmission.
        """
        import json  # local import keeps module-import cost low for fallback use
        user_payload = json.dumps(governed, ensure_ascii=False, indent=2)
        return [
            {"role": "system", "content": _build_system_prompt()},
            {"role": "user", "content": user_payload},
        ]


# ---------------------------------------------------------------------------
# Governed-evidence extraction
# ---------------------------------------------------------------------------

_FORBIDDEN_PAYLOAD_KEYS = (
    "raw_history",
    "correlation_matrix",
    "raw_correlations",
    "spearman",
    "p_value",
    "pvalue",
    "history",
    "raw_kpis",
    "raw_correlation_coefficients",
    "raw_spearman",
)


def _extract_governed_payload(
    connected_signal_result: Dict[str, Any],
) -> Dict[str, Any]:
    """Reduce a Connected Signal result to the governed evidence slice.

    The result of this function is the *only* data structure that is ever
    serialised to Hy3. It deliberately omits:

      * raw correlation coefficients,
      * p-values,
      * raw KPI history,
      * hospital / department / KPI coded identifiers,
      * relationship schema version,
      * engine-internal flags that could leak structure.

    It does contain:
      * KPI display names from the supported chain,
      * movement directions (e.g. ``"up"`` / ``"down"``),
      * the strength label (e.g. ``"STRONG"``),
      * the selected forecast month label (e.g. ``"August 2025"``),
      * the continuation status (e.g. ``"CONTINUES"``),
      * ``causality_confirmed`` -- always set to ``False``.
    """
    if not isinstance(connected_signal_result, dict):
        return {
            "has_supported_chain": False,
            "chain_labels": [],
            "movement_directions": [],
            "strength_label": "",
            "forecast_month": "",
            "continuation_status": "",
            "causality_confirmed": False,
        }

    primary = connected_signal_result.get("primary_chain") or {}
    if not primary:
        primary = {}

    has_chain = bool(primary)

    chain_labels = _safe_list(primary.get("chain_kpi_names")) or _safe_list(
        primary.get("chain_labels")
    )

    movement_directions = _safe_list(primary.get("trend_directions")) or _safe_list(
        primary.get("movement_directions")
    )

    strength_label = (
        _safe_str(primary.get("strength_label"))
        or _safe_str(connected_signal_result.get("strength_label"))
        or _safe_str(connected_signal_result.get("strength"))
    )

    forecast_continuation = (
        connected_signal_result.get("forecast_continuation") or {}
    )

    continuation_status = (
        _safe_str(primary.get("continuation_status"))
        or _safe_str(primary.get("forecast_continuation_status"))
        or _safe_str(forecast_continuation.get("continuation_status"))
        or _safe_str(connected_signal_result.get("continuation_status"))
    )

    # The engine stores the year/month of the forecast at the top
    # level. Convert numeric month -> English month label.
    selected_month = (
        _safe_str(primary.get("selected_forecast_month_label"))
        or _safe_str(primary.get("forecast_month_label"))
        or _safe_str(primary.get("forecast_month"))
        or _safe_str(connected_signal_result.get("selected_forecast_month_label"))
    )
    if not selected_month:
        fc_year = connected_signal_result.get("selected_forecast_year")
        fc_month = connected_signal_result.get("selected_forecast_month")
        if fc_year and fc_month:
            try:
                m = int(fc_month)
                if 1 <= m <= 12:
                    selected_month = _ENGLISH_MONTHS[m] + " " + str(int(fc_year))
            except (TypeError, ValueError):
                selected_month = ""

    return {
        "has_supported_chain": has_chain,
        "chain_labels": chain_labels,
        "movement_directions": movement_directions,
        "strength_label": strength_label,
        "forecast_month": selected_month,
        "continuation_status": continuation_status,
        "causality_confirmed": False,  # hard-coded; never allow override.
    }


def _safe_str(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        return ""
    if isinstance(value, (list, tuple)):
        return ""
    if value is None:
        return ""
    return str(value)


def _safe_list(value: Any) -> List[str]:
    if isinstance(value, list):
        out: List[str] = []
        for v in value:
            if isinstance(v, str):
                out.append(v)
            elif v is None:
                out.append("")
            else:
                out.append(str(v))
        return out
    return []


# ---------------------------------------------------------------------------
# Deterministic fallback sentence builders
# ---------------------------------------------------------------------------

def _deterministic_no_chain_sentence(
    hospital: Optional[str],
    department: Optional[str],
    period_label: Optional[str],
) -> str:
    """Sentence rendered on the connected signal card when no chain is found.

    Per CS-3: ``"No sufficiently strong connected signal detected from
    the available actual history."`` -- short, deterministic, no
    hallucination.
    """
    return (
        "No sufficiently strong connected signal detected from the "
        "available actual history."
    )


def _deterministic_interpretation(governed: Dict[str, Any]) -> str:
    """Deterministic fallback interpretation for the management card.

    Used when:
      * the live Hy3 call fails / is not configured, or
      * Hy3 returns an empty / causal-leaking / over-budget response.

    Returns a 1 to 2 sentence management-voice interpretation derived
    from the continuation status, the chain KPI labels, and the
    selected forecast month. Wording avoids raw internal status codes
    (CONTINUES / PARTIAL / NOT_CONTINUING) and avoids causal language.
    """
    chain = _format_chain_for_prose(governed.get("chain_labels"))
    month = _format_month_for_prose(governed.get("forecast_month"))
    status = str(governed.get("continuation_status") or "").strip().upper()

    if status == "CONTINUES":
        return (
            "The historical pattern connecting " + chain + " is also "
            "visible in the " + month + " forecast, suggesting the "
            "connected operational signal may persist. Management "
            "should consider closer monitoring of the affected KPIs."
        )
    if status == "PARTIAL":
        return (
            "Some elements of the historical connected pattern between "
            + chain + " remain visible in the " + month + " forecast, "
            "but the full sequence is not consistently present. "
            "Management should review the affected KPIs individually "
            "before treating this as a sustained connected risk."
        )
    if status in ("NOT_CONTINUING", "NOT_CONTINUE", "NOT_CONTINUES"):
        return (
            "Historically, " + chain + " moved together, but the "
            + month + " forecast does not show the full pattern "
            "continuing. Management should monitor these indicators "
            "individually rather than treat them as one connected "
            "forward risk."
        )
    if status == "NOT_APPLICABLE":
        return (
            "No forecast month is currently selected for this connected "
            "pattern, so the forward signal is not applicable for "
            + month + "."
        )
    # Unknown continuation status: keep the sentence honest and short.
    return (
        "A historically observed connected pattern involving " + chain
        + " is associated with the " + month + " outlook. Management "
        + "should verify whether the signal continues before treating "
        + "it as a sustained operational risk."
    )


def _format_chain_for_prose(chain_labels: Any) -> str:
    """Render a list of KPI display names as flowing prose.

    Examples:
        ["A"]                          -> "A"
        ["A", "B"]                     -> "A and B"
        ["A", "B", "C"]                -> "A, B and C"
        []                             -> "the connected pattern"
    """
    if not isinstance(chain_labels, list) or not chain_labels:
        return "the connected pattern"
    labels = [str(x).strip() for x in chain_labels if str(x or "").strip()]
    if not labels:
        return "the connected pattern"
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return " and ".join(labels)
    return ", ".join(labels[:-1]) + " and " + labels[-1]


def _format_month_for_prose(forecast_month: Any) -> str:
    """Render the forecast-month label as prose ("August 2025" or "August").

    Accepts an int (1-12), a "YYYY-MM" string, a month name, or a
    already-formatted string. Returns the month name (long form) for
    management wording.
    """
    if forecast_month is None:
        return "the selected forecast"
    if isinstance(forecast_month, int):
        m = forecast_month
        if 1 <= m <= 12:
            return _ENGLISH_MONTHS[m - 1]
        return "the selected forecast"
    label = str(forecast_month).strip()
    if not label:
        return "the selected forecast"
    if label.lower() in {"the selected forecast", "the selected forecast month"}:
        return "the selected forecast"
    # Try "YYYY-MM"
    parts = label.split("-")
    if len(parts) == 2:
        try:
            m = int(parts[1])
            if 1 <= m <= 12:
                return _ENGLISH_MONTHS[m - 1]
        except ValueError:
            pass
    # If already a month name, return as-is.
    if label[:1].isalpha() and not label[:1].isdigit():
        return label
    return label


# ---------------------------------------------------------------------------
# Sentence cleaning and budget enforcement
# ---------------------------------------------------------------------------

_MARKDOWN_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.IGNORECASE)
_LINE_BREAK_RE = re.compile(r"\s*\n\s*")

_ENGLISH_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def _clean_and_enforce_budget(text: str, *, min_words: int = 30, max_words: int = 50) -> str:
    """Reduce an LLM message to 1-2 sentences within the 30-50 word budget.

    Strips markdown fences, collapses whitespace, keeps up to two
    sentences, and clips to ``max_words`` if necessary. If the model
    produces fewer than ``min_words`` words, a short management
    sentence is appended.
    """
    if not text or not isinstance(text, str):
        return ""
    cleaned = text.strip()
    if cleaned.startswith("```") and cleaned.endswith("```"):
        cleaned = _MARKDOWN_FENCE_RE.sub("", cleaned).strip()
    cleaned = _LINE_BREAK_RE.sub(" ", cleaned)
    cleaned = " ".join(cleaned.split())

    # Keep up to TWO sentences (split on ". ", "? ", "! ").
    sentence_ends: List[int] = []
    cursor = 0
    while cursor < len(cleaned):
        next_end = -1
        next_delim = ""
        for delim in (". ", "? ", "! "):
            idx = cleaned.find(delim, cursor)
            if idx != -1 and (next_end == -1 or idx < next_end):
                next_end = idx
                next_delim = delim
        if next_end == -1:
            break
        sentence_ends.append(next_end + len(next_delim))
        cursor = next_end + len(next_delim)
        if len(sentence_ends) >= 2:
            break

    if sentence_ends:
        cleaned = cleaned[: sentence_ends[-1]].strip()
    elif cleaned and cleaned[-1] not in (".", "?", "!"):
        cleaned = cleaned.rstrip(",;:-") + "."

    # Clip to max_words (keep whole words).
    words = cleaned.split()
    if len(words) > max_words:
        words = words[:max_words]
        if words and words[-1][-1] not in (".", "?", "!"):
            words[-1] = words[-1].rstrip(",;:-") + "."

    sentence = " ".join(words).strip()

    # If the model produced a too-short output, top up with a management
    # sentence so the card never reads as a fragment.
    if len(sentence.split()) < min_words:
        sentence = _top_up_sentence(sentence)

    return sentence


def _top_up_sentence(sentence: str) -> str:
    """Append a short management sentence to reach the 30-word floor.

    The tail is governance-safe language so we never accidentally inject
    causal claims or raw internal status codes.
    """
    if not sentence:
        return sentence
    tail = (
        " Management should monitor these KPIs closely given the historical "
        "association and the forward signal."
    )
    candidate = (sentence.rstrip(".").strip() + tail).strip()
    words = candidate.split()
    if len(words) > 50:
        words = words[:50]
        if words and words[-1][-1] not in (".", "?", "!"):
            words[-1] = words[-1].rstrip(",;:-") + "."
    return " ".join(words).strip()


def _contains_causal_language(text: str) -> bool:
    """Return True if *text* contains any causal phrasing Hy3 must avoid."""
    low = text.lower()
    for phrase in _CAUSAL_PHRASES:
        if phrase in low:
            return True
    return False
