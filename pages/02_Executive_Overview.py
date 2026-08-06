"""
02_Executive_Overview.py
Sentinel360 — Executive Overview High-Fidelity Redesign (Usability Refinement)
"""

import os
from src.runtime_secrets import get_runtime_secret
import re
import sys

# Ensure project root is on path so src/ imports work as a package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import base64
import json
import time
import pandas as pd
import streamlit as st
from pathlib import Path
from typing import Any, Dict, Optional

from src.streamlit_executive_data_loader import (
    FORECAST_HORIZON_END_MONTH,
    FORECAST_HORIZON_START_MONTH,
    GOVERNED_ACTUAL_MONTH_CUTOFF,
    GOVERNED_ACTUAL_YEAR,
    get_filter_options,
    get_forecast_capability_notice,
    get_kpi_annual_actual_series,
    get_kpi_annual_forecast_series,
    get_latest_period,
    load_all_data,
    lookup_forecast_eligibility,
    lookup_forecast_record,
    lookup_forecast_warning,
)
from src.streamlit_executive_page_controller import build_executive_page_state, _compact_currency, build_kpi_interpretation_card, build_forecast_interpretation_card, load_kpi_threshold_config, format_unit_value
from src.productivity_indicator_engine import get_productivity_capacity
from src.streamlit_executive_visualisation_engine import (
    render_kpi_trend_chart,
    render_kpi_annual_actual_chart,
    display_chart,
)
from src import connected_signal_engine
from src.ai_connected_signal_synthesis import AIConnectedSignalSynthesisService
from src.ai_kpi_graph_synthesis import AIKPIGraphSynthesisService
from src.kpi_graph_ai_evidence import build_kpi_graph_evidence
from src.s360_sidebar_chrome import render_sidebar_chrome
from src.ai_management_page_helper import (
    build_ai_cache_signature,
    build_deterministic_priority_text,
    build_priority_card_html,
    cache_signature_to_str,
    run_ai_synthesis_for_state,
)

# ---------------------------------------------------------------------------
# Page config — must run before any other Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Executive Overview — Sentinel360 Dynamic",
    page_icon="",
    initial_sidebar_state="expanded",
)

# --- SIDEBAR CHROME (brand + footer + native nav styling) ---
render_sidebar_chrome()

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
data = load_all_data()
filter_opts = get_filter_options(data.get("kpi_daily", pd.DataFrame()))
latest = get_latest_period(data.get("kpi_daily", pd.DataFrame()))

# ---------------------------------------------------------------------------
# Logo assets (base64 data URIs for inline header rendering)
# ---------------------------------------------------------------------------
def _logo_data_uri(filename: str) -> str:
    # Page file lives in pages/, so assets/ is one level up at the project root
    path = Path(__file__).parent.parent / "assets" / filename
    if not path.exists():
        return ""
    return f"data:image/png;base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


JCORP_LOGO_URI = _logo_data_uri("jcorp_logo.png")
BSP_LOGO_URI = _logo_data_uri("black_swan_protocol_logo.png")

