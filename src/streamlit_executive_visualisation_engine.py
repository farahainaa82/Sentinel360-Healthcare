"""
streamlit_executive_visualisation_engine.py
Matplotlib visualisations for Executive Overview.
"""

from typing import Dict, List, Optional

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from .streamlit_executive_logging import log_event

matplotlib.use("Agg")


_STATUS_COLOURS = {
    "red": "#dc3545",
    "amber": "#fd7e14",
    "green": "#28a745",
    "blue": "#0d6efd",
    "grey": "#6c757d",
    "navy": "#1a2b4c",
}


def _card_border_colour(status: str) -> str:
    s = str(status).lower()
    if s in ("red", "critical"):
        return "red"
    if s in ("amber", "warning"):
        return "amber"
    if s in ("green", "acceptable", "stable"):
        return "green"
    if s in ("monitoring", "informational"):
        return "blue"
    return "grey"


def render_kpi_trend_chart(
    trend_df: pd.DataFrame,
    kpi_name: str,
    unit: str,
    threshold_value: Optional[float] = None,
    status: str = "",
) -> Optional[plt.Figure]:
    """Render a compact Matplotlib trend chart for a KPI card with title."""
    if trend_df.empty or len(trend_df) < 2:
        return None
    if "kpi_value" not in trend_df.columns or "reporting_date" not in trend_df.columns:
        return None

    values = pd.to_numeric(trend_df["kpi_value"], errors="coerce").dropna()
    dates = trend_df.loc[values.index, "reporting_date"]
    if len(values) < 2:
        return None

    # Compact figure with title
    fig, ax = plt.subplots(figsize=(3.0, 1.4))
    ax.set_title(f"{kpi_name} Trend", fontsize=9, fontweight="semibold", color="#1a2b4c", pad=6)
    ax.plot(dates, values, color=_STATUS_COLOURS["navy"], linewidth=1.2, marker="o", markersize=2.5)

    if threshold_value is not None and pd.notna(threshold_value):
        ax.axhline(y=threshold_value, color=_STATUS_COLOURS["amber"], linestyle="--", linewidth=0.8)

    # Highlight latest point using the evaluated KPI status colour
    marker_colour = _STATUS_COLOURS.get(_card_border_colour(status), _STATUS_COLOURS["red"])
    ax.scatter([dates.iloc[-1]], [values.iloc[-1]], color=marker_colour, s=25, zorder=5, edgecolors="white", linewidths=0.5)

    ax.set_ylabel(unit if unit else "Value", fontsize=8)
    ax.tick_params(axis="both", labelsize=7)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Compact date labels
    if len(dates) > 0:
        ax.set_xticks([dates.iloc[0], dates.iloc[-1]])
        ax.set_xticklabels(
            [d.strftime("%d %b") if hasattr(d, "strftime") else str(d)[:10] for d in [dates.iloc[0], dates.iloc[-1]]],
            fontsize=7,
        )

    fig.tight_layout()
    log_event("KPI_TREND_RENDERED", kpi_name)
    return fig


def render_relationship_pathway(
    nodes: List[Dict],
) -> Optional[plt.Figure]:
    """Render a horizontal Matplotlib pathway with nodes and arrows."""
    if not nodes or len(nodes) < 2:
        return None

    fig, ax = plt.subplots(figsize=(12, 2.2))
    ax.axis("off")

    n = len(nodes)
    x_positions = [i / max(1, n - 1) for i in range(n)]
    y_position = 0.5

    for i, node in enumerate(nodes):
        x = x_positions[i]
        label = node.get("label", "")
        value = node.get("value", "")
        direction = node.get("direction", "")
        status = node.get("status", "")

        colour = _STATUS_COLOURS.get(_card_border_colour(status), _STATUS_COLOURS["blue"])

        box_text = f"{label}\n{value}\n{direction}"
        ax.annotate(
            box_text,
            xy=(x, y_position),
            fontsize=9,
            ha="center",
            va="center",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor=colour, linewidth=2),
        )

        if i < n - 1:
            ax.annotate(
                "",
                xy=(x_positions[i + 1] - 0.08, y_position),
                xytext=(x + 0.08, y_position),
                arrowprops=dict(arrowstyle="->", color=_STATUS_COLOURS["navy"], lw=2),
            )

    ax.set_xlim(-0.1, 1.1)
    ax.set_ylim(0, 1)
    fig.tight_layout()
    log_event("PATHWAY_RENDERED", f"nodes={n}")
    return fig


def _compact_currency(val: float) -> str:
    """Format financial value in compact RM form."""
    if val is None or pd.isna(val):
        return "N/A"
    v = float(val)
    if abs(v) >= 1_000_000:
        return f"RM{v / 1_000_000:.2f}M"
    if abs(v) >= 1_000:
        return f"RM{v / 1_000:.1f}K"
    return f"RM{v:.0f}"


