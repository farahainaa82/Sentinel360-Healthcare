"""
decision_history_contract_engine.py
Phase 2D-6 — Decision history contracts per package.
"""

import pandas as pd
import uuid


def build_history_contracts(routing_df: pd.DataFrame) -> pd.DataFrame:
    records = []
    for _, row in routing_df.iterrows():
        records.append({
            "decision_history_id": f"HST-{uuid.uuid4().hex[:8].upper()}",
            "decision_package_id": row["decision_package_id"],
            "current_package_version": "1.0",
            "current_readiness_status": row["final_readiness_status"],
            "current_primary_action": "",
            "current_queue": row.get("primary_queue", ""),
            "current_approval_status": "Pending Management Review",
            "prior_version": "",
            "prior_readiness_status": "",
            "prior_primary_action": "",
            "prior_queue": "",
            "prior_approval_status": "",
            "change_reason": "",
            "changed_by": "",
            "changed_timestamp": "",
            "change_event_id": "",
            "history_status": "Initial Governed State",
            "governance_note": "No historical decisions invented",
        })
    return pd.DataFrame(records)
