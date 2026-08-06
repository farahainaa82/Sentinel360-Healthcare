"""
risk_alert_controller.py

Phase 3C — Risk & Alert page helper module.

Reuses existing governed outputs and helpers:

- ``src.streamlit_executive_data_loader`` loaders for canonical monthly actual
  data, governed forecast outputs, forecast warning signals, and eligibility
  audit.
- ``src.streamlit_executive_page_controller`` for ``format_unit_value``,
  ``evaluate_kpi_status``, ``_warning_severity_score``, ``_card_border_colour``,
  and shared constants.
- ``src.streamlit_executive_visualisation_engine`` for ``display_chart`` and
  chart helpers.

The controller is **read-only with respect to governed data** — it never
mutates the canonical forecasts, eligibility, warning, or threshold files and
never invents new analytical values. It only assembles views on top of them.

Public entry points used by the page:

- :func:`build_risk_alert_state`       — assembles the full state
- :func:`compute_risk_summary`         — 4 summary cards
- :func:`build_priority_risk_table`    — ranked risk table
- :func:`build_selected_risk_detail`   — selected risk panel data
- :func:`render_selected_risk_chart`   — actual + forecast trend chart
- :func:`build_risk_progression_strip` — 12-month status strip
- :func:`build_management_interpretation` — interpretation card
- :func:`build_suggested_action_card`  — preventive action card
- :func:`get_filter_options`           — page-level filters
- :func:`get_excluded_dept_ids`        — department exclusion list
"""

from __future__ import annotations

import calendar
import importlib
import os
import sys
from typing import Dict, List, Optional, Tuple

import pandas as pd

# Make sibling modules importable when running tests directly
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.streamlit_executive_data_loader import (  # noqa: E402
    FORECAST_HORIZON_START_MONTH,
    GOVERNED_ACTUAL_MONTH_CUTOFF,
    GOVERNED_ACTUAL_YEAR,
    _display_department,
    get_filter_options as _get_data_filter_options,
    get_kpi_annual_actual_series,
    get_kpi_annual_forecast_series,
    get_kpi_monthly_actual_table,
    load_kpi_forecast_warning_signals,
    load_kpi_monthly_forecast,
    load_kpi_daily,
)
from src.streamlit_executive_page_controller import (  # noqa: E402
    _warning_severity_score,
    evaluate_kpi_status,
    format_unit_value,
    load_kpi_threshold_config,
)
from src.streamlit_executive_visualisation_engine import (  # noqa: E402
    _card_border_colour,
    display_chart,
    render_kpi_annual_actual_chart,
)


# --------------------------------------------------------------------------
# Constants — single source of truth for Phase 3C page conventions
# --------------------------------------------------------------------------

EXCLUDED_DEPT_IDS: Tuple[str, ...] = ("ALL", "DEPT-PEX")

# Warning level ordering — used by the priority table
WARNING_PRIORITY_ORDER: Tuple[str, ...] = (
    "High Early Warning",
    "Escalating Warning",
    "Emerging Warning",
    "Monitoring",
)

WARNING_PRIORITY_RANK: Dict[str, int] = {
    name: idx for idx, name in enumerate(WARNING_PRIORITY_ORDER)
}

# Status severity ordering (used as tie-breaker and ranking secondary key)
STATUS_PRIORITY_ORDER: Tuple[str, ...] = ("Red", "Amber", "Green", "Monitoring")
STATUS_PRIORITY_RANK: Dict[str, int] = {name: idx for idx, name in enumerate(STATUS_PRIORITY_ORDER)}

# Status text map (display labels for the priority table)
STATUS_TEXT_BY_CODE: Dict[str, str] = {
    "Red": "Critical",
    "Amber": "Warning",
    "Green": "Acceptable",
    "Monitoring": "Monitoring",
    "Not Assessable": "Not Assessable",
}

MONTH_LABELS: List[str] = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


# --------------------------------------------------------------------------
# Public helpers
# --------------------------------------------------------------------------

def get_excluded_dept_ids() -> Tuple[str, ...]:
    """Return the list of department IDs to exclude from the slicer.

    Reuses the same exclusion list used by Executive Overview.
    """
    return EXCLUDED_DEPT_IDS


