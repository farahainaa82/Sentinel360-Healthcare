"""
Decision Scorecard Display Level Engine for Phase 2D-3.

Maps each dimension to a transparent display level for executive consumption.
"""

import logging
import pandas as pd
from typing import Dict, Any, List

LOG = logging.getLogger("decision_scorecard_display_level_engine")

DISPLAY_LEVELS = ["Strong", "Adequate", "Conditional", "Limited", "Blocking", "Not Applicable", "Not Assessable"]


def _map_risk_to_display(risk_tier: str) -> str:
    mapping = {
        "Critical": "Blocking",
        "High": "Limited",
        "Elevated": "Conditional",
        "Moderate": "Adequate",
        "Low": "Strong",
        "Monitoring": "Limited",
        "Not Assessable": "Not Assessable",
    }
    return mapping.get(risk_tier, "Not Assessable")


def _map_evidence_to_display(ev_status: str) -> str:
    mapping = {
        "Complete": "Strong",
        "Complete with Conditions": "Adequate",
        "Partial": "Conditional",
        "Limited": "Limited",
        "Not Available": "Not Assessable",
    }
    return mapping.get(ev_status, "Not Assessable")


def _map_readiness_to_display(ready: str) -> str:
    mapping = {
        "Ready with Conditions": "Conditional",
        "Monitoring Only": "Limited",
        "Requires Assumption Validation": "Blocking",
        "Non-Quantitative": "Not Assessable",
        "Ready for Integrated Management Review": "Strong",
        "Requires Baseline Validation": "Blocking",
        "Requires Financial Input": "Blocking",
        "Requires Stakeholder Validation": "Blocking",
        "Requires Additional Scenario Analysis": "Blocking",
        "Not Suitable for Decision Use": "Not Applicable",
        "Rejected": "Not Applicable",
    }
    return mapping.get(ready, "Not Assessable")


def build_display_levels(dim_df: pd.DataFrame, logger: logging.Logger = None) -> pd.DataFrame:
    logger = logger or LOG
    logger.info("Building display levels")

    rows: List[Dict[str, Any]] = []
    for _, rec in dim_df.iterrows():
        pkg_id = rec["decision_package_id"]
        rows.append({
            "display_level_record_id": f"{pkg_id}-DL",
            "decision_package_id": pkg_id,
            "approval_package_id": rec["approval_package_id"],
            "operational_risk_display": _map_risk_to_display(rec["risk_tier"]),
            "evidence_strength_display": _map_evidence_to_display(rec["evidence_status"]),
            "lineage_strength_display": _map_evidence_to_display(rec["lineage_status"]),
            "recommendation_readiness_display": _map_readiness_to_display(rec["recommendation_readiness"]),
            "scenario_readiness_display": _map_readiness_to_display(rec["scenario_readiness"]),
            "financial_readiness_display": _map_readiness_to_display(rec["financial_readiness"]),
            "uncertainty_display": _map_evidence_to_display(rec["uncertainty_status"]),
            "governance_burden_display": _map_risk_to_display(rec["governance_burden_status"]),
            "management_readiness_display": _map_readiness_to_display(rec["package_readiness"]),
            "overall_display_level": rec.get("display_level", "Not Assessable"),
            "display_level_formula": "Transparent mapping from governed status to display band. Not a hidden score.",
        })

    df = pd.DataFrame(rows)
    logger.info(f"Display levels built: {len(df)} records")
    return df
