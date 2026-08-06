"""
Decision Scorecard Data Contract Engine for Phase 2D-3.

Creates Streamlit-ready data contracts for executive, risk, recommendation,
scenario, financial, governance, and management action cards.
"""

import logging
import pandas as pd
from typing import Dict, Any, List

LOG = logging.getLogger("decision_scorecard_data_contract_engine")


def build_data_contracts(dim_df: pd.DataFrame, logger: logging.Logger = None) -> pd.DataFrame:
    logger = logger or LOG
    logger.info("Building Streamlit data contracts")

    rows: List[Dict[str, Any]] = []
    for _, rec in dim_df.iterrows():
        pkg_id = rec["decision_package_id"]
        apid = rec["approval_package_id"]

        contracts = [
            {
                "contract_name": "executive_overview_card",
                "fields": "decision_scorecard_id,hospital,department,dominant_kpi,risk_tier,urgency,decision_readiness,top_warning,top_action,reporting_date",
            },
            {
                "contract_name": "risk_card",
                "fields": "risk_score,risk_tier,threshold_status,trend_direction,sustained_movement_flag,breach_status,watch_status",
            },
            {
                "contract_name": "recommendation_card",
                "fields": "representative_recommendation,recommendation_readiness,recommendation_confirmation_required,recommendation_warning",
            },
            {
                "contract_name": "scenario_card",
                "fields": "comparator_completeness,comparator_consistency,scenario_readiness,scenario_confidence,tradeoff_summary,displacement_summary",
            },
            {
                "contract_name": "financial_card",
                "fields": "cost_completeness,central_financial_estimate,lower_financial_estimate,upper_financial_estimate,financial_confidence,financial_readiness,affordability_status",
            },
            {
                "contract_name": "governance_card",
                "fields": "causality_status,contradiction_warning,provisional_warning,required_validation,governance_burden_status",
            },
            {
                "contract_name": "management_action_card",
                "fields": "permitted_next_action,blocking_condition,top_management_question,approval_status",
            },
        ]

        for c in contracts:
            rows.append({
                "contract_record_id": f"{pkg_id}-DC-{c['contract_name']}",
                "decision_package_id": pkg_id,
                "approval_package_id": apid,
                "contract_name": c["contract_name"],
                "required_fields": c["fields"],
                "contract_status": "Active",
                "governance_note": "Streamlit-ready contract. No UI generated in this step.",
            })

    df = pd.DataFrame(rows)
    logger.info(f"Data contracts built: {len(df)} records")
    return df
