"""
decision_action_evidence_lineage_engine.py
Phase 2D-5 — Evidence and lineage reconciliation.
"""

import pandas as pd
import uuid
from typing import List, Dict


def build_evidence_records(routing_df: pd.DataFrame, readiness_evidence: pd.DataFrame) -> pd.DataFrame:
    """Reconcile evidence references from readiness to action routing."""
    records = []
    for _, row in routing_df.iterrows():
        routing_id = row["decision_action_routing_id"]
        readiness_id = row.get("decision_readiness_id", "")

        ev = readiness_evidence[readiness_evidence["decision_readiness_id"] == readiness_id]
        if not ev.empty:
            for _, e in ev.iterrows():
                records.append({
                    "action_evidence_id": f"AEV-{uuid.uuid4().hex[:8].upper()}",
                    "decision_action_routing_id": routing_id,
                    "decision_readiness_id": readiness_id,
                    "evidence_type": e.get("evidence_type", "General"),
                    "evidence_description": e.get("evidence_description", ""),
                    "evidence_status": e.get("evidence_status", "Pending"),
                    "source_phase": "2D-4",
                    "reconciliation_status": "Reconciled",
                    "governance_note": "Evidence reference carried forward from readiness",
                })
        else:
            records.append({
                "action_evidence_id": f"AEV-{uuid.uuid4().hex[:8].upper()}",
                "decision_action_routing_id": routing_id,
                "decision_readiness_id": readiness_id,
                "evidence_type": "General",
                "evidence_description": "No specific evidence record found",
                "evidence_status": "Pending",
                "source_phase": "2D-4",
                "reconciliation_status": "No Source",
                "governance_note": "Evidence reference carried forward from readiness",
            })

    return pd.DataFrame(records)


def build_lineage_records(routing_df: pd.DataFrame, readiness_lineage: pd.DataFrame) -> pd.DataFrame:
    """Reconcile lineage references from readiness to action routing."""
    records = []
    for _, row in routing_df.iterrows():
        routing_id = row["decision_action_routing_id"]
        readiness_id = row.get("decision_readiness_id", "")

        ln = readiness_lineage[readiness_lineage["decision_readiness_id"] == readiness_id]
        if not ln.empty:
            for _, l in ln.iterrows():
                records.append({
                    "action_lineage_id": f"ALN-{uuid.uuid4().hex[:8].upper()}",
                    "decision_action_routing_id": routing_id,
                    "decision_readiness_id": readiness_id,
                    "lineage_type": l.get("lineage_type", "General"),
                    "lineage_description": l.get("lineage_description", ""),
                    "lineage_status": l.get("lineage_status", "Pending"),
                    "source_phase": "2D-4",
                    "reconciliation_status": "Reconciled",
                    "governance_note": "Lineage reference carried forward from readiness",
                })
        else:
            records.append({
                "action_lineage_id": f"ALN-{uuid.uuid4().hex[:8].upper()}",
                "decision_action_routing_id": routing_id,
                "decision_readiness_id": readiness_id,
                "lineage_type": "General",
                "lineage_description": "No specific lineage record found",
                "lineage_status": "Pending",
                "source_phase": "2D-4",
                "reconciliation_status": "No Source",
                "governance_note": "Lineage reference carried forward from readiness",
            })

    return pd.DataFrame(records)
