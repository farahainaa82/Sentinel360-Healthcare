"""
decision_action_data_contract_engine.py
Phase 2D-5 — Streamlit action data contract.
"""

import pandas as pd
from typing import List, Dict


def build_streamlit_contract(
    routing_df: pd.DataFrame,
    primary_actions: pd.DataFrame,
    eligibility_df: pd.DataFrame,
    role_df: pd.DataFrame,
    escalation_df: pd.DataFrame,
    prerequisite_df: pd.DataFrame,
    blocking_df: pd.DataFrame,
    monitoring_df: pd.DataFrame
) -> pd.DataFrame:
    """Build Streamlit-ready action data contract."""
    records = []
    for _, row in routing_df.iterrows():
        routing_id = row["decision_action_routing_id"]
        package_id = row["decision_package_id"]
        status = row["final_readiness_status"]

        pa = primary_actions[primary_actions["decision_action_routing_id"] == routing_id]
        primary_action = pa["primary_permitted_action"].iloc[0] if not pa.empty else ""

        rl = role_df[role_df["decision_action_routing_id"] == routing_id]
        responsible = rl["primary_responsible_role"].iloc[0] if not rl.empty else ""

        esc = escalation_df[escalation_df["decision_action_routing_id"] == routing_id]
        escalation_status = esc["escalation_status"].iloc[0] if not esc.empty else "No Escalation"

        # Action button model for primary action
        elg = eligibility_df[
            (eligibility_df["decision_action_routing_id"] == routing_id) &
            (eligibility_df["action_name"] == primary_action)
        ]
        if not elg.empty:
            eligibility = elg.iloc[0]["action_eligibility_status"]
            enabled = eligibility in ("Allowed", "Allowed with Conditions")
            disabled_reason = "" if enabled else f"Action is {eligibility}"
        else:
            eligibility = "Unknown"
            enabled = False
            disabled_reason = "No eligibility found"

        records.append({
            "panel_type": "Action Summary",
            "decision_action_routing_id": routing_id,
            "decision_package_id": package_id,
            "final_readiness_status": status,
            "primary_permitted_action": primary_action,
            "primary_queue": "",
            "responsible_role": responsible,
            "escalation_status": escalation_status,
            "approval_status": "Pending Management Review",
            "action_id": "",
            "action_name": primary_action,
            "action_eligibility_status": eligibility,
            "enabled_flag": enabled,
            "disabled_reason": disabled_reason,
            "confirmation_required": True,
            "audit_required": True,
            "management_selection_required": True,
            "selected_flag": False,
            "governance_note": "Streamlit contract - UI eligibility only",
        })

    # Add action button models for all actions
    for _, elg in eligibility_df.iterrows():
        routing_id = elg["decision_action_routing_id"]
        eligibility = elg["action_eligibility_status"]
        enabled = eligibility in ("Allowed", "Allowed with Conditions")

        records.append({
            "panel_type": "Action Button",
            "decision_action_routing_id": routing_id,
            "decision_package_id": elg["decision_package_id"],
            "final_readiness_status": "",
            "primary_permitted_action": "",
            "primary_queue": "",
            "responsible_role": "",
            "escalation_status": "",
            "approval_status": "Pending Management Review",
            "action_id": elg["action_id"],
            "action_name": elg["action_name"],
            "action_eligibility_status": eligibility,
            "enabled_flag": enabled,
            "disabled_reason": "" if enabled else f"Action is {eligibility}",
            "confirmation_required": True,
            "audit_required": True,
            "management_selection_required": True,
            "selected_flag": False,
            "governance_note": "Streamlit contract - UI eligibility only",
        })

    return pd.DataFrame(records)
