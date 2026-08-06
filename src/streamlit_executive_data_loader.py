"""
streamlit_executive_data_loader.py
Loads frozen authoritative Sentinel360 outputs for the Executive Overview.
"""

import json
import os
from typing import Dict, Optional

import pandas as pd
import streamlit as st

from .streamlit_executive_logging import log_event


# Governed reporting cut-off: no forecast data exists beyond this month
GOVERNED_ACTUAL_MONTH_CUTOFF = 7  # July 2025
GOVERNED_ACTUAL_YEAR = 2025


_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_KPI_DAILY_PATH = os.path.join(_BASE_DIR, "data", "analytical", "analytical_six_kpi_daily.csv")
_RELATIONSHIP_PATH = os.path.join(_BASE_DIR, "data", "analytical", "analytical_relationship_network_edges.csv")
_FINANCIAL_PATH = os.path.join(_BASE_DIR, "outputs", "decision_intelligence", "step_2d9_financial_impact_dataset.csv")
_SCENARIO_PATH = os.path.join(_BASE_DIR, "outputs", "decision_intelligence", "step_2d9_scenario_comparison_dataset.csv")
_INTEGRATED_PATH = os.path.join(_BASE_DIR, "outputs", "decision_intelligence", "step_2d9_integrated_decision_dataset.csv")
_RISK_PATH = os.path.join(_BASE_DIR, "outputs", "decision_intelligence", "step_2d9_risk_alert_dataset.csv")
_EXEC_PATH = os.path.join(_BASE_DIR, "outputs", "decision_intelligence", "step_2d9_executive_overview_dataset.csv")
_KPI_DASH_PATH = os.path.join(_BASE_DIR, "outputs", "decision_intelligence", "step_2d9_kpi_dashboard_dataset.csv")
_MANIFEST_PATH = os.path.join(_BASE_DIR, "outputs", "decision_intelligence", "step_2d9_executive_package_handover_manifest.json")

# Forecast paths (Phase 3B-FI)
_FORECAST_MONTHLY_PATH = os.path.join(_BASE_DIR, "outputs", "forecasting", "analytical_kpi_monthly_forecast.csv")
_FORECAST_WARNING_PATH = os.path.join(_BASE_DIR, "outputs", "forecasting", "analytical_kpi_forecast_warning_signals.csv")
_FORECAST_ELIGIBILITY_PATH = os.path.join(_BASE_DIR, "outputs", "forecasting", "kpi_forecast_eligibility_audit.csv")
_FORECAST_METHOD_PATH = os.path.join(_BASE_DIR, "outputs", "forecasting", "kpi_forecast_method_selection.csv")

# Governed forecast horizon
FORECAST_HORIZON_START_MONTH = 8  # August
FORECAST_HORIZON_END_MONTH = 12  # December


_DEPARTMENT_NAMES = {
    "DEPT-ADM": "Admissions",
    "DEPT-DIAG": "Diagnostic Services",
    "DEPT-ED": "Emergency Department",
    "DEPT-ICU": "Intensive Care Unit",
    "DEPT-MED": "Medical Ward",
    "DEPT-OPC": "Outpatient Clinic",
    "DEPT-PEX": "Patient Experience",
    "DEPT-SURG": "Surgical Ward",
}


def _display_hospital(hospital_id: str) -> str:
    """Return hospital code for display (standardized across all pages)."""
    return hospital_id


def _display_department(dept_id: str) -> str:
    return _DEPARTMENT_NAMES.get(dept_id, dept_id)


def _parse_package_id(package_id: str) -> Dict[str, str]:
    """Parse DPKG-PKG-EP-HOSP-001-DEPT-ADM-kpi_001-20260108 format."""
    import re
    result = {"package_id": package_id}
    m = re.search(r"(HOSP-\d+)", package_id)
    if m:
        result["hospital_id"] = m.group(1)
    m = re.search(r"(DEPT-[A-Z]+)", package_id)
    if m:
        result["department_id"] = m.group(1)
    m = re.search(r"(kpi_\d+)", package_id)
    if m:
        result["kpi_id"] = m.group(1)
    m = re.search(r"-(\d{8})$", package_id)
    if m:
        part = m.group(1)
        result["date"] = f"{part[:4]}-{part[4:6]}-{part[6:]}"
    return result


