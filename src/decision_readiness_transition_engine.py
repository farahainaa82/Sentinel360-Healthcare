"""
Decision Readiness Transition Engine for Phase 2D-4.

Creates governed transition rules showing how a package may move between states.
Rules are created only; no transitions are executed.
"""

import logging
import pandas as pd
from typing import Dict, Any, List

LOG = logging.getLogger("decision_readiness_transition_engine")

TRANSITION_RULES = [
    {"current_state": "Requires Assumption Validation", "eligible_next_state": "Ready with Conditions", "transition_requirements": "Required assumptions validated"},
    {"current_state": "Requires Baseline Validation", "eligible_next_state": "Ready with Conditions", "transition_requirements": "Baseline validation passes"},
    {"current_state": "Requires Financial Input", "eligible_next_state": "Ready with Conditions", "transition_requirements": "Mandatory financial inputs provided and validated"},
    {"current_state": "Requires Budget Data", "eligible_next_state": "Ready with Conditions", "transition_requirements": "Authoritative budget data supplied"},
    {"current_state": "Ready with Conditions", "eligible_next_state": "Ready for Integrated Management Review", "transition_requirements": "All blocking conditions resolved and confirmations completed"},
    {"current_state": "Monitoring Only", "eligible_next_state": "Ready with Conditions", "transition_requirements": "Escalation trigger met and valid intervention package available"},
    {"current_state": "Non-Quantitative", "eligible_next_state": "Ready with Conditions", "transition_requirements": "Sufficient governed quantitative data become available"},
    {"current_state": "Requires Evidence Completion", "eligible_next_state": "Ready with Conditions", "transition_requirements": "Required evidence references provided"},
    {"current_state": "Requires Lineage Completion", "eligible_next_state": "Ready with Conditions", "transition_requirements": "Source-to-decision lineage completed"},
    {"current_state": "Requires Stakeholder Validation", "eligible_next_state": "Ready with Conditions", "transition_requirements": "Stakeholder confirmation received"},
    {"current_state": "Requires Benefit Validation", "eligible_next_state": "Ready with Conditions", "transition_requirements": "Benefit eligibility resolved"},
    {"current_state": "Requires Additional Scenario Analysis", "eligible_next_state": "Ready with Conditions", "transition_requirements": "Additional modelling completed"},
]


def build_transitions(
    readiness_df: pd.DataFrame,
    logger: logging.Logger = None,
) -> pd.DataFrame:
    logger = logger or LOG
    logger.info("Building transition rules")

    rows: List[Dict[str, Any]] = []
    for _, rec in readiness_df.iterrows():
        readiness_id = rec["decision_readiness_id"]
        pkg_id = rec["decision_package_id"]
        current = rec["final_readiness_status"]

        # Find applicable transitions
        for idx, rule in enumerate(TRANSITION_RULES):
            if rule["current_state"] == current:
                rows.append({
                    "transition_rule_id": f"TRANS-{readiness_id}-{idx}",
                    "decision_readiness_id": readiness_id,
                    "decision_package_id": pkg_id,
                    "current_state": rule["current_state"],
                    "eligible_next_state": rule["eligible_next_state"],
                    "transition_requirements": rule["transition_requirements"],
                    "transition_not_executed_flag": True,
                    "transition_executed": False,
                    "execution_timestamp": "",
                    "executed_by": "",
                    "governance_note": "Rule created only; transition not executed in Step 2D-4",
                })

        # If no transition found, add a placeholder
        if not any(r["current_state"] == current for r in TRANSITION_RULES):
            rows.append({
                "transition_rule_id": f"TRANS-{readiness_id}-NA",
                "decision_readiness_id": readiness_id,
                "decision_package_id": pkg_id,
                "current_state": current,
                "eligible_next_state": "No eligible transition defined",
                "transition_requirements": "No transition available from this state",
                "transition_not_executed_flag": True,
                "transition_executed": False,
                "execution_timestamp": "",
                "executed_by": "",
                "governance_note": "Terminal or stable state; no transition defined",
            })

    result = pd.DataFrame(rows)
    logger.info("Transition rules built: %s records", len(result))
    return result
