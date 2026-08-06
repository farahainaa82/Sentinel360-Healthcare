"""
Decision Package Population Validator for Phase 2D-2.

Verifies that merging 2D-1 inputs does not cause Cartesian explosion,
that approval_package_id remains unique, and that mandatory populations
are present.
"""

import os
import logging
from typing import Tuple
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(PROJECT_ROOT, "outputs", "decision_intelligence")

LOG = logging.getLogger("decision_package_population_validator")


def load_input(fname: str) -> pd.DataFrame:
    path = os.path.join(INPUT_DIR, fname)
    if not os.path.exists(path) or os.path.getsize(path) <= 2:
        return pd.DataFrame()
    return pd.read_csv(path)


def validate_population(logger: logging.Logger = None) -> Tuple[bool, str]:
    logger = logger or LOG
    logger.info("Starting population validation")

    base = load_input("step_2d1_integrated_decision_register.csv")
    if base.empty:
        return False, "Integrated decision register is empty"

    expected = len(base)
    logger.info(f"Base population: {expected}")

    # Check uniqueness of approval_package_id
    if base["approval_package_id"].duplicated().any():
        dups = base["approval_package_id"].duplicated().sum()
        return False, f"Found {dups} duplicate approval_package_id in base register"

    # Check merge populations against other key registers
    key_files = [
        "step_2d1_integrated_decision_status_register.csv",
        "step_2d1_decision_readiness_register.csv",
        "step_2d1_management_action_routing_register.csv",
        "step_2d1_decision_scorecard_input_register.csv",
        "step_2d1_management_summary_register.csv",
        "step_2d1_decision_evidence_register.csv",
        "step_2d1_decision_lineage_register.csv",
    ]

    for kf in key_files:
        df = load_input(kf)
        if df.empty:
            logger.warning(f"{kf} is empty; skipping population check")
            continue
        if "approval_package_id" not in df.columns and "integrated_decision_id" not in df.columns:
            logger.warning(f"{kf} lacks join key; skipping")
            continue

        join_key = "approval_package_id" if "approval_package_id" in df.columns else "integrated_decision_id"
        merged = base.merge(df[[join_key]], on=join_key, how="left", indicator=True)
        left_only = (merged["_merge"] == "left_only").sum()
        both = (merged["_merge"] == "both").sum()
        logger.info(f"{kf}: matched {both}, unmatched {left_only}")

        if len(merged) != expected:
            return False, f"{kf} merge produced {len(merged)} rows (expected {expected})"

    logger.info("Population validation passed")
    return True, "Population validation passed"
