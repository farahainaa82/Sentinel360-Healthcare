"""
streamlit_executive_priority_engine.py
Primary package selection and operational status derivation.
"""

from typing import Dict, Optional

import pandas as pd

from .streamlit_executive_logging import log_event


def select_primary_package(risk_df: pd.DataFrame) -> Dict:
    """Select one primary package using rule-based ranking.

    Priority:
    1. Latest date in the filtered period (to avoid stale data)
    2. operational escalation (non-No Escalation first)
    3. risk tier (highest numeric)
    4. urgency (Immediate Review > Prompt Review > Standard > Routine)
    5. breach severity (Red > Amber > Green)
    6. sustained deterioration
    7. management attention level
    8. readiness
    9. evidence completeness
    """
    if risk_df.empty:
        return {}

    df = risk_df.copy()

    # 0. Date score — prefer latest date to avoid stale data
    if "reporting_date" in df.columns:
        df["date_score"] = pd.to_datetime(df["reporting_date"], errors="coerce").astype("int64")
    else:
        df["date_score"] = 0

    # 1. Escalation score
    df["escalation_score"] = (
        df["operational_escalation"]
        .astype(str)
        .str.strip()
        .str.lower()
        .ne("no escalation")
        .astype(int)
    )

    # 2. Risk tier numeric
    if "risk_tier_num" in df.columns:
        df["risk_score"] = df["risk_tier_num"].fillna(0)
    elif "risk_tier" in df.columns:
        df["risk_score"] = pd.to_numeric(df["risk_tier"], errors="coerce").fillna(0)
    else:
        df["risk_score"] = 0

    # 3. Urgency order
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

    # 4. Breach severity from dominant_breach text
    def _breach_score(text):
        if pd.isna(text):
            return 0
        t = str(text).lower()
        if "red breach" in t:
            return 3
        if "amber condition" in t:
            return 2
        if "green" in t:
            return 1
        return 0

    if "dominant_breach" in df.columns:
        df["breach_score"] = df["dominant_breach"].apply(_breach_score)
    else:
        df["breach_score"] = 0

    # 5. Management attention
    attention_order = {
        "Immediate Action": 1,
        "Conditional Review": 2,
        "Standard Management Review": 3,
        "Monitoring": 4,
        "Non-Quantitative Review": 5,
    }
    if "management_attention" in df.columns:
        df["attention_order"] = df["management_attention"].map(attention_order).fillna(99)
    else:
        df["attention_order"] = 99

    # Sort by priority — LATEST DATE FIRST, then escalation, risk, urgency, breach, attention
    df = df.sort_values(
        by=["date_score", "escalation_score", "risk_score", "urgency_order", "breach_score", "attention_order"],
        ascending=[False, False, False, True, False, True],
    )

    if df.empty:
        return {}

    top = df.iloc[0]
    pkg = {
        "decision_package_id": str(top.get("decision_package_id", "")),
        "hospital_id": str(top.get("hospital_id", "")),
        "hospital_name": str(top.get("hospital_name", "")),
        "department_id": str(top.get("department_id", "")),
        "department_name": str(top.get("department_name", "")),
        "affected_department": str(top.get("affected_department", "")),
        "dominant_kpi_name": str(top.get("dominant_kpi_name", "")),
        "dominant_kpi_id": str(top.get("dominant_kpi_id", "")),
        "risk_tier": str(top.get("risk_tier", "")),
        "urgency": str(top.get("urgency", "")),
        "operational_escalation": str(top.get("operational_escalation", "")),
        "management_attention": str(top.get("management_attention", "")),
        "dominant_breach": str(top.get("dominant_breach", "")),
        "contributing_factors": str(top.get("contributing_factors", "")),
        "reporting_date": top.get("reporting_date"),
    }
    log_event("PRIMARY_PACKAGE_SELECTED", pkg["decision_package_id"])
    return pkg


def derive_operational_status(pkg: Optional[Dict]) -> str:
    """Derive operational status from primary package fields."""
    if not pkg:
        return "NOT ASSESSABLE"

    escalation = str(pkg.get("operational_escalation", "")).strip().lower()
    if escalation and escalation != "no escalation":
        return "HIGH OPERATIONAL PRESSURE"

    risk = pkg.get("risk_tier", "")
    try:
        risk_num = float(risk)
    except (ValueError, TypeError):
        risk_num = 0

    urgency = str(pkg.get("urgency", "")).strip()
    attention = str(pkg.get("management_attention", "")).strip().lower()

    if risk_num >= 70 or urgency == "Immediate Review":
        return "HIGH OPERATIONAL PRESSURE"
    if risk_num >= 50 or urgency == "Prompt Review":
        return "MATERIAL OPERATIONAL PRESSURE"
    if "conditional" in attention:
        return "CONDITIONAL MANAGEMENT REVIEW"
    if attention == "monitoring":
        return "MONITORING REQUIRED"
    if risk_num > 0:
        return "NO CURRENT HIGH-PRIORITY ALERT"

    return "NOT ASSESSABLE"
