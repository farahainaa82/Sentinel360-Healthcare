"""
Decision Readiness Role Engine for Phase 2D-4.

Assigns responsible roles based on blocking conditions.
Uses only governed role names.
"""

import logging
import pandas as pd
from typing import Dict, Any, List

LOG = logging.getLogger("decision_readiness_role_engine")

ROLE_ASSIGNMENTS = {
    "Requires Assumption Validation": "Analytics Team",
    "Requires Baseline Validation": "Data Owner",
    "Requires Financial Input": "Finance",
    "Requires Benefit Validation": "Finance",
    "Requires Budget Data": "Finance",
    "Requires Stakeholder Validation": "Stakeholder Owner",
    "Requires Additional Scenario Analysis": "Analytics Team",
    "Requires Evidence Completion": "Data Owner",
    "Requires Lineage Completion": "Data Owner",
    "Ready with Conditions": "Department Head",
    "Ready for Integrated Management Review": "Hospital COO / General Manager",
    "Monitoring Only": "Operations Manager",
    "Non-Quantitative": "Clinical Lead",
    "Not Suitable for Decision Use": "Medical Director",
    "Rejected": "Hospital COO / General Manager",
}


def build_roles(
    readiness_df: pd.DataFrame,
    logger: logging.Logger = None,
) -> pd.DataFrame:
    logger = logger or LOG
    logger.info("Building responsible role assignments")

    rows: List[Dict[str, Any]] = []
    for _, rec in readiness_df.iterrows():
        status = rec["final_readiness_status"]
        role = ROLE_ASSIGNMENTS.get(status, "Operations Manager")

        rows.append({
            "role_assignment_id": f"RA-{rec['decision_readiness_id']}",
            "decision_readiness_id": rec["decision_readiness_id"],
            "decision_scorecard_id": rec["decision_scorecard_id"],
            "decision_package_id": rec["decision_package_id"],
            "final_readiness_status": status,
            "responsible_role": role,
            "role_scope": "Primary",
            "escalation_role": "Hospital COO / General Manager",
            "assignment_basis": f"Derived from readiness status: {status}",
            "governance_note": "Governed role assignment only; no named individual",
        })

    result = pd.DataFrame(rows)
    logger.info("Role assignments built: %s records", len(result))
    return result
