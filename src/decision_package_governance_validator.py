"""
Decision Package Governance Validator for Phase 2D-2.

Validates that no prohibited decisions, wording, or selections appear in packages.
"""

import logging
import re
import pandas as pd
from typing import List, Dict, Any, Tuple

LOG = logging.getLogger("decision_package_governance_validator")

PROHIBITED_WORDS = [
    "optimal", "best", "preferred", "approved", "guaranteed", "certain",
    "will save", "must select", "recommended option", "choose this",
]


def validate_packages(
    package_df: pd.DataFrame,
    action_df: pd.DataFrame,
    confirmation_df: pd.DataFrame,
    narrative_df: pd.DataFrame,
    logger: logging.Logger = None,
) -> Tuple[pd.DataFrame, bool]:
    logger = logger or LOG
    logger.info("Running governance validation")

    issues: List[Dict[str, Any]] = []
    passed = True

    # Check package-level fields
    check_cols = ["management_narrative", "scenario_tradeoff_summary", "scenario_displacement_summary",
                  "scenario_dominance_summary", "permitted_management_actions"]
    for _, row in package_df.iterrows():
        pkg_id = row["decision_package_id"]
        for col in check_cols:
            if col not in row or pd.isna(row[col]):
                continue
            text = str(row[col]).lower()
            for word in PROHIBITED_WORDS:
                pattern = r"\\b" + re.escape(word) + r"\\b"
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

    # Check no action selected
    if action_df["action_selected"].any():
        selected = action_df[action_df["action_selected"]]
        for _, row in selected.iterrows():
            issues.append({
                "issue_id": f"GOV-{row['decision_package_id']}-ACTION-SELECTED",
                "decision_package_id": row["decision_package_id"],
                "approval_package_id": row["approval_package_id"],
                "issue_type": "Action Pre-selected",
                "field_name": "action_selected",
                "prohibited_word": "",
                "severity": "Critical",
                "governance_warning": "Management action is pre-selected. This is prohibited.",
                "resolution_required": True,
            })
        passed = False

    # Check no confirmation completed
    completed = confirmation_df[confirmation_df["current_status"] == "Completed"]
    for _, row in completed.iterrows():
        issues.append({
            "issue_id": f"GOV-{row['decision_package_id']}-CONF-COMPLETED",
            "decision_package_id": row["decision_package_id"],
            "approval_package_id": row["approval_package_id"],
            "issue_type": "Confirmation Pre-completed",
            "field_name": "current_status",
            "prohibited_word": "",
            "severity": "Critical",
            "governance_warning": "Confirmation is marked as completed without evidence.",
            "resolution_required": True,
        })
        passed = False

    # Check causality and approval status
    if (package_df["causality_status"] != "Not Confirmed").any():
        issues.append({
            "issue_id": "GOV-CAUSALITY",
            "decision_package_id": "ALL",
            "approval_package_id": "ALL",
            "issue_type": "Causality Violation",
            "field_name": "causality_status",
            "prohibited_word": "",
            "severity": "Critical",
            "governance_warning": "One or more packages have causality_status != Not Confirmed",
            "resolution_required": True,
        })
        passed = False

    if (package_df["approval_status"] != "Pending Management Review").any():
        issues.append({
            "issue_id": "GOV-APPROVAL",
            "decision_package_id": "ALL",
            "approval_package_id": "ALL",
            "issue_type": "Approval Violation",
            "field_name": "approval_status",
            "prohibited_word": "",
            "severity": "Critical",
            "governance_warning": "One or more packages have approval_status != Pending Management Review",
            "resolution_required": True,
        })
        passed = False

    df = pd.DataFrame(issues)
    logger.info(f"Governance validation complete. Issues: {len(df)}, Passed: {passed}")
    return df, passed
