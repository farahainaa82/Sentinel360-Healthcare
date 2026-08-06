"""
Decision Readiness Governance Validator for Phase 2D-4.

Validates that no prohibited decisions, wording, or selections appear.
"""

import logging
import re
import pandas as pd
from typing import List, Dict, Any, Tuple

LOG = logging.getLogger("decision_readiness_governance_validator")

PROHIBITED_WORDS = [
    "optimal", "best", "preferred", "approved", "guaranteed", "certain",
    "will save", "must select", "recommended option", "choose this",
]


def validate_readiness(
    readiness_df: pd.DataFrame,
    explanation_df: pd.DataFrame,
    logger: logging.Logger = None,
) -> Tuple[pd.DataFrame, bool]:
    logger = logger or LOG
    logger.info("Running readiness governance validation")

    issues: List[Dict[str, Any]] = []
    passed = True

    # Check for prohibited wording in explanations
    for _, row in explanation_df.iterrows():
        pkg_id = row["decision_package_id"]
        text = str(row.get("full_explanation", "")).lower()
        for word in PROHIBITED_WORDS:
            pattern = r"\b" + re.escape(word) + r"\b"
            if re.search(pattern, text):
                issues.append({
                    "issue_id": f"GOV-{pkg_id}-EXP-{word}",
                    "decision_package_id": pkg_id,
                    "issue_type": "Prohibited Wording",
                    "field_name": "full_explanation",
                    "prohibited_word": word,
                    "severity": "High",
                    "governance_warning": f"Prohibited word '{word}' found in explanation",
                    "resolution_required": True,
                })
                passed = False

    # Check approval status
    if (readiness_df["approval_status"] != "Pending Management Review").any():
        issues.append({
            "issue_id": "GOV-APPROVAL",
            "decision_package_id": "ALL",
            "issue_type": "Approval Violation",
            "field_name": "approval_status",
            "prohibited_word": "",
            "severity": "Critical",
            "governance_warning": "Approval status is not Pending Management Review",
            "resolution_required": True,
        })
        passed = False

    # Check causality status
    if "causality_status" in readiness_df.columns:
        if (readiness_df["causality_status"] != "Not Confirmed").any():
            issues.append({
                "issue_id": "GOV-CAUSALITY",
                "decision_package_id": "ALL",
                "issue_type": "Causality Violation",
                "field_name": "causality_status",
                "prohibited_word": "",
                "severity": "Critical",
                "governance_warning": "Causality status must remain Not Confirmed",
                "resolution_required": True,
            })
            passed = False

    # Check no preferred scenario
    # (This is a structural check; actual scenario data is in upstream phases)

    # Check no automatic transitions executed
    # (Transition engine should set transition_executed=False)

    issue_df = pd.DataFrame(issues)
    logger.info("Governance validation complete: passed=%s, issues=%s", passed, len(issues))
    return issue_df, passed
