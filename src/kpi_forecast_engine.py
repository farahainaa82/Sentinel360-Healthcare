"""KPI Forecast Engine — eligibility, method selection, and forecast generation.

Governs plausibility constraints, uncertainty ranges, confidence classification,
and horizon risk.
"""

import os
import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from calendar import monthrange
import numpy as np
import pandas as pd

from src.kpi_forecast_methods import METHOD_MAP, MIN_TRAIN_MONTHS
from src.kpi_forecast_validation import validate_method

CUTOFF_DATE = pd.Timestamp("2026-07-31")
FORECAST_HORIZON = [8, 9, 10, 11, 12]  # Aug-Dec 2026
HISTORICAL_YEAR = 2026

OUTPUT_DIR = "outputs/forecasting"

# Plausibility rules per KPI
PLAUSIBILITY_RULES = {
    "kpi_001": {"min": 0, "max": 100, "unit": "Percent"},
    "kpi_002": {"min": 0, "max": 100, "unit": "Percent"},
    "kpi_003": {"min": 0, "max": None, "unit": "Percent"},
    "kpi_004": {"min": 0, "max": None, "unit": "Minutes"},
    "kpi_005": {"min": 0, "max": None, "unit": "Complaints per 1000 encounters"},
    "kpi_006": {"min": 1, "max": 5, "unit": "1-5 Likert Score"},
}

# Bed occupancy specific cap from threshold (section 10)
BED_OCCUPANCY_MAX = 104.761905


def _load_monthly_history(path: str = os.path.join(OUTPUT_DIR, "kpi_monthly_actual_history.csv")) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=["period_start", "period_end"])


def _load_threshold_config(path: str = "config/kpi_threshold_config.csv") -> pd.DataFrame:
    return pd.read_csv(path)


def _load_interventions(path: str = "config/intervention_catalogue.csv") -> pd.DataFrame:
    return pd.read_csv(path)


def assess_eligibility(monthly: pd.DataFrame, daily_path: str = "data/analytical/analytical_six_kpi_daily.csv") -> pd.DataFrame:
    """Assess data sufficiency for every hospital-department-KPI combination."""
    # Load daily data to get the full universe of combinations
    daily = pd.read_csv(daily_path, usecols=["hospital_id", "department_id", "kpi_id", "kpi_name", "unit"]).drop_duplicates()
    daily = daily.rename(columns={"hospital_id": "hospital", "department_id": "department_code"})
    # Merge department names
    dept_master = pd.read_csv("data/demo/department_master.csv")
    dept_map = dept_master.set_index("department_id")["department_name"].to_dict()
    daily["department"] = daily["department_code"].map(dept_map)

    # Summarise monthly data per combination (without department name to avoid collision)
    monthly_summary = (
        monthly.groupby(["hospital", "department_code", "kpi_id", "kpi_name", "unit"])
        .agg(
            valid_observation_count=("valid_observation_count", "sum"),
            missing_observation_count=("missing_observation_count", "sum"),
            valid_historical_months=("month", "count"),
        )
        .reset_index()
    )

    # Merge full universe with monthly summary
    elig = daily.merge(monthly_summary, on=["hospital", "department_code", "kpi_id", "kpi_name", "unit"], how="left")
    elig["valid_observation_count"] = elig["valid_observation_count"].fillna(0).astype(int)
    elig["missing_observation_count"] = elig["missing_observation_count"].fillna(0).astype(int)
    elig["valid_historical_months"] = elig["valid_historical_months"].fillna(0).astype(int)

    results = []
    for _, row in elig.iterrows():
        valid_obs = int(row["valid_observation_count"])
        valid_months = int(row["valid_historical_months"])
        missing_obs = int(row["missing_observation_count"])
        total_days = valid_obs + missing_obs
        missing_rate = missing_obs / total_days if total_days > 0 else 1.0

        unit_consistent = True  # Guaranteed by grouping
        calc_status = "Calculated" if valid_months > 0 else "Invalid"

        status = "ELIGIBLE"
        limitation = ""
        required_additional = ""

        if valid_obs < 90 or valid_months < 4:
            status = "INSUFFICIENT HISTORICAL DATA"
            limitation = "Below minimum daily observation or month count"
            required_additional = "Extend historical data or improve data capture"
        elif missing_rate > 0.40:
            status = "ELIGIBLE WITH LIMITATIONS"
            limitation = f"High missing rate ({missing_rate:.1%})"
            required_additional = "Improve data completeness"
        elif not unit_consistent:
            status = "UNIT MISMATCH"
            limitation = "Inconsistent units across observations"
            required_additional = "Reconcile unit definitions"
        elif calc_status != "Calculated":
            status = "INVALID KPI CALCULATION"
            limitation = "Invalid or missing calculation status"
            required_additional = "Validate KPI calculation logic"
        else:
            if valid_obs < 150 or valid_months < 6:
                status = "ELIGIBLE WITH LIMITATIONS"
                limitation = "Below preferred observation or month count"
                required_additional = "Extend historical data for improved accuracy"

        results.append({
            "hospital": row["hospital"],
            "department": row["department"],
            "department_code": row["department_code"],
            "kpi_id": row["kpi_id"],
            "kpi_name": row["kpi_name"],
            "valid_daily_observations": valid_obs,
            "valid_historical_months": valid_months,
            "missing_rate": missing_rate,
            "unit": row["unit"],
            "unit_consistent": unit_consistent,
            "calculation_status": calc_status,
            "eligibility_status": status,
            "limitation": limitation,
            "required_additional_data": required_additional,
        })

    return pd.DataFrame(results)