def get_filter_options() -> Dict[str, list]:
    """Return valid filter options for Hospital, Department, Year, Month.

    Department list excludes ``ALL`` and ``DEPT-PEX``.
    Month list is restricted to forecast months only (Aug-Dec) because
    this page is for highlighting emerging/future risk.
    """
    kpi_daily = load_kpi_daily()
    raw = _get_data_filter_options(kpi_daily)

    # Strip out ALL and the excluded department IDs
    dept_pairs = raw.get("department", [])
    dept_pairs = [
        (d, label) for (d, label) in dept_pairs
        if d != "ALL" and d not in EXCLUDED_DEPT_IDS
    ]

    # Forecast months only (Aug-Dec)
    forecast_months = list(range(FORECAST_HORIZON_START_MONTH, 13))

    return {
        "hospital": raw.get("hospital", []),
        "department": dept_pairs,
        "year": raw.get("year", []),
        "month": forecast_months,
    }


def _kpi_directional_score(value_status: str) -> float:
    """KPI direction severity (Red > Amber > Green > Monitoring)."""
    return float(STATUS_PRIORITY_RANK.get(value_status, 99))


# --------------------------------------------------------------------------
# 1. Risk Summary — 4 compact cards
# --------------------------------------------------------------------------

def compute_risk_summary(
    kpi_daily: pd.DataFrame,
    warning_signals: pd.DataFrame,
    department_code: str,
    year: int,
    month: int,
) -> Dict[str, object]:
    """Compute counts for the 4 summary cards.

    Returns
    -------
    dict
        - active_actual_risks
        - emerging_forecast_risks
        - high_or_escalating_warnings
        - departments_with_risk
        - context_label
    """
    is_actual_month = month <= GOVERNED_ACTUAL_MONTH_CUTOFF

    monthly_actual = get_kpi_monthly_actual_table(kpi_daily)
    monthly_actual = monthly_actual[
        (monthly_actual["department_code"] == department_code)
        & (monthly_actual["year"] == year)
        & (monthly_actual["month"] <= GOVERNED_ACTUAL_MONTH_CUTOFF)
    ]

    # ---- (1) Active Actual Risks ----------------------------------------
    active_actual_risks = 0
    actual_depts_with_risk: set = set()
    if is_actual_month and not monthly_actual.empty:
        # Restrict to *governed* actual months only — Jan-Jul in the
        # governed year. Aug-Dec are forecast months even if the canonical
        # monthly actual dataset happens to contain values there.
        governed_monthly = monthly_actual[
            monthly_actual["month"] <= GOVERNED_ACTUAL_MONTH_CUTOFF
        ]
        latest_actual = (
            governed_monthly.sort_values("month")
            .groupby(["department_code", "kpi_id"])
            .last()
            .reset_index()
        )
        for _, row in latest_actual.iterrows():
            status = _evaluate_actual_status(row)
            if status in ("Red", "Amber"):
                active_actual_risks += 1
                actual_depts_with_risk.add(row["department_code"])

    # ---- (2) Emerging Forecast Risks ------------------------------------
    ctx_warning = _filter_warnings(warning_signals, department_code, year, month)
    emerging_forecast_risks = int(
        ctx_warning["warning_level"].isin(["Emerging Warning", "Escalating Warning", "High Early Warning"]).sum()
    )

    # ---- (3) High / Escalating Warnings ----------------------------------
    high_or_escalating = int(
        ctx_warning["warning_level"].isin(["High Early Warning", "Escalating Warning"]).sum()
    )

    # ---- (4) Departments with Risk --------------------------------------
    forecast_depts_with_risk = set(ctx_warning["department_code"].dropna().tolist())
    departments_with_risk = sorted(actual_depts_with_risk | forecast_depts_with_risk)

    return {
        "active_actual_risks": int(active_actual_risks),
        "emerging_forecast_risks": emerging_forecast_risks,
        "high_or_escalating_warnings": high_or_escalating,
        "departments_with_risk": departments_with_risk,
        "context_label": (
            f"Department: {_display_department(department_code)} "
            f"• Year: {year} • Review Month: {calendar.month_abbr[month]} ({month:02d})"
        ),
        "is_actual_month": is_actual_month,
    }


