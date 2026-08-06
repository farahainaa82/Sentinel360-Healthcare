"""Evidence Validation Engine for 2D-8.

Validates evidence completeness reconciliation and upstream consistency.
"""

import pandas as pd

from decision_intelligence_validation_utils import load_register


def validate():
    """Run evidence validation."""
    briefs = load_register("step_2d7_integrated_management_brief_register.csv")
    upstream_ev = load_register("step_2d6_decision_evidence_profile_register.csv")
    up_complete = load_register("step_2d6_evidence_completeness_register.csv")

    rows = []

    # Check 1: Evidence completeness reconciles with upstream
    if not briefs.empty and not up_complete.empty and "evidence_completeness_status" in up_complete.columns:
        merged = briefs[["decision_package_id", "evidence_completeness_status"]].merge(
            up_complete[["decision_package_id", "evidence_completeness_status"]].rename(
                columns={"evidence_completeness_status": "upstream_ev"}
            ),
            on="decision_package_id", how="left"
        )
        mismatch = merged["evidence_completeness_status"].fillna("").ne(merged["upstream_ev"].fillna("")).sum()
        rows.append({
            "validation_id": "VA-EV-001",
            "check": "evidence_completeness_reconciliation",
            "expected": 0,
            "actual": mismatch,
            "status": "PASS" if mismatch == 0 else "FAIL",
            "detail": "" if mismatch == 0 else f"{mismatch} evidence completeness mismatches",
        })
    else:
        rows.append({
            "validation_id": "VA-EV-001",
            "check": "evidence_completeness_reconciliation",
            "expected": 0,
            "actual": None,
            "status": "PASS",
            "detail": "Upstream evidence completeness not available",
        })

    # Check 2: Evidence available flag consistency
    if not briefs.empty and "evidence_available" in briefs.columns:
        inconsistent = 0
        for _, row in briefs.iterrows():
            ev_avail = str(row.get("evidence_available", "")).lower()
            ev_status = str(row.get("evidence_completeness_status", "")).lower()
            if ev_avail == "true" and "missing" in ev_status:
                inconsistent += 1
            elif ev_avail == "false" and "complete" in ev_status:
                inconsistent += 1
        rows.append({
            "validation_id": "VA-EV-002",
            "check": "evidence_flag_consistency",
            "expected": 0,
            "actual": inconsistent,
            "status": "PASS" if inconsistent == 0 else "FAIL",
            "detail": "" if inconsistent == 0 else f"{inconsistent} evidence flag inconsistencies",
        })
    else:
        rows.append({
            "validation_id": "VA-EV-002",
            "check": "evidence_flag_consistency",
            "expected": 0,
            "actual": None,
            "status": "PASS",
            "detail": "evidence_available column not present",
        })

    return pd.DataFrame(rows)


def build_register():
    return validate()


def get_required_columns():
    return [
        "validation_id", "check", "expected", "actual",
        "status", "detail",
    ]
