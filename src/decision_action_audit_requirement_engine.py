"""
decision_action_audit_requirement_engine.py
Phase 2D-5 — Action audit requirements.
"""

import pandas as pd
import uuid
from typing import List, Dict


def load_audit_config(config_path: str = "config/decision_action_audit_config.csv") -> pd.DataFrame:
    return pd.read_csv(config_path)


def build_audit_records(
    eligibility_df: pd.DataFrame,
    audit_config: pd.DataFrame
) -> pd.DataFrame:
    """Build audit requirement records for all action eligibility entries."""
    records = []
    for _, row in eligibility_df.iterrows():
        action_id = row["action_id"]
        action_name = row["action_name"]
        routing_id = row["decision_action_routing_id"]

        match = audit_config[audit_config["action_id"] == action_id]
        if not match.empty:
            ac = match.iloc[0]
            audit_required = ac["audit_required"]
            event_type = ac["audit_event_type"]
            actor = ac["required_actor_role"]
            evidence = ac["evidence_attachment_required"]
            reason = ac["reason_required"]
            ts = ac["timestamp_required"]
            ref = ac["approval_reference_required"]
            future_status = ac["future_audit_status"]
        else:
            audit_required = False
            event_type = ""
            actor = ""
            evidence = False
            reason = False
            ts = False
            ref = False
            future_status = "Awaiting Management Action"

        records.append({
            "audit_requirement_id": f"AUD-{uuid.uuid4().hex[:8].upper()}",
            "decision_action_routing_id": routing_id,
            "action_id": action_id,
            "action_name": action_name,
            "audit_required": audit_required,
            "audit_event_type": event_type,
            "required_actor_role": actor,
            "evidence_attachment_required": evidence,
            "reason_required": reason,
            "timestamp_required": ts,
            "approval_reference_required": ref,
            "future_audit_status": future_status,
            "governance_note": "No completed audit event created",
        })

    return pd.DataFrame(records)
