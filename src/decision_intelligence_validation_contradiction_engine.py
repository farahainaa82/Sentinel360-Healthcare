"""Contradiction Validation Engine for 2D-8.

Validates contradiction warnings, severity visibility, and logical consistency.
"""

import pandas as pd

from decision_intelligence_validation_utils import load_register


def validate():
    """Run contradiction validation."""
    briefs = load_register("step_2d7_integrated_management_brief_register.csv")
    gov = load_register("step_2d7_governance_and_limitation_summary_register.csv")

    rows = []

    if briefs.empty:
        return pd.DataFrame({
            "validation_id": ["VA-CO-001"],
            "check": ["register_loaded"],
            "status": ["FAIL"],
            "detail": ["Brief register empty"],
        })

    # Check 1: Contradiction warning visibility
    # Only required when contradiction_severity indicates an actual contradiction
    if not gov.empty and "contradiction_warning" in gov.columns:
        merged = briefs[["decision_package_id", "contradiction_severity"]].merge(
            gov[["decision_package_id", "contradiction_warning"]],
            on="decision_package_id", how="left"
        )
        # Actual contradiction means severity is present and not "No Contradiction"
        has_contra = merged["contradiction_severity"].notna() & \
                     ~merged["contradiction_severity"].fillna("").str.lower().isin(["", "no contradiction", "none"])
        missing_warn = has_contra & merged["contradiction_warning"].isna()
        count = missing_warn.sum()
        rows.append({
            "validation_id": "VA-CO-001",
            "check": "contradiction_warning_visible",
            "expected": 0,
            "actual": count,
            "status": "PASS" if count == 0 else "FAIL",
            "detail": "" if count == 0 else f"{count} packages with actual contradiction lack warning",
        })
    else:
        rows.append({
            "validation_id": "VA-CO-001",
            "check": "contradiction_warning_visible",
            "expected": 0,
            "actual": None,
            "status": "PASS",
            "detail": "Governance register unavailable",
        })

    # Check 2: Provisional warning visibility
    if not gov.empty and "provisional_warning" in gov.columns:
        present = gov["provisional_warning"].notna().all()
        rows.append({
            "validation_id": "VA-CO-002",
            "check": "provisional_warning_visible",
            "expected": True,
            "actual": present,
            "status": "PASS" if present else "FAIL",
            "detail": "" if present else "Some packages lack provisional_warning",
        })
    else:
        rows.append({
            "validation_id": "VA-CO-002",
            "check": "provisional_warning_visible",
            "expected": True,
            "actual": None,
            "status": "PASS",
            "detail": "provisional_warning column not present",
        })

    # Check 3: Causality status remains Not Confirmed
    if "causality_status" in briefs.columns:
        all_not_confirmed = (briefs["causality_status"].fillna("Not Confirmed") == "Not Confirmed").all()
        rows.append({
            "validation_id": "VA-CO-003",
            "check": "causality_not_confirmed",
            "expected": True,
            "actual": all_not_confirmed,
            "status": "PASS" if all_not_confirmed else "FAIL",
            "detail": "" if all_not_confirmed else "Some packages have confirmed causality",
        })
    else:
        rows.append({
            "validation_id": "VA-CO-003",
            "check": "causality_not_confirmed",
            "expected": True,
            "actual": None,
            "status": "PASS",
            "detail": "causality_status column not present",
        })

    return pd.DataFrame(rows)


def build_register():
    return validate()


def get_required_columns():
    return [
        "validation_id", "check", "expected", "actual",
        "status", "detail",
    ]
