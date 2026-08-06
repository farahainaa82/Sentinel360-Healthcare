"""
Decision Package Narrative Engine for Phase 2D-2.

Creates a concise management narrative per package for executive consumption.
"""

import logging
import pandas as pd
from typing import Dict, Any, List

LOG = logging.getLogger("decision_package_narrative_engine")


def _safe(val):
    if pd.isna(val):
        return "Not available"
    return str(val)


def build_narrative(integrated_df: pd.DataFrame, logger: logging.Logger = None) -> pd.DataFrame:
    logger = logger or LOG
    logger.info("Building package narratives")

    rows: List[Dict[str, Any]] = []
    for _, rec in integrated_df.iterrows():
        pkg_id = f"DPKG-{rec['approval_package_id']}"

        issue = _safe(rec.get("issue_title", rec.get("issue_description", "Operational issue")))
        significance = _safe(rec.get("management_attention_reason", "Requires management attention due to KPI indicators."))
        evidence = _safe(rec.get("kpi_evidence_summary", rec.get("operational_evidence_summary", "KPI and trend evidence reviewed.")))
        rec_text = _safe(rec.get("representative_recommendation", "Recommendation options under review."))
        scenarios = _safe(rec.get("scenario_family", "Scenario analysis pending."))
        tradeoffs = _safe(rec.get("scenario_tradeoff_summary", "Trade-offs not yet quantified."))
        financial = _safe(rec.get("estimated_net_financial_impact", "Financial impact not yet determined."))
        uncertainty = _safe(rec.get("scenario_uncertainty_summary", "Uncertainty remains under assessment."))
        confirmation = _safe(rec.get("required_confirmations_summary", "Management confirmation required before proceeding."))
        action = _safe(rec.get("permitted_management_actions", "Review Integrated Decision Package"))

        narrative = (
            f"1. Issue: {issue}\n"
            f"2. Operational significance: {significance}\n"
            f"3. Evidence: {evidence}\n"
            f"4. Recommendation options: {rec_text}\n"
            f"5. Scenario options: {scenarios}\n"
            f"6. Main trade-offs: {tradeoffs}\n"
            f"7. Estimated financial implications: {financial}\n"
            f"8. Key uncertainty: {uncertainty}\n"
            f"9. Required management confirmation: {confirmation}\n"
            f"10. Permitted next action: {action}"
        )

        rows.append({
            "narrative_id": f"{pkg_id}-NAR",
            "decision_package_id": pkg_id,
            "approval_package_id": rec["approval_package_id"],
            "management_narrative": narrative,
            "narrative_version": "1.0",
            "narrative_status": "Active",
        })

    df = pd.DataFrame(rows)
    logger.info(f"Narratives built: {len(df)} total")
    return df
