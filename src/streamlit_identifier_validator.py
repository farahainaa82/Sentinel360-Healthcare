"""Identifier validation: uniqueness and validity of primary identifiers."""

import pandas as pd
from typing import List, Dict
from .streamlit_schema_registry import get_primary_identifier


def validate_identifiers(
    df: pd.DataFrame,
    dataset_type: str,
    filename: str,
    issue_engine,
    upload_session_id: str = "",
) -> List[Dict]:
    """Validate primary identifier uniqueness. Returns list of issues."""
    issues = []
    if df.empty:
        return issues

    primary_id = get_primary_identifier(dataset_type)
    if not primary_id:
        return issues

    if primary_id not in df.columns:
        # Missing primary identifier column is a schema issue, not an identifier issue
        return issues

    # Check uniqueness of primary identifier
    dupes = df[primary_id].duplicated().sum()
    if dupes > 0:
        issue = issue_engine.add_issue(
            filename=filename,
            dataset_type=dataset_type,
            issue_category="Duplicate Record",
            issue_severity="Error",
            issue_description=f"Primary identifier '{primary_id}' has {dupes} duplicate values",
            column_name=primary_id,
            row_number="",
            observed_value=f"{dupes} duplicates",
            expected_rule=f"{primary_id} must be unique per row",
            suggested_correction="Remove or consolidate duplicate records",
            blocking_flag="Blocking",
            validation_issue_id=f"ISS-{upload_session_id}-DUP-{primary_id}",
            upload_session_id=upload_session_id,
        )
        issues.append(issue)

    # Check for null primary identifiers
    nulls = df[primary_id].isna().sum()
    if nulls > 0:
        issue = issue_engine.add_issue(
            filename=filename,
            dataset_type=dataset_type,
            issue_category="Invalid Identifier",
            issue_severity="Error",
            issue_description=f"Primary identifier '{primary_id}' has {nulls} null values",
            column_name=primary_id,
            row_number="",
            observed_value=f"{nulls} nulls",
            expected_rule=f"{primary_id} must not be null",
            suggested_correction="Populate missing primary identifiers",
            blocking_flag="Blocking",
            validation_issue_id=f"ISS-{upload_session_id}-IDNULL-{primary_id}",
            upload_session_id=upload_session_id,
        )
        issues.append(issue)

    return issues