def _evaluate_actual_status(row: pd.Series) -> str:
    """Evaluate actual status using existing evaluate_kpi_status.

    Reuses threshold config from ``kpi_threshold_config.csv`` via the
    shared :func:`load_kpi_threshold_config` helper which already
    normalises directionality labels (e.g. ``"Higher is better"`` ->
    ``"HIGHER_IS_BETTER"``). If no config is available the result falls
    back to ``Monitoring``.
    """
    try:
        kpi_id = row.get("kpi_id")
        value = row.get("monthly_actual_value")
        if kpi_id is None or value is None or pd.isna(value):
            return "Monitoring"
        cfg_map = load_kpi_threshold_config()
        cfg_row = cfg_map.get(kpi_id)
        if not cfg_row:
            return "Monitoring"
        evaluated = evaluate_kpi_status(
            kpi_id=kpi_id,
            value=value,
            lower_red_boundary=cfg_row.get("lower_red_boundary"),
            lower_amber_boundary=cfg_row.get("lower_amber_boundary"),
            green_lower_boundary=cfg_row.get("green_lower_boundary"),
            green_upper_boundary=cfg_row.get("green_upper_boundary"),
            upper_amber_boundary=cfg_row.get("upper_amber_boundary"),
            upper_red_boundary=cfg_row.get("upper_red_boundary"),
            directionality=cfg_row.get("directionality"),
            unit=cfg_row.get("unit"),
        )
        return evaluated.get("status", "Monitoring")
    except Exception:
        return "Monitoring"


def _filter_warnings(
    warning_signals: pd.DataFrame,
    department_code: str,
    year: int,
    month: int,
) -> pd.DataFrame:
    if warning_signals.empty:
        return warning_signals
    return warning_signals[
        (warning_signals["department_code"] == department_code)
        & (warning_signals["forecast_year"] == year)
        & (warning_signals["forecast_month"] == month)
    ]


# --------------------------------------------------------------------------
# 2. Priority Risk Table
# --------------------------------------------------------------------------

