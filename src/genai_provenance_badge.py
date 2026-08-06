"""
Sentinel360 Dynamic -- GenAI provenance badge helper.

Single source of truth for the on-screen "AI-ASSISTED · Tencent Hy3"
provenance convention used across the Executive Overview. Both the
KPI graph interpretation card and the Connected Signal card MUST
render the badge using these helpers so the styling stays identical.

Governance rule (do NOT relax):
    The badge and its associated caption only ever appear when the
    underlying synthesis result has ``status == "OK"`` from a live
    Tencent Hy3 call. Deterministic fallback text MUST NOT be labelled
    as AI-generated. The helpers enforce this gate so callers cannot
    accidentally render the badge on a non-OK result.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional


# ---------------------------------------------------------------------------
# Public constants (used by tests + by callers for wiring assertions)
# ---------------------------------------------------------------------------

BADGE_LABEL = "AI-ASSISTED · Tencent Hy3"

KPI_PROVENANCE_CAPTION = "Generated from governed Sentinel360 forecast evidence"
CS_PROVENANCE_CAPTION = "Generated from governed Sentinel360 connected-signal evidence"
RISK_PROVENANCE_CAPTION = "Generated from governed Sentinel360 Risk & Alert evidence"
DECISION_PROVENANCE_CAPTION = "Generated from governed Sentinel360 scenario evidence"


# Inline 4-point sparkle SVG. Colour is the only theming point.
_SPARKLE_SVG = (
    "<svg width='10' height='10' viewBox='0 0 16 16' "
    "xmlns='http://www.w3.org/2000/svg' "
    "style='vertical-align:-1px;margin-right:4px;'>"
    "<path d='M8 0 L9.2 6.8 L16 8 L9.2 9.2 L8 16 L6.8 9.2 L0 8 L6.8 6.8 Z' "
    "fill='#4A6A99'/></svg>"
)


# ---------------------------------------------------------------------------
# Gate: is this a genuine live Hy3 result?
# ---------------------------------------------------------------------------

def is_hy3_live(ai_result: Any) -> bool:
    """Return True only when ``ai_result`` represents a live Hy3 success.

    Accepts either:
      * a dict / Mapping with a ``"status"`` key whose value is ``"OK"``, or
      * an object exposing a ``.status`` attribute equal to ``"OK"``.

    Any other value (None, missing, fallback statuses such as
    ``NOT_CONFIGURED`` / ``TIMEOUT`` / ``API_UNAVAILABLE`` /
    ``INVALID_RESPONSE`` / ``PROVIDER_ERROR`` / ``GOVERNANCE_FILTERED``)
    returns False.
    """
    if ai_result is None:
        return False
    status: Optional[str] = None
    if isinstance(ai_result, Mapping):
        status = ai_result.get("status")
    else:
        status = getattr(ai_result, "status", None)
    if not isinstance(status, str):
        return False
    return status.strip().upper() == "OK"


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------

def render_hy3_badge_html() -> str:
    """Render the small rounded pill "AI-ASSISTED · Tencent Hy3" badge.

    The styling is identical for every caller (KPI card, Connected
    Signal card) so the user sees one consistent GenAI provenance
    convention. Caller is responsible for wrapping / positioning.
    """
    return (
        "<div style='margin:0 0 6px 0;'>"
        "<span style='display:inline-block;background:#E6EBF2;color:#4A6A99;"
        "font-size:9px;font-weight:700;letter-spacing:0.7px;"
        "text-transform:uppercase;padding:2px 8px;border-radius:10px;'>"
        f"{_SPARKLE_SVG}{BADGE_LABEL}</span>"
        "</div>"
    )


def render_hy3_caption_html(scope: str = "kpi") -> str:
    """Render the small muted provenance caption used under Hy3 output.

    Parameters
    ----------
    scope: str
        One of ``"kpi"`` (default) for the KPI graph interpretation
        card, ``"cs"`` for the Connected Signal card, or ``"risk"``
        for the Risk & Alert AI assistant. The wording matches the
        scope's data origin.
    """
    scope_lower = (scope or "").strip().lower()
    if scope_lower == "cs":
        text = CS_PROVENANCE_CAPTION
    elif scope_lower == "risk":
        text = RISK_PROVENANCE_CAPTION
    elif scope_lower == "decision":
        text = DECISION_PROVENANCE_CAPTION
    else:
        text = KPI_PROVENANCE_CAPTION
    return (
        "<div style='font-size:10px;color:#9AA5B5;font-style:italic;"
        "margin:6px 0 0 0;'>"
        f"{text}"
        "</div>"
    )


def render_hy3_provenance_html(ai_result: Any, scope: str = "kpi") -> str:
    """Render badge + caption as a single HTML block, gated on live Hy3.

    Returns the combined block when ``is_hy3_live(ai_result)`` is
    True, otherwise an empty string. Callers can therefore call this
    unconditionally -- the badge and caption only ever appear for
    genuine live Hy3 results.
    """
    if not is_hy3_live(ai_result):
        return ""
    return render_hy3_badge_html() + render_hy3_caption_html(scope=scope)
