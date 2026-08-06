"""
decision_action_prerequisite_engine.py
Phase 2D-5 — Prerequisite model for actions.
"""

import pandas as pd
from typing import List, Dict
import uuid


def load_prerequisite_config(config_path: str = "config/decision_action_prerequisite_config.csv") -> pd.DataFrame:
    return pd.read_csv(config_path)


def build_prerequisites(
    routing_id: str,
    package_id: str,
    action_id: str,
    action_name: str,
    prerequisite_config: pd.DataFrame
) -> List[Dict]:
    """Build prerequisite records for a single action."""
    config = prerequisite_config[prerequisite_config["action_id"] == action_id]
    records = []
    for _, row in config.iterrows():
        records.append({
            "action_prerequisite_id": f"PRQ-{uuid.uuid4().hex[:8].upper()}",
            "decision_action_routing_id": routing_id,
            "action_id": action_id,
            "action_name": action_name,
            "prerequisite_type": row["prerequisite_type"],
            "prerequisite_description": row["prerequisite_description"],
            "source_gate": "",
            "source_condition_id": "",
            "mandatory_flag": row["mandatory_flag"],
            "blocking_flag": row["blocking_flag"],
            "responsible_role": row["responsible_role"],
            "evidence_required": row["evidence_required"],
            "current_status": "Pending",
            "completion_required_before_action": row["completion_required_before_action"],
        })
    return records
