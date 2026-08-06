"""Schema validation: required, optional, and unexpected columns."""

import pandas as pd
from typing import List, Dict
from .streamlit_schema_registry import get_required_columns, get_expected_columns


def validate_schema(
    df: pd.DataFrame,
    dataset_type: str,
    filename: str,
    issue_engine,
    upload_session_id: str = "",
    schema_profile: str = "GENERIC_UPLOAD",
) -> List[Dict]:
    """Validate DataFrame columns against expected schema.

    Returns list of issues added to engine.
    """
    issues = []
    if df.empty and len(df.columns) == 0:
        return issues

    expected = get_expected_columns(dataset_type, schema_profile)
    if not expected:
        # Unknown dataset type — no schema to validate against
        return issues

    expected_lower = [c.lower() for c in expected]
    actual_lower = [c.lower() for c in df.columns]

    # Missing columns
    for col in expected:
        if col.lower() not in actual_lower:
            issue = issue_engine.add_issue(
                filename=filename,
                dataset_type=dataset_type,
                issue_category="Missing Column",
                issue_severity="Error",
                issue_description=f"Expected column '{col}' is missing from uploaded file",
                column_name=col,
                row_number="",
                observed_value="Column not found",
                expected_rule=f"Column '{col}' is defined in schema for {dataset_type}",
                suggested_correction="Add missing column or confirm dataset type",
                blocking_flag="Blocking",
                validation_issue_id=f"ISS-{upload_session_id}-MISS-{col}",
                upload_session_id=upload_session_id,
            )
            issues.append(issue)

    # Unexpected columns
    for col in df.columns:
        if col.lower() not in expected_lower:
            issue = issue_engine.add_issue(
                filename=filename,
                dataset_type=dataset_type,
                issue_category="Unexpected Column",
                issue_severity="Warning",
                issue_description=f"Column '{col}' is not defined in schema for {dataset_type}",
                column_name=col,
                row_number="",
                observed_value=f"Unexpected column: {col}",
                expected_rule=f"Only expected columns should be present for {dataset_type}",
                suggested_correction="Remove unexpected column or update schema configuration",
                blocking_flag="Non-blocking",
                validation_issue_id=f"ISS-{upload_session_id}-UNEXP-{col}",
                upload_session_id=upload_session_id,
            )
            issues.append(issue)

    return issues
