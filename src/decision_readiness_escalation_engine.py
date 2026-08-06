"""
Decision Readiness Escalation Engine for Phase 2D-4.

Creates escalation rules using existing risk and urgency.
Separates operational escalation from analytical readiness.
"""

import logging
import pandas as pd
from typing import Dict, Any, List

LOG = logging.getLogger("decision_readiness_escalation_engine")


def build_escalation(
    readiness_df: pd.DataFrame,
    dimension_df: pd.DataFrame,
    logger: logging.Logger = None,
) -> pd.DataFrame:
    logger = logger or LOG
    logger.info("Building escalation assignments")

    merged = readiness_df.merge(
        dimension_df[["decision_package_id", "risk_tier", "urgency"]],
        on="decision_package_id",
        how="left",
    )

    rows: List[Dict[str, Any]] = []
    for _, rec in merged.iterrows():
        risk_tier = str(rec.get("risk_tier", "Not Assessable"))
        urgency = str(rec.get("urgency", ""))
        readiness_status = rec["final_readiness_status"]

        # Determine escalation status
        if risk_tier == "High":
            escalation_status = "Immediate Management Attention"
            attention_required = True
        elif risk_tier == "Moderate" and urgency == "High":
            escalation_status = "Priority Review"
            attention_required = True
        elif risk_tier == "Moderate":
            escalation_status = "Standard Review"
            attention_required = False
        elif readiness_status == "Monitoring Only":
            escalation_status = "Monitoring"
            attention_required = False
        elif risk_tier == "Not Assessable":
            escalation_status = "Not Assessable"
            attention_required = False
        else:
            escalation_status = "Standard Review"
            attention_required = False

        rows.append({
            "escalation_id": f"ESC-{rec['decision_readiness_id']}",
            "decision_readiness_id": rec["decision_readiness_id"],
            "decision_scorecard_id": rec["decision_scorecard_id"],
            "decision_package_id": rec["decision_package_id"],
            "operational_escalation_status": escalation_status,
            "readiness_status": readiness_status,
            "risk_tier": risk_tier,
            "urgency": urgency,
            "management_attention_required": attention_required,
            "escalation_basis": "Derived from risk tier and urgency; separate from analytical readiness",
            "governance_note": "Operational escalation remains independent of readiness classification",
        })

    result = pd.DataFrame(rows)
    logger.info("Escalation assignments built: %s records", len(result))
    return result
