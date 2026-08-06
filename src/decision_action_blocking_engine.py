"""
decision_action_blocking_engine.py
Phase 2D-5 — Action blocking records.
"""

import pandas as pd
from typing import List, Dict
import uuid


def load_blocking_config(config_path: str = "config/decision_action_blocking_config.csv") -> pd.DataFrame:
    return pd.read_csv(config_path)


def build_blocking_records(
    routing_id: str,
    package_id: str,
    action_id: str,
    action_name: str,
    eligibility_status: str,
    blocking_gate: str,
    readiness_status: str,
    blocking_config: pd.DataFrame,
    gate_register: pd.DataFrame
) -> List[Dict]:
    """Create explicit blocking records for blocked actions."""
    records = []

    if eligibility_status not in ("Blocked", "Not Permitted"):
        return records

    if blocking_gate and blocking_gate != "None" and blocking_gate != "":
        # Match against blocking config by gate name
        match = blocking_config[blocking_config["source_gate"] == blocking_gate]
        if not match.empty:
            bc = match.iloc[0]
            records.append({
                "action_block_id": f"BLK-{uuid.uuid4().hex[:8].upper()}",
                "decision_action_routing_id": routing_id,
                "action_id": action_id,
                "action_name": action_name,
                "blocking_condition_id": bc["configuration_id"],
                "blocking_reason": bc["blocking_reason"],
                "blocking_severity": bc["blocking_severity"],
                "source_phase": bc["source_phase"],
                "source_record_id": "",
                "resolution_required": True,
                "responsible_role": "",
                "current_status": "Active",
            })
        else:
            records.append({
                "action_block_id": f"BLK-{uuid.uuid4().hex[:8].upper()}",
                "decision_action_routing_id": routing_id,
                "action_id": action_id,
                "action_name": action_name,
                "blocking_condition_id": "UNKNOWN",
                "blocking_reason": f"Blocked due to {blocking_gate}",
                "blocking_severity": "Critical",
                "source_phase": "2D-4",
                "source_record_id": "",
                "resolution_required": True,
                "responsible_role": "",
                "current_status": "Active",
            })
    else:
        # General blocking by readiness status
        records.append({
            "action_block_id": f"BLK-{uuid.uuid4().hex[:8].upper()}",
            "decision_action_routing_id": routing_id,
            "action_id": action_id,
            "action_name": action_name,
            "blocking_condition_id": f"BLK-{readiness_status.upper().replace(' ', '-')}",
            "blocking_reason": f"Action not permitted for readiness status: {readiness_status}",
            "blocking_severity": "Critical",
            "source_phase": "2D-4",
            "source_record_id": "",
            "resolution_required": True,
            "responsible_role": "",
            "current_status": "Active",
        })

    return records
