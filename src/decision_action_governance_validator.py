"""
decision_action_governance_validator.py
Phase 2D-5 — Final governance validation before output.
"""

import pandas as pd
from typing import Tuple, List


def validate_governance_rules(
    routing_df: pd.DataFrame,
    eligibility_df: pd.DataFrame,
    primary_actions: pd.DataFrame,
    selection_contracts: pd.DataFrame,
    blocking_df: pd.DataFrame,
    prerequisite_df: pd.DataFrame,
    monitoring_df: pd.DataFrame,
    audit_df: pd.DataFrame
) -> Tuple[bool, List[str]]:
    """
    Run comprehensive governance validation.
    Returns (passed, list_of_issues).
    """
    issues = []

    # 1. No selection fabricated
    if selection_contracts["selected_flag"].any():
        issues.append("CRITICAL: selected_flag is True for at least one record")

    # 2. All approval statuses pending
    if (routing_df["approval_status"] != "Pending Management Review").any():
        issues.append("CRITICAL: Non-pending approval status found")

    # 3. No prohibited actions
    prohibited = [
        "Approve Scenario", "Approve Recommendation", "Approve Budget",
        "Implement Intervention", "Select Best Scenario", "Accept AI Recommendation"
    ]
    found_prohibited = eligibility_df[eligibility_df["action_name"].isin(prohibited)]
    if not found_prohibited.empty:
        issues.append(f"CRITICAL: {len(found_prohibited)} prohibited action records found")

    # 4. All prerequisites pending
    if not prerequisite_df.empty and (prerequisite_df["current_status"] == "Completed").any():
        issues.append("CRITICAL: At least one prerequisite marked Completed")

    # 5. All blocking conditions active
    if not blocking_df.empty and (blocking_df["current_status"] == "Resolved").any():
        issues.append("CRITICAL: At least one blocking condition marked Resolved")

    # 6. Monitoring not falsely implemented
    if not monitoring_df.empty and (monitoring_df["current_status"] == "Implemented").any():
        issues.append("CRITICAL: At least one monitoring action marked Implemented")

    # 7. No completed audit events
    if not audit_df.empty and (audit_df["future_audit_status"] == "Completed").any():
        issues.append("CRITICAL: At least one audit event marked Completed")

    # 8. Every package has exactly one primary action
    primary_counts = primary_actions.groupby("decision_action_routing_id").size()
    if (primary_counts != 1).any():
        issues.append(f"CRITICAL: {len(primary_counts[primary_counts != 1])} packages without exactly one primary action")

    # 9. All routing IDs unique
    if routing_df["decision_action_routing_id"].duplicated().any():
        issues.append("CRITICAL: Duplicate routing IDs found")

    # 10. Causality status preserved
    if "causality_status" in routing_df.columns:
        if (routing_df["causality_status"] != "Not Confirmed").any():
            issues.append("CRITICAL: causality_status changed from Not Confirmed")

    return len(issues) == 0, issues
