"""
decision_action_escalation_engine.py
Phase 2D-5 — Escalation routing.
"""

import pandas as pd
from typing import Dict


def load_escalation_config(config_path: str = "config/decision_action_escalation_config.csv") -> pd.DataFrame:
    return pd.read_csv(config_path)


def build_escalation_records(
    routing_df: pd.DataFrame,
    escalation_config: pd.DataFrame,
    operational_escalation: pd.DataFrame
) -> pd.DataFrame:
    """Build escalation routing records."""
    records = []
    for _, row in routing_df.iterrows():
        routing_id = row["decision_action_routing_id"]
        status = row["final_readiness_status"]
        package_id = row["decision_package_id"]

        # Match config
        match = escalation_config[escalation_config["readiness_status"] == status]
        if not match.empty:
            ec = match.iloc[0]
            escalation_status = ec["escalation_status"]
            escalation_reason = ec["escalation_reason"]
            target_role = ec["escalation_target_role"]
            queue = ec["escalation_queue"]
            timeframe = ec["escalation_timeframe_category"]
            limitation = ec["readiness_limitation"]
            attention = ec["management_attention_required"]
        else:
            escalation_status = "No Escalation"
            escalation_reason = "No escalation configured"
            target_role = ""
            queue = ""
            timeframe = "Not Applicable"
            limitation = ""
            attention = False

        # Check operational escalation separately
        op_esc = operational_escalation[operational_escalation["decision_readiness_id"] == row.get("decision_readiness_id", "")]
        if not op_esc.empty:
            op_status = op_esc.iloc[0].get("operational_escalation_status", "No Escalation")
            if op_status != "No Escalation" and escalation_status == "No Escalation":
                escalation_status = op_status
                escalation_reason = "Operational escalation trigger"
                attention = True

        records.append({
            "decision_action_routing_id": routing_id,
            "decision_package_id": package_id,
            "final_readiness_status": status,
            "escalation_required": escalation_status not in ("No Escalation", "Monitoring"),
            "escalation_status": escalation_status,
            "escalation_reason": escalation_reason,
            "escalation_target_role": target_role,
            "escalation_queue": queue,
            "escalation_timeframe_category": timeframe,
            "readiness_limitation": limitation,
            "management_attention_required": attention,
            "operational_escalation_separate": True,
            "governance_note": "Escalation separate from analytical readiness",
        })

    return pd.DataFrame(records)
