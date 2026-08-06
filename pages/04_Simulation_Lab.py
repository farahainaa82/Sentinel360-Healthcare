"""pages/04_Simulation_Lab.py — Simulation Lab (Phase 3D).

Uses ONLY existing governed engines, configs, and data.
No new models.  No new assumptions.  No frozen output modification.

Phase 3D visual redesign: this page has been restyled to match the
Sentinel360 Healthcare design system used by the homepage, Executive
Overview, and Risk & Alert pages.  All simulation formulas, scenario
assumptions, intervention mappings, action strategy logic, baseline
logic, forecast values, KPI calculations, financial calculations,
scenario eligibility, confidence logic, session state, decision
handoff logic, saved scenario logic, the 2025 timeline, datasets, and
analytical engines remain unchanged.
"""
from __future__ import annotations

import base64
import calendar
import datetime
import os
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Sentinel360 imports
# ---------------------------------------------------------------------------
from src.simulation_lab_controller import (
    build_simulation_state,
    get_filter_options,
    _COMPARATOR_ORDER,
    _DISPLAY_LABEL_FOR_COMPARATOR_ID,
    _FINANCIAL_DISPLAY_RULES,
    _FORBIDDEN_WORDS,
    _SUPPORTED_KPI_IDS,
    _KPI_ID_TO_NAME,
    _KPI_TO_ACTION_STRATEGY,
)
from src.streamlit_executive_data_loader import (
    FORECAST_HORIZON_START_MONTH,
    GOVERNED_ACTUAL_YEAR,
    GOVERNED_ACTUAL_MONTH_CUTOFF,
    _display_department,
)
from src.streamlit_executive_page_controller import (
    format_unit_value,
    load_kpi_threshold_config,
)
from src.s360_sidebar_chrome import render_sidebar_chrome

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Simulation Lab", page_icon="", layout="wide")

# --- SIDEBAR CHROME (brand + footer + native nav styling) ---
# Called BEFORE the Simulation Lab's own <style> block below so the page's
# own sidebar background (#EAF4FF) and border win via DOM order.
render_sidebar_chrome()

# ---------------------------------------------------------------------------
# Logo helper — same working pattern as app.py / Executive Overview / Risk
# ---------------------------------------------------------------------------
def _logo_data_uri(filename: str) -> str:
    # Page file lives in pages/, so assets/ is one level up at the project root
    path = Path(__file__).parent.parent / "assets" / filename
    if not path.exists():
        return ""
    return f"data:image/png;base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


