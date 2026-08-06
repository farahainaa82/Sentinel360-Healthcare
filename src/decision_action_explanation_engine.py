"""
decision_action_explanation_engine.py
Phase 2D-5 — Action routing explanation per package.
"""

import pandas as pd
from typing import List, Dict


def build_explanation_records(
    routing_df: pd.DataFrame,
    primary_actions: pd.DataFrame,
    eligibility_df: pd.DataFrame,
    role_df: pd.DataFrame,
    escalation_df: pd.DataFrame,
    blocking_df: pd.DataFrame
) -> pd.DataFrame:
    """Create one concise explanation per routing package."""
    records = []
    for _, row in routing_df.iterrows():
        routing_id = row["decision_action_routing_id"]
        status = row["final_readiness_status"]
        package_id = row["decision_package_id"]

        primary = primary_actions[primary_actions["decision_action_routing_id"] == routing_id]
        primary_action = primary["primary_permitted_action"].iloc[0] if not primary.empty else "Unknown"

        roles = role_df[role_df["decision_action_routing_id"] == routing_id]
        responsible = roles["primary_responsible_role"].iloc[0] if not roles.empty else "Unknown"

        esc = escalation_df[escalation_df["decision_action_routing_id"] == routing_id]
        escalation_required = esc["escalation_required"].iloc[0] if not esc.empty else False
        escalation_status = esc["escalation_status"].iloc[0] if not esc.empty else "No Escalation"

        # Find main blocked action
        blocks = blocking_df[blocking_df["decision_action_routing_id"] == routing_id]
        if not blocks.empty:
            main_blocked = blocks.iloc[0]["action_name"]
            block_reason = blocks.iloc[0]["blocking_reason"]
        else:
            main_blocked = "None"
            block_reason = "No blocking conditions"

        explanation = (
            f"Current readiness: {status}. "
            f"Primary permitted action: {primary_action}. "
            f"This action is permitted because the readiness status governs allowed actions. "
            f"Main blocking action: {main_blocked}. "
            f"Reason: {block_reason}. "
            f"Responsible role: {responsible}. "
            f"Escalation requirement: {'Yes' if escalation_required else 'No'} ({escalation_status}). "
            f"What must happen next: Management review of primary permitted action and conditions. "
            f"What this routing does not mean: No action is selected or approved. "
            f"This routing supports management workflow and does not constitute action selection or approval."
        )

        records.append({
            "decision_action_routing_id": routing_id,
            "decision_package_id": package_id,
            "final_readiness_status": status,
            "action_routing_explanation": explanation,
            "primary_permitted_action": primary_action,
            "main_blocking_action": main_blocked,
            "main_blocking_reason": block_reason,
            "responsible_role": responsible,
            "escalation_required": escalation_required,
            "escalation_status": escalation_status,
            "governance_note": "Explanation for management workflow support only",
        })

    return pd.DataFrame(records)
