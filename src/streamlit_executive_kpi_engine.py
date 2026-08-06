"""
streamlit_executive_kpi_engine.py
KPI pressure overview engine — exactly three headline KPI cards.
"""

from typing import Dict, List, Optional

import pandas as pd

from .streamlit_executive_logging import log_event

_ALL_KPIS = [
    "Staffing Level",
    "Staff Absenteeism Rate",
    "Bed Occupancy Rate",
    "Average Patient Waiting Time",
    "Patient Complaint Rate",
    "Patient Satisfaction Score",
]


def _kpi_card(kpi_name: str, row: Optional[pd.Series]) -> Dict:
    if row is None:
        return {
            "kpi_name": kpi_name,
            "latest_value": "No data",
            "unit": "",
            "threshold_status": "Unknown",
            "trend": "",
            "department": "",
            "confidence": "",
            "border_colour": "grey",
            "trend_df": pd.DataFrame(),
            "trend_count": 0,
            "threshold_value": None,
        }

    val = row.get("kpi_value")
    val_display = ""
    if val is not None and pd.notna(val):
        unit = str(row.get("unit", "")).strip()
        if unit.lower() == "percent":
            val_display = f"{float(val):.1f}%"
        elif unit.lower() == "minutes":
            val_display = f"{float(val):.0f} min"
        elif unit.lower() == "score":
            val_display = f"{float(val):.1f}"
        else:
            val_display = f"{float(val):.1f}"
    else:
        val_display = "No data"

    status = str(row.get("threshold_status", "")).strip()
    if not status or status.lower() == "nan":
        status = "Monitoring"

    border = _card_border_colour(status)

    return {
        "kpi_name": kpi_name,
        "latest_value": val_display,
        "raw_value": val,
        "unit": str(row.get("unit", "")),
        "threshold_status": status,
        "trend": str(row.get("trend_direction", "")),
        "department": str(row.get("department_name", row.get("department_id", ""))),
        "confidence": str(row.get("data_confidence_level", "")),
        "border_colour": border,
        "trend_df": pd.DataFrame(),
        "trend_count": 0,
        "threshold_value": None,
    }


def _card_border_colour(status: str) -> str:
    s = str(status).lower()
    if "red" in s or "critical" in s or "breach" in s:
        return "red"
    if "amber" in s or "warning" in s or "condition" in s:
        return "amber"
    if "green" in s or "valid" in s or "acceptable" in s or "monitoring" in s:
        return "green"
    return "blue"


def build_three_kpi_cards(
    kpi_df: pd.DataFrame,
    dominant_kpi: Optional[str] = None,
) -> List[Dict]:
    """Return exactly three KPI cards: dominant + two related."""
    if kpi_df.empty:
        return [_kpi_card(k, None) for k in _ALL_KPIS[:3]]

    cards: List[Dict] = []
    used: set = set()

    # 1. dominant KPI
    if dominant_kpi and dominant_kpi in _ALL_KPIS:
        sub = kpi_df[kpi_df["kpi_name"] == dominant_kpi]
        row = sub.iloc[0] if not sub.empty else None
        cards.append(_kpi_card(dominant_kpi, row))
        used.add(dominant_kpi)

    # 2. next two distinct KPIs from available data, preferring ones with actual values
    available = kpi_df[kpi_df["kpi_value"].notna()]["kpi_name"].unique().tolist()
    for kpi_name in _ALL_KPIS:
        if len(cards) >= 3:
            break
        if kpi_name in used:
            continue
        if kpi_name in available:
            sub = kpi_df[kpi_df["kpi_name"] == kpi_name]
            row = sub.iloc[0] if not sub.empty else None
            cards.append(_kpi_card(kpi_name, row))
            used.add(kpi_name)

    # Fill remaining with any available
    for kpi_name in _ALL_KPIS:
        if len(cards) >= 3:
            break
        if kpi_name in used:
            continue
        sub = kpi_df[kpi_df["kpi_name"] == kpi_name]
        row = sub.iloc[0] if not sub.empty else None
        cards.append(_kpi_card(kpi_name, row))
        used.add(kpi_name)

    # Pad if needed
    while len(cards) < 3:
        for kpi_name in _ALL_KPIS:
            if kpi_name not in used:
                cards.append(_kpi_card(kpi_name, None))
                used.add(kpi_name)
                break

    log_event("THREE_KPI_CARDS_BUILT", f"count={len(cards)}")
    return cards[:3]


def build_kpi_cards(kpi_df: pd.DataFrame) -> List[Dict]:
    """Legacy compatibility — returns all six headline KPIs."""
    if kpi_df.empty:
        return []
    cards: List[Dict] = []
    for kpi_name in _ALL_KPIS:
        sub = kpi_df[kpi_df["kpi_name"] == kpi_name]
        if sub.empty:
            cards.append(
                {
                    "kpi_name": kpi_name,
                    "latest_value": "No data",
                    "threshold_status": "Unknown",
                    "departments_red": 0,
                    "trend": "",
                    "watch": False,
                    "confidence": "",
                }
            )
            continue
        row = sub.iloc[0]
        red_count = 0
        if "threshold_status" in sub.columns:
            red_count = int(
                sub["threshold_status"]
                .astype(str)
                .str.contains("Red|Critical", case=False, na=False)
                .sum()
            )
        cards.append(
            {
                "kpi_name": kpi_name,
                "latest_value": str(row.get("current_value", "")),
                "threshold_status": str(row.get("threshold_status", "")),
                "departments_red": red_count,
                "trend": str(row.get("trend", "")),
                "watch": str(row.get("watch_flag", "")).lower() == "true",
                "confidence": str(row.get("confidence_status", "")),
            }
        )
    log_event("KPI_CARDS_BUILT", f"count={len(cards)}")
    return cards
