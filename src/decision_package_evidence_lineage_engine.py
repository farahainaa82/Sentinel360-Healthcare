"""
Decision Package Evidence and Lineage Engine for Phase 2D-2.

Assembles evidence and lineage references per package from all applicable phases.
"""

import logging
import pandas as pd
from typing import Dict, Any, List

LOG = logging.getLogger("decision_package_evidence_lineage_engine")


def build_evidence(integrated_df: pd.DataFrame, logger: logging.Logger = None) -> pd.DataFrame:
    logger = logger or LOG
    logger.info("Building evidence register")

    rows: List[Dict[str, Any]] = []
    for _, rec in integrated_df.iterrows():
        pkg_id = f"DPKG-{rec['approval_package_id']}"
        evidence_ids = []
        if pd.notna(rec.get("kpi_evidence_id")):
            evidence_ids.append(str(rec["kpi_evidence_id"]))
        if pd.notna(rec.get("trend_evidence_id")):
            evidence_ids.append(str(rec["trend_evidence_id"]))
        if pd.notna(rec.get("threshold_evidence_id")):
            evidence_ids.append(str(rec["threshold_evidence_id"]))
        if pd.notna(rec.get("risk_evidence_id")):
            evidence_ids.append(str(rec["risk_evidence_id"]))

        rows.append({
            "evidence_record_id": f"{pkg_id}-EV",
            "decision_package_id": pkg_id,
            "approval_package_id": rec["approval_package_id"],
            "evidence_reference_count": len(evidence_ids),
            "evidence_complete": rec.get("evidence_completeness", False),
            "evidence_ids": "|".join(evidence_ids) if evidence_ids else "None",
            "source_phase_list": "Phase 2B|Phase 2C-1|Phase 2C-2|Phase 2C-3|Phase 2D-1",
            "audit_traceability_status": "Traceable" if evidence_ids else "Partial",
        })

    df = pd.DataFrame(rows)
    logger.info(f"Evidence register built: {len(df)} records")
    return df


def build_lineage(integrated_df: pd.DataFrame, logger: logging.Logger = None) -> pd.DataFrame:
    logger = logger or LOG
    logger.info("Building lineage register")

    rows: List[Dict[str, Any]] = []
    for _, rec in integrated_df.iterrows():
        pkg_id = f"DPKG-{rec['approval_package_id']}"
        lineage_ids = []
        if pd.notna(rec.get("lineage_id")):
            lineage_ids.append(str(rec["lineage_id"]))

        rows.append({
            "lineage_record_id": f"{pkg_id}-LN",
            "decision_package_id": pkg_id,
            "approval_package_id": rec["approval_package_id"],
            "lineage_reference_count": len(lineage_ids),
            "lineage_complete": rec.get("lineage_completeness", False),
            "lineage_ids": "|".join(lineage_ids) if lineage_ids else "None",
            "source_phase_list": "Phase 2B|Phase 2C-1|Phase 2C-2|Phase 2C-3|Phase 2D-1",
            "audit_traceability_status": "Traceable" if lineage_ids else "Partial",
        })

    df = pd.DataFrame(rows)
    logger.info(f"Lineage register built: {len(df)} records")
    return df
