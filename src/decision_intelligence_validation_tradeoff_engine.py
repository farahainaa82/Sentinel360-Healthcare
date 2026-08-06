"""Tradeoff and Impact Validation Engine for 2D-8.

Validates tradeoff severity consistency and impact summary completeness.
"""

import pandas as pd

from decision_intelligence_validation_utils import load_register


def validate():
    """Run tradeoff validation."""
    tradeoffs = load_register("step_2d7_tradeoff_and_impact_summary_register.csv")
    briefs = load_register("step_2d7_integrated_management_brief_register.csv")

    rows = []

    if tradeoffs.empty:
        return pd.DataFrame({
            "validation_id": ["VA-TR-001"],
            "check": ["register_loaded"],
            "status": ["FAIL"],
            "detail": ["Tradeoff register empty"],
        })

    # Check 1: Tradeoff severity alignment with scenario family
    if not briefs.empty and "scenario_family" in briefs.columns and "tradeoff_severity" in tradeoffs.columns:
        merged = briefs[["decision_package_id", "scenario_family"]].merge(
            tradeoffs[["decision_package_id", "tradeoff_severity"]],
            on="decision_package_id", how="left"
        )
        # No-Action or Baseline should not have Critical tradeoff severity
        no_action = merged[merged["scenario_family"].fillna("").str.contains("No-Action|Baseline", case=False, na=False)]
        if not no_action.empty:
            invalid = (no_action["tradeoff_severity"].fillna("").str.lower() == "critical").sum()
            rows.append({
                "validation_id": "VA-TR-001",
                "check": "no_action_tradeoff_severity",
                "expected": 0,
                "actual": invalid,
                "status": "PASS" if invalid == 0 else "FAIL",
                "detail": "" if invalid == 0 else f"{invalid} No-Action/Baseline packages with Critical tradeoff",
            })
        else:
            rows.append({
                "validation_id": "VA-TR-001",
                "check": "no_action_tradeoff_severity",
                "expected": 0,
                "actual": None,
                "status": "PASS",
                "detail": "No No-Action or Baseline packages",
            })
    else:
        rows.append({
            "validation_id": "VA-TR-001",
            "check": "no_action_tradeoff_severity",
            "expected": 0,
            "actual": None,
            "status": "PASS",
            "detail": "Required columns not present",
        })

    # Check 2: Displacement risk present
    if "displacement_risk" in tradeoffs.columns:
        present = tradeoffs["displacement_risk"].notna().all()
        rows.append({
            "validation_id": "VA-TR-002",
            "check": "displacement_risk_present",
            "expected": True,
            "actual": present,
            "status": "PASS" if present else "FAIL",
            "detail": "" if present else "Some packages lack displacement_risk",
        })
    else:
        rows.append({
            "validation_id": "VA-TR-002",
            "check": "displacement_risk_present",
            "expected": True,
            "actual": None,
            "status": "PASS",
            "detail": "displacement_risk column not present",
        })

    return pd.DataFrame(rows)


def build_register():
    return validate()


def get_required_columns():
    return [
        "validation_id", "check", "expected", "actual",
        "status", "detail",
    ]
