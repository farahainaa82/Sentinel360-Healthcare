"""Governed Risk & Alert evidence pack builder.

Builds a structured, deterministic evidence dictionary from the existing
governed Risk & Alert state so that the Hy3 Risk Assistant answers only
from the data the risk engine has already computed.

Contract:
  * The AI may NOT calculate new risk values.
  * The AI may NOT infer missing KPIs.
  * The AI may NOT modify warning classifications.
  * The AI may only EXPLAIN and INTERPRET the governed evidence.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional

from src.risk_alert_controller import WARNING_PRIORITY_ORDER, WARNING_PRIORITY_RANK
from src.streamlit_executive_data_loader import _DEPARTMENT_NAMES, _display_hospital


def _safe_get(
    row: Dict[str, Any], key: str, default: Any = None
) -> Any:
    """Return the value for *key* in *row* if it exists and is not None."""
    val = row.get(key)
    return val if val is not None else default


def _hash_evidence(evidence: Dict[str, Any]) -> str:
    """Deterministic content hash used for cache invalidation."""
    canonical = json.dumps(evidence, sort_keys=True, ensure_ascii=True)
    return hashlib.md5(canonical.encode("utf-8")).hexdigest()[:16]


def build_risk_ai_evidence(
    risk_state: Dict[str, Any],
    *,
    hospital_label: str,
    department_code: Optional[str],
    year: int,
    month: int,
) -> Dict[str, Any]:
    """Construct a governed evidence pack from the existing risk state.

    Parameters
    ----------
    risk_state
        The dict returned by ``build_risk_alert_state``.
    hospital_label
        The selected hospital (e.g. ``"HOSP-001"``).
    department_code
        The selected department code (e.g. ``"DEPT-ICU"``) or ``None``
        for all-departments.
    year
        The selected review year.
    month
        The selected review month (1-12).

    Returns
    -------
    dict
        A governed evidence dictionary with the exact structure the AI
        risk assistant service consumes.
    """
    summary = risk_state.get("summary", {})
    table = risk_state.get("table")
    internal_rows = risk_state.get("internal_rows", [])

    department_name = (
        "All Departments"
        if department_code is None
        else _DEPARTMENT_NAMES.get(department_code, department_code)
    )
    hospital_display = _display_hospital(hospital_label)

    # --- Priority risks (ordered by warning severity) ---
    priority_risks: List[Dict[str, Any]] = []
    for row in internal_rows:
        warning = str(row.get("warning_level") or "").strip()
        if not warning:
            continue
        priority_risks.append(_build_risk_entry(row))
    # Sort by warning priority (lowest rank = most severe first), then by target gap
    priority_risks.sort(key=_risk_priority_sort_key, reverse=False)
    # Assign sequential rank after sort (1-based for display)
    for idx, entry in enumerate(priority_risks, start=1):
        entry["risk_rank"] = idx

    # --- Emerging risks (actual status indicates deterioration but no high warning) ---
    emerging_risks = [
        _build_risk_entry(row)
        for row in internal_rows
        if _is_emerging_risk(row)
    ]
    emerging_risks.sort(key=_risk_priority_sort_key, reverse=True)

    # --- Escalating risks (High Early Warning or Escalating Warning) ---
    escalating_warnings = ["High Early Warning", "Escalating Warning"]
    escalating_risks = [
        _build_risk_entry(row)
        for row in internal_rows
        if (str(row.get("warning_level") or "").strip() in escalating_warnings)
    ]
    escalating_risks.sort(key=_risk_priority_sort_key, reverse=True)

    # --- Highest warning level among active risks ---
    active_warnings = [
        str(row.get("warning_level") or "").strip()
        for row in internal_rows
        if row.get("warning_level")
    ]
    highest_warning = _pick_highest_warning(active_warnings)

    # --- Summary counts ---
    kpis_at_risk_count = summary.get("active_actual_risks", 0)
    emerging_forecast_risk_count = summary.get("emerging_forecast_risks", 0)
    high_escalating_warning_count = len(escalating_risks)

    evidence = {
        "context": {
            "hospital_id": hospital_label,
            "hospital_display": hospital_display,
            "department_code": department_code,
            "department_name": department_name,
            "year": year,
            "month": month,
            "month_name": _MONTH_NAMES[month],
        },
        "summary": {
            "kpis_at_risk_count": kpis_at_risk_count,
            "emerging_forecast_risk_count": emerging_forecast_risk_count,
            "high_escalating_warning_count": high_escalating_warning_count,
            "highest_warning_level": highest_warning,
        },
        "priority_risks": priority_risks,
        "emerging_risks": emerging_risks,
        "escalating_risks": escalating_risks,
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


_MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
}


def _build_risk_entry(row: Dict[str, Any]) -> Dict[str, Any]:
    """Extract a single governed risk entry from an internal row."""
    return {
        "kpi_id": _safe_get(row, "kpi_id", ""),
        "kpi_name": _safe_get(row, "kpi_name", ""),
        "department_code": _safe_get(row, "department_code", ""),
        "department_name": _DEPARTMENT_NAMES.get(
            _safe_get(row, "department_code", ""),
            _safe_get(row, "department_code", ""),
        ),
        "actual_value": _safe_get(row, "latest_actual_value"),
        "actual_unit": _safe_get(row, "latest_actual_unit", ""),
        "actual_status": _safe_get(row, "latest_actual_status", ""),
        "actual_status_label": _safe_get(row, "latest_actual_status_label", ""),
        "forecast_value": _safe_get(row, "forecast_value"),
        "forecast_lower": _safe_get(row, "forecast_lower"),
        "forecast_upper": _safe_get(row, "forecast_upper"),
        "forecast_month_display": _safe_get(row, "forecast_month_display", ""),
        "warning_level": _safe_get(row, "warning_level", ""),
        "warning_level_forecast": _safe_get(row, "warning_level_forecast", ""),
        "target_value": _safe_get(row, "target_value"),
        "target_gap": _safe_get(row, "target_gap_value"),
        "target_gap_pct": _safe_get(row, "target_gap_pct"),
        "risk_direction": _safe_get(row, "risk_direction", ""),
        "suggested_action": _safe_get(row, "suggested_action", ""),
    }


def _risk_priority_sort_key(entry: Dict[str, Any]) -> tuple:
    """Return a sort key for risk severity (higher = more severe)."""
    warning = str(entry.get("warning_level") or "").strip()
    rank = WARNING_PRIORITY_RANK.get(warning, -1)
    # Tie-break on target_gap_pct (larger = more severe) if available
    gap_pct = entry.get("target_gap_pct")
    try:
        gap_val = float(gap_pct) if gap_pct is not None else 0.0
    except (TypeError, ValueError):
        gap_val = 0.0
    return (rank, gap_val)


def _is_emerging_risk(row: Dict[str, Any]) -> bool:
    """True when the row represents an emerging risk.

    A KPI is considered emerging when its actual status is "Not Improving"
    or "Deteriorating" but its warning level is NOT in the high/escalating
    tier.
    """
    actual_status = str(row.get("latest_actual_status") or "").strip().lower()
    warning = str(row.get("warning_level") or "").strip()
    is_deteriorating = actual_status in ("not improving", "deteriorating")
    is_high_warning = warning in ("High Early Warning", "Escalating")
    return is_deteriorating and not is_high_warning


def _pick_highest_warning(warnings: List[str]) -> str:
    """Return the single most severe warning from a list of warning labels."""
    # WARNING_PRIORITY_ORDER is highest-first
    for candidate in WARNING_PRIORITY_ORDER:
        if candidate in warnings:
            return candidate
    return "No active warnings"
