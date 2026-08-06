# ============================================================
# SENTINEL360 HEALTHCARE 1.0 — HOMEPAGE
# Intelligent Early Warning System for Organisational Performance
# Black Swan Protocol · 2026
# ============================================================
# This is the entry point of the Sentinel360 multipage Streamlit app.
# The pages/ directory provides the full decision-support flow:
#   1. Data Upload & Validation
#   2. Executive Overview
#   3. Risk & Alert
#   4. Simulation Lab
#   5. Decision & Call for Action
#
# This homepage only renders a branded landing experience.
# It does not load datasets, run analytics, or alter session state
# used by the analytical pages.

import streamlit as st
import base64
from pathlib import Path
from src.s360_sidebar_chrome import render_sidebar_chrome

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Sentinel360 Healthcare 1.0",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- SIDEBAR CHROME (brand + footer + native nav styling) ---
render_sidebar_chrome()

# --- COLOUR TOKENS ---
COLOR_NAVY = "#0B1E3D"
COLOR_TEAL = "#0288D1"
COLOR_BG = "#F5F7FA"
COLOR_BORDER = "#DDE3EC"
COLOR_TEXT_PRIMARY = "#1A2B47"
COLOR_TEXT_SECONDARY = "#4A5568"
COLOR_TEXT_MUTED = "#718096"
COLOR_TEXT_DISABLED = "#A0AEC0"
COLOR_FORECAST_BG = "#E3F0FF"
COLOR_FORECAST_BORDER = "#1565C0"


# --- LOGO ASSETS (base64 data URIs for inline header rendering) ---
def _logo_data_uri(filename: str) -> str:
    """Return a base64-encoded data URI for an asset, or empty string if missing."""
    path = Path(__file__).parent / "assets" / filename
    if not path.exists():
        return ""
    return f"data:image/png;base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


JCORP_LOGO_URI = _logo_data_uri("jcorp_logo.png")
BSP_LOGO_URI = _logo_data_uri("black_swan_protocol_logo.png")

CARD_COLORS = {
    1: "#1565C0",   # Data Upload — blue
    2: "#0277BD",   # Executive Overview — teal-blue
    3: "#B71C1C",   # Risk & Alert — red
    4: "#E65100",   # Simulation Lab — orange
    5: "#1B5E20",   # Decision — green
}

# --- MODULE DATA ---
MODULES = [
    {
        "step": 1,
        "title": "Data Upload & Validation",
        "objective": "Visualize how hospital data moves through the ETL process before it enters the analytical layer.",
        "try_this": "Upload the demo dataset and follow the pipeline: Extract → Validate → Transform → Load",
        "look_for": [
            "Rows Received",
            "Rows Accepted",
            "Rows Requiring Review",
            "Data Ready for Analytics status"
        ]
    },
    {
        "step": 2,
        "title": "Executive Overview",
        "objective": "Identify the KPI requiring immediate management attention",
        "try_this": "Select HOSP-001 · ICU · Aug 2025 — review the KPI summary",
        "look_for": [
            "Priority KPI highlights",
            "Forecast warning flags",
            "Actual vs Forecast trend"
        ]
    },
    {
        "step": 3,
        "title": "Risk & Alert",
        "objective": "Investigate why a KPI is becoming a management risk",
        "try_this": "Dept: ICU · Year: 2025 · Month: Aug · KPI: Staff Absenteeism Rate",
        "look_for": [
            "WARNING badge on absenteeism",
            "Risk Progression chart",
            "Suggested preventive action"
        ]
    },
    {
        "step": 4,
        "title": "Simulation Lab",
        "objective": "Compare interventions before committing resources",
        "try_this": "Select Staff Absenteeism Rate — compare Minimum / Recommended / Intensive Action",
        "look_for": [
            "Scenario impact forecast",
            "Cost vs outcome comparison",
            "Recommended scenario highlighted"
        ]
    },
    {
        "step": 5,
        "title": "Decision & Call for Action",
        "objective": "Generate a management decision ready for executive sign-off",
        "try_this": "Review the recommended action for ICU · Aug 2025",
        "look_for": [
            "Decision card with owner",
            "Approved action summary",
            "Call-to-action button"
        ]
    }
]


