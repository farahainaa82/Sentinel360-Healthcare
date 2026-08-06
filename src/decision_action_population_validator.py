"""
decision_action_population_validator.py
Phase 2D-5 — Validate action-routing population integrity.
"""

import pandas as pd
from typing import Tuple


def validate_action_routing_population(
    readiness_df: pd.DataFrame,
    routing_df: pd.DataFrame
) -> Tuple[bool, str]:
    """
    Ensure exactly one routing package per readiness record,
    no duplicates, no drops, IDs are unique.
    """
    expected_count = len(readiness_df)
    actual_count = len(routing_df)

    if actual_count != expected_count:
        return False, f"Population mismatch: expected {expected_count}, got {actual_count}"

    if routing_df["decision_action_routing_id"].duplicated().any():
        dupes = routing_df["decision_action_routing_id"].duplicated().sum()
        return False, f"Duplicate routing IDs found: {dupes}"

    missing_readiness = set(readiness_df["decision_readiness_id"]) - set(routing_df["decision_readiness_id"])
    if missing_readiness:
        return False, f"Missing readiness IDs in routing: {len(missing_readiness)}"

    missing_packages = set(readiness_df["decision_package_id"]) - set(routing_df["decision_package_id"])
    if missing_packages:
        return False, f"Missing package IDs in routing: {len(missing_packages)}"

    return True, "Population validated"
