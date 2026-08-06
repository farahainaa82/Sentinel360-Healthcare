"""
Decision Scorecard Condition Engine for Phase 2D-3.

Creates explicit condition flags per scorecard with source references.
"""

import logging
import pandas as pd
from typing import Dict, Any, List

LOG = logging.getLogger("decision_scorecard_condition_engine")

CONDITION_DEFINITIONS = [
    {"flag_name": "provisional_threshold_condition", "source_field": "provisional_threshold_flag", "severity": "Moderate"},
    {"flag_name": "contradiction_condition", "source_field": "contradiction_warning", "severity": "High"},
    {"flag_name": "assumption_validation_condition", "source_field": "assumption_validation_required", "severity": "High"},
    {"flag_name": "baseline_validation_condition", "source_field": "baseline_validation_required", "severity": "Moderate"},
    {"flag_name": "financial_input_condition", "source_field": "missing_financial_input_flag", "severity": "Moderate"},
    {"flag_name": "stakeholder_validation_condition", "source_field": "stakeholder_validation_required", "severity": "Moderate"},
    {"flag_name": "scenario_completeness_condition", "source_field": "scenario_readiness", "severity": "Moderate"},
    {"flag_name": "evidence_completeness_condition", "source_field": "evidence_completeness", "severity": "Low"},
    {"flag_name": "lineage_completeness_condition", "source_field": "lineage_completeness", "severity": "Low"},
    {"flag_name": "uncertainty_condition", "source_field": "uncertainty_available", "severity": "Low"},
    {"flag_name": "monitoring_condition", "source_field": "package_readiness", "severity": "Low"},
    {"flag_name": "non_quantitative_condition", "source_field": "package_readiness", "severity": "Low"},
    {"flag_name": "blocking_condition", "source_field": "governance_burden_status", "severity": "High"},
]


def build_conditions(dim_df: pd.DataFrame, logger: logging.Logger = None) -> pd.DataFrame:
    logger = logger or LOG
    logger.info("Building condition flags")

    rows: List[Dict[str, Any]] = []
    for _, rec in dim_df.iterrows():
        pkg_id = rec["decision_package_id"]
        for cond in CONDITION_DEFINITIONS:
            field = cond["source_field"]
            val = rec.get(field, False)
            if pd.isna(val):
                val = False

            # Determine flag_status
            if field == "package_readiness":
                if cond["flag_name"] == "monitoring_condition":
                    active = "Monitoring Only" in str(val)
                elif cond["flag_name"] == "non_quantitative_condition":
                    active = "Non-Quantitative" in str(val)
                else:
                    active = bool(val)
            elif field == "scenario_readiness":
                active = str(val) not in ("Ready with Conditions", "Monitoring Only", "Not Assessable", "Not Available")
            else:
                active = bool(val)

            flag_status = "Active" if active else "Inactive"
            required_action = "Review and resolve before proceeding" if active else "None"

            rows.append({
                "condition_flag_id": f"{pkg_id}-CF-{cond['flag_name']}",
                "decision_package_id": pkg_id,
                "approval_package_id": rec["approval_package_id"],
                "flag_name": cond["flag_name"],
                "flag_status": flag_status,
                "flag_severity": cond["severity"],
                "flag_reason": f"Derived from {field} = {val}",
                "required_action": required_action,
                "responsible_role": "Operations Manager",
                "source_reference": f"Step 2D-2 decision package field: {field}",
            })

    df = pd.DataFrame(rows)
    logger.info(f"Condition flags built: {len(df)} records")
    return df
