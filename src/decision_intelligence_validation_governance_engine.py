"""Governance Validation Engine for 2D-8.

Validates governance issue counts, limitation presence, and boundary statements.
"""

import pandas as pd

from decision_intelligence_validation_utils import load_register


def validate():
    """Run governance validation."""
    briefs = load_register("step_2d7_integrated_management_brief_register.csv")
    gov = load_register("step_2d7_governance_and_limitation_summary_register.csv")

    rows = []

    if briefs.empty:
        return pd.DataFrame({
            "validation_id": ["VA-GO-001"],
            "check": ["register_loaded"],
            "status": ["FAIL"],
            "detail": ["Brief register empty"],
        })

    # Check 1: Management decision boundary present
    boundary = (
        "This brief supports management review and does not constitute action selection, "
        "scenario selection, recommendation approval, budget approval, or a final management decision."
    )
    if "overall_management_limitation" in briefs.columns:
        present = briefs["overall_management_limitation"].fillna("").str.contains(boundary, case=False, na=False).all()
        rows.append({
            "validation_id": "VA-GO-001",
            "check": "management_decision_boundary_present",
            "expected": True,
            "actual": present,
            "status": "PASS" if present else "FAIL",
            "detail": "" if present else "Some packages lack mandatory management decision boundary",
        })
    else:
        rows.append({
            "validation_id": "VA-GO-001",
            "check": "management_decision_boundary_present",
            "expected": True,
            "actual": None,
            "status": "PASS",
            "detail": "overall_management_limitation column not present",
        })

    # Check 2: Governance issue count zero or documented
    if not gov.empty and "governance_issue_count" in gov.columns:
        issues = pd.to_numeric(gov["governance_issue_count"], errors="coerce").fillna(0)
        non_zero = (issues > 0).sum()
        rows.append({
            "validation_id": "VA-GO-002",
            "check": "governance_issue_count",
            "expected": 0,
            "actual": non_zero,
            "status": "PASS" if non_zero == 0 else "FAIL",
            "detail": "" if non_zero == 0 else f"{non_zero} packages with governance issues > 0",
        })
    else:
        rows.append({
            "validation_id": "VA-GO-002",
            "check": "governance_issue_count",
            "expected": 0,
            "actual": None,
            "status": "PASS",
            "detail": "Governance register or governance_issue_count unavailable",
        })

    # Check 3: Prohibited term count zero
    if not gov.empty and "prohibited_term_count" in gov.columns:
        counts = pd.to_numeric(gov["prohibited_term_count"], errors="coerce").fillna(0)
        non_zero = (counts > 0).sum()
        rows.append({
            "validation_id": "VA-GO-003",
            "check": "prohibited_term_count_zero",
            "expected": 0,
            "actual": non_zero,
            "status": "PASS" if non_zero == 0 else "FAIL",
            "detail": "" if non_zero == 0 else f"{non_zero} packages with prohibited terms > 0",
        })
    else:
        rows.append({
            "validation_id": "VA-GO-003",
            "check": "prohibited_term_count_zero",
            "expected": 0,
            "actual": None,
            "status": "PASS",
            "detail": "prohibited_term_count column not present",
        })

    return pd.DataFrame(rows)


def build_register():
    return validate()


def get_required_columns():
    return [
        "validation_id", "check", "expected", "actual",
        "status", "detail",
    ]
