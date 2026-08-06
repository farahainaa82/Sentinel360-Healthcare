"""
decision_evidence_profile_engine.py
Phase 2D-6 — Evidence profile creation per routing package.
"""

import pandas as pd
import uuid


def build_evidence_profiles(routing_df: pd.DataFrame) -> pd.DataFrame:
    records = []
    for _, row in routing_df.iterrows():
        records.append({
            "decision_evidence_profile_id": f"EVP-{uuid.uuid4().hex[:8].upper()}",
            "decision_action_routing_id": row["decision_action_routing_id"],
            "decision_readiness_id": row.get("decision_readiness_id", ""),
            "decision_scorecard_id": row.get("decision_scorecard_id", ""),
            "decision_package_id": row["decision_package_id"],
            "integrated_decision_id": row.get("integrated_decision_id", ""),
            "approval_package_id": row.get("approval_package_id", ""),
            "episode_id": row.get("episode_id", ""),
            "hospital_id": row.get("hospital_id", ""),
            "department_id": row.get("department_id", ""),
            "final_readiness_status": row["final_readiness_status"],
            "primary_action_id": "",
            "primary_queue": row.get("primary_queue", ""),
            "approval_status": "Pending Management Review",
            "causality_status": "Not Confirmed",
            "governance_note": "Evidence profile for audit traceability",
        })
    return pd.DataFrame(records)