def render_financial_impact_chart(
    cost: Optional[float],
    benefit: Optional[float],
    net: Optional[float],
) -> Optional[plt.Figure]:
    """Render a compact horizontal bar chart for cost, benefit, net impact."""
    values = []
    labels = []
    colours = []

    if cost is not None and pd.notna(cost):
        values.append(-abs(cost))
        labels.append("Estimated Cost")
        colours.append(_STATUS_COLOURS["red"])
    if benefit is not None and pd.notna(benefit):
        values.append(abs(benefit))
        labels.append("Estimated Benefit")
        colours.append(_STATUS_COLOURS["green"])
    if net is not None and pd.notna(net):
        values.append(net)
        labels.append("Net Impact")
        colours.append(_STATUS_COLOURS["blue"] if net >= 0 else _STATUS_COLOURS["red"])

    if len(values) < 2:
        return None

    fig, ax = plt.subplots(figsize=(5.5, 1.6))
    y_pos = range(len(values))
    bars = ax.barh(y_pos, values, color=colours, height=0.45)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=7.5)
    ax.axvline(x=0, color="black", linewidth=0.6)
    ax.grid(axis="x", linestyle=":", alpha=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="x", labelsize=6)

    max_extent = max(abs(v) for v in values) if values else 1
    for bar, val in zip(bars, values):
        width = bar.get_width()
        offset = max_extent * 0.03
        label_x = width + offset if width >= 0 else width - offset
        ax.text(
            label_x,
            bar.get_y() + bar.get_height() / 2,
            _compact_currency(val),
            ha="left" if width >= 0 else "right",
            va="center",
            fontsize=7.5,
            fontweight="bold",
        )

    fig.tight_layout()
    log_event("FINANCIAL_CHART_RENDERED", f"bars={len(values)}")
    return fig


def render_scenario_comparison_chart(
    scenarios: List[Dict],
    measure_key: str = "net_impact",
) -> Optional[plt.Figure]:
    """Render a horizontal bar chart comparing scenario net impacts."""
    if not scenarios:
        return None

    labels = []
    values = []
    colours = []
    for s in scenarios:
        val = s.get(measure_key)
        if val is None or pd.isna(val):
            continue
        labels.append(s.get("label", "Scenario"))
        values.append(float(val))
        colours.append(_STATUS_COLOURS["blue"])

    if len(values) < 1:
        return None

    fig, ax = plt.subplots(figsize=(6.5, 2.6))
    y_pos = range(len(values))
    bars = ax.barh(y_pos, values, color=colours, height=0.4)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=9)
    ax.axvline(x=0, color="black", linewidth=0.8)
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    for bar, val in zip(bars, values):
        width = bar.get_width()
        label_x = width + (max([abs(v) for v in values]) * 0.02) if width >= 0 else width - (max([abs(v) for v in values]) * 0.02)
        ax.text(
            label_x,
            bar.get_y() + bar.get_height() / 2,
            f"RM {val:,.0f}",
            ha="left" if width >= 0 else "right",
            va="center",
            fontsize=9,
            fontweight="bold",
        )

    fig.tight_layout()
    log_event("SCENARIO_CHART_RENDERED", f"scenarios={len(values)}")
    return fig


def display_chart(fig: Optional[plt.Figure], key: str = "chart", use_container_width: bool = True) -> None:
    """Display a Matplotlib figure in Streamlit and close it."""
    if fig is None:
        return
    try:
        st.pyplot(fig, use_container_width=use_container_width)
    except TypeError:
        # Fallback for older/newer Streamlit versions that renamed the parameter
        try:
            width = "stretch" if use_container_width else "content"
            st.pyplot(fig, width=width)
        except TypeError:
            st.pyplot(fig)
    plt.close(fig)
    log_event("CHART_DISPLAYED", key)

