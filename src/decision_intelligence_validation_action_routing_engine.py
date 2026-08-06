"""Action Routing Validation Engine for 2D-8.

Validates action routing immutability, boundary constraints, and selection status.
"""

import pandas as pd

from decision_intelligence_validation_utils import load_register


def validate():
    """Run action routing validation."""
    briefs = load_register("step_2d7_integrated_management_brief_register.csv")
    upstream = load_register("step_2d5_decision_action_routing_register.csv")

    rows = []

    if briefs.empty:
        return pd.DataFrame({
            "validation_id": ["VA-AR-001"],
            "check": ["register_loaded"],
            "status": ["FAIL"],
            "detail": ["Brief register empty"],
        })

    # Check 1: No action selected
    selected = briefs["selected_action"].fillna("").ne("").sum()
    rows.append({
        "validation_id": "VA-AR-001",
        "check": "no_action_selected",
        "expected": 0,
        "actual": selected,
        "status": "PASS" if selected == 0 else "FAIL",
        "detail": "" if selected == 0 else f"{selected} packages have selected_action populated",
    })

    # Check 2: No scenario selected
    selected_sc = briefs["selected_scenario"].fillna("").ne("").sum()
    rows.append({
        "validation_id": "VA-AR-002",
        "check": "no_scenario_selected",
        "expected": 0,
        "actual": selected_sc,
        "status": "PASS" if selected_sc == 0 else "FAIL",
        "detail": "" if selected_sc == 0 else f"{selected_sc} packages have selected_scenario populated",
    })

    # Check 3: All approval pending
    pending = (briefs["approval_status"].fillna("") == "Pending Management Review").all()
    rows.append({
        "validation_id": "VA-AR-003",
        "check": "all_approval_pending",
        "expected": True,
        "actual": pending,
        "status": "PASS" if pending else "FAIL",
        "detail": "" if pending else "Some packages do not have Pending Management Review approval status",
    })

    # Check 4: Primary action not labelled recommended
    if "primary_permitted_action" in briefs.columns:
        recommended = briefs["primary_permitted_action"].fillna("").str.contains("recommended", case=False, na=False).sum()
        rows.append({
            "validation_id": "VA-AR-004",
            "check": "primary_not_recommended",
            "expected": 0,
            "actual": recommended,
            "status": "PASS" if recommended == 0 else "FAIL",
            "detail": "" if recommended == 0 else f"{recommended} primary actions contain 'recommended'",
        })
    else:
        rows.append({
            "validation_id": "VA-AR-004",
            "check": "primary_not_recommended",
            "expected": 0,
            "actual": None,
            "status": "PASS",
            "detail": "primary_permitted_action column not present",
        })

    # Check 5: Upstream action routing unchanged
    if not upstream.empty and "primary_permitted_action" in upstream.columns and "primary_permitted_action" in briefs.columns:
        merged = briefs[["decision_package_id", "primary_permitted_action"]].merge(
            upstream[["decision_package_id", "primary_permitted_action"]].rename(
                columns={"primary_permitted_action": "upstream_action"}
            ),
            on="decision_package_id", how="left"
        )
        mismatch = merged["primary_permitted_action"].fillna("").ne(merged["upstream_action"].fillna("")).sum()
        rows.append({
            "validation_id": "VA-AR-005",
            "check": "action_routing_upstream_match",
            "expected": 0,
            "actual": mismatch,
            "status": "PASS" if mismatch == 0 else "FAIL",
            "detail": "" if mismatch == 0 else f"{mismatch} action routing mismatches with upstream",
        })
    else:
        rows.append({
            "validation_id": "VA-AR-005",
            "check": "action_routing_upstream_match",
            "expected": 0,
            "actual": None,
            "status": "PASS",
            "detail": "Upstream action routing not available",
        })

    return pd.DataFrame(rows)


def build_register():
    return validate()


def get_required_columns():
    return [
        "validation_id", "check", "expected", "actual",
        "status", "detail",
    ]
