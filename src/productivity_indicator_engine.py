"""
Productivity Indicator Engine — Sentinel360 Executive Overview

Provides governed actual and forecast productive staff-hours for kpi_001
(Staffing Level) using only existing governed data sources and the
ForecastDenominatorCalculator policy.

No hardcoded 8-hour shift assumptions.
No fabricated forecast denominators.
No cumulative actual totals.
"""

import os
import sys
from typing import Dict, Any, Optional
from dataclasses import dataclass

import pandas as pd

# Ensure src is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.productivity_forecast_denominator_policy import (
    ForecastDenominatorCalculator,
)


@dataclass(frozen=True)
class ProductivityResult:
    """Structured result for a single selected month."""

    selected_year: int
    selected_month: int
    period_type: str  # "ACTUAL" or "FORECAST"
    productive_staff_hours: Optional[float]
    staffing_coverage_pct: Optional[float]
    unit: str
    status: str  # "OK", "UNAVAILABLE", "INSUFFICIENT_MONTHS", "NOT_SUPPORTED"
    source: str
    governance_label: str = "ESTIMATED"
    message: str = ""


# ───────────────────────────────────────────────────────────────────────────
# Data paths (governed)
# ───────────────────────────────────────────────────────────────────────────

_KPI_DAILY_PATH = os.path.join("data", "analytical", "analytical_six_kpi_daily.csv")
_FORECAST_MONTHLY_PATH = os.path.join(
    "outputs", "forecasting", "analytical_kpi_monthly_forecast.csv"
)


# ───────────────────────────────────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────────────────────────────────

def _load_kpi_daily() -> pd.DataFrame:
    if not os.path.isfile(_KPI_DAILY_PATH):
        return pd.DataFrame()
    df = pd.read_csv(_KPI_DAILY_PATH, keep_default_na=False, na_values=[""])
    return df


