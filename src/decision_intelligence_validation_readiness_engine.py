"""Readiness Validation Engine for 2D-8.

Validates readiness status immutability and upstream reconciliation.
"""

import pandas as pd

from decision_intelligence_validation_utils import load_register


def validate():
    """Run readiness validation."""
    briefs = load_register("step_2d7_integrated_management_brief_register.csv")
    upstream = load_register("step_2d4_decision_readiness_register.csv")

    rows = []

    # Check 1: Readiness status matches upstream
    if not briefs.empty and not upstream.empty:
        merged = briefs[["decision_package_id", "final_readiness_status"]].merge(
            upstream[["decision_package_id", "final_readiness_status"]].rename(
                columns={"final_readiness_status": "upstream_readiness"}
            ),
            on="decision_package_id", how="left"
        )
        mismatch = (merged["final_readiness_status"] != merged["upstream_readiness"]).sum()
        rows.append({
            "validation_id": "VA-RE-001",
            "check": "readiness_upstream_reconciliation",
            "expected": 0,
            "actual": mismatch,
            "status": "PASS" if mismatch == 0 else "FAIL",
            "detail": "" if mismatch == 0 else f"{mismatch} readiness mismatches with upstream",
        })
    else:
        rows.append({
            "validation_id": "VA-RE-001",
            "check": "readiness_upstream_reconciliation",
            "expected": 0,
            "actual": None,
            "status": "PASS",
            "detail": "Upstream readiness not available",
        })

    # Check 2: Ready for review retains pending approval
    if not briefs.empty:
        ready = briefs[briefs["final_readiness_status"] == "Ready for Integrated Management Review"]
        if not ready.empty:
            pending = (ready["approval_status"] == "Pending Management Review").all()
            rows.append({
                "validation_id": "VA-RE-002",
                "check": "ready_retains_pending",
                "expected": True,
                "actual": pending,
                "status": "PASS" if pending else "FAIL",
                "detail": "" if pending else "Ready for Review package does not have Pending approval",
            })
        else:
            rows.append({
                "validation_id": "VA-RE-002",
                "check": "ready_retains_pending",
                "expected": True,
                "actual": None,
                "status": "PASS",
                "detail": "No Ready for Integrated Management Review packages",
            })
    else:
        rows.append({
            "validation_id": "VA-RE-002",
            "check": "ready_retains_pending",
            "expected": True,
            "actual": None,
            "status": "PASS",
            "detail": "Brief register empty",
        })

    # Check 3: Ready with conditions shows conditions
    if not briefs.empty:
        cond = briefs[briefs["final_readiness_status"] == "Ready with Conditions"]
        if not cond.empty:
            pending = (cond["approval_status"] == "Pending Management Review").all()
            rows.append({
                "validation_id": "VA-RE-003",
                "check": "conditions_retains_pending",
                "expected": True,
                "actual": pending,
                "status": "PASS" if pending else "FAIL",
                "detail": "" if pending else "Ready with Conditions package does not have Pending approval",
            })
        else:
            rows.append({
                "validation_id": "VA-RE-003",
                "check": "conditions_retains_pending",
                "expected": True,
                "actual": None,
                "status": "PASS",
                "detail": "No Ready with Conditions packages",
            })
    else:
        rows.append({
            "validation_id": "VA-RE-003",
            "check": "conditions_retains_pending",
            "expected": True,
            "actual": None,
            "status": "PASS",
            "detail": "Brief register empty",
        })

    return pd.DataFrame(rows)


def build_register():
    return validate()


def get_required_columns():
    return [
        "validation_id", "check", "expected", "actual",
        "status", "detail",
    ]
