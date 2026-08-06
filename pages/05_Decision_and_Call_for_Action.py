"""pages/05_Decision_and_Call_for_Action.py — Decision & Call for Action (Phase 3E).

Reads ONLY the existing Simulation Lab handoff.
No new models. No new calculations. No financial engines.
"""
from __future__ import annotations

import base64
import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import streamlit as st

from src.simulation_lab_controller import (
    _KPI_ID_TO_NAME,
    _KPI_TO_ACTION_STRATEGY,
)
from src.streamlit_executive_data_loader import (
    GOVERNED_ACTUAL_YEAR,
    _display_department,
)
from src.streamlit_executive_page_controller import (
    format_unit_value,
    load_kpi_threshold_config,
)
from src.s360_sidebar_chrome import render_sidebar_chrome
from src.decision_confidence_demo import get_decision_confidence
from src.decision_impact_ai_evidence import (
    build_decision_impact_evidence,
    build_decision_impact_cache_key,
)
from src.ai_decision_impact_synthesis import AIDecisionImpactSynthesisService

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Decision & Call for Action", page_icon="", layout="wide")

# --- SIDEBAR CHROME (brand + footer + native nav styling) ---
render_sidebar_chrome()

# ---------------------------------------------------------------------------
# CSS — Sentinel360 design system
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

/* Header bar */
.s360-dec-header-bar {
    background: #0B1E3D;
    border-radius: 8px;
    padding: 18px 24px;
    margin-bottom: 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.s360-dec-header-left { flex: 1; }
.s360-dec-header-title {
    font-size: 1.35rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 2px;
    letter-spacing: -0.3px;
}
.s360-dec-header-sub {
    font-size: 0.8rem;
    font-weight: 400;
    color: #A0B1C8;
    margin-top: 2px;
}
.s360-dec-header-version {
    font-size: 0.65rem;
    font-weight: 600;
    color: #0288D1;
    background: rgba(2, 136, 209, 0.15);
    padding: 2px 8px;
    border-radius: 12px;
    display: inline-block;
    margin-top: 4px;
}
.s360-dec-logo-cell {
    display: flex;
    align-items: center;
    justify-content: center;
    background: #ffffff;
    border-radius: 6px;
    padding: 6px 10px;
    margin-left: 12px;
}
.s360-dec-logo-cell img { max-height: 28px; display: block; }

/* Management Decision Review strip */
.s360-dec-strip {
    background: #EAF4FF;
    border: 1px solid #BBDEFB;
    border-left: 4px solid #0288D1;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 18px;
}
.s360-dec-strip-title {
    font-size: 0.8rem;
    font-weight: 700;
    color: #0B1E3D;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin-bottom: 4px;
}
.s360-dec-strip-help {
    font-size: 0.8rem;
    color: #4A5568;
    margin: 0;
}

/* Section label (page hierarchy) */
.s360-dec-section-label {
    font-size: 16px;
    font-weight: 800;
    color: #718096;
    text-transform: uppercase;
    letter-spacing: 0.9px;
    margin: 22px 0 12px 0;
    padding-bottom: 7px;
    border-bottom: 1px solid #DDE3EC;
    line-height: 1.2;
}

/* Cards */
.s360-dec-card {
    background: #ffffff;
    border: 1px solid #DDE3EC;
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 8px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.03);
}
.s360-dec-micro {
    font-size: 0.7rem;
    font-weight: 600;
    color: #718096;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    margin-bottom: 4px;
}
.s360-dec-value {
    font-size: 1.15rem;
    font-weight: 700;
    color: #1A2B47;
}
.s360-dec-caption {
    font-size: 0.8rem;
    color: #4A5568;
    margin-top: 2px;
}

