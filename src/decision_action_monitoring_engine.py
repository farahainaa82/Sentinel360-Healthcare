"""
decision_action_monitoring_engine.py
Phase 2D-5 — Monitoring action model.
"""

import pandas as pd
import uuid
from typing import List, Dict


def build_monitoring_records(routing_df: pd.DataFrame) -> pd.DataFrame:
    """Create monitoring action records for all routing packages."""
    records = []
    for _, row in routing_df.iterrows():
        routing_id = row["decision_action_routing_id"]
        status = row["final_readiness_status"]
        package_id = row["decision_package_id"]
        kpi = row.get("dominant_kpi_name", "General Monitoring")

        monitoring_required = status in (
            "Monitoring Only",
            "Ready with Conditions",
            "Ready for Integrated Management Review",
            "Requires Assumption Validation",
        )

        records.append({
            "monitoring_action_id": f"MON-{uuid.uuid4().hex[:8].upper()}",
            "decision_action_routing_id": routing_id,
            "decision_package_id": package_id,
            "monitoring_required": monitoring_required,
            "monitoring_kpi": kpi,
            "monitoring_frequency": "Monthly" if monitoring_required else "Not Applicable",
            "trigger_condition": "KPI threshold breach" if monitoring_required else "Not Applicable",
            "escalation_condition": "Sustained threshold breach > 2 periods" if monitoring_required else "Not Applicable",
            "reassessment_condition": "Quarterly review" if monitoring_required else "Not Applicable",
            "responsible_role": "Operations Manager",
            "reporting_requirement": "Standard monitoring report" if monitoring_required else "Not Applicable",
            "current_status": "Pending Setup",
            "governance_note": "Prototype default - Pending Setup",
        })

    return pd.DataFrame(records)
