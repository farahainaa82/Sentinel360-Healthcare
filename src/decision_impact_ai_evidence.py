"""Governed evidence pack builder for the Decision & Call for Action
impact interpretation.

Builds a scenario evidence dictionary from the existing Simulation Lab handoff
so that Hy3 only explains the expected impact, never recalculates it.

Contract:
  * The AI may NOT recalculate scenario values.
  * The AI may NOT infer missing KPIs.
  * The AI may only EXPLAIN and INTERPRET the governed evidence.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Optional

from src.streamlit_executive_page_controller import format_unit_value


def _compute_target_status(
    selected_scenario_value: Any,
    threshold_cfg: Any,
    kpi_id: str,
) -> tuple[bool, bool, str]:
    """Return (target_met, ceiling_reached, target_display) for the scenario.

    All three booleans / text are derived from the governed threshold config.
    No new calculations are performed beyond the threshold comparison itself.
    """
    cfg = threshold_cfg if isinstance(threshold_cfg, dict) else {}
    row = cfg.get(kpi_id) if kpi_id else None
    if not isinstance(row, dict):
        return False, False, "Not configured"

    direction = (row.get("directionality") or "").strip().upper()
    lo = row.get("green_lower_boundary")
    hi = row.get("green_upper_boundary")
    unit = (row.get("unit") or "").strip()

    if lo is None or hi is None:
        return False, False, "Not configured"

    try:
        lo_f = float(lo)
        hi_f = float(hi)
    except (TypeError, ValueError):
        return False, False, "Not configured"

    target_display = "Not configured"
    try:
        if direction == "HIGHER_IS_BETTER":
            target_display = f"≥ {format_unit_value(lo_f, unit)}"
        elif direction == "LOWER_IS_BETTER":
            target_display = f"≤ {format_unit_value(hi_f, unit)}"
        elif direction == "TARGET_BAND":
            target_display = (
                f"{format_unit_value(lo_f, unit)} – "
                f"{format_unit_value(hi_f, unit)}"
            )
    except Exception:
        target_display = "Not configured"

    if selected_scenario_value is None:
        return False, False, target_display

    try:
        v = float(selected_scenario_value)
    except (TypeError, ValueError):
        return False, False, target_display

    target_met = False
    ceiling_reached = False

    if direction == "HIGHER_IS_BETTER":
        target_met = v >= lo_f
        ceiling_reached = v >= hi_f
    elif direction == "LOWER_IS_BETTER":
        target_met = v <= hi_f
        ceiling_reached = v <= lo_f
    elif direction == "TARGET_BAND":
        target_met = lo_f <= v < hi_f
        ceiling_reached = target_met

    return target_met, ceiling_reached, target_display


def build_decision_impact_evidence(
    *,
    hospital_id: str,
    department_name: str,
    kpi_id: str,
    kpi_name: str,
    forecast_month_label: str,
    do_nothing_forecast: Any,
    selected_scenario_value: Any,
    change_value: Any,
    change_pct: Any,
    action_strategy: str,
    resource_line: str,
    selected_action_level: str,
    threshold_cfg: Any,
    unit: str,
) -> Dict[str, Any]:
    """Build a governed evidence pack for the Decision Impact interpretation.

    Parameters
    ----------
    All keyword arguments carry the existing governed values from the Simulation
    Lab handoff and the Decision page context.  None are recalculated.

    Returns
    -------
    dict
        Evidence dictionary with the exact structure the
        ``AIDecisionImpactSynthesisService`` consumes.
    """
    target_met, ceiling_reached, target_display = _compute_target_status(
        selected_scenario_value, threshold_cfg, kpi_id
    )

    evidence: Dict[str, Any] = {
        "context": {
            "hospital_id": str(hospital_id),
            "department_name": str(department_name),
            "forecast_month": str(forecast_month_label),
        },
        "kpi": {
            "kpi_id": str(kpi_id),
            "kpi_name": str(kpi_name),
            "target_display": target_display,
            "unit": str(unit),
        },
        "baseline": {
            "do_nothing_forecast_display": format_unit_value(
                do_nothing_forecast, unit
            )
            if do_nothing_forecast is not None
            else "Not available",
        },
        "scenario": {
            "selected_action_level": str(selected_action_level),
            "selected_scenario_display": format_unit_value(
                selected_scenario_value, unit
            )
            if selected_scenario_value is not None
            else "Not available",
            "expected_kpi_change_display": format_unit_value(change_value, unit)
            if change_value is not None
            else "Not available",
            "relative_change_display": format_unit_value(change_pct, "%")
            if change_pct is not None
            else "Not available",
            "action_strategy": str(action_strategy),
            "resource_commitment": str(resource_line),
            "governed_ceiling_reached": bool(ceiling_reached),
            "target_met": bool(target_met),
        },
        "governance": {
            "evidence_is_governed": True,
            "ai_may_calculate": False,
            "ai_may_modify_values": False,
            "ai_may_infer_missing_values": False,
            "causality_confirmed": False,
        },
    }

    # Deterministic evidence hash for cache keys (stable ordering)
    evidence_str = json.dumps(evidence, sort_keys=True, separators=(",", ":"))
    evidence["_evidence_hash"] = hashlib.sha256(
        evidence_str.encode("utf-8")
    ).hexdigest()[:32]

    return evidence


def build_decision_impact_cache_key(evidence: Dict[str, Any]) -> str:
    """Build a deterministic cache key for the decision impact interpretation.

    The key never contains the API key.  It uses the evidence content hash
    (which changes when any governed value changes).
    """
    evidence_hash = evidence.get("_evidence_hash", "")
    return f"s360_decision_impact_cache_v1:{evidence_hash}"
