"""
streamlit_executive_queue_engine.py
Management attention queue engine.
"""

from typing import Dict, List
import pandas as pd

from .streamlit_executive_logging import log_event

_QUEUE_MAP = {
    "Integrated Management Review Queue": "Ready for Integrated Management Review",
    "Conditional Review Queue": "Ready with Conditions",
    "Assumption Validation Queue": "Requires Assumption Validation",
    "Financial Input Queue": "Requires Financial Input",
    "Budget Information Queue": "Requires Budget Information",
    "Stakeholder Validation Queue": "Requires Stakeholder Validation",
    "Additional Scenario Queue": "Requires Additional Scenario Analysis",
    "Monitoring Queue": "Monitoring Only",
    "Non-Quantitative Review Queue": "Non-Quantitative",
    "Evidence Completion Queue": "Requires Evidence Completion",
    "Lineage Completion Queue": "Requires Lineage Completion",
}


def build_queue_summary(df: pd.DataFrame) -> List[Dict]:
    if df.empty or "readiness_status" not in df.columns:
        return []
    summary: List[Dict] = []
    for queue_name, readiness in _QUEUE_MAP.items():
        sub = df[df["readiness_status"] == readiness]
        count = len(sub)
        urgency_dist: Dict[str, int] = {}
        if "urgency" in sub.columns:
            urgency_dist = sub["urgency"].value_counts().to_dict()
        oldest = ""
        latest = ""
        if "reporting_date" in sub.columns:
            dates = pd.to_datetime(sub["reporting_date"], errors="coerce").dropna()
            if not dates.empty:
                oldest = str(dates.min().date())
                latest = str(dates.max().date())
        top_reason = readiness
        summary.append(
            {
                "queue_name": queue_name,
                "count": int(count),
                "responsible_role": "",
                "urgency_distribution": urgency_dist,
                "oldest_date": oldest,
                "latest_date": latest,
                "top_reason": top_reason,
            }
        )
    log_event("QUEUE_SUMMARY_BUILT", f"queues={len(summary)}")
    return summary
