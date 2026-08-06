"""
Decision Readiness Population Validator for Phase 2D-4.

Ensures exactly one readiness record per decision scorecard.
Prevents Cartesian joins and duplicate IDs.
"""

import logging
import pandas as pd
from typing import Tuple

LOG = logging.getLogger("decision_readiness_population_validator")


def validate_population(
    scorecard_df: pd.DataFrame,
    readiness_df: pd.DataFrame,
    logger: logging.Logger = None,
) -> Tuple[bool, str]:
    logger = logger or LOG
    logger.info("Starting population validation")

    expected = len(scorecard_df)
    actual = len(readiness_df)

    if expected == 0:
        return False, "No scorecards found"

    if actual == 0:
        return False, "No readiness records created"

    if actual != expected:
        return False, f"Population mismatch: expected {expected}, got {actual}"

    # Check for duplicate scorecard IDs
    dup_scorecards = readiness_df["decision_scorecard_id"].duplicated().sum()
    if dup_scorecards > 0:
        return False, f"Duplicate scorecard IDs found: {dup_scorecards}"

    # Check for duplicate package IDs
    dup_packages = readiness_df["decision_package_id"].duplicated().sum()
    if dup_packages > 0:
        return False, f"Duplicate package IDs found: {dup_packages}"

    # Check for duplicate readiness IDs
    dup_readiness = readiness_df["decision_readiness_id"].duplicated().sum()
    if dup_readiness > 0:
        return False, f"Duplicate readiness IDs found: {dup_readiness}"

    # Verify no orphan records
    orphan = ~readiness_df["decision_scorecard_id"].isin(scorecard_df["decision_scorecard_id"])
    if orphan.any():
        return False, f"Orphan readiness records: {orphan.sum()}"

    logger.info("Population validation passed: %s records", actual)
    return True, f"Population validated: {actual} readiness records for {expected} scorecards"
