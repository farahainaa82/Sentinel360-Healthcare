"""Management priority view engine for Step 2D-7."""

import pandas as pd


def create_priority_view(briefs_df):
    """Create management-priority register from briefs."""
    cols = [
        "integrated_management_brief_id",
        "decision_package_id",
        "hospital_name",
        "department_name",
        "dominant_kpi_name",
        "risk_tier",
        "urgency",
        "management_attention_level",
        "final_readiness_status",
        "primary_permitted_action",
        "main_blocking_condition",
        "top_management_questions",
        "central_financial_estimate",
        "financial_confidence",
        "evidence_completeness_status",
        "lineage_completeness_status",
        "approval_status"
    ]
    available = [c for c in cols if c in briefs_df.columns]
    pv = briefs_df[available].copy()
    # Ordering: operational_escalation, risk_tier, urgency, breach, sustained, management_attention
    sort_cols = []
    if "operational_escalation_status" in pv.columns:
        sort_cols.append("operational_escalation_status")
    if "risk_tier" in pv.columns:
        sort_cols.append("risk_tier")
    if "urgency" in pv.columns:
        sort_cols.append("urgency")
    if sort_cols:
        pv = pv.sort_values(by=sort_cols, ascending=False)
    return pv
