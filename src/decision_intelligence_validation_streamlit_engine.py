"""Streamlit Handover Readiness Validation Engine for 2D-8.

Validates Streamlit contract fields, completeness, and readiness criteria.
"""

import pandas as pd

from decision_intelligence_validation_utils import EXPECTED_PACKAGES, load_register


def validate():
    """Run Streamlit handover readiness validation."""
    streamlit = load_register("step_2d7_streamlit_management_brief_contract.csv")

    rows = []

    # Check 1: Streamlit contract row count
    if not streamlit.empty:
        count_ok = len(streamlit) == EXPECTED_PACKAGES
        rows.append({
            "validation_id": "VA-ST-001",
            "check": "streamlit_row_count",
            "expected": EXPECTED_PACKAGES,
            "actual": len(streamlit),
            "status": "PASS" if count_ok else "FAIL",
            "detail": "" if count_ok else f"Expected {EXPECTED_PACKAGES}, got {len(streamlit)}",
        })
    else:
        rows.append({
            "validation_id": "VA-ST-001",
            "check": "streamlit_row_count",
            "expected": EXPECTED_PACKAGES,
            "actual": 0,
            "status": "FAIL",
            "detail": "Streamlit contract register empty",
        })
        return pd.DataFrame(rows)

    # Check 2: Required fields present
    required = [
        "decision_package_id", "brief_title", "final_readiness_status",
        "approval_status", "integrated_management_brief_id",
    ]
    missing_fields = [f for f in required if f not in streamlit.columns]
    rows.append({
        "validation_id": "VA-ST-002",
        "check": "required_fields_present",
        "expected": len(required),
        "actual": len(required) - len(missing_fields),
        "status": "PASS" if not missing_fields else "FAIL",
        "detail": f"Missing fields: {missing_fields}" if missing_fields else "",
    })

    # Check 3: No null critical IDs
    if "decision_package_id" in streamlit.columns:
        nulls = streamlit["decision_package_id"].isna().sum()
        rows.append({
            "validation_id": "VA-ST-003",
            "check": "decision_package_id_not_null",
            "expected": 0,
            "actual": nulls,
            "status": "PASS" if nulls == 0 else "FAIL",
            "detail": "" if nulls == 0 else f"{nulls} null decision_package_id",
        })

    # Check 4: Approval status all pending
    if "approval_status" in streamlit.columns:
        pending = (streamlit["approval_status"].fillna("") == "Pending Management Review").all()
        rows.append({
            "validation_id": "VA-ST-004",
            "check": "approval_status_pending",
            "expected": True,
            "actual": pending,
            "status": "PASS" if pending else "FAIL",
            "detail": "" if pending else "Some Streamlit contract rows lack Pending approval",
        })

    return pd.DataFrame(rows)


def build_register():
    return validate()


def get_required_columns():
    return [
        "validation_id", "check", "expected", "actual",
        "status", "detail",
    ]
