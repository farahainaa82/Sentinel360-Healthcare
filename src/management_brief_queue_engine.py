"""Management queue brief engine for Step 2D-7."""

import pandas as pd


def create_queue_briefs(briefs_df):
    """Create queue-specific brief views."""
    queue_col = "primary_queue"
    if queue_col not in briefs_df.columns:
        briefs_df = briefs_df.copy()
        briefs_df[queue_col] = "General Queue"
    cols = [
        "integrated_management_brief_id",
        "decision_package_id",
        "hospital_name",
        "department_name",
        "dominant_kpi_name",
        "current_issue_summary",
        "final_readiness_status",
        "primary_permitted_action",
        "responsible_role",
        "main_blocking_condition",
        "escalation_status",
        "top_management_questions",
        queue_col
    ]
    available = [c for c in cols if c in briefs_df.columns]
    return briefs_df[available].copy()