def select_methods(monthly: pd.DataFrame, eligibility: pd.DataFrame) -> pd.DataFrame:
    """Validate candidate methods and select the best per eligible combination."""
    eligible = eligibility[eligibility["eligibility_status"].isin(["ELIGIBLE", "ELIGIBLE WITH LIMITATIONS"])].copy()
    selections = []

    for _, row in eligible.iterrows():
        hospital = row["hospital"]
        dept_code = row["department_code"]
        kpi_id = row["kpi_id"]

        g = monthly[
            (monthly["hospital"] == hospital)
            & (monthly["department_code"] == dept_code)
            & (monthly["kpi_id"] == kpi_id)
        ].sort_values(["year", "month"]).reset_index(drop=True)

        if len(g) == 0:
            continue

        series = g["monthly_actual_value"].values
        training_months = len(series)
        training_obs = int(g["valid_observation_count"].sum())

        best_method = None
        best_mae = float("inf")
        best_details = None

        for method_name, min_train in MIN_TRAIN_MONTHS.items():
            if training_months < min_train:
                continue
            v = validate_method(series, method_name)
            if not v["method_eligible"]:
                continue
            if v["mae"] < best_mae or (v["mae"] == best_mae and _method_simpler(method_name, best_method)):
                best_method = method_name
                best_mae = v["mae"]
                best_details = v

        if best_method is None:
            # Fallback to Naive if eligible
            if training_months >= MIN_TRAIN_MONTHS["Naive Last Value"]:
                best_method = "Naive Last Value"
                best_details = validate_method(series, best_method)
                best_mae = best_details["mae"]
            else:
                continue

        selections.append({
            "hospital": hospital,
            "department": row["department"],
            "department_code": dept_code,
            "kpi_id": kpi_id,
            "kpi_name": row["kpi_name"],
            "unit": row.get("unit", ""),
            "selected_method": best_method,
            "selection_reason": f"Lowest validation MAE among eligible methods ({best_mae:.4f})" if best_method != "Naive Last Value" else "Fallback to Naive Last Value",
            "validation_mae": best_details["mae"] if best_details else np.nan,
            "validation_rmse": best_details["rmse"] if best_details else np.nan,
            "validation_mape": best_details["mape"] if best_details else np.nan,
            "training_months": training_months,
            "training_observations": training_obs,
            "eligibility_status": row["eligibility_status"],
            "limitation": row["limitation"],
            "approval_status": "Indicative Prototype",
        })

    return pd.DataFrame(selections)


def _method_simpler(a: str, b: Optional[str]) -> bool:
    """Return True if a is simpler than b."""
    if b is None:
        return True
    order = [
        "Naive Last Value",
        "Three-Month Moving Average",
        "Linear Trend",
        "Simple Exponential Smoothing",
        "Holt Linear Trend",
    ]
    return order.index(a) < order.index(b)


def _apply_plausibility(kpi_id: str, raw_forecast: float) -> Tuple[float, str, str]:
    """Apply KPI-specific plausibility constraints."""
    rules = PLAUSIBILITY_RULES.get(kpi_id, {})
    min_val = rules.get("min")
    max_val = rules.get("max")
    if kpi_id == "kpi_003":
        max_val = BED_OCCUPANCY_MAX

    adjusted = raw_forecast
    constraint = "None"
    reason = ""

    if min_val is not None and raw_forecast < min_val:
        adjusted = min_val
        constraint = "Minimum bound"
        reason = f"Below KPI minimum ({min_val})"

    if max_val is not None and raw_forecast > max_val:
        adjusted = max_val
        constraint = "Maximum bound"
        reason = f"Above KPI maximum ({max_val})"

    return adjusted, constraint, reason


