"""
Decision Readiness Queue Engine for Phase 2D-4.

Aligns readiness with permitted management queues.
Every readiness record maps to exactly one primary queue.
"""

import logging
import pandas as pd
from typing import Dict, Any, List

LOG = logging.getLogger("decision_readiness_queue_engine")

QUEUE_MAPPING = {
    "Ready for Integrated Management Review": "Integrated Management Review Queue",
    "Ready with Conditions": "Conditional Review Queue",
    "Requires Assumption Validation": "Assumption Validation Queue",
    "Requires Baseline Validation": "Baseline Validation Queue",
    "Requires Financial Input": "Financial Input Queue",
    "Requires Benefit Validation": "Benefit Validation Queue",
    "Requires Budget Data": "Budget Information Queue",
    "Requires Stakeholder Validation": "Stakeholder Validation Queue",
    "Requires Additional Scenario Analysis": "Additional Scenario Queue",
    "Requires Evidence Completion": "Evidence Completion Queue",
    "Requires Lineage Completion": "Lineage Completion Queue",
    "Monitoring Only": "Monitoring Queue",
    "Non-Quantitative": "Non-Quantitative Review Queue",
    "Not Suitable for Decision Use": "Not Suitable Register",
    "Rejected": "Rejected Register",
}


def build_queues(
    readiness_df: pd.DataFrame,
    logger: logging.Logger = None,
) -> pd.DataFrame:
    logger = logger or LOG
    logger.info("Building queue assignments")

    rows: List[Dict[str, Any]] = []
    for _, rec in readiness_df.iterrows():
        status = rec["final_readiness_status"]
        queue = QUEUE_MAPPING.get(status, "Unmapped Queue")

        rows.append({
            "queue_assignment_id": f"QA-{rec['decision_readiness_id']}",
            "decision_readiness_id": rec["decision_readiness_id"],
            "decision_scorecard_id": rec["decision_scorecard_id"],
            "decision_package_id": rec["decision_package_id"],
            "final_readiness_status": status,
            "primary_queue": queue,
            "secondary_queue": "",
            "queue_entry_date": pd.Timestamp.now().isoformat(),
            "queue_priority": "Standard",
            "queue_status": "Active",
            "governance_note": "Exactly one primary queue assigned",
        })

    result = pd.DataFrame(rows)
    logger.info("Queue assignments built: %s records", len(result))
    return result
