"""Governed evidence pack builder for the Risk & Alert management interpretation.

Builds a single-KPI evidence dictionary from the existing governed Risk & Alert
state so that Hy3 only explains, never calculates.

Contract:
  * The AI may NOT calculate new risk values.
  * The AI may NOT infer missing KPIs.
  * The AI may NOT modify warning classifications.
  * The AI may only EXPLAIN and INTERPRET the governed evidence.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Optional

import pandas as pd

from src.risk_alert_controller import (
    GOVERNED_ACTUAL_MONTH_CUTOFF,
    MONTH_LABELS,
    format_unit_value,
)
from src.streamlit_executive_data_loader import (
    _DEPARTMENT_NAMES,
)


def build_risk_interpretation_evidence(
    selected_row: Dict[str, Any],
    monthly_actual: pd.DataFrame,
    review_year: int,
    review_month: int,
) -> Dict[str, Any]:
    """Build a governed evidence pack for the selected KPI interpretation.

    Parameters
    ----------
    selected_row
        One ranked row dict from ``build_priority_risk_table``.
    monthly_actual
        Monthly actual history DataFrame (from ``get_kpi_monthly_actual_table``).
    review_year
        The selected review year.
    review_month
        The selected review month (1-12).

    Returns
    -------
    dict
        A governed evidence dictionary with the exact structure the
        ``AIRiskInterpretationService`` consumes.
    """
    kpi_id = selected_row.get("kpi_id")
    kpi_name = selected_row.get("kpi_name", kpi_id)
    unit = selected_row.get("latest_actual_unit", "")
    department_code = selected_row.get("department_code")
    department_name = (
        _DEPARTMENT_NAMES.get(department_code, department_code)
        if department_code
        else "All Departments"
    )

    # --- Historical evidence ---
    historical: Dict[str, Any] = {}
    if department_code and kpi_id and not monthly_actual.empty:
        actual_for_kpi = monthly_actual[
            (monthly_actual["department_code"] == department_code)
            & (monthly_actual["kpi_id"] == kpi_id)
            & (monthly_actual["year"] == review_year)
            & (monthly_actual["month"] <= GOVERNED_ACTUAL_MONTH_CUTOFF)
        ].sort_values("month")

        if not actual_for_kpi.empty and len(actual_for_kpi) >= 2:
            earliest = actual_for_kpi.iloc[0]
            latest = actual_for_kpi.iloc[-1]
            historical = {
                "start_month": (
                    f"{MONTH_LABELS[int(earliest['month']) - 1]} {review_year}"
                ),
                "start_value_display": format_unit_value(
                    earliest["monthly_actual_value"], unit
                ),
                "latest_actual_month": (
                    f"{MONTH_LABELS[int(latest['month']) - 1]} {review_year}"
                ),
                "latest_actual_value_display": format_unit_value(
                    latest["monthly_actual_value"], unit
                ),
                "latest_actual_status": str(
                    selected_row.get("actual_status_text", "")
                ),
            }
        elif not actual_for_kpi.empty:
            latest = actual_for_kpi.iloc[-1]
            historical = {
                "start_month": None,
                "start_value_display": None,
                "latest_actual_month": (
                    f"{MONTH_LABELS[int(latest['month']) - 1]} {review_year}"
                ),
                "latest_actual_value_display": format_unit_value(
                    latest["monthly_actual_value"], unit
                ),
                "latest_actual_status": str(
                    selected_row.get("actual_status_text", "")
                ),
            }
        else:
            historical = {
                "start_month": None,
                "start_value_display": None,
                "latest_actual_month": None,
                "latest_actual_value_display": None,
                "latest_actual_status": str(
                    selected_row.get("actual_status_text", "")
                ),
            }
    else:
        historical = {
            "start_month": None,
            "start_value_display": None,
            "latest_actual_month": None,
            "latest_actual_value_display": None,
            "latest_actual_status": str(
                selected_row.get("actual_status_text", "")
            ),
        }

    # --- Forecast evidence ---
    forecast_value = selected_row.get("forecast_value")
    has_forecast = forecast_value is not None and not pd.isna(forecast_value)
    forecast: Dict[str, Any] = {
        "forecast_month": str(selected_row.get("forecast_month", "")),
        "forecast_value_display": (
            format_unit_value(forecast_value, unit)
            if has_forecast
            else "Not available"
        ),
        "warning_level": str(selected_row.get("warning_level", "")),
        "forecast_status": str(selected_row.get("forecast_status", "")),
    }

    evidence: Dict[str, Any] = {
        "context": {
            "hospital_id": str(selected_row.get("hospital_id", "HOSP-001")),
            "department_name": department_name,
            "year": review_year,
            "selected_month": review_month,
        },
        "kpi": {
            "kpi_name": kpi_name,
            "unit": unit,
            "kpi_id": kpi_id,
        },
        "historical": historical,
        "forecast": forecast,
        "governance": {
            "evidence_is_governed": True,
            "ai_may_calculate": False,
            "ai_may_modify_values": False,
            "ai_may_infer_missing_values": False,
            "causality_confirmed": False,
        },
    }
    evidence["_evidence_hash"] = _hash_evidence(evidence)
    return evidence


def _hash_evidence(evidence: Dict[str, Any]) -> str:
    """Deterministic content hash used for cache invalidation."""
    canonical = json.dumps(evidence, sort_keys=True, ensure_ascii=True)
    return hashlib.md5(canonical.encode("utf-8")).hexdigest()[:16]
