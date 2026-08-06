"""Validation scorecard engine for transparent dimension scoring."""

import pandas as pd
from typing import Dict, List, Any, Optional


DIMENSIONS = [
    "File Integrity",
    "Schema Completeness",
    "Data-Type Validity",
    "Missing-Value Quality",
    "Duplicate Quality",
    "Identifier Integrity",
    "Date Validity",
    "Value-Range Validity",
    "Referential Integrity",
    "Governance Compliance",
]


def build_scorecard(
    issues: List[Dict[str, Any]],
    dataset_type: str,
    schema_df: pd.DataFrame,
    df: Optional[pd.DataFrame] = None,
) -> List[Dict[str, Any]]:
    """Build a transparent validation scorecard."""
    scorecard = []
    blocking = [i for i in issues if i.get("blocking_flag") == "Blocking"]
    warnings = [i for i in issues if i.get("blocking_flag") != "Blocking" and i.get("issue_severity") in ("Warning", "Error")]
    errors = [i for i in issues if i.get("issue_severity") == "Error"]
    info = [i for i in issues if i.get("issue_severity") == "Informational"]

    def dim_status(category: str) -> str:
        cat_issues = {i["issue_category"]: i for i in issues if i["issue_category"] == category}
        if category in cat_issues:
            if cat_issues[category].get("blocking_flag") == "Blocking":
                return "Fail"
            if cat_issues[category].get("issue_severity") == "Error":
                return "Fail"
            return "Pass with Warnings"
        return "Pass"

    def overall_for_dim(name: str) -> str:
        if name in ("File Integrity", "Schema Completeness", "Data-Type Validity", "Identifier Integrity", "Value-Range Validity"):
            if any(i["issue_category"] in ("File Format", "Empty File", "Corrupted File", "Missing Column", "Schema", "Data Type", "Invalid Identifier", "Duplicate Record", "Value Range") for i in blocking):
                return "Fail"
            if any(i["issue_category"] in ("File Format", "Empty File", "Corrupted File", "Missing Column", "Schema", "Data Type", "Invalid Identifier", "Duplicate Record", "Value Range") for i in errors if i.get("blocking_flag") == "Blocking"):
                return "Fail"
            if any(i["issue_category"] in ("File Format", "Empty File", "Corrupted File", "Missing Column", "Schema", "Data Type", "Invalid Identifier", "Duplicate Record", "Value Range") for i in warnings):
                return "Pass with Warnings"
        if name == "Referential Integrity":
            if any(i["issue_category"] == "Referential Integrity" and i.get("issue_severity") == "Informational" for i in issues):
                return "Not Assessable"
            if any(i["issue_category"] == "Referential Integrity" for i in blocking):
                return "Fail"
            if any(i["issue_category"] == "Referential Integrity" for i in warnings):
                return "Pass with Warnings"
        if any(i["issue_category"] in ("Governance Warning", "Unexpected Column") for i in warnings if name == "Governance Compliance"):
            return "Pass with Warnings"
        if any(i["issue_category"] == "Missing Value" for i in warnings if name == "Missing-Value Quality"):
            return "Pass with Warnings"
        if any(i["issue_category"] == "Duplicate Record" for i in warnings if name == "Duplicate Quality"):
            return "Pass with Warnings"
        if any(i["issue_category"] in ("Invalid Date", "Date Range") for i in warnings if name == "Date Validity"):
            return "Pass with Warnings"
        return "Pass"

    for dim in DIMENSIONS:
        status = overall_for_dim(dim)
        scorecard.append({
            "dimension": dim,
            "status": status,
            "blocking_count": len([i for i in blocking if i.get("issue_severity") == "Error"]),
            "warning_count": len([i for i in warnings if i["issue_category"] in dim_categories(dim)]),
            "info_count": len([i for i in info if i["issue_category"] in dim_categories(dim)]),
        })

    return scorecard


def dim_categories(dim: str) -> tuple:
    mapping = {
        "File Integrity": ("File Format", "Empty File", "Corrupted File", "Encoding"),
        "Schema Completeness": ("Schema", "Missing Column", "Unexpected Column"),
        "Data-Type Validity": ("Data Type",),
        "Missing-Value Quality": ("Missing Value",),
        "Duplicate Quality": ("Duplicate Record",),
        "Identifier Integrity": ("Invalid Identifier", "Duplicate Record"),
        "Date Validity": ("Invalid Date", "Date Range"),
        "Value-Range Validity": ("Value Range",),
        "Referential Integrity": ("Referential Integrity",),
        "Governance Compliance": ("Governance Warning", "Unexpected Column"),
    }
    return mapping.get(dim, ())


def compute_overall_status(scorecard: List[Dict[str, Any]]) -> str:
    """Compute overall status from scorecard."""
    statuses = [s["status"] for s in scorecard]
    if any(s == "Fail" for s in statuses):
        return "Rejected"
    if any(s == "Pass with Warnings" for s in statuses):
        return "Accepted with Warnings"
    if all(s in ("Pass", "Not Assessable", "Not Applicable") for s in statuses):
        return "Accepted"
    return "Not Yet Validated"
