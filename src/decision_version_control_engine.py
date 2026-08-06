"""
decision_version_control_engine.py
Phase 2D-6 — Version control records per governed object.
"""

import pandas as pd
import uuid


def build_version_control_records(
    routing_df: pd.DataFrame,
    evidence_profiles: pd.DataFrame,
    lineage_profiles: pd.DataFrame
) -> pd.DataFrame:
    records = []

    object_lists = [
        ("Decision Package", routing_df, "decision_package_id"),
        ("Decision Scorecard", routing_df, "decision_scorecard_id"),
        ("Decision Readiness", routing_df, "decision_readiness_id"),
        ("Action Routing", routing_df, "decision_action_routing_id"),
        ("Evidence Profile", evidence_profiles, "decision_evidence_profile_id"),
        ("Lineage Profile", lineage_profiles, "decision_lineage_profile_id"),
    ]

    for obj_type, df, id_col in object_lists:
        for _, row in df.iterrows():
            obj_id = row.get(id_col, "")
            if not obj_id:
                continue
            records.append({
                "version_control_id": f"VER-{uuid.uuid4().hex[:8].upper()}",
                "governed_object_type": obj_type,
                "governed_object_id": obj_id,
                "current_version": "1.0",
                "previous_version": "",
                "version_status": "Current",
                "effective_timestamp": "",
                "created_by_role": "Analytics Team",
                "source_manifest": "step_2d6_manifest.json",
                "checksum": "",
                "immutable_flag": True,
                "superseded_flag": False,
                "correction_reason": "",
                "future_update_rule": "Minor increment on change",
                "governance_note": "Version control for audit traceability",
            })

    return pd.DataFrame(records)