def _priority_risk_internal_rows(
    kpi_daily: pd.DataFrame,
    forecast_df: pd.DataFrame,
    warning_signals: pd.DataFrame,
    department_code: str,
    year: int,
    month: int,
) -> List[Dict[str, object]]:
    """Build ordered list of internal risk row dicts (used by both display
    table and drill-down panels).
    """
    del forecast_df  # reserved for future enrichment
    is_actual_month = month <= GOVERNED_ACTUAL_MONTH_CUTOFF

    monthly_actual = get_kpi_monthly_actual_table(kpi_daily)
    actual_for_dept = monthly_actual[
        (monthly_actual["department_code"] == department_code)
        & (monthly_actual["year"] == year)
        & (monthly_actual["month"] <= GOVERNED_ACTUAL_MONTH_CUTOFF)
    ]

    if not actual_for_dept.empty:
        latest_actual_per_kpi = (
            actual_for_dept.sort_values("month")
            .groupby("kpi_id")
            .last()
            .reset_index()
        )
    else:
        latest_actual_per_kpi = pd.DataFrame(
            columns=["kpi_id", "monthly_actual_value", "unit", "year", "month"]
        )

    ctx_warnings = _filter_warnings(warning_signals, department_code, year, month)
    rows: List[Dict[str, object]] = []
    seen_kpis: set = set()

    # ---- Forecast-driven rows ----------------------------------------
    for _, w in ctx_warnings.iterrows():
        kpi_id = w.get("kpi_id", "")
        seen_kpis.add(kpi_id)
        actual_match = latest_actual_per_kpi[latest_actual_per_kpi["kpi_id"] == kpi_id]
        if not actual_match.empty:
            actual_row = actual_match.iloc[0]
            actual_value = actual_row.get("monthly_actual_value")
            actual_unit = actual_row.get("unit", "")
            actual_month_str = f"{int(actual_row['year'])}-{int(actual_row['month']):02d}"
            actual_status = _evaluate_actual_status(actual_row)
        else:
            actual_value = None
            actual_unit = ""
            actual_month_str = ""
            actual_status = "Not Assessable"

        rows.append({
            "kpi_id": kpi_id,
            "kpi_name": w.get("kpi_name", kpi_id),
            "department_code": department_code,
            "department": _display_department(department_code),
            "latest_actual": actual_value,
            "latest_actual_unit": actual_unit,
            "latest_actual_month": actual_month_str,
            "actual_status": actual_status,
            "actual_status_text": STATUS_TEXT_BY_CODE.get(actual_status, actual_status),
            "forecast_value": w.get("point_forecast"),
            "forecast_lower": w.get("lower_bound"),
            "forecast_upper": w.get("upper_bound"),
            "forecast_quality": w.get("forecast_quality", ""),
            "horizon_months_ahead": w.get("horizon_months_ahead", ""),
            "warning_level": w.get("warning_level", "Monitoring"),
            "forecast_month": f"{int(w['forecast_year'])}-{int(w['forecast_month']):02d}",
            "suggested_action": w.get("suggested_action_text", "Preventive action requires management review."),
        })

    # ---- Actual-driven rows ------------------------------------------
    if is_actual_month and not latest_actual_per_kpi.empty:
        for _, a in latest_actual_per_kpi.iterrows():
            kpi_id = a.get("kpi_id", "")
            if kpi_id in seen_kpis:
                continue
            status = _evaluate_actual_status(a)
            if status not in ("Red", "Amber"):
                continue
            kpi_name = a.get("kpi_name") or kpi_id
            rows.append({
                "kpi_id": kpi_id,
                "kpi_name": kpi_name,
                "department_code": department_code,
                "department": _display_department(department_code),
                "latest_actual": a.get("monthly_actual_value"),
                "latest_actual_unit": a.get("unit", ""),
                "latest_actual_month": f"{int(a['year'])}-{int(a['month']):02d}",
                "actual_status": status,
                "actual_status_text": STATUS_TEXT_BY_CODE.get(status, status),
                "forecast_value": None,
                "forecast_lower": None,
                "forecast_upper": None,
                "forecast_quality": "",
                "horizon_months_ahead": "",
                "warning_level": "Monitoring",
                "forecast_month": "",
                "suggested_action": "Preventive action requires management review.",
            })

    def _rank_key(r: Dict[str, object]) -> tuple:
        warn_rank = WARNING_PRIORITY_RANK.get(str(r.get("warning_level", "Monitoring")), 99)
        st_rank = STATUS_PRIORITY_RANK.get(str(r.get("actual_status", "Monitoring")), 99)
        return (warn_rank, st_rank)

    rows.sort(key=_rank_key)
    return rows


def build_priority_risk_table(
    kpi_daily: pd.DataFrame,
    forecast_df: pd.DataFrame,
    warning_signals: pd.DataFrame,
    department_code: str,
    year: int,
    month: int,
) -> pd.DataFrame:
    """Return a ranked DataFrame, one row per governed (dept, kpi) risk.

    Columns: Priority, Department, KPI, Latest Actual, Actual Status,
    Forecast, Warning, Forecast Month, Suggested Action.
    """
    rows = _priority_risk_internal_rows(
        kpi_daily=kpi_daily,
        forecast_df=forecast_df,
        warning_signals=warning_signals,
        department_code=department_code,
        year=year,
        month=month,
    )

    out_rows: List[Dict[str, object]] = []
    for priority_idx, r in enumerate(rows, start=1):
        out_rows.append({
            "Priority": priority_idx,
            "Department": r["department"],
            "KPI": r["kpi_name"],
            "Latest Actual": _format_value_with_unit(r.get("latest_actual"), r.get("latest_actual_unit", "")),
            "Actual Status": r["actual_status_text"],
            "Forecast": _format_forecast(r.get("forecast_value")),
            "Warning": r["warning_level"],
            "Forecast Month": r["forecast_month"] if r["forecast_month"] else "Forecast Not Available",
            "Suggested Action": _clean_suggested_action(r["suggested_action"]),
        })

    return pd.DataFrame(out_rows, columns=[
        "Priority", "Department", "KPI", "Latest Actual", "Actual Status",
        "Forecast", "Warning", "Forecast Month", "Suggested Action",
    ])


