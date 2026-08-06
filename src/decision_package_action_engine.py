"""
Decision Package Action Engine for Phase 2D-2.

Generates permitted management actions per package. No action is marked selected.
"""

import logging
import pandas as pd
from typing import List, Dict, Any

LOG = logging.getLogger("decision_package_action_engine")

ACTION_TEMPLATES: List[Dict[str, Any]] = [
    {
        "action_name": "Review Integrated Decision Package",
        "allowed": True,
        "reason": "Fundamental step for all packages.",
        "prerequisite": "None",
        "blocking_condition": "None",
        "audit_required": True,
    },
    {
        "action_name": "Compare Scenario Options",
        "allowed": True,
        "reason": "Permitted when scenarios are available.",
        "prerequisite": "Scenario data present",
        "blocking_condition": "No scenario data",
        "audit_required": True,
    },
    {
        "action_name": "Validate Assumptions",
        "allowed": True,
        "reason": "Required when assumption gaps exist.",
        "prerequisite": "Assumption validation question open",
        "blocking_condition": "None",
        "audit_required": True,
    },
    {
        "action_name": "Validate Baseline",
        "allowed": True,
        "reason": "Required when baseline uncertainty exists.",
        "prerequisite": "Baseline validation question open",
        "blocking_condition": "None",
        "audit_required": True,
    },
    {
        "action_name": "Validate Financial Inputs",
        "allowed": True,
        "reason": "Required when financial completeness is partial.",
        "prerequisite": "Financial validation question open",
        "blocking_condition": "None",
        "audit_required": True,
    },
    {
        "action_name": "Request Additional Scenario",
        "allowed": True,
        "reason": "Permitted when current scenarios are insufficient.",
        "prerequisite": "Scenario analysis incomplete",
        "blocking_condition": "None",
        "audit_required": True,
    },
    {
        "action_name": "Request Stakeholder Review",
        "allowed": True,
        "reason": "Permitted when stakeholder alignment is uncertain.",
        "prerequisite": "Stakeholder question open",
        "blocking_condition": "None",
        "audit_required": True,
    },
    {
        "action_name": "Proceed to Limited-Trial Consideration",
        "allowed": True,
        "reason": "Permitted only for Ready with Conditions packages.",
        "prerequisite": "Package readiness is Ready with Conditions",
        "blocking_condition": "Package not Ready with Conditions",
        "audit_required": True,
    },
    {
        "action_name": "Continue Monitoring",
        "allowed": True,
        "reason": "Default action for Monitoring Only packages.",
        "prerequisite": "None",
        "blocking_condition": "None",
        "audit_required": False,
    },
    {
        "action_name": "Defer Decision",
        "allowed": True,
        "reason": "Permitted when further validation is needed.",
        "prerequisite": "Validation questions remain open",
        "blocking_condition": "None",
        "audit_required": True,
    },
    {
        "action_name": "Reject Decision Use",
        "allowed": True,
        "reason": "Permitted when package is Not Suitable.",
        "prerequisite": "Package marked Not Suitable",
        "blocking_condition": "None",
        "audit_required": True,
    },
]


def build_actions(integrated_df: pd.DataFrame, logger: logging.Logger = None) -> pd.DataFrame:
    logger = logger or LOG
    logger.info("Building permitted management actions")

    rows: List[Dict[str, Any]] = []
    for _, rec in integrated_df.iterrows():
        pkg_id = f"DPKG-{rec['approval_package_id']}"
        status = rec["decision_status"]

        for act in ACTION_TEMPLATES:
            # Adjust allowance based on status
            allowed = act["allowed"]
            if act["action_name"] == "Proceed to Limited-Trial Consideration" and status != "Ready with Conditions":
                allowed = False
            if act["action_name"] == "Continue Monitoring" and status != "Monitoring Only":
                allowed = True  # Still allowed, just not default
            if act["action_name"] == "Reject Decision Use" and status not in ("Not Suitable for Decision Use", "Rejected"):
                allowed = True  # Always technically allowed

            rows.append({
                "management_action_id": f"{pkg_id}-ACT-{act['action_name'][:3].upper()}",
                "decision_package_id": pkg_id,
                "approval_package_id": rec["approval_package_id"],
                "action_name": act["action_name"],
                "action_allowed": allowed,
                "action_reason": act["reason"],
                "prerequisite": act["prerequisite"],
                "blocking_condition": act["blocking_condition"],
                "audit_required": act["audit_required"],
                "action_selected": False,
            })

    df = pd.DataFrame(rows)
    logger.info(f"Actions built: {len(df)} total")
    return df
