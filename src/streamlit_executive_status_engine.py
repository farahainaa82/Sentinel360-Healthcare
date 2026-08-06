"""
streamlit_executive_status_engine.py
Build executive status strip counts.
"""

from typing import Dict
import pandas as pd

from .streamlit_executive_logging import log_event


def build_executive_cards(df: pd.DataFrame) -> Dict[str, Dict]:
    if df.empty:
        return {}
    total = len(df)

    def pct(count: int) -> float:
        return round((count / total) * 100, 1) if total else 0.0

    # Card 1: Packages Requiring Attention
    attention_vals = {"Immediate Management Attention", "Priority Management Review"}
    c1 = (
        df["management_attention_level"]
        .astype(str)
        .isin(attention_vals)
        .sum()
        if "management_attention_level" in df.columns
        else 0
    )

    # Card 2: Critical and High Risk (risk_tier numeric >= 70)
    c2 = 0
    if "risk_tier" in df.columns:
        try:
            c2 = (pd.to_numeric(df["risk_tier"], errors="coerce") >= 70).sum()
        except Exception:
            c2 = 0

    # Card 3: Ready for Integrated Management Review
    c3 = (
        (df["readiness_status"] == "Ready for Integrated Management Review").sum()
        if "readiness_status" in df.columns
        else 0
    )

    # Card 4: Ready with Conditions
    c4 = (
        (df["readiness_status"] == "Ready with Conditions").sum()
        if "readiness_status" in df.columns
        else 0
    )

    # Card 5: Monitoring Only
    c5 = (
        (df["readiness_status"] == "Monitoring Only").sum()
        if "readiness_status" in df.columns
        else 0
    )

    # Card 6: Pending Management Review
    c6 = (
        (df["approval_status"] == "Pending Management Review").sum()
        if "approval_status" in df.columns
        else 0
    )

    cards = {
        "Packages Requiring Attention": {
            "count": int(c1),
            "percentage": pct(int(c1)),
            "status": "Attention",
        },
        "Critical and High Risk": {
            "count": int(c2),
            "percentage": pct(int(c2)),
            "status": "Risk",
        },
        "Ready for Management Review": {
            "count": int(c3),
            "percentage": pct(int(c3)),
            "status": "Ready",
        },
        "Ready with Conditions": {
            "count": int(c4),
            "percentage": pct(int(c4)),
            "status": "Conditional",
        },
        "Monitoring Only": {
            "count": int(c5),
            "percentage": pct(int(c5)),
            "status": "Monitoring",
        },
        "Pending Management Review": {
            "count": int(c6),
            "percentage": pct(int(c6)),
            "status": "Pending",
        },
    }
    log_event("CARDS_BUILT", f"total={total}")
    return cards