def _load_forecast_monthly() -> pd.DataFrame:
    if not os.path.isfile(_FORECAST_MONTHLY_PATH):
        return pd.DataFrame()
    df = pd.read_csv(_FORECAST_MONTHLY_PATH, keep_default_na=False, na_values=[""])
    for col in ["point_forecast", "lower_bound", "upper_bound"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ["forecast_year", "forecast_month"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    return df


def _is_operational_department(department_id: str) -> bool:
    """Exclude ALL and DEPT-PEX per Executive Overview scope."""
    if not department_id:
        return False
    d = str(department_id).strip().upper()
    return d not in ("ALL", "ALL DEPARTMENTS", "", "DEPT-PEX")


# ───────────────────────────────────────────────────────────────────────────
# Actual month calculation
# ───────────────────────────────────────────────────────────────────────────

def _calculate_actual(
    kpi_daily: pd.DataFrame,
    hospital_id: str,
    department_id: str,
    year: int,
    month: int,
) -> ProductivityResult:
    """Sum numerator_value for selected month = productive staff-hours."""
    if kpi_daily.empty:
        return ProductivityResult(
            selected_year=year,
            selected_month=month,
            period_type="ACTUAL",
            productive_staff_hours=None,
            staffing_coverage_pct=None,
            unit="staff-hours",
            status="UNAVAILABLE",
            source="analytical_six_kpi_daily.csv",
            message="KPI daily data not available.",
        )

    mask = (
        (kpi_daily["hospital_id"] == hospital_id)
        & (kpi_daily["department_id"] == department_id)
        & (kpi_daily["kpi_id"] == "kpi_001")
    )
    sub = kpi_daily[mask].copy()
    if sub.empty:
        return ProductivityResult(
            selected_year=year,
            selected_month=month,
            period_type="ACTUAL",
            productive_staff_hours=None,
            staffing_coverage_pct=None,
            unit="staff-hours",
            status="UNAVAILABLE",
            source="analytical_six_kpi_daily.csv",
            message="No kpi_001 data for selected context.",
        )

    # Ensure numeric month/year
    sub["reporting_year"] = pd.to_numeric(sub["reporting_year"], errors="coerce")
    sub["reporting_month"] = pd.to_numeric(sub["reporting_month"], errors="coerce")
    sub = sub.dropna(subset=["reporting_year", "reporting_month"])
    sub = sub[
        (sub["reporting_year"] == year) & (sub["reporting_month"] == month)
    ]

    if sub.empty:
        return ProductivityResult(
            selected_year=year,
            selected_month=month,
            period_type="ACTUAL",
            productive_staff_hours=None,
            staffing_coverage_pct=None,
            unit="staff-hours",
            status="UNAVAILABLE",
            source="analytical_six_kpi_daily.csv",
            message="No actual data for selected month.",
        )

    # Productive staff-hours = sum of numerator_value
    sub["numerator_value"] = pd.to_numeric(sub["numerator_value"], errors="coerce")
    productive_hours = float(sub["numerator_value"].sum())

    # Staffing coverage = mean of daily kpi_value for the month
    sub["kpi_value"] = pd.to_numeric(sub["kpi_value"], errors="coerce")
    coverage = float(sub["kpi_value"].mean()) if not sub["kpi_value"].empty else None

    return ProductivityResult(
        selected_year=year,
        selected_month=month,
        period_type="ACTUAL",
        productive_staff_hours=productive_hours,
        staffing_coverage_pct=coverage,
        unit="staff-hours",
        status="OK",
        source="analytical_six_kpi_daily.csv",
        message="",
    )


# ───────────────────────────────────────────────────────────────────────────
# Forecast month calculation
# ───────────────────────────────────────────────────────────────────────────

def _calculate_forecast(
    forecast_df: pd.DataFrame,
    hospital_id: str,
    department_id: str,
    year: int,
    month: int,
) -> ProductivityResult:
    """Forecast productive staff-hours = point_forecast % * governed denominator."""
    if forecast_df.empty:
        return ProductivityResult(
            selected_year=year,
            selected_month=month,
            period_type="FORECAST",
            productive_staff_hours=None,
            staffing_coverage_pct=None,
            unit="staff-hours",
            status="UNAVAILABLE",
            source="analytical_kpi_monthly_forecast.csv",
            message="Forecast data not available.",
        )

    mask = (
        (forecast_df["hospital"] == hospital_id)
        & (forecast_df["department_code"] == department_id)
        & (forecast_df["kpi_id"] == "kpi_001")
        & (forecast_df["forecast_year"] == year)
        & (forecast_df["forecast_month"] == month)
    )
    matches = forecast_df[mask]
    if matches.empty:
        return ProductivityResult(
            selected_year=year,
            selected_month=month,
            period_type="FORECAST",
            productive_staff_hours=None,
            staffing_coverage_pct=None,
            unit="staff-hours",
            status="UNAVAILABLE",
            source="analytical_kpi_monthly_forecast.csv",
            message="No forecast record for selected month.",
        )

    rec = matches.iloc[0]
    point_forecast = float(rec["point_forecast"]) if pd.notna(rec.get("point_forecast")) else None
    if point_forecast is None:
        return ProductivityResult(
            selected_year=year,
            selected_month=month,
            period_type="FORECAST",
            productive_staff_hours=None,
            staffing_coverage_pct=None,
            unit="staff-hours",
            status="UNAVAILABLE",
            source="analytical_kpi_monthly_forecast.csv",
            message="Forecast point value missing.",
        )

    # Governed denominator from policy (no hardcoded May/Jun/Jul)
    calc = ForecastDenominatorCalculator()
    denom_result = calc.calculate(
        hospital_id=hospital_id,
        department_id=department_id,
        target_year=year,
    )

    if denom_result.status != "OK":
        return ProductivityResult(
            selected_year=year,
            selected_month=month,
            period_type="FORECAST",
            productive_staff_hours=None,
            staffing_coverage_pct=point_forecast,
            unit="staff-hours",
            status=denom_result.status,
            source="productivity_forecast_denominator_policy",
            message=f"Denominator unavailable: {denom_result.message}",
        )

    required_hours = denom_result.value if denom_result.value is not None else 0.0
    estimated_hours = (point_forecast / 100.0) * required_hours

    return ProductivityResult(
        selected_year=year,
        selected_month=month,
        period_type="FORECAST",
        productive_staff_hours=estimated_hours,
        staffing_coverage_pct=point_forecast,
        unit="staff-hours",
        status="OK",
        source="analytical_kpi_monthly_forecast.csv + productivity_forecast_denominator_policy",
        message="",
    )


# ───────────────────────────────────────────────────────────────────────────
# Public API
# ───────────────────────────────────────────────────────────────────────────

def get_productivity_capacity(
    hospital_id: str,
    department_id: str,
    year: int,
    month: int,
    *,
    kpi_daily_df: Optional[pd.DataFrame] = None,
    forecast_df: Optional[pd.DataFrame] = None,
) -> ProductivityResult:
    """Return the governed productivity capacity for the selected month.

    Parameters
    ----------
    hospital_id : str
    department_id : str
    year : int
    month : int
    kpi_daily_df : pd.DataFrame, optional
        Pre-loaded analytical_six_kpi_daily data.
    forecast_df : pd.DataFrame, optional
        Pre-loaded analytical_kpi_monthly_forecast data.

    Returns
    -------
    ProductivityResult
    """
    if not _is_operational_department(department_id):
        return ProductivityResult(
            selected_year=year,
            selected_month=month,
            period_type="ACTUAL",
            productive_staff_hours=None,
            staffing_coverage_pct=None,
            unit="staff-hours",
            status="NOT_SUPPORTED",
            source="scope_exclusion",
            message="Department not supported for productivity indicator.",
        )

    # Determine period type using the same rule as the rest of the app
    from src.streamlit_executive_data_loader import get_period_type

    period_type = get_period_type(year, month)

    if period_type == "ACTUAL":
        df = kpi_daily_df if kpi_daily_df is not None else _load_kpi_daily()
        return _calculate_actual(df, hospital_id, department_id, year, month)

    # FORECAST
    df = forecast_df if forecast_df is not None else _load_forecast_monthly()
    return _calculate_forecast(df, hospital_id, department_id, year, month)
