"""
Decision Readiness Precedence Engine for Phase 2D-4.

Applies explicit precedence so blocking conditions are not hidden.
"""

import logging
import pandas as pd
from typing import Dict, List, Any

LOG = logging.getLogger("decision_readiness_precedence_engine")

# Precedence from strongest exclusion to most advanced readiness
PRECEDENCE_RANK = {
    "Rejected": 1,
    "Not Suitable for Decision Use": 2,
    "Non-Quantitative": 3,
    "Monitoring Only": 4,
    "Requires Evidence Completion": 5,
    "Requires Lineage Completion": 6,
    "Requires Baseline Validation": 7,
    "Requires Assumption Validation": 8,
    "Requires Additional Scenario Analysis": 9,
    "Requires Financial Input": 10,
    "Requires Benefit Validation": 11,
    "Requires Budget Data": 12,
    "Requires Stakeholder Validation": 13,
    "Ready with Conditions": 14,
    "Ready for Integrated Management Review": 15,
}


def apply_precedence(
    readiness_df: pd.DataFrame,
    logger: logging.Logger = None,
) -> pd.DataFrame:
    logger = logger or LOG
    logger.info("Applying readiness precedence")

    readiness_df = readiness_df.copy()
    readiness_df["precedence_rank"] = readiness_df["final_readiness_status"].map(
        PRECEDENCE_RANK
    ).fillna(99).astype(int)

    # Validate no duplicate statuses per package
    dup_status = readiness_df.groupby("decision_package_id").size()
    multi_status = dup_status[dup_status > 1]
    if len(multi_status) > 0:
        logger.warning("Packages with multiple readiness records: %s", len(multi_status))

    logger.info("Precedence applied for %s records", len(readiness_df))
    return readiness_df


def get_precedence_config() -> pd.DataFrame:
    """Return the precedence configuration as a DataFrame."""
    rows: List[Dict[str, Any]] = []
    for status, rank in PRECEDENCE_RANK.items():
        rows.append({
            "status_name": status,
            "precedence_rank": rank,
            "blocking_flag": rank <= 13 and status not in ("Non-Quantitative", "Monitoring Only"),
            "exclusion_flag": rank <= 2,
        })
    return pd.DataFrame(rows)
