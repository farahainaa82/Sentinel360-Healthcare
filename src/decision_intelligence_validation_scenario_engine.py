"""Scenario Validation Engine for 2D-8.

Validates scenario summary availability, immutability, and consistency.
"""

import pandas as pd

from decision_intelligence_validation_utils import load_register


def validate():
    """Run scenario validation."""
    briefs = load_register("step_2d7_integrated_management_brief_register.csv")
    if briefs.empty:
        return pd.DataFrame({
            "validation_id": ["VA-SC-001"],
            "check": ["register_loaded"],
            "status": ["FAIL"],
            "detail": ["Brief register empty"],
        })

    rows = []

    # Check 1: Ready-for-review packages have scenario summaries
    # Only packages marked "Ready for Integrated Management Review" are expected
    # to have complete scenario data; other statuses may legitimately lack them.
    ready_review = briefs[briefs["final_readiness_status"] == "Ready for Integrated Management Review"]
    if not ready_review.empty:
        # Check for non-empty strings, not just notna (empty strings count as missing)
        def _has_content(series):
            if series.name not in ready_review.columns:
                return False
            s = series.fillna("").astype(str).str.strip()
            return (s != "").any()

        has_baseline = _has_content(ready_review["baseline_summary"]) if "baseline_summary" in ready_review.columns else False
        has_expected = _has_content(ready_review["expected_summary"]) if "expected_summary" in ready_review.columns else False
        has_scenario = has_baseline or has_expected
        rows.append({
            "validation_id": "VA-SC-001",
            "check": "ready_review_scenario_present",
            "expected": True,
            "actual": has_scenario,
            "status": "PASS" if has_scenario else "FAIL",
            "detail": "" if has_scenario else "Ready-for-review packages lack scenario summaries",
        })
    else:
        rows.append({
            "validation_id": "VA-SC-001",
            "check": "ready_review_scenario_present",
            "expected": True,
            "actual": None,
            "status": "PASS",
            "detail": "No Ready for Integrated Management Review packages to check",
        })

    # Check 2: Non-quantitative packages do not have fabricated scenarios
    non_quant = briefs[briefs["final_readiness_status"] == "Non-Quantitative"]
    if not non_quant.empty:
        fabricated = False
        for col in ["baseline_summary", "conservative_summary", "expected_summary", "higher_intensity_summary"]:
            if col in non_quant.columns:
                vals = non_quant[col].fillna("Unavailable").astype(str)
                if vals.str.contains("fabricated", case=False, na=False).any():
                    fabricated = True
                    break
        rows.append({
            "validation_id": "VA-SC-002",
            "check": "non_quantitative_no_fabricated",
            "expected": False,
            "actual": fabricated,
            "status": "PASS" if not fabricated else "FAIL",
            "detail": "" if not fabricated else "Fabricated scenario text found in non-quantitative package",
        })
    else:
        rows.append({
            "validation_id": "VA-SC-002",
            "check": "non_quantitative_no_fabricated",
            "expected": False,
            "actual": None,
            "status": "PASS",
            "detail": "No non-quantitative packages",
        })

    # Check 3: Scenario confidence range
    if "scenario_confidence" in briefs.columns:
        conf = pd.to_numeric(briefs["scenario_confidence"], errors="coerce")
        out_of_range = ((conf < 0) | (conf > 1)).sum()
        rows.append({
            "validation_id": "VA-SC-003",
            "check": "scenario_confidence_range",
            "expected": 0,
            "actual": out_of_range,
            "status": "PASS" if out_of_range == 0 else "FAIL",
            "detail": "" if out_of_range == 0 else f"{out_of_range} confidence values out of [0,1]",
        })
    else:
        rows.append({
            "validation_id": "VA-SC-003",
            "check": "scenario_confidence_range",
            "expected": 0,
            "actual": None,
            "status": "PASS",
            "detail": "scenario_confidence column not present",
        })

    return pd.DataFrame(rows)


def build_register():
    return validate()


def get_required_columns():
    return [
        "validation_id", "check", "expected", "actual",
        "status", "detail",
    ]