def generate_forecasts(monthly: pd.DataFrame, selection: pd.DataFrame) -> pd.DataFrame:
    """Generate August–December 2026 point forecasts with uncertainty."""
    records = []
    generated_at = datetime.now().isoformat()

    for _, sel in selection.iterrows():
        hospital = sel["hospital"]
        dept_code = sel["department_code"]
        kpi_id = sel["kpi_id"]
        kpi_name = sel["kpi_name"]
        method_name = sel["selected_method"]
        method = METHOD_MAP[method_name]
        unit = sel.get("unit", PLAUSIBILITY_RULES.get(kpi_id, {}).get("unit", ""))

        g = monthly[
            (monthly["hospital"] == hospital)
            & (monthly["department_code"] == dept_code)
            & (monthly["kpi_id"] == kpi_id)
        ].sort_values(["year", "month"]).reset_index(drop=True)

        if len(g) == 0:
            continue

        series = g["monthly_actual_value"].values
        training_months = len(series)
        training_obs = int(g["valid_observation_count"].sum())
        training_start = g["period_start"].iloc[0].strftime("%Y-%m-%d")
        training_end = g["period_end"].iloc[-1].strftime("%Y-%m-%d")

        # Validate to get residuals for uncertainty
        v = validate_method(series, method_name)
        mae = v.get("mae", np.nan)
        rmse = v.get("rmse", np.nan)
        residual_uncertainty = mae if not np.isnan(mae) else rmse if not np.isnan(rmse) else 0.0

        raw_forecasts = method(series, steps=5)

        for idx, month in enumerate(FORECAST_HORIZON):
            raw = raw_forecasts[idx]
            if np.isnan(raw):
                continue

            adj, constraint, reason = _apply_plausibility(kpi_id, raw)

            lower = adj - residual_uncertainty
            upper = adj + residual_uncertainty

            # Apply plausibility to bounds too
            lower_bound, _, _ = _apply_plausibility(kpi_id, lower)
            upper_bound, _, _ = _apply_plausibility(kpi_id, upper)

            horizon_ahead = idx + 1
            horizon_risk = _horizon_risk_label(horizon_ahead)
            quality = _forecast_quality(sel, horizon_ahead, residual_uncertainty)

            records.append({
                "forecast_id": f"{hospital}_{dept_code}_{kpi_id}_2026_{month:02d}",
                "hospital": hospital,
                "department": sel["department"],
                "department_code": dept_code,
                "kpi_id": kpi_id,
                "kpi_name": kpi_name,
                "forecast_year": 2026,
                "forecast_month": month,
                "forecast_period_start": pd.Timestamp(2026, month, 1).strftime("%Y-%m-%d"),
                "forecast_period_end": pd.Timestamp(2026, month, monthrange(2026, month)[1]).strftime("%Y-%m-%d"),
                "point_forecast": round(adj, 6),
                "lower_bound": round(lower_bound, 6),
                "upper_bound": round(upper_bound, 6),
                "unit": unit,
                "selected_method": method_name,
                "validation_mae": round(mae, 6) if not np.isnan(mae) else np.nan,
                "validation_rmse": round(rmse, 6) if not np.isnan(rmse) else np.nan,
                "forecast_quality": quality,
                "eligibility_status": sel["eligibility_status"],
                "limitation": sel["limitation"],
                "raw_forecast": round(raw, 6),
                "constraint_applied": constraint,
                "constraint_reason": reason,
                "horizon_months_ahead": horizon_ahead,
                "horizon_risk": horizon_risk,
                "uncertainty_note": f"Indicative uncertainty range ±{residual_uncertainty:.2f}",
                "forecast_generated_at": generated_at,
                "training_start_date": training_start,
                "training_end_date": training_end,
                "training_observation_count": training_obs,
                "training_month_count": training_months,
                "source_actual_file": "data/analytical/analytical_six_kpi_daily.csv",
                "model_version": "1.0.0-indicative",
                "approval_status": "Indicative Prototype",
                "disclaimer": "These forecasts are indicative operational estimates generated from available synthetic historical data. They support early-warning demonstration and require further validation before operational deployment.",
            })

    return pd.DataFrame(records)


def _horizon_risk_label(horizon_ahead: int) -> str:
    mapping = {
        1: "nearest indicative horizon",
        2: "short indicative horizon",
        3: "medium indicative horizon",
        4: "extended indicative horizon",
        5: "extended indicative horizon with highest uncertainty",
    }
    return mapping.get(horizon_ahead, "unknown horizon")