def _format_value_with_unit(value: object, unit: str) -> str:
    if value is None or pd.isna(value):
        return "No actual data"
    try:
        return format_unit_value(float(value), unit)
    except Exception:
        return f"{value}"


def _format_forecast(value: object) -> str:
    if value is None or pd.isna(value):
        return "Forecast Not Available"
    try:
        return f"{float(value):.1f}"
    except Exception:
        return str(value)


def _clean_suggested_action(text: object) -> str:
    """Strip the "SUGGESTED ACTION: " prefix for clean display."""
    s = str(text or "").strip()
    if s.upper().startswith("SUGGESTED ACTION:"):
        s = s[len("SUGGESTED ACTION:"):].strip()
    return s or "Preventive action requires management review."


def _format_month_label(yyyy_mm: str) -> str:
    """Convert ``YYYY-MM`` to a clean ``JUL 2025`` style month label.

    Returns an empty string for empty or invalid input so callers can simply
    check truthiness.
    """
    if not yyyy_mm or "-" not in yyyy_mm:
        return ""
    try:
        parts = yyyy_mm.split("-")
        year = int(parts[0])
        month = int(parts[1])
        if month < 1 or month > 12:
            return ""
        return f"{calendar.month_abbr[month].upper()} {year}"
    except (ValueError, IndexError):
        return ""


# --------------------------------------------------------------------------
# 3. Selected Risk Detail
# --------------------------------------------------------------------------

def build_selected_risk_detail(
    selected_row: Dict[str, object],
    monthly_actual_for_kpi: pd.DataFrame,
) -> Dict[str, object]:
    """Assemble the two compact information blocks for the selected risk.

    Parameters
    ----------
    selected_row
        One ranked row dict from :func:`build_priority_risk_table`.
    monthly_actual_for_kpi
        Monthly actual history for this dept+kpi (used for chart and progression).
    """
    actual_value = selected_row.get("latest_actual")
    actual_unit = selected_row.get("latest_actual_unit", "")
    actual_status = selected_row.get("actual_status_text", "")
    actual_month = selected_row.get("latest_actual_month", "")

    forecast_value = selected_row.get("forecast_value")
    forecast_lower = selected_row.get("forecast_lower")
    forecast_upper = selected_row.get("forecast_upper")
    forecast_warning = selected_row.get("warning_level", "")
    forecast_quality = selected_row.get("forecast_quality", "")
    forecast_month = selected_row.get("forecast_month", "")
    horizon = selected_row.get("horizon_months_ahead", "")

    has_forecast = forecast_value is not None and not pd.isna(forecast_value)

    # Phase 3C visual polish — clean month labels and baseline line.
    actual_month_label = _format_month_label(actual_month)
    forecast_month_label = _format_month_label(forecast_month)
    baseline_label = (
        f"BASELINE AS OF MTD {actual_month_label}" if actual_month_label else ""
    )

    return {
        "header": (
            f"Selected Risk — {_display_department(selected_row['department_code'])} "
            f"— {selected_row['kpi_name']}"
        ),
        "historical": {
            "value": _format_value_with_unit(actual_value, actual_unit),
            "status": actual_status,
            "month": actual_month,
            "month_label": actual_month_label,
            "baseline_label": baseline_label,
        },
        "forecast": {
            "value": (
                format_unit_value(forecast_value, actual_unit)
                if has_forecast
                else "Forecast Not Available"
            ),
            "indicative_range": (
                f"{_format_value_with_unit(forecast_lower, actual_unit)} – "
                f"{_format_value_with_unit(forecast_upper, actual_unit)}"
            ) if has_forecast and forecast_lower is not None and forecast_upper is not None else "Not available",
            "warning": forecast_warning,
            "quality": forecast_quality or "Not available",
            "horizon": (f"{horizon} months ahead" if horizon not in (None, "", "Not Assessable") else "Not available"),
            "month": forecast_month or "Not available",
            "month_label": forecast_month_label or "Not available",
            "available": has_forecast,
        },
    }


