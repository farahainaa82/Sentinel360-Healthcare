"""
decision_retention_classification_engine.py
Phase 2D-6 — Record retention classifications.
"""

import pandas as pd
import uuid


def build_retention_records(
    evidence_profiles: pd.DataFrame,
    lineage_profiles: pd.DataFrame,
    audit_contracts: pd.DataFrame,
    history_contracts: pd.DataFrame
) -> pd.DataFrame:
    records = []

    for _, row in evidence_profiles.iterrows():
        records.append({
            "retention_record_id": f"RET-{uuid.uuid4().hex[:8].upper()}",
            "object_type": "Evidence Profile",
            "object_id": row["decision_evidence_profile_id"],
            "record_class": "Decision Evidence",
            "retention_status": "Active",
            "retention_period_rule": "Retention Period Requires Organisational Policy",
            "archival_required": True,
            "deletion_permitted": False,
            "legal_hold_flag": False,
            "sensitive_data_flag": False,
            "access_classification": "Restricted",
            "governance_note": "Retention classification for evidence profile",
        })

    for _, row in lineage_profiles.iterrows():
        records.append({
            "retention_record_id": f"RET-{uuid.uuid4().hex[:8].upper()}",
            "object_type": "Lineage Profile",
            "object_id": row["decision_lineage_profile_id"],
            "record_class": "Governance Record",
            "retention_status": "Active",
            "retention_period_rule": "Retention Period Requires Organisational Policy",
            "archival_required": True,
            "deletion_permitted": False,
            "legal_hold_flag": True,
            "sensitive_data_flag": False,
            "access_classification": "Restricted",
            "governance_note": "Retention classification for lineage profile",
        })

    for _, row in audit_contracts.iterrows():
        records.append({
            "retention_record_id": f"RET-{uuid.uuid4().hex[:8].upper()}",
            "object_type": "Audit Event Contract",
            "object_id": row["audit_event_contract_id"],
            "record_class": "Audit Event Contract",
            "retention_status": "Active",
            "retention_period_rule": "Retention Period Requires Organisational Policy",
            "archival_required": True,
            "deletion_permitted": False,
            "legal_hold_flag": True,
            "sensitive_data_flag": False,
            "access_classification": "Restricted",
            "governance_note": "Retention classification for audit contract",
        })

    for _, row in history_contracts.iterrows():
        records.append({
            "retention_record_id": f"RET-{uuid.uuid4().hex[:8].upper()}",
            "object_type": "Decision History",
            "object_id": row["decision_history_id"],
            "record_class": "Decision History",
            "retention_status": "Active",
            "retention_period_rule": "Retention Period Requires Organisational Policy",
            "archival_required": True,
            "deletion_permitted": False,
            "legal_hold_flag": False,
            "sensitive_data_flag": False,
            "access_classification": "Restricted",
            "governance_note": "Retention classification for decision history",
        })

    return pd.DataFrame(records)
