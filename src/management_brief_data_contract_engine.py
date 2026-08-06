"""Streamlit management brief data contract engine for Step 2D-7."""

import pandas as pd


def create_streamlit_contract(briefs_df):
    """Create Streamlit-ready management brief data contract."""
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
        "approval_status",
        "brief_title",
        "executive_headline",
        "current_issue_summary",
        "why_it_matters",
        "representative_recommendation",
        "immediate_action_option",
        "near_term_action_option",
        "preventive_action_option",
        "baseline_summary",
        "conservative_summary",
        "expected_summary",
        "higher_intensity_summary",
        "main_tradeoff",
        "displacement_risk",
        "estimated_scenario_cost",
        "estimated_financial_benefit",
        "estimated_net_financial_impact",
        "lower_financial_estimate",
        "central_financial_estimate",
        "upper_financial_estimate",
        "financial_confidence",
        "affordability_status",
        "main_blocking_condition",
        "top_secondary_conditions",
        "failed_gates",
        "required_resolution",
        "primary_permitted_action",
        "secondary_permitted_actions",
        "escalation_status",
        "monitoring_required",
        "top_management_questions",
        "blocking_question_count",
        "causality_status",
        "provisional_warning",
        "contradiction_warning",
        "evidence_completeness_status",
        "lineage_completeness_status",
        "future_audit_status"
    ]
    available = [c for c in cols if c in briefs_df.columns]
    contract = briefs_df[available].copy()
    contract["display_colour"] = "grey"
    contract["display_icon"] = "clock"
    contract["display_priority"] = 1
    return contract
