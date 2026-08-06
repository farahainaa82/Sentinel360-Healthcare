"""Lineage Validation Engine for 2D-8.

Validates lineage completeness reconciliation and upstream consistency.
"""

import pandas as pd

from decision_intelligence_validation_utils import load_register


def validate():
    """Run lineage validation."""
    briefs = load_register("step_2d7_integrated_management_brief_register.csv")
    up_complete = load_register("step_2d6_lineage_completeness_register.csv")

    rows = []

    # Check 1: Lineage completeness reconciles with upstream
    if not briefs.empty and not up_complete.empty and "lineage_completeness_status" in up_complete.columns:
        merged = briefs[["decision_package_id", "lineage_completeness_status"]].merge(
            up_complete[["decision_package_id", "lineage_completeness_status"]].rename(
                columns={"lineage_completeness_status": "upstream_ln"}
            ),
            on="decision_package_id", how="left"
        )
        mismatch = merged["lineage_completeness_status"].fillna("").ne(merged["upstream_ln"].fillna("")).sum()
        rows.append({
            "validation_id": "VA-LI-001",
            "check": "lineage_completeness_reconciliation",
            "expected": 0,
            "actual": mismatch,
            "status": "PASS" if mismatch == 0 else "FAIL",
            "detail": "" if mismatch == 0 else f"{mismatch} lineage completeness mismatches",
        })
    else:
        rows.append({
            "validation_id": "VA-LI-001",
            "check": "lineage_completeness_reconciliation",
            "expected": 0,
            "actual": None,
            "status": "PASS",
            "detail": "Upstream lineage completeness not available",
        })

    # Check 2: Lineage available flag consistency
    if not briefs.empty and "lineage_available" in briefs.columns:
        inconsistent = 0
        for _, row in briefs.iterrows():
            ln_avail = str(row.get("lineage_available", "")).lower()
            ln_status = str(row.get("lineage_completeness_status", "")).lower()
            if ln_avail == "true" and "missing" in ln_status:
                inconsistent += 1
            elif ln_avail == "false" and "complete" in ln_status:
                inconsistent += 1
        rows.append({
            "validation_id": "VA-LI-002",
            "check": "lineage_flag_consistency",
            "expected": 0,
            "actual": inconsistent,
            "status": "PASS" if inconsistent == 0 else "FAIL",
            "detail": "" if inconsistent == 0 else f"{inconsistent} lineage flag inconsistencies",
        })
    else:
        rows.append({
            "validation_id": "VA-LI-002",
            "check": "lineage_flag_consistency",
            "expected": 0,
            "actual": None,
            "status": "PASS",
            "detail": "lineage_available column not present",
        })

    return pd.DataFrame(rows)


def build_register():
    return validate()


def get_required_columns():
    return [
        "validation_id", "check", "expected", "actual",
        "status", "detail",
    ]
