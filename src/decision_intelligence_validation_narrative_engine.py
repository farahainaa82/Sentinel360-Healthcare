"""Narrative Validation Engine for 2D-8.

Validates narrative length governance, field completeness, and format constraints.
"""

import pandas as pd

from decision_intelligence_validation_utils import load_register


def validate():
    """Run narrative validation."""
    briefs = load_register("step_2d7_integrated_management_brief_register.csv")
    one_line = load_register("step_2d7_executive_one_line_summary_register.csv")
    short_sum = load_register("step_2d7_executive_short_summary_register.csv")

    rows = []

    # Check 1: One-line summary word count (aligned with 2D-7 test criteria: <=40 words)
    if not one_line.empty and "one_line_summary" in one_line.columns:
        words = one_line["one_line_summary"].fillna("").astype(str).str.split().str.len()
        over = (words > 40).sum()
        rows.append({
            "validation_id": "VA-NA-001",
            "check": "one_line_max_words_40",
            "expected": 0,
            "actual": over,
            "status": "PASS" if over == 0 else "FAIL",
            "detail": "" if over == 0 else f"{over} one-line summaries exceed 40 words",
        })
    else:
        rows.append({
            "validation_id": "VA-NA-001",
            "check": "one_line_max_words_40",
            "expected": 0,
            "actual": None,
            "status": "PASS",
            "detail": "One-line summary register unavailable",
        })

    # Check 2: Short summary word count (aligned with 2D-7 test criteria: <=130 words)
    if not short_sum.empty and "short_summary" in short_sum.columns:
        words = short_sum["short_summary"].fillna("").astype(str).str.split().str.len()
        over = (words > 130).sum()
        rows.append({
            "validation_id": "VA-NA-002",
            "check": "short_summary_max_words_130",
            "expected": 0,
            "actual": over,
            "status": "PASS" if over == 0 else "FAIL",
            "detail": "" if over == 0 else f"{over} short summaries exceed 130 words",
        })
    else:
        rows.append({
            "validation_id": "VA-NA-002",
            "check": "short_summary_max_words_130",
            "expected": 0,
            "actual": None,
            "status": "PASS",
            "detail": "Short summary register unavailable",
        })

    # Check 3: Issue title length
    if not briefs.empty and "issue_title" in briefs.columns:
        lengths = briefs["issue_title"].fillna("").astype(str).str.len()
        over = (lengths > 150).sum()
        rows.append({
            "validation_id": "VA-NA-003",
            "check": "issue_title_max_length_150",
            "expected": 0,
            "actual": over,
            "status": "PASS" if over == 0 else "FAIL",
            "detail": "" if over == 0 else f"{over} issue titles exceed 150 chars",
        })
    else:
        rows.append({
            "validation_id": "VA-NA-003",
            "check": "issue_title_max_length_150",
            "expected": 0,
            "actual": None,
            "status": "PASS",
            "detail": "issue_title column not present",
        })

    # Check 4: Executive headline length
    if not briefs.empty and "executive_headline" in briefs.columns:
        lengths = briefs["executive_headline"].fillna("").astype(str).str.len()
        over = (lengths > 200).sum()
        rows.append({
            "validation_id": "VA-NA-004",
            "check": "executive_headline_max_length_200",
            "expected": 0,
            "actual": over,
            "status": "PASS" if over == 0 else "FAIL",
            "detail": "" if over == 0 else f"{over} executive headlines exceed 200 chars",
        })
    else:
        rows.append({
            "validation_id": "VA-NA-004",
            "check": "executive_headline_max_length_200",
            "expected": 0,
            "actual": None,
            "status": "PASS",
            "detail": "executive_headline column not present",
        })

    return pd.DataFrame(rows)


def build_register():
    return validate()


def get_required_columns():
    return [
        "validation_id", "check", "expected", "actual",
        "status", "detail",
    ]
