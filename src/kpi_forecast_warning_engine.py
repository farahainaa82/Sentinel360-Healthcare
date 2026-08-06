"""Forecast Warning Engine — early-warning signals and suggested action linkage.

Evaluates status transitions between latest actual and forecast,
classifies warning levels, and links to existing permitted interventions.
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

from src.kpi_forecast_engine import _load_monthly_history

OUTPUT_DIR = "outputs/forecasting"


def _load_interventions(path: str = "config/intervention_catalogue.csv") -> pd.DataFrame:
    return pd.read_csv(path)


def generate_warning_signals(
    forecasts_status: pd.DataFrame,
    monthly_history: pd.DataFrame,
    interventions: pd.DataFrame,
    threshold_cfg: pd.DataFrame = None,
) -> pd.DataFrame:
    """Generate early-warning signals for each forecast month.

    Parameters
    ----------
    forecasts_status : pd.DataFrame
        Forecasts with threshold_status columns.
    monthly_history : pd.DataFrame
        Monthly actual history.
    interventions : pd.DataFrame
        Intervention catalogue.
    threshold_cfg : pd.DataFrame, optional
        Threshold configuration for evaluating latest actual status.

    Returns
    -------
    pd.DataFrame
        Warning signals with suggested action linkage.
    """
    if threshold_cfg is None:
        threshold_cfg = pd.read_csv("config/kpi_threshold_config.csv")
    from src.kpi_forecast_engine import evaluate_single_value_against_thresholds

    records = []
    approval_status = "Indicative Prototype"

    # Latest actual value per combination
    latest_actual = (
        monthly_history.sort_values(["year", "month"])
        .groupby(["hospital", "department_code", "kpi_id"])
        .last()
        .reset_index()
    )
    # Build threshold lookup
    thresh_lookup = threshold_cfg.set_index("kpi_id").to_dict("index")

    latest_actual_map = {}
    for _, r in latest_actual.iterrows():
        key = (r["hospital"], r["department_code"], r["kpi_id"])
        thresh_row = thresh_lookup.get(r["kpi_id"], {})
        status = evaluate_single_value_against_thresholds(r.get("monthly_actual_value"), pd.Series(thresh_row))
        latest_actual_map[key] = status

    for _, row in forecasts_status.iterrows():
        key = (row["hospital"], row["department_code"], row["kpi_id"])
        latest_status = latest_actual_map.get(key, "Not Assessable")
        forecast_status = row.get("forecast_status", "Not Assessable")

        warning_level, warning_reason, expected_change = _classify_warning(
            latest_status, forecast_status
        )

        # Link suggested action
        action_id, action_text, action_source, readiness, condition, rec_limit = _link_action(
            row["kpi_id"], interventions
        )

        records.append({
            "warning_id": f"WARN_{row['forecast_id']}",
            "hospital": row["hospital"],
            "department": row["department"],
            "department_code": row["department_code"],
            "kpi_id": row["kpi_id"],
            "kpi_name": row["kpi_name"],
            "forecast_year": row["forecast_year"],
            "forecast_month": row["forecast_month"],
            "point_forecast": row["point_forecast"],
            "lower_bound": row["lower_bound"],
            "upper_bound": row["upper_bound"],
            "forecast_status": forecast_status,
            "latest_actual_status": latest_status,
            "expected_status_change": expected_change,
            "warning_level": warning_level,
            "warning_reason": warning_reason,
            "horizon_months_ahead": row["horizon_months_ahead"],
            "forecast_quality": row["forecast_quality"],
            "suggested_action_id": action_id,
            "suggested_action_text": action_text,
            "action_source": action_source,
            "action_readiness": readiness,
            "outstanding_condition": condition,
            "recommendation_limit": rec_limit,
            "approval_status": approval_status,
        })

    return pd.DataFrame(records)


def _classify_warning(latest_status: str, forecast_status: str) -> Tuple[str, str, str]:
    """Classify warning level based on status transition."""
    if latest_status == "Not Assessable" or forecast_status == "Not Assessable":
        return "Not Assessable", "Insufficient data for transition assessment", "Not Assessable"

    # Map to simple severity levels
    severity = {"Green": 1, "Amber": 2, "Red": 3}
    latest_sev = severity.get(latest_status, 0)
    forecast_sev = severity.get(forecast_status, 0)

    if latest_sev == 0 or forecast_sev == 0:
        return "Not Assessable", "Unrecognised status values", "Not Assessable"

    if forecast_sev > latest_sev:
        expected = f"{latest_status} to {forecast_status}"
        if latest_status == "Green" and forecast_status == "Amber":
            return "Emerging Warning", "Green actual moving to Amber forecast", expected
        if latest_status == "Green" and forecast_status == "Red":
            return "High Early Warning", "Green actual moving to Red forecast", expected
        if latest_status == "Amber" and forecast_status == "Red":
            return "Escalating Warning", "Amber actual moving to Red forecast", expected
        return "Emerging Warning", f"Status deterioration from {latest_status} to {forecast_status}", expected

    if forecast_sev < latest_sev:
        expected = f"{latest_status} to {forecast_status}"
        return "Monitoring", f"Status improvement from {latest_status} to {forecast_status}", expected

    return "Monitoring", f"Status stable at {latest_status}", f"{latest_status} to {forecast_status}"


def _link_action(kpi_id: str, interventions: pd.DataFrame) -> Tuple[str, str, str, str, str, str]:
    """Link a forecast warning to an existing permitted intervention."""
    # Find interventions that match the KPI (case-insensitive substring)
    kpi_name_map = {
        "kpi_001": "Staffing",
        "kpi_002": "Absenteeism",
        "kpi_003": "Bed Occupancy",
        "kpi_004": "Waiting Time",
        "kpi_005": "Complaint",
        "kpi_006": "Satisfaction",
    }
    keyword = kpi_name_map.get(kpi_id, kpi_id)
    matches = interventions[
        interventions["intervention_name"].str.contains(keyword, case=False, na=False) |
        interventions["intervention_description"].str.contains(keyword, case=False, na=False)
    ]

    if matches.empty:
        return "", "No matching intervention found", "", "Not Ready", "Requires intervention catalogue review", "Link to permitted interventions only"

    # Pick the first matching intervention (simple deterministic linkage)
    match = matches.iloc[0]
    return (
        match.get("intervention_id", ""),
        f"SUGGESTED ACTION: {match.get('intervention_name', '')}",
        match.get("intervention_source", "Intervention Catalogue"),
        "Proposed",
        match.get("conditions_of_approval", "Review conditions before implementation"),
        "Demonstration only; not approved for operational deployment",
    )