@st.cache_data(show_spinner=False)
def _load_csv(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path, dtype=str, keep_default_na=True)
    log_event("DATA_LOADED", f"file={os.path.basename(path)}, rows={len(df)}")
    return df


def load_kpi_daily() -> pd.DataFrame:
    """Load actual numeric KPI daily data with trends."""
    df = _load_csv(_KPI_DAILY_PATH)
    if df.empty:
        return df
    for col in ["kpi_value", "numerator_value", "denominator_value"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "reporting_date" in df.columns:
        df["reporting_date"] = pd.to_datetime(df["reporting_date"], errors="coerce")
    if "reporting_year" in df.columns:
        df["reporting_year"] = pd.to_numeric(df["reporting_year"], errors="coerce").astype("Int64")
    if "reporting_month" in df.columns:
        df["reporting_month"] = pd.to_numeric(df["reporting_month"], errors="coerce").astype("Int64")
    df["hospital_name"] = df["hospital_id"].map(_display_hospital)
    df["department_name"] = df["department_id"].map(_display_department)
    return df


def get_kpi_monthly_actual_table(kpi_daily: pd.DataFrame) -> pd.DataFrame:
    """Build canonical monthly KPI actual table from daily data.

    Returns one row per hospital--department--KPI--year--month with
    the arithmetic mean of valid daily observations.
    """
    if kpi_daily.empty:
        return pd.DataFrame()

    df = kpi_daily.copy()

    # Derive reporting_date if missing but year/month exist
    if "reporting_date" not in df.columns and "reporting_year" in df.columns and "reporting_month" in df.columns:
        df["reporting_date"] = pd.to_datetime(
            df[["reporting_year", "reporting_month"]].assign(day=1).rename(
                columns={"reporting_year": "year", "reporting_month": "month"}
            )
        )

    # Derive reporting_year and reporting_month from reporting_date if missing
    if "reporting_date" in df.columns:
        df["reporting_date"] = pd.to_datetime(df["reporting_date"], errors="coerce")
        if "reporting_year" not in df.columns:
            df["reporting_year"] = df["reporting_date"].dt.year
        if "reporting_month" not in df.columns:
            df["reporting_month"] = df["reporting_date"].dt.month

    # Default hospital_id if missing
    if "hospital_id" not in df.columns:
        df["hospital_id"] = "HOSP-001"

    # Default kpi_name from kpi_id if missing
    if "kpi_name" not in df.columns and "kpi_id" in df.columns:
        # Simple mapping for known IDs; fallback to kpi_id itself
        name_map = {
            "kpi_001": "Staffing Level",
            "kpi_002": "Staff Absenteeism Rate",
            "kpi_003": "Bed Occupancy Rate",
            "kpi_004": "Average Patient Waiting Time",
            "kpi_005": "Patient Complaint Rate",
            "kpi_006": "Patient Satisfaction Score",
        }
        df["kpi_name"] = df["kpi_id"].map(name_map).fillna(df["kpi_id"])

    # Default calculation_status if missing
    if "calculation_status" not in df.columns:
        df["calculation_status"] = "Calculated"

    # Accept governed validity statuses (same rules as analytical outputs)
    valid_statuses = {"Calculated", "Validated", "Conditionally Ready", "Ready"}
    if "calculation_status" in df.columns:
        df = df[df["calculation_status"].isin(valid_statuses)]

    if df.empty:
        return pd.DataFrame()

    # Ensure numeric types
    if "reporting_year" in df.columns:
        df["reporting_year"] = pd.to_numeric(df["reporting_year"], errors="coerce").astype("Int64")
    if "reporting_month" in df.columns:
        df["reporting_month"] = pd.to_numeric(df["reporting_month"], errors="coerce").astype("Int64")
    if "kpi_value" in df.columns:
        df["kpi_value_num"] = pd.to_numeric(df["kpi_value"], errors="coerce")
    if "reporting_date" in df.columns:
        df["reporting_date"] = pd.to_datetime(df["reporting_date"], errors="coerce")

    # Fallback: derive reporting_year/reporting_month from reporting_date where missing
    if "reporting_date" in df.columns:
        date_year = pd.to_numeric(df["reporting_date"].dt.year, errors="coerce").astype("Int64")
        date_month = pd.to_numeric(df["reporting_date"].dt.month, errors="coerce").astype("Int64")
        if "reporting_year" in df.columns:
            df["reporting_year"] = df["reporting_year"].fillna(date_year)
        else:
            df["reporting_year"] = date_year
        if "reporting_month" in df.columns:
            df["reporting_month"] = df["reporting_month"].fillna(date_month)
        else:
            df["reporting_month"] = date_month

    # Drop rows without a numeric KPI value, year, or month
    required = ["kpi_value_num"]
    if "reporting_year" in df.columns:
        required.append("reporting_year")
    if "reporting_month" in df.columns:
        required.append("reporting_month")
    df = df.dropna(subset=required)

    if df.empty:
        return pd.DataFrame()

    # Aggregation group key
    group_cols = ["hospital_id", "department_id", "kpi_id", "kpi_name", "reporting_year", "reporting_month"]
    group_cols = [c for c in group_cols if c in df.columns]

    if not group_cols:
        return pd.DataFrame()

    agg = df.groupby(group_cols).agg(
        monthly_actual_value=("kpi_value_num", "mean"),
        valid_observation_count=("kpi_value_num", "count"),
        first_date=("reporting_date", "min"),
        last_date=("reporting_date", "max"),
    ).reset_index()

    agg["aggregation_method"] = "arithmetic_mean"
    agg["calculation_status"] = "Calculated"
    agg["source_file"] = "analytical_six_kpi_daily.csv"

    # Pull unit from first row in each group
    if "unit" in df.columns:
        unit_map = df.groupby(group_cols)["unit"].first().reset_index()
        agg = agg.merge(unit_map, on=group_cols, how="left")

    # Rename for canonical consumption
    agg = agg.rename(columns={
        "hospital_id": "hospital",
        "department_id": "department_code",
        "reporting_year": "year",
        "reporting_month": "month",
    })

    # Add display department name
    if "department_code" in agg.columns:
        agg["department"] = agg["department_code"].map(_display_department)

    # Ensure required columns exist
    for col in [
        "hospital", "department", "department_code", "kpi_id", "kpi_name",
        "year", "month", "monthly_actual_value", "unit",
        "valid_observation_count", "first_date", "last_date",
        "aggregation_method", "calculation_status", "source_file",
    ]:
        if col not in agg.columns:
            agg[col] = None

    agg = agg.sort_values(["hospital", "department_code", "kpi_id", "year", "month"])
    return agg


def load_relationship_edges() -> pd.DataFrame:
    """Load relationship network edges for pathway visualisation."""
    df = _load_csv(_RELATIONSHIP_PATH)
    if df.empty:
        return df
    for col in ["relationship_strength", "lag_days"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def load_risk_alert_dataset() -> pd.DataFrame:
    """Alias for load_risk_alert for test compatibility."""
    return load_risk_alert()


def load_risk_alert() -> pd.DataFrame:
    """Load risk alert dataset with package metadata."""
    df = _load_csv(_RISK_PATH)
    if df.empty:
        return df
    # Parse package_id to extract IDs
    parsed = df["decision_package_id"].apply(_parse_package_id).apply(pd.Series)
    for col in ["hospital_id", "department_id", "kpi_id", "date"]:
        if col in parsed.columns:
            df[col] = parsed[col]
    if "date" in df.columns:
        df["reporting_date"] = pd.to_datetime(df["date"], errors="coerce")
    df["hospital_name"] = df["hospital_id"].map(_display_hospital)
    df["department_name"] = df["department_id"].map(_display_department)
    if "risk_tier" in df.columns:
        df["risk_tier_num"] = pd.to_numeric(df["risk_tier"], errors="coerce")
    return df


def load_executive_overview_dataset() -> pd.DataFrame:
    """Alias for load_executive_overview for test compatibility."""
    return load_executive_overview()


def load_executive_overview() -> pd.DataFrame:
    """Load executive overview dataset."""
    df = _load_csv(_EXEC_PATH)
    if df.empty:
        return df
    parsed = df["decision_package_id"].apply(_parse_package_id).apply(pd.Series)
    for col in ["hospital_id", "department_id", "kpi_id", "date"]:
        if col in parsed.columns:
            df[col] = parsed[col]
    if "date" in df.columns:
        df["reporting_date"] = pd.to_datetime(df["date"], errors="coerce")
    df["hospital_name"] = df["hospital_id"].map(_display_hospital)
    df["department_name"] = df["department_id"].map(_display_department)
    return df


def load_kpi_dashboard_dataset() -> pd.DataFrame:
    """Alias for load_kpi_dashboard for test compatibility."""
    return load_kpi_dashboard()


def load_kpi_dashboard() -> pd.DataFrame:
    """Load KPI dashboard dataset."""
    df = _load_csv(_KPI_DASH_PATH)
    if df.empty:
        return df
    parsed = df["decision_package_id"].apply(_parse_package_id).apply(pd.Series)
    for col in ["hospital_id", "department_id", "kpi_id", "date"]:
        if col in parsed.columns:
            df[col] = parsed[col]
    if "date" in df.columns:
        df["reporting_date"] = pd.to_datetime(df["date"], errors="coerce")
    df["hospital_name"] = df["hospital_id"].map(_display_hospital)
    df["department_name"] = df["department_id"].map(_display_department)
    return df


def load_financial_impact_dataset() -> pd.DataFrame:
    """Alias for load_financial_impact for test compatibility."""
    return load_financial_impact()


def load_financial_impact() -> pd.DataFrame:
    """Load financial impact dataset."""
    df = _load_csv(_FINANCIAL_PATH)
    if df.empty:
        return df
    for col in ["net_financial_impact", "lower_estimate", "central_estimate", "upper_estimate"]:
        if col in df.columns:
            df[col + "_num"] = pd.to_numeric(df[col], errors="coerce")
    return df


def load_scenario_comparison() -> pd.DataFrame:
    """Load scenario comparison dataset."""
    df = _load_csv(_SCENARIO_PATH)
    if df.empty:
        return df
    return df


def load_audit_traceability_dataset() -> pd.DataFrame:
    """Alias for backward compatibility."""
    return load_integrated_decision()


def load_integrated_decision() -> pd.DataFrame:
    """Load integrated decision dataset for management review."""
    df = _load_csv(_INTEGRATED_PATH)
    if df.empty:
        return df
    return df


def load_handover_manifest() -> dict:
    """Load the frozen Phase 2D9 handover manifest."""
    if not os.path.exists(_MANIFEST_PATH):
        return {}
    try:
        with open(_MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def load_all_data() -> Dict[str, pd.DataFrame]:
    """Load all authoritative datasets."""
    return {
        "kpi_daily": load_kpi_daily(),
        "relationship_edges": load_relationship_edges(),
        "risk_alert": load_risk_alert(),
        "executive_overview": load_executive_overview(),
        "kpi_dashboard": load_kpi_dashboard(),
        "financial_impact": load_financial_impact(),
        "scenario_comparison": load_scenario_comparison(),
        "integrated_decision": load_integrated_decision(),
        "forecast_monthly": load_kpi_monthly_forecast(),
        "forecast_warnings": load_kpi_forecast_warning_signals(),
        "forecast_eligibility": load_kpi_forecast_eligibility_audit(),
        "forecast_method": load_kpi_forecast_method_selection(),
    }


def load_kpi_monthly_forecast() -> pd.DataFrame:
    """Load authoritative KPI monthly forecast output.

    Source: outputs/forecasting/analytical_kpi_monthly_forecast.csv
    Columns include: forecast_id, hospital, department, department_code, kpi_id,
    kpi_name, forecast_year, forecast_month, point_forecast, lower_bound,
    upper_bound, unit, forecast_quality, eligibility_status, horizon_months_ahead.
    """
    df = _load_csv(_FORECAST_MONTHLY_PATH)
    if df.empty:
        return df
    for col in ["point_forecast", "lower_bound", "upper_bound",
                "validation_mae", "validation_rmse", "horizon_months_ahead"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "forecast_year" in df.columns:
        df["forecast_year"] = pd.to_numeric(df["forecast_year"], errors="coerce").astype("Int64")
    if "forecast_month" in df.columns:
        df["forecast_month"] = pd.to_numeric(df["forecast_month"], errors="coerce").astype("Int64")
    if "forecast_period_start" in df.columns:
        df["forecast_period_start"] = pd.to_datetime(df["forecast_period_start"], errors="coerce")
    if "forecast_period_end" in df.columns:
        df["forecast_period_end"] = pd.to_datetime(df["forecast_period_end"], errors="coerce")
    return df


def load_kpi_forecast_warning_signals() -> pd.DataFrame:
    """Load authoritative forecast warning signals.

    Source: outputs/forecasting/analytical_kpi_forecast_warning_signals.csv
    Columns include: warning_id, hospital, department, department_code, kpi_id,
    warning_level, warning_reason, forecast_status, latest_actual_status,
    expected_status_change, forecast_quality, horizon_months_ahead,
    suggested_action_text, suggested_action_id.
    """
    df = _load_csv(_FORECAST_WARNING_PATH)
    if df.empty:
        return df
    for col in ["point_forecast", "lower_bound", "upper_bound", "horizon_months_ahead"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "forecast_year" in df.columns:
        df["forecast_year"] = pd.to_numeric(df["forecast_year"], errors="coerce").astype("Int64")
    if "forecast_month" in df.columns:
        df["forecast_month"] = pd.to_numeric(df["forecast_month"], errors="coerce").astype("Int64")
    return df


def load_kpi_forecast_eligibility_audit() -> pd.DataFrame:
    """Load forecast eligibility audit (48 dept–KPI combinations).

    Source: outputs/forecasting/kpi_forecast_eligibility_audit.csv
    Columns include: hospital, department, department_code, kpi_id, kpi_name,
    eligibility_status, limitation.
    """
    df = _load_csv(_FORECAST_ELIGIBILITY_PATH)
    if df.empty:
        return df
    return df


def load_kpi_forecast_method_selection() -> pd.DataFrame:
    """Load forecast method selection (33 eligible combinations).

    Source: outputs/forecasting/kpi_forecast_method_selection.csv
    Columns include: hospital, department, department_code, kpi_id,
    selected_method, forecast_quality, validation_mae.
    """
    df = _load_csv(_FORECAST_METHOD_PATH)
    if df.empty:
        return df
    for col in ["validation_mae", "validation_rmse"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def get_forecast_capability_notice() -> Dict[str, object]:
    """Return a compact forecast capability notice.

    Combines coverage counts from the eligibility audit and forecast horizon
    from the monthly forecast dataset.
    """
    eligibility = load_kpi_forecast_eligibility_audit()
    forecast = load_kpi_monthly_forecast()

    total = int(len(eligibility))
    eligible = int((eligibility.get("eligibility_status", pd.Series(dtype=str)) == "ELIGIBLE").sum()) if not eligibility.empty else 0
    ineligible = total - eligible
    coverage_text = f"{eligible} of {total} department–KPI combinations"

    horizon_months = []
    if not forecast.empty and "forecast_month" in forecast.columns:
        horizon_months = sorted(int(m) for m in forecast["forecast_month"].dropna().unique().tolist())
    horizon_text = "August–December 2025" if horizon_months else "Not available"

    limitations = "Generated from short synthetic historical series and not production-approved."
    unsupported_text = f"{ineligible} combinations due to insufficient or invalid historical data."

    return {
        "status": "Indicative Prototype Available",
        "coverage": coverage_text,
        "horizon": horizon_text,
        "limitations": limitations,
        "unsupported": unsupported_text,
        "total": total,
        "eligible": eligible,
        "ineligible": ineligible,
    }


def get_filter_options(kpi_daily: pd.DataFrame) -> Dict[str, list]:
    """Derive valid filter options from actual KPI daily data.

    For the governed forecast year (2025), months 1-12 are exposed so the
    user can select actual months (Jan-Jul) and forecast months (Aug-Dec).
    Actual data only exists for Jan-Jul; forecast data only exists for Aug-Dec.
    """
    if kpi_daily.empty:
        return {"hospital": [], "department": [], "year": [], "month": []}

    hospitals = kpi_daily["hospital_id"].dropna().unique().tolist()
    hospital_options = [(h, _display_hospital(h)) for h in hospitals]

    departments = sorted(kpi_daily["department_id"].dropna().unique().tolist())
    dept_options = [("ALL", "All Departments")] + [(d, _display_department(d)) for d in departments]

    years = kpi_daily["reporting_year"].dropna().unique().tolist()
    year_options = sorted([int(y) for y in years if pd.notna(y)])

    months = kpi_daily["reporting_month"].dropna().unique().tolist()
    month_options = sorted([int(m) for m in months if pd.notna(m)])

    # Extend to full Jan-Dec if the forecast year is selectable (2025)
    full_year_months = list(range(1, 13))
    if GOVERNED_ACTUAL_YEAR in year_options:
        month_options = sorted(set(month_options) | set(full_year_months))
    else:
        # Cap months to governed actual cut-off for non-forecast years
        capped_months = []
        for m in month_options:
            if m > GOVERNED_ACTUAL_MONTH_CUTOFF:
                continue
            capped_months.append(m)
        month_options = capped_months if capped_months else month_options

    return {
        "hospital": hospital_options,
        "department": dept_options,
        "year": year_options,
        "month": month_options,
    }


def get_latest_period(kpi_daily: pd.DataFrame) -> Dict[str, int]:
    """Return the latest available year and month from KPI daily data."""
    if kpi_daily.empty or "reporting_date" not in kpi_daily.columns:
        return {"year": 2025, "month": 1}
    valid = kpi_daily["reporting_date"].dropna()
    if valid.empty:
        return {"year": 2025, "month": 1}
    latest = valid.max()
    return {"year": latest.year, "month": latest.month}


def get_kpi_trend(
    kpi_daily: pd.DataFrame,
    hospital_id: str,
    department_id: str,
    kpi_name: str,
    year: int,
    month: int,
    max_points: int = 12,
) -> pd.DataFrame:
    """Return ordered historical KPI observations for trend chart."""
    if kpi_daily.empty:
        return pd.DataFrame()
    mask = (
        (kpi_daily["hospital_id"] == hospital_id)
        & (kpi_daily["department_id"] == department_id)
        & (kpi_daily["kpi_name"] == kpi_name)
    )
    sub = kpi_daily[mask].copy()
    if sub.empty:
        return pd.DataFrame()
    sub = sub.sort_values("reporting_date")
    # Filter to selected month and prior months in same year, plus some history
    sub = sub.tail(max_points)
    return sub

def get_kpi_annual_actual_series(
    kpi_daily: pd.DataFrame,
    hospital_id: str,
    department_id: str,
    kpi_id: str,
    year: int,
) -> pd.DataFrame:
    """Return monthly actual averages for Jan-Jul; Aug-Dec as empty / unsupported."""
    monthly = get_kpi_monthly_actual_table(kpi_daily)
    if monthly.empty:
        return pd.DataFrame()

    mask = (
        (monthly["hospital"] == hospital_id)
        & (monthly["kpi_id"] == kpi_id)
        & (monthly["year"] == year)
    )
    if department_id != "ALL":
        mask = mask & (monthly["department_code"] == department_id)
    sub = monthly[mask].copy()
    if sub.empty:
        return pd.DataFrame()

    if department_id == "ALL":
        # Aggregate across all departments: mean per month
        result = (
            sub.groupby(["kpi_id", "month"], as_index=False)["monthly_actual_value"]
            .mean()
            .rename(columns={"monthly_actual_value": "monthly_value"})
        )
    else:
        result = sub.rename(columns={"monthly_actual_value": "monthly_value"})

    result["supported"] = result["month"] <= GOVERNED_ACTUAL_MONTH_CUTOFF
    result["month_label"] = result["month"].apply(
        lambda m: ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][m - 1]
    )
    result = result.sort_values("month")
    return result


def get_period_type(year: int, month: int) -> str:
    """Return 'ACTUAL' for Jan-Jul or 'FORECAST' for Aug-Dec for the governed year."""
    if year == GOVERNED_ACTUAL_YEAR and month >= FORECAST_HORIZON_START_MONTH:
        return "FORECAST"
    return "ACTUAL"


def get_kpi_annual_forecast_series(
    forecast_df: pd.DataFrame,
    hospital_id: str,
    department_id: str,
    kpi_id: str,
    year: int,
) -> pd.DataFrame:
    """Return monthly forecast rows for Aug-Dec for one dept-KPI combination."""
    if forecast_df.empty:
        return pd.DataFrame()
    if department_id == "ALL":
        return pd.DataFrame()

    mask = (
        (forecast_df["hospital"] == hospital_id)
        & (forecast_df["department_code"] == department_id)
        & (forecast_df["kpi_id"] == kpi_id)
        & (forecast_df["forecast_year"] == year)
    )
    sub = forecast_df[mask].copy()
    if sub.empty:
        return pd.DataFrame()

    result = sub.rename(columns={
        "forecast_month": "month",
        "point_forecast": "monthly_value",
        "lower_bound": "lower_value",
        "upper_bound": "upper_value",
    })
    result["supported"] = True
    result["source_type"] = "FORECAST"
    result["month_label"] = result["month"].apply(
        lambda m: ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][m - 1]
    )
    result = result.sort_values("month")
    return result


def lookup_forecast_record(
    forecast_df: pd.DataFrame,
    hospital_id: str,
    department_id: str,
    kpi_id: str,
    year: int,
    month: int,
) -> Dict[str, object]:
    """Return the governed forecast record for the selected context, or {} if none."""
    if forecast_df.empty or department_id == "ALL":
        return {}
    mask = (
        (forecast_df["hospital"] == hospital_id)
        & (forecast_df["department_code"] == department_id)
        & (forecast_df["kpi_id"] == kpi_id)
        & (forecast_df["forecast_year"] == year)
        & (forecast_df["forecast_month"] == month)
    )
    matches = forecast_df[mask]
    if matches.empty:
        return {}
    return matches.iloc[0].to_dict()


def lookup_forecast_warning(
    warning_df: pd.DataFrame,
    hospital_id: str,
    department_id: str,
    kpi_id: str,
    year: int,
    month: int,
) -> Dict[str, object]:
    """Return the governed forecast warning record, or {} if none."""
    if warning_df.empty or department_id == "ALL":
        return {}
    mask = (
        (warning_df["hospital"] == hospital_id)
        & (warning_df["department_code"] == department_id)
        & (warning_df["kpi_id"] == kpi_id)
        & (warning_df["forecast_year"] == year)
        & (warning_df["forecast_month"] == month)
    )
    matches = warning_df[mask]
    if matches.empty:
        return {}
    return matches.iloc[0].to_dict()


def lookup_forecast_eligibility(
    eligibility_df: pd.DataFrame,
    hospital_id: str,
    department_id: str,
    kpi_id: str,
) -> Dict[str, object]:
    """Return the forecast eligibility audit record, or {} if none."""
    if eligibility_df.empty:
        return {}
    mask = (
        (eligibility_df["hospital"] == hospital_id)
        & (eligibility_df["department_code"] == department_id)
        & (eligibility_df["kpi_id"] == kpi_id)
    )
    matches = eligibility_df[mask]
    if matches.empty:
        return {}
    rec = matches.iloc[0].to_dict()
    return {
        "eligibility_status": rec.get("eligibility_status", ""),
        "limitation": rec.get("limitation", ""),
    }
