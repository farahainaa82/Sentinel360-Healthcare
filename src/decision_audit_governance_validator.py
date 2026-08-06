"""
decision_audit_governance_validator.py
Phase 2D-6 — Final governance validation before output.
"""

import pandas as pd
from typing import Tuple, List


def validate_governance_rules(
    routing_df: pd.DataFrame,
    audit_contracts: pd.DataFrame,
    history_contracts: pd.DataFrame,
    management_reviews: pd.DataFrame,
    evidence_profiles: pd.DataFrame,
    lineage_profiles: pd.DataFrame,
    prereq_df: pd.DataFrame = None,
    blocking_df: pd.DataFrame = None
) -> Tuple[bool, List[str]]:
    issues = []

    # 1. No completed audit events
    if not audit_contracts.empty and (audit_contracts["event_status"] == "Completed").any():
        issues.append("CRITICAL: Completed audit event found")

    # 2. No fabricated actors
    if not audit_contracts.empty and (audit_contracts["actor_id"] != "").any():
        issues.append("CRITICAL: Fabricated actor_id found in audit contracts")
    if not audit_contracts.empty and (audit_contracts["actor_name"] != "").any():
        issues.append("CRITICAL: Fabricated actor_name found in audit contracts")

    # 3. No fabricated timestamps
    if not audit_contracts.empty and (audit_contracts["event_timestamp"] != "").any():
        issues.append("CRITICAL: Fabricated timestamp found in audit contracts")

    # 4. No fabricated management reviews
    if not management_reviews.empty and (management_reviews["reviewer_id"] != "").any():
        issues.append("CRITICAL: Fabricated reviewer_id found")
    if not management_reviews.empty and (management_reviews["reviewer_name"] != "").any():
        issues.append("CRITICAL: Fabricated reviewer_name found")

    # 5. All approval statuses pending
    if (routing_df["approval_status"] != "Pending Management Review").any():
        issues.append("CRITICAL: Non-pending approval status found")

    # 6. causality_status preserved
    if "causality_status" in routing_df.columns:
        if (routing_df["causality_status"] != "Not Confirmed").any():
            issues.append("CRITICAL: causality_status changed from Not Confirmed")

    # 7. History contracts in Initial Governed State
    if not history_contracts.empty and (history_contracts["history_status"] != "Initial Governed State").any():
        issues.append("CRITICAL: History contract not in Initial Governed State")

    # 8. No orphan profiles
    routing_ids = set(routing_df["decision_package_id"])
    ev_ids = set(evidence_profiles["decision_package_id"])
    ln_ids = set(lineage_profiles["decision_package_id"])
    if not ev_ids.issubset(routing_ids):
        issues.append("CRITICAL: Orphan evidence profiles found")
    if not ln_ids.issubset(routing_ids):
        issues.append("CRITICAL: Orphan lineage profiles found")

    # 9. Unique profile IDs
    if evidence_profiles["decision_evidence_profile_id"].duplicated().any():
        issues.append("CRITICAL: Duplicate evidence profile IDs")
    if lineage_profiles["decision_lineage_profile_id"].duplicated().any():
        issues.append("CRITICAL: Duplicate lineage profile IDs")

    return len(issues) == 0, issues
