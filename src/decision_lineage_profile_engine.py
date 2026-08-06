"""
decision_lineage_profile_engine.py
Phase 2D-6 — Lineage profile creation per package.
"""

import pandas as pd
import uuid


def build_lineage_profiles(routing_df: pd.DataFrame) -> pd.DataFrame:
    records = []
    for _, row in routing_df.iterrows():
        records.append({
            "decision_lineage_profile_id": f"LNP-{uuid.uuid4().hex[:8].upper()}",
            "decision_action_routing_id": row["decision_action_routing_id"],
            "decision_readiness_id": row.get("decision_readiness_id", ""),
            "decision_package_id": row["decision_package_id"],
            "integrated_decision_id": row.get("integrated_decision_id", ""),
            "episode_id": row.get("episode_id", ""),
            "hospital_id": row.get("hospital_id", ""),
            "department_id": row.get("department_id", ""),
            "final_readiness_status": row["final_readiness_status"],
            "governance_note": "Lineage profile traces source-to-decision path",
        })
    return pd.DataFrame(records)
