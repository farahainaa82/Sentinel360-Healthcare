"""
Decision Package Priority Engine for Phase 2D-2.

Creates a priority-ready register for executive use.
"""

import logging
import pandas as pd
from typing import Dict, Any, List

LOG = logging.getLogger("decision_package_priority_engine")


def build_priority_view(integrated_df: pd.DataFrame, logger: logging.Logger = None) -> pd.DataFrame:
    logger = logger or LOG
    logger.info("Building priority view")

    rows: List[Dict[str, Any]] = []
    for _, rec in integrated_df.iterrows():
        pkg_id = f"DPKG-{rec['approval_package_id']}"

        # Determine top management question and permitted next action
        status = rec["decision_status"]
        if status == "Ready with Conditions":
            top_q = "Are the trade-offs acceptable?"
            next_act = "Proceed to Limited-Trial Consideration"
        elif status == "Monitoring Only":
            top_q = "Should the case remain under monitoring?"
            next_act = "Continue Monitoring"
        elif status == "Requires Assumption Validation":
            top_q = "Are the recommendation assumptions acceptable?"
            next_act = "Validate Assumptions"
        elif status == "Non-Quantitative":
            top_q = "Is stakeholder review required?"
            next_act = "Request Stakeholder Review"
        else:
            top_q = "Is the current operational risk accurately represented?"
            next_act = "Review Integrated Decision Package"

        rows.append({
            "priority_view_id": f"{pkg_id}-PV",
            "decision_package_id": pkg_id,
            "approval_package_id": rec["approval_package_id"],
            "hospital": rec.get("hospital_name", "Unknown"),
            "department": rec.get("department_name", "Unknown"),
            "dominant_kpi": rec.get("dominant_kpi_name", rec.get("dominant_kpi_id", "Unknown")),
            "risk_tier": rec.get("risk_tier", "Unknown"),
            "urgency": rec.get("urgency", "Unknown"),
            "package_status": rec.get("decision_status", "Unknown"),
            "decision_readiness": rec.get("decision_readiness", "Unknown"),
            "scenario_readiness": rec.get("scenario_readiness", "Unknown"),
            "financial_readiness": rec.get("financial_readiness", "Unknown"),
            "contradiction_warning": rec.get("contradiction_warning", False),
            "provisional_warning": rec.get("provisional_warning", False),
            "top_management_question": top_q,
            "permitted_next_action": next_act,
            "monitoring_required": status in ("Monitoring Only", "Ready with Conditions", "Requires Assumption Validation"),
        })

    df = pd.DataFrame(rows)
    logger.info(f"Priority view built: {len(df)} records")
    return df
