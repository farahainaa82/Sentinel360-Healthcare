"""
Decision Scorecard Interpretation Engine for Phase 2D-3.

Creates one short management interpretation per scorecard using permitted wording only.
"""

import logging
import pandas as pd
from typing import Dict, Any, List

LOG = logging.getLogger("decision_scorecard_interpretation_engine")


def _safe(val):
    if pd.isna(val):
        return "Not available"
    return str(val)


def build_interpretation(dim_df: pd.DataFrame, logger: logging.Logger = None) -> pd.DataFrame:
    logger = logger or LOG
    logger.info("Building management interpretations")

    rows: List[Dict[str, Any]] = []
    for _, rec in dim_df.iterrows():
        pkg_id = rec["decision_package_id"]

        current_risk = _safe(rec.get("risk_tier", "Not Assessable"))
        analytical_readiness = _safe(rec.get("decision_readiness", "Not Assessable"))
        rec_condition = _safe(rec.get("recommendation_readiness", "Not available"))
        scen_condition = _safe(rec.get("scenario_readiness", "Not available"))
        fin_condition = _safe(rec.get("financial_readiness", "Not available"))
        gov_warning = _safe(rec.get("governance_burden_status", "Low"))
        next_action = _safe(rec.get("permitted_management_actions", "Review Integrated Decision Package"))

        interpretation = (
            f"1. Current risk: The operational risk tier is {current_risk}. "
            f"2. Analytical readiness: {analytical_readiness}. "
            f"3. Main recommendation condition: {rec_condition}. "
            f"4. Main scenario condition: {scen_condition}. "
            f"5. Main financial condition: {fin_condition}. "
            f"6. Main governance warning: Governance burden is {gov_warning}. "
            f"7. Permitted next management action: {next_action}."
        )

        rows.append({
            "interpretation_id": f"{pkg_id}-INT",
            "decision_package_id": pkg_id,
            "approval_package_id": rec["approval_package_id"],
            "management_interpretation": interpretation,
            "interpretation_version": "1.0",
            "wording_compliance": "Permitted wording only. No 'best', 'optimal', 'guaranteed', or 'approved' language.",
        })

    df = pd.DataFrame(rows)
    logger.info(f"Interpretations built: {len(df)} records")
    return df