# --------------------------------------------------------------------------
# 4. Actual + Forecast Trend Chart
# --------------------------------------------------------------------------

def render_selected_risk_chart(
    selected_row: Dict[str, object],
    monthly_actual: pd.DataFrame,
    forecast_df: pd.DataFrame,
    review_year: int,
    review_month: int,
) -> None:
    """Render the Actual + Forecast trend chart for the selected risk row.

    Reuses ``render_kpi_annual_actual_chart`` with its **exact** signature:

        render_kpi_annual_actual_chart(
            monthly_df, kpi_name, unit,
            selected_month=1, threshold_value=None, status='',
            forecast_df=None, eligibility_status="ELIGIBLE",
            forecast_limitation="",
        )

    ``monthly_df`` needs columns ``month`` and ``monthly_value``.
    ``forecast_df`` needs columns ``month``, ``monthly_value``,
    ``lower_value``, ``upper_value``.
    """
    if not selected_row:
        return
    department_code = selected_row.get("department_code")
    kpi_id = selected_row.get("kpi_id")
    kpi_name = selected_row.get("kpi_name", kpi_id or "")
    unit = selected_row.get("latest_actual_unit", "")
    if not department_code or not kpi_id:
        return

    # Build annual actual series (Jan-Jul) via existing helper
    kpi_daily = load_kpi_daily()
    annual_actual = get_kpi_annual_actual_series(
        kpi_daily=kpi_daily,
        hospital_id="HOSP-001",
        department_id=department_code,
        kpi_id=kpi_id,
        year=review_year,
    )

    # Build annual forecast series (Aug-Dec) via existing helper
    annual_forecast = get_kpi_annual_forecast_series(
        forecast_df=forecast_df,
        hospital_id="HOSP-001",
        department_id=department_code,
        kpi_id=kpi_id,
        year=review_year,
    )

    # Status colour for the selected-month highlight
    status = selected_row.get("actual_status", "")
    if not status:
        status = selected_row.get("warning_level", "")

    fig = render_kpi_annual_actual_chart(
        monthly_df=annual_actual,
        kpi_name=kpi_name,
        unit=unit,
        selected_month=review_month,
        threshold_value=None,
        status=status,
        forecast_df=annual_forecast,
        eligibility_status="ELIGIBLE" if not annual_forecast.empty else "INELIGIBLE",
        forecast_limitation="",
    )
    display_chart(fig, key=f"risk_chart_{department_code}_{kpi_id}_{review_year}_{review_month}")


# --------------------------------------------------------------------------
# 5. Risk Progression — 12-month status strip
# --------------------------------------------------------------------------

