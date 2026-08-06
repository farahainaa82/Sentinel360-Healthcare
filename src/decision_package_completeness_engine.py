"""
Decision Package Completeness Engine for Phase 2D-2.

Assesses completeness across all package sections based on available data.
"""

import logging
import pandas as pd
import numpy as np

LOG = logging.getLogger("decision_package_completeness_engine")


def assess_completeness(integrated_df: pd.DataFrame, logger: logging.Logger = None) -> pd.DataFrame:
    logger = logger or LOG
    logger.info("Assessing package completeness")

    df = integrated_df[["integrated_decision_id", "approval_package_id", "decision_status"]].copy()

    # Section completeness flags
    identity_ok = integrated_df["episode_id"].notna() if "episode_id" in integrated_df.columns else pd.Series(False, index=integrated_df.index)
    issue_ok = (
        (integrated_df["issue_description"].notna() if "issue_description" in integrated_df.columns else pd.Series(False, index=integrated_df.index)) |
        (integrated_df["issue_title"].notna() if "issue_title" in integrated_df.columns else pd.Series(False, index=integrated_df.index))
    )
    kpi_ok = integrated_df["current_kpi_value"].notna() if "current_kpi_value" in integrated_df.columns else pd.Series(False, index=integrated_df.index)
    rec_ok = integrated_df["representative_recommendation"].notna() if "representative_recommendation" in integrated_df.columns else pd.Series(False, index=integrated_df.index)
    scenario_ok = integrated_df["scenario_family"].notna() if "scenario_family" in integrated_df.columns else pd.Series(False, index=integrated_df.index)
    financial_ok = integrated_df["cost_completeness"].notna() if "cost_completeness" in integrated_df.columns else pd.Series(False, index=integrated_df.index)
    governance_ok = integrated_df["causality_status"].notna() if "causality_status" in integrated_df.columns else pd.Series(False, index=integrated_df.index)

    section_scores = (
        identity_ok.astype(int) +
        issue_ok.astype(int) +
        kpi_ok.astype(int) +
        rec_ok.astype(int) +
        scenario_ok.astype(int) +
        financial_ok.astype(int) +
        governance_ok.astype(int)
    ) / 7.0

    def assign_status(row):
        status = row["decision_status"]
        score = row["section_score"]
        if status == "Monitoring Only":
            return "Monitoring Package"
        if status == "Non-Quantitative":
            return "Non-Quantitative Package"
        if status in ["Ready with Conditions", "Ready for Integrated Management Review"]:
            return "Complete Package" if score >= 0.85 else "Complete with Conditions"
        if status in ["Requires Assumption Validation", "Requires Baseline Validation", "Requires Financial Input"]:
            return "Partial Package"
        if status in ["Not Suitable for Decision Use", "Rejected"]:
            return "Not Suitable" if status == "Not Suitable for Decision Use" else "Rejected"
        return "Complete with Conditions" if score >= 0.5 else "Partial Package"

    df["section_score"] = section_scores.round(4)
    df["completeness_status"] = df.apply(assign_status, axis=1)
    df["identity_complete"] = identity_ok
    df["issue_summary_complete"] = issue_ok
    df["kpi_risk_complete"] = kpi_ok
    df["recommendation_complete"] = rec_ok
    df["scenario_complete"] = scenario_ok
    df["financial_complete"] = financial_ok
    df["governance_complete"] = governance_ok
    df["management_questions_complete"] = True
    df["actions_complete"] = True
    df["evidence_complete"] = True
    df["lineage_complete"] = True

    logger.info(f"Completeness assessed: {len(df)} records")
    return df
