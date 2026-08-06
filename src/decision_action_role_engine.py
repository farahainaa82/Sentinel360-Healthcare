"""
decision_action_role_engine.py
Phase 2D-5 — Responsible role routing.
"""

import pandas as pd
from typing import Dict


def load_role_config(config_path: str = "config/decision_action_role_config.csv") -> pd.DataFrame:
    return pd.read_csv(config_path)


def assign_responsible_roles(
    routing_df: pd.DataFrame,
    primary_actions: pd.DataFrame,
    role_config: pd.DataFrame
) -> pd.DataFrame:
    """Assign responsible roles based on primary action."""
    records = []
    for _, row in routing_df.iterrows():
        routing_id = row["decision_action_routing_id"]
        package_id = row["decision_package_id"]
        status = row["final_readiness_status"]

        # Get primary action for this routing
        pa = primary_actions[primary_actions["decision_action_routing_id"] == routing_id]
        primary_action = pa["primary_permitted_action"].iloc[0] if not pa.empty else ""

        # Lookup role config
        role_match = role_config[role_config["action_name"] == primary_action]
        if not role_match.empty:
            rc = role_match.iloc[0]
            primary_role = rc["primary_role"]
            secondary_role = rc["secondary_role"] if pd.notna(rc["secondary_role"]) else ""
            tertiary_role = rc["tertiary_role"] if pd.notna(rc["tertiary_role"]) else ""
        else:
            primary_role = "Hospital COO / General Manager"
            secondary_role = ""
            tertiary_role = ""

        records.append({
            "decision_action_routing_id": routing_id,
            "decision_package_id": package_id,
            "final_readiness_status": status,
            "primary_permitted_action": primary_action,
            "primary_responsible_role": primary_role,
            "secondary_responsible_role": secondary_role,
            "tertiary_responsible_role": tertiary_role,
            "role_assignment_basis": "Action-type based governed role assignment",
            "governance_note": "No named individuals assigned",
        })

    return pd.DataFrame(records)
