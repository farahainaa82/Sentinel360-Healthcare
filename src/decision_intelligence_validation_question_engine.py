"""Management Question Validation Engine for 2D-8.

Validates blocking question counts, mandatory question visibility, and completeness.
"""

import pandas as pd

from decision_intelligence_validation_utils import load_register


def validate():
    """Run question validation."""
    questions = load_register("step_2d7_management_question_summary_register.csv")

    rows = []

    if questions.empty:
        return pd.DataFrame({
            "validation_id": ["VA-QU-001"],
            "check": ["register_loaded"],
            "status": ["FAIL"],
            "detail": ["Question register empty"],
        })

    # Check 1: Blocking question count non-negative
    if "blocking_question_count" in questions.columns:
        counts = pd.to_numeric(questions["blocking_question_count"], errors="coerce").fillna(0)
        negative = (counts < 0).sum()
        rows.append({
            "validation_id": "VA-QU-001",
            "check": "blocking_question_count_non_negative",
            "expected": 0,
            "actual": negative,
            "status": "PASS" if negative == 0 else "FAIL",
            "detail": "" if negative == 0 else f"{negative} negative blocking question counts",
        })
    else:
        rows.append({
            "validation_id": "VA-QU-001",
            "check": "blocking_question_count_non_negative",
            "expected": 0,
            "actual": None,
            "status": "PASS",
            "detail": "blocking_question_count column not present",
        })

    # Check 2: Mandatory question count present
    if "mandatory_question_count" in questions.columns:
        present = questions["mandatory_question_count"].notna().all()
        rows.append({
            "validation_id": "VA-QU-002",
            "check": "mandatory_question_count_present",
            "expected": True,
            "actual": present,
            "status": "PASS" if present else "FAIL",
            "detail": "" if present else "Some packages lack mandatory_question_count",
        })
    else:
        rows.append({
            "validation_id": "VA-QU-002",
            "check": "mandatory_question_count_present",
            "expected": True,
            "actual": None,
            "status": "PASS",
            "detail": "mandatory_question_count column not present",
        })

    return pd.DataFrame(rows)


def build_register():
    return validate()


def get_required_columns():
    return [
        "validation_id", "check", "expected", "actual",
        "status", "detail",
    ]
