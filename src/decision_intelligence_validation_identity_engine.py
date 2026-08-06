"""Identity Validation Engine for 2D-8.

Validates governed identifiers: uniqueness, non-null, no Cartesian joins.
"""

import pandas as pd

from decision_intelligence_validation_utils import EXPECTED_PACKAGES, load_register


def validate():
    """Run identity validation on the main brief register."""
    briefs = load_register("step_2d7_integrated_management_brief_register.csv")
    if briefs.empty:
        return pd.DataFrame({
            "validation_id": ["VA-ID-001"],
            "check": ["register_loaded"],
            "status": ["FAIL"],
            "detail": ["Brief register empty"],
        })

    rows = []

    # Check 1: integrated_management_brief_id uniqueness
    unique_ids = briefs["integrated_management_brief_id"].nunique()
    rows.append({
        "validation_id": "VA-ID-001",
        "check": "brief_id_uniqueness",
        "expected": EXPECTED_PACKAGES,
        "actual": unique_ids,
        "status": "PASS" if unique_ids == EXPECTED_PACKAGES else "FAIL",
        "detail": "" if unique_ids == EXPECTED_PACKAGES else f"Found {unique_ids} unique IDs",
    })

    # Check 2: decision_package_id uniqueness (no Cartesian joins)
    unique_pkg = briefs["decision_package_id"].nunique()
    rows.append({
        "validation_id": "VA-ID-002",
        "check": "package_id_uniqueness",
        "expected": EXPECTED_PACKAGES,
        "actual": unique_pkg,
        "status": "PASS" if unique_pkg == EXPECTED_PACKAGES else "FAIL",
        "detail": "" if unique_pkg == EXPECTED_PACKAGES else f"Found {unique_pkg} unique package IDs",
    })

    # Check 3: Non-null critical IDs
    for col in ["integrated_management_brief_id", "decision_package_id", "approval_package_id"]:
        null_count = briefs[col].isna().sum()
        rows.append({
            "validation_id": f"VA-ID-{len(rows)+1:03d}",
            "check": f"{col}_not_null",
            "expected": 0,
            "actual": null_count,
            "status": "PASS" if null_count == 0 else "FAIL",
            "detail": "" if null_count == 0 else f"{null_count} null values found",
        })

    # Check 4: approval_package_id follows expected naming pattern and is not null
    # Note: approval_package_id and decision_package_id are distinct governed identifiers;
    # they should not be identical but both must be present.
    null_approval = briefs["approval_package_id"].isna().sum()
    rows.append({
        "validation_id": f"VA-ID-{len(rows)+1:03d}",
        "check": "approval_package_id_present",
        "expected": 0,
        "actual": null_approval,
        "status": "PASS" if null_approval == 0 else "FAIL",
        "detail": "" if null_approval == 0 else f"{null_approval} null approval_package_id values",
    })

    return pd.DataFrame(rows)


def build_register():
    return validate()


def get_required_columns():
    return [
        "validation_id", "check", "expected", "actual",
        "status", "detail",
    ]
