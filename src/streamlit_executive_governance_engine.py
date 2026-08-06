"""
streamlit_executive_governance_engine.py
Evidence, lineage, and governance engine.
"""

from typing import Dict, List
import pandas as pd

from .streamlit_executive_logging import log_event


def build_governance_summary(audit_df: pd.DataFrame) -> List[Dict]:
    if audit_df.empty:
        return []
    total = len(audit_df)
    cards: List[Dict] = []
    # Evidence Complete
    if "evidence_completeness" in audit_df.columns:
        evidence_complete = (
            pd.to_numeric(audit_df["evidence_completeness"], errors="coerce").fillna(0)
            >= 1.0
        ).sum()
        cards.append(
            {
                "label": "Evidence Complete",
                "count": int(evidence_complete),
                "total": total,
            }
        )
    # Lineage Complete
    if "lineage_completeness" in audit_df.columns:
        lineage_complete = (
            pd.to_numeric(audit_df["lineage_completeness"], errors="coerce").fillna(0)
            >= 1.0
        ).sum()
        cards.append(
            {
                "label": "Lineage Complete",
                "count": int(lineage_complete),
                "total": total,
            }
        )
    # Integrity Verified
    if "integrity_status" in audit_df.columns:
        integrity = (
            audit_df["integrity_status"].astype(str).str.contains("Verified", case=False, na=False)
        ).sum()
        cards.append(
            {
                "label": "Integrity Verified",
                "count": int(integrity),
                "total": total,
            }
        )
    log_event("GOVERNANCE_SUMMARY_BUILT", f"cards={len(cards)}")
    return cards


def get_governance_constants() -> Dict[str, str]:
    return {
        "causality_status": "Not Confirmed",
        "approval_status": "Pending Management Review",
        "future_audit_status": "Awaiting Management Action",
    }
