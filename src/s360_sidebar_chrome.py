"""Sentinel360 — Sidebar Navigation Chrome.

One clean navigation system using only real Streamlit st.page_link widgets.
No custom HTML nav cards, no JavaScript, no hidden wrappers, no duplicate
navigation layers.  Session state is preserved natively by st.page_link.

Usage in each page script (right after `st.set_page_config()`):

    from src.s360_sidebar_chrome import render_sidebar_chrome
    render_sidebar_chrome()
"""

import streamlit as st


# ---------------------------------------------------------------------------
# CSS — Sentinel360 sidebar design system
# ---------------------------------------------------------------------------
_SIDEBAR_CSS = """
<style>
/* ---- Sidebar base ---- */
[data-testid="stSidebar"] {
    background-color: #F3F6FA;
    border-right: 1px solid #DDE3EC;
}
[data-testid="stSidebarContent"] {
    display: flex;
    flex-direction: column;
    padding: 0 16px;
}
/* Hide the default Streamlit sidebar header (collapse button) */
[data-testid="stSidebarHeader"] {
    display: none;
}

/* ---- Hide the auto-generated native multipage nav list ---- */
[data-testid="stSidebarNav"],
[data-testid="stSidebarNavSeparator"] {
    display: none !important;
}

/* ---- Sidebar bordered containers (group frames — subtle, transparent fill) ---- */
[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
    background-color: transparent !important;
    border: 1px solid #DDE3EC !important;
    border-radius: 10px !important;
    box-sizing: border-box !important;
    width: 100% !important;
    margin-bottom: 10px !important;
}
[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] > [data-testid="stVerticalBlock"] {
    padding: 8px !important;
    box-sizing: border-box !important;
    width: 100% !important;
}

/* ---- Group headers ---- */
.s360-group-header {
    font-size: 14px;
    font-weight: 800;
    color: #1A2B47;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 8px 4px 12px 4px;
    line-height: 1.25;
    user-select: none;
    border-bottom: 1px solid #DDE3EC;
    margin-bottom: 10px;
}

/* ---- Page links: ONE clean flat button per nav item ---- */
[data-testid^="stPageLink"] {
    width: 100%;
    margin-bottom: 6px;
}

/* Direct child is the single button surface (a for inactive, div for active) */
[data-testid^="stPageLink"] > * {
    display: flex;
    align-items: center;
    width: 100%;
    min-height: 40px;
    box-sizing: border-box;
    padding: 0 12px;
    border-radius: 8px;
    font-size: 14px;
    line-height: 1.2;
    text-decoration: none;
    transition: background-color 120ms ease, border-color 120ms ease;
}

/* Inactive (clickable link) */
[data-testid^="stPageLink"] a {
    background-color: #FFFFFF;
    border: 1px solid #DDE3EC;
    color: #1A2B47;
    font-weight: 500;
}
[data-testid^="stPageLink"] a:hover {
    background-color: #EDF4FB;
    border-color: #C8D8EA;
}

/* Active (current page) */
[data-testid^="stPageLink"] > :not(a) {
    background-color: #E4EEF9;
    border: 1px solid #B8CCE3;
    border-left: 3px solid #0288D1;
    font-weight: 700;
    color: #0B1E3D;
}

/* Defensive: kill any inner background / border that creates a nested card */
[data-testid^="stPageLink"] a *,
[data-testid^="stPageLink"] > :not(a) * {
    background: transparent;
    border: none;
    padding: 0;
    margin: 0;
    box-shadow: none;
}

/* ---- Brand area ---- */
.s360-side-brand {
    padding: 18px 0 14px 0;
    border-bottom: 1px solid #DDE3EC;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.s360-side-brand-mark {
    width: 30px;
    height: 30px;
    border-radius: 6px;
    background: #0B1E3D;
    color: #ffffff;
    font-size: 9px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    letter-spacing: 0.4px;
    flex-shrink: 0;
    line-height: 1;
}
.s360-side-brand-text {
    flex: 1;
    min-width: 0;
}
.s360-side-brand-title {
    font-size: 13px;
    font-weight: 700;
    color: #0B1E3D;
    letter-spacing: -0.2px;
    line-height: 1.15;
    display: flex;
    align-items: center;
    gap: 6px;
    white-space: nowrap;
}
.s360-side-brand-version {
    border: 1px solid #0288D1;
    color: #0288D1;
    background: transparent;
    font-size: 9px;
    font-weight: 500;
    border-radius: 3px;
    padding: 1px 5px;
    line-height: 1.3;
    letter-spacing: 0;
}
.s360-side-brand-sub {
    font-size: 10px;
    color: #718096;
    margin-top: 4px;
    letter-spacing: 0.1px;
    line-height: 1.25;
}

/* ---- Footer ---- */
.s360-side-footer {
    margin-top: auto;
    padding: 8px 4px 8px 4px;
    border-top: 1px solid #DDE3EC;
    font-size: 10px;
    color: #718096;
    line-height: 1.35;
}
.s360-side-footer-name {
    font-weight: 600;
    color: #4A5568;
    font-size: 11px;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 7px;
    letter-spacing: 0.1px;
}
.s360-side-footer-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #0288D1;
    display: inline-block;
    flex-shrink: 0;
}
.s360-side-footer-version {
    color: #A0AEC0;
    font-size: 10px;
    letter-spacing: 0.15px;
    padding-left: 13px;
}
</style>
"""


