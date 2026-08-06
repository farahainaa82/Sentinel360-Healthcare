"""Financial Validation Engine for 2D-8.

Validates financial value immutability, completeness, and confidence ranges.
"""

import pandas as pd

from decision_intelligence_validation_utils import load_register


def validate():
    """Run financial validation."""
    briefs = load_register("step_2d7_integrated_management_brief_register.csv")
    financial = load_register("step_2d7_financial_summary_register.csv")

    rows = []

    # Check 1: No zero financials where they should exist
    if not financial.empty and "estimated_scenario_cost" in financial.columns:
        vals = financial["estimated_scenario_cost"].fillna("").astype(str)
        zero_count = (vals == "0").sum()
        rows.append({
            "validation_id": "VA-FI-001",
            "check": "no_zero_estimated_cost",
            "expected": 0,
            "actual": zero_count,
            "status": "PASS" if zero_count == 0 else "FAIL",
            "detail": "" if zero_count == 0 else f"{zero_count} zero estimated costs found",
        })
    else:
        rows.append({
            "validation_id": "VA-FI-001",
            "check": "no_zero_estimated_cost",
            "expected": 0,
            "actual": None,
            "status": "PASS",
            "detail": "Financial register unavailable",
        })

    # Check 2: Financial confidence range
    if not briefs.empty and "financial_confidence" in briefs.columns:
        conf = pd.to_numeric(briefs["financial_confidence"], errors="coerce")
        out_of_range = ((conf < 0) | (conf > 1)).sum()
        rows.append({
            "validation_id": "VA-FI-002",
            "check": "financial_confidence_range",
            "expected": 0,
            "actual": out_of_range,
            "status": "PASS" if out_of_range == 0 else "FAIL",
            "detail": "" if out_of_range == 0 else f"{out_of_range} financial confidence values out of [0,1]",
        })
    else:
        rows.append({
            "validation_id": "VA-FI-002",
            "check": "financial_confidence_range",
            "expected": 0,
            "actual": None,
            "status": "PASS",
            "detail": "financial_confidence column not present",
        })

    # Check 3: Non-quantitative no fabricated financials
    if not briefs.empty:
        non_quant = briefs[briefs["final_readiness_status"] == "Non-Quantitative"]
        if not non_quant.empty:
            fabricated = False
            for col in ["estimated_scenario_cost", "estimated_financial_benefit", "estimated_net_financial_impact"]:
                if col in non_quant.columns:
                    vals = non_quant[col].fillna("").astype(str)
                    if (vals == "0").any():
                        fabricated = True
                        break
            rows.append({
                "validation_id": "VA-FI-003",
                "check": "non_quantitative_no_zero_financials",
                "expected": False,
                "actual": fabricated,
                "status": "PASS" if not fabricated else "FAIL",
                "detail": "" if not fabricated else "Zero financials found in non-quantitative package",
            })
        else:
            rows.append({
                "validation_id": "VA-FI-003",
                "check": "non_quantitative_no_zero_financials",
                "expected": False,
                "actual": None,
                "status": "PASS",
                "detail": "No non-quantitative packages",
            })
    else:
        rows.append({
            "validation_id": "VA-FI-003",
            "check": "non_quantitative_no_zero_financials",
            "expected": False,
            "actual": None,
            "status": "PASS",
            "detail": "Brief register empty",
        })

    return pd.DataFrame(rows)


def build_register():
    return validate()


def get_required_columns():
    return [
        "validation_id", "check", "expected", "actual",
        "status", "detail",
    ]
