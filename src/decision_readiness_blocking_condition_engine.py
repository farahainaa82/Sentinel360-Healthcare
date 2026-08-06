"""
Decision Readiness Blocking Condition Engine for Phase 2D-4.

Creates one blocking-condition record for every active blocking issue.
"""

import logging
import pandas as pd
from typing import Dict, Any, List

LOG = logging.getLogger("decision_readiness_blocking_condition_engine")


def build_blocking_conditions(
    readiness_df: pd.DataFrame,
    condition_flag_df: pd.DataFrame,
    logger: logging.Logger = None,
) -> pd.DataFrame:
    logger = logger or LOG
    logger.info("Building blocking conditions")

    # Filter to active conditions that are blocking
    blocking_flags = [
        "assumption_validation_condition",
        "baseline_validation_condition",
        "financial_input_condition",
        "stakeholder_validation_condition",
        "scenario_completeness_condition",
        "evidence_completeness_condition",
        "lineage_completeness_condition",
        "blocking_condition",
    ]

    active_conditions = condition_flag_df[
        (condition_flag_df["flag_status"] == "Active") &
        (condition_flag_df["flag_name"].isin(blocking_flags))
    ].copy()

    rows: List[Dict[str, Any]] = []
    for _, cond in active_conditions.iterrows():
        pkg_id = cond["decision_package_id"]
        # Find matching readiness record
        match = readiness_df[readiness_df["decision_package_id"] == pkg_id]
        if match.empty:
            continue

        readiness_id = match.iloc[0]["decision_readiness_id"]
        scorecard_id = match.iloc[0]["decision_scorecard_id"]

        severity = cond.get("flag_severity", "Moderate")
        is_blocking = severity in ("High", "Critical") or cond["flag_name"] == "blocking_condition"

        rows.append({
            "blocking_condition_id": f"BC-{cond['condition_flag_id']}",
            "decision_readiness_id": readiness_id,
            "decision_scorecard_id": scorecard_id,
            "decision_package_id": pkg_id,
            "condition_type": cond["flag_name"],
            "condition_category": "Blocking" if is_blocking else "Conditional",
            "condition_description": cond.get("flag_reason", ""),
            "severity": severity,
            "blocking_flag": is_blocking,
            "source_phase": "2D-3",
            "source_record_id": cond["condition_flag_id"],
            "responsible_role": cond.get("responsible_role", "Operations Manager"),
            "required_resolution": cond.get("required_action", "Review and resolve before proceeding"),
            "resolution_evidence_required": "Validation documentation required",
            "current_status": "Pending",
            "transition_enabled_after_resolution": False,
        })

    result = pd.DataFrame(rows)
    logger.info("Blocking conditions built: %s records", len(result))
    return result
