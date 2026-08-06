"""
decision_action_secondary_routing_engine.py
Phase 2D-5 — Secondary permitted actions.
"""

import pandas as pd
from typing import List, Dict


SECONDARY_ACTION_MAP = {
    "Ready for Integrated Management Review": [
        "Compare Scenario Options",
        "Request Stakeholder Review",
        "Defer Decision",
    ],
    "Ready with Conditions": [
        "Compare Scenario Options",
        "Validate Assumptions",
        "Validate Baseline",
        "Validate Financial Inputs",
        "Request Stakeholder Review",
        "Continue Monitoring",
    ],
    "Requires Assumption Validation": [
        "Request Stakeholder Review",
        "Continue Monitoring",
        "Defer Decision",
    ],
    "Requires Baseline Validation": [
        "Request Evidence Completion",
        "Continue Monitoring",
        "Defer Decision",
    ],
    "Requires Financial Input": [
        "Provide Budget Information",
        "Request Stakeholder Review",
        "Continue Monitoring",
    ],
    "Requires Benefit Validation": [
        "Request Stakeholder Review",
        "Defer Decision",
    ],
    "Requires Budget Data": [
        "Validate Financial Inputs",
        "Defer Decision",
    ],
    "Requires Stakeholder Validation": [
        "Validate Assumptions",
        "Validate Financial Inputs",
        "Continue Monitoring",
    ],
    "Requires Additional Scenario Analysis": [
        "Validate Assumptions",
        "Validate Baseline",
        "Continue Monitoring",
    ],
    "Requires Evidence Completion": [
        "Request Stakeholder Review",
        "Continue Monitoring",
        "Defer Decision",
    ],
    "Requires Lineage Completion": [
        "Request Evidence Completion",
        "Defer Decision",
    ],
    "Monitoring Only": [
        "No Action - Monitoring Continues",
        "Request Stakeholder Review",
    ],
    "Non-Quantitative": [
        "Request Stakeholder Review",
        "Request Evidence Completion",
        "Continue Monitoring",
        "Defer Decision",
    ],
    "Not Suitable for Decision Use": [
        "Defer Decision",
        "Request Evidence Completion",
        "Request Lineage Completion",
    ],
    "Rejected": [],
}


def build_secondary_action_records(routing_df: pd.DataFrame) -> pd.DataFrame:
    records = []
    for _, row in routing_df.iterrows():
        status = row["final_readiness_status"]
        actions = SECONDARY_ACTION_MAP.get(status, [])
        for action in actions:
            records.append({
                "decision_action_routing_id": row["decision_action_routing_id"],
                "decision_package_id": row["decision_package_id"],
                "secondary_permitted_action": action,
                "assigned_flag": False,
                "selected_flag": False,
                "governance_note": f"Secondary action for {status}",
            })
    return pd.DataFrame(records)
