"""
Decision Package Monitoring Engine for Phase 2D-2.

Generates monitoring requirements per package. No exact future dates are invented.
"""

import logging
import pandas as pd
from typing import List, Dict, Any

LOG = logging.getLogger("decision_package_monitoring_engine")


def build_monitoring(integrated_df: pd.DataFrame, logger: logging.Logger = None) -> pd.DataFrame:
    logger = logger or LOG
    logger.info("Building monitoring requirements")

    rows: List[Dict[str, Any]] = []
    for _, rec in integrated_df.iterrows():
        pkg_id = f"DPKG-{rec['approval_package_id']}"
        status = rec["decision_status"]

        monitoring_required = status in ("Monitoring Only", "Ready with Conditions", "Requires Assumption Validation")

        if monitoring_required:
            frequency = (
                "Weekly" if status == "Monitoring Only" else
                "Bi-weekly" if status == "Requires Assumption Validation" else
                "Monthly"
            )
            rows.append({
                "monitoring_id": f"{pkg_id}-MON",
                "decision_package_id": pkg_id,
                "approval_package_id": rec["approval_package_id"],
                "monitoring_required": True,
                "monitoring_frequency": frequency,
                "monitoring_kpi": rec.get("dominant_kpi_id", "dominant_kpi"),
                "trigger_condition": "KPI threshold breach or trend deterioration",
                "escalation_condition": "Repeated breach or risk tier increase",
                "responsible_role": "Operations Manager",
                "reassessment_condition": "Status change or new evidence",
                "next_review_requirement": f"Next review per {frequency} schedule",
            })

    df = pd.DataFrame(rows)
    logger.info(f"Monitoring requirements built: {len(df)} total")
    return df