# --- HELPER: CARD RENDERER ---
def render_card(module: dict) -> str:
    step = module["step"]
    color = CARD_COLORS[step]
    title = module["title"]
    objective = module["objective"]
    try_this = module["try_this"]
    look_for_items = module["look_for"]

    look_for_html = "".join(
        f'<div style="line-height:1.7;font-size:12px;color:#4A5568;">· {item}</div>'
        for item in look_for_items
    )

    return f"""
<div style="
    background:#ffffff;
    border:1px solid #DDE3EC;
    border-top:3px solid {color};
    border-radius:8px;
    padding:18px;
    box-shadow:0 1px 4px rgba(0,0,0,0.06);
    height:100%;
    box-sizing:border-box;
">
    <div style="
        width:22px;
        height:22px;
        border-radius:50%;
        background:{color};
        color:#ffffff;
        font-size:11px;
        font-weight:700;
        display:flex;
        align-items:center;
        justify-content:center;
        margin-bottom:10px;
    ">{step}</div>
    <div style="font-size:13px;font-weight:600;color:#1A2B47;margin-bottom:12px;line-height:1.4;">
        {title}
    </div>
    <hr style="border:none;border-top:1px solid #DDE3EC;margin:0 0 12px 0;" />
    <div style="margin-bottom:10px;">
        <div style="
            font-size:10px;
            font-weight:600;
            text-transform:uppercase;
            letter-spacing:1px;
            color:#718096;
            margin-bottom:4px;
        ">OBJECTIVE</div>
        <div style="font-size:12px;font-weight:400;color:#4A5568;line-height:1.5;">
            {objective}
        </div>
    </div>
    <div style="margin-bottom:10px;">
        <div style="
            font-size:10px;
            font-weight:600;
            text-transform:uppercase;
            letter-spacing:1px;
            color:#718096;
            margin-bottom:4px;
        ">TRY THIS</div>
        <div style="font-size:12px;font-weight:400;color:#4A5568;line-height:1.5;">
            {try_this}
        </div>
    </div>
    <div>
        <div style="
            font-size:10px;
            font-weight:600;
            text-transform:uppercase;
            letter-spacing:1px;
            color:#718096;
            margin-bottom:4px;
        ">LOOK FOR</div>
        {look_for_html}
    </div>
</div>
"""


# --- GLOBAL CSS ---
# Note: We deliberately keep [data-testid="stSidebar"] visible so the
# Streamlit multipage navigation remains accessible. We only hide the
# top header / hamburger / default footer because the homepage renders
# its own branded hero and footer.
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* {
    font-family: 'Inter', sans-serif;
}

body {
    background-color: #F5F7FA !important;
    font-family: 'Inter', sans-serif;
}

[data-testid="stAppViewContainer"] {
    background-color: #F5F7FA !important;
}

[data-testid="stSidebar"] {
    background-color: #F3F6FA !important;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.block-container {
    padding-top: 0 !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    max-width: 100% !important;
}

.block-container > div:first-child {
    margin-top: 0 !important;
}

[data-testid="stVerticalBlock"] > div:first-child {
    margin-top: 0 !important;
}
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SECTION A — HERO HEADER BAND
# ============================================================
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
        ">Intelligent Early Warning System for Organisational Performance</div>
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


# ============================================================
# SECTION B — DEMO CONTEXT BAR
# ============================================================
# This dismiss state is purely UI-local to the homepage and does not
# touch any of the analytical session-state keys used by the pages.
if "demo_bar_visible" not in st.session_state:
    st.session_state.demo_bar_visible = True

