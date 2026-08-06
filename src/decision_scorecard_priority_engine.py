"""
Decision Scorecard Priority Engine for Phase 2D-3.

Creates a priority-view register ordered by risk, urgency, and governance.
Primary ordering uses operational risk; secondary uses readiness and burden.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List

LOG = logging.getLogger("decision_scorecard_priority_engine")

RISK_ORDER = {"Critical": 1, "High": 2, "Elevated": 3, "Moderate": 4, "Low": 5, "Monitoring": 6, "Not Assessable": 7}
URGENCY_ORDER = {"Immediate Review": 1, "Prompt Review": 2, "Routine Review": 3, "": 4, "Unknown": 4}


def build_priority_view(dim_df: pd.DataFrame, logger: logging.Logger = None) -> pd.DataFrame:
    logger = logger or LOG
    logger.info("Building scorecard priority view")

    rows: List[Dict[str, Any]] = []
    for _, rec in dim_df.iterrows():
        pkg_id = rec["decision_package_id"]
        risk_tier = rec.get("risk_tier", "Not Assessable")
        urgency = rec.get("urgency", "")
        if pd.isna(urgency):
            urgency = ""
        if pd.isna(risk_tier):
            risk_tier = "Not Assessable"

        rows.append({
            "priority_view_id": f"{pkg_id}-PV",
            "decision_package_id": pkg_id,
            "approval_package_id": rec["approval_package_id"],
            "risk_tier": risk_tier,
            "urgency": urgency,
            "breach_status": rec.get("breach_status", ""),
            "sustained_movement_flag": rec.get("sustained_movement_flag", False),
            "management_attention_required": rec.get("management_review_required", False),
            "decision_readiness": rec.get("decision_readiness", ""),
            "governance_burden_status": rec.get("governance_burden_status", "Low"),
            "evidence_status": rec.get("evidence_status", "Not Available"),
            "financial_readiness": rec.get("financial_readiness", ""),
            "package_readiness": rec.get("package_readiness", ""),
            "primary_sort_key": RISK_ORDER.get(risk_tier, 99),
            "secondary_sort_key": URGENCY_ORDER.get(urgency, 99),
            "priority_ordering_note": "Primary: risk tier. Secondary: urgency. Tertiary: governance burden. Financial value is not primary.",
        })

    df = pd.DataFrame(rows)
    df = df.sort_values(["primary_sort_key", "secondary_sort_key", "governance_burden_status"])
    logger.info(f"Priority view built: {len(df)} records")
    return df