def build_risk_progression(
    monthly_actual: pd.DataFrame,
    forecast_df: pd.DataFrame,
    selected_row: Dict[str, object],
    review_year: int,
) -> List[Dict[str, object]]:
    """Return a list of 12 month entries (Jan-Dec) for the selected KPI.

    Each entry has:
        - month (1..12)
        - label ("Jan"..."Dec")
        - status: "Actual" | "Forecast" | "Unsupported"
        - severity: "red" | "amber" | "green" | "grey"
        - value (formatted) or None
    """
    department_code = selected_row.get("department_code")
    kpi_id = selected_row.get("kpi_id")
    unit = selected_row.get("latest_actual_unit", "")

    out: List[Dict[str, object]] = []
    if not department_code or not kpi_id:
        # Always return 12 placeholder entries so the strip is stable
        for m in range(1, 13):
            out.append({
                "month": m,
                "label": MONTH_LABELS[m - 1],
                "status": "Unsupported",
                "severity": "grey",
                "value": None,
            })
        return out

    actual_for_risk = monthly_actual[
        (monthly_actual["department_code"] == department_code)
        & (monthly_actual["kpi_id"] == kpi_id)
        & (monthly_actual["year"] == review_year)
    ]

    # Build per-month actual values
    actual_map: Dict[int, float] = {}
    actual_status_map: Dict[int, str] = {}
    for _, a in actual_for_risk.iterrows():
        m = int(a["month"])
        actual_map[m] = float(a["monthly_actual_value"])
        actual_status_map[m] = _evaluate_actual_status(a)

    forecast_map: Dict[int, float] = {}
    forecast_status_map: Dict[int, str] = {}
    if not forecast_df.empty:
        fc = forecast_df[
            (forecast_df["department_code"] == department_code)
            & (forecast_df["kpi_id"] == kpi_id)
            & (forecast_df["forecast_year"] == review_year)
        ]
        for _, f in fc.iterrows():
            m = int(f["forecast_month"])
            forecast_map[m] = float(f["point_forecast"])
            # Use threshold_status if available, else Monitoring
            forecast_status_map[m] = str(f.get("threshold_status", "Monitoring") or "Monitoring")

    for m in range(1, 13):
        if m <= GOVERNED_ACTUAL_MONTH_CUTOFF:
            if m in actual_map:
                sev_status = actual_status_map.get(m, "Monitoring")
                sev = {"Red": "red", "Amber": "amber", "Green": "green"}.get(sev_status, "grey")
                out.append({
                    "month": m,
                    "label": MONTH_LABELS[m - 1],
                    "status": "Actual",
                    "severity": sev,
                    "value": format_unit_value(actual_map[m], unit),
                })
            else:
                out.append({
                    "month": m,
                    "label": MONTH_LABELS[m - 1],
                    "status": "Unsupported",
                    "severity": "grey",
                    "value": None,
                })
        else:
            if m in forecast_map:
                sev_status = forecast_status_map.get(m, "Monitoring")
                sev = {"Red": "red", "Amber": "amber", "Green": "green"}.get(sev_status, "grey")
                out.append({
                    "month": m,
                    "label": MONTH_LABELS[m - 1],
                    "status": "Forecast",
                    "severity": sev,
                    "value": format_unit_value(forecast_map[m], unit),
                })
            else:
                out.append({
                    "month": m,
                    "label": MONTH_LABELS[m - 1],
                    "status": "Unsupported",
                    "severity": "grey",
                    "value": None,
                })

    return out


# --------------------------------------------------------------------------
# 6. Management Interpretation
# --------------------------------------------------------------------------

def build_management_interpretation(
    selected_row: Dict[str, object],
    monthly_actual: pd.DataFrame,
    review_year: int,
) -> Dict[str, str]:
    """Return short factual historical + forecast interpretation text."""
    department_code = selected_row.get("department_code")
    kpi_id = selected_row.get("kpi_id")
    kpi_name = selected_row.get("kpi_name", kpi_id)
    unit = selected_row.get("latest_actual_unit", "")

    historical_text = ""
    forecast_text = ""

    if department_code and kpi_id:
        # Restrict to GOVERNED actual months only (Jan-Jul)
        actual_for_risk = monthly_actual[
            (monthly_actual["department_code"] == department_code)
            & (monthly_actual["kpi_id"] == kpi_id)
            & (monthly_actual["year"] == review_year)
            & (monthly_actual["month"] <= GOVERNED_ACTUAL_MONTH_CUTOFF)
        ].sort_values("month")

        if not actual_for_risk.empty and len(actual_for_risk) >= 2:
            earliest = actual_for_risk.iloc[0]
            latest = actual_for_risk.iloc[-1]
            earliest_val = format_unit_value(earliest["monthly_actual_value"], unit)
            latest_val = format_unit_value(latest["monthly_actual_value"], unit)
            earliest_month = MONTH_LABELS[int(earliest["month"]) - 1]
            latest_month = MONTH_LABELS[int(latest["month"]) - 1]
            historical_text = (
                f"Historical: {kpi_name} moved from {earliest_val} in {earliest_month} "
                f"to {latest_val} in {latest_month} during the supported actual period. "
                f"Latest actual status: {selected_row.get('actual_status_text', '')}."
            )
        elif not actual_for_risk.empty:
            latest = actual_for_risk.iloc[-1]
            latest_val = format_unit_value(latest["monthly_actual_value"], unit)
            latest_month = MONTH_LABELS[int(latest["month"]) - 1]
            historical_text = (
                f"Historical: {kpi_name} latest supported actual is {latest_val} "
                f"in {latest_month}. Latest actual status: "
                f"{selected_row.get('actual_status_text', '')}."
            )
        else:
            historical_text = (
                f"Historical: No supported actual data available for {kpi_name} "
                f"in the selected context."
            )

    forecast_value = selected_row.get("forecast_value")
    forecast_month = selected_row.get("forecast_month", "")
    warning_level = selected_row.get("warning_level", "")
    has_forecast = forecast_value is not None and not pd.isna(forecast_value)

    if has_forecast:
        forecast_val = format_unit_value(forecast_value, unit)
        forecast_text = (
            f"Forecast: {kpi_name} is projected at {forecast_val} by {forecast_month}, "
            f"classified as {warning_level}."
        )
    else:
        forecast_text = (
            "Forecast Not Available — insufficient historical data."
        )

    return {
        "historical": historical_text,
        "forecast": forecast_text,
        "combined": f"{historical_text}\n\n{forecast_text}",
    }


