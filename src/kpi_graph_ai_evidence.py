"""
Governed KPI graph evidence builder for AI interpretation.

Produces a JSON-safe evidence object using existing card values only.
No calculation, no inference, no modification.
"""

from typing import Any, Dict, Optional

import pandas as pd


def build_kpi_graph_evidence(
    card: Dict[str, Any],
    hospital_id: str,
    department_name: str,
    year: int,
    month: int,
) -> Dict[str, Any]:
    """Build JSON-safe governed evidence for a single KPI graph.

    Parameters
    ----------
    card: dict
        KPI card produced by ``build_kpi_cards`` / ``_build_forecast_kpi_card``.
    hospital_id: str
        Selected hospital identifier.
    department_name: str
        Human-readable department name (or "ALL").
    year: int
        Selected year.
    month: int
        Selected month (1-12).

    Returns
    -------
    dict
        JSON-safe evidence payload for the Hy3 synthesis service.
    """
    kpi_id = card.get("kpi_id", "")
    kpi_name = card.get("kpi_name", kpi_id)
    unit = card.get("unit", "")
    period_type = card.get("period_type", "FORECAST")

    month_names = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]

    # ------------------------------------------------------------------
    # Latest actual from annual_df (last actual month before forecast)
    # ------------------------------------------------------------------
    annual_df = card.get("annual_df")
    latest_actual_display: Optional[str] = None
    latest_actual_month: Optional[str] = None
    actual_status: Optional[str] = None

    if isinstance(annual_df, pd.DataFrame) and not annual_df.empty:
        # Actual rows have supported == True (or no source_type column)
        if "supported" in annual_df.columns:
            actual_rows = annual_df[annual_df["supported"] == True].copy()  # noqa: E712
        else:
            actual_rows = annual_df.copy()
        if not actual_rows.empty:
            last_actual = actual_rows.iloc[-1]
            val = last_actual.get("monthly_value")
            m = last_actual.get("month")
            if val is not None and not pd.isna(val):
                latest_actual_display = (
                    f"{float(val):.1f}{' ' + unit if unit else ''}"
                )
                if m is not None:
                    latest_actual_month = f"{month_names[int(m) - 1]} {year}"

    # ------------------------------------------------------------------
    # Forecast info
    # ------------------------------------------------------------------
    forecast_display = card.get("latest_value", "N/A")
    forecast_month = f"{month_names[month - 1]} {year}" if 1 <= month <= 12 else None

    expected_change = str(card.get("expected_status_change", "") or "").strip()
    warning_level = str(card.get("warning_level", "Monitoring") or "Monitoring").strip()
    forecast_quality = str(card.get("forecast_quality", "") or "").strip()

    evidence: Dict[str, Any] = {
        "context": {
            "hospital_id": hospital_id,
            "department_name": department_name,
            "selected_year": year,
            "selected_month": month,
            "period_type": period_type,
        },
        "kpi": {
            "kpi_id": kpi_id,
            "kpi_name": kpi_name,
            "unit": unit,
        },
        "actual": {
            "latest_actual_display": latest_actual_display,
            "latest_actual_month": latest_actual_month,
            "actual_status": actual_status,
        },
        "forecast": {
            "forecast_display": forecast_display,
            "forecast_month": forecast_month,
            "warning_level": warning_level,
            "confidence_label": _map_quality_to_confidence(forecast_quality),
            "expected_status_change": expected_change,
        },
        "governance": {
            "evidence_is_governed": True,
            "ai_may_calculate": False,
            "ai_may_modify_values": False,
            "ai_may_infer_missing_values": False,
            "causality_confirmed": False,
        },
    }

    # Include threshold config if the card carries it
    threshold_cfg = card.get("threshold_config")
    if threshold_cfg:
        evidence["target"] = {
            "directionality": threshold_cfg.get("directionality", ""),
            "green_lower": _to_float(threshold_cfg.get("green_lower_boundary")),
            "green_upper": _to_float(threshold_cfg.get("green_upper_boundary")),
        }

    return evidence


def _map_quality_to_confidence(quality: str) -> str:
    """Map forecast quality label to a confidence label."""
    q = str(quality or "").strip().lower()
    if "high" in q:
        return "High Confidence"
    if "low" in q:
        return "Low Confidence"
    return "Moderate Confidence"


def _to_float(x: Any) -> Optional[float]:
    if x is None or (isinstance(x, str) and str(x).strip() == ""):
        return None
    try:
        return float(x)
    except (ValueError, TypeError):
        return None