def _forecast_quality(sel: pd.Series, horizon_ahead: int, residual_uncertainty: float) -> str:
    """Classify forecast confidence."""
    months = sel["training_months"]
    obs = sel["training_observations"]
    eligibility = sel["eligibility_status"]
    method = sel["selected_method"]

    if eligibility == "INSUFFICIENT HISTORICAL DATA":
        return "NOT FORECASTED"

    quality = "MODERATE INDICATIVE CONFIDENCE"
    if months < 6 or obs < 150 or method == "Naive Last Value":
        quality = "LOW INDICATIVE CONFIDENCE"
    if horizon_ahead >= 4:
        quality = "VERY LOW INDICATIVE CONFIDENCE"
    if residual_uncertainty > 20 and method != "Naive Last Value":
        quality = "LOW INDICATIVE CONFIDENCE"
    if months < 4:
        quality = "VERY LOW INDICATIVE CONFIDENCE"

    return quality


def evaluate_single_value_against_thresholds(val: float, threshold_row: pd.Series) -> str:
    """Evaluate a single numeric value against threshold boundaries.

    Returns 'Green', 'Amber', 'Red', or 'Not Assessable'.
    """
    if pd.isna(val):
        return "Not Assessable"
    lower_red = threshold_row.get("lower_red_boundary")
    lower_amber = threshold_row.get("lower_amber_boundary")
    green_lower = threshold_row.get("green_lower_boundary")
    green_upper = threshold_row.get("green_upper_boundary")
    upper_amber = threshold_row.get("upper_amber_boundary")
    upper_red = threshold_row.get("upper_red_boundary")

    # Check if any boundary is defined
    has_any = any(not pd.isna(b) for b in [lower_red, lower_amber, green_lower, green_upper, upper_amber, upper_red])
    if not has_any:
        return "Not Assessable"

    if not pd.isna(lower_red) and val <= lower_red:
        return "Red"
    if not pd.isna(upper_red) and val >= upper_red:
        return "Red"
    if not pd.isna(lower_amber) and val <= lower_amber:
        return "Amber"
    if not pd.isna(upper_amber) and val >= upper_amber:
        return "Amber"
    if not pd.isna(green_lower) and not pd.isna(green_upper):
        if green_lower <= val <= green_upper:
            return "Green"
        return "Amber"
    if not pd.isna(green_lower) and val >= green_lower:
        return "Green"
    if not pd.isna(green_upper) and val <= green_upper:
        return "Green"
    return "Amber"


def evaluate_threshold_status(forecasts: pd.DataFrame, threshold_cfg: pd.DataFrame) -> pd.DataFrame:
    """Evaluate forecast status using governed KPI threshold rules."""
    # Use only needed threshold columns to avoid name collisions
    threshold_cols = [
        "kpi_id", "directionality", "lower_red_boundary", "lower_amber_boundary",
        "green_lower_boundary", "green_upper_boundary", "upper_amber_boundary",
        "upper_red_boundary", "threshold_version",
    ]
    merged = forecasts.merge(threshold_cfg[threshold_cols], on="kpi_id", how="left")

    merged["forecast_status"] = merged.apply(
        lambda row: evaluate_single_value_against_thresholds(row["point_forecast"], row), axis=1
    )
    merged["threshold_rule"] = merged.apply(
        lambda row: (
            "Lower Red" if row["forecast_status"] == "Red" and not pd.isna(row.get("lower_red_boundary")) and row["point_forecast"] <= row.get("lower_red_boundary")
            else "Upper Red" if row["forecast_status"] == "Red" and not pd.isna(row.get("upper_red_boundary")) and row["point_forecast"] >= row.get("upper_red_boundary")
            else "Lower Amber" if row["forecast_status"] == "Amber" and not pd.isna(row.get("lower_amber_boundary")) and row["point_forecast"] <= row.get("lower_amber_boundary")
            else "Upper Amber" if row["forecast_status"] == "Amber" and not pd.isna(row.get("upper_amber_boundary")) and row["point_forecast"] >= row.get("upper_amber_boundary")
            else "Green Band" if row["forecast_status"] == "Green"
            else "Between boundaries"
        ), axis=1
    )
    merged["threshold_direction"] = merged.apply(
        lambda row: (
            "lower_red" if row["threshold_rule"] == "Lower Red"
            else "upper_red" if row["threshold_rule"] == "Upper Red"
            else "lower_amber" if row["threshold_rule"] == "Lower Amber"
            else "upper_amber" if row["threshold_rule"] == "Upper Amber"
            else "green" if row["threshold_rule"] == "Green Band"
            else "intermediate"
        ), axis=1
    )
    merged["threshold_version"] = merged.get("threshold_version", "v1.0")

    # Keep only original forecast columns plus new status columns
    keep = list(forecasts.columns) + ["forecast_status", "threshold_rule", "threshold_direction", "threshold_version"]
    return merged[keep]
