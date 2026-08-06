"""
streamlit_executive_narrative_engine.py
Executive narrative and health summary.
"""

from typing import Dict, Optional

import pandas as pd

from .streamlit_executive_logging import log_event


def build_health_summary(
    exec_df: pd.DataFrame,
    risk_df: pd.DataFrame,
) -> str:
    if exec_df.empty:
        return "No data available for summary."
    total = len(exec_df)
    crit_high = 0
    if "risk_tier" in exec_df.columns:
        try:
            crit_high = int((pd.to_numeric(exec_df["risk_tier"], errors="coerce") >= 70).sum())
        except Exception:
            crit_high = 0
    ready = 0
    if "readiness_status" in exec_df.columns:
        ready = int(
            (exec_df["readiness_status"] == "Ready for Integrated Management Review").sum()
        )
    blocked = 0
    if "readiness_status" in exec_df.columns:
        blocked = int(
            exec_df["readiness_status"]
            .astype(str)
            .isin(
                {
                    "Requires Assumption Validation",
                    "Requires Evidence Completion",
                    "Requires Lineage Completion",
                    "Requires Additional Scenario Analysis",
                }
            )
            .sum()
        )
    dept_pressure = ""
    if "department_name" in exec_df.columns and crit_high > 0:
        depts = (
            exec_df[pd.to_numeric(exec_df["risk_tier"], errors="coerce") >= 70]["department_name"]
            .dropna()
            .unique()
        )
        if len(depts) > 0:
            dept_pressure = ", ".join(str(d) for d in depts[:3])
    parts = [
        f"Operational pressure is concentrated in {dept_pressure or 'multiple departments'}",
        f"with {crit_high} Critical or High-risk packages.",
        f"{ready} packages are ready for review,",
        f"while {blocked} require further validation or conditions before progression.",
    ]
    summary = " ".join(parts)
    words = summary.split()
    if len(words) > 80:
        summary = " ".join(words[:80]) + "."
    log_event("HEALTH_SUMMARY_BUILT", f"words={len(words)}")
    return summary


def build_executive_narrative(pkg: Optional[Dict], exec_df: pd.DataFrame) -> str:
    """Build a concise 55-word max narrative for the priority banner."""
    if pkg is None or not pkg:
        return "No governed narrative available for the current selection."

    dept = str(pkg.get("affected_department", pkg.get("department_name", ""))).strip()
    kpi = str(pkg.get("dominant_kpi_name", "")).strip()
    attention = str(pkg.get("management_attention", "")).strip()
    urgency = str(pkg.get("urgency", "")).strip()
    escalation = str(pkg.get("operational_escalation", "")).strip()

    # Find related KPIs from contributing_factors
    related = []
    cf = str(pkg.get("contributing_factors", "")).strip()
    if cf and cf.lower() != "nan":
        parts = cf.split(" may be associated with ")
        if len(parts) == 2:
            related = [parts[0].strip(), parts[1].strip()]

    related_text = ""
    if related:
        related_text = f" {', '.join(related[:2])} indicators appear alongside this signal."

    # Build narrative with cautious wording
    verb = "requires" if (kpi and not kpi.endswith("s")) else "require"
    narrative = (
        f"{kpi or 'Operational signals'} {verb} management attention in {dept or 'the selected department'}."
        f"{related_text}"
        f" Urgency is {urgency or 'under review'}."
    )

    words = narrative.split()
    if len(words) > 55:
        narrative = " ".join(words[:55]) + "."
    log_event("NARRATIVE_BUILT", f"words={len(words)}")
    return narrative
