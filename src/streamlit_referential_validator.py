"""Referential integrity validator."""

import pandas as pd
from typing import List, Dict, Any


def validate_referential(
    df: pd.DataFrame,
    dataset_type: str,
    schema_df: pd.DataFrame,
    reference_data: Dict[str, pd.DataFrame] = None,
) -> List[Dict[str, Any]]:
    """Validate referential integrity against reference datasets.

    If reference_data is None, returns "Not Assessable" informational issue.
    """
    issues = []
    if reference_data is None:
        issues.append({
            "issue_category": "Referential Integrity",
            "issue_severity": "Informational",
            "issue_description": "Referential integrity checks require authoritative reference datasets (not available in demo mode).",
            "blocking_flag": "Non-blocking",
            "column_name": "",
        })
        return issues

    # Validate department_id references if reference data available
    if "departments" in reference_data and "department_id" in df.columns:
        ref_ids = set(reference_data["departments"]["department_id"].dropna().astype(str))
        invalid = df[~df["department_id"].astype(str).isin(ref_ids)]
        if not invalid.empty:
            issues.append({
                "issue_category": "Referential Integrity",
                "issue_severity": "Error",
                "issue_description": f"{len(invalid)} rows have department_id not found in reference departments.",
                "blocking_flag": "Blocking",
                "column_name": "department_id",
            })

    return issues
