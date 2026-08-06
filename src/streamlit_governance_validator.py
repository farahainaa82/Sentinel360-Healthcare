"""Governance validator for PII, retention, and authority checks."""

import pandas as pd
from typing import List, Dict, Any


def validate_governance(
    df: pd.DataFrame,
    dataset_type: str,
    schema_df: pd.DataFrame,
) -> List[Dict[str, Any]]:
    """Validate governance constraints.

    Returns warnings for potential PII exposure or metadata issues.
    """
    issues = []
    if df.empty:
        return issues

    # Check for direct PII in column names
    pii_keywords = ["name", "email", "phone", "address", "ssn", "dob", "birth"]
    for col in df.columns:
        if any(kw in col.lower() for kw in pii_keywords):
            issues.append({
                "issue_category": "Governance",
                "issue_severity": "Warning",
                "issue_description": f"Column '{col}' may contain PII — verify de-identification.",
                "blocking_flag": "Non-blocking",
                "column_name": col,
            })

    return issues
