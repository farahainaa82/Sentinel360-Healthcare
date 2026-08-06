"""
Decision Scorecard Governance Validator for Phase 2D-3.

Validates that no prohibited decisions, wording, or selections appear in scorecards.
"""

import logging
import re
import pandas as pd
from typing import List, Dict, Any, Tuple

LOG = logging.getLogger("decision_scorecard_governance_validator")

PROHIBITED_WORDS = [
    "optimal", "best", "preferred", "approved", "guaranteed", "certain",
    "will save", "must select", "recommended option", "choose this",
]


def validate_scorecards(
    dim_df: pd.DataFrame,
    interpretation_df: pd.DataFrame,
    logger: logging.Logger = None,
) -> Tuple[pd.DataFrame, bool]:
    logger = logger or LOG
    logger.info("Running scorecard governance validation")

    issues: List[Dict[str, Any]] = []
    passed = True

    check_cols = ["management_interpretation", "tradeoff_status", "displacement_status", "dominance_status"]
    for _, row in interpretation_df.iterrows():
        pkg_id = row["decision_package_id"]
        for col in check_cols:
            if col not in row or pd.isna(row[col]):
                continue
            text = str(row[col]).lower()
            for word in PROHIBITED_WORDS:
                pattern = r"\b" + re.escape(word) + r"\b"
                if re.search(pattern, text):
                    issues.append({
                        "issue_id": f"GOV-{pkg_id}-{col}-{word}",
                        "decision_package_id": pkg_id,
                        "approval_package_id": row["approval_package_id"],
                        "issue_type": "Prohibited Wording",
                        "field_name": col,
                        "prohibited_word": word,
                        "severity": "High",
                        "governance_warning": f"Prohibited word '{word}' found in {col}",
                        "resolution_required": True,
                    })
                    passed = False

    # Check causality and approval status
    if (dim_df["approval_status"] != "Pending Management Review").any():
        issues.append({
            "issue_id": "GOV-APPROVAL",
            "decision_package_id": "ALL",
            "approval_package_id": "ALL",
            "issue_type": "Approval Violation",
            "field_name": "approval_status",
            "prohibited_word": "",
            "severity": "Critical",
            "governance_warning": "One or more scorecards have approval_status != Pending Management Review",
            "resolution_required": True,
        })
        passed = False

    # Check no High financial confidence introduced
    if "financial_confidence" in dim_df.columns:
        high_conf = dim_df["financial_confidence"].astype(str).str.contains("High", case=False, na=False)
        if high_conf.any():
            issues.append({
                "issue_id": "GOV-FIN-CONF",
                "decision_package_id": "ALL",
                "approval_package_id": "ALL",
                "issue_type": "High Financial Confidence",
                "field_name": "financial_confidence",
                "prohibited_word": "",
                "severity": "High",
                "governance_warning": "High financial confidence detected. Only Moderate or lower is permitted.",
                "resolution_required": True,
            })
            passed = False

    df = pd.DataFrame(issues)
    logger.info(f"Governance validation complete. Issues: {len(df)}, Passed: {passed}")
    return df, passed
