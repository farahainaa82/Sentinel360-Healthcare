"""
Decision Package Readiness Engine for Phase 2D-2.

Maps Step 2D-1 decision statuses to package readiness categories.
"""

import logging
import pandas as pd

LOG = logging.getLogger("decision_package_readiness_engine")

STATUS_TO_READINESS = {
    "Ready with Conditions": "Package Ready with Conditions",
    "Monitoring Only": "Package Monitoring Only",
    "Requires Assumption Validation": "Package Requires Assumption Validation",
    "Non-Quantitative": "Package Non-Quantitative",
    "Ready for Integrated Management Review": "Package Ready for Integrated Management Review",
    "Requires Baseline Validation": "Package Requires Baseline Validation",
    "Requires Financial Input": "Package Requires Financial Input",
    "Requires Stakeholder Validation": "Package Requires Stakeholder Validation",
    "Requires Additional Scenario Analysis": "Package Requires Additional Scenario Analysis",
    "Not Suitable for Decision Use": "Package Not Suitable",
    "Rejected": "Package Rejected",
}


def build_package_readiness(integrated_df: pd.DataFrame, logger: logging.Logger = None) -> pd.DataFrame:
    logger = logger or LOG
    logger.info("Building package readiness")

    df = integrated_df[["integrated_decision_id", "approval_package_id", "decision_status"]].copy()
    df["package_readiness"] = df["decision_status"].map(STATUS_TO_READINESS).fillna("Package Not Suitable")
    df["readiness_source"] = "Step 2D-1 integrated decision status"
    df["readiness_reconciliation_flag"] = True

    logger.info(f"Package readiness built: {len(df)} records")
    return df
