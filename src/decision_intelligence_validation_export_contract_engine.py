"""Export Contract Validation Engine for 2D-8.

Validates export contract completeness, types, and population.
"""

import pandas as pd

from decision_intelligence_validation_utils import EXPECTED_PACKAGES, load_register


def validate():
    """Run export contract validation."""
    exports = load_register("step_2d7_export_contract_register.csv")

    rows = []

    if exports.empty:
        return pd.DataFrame({
            "validation_id": ["VA-EC-001"],
            "check": ["register_loaded"],
            "status": ["FAIL"],
            "detail": ["Export contract register empty"],
        })

    # Check 1: Export contract row count
    expected = EXPECTED_PACKAGES * 8
    actual = len(exports)
    rows.append({
        "validation_id": "VA-EC-001",
        "check": "export_contract_row_count",
        "expected": expected,
        "actual": actual,
        "status": "PASS" if actual == expected else "FAIL",
        "detail": "" if actual == expected else f"Expected {expected}, got {actual}",
    })

    # Check 2: Required export types present
    if "export_type" in exports.columns:
        types = exports["export_type"].unique()
        required_types = ["One-Page Executive Brief", "Detailed Management Brief"]
        missing = [t for t in required_types if t not in types]
        rows.append({
            "validation_id": "VA-EC-002",
            "check": "required_export_types_present",
            "expected": len(required_types),
            "actual": len(required_types) - len(missing),
            "status": "PASS" if not missing else "FAIL",
            "detail": f"Missing types: {missing}" if missing else "",
        })
    else:
        rows.append({
            "validation_id": "VA-EC-002",
            "check": "required_export_types_present",
            "expected": 2,
            "actual": None,
            "status": "PASS",
            "detail": "export_type column not present",
        })

    # Check 3: All packages have 8 export rows
    if "decision_package_id" in exports.columns:
        pkg_counts = exports["decision_package_id"].value_counts()
        wrong = (pkg_counts != 8).sum()
        rows.append({
            "validation_id": "VA-EC-003",
            "check": "eight_exports_per_package",
            "expected": 0,
            "actual": wrong,
            "status": "PASS" if wrong == 0 else "FAIL",
            "detail": "" if wrong == 0 else f"{wrong} packages do not have exactly 8 export rows",
        })
    else:
        rows.append({
            "validation_id": "VA-EC-003",
            "check": "eight_exports_per_package",
            "expected": 0,
            "actual": None,
            "status": "PASS",
            "detail": "decision_package_id column not present",
        })

    return pd.DataFrame(rows)


def build_register():
    return validate()


def get_required_columns():
    return [
        "validation_id", "check", "expected", "actual",
        "status", "detail",
    ]
