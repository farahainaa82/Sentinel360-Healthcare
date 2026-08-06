"""
Decision Governance Validator for Phase 2D-1.

Validates integrated decision outputs for prohibited wording,
unsupported approvals, and governance compliance.
"""

import pandas as pd
from typing import List, Tuple


class DecisionGovernanceValidator:
    PROHIBITED_WORDS = [
        "Guaranteed", "Proven", "Best", "Optimal", "Approved",
        "Will improve", "Will save", "Recommended scenario",
        "Preferred scenario", "Selected scenario", "Best scenario",
    ]

    def validate_outputs(self, integrated_df: pd.DataFrame, status_df: pd.DataFrame,
                         action_df: pd.DataFrame, summary_df: pd.DataFrame) -> Tuple[pd.DataFrame, bool]:
        """
        Returns (issue_register DataFrame, all_valid bool)
        """
        issues = []
        all_valid = True

        # Check integrated records for prohibited wording
        # Only check Phase 2D-1 output fields that we control, not upstream data fields
        check_cols = ["management_summary", "decision_status_reason", "scenario_tradeoff_summary",
                      "scenario_displacement_summary", "scenario_dominance_summary", "permitted_management_actions"]
        check_cols = [c for c in check_cols if c in integrated_df.columns]
        for _, row in integrated_df.iterrows():
            pkg_id = row.get("approval_package_id", "")
            for col in check_cols:
                val = str(row.get(col, ""))
                for word in self.PROHIBITED_WORDS:
                    # Use word boundary regex to avoid substring matches within other words
                    import re
                    pattern = r"\b" + re.escape(word.lower()) + r"\b"
                    if re.search(pattern, val.lower()):
                        issues.append({
                            "issue_id": f"GOV-WORD-{pkg_id}-{len(issues)+1:04d}",
                            "approval_package_id": pkg_id,
                            "issue_type": "Prohibited Wording",
                            "field_name": col,
                            "prohibited_word": word,
                            "severity": "High",
                            "governance_warning": f"Prohibited wording '{word}' found in {col}",
                            "resolution_required": True,
                        })
                        all_valid = False

        # Check no approval statuses
        if "approval_status" in integrated_df.columns:
            approved = integrated_df[integrated_df["approval_status"].str.contains(
                "Approved|Authorised|Signed Off", case=False, na=False
            )]
            for _, row in approved.iterrows():
                issues.append({
                    "issue_id": f"GOV-APPR-{row['approval_package_id']}-{len(issues)+1:04d}",
                    "approval_package_id": row["approval_package_id"],
                    "issue_type": "Unauthorized Approval",
                    "field_name": "approval_status",
                    "prohibited_word": row["approval_status"],
                    "severity": "Critical",
                    "governance_warning": "Management approval must not be recorded at this stage",
                    "resolution_required": True,
                })
                all_valid = False

        # Check action selection status — must be "Not Selected" or equivalent, not "Selected"
        if "action_selection_status" in action_df.columns:
            selected = action_df[
                action_df["action_selection_status"].str.lower().isin(["selected", "approved", "chosen"])
            ]
            for _, row in selected.iterrows():
                issues.append({
                    "issue_id": f"GOV-ACT-{row['approval_package_id']}-{len(issues)+1:04d}",
                    "approval_package_id": row["approval_package_id"],
                    "issue_type": "Unauthorized Action Selection",
                    "field_name": "action_selection_status",
                    "prohibited_word": row["action_selection_status"],
                    "severity": "High",
                    "governance_warning": "Management action must not be pre-selected",
                    "resolution_required": True,
                })
                all_valid = False

        # Check causality status
        if "causality_status" in integrated_df.columns:
            confirmed = integrated_df[integrated_df["causality_status"].str.contains(
                r"(?<!Not\s)Confirmed", case=False, na=False, regex=True
            )]
            for _, row in confirmed.iterrows():
                issues.append({
                    "issue_id": f"GOV-CAUS-{row['approval_package_id']}-{len(issues)+1:04d}",
                    "approval_package_id": row["approval_package_id"],
                    "issue_type": "Unauthorized Causality Confirmation",
                    "field_name": "causality_status",
                    "prohibited_word": "Confirmed",
                    "severity": "High",
                    "governance_warning": "Causality must remain Not Confirmed",
                    "resolution_required": True,
                })
                all_valid = False

        return pd.DataFrame(issues), all_valid