# --------------------------------------------------------------------------
# 7. Suggested Preventive Action Card
# --------------------------------------------------------------------------

def build_suggested_action_card(selected_row: Dict[str, object]) -> Dict[str, str]:
    """Return the data for the preventive action card."""
    suggested = _clean_suggested_action(selected_row.get("suggested_action", ""))
    warning = selected_row.get("warning_level", "Monitoring")
    forecast_month = selected_row.get("forecast_month", "")
    actual_status = selected_row.get("actual_status_text", "")

    why = (
        f"This risk requires management attention because the forecast "
        f"({forecast_month}) is classified as {warning} and the latest "
        f"actual status is {actual_status}."
    ).strip()

    return {
        "title": "Suggested Preventive Action",
        "action": suggested,
        "why": why,
        "status": "Suggested — Management Review Required",
    }


# --------------------------------------------------------------------------
# Top-level entry point
# --------------------------------------------------------------------------

def build_risk_alert_state(
    department_code: str,
    year: int,
    month: int,
    hospital_label: Optional[str] = None,
) -> Dict[str, object]:
    """Assemble the full state used by the page."""
    kpi_daily = load_kpi_daily()
    forecast_df = load_kpi_monthly_forecast()
    warning_signals = load_kpi_forecast_warning_signals()

    summary = compute_risk_summary(
        kpi_daily=kpi_daily,
        warning_signals=warning_signals,
        department_code=department_code,
        year=year,
        month=month,
    )

    table = build_priority_risk_table(
        kpi_daily=kpi_daily,
        forecast_df=forecast_df,
        warning_signals=warning_signals,
        department_code=department_code,
        year=year,
        month=month,
    )

    return {
        "department_code": department_code,
        "year": year,
        "month": month,
        "hospital_label": hospital_label or "",
        "summary": summary,
        "table": table,
        # Parallel list of dicts in the same row order as the displayed
        # table — used by the detail panel / chart / progression /
        # interpretation helpers to avoid recomputing joins.
        "internal_rows": _priority_risk_internal_rows(
            kpi_daily=kpi_daily,
            forecast_df=forecast_df,
            warning_signals=warning_signals,
            department_code=department_code,
            year=year,
            month=month,
        ),
        "_raw": {
            "kpi_daily": kpi_daily,
            "forecast_df": forecast_df,
            "warning_signals": warning_signals,
        },
    }


__all__ = [
    "EXCLUDED_DEPT_IDS",
    "WARNING_PRIORITY_ORDER",
    "WARNING_PRIORITY_RANK",
    "STATUS_PRIORITY_ORDER",
    "STATUS_PRIORITY_RANK",
    "STATUS_TEXT_BY_CODE",
    "MONTH_LABELS",
    "get_excluded_dept_ids",
    "get_filter_options",
    "compute_risk_summary",
    "_priority_risk_internal_rows",
    "build_priority_risk_table",
    "build_selected_risk_detail",
    "render_selected_risk_chart",
    "build_risk_progression",
    "build_management_interpretation",
    "build_suggested_action_card",
    "build_risk_alert_state",
]