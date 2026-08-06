"""Brief Type Validation Engine for 2D-8.

Validates brief type reconciliation with readiness status and consistency.
"""

import pandas as pd

from decision_intelligence_validation_utils import load_register


def validate():
    """Run brief type validation."""
    briefs = load_register("step_2d7_integrated_management_brief_register.csv")
    types = load_register("step_2d7_management_brief_type_register.csv")

    rows = []

    if briefs.empty:
        return pd.DataFrame({
            "validation_id": ["VA-TY-001"],
            "check": ["register_loaded"],
            "status": ["FAIL"],
            "detail": ["Brief register empty"],
        })

    # Check 1: Brief type reconciles with readiness
    mapping = {
        "Ready for Integrated Management Review": "Integrated Management Review Brief",
        "Ready with Conditions": "Conditional Management Review Brief",
        "Monitoring Only": "Monitoring Brief",
        "Non-Quantitative": "Non-Quantitative Review Brief",
        "Not Suitable": "Not Suitable Brief",
        "Rejected": "Rejected Brief",
        "Requires Assumption Validation": "Assumption Validation Brief",
        "Requires Baseline Validation": "Baseline Validation Brief",
        "Requires Financial Input": "Financial Input Brief",
        "Requires Benefit Validation": "Benefit Validation Brief",
        "Requires Budget Information": "Budget Information Brief",
        "Requires Stakeholder Validation": "Stakeholder Validation Brief",
        "Requires Additional Scenario": "Additional Scenario Brief",
        "Requires Evidence Completion": "Evidence Completion Brief",
        "Requires Lineage Completion": "Lineage Completion Brief",
    }

    mismatches = 0
    mismatch_detail = []
    for _, row in briefs.iterrows():
        expected = mapping.get(row["final_readiness_status"], "Integrated Management Review Brief")
        if row.get("brief_type", "") != expected:
            mismatches += 1
            if len(mismatch_detail) < 5:
                mismatch_detail.append(f"{row['decision_package_id']}: expected {expected}, got {row.get('brief_type', '')}")

    rows.append({
        "validation_id": "VA-TY-001",
        "check": "brief_type_reconciles_with_readiness",
        "expected": 0,
        "actual": mismatches,
        "status": "PASS" if mismatches == 0 else "FAIL",
        "detail": "; ".join(mismatch_detail) if mismatch_detail else "",
    })

    # Check 2: Type register row count
    if not types.empty:
        count_ok = len(types) == len(briefs)
        rows.append({
            "validation_id": "VA-TY-002",
            "check": "type_register_row_count",
            "expected": len(briefs),
            "actual": len(types),
            "status": "PASS" if count_ok else "FAIL",
            "detail": "" if count_ok else f"Expected {len(briefs)}, got {len(types)}",
        })
    else:
        rows.append({
            "validation_id": "VA-TY-002",
            "check": "type_register_row_count",
            "expected": len(briefs),
            "actual": 0,
            "status": "FAIL",
            "detail": "Type register empty",
        })

    return pd.DataFrame(rows)


def build_register():
    return validate()


def get_required_columns():
    return [
        "validation_id", "check", "expected", "actual",
        "status", "detail",
    ]