if st.session_state.demo_bar_visible:
    bar_col, dismiss_col = st.columns([20, 1])
    with bar_col:
        st.markdown(
            """
<div style="
    background:#E3F0FF;
    border-left:4px solid #1565C0;
    padding:13px 32px;
    display:flex;
    align-items:center;
    justify-content:space-between;
    width:100%;
    box-sizing:border-box;
">
    <div style="display:flex;align-items:center;gap:8px;font-size:13px;color:#1A2B47;">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0;">
            <circle cx="8" cy="8" r="7.5" stroke="#1565C0" stroke-width="1" fill="none"/>
            <text x="8" y="12" text-anchor="middle" font-size="10" font-weight="600" fill="#1565C0" font-family="Inter, sans-serif">i</text>
        </svg>
        <span>
            <strong style="color:#1565C0;">Demo dataset —</strong>
            Hospital: HOSP-001 · Department: Intensive Care Unit · Year: 2025 · Month: August · KPI: Staff Absenteeism Rate
        </span>
    </div>
</div>
""",
            unsafe_allow_html=True,
        )
    with dismiss_col:
        st.markdown(
            "<div style='display:flex;align-items:center;justify-content:center;height:100%;padding-top:4px;'>",
            unsafe_allow_html=True,
        )
        if st.button("✕", key="dismiss_demo_bar", help="Dismiss demo bar"):
            st.session_state.demo_bar_visible = False
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# SECTION C — QUICK START GUIDE CARDS
# ============================================================
st.markdown(
    """
<div style="
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding:24px 32px 12px 32px;
    box-sizing:border-box;
">
    <span style="
        font-size:11px;
        font-weight:600;
        text-transform:uppercase;
        letter-spacing:1.5px;
        color:#718096;
    ">QUICK START GUIDE</span>
    <span style="
        font-size:11px;
        font-weight:400;
        color:#A0AEC0;
    ">Follow the steps in order &nbsp;→</span>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div style="padding:0 24px 24px 24px;box-sizing:border-box;">
""",
    unsafe_allow_html=True,
)

cols = st.columns(5)
for i, col in enumerate(cols):
    with col:
        st.markdown(render_card(MODULES[i]), unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# SECTION D — DEMO NAVIGATION PATH
# ============================================================
PIPELINE_NODES = [
    {"num": "01", "label": "DATA\nUPLOAD"},
    {"num": "02", "label": "EXEC\nOVERVIEW"},
    {"num": "03", "label": "RISK &\nALERT"},
    {"num": "04", "label": "SIMULATION\nLAB"},
    {"num": "05", "label": "DECISION"},
]

nodes_html = ""
for idx, node in enumerate(PIPELINE_NODES):
    label_lines = node["label"].split("\n")
    label_inner = "<br>".join(label_lines)
    nodes_html += f"""
<div style="
    background:#0B1E3D;
    border-radius:8px;
    padding:10px 18px;
    min-width:130px;
    text-align:center;
    flex-shrink:0;
">
    <div style="font-size:10px;color:rgba(255,255,255,0.55);line-height:1.4;">{node['num']}</div>
    <div style="font-size:12px;font-weight:600;color:#ffffff;line-height:1.4;">{label_inner}</div>
</div>
"""
    if idx < len(PIPELINE_NODES) - 1:
        nodes_html += """
<div style="font-size:18px;color:#A0AEC0;padding:0 8px;flex-shrink:0;">→</div>
"""

st.markdown(
    f"""
<div style="
    background:#F5F7FA;
    border-top:1px solid #DDE3EC;
    border-bottom:1px solid #DDE3EC;
    padding:20px 32px;
    box-sizing:border-box;
">
    <div style="
        font-size:11px;
        font-weight:600;
        text-transform:uppercase;
        letter-spacing:1.5px;
        color:#718096;
        margin-bottom:14px;
    ">DEMO NAVIGATION PATH</div>
<div style="
display:flex;
align-items:center;
justify-content:center;
flex-wrap:wrap;
gap:4px;
">
{nodes_html}
</div>
<div style="
text-align:center;
font-size:12px;
font-style:italic;
color:#718096;
margin-top:16px;
">Follow this path for the complete Sentinel360 decision-support demonstration.</div>
</div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SECTION E — FOOTER
# ============================================================
st.markdown(
    """
<div style="
    background:#ffffff;
    border-top:1px solid #DDE3EC;
    padding:14px 32px;
    display:flex;
    justify-content:space-between;
    align-items:center;
    box-sizing:border-box;
    width:100%;
">
    <!-- Left: BSP placeholder + name -->
    <div style="display:flex;align-items:center;gap:8px;">
        <div style="
            width:44px;
            height:22px;
            border:1px dashed #DDE3EC;
            border-radius:3px;
            display:flex;
            align-items:center;
            justify-content:center;
            font-size:9px;
            color:#A0AEC0;
        ">BSP</div>
        <span style="
            font-size:12px;
            font-weight:400;
            color:#718096;
        ">Black Swan Protocol</span>
    </div>
    <!-- Right: version + year -->
    <span style="
        font-size:12px;
        font-weight:400;
        color:#A0AEC0;
    ">Sentinel360 Healthcare v1.0 &nbsp;·&nbsp; 2026</span>
</div>
""",
    unsafe_allow_html=True,
)
