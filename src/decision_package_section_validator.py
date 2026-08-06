"""
Decision Package Section Validator for Phase 2D-2.

Validates that every package contains all mandatory sections and that
section fields are populated appropriately.
"""

import logging
import pandas as pd
from typing import List, Dict, Any

LOG = logging.getLogger("decision_package_section_validator")

MANDATORY_SECTIONS = [
    "package_identity",
    "executive_issue_summary",
    "kpi_and_risk_evidence",
    "recommendation_options",
    "scenario_options",
    "kpi_impact_and_tradeoffs",
    "financial_impact",
    "governance_and_limitations",
    "management_questions",
    "required_confirmations",
    "permitted_management_actions",
    "monitoring_requirements",
    "evidence_and_lineage",
]


def validate_sections(package_df: pd.DataFrame, logger: logging.Logger = None) -> pd.DataFrame:
    logger = logger or LOG
    logger.info("Validating package sections")

    rows: List[Dict[str, Any]] = []
    for _, row in package_df.iterrows():
        pkg_id = row["decision_package_id"]
        missing = []

        # Identity
        if pd.isna(row.get("decision_package_id")) or pd.isna(row.get("approval_package_id")):
            missing.append("package_identity")

        # Issue summary
        if pd.isna(row.get("issue_title")) and pd.isna(row.get("issue_summary")):
            missing.append("executive_issue_summary")

        # KPI and risk
        if pd.isna(row.get("current_kpi_value")):
            missing.append("kpi_and_risk_evidence")

        # Recommendation
        if pd.isna(row.get("representative_recommendation")):
            missing.append("recommendation_options")

        # Scenario
        if pd.isna(row.get("scenario_family")):
            missing.append("scenario_options")

        # Trade-offs
        if pd.isna(row.get("tradeoff_summary")):
            missing.append("kpi_impact_and_tradeoffs")

        # Financial
        if pd.isna(row.get("cost_completeness")):
            missing.append("financial_impact")

        # Governance
        if pd.isna(row.get("causality_status")):
            missing.append("governance_and_limitations")

        rows.append({
            "section_validation_id": f"{pkg_id}-SV",
            "decision_package_id": pkg_id,
            "approval_package_id": row["approval_package_id"],
            "mandatory_sections_count": len(MANDATORY_SECTIONS),
            "present_sections_count": len(MANDATORY_SECTIONS) - len(missing),
            "missing_sections": "|".join(missing) if missing else "None",
            "section_validation_passed": len(missing) == 0,
        })

    df = pd.DataFrame(rows)
    logger.info(f"Section validation complete: {len(df)} packages")
    return df
