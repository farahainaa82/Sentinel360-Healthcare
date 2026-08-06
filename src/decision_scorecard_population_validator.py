"""
Decision Scorecard Population Validator for Phase 2D-3.

Verifies that merging 2D-2 inputs does not cause Cartesian explosion,
that decision_package_id remains unique, and that mandatory populations
are present.
"""

import os
import logging
from typing import Tuple
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(PROJECT_ROOT, "outputs", "decision_intelligence")

LOG = logging.getLogger("decision_scorecard_population_validator")


def load_input(fname: str) -> pd.DataFrame:
    path = os.path.join(INPUT_DIR, fname)
    if not os.path.exists(path) or os.path.getsize(path) <= 2:
        return pd.DataFrame()
    return pd.read_csv(path)


def validate_population(logger: logging.Logger = None) -> Tuple[bool, str]:
    logger = logger or LOG
    logger.info("Starting population validation")

    base = load_input("step_2d2_decision_package_register.csv")
    if base.empty:
        return False, "Decision package register is empty"

    expected = len(base)
    logger.info(f"Base population: {expected}")

    if base["decision_package_id"].duplicated().any():
        dups = base["decision_package_id"].duplicated().sum()
        return False, f"Found {dups} duplicate decision_package_id in base register"

    key_files = [
        "step_2d2_decision_package_readiness_register.csv",
        "step_2d2_decision_package_completeness_register.csv",
        "step_2d2_priority_view_register.csv",
        "step_2d2_evidence_register.csv",
        "step_2d2_lineage_register.csv",
    ]

    for kf in key_files:
        df = load_input(kf)
        if df.empty:
            logger.warning(f"{kf} is empty; skipping population check")
            continue
        join_key = "decision_package_id" if "decision_package_id" in df.columns else "approval_package_id"
        merged = base.merge(df[[join_key]], on=join_key, how="left", indicator=True)
        left_only = (merged["_merge"] == "left_only").sum()
        both = (merged["_merge"] == "both").sum()
        logger.info(f"{kf}: matched {both}, unmatched {left_only}")
        if len(merged) != expected:
            return False, f"{kf} merge produced {len(merged)} rows (expected {expected})"

    logger.info("Population validation passed")
    return True, "Population validation passed"
