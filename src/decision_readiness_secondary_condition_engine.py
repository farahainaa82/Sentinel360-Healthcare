"""
Decision Readiness Secondary Condition Engine for Phase 2D-4.

Retains secondary non-blocking conditions separately.
"""

import logging
import pandas as pd
from typing import Dict, Any, List

LOG = logging.getLogger("decision_readiness_secondary_condition_engine")


def build_secondary_conditions(
    readiness_df: pd.DataFrame,
    condition_flag_df: pd.DataFrame,
    logger: logging.Logger = None,
) -> pd.DataFrame:
    logger = logger or LOG
    logger.info("Building secondary conditions")

    # Non-blocking condition types
    secondary_flags = [
        "provisional_threshold_condition",
        "contradiction_condition",
        "uncertainty_condition",
        "monitoring_condition",
        "non_quantitative_condition",
    ]

    active_conditions = condition_flag_df[
        (condition_flag_df["flag_status"] == "Active") &
        (condition_flag_df["flag_name"].isin(secondary_flags))
    ].copy()

    rows: List[Dict[str, Any]] = []
    for _, cond in active_conditions.iterrows():
        pkg_id = cond["decision_package_id"]
        match = readiness_df[readiness_df["decision_package_id"] == pkg_id]
        if match.empty:
            continue

        readiness_id = match.iloc[0]["decision_readiness_id"]
        scorecard_id = match.iloc[0]["decision_scorecard_id"]

        rows.append({
            "secondary_condition_id": f"SC-{cond['condition_flag_id']}",
            "decision_readiness_id": readiness_id,
            "decision_scorecard_id": scorecard_id,
            "decision_package_id": pkg_id,
            "condition_type": cond["flag_name"],
            "condition_category": "Secondary",
            "condition_description": cond.get("flag_reason", ""),
            "severity": cond.get("flag_severity", "Low"),
            "blocking_flag": False,
            "source_phase": "2D-3",
            "source_record_id": cond["condition_flag_id"],
            "responsible_role": cond.get("responsible_role", "Operations Manager"),
            "required_action": cond.get("required_action", "Review"),
            "current_status": "Pending",
            "visibility_required": True,
        })

    result = pd.DataFrame(rows)
    logger.info("Secondary conditions built: %s records", len(result))
    return result
