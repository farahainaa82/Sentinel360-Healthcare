"""
streamlit_executive_readiness_engine.py
Decision readiness distribution engine.
"""

from typing import Dict, List
import pandas as pd

from .streamlit_executive_logging import log_event

_READINESS_ORDER = [
    "Ready for Integrated Management Review",
    "Ready with Conditions",
    "Monitoring Only",
    "Requires Assumption Validation",
    "Non-Quantitative",
]


def build_readiness_distribution(df: pd.DataFrame) -> List[Dict]:
    if df.empty or "readiness_status" not in df.columns:
        return []
    total = len(df)
    counts = df["readiness_status"].value_counts().to_dict()
    result: List[Dict] = []
    for status in _READINESS_ORDER:
        count = counts.get(status, 0)
        pct = round((count / total) * 100, 1) if total else 0.0
        result.append(
            {
                "status": status,
                "count": int(count),
                "percentage": pct,
            }
        )
    log_event("READINESS_BUILT", f"total={total}")
    return result


def build_blocking_summary(df: pd.DataFrame) -> Dict[str, int]:
    summary = {
        "blocking_conditions": 0,
        "pending_confirmations": 0,
        "stakeholder_validation": 0,
        "financial_input": 0,
        "scenario_validation": 0,
    }
    if df.empty:
        return summary
    if "readiness_status" in df.columns:
        summary["blocking_conditions"] = int(
            df["readiness_status"]
            .astype(str)
            .str.contains("Requires|Conditional", case=False, na=False)
            .sum()
        )
    # Use evidence_warning as proxy for pending confirmations
    if "evidence_warning" in df.columns:
        summary["pending_confirmations"] = int(
            df["evidence_warning"].astype(str).str.strip().ne("").sum()
        )
    log_event("BLOCKING_SUMMARY_BUILT", str(summary))
    return summary