_BRAND_HTML = """
<div class="s360-side-brand">
    <div class="s360-side-brand-mark">S360</div>
    <div class="s360-side-brand-text">
        <div class="s360-side-brand-title">
            <span>Sentinel360 Healthcare</span>
            <span class="s360-side-brand-version">1.0</span>
        </div>
        <div class="s360-side-brand-sub">Intelligent Early Warning System</div>
    </div>
</div>
"""


_FOOTER_HTML = """
<div class="s360-side-footer">
    <div class="s360-side-footer-name">
        <span class="s360-side-footer-dot"></span>
        Black Swan Protocol
    </div>
    <div class="s360-side-footer-version">Sentinel360 Healthcare v1.0 &middot; 2026</div>
</div>
"""


def render_sidebar_chrome() -> None:
    """Render the Sentinel360 sidebar: brand, two real Streamlit container
    groups with six real st.page_link widgets, and footer.

    Call once per page, immediately after `st.set_page_config()`.
    """
    # 1. Global sidebar CSS
    st.markdown(_SIDEBAR_CSS, unsafe_allow_html=True)

    # 2. Brand area
    st.sidebar.markdown(_BRAND_HTML, unsafe_allow_html=True)

    # 3. OVERVIEW group — three real page_link widgets inside a bordered container
    with st.sidebar.container(border=True):
        st.markdown(
            '<div class="s360-group-header">Overview</div>',
            unsafe_allow_html=True,
        )
        st.page_link("app.py", label="\u2302  Home")
        st.page_link("pages/01_Data_Upload_and_Validation.py", label="\u21E7  Data Upload")
        st.page_link("pages/02_Executive_Overview.py", label="\u25A6  Executive Overview")

    # 4. DECISION INTELLIGENCE group — three real page_link widgets inside a bordered container
    with st.sidebar.container(border=True):
        st.markdown(
            '<div class="s360-group-header">Decision Intelligence</div>',
            unsafe_allow_html=True,
        )
        st.page_link("pages/03_Risk_and_Alert.py", label="\u26A0  Risk and Alert")
        st.page_link("pages/04_Simulation_Lab.py", label="\u25C7  Simulation Lab")
        st.page_link("pages/05_Decision_and_Call_for_Action.py", label="\u2713  Decision & Call for Action")

    # 5. Footer
    st.sidebar.markdown(_FOOTER_HTML, unsafe_allow_html=True)
