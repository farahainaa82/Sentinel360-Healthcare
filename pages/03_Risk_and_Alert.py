"""
03_Risk_and_Alert.py — Phase 3C

Executive Risk & Alert page.

UI redesigned to match the Sentinel360 Healthcare design system used on the
homepage and Executive Overview. No changes to risk logic, KPI calculations,
warning classifications, forecast values, filters, session state, datasets,
or analytical engines. The visual presentation only is being refactored.
"""

from __future__ import annotations

import base64
import calendar
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.s360_sidebar_chrome import render_sidebar_chrome  # noqa: E402

from src.risk_alert_controller import (  # noqa: E402
    WARNING_PRIORITY_RANK,
    build_management_interpretation,
    build_risk_alert_state,
    build_risk_progression,
    build_selected_risk_detail,
    build_suggested_action_card,
    get_excluded_dept_ids,
    get_filter_options,
    render_selected_risk_chart,
)
from src.streamlit_executive_data_loader import (  # noqa: E402
    get_kpi_monthly_actual_table,
    load_kpi_daily,
    load_kpi_forecast_warning_signals,
    load_kpi_monthly_forecast,
)
from src.simulation_lab_controller import (  # noqa: E402
    _SUPPORTED_KPI_IDS,
)
from src.streamlit_executive_page_controller import (  # noqa: E402
    format_unit_value,
    load_kpi_threshold_config,
)

PAGE_KEY = "risk_alert_page"
_PRIORITY_KEY = f"{PAGE_KEY}_selected_priority"

# Severity colour tokens used for progression status dots
_SEVERITY_BORDER = {
    "red": "#dc3545",
    "amber": "#ffc107",
    "green": "#28a745",
    "grey": "#6c757d",
}

# Action text strings that indicate a "no real intervention" state
_NEUTRAL_ACTION_TEXT = (
    "No matching intervention found",
    "Preventive action requires management review.",
)


# ---------------------------------------------------------------------------
# Logo helper — same working pattern as app.py / Executive Overview
# ---------------------------------------------------------------------------
def _logo_data_uri(filename: str) -> str:
    # Page file lives in pages/, so assets/ is one level up at the project root
    path = Path(__file__).parent.parent / "assets" / filename
    if not path.exists():
        return ""
    return f"data:image/png;base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