def render_kpi_annual_actual_chart(
    monthly_df,
    kpi_name: str,
    unit: str,
    selected_month: int = 1,
    threshold_value=None,
    status: str = '',
    forecast_df=None,
    eligibility_status: str = "ELIGIBLE",
    forecast_limitation: str = "",
):
    """Render a Jan-Dec annual chart.

    Jan-Jul: solid line from actual monthly values.
    Aug-Dec: dashed line from governed forecast when eligible;
             "Forecast Not Available" annotation when ineligible.
    A subtle uncertainty band is drawn between lower_bound and upper_bound
    for eligible forecasts. Selected month is highlighted across both periods.
    """
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import pandas as pd
    if monthly_df is None or monthly_df.empty:
        return None
    all_months = list(range(1, 13))
    labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    actual_values = [None] * 12
    for _, row in monthly_df.iterrows():
        m = int(row['month']) - 1
        if 0 <= m < 12:
            actual_values[m] = row['monthly_value'] if row.get('supported', True) else None

    forecast_values = [None] * 12
    forecast_lower = [None] * 12
    forecast_upper = [None] * 12
    forecast_quality = ""
    has_forecast = forecast_df is not None and not forecast_df.empty and eligibility_status == "ELIGIBLE"
    if has_forecast:
        for _, row in forecast_df.iterrows():
            m = int(row['month']) - 1
            if 0 <= m < 12:
                forecast_values[m] = row.get('monthly_value')
                lb = row.get('lower_value')
                ub = row.get('upper_value')
                if lb is not None and pd.notna(lb):
                    forecast_lower[m] = float(lb)
                if ub is not None and pd.notna(ub):
                    forecast_upper[m] = float(ub)
                if not forecast_quality and row.get('forecast_quality'):
                    forecast_quality = str(row.get('forecast_quality'))

    fig, ax = plt.subplots(figsize=(6.0, 2.4))
    ax.set_title(f"{kpi_name} - Annual Actual + Forecast", fontsize=10, fontweight="semibold", color="#1a2b4c", pad=8)

    # Solid actual line (Jan-Jul)
    actual_x = [i for i in range(7) if actual_values[i] is not None]
    actual_y = [actual_values[i] for i in actual_x]
    if actual_x:
        ax.plot(actual_x, actual_y, color=_STATUS_COLOURS["navy"], linewidth=2.0,
                marker="o", markersize=6, zorder=4, label="Actual")
    # Connector Jul->Aug if both present
    if actual_x and actual_values[6] is not None:
        last_actual_idx = actual_x[-1]
        if 7 <= 11 and forecast_values[7] is not None:
            ax.plot([last_actual_idx, 7], [actual_values[6], forecast_values[7]],
                    color=_STATUS_COLOURS["navy"], linewidth=1.2, linestyle=":", zorder=3)

    if has_forecast:
        # Uncertainty band across Aug-Dec
        band_x = [i for i in range(7, 12) if forecast_lower[i] is not None and forecast_upper[i] is not None]
        if band_x:
            band_lo = [forecast_lower[i] for i in band_x]
            band_hi = [forecast_upper[i] for i in band_x]
            ax.fill_between(band_x, band_lo, band_hi, color=_STATUS_COLOURS["blue"], alpha=0.10, zorder=1)
        # Dashed forecast line
        fc_x = [i for i in range(7, 12) if forecast_values[i] is not None]
        fc_y = [forecast_values[i] for i in fc_x]
        if fc_x:
            ax.plot(fc_x, fc_y, color=_STATUS_COLOURS["blue"], linewidth=2.0,
                    linestyle="--", marker="s", markersize=5, zorder=3, label="Forecast")
        # Cut-off vertical line at July/August boundary
        ax.axvline(x=6.5, color='#9aa0a6', linestyle=":", linewidth=1.0, zorder=2)
        # Legend for Actual / Forecast
        ax.legend(loc="upper left", fontsize=7, framealpha=0.85)
    else:
        # Shade unsupported Aug-Dec area
        ax.axvspan(6.5, 11.5, alpha=0.12, color='#6c757d', zorder=1)
        note = "Forecast Not Available"
        if forecast_limitation:
            note = f"Forecast Not Available\nReason: {forecast_limitation}"
        ax.text(9.0, ax.get_ylim()[1] if ax.has_data() else 0, note,
                fontsize=7, color='#6c757d', ha='center', va='top', style='italic', alpha=0.9)

    # Highlight selected month across both actual and forecast
    sel_idx = selected_month - 1
    if 0 <= sel_idx < 12:
        if sel_idx < 7 and actual_values[sel_idx] is not None:
            marker_colour = _STATUS_COLOURS.get(_card_border_colour(status), _STATUS_COLOURS["red"])
            ax.scatter([sel_idx], [actual_values[sel_idx]], color=marker_colour,
                       s=80, zorder=6, edgecolors='white', linewidths=1.5)
        elif sel_idx >= 7 and has_forecast and forecast_values[sel_idx] is not None:
            # Forecast-month highlight uses the same status-driven colour as the
            # actual-month highlight so the user can read it the same way. The
            # forecast line itself stays blue and dashed; only the selected point
            # changes colour to match the card status (red/amber/green).
            marker_colour = _STATUS_COLOURS.get(_card_border_colour(status), _STATUS_COLOURS["red"])
            ax.scatter([sel_idx], [forecast_values[sel_idx]], color=marker_colour,
                       s=80, zorder=6, edgecolors='white', linewidths=1.5,
                       marker="D")

    # Threshold line
    if threshold_value is not None and pd.notna(threshold_value):
        ax.axhline(y=threshold_value, color=_STATUS_COLOURS["amber"], linestyle="--", linewidth=1.0, zorder=2)

    ax.set_xticks(range(12))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel(unit if unit else "Value", fontsize=9)
    ax.tick_params(axis='y', labelsize=8)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    log_event("KPI_ANNUAL_ACTUAL_RENDERED", kpi_name)
    return fig
