"""
Decision Scorecard Management Readiness Engine for Phase 2D-3.

Reconciles management readiness from 2D-1/2D-2 and produces a governed
management-readiness record per scorecard.
"""

import logging
import pandas as pd
from typing import Dict, Any, List

LOG = logging.getLogger("decision_scorecard_management_readiness_engine")


def build_management_readiness(dim_df: pd.DataFrame, logger: logging.Logger = None) -> pd.DataFrame:
    logger = logger or LOG
    logger.info("Building management readiness records")

    rows: List[Dict[str, Any]] = []
    for _, rec in dim_df.iterrows():
        pkg_id = rec["decision_package_id"]
        rows.append({
            "management_readiness_record_id": f"{pkg_id}-MR",
            "decision_package_id": pkg_id,
            "approval_package_id": rec["approval_package_id"],
            "package_readiness": rec["package_readiness"],
            "package_completeness": rec["package_completeness"],
            "decision_readiness": rec["decision_readiness"],
            "permitted_management_actions": rec["permitted_management_actions"],
            "blocking_condition_count": rec["blocking_condition_count"],
            "management_review_required": rec["management_review_required"],
            "approval_status": "Pending Management Review",
            "readiness_reconciliation_note": "Reconciled from Step 2D-1 and Step 2D-2 status fields.",
        })

    df = pd.DataFrame(rows)
    logger.info(f"Management readiness built: {len(df)} records")
    return df