def _init_session_state() -> None:
    defaults = {
        "risk_alert_selected_department": "DEPT-ICU",
        "risk_alert_selected_year": 2025,
        "risk_alert_selected_month": 12,  # default to a forecast month
        _PRIORITY_KEY: 1,
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


# ---------------------------------------------------------------------------
# Self-contained CSS — Sentinel360 design system
# ---------------------------------------------------------------------------
_CSS = """
<style>
/* Page background and base typography */
.stApp { background: #F5F7FA; }
html, body, [class*="css"]  { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }

/* ---- Navy branded header (matches homepage / Executive Overview) ---- */
.s360-risk-header {
    background: #0B1E3D;
    height: 130px;
    padding: 0 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    box-sizing: border-box;
    border-radius: 0 0 8px 8px;
}
.s360-risk-header-left { display: flex; flex-direction: column; justify-content: center; gap: 6px; }
.s360-risk-header-brand { display: flex; align-items: center; gap: 10px; }
.s360-risk-header-brand-name {
    font-size: 30px; font-weight: 700; color: #ffffff;
    letter-spacing: -0.5px; line-height: 1;
}
.s360-risk-header-version {
    border: 1px solid #0288D1; color: #0288D1; background: transparent;
    font-size: 11px; font-weight: 500; border-radius: 4px;
    padding: 3px 8px; line-height: 1;
}
.s360-risk-header-page-title {
    font-size: 20px; font-weight: 600; color: #ffffff; line-height: 1; margin-top: 2px;
}
.s360-risk-header-subtitle {
    font-size: 13px; font-weight: 400; color: rgba(255,255,255,0.72); line-height: 1;
}
.s360-risk-header-right { display: flex; flex-direction: row; align-items: center; gap: 14px; }
.s360-risk-logo-cell {
    background: #ffffff; padding: 8px 10px; border-radius: 6px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.22);
    display: flex; align-items: center; justify-content: center;
    height: 64px; box-sizing: border-box;
}
.s360-risk-logo-cell.jcorp { width: 76px; }
.s360-risk-logo-cell.bsp   { width: 108px; }
.s360-risk-logo-cell img { max-width: 100%; max-height: 48px; display: block; }

/* Page body wrapper */
.s360-risk-page { padding: 0 4px; }

/* ---- Filter bar ---- */
.s360-risk-filter-bar {
    background: #ffffff; border: 1px solid #DDE3EC; border-radius: 8px;
    padding: 12px 14px; box-shadow: 0 1px 4px rgba(0,0,0,0.03);
    margin: 4px 0 6px 0;
}
.s360-risk-filter-bar [data-testid="stWidgetLabel"] label,
.s360-risk-filter-bar .stSelectbox label {
    font-size: 0.7rem !important; font-weight: 600 !important;
    color: #4A5568 !important; text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}
.s360-risk-filter-excluded {
    font-size: 0.7rem; color: #718096; margin-top: 6px; font-style: italic;
}

/* ---- Section labels (page hierarchy) ---- */
.s360-risk-section-label {
    font-size: 16px; font-weight: 800; color: #0B1E3D;
    text-transform: uppercase; letter-spacing: 0.9px;
    margin: 22px 0 12px 0; padding-bottom: 7px;
    border-bottom: 1px solid #DDE3EC;
    line-height: 1.2;
}

/* ---- Top Risk Summary cards (4 tinted variants) ---- */
.s360-risk-summary-grid {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;
    margin: 4px 0 6px 0;
}
@media (max-width: 980px) {
    .s360-risk-summary-grid { grid-template-columns: repeat(2, 1fr); }
}
.s360-risk-summary-card {
    border: 1px solid #DDE3EC; border-left-width: 4px; border-left-style: solid;
    border-radius: 8px; padding: 12px 14px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.03);
}
.s360-risk-summary-card .label {
    font-size: 0.66rem; font-weight: 700; color: #4A5568;
    text-transform: uppercase; letter-spacing: 0.6px;
}
.s360-risk-summary-card .value {
    font-size: 1.7rem; font-weight: 700; color: #1A2B47;
    margin-top: 4px; line-height: 1.1;
}
.s360-risk-summary-card .meta {
    font-size: 0.7rem; color: #718096; margin-top: 6px; line-height: 1.4;
}
.s360-risk-summary-card.actual-risks   { background: #EAF4FF; border-left-color: #2F80ED; }
.s360-risk-summary-card.emerging-risks { background: #EEF3F8; border-left-color: #7C8EA3; }
.s360-risk-summary-card.high-warnings  { background: #FFF4E5; border-left-color: #F59E0B; }
.s360-risk-summary-card.dept-risks     { background: #EAF8F4; border-left-color: #2E9F6B; }
/* Text-value variant (HIGHEST WARNING LEVEL) — smaller value font so labels fit */
.s360-risk-summary-card.text-value .value {
    font-size: 1.0rem; font-weight: 700; line-height: 1.15;
    letter-spacing: 0.2px;
}

/* ---- Generic white panel (table, selector, etc.) ---- */
.s360-risk-panel {
    background: #ffffff; border: 1px solid #DDE3EC; border-radius: 8px;
    padding: 12px 14px; box-shadow: 0 1px 4px rgba(0,0,0,0.03);
    margin-top: 4px;
}

/* ---- Selected Risk selector ---- */
.s360-risk-selector-panel { margin-top: 4px; }
.s360-risk-selector-panel [data-testid="stWidgetLabel"] label,
.s360-risk-selector-panel .stSelectbox label {
    font-size: 0.7rem !important; font-weight: 600 !important;
    color: #4A5568 !important; text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

/* ---- Highlighted interactive slicer (Selected Risk) ---- */
.s360-risk-selector-highlight {
    background: #EAF4FF;
    border: 1px solid #B8CCE3;
    border-left: 3px solid #0288D1;
    border-radius: 8px;
    padding: 12px 14px 10px 14px;
    margin: 4px 0 8px 0;
    box-shadow: 0 1px 4px rgba(2, 136, 209, 0.08);
    box-sizing: border-box;
}
.s360-risk-selector-helper-label {
    font-size: 0.7rem; font-weight: 800; color: #0288D1;
    text-transform: uppercase; letter-spacing: 0.9px;
    margin: 0 0 4px 0;
    display: flex; align-items: center; gap: 7px;
    line-height: 1.2;
}
.s360-risk-selector-helper-label .dot {
    width: 8px; height: 8px; border-radius: 50%; background: #0288D1;
    display: inline-block; flex-shrink: 0;
}
.s360-risk-selector-helper-text {
    font-size: 0.75rem; color: #4A5568; margin: 0 0 8px 0;
    line-height: 1.45;
}
.s360-risk-selector-highlight [data-testid="stWidgetLabel"] label,
.s360-risk-selector-highlight .stSelectbox label {
    font-size: 0.7rem !important; font-weight: 600 !important;
    color: #4A5568 !important; text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

/* ---- Bold Selected Risk selectbox (slicer control itself) ---- */
.s360-risk-selector-highlight [data-testid="stSelectbox"] [data-baseweb="select"] > div,
.s360-risk-selector-highlight [data-testid="stSelectbox"] [role="combobox"] {
    background: #FFFFFF !important;
    border: 2px solid #0288D1 !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08) !important;
    min-height: 44px !important;
    padding: 10px 14px !important;
    box-sizing: border-box !important;
    transition: border-color 120ms ease, box-shadow 120ms ease;
}
.s360-risk-selector-highlight [data-testid="stSelectbox"] [data-baseweb="select"] > div:hover,
.s360-risk-selector-highlight [data-testid="stSelectbox"] [role="combobox"]:hover {
    border-color: #01579B !important;
    box-shadow: 0 2px 6px rgba(2, 136, 209, 0.18) !important;
}
.s360-risk-selector-highlight [data-testid="stSelectbox"] [data-baseweb="select"] > div > *,
.s360-risk-selector-highlight [data-testid="stSelectbox"] [role="combobox"] > * {
    font-weight: 700 !important;
    font-size: 15px !important;
    color: #1A2B47 !important;
    line-height: 1.3 !important;
}
.s360-risk-selector-highlight [data-testid="stSelectbox"] [data-baseweb="select"] svg,
.s360-risk-selector-highlight [data-testid="stSelectbox"] [role="combobox"] svg {
    color: #0288D1 !important;
    opacity: 1 !important;
    width: 18px !important;
    height: 18px !important;
}

/* ---- Selected risk detail grid (Historical + Forecast) ---- */
.s360-risk-detail-grid {
    display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 6px;
}
@media (max-width: 880px) {
    .s360-risk-detail-grid { grid-template-columns: 1fr; }
}
.s360-risk-detail-block {
    background: #ffffff; border: 1px solid #DDE3EC; border-radius: 8px;
    padding: 12px 14px; box-shadow: 0 1px 4px rgba(0,0,0,0.03);
}
.s360-risk-detail-block .title {
    font-size: 0.66rem; color: #4A5568; text-transform: uppercase;
    letter-spacing: 0.6px; font-weight: 700;
}
.s360-risk-detail-block .value {
    font-size: 1.4rem; font-weight: 700; color: #1A2B47;
    margin-top: 6px; line-height: 1.1;
}
.s360-risk-detail-block .meta {
    font-size: 0.72rem; color: #718096; margin-top: 6px; line-height: 1.4;
}
.s360-risk-baseline-line {
    display: inline-block; font-size: 0.72rem; color: #1565C0; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.6px;
    margin-top: 8px; padding: 3px 8px; background: #E3F0FF;
    border-left: 3px solid #0d6efd; border-radius: 3px;
}

/* ---- Governed Target / Target Band card (neutral treatment) ---- */
.s360-risk-target-card {
    background: #FFFFFF;
    border: 1px solid #CFD8DC;
    border-left: 4px solid #0288D1;
    border-radius: 8px;
    padding: 12px 14px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.03);
    box-sizing: border-box;
}
.s360-risk-target-card .title {
    font-size: 0.66rem; color: #37474F; text-transform: uppercase;
    letter-spacing: 0.6px; font-weight: 700;
}
.s360-risk-target-card .value {
    font-size: 1.45rem; font-weight: 700; color: #0B1E3D;
    margin-top: 6px; line-height: 1.15;
}
.s360-risk-target-card .meta {
    font-size: 0.72rem; color: #546E7A; margin-top: 6px; line-height: 1.4;
}
.s360-risk-target-card .provisional {
    font-size: 0.72rem; color: #6A1B9A; margin-top: 6px;
}

/* ---- Compact gap-to-target line on Forecast card ---- */
.s360-risk-forecast-gap {
    font-size: 0.78rem;
    margin-top: 6px;
    color: #1A2B47;
}
.s360-risk-forecast-gap .gap-on {
    color: #2E7D32; font-weight: 700;
}
.s360-risk-forecast-gap .gap-off {
    color: #C62828; font-weight: 700;
}
.s360-risk-forecast-gap .gap-band {
    color: #1565C0; font-weight: 700;
}
.s360-risk-forecast-gap .gap-empty {
    color: #6A1B9A; font-style: italic; font-weight: 600;
}

/* ---- Forecast card (light professional treatment, not full saturated blue) ---- */
.s360-risk-forecast-card {
    background: #EAF4FF; border: 1px solid #BBDEFB; border-left: 4px solid #0d6efd;
    border-radius: 8px; padding: 12px 14px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.03);
}
.s360-risk-forecast-card .title {
    font-size: 0.66rem; color: #1565C0; text-transform: uppercase;
    letter-spacing: 0.6px; font-weight: 700;
}
.s360-risk-forecast-card .value {
    font-size: 1.55rem; font-weight: 700; color: #0B1E3D;
    margin-top: 6px; line-height: 1.1;
}
.s360-risk-forecast-card .meta {
    font-size: 0.72rem; color: #4A5568; margin-top: 6px; line-height: 1.4;
}
.s360-risk-forecast-card .warning-pill {
    display: inline-block; font-size: 0.7rem; font-weight: 700;
    padding: 3px 9px; margin-top: 8px; border-radius: 999px;
    border: 1px solid transparent;
}
.s360-risk-forecast-card .warning-pill.sev-red   { background: #FDECEA; color: #B71C1C; border-color: #F5C6CB; }
.s360-risk-forecast-card .warning-pill.sev-amber { background: #FFF4E5; color: #B45309; border-color: #FCD9A8; }
.s360-risk-forecast-card .warning-pill.sev-green { background: #E6F4EA; color: #1B5E20; border-color: #C8E6C9; }
.s360-risk-forecast-card .warning-pill.sev-grey  { background: #EDF2F7; color: #4A5568; border-color: #DDE3EC; }

/* ---- Chart panel (preserved production chart) ---- */
.s360-risk-chart-panel {
    background: #ffffff; border: 1px solid #DDE3EC; border-radius: 8px;
    padding: 12px 14px; box-shadow: 0 1px 4px rgba(0,0,0,0.03);
    margin-top: 4px;
}

/* ---- Risk Progression strip ---- */
.s360-risk-progression { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; padding: 6px 0; }
.s360-risk-progression .month {
    display: inline-flex; flex-direction: column; align-items: center;
    padding: 6px 6px; border: 1px solid #DDE3EC; border-radius: 6px;
    min-width: 60px; background: #ffffff;
}
.s360-risk-progression .month.actual   { background: #ffffff; }
.s360-risk-progression .month.forecast { background: #F5F7FA; border-style: dashed; }
.s360-risk-progression .month .label {
    font-size: 0.65rem; color: #4A5568; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.4px;
}
.s360-risk-progression .month .dot { width: 12px; height: 12px; border-radius: 50%; margin: 4px 0; }
.s360-risk-progression .month .value { font-size: 0.68rem; color: #1A2B47; font-weight: 600; }
.s360-risk-progression .month .badge {
    font-size: 0.55rem; color: #718096; text-transform: uppercase;
    letter-spacing: 0.4px; margin-top: 1px;
}

/* ---- Management interpretation card ---- */
.s360-risk-interpretation {
    background: #F0F7FF; border: 1px solid #DDE3EC; border-left: 4px solid #0288D1;
    border-radius: 6px; padding: 12px 14px; margin-top: 4px;
    font-size: 0.85rem; color: #1A2B47; line-height: 1.55;
}

/* ---- Suggested Preventive Action card ---- */
.s360-risk-action {
    background: #ffffff; border: 1px solid #DDE3EC; border-left: 4px solid #0288D1;
    border-radius: 8px; padding: 14px 16px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.03);
    margin-top: 4px;
}
.s360-risk-action .title {
    font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.6px;
    color: #1565C0; font-weight: 700;
}
.s360-risk-action .action {
    font-size: 1.0rem; font-weight: 600; color: #1A2B47;
    margin-top: 8px; line-height: 1.4;
}
.s360-risk-action .why {
    font-size: 0.8rem; color: #4A5568; margin-top: 8px; line-height: 1.5;
}
.s360-risk-action .status {
    font-size: 0.7rem; color: #718096; margin-top: 10px;
    font-style: italic; padding-top: 6px;
    border-top: 1px dashed #EDF2F7;
}
.s360-risk-action.neutral { background: #F5F7FA; border-left-color: #718096; }
.s360-risk-action.neutral .title { color: #4A5568; }
.s360-risk-action.neutral .action { color: #4A5568; font-style: italic; }
.s360-risk-action .context {
    font-size: 0.78rem; color: #4A5568; margin-top: 8px; line-height: 1.4;
    font-style: italic;
}

/* ---- Footer note ---- */
.s360-page-scope-note {
    color: #718096; font-size: 0.72rem; font-style: italic;
    margin-top: 18px; padding: 10px 12px;
    border-top: 1px solid #EDF2F7;
}
.s360-no-traceback-note {
    color: #718096; font-size: 0.72rem; font-style: italic; margin-top: 8px;
}
</style>
"""


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
def _render_header(jcorp_uri: str, bsp_uri: str) -> None:
    st.markdown(
        f"""
<div class="s360-risk-header">
    <div class="s360-risk-header-left">
        <div class="s360-risk-header-brand">
            <span class="s360-risk-header-brand-name">Sentinel360 Healthcare</span>
            <span class="s360-risk-header-version">1.0</span>
        </div>
        <div class="s360-risk-header-page-title">Risk &amp; Alert</div>
        <div class="s360-risk-header-subtitle">Intelligent Early Warning System for Organisational Performance</div>
    </div>
    <div class="s360-risk-header-right">
        <div class="s360-risk-logo-cell jcorp">
            <img src="{jcorp_uri}" alt="JCORP" />
        </div>
        <div class="s360-risk-logo-cell bsp">
            <img src="{bsp_uri}" alt="Black Swan Protocol" />
        </div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Summary cards
# ---------------------------------------------------------------------------
def _render_summary_cards(summary: dict, internal_rows: list) -> None:
    # Card 1 — KPIs AT RISK: distinct KPI count from Priority Risk Table
    # (matches the row set shown in the Priority Risk Table)
    _RISK_STATUSES = ("Red", "Amber")
    _RISK_WARNINGS = (
        "Emerging Warning",
        "Escalating Warning",
        "High Early Warning",
    )
    kpi_ids_at_risk: set = set()
    for r in internal_rows or []:
        status = str(r.get("actual_status", ""))
        warning = str(r.get("warning_level", ""))
        kpi_id = r.get("kpi_id")
        if status in _RISK_STATUSES or warning in _RISK_WARNINGS:
            if kpi_id:
                kpi_ids_at_risk.add(kpi_id)
    kpis_at_risk = len(kpi_ids_at_risk)

    # Card 2 — EMERGING FORECAST RISKS: distinct KPIs classified exactly as
    # "Emerging Warning" (does NOT include Escalating or High Early Warning,
    # which are reported on the separate HIGH / ESCALATING WARNINGS card).
    _EMERGING_ONLY = ("Emerging Warning",)
    emerging_kpi_ids: set = set()
    for r in internal_rows or []:
        lvl = str(r.get("warning_level", ""))
        kpi_id = r.get("kpi_id")
        if lvl in _EMERGING_ONLY and kpi_id:
            emerging_kpi_ids.add(kpi_id)
    emerging_forecast_risks = len(emerging_kpi_ids)

    # Card 4 — HIGHEST WARNING LEVEL: most severe warning in Priority Risk Table
    # (rank 0 = most severe per WARNING_PRIORITY_RANK; tie-break by first-seen)
    supported_levels = []
    for r in internal_rows or []:
        lvl = str(r.get("warning_level", ""))
        if lvl in WARNING_PRIORITY_RANK:
            supported_levels.append(lvl)
    if supported_levels:
        highest_warning = min(supported_levels, key=lambda lv: WARNING_PRIORITY_RANK[lv])
    else:
        highest_warning = "No Active Warning"

    cards = [
        ("KPIs AT RISK", kpis_at_risk,
         "Distinct KPIs in Red/Amber actual status or with an active warning",
         "actual-risks"),
        ("Emerging Forecast Risks", emerging_forecast_risks,
         "Forecast KPIs newly showing an Emerging Warning signal",
         "emerging-risks"),
        ("High / Escalating Warnings", summary.get("high_or_escalating_warnings", 0),
         "Forecasts classified as Escalating or High Early Warning",
         "high-warnings"),
        ("HIGHEST WARNING LEVEL", highest_warning,
         "Most severe warning present in the Priority Risk Table",
         "dept-risks text-value"),
    ]
    html = '<div class="s360-risk-summary-grid">'
    for label, value, hint, variant in cards:
        html += (
            f'<div class="s360-risk-summary-card {variant}">'
            f'<div class="label">{label}</div>'
            f'<div class="value">{value}</div>'
            f'<div class="meta">{hint}</div>'
            f'</div>'
        )
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Priority risk table
# ---------------------------------------------------------------------------
def _render_priority_table(table: pd.DataFrame) -> None:
    st.markdown(
        '<div class="s360-risk-section-label">Priority Risk Table</div>',
        unsafe_allow_html=True,
    )
    if table.empty:
        st.markdown(
            '<div class="s360-risk-panel">'
            '<div class="s360-no-traceback-note">No governed risks identified for the selected context.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        return
    st.markdown('<div class="s360-risk-panel">', unsafe_allow_html=True)
    st.dataframe(table.reset_index(drop=True), use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Selected risk selector
# ---------------------------------------------------------------------------
def _select_priority_row(table: pd.DataFrame) -> Optional[int]:
    st.markdown(
        '<div class="s360-risk-section-label">Selected Risk</div>',
        unsafe_allow_html=True,
    )
    if table.empty:
        st.markdown(
            '<div class="s360-risk-panel">'
            '<div class="s360-no-traceback-note">Select a department and review month to drill into a risk.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        return None
    # Open highlighted interactive slicer container
    st.markdown(
        '<div class="s360-risk-selector-highlight">'
        '<div class="s360-risk-selector-helper-label">'
        '<span class="dot"></span>Select Risk to Inspect</div>'
        '<div class="s360-risk-selector-helper-text">'
        'Choose one priority risk from the table above to investigate in detail.'
        '</div>',
        unsafe_allow_html=True,
    )
    options = list(range(1, len(table) + 1))
    default_idx = st.session_state.get(_PRIORITY_KEY, 1)
    if default_idx not in options:
        default_idx = options[0]
    selected = st.selectbox(
        "Choose a priority row to inspect",
        options=options,
        index=options.index(default_idx),
        format_func=lambda p: (
            f"#{p} — "
            f"{table.iloc[p - 1]['KPI']} "
            f"({table.iloc[p - 1]['Department']}) "
            f"— {table.iloc[p - 1]['Warning']}"
        ),
        key=f"{_PRIORITY_KEY}_widget",
    )
    # Close highlighted slicer container
    st.markdown('</div>', unsafe_allow_html=True)
    st.session_state[_PRIORITY_KEY] = selected
    return selected


# ---------------------------------------------------------------------------
# Severity helpers
# ---------------------------------------------------------------------------
def _warning_pill_severity_class(fc_warning: str) -> str:
    """Map a warning text to a pill severity class (red / amber / green / grey)."""
    text = (fc_warning or "").lower()
    if any(t in text for t in ("high", "escalating", "critical", "severe")):
        return "sev-red"
    if any(t in text for t in ("emerging", "amber", "watch", "warning", "elevated")):
        return "sev-amber"
    if "monitor" in text:
        return "sev-green"
    return "sev-grey"


# ---------------------------------------------------------------------------
# Governed Target card and Forecast gap helpers (display-only)
# ---------------------------------------------------------------------------
def _gap_unit_word(unit: str) -> str:
    """Map a KPI unit to the wording used in gap-to-target lines."""
    u = (unit or "").strip().lower()
    if u == "percent":
        return "percentage points"
    if u == "minutes":
        return "minutes"
    if u == "likert":
        return "Likert points"
    if u in ("complaint", "encounter"):
        return "per 1,000 encounters"
    return ""


def _build_target_card_html(
    kpi_id: Optional[str],
    unit_unused: str,
    threshold_cfg,
) -> str:
    """Render the governed Target / Target Band HTML card.

    The threshold_cfg returned by ``load_kpi_threshold_config()`` is a
    *dictionary* keyed by ``kpi_id`` (NOT a pandas DataFrame). The
    ``directionality`` field inside each entry is already normalized to
    one of ``HIGHER_IS_BETTER``, ``LOWER_IS_BETTER``, or ``TARGET_BAND``
    by the loader. The unit is read from the threshold row to keep the
    label consistent with the governed source.

    Source of truth is always the governed Green band. The function
    never fabricates values; if the threshold row is missing or invalid
    the card renders a calm ``Not configured`` fallback.
    """
    cfg = threshold_cfg if isinstance(threshold_cfg, dict) else {}
    row = cfg.get(kpi_id) if kpi_id else None
    if not isinstance(row, dict):
        return (
            '<div class="s360-risk-target-card">'
            '<div class="title">Target</div>'
            '<div class="value" style="color:#6A1B9A;">Not configured</div>'
            '<div class="meta">Governed Green band not yet configured for this KPI.</div>'
            "</div>"
        )

    direction = (row.get("directionality") or "").strip().upper()
    lo = row.get("green_lower_boundary")
    hi = row.get("green_upper_boundary")
    unit = (row.get("unit") or "").strip() or unit_unused
    is_provisional = bool(row.get("threshold_is_provisional", False))
    review_date = (
        (row.get("required_review_date") or row.get("review_date") or "").strip()
        if is_provisional
        else ""
    )

    if lo is None or hi is None:
        return (
            '<div class="s360-risk-target-card">'
            '<div class="title">Target</div>'
            '<div class="value" style="color:#6A1B9A;">Not configured</div>'
            '<div class="meta">Missing Green range boundaries.</div>'
            "</div>"
        )

    value_html = ""
    caption_html = ""
    label_html = "Target"

    try:
        if direction == "HIGHER_IS_BETTER":
            display = format_unit_value(float(lo), unit)
            value_html = f"\u2265 {display}"  # ≥
            caption_html = "Governed Green performance threshold"
            label_html = "Target"
        elif direction == "LOWER_IS_BETTER":
            display = format_unit_value(float(hi), unit)
            value_html = f"\u2264 {display}"  # ≤
            caption_html = "Governed Green performance threshold"
            label_html = "Target"
        elif direction == "TARGET_BAND":
            display_lo = format_unit_value(float(lo), unit)
            display_hi = format_unit_value(float(hi), unit)
            value_html = f"{display_lo} \u2013 {display_hi}"  # en-dash
            caption_html = "Governed Green operating range"
            label_html = "Target Band"
        else:
            return (
                '<div class="s360-risk-target-card">'
                '<div class="title">Target</div>'
                '<div class="value" style="color:#6A1B9A;">Not configured</div>'
                '<div class="meta">Unknown directionality in threshold config.</div>'
                "</div>"
            )
    except (TypeError, ValueError):
        return (
            '<div class="s360-risk-target-card">'
            '<div class="title">Target</div>'
            '<div class="value" style="color:#6A1B9A;">Not configured</div>'
            '<div class="meta">Governed Green range could not be parsed.</div>'
            "</div>"
        )

    provisional_html = ""
    if is_provisional:
        if review_date:
            provisional_html = (
                f'<div class="provisional">Provisional target \u00b7 Review: {review_date}</div>'
            )
        else:
            provisional_html = '<div class="provisional">Provisional target</div>'

    return (
        f'<div class="s360-risk-target-card">'
        f'<div class="title">{label_html}</div>'
        f'<div class="value">{value_html}</div>'
        f'<div class="meta">{caption_html}</div>'
        f'{provisional_html}'
        f"</div>"
    )


def _build_gap_to_target_html(
    forecast_value,
    unit_unused: str,
    threshold_cfg,
    kpi_id: Optional[str],
) -> str:
    """Render a compact gap-to-target line comparing the forecast to the
    governed Green band. Returns an empty string if no comparison can be made.

    threshold_cfg is a dictionary keyed by kpi_id; ``directionality``
    inside each entry is the loader-normalized uppercase token.
    """
    if forecast_value is None:
        return ""
    try:
        if pd.isna(forecast_value):
            return ""
    except (TypeError, ValueError):
        pass

    cfg = threshold_cfg if isinstance(threshold_cfg, dict) else {}
    row = cfg.get(kpi_id) if kpi_id else None
    if not isinstance(row, dict):
        return ""

    direction = (row.get("directionality") or "").strip().upper()
    lo = row.get("green_lower_boundary")
    hi = row.get("green_upper_boundary")
    unit = (row.get("unit") or "").strip() or unit_unused

    try:
        fv = float(forecast_value)
    except (TypeError, ValueError):
        return ""

    unit_word = _gap_unit_word(unit)
    gap_unit = unit_word if unit_word else "points"

    if direction == "HIGHER_IS_BETTER":
        if lo is None:
            return ""
        if fv < lo:
            diff = float(lo) - fv
            diff_str = format_unit_value(diff, unit)
            return (
                f'<div class="s360-risk-forecast-gap">'
                f'<span class="gap-off">{diff_str} {gap_unit} below target</span>'
                f"</div>"
            )
        return (
            f'<div class="s360-risk-forecast-gap">'
            f'<span class="gap-on">On target</span>'
            f"</div>"
        )

    if direction == "LOWER_IS_BETTER":
        if hi is None:
            return ""
        if fv > hi:
            diff = fv - float(hi)
            diff_str = format_unit_value(diff, unit)
            return (
                f'<div class="s360-risk-forecast-gap">'
                f'<span class="gap-off">{diff_str} {gap_unit} above target</span>'
                f"</div>"
            )
        return (
            f'<div class="s360-risk-forecast-gap">'
            f'<span class="gap-on">On target</span>'
            f"</div>"
        )

    if direction == "TARGET_BAND":
        if lo is None or hi is None:
            return ""
        # Boundary rule: inclusive lower, exclusive upper
        if fv >= float(lo) and fv < float(hi):
            return (
                f'<div class="s360-risk-forecast-gap">'
                f'<span class="gap-band">Within target band</span>'
                f"</div>"
            )
        if fv < float(lo):
            diff = float(lo) - fv
            diff_str = format_unit_value(diff, unit)
            return (
                f'<div class="s360-risk-forecast-gap">'
                f'<span class="gap-off">{diff_str} {gap_unit} below target band</span>'
                f"</div>"
            )
        # fv >= hi
        diff = fv - float(hi)
        diff_str = format_unit_value(diff, unit)
        return (
            f'<div class="s360-risk-forecast-gap">'
            f'<span class="gap-off">{diff_str} {gap_unit} above target band</span>'
            f"</div>"
        )

    return ""


# ---------------------------------------------------------------------------
# Selected risk detail (Governed Target + Forecast)
# ---------------------------------------------------------------------------
def _render_detail_panels(
    detail: dict,
    selected_row: Optional[dict] = None,
    threshold_cfg: Optional[pd.DataFrame] = None,
) -> None:
    if not detail:
        return
    st.markdown(
        '<div class="s360-risk-section-label">Selected Risk Summary</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div style="font-size:1.0rem;font-weight:700;color:#0B1E3D;margin:2px 0 8px 0;">{detail["header"]}</div>',
        unsafe_allow_html=True,
    )
    fc = detail["forecast"]

    # Resolve KPI id and unit for governed-target lookup
    kpi_id = (selected_row or {}).get("kpi_id") if selected_row else None
    unit = (selected_row or {}).get("latest_actual_unit", "") if selected_row else ""

    target_card_html = _build_target_card_html(kpi_id, unit, threshold_cfg)

    fc_warning = (fc.get("warning") or "").strip()
    warning_html = ""
    if fc_warning:
        sev_class = _warning_pill_severity_class(fc_warning)
        if fc_warning.lower() == "monitoring":
            warning_html = (
                f'<div class="warning-pill {sev_class}">Status: {fc_warning}</div>'
            )
        else:
            warning_html = (
                f'<div class="warning-pill {sev_class}">Warning: {fc_warning}</div>'
            )

    forecast_month_label = fc.get("month_label") or fc.get("month") or "Not available"

    # Gap-to-target line — uses the raw forecast numeric value
    forecast_numeric = (selected_row or {}).get("forecast_value") if selected_row else None
    if forecast_numeric is not None and pd.isna(forecast_numeric):
        forecast_numeric = None
    gap_html = _build_gap_to_target_html(
        forecast_numeric, unit, threshold_cfg, kpi_id
    )
    if not gap_html and fc.get("available") is False:
        gap_html = (
            '<div class="s360-risk-forecast-gap">'
            '<span class="gap-empty">Gap not assessable (forecast not available)</span>'
            "</div>"
        )

    st.markdown(
        f"""
<div class="s360-risk-detail-grid">
    {target_card_html}
    <div class="s360-risk-forecast-card">
        <div class="title">Forecast</div>
        <div class="value">{fc['value']}</div>
        <div class="meta">Forecast month: {forecast_month_label}</div>
        <div class="meta">Indicative range: {fc['indicative_range']}</div>
        {warning_html}
        <div class="meta">Quality: {fc['quality']}</div>
        <div class="meta">Horizon: {fc['horizon']}</div>
        {gap_html}
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Risk progression
# ---------------------------------------------------------------------------
def _render_progression(strip: list) -> None:
    st.markdown(
        '<div class="s360-risk-section-label">Risk Progression</div>',
        unsafe_allow_html=True,
    )
    if not strip:
        st.markdown(
            '<div class="s360-no-traceback-note">No progression data available.</div>',
            unsafe_allow_html=True,
        )
        return
    chips = []
    legend_seen = set()
    for entry in strip:
        sev = entry.get("severity", "grey")
        colour = _SEVERITY_BORDER.get(sev, _SEVERITY_BORDER["grey"])
        status = entry.get("status", "Unsupported")
        label = entry.get("label", "")
        value = entry.get("value")
        value_html = (
            f'<div class="value">{value}</div>' if value else
            f'<div class="value" style="color:#adb5bd;">—</div>'
        )
        kind_class = "actual" if status == "Actual" else ("forecast" if status == "Forecast" else "")
        chips.append(
            f'<div class="month {kind_class}" title="{label} • {status}">'
            f'<div class="label">{label}</div>'
            f'<div class="dot" style="background:{colour};"></div>'
            f'{value_html}'
            f'</div>'
        )
        legend_seen.add(status)
    html = '<div class="s360-risk-progression">' + "".join(chips) + "</div>"
    legend_parts = []
    if "Actual" in legend_seen:
        legend_parts.append("Jan–Jul reflect governed actual status")
    if "Forecast" in legend_seen:
        legend_parts.append("Aug–Dec reflect governed forecast status")
    if "Unsupported" in legend_seen:
        legend_parts.append("Unsupported months shown neutral")
    legend = " • ".join(legend_parts)
    st.markdown(html, unsafe_allow_html=True)
    st.markdown(
        f'<div class="s360-no-traceback-note">{legend}</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Management interpretation
# ---------------------------------------------------------------------------
def _render_interpretation(interpretation: dict) -> None:
    st.markdown(
        '<div class="s360-risk-section-label">Management Interpretation</div>',
        unsafe_allow_html=True,
    )
    combined = interpretation.get("combined", "")
    if combined:
        st.markdown(
            f'<div class="s360-risk-interpretation">{combined}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="s360-no-traceback-note">No interpretation available.</div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Suggested preventive action / management follow-up
# ---------------------------------------------------------------------------
def _render_action_card(
    action: dict,
    context_label: str = "",
    is_sim_lab_supported: bool = True,
    kpi_name: str = "",
) -> None:
    # Unsupported-by-Simulation-Lab branch: never send the user to a function
    # that does not exist for this KPI. Show a management follow-up card
    # instead and route the user to Decision & Call for Action.
    if not is_sim_lab_supported:
        display_kpi = (kpi_name or "this KPI").strip() or "this KPI"
        st.markdown(
            '<div class="s360-risk-section-label">Management Follow-Up</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
<div class="s360-risk-action neutral">
    <div class="title">Management Follow-Up</div>
    <div class="action">No simulation scenario is currently configured for {display_kpi}.</div>
    <div class="why">Review the forecast deterioration and supporting evidence before deciding on management action.</div>
    <div class="status">Next Step: Review this alert in Decision &amp; Call for Action.</div>
</div>
""",
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        '<div class="s360-risk-section-label">Suggested Preventive Action</div>',
        unsafe_allow_html=True,
    )
    action_text = (action.get("action", "") or "").strip()
    is_neutral = (action_text == "") or (action_text in _NEUTRAL_ACTION_TEXT)

    if is_neutral:
        context_line = (
            f'<div class="context">Current context: {context_label}</div>'
            if context_label else ""
        )
        st.markdown(
            f"""
<div class="s360-risk-action neutral">
    <div class="title">Suggested Preventive Action</div>
    <div class="action">Explore intervention options in the Simulation Lab.</div>
    <div class="why">Use the Simulation Lab to compare Minimum, Recommended, and Intensive Action scenarios for this KPI before selecting an option for management review.</div>
    {context_line}
    <div class="status">Next Step: Open Simulation Lab</div>
</div>
""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
<div class="s360-risk-action">
    <div class="title">{action.get('title', 'Suggested Preventive Action')}</div>
    <div class="action">{action_text}</div>
    <div class="why">Why this requires attention: {action.get('why', '')}</div>
    <div class="status">Action Status: {action.get('status', 'Suggested — Management Review Required')}</div>
</div>
""",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
def _render_footer() -> None:
    st.markdown(
        '<div class="s360-page-scope-note">'
        "No financial impact, scenario simulation, intervention execution, "
        "or cost-benefit analysis is shown on this page."
        "</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    st.set_page_config(
        page_title="Risk & Alert — Sentinel360 Dynamic",
        layout="wide",
    )
    _init_session_state()
    # --- SIDEBAR CHROME (brand + footer + native nav styling) ---
    render_sidebar_chrome()
    st.markdown(_CSS, unsafe_allow_html=True)

    # Build logo URIs (same working pattern as app.py / Executive Overview)
    jcorp_uri = _logo_data_uri("jcorp_logo.png")
    bsp_uri = _logo_data_uri("black_swan_protocol_logo.png")

    _render_header(jcorp_uri, bsp_uri)

    st.markdown('<div class="s360-risk-page">', unsafe_allow_html=True)

    # --- Filter bar ---
    st.markdown(
        '<div class="s360-risk-section-label">Filters</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="s360-risk-filter-bar">', unsafe_allow_html=True)
    opts = get_filter_options()
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        hospital_options = opts["hospital"] or [("HOSP-001", "HOSP-001")]
        st.selectbox(
            "Hospital",
            options=[h for h, _ in hospital_options],
            index=0,
            key="risk_alert_hospital",
            disabled=True,
        )
    with fc2:
        dept_options = opts["department"]
        dept_ids = [d for d, _ in dept_options]
        current = st.session_state.risk_alert_selected_department
        if current not in dept_ids:
            current = dept_ids[0] if dept_ids else "DEPT-ICU"
        st.selectbox(
            "Department",
            options=dept_ids,
            format_func=lambda d: dict(dept_options).get(d, d),
            index=dept_ids.index(current),
            key="risk_alert_selected_department",
        )
    with fc3:
        year_options = opts["year"] or [2025]
        st.selectbox(
            "Year",
            options=year_options,
            index=year_options.index(st.session_state.risk_alert_selected_year)
            if st.session_state.risk_alert_selected_year in year_options else 0,
            key="risk_alert_selected_year",
        )
    with fc4:
        month_options = opts["month"] or list(range(1, 13))
        current_month = st.session_state.risk_alert_selected_month
        if current_month not in month_options:
            current_month = month_options[0]
        st.selectbox(
            "Review Month",
            options=month_options,
            format_func=lambda m: f"{calendar.month_abbr[m]}",
            index=month_options.index(current_month),
            key="risk_alert_selected_month",
        )
    st.markdown(
        f'<div class="s360-risk-filter-excluded">Excluded from slicer: {", ".join(get_excluded_dept_ids()) or "(none)"}</div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # --- State + summary + table ---
    department = st.session_state.risk_alert_selected_department
    year = st.session_state.risk_alert_selected_year
    month = st.session_state.risk_alert_selected_month

    state = build_risk_alert_state(
        department_code=department,
        year=year,
        month=month,
        hospital_label="HOSP-001",
    )
    summary = state["summary"]
    display_table = state["table"]
    internal_rows = state["internal_rows"]

    _render_summary_cards(summary, internal_rows)
    _render_priority_table(display_table)

    # --- Selected risk selector ---
    priority_idx = _select_priority_row(display_table)
    if priority_idx is None or display_table.empty:
        st.markdown('</div>', unsafe_allow_html=True)
        _render_footer()
        return

    selected_dict = (
        internal_rows[priority_idx - 1]
        if priority_idx - 1 < len(internal_rows)
        else {}
    )

    kpi_daily = load_kpi_daily()
    forecast_df = load_kpi_monthly_forecast()
    monthly_actual = get_kpi_monthly_actual_table(kpi_daily)

    detail = build_selected_risk_detail(selected_dict, monthly_actual)
    threshold_cfg = load_kpi_threshold_config()
    _render_detail_panels(detail, selected_dict, threshold_cfg)

    # --- Actual + Forecast Trend chart (preserved production chart) ---
    st.markdown(
        '<div class="s360-risk-section-label">Actual + Forecast Trend</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="s360-risk-chart-panel">', unsafe_allow_html=True)
    try:
        render_selected_risk_chart(
            selected_row=selected_dict,
            monthly_actual=monthly_actual,
            forecast_df=forecast_df,
            review_year=year,
            review_month=month,
        )
    except Exception as exc:
        st.error(f"Trend chart could not be rendered: {exc}")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Risk progression ---
    strip = build_risk_progression(
        monthly_actual=monthly_actual,
        forecast_df=forecast_df,
        selected_row=selected_dict,
        review_year=year,
    )
    _render_progression(strip)

    # --- Management interpretation ---
    interpretation = build_management_interpretation(
        selected_row=selected_dict,
        monthly_actual=monthly_actual,
        review_year=year,
    )
    _render_interpretation(interpretation)

    # --- Suggested action ---
    action = build_suggested_action_card(selected_dict)
    # Build optional context label for the Simulation-Lab fallback using
    # only values that are already in page state.
    _MONTH_ABBR = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
    }
    _kpi = (selected_dict.get("kpi_name") or "").strip()
    _dept = (
        selected_dict.get("department_name")
        or selected_dict.get("department")
        or ""
    ).strip()
    _month_label = _MONTH_ABBR.get(month, str(month))
    _ctx_parts = [p for p in (_kpi, _dept, f"{_month_label} {year}") if p]
    context_label = " · ".join(_ctx_parts)

    # Only route the user to Simulation Lab when the selected KPI is in the
    # authoritative supported set already used by pages/04_Simulation_Lab.py.
    # No duplicate KPI-support logic is introduced here — we just consult the
    # same source of truth via _SUPPORTED_KPI_IDS.
    _selected_kpi_id = (selected_dict.get("kpi_id") or "").strip()
    _is_sim_lab_supported = _selected_kpi_id in _SUPPORTED_KPI_IDS

    _render_action_card(
        action,
        context_label=context_label,
        is_sim_lab_supported=_is_sim_lab_supported,
        kpi_name=_kpi,
    )

    st.markdown('</div>', unsafe_allow_html=True)
    _render_footer()


main()
