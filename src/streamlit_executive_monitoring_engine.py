"""
streamlit_executive_monitoring_engine.py
Monitoring and validation watchlist engine.
"""

from typing import Dict, List
import pandas as pd

from .streamlit_executive_logging import log_event


def build_monitoring_watchlist(
    exec_df: pd.DataFrame,
    mon_df: pd.DataFrame,
) -> List[Dict]:
    if exec_df.empty:
        return []
    sub = exec_df[exec_df["readiness_status"] == "Monitoring Only"]
    if sub.empty:
        return []
    if not mon_df.empty and "decision_package_id" in mon_df.columns:
        sub = sub.merge(
            mon_df[["decision_package_id", "monitoring_kpis", "monitoring_responsible_role", "escalation_required"]],
            on="decision_package_id",
            how="left",
        )
    records: List[Dict] = []
    for _, row in sub.iterrows():
        records.append(
            {
                "department": str(row.get("department_name", "")),
                "kpi": str(row.get("dominant_kpi_name", "")),
                "current_condition": str(row.get("readiness_status", "")),
                "watch_status": "Watch",
                "escalation_trigger": str(row.get("escalation_required", "")),
                "reassessment_condition": "",
            }
        )
    log_event("MONITORING_WATCHLIST_BUILT", f"count={len(records)}")
    return records


def build_validation_watchlist(exec_df: pd.DataFrame) -> List[Dict]:
    if exec_df.empty:
        return []
    validation_statuses = {
        "Requires Assumption Validation",
        "Requires Baseline Validation",
        "Requires Financial Input",
        "Requires Stakeholder Validation",
        "Requires Evidence Completion",
        "Requires Lineage Completion",
    }
    sub = exec_df[exec_df["readiness_status"].isin(validation_statuses)]
    records: List[Dict] = []
    for _, row in sub.iterrows():
        records.append(
            {
                "department": str(row.get("department_name", "")),
                "kpi": str(row.get("dominant_kpi_name", "")),
                "current_condition": str(row.get("readiness_status", "")),
                "required_validation": str(row.get("readiness_status", "")),
                "responsible_role": "",
                "primary_queue": str(row.get("primary_queue", "")),
                "urgency": str(row.get("urgency", "")),
            }
        )
    log_event("VALIDATION_WATCHLIST_BUILT", f"count={len(records)}")
    return records