/* Evidence cards — tinted left borders */
.s360-dec-evidence-latest { border-left: 4px solid #718096; }
.s360-dec-evidence-forecast { border-left: 4px solid #7C8EA3; }
.s360-dec-evidence-scenario { border-left: 4px solid #2E9F6B; }
.s360-dec-evidence-target { border-left: 4px solid #0288D1; }

/* Arrow */
.s360-dec-arrow {
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.5rem;
    font-weight: 700;
    line-height: 1;
    min-height: 80px;
    color: #0288D1;
}

/* Impact cards */
.s360-dec-impact-card { border-left: 4px solid #0288D1; }

/* Action card */
.s360-dec-action-card {
    background: #ffffff;
    border: 1px solid #DDE3EC;
    border-left: 4px solid #0288D1;
    border-radius: 8px;
    padding: 18px 20px;
    margin-bottom: 12px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.03);
}
.s360-dec-action-headline {
    font-size: 1.25rem;
    font-weight: 700;
    color: #1A2B47;
    margin-bottom: 14px;
    line-height: 1.4;
}
.s360-dec-meta-row {
    display: flex;
    gap: 32px;
    flex-wrap: wrap;
    font-size: 0.85rem;
    color: #4A5568;
}
.s360-dec-meta-label {
    font-size: 0.7rem;
    font-weight: 600;
    color: #718096;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    margin-bottom: 2px;
}
.s360-dec-meta-value {
    font-weight: 600;
    color: #1A2B47;
}

/* Confidence */
.s360-dec-confidence-card { border-left: 4px solid #0288D1; }

/* Decision container */
.s360-dec-decision-container {
    background: #ffffff;
    border: 1px solid #DDE3EC;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 12px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.03);
}
.s360-dec-decision-legend {
    display: flex;
    gap: 8px;
    margin-bottom: 12px;
    flex-wrap: wrap;
}
.s360-dec-legend-chip {
    font-size: 0.75rem;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 4px;
}
.s360-dec-legend-approve { background: #E6F4EA; color: #1B5E20; }
.s360-dec-legend-revision { background: #FFF4E5; color: #B45309; }
.s360-dec-legend-defer { background: #EAF4FF; color: #2F80ED; }
.s360-dec-legend-not-approved { background: #FDECEA; color: #B71C1C; }

/* Selected indicator */
.s360-dec-selected-chip {
    display: inline-block;
    font-size: 0.8rem;
    font-weight: 600;
    padding: 6px 14px;
    border-radius: 16px;
    margin-top: 8px;
}

/* Note card */
.s360-dec-note-card {
    background: #ffffff;
    border: 1px solid #DDE3EC;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.03);
}

/* CTA */
.s360-dec-cta {
    background: #0B1E3D;
    border-radius: 8px;
    padding: 24px;
    color: #ffffff;
    margin-bottom: 16px;
}
.s360-dec-cta-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 4px;
}
.s360-dec-cta-help {
    font-size: 0.85rem;
    color: #A0B1C8;
    margin-bottom: 14px;
}

/* Status chips */
.s360-dec-status-chip {
    display: inline-block;
    padding: 5px 14px;
    border-radius: 16px;
    font-size: 0.85rem;
    font-weight: 600;
}
.s360-dec-status-pending { background: #FFF4E5; color: #B45309; }
.s360-dec-status-approved { background: #E6F4EA; color: #1B5E20; }
.s360-dec-status-revision { background: #FFF4E5; color: #B45309; }
.s360-dec-status-deferred { background: #EAF4FF; color: #2F80ED; }
.s360-dec-status-not-approved { background: #FDECEA; color: #B71C1C; }

/* Record card */
.s360-dec-record-card {
    background: #ffffff;
    border: 1px solid #DDE3EC;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.03);
}
.s360-dec-record-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    padding: 6px 0;
    border-bottom: 1px solid #F5F7FA;
    font-size: 0.9rem;
}
.s360-dec-record-row:last-child { border-bottom: none; }
.s360-dec-record-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: #718096;
    text-transform: uppercase;
    letter-spacing: 0.4px;
}
.s360-dec-record-value {
    font-weight: 600;
    color: #1A2B47;
}

/* Empty / error states */
.s360-dec-empty-state {
    background: #F5F7FA;
    border: 1px solid #DDE3EC;
    border-radius: 8px;
    padding: 24px;
    text-align: center;
    margin-bottom: 16px;
}
.s360-dec-empty-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #1A2B47;
    margin-bottom: 8px;
}
.s360-dec-empty-help {
    font-size: 0.85rem;
    color: #4A5568;
    max-width: 480px;
    margin: 0 auto;
}
.s360-dec-error-state {
    background: #FDECEA;
    border: 1px solid #FDECEA;
    border-radius: 8px;
    padding: 24px;
    text-align: center;
    margin-bottom: 16px;
}
.s360-dec-error-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #B71C1C;
    margin-bottom: 8px;
}
.s360-dec-error-help {
    font-size: 0.85rem;
    color: #4A5568;
    max-width: 480px;
    margin: 0 auto;
}

/* Demo Decision Confidence — level-based visual treatment */
.s360-dec-confidence-card.s360-dec-cf-high {
    border-left-color: #1B5E20;
    border-top-color: #1B5E20;
}
.s360-dec-confidence-card.s360-dec-cf-moderate {
    border-left-color: #B45309;
    border-top-color: #B45309;
}
.s360-dec-confidence-card.s360-dec-cf-low {
    border-left-color: #B71C1C;
    border-top-color: #B71C1C;
}
.s360-dec-confidence-card.s360-dec-cf-unavailable {
    border-left-color: #94A3B8;
    border-top-color: #94A3B8;
    background: #F8FAFC;
    box-shadow: none;
}

.s360-dec-confidence-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
}
.s360-dec-confidence-head .s360-dec-micro { margin-bottom: 0; }

.s360-dec-confidence-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.6px;
    padding: 6px 14px;
    border-radius: 999px;
    text-transform: uppercase;
    line-height: 1;
}
.s360-dec-cf-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: currentColor;
    opacity: 0.75;
}
.s360-dec-pill-high { background: #E6F4EA; color: #1B5E20; }
.s360-dec-pill-moderate { background: #FFF4E5; color: #B45309; }
.s360-dec-pill-low { background: #FDECEA; color: #B71C1C; }
.s360-dec-pill-muted { background: #F1F5F9; color: #475569; }

.s360-dec-confidence-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin: 0 0 10px 0;
}
.s360-dec-confidence-block {
    background: #F8FAFC;
    border: 1px solid #EEF2F7;
    border-radius: 8px;
    padding: 10px 12px;
}
.s360-dec-confidence-block .s360-dec-micro { margin-bottom: 4px; }
.s360-dec-confidence-block-body {
    font-size: 0.88rem;
    color: #1A2B47;
    line-height: 1.4;
}
.s360-dec-confidence-foot {
    margin-top: 10px;
    font-size: 0.7rem;
    font-weight: 600;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.s360-dec-confidence-help {
    font-size: 0.72rem;
    color: #94A3B8;
    margin-top: 2px;
    line-height: 1.35;
}
.s360-dec-confidence-empty {
    font-size: 0.95rem;
    color: #475569;
    margin: 8px 0 4px 0;
    line-height: 1.45;
}
.s360-dec-confidence-empty-help {
    font-size: 0.78rem;
    color: #94A3B8;
    line-height: 1.4;
    margin-bottom: 8px;
}

/* ---- AI-Assisted Decision Impact interpretation card ---- */
.s360-dec-impact-card {
    background: #F7F9FC;
    border: 1px solid #DDE3EC;
    border-radius: 8px;
    padding: 14px 16px 12px 16px;
    margin: 4px 0 12px 0;
    box-shadow: 0 1px 4px rgba(15, 23, 42, 0.03);
    box-sizing: border-box;
}
.s360-dec-impact-card-title {
    font-size: 13px;
    font-weight: 700;
    color: #0B1E3D;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin: 0 0 10px 0;
    padding-bottom: 6px;
    border-bottom: 1px solid #DDE3EC;
    line-height: 1.2;
}
.s360-dec-impact-subhead {
    font-size: 11px;
    font-weight: 700;
    color: #0B1E3D;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin: 8px 0 4px 0;
    line-height: 1.3;
}
.s360-dec-impact-body {
    font-size: 13px;
    color: #1A202C;
    line-height: 1.55;
    margin: 0 0 6px 0;
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Logo helper
# ---------------------------------------------------------------------------

def _logo_data_uri(filename: str) -> str:
    p = Path(__file__).parent.parent / "assets" / filename
    if p.exists():
        return f"data:image/png;base64,{base64.b64encode(p.read_bytes()).decode()}"
    return ""


# ---------------------------------------------------------------------------
# Header render
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# AI-Assisted Decision Impact Interpretation
# ---------------------------------------------------------------------------

_DECISION_IMPACT_CACHE_NS = "s360_decision_impact_cache_v1"
_DECISION_IMPACT_CONTEXT_NS = "s360_decision_impact_context_v1"


def _get_decision_impact(
    evidence: Dict[str, Any],
    *,
    kpi_id: str,
    department_id: str,
    forecast_month_label: str,
) -> Any:
    """Resolve decision impact through cache → live Hy3 → fallback pipeline."""
    _ctx_key = (
        f"{_DECISION_IMPACT_CONTEXT_NS}:kpi={kpi_id}:dept={department_id}"
        f":month={forecast_month_label}"
    )
    _prev_ctx = st.session_state.get(_DECISION_IMPACT_CONTEXT_NS)
    if _prev_ctx != _ctx_key:
        st.session_state[_DECISION_IMPACT_CONTEXT_NS] = _ctx_key
        _ns = _DECISION_IMPACT_CACHE_NS
        for key in list(st.session_state.keys()):
            if key.startswith(_ns + ":"):
                del st.session_state[key]

    cache_key = build_decision_impact_cache_key(evidence)
    cached = st.session_state.get(cache_key)
    if cached is not None:
        return cached

    result = AIDecisionImpactSynthesisService().interpret(evidence)
    if result.status == "OK":
        st.session_state[cache_key] = result
    return result


def _render_decision_impact(interp_result: Any) -> None:
    """Render the AI-Assisted Decision Impact Interpretation section."""
    from src.genai_provenance_badge import (
        is_hy3_live,
        render_hy3_badge_html,
        render_hy3_caption_html,
    )

    _card_parts: list[str] = [
        '<div class="s360-dec-impact-card">',
        '<div class="s360-dec-impact-card-title">Decision Impact Interpretation</div>',
    ]
    if is_hy3_live(interp_result):
        _card_parts.append(render_hy3_badge_html())
    _card_parts.append(
        '<div class="s360-dec-impact-subhead">What does this mean for the decision?</div>'
        f'<div class="s360-dec-impact-body">{interp_result.what_it_means}</div>'
        '<div class="s360-dec-impact-subhead">Decision Implication</div>'
        f'<div class="s360-dec-impact-body">{interp_result.decision_implication}</div>'
    )
    if is_hy3_live(interp_result):
        _card_parts.append(render_hy3_caption_html(scope="decision"))
    if not interp_result.what_it_means and not interp_result.decision_implication:
        _card_parts.append(
            '<div class="s360-dec-impact-body" style="color:#64748B;font-style:italic;">'
            'No interpretation available.</div>'
        )
    _card_parts.append('</div>')
    st.markdown(''.join(_card_parts), unsafe_allow_html=True)


def _render_header() -> None:
    jcorp = _logo_data_uri("jcorp_logo.png")
    bsw = _logo_data_uri("black_swan_protocol_logo.png")
    logo_html = ""
    if jcorp:
        logo_html += f'<div class="s360-dec-logo-cell"><img src="{jcorp}" alt="JCORP"></div>'
    if bsw:
        logo_html += f'<div class="s360-dec-logo-cell"><img src="{bsw}" alt="Black Swan Protocol"></div>'
    st.markdown(
        f"""
        <div class="s360-dec-header-bar">
            <div class="s360-dec-header-left">
                <div class="s360-dec-header-title">Sentinel360 Healthcare</div>
                <div class="s360-dec-header-version">1.0</div>
                <div class="s360-dec-header-sub">Intelligent Early Warning System for Organisational Performance</div>
            </div>
            <div style="display:flex; align-items:center;">
                {logo_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _kpi_unit(kpi_id: str) -> str:
    """Return a display unit for a KPI id (best-effort)."""
    mapping = {
        "kpi_001": "FTE",
        "kpi_002": "%",
        "kpi_003": "%",
        "kpi_004": "min",
        "kpi_005": "%",
        "kpi_006": "/5 Likert",
    }
    return mapping.get(kpi_id, "")


def _resolve_kpi_name(kpi_id: str) -> str:
    return _KPI_ID_TO_NAME.get(kpi_id, kpi_id)


def _resolve_department_name(dept_id: str) -> str:
    return _display_department(dept_id)


def _status_css_class(status: str) -> str:
    s = str(status).strip().upper()
    if s == "APPROVED":
        return "s360-dec-status-approved"
    if s in ("REVISION REQUIRED", "REVISION"):
        return "s360-dec-status-revision"
    if s == "DEFERRED":
        return "s360-dec-status-deferred"
    if s in ("NOT APPROVED", "NOT_APPROVED"):
        return "s360-dec-status-not-approved"
    return "s360-dec-status-pending"


def _decision_status_text(decision: str) -> str:
    d = str(decision).strip().upper()
    if d == "APPROVE":
        return "APPROVED FOR ACTION PLANNING"
    if d == "REVISION REQUIRED":
        return "REVISION REQUIRED"
    if d == "DEFER":
        return "DEFERRED"
    if d == "NOT APPROVED":
        return "NOT APPROVED"
    return "PENDING MANAGEMENT REVIEW"


def _confidence_pill_class(level: str) -> str:
    """Return the CSS class for a demo decision confidence level pill."""
    s = str(level or "").strip().upper()
    if s == "HIGH":
        return "s360-dec-pill-high"
    if s == "MODERATE":
        return "s360-dec-pill-moderate"
    if s == "LOW":
        return "s360-dec-pill-low"
    return "s360-dec-pill-muted"


def _confidence_card_class(level: str) -> str:
    """Return the CSS class for the confidence card level accent (border + top bar)."""
    s = str(level or "").strip().upper()
    if s == "HIGH":
        return "s360-dec-cf-high"
    if s == "MODERATE":
        return "s360-dec-cf-moderate"
    if s == "LOW":
        return "s360-dec-cf-low"
    return "s360-dec-cf-unavailable"


# ---------------------------------------------------------------------------
# Governed Target helpers (Decision Comparison).
#
# Display-only. Sources target edges ONLY from the governed GREEN performance
# band (green_lower / green_upper boundaries). Amber / red boundaries and the
# Green / Amber / Red status engine are NEVER touched.
#
# Logic matches the rules already implemented on Executive Overview:
#   HIGHER_IS_BETTER   -> Target: ≥ green_lower_boundary
#   LOWER_IS_BETTER    -> Target: ≤ green_upper_boundary
#   TARGET_BAND        -> Target band: green_lower – green_upper
# The unit word is always spelled in full ("percentage points", never "pp").
# ---------------------------------------------------------------------------


def _gap_unit_word(unit: str) -> str:
    """Map a threshold-canonical unit to a management-friendly gap unit word."""
    u = (unit or "").strip().lower()
    if u == "percent":
        return "percentage points"
    if u == "minutes":
        return "minutes"
    if "likert" in u:
        return "Likert points"
    if "complaint" in u or "encounter" in u:
        return "per 1,000 encounters"
    return unit or "units"


def _build_target_card_html(kpi_id: str, threshold_cfg) -> str:
    """Render the standalone Target / Target Band card for the first comparison row."""
    cfg = threshold_cfg if isinstance(threshold_cfg, dict) else {}
    row = cfg.get(kpi_id) if kpi_id else None
    if not isinstance(row, dict):
        return (
            '<div class="s360-dec-card s360-dec-evidence-target">'
            '<div class="s360-dec-micro">Target</div>'
            '<div class="s360-dec-value">Not configured</div>'
            '<div class="s360-dec-caption">Governed target unavailable</div>'
            '</div>'
        )

    direction = (row.get("directionality") or "").strip().upper()
    lo = row.get("green_lower_boundary")
    hi = row.get("green_upper_boundary")
    unit = (row.get("unit") or "").strip()
    is_provisional = bool(row.get("threshold_is_provisional", False))

    if lo is None or hi is None:
        return (
            '<div class="s360-dec-card s360-dec-evidence-target">'
            '<div class="s360-dec-micro">Target</div>'
            '<div class="s360-dec-value">Not configured</div>'
            '<div class="s360-dec-caption">Governed target unavailable</div>'
            '</div>'
        )

    try:
        if direction == "HIGHER_IS_BETTER":
            target_line = f"≥ {format_unit_value(float(lo), unit)}"
            ruled_note = "Governed Green performance threshold"
            label = "Target"
        elif direction == "LOWER_IS_BETTER":
            target_line = f"≤ {format_unit_value(float(hi), unit)}"
            ruled_note = "Governed Green performance threshold"
            label = "Target"
        elif direction == "TARGET_BAND":
            target_line = (
                f"{format_unit_value(float(lo), unit)} – "
                f"{format_unit_value(float(hi), unit)}"
            )
            ruled_note = "Governed Green operating range"
            label = "Target Band"
        else:
            return (
                '<div class="s360-dec-card s360-dec-evidence-target">'
                '<div class="s360-dec-micro">Target</div>'
                '<div class="s360-dec-value">Not configured</div>'
                '<div class="s360-dec-caption">Governed target unavailable</div>'
                '</div>'
            )
    except Exception:
        return (
            '<div class="s360-dec-card s360-dec-evidence-target">'
            '<div class="s360-dec-micro">Target</div>'
            '<div class="s360-dec-value">Not configured</div>'
            '<div class="s360-dec-caption">Governed target unavailable</div>'
            '</div>'
        )

    provisional_cue = ""
    if is_provisional:
        provisional_cue = (
            '<div class="s360-dec-caption" '
            'style="margin-top:4px; font-style:italic; color:#6c7a92;">'
            'Provisional target</div>'
        )

    return (
        f'<div class="s360-dec-card s360-dec-evidence-target">'
        f'<div class="s360-dec-micro">{label}</div>'
        f'<div class="s360-dec-value">{target_line}</div>'
        f'<div class="s360-dec-caption">{ruled_note}</div>'
        f'{provisional_cue}'
        f'</div>'
    )


def _build_target_status_line(kpi_id: str, forecast_value, threshold_cfg) -> str:
    """Render a compact gap-to-target status line for the Do-Nothing Forecast.

    Returns "" if no governed threshold exists or the forecast value is missing.
    Never fabricates a number; surfaces "Not assessable" only when the
    underlying comparison is not derivable.
    """
    cfg = threshold_cfg if isinstance(threshold_cfg, dict) else {}
    row = cfg.get(kpi_id) if kpi_id else None
    if not isinstance(row, dict) or forecast_value is None:
        return ""

    direction = (row.get("directionality") or "").strip().upper()
    lo = row.get("green_lower_boundary")
    hi = row.get("green_upper_boundary")
    unit = (row.get("unit") or "").strip()
    if lo is None or hi is None:
        return ""

    gap_unit = _gap_unit_word(unit)
    try:
        v = float(forecast_value)
        if direction == "HIGHER_IS_BETTER":
            t = float(lo)
            if v >= t:
                status = "On target"
            else:
                status = f"{abs(t - v):.1f} {gap_unit} below target"
        elif direction == "LOWER_IS_BETTER":
            t = float(hi)
            if v <= t:
                status = "On target"
            else:
                status = f"{abs(v - t):.1f} {gap_unit} above target"
        elif direction == "TARGET_BAND":
            lo_f, hi_f = float(lo), float(hi)
            # Lower boundary inclusive, upper boundary exclusive.
            if lo_f <= v < hi_f:
                status = "Within target band"
            elif v < lo_f:
                status = f"{abs(lo_f - v):.1f} {gap_unit} below target band"
            else:
                status = f"{abs(v - hi_f):.1f} {gap_unit} above target band"
        else:
            return ""
    except (TypeError, ValueError):
        return ""

    return (
        '<div class="s360-dec-caption" '
        'style="margin-top:6px; color:#0288D1; font-weight:600;">'
        f'{status}</div>'
    )


# ---------------------------------------------------------------------------
# Read handoff
# ---------------------------------------------------------------------------
context: Optional[Dict[str, Any]] = st.session_state.get("decision_review_context")

# ---------------------------------------------------------------------------
# Render header
# ---------------------------------------------------------------------------
_render_header()

# ---------------------------------------------------------------------------
# Empty / unsupported state
# ---------------------------------------------------------------------------
if context is None:
    st.markdown(
        '<div class="s360-dec-empty-state">'
        '<div class="s360-dec-empty-title">NO DECISION CASE SELECTED</div>'
        '<div class="s360-dec-empty-help">Return to Simulation Lab, select a supported scenario, then use '
        '<strong>USE THIS SCENARIO FOR DECISION REVIEW</strong>.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.warning("NO DECISION CASE SELECTED")
    st.info(
        "Select and save a supported scenario in Simulation Lab, then choose "
        "'Use This Scenario for Decision Review'."
    )
    st.stop()

required_keys = [
    "hospital_id",
    "department_id",
    "kpi_id",
    "forecast_month_label",
    "selected_action_level",
    "action_strategy",
    "do_nothing_forecast",
    "scenario_kpi_value",
]
missing = [k for k in required_keys if context.get(k) is None]
if missing:
    st.markdown(
        '<div class="s360-dec-error-state">'
        '<div class="s360-dec-error-title">DECISION SUPPORT NOT AVAILABLE</div>'
        '<div class="s360-dec-error-help">The selected scenario does not contain sufficient supported evidence '
        'for management review.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.error("DECISION SUPPORT NOT AVAILABLE")
    st.info(
        "The selected scenario does not contain sufficient supported evidence for management review."
    )
    st.stop()

# ---------------------------------------------------------------------------
# Resolve display names
# ---------------------------------------------------------------------------
hospital_id = str(context.get("hospital_id", "HOSP-001"))
department_id = str(context.get("department_id", ""))
kpi_id = str(context.get("kpi_id", ""))
department_name = _resolve_department_name(department_id)
kpi_name = _resolve_kpi_name(kpi_id)
forecast_year = GOVERNED_ACTUAL_YEAR
forecast_month_label = str(context.get("forecast_month_label", ""))
action_strategy = str(context.get("action_strategy", ""))
selected_action_level = str(context.get("selected_action_level", ""))

# Map ACTUAL handoff keys to the variables used in the page.
# The Simulation Lab handoff uses: latest_actual_baseline, scenario_kpi_value,
# change, scenario_status, management_takeaway, intervention_id, comparator,
# and *_unit fields.
latest_actual = context.get("latest_actual_baseline")
do_nothing_forecast = context.get("do_nothing_forecast")
selected_scenario_value = context.get("scenario_kpi_value")
change_value = context.get("change")
# Derive change_pct locally only if both are present and denominator is non-zero.
_change_pct_raw = context.get("change_pct")
if _change_pct_raw is not None:
    change_pct = _change_pct_raw
elif change_value is not None and do_nothing_forecast not in (None, 0):
    change_pct = (change_value / do_nothing_forecast) * 100.0
else:
    change_pct = None
action_status = str(context.get("scenario_status", ""))
# action_detail and resource_line come from the live handoff directly so the
# Decision page shows the EXACT same text as Simulation Lab. Fall back to the
# older management_takeaway / intervention_id+comparator only if missing.
action_detail = str(
    context.get("action_detail")
    or context.get("management_takeaway")
    or ""
)
_resource_line_raw = context.get("resource_line")
if _resource_line_raw:
    resource_line = str(_resource_line_raw)
else:
    resource_line = str(
        f"{context.get('intervention_id', '')} — {context.get('comparator', '')}".strip(" —")
    )
confidence = str(context.get("confidence", ""))
confidence_pct = context.get("confidence_pct")
waiting_time_direction = str(context.get("waiting_time_direction", ""))

# ---------------------------------------------------------------------------
# Demo Decision Confidence lookup (read-only, governed by CSV)
# ---------------------------------------------------------------------------
# Context for the lookup comes directly from the existing Simulation Lab
# handoff. No new slicers, no new context logic. If the integer month is
# not present in the handoff, we pass None and the helper returns a
# structured unavailable result (NOT_CONFIGURED / INVALID_INPUT). We do
# NOT fall back to a previous month, a nearest row, or any inferred value.
try:
    _fm_raw = context.get("forecast_month")
    _forecast_month_int = int(_fm_raw) if _fm_raw is not None else None
except (TypeError, ValueError):
    _forecast_month_int = None
try:
    _forecast_year_int = int(forecast_year) if forecast_year is not None else None
except (TypeError, ValueError):
    _forecast_year_int = None

_confidence_result = get_decision_confidence(
    forecast_year=_forecast_year_int,
    forecast_month=_forecast_month_int,
    kpi_id=kpi_id,
)

# Prefer the actual unit carried in the handoff; fall back to KPI lookup.
unit = (
    context.get("latest_actual_unit")
    or context.get("do_nothing_unit")
    or context.get("scenario_unit")
    or _kpi_unit(kpi_id)
)

# Governed threshold config (display-only, mirrors the Executive Overview pipeline).
_threshold_cfg = load_kpi_threshold_config()
_target_card_html = _build_target_card_html(kpi_id, _threshold_cfg)
_do_nothing_target_status_html = _build_target_status_line(kpi_id, do_nothing_forecast, _threshold_cfg)

# ---------------------------------------------------------------------------
# Management Decision Review strip
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="s360-dec-strip">
        <div class="s360-dec-strip-title">Management Decision Review</div>
        <div class="s360-dec-strip-help">
            Review the selected scenario evidence, confirm the preferred action, and record management intent.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Decision Context
# ---------------------------------------------------------------------------
st.markdown('<div class="s360-dec-section-label">Decision Context</div>', unsafe_allow_html=True)
ctx_cols = st.columns(4)
with ctx_cols[0]:
    st.markdown(
        f"""
        <div class="s360-dec-card">
            <div class="s360-dec-micro">Hospital</div>
            <div class="s360-dec-value">{hospital_id}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with ctx_cols[1]:
    st.markdown(
        f"""
        <div class="s360-dec-card">
            <div class="s360-dec-micro">Department</div>
            <div class="s360-dec-value">{department_name}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with ctx_cols[2]:
    st.markdown(
        f"""
        <div class="s360-dec-card">
            <div class="s360-dec-micro">KPI</div>
            <div class="s360-dec-value">{kpi_name}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with ctx_cols[3]:
    st.markdown(
        f"""
        <div class="s360-dec-card">
            <div class="s360-dec-micro">Forecast Month</div>
            <div class="s360-dec-value">{forecast_month_label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Decision Comparison
# ---------------------------------------------------------------------------
st.markdown('<div class="s360-dec-section-label">Decision Comparison</div>', unsafe_allow_html=True)

_ev_cols = st.columns([2, 1, 2])
with _ev_cols[0]:
    # Display-only governed Target card. Latest-actual variables are
    # intentionally retained in the backend context but are NOT rendered here
    # so the comparison answers: "if management does nothing, where is
    # performance expected to land relative to the governed target?".
    st.markdown(_target_card_html, unsafe_allow_html=True)
with _ev_cols[1]:
    st.markdown(
        '<div class="s360-dec-arrow" style="color: #0288D1;">→</div>',
        unsafe_allow_html=True,
    )
with _ev_cols[2]:
    st.markdown(
        f"""
        <div class="s360-dec-card s360-dec-evidence-forecast">
            <div class="s360-dec-micro">Do-Nothing Forecast</div>
            <div class="s360-dec-value">{format_unit_value(do_nothing_forecast, unit)}</div>
            <div class="s360-dec-caption">{forecast_month_label}</div>
            {_do_nothing_target_status_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

_ev2_cols = st.columns([2, 1, 2])
with _ev2_cols[0]:
    st.markdown(
        f"""
        <div class="s360-dec-card s360-dec-evidence-forecast">
            <div class="s360-dec-micro">Do-Nothing Forecast</div>
            <div class="s360-dec-value">{format_unit_value(do_nothing_forecast, unit)}</div>
            <div class="s360-dec-caption">{forecast_month_label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with _ev2_cols[1]:
    st.markdown(
        '<div class="s360-dec-arrow" style="color: #0288D1;">→</div>',
        unsafe_allow_html=True,
    )
with _ev2_cols[2]:
    st.markdown(
        f"""
        <div class="s360-dec-card s360-dec-evidence-scenario">
            <div class="s360-dec-micro">Selected Scenario</div>
            <div class="s360-dec-value">{format_unit_value(selected_scenario_value, unit)}</div>
            <div class="s360-dec-caption">{selected_action_level}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Expected Impact
# ---------------------------------------------------------------------------
st.markdown('<div class="s360-dec-section-label">Expected Impact</div>', unsafe_allow_html=True)

impact_cols = st.columns(2)
with impact_cols[0]:
    st.markdown(
        f"""
        <div class="s360-dec-card s360-dec-impact-card">
            <div class="s360-dec-micro">Expected KPI Change</div>
            <div class="s360-dec-value">{format_unit_value(change_value, unit)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with impact_cols[1]:
    st.markdown(
        f"""
        <div class="s360-dec-card s360-dec-impact-card">
            <div class="s360-dec-micro">Relative Change</div>
            <div class="s360-dec-value">{format_unit_value(change_pct, "%")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# AI-Assisted Decision Impact Interpretation
# ---------------------------------------------------------------------------
dec_evidence = build_decision_impact_evidence(
    hospital_id=hospital_id,
    department_name=department_name,
    kpi_id=kpi_id,
    kpi_name=kpi_name,
    forecast_month_label=forecast_month_label,
    do_nothing_forecast=do_nothing_forecast,
    selected_scenario_value=selected_scenario_value,
    change_value=change_value,
    change_pct=change_pct,
    action_strategy=action_strategy,
    resource_line=resource_line,
    selected_action_level=selected_action_level,
    threshold_cfg=_threshold_cfg,
    unit=unit,
)

dec_result = _get_decision_impact(
    dec_evidence,
    kpi_id=kpi_id,
    department_id=department_id,
    forecast_month_label=forecast_month_label,
)

_render_decision_impact(dec_result)

if kpi_id == "kpi_004" and waiting_time_direction:
    st.info("Lower waiting time is better.")

# ---------------------------------------------------------------------------
# Action Commitment
# Recommended Action card
# ---------------------------------------------------------------------------
st.markdown('<div class="s360-dec-section-label">Recommended Action</div>', unsafe_allow_html=True)

st.markdown(
    f"""
    <div class="s360-dec-action-card">
        <div class="s360-dec-action-headline">{action_detail or "—"}</div>
        <div class="s360-dec-meta-row">
            <div class="s360-dec-meta-item">
                <div class="s360-dec-meta-label">Action Strategy</div>
                <div class="s360-dec-meta-value">{action_strategy}</div>
            </div>
            <div class="s360-dec-meta-item">
                <div class="s360-dec-meta-label">Selected Action Level</div>
                <div class="s360-dec-meta-value">{selected_action_level}</div>
            </div>
            <div class="s360-dec-meta-item">
                <div class="s360-dec-meta-label">Resource Commitment</div>
                <div class="s360-dec-meta-value">{resource_line or "—"}</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Decision Confidence (Demo Governance)
# ---------------------------------------------------------------------------
# Replaces the previous two-card "Confidence / Confidence Score" block.
# Underlying analytical `confidence` and `confidence_pct` variables are
# intentionally left untouched and remain available to the rest of the
# page. Only the visible UI is updated.
st.markdown(
    '<div class="s360-dec-section-label">Decision Confidence</div>',
    unsafe_allow_html=True,
)

if _confidence_result.status == "OK":
    _level = str(_confidence_result.confidence_level or "—").strip()
    _posture = str(_confidence_result.decision_posture or "—").strip()
    _implication = str(_confidence_result.decision_implication or "—").strip()
    _action = str(_confidence_result.evidence_action or "—").strip()
    _pill_class = _confidence_pill_class(_level)
    _card_class = _confidence_card_class(_level)
    # _posture is intentionally retained for potential future use but is
    # not rendered in this card (the section already shows the posture
    # context, and the decision_implication is shown in the grid below).
    st.markdown(
        f"""
        <div class="s360-dec-card s360-dec-confidence-card {_card_class}">
            <div class="s360-dec-confidence-head">
                <span class="s360-dec-confidence-pill {_pill_class}">
                    <span class="s360-dec-cf-dot"></span>
                    {_level}
                </span>
            </div>
            <div class="s360-dec-confidence-grid">
                <div class="s360-dec-confidence-block">
                    <div class="s360-dec-micro">Decision Implication</div>
                    <div class="s360-dec-confidence-block-body">{_implication}</div>
                </div>
                <div class="s360-dec-confidence-block">
                    <div class="s360-dec-micro">Evidence Action</div>
                    <div class="s360-dec-confidence-block-body">{_action}</div>
                </div>
            </div>
            <div class="s360-dec-confidence-foot">Indicative Decision Confidence — Demo Governance</div>
            <div class="s360-dec-confidence-help">This is a prototype governance mapping, not a statistical confidence score.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    _msg = str(
        _confidence_result.message
        or "Decision confidence is not configured for the selected context."
    )
    st.markdown(
        f"""
        <div class="s360-dec-card s360-dec-confidence-card s360-dec-cf-unavailable">
            <div class="s360-dec-confidence-head">
                <span class="s360-dec-confidence-pill s360-dec-pill-muted">
                    <span class="s360-dec-cf-dot"></span>
                    N/A
                </span>
            </div>
            <div class="s360-dec-confidence-empty">Decision confidence is not configured for the selected context.</div>
            <div class="s360-dec-confidence-empty-help">{_msg}</div>
            <div class="s360-dec-confidence-foot">Indicative Decision Confidence — Demo Governance</div>
            <div class="s360-dec-confidence-help">This is a prototype governance mapping, not a statistical confidence score.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Management Decision
# ---------------------------------------------------------------------------
st.markdown('<div class="s360-dec-section-label">Management Decision</div>', unsafe_allow_html=True)

if "management_decision_record" not in st.session_state:
    st.session_state["management_decision_record"] = None

existing_record: Optional[Dict[str, Any]] = st.session_state.get("management_decision_record")

# If a record already exists for this exact context, pre-select it
preselected: Optional[str] = None
pre_note: str = ""
if existing_record is not None:
    if (
        existing_record.get("hospital_id") == hospital_id
        and existing_record.get("department_id") == department_id
        and existing_record.get("kpi_id") == kpi_id
        and existing_record.get("forecast_month_label") == forecast_month_label
        and existing_record.get("selected_action_level") == selected_action_level
    ):
        preselected = existing_record.get("management_decision")
        pre_note = existing_record.get("management_note", "")

decision_options = ["APPROVE", "REVISION REQUIRED", "DEFER", "NOT APPROVED"]

st.markdown(
    """
    <div class="s360-dec-decision-legend">
        <div class="s360-dec-legend-chip s360-dec-legend-approve">APPROVE</div>
        <div class="s360-dec-legend-chip s360-dec-legend-revision">REVISION REQUIRED</div>
        <div class="s360-dec-legend-chip s360-dec-legend-defer">DEFER</div>
        <div class="s360-dec-legend-chip s360-dec-legend-not-approved">NOT APPROVED</div>
    </div>
    """,
    unsafe_allow_html=True,
)

decision = st.radio(
    "Select management decision",
    options=decision_options,
    index=decision_options.index(preselected) if preselected in decision_options else 0,
    horizontal=True,
)

# Selected indicator chip
_chip_colors = {
    "APPROVE": ("#E6F4EA", "#1B5E20", "APPROVED FOR ACTION PLANNING"),
    "REVISION REQUIRED": ("#FFF4E5", "#B45309", "REVISION REQUIRED"),
    "DEFER": ("#EAF4FF", "#2F80ED", "DEFERRED"),
    "NOT APPROVED": ("#FDECEA", "#B71C1C", "NOT APPROVED"),
}
if decision in _chip_colors:
    bg, fg, label = _chip_colors[decision]
    st.markdown(
        f'<div class="s360-dec-selected-chip" style="background:{bg}; color:{fg};">SELECTED: {label}</div>',
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Management Note
# ---------------------------------------------------------------------------
st.markdown('<div class="s360-dec-section-label">Management Note</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="s360-dec-caption" style="margin-bottom:10px;">'
    "Optional rationale, conditions, or follow-up requirements.</div>",
    unsafe_allow_html=True,
)
management_note = st.text_area(
    "Management Note",
    value=pre_note,
    placeholder="Add decision rationale, conditions, or follow-up instructions…",
    label_visibility="collapsed",
)

# ---------------------------------------------------------------------------
# Record Decision CTA
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="s360-dec-cta">
        <div class="s360-dec-cta-title">Ready to Record Management Decision?</div>
        <div class="s360-dec-cta-help">Confirm the selected management intent for this scenario.</div>
    </div>
    """,
    unsafe_allow_html=True,
)
if st.button("RECORD MANAGEMENT DECISION", type="primary"):
    record = {
        "hospital_id": hospital_id,
        "department_id": department_id,
        "department_name": department_name,
        "kpi_id": kpi_id,
        "kpi_name": kpi_name,
        "forecast_month_label": forecast_month_label,
        "action_strategy": action_strategy,
        "selected_action_level": selected_action_level,
        "latest_actual": latest_actual,
        "do_nothing_forecast": do_nothing_forecast,
        "selected_scenario_value": selected_scenario_value,
        "change_value": change_value,
        "change_pct": change_pct,
        "action_status": action_status,
        "confidence": confidence,
        "confidence_pct": confidence_pct,
        "management_decision": decision,
        "management_note": management_note,
        "decision_status": _decision_status_text(decision),
        "decision_timestamp": datetime.datetime.now().isoformat(),
    }
    st.session_state["management_decision_record"] = record
    st.success(f"Decision recorded: {_decision_status_text(decision)}")

# ---------------------------------------------------------------------------
# Decision Status
# ---------------------------------------------------------------------------
st.markdown('<div class="s360-dec-section-label">Decision Status</div>', unsafe_allow_html=True)

if existing_record is not None:
    status_text = existing_record.get("decision_status", "PENDING MANAGEMENT REVIEW")
    status_class = _status_css_class(status_text)
    st.markdown(
        f'<div class="s360-dec-status-chip {status_class}">{status_text}</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="s360-dec-status-chip s360-dec-status-pending">PENDING MANAGEMENT REVIEW</div>',
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Decision Record Summary
# ---------------------------------------------------------------------------
if existing_record is not None:
    st.markdown('<div class="s360-dec-section-label">Decision Record Summary</div>', unsafe_allow_html=True)
    rec = existing_record
    rec_recommended = f"{rec.get('action_strategy', '—')} — {rec.get('selected_action_level', '—')}"
    rec_timestamp = rec.get("decision_timestamp", "—")
    # Format timestamp to a readable string if it's ISO
    if rec_timestamp != "—":
        try:
            rec_timestamp = datetime.datetime.fromisoformat(rec_timestamp).strftime("%Y-%m-%d %H:%M")
        except Exception:
            pass

    rec_rows = [
        ("Decision", rec.get("management_decision", "—")),
        ("Decision Status", rec.get("decision_status", "—")),
        ("Hospital", rec.get("hospital_id", "—")),
        ("Department", rec.get("department_name", rec.get("department_id", "—"))),
        ("KPI", rec.get("kpi_name", rec.get("kpi_id", "—"))),
        ("Forecast Month", rec.get("forecast_month_label", "—")),
        ("Recommended Action", rec_recommended),
        ("Action Strategy", rec.get("action_strategy", "—")),
        ("Selected Action Level", rec.get("selected_action_level", "—")),
        ("Expected KPI Impact", format_unit_value(rec.get("change_value"), unit)),
        ("Resource Commitment", rec.get("management_note", "—")),
        ("Confidence", rec.get("confidence", "—")),
        ("Management Note", rec.get("management_note", "—")),
        ("Recorded Timestamp", rec_timestamp),
    ]

    rows_html = ""
    for label, value in rec_rows:
        rows_html += (
            f'<div class="s360-dec-record-row">'
            f'<div><span class="s360-dec-record-label">{label}</span></div>'
            f'<div class="s360-dec-record-value">{value}</div>'
            f'</div>'
        )

    st.markdown(
        f'<div class="s360-dec-record-card">{rows_html}</div>',
        unsafe_allow_html=True,
    )
