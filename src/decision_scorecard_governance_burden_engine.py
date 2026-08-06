"""
Decision Scorecard Governance Burden Engine for Phase 2D-3.

Calculates governance burden metrics including blocking question count
and pending confirmation count per scorecard.
"""

import os
import logging
import pandas as pd
from typing import Dict, Any, List

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(PROJECT_ROOT, "outputs", "decision_intelligence")

LOG = logging.getLogger("decision_scorecard_governance_burden_engine")


def load_input(fname: str) -> pd.DataFrame:
    path = os.path.join(INPUT_DIR, fname)
    if not os.path.exists(path) or os.path.getsize(path) <= 2:
        return pd.DataFrame()
    return pd.read_csv(path)


def build_governance_burden(dim_df: pd.DataFrame, logger: logging.Logger = None) -> pd.DataFrame:
    logger = logger or LOG
    logger.info("Building governance burden details")

    questions = load_input("step_2d2_management_question_register.csv")
    confirmations = load_input("step_2d2_required_confirmation_register.csv")

    rows: List[Dict[str, Any]] = []
    for _, rec in dim_df.iterrows():
        pkg_id = rec["decision_package_id"]
        apid = rec["approval_package_id"]

        # Count blocking questions
        if not questions.empty and "decision_package_id" in questions.columns:
            pkg_questions = questions[questions["decision_package_id"] == pkg_id]
            blocking_count = pkg_questions["blocking_flag"].sum() if "blocking_flag" in pkg_questions.columns else 0
        else:
            blocking_count = 0

        # Count pending confirmations
        if not confirmations.empty and "decision_package_id" in confirmations.columns:
            pkg_conf = confirmations[confirmations["decision_package_id"] == pkg_id]
            pending_count = (pkg_conf["current_status"] == "Pending").sum() if "current_status" in pkg_conf.columns else 0
        else:
            pending_count = 0

        rows.append({
            "governance_burden_record_id": f"{pkg_id}-GB",
            "decision_package_id": pkg_id,
            "approval_package_id": apid,
            "blocking_question_count": int(blocking_count),
            "pending_confirmation_count": int(pending_count),
            "governance_issue_count": int(rec.get("governance_issue_count", 0)),
            "contradiction_warning": rec.get("contradiction_warning", False),
            "provisional_warning": rec.get("provisional_warning", False),
            "stakeholder_validation_required": rec.get("stakeholder_validation_required", False),
            "assumption_validation_required": rec.get("assumption_validation_required", False),
            "baseline_validation_required": rec.get("baseline_validation_required", False),
            "financial_validation_required": rec.get("financial_validation_required", False),
            "governance_burden_status": rec.get("governance_burden_status", "Low"),
            "burden_source_reference": "Step 2D-2 management questions and confirmations",
        })

    df = pd.DataFrame(rows)
    logger.info(f"Governance burden built: {len(df)} records")
    return df