# ---------------------------------------------------------------------------
# CSS — Sentinel360 design system
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
.stApp { background: #F5F7FA; }
html, body, [class*="css"]  { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }

/* ---- Navy branded header ---- */
.s360-sim-header {
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
.s360-sim-header-left { display: flex; flex-direction: column; justify-content: center; gap: 6px; }
.s360-sim-header-brand { display: flex; align-items: center; gap: 10px; }
.s360-sim-header-brand-name {
    font-size: 30px; font-weight: 700; color: #ffffff;
    letter-spacing: -0.5px; line-height: 1;
}
.s360-sim-header-version {
    border: 1px solid #0288D1; color: #0288D1; background: transparent;
    font-size: 11px; font-weight: 500; border-radius: 4px;
    padding: 3px 8px; line-height: 1;
}
.s360-sim-header-page-title {
    font-size: 20px; font-weight: 600; color: #ffffff; line-height: 1; margin-top: 2px;
}
.s360-sim-header-subtitle {
    font-size: 13px; font-weight: 400; color: rgba(255,255,255,0.72); line-height: 1;
}
.s360-sim-header-right { display: flex; flex-direction: row; align-items: center; gap: 14px; }
.s360-sim-logo-cell {
    background: #ffffff; padding: 8px 10px; border-radius: 6px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.22);
    display: flex; align-items: center; justify-content: center;
    height: 64px; box-sizing: border-box;
}
.s360-sim-logo-cell.jcorp { width: 76px; }
.s360-sim-logo-cell.bsp   { width: 108px; }
.s360-sim-logo-cell img { max-width: 100%; max-height: 48px; display: block; }

/* ---- Sidebar SIMULATION CONTROLS pane ---- */
[data-testid="stSidebar"] { background: #EAF4FF; border-right: 1px solid #BBDEFB; }
/* Preserve Streamlit's native sidebar viewport sizing and vertical scrolling. */
[data-testid="stSidebarContent"] {
    height: 100vh;
    overflow-y: auto;
    overflow-x: hidden;
}
/* Bottom scroll-space so the last (KPI) control can be positioned higher
   before its dropdown opens, giving the popover room to render. */
[data-testid="stSidebarContent"] { padding-bottom: 180px; }
.s360-sim-controls-heading {
    font-size: 0.7rem; font-weight: 700; color: #0B1E3D;
    text-transform: uppercase; letter-spacing: 1.0px;
    margin-top: 4px; margin-bottom: 6px; padding-bottom: 6px;
    border-bottom: 1px solid #BBDEFB;
}
.s360-sim-controls-help {
    font-size: 0.7rem; color: #4A5568; margin-bottom: 8px; line-height: 1.45;
}
.s360-sim-controls-flow {
    font-size: 0.62rem; color: #1565C0;
    background: #ffffff; padding: 5px 8px; border-radius: 4px;
    margin-bottom: 10px; font-weight: 600; border: 1px solid #DDE3EC;
}

/* ---- Section labels (page hierarchy) ---- */
.s360-sim-section {
    font-size: 16px; font-weight: 800; color: #718096;
    text-transform: uppercase; letter-spacing: 0.9px;
    margin: 22px 0 12px 0; padding-bottom: 7px;
    border-bottom: 1px solid #DDE3EC;
    line-height: 1.2;
}

/* ---- Action Strategy card (light blue) ---- */
.s360-sim-strategy {
    background: #EAF4FF; border: 1px solid #BBDEFB; border-left: 4px solid #0288D1;
    border-radius: 8px; padding: 12px 14px; margin: 4px 0 12px 0;
    box-shadow: 0 1px 4px rgba(0,0,0,0.03);
}
.s360-sim-strategy .label {
    font-size: 0.62rem; font-weight: 700; color: #1565C0;
    text-transform: uppercase; letter-spacing: 0.8px;
}
.s360-sim-strategy .value {
    font-size: 1.0rem; font-weight: 700; color: #0B1E3D;
    margin-top: 4px; line-height: 1.2;
}
.s360-sim-strategy .sub {
    font-size: 0.7rem; color: #4A5568; margin-top: 2px;
}

/* ---- Baseline (Latest Actual + Do-Nothing) — two side-by-side cards ---- */
.s360-sim-baseline-grid {
    display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 4px 0 6px 0;
}
@media (max-width: 880px) { .s360-sim-baseline-grid { grid-template-columns: 1fr; } }
.s360-sim-baseline-block {
    border: 1px solid #DDE3EC; border-radius: 8px;
    padding: 12px 14px; background: #ffffff;
    box-shadow: 0 1px 4px rgba(0,0,0,0.03);
}
.s360-sim-baseline-block.do-nothing {
    background: #EEF3F8; border-left: 4px solid #7C8EA3;
}
.s360-sim-baseline-block .title {
    font-size: 0.66rem; color: #4A5568; text-transform: uppercase;
    letter-spacing: 0.6px; font-weight: 700;
}
.s360-sim-baseline-block .value {
    font-size: 1.55rem; font-weight: 700; color: #1A2B47;
    margin-top: 6px; line-height: 1.1;
}
.s360-sim-baseline-block .meta {
    font-size: 0.72rem; color: #718096; margin-top: 4px; line-height: 1.4;
}

/* ---- Governed Target / Target Band card (neutral, parallel to baseline-block) ---- */
.s360-sim-target-card {
    display: block;
    border: 1px solid #DDE3EC;
    border-left: 4px solid #0288D1;
    border-radius: 8px;
    padding: 12px 14px;
    background: #ffffff;
    box-shadow: 0 1px 4px rgba(0,0,0,0.03);
    box-sizing: border-box;
}
.s360-sim-target-card .title {
    font-size: 0.66rem; color: #4A5568; text-transform: uppercase;
    letter-spacing: 0.6px; font-weight: 700;
}
.s360-sim-target-card .value {
    font-size: 1.55rem; font-weight: 700; color: #1A2B47;
    margin-top: 6px; line-height: 1.1;
}
.s360-sim-target-card .meta {
    font-size: 0.72rem; color: #718096; margin-top: 4px; line-height: 1.4;
}
.s360-sim-target-card .provisional {
    font-size: 0.72rem; color: #6A1B9A; margin-top: 6px;
    font-style: italic;
}

/* Compact gap-to-target line appended to the Do-Nothing card */
.s360-sim-do-nothing-gap {
    font-size: 0.78rem;
    margin-top: 6px;
    color: #1A2B47;
}
.s360-sim-do-nothing-gap .gap-on { color: #2E7D32; font-weight: 700; }
.s360-sim-do-nothing-gap .gap-off { color: #C62828; font-weight: 700; }
.s360-sim-do-nothing-gap .gap-band { color: #1565C0; font-weight: 700; }

/* ---- Scenario comparator cards (3 tinted variants) ---- */
.s360-sim-scenario-card {
    border: 1px solid #DDE3EC; border-radius: 8px;
    padding: 12px 14px 8px 14px; background: #ffffff;
    box-shadow: 0 1px 4px rgba(0,0,0,0.03);
    border-left-width: 4px; border-left-style: solid;
    margin-bottom: 8px;
}
.s360-sim-scenario-card.minimum     { background: #EAF4FF; border-left-color: #2F80ED; }
.s360-sim-scenario-card.recommended { background: #EAF8F4; border-left-color: #2E9F6B; }
.s360-sim-scenario-card.intensive   { background: #FFF4E5; border-left-color: #F59E0B; }
.s360-sim-scenario-card.selected {
    border: 2px solid #0288D1;
    box-shadow: 0 6px 18px rgba(2,136,209,0.28);
}

/* ---- Scenario selector buttons (active vs inactive) ---- */
.s360-sim-btn-active .stButton > button {
    background: #0B1E3D !important;
    color: #ffffff !important;
    border: 2px solid #0288D1 !important;
    font-weight: 800 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.4px !important;
    box-shadow: 0 4px 10px rgba(11,30,61,0.35) !important;
}
.s360-sim-btn-active .stButton > button:hover {
    background: #1A2B47 !important;
    color: #ffffff !important;
    border-color: #0288D1 !important;
}
.s360-sim-btn-inactive .stButton > button {
    background: #ffffff !important;
    color: #1A2B47 !important;
    border: 1px solid #DDE3EC !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
}
.s360-sim-btn-inactive .stButton > button:hover {
    background: #F4F7FB !important;
    color: #0B1E3D !important;
    border-color: #0288D1 !important;
}
.s360-sim-scenario-card .badge {
    display: inline-block; font-size: 0.6rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.5px;
    padding: 2px 8px; border-radius: 999px;
    background: #0B1E3D; color: #ffffff;
    margin-left: 6px; vertical-align: middle;
}
.s360-sim-scenario-card .title {
    font-size: 0.66rem; color: #4A5568; text-transform: uppercase;
    letter-spacing: 0.6px; font-weight: 700;
}
.s360-sim-scenario-card .value {
    font-size: 1.4rem; font-weight: 700; color: #1A2B47;
    margin-top: 4px; line-height: 1.1;
}
.s360-sim-scenario-card .change {
    font-size: 0.85rem; font-weight: 600; margin-top: 4px;
}
.s360-sim-scenario-card .change.positive { color: #198754; }
.s360-sim-scenario-card .change.negative { color: #dc3545; }
.s360-sim-scenario-card .meta {
    font-size: 0.72rem; color: #718096; margin-top: 4px; line-height: 1.4;
}

/* Prominent Action line inside scenario card */
.s360-sim-action {
    font-size: 1.0rem; font-weight: 700; color: #0B1E3D;
    margin-top: 10px; margin-bottom: 6px; padding: 8px 10px;
    background: rgba(255,255,255,0.7); border-left: 3px solid #0288D1;
    border-radius: 3px; line-height: 1.3;
}
.s360-sim-action .label {
    font-size: 0.62rem; font-weight: 700; color: #1565C0;
    text-transform: uppercase; letter-spacing: 0.6px; margin-right: 6px;
}

.s360-sim-scenario-unavailable {
    border: 1px dashed #adb5bd; background: #F5F7FA; color: #4A5568;
    border-radius: 8px; padding: 12px 14px; margin: 6px 0 10px 0;
}
.s360-sim-scenario-unavailable .title {
    font-size: 0.7rem; font-weight: 700; color: #4A5568;
    text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 4px;
}
.s360-sim-scenario-unavailable .meta {
    font-size: 0.8rem; color: #4A5568; line-height: 1.4;
}

/* ---- Baseline vs Selected Scenario — before/after comparison visual ---- */
.s360-sim-compare {
    display: grid; grid-template-columns: 1fr auto 1fr; gap: 12px;
    align-items: center; background: #ffffff;
    border: 1px solid #DDE3EC; border-radius: 8px;
    padding: 14px 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.03);
    margin-top: 6px;
}
.s360-sim-compare-card {
    background: #F5F7FA; border: 1px solid #DDE3EC;
    border-radius: 6px; padding: 10px 12px; text-align: center;
}
.s360-sim-compare-card.scenario {
    background: #EAF4FF; border-color: #BBDEFB; border-left: 4px solid #2F80ED;
}
.s360-sim-compare-card .label {
    font-size: 0.62rem; color: #4A5568; text-transform: uppercase;
    letter-spacing: 0.6px; font-weight: 700;
}
.s360-sim-compare-card .value {
    font-size: 1.55rem; font-weight: 700; color: #0B1E3D;
    margin-top: 4px; line-height: 1.1;
}
.s360-sim-compare-card .meta {
    font-size: 0.7rem; color: #718096; margin-top: 2px;
}
.s360-sim-compare-arrow {
    font-size: 1.6rem; color: #0288D1; font-weight: 700; text-align: center;
}
.s360-sim-compare-bar {
    margin-top: 8px; background: #ffffff;
    border: 1px solid #DDE3EC; border-radius: 8px;
    padding: 10px 14px; box-shadow: 0 1px 4px rgba(0,0,0,0.03);
}
.s360-sim-compare-bar-track {
    position: relative; height: 8px; background: #EDF2F7;
    border-radius: 999px; margin: 6px 0 8px 0;
}
.s360-sim-compare-bar-track .marker {
    position: absolute; top: 50%;
    transform: translate(-50%, -50%);
    width: 14px; height: 14px; border-radius: 50%;
    border: 2px solid #ffffff; box-shadow: 0 1px 4px rgba(0,0,0,0.2);
}
.s360-sim-compare-bar-track .marker.do-nothing { background: #7C8EA3; }
.s360-sim-compare-bar-track .marker.scenario   { background: #2F80ED; }
.s360-sim-compare-bar-legend {
    display: flex; justify-content: space-between;
    font-size: 0.7rem; color: #4A5568;
}
.s360-sim-compare-delta {
    text-align: center; font-size: 0.95rem; font-weight: 700;
    margin-top: 8px; padding-top: 8px;
    border-top: 1px dashed #EDF2F7;
}
.s360-sim-compare-delta.improvement  { color: #1B5E20; }
.s360-sim-compare-delta.deterioration { color: #B71C1C; }
.s360-sim-compare-delta.neutral { color: #4A5568; }

/* ---- Financial Impact — compact executive cards ---- */
.s360-sim-fin-grid {
    display: grid; grid-template-columns: repeat(2, 1fr);
    gap: 12px; margin-top: 6px;
}
@media (max-width: 880px) { .s360-sim-fin-grid { grid-template-columns: 1fr; } }
.s360-sim-fin-card {
    border: 1px solid #DDE3EC; border-radius: 8px;
    padding: 12px 14px; background: #ffffff;
    box-shadow: 0 1px 4px rgba(0,0,0,0.03);
}
.s360-sim-fin-card .title {
    font-size: 0.62rem; color: #4A5568; text-transform: uppercase;
    letter-spacing: 0.6px; font-weight: 700;
}
.s360-sim-fin-card .value {
    font-size: 1.3rem; font-weight: 700; color: #1A2B47;
    margin-top: 6px; line-height: 1.1;
}
.s360-sim-fin-card .meta {
    font-size: 0.72rem; color: #718096; margin-top: 4px; line-height: 1.4;
}

/* ---- Trade-Off & Displacement Risk — secondary caution card ---- */
.s360-sim-tradeoff {
    background: #FFF8E1; border: 1px solid #F0E0B0;
    border-left: 4px solid #B45309; border-radius: 8px;
    padding: 12px 14px; margin-top: 6px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.03);
}
.s360-sim-tradeoff .title {
    font-size: 0.66rem; color: #B45309; text-transform: uppercase;
    letter-spacing: 0.6px; font-weight: 700; margin-bottom: 6px;
}
.s360-sim-tradeoff .body {
    font-size: 0.85rem; color: #1A2B47; line-height: 1.55;
}
.s360-sim-displacement {
    font-size: 0.78rem; color: #4A5568; margin-top: 6px;
    line-height: 1.5; font-style: italic;
}

/* ---- Management Takeaway — 2-column decision summary ---- */
.s360-sim-takeaway-grid {
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 12px; margin-top: 6px;
}
@media (max-width: 880px) { .s360-sim-takeaway-grid { grid-template-columns: 1fr; } }
.s360-sim-takeaway-col {
    background: #ffffff; border: 1px solid #DDE3EC;
    border-radius: 8px; padding: 12px 14px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.03);
}
.s360-sim-takeaway-col .col-title {
    font-size: 0.62rem; color: #4A5568; text-transform: uppercase;
    letter-spacing: 0.6px; font-weight: 700;
    margin-bottom: 8px; padding-bottom: 6px;
    border-bottom: 1px solid #EDF2F7;
}
.s360-sim-takeaway-row { margin-bottom: 8px; }
.s360-sim-takeaway-row:last-child { margin-bottom: 0; }
.s360-sim-takeaway-row .row-label {
    font-size: 0.62rem; color: #718096; text-transform: uppercase;
    letter-spacing: 0.5px; font-weight: 600; margin-bottom: 2px;
}
.s360-sim-takeaway-row .row-value {
    font-size: 0.85rem; color: #1A2B47; line-height: 1.4; font-weight: 500;
}
.s360-sim-takeaway-row .row-value.recommended-action {
    font-size: 1.0rem; font-weight: 700; color: #0B1E3D;
}

/* ---- Management Takeaway — compact executive synthesis card ---- */
.s360-sim-takeaway-card {
    background: #ffffff; border: 1px solid #DDE3EC;
    border-radius: 8px; padding: 16px 18px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.03);
    margin-top: 6px;
}
.s360-sim-takeaway-header {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 14px; padding-bottom: 10px;
    border-bottom: 1px solid #EDF2F7;
}
.s360-sim-takeaway-header-title {
    font-size: 0.85rem; font-weight: 800; color: #1A2B47;
    text-transform: uppercase; letter-spacing: 0.6px;
}
.s360-sim-takeaway-pill {
    font-size: 0.65rem; font-weight: 700; letter-spacing: 0.5px;
    padding: 3px 10px; border-radius: 999px;
    background: #F59E0B; color: #ffffff; text-transform: uppercase;
}
.s360-sim-takeaway-pill.unavailable { background: #7C8EA3; }
.s360-sim-takeaway-row-compact { margin-bottom: 12px; }
.s360-sim-takeaway-row-compact .label {
    font-size: 0.68rem; color: #718096; text-transform: uppercase;
    letter-spacing: 0.5px; font-weight: 700; margin-bottom: 2px;
}
.s360-sim-takeaway-row-compact .value {
    font-size: 0.95rem; font-weight: 700; color: #1A2B47;
}
.s360-sim-takeaway-metrics {
    display: grid; grid-template-columns: repeat(3, 1fr);
    gap: 12px; margin-bottom: 14px; padding: 10px 0;
    border-top: 1px solid #EDF2F7; border-bottom: 1px solid #EDF2F7;
}
.s360-sim-takeaway-metrics .label {
    font-size: 0.65rem; color: #718096; text-transform: uppercase;
    letter-spacing: 0.5px; font-weight: 700; margin-bottom: 2px;
}
.s360-sim-takeaway-metrics .value {
    font-size: 0.9rem; font-weight: 700; color: #1A2B47;
}

/* ---- Decision Status badge ---- */
.s360-sim-decision-status {
    margin-top: 10px; padding: 10px 14px;
    background: #FFF4E5; border: 1px solid #FCD9A8;
    border-left: 4px solid #F59E0B; border-radius: 8px;
    font-size: 0.9rem; font-weight: 600; color: #1A2B47;
    display: flex; justify-content: space-between; align-items: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.03);
}
.s360-sim-decision-status .pill {
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.6px;
    padding: 3px 10px; border-radius: 999px;
    background: #F59E0B; color: #ffffff; text-transform: uppercase;
}
.s360-sim-decision-status .pill.available { background: #2E9F6B; }
.s360-sim-decision-status .pill.unavailable { background: #7C8EA3; }

/* ---- Decision Review Handoff CTA card ---- */
.s360-sim-cta {
    background: #0B1E3D; border: 1px solid #0B1E3D;
    border-radius: 8px; padding: 18px 20px;
    margin-top: 14px; box-shadow: 0 2px 8px rgba(11,30,61,0.18);
    color: #ffffff;
}
.s360-sim-cta .title { font-size: 1.0rem; font-weight: 700; color: #ffffff; margin-bottom: 4px; }
.s360-sim-cta .help { font-size: 0.85rem; color: rgba(255,255,255,0.78); margin-bottom: 12px; line-height: 1.45; }
.s360-sim-cta .stButton > button {
    background: #0288D1 !important; color: #ffffff !important;
    border: none !important; font-weight: 700 !important;
    font-size: 0.85rem !important; letter-spacing: 0.4px !important;
    text-transform: uppercase !important; padding: 8px 16px !important;
    border-radius: 6px !important;
    box-shadow: 0 2px 6px rgba(2,136,209,0.4) !important;
}
.s360-sim-cta .stButton > button:hover { background: #0277BD !important; }
.s360-sim-cta .saved-note { font-size: 0.78rem; color: #4ADE80; margin-top: 8px; }

.s360-page-scope-note {
    color: #718096; font-size: 0.72rem; font-style: italic;
    margin-top: 16px; padding: 8px 12px; border-top: 1px solid #EDF2F7;
}
.s360-sim-disclaimer { font-size: 0.72rem; color: #718096; margin-top: 6px; font-style: italic; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _month_label(m: int) -> str:
    return f"{calendar.month_abbr[m]}"


def _clean_unit_label(unit: str) -> str:
    """Map raw units to clean display labels."""
    u = (unit or "").strip()
    if u.lower() == "percent":
        return "%"
    if u.lower() == "minutes":
        return "minutes"
    return u


def _format_change_text(value: Optional[float], unit: str) -> str:
    """Return clean change text without raw 'Percent'/'Minutes'."""
    if value is None:
        return ""
    label = _clean_unit_label(unit)
    if label == "%":
        return f"{value:+.1f} percentage points"
    if label == "minutes":
        return f"{value:+.1f} minutes"
    return f"{value:+.1f} {label}"


def _assumption_intensity_line(assumptions: Dict[str, float]) -> str:
    """Render key assumption differences for action intensity display."""
    if not assumptions:
        return ""
    parts = []
    if "additional_staff_count" in assumptions:
        parts.append(f"+{int(assumptions['additional_staff_count'])} staff")
    if "temporary_staff_count" in assumptions:
        parts.append(f"+{int(assumptions['temporary_staff_count'])} temp")
    if "staff_reassignment_count" in assumptions:
        n = int(assumptions.get("staff_reassignment_count", 0))
        if n > 0:
            parts.append(f"+{n} reassign")
    if "service_capacity_change_pct" in assumptions:
        parts.append(f"+{int(assumptions['service_capacity_change_pct'])}% capacity")
    if "throughput_change_pct" in assumptions:
        parts.append(f"+{int(assumptions['throughput_change_pct'])}% throughput")
    if "arrival_change_pct" in assumptions and assumptions.get("arrival_change_pct", 0) != 0:
        parts.append(f"{int(assumptions['arrival_change_pct']):+d}% arrivals")
    duration = assumptions.get("intervention_duration_days")
    if duration:
        parts.append(f"{int(duration)} days")
    return " · ".join(parts)


def _action_detail_for_profile(kpi_id: str, assumptions: Dict[str, float]) -> str:
    """Build the prominent Action line text from governed assumption values."""
    if not assumptions:
        return ""

    parts: list[str] = []

    if kpi_id == "kpi_001":
        if "additional_staff_count" in assumptions:
            parts.append(f"+{int(assumptions['additional_staff_count'])} staff")
        if "temporary_staff_count" in assumptions:
            parts.append(f"+{int(assumptions['temporary_staff_count'])} temp")
        if "staff_reassignment_count" in assumptions:
            n = int(assumptions.get("staff_reassignment_count", 0))
            if n > 0:
                parts.append(f"+{n} reassign")
        if "uncovered_shift_reduction_pct" in assumptions:
            v = float(assumptions["uncovered_shift_reduction_pct"])
            if v != 0:
                parts.append(f"{int(round(v))}% shift coverage")

    elif kpi_id == "kpi_002":
        if "assumed_absenteeism_reduction_pct" in assumptions:
            v = float(assumptions["assumed_absenteeism_reduction_pct"])
            parts.append(f"{int(round(v))}% reduction")
        if "replacement_coverage_pct" in assumptions:
            v = float(assumptions["replacement_coverage_pct"])
            if v > 0:
                parts.append(f"{int(round(v))}% replacement")
        if "contingency_roster_activation_pct" in assumptions:
            v = float(assumptions["contingency_roster_activation_pct"])
            if v > 0:
                parts.append(f"{int(round(v))}% contingency roster")

    elif kpi_id in ("kpi_003", "kpi_004"):
        if "service_capacity_change_pct" in assumptions:
            v = float(assumptions["service_capacity_change_pct"])
            if v != 0:
                parts.append(f"{int(round(v)):+d}% service capacity")
        if "throughput_change_pct" in assumptions:
            v = float(assumptions["throughput_change_pct"])
            if v != 0:
                parts.append(f"{int(round(v)):+d}% throughput")
        if "routing_efficiency_change_pct" in assumptions:
            v = float(assumptions["routing_efficiency_change_pct"])
            if v != 0:
                parts.append(f"{int(round(v)):+d}% routing efficiency")
        if "arrival_change_pct" in assumptions:
            v = float(assumptions["arrival_change_pct"])
            if v != 0:
                parts.append(f"{int(round(v)):+d}% arrivals")
        if "temporary_resource_change" in assumptions:
            v = float(assumptions["temporary_resource_change"])
            if v != 0:
                parts.append(f"{int(round(v)):+d} temp resource")

    duration = assumptions.get("intervention_duration_days")
    if duration:
        parts.append(f"{int(duration)} days")

    return " · ".join(parts)


def _scenario_variant_class(comp_type: str) -> str:
    """Map comparator type to a CSS variant class for the scenario card."""
    if comp_type == "Conservative":
        return "minimum"
    if comp_type == "Expected":
        return "recommended"
    if comp_type == "Higher Intensity":
        return "intensive"
    return ""


# ---------------------------------------------------------------------------
# Governed Target card + Do-Nothing gap helpers (display-only)
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
    threshold_cfg,
    fallback_unit: str = "",
) -> str:
    """Render the governed Target / Target Band HTML card.

    ``threshold_cfg`` is a dictionary keyed by ``kpi_id`` (returned by
    ``load_kpi_threshold_config()``); ``directionality`` values inside the
    dictionary are loader-normalised to one of ``HIGHER_IS_BETTER`` /
    ``LOWER_IS_BETTER`` / ``TARGET_BAND``. Never fabricate a value when the
    governed row is missing or unparsable — return a calm ``Not configured``
    fallback instead.
    """
    cfg = threshold_cfg if isinstance(threshold_cfg, dict) else {}
    row = cfg.get(kpi_id) if kpi_id else None
    if not isinstance(row, dict):
        return (
            '<div class="s360-sim-target-card">'
            '<div class="title">Target</div>'
            '<div class="value" style="color:#6A1B9A;">Not configured</div>'
            '<div class="meta">Governed Green band not yet configured for this KPI.</div>'
            "</div>"
        )

    direction = (row.get("directionality") or "").strip().upper()
    lo = row.get("green_lower_boundary")
    hi = row.get("green_upper_boundary")
    unit = (row.get("unit") or "").strip() or fallback_unit
    is_provisional = bool(row.get("threshold_is_provisional", False))
    review_date = (
        (row.get("required_review_date") or row.get("review_date") or "").strip()
        if is_provisional
        else ""
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
                '<div class="s360-sim-target-card">'
                '<div class="title">Target</div>'
                '<div class="value" style="color:#6A1B9A;">Not configured</div>'
                '<div class="meta">Unknown directionality in threshold config.</div>'
                "</div>"
            )
    except (TypeError, ValueError):
        return (
            '<div class="s360-sim-target-card">'
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
        f'<div class="s360-sim-target-card">'
        f'<div class="title">{label_html}</div>'
        f'<div class="value">{value_html}</div>'
        f'<div class="meta">{caption_html}</div>'
        f'{provisional_html}'
        f"</div>"
    )


def _build_gap_to_target_html(
    forecast_value,
    kpi_id: Optional[str],
    threshold_cfg,
) -> str:
    """Render a compact gap-to-target line comparing the Do-Nothing forecast
    to the governed Green band. Returns an empty string if no comparison can
    be made. Written in full ("percentage points") — never abbreviated.
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
    unit = (row.get("unit") or "").strip()

    try:
        fv = float(forecast_value)
    except (TypeError, ValueError):
        return ""

    unit_word = _gap_unit_word(unit)
    gap_unit = unit_word if unit_word else "points"

    if direction == "HIGHER_IS_BETTER":
        if lo is None:
            return ""
        if fv < float(lo):
            diff = float(lo) - fv
            diff_str = format_unit_value(diff, unit)
            return (
                f'<div class="s360-sim-do-nothing-gap">'
                f'<span class="gap-off">{diff_str} {gap_unit} below target</span>'
                f"</div>"
            )
        return (
            f'<div class="s360-sim-do-nothing-gap">'
            f'<span class="gap-on">On target</span>'
            f"</div>"
        )

    if direction == "LOWER_IS_BETTER":
        if hi is None:
            return ""
        if fv > float(hi):
            diff = fv - float(hi)
            diff_str = format_unit_value(diff, unit)
            return (
                f'<div class="s360-sim-do-nothing-gap">'
                f'<span class="gap-off">{diff_str} {gap_unit} above target</span>'
                f"</div>"
            )
        return (
            f'<div class="s360-sim-do-nothing-gap">'
            f'<span class="gap-on">On target</span>'
            f"</div>"
        )

    if direction == "TARGET_BAND":
        if lo is None or hi is None:
            return ""
        # Boundary rule: inclusive lower, exclusive upper
        if fv >= float(lo) and fv < float(hi):
            return (
                f'<div class="s360-sim-do-nothing-gap">'
                f'<span class="gap-band">Within target band</span>'
                f"</div>"
            )
        if fv < float(lo):
            diff = float(lo) - fv
            diff_str = format_unit_value(diff, unit)
            return (
                f'<div class="s360-sim-do-nothing-gap">'
                f'<span class="gap-off">{diff_str} {gap_unit} below target band</span>'
                f"</div>"
            )
        # fv >= hi
        diff = fv - float(hi)
        diff_str = format_unit_value(diff, unit)
        return (
            f'<div class="s360-sim-do-nothing-gap">'
            f'<span class="gap-off">{diff_str} {gap_unit} above target band</span>'
            f"</div>"
        )

    return ""


def _format_value_str(value: Optional[float], unit: str) -> str:
    """Render a single KPI value with its unit (clean labels)."""
    if value is None:
        return "Not available"
    unit_label = _clean_unit_label(unit)
    num_str = f"{value:,.2f}".rstrip("0").rstrip(".")
    if unit_label == "%":
        return f"{num_str}%"
    if unit_label == "minutes":
        return f"{num_str} minutes"
    return f"{num_str} {unit_label}".strip()


def _render_baseline_block(
    title: str,
    value: Optional[float],
    unit: str,
    meta_lines: list,
    variant: str = "",
) -> None:
    value_str = _format_value_str(value, unit)
    meta_html = "\n".join(f'<div class="meta">{line}</div>' for line in meta_lines)
    variant_class = f' {variant}' if variant else ''
    st.markdown(
        f"""
<div class="s360-sim-baseline-block{variant_class}">
  <div class="title">{title}</div>
  <div class="value">{value_str}</div>
  {meta_html}
</div>
""",
        unsafe_allow_html=True,
    )


def _render_scenario_card(
    title: str,
    scenario_value: Optional[float],
    baseline_value: Optional[float],
    unit: str,
    status: str,
    confidence: str,
    selected: bool,
    intensity_line: str = "",
    capped_note: str = "",
    action_detail: str = "",
    variant: str = "",
) -> None:
    sel_class = " selected" if selected else ''
    variant_class = f' {variant}' if variant else ''
    value_str = _format_value_str(scenario_value, unit)

    change_html = ""
    if scenario_value is not None and baseline_value is not None:
        diff = scenario_value - baseline_value
        change_str = _format_change_text(diff, unit)
        change_class = "positive" if diff < 0 else "negative" if diff > 0 else ""
        change_html = f'<div class="change {change_class}">{change_str}</div>'

    if action_detail:
        action_html = (
            f'<div class="s360-sim-action">'
            f'<span class="label">Action</span>'
            f'{action_detail}'
            f'</div>'
        )
    else:
        action_html = ""
    intensity_html = (
        f'<div class="meta">{intensity_line}</div>' if intensity_line and not action_detail else ""
    )
    capped_html = f'<div class="meta" style="color:#0d6efd;">{capped_note}</div>' if capped_note else ""

    selected_badge = '<span class="badge">Selected</span>' if selected else ''

    st.markdown(
        f"""
<div class="s360-sim-scenario-card{variant_class}{sel_class}">
  <div class="title">{title}{selected_badge}</div>
  <div class="value">{value_str}</div>
  {change_html}
  {action_html}
  {intensity_html}
  {capped_html}
  <div class="meta">Status: {status}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def _render_financial_card(title: str, value_str: str, meta: str = "") -> None:
    meta_html = f'<div class="meta">{meta}</div>' if meta else ""
    st.markdown(
        f"""
<div class="s360-sim-fin-card">
  <div class="title">{title}</div>
  <div class="value">{value_str}</div>
  {meta_html}
</div>
""",
        unsafe_allow_html=True,
    )


def _render_productivity_cylinder(label: str, coverage_pct: Optional[float], capacity_hours: Optional[float]) -> str:
    """Return compact SVG cylinder HTML for Simulation Lab productivity comparison."""
    if coverage_pct is None:
        return (
            f'<div style="text-align:center;padding:12px;">'
            f'<div style="font-size:0.65rem;color:#718096;text-transform:uppercase;letter-spacing:0.5px;font-weight:700;">{label}</div>'
            f'<div style="font-size:0.85rem;color:#718096;margin-top:8px;">Not available</div>'
            f'</div>'
        )

    _visual_pct = max(0.0, min(float(coverage_pct), 100.0))
    _fill_ratio = _visual_pct / 100.0

    _svg_w, _svg_h = 180, 260
    _top_y, _bottom_y = 22, 215
    _usable_h = _bottom_y - _top_y
    _fill_h = _usable_h * _fill_ratio
    _fill_y = _bottom_y - _fill_h

    _cx = 90
    _rx = 45
    _ry = 12
    _x = _cx - _rx
    _uid = "dn" if "Nothing" in label else "sc"

    capacity_str = f"{capacity_hours:,.0f} staff-hours" if capacity_hours is not None else ""

    html = (
        f'<div style="text-align:center;">'
        f'<div style="font-size:0.68rem;color:#718096;text-transform:uppercase;letter-spacing:0.5px;font-weight:700;margin-bottom:6px;">{label}</div>'
        f'<svg viewBox="0 0 {_svg_w} {_svg_h}" width="160" height="230" xmlns="http://www.w3.org/2000/svg" style="display:block;margin:0 auto;">'
        f'<defs>'
        f'<linearGradient id="simFill{_uid}" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0%" stop-color="#1f5fae"/>'
        f'<stop offset="50%" stop-color="#3278d4"/>'
        f'<stop offset="100%" stop-color="#1d5ca8"/>'
        f'</linearGradient>'
        f'<linearGradient id="simEmpty{_uid}" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0%" stop-color="#e2e8f0"/>'
        f'<stop offset="50%" stop-color="#eef3f8"/>'
        f'<stop offset="100%" stop-color="#e2e8f0"/>'
        f'</linearGradient>'
        f'</defs>'
        f'<rect x="{_x}" y="{_top_y}" width="{_rx*2}" height="{_fill_y - _top_y}" fill="url(#simEmpty{_uid})"/>'
        f'<rect x="{_x}" y="{_fill_y}" width="{_rx*2}" height="{_fill_h}" fill="url(#simFill{_uid})"/>'
        f'<ellipse cx="{_cx}" cy="{_fill_y}" rx="{_rx}" ry="{_ry}" fill="#3278d4"/>'
        f'<rect x="{_x}" y="{_top_y}" width="{_rx*2}" height="{_usable_h}" fill="none" stroke="#9aa8b8" stroke-width="1.2"/>'
        f'<ellipse cx="{_cx}" cy="{_top_y}" rx="{_rx}" ry="{_ry}" fill="#f7f9fc" fill-opacity="0.70" stroke="#9aa8b8" stroke-width="1.2"/>'
        f'<ellipse cx="{_cx}" cy="{_bottom_y}" rx="{_rx}" ry="{_ry}" fill="#1e5ca5"/>'
        f'<ellipse cx="{_cx}" cy="{_bottom_y}" rx="{_rx}" ry="{_ry}" fill="none" stroke="#8291a3" stroke-width="1.2"/>'
        f'<text x="145" y="{_top_y + 4}" font-size="10" fill="#718096" font-family="Inter,sans-serif">100%</text>'
        f'<text x="145" y="{_fill_y + 4}" font-size="10" fill="#1A202C" font-weight="600" font-family="Inter,sans-serif">{_visual_pct:.1f}%</text>'
        f'<text x="145" y="{_bottom_y + 4}" font-size="10" fill="#718096" font-family="Inter,sans-serif">0%</text>'
        f'<line x1="138" y1="{_top_y}" x2="142" y2="{_top_y}" stroke="#CBD5E0" stroke-width="1"/>'
        f'<line x1="138" y1="{_fill_y}" x2="142" y2="{_fill_y}" stroke="#3278d4" stroke-width="1.2"/>'
        f'<line x1="138" y1="{_bottom_y}" x2="142" y2="{_bottom_y}" stroke="#CBD5E0" stroke-width="1"/>'
        f'</svg>'
    )
    if capacity_str:
        html += f'<div style="font-size:0.78rem;color:#4A5568;margin-top:4px;font-weight:600;">{capacity_str}</div>'
    html += '</div>'
    return html


# ---------------------------------------------------------------------------
# Management decision table renderer (signature/structure preserved for tests)
# ---------------------------------------------------------------------------
_STATUS_PHRASE_FOR_TAKEAWAY = {
    "ABOVE_TARGET": "current forecast exceeds target",
    "TARGET_MET": "current forecast meets target",
    "BELOW_TARGET": "current forecast is below target",
    "NEEDS_REVIEW": "current forecast needs review",
    "CAUTION": "current forecast is in caution",
    "ALERT": "current forecast is in alert",
}

_comp_label_for_table: str = ""


def comp_label_for_table() -> str:
    return _comp_label_for_table


def _why_act_now_text(kpi_id: str, scenario_val: Optional[float], forecast_val: Optional[float]) -> str:
    """Return a short 'Why Act Now' sentence based on governed status logic."""
    target = scenario_val if scenario_val is not None else forecast_val
    if target is None:
        return "Forecast is indicative under governed analytical assumptions."
    try:
        from src.simulation_lab_controller import _get_status_for_value
        _txt, status_code = _get_status_for_value(kpi_id, target)
    except Exception:
        status_code = ""
    phrase = _STATUS_PHRASE_FOR_TAKEAWAY.get(
        status_code, "current forecast signals operational pressure"
    )
    if status_code in ("BELOW_TARGET", "NEEDS_REVIEW", "CAUTION", "ALERT"):
        return f"{phrase.capitalize()} \u2014 do-nothing forecast remains below target."
    return f"{phrase.capitalize()} under the {comp_label_for_table()} scenario."


def _expected_impact_text(
    kpi_name: str,
    baseline_unit: str,
    forecast_value: Optional[float],
    forecast_unit: str,
    scenario_val: Optional[float],
) -> str:
    """Build the expected operational impact sentence with clean units."""
    forecast_str = (
        format_unit_value(forecast_value, forecast_unit)
        if forecast_value is not None
        else "Not available"
    )
    if scenario_val is not None:
        scenario_str = format_unit_value(scenario_val, baseline_unit)
        return f"{kpi_name} improves from {forecast_str} to {scenario_str} under the selected intervention."
    return f"{kpi_name} impact is indicative under governed analytical assumptions."


def _financial_view_text(financial: Optional[Dict[str, Any]]) -> str:
    """Build the financial view row text from the new adapter dict format."""
    if financial is None or not isinstance(financial, dict):
        return "Financial impact is not available under the current governed mapping."
    if financial.get("total_cost") is not None:
        cost = float(financial.get("total_cost", 0))
        currency = financial.get("currency", "MYR")
        days = int(financial.get("duration_days", 0) or 0)
        return (
            f"Estimated Intervention Cost: {currency} {cost:,.0f} over {days} days. "
            f"Causality: Estimated. Confidence: Moderate."
        )
    if financial.get("available"):
        cost = float(financial.get("cost", 0))
        return f"Estimated Intervention Cost: RM {cost:,.0f}. Causality: Estimated. Confidence: Moderate."
    return "Financial impact is not available under the current governed mapping."


def _render_decision_table(
    kpi_id: str,
    kpi_name: str,
    action_strategy: str,
    selected_action_level: str,
    comp_label: str,
    baseline_unit: str,
    forecast_value: Optional[float],
    forecast_unit: str,
    scenario_val: Optional[float],
    resource_line: str,
    financial: Optional[Dict[str, Any]],
    action_detail: str = "",
    capacity_gain_hours: Optional[float] = None,
) -> None:
    """Render the Management Takeaway as a compact executive decision synthesis."""
    global _comp_label_for_table
    _comp_label_for_table = comp_label

    def _compact_cost(financial: Optional[Dict[str, Any]]) -> str:
        if financial is None or not isinstance(financial, dict):
            return "Not available"
        if financial.get("total_cost") is not None:
            cost = float(financial.get("total_cost", 0))
            currency = financial.get("currency", "MYR")
            days = int(financial.get("duration_days", 0) or 0)
            if days > 0:
                return f"{currency} {cost:,.0f} \u00b7 {days} days"
            return f"{currency} {cost:,.0f}"
        if financial.get("available"):
            cost = float(financial.get("cost", 0))
            return f"RM {cost:,.0f}"
        return "Not available"

    scenario_available = scenario_val is not None
    decision_status = _FINANCIAL_DISPLAY_RULES.get("decision_status", "PENDING MANAGEMENT REVIEW")
    pill_class = ""

    if not scenario_available:
        decision_status = "Not Available"
        pill_class = "unavailable"

    action_label = (comp_label or selected_action_level or "Selected Action").upper()

    forecast_str = format_unit_value(forecast_value, forecast_unit) if forecast_value is not None else "\u2014"
    scenario_str = format_unit_value(scenario_val, baseline_unit) if scenario_val is not None else "\u2014"
    outcome_str = f"{forecast_str} \u2192 {scenario_str}"
    cost_str = _compact_cost(financial)

    cap_gain_str = ""
    if capacity_gain_hours is not None:
        cap_sign = "+" if capacity_gain_hours > 0 else ""
        cap_gain_str = f"{cap_sign}{capacity_gain_hours:,.0f} staff-hours"

    decision_text = "Review this intervention for management approval."
    if not scenario_available:
        decision_text = "Decision support is not available for this scenario because the expected operational impact could not be calculated."
        outcome_str = "Not available"
        cost_str = "Not available"
        action_label = "NOT AVAILABLE"

    metrics_html = ""
    if scenario_available:
        metrics_html = (
            '<div class="s360-sim-takeaway-metrics">'
            f'<div><div class="label">Expected Outcome</div><div class="value">{outcome_str}</div></div>'
            f'<div><div class="label">Capacity Gain</div><div class="value">{cap_gain_str if cap_gain_str else "\u2014"}</div></div>'
            f'<div><div class="label">Estimated Cost</div><div class="value">{cost_str}</div></div>'
            "</div>"
        )

    st.markdown(
        f"""
<div class="s360-sim-takeaway-card">
  <div class="s360-sim-takeaway-header">
    <div class="s360-sim-takeaway-header-title">Management Takeaway</div>
    <span class="s360-sim-takeaway-pill {pill_class}">{decision_status}</span>
  </div>
  <div class="s360-sim-takeaway-row-compact">
    <div class="label">Selected Intervention</div>
    <div class="value">{action_label}</div>
  </div>
  {metrics_html}
  <div class="s360-sim-takeaway-row-compact">
    <div class="label">Decision Required</div>
    <div class="value">{decision_text}</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Branded header renderer
# ---------------------------------------------------------------------------
def _render_header(jcorp_uri: str, bsp_uri: str) -> None:
    st.markdown(
        f"""
<div class="s360-sim-header">
    <div class="s360-sim-header-left">
        <div class="s360-sim-header-brand">
            <span class="s360-sim-header-brand-name">Sentinel360 Healthcare</span>
            <span class="s360-sim-header-version">1.0</span>
        </div>
        <div class="s360-sim-header-page-title">Simulation Lab</div>
        <div class="s360-sim-header-subtitle">Intelligent Early Warning System for Organisational Performance</div>
    </div>
    <div class="s360-sim-header-right">
        <div class="s360-sim-logo-cell jcorp">
            <img src="{jcorp_uri}" alt="JCORP" />
        </div>
        <div class="s360-sim-logo-cell bsp">
            <img src="{bsp_uri}" alt="Black Swan Protocol" />
        </div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Sidebar filter pane \u2014 SIMULATION CONTROLS highlight
# ---------------------------------------------------------------------------
def _render_sidebar_controls_header() -> None:
    st.sidebar.markdown(
        '<div class="s360-sim-controls-heading">Simulation Controls</div>',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        '<div class="s360-sim-controls-help">Select the context below to generate the applicable scenario comparison.</div>',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        '<div class="s360-sim-controls-flow">Hospital &rarr; Department &rarr; Forecast Month &rarr; KPI</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Session state init
# ---------------------------------------------------------------------------
for key in ["sim_selected_comparator_index", "sim_scenario_saved"]:
    if key not in st.session_state:
        st.session_state[key] = 0 if key == "sim_selected_comparator_index" else False

# ---------------------------------------------------------------------------
# Branded header
# ---------------------------------------------------------------------------
jcorp_uri = _logo_data_uri("jcorp_logo.png")
bsp_uri = _logo_data_uri("black_swan_protocol_logo.png")
_render_header(jcorp_uri, bsp_uri)

# ---------------------------------------------------------------------------
# Filters (sidebar)
# ---------------------------------------------------------------------------
options = get_filter_options()

with st.sidebar:
    _render_sidebar_controls_header()
    hospital_id = st.selectbox(
        "Hospital",
        options=options["hospitals"],
        index=0 if options["hospitals"] else None,
        key="sim_hospital",
    )
    department_id = st.selectbox(
        "Department",
        options=options["departments"],
        index=0 if options["departments"] else None,
        key="sim_department",
        format_func=_display_department,
    )
    forecast_month = st.selectbox(
        "Forecast Month",
        options=options["months"],
        format_func=_month_label,
        index=len(options["months"]) - 1 if options["months"] else None,
        key="sim_month",
    )
    kpi_options = {k["name"]: k["id"] for k in options["kpis"]}
    kpi_name = st.selectbox(
        "KPI",
        options=list(kpi_options.keys()),
        index=0,
        key="sim_kpi_name",
    )
    kpi_id = kpi_options.get(kpi_name, "")

# ---------------------------------------------------------------------------
# Derive Action Strategy from governed KPI mapping
# ---------------------------------------------------------------------------
action_strategy = _KPI_TO_ACTION_STRATEGY.get(kpi_id, "Clinical Operational Adjustment")

_KPI_TO_DEFAULT_INTERVENTION = {
    "kpi_001": "INT-STAFF-001",
    "kpi_002": "INT-ABS-001",
    "kpi_003": "INT-FLOW-001",
    "kpi_004": "INT-FLOW-001",
}
intervention_id = _KPI_TO_DEFAULT_INTERVENTION.get(kpi_id, "INT-STAFF-001")

# ---------------------------------------------------------------------------
# Build simulation state
# ---------------------------------------------------------------------------
with st.spinner("Running scenario analysis..."):
    state = build_simulation_state(
        hospital_id=hospital_id,
        department_id=department_id,
        kpi_id=kpi_id,
        forecast_month=forecast_month,
        intervention_id=intervention_id,
    )

# ---------------------------------------------------------------------------
# Simulation eligibility gate
# ---------------------------------------------------------------------------
_baseline_ok = state.get("baseline") is not None and state.get("baseline_value") is not None
_forecast_ok = state.get("forecast_value") is not None
_mapping_ok = bool(state.get("comparator_profiles"))

if not (_baseline_ok and _forecast_ok and _mapping_ok):
    st.markdown(
        """
<div style="
    border: 2px solid #dc3545;
    border-radius: 6px;
    padding: 24px 20px;
    background: #fff5f5;
    text-align: center;
    margin-top: 24px;
">
  <div style="font-size: 1.5rem; font-weight: 800; color: #dc3545; letter-spacing: 0.04em;">
    SIMULATION NOT AVAILABLE
  </div>
  <div style="font-size: 0.95rem; color: #6c757d; margin-top: 10px;">
    Simulation requires a valid baseline, forecast, and scenario mapping for the selected
    department, KPI, and forecast month.<br>
    Please select a different combination from the sidebar filters.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.stop()

# ---------------------------------------------------------------------------
# Action Strategy display (light-blue card)
# ---------------------------------------------------------------------------
st.markdown(
    f"""
<div class="s360-sim-strategy">
    <div class="label">Action Strategy</div>
    <div class="value">{action_strategy}</div>
    <div class="sub">Governed intervention family for the selected Department.</div>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Baseline \u2014 two side-by-side cards
# ---------------------------------------------------------------------------
st.markdown('<div class="s360-sim-section">Target vs Do-Nothing Forecast</div>', unsafe_allow_html=True)

baseline = state.get("baseline")
baseline_value = state.get("baseline_value")
baseline_unit = state.get("baseline_unit", "")
baseline_date = state.get("baseline_date")
forecast_value = state.get("forecast_value")
forecast_unit = state.get("forecast_unit", "")
forecast_warning = state.get("forecast_warning", "Monitoring")
bl_status = state.get("baseline_status", "Not Assessable")
fc_status = state.get("forecast_status", "Not Assessable")

bl_month_label = ""
if baseline_date and "-" in baseline_date:
    try:
        parts = baseline_date.split("-")
        bl_month_label = f"{calendar.month_abbr[int(parts[1])].upper()} {parts[0]}"
    except (ValueError, IndexError):
        bl_month_label = baseline_date

fc_month_label = f"{calendar.month_abbr[forecast_month].upper()} {GOVERNED_ACTUAL_YEAR}"

# Load governed threshold config once for the target card + gap line.
_threshold_cfg = load_kpi_threshold_config()
_target_card_html = _build_target_card_html(
    kpi_id=kpi_id,
    threshold_cfg=_threshold_cfg,
    fallback_unit=baseline_unit,
)
_gap_html = _build_gap_to_target_html(
    forecast_value=forecast_value,
    kpi_id=kpi_id,
    threshold_cfg=_threshold_cfg,
)

st.markdown('<div class="s360-sim-baseline-grid">', unsafe_allow_html=True)
col_l, col_r = st.columns(2)
with col_l:
    # Governed Target / Target Band replaces the historical-actual comparator
    # for this top section. Underlying baseline / baseline_value variables
    # above remain available for downstream state and scenario code.
    st.markdown(_target_card_html, unsafe_allow_html=True)
with col_r:
    _render_baseline_block(
        title="Forecast \u2014 Do Nothing",
        value=forecast_value,
        unit=forecast_unit,
        meta_lines=[
            f"Forecast month: {fc_month_label}",
            f"Warning: {forecast_warning}",
            f"Forecast status: {fc_status}",
        ],
        variant="do-nothing",
    )
    if _gap_html:
        st.markdown(_gap_html, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Scenario comparator cards (3 tinted variants)
# ---------------------------------------------------------------------------
st.markdown('<div class="s360-sim-section">Indicative Scenario Comparators</div>', unsafe_allow_html=True)

profiles = state.get("comparator_profiles", [])
scenario_results = state.get("scenario_results", [])

if not profiles:
    st.warning("No comparator profiles available for this KPI.")
    st.stop()

cols = st.columns(len(profiles))
for idx, (col, profile, result) in enumerate(zip(cols, profiles, scenario_results)):
    with col:
        comp_type = profile["comparator_type"]
        comp_label = _DISPLAY_LABEL_FOR_COMPARATOR_ID.get(comp_type, comp_type)
        scenario_val = result.scenario_primary_kpi_value if result else None
        scenario_available = result is not None and scenario_val is not None
        status = "Not Assessable"
        confidence = "Moderate"
        if result:
            from src.simulation_lab_controller import _get_status_for_value
            status, _ = _get_status_for_value(kpi_id, scenario_val)
            raw_conf = str(result.final_scenario_confidence) if result.final_scenario_confidence else "Moderate"
            if "." in raw_conf:
                raw_conf = raw_conf.split(".")[-1]
            confidence = raw_conf.replace("_", " ").title()

        selected = st.session_state.sim_selected_comparator_index == idx

        btn_wrapper_class = "s360-sim-btn-active" if selected else "s360-sim-btn-inactive"
        st.markdown(f'<div class="{btn_wrapper_class}">', unsafe_allow_html=True)
        btn_label = f"\u2713 {comp_label} Selected" if selected else f"Select {comp_label}"
        if st.button(btn_label, key=f"sim_btn_{idx}", use_container_width=True):
            st.session_state.sim_selected_comparator_index = idx
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        if not scenario_available:
            st.markdown(
                """
<div class="s360-sim-scenario-unavailable">
  <div class="title">SCENARIO NOT AVAILABLE</div>
  <div class="meta">Expected operational impact cannot be calculated for this department / KPI / forecast-month combination.</div>
</div>
""",
                unsafe_allow_html=True,
            )
            continue

        all_vals = [r.scenario_primary_kpi_value for r in scenario_results if r]
        intensity_line = _assumption_intensity_line(profile.get("assumptions", {}))
        action_detail = _action_detail_for_profile(kpi_id, profile.get("assumptions", {}))
        capped_note = ""
        if (
            all_vals
            and len(set(round(v, 2) for v in all_vals if v is not None)) == 1
            and scenario_val is not None
        ):
            capped_note = "KPI reaches a governed ceiling \u2014 compare action intensity below."

        variant_class = _scenario_variant_class(comp_type)

        _render_scenario_card(
            title=comp_label,
            scenario_value=scenario_val,
            baseline_value=forecast_value,
            unit=baseline_unit,
            status=status,
            confidence=confidence,
            selected=selected,
            intensity_line=intensity_line,
            capped_note=capped_note,
            action_detail=action_detail,
            variant=variant_class,
        )

# ---------------------------------------------------------------------------
# Selected scenario detail
# ---------------------------------------------------------------------------
sel_idx = st.session_state.sim_selected_comparator_index
sel_profile = profiles[sel_idx] if sel_idx < len(profiles) else profiles[0]
sel_result = scenario_results[sel_idx] if sel_idx < len(scenario_results) else None
sel_financial = (
    state.get("financial_results", [])[sel_idx]
    if sel_idx < len(state.get("financial_results", []))
    else None
)

comp_type = sel_profile["comparator_type"]
comp_label = _DISPLAY_LABEL_FOR_COMPARATOR_ID.get(comp_type, comp_type)
scenario_val = sel_result.scenario_primary_kpi_value if sel_result else None

st.markdown(
    f'<div class="s360-sim-section">Baseline vs {comp_label} Scenario</div>',
    unsafe_allow_html=True,
)

sel_scenario_available = sel_result is not None and scenario_val is not None

if not sel_scenario_available:
    st.markdown(
        """
<div class="s360-sim-scenario-unavailable">
  <div class="title">EXPECTED IMPACT NOT AVAILABLE</div>
  <div class="meta">No supported scenario result is available for the selected context.</div>
</div>
""",
        unsafe_allow_html=True,
    )
else:
    do_nothing_str = _format_value_str(forecast_value, forecast_unit)
    scenario_str = _format_value_str(scenario_val, baseline_unit)
    scenario_status = "Not Assessable"
    if sel_result:
        from src.simulation_lab_controller import _get_status_for_value
        scenario_status, _ = _get_status_for_value(kpi_id, scenario_val)

    if forecast_value is not None and scenario_val is not None:
        lo = min(forecast_value, scenario_val)
        hi = max(forecast_value, scenario_val)
        span = (hi - lo) if hi != lo else None
        if span is None or span == 0:
            dn_pct = 50.0
            sc_pct = 50.0
        else:
            dn_pct = (forecast_value - lo) / span * 100.0
            sc_pct = (scenario_val - lo) / span * 100.0

        diff = scenario_val - forecast_value
        change_str = _format_change_text(diff, baseline_unit)
        if diff < 0:
            delta_class = "improvement"
        elif diff > 0:
            delta_class = "deterioration"
        else:
            delta_class = "neutral"
    else:
        dn_pct = sc_pct = 50.0
        change_str = "Not available"
        delta_class = "neutral"

    st.markdown(
        f"""
<div class="s360-sim-compare">
    <div class="s360-sim-compare-card">
        <div class="label">Do Nothing</div>
        <div class="value">{do_nothing_str}</div>
        <div class="meta">Forecast month: {fc_month_label} \u00b7 Status: {fc_status}</div>
    </div>
    <div class="s360-sim-compare-arrow">&rarr;</div>
    <div class="s360-sim-compare-card scenario">
        <div class="label">{comp_label} Scenario</div>
        <div class="value">{scenario_str}</div>
        <div class="meta">Indicative Scenario \u00b7 Status: {scenario_status}</div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Estimated Productivity Impact
# ---------------------------------------------------------------------------
st.markdown('<div class="s360-sim-section">Estimated Productivity Impact</div>', unsafe_allow_html=True)

_is_staffing_context = kpi_id == "kpi_001"

if not _is_staffing_context:
    st.markdown(
        """
<div style="border:1px dashed #adb5bd;background:#F5F7FA;color:#4A5568;border-radius:8px;padding:12px 14px;margin:6px 0 10px 0;">
  <div style="font-size:0.7rem;font-weight:700;color:#4A5568;text-transform:uppercase;letter-spacing:0.6px;margin-bottom:4px;">
    NOT AVAILABLE
  </div>
  <div style="font-size:0.8rem;color:#4A5568;line-height:1.4;">
    Estimated productivity impact is available for staffing-related intervention scenarios only.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
else:
    if not sel_scenario_available or forecast_value is None:
        st.markdown(
            """
<div style="border:1px dashed #adb5bd;background:#F5F7FA;color:#4A5568;border-radius:8px;padding:12px 14px;margin:6px 0 10px 0;">
  <div style="font-size:0.7rem;font-weight:700;color:#4A5568;text-transform:uppercase;letter-spacing:0.6px;margin-bottom:4px;">
    PRODUCTIVITY IMPACT NOT AVAILABLE
  </div>
  <div style="font-size:0.8rem;color:#4A5568;line-height:1.4;">
    Productivity impact not available for the selected scenario context.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
    else:
        # Governed required staff-hours denominator (read-only)
        _prod_required_hours = None
        try:
            from src.productivity_forecast_denominator_policy import ForecastDenominatorCalculator

            _calc = ForecastDenominatorCalculator()
            _denom_result = _calc.calculate(
                hospital_id=hospital_id,
                department_id=department_id,
                target_year=GOVERNED_ACTUAL_YEAR,
            )
            if _denom_result.status == "OK":
                _prod_required_hours = _denom_result.value
        except Exception:
            _prod_required_hours = None

        # UI-ONLY DISPLAY DERIVATION.
        # Converts existing governed coverage percentages into operational
        # staff-hour equivalents for Simulation Lab display only.
        # Does not alter Sentinel360 analytical logic.
        _dn_coverage = forecast_value
        _sc_coverage = scenario_val if scenario_val is not None else _dn_coverage

        _dn_cap_hours = None
        _sc_cap_hours = None
        _cap_delta_hours = None
        if _prod_required_hours is not None:
            _dn_cap_hours = (_dn_coverage / 100.0) * _prod_required_hours
            _sc_cap_hours = (_sc_coverage / 100.0) * _prod_required_hours
            _cap_delta_hours = _sc_cap_hours - _dn_cap_hours

        # UI-ONLY DISPLAY DERIVATION.
        # Converts explicit scenario staff levers into staff-days for display.
        # No new operational assumption is introduced.
        _sel_assumptions = sel_profile.get("assumptions", {})
        _explicit_staff = 0
        if "additional_staff_count" in _sel_assumptions:
            _explicit_staff += int(_sel_assumptions["additional_staff_count"])
        if "temporary_staff_count" in _sel_assumptions:
            _explicit_staff += int(_sel_assumptions["temporary_staff_count"])
        _duration_days = int(_sel_assumptions.get("intervention_duration_days", 0) or 0)
        _equivalent_staff_days = None
        if _explicit_staff > 0 and _duration_days > 0:
            _equivalent_staff_days = _explicit_staff * _duration_days

        _pp_change = _sc_coverage - _dn_coverage
        _delta_color = "#1B5E20" if _pp_change > 0 else "#B71C1C" if _pp_change < 0 else "#4A5568"
        _delta_sign = "+" if _pp_change > 0 else ""
        _action_label = comp_label.upper() if comp_label else "SELECTED ACTION"

        st.markdown(
            '<div style="font-size:0.78rem;color:#4A5568;margin-bottom:10px;">'
            "Shows how the selected intervention may change operational staffing capacity relative to the do-nothing forecast."
            "</div>",
            unsafe_allow_html=True,
        )

        # Two cylinders + central impact (compact layout)
        st.markdown(
            '<div style="background:#ffffff;border:1px solid #DDE3EC;border-radius:8px;padding:14px 16px;box-shadow:0 1px 4px rgba(0,0,0,0.03);margin-bottom:10px;">',
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns([1.1, 0.6, 1.1])
        with c1:
            st.markdown(_render_productivity_cylinder("DO NOTHING", _dn_coverage, _dn_cap_hours), unsafe_allow_html=True)
        with c2:
            _center_html = (
                f'<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;">'
                f'<div style="font-size:1.6rem;color:#0288D1;font-weight:700;">&rarr;</div>'
                f'<div style="font-size:1.0rem;font-weight:700;color:{_delta_color};margin-top:6px;">{_delta_sign}{_pp_change:.1f} pp</div>'
            )
            if _cap_delta_hours is not None:
                _cap_sign = "+" if _cap_delta_hours > 0 else ""
                _center_html += (
                    f'<div style="font-size:0.78rem;color:#4A5568;margin-top:4px;font-weight:600;">'
                    f'{_cap_sign}{_cap_delta_hours:,.0f} staff-hours</div>'
                    f'<div style="font-size:0.68rem;color:#718096;">capacity gain</div>'
                )
            _center_html += '</div>'
            st.markdown(_center_html, unsafe_allow_html=True)
        with c3:
            st.markdown(_render_productivity_cylinder(_action_label, _sc_coverage, _sc_cap_hours), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Compact summary row only
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            _render_financial_card("DO NOTHING", f"{_dn_coverage:.1f}%", meta="Do-nothing forecast coverage")
        with m2:
            _render_financial_card("SELECTED ACTION", f"{_sc_coverage:.1f}%", meta="Scenario forecast coverage")
        with m3:
            _window_str = f"{_duration_days} days" if _duration_days > 0 else "Not available"
            _render_financial_card("INTERVENTION WINDOW", _window_str, meta="Duration from scenario assumptions")
        with m4:
            if _equivalent_staff_days is not None:
                _render_financial_card("INTERVENTION STAFFING VOLUME", f"+{_equivalent_staff_days} staff-days", meta="From explicit staff levers")
            else:
                _render_financial_card("INTERVENTION STAFFING VOLUME", "Not available", meta="No count-based staff values in scenario")

        # Governance footer
        st.markdown(
            '<div style="font-size:0.68rem;color:#A0AEC0;margin-top:8px;font-style:italic;">'
            "Indicative operational capacity translation for decision support. Not a new analytical KPI."
            "</div>",
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# Financial impact
# ---------------------------------------------------------------------------
st.markdown('<div class="s360-sim-section">Financial Impact</div>', unsafe_allow_html=True)

if sel_financial is None:
    st.info("Financial impact is not available under the current governed mapping.")
elif isinstance(sel_financial, dict) and sel_financial.get("available"):
    fin1, fin2, fin3, fin4 = st.columns(4)
    with fin1:
        cost = sel_financial.get("cost", 0)
        _render_financial_card(
            _FINANCIAL_DISPLAY_RULES["cost_label"],
            f"RM {cost:,.0f}",
            meta="Estimated Operational Financial Exposure",
        )
    with fin2:
        benefit = sel_financial.get("benefit", 0)
        _render_financial_card(
            _FINANCIAL_DISPLAY_RULES["benefit_label"],
            f"RM {benefit:,.0f}",
            meta="Governed Analytical Assumption",
        )
    with fin3:
        net = sel_financial.get("net", 0)
        _render_financial_card(
            _FINANCIAL_DISPLAY_RULES["net_label"],
            f"RM {net:,.0f}",
            meta="Not Confirmed causality",
        )
    with fin4:
        roi = sel_financial.get("roi")
        roi_str = f"{roi:.1f}%" if roi is not None else "Not available"
        _render_financial_card(
            _FINANCIAL_DISPLAY_RULES["roi_label"],
            roi_str,
            meta="Moderate confidence",
        )
elif isinstance(sel_financial, dict) and sel_financial.get("total_cost") is not None:
    cost = float(sel_financial.get("total_cost", 0))
    currency = sel_financial.get("currency", "MYR")
    days = int(sel_financial.get("duration_days", 0) or 0)
    drivers = sel_financial.get("cost_drivers", []) or []
    drivers_str = ", ".join(str(d) for d in drivers) if drivers else "Governed analytical assumption"
    st.markdown('<div class="s360-sim-fin-grid">', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        _render_financial_card(
            "Estimated Intervention Cost",
            f"{currency} {cost:,.0f}",
            meta=f"Duration: {days} days \u00b7 Causality: Estimated \u00b7 Confidence: Moderate",
        )
    with col_b:
        _render_financial_card(
            "Cost Drivers",
            drivers_str,
            meta="Governed mapping \u00b7 moderate confidence",
        )
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("Financial impact is not available under the current governed mapping.")

# ---------------------------------------------------------------------------
# Management Takeaway
# ---------------------------------------------------------------------------
st.markdown('<div class="s360-sim-section">Management Takeaway</div>', unsafe_allow_html=True)

sel_assumptions = sel_profile.get("assumptions", {})
sel_resource_line = _assumption_intensity_line(sel_assumptions)
sel_action_detail = _action_detail_for_profile(kpi_id, sel_assumptions)
selected_action_level = comp_label

_cap_gain_for_takeaway = None
try:
    _cap_gain_for_takeaway = _cap_delta_hours
except NameError:
    pass

_render_decision_table(
    kpi_id=kpi_id,
    kpi_name=kpi_name,
    action_strategy=action_strategy,
    selected_action_level=selected_action_level,
    comp_label=comp_label,
    baseline_unit=baseline_unit,
    forecast_value=forecast_value,
    forecast_unit=forecast_unit,
    scenario_val=scenario_val,
    resource_line=sel_resource_line,
    financial=sel_financial,
    action_detail=sel_action_detail,
    capacity_gain_hours=_cap_gain_for_takeaway,
)

# ---------------------------------------------------------------------------
# Decision Review Handoff
# ---------------------------------------------------------------------------
st.markdown('<div class="s360-sim-section">Decision Review Handoff</div>', unsafe_allow_html=True)

handoff_supported = sel_scenario_available and sel_financial is not None
st.markdown('<div class="s360-sim-cta">', unsafe_allow_html=True)
st.markdown(
    '<div class="title">Ready for Decision Review?</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="help">Send the selected scenario to Decision &amp; Call for Action for management review.</div>',
    unsafe_allow_html=True,
)

if handoff_supported:
    if st.button("USE THIS SCENARIO FOR DECISION REVIEW", key="sim_handoff_btn", use_container_width=False):
        # Compute the live change value for the selected scenario
        _handoff_change = None
        if scenario_val is not None and forecast_value is not None:
            _handoff_change = scenario_val - forecast_value

        # Compute the live confidence string from the selected scenario result
        _handoff_confidence = "Moderate"
        if sel_result is not None and getattr(sel_result, "final_scenario_confidence", None):
            _raw_conf = str(sel_result.final_scenario_confidence)
            if "." in _raw_conf:
                _raw_conf = _raw_conf.split(".")[-1]
            _handoff_confidence = _raw_conf.replace("_", " ").title()

        # Compute the live scenario status
        _handoff_scenario_status = "Not Assessable"
        if scenario_val is not None:
            try:
                from src.simulation_lab_controller import _get_status_for_value
                _handoff_scenario_status, _ = _get_status_for_value(kpi_id, scenario_val)
            except Exception:
                _handoff_scenario_status = "Not Assessable"

        # Resolve intervention_id for the selected profile (live value)
        _handoff_intervention_id = None
        if sel_profile is not None:
            _handoff_intervention_id = sel_profile.get("intervention_id") or sel_profile.get(
                "intervention_lookup_id"
            )

        # Trade-off / displacement values for handoff payload.
        # Underlying analytical logic preserved; visible UI section intentionally removed.
        if isinstance(state, dict):
            tradeoff_main = state.get("tradeoff_statement", "") or ""
            tradeoff_secondary = state.get("tradeoff_displacement_note", "") or ""
        else:
            tradeoff_main = ""
            tradeoff_secondary = ""

        st.session_state["decision_review_context"] = {
            # --- Required keys (Decision page validation) ---
            "hospital_id": hospital_id,
            "department_id": department_id,
            "kpi_id": kpi_id,
            "kpi_name": kpi_name,
            "forecast_month": forecast_month,
            "forecast_month_label": fc_month_label,
            "latest_actual_baseline": baseline_value,
            "latest_actual_unit": baseline_unit,
            "latest_actual_date": baseline_date,
            "do_nothing_forecast": forecast_value,
            "do_nothing_unit": forecast_unit,
            "forecast_warning": forecast_warning,
            "action_strategy": action_strategy,
            "selected_action_level": selected_action_level,
            "action_detail": sel_action_detail,
            "resource_line": sel_resource_line,
            "intervention_id": _handoff_intervention_id,
            "comparator": comp_type,
            "scenario_kpi_value": scenario_val,
            "scenario_unit": baseline_unit,
            "scenario_status": _handoff_scenario_status,
            "change": _handoff_change,
            "confidence": _handoff_confidence,
            "confidence_pct": None,
            "waiting_time_direction": "",
            "financial": sel_financial,
            "tradeoff_text": tradeoff_main,
            "displacement_text": tradeoff_secondary,
            "management_takeaway": sel_action_detail,
            "prepared_at": datetime.datetime.now().isoformat(timespec="seconds"),
            # --- Internal / backward-compat keys ---
            "comparator_label": comp_label,
            "decision_status": _FINANCIAL_DISPLAY_RULES["decision_status"],
            "saved_at": None,
        }
        st.session_state["sim_scenario_saved"] = True
        st.success("Scenario saved for Decision Review handoff.")
        # Preserve session state by using Streamlit-native page switch
        st.switch_page("pages/05_Decision_and_Call_for_Action.py")
else:
    st.info(
        "Decision support is not available for this scenario because the expected operational impact could not be calculated."
    )

if st.session_state.get("sim_scenario_saved"):
    st.markdown(
        '<div class="saved-note">Scenario saved. It is now available in the Decision &amp; Call for Action page.</div>',
        unsafe_allow_html=True,
    )
st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Page-scope footer
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="s360-page-scope-note">'
    "This page does not perform financial impact, scenario simulation beyond the "
    "indicative comparators above, intervention execution, or cost-benefit analysis."
    "</div>",
    unsafe_allow_html=True,
)
