"""
decision_action_queue_engine.py
Phase 2D-5 — Queue assignment model.
"""

import pandas as pd
import uuid
from typing import List, Dict


def load_queue_config(config_path: str = "config/decision_action_queue_config.csv") -> pd.DataFrame:
    return pd.read_csv(config_path)


def build_queue_records(
    routing_df: pd.DataFrame,
    queue_config: pd.DataFrame,
    blocking_df: pd.DataFrame,
    prerequisite_df: pd.DataFrame
) -> pd.DataFrame:
    """Build queue assignment records."""
    records = []
    for _, row in routing_df.iterrows():
        routing_id = row["decision_action_routing_id"]
        status = row["final_readiness_status"]
        package_id = row["decision_package_id"]

        match = queue_config[queue_config["readiness_status"] == status]
        if not match.empty:
            qc = match.iloc[0]
            primary_queue = qc["primary_queue"]
            secondary_queue = qc["secondary_queue"] if pd.notna(qc["secondary_queue"]) else ""
            priority = qc["queue_priority"]
        else:
            primary_queue = "General Queue"
            secondary_queue = ""
            priority = "Standard"

        # Count blocking conditions and prerequisites
        bc_count = len(blocking_df[blocking_df["decision_action_routing_id"] == routing_id])
        pr_count = len(prerequisite_df[prerequisite_df["decision_action_routing_id"] == routing_id])

        records.append({
            "queue_assignment_id": f"QUE-{uuid.uuid4().hex[:8].upper()}",
            "decision_action_routing_id": routing_id,
            "decision_package_id": package_id,
            "primary_queue": primary_queue,
            "secondary_queue": secondary_queue,
            "queue_reason": f"Routed based on readiness status: {status}",
            "queue_priority": priority,
            "responsible_role": "",
            "escalation_status": "Pending Routing",
            "blocking_condition_count": bc_count,
            "pending_prerequisite_count": pr_count,
            "current_status": "Pending Routing",
            "governance_note": "Prototype default - Pending Routing",
        })

    return pd.DataFrame(records)