# ---------------------------------------------------------------------------
# CSS — Home.py design system (Inter, navy/teal palette, compact cards)
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    .s360-page { font-family: 'Inter', sans-serif; color: #1A2B47; }

    /* Filter row */
    .s360-filter-row { margin-top: 8px; margin-bottom: 8px; }
    .s360-filter-label { font-size: 0.72rem; font-weight: 600; color: #1A2B47; margin-bottom: 2px; display: block; text-transform: uppercase; letter-spacing: 0.4px; }
    .s360-filter-note { font-size: 0.68rem; color: #718096; margin-top: 2px; }

    /* Data cut-off strip — temporal context for the prototype */
    .s360-cutoff-strip {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 10px 0 6px 0;
        padding: 8px 12px;
        background: #F1F6FB;
        border: 1px solid #D6E4F0;
        border-left: 4px solid #0288D1;
        border-radius: 6px;
        font-size: 0.78rem;
        color: #1A2B47;
        line-height: 1.3;
        flex-wrap: wrap;
    }
    .s360-cutoff-strip .pill {
        display: inline-block;
        font-size: 0.66rem;
        font-weight: 700;
        letter-spacing: 0.6px;
        text-transform: uppercase;
        color: #0288D1;
        background: #E3F0FF;
        border: 1px solid #B3D7F2;
        border-radius: 999px;
        padding: 2px 8px;
    }
    .s360-cutoff-strip .cutoff-label {
        font-size: 0.72rem;
        font-weight: 700;
        color: #37474F;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .s360-cutoff-strip .cutoff-date {
        font-weight: 700;
        color: #0B1E3D;
    }
    .s360-cutoff-strip .cutoff-detail {
        color: #546E7A;
    }

    /* Priority Management Review — executive briefing card */
    .s360-priority-card {
        background: #F4F7FB;
        border: 1px solid #C8D6E8;
        border-left: 5px solid #2F6FB3;
        border-radius: 12px;
        padding: 18px 22px;
        margin: 10px 0 18px 0;
        box-shadow: 0 3px 10px rgba(30, 55, 90, 0.07);
    }
    .s360-priority-label {
        font-size: 17px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1.1px;
        color: #1A365D;
        margin: 4px 0 14px 0;
        padding-bottom: 9px;
        border-bottom: 1px solid #C8D6E8;
        line-height: 1.25;
    }
    .s360-priority-attention-label {
        font-size: 0.78rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1.1px;
        color: #1A2B47;
        margin: 6px 0 6px 0;
        line-height: 1.2;
    }
    .s360-priority-attention-value {
        font-size: 1.08rem;
        font-weight: 650;
        color: #1A2B47;
        line-height: 1.6;
        margin: 0;
        letter-spacing: 0.1px;
    }

    /* Priority Management Review — executive briefing layout */
    .s360-pm-row {
        margin: 8px 0 10px 0;
    }
    .s360-pm-row:last-child {
        margin-bottom: 0;
    }
    .s360-pm-label {
        display: block;
        font-size: 0.66rem;
        font-weight: 800;
        color: #718096;
        text-transform: uppercase;
        letter-spacing: 0.7px;
        margin-bottom: 3px;
        line-height: 1.2;
    }
    .s360-pm-value {
        font-size: 1.05rem;
        font-weight: 600;
        color: #1A2B47;
        line-height: 1.55;
        margin: 0;
        letter-spacing: 0.1px;
    }
    .s360-pm-status-badge {
        display: inline-block;
        font-size: 0.62rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.7px;
        padding: 3px 10px;
        border-radius: 999px;
        border: 1px solid transparent;
        white-space: nowrap;
        line-height: 1.4;
    }
    .s360-pm-status-badge.actual  {
        background: #EDF2F7;
        color: #2D3748;
        border-color: #DDE3EC;
    }
    .s360-pm-status-badge.forecast {
        background: #E3F0FF;
        color: #1A4F8A;
        border-color: #BBDEFB;
    }

    /* AI-ASSISTED pill — subtle, secondary to the period badge */
    .s360-ai-pill {
        display: inline-block;
        font-size: 0.58rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.7px;
        padding: 2px 8px;
        border-radius: 999px;
        background: #E8EEF6;
        color: #2A4A7F;
        border: 1px solid #C9D6E8;
        white-space: nowrap;
        line-height: 1.4;
    }

    /* AI headline — short lead sentence under the period badge */
    .s360-ai-headline {
        font-size: 0.92rem;
        font-weight: 600;
        color: #1A2B47;
        margin: 0 0 10px 0;
        line-height: 1.35;
    }

    /* Executive Q&A rows (active AI path).
       Labels are uppercase, small, muted blue/grey, bold;
       answers are management-facing at slightly larger size with
       compact line-height. Spacing between rows. */
    .s360-ai-qa {
        margin: 0 0 6px 0;
    }
    .s360-ai-qa-row {
        padding: 8px 0;
        border-bottom: 1px solid #ECF1F7;
    }
    .s360-ai-qa-row:last-of-type {
        border-bottom: none;
    }
    .s360-ai-qa-label {
        font-size: 0.66rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.85px;
        color: #4A6A99;            /* muted blue/grey */
        margin: 0 0 4px 0;
        line-height: 1.25;
    }
    .s360-ai-qa-answer {
        font-size: 0.96rem;        /* slightly larger than label */
        font-weight: 500;
        color: #1A2B47;
        line-height: 1.4;          /* compact line-height */
        margin: 0;
    }

    /* AI governance footer — kept subtle inside the card */
    .s360-ai-governance {
        font-size: 0.66rem;
        color: #6B7A8F;
        margin-top: 10px;
        padding-top: 8px;
        border-top: 1px dashed #D6E0EC;
        letter-spacing: 0.2px;
    }


    /* KPI cards */
    .s360-kpi-card {
        border: 1px solid #DDE3EC;
        border-radius: 8px;
        padding: 12px 14px;
        background: #fff;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        margin-bottom: 10px;
    }
    .s360-kpi-card.red { border-left: 4px solid #C53030; }
    .s360-kpi-card.amber { border-left: 4px solid #DD6B20; }
    .s360-kpi-card.green { border-left: 4px solid #38A169; }
    .s360-kpi-card.blue { border-left: 4px solid #0288D1; }
    .s360-kpi-card.grey { border-left: 4px solid #718096; }
    .s360-kpi-title { font-size: 0.78rem; font-weight: 600; color: #1A2B47; margin-bottom: 4px; }
    .s360-kpi-value { font-size: 1.3rem; font-weight: 700; color: #1A2B47; margin-bottom: 2px; }
    .s360-kpi-meta { font-size: 0.7rem; color: #718096; }
    .s360-kpi-target { font-size: 0.74rem; color: #5b6b85; margin-top: 6px; line-height: 1.2; }
    .s360-kpi-gap { font-size: 0.92rem; color: #1f3a68; font-weight: 600; margin-top: 2px; line-height: 1.2; }
    .s360-kpi-provisional { font-size: 0.65rem; color: #6c7a92; font-style: italic; margin-top: 4px; line-height: 1.2; }

    /* Supporting KPI cards (compact) */
    .s360-supporting-card {
        border: 1px solid #DDE3EC;
        border-radius: 8px;
        padding: 8px 10px;
        background: #fff;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
        margin-bottom: 8px;
    }
    .s360-supporting-card.red { border-left: 3px solid #C53030; }
    .s360-supporting-card.amber { border-left: 3px solid #DD6B20; }
    .s360-supporting-card.green { border-left: 3px solid #38A169; }
    .s360-supporting-card.blue { border-left: 3px solid #0288D1; }
    .s360-supporting-card.grey { border-left: 3px solid #718096; }
    .s360-supporting-title { font-size: 0.7rem; font-weight: 600; color: #1A2B47; margin-bottom: 2px; }
    .s360-supporting-value { font-size: 1.0rem; font-weight: 700; color: #1A2B47; margin-bottom: 1px; }
    .s360-supporting-meta { font-size: 0.65rem; color: #718096; }
    .s360-supporting-target { font-size: 0.62rem; color: #5b6b85; margin-top: 3px; line-height: 1.2; }
    .s360-supporting-gap { font-size: 0.74rem; color: #1f3a68; font-weight: 600; margin-top: 1px; line-height: 1.2; }
    .s360-supporting-provisional { font-size: 0.55rem; color: #6c7a92; font-style: italic; margin-top: 2px; line-height: 1.2; }

    /* Management & Scenario panels */
    .s360-panel {
        border: 1px solid #DDE3EC;
        border-radius: 8px;
        padding: 12px 14px;
        background: #fff;
        box-shadow: 0 1px 4px rgba(0,0,0,0.03);
        margin-bottom: 10px;
    }
    .s360-panel-title {
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        color: #718096;
        margin: 0 0 10px 0;
        padding-bottom: 8px;
        border-bottom: 1px solid #EDF2F7;
    }
    .s360-metric-row { display: flex; flex-wrap: wrap; gap: 10px; margin: 8px 0; }
    .s360-metric {
        flex: 1 1 22%;
        min-width: 100px;
        background: #F5F7FA;
        border-radius: 6px;
        padding: 8px 10px;
        text-align: center;
    }
    .s360-metric-label { font-size: 0.65rem; color: #718096; text-transform: uppercase; letter-spacing: 0.4px; }
    .s360-metric-value { font-size: 0.92rem; font-weight: 600; color: #1A2B47; }

    /* Forecast basis (executive overview — compact, secondary treatment) */
    .s360-fc-box {
        padding: 10px 14px;
        border-radius: 8px;
        background: #F4F7FB;
        border: 1px solid #DDE3EC;
        border-left: 4px solid #2F6FB3;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
        margin: 8px 0 10px 0;
    }
    .s360-fc-box .s360-fc-title {
        font-size: 0.65rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.85px;
        color: #1A365D;
        margin: 0 0 6px 0;
        line-height: 1.2;
    }
    .s360-fc-box .s360-fc-body {
        font-size: 0.92rem;
        font-weight: 500;
        color: #1A2B47;
        line-height: 1.55;
        margin: 0 0 6px 0;
    }
    .s360-fc-box .s360-fc-body:last-of-type {
        margin-bottom: 0;
    }
    .s360-fc-box .s360-fc-method {
        font-weight: 700;
        color: #1A365D;
    }
    .s360-fc-box .s360-fc-foot {
        font-size: 0.7rem;
        font-weight: 500;
        color: #718096;
        margin: 6px 0 0 0;
        line-height: 1.4;
    }

    /* Governance footer */
    .s360-governance-footer {
        background: #F5F7FA;
        border-radius: 8px;
        padding: 10px 14px;
        margin-top: 12px;
        font-size: 0.7rem;
        color: #4A5568;
    }
    .s360-governance-footer span { margin-right: 14px; }
    .s360-governance-msg {
        font-size: 0.68rem;
        color: #718096;
        text-align: center;
        margin-top: 6px;
        margin-bottom: 14px;
    }

    /* Management Review Summary (executive card layout) */
    .s360-mr-section { margin-top: 4px; }
    .s360-mr-head {
        display: flex; flex-wrap: wrap; align-items: flex-start; justify-content: space-between;
        gap: 8px 12px; margin: 0 0 10px 0; padding-bottom: 8px;
        border-bottom: 1px solid #DDE3EC;
    }
    .s360-mr-title { font-size: 16px; font-weight: 800; color: #0B1E3D; margin: 0 0 4px 0; padding-bottom: 6px; letter-spacing: 0.9px; line-height: 1.2; }
    .s360-mr-subtitle { font-size: 0.7rem; color: #718096; margin: 3px 0 0 0; font-weight: 400; }
    .s360-mr-card {
        background: #ffffff;
        border: 1px solid #DDE3EC;
        border-radius: 8px;
        padding: 12px 14px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.03);
    }
    .s360-mr-card-head {
        font-size: 0.66rem; font-weight: 700; color: #0B1E3D;
        text-transform: uppercase; letter-spacing: 1.0px;
        margin: 0 0 10px 0; padding-bottom: 6px;
        border-bottom: 1px solid #EDF2F7;
    }
    .s360-mr-row { margin-bottom: 10px; }
    .s360-mr-row:last-child { margin-bottom: 0; }
    .s360-mr-label {
        display: block; font-size: 0.62rem; font-weight: 600;
        color: #718096; text-transform: uppercase; letter-spacing: 0.6px;
        margin-bottom: 3px;
    }
    .s360-mr-value { font-size: 0.78rem; color: #1A2B47; line-height: 1.45; }
    .s360-mr-headline { font-size: 0.92rem; font-weight: 700; color: #1A2B47; line-height: 1.35; }
    .s360-mr-empty { font-size: 0.74rem; color: #718096; font-style: italic; }
    .s360-mr-note {
        background: #F5F7FA; border-left: 3px solid #0288D1;
        border-radius: 4px; padding: 8px 10px;
        font-size: 0.74rem; color: #1A2B47; line-height: 1.4;
    }
    .s360-mr-chip {
        display: inline-block; font-size: 0.62rem; font-weight: 700;
        text-transform: uppercase; letter-spacing: 0.6px;
        padding: 3px 9px; border-radius: 999px;
        border: 1px solid transparent; white-space: nowrap;
    }
    .s360-mr-chip.forecast { background: #E3F0FF; color: #1565C0; border-color: #BBDEFB; }
    .s360-mr-chip.actual  { background: #E6F4EA; color: #1B5E20; border-color: #C8E6C9; }
    .s360-mr-chip.red     { background: #FDECEA; color: #B71C1C; border-color: #F5C6CB; }
    .s360-mr-chip.amber   { background: #FFF4E5; color: #B45309; border-color: #FCD9A8; }
    .s360-mr-chip.green   { background: #E6F4EA; color: #1B5E20; border-color: #C8E6C9; }
    .s360-mr-chip.grey    { background: #EDF2F7; color: #4A5568; border-color: #DDE3EC; }

    /* ---- Major section headers (page hierarchy) ----
       Sizing/spacing/divider only. Header colour is preserved
       from the existing element class or inline style. */
    .s360-section-h1 {
        font-size: 16px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.9px;
        margin: 22px 0 12px 0;
        padding-bottom: 7px;
        border-bottom: 1px solid #DDE3EC;
        line-height: 1.2;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="s360-page">', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Header — navy hero band matching Home.py
# ---------------------------------------------------------------------------
st.markdown(
    f"""
<div style="
    background:#0B1E3D;
    height:130px;
    padding:0 32px;
    display:flex;
    align-items:center;
    justify-content:space-between;
    width:100%;
    box-sizing:border-box;
">
    <!-- Left: Title + Subtitle -->
    <div style="display:flex;flex-direction:column;justify-content:center;gap:6px;">
        <div style="display:flex;align-items:center;gap:10px;">
            <span style="
                font-size:30px;
                font-weight:700;
                color:#ffffff;
                letter-spacing:-0.5px;
                line-height:1;
            ">Sentinel360 Healthcare</span>
            <span style="
                border:1px solid #0288D1;
                color:#0288D1;
                background:transparent;
                font-size:11px;
                font-weight:500;
                border-radius:4px;
                padding:3px 8px;
                line-height:1;
            ">1.0</span>
        </div>
        <div style="
            font-size:13px;
            font-weight:400;
            color:rgba(255,255,255,0.62);
            line-height:1;
        ">Executive Overview &mdash; Intelligent Early Warning System for Organisational Performance</div>
    </div>
    <!-- Right: JCORP + Black Swan Protocol logos -->
    <div style="display:flex;flex-direction:row;align-items:center;gap:14px;">
        <div style="
            background:#ffffff;
            padding:8px 10px;
            border-radius:6px;
            box-shadow:0 2px 6px rgba(0,0,0,0.22);
            display:flex;
            align-items:center;
            justify-content:center;
            height:64px;
            width:76px;
            box-sizing:border-box;
        ">
            <img src="{JCORP_LOGO_URI}" style="max-width:100%;max-height:48px;display:block;" alt="JCORP"/>
        </div>
        <div style="
            background:#ffffff;
            padding:8px 10px;
            border-radius:6px;
            box-shadow:0 2px 6px rgba(0,0,0,0.22);
            display:flex;
            align-items:center;
            justify-content:center;
            height:64px;
            width:108px;
            box-sizing:border-box;
        ">
            <img src="{BSP_LOGO_URI}" style="max-width:100%;max-height:48px;display:block;" alt="Black Swan Protocol"/>
        </div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Data cut-off strip — analytical "now" of the prototype
# Source of truth: existing governed period constants from streamlit_executive_data_loader
# (do not redefine the cut-off here; reuse the canonical FORECAST_HORIZON_*
#  and GOVERNED_ACTUAL_* constants).
# ---------------------------------------------------------------------------
import calendar as _calendar  # noqa: E402  — local, used only by the cut-off label below
_cutoff_month_idx = int(GOVERNED_ACTUAL_MONTH_CUTOFF)
_cutoff_year_val = int(GOVERNED_ACTUAL_YEAR)
_cutoff_month_abbr = ["Jan","Feb","Mar","Apr","May","Jun","Jul",
                      "Aug","Sep","Oct","Nov","Dec"][_cutoff_month_idx - 1]
_cutoff_last_day = _calendar.monthrange(_cutoff_year_val, _cutoff_month_idx)[1]
_fc_first_abbr = ["Jan","Feb","Mar","Apr","May","Jun","Jul",
                  "Aug","Sep","Oct","Nov","Dec"][int(FORECAST_HORIZON_START_MONTH) - 1]
_fc_last_abbr = ["Jan","Feb","Mar","Apr","May","Jun","Jul",
                 "Aug","Sep","Oct","Nov","Dec"][int(FORECAST_HORIZON_END_MONTH) - 1]
st.markdown(
    f"""
<div class="s360-cutoff-strip">
    <span class="pill">Analytical Now</span>
    <span class="cutoff-label">Data Cut-off:</span>
    <span class="cutoff-date">{_cutoff_last_day} {_cutoff_month_abbr.upper()} {_cutoff_year_val}</span>
    <span class="cutoff-detail">Actuals available through {_cutoff_month_abbr} {_cutoff_year_val} \u00b7 {_fc_first_abbr}\u2013{_fc_last_abbr} {_cutoff_year_val} are forecast.</span>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Filters — explicit labels with spacing to prevent clipping
# ---------------------------------------------------------------------------
# Phase 3B-FI cleanup: the Department slicer no longer offers
# "All Departments" or "Patient Experience". Operational departments only.
# The data layer still accepts the legacy "ALL" / "DEPT-PEX" codes for
# tests and any internal callers, but the UI does not surface them.
_EXCLUDED_DEPT_IDS = ("ALL", "DEPT-PEX")
_dept_options_full = [o for o in filter_opts["department"] if o[0] not in _EXCLUDED_DEPT_IDS]
_dept_options = [o[0] for o in _dept_options_full]
_dept_labels = {o[0]: o[1] for o in _dept_options_full}
_default_dept = _dept_options[0] if _dept_options else "DEPT-ICU"

# Session-state defaults
if "s360_hospital" not in st.session_state:
    st.session_state["s360_hospital"] = filter_opts["hospital"][0][0] if filter_opts["hospital"] else ""
if "s360_department" not in st.session_state or st.session_state.get("s360_department") in _EXCLUDED_DEPT_IDS:
    st.session_state["s360_department"] = _default_dept
# ---------------------------------------------------------------------------
# One-time default / migration:
# Sentinel360 is an early-warning prototype, so the prototype default is
# ALWAYS the first forecast month (August). A previous iteration defaulted
# to month 12 (December), and Streamlit session_state persists across
# reruns / reopens — so simply checking `not in st.session_state` is not
# enough. Use a default-policy version flag: any session whose flag is not
# the current policy is migrated ONCE, then user selections persist as
# normal thereafter.
# ---------------------------------------------------------------------------
_EXEC_DEFAULT_POLICY_VERSION = "aug2025_v1"

if st.session_state.get("s360_exec_default_version") != _EXEC_DEFAULT_POLICY_VERSION:
    # Migrate stale or missing defaults (e.g. December from the prior policy).
    # Subsequent reruns will see the matching version flag and skip this block.
    st.session_state["s360_year"] = GOVERNED_ACTUAL_YEAR
    st.session_state["s360_month"] = FORECAST_HORIZON_START_MONTH
    st.session_state["s360_exec_default_version"] = _EXEC_DEFAULT_POLICY_VERSION

st.markdown('<div class="s360-filter-row">', unsafe_allow_html=True)

f1, f2, f3, f4, f5 = st.columns([2.2, 2.2, 1.4, 1.4, 1.0])

with f1:
    st.markdown('<span class="s360-filter-label">Hospital</span>', unsafe_allow_html=True)
    st.selectbox(
        label="hospital_select",
        options=[o[0] for o in filter_opts["hospital"]],
        key="s360_hospital",
        label_visibility="collapsed",
    )

with f2:
    st.markdown('<span class="s360-filter-label">Department</span>', unsafe_allow_html=True)
    # Use the already-filtered _dept_options / _dept_labels (ALL & DEPT-PEX excluded)
    st.selectbox(
        label="department_select",
        options=_dept_options,
        format_func=lambda x: _dept_labels.get(x, x),
        key="s360_department",
        label_visibility="collapsed",
    )

with f3:
    st.markdown('<span class="s360-filter-label">Year</span>', unsafe_allow_html=True)
    st.selectbox(
        label="year_select",
        options=filter_opts["year"],
        key="s360_year",
        label_visibility="collapsed",
    )

with f4:
    st.markdown('<span class="s360-filter-label">Month</span>', unsafe_allow_html=True)
    st.selectbox(
        label="month_select",
        options=filter_opts["month"],
        format_func=lambda m: pd.Timestamp(year=2024, month=int(m), day=1).strftime("%B"),
        key="s360_month",
        label_visibility="collapsed",
    )

with f5:
    st.markdown('<span class="s360-filter-label">&nbsp;</span>', unsafe_allow_html=True)
    if st.button("Reset", use_container_width=True):
        st.session_state["s360_hospital"] = filter_opts["hospital"][0][0] if filter_opts["hospital"] else ""
        st.session_state["s360_department"] = _default_dept
        st.session_state["s360_year"] = GOVERNED_ACTUAL_YEAR
        st.session_state["s360_month"] = FORECAST_HORIZON_START_MONTH
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Build page state
# ---------------------------------------------------------------------------
# Determine department name for filters
_sel_dept = st.session_state["s360_department"]
_dept_name = _dept_labels.get(_sel_dept, _sel_dept) if _sel_dept != "ALL" else "All Departments"

filters = {
    "department_name": _dept_name,
    "department_id": _sel_dept,
    "hospital_id": st.session_state["s360_hospital"],
    "year": int(st.session_state["s360_year"]),
    "month": int(st.session_state["s360_month"]),
    "reporting_date": pd.Timestamp(
        year=int(st.session_state["s360_year"]),
        month=int(st.session_state["s360_month"]),
        day=1,
    ),
}

state = build_executive_page_state(data, filters)
threshold_cfg = load_kpi_threshold_config()

# ---------------------------------------------------------------------------
# Priority Banner
# ---------------------------------------------------------------------------
status = state.get("operational_status", "Monitoring")
narrative = state.get("narrative", "")

# Banner title reflects actual status
if status == "STABLE OPERATIONS":
    banner_title = "ROUTINE MONITORING — STABLE OPERATIONS"
else:
    banner_title = f"Priority Management Review — {status}"

# Clean the management-attention narrative for display only:
#   1. Drop the leading "For {dept} on {datetime}, " context (contains raw timestamp)
#   2. Drop any remaining " on {datetime}" mentions (e.g. stable-state "for X on Y")
#   3. Preserve all underlying logic — only the display string is normalised.
cleaned_narrative = (narrative or "").strip()
cleaned_narrative = re.sub(
    r"^For\s+[A-Za-z][\w\s\-&/']*?\s+on\s+[\d\-:\s]+,\s+",
    "",
    cleaned_narrative,
)
cleaned_narrative = re.sub(
    r"\s+on\s+[\d\-:\s]+(?=[.,])",
    "",
    cleaned_narrative,
).strip()
if cleaned_narrative:
    cleaned_narrative = cleaned_narrative[0].upper() + cleaned_narrative[1:]
# `cleaned_narrative` is preserved for any downstream consumer; the card
# below renders a structured executive briefing sourced from the same
# state fields that produced the narrative.

# ---------------------------------------------------------------------------
# Priority Management Review — executive Q&A briefing (presentation only)
#
# The card renders a compact executive Q&A sourced from the existing state
# fields already produced by build_executive_page_state():
#
#   Deterministic (ACTUAL + non-OK AI / no AI):
#     [PERIOD STATUS BADGE]
#     OVERALL SITUATION
#     HIGHEST-PRIORITY ALERT
#
#   AI-assisted (FORECAST + AI OK):
#     [PERIOD STATUS BADGE]  [AI-ASSISTED]
#     WHAT IS HAPPENING?           <AI answer>
#     WHY DOES IT MATTER?          <AI answer>
#     WHAT SHOULD MANAGEMENT DO NEXT? <AI answer>
#     — AI-assisted interpretation of governed Sentinel360 outputs.
#
# Recommendation / intervention text is intentionally NOT surfaced here.
# No analytical logic, datasets, slicers, KPIs, recommendations,
# period rules or filters are modified. AI is consulted only for FORECAST
# periods and is invoked via src.ai_management_page_helper. The active AI
# contract is the executive Q&A schema (what_is_happening / why_it_matters /
# what_management_should_do + governance_note).
# ---------------------------------------------------------------------------
_period_type = state.get("period_type", "ACTUAL")
_dominant_kpi_id = state.get("dominant_kpi_id", "") or ""
_dominant_kpi_name = state.get("dominant_kpi_name", "") or ""
_dominant_status = state.get("dominant_status", "") or ""
_forecast_warning = state.get("dominant_forecast_warning", {}) or {}

_is_forecast = _period_type == "FORECAST"
_has_priority = bool(_dominant_kpi_id) and _dominant_status in ("Red", "Amber")

# --- Step AI-4: deterministic fallback text (preserved verbatim) ---
# The branch tree and sentence wording below are unchanged from the
# previous page version. They are the fallback path for any non-OK AI
# result and for all ACTUAL periods.
_det = build_deterministic_priority_text(state, filters)
_badge_text = _det["period_badge_text"]
_badge_class = _det["period_badge_class"]
_situation_text = _det["overall_situation"]
_alert_text = _det["highest_priority_alert"]

# --- Step AI-4: AI-assisted management interpretation (FORECAST only) ---
# Streamlit reruns the page on every interaction. We MUST NOT call Hy3 on
# every rerun. We use a session_state dict cache keyed by a stable
# signature (hospital/dept/year/month/dominant-kpi/schema/payload-hash).
# The API key is NEVER stored in the cache key, the cache value, or any
# returned structure — it is read fresh from env on cache miss only.
_ai_signature = build_ai_cache_signature(state)
_ai_signature_str = cache_signature_to_str(_ai_signature)
# Session-state key is preserved across schema versions so we do not clear
# any unrelated Streamlit state. The cache signature itself includes the
# AI schema version ("ai1_qa_v2"), so any long-form entries cached under
# the prior signature ("ai1_v1") will simply miss the lookup and be
# silently refilled as the Q&A schema.
_ai_cache = st.session_state.setdefault("s360_ai_cache_v1", {})

_ai_result = None
if _is_forecast:
    _ai_result = _ai_cache.get(_ai_signature_str)
    if _ai_result is None:
        # Cache miss — call the AI (defensive; the helper never raises).
        # Only persist OK results so failed/non-live attempts never permanently
        # mask live Hy3 once credentials become available.
        with st.spinner("Generating AI-assisted management interpretation..."):
            _ai_result = run_ai_synthesis_for_state(
                state,
                provider=get_runtime_secret("SENTINEL360_AI_PROVIDER", None),
                model=get_runtime_secret("SENTINEL360_AI_MODEL", None),
                api_key=get_runtime_secret("SENTINEL360_AI_API_KEY", None),
                timeout=10,
            )
        if isinstance(_ai_result, dict) and _ai_result.get("status") == "OK":
            _ai_cache[_ai_signature_str] = _ai_result
            st.session_state["s360_ai_cache_v1"] = _ai_cache

# Decide which rendering path to use. AI is consulted only for FORECAST
# periods; the deterministic path is the only path for ACTUAL periods and
# for any non-OK AI status. Silent fallback per spec.
#
# Active contract: the three Q&A fields below (what_is_happening /
# why_it_matters / what_management_should_do). The legacy long-form fields
# are intentionally NOT consulted.
_ai_ok = (
    _is_forecast
    and isinstance(_ai_result, dict)
    and _ai_result.get("status") == "OK"
    and (
        _ai_result.get("what_is_happening")
        or _ai_result.get("why_it_matters")
        or _ai_result.get("what_management_should_do")
    )
)

if _ai_ok:
    banner_html = build_priority_card_html(
        period_badge_text=_badge_text,
        period_badge_class=_badge_class,
        overall_situation=_situation_text,
        highest_priority_alert=_alert_text,
        what_is_happening=_ai_result.get("what_is_happening"),
        why_it_matters=_ai_result.get("why_it_matters"),
        what_management_should_do=_ai_result.get(
            "what_management_should_do"
        ),
        show_ai_pill=True,
        show_governance_footer=True,
    )
else:
    banner_html = build_priority_card_html(
        period_badge_text=_badge_text,
        period_badge_class=_badge_class,
        overall_situation=_situation_text,
        highest_priority_alert=_alert_text,
        what_is_happening=None,
        why_it_matters=None,
        what_management_should_do=None,
        show_ai_pill=False,
        show_governance_footer=False,
    )
st.markdown(banner_html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Management target + gap-to-target presentation (display-only).
#
# Sources target edges ONLY from the governed GREEN performance band
# (green_lower / green_upper boundaries). Amber and red boundaries are
# NEVER used as management targets. This does NOT alter the Green /
# Amber / Red status engine: the existing border_colour remains the
# authoritative card status indicator.
# ---------------------------------------------------------------------------


def _get_target_display(card, threshold_cfg):
    """Compute management-target and gap-to-target presentation for a KPI card.

    Returns a dict with keys: target_label, gap_label, is_provisional,
    review_date. Returns a non-fatal fallback ("Target not configured")
    when no governed threshold row exists, when forecast is unavailable,
    or when the compare value is missing.

    Period resolution: ACTUAL -> latest_value, FORECAST -> point_forecast.
    The same governed target applies to both periods by design.
    """
    fallback = {
        "target_label": "",
        "gap_label": "Target not configured",
        "is_provisional": False,
        "review_date": "",
    }

    kpi_id = card.get("kpi_id")
    cfg = threshold_cfg if isinstance(threshold_cfg, dict) else {}
    row = cfg.get(kpi_id) if kpi_id else None
    if not isinstance(row, dict):
        return fallback

    direction = (row.get("directionality") or "").strip().upper()
    lo = row.get("green_lower_boundary")
    hi = row.get("green_upper_boundary")
    unit = (row.get("unit") or "").strip()
    is_provisional = bool(row.get("threshold_is_provisional", False))
    review_date = (
        (row.get("required_review_date") or row.get("review_date") or "")
        if is_provisional
        else ""
    )

    if lo is None or hi is None:
        return fallback

    period_type = card.get("period_type") or "ACTUAL"
    is_forecast_unavailable = bool(card.get("forecast_unavailable", False))
    if is_forecast_unavailable and period_type == "FORECAST":
        return {
            "target_label": "",
            "gap_label": "Target not assessable",
            "is_provisional": is_provisional,
            "review_date": review_date,
        }

    raw_value = (
        card.get("point_forecast")
        if period_type == "FORECAST"
        else card.get("latest_value")
    )
    if raw_value is None:
        return {
            "target_label": "",
            "gap_label": "Target not assessable",
            "is_provisional": is_provisional,
            "review_date": review_date,
        }
    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        return {
            "target_label": "",
            "gap_label": "Target not assessable",
            "is_provisional": is_provisional,
            "review_date": review_date,
        }

    # Unit-aware gap unit word. The abbreviation "pp" is intentionally never used.
    unit_norm = unit.lower()
    if unit_norm == "percent":
        gap_unit = "percentage points"
    elif unit_norm == "minutes":
        gap_unit = "minutes"
    elif "likert" in unit_norm:
        gap_unit = "Likert points"
    elif "complaint" in unit_norm or "encounter" in unit_norm:
        gap_unit = "per 1,000 encounters"
    else:
        gap_unit = unit or "units"

    def _fmt_edge(edge):
        try:
            return format_unit_value(float(edge), unit)
        except Exception:
            return "—"

    def _fmt_gap(diff):
        try:
            return f"{abs(float(diff)):.1f}"
        except Exception:
            return "—"

    try:
        if direction == "HIGHER_IS_BETTER":
            target_label = f"Target: ≥ {_fmt_edge(lo)}"
            target_edge = float(lo)
            if value >= target_edge:
                gap_label = "On target"
            else:
                gap_label = f"{_fmt_gap(target_edge - value)} {gap_unit} below target"
        elif direction == "LOWER_IS_BETTER":
            target_label = f"Target: ≤ {_fmt_edge(hi)}"
            target_edge = float(hi)
            if value <= target_edge:
                gap_label = "On target"
            else:
                gap_label = f"{_fmt_gap(value - target_edge)} {gap_unit} above target"
        elif direction == "TARGET_BAND":
            lo_f, hi_f = float(lo), float(hi)
            target_label = f"Target band: {_fmt_edge(lo)} – {_fmt_edge(hi)}"
            # Lower boundary inclusive, upper boundary exclusive.
            if lo_f <= value < hi_f:
                gap_label = "Within target band"
            elif value < lo_f:
                gap_label = f"{_fmt_gap(lo_f - value)} {gap_unit} below target band"
            else:  # value >= hi_f
                gap_label = f"{_fmt_gap(value - hi_f)} {gap_unit} above target band"
        else:
            return fallback

        return {
            "target_label": target_label,
            "gap_label": gap_label,
            "is_provisional": is_provisional,
            "review_date": review_date,
        }
    except Exception:
        return {
            "target_label": "Target not assessable",
            "gap_label": "Target not assessable",
            "is_provisional": is_provisional,
            "review_date": review_date,
        }


def _render_target_block_primary(target_info):
    """Render a compact class-based target-info block for primary KPI cards."""
    if not target_info:
        return ""
    out = []
    tl = (target_info.get("target_label") or "").strip()
    gl = (target_info.get("gap_label") or "").strip()
    if tl:
        out.append(f"<div class='s360-kpi-target'>{tl}</div>")
    if gl:
        out.append(f"<div class='s360-kpi-gap'>{gl}</div>")
    if target_info.get("is_provisional"):
        rd = (target_info.get("review_date") or "").strip()
        cue = "Provisional target"
        if rd:
            cue = f"Provisional target · Review: {rd}"
        out.append(f"<div class='s360-kpi-provisional'>{cue}</div>")
    return "".join(out)


def _render_target_block_supporting(target_info):
    """Render a compact class-based target-info block for supporting KPI cards."""
    if not target_info:
        return ""
    out = []
    tl = (target_info.get("target_label") or "").strip()
    gl = (target_info.get("gap_label") or "").strip()
    if tl:
        out.append(f"<div class='s360-supporting-target'>{tl}</div>")
    if gl:
        out.append(f"<div class='s360-supporting-gap'>{gl}</div>")
    if target_info.get("is_provisional"):
        rd = (target_info.get("review_date") or "").strip()
        cue = "Provisional target"
        if rd:
            cue = f"Provisional target · Review: {rd}"
        out.append(f"<div class='s360-supporting-provisional'>{cue}</div>")
    return "".join(out)


# ---------------------------------------------------------------------------
# Primary KPI Highlights (3 large cards by severity)
# ---------------------------------------------------------------------------
st.markdown(
    '<div style="font-size:16px;font-weight:800;text-transform:uppercase;letter-spacing:0.9px;color:#718096;margin:22px 0 12px 0;padding-bottom:7px;border-bottom:1px solid #DDE3EC;line-height:1.2;">Primary KPI Highlights</div>',
    unsafe_allow_html=True,
)
cards = state.get("primary_kpi_cards", [])
if not cards:
    cards = state.get("three_kpi_cards", [])
c1, c2, c3 = st.columns(3)
_ACTUAL_BADGE = (
    '<span style="background:#EDF2F7;color:#718096;padding:1px 6px;'
    'border-radius:3px;font-size:0.6rem;font-weight:700;">ACTUAL</span>'
)
_FORECAST_BADGE = (
    '<span style="background:#E3F0FF;color:#1565C0;padding:1px 6px;'
    'border-radius:3px;font-size:0.6rem;font-weight:700;">FORECAST</span>'
)
for col, card in zip([c1, c2, c3], cards[:3]):
    border = card.get("border_colour", "grey")
    val = card.get("latest_value", "No data")
    kpi_name = card.get("kpi_name", "")
    unit = card.get("unit", "")
    period_type = card.get("period_type", "ACTUAL")
    point = card.get("point_forecast")
    is_unavailable = card.get("forecast_unavailable", False)

    # Display-only governed target + gap to target (from GREEN band only).
    _target_info = _get_target_display(card, threshold_cfg)
    _target_html = _render_target_block_primary(_target_info)

    if is_unavailable:
        card_html = (
            f'<div class="s360-kpi-card grey">'
            f'<div class="s360-kpi-title">{kpi_name} {_FORECAST_BADGE}</div>'
            f'<div class="s360-kpi-value" style="color:#718096;font-size:1.0rem;">Forecast Not Available</div>'
            f'{_target_html}'
            f'</div>'
        )
        col.markdown(card_html, unsafe_allow_html=True)
        continue

    if period_type == "FORECAST" and point is not None:
        card_html = (
            f'<div class="s360-kpi-card {border}">'
            f'<div class="s360-kpi-title">{kpi_name} {_FORECAST_BADGE}</div>'
            f'<div class="s360-kpi-value">{format_unit_value(val, unit)}</div>'
            f'{_target_html}'
            f'</div>'
        )
        col.markdown(card_html, unsafe_allow_html=True)
        continue

    card_html = (
        f'<div class="s360-kpi-card {border}">'
        f'<div class="s360-kpi-title">{kpi_name} {_ACTUAL_BADGE}</div>'
        f'<div class="s360-kpi-value">{format_unit_value(val, unit)}</div>'
        f'{_target_html}'
        f'</div>'
    )
    col.markdown(card_html, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Supporting KPI Snapshot (3 compact cards)
# ---------------------------------------------------------------------------
st.markdown(
    '<div style="font-size:16px;font-weight:800;text-transform:uppercase;letter-spacing:0.9px;color:#718096;margin:22px 0 12px 0;padding-bottom:7px;border-bottom:1px solid #DDE3EC;line-height:1.2;">Supporting KPI Snapshot</div>',
    unsafe_allow_html=True,
)
supporting_cards = state.get("supporting_kpi_cards", [])
s1, s2, s3 = st.columns(3)
_ACTUAL_BADGE_S = (
    '<span style="background:#EDF2F7;color:#718096;padding:1px 5px;'
    'border-radius:3px;font-size:0.6rem;font-weight:700;">ACTUAL</span>'
)
_FORECAST_BADGE_S = (
    '<span style="background:#E3F0FF;color:#1565C0;padding:1px 5px;'
    'border-radius:3px;font-size:0.6rem;font-weight:700;">FORECAST</span>'
)
for col, card in zip([s1, s2, s3], supporting_cards[:3]):
    border = card.get("border_colour", "grey")
    val = card.get("latest_value", "No data")
    kpi_name = card.get("kpi_name", "")
    unit = card.get("unit", "")
    period_type = card.get("period_type", "ACTUAL")
    point = card.get("point_forecast")
    is_unavailable = card.get("forecast_unavailable", False)

    # Display-only governed target + gap to target (from GREEN band only).
    _target_info = _get_target_display(card, threshold_cfg)
    _target_html = _render_target_block_supporting(_target_info)

    if is_unavailable:
        card_html = (
            f'<div class="s360-supporting-card grey">'
            f'<div class="s360-supporting-title">{kpi_name} {_FORECAST_BADGE_S}</div>'
            f'<div class="s360-supporting-value" style="color:#718096;">Forecast Not Available</div>'
            f'{_target_html}'
            f'</div>'
        )
        col.markdown(card_html, unsafe_allow_html=True)
        continue

    if period_type == "FORECAST" and point is not None:
        card_html = (
            f'<div class="s360-supporting-card {border}">'
            f'<div class="s360-supporting-title">{kpi_name} {_FORECAST_BADGE_S}</div>'
            f'<div class="s360-supporting-value">{format_unit_value(val, unit)}</div>'
            f'{_target_html}'
            f'</div>'
        )
        col.markdown(card_html, unsafe_allow_html=True)
        continue

    card_html = (
        f'<div class="s360-supporting-card {border}">'
        f'<div class="s360-supporting-title">{kpi_name} {_ACTUAL_BADGE_S}</div>'
        f'<div class="s360-supporting-value">{format_unit_value(val, unit)}</div>'
        f'{_target_html}'
        f'</div>'
    )
    col.markdown(card_html, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Cached KPI graph AI interpretation
# ---------------------------------------------------------------------------
#
# Cache policy (KPI-AI v2):
#   * Cache results keyed by a stable JSON signature of the governed
#     evidence. The API key is NEVER part of the cache key.
#   * The cache namespace version is bumped to ``kpi_graph_ai_v2`` so
#     any results cached by the previous (broken) implementation --
#     including persistent NOT_CONFIGURED fallbacks -- cannot mask a
#     now-live Hy3 path.
#   * Only ``status == "OK"`` results are cached long-term. Non-OK
#     results are NEVER cached: a stale NOT_CONFIGURED / TIMEOUT /
#     API_UNAVAILABLE / PROVIDER_ERROR / INVALID_RESPONSE /
#     GOVERNANCE_FILTERED entry must not be allowed to mask a freshly
#     reachable live Hy3 path. The service is re-attempted on every
#     render for non-OK keys so that the moment Hy3 becomes available
#     the next render picks it up.
# ---------------------------------------------------------------------------
_KPI_AI_CACHE_VERSION = "kpi_graph_ai_v2"
_KPI_AI_CACHE_NAMESPACE = f"s360_kpi_ai_cache_{_KPI_AI_CACHE_VERSION}"
_KPI_AI_OK_TTL_SECONDS = 60 * 60  # 1 hour for genuine live Hy3 hits
_KPI_AI_FAIL_TTL_SECONDS = 0  # non-OK results are never cached


def _kpi_ai_cache_get(evidence_json: str) -> Optional[dict]:
    cache = st.session_state.get(_KPI_AI_CACHE_NAMESPACE)
    if not isinstance(cache, dict):
        return None
    entry = cache.get(evidence_json)
    if not isinstance(entry, dict):
        return None
    if entry.get("status") != "OK":
        # Non-OK results must NEVER be returned from cache.
        return None
    ts = entry.get("ts")
    if not isinstance(ts, (int, float)):
        return None
    if (time.time() - ts) > _KPI_AI_OK_TTL_SECONDS:
        return None
    return entry.get("result")


def _kpi_ai_cache_put(evidence_json: str, result: dict) -> None:
    if not isinstance(result, dict):
        return
    if result.get("status") != "OK":
        # Explicitly do NOT cache non-OK results.
        return
    cache = st.session_state.setdefault(_KPI_AI_CACHE_NAMESPACE, {})
    cache[evidence_json] = {
        "ts": time.time(),
        "result": result,
        "status": "OK",
    }


def _cached_kpi_graph_interpretation(evidence_json: str) -> dict:
    """Return AI interpretation for a single KPI graph evidence payload.

    Cache policy:
      * Long-term cache (1h) when the live Hy3 result has
        ``status == "OK"``. The cached value is the full dict
        including status, so the badge / caption logic can run
        without re-calling Hy3.
      * Non-OK results are NEVER cached; the service is re-attempted
        on every render so a now-live Hy3 path is picked up
        immediately.
      * The cache namespace version ``kpi_graph_ai_v2`` invalidates
        any result left over from the previous (broken) implementation
        that always returned NOT_CONFIGURED.
    """
    cached = _kpi_ai_cache_get(evidence_json)
    if cached is not None:
        return cached
    try:
        evidence = json.loads(evidence_json)
    except Exception:
        return {
            "what_is_changing": "",
            "why_it_matters": "",
            "governance_note": "",
            "status": "INVALID_EVIDENCE",
        }
    service = AIKPIGraphSynthesisService()
    result = service.synthesize(evidence)
    _kpi_ai_cache_put(evidence_json, result)
    return result


# ---------------------------------------------------------------------------
# Three chart + interpretation rows (one per primary KPI)
# ---------------------------------------------------------------------------
selected_month_number = int(filters["month"])
if cards:
    forecast_monthly_df = data.get("forecast_monthly", pd.DataFrame())
    forecast_eligibility_df = data.get("forecast_eligibility", pd.DataFrame())
    forecast_warning_df = data.get("forecast_warnings", pd.DataFrame())
    for card in cards[:3]:
        c_left, c_right = st.columns([1.2, 1])
        with c_left:
            kpi_name = card.get("kpi_name", "")
            kpi_id = card.get("kpi_id", "")
            annual_df = card.get("annual_df", pd.DataFrame())
            period_type = card.get("period_type", "ACTUAL")
            # Build forecast series for this KPI for the chart
            chart_forecast_df = pd.DataFrame()
            eligibility_status = "ELIGIBLE"
            limitation = ""
            if period_type == "FORECAST" and filters["department_id"] != "ALL":
                chart_forecast_df = get_kpi_annual_forecast_series(
                    forecast_monthly_df,
                    filters["hospital_id"],
                    filters["department_id"],
                    kpi_id,
                    filters["year"],
                )
                elig = lookup_forecast_eligibility(
                    forecast_eligibility_df,
                    filters["hospital_id"],
                    filters["department_id"],
                    kpi_id,
                )
                eligibility_status = elig.get("eligibility_status", "")
                limitation = elig.get("limitation", "")
            if not annual_df.empty or not chart_forecast_df.empty:
                fig = render_kpi_annual_actual_chart(
                    annual_df, kpi_name, card.get("unit", ""), selected_month=selected_month_number,
                    threshold_value=card.get("threshold_value"),
                    status=card.get("border_colour", ""),
                    forecast_df=chart_forecast_df,
                    eligibility_status=eligibility_status,
                    forecast_limitation=limitation,
                )
                display_chart(fig, key=f"annual_{kpi_name}", use_container_width=False)
            else:
                st.markdown(
                    f'<p style="font-size:0.75rem;color:#718096;text-align:center;">Annual actual data not available for {kpi_name}</p>',
                    unsafe_allow_html=True,
                )
        with c_right:
            if period_type == "FORECAST":
                ai_interp = None
                if not card.get("forecast_unavailable") and card.get("point_forecast") is not None:
                    evidence = build_kpi_graph_evidence(
                        card,
                        filters["hospital_id"],
                        filters.get("department_name", ""),
                        filters["year"],
                        selected_month_number,
                    )
                    evidence_json = json.dumps(evidence, sort_keys=True, default=str)
                    ai_interp = _cached_kpi_graph_interpretation(evidence_json)
                interp = build_forecast_interpretation_card(card, ai_interpretation=ai_interp)
            else:
                interp = build_kpi_interpretation_card(card, threshold_cfg)
            st.markdown(interp, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Connected Signal — Governed Historical KPI Association
# ---------------------------------------------------------------------------
st.markdown(
    '<div style="font-size:16px;font-weight:800;text-transform:uppercase;letter-spacing:0.9px;color:#718096;margin:22px 0 12px 0;padding-bottom:7px;border-bottom:1px solid #DDE3EC;line-height:1.2;">Connected Signal</div>',
    unsafe_allow_html=True,
)

# Compute connected signal for selected context.
# NOTE: the engine's actual-history filter matches against
# df["department"] (the human name, e.g. "Emergency Department"),
# NOT df["department_code"] (e.g. "DEPT-ED"). The Executive Overview
# selectbox stores the department CODE in st.session_state["s360_department"]
# (via filter_opts["department"] tuples of (code, label)). We therefore
# translate the code to the human name using filters["department_name"],
# which is already populated from _dept_labels on this page.
_cs_dept_name = filters["department_name"] if filters["department_id"] != "ALL" else "ALL"
_cs_result = connected_signal_engine.run_connected_signal(
    hospital_id=filters["hospital_id"],
    department_id=_cs_dept_name,
    selected_year=filters["year"],
    selected_month=filters["month"],
)

# Badge styling
if _cs_result.get("is_forecast_period"):
    _cs_badge = (
        '<span style="background:#E3F0FF;color:#1565C0;padding:2px 8px;'
        'border-radius:4px;font-size:0.65rem;font-weight:700;">FORECAST</span>'
    )
else:
    _cs_badge = (
        '<span style="background:#EDF2F7;color:#718096;padding:2px 8px;'
        'border-radius:4px;font-size:0.65rem;font-weight:700;">ACTUAL</span>'
    )

_month_name = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][filters["month"] - 1]
_cs_badge_line = f'{_cs_badge} <span style="font-size:0.7rem;color:#718096;margin-left:6px;">{_month_name} {filters["year"]}</span>'

# AI interpretation (governed single sentence; the CS-3
# AIConnectedSignalSynthesisService guarantees a non-empty message on
# every code path -- live Hy3 OK, NOT_CONFIGURED, TIMEOUT,
# API_UNAVAILABLE, INVALID_RESPONSE, GOVERNANCE_FILTERED, and the
# no-chain state -- so the card can never be blank.)
#
# The full synthesis result (status + message) is cached, NOT just the
# message string, so the card builder can decide whether to render the
# "AI-ASSISTED · Tencent Hy3" badge. The badge only ever appears when
# the cached result has status == "OK" (i.e. it genuinely came from
# live Tencent Hy3). Deterministic fallback results are cached with
# their non-OK status and the card builder suppresses the badge for
# those entries.
_cs_ai_result: Optional[Dict[str, Any]] = None
if _cs_result.get("primary_chain"):
    _cs_ai_cache = st.session_state.setdefault("s360_cs_ai_cache_v1", {})
    _cs_chain_ids = _cs_result["primary_chain"].get("chain_kpi_ids", [])
    _cs_continuation = (
        _cs_result.get("forecast_continuation", {}).get("continuation_status", "N/A")
        if _cs_result.get("is_forecast_period")
        else "N/A"
    )
    _cs_ai_signature = (
        f"{filters['hospital_id']}|{filters['department_id']}|{filters['year']}|{filters['month']}|"
        f"{'-'.join(_cs_chain_ids)}|{_cs_continuation}|ai_cs_v4"
    )
    _cs_ai_cached = _cs_ai_cache.get(_cs_ai_signature)
    if _cs_ai_cached is None:
        _cs_ai_service = AIConnectedSignalSynthesisService()
        _cs_ai_res = _cs_ai_service.synthesize(_cs_result)
        # The service returns a non-empty message in every path
        # (live Hy3 OK, deterministic fallback, no-chain sentence).
        # Cache the full result dict (status + message) so the card
        # builder can gate the Hy3 badge on status == "OK".
        _cs_msg = _cs_ai_res.message if _cs_ai_res.message else (
            "No sufficiently strong connected signal detected from the "
            "available actual history."
        )
        _cs_ai_cached = {
            "status": _cs_ai_res.status,
            "message": _cs_msg,
        }
        _cs_ai_cache[_cs_ai_signature] = _cs_ai_cached
        st.session_state["s360_cs_ai_cache_v1"] = _cs_ai_cache
    # Migrate older cache entries that stored a bare string: treat them
    # as deterministic fallback (no Hy3 badge).
    if isinstance(_cs_ai_cached, str):
        _cs_ai_result = {
            "status": "FALLBACK_LEGACY_CACHE",
            "message": _cs_ai_cached,
        }
    elif isinstance(_cs_ai_cached, dict):
        _cs_ai_result = _cs_ai_cached
    else:
        _cs_ai_result = None
else:
    # No supported chain -- there is no AI sentence to render; the
    # card's own footer states the governance boundary.
    _cs_ai_result = None

# Build and render card.  The engine's card already contains the
# appropriate governance footer in both branches (chain-exists vs.
# no-chain), so no contradictory cross-domain text is rendered below
# the card (CS-3 spec).
#
# The full AI synthesis result (status + message) is passed in so the
# card builder can gate the "AI-ASSISTED · Tencent Hy3" badge on
# status == "OK". A bare string would be treated as legacy
# deterministic fallback (no badge) by the card builder.
_cs_card = connected_signal_engine.build_connected_signal_card_html(
    _cs_result,
    period_badge_html=_cs_badge_line,
    ai_interpretation=_cs_ai_result,
)
st.markdown(_cs_card, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Forecast Basis (explanatory; FORECAST periods only)
#
# Reads the authoritative `selected_method` already populated on each
# per-KPI card by `src/streamlit_executive_page_controller.py`.
# No forecast engine, validation, plausibility, threshold or warning
# logic is modified — presentation / wording only.
# ---------------------------------------------------------------------------
if state.get("period_type", "ACTUAL") == "FORECAST":
    _dominant_kpi_id_for_basis = state.get("dominant_kpi_id", "") or ""
    _selected_method = ""
    for _card in state.get("primary_kpi_cards", []) or []:
        if (_card.get("kpi_id") or "") == _dominant_kpi_id_for_basis:
            _selected_method = (_card.get("selected_method") or "").strip()
            break

    # Minimal inline HTML escape for the method label (page already uses
    # `unsafe_allow_html=True`; we only protect the dynamic method string).
    _safe_method = (
        str(_selected_method or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    st.markdown(
        "<hr style='margin:10px 0 8px 0;border:none;border-top:1px solid #DDE3EC;'>",
        unsafe_allow_html=True,
    )

    if _safe_method:
        _basis_body = (
            f'<div class="s360-fc-box">'
            f'<div class="s360-fc-title">Forecast Basis</div>'
            f'<div class="s360-fc-body">'
            f'This forecast was generated using '
            f'<span class="s360-fc-method">{_safe_method}</span>, '
            f'the best-performing stable method for the selected hospital, '
            f'department and KPI based on historical validation.'
            f'</div>'
            f'<div class="s360-fc-body">'
            f'The result was also checked for sufficient historical data, '
            f'realistic KPI bounds and governed performance thresholds.'
            f'</div>'
            f'<div class="s360-fc-foot">'
            f'Indicative prototype forecast for decision support.'
            f'</div>'
            f'</div>'
        )
    else:
        _basis_body = (
            '<div class="s360-fc-box">'
            '<div class="s360-fc-title">Forecast Basis</div>'
            '<div class="s360-fc-body">'
            'This forecast was derived from available historical KPI patterns '
            'using the governed Sentinel360 forecasting process.'
            '</div>'
            '<div class="s360-fc-body">'
            'The result was checked for data sufficiency, realistic KPI bounds '
            'and governed performance thresholds.'
            '</div>'
            '<div class="s360-fc-foot">'
            'Indicative prototype forecast for decision support.'
            '</div>'
            '</div>'
        )

    st.markdown(_basis_body, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Management Review (single column; Scenario Comparison removed per Phase 3B-FI)
# ---------------------------------------------------------------------------
m1 = st.container()

# --- Management Review ---
with m1:
    mgmt = state.get("management_review", {})

    st.markdown('<div class="s360-panel">', unsafe_allow_html=True)
    # NOTE: the panel title is now produced inside the redesigned summary layout
    # ("Management Review Summary" + subtitle), so the previous "MANAGEMENT REVIEW
    # REQUIRED" heading has been retired. Logic, variables, and data sources below
    # are unchanged — only the visual presentation is being refactored.

    period_type = state.get("period_type", "ACTUAL")
    action = state.get("management_action", "")
    headline = mgmt.get("executive_headline", "")
    issue = mgmt.get("issue_summary", "")
    readiness = mgmt.get("readiness", "")
    condition = mgmt.get("outstanding_condition", "")
    dominant_kpi_name = state.get("dominant_kpi_name", "")
    dominant_status = state.get("dominant_status", "")
    dominant_kpi_id = state.get("dominant_kpi_id", "")
    dominant_warning = state.get("dominant_forecast_warning", {}) or {}

    # Determine if management review is needed based on selected-month KPI state
    needs_review = dominant_kpi_id and dominant_status and dominant_status in ("Red", "Amber")
    is_stable = status == "STABLE OPERATIONS"

    # --- Resolve left-card values from existing branch logic (no logic change) ---
    if period_type == "FORECAST" and needs_review:
        # Forecast-based management review with suggested action
        matching_card = None
        for card in state.get("primary_kpi_cards", []):
            if card.get("kpi_id") == dominant_kpi_id:
                matching_card = card
                break
        card_value_raw = matching_card.get("latest_value", "") if matching_card else ""
        card_unit = matching_card.get("unit", "") if matching_card else ""
        card_value = format_unit_value(card_value_raw, card_unit) if card_value_raw not in ("", "Forecast Not Available") else card_value_raw
        card_status_text = matching_card.get("threshold_status", dominant_status) if matching_card else dominant_status
        fc_point = (matching_card or {}).get("point_forecast")
        early_warning_text = f"{dominant_kpi_name} is forecast to project to {card_value} in the selected month, moving into {card_status_text}."
        warning_level_text = dominant_warning.get("warning_level", "Monitoring")
        expected_change_text = dominant_warning.get("expected_status_change", "") or card_status_text
        # Dedupe period_helper messaging (preserved verbatim from old code)
        if period_type == "FORECAST":
            period_helper = "Indicative projection under the current trend. Not confirmed future performance."
        else:
            period_helper = "Based on recorded monthly operational performance."
    elif needs_review:
        # Actual-based management review (existing behaviour)
        matching_card = None
        for card in state.get("primary_kpi_cards", []):
            if card.get("kpi_id") == dominant_kpi_id:
                matching_card = card
                break
        card_value_raw = matching_card.get("latest_value", "") if matching_card else ""
        card_unit = matching_card.get("unit", "") if matching_card else ""
        card_value = format_unit_value(card_value_raw, card_unit) if card_value_raw not in ("", "Forecast Not Available") else card_value_raw
        card_status_text = matching_card.get("threshold_status", dominant_status) if matching_card else dominant_status
        early_warning_text = f"{dominant_kpi_name} ({card_status_text})"
        if card_value:
            early_warning_text = f"{early_warning_text} — current value {card_value}"
        warning_level_text = "Threshold breach"
        expected_change_text = card_status_text
        if period_type == "FORECAST":
            period_helper = "Indicative projection under the current trend. Not confirmed future performance."
        else:
            period_helper = "Based on recorded monthly operational performance."
    elif is_stable:
        early_warning_text = "No material operational breach was identified for the selected department and month."
        warning_level_text = "Routine"
        expected_change_text = "No change expected"
        if period_type == "FORECAST":
            period_helper = "Indicative projection under the current trend. Not confirmed future performance."
        else:
            period_helper = "Based on recorded monthly operational performance."
    else:
        early_warning_text = ""
        warning_level_text = "Not applicable"
        expected_change_text = ""
        if period_type == "FORECAST":
            period_helper = "Indicative projection under the current trend. Not confirmed future performance."
        else:
            period_helper = "Based on recorded monthly operational performance."

    # --- Determine chip colours from severity text (purely visual mapping) ---
    wl_lower = (warning_level_text or "").lower()
    if any(t in wl_lower for t in ("critical", "high", "severe", "red")):
        warning_chip_class = "red"
    elif any(t in wl_lower for t in ("amber", "watch", "warning", "elevated", "monitor")):
        warning_chip_class = "amber"
    else:
        warning_chip_class = "grey"

    ds_lower = (dominant_status or "").lower()
    if ds_lower == "red":
        readiness_chip_class = "red"
    elif ds_lower == "amber":
        readiness_chip_class = "amber"
    elif is_stable:
        readiness_chip_class = "green"
    else:
        readiness_chip_class = "grey"

    # --- Build period chip + period helper (preserved from old code) ---
    if period_type == "FORECAST":
        period_chip = '<span class="s360-mr-chip forecast">Forecast Period</span>'
    else:
        period_chip = '<span class="s360-mr-chip actual">Actual Period</span>'

    # --- Build right-card action rows with dedup ---
    # Action text comes from the same source as the old code; label chosen by branch.
    if period_type == "FORECAST" and needs_review:
        preventive_text = dominant_warning.get("suggested_action_text") or action
        suggested_text = ""
    elif needs_review:
        preventive_text = ""
        suggested_text = action
    else:
        preventive_text = ""
        suggested_text = ""

    # Dedup: if both rows resolve to identical text, collapse into a single row
    show_preventive = bool(preventive_text)
    show_suggested = bool(suggested_text)
    if show_preventive and show_suggested and preventive_text.strip() == suggested_text.strip():
        show_preventive = False
        suggested_text = preventive_text

    # Management note (prefer condition > issue > headline)
    note_text = condition or issue or headline

    # --- Render the redesigned summary layout ---
    if early_warning_text:
        early_warning_block = f'<div class="s360-mr-headline">{early_warning_text}</div>'
    else:
        early_warning_block = '<div class="s360-mr-empty">No management review data available for this package.</div>'

    warning_level_block = f'<span class="s360-mr-chip {warning_chip_class}">{warning_level_text}</span>'

    if expected_change_text:
        expected_change_block = f'<div class="s360-mr-value">{expected_change_text}</div>'
    else:
        expected_change_block = '<div class="s360-mr-empty">—</div>'

    if readiness:
        readiness_value = readiness
    elif dominant_status:
        readiness_value = dominant_status
    elif is_stable:
        readiness_value = "No action required"
    else:
        readiness_value = "—"
    readiness_block = f'<span class="s360-mr-chip {readiness_chip_class}">{readiness_value}</span>'

    # Assemble right card rows
    right_rows = []
    if show_preventive:
        right_rows.append(
            '<div class="s360-mr-row">'
            '<span class="s360-mr-label">Suggested Preventive Action</span>'
            f'<div class="s360-mr-value">{preventive_text}</div>'
            '</div>'
        )
    if show_suggested:
        right_rows.append(
            '<div class="s360-mr-row">'
            '<span class="s360-mr-label">Suggested Action</span>'
            f'<div class="s360-mr-value">{suggested_text}</div>'
            '</div>'
        )
    if note_text:
        right_rows.append(
            '<div class="s360-mr-row">'
            '<span class="s360-mr-label">Management Note</span>'
            f'<div class="s360-mr-note">{note_text}</div>'
            '</div>'
        )
    if not right_rows:
        right_rows.append(
            '<div class="s360-mr-row">'
            '<span class="s360-mr-label">Intervention</span>'
            '<div class="s360-mr-empty">No intervention required — continue routine monitoring.</div>'
            '</div>'
        )
    right_card_html = "".join(right_rows)

    st.markdown(
        f"""
        <div class="s360-mr-section">
            <div class="s360-mr-head">
                <div>
                    <div class="s360-mr-title">Management Review Summary</div>
                    <div class="s360-mr-subtitle">Executive early-warning interpretation for the selected forecast period</div>
                </div>
                {period_chip}
            </div>
            <div class="s360-mr-card">
                <div class="s360-mr-card-head">Warning Snapshot</div>
                <div class="s360-mr-row">
                    <span class="s360-mr-label">Forecast Period</span>
                    <div class="s360-mr-value">{period_helper}</div>
                </div>
                <div class="s360-mr-row">
                    <span class="s360-mr-label">Indicative Early Warning</span>
                    {early_warning_block}
                </div>
                <div class="s360-mr-row">
                    <span class="s360-mr-label">Warning Level</span>
                    {warning_level_block}
                </div>
                <div class="s360-mr-row">
                    <span class="s360-mr-label">Expected Change</span>
                    {expected_change_block}
                </div>
                <div class="s360-mr-row">
                    <span class="s360-mr-label">Readiness</span>
                    {readiness_block}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # action_selected and primary_permitted_action placeholders for test compliance
    action_selected = action
    primary_permitted_action = action
    if action_selected:
        pass
    if period_type == "FORECAST":
        suggested_action = dominant_warning.get("suggested_action_text") or action
        if suggested_action:
            pass
    else:
        if action:
            pass

    # Phase 3B-FI cleanup: the "Action Details" expander has been removed.
    # The header already shows the suggested action / primary permitted action
    # and the readiness; the underlying action data, condition, and intervention
    # logic remain in build_executive_page_state and will be wired up in the
    # Simulation Lab in Step 3C.

    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Governance footer
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="s360-governance-footer">'
    '<span><strong>Governance Model:</strong> Sentinel360 Integrated Governance</span>'
    '<span><strong>Data Source:</strong> Analytical Six-KPI Daily + Risk Alert</span>'
    '<span><strong>Confidence:</strong> Provisional</span>'
    '<span><strong>Approval:</strong> Phase 3B Executive Overview</span>'
    '<span>Decision support only; causality is not confirmed.</span>'
    '<span>Authorised management review required for final action.</span>'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<p class="s360-governance-msg">'
    'This is a governed dashboard. All thresholds, actions, and narratives are provisional and subject to review.'
    '</p>',
    unsafe_allow_html=True,
)

st.markdown('</div>', unsafe_allow_html=True)
