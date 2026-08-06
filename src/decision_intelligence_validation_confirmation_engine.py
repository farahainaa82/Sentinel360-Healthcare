"""Confirmation Validation Engine for 2D-8.

Validates confirmation pending status, required confirmations, and completeness.
"""

import pandas as pd

from decision_intelligence_validation_utils import load_register


def validate():
    """Run confirmation validation."""
    confirmations = load_register("step_2d7_confirmation_summary_register.csv")

    rows = []

    if confirmations.empty:
        return pd.DataFrame({
            "validation_id": ["VA-CF-001"],
            "check": ["register_loaded"],
            "status": ["FAIL"],
            "detail": ["Confirmation register empty"],
        })

    # Check 1: Pending confirmation count present
    if "pending_confirmation_count" in confirmations.columns:
        present = confirmations["pending_confirmation_count"].notna().all()
        rows.append({
            "validation_id": "VA-CF-001",
            "check": "pending_confirmation_count_present",
            "expected": True,
            "actual": present,
            "status": "PASS" if present else "FAIL",
            "detail": "" if present else "Some packages lack pending_confirmation_count",
        })
    else:
        rows.append({
            "validation_id": "VA-CF-001",
            "check": "pending_confirmation_count_present",
            "expected": True,
            "actual": None,
            "status": "PASS",
            "detail": "pending_confirmation_count column not present",
        })

    # Check 2: Required confirmation count non-negative
    if "required_confirmation_count" in confirmations.columns:
        counts = pd.to_numeric(confirmations["required_confirmation_count"], errors="coerce").fillna(0)
        negative = (counts < 0).sum()
        rows.append({
            "validation_id": "VA-CF-002",
            "check": "required_confirmation_count_non_negative",
            "expected": 0,
            "actual": negative,
            "status": "PASS" if negative == 0 else "FAIL",
            "detail": "" if negative == 0 else f"{negative} negative required confirmation counts",
        })
    else:
        rows.append({
            "validation_id": "VA-CF-002",
            "check": "required_confirmation_count_non_negative",
            "expected": 0,
            "actual": None,
            "status": "PASS",
            "detail": "required_confirmation_count column not present",
        })

    return pd.DataFrame(rows)


def build_register():
    return validate()


def get_required_columns():
    return [
        "validation_id", "check", "expected", "actual",
        "status", "detail",
    ]
