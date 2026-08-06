"""
Decision Scorecard Evidence and Lineage Engine for Phase 2D-3.

Assembles evidence and lineage references per scorecard from decision packages.
"""

import logging
import pandas as pd
from typing import Dict, Any, List

LOG = logging.getLogger("decision_scorecard_evidence_lineage_engine")


def build_evidence(dim_df: pd.DataFrame, logger: logging.Logger = None) -> pd.DataFrame:
    logger = logger or LOG
    logger.info("Building scorecard evidence register")

    rows: List[Dict[str, Any]] = []
    for _, rec in dim_df.iterrows():
        pkg_id = rec["decision_package_id"]
        rows.append({
            "evidence_record_id": f"{pkg_id}-EV",
            "decision_package_id": pkg_id,
            "approval_package_id": rec["approval_package_id"],
            "evidence_reference_count": rec.get("evidence_reference_count", 0),
            "evidence_complete": rec.get("evidence_completeness", False),
            "evidence_ids": "Derived from Step 2D-2 evidence register",
            "source_phase_list": "Phase 2B|Phase 2C-1|Phase 2C-2|Phase 2C-3|Phase 2D-1|Phase 2D-2",
            "audit_traceability_status": "Traceable" if rec.get("evidence_completeness", False) else "Partial",
        })

    df = pd.DataFrame(rows)
    logger.info(f"Scorecard evidence built: {len(df)} records")
    return df


def build_lineage(dim_df: pd.DataFrame, logger: logging.Logger = None) -> pd.DataFrame:
    logger = logger or LOG
    logger.info("Building scorecard lineage register")

    rows: List[Dict[str, Any]] = []
    for _, rec in dim_df.iterrows():
        pkg_id = rec["decision_package_id"]
        rows.append({
            "lineage_record_id": f"{pkg_id}-LN",
            "decision_package_id": pkg_id,
            "approval_package_id": rec["approval_package_id"],
            "lineage_reference_count": rec.get("lineage_reference_count", 0),
            "lineage_complete": rec.get("lineage_completeness", False),
            "lineage_ids": "Derived from Step 2D-2 lineage register",
            "source_phase_list": "Phase 2B|Phase 2C-1|Phase 2C-2|Phase 2C-3|Phase 2D-1|Phase 2D-2",
            "audit_traceability_status": "Traceable" if rec.get("lineage_completeness", False) else "Partial",
        })

    df = pd.DataFrame(rows)
    logger.info(f"Scorecard lineage built: {len(df)} records")
    return df
