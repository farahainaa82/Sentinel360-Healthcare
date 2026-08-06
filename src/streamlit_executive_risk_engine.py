"""
streamlit_executive_risk_engine.py
Top risks and alerts engine.
"""

from typing import List, Dict
import pandas as pd

from .streamlit_executive_logging import log_event


def build_top_risks(risk_df: pd.DataFrame, top_n: int = 10) -> List[Dict]:
    if risk_df.empty:
        return []
    df = risk_df.copy()
    # Operational escalation first
    if "operational_escalation" in df.columns:
        df["escalation_score"] = (
            df["operational_escalation"]
            .astype(str)
            .str.contains("Escalation", case=False, na=False)
            .astype(int)
        )
    else:
        df["escalation_score"] = 0
    # Risk tier numeric desc
    if "risk_tier" in df.columns:
        df["risk_tier_num"] = pd.to_numeric(df["risk_tier"], errors="coerce").fillna(0)
    else:
        df["risk_tier_num"] = 0
    # Urgency mapping
    urgency_order = {
        "Immediate Review": 1,
        "Prompt Review": 2,
        "Standard Management Review": 3,
        "Routine": 4,
    }
    if "urgency" in df.columns:
        df["urgency_order"] = df["urgency"].map(urgency_order).fillna(99)
    else:
        df["urgency_order"] = 99
    # Breach severity
    if "dominant_breach" in df.columns:
        df["breach_score"] = (
            df["dominant_breach"]
            .astype(str)
            .str.contains("Red|Critical", case=False, na=False)
            .astype(int)
        )
    else:
        df["breach_score"] = 0
    df = df.sort_values(
        by=["escalation_score", "risk_tier_num", "urgency_order", "breach_score"],
        ascending=[False, False, True, False],
    )
    top = df.head(top_n)
    records: List[Dict] = []
    for _, row in top.iterrows():
        records.append(
            {
                "hospital": str(row.get("hospital_name", "")),
                "department": str(row.get("affected_department", "")),
                "dominant_kpi": str(row.get("dominant_kpi_name", "")),
                "risk_tier": str(row.get("risk_tier", "")),
                "urgency": str(row.get("urgency", "")),
                "management_attention": str(row.get("management_attention", "")),
                "readiness": "",
                "primary_queue": str(row.get("primary_queue", "")),
                "main_warning": str(row.get("dominant_breach", "")),
                "reporting_date": str(row.get("reporting_date", "")),
            }
        )
    log_event("TOP_RISKS_BUILT", f"top_n={top_n} returned={len(records)}")
    return records
