"""
Step AI-4: Page-level helper for integrating the AI management synthesis
service into the Executive Overview Priority Management Review card.

This module is intentionally pure (no Streamlit imports). It is the single
seam between the Executive Overview page and the synthesis service, so all
cache-key logic, state -> text projection, fallback behaviour, and HTML
assembly for the Priority Management Review card live here. That makes
every rendering decision testable without spinning up Streamlit.

Hard rules (carried over from the integration spec):
  * No analytical value is recomputed. The deterministic fallback text is
    built from the same page-state fields the existing card already uses.
  * The API key is NEVER stored in the cache key, the cache value, or any
    returned structure. It is consumed once per call and discarded.
  * Any exception in the AI path is caught and converted to a non-OK
    status dict. The page never needs to wrap this in try/except.
  * Actual periods NEVER call the AI; the deterministic path is the only
    path for actual periods.

Active AI contract: **executive Q&A schema** — what_is_happening /
why_it_matters / what_management_should_do + governance_note rendered
as three compact rows beneath the FORWARD RISK / AI-ASSISTED pills.

Cache schema version ``ai1_qa_v2`` supersedes the legacy ``ai1_v1`` long-
form schema. The signature bump invalidates any stale long-form cache
entries; on miss the page falls back to deterministic text and refills.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Optional, Tuple

from src.ai_management_synthesis import AIManagementSynthesisService
from src.genai_provenance_badge import render_hy3_badge_html
from src.management_evidence_pack import ManagementEvidencePack
from src.runtime_secrets import get_runtime_secret


# ---------------------------------------------------------------------------
# Cache signature
# ---------------------------------------------------------------------------
# Active schema version. Bumped from "ai1_v1" (legacy long-form schema)
# to "ai1_qa_v2" (current executive Q&A schema) so that stale long-form
# responses are not reused after the schema change.
_AI_CACHE_SCHEMA_VERSION = "ai1_qa_v2"
def build_ai_cache_signature(state: Dict[str, Any]) -> Tuple[Any, ...]:
    """Build a stable cache key for the AI synthesis call.

    Key components (all required by spec):
        hospital_id, department_id, year, month,
        dominant_kpi_id, evidence schema version,
        deterministic hash of the AI evidence payload.

    The API key is intentionally NOT in the key — it is a credential, not a
    content signature. Changing the key never invalidates the AI wording.
    """
    payload_hash = ""
    try:
        ctx = state.get("selected_context") or {}
        if not isinstance(ctx, dict):
            ctx = {}
        pack = ManagementEvidencePack.from_executive_state(state)
        payload = pack.to_ai_payload()
        payload_json = json.dumps(
            payload, sort_keys=True, ensure_ascii=False, default=str
        )
        payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()[:16]
    except Exception:
        try:
            ctx = state.get("selected_context") or {}
            if not isinstance(ctx, dict):
                ctx = {}
        except Exception:
            ctx = {}

    return (
        ctx.get("hospital_id"),
        ctx.get("department_id"),
        ctx.get("selected_year"),
        ctx.get("selected_month"),
        state.get("dominant_kpi_id"),
        _AI_CACHE_SCHEMA_VERSION,
        payload_hash,
    )


def cache_signature_to_str(sig: Tuple[Any, ...]) -> str:
    """Render a signature tuple as a string key for dict-based caches."""
    return "|".join("" if v is None else str(v) for v in sig)


# ---------------------------------------------------------------------------
# AI synthesis call (defensive)
# ---------------------------------------------------------------------------
_EMPTY_AI_RESULT: Dict[str, Any] = {
    "status": "API_UNAVAILABLE",
    "what_is_happening": None,
    "why_it_matters": None,
    "what_management_should_do": None,
    "governance_note": None,
    "model_provider": None,
    "model_name": None,
    "message": "AI synthesis unavailable.",
    "response_duration_seconds": None,
}


def _build_empty_ai_result(reason: str) -> Dict[str, Any]:
    out = dict(_EMPTY_AI_RESULT)
    out["message"] = reason
    return out


def run_ai_synthesis_for_state(
    state: Dict[str, Any],
    *,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    timeout: int = 10,
) -> Dict[str, Any]:
    """Build an evidence pack from the page state, call the AI service,
    and return the result as a JSON-safe dict.

    This function is *defensive*: any exception (TypeError, ValueError, JSON
    errors, network errors, AI service errors) is caught and converted to a
    non-OK status dict. The page never needs to wrap this in try/except.

    The API key is consumed once and is NEVER returned. The result dict has
    no ``api_key``, ``authorization``, or other credential fields.
    """
    try:
        prov = provider if provider is not None else get_runtime_secret(
            "SENTINEL360_AI_PROVIDER", ""
        )
        mod = model if model is not None else get_runtime_secret(
            "SENTINEL360_AI_MODEL", ""
        )
        key = api_key if api_key is not None else get_runtime_secret(
            "SENTINEL360_AI_API_KEY", ""
        )
        pack = ManagementEvidencePack.from_executive_state(state)
        svc = AIManagementSynthesisService(
            provider=prov or None,
            model=mod or None,
            api_key=key or None,
            timeout=timeout,
        )
        result = svc.synthesize(pack)
        d = result.to_dict()
        # Defensive: scrub any accidental credential-like field.
        for forbidden in (
            "api_key", "apikey", "api-key", "authorization", "auth",
            "token", "secret", "password", "credential", "bearer",
        ):
            d.pop(forbidden, None)
        return d
    except Exception as exc:
        return _build_empty_ai_result(
            f"AI synthesis failed: {type(exc).__name__}: {exc}"
        )


# ---------------------------------------------------------------------------
# Deterministic fallback text — preserves the existing page logic exactly
# ---------------------------------------------------------------------------
_MONTH_NAMES = [
    "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def _month_name(month: Any) -> str:
    try:
        m = int(month)
    except (TypeError, ValueError):
        return ""
    if 1 <= m <= 12:
        return _MONTH_NAMES[m]
    return ""


def _safe_int(value: Any) -> int:
    try:
        s = str(value or "").strip()
        if s.isdigit():
            return int(s)
    except Exception:
        pass
    return 0


def build_deterministic_priority_text(
    state: Dict[str, Any], filters: Dict[str, Any]
) -> Dict[str, str]:
    """Compute the existing deterministic Priority Management Review text.

    Returns a dict with keys:
        period_badge_text, period_badge_class,
        overall_situation, highest_priority_alert

    The logic is a direct extraction of the page's existing branch tree; no
    sentence is reworded, no field is re-interpreted, no new condition is
    added. This is the fallback path for any non-OK AI result and for all
    ACTUAL periods.
    """
    period_type = state.get("period_type", "ACTUAL")
    dominant_kpi_id = state.get("dominant_kpi_id", "") or ""
    dominant_kpi_name = state.get("dominant_kpi_name", "") or ""
    dominant_status = state.get("dominant_status", "") or ""
    forecast_warning = state.get("dominant_forecast_warning", {}) or {}

    is_forecast = period_type == "FORECAST"
    has_priority = bool(dominant_kpi_id) and dominant_status in ("Red", "Amber")

    month_name = _month_name(filters.get("month"))
    year_value = _safe_int(filters.get("year"))
    dept_label = filters.get("department_name") or "All Departments"

    if is_forecast:
        badge_text = "Forward Risk \u2014 Action to Consider"
        badge_class = "forecast"
    else:
        badge_text = "Past Performance \u2014 Review"
        badge_class = "actual"

    if is_forecast:
        if has_priority:
            situation_text = (
                f"Operational pressure is forecast for {month_name} {year_value}, "
                f"primarily driven by {dominant_kpi_name}."
            )
        else:
            situation_text = (
                f"{month_name} {year_value} is forecast to remain within acceptable "
                f"operational thresholds for {dept_label}."
            )
    else:
        if has_priority:
            situation_text = (
                f"Operational pressure was recorded during {month_name} {year_value}, "
                f"primarily driven by {dominant_kpi_name}."
            )
        else:
            situation_text = (
                f"{month_name} {year_value} performance remained within acceptable "
                f"thresholds for {dept_label}."
            )

    if has_priority:
        if is_forecast:
            warning_level = (
                str(forecast_warning.get("warning_level") or "").strip() or "elevated"
            )
            alert_text = (
                f"{dominant_kpi_name} is the most significant forecast risk and may move "
                f"the service into {warning_level.lower()} severity during {month_name} {year_value}."
            )
        else:
            alert_text = (
                f"{dominant_kpi_name} ({dominant_status}) was the most significant "
                f"operational concern during the period."
            )
    else:
        alert_text = "No priority operational concern was identified for this period."

    return {
        "period_badge_text": badge_text,
        "period_badge_class": badge_class,
        "overall_situation": situation_text,
        "highest_priority_alert": alert_text,
    }


# ---------------------------------------------------------------------------
# Render-plan contract: decides between Q&A AI path and deterministic text
# ---------------------------------------------------------------------------
_QA_LABELS: List[str] = [
    "WHAT IS HAPPENING?",
    "WHY DOES IT MATTER?",
    "WHAT SHOULD MANAGEMENT DO NEXT?",
]


def build_render_plan(
    *,
    is_forecast: bool,
    ai_status: Optional[str],
    ai_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Decide what the Priority Management Review card should render.

    Contract:
        * ``is_forecast and ai_status == "OK"`` -> ``mode == "ai"`` with
          three Q&A rows populated from ``ai_payload`` plus a subtle
          governance footer line.
        * Otherwise -> ``mode == "deterministic"``; no AI badge, no
          governance footer, no Q&A rows.
    """
    payload = ai_payload or {}
    if is_forecast and ai_status == "OK":
        return {
            "mode": "ai",
            "questions": [
                {
                    "label": _QA_LABELS[0],
                    "answer": payload.get("what_is_happening"),
                },
                {
                    "label": _QA_LABELS[1],
                    "answer": payload.get("why_it_matters"),
                },
                {
                    "label": _QA_LABELS[2],
                    "answer": payload.get(
                        "what_management_should_do"
                    ),
                },
            ],
            "governance_note": payload.get("governance_note") or (
                "AI-assisted interpretation of governed Sentinel360 outputs."
            ),
            "show_ai_pill": True,
            "show_governance_footer": True,
        }
    return {
        "mode": "deterministic",
        "questions": [],
        "show_ai_pill": False,
        "show_governance_footer": False,
    }


