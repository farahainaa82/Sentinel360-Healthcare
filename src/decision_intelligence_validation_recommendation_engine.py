"""Recommendation Validation Engine for 2D-8.

Validates recommendation confidence, readiness, and governance constraints.
"""

import pandas as pd

from decision_intelligence_validation_utils import load_register


def validate():
    """Run recommendation validation."""
    briefs = load_register("step_2d7_integrated_management_brief_register.csv")
    recs = load_register("step_2d7_recommendation_summary_register.csv")

    rows = []

    if briefs.empty:
        return pd.DataFrame({
            "validation_id": ["VA-RC-001"],
            "check": ["register_loaded"],
            "status": ["FAIL"],
            "detail": ["Brief register empty"],
        })

    # Check 1: Recommendation confidence range
    if "recommendation_confidence" in briefs.columns:
        conf = pd.to_numeric(briefs["recommendation_confidence"], errors="coerce")
        out_of_range = ((conf < 0) | (conf > 1)).sum()
        rows.append({
            "validation_id": "VA-RC-001",
            "check": "recommendation_confidence_range",
            "expected": 0,
            "actual": out_of_range,
            "status": "PASS" if out_of_range == 0 else "FAIL",
            "detail": "" if out_of_range == 0 else f"{out_of_range} confidence values out of [0,1]",
        })
    else:
        rows.append({
            "validation_id": "VA-RC-001",
            "check": "recommendation_confidence_range",
            "expected": 0,
            "actual": None,
            "status": "PASS",
            "detail": "recommendation_confidence column not present",
        })

    # Check 2: Recommendation readiness present
    if "recommendation_readiness" in briefs.columns:
        present = briefs["recommendation_readiness"].notna().all()
        rows.append({
            "validation_id": "VA-RC-002",
            "check": "recommendation_readiness_present",
            "expected": True,
            "actual": present,
            "status": "PASS" if present else "FAIL",
            "detail": "" if present else "Some packages lack recommendation_readiness",
        })
    else:
        rows.append({
            "validation_id": "VA-RC-002",
            "check": "recommendation_readiness_present",
            "expected": True,
            "actual": None,
            "status": "PASS",
            "detail": "recommendation_readiness column not present",
        })

    # Check 3: Representative recommendation not pre-approved
    if "recommendation_review_outcome" in briefs.columns:
        pre_approved = briefs["recommendation_review_outcome"].fillna("").str.contains("approved", case=False, na=False).sum()
        rows.append({
            "validation_id": "VA-RC-003",
            "check": "no_pre_approved_recommendation",
            "expected": 0,
            "actual": pre_approved,
            "status": "PASS" if pre_approved == 0 else "FAIL",
            "detail": "" if pre_approved == 0 else f"{pre_approved} recommendations marked approved",
        })
    else:
        rows.append({
            "validation_id": "VA-RC-003",
            "check": "no_pre_approved_recommendation",
            "expected": 0,
            "actual": None,
            "status": "PASS",
            "detail": "recommendation_review_outcome column not present",
        })

    return pd.DataFrame(rows)


def build_register():
    return validate()


def get_required_columns():
    return [
        "validation_id", "check", "expected", "actual",
        "status", "detail",
    ]
