"""
decision_action_eligibility_engine.py
Phase 2D-5 — Action eligibility engine.
Assigns exactly one eligibility status per action-package combination.
"""

import pandas as pd
from typing import Dict, List


def load_eligibility_config(config_path: str = "config/decision_action_eligibility_config.csv") -> pd.DataFrame:
    return pd.read_csv(config_path)


def evaluate_action_eligibility(
    readiness_row: pd.Series,
    eligibility_config: pd.DataFrame,
    action_catalogue: pd.DataFrame
) -> List[Dict]:
    """
    For a single readiness record, evaluate eligibility for all catalogue actions.
    Returns list of eligibility records.
    """
    readiness_status = readiness_row["final_readiness_status"]
    routing_id = readiness_row.get("decision_action_routing_id", "")
    package_id = readiness_row.get("decision_package_id", "")

    # Filter config for this readiness status
    status_config = eligibility_config[eligibility_config["readiness_status"] == readiness_status]

    results = []
    for _, action in action_catalogue.iterrows():
        action_id = action["action_id"]
        action_name = action["action_name"]

        match = status_config[status_config["action_id"] == action_id]
        if not match.empty:
            eligibility = match.iloc[0]["eligibility_status"]
            reason = f"Governed eligibility for {readiness_status}"
            prereq = match.iloc[0].get("prerequisite_required", False)
            blocking_gate = match.iloc[0].get("blocking_gate_affected", "")
        else:
            eligibility = "Not Applicable"
            reason = f"No eligibility rule defined for {action_name} under {readiness_status}"
            prereq = False
            blocking_gate = ""

        results.append({
            "decision_action_routing_id": routing_id,
            "decision_package_id": package_id,
            "action_id": action_id,
            "action_name": action_name,
            "action_eligibility_status": eligibility,
            "action_reason": reason,
            "prerequisite_count": 1 if prereq else 0,
            "blocking_condition_count": 1 if blocking_gate and blocking_gate != "None" else 0,
            "audit_required": True,
            "management_selection_required": True,
            "readiness_status": readiness_status,
            "blocking_gate_affected": blocking_gate,
        })

    return results
