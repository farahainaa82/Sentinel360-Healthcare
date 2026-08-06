"""Monitoring and Escalation Validation Engine for 2D-8.

Validates monitoring triggers, escalation status, and condition definitions.
"""

import pandas as pd

from decision_intelligence_validation_utils import load_register


def validate():
    """Run monitoring validation."""
    monitoring = load_register("step_2d7_monitoring_and_escalation_summary_register.csv")
    briefs = load_register("step_2d7_integrated_management_brief_register.csv")

    rows = []

    if monitoring.empty:
        return pd.DataFrame({
            "validation_id": ["VA-MO-001"],
            "check": ["register_loaded"],
            "status": ["FAIL"],
            "detail": ["Monitoring register empty"],
        })

    # Check 1: Monitoring packages have trigger condition
    if not briefs.empty and "final_readiness_status" in briefs.columns:
        mon_ids = briefs[briefs["final_readiness_status"] == "Monitoring Only"]["decision_package_id"].tolist()
        if mon_ids and "trigger_condition" in monitoring.columns:
            mon_rows = monitoring[monitoring["decision_package_id"].isin(mon_ids)]
            missing = mon_rows["trigger_condition"].isna().sum()
            rows.append({
                "validation_id": "VA-MO-001",
                "check": "monitoring_trigger_present",
                "expected": 0,
                "actual": missing,
                "status": "PASS" if missing == 0 else "FAIL",
                "detail": "" if missing == 0 else f"{missing} monitoring packages lack trigger_condition",
            })
        else:
            rows.append({
                "validation_id": "VA-MO-001",
                "check": "monitoring_trigger_present",
                "expected": 0,
                "actual": None,
                "status": "PASS",
                "detail": "No monitoring packages or trigger_condition column missing",
            })
    else:
        rows.append({
            "validation_id": "VA-MO-001",
            "check": "monitoring_trigger_present",
            "expected": 0,
            "actual": None,
            "status": "PASS",
            "detail": "Brief register unavailable",
        })

    # Check 2: Escalation status consistency
    if "escalation_status" in monitoring.columns:
        valid_statuses = ["No Escalation", "Executive Escalation Required", "Clinical Escalation Required", ""]
        invalid = ~monitoring["escalation_status"].fillna("").isin(valid_statuses)
        count = invalid.sum()
        rows.append({
            "validation_id": "VA-MO-002",
            "check": "escalation_status_valid",
            "expected": 0,
            "actual": count,
            "status": "PASS" if count == 0 else "FAIL",
            "detail": "" if count == 0 else f"{count} invalid escalation statuses",
        })
    else:
        rows.append({
            "validation_id": "VA-MO-002",
            "check": "escalation_status_valid",
            "expected": 0,
            "actual": None,
            "status": "PASS",
            "detail": "escalation_status column not present",
        })

    return pd.DataFrame(rows)


def build_register():
    return validate()


def get_required_columns():
    return [
        "validation_id", "check", "expected", "actual",
        "status", "detail",
    ]
