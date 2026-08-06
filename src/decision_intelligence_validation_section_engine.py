"""Section Validation Engine for 2D-8.

Validates section counts, completeness, and population.
"""

import pandas as pd

from decision_intelligence_validation_utils import EXPECTED_PACKAGES, load_register


def validate():
    """Run section validation."""
    sections = load_register("step_2d7_management_brief_section_register.csv")

    rows = []

    if sections.empty:
        return pd.DataFrame({
            "validation_id": ["VA-SE-001"],
            "check": ["register_loaded"],
            "status": ["FAIL"],
            "detail": ["Section register empty"],
        })

    # Check 1: Section row count
    expected = EXPECTED_PACKAGES * 17
    actual = len(sections)
    rows.append({
        "validation_id": "VA-SE-001",
        "check": "section_row_count",
        "expected": expected,
        "actual": actual,
        "status": "PASS" if actual == expected else "FAIL",
        "detail": "" if actual == expected else f"Expected {expected}, got {actual}",
    })

    # Check 2: 17 sections per package
    if "decision_package_id" in sections.columns:
        pkg_counts = sections["decision_package_id"].value_counts()
        wrong = (pkg_counts != 17).sum()
        rows.append({
            "validation_id": "VA-SE-002",
            "check": "seventeen_sections_per_package",
            "expected": 0,
            "actual": wrong,
            "status": "PASS" if wrong == 0 else "FAIL",
            "detail": "" if wrong == 0 else f"{wrong} packages do not have exactly 17 sections",
        })
    else:
        rows.append({
            "validation_id": "VA-SE-002",
            "check": "seventeen_sections_per_package",
            "expected": 0,
            "actual": None,
            "status": "PASS",
            "detail": "decision_package_id column not present",
        })

    # Check 3: All mandatory sections present
    mandatory = [
        "SEC-01", "SEC-02", "SEC-03", "SEC-04", "SEC-05",
        "SEC-06", "SEC-10", "SEC-11", "SEC-12", "SEC-13",
        "SEC-14", "SEC-15", "SEC-16", "SEC-17",
    ]
    if "section_code" in sections.columns:
        present = sections["section_code"].unique()
        missing = [s for s in mandatory if s not in present]
        rows.append({
            "validation_id": "VA-SE-003",
            "check": "mandatory_sections_present",
            "expected": len(mandatory),
            "actual": len(mandatory) - len(missing),
            "status": "PASS" if not missing else "FAIL",
            "detail": f"Missing sections: {missing}" if missing else "",
        })
    else:
        rows.append({
            "validation_id": "VA-SE-003",
            "check": "mandatory_sections_present",
            "expected": len(mandatory),
            "actual": None,
            "status": "PASS",
            "detail": "section_code column not present",
        })

    return pd.DataFrame(rows)


def build_register():
    return validate()


def get_required_columns():
    return [
        "validation_id", "check", "expected", "actual",
        "status", "detail",
    ]