# ---------------------------------------------------------------------------
# Priority card HTML assembly
# ---------------------------------------------------------------------------
def _esc(s: Any) -> str:
    """Minimal HTML escape for user/LLM-provided text inside card body."""
    if s is None:
        return ""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _qa_row_html(question: str, answer: Optional[str]) -> str:
    """Render a single Q&A row (uppercase label + answer) as compact HTML."""
    return (
        '<div class="s360-ai-qa-row">'
        f'<div class="s360-ai-qa-label">{_esc(question)}</div>'
        f'<div class="s360-ai-qa-answer">{_esc(answer)}</div>'
        '</div>'
    )


def build_priority_card_html(
    *,
    period_badge_text: str,
    period_badge_class: str,
    overall_situation: str,
    highest_priority_alert: str,
    what_is_happening: Optional[str] = None,
    why_it_matters: Optional[str] = None,
    what_management_should_do: Optional[str] = None,
    show_ai_pill: bool = False,
    show_governance_footer: bool = False,
) -> str:
    """Assemble the Priority Management Review card HTML.

    Deterministic path (default — ACTUAL periods, AI failure, AI not
    configured):
        Period badge + Overall Situation + Highest-Priority Alert.

    AI-assisted path (FORECAST + AI OK):
        Period badge + AI-ASSISTED pill + three compact Q&A rows:
            WHAT IS HAPPENING?           -> what_is_happening
            WHY DOES IT MATTER?          -> why_it_matters
            WHAT SHOULD MANAGEMENT DO NEXT? -> what_management_should_do
        plus a subtle governance footer line.

    When the AI path is active, the legacy 'Overall Situation' and
    'Highest-Priority Alert' rows are suppressed in favor of the three
    Q&A rows so the card stays compact.

    Only the **executive Q&A schema** is rendered. The legacy long-form
    AI fields (ai_headline / management_significance / next_management_step)
    are no longer accepted by this signature.
    """
    badge_html = (
        f'<span class="s360-pm-status-badge {_esc(period_badge_class)}">'
        f'{_esc(period_badge_text)}</span>'
    )
    # Reuse the shared GenAI provenance badge helper so this card uses
    # exactly the same "AI-ASSISTED · Tencent Hy3" pill as the other
    # Hy3-powered sections (Management Interpretation, KPI graph
    # interpretation, Connected Signal, AI Risk Brief).
    ai_pill_html = render_hy3_badge_html() if show_ai_pill else ""
    badge_row = (
        f'<div style="margin:6px 0 14px 0; display:flex; gap:8px; '
        f'align-items:center; flex-wrap:wrap;">{badge_html}{ai_pill_html}</div>'
    )

    governance_footer = ""
    if show_governance_footer:
        governance_footer = (
            '<div class="s360-ai-governance">'
            'AI-assisted interpretation of governed Sentinel360 outputs.'
            '</div>'
        )

    if show_ai_pill:
        # ----- AI-assisted executive Q&A path -----------------------------
        # Render exactly three Q&A rows; never fall back to legacy labels.
        qa_block = (
            '<div class="s360-ai-qa">'
            + _qa_row_html(_QA_LABELS[0], what_is_happening)
            + _qa_row_html(_QA_LABELS[1], why_it_matters)
            + _qa_row_html(_QA_LABELS[2], what_management_should_do)
            + '</div>'
        )
        return (
            '<div class="s360-priority-card">'
            '<div class="s360-priority-label">Priority Management Review</div>'
            f'{badge_row}'
            f'{qa_block}'
            f'{governance_footer}'
            '</div>'
        )

    # ----- Deterministic path (ACTUAL + fallback) ------------------------
    rows = [
        (
            f'<div class="s360-pm-row">'
            f'<span class="s360-pm-label">Overall Situation</span>'
            f'<div class="s360-pm-value">{_esc(overall_situation)}</div>'
            f'</div>'
        ),
        (
            f'<div class="s360-pm-row">'
            f'<span class="s360-pm-label">Highest-Priority Alert</span>'
            f'<div class="s360-pm-value">{_esc(highest_priority_alert)}</div>'
            f'</div>'
        ),
    ]
    return (
        '<div class="s360-priority-card">'
        '<div class="s360-priority-label">Priority Management Review</div>'
        f'{badge_row}'
        + "".join(rows)
        + '</div>'
    )


__all__ = [
    "_AI_CACHE_SCHEMA_VERSION",
    "build_ai_cache_signature",
    "build_deterministic_priority_text",
    "build_render_plan",
    "build_priority_card_html",
    "cache_signature_to_str",
    "run_ai_synthesis_for_state",
]  # noqa: W391
