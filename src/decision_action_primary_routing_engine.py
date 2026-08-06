"""
decision_action_primary_routing_engine.py
Phase 2D-5 — Primary action routing assignment.
"""

import pandas as pd
from typing import Dict


PRIMARY_ACTION_MAP = {
    "Ready for Integrated Management Review": "Review Integrated Decision Package",
    "Ready with Conditions": "Review Integrated Decision Package",
    "Requires Assumption Validation": "Validate Assumptions",
    "Requires Baseline Validation": "Validate Baseline",
    "Requires Financial Input": "Validate Financial Inputs",
    "Requires Benefit Validation": "Validate Benefit Assumptions",
    "Requires Budget Data": "Provide Budget Information",
    "Requires Stakeholder Validation": "Request Stakeholder Review",
    "Requires Additional Scenario Analysis": "Request Additional Scenario",
    "Requires Evidence Completion": "Request Evidence Completion",
    "Requires Lineage Completion": "Request Lineage Completion",
    "Monitoring Only": "Continue Monitoring",
    "Non-Quantitative": "Route to Non-Quantitative Review",
    "Not Suitable for Decision Use": "Reject Decision Use",
    "Rejected": "Reject Decision Use",
}


def assign_primary_action(readiness_status: str) -> str:
    return PRIMARY_ACTION_MAP.get(readiness_status, "Review Integrated Decision Package")


def build_primary_action_records(routing_df: pd.DataFrame) -> pd.DataFrame:
    """Build primary action assignment records."""
    records = []
    for _, row in routing_df.iterrows():
        status = row["final_readiness_status"]
        primary = assign_primary_action(status)
        records.append({
            "decision_action_routing_id": row["decision_action_routing_id"],
            "decision_package_id": row["decision_package_id"],
            "final_readiness_status": status,
            "primary_permitted_action": primary,
            "primary_action_id": "",  # Will be resolved later
            "assigned_flag": False,
            "selected_flag": False,
            "governance_note": f"Primary action reflects readiness status: {status}",
        })
    return pd.DataFrame(records)
