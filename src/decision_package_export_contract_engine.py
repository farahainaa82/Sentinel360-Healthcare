"""
Decision Package Export Contract Engine for Phase 2D-2.

Creates structured export-ready data contracts for downstream consumers.
"""

import logging
import pandas as pd
from typing import Dict, Any, List

LOG = logging.getLogger("decision_package_export_contract_engine")

EXPORT_CONTRACTS = [
    {
        "contract_name": "decision_package_summary",
        "required_fields": [
            "decision_package_id", "approval_package_id", "hospital_name", "department_name",
            "dominant_kpi_name", "package_status", "package_readiness", "completeness_status",
            "issue_title", "management_narrative",
        ],
    },
    {
        "contract_name": "full_evidence_package",
        "required_fields": [
            "decision_package_id", "approval_package_id", "evidence_reference_count",
            "lineage_reference_count", "evidence_complete", "lineage_complete",
            "evidence_ids", "lineage_ids", "source_phase_list", "audit_traceability_status",
        ],
    },
    {
        "contract_name": "management_review_sheet",
        "required_fields": [
            "decision_package_id", "approval_package_id", "management_question_id",
            "question_text", "question_category", "mandatory_flag", "blocking_flag",
            "responsible_role", "confirmation_id", "confirmation_type", "current_status",
        ],
    },
    {
        "contract_name": "scenario_comparison_sheet",
        "required_fields": [
            "decision_package_id", "approval_package_id", "scenario_family",
            "baseline_available", "conservative_available", "expected_available",
            "higher_intensity_available", "comparator_completeness", "comparator_consistency",
            "scenario_tradeoff_summary", "scenario_displacement_summary", "scenario_dominance_summary",
        ],
    },
    {
        "contract_name": "financial_comparison_sheet",
        "required_fields": [
            "decision_package_id", "approval_package_id", "financial_review_required",
            "cost_completeness", "estimated_scenario_cost", "estimated_financial_benefit",
            "estimated_net_financial_impact", "roi_status", "payback_status",
            "affordability_status", "lower_financial_estimate", "central_financial_estimate",
            "upper_financial_estimate", "financial_confidence",
        ],
    },
    {
        "contract_name": "audit_and_lineage_sheet",
        "required_fields": [
            "decision_package_id", "approval_package_id", "causality_status",
            "contradiction_warning", "provisional_warning", "evidence_completeness",
            "lineage_completeness", "governance_issue_count", "package_limitations",
            "source_phase_list", "audit_traceability_status",
        ],
    },
]


def build_export_contracts(integrated_df: pd.DataFrame, logger: logging.Logger = None) -> pd.DataFrame:
    logger = logger or LOG
    logger.info("Building export contracts")

    rows: List[Dict[str, Any]] = []
    for _, rec in integrated_df.iterrows():
        pkg_id = f"DPKG-{rec['approval_package_id']}"
        for contract in EXPORT_CONTRACTS:
            rows.append({
                "export_contract_id": f"{pkg_id}-EC-{contract['contract_name']}",
                "decision_package_id": pkg_id,
                "approval_package_id": rec["approval_package_id"],
                "contract_name": contract["contract_name"],
                "required_fields": "|".join(contract["required_fields"]),
                "contract_status": "Active",
                "governance_note": "Export contract governed by Step 2D-2 specification.",
            })

    df = pd.DataFrame(rows)
    logger.info(f"Export contracts built: {len(df)} total")
    return df
