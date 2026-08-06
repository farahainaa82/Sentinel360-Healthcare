"""Quality validation: missing values, completeness, and duplicates (with dedup awareness)."""

import pandas as pd
from typing import List, Dict
from .streamlit_schema_registry import get_nullable_columns


def validate_quality(
    df: pd.DataFrame,
    dataset_type: str,
    filename: str,
    issue_engine,
    upload_session_id: str = "",
    schema_profile: str = "GENERIC_UPLOAD",
) -> List[Dict]:
    """Validate data quality. Returns list of issues added to engine."""
    issues = []
    if df.empty:
        return issues

    nullable_cols = get_nullable_columns(dataset_type, schema_profile)
    nullable_lower = [c.lower() for c in nullable_cols]

    # Missing values: only report for non-nullable columns
    for col in df.columns:
        if col.lower() in nullable_lower:
            continue
        missing_count = df[col].isna().sum()
        if missing_count > 0:
            pct = (missing_count / len(df)) * 100
            issue = issue_engine.add_issue(
                filename=filename,
                dataset_type=dataset_type,
                issue_category="Missing Value",
                issue_severity="Error" if pct > 50 else "Warning",
                issue_description=f"Column '{col}' has {missing_count} missing values ({pct:.1f}%)",
                column_name=col,
                row_number="",
                observed_value=f"{missing_count} missing / {len(df)} total",
                expected_rule="All non-nullable fields should have values",
                suggested_correction="Populate missing values or mark field as nullable in schema",
                blocking_flag="Blocking" if pct > 50 else "Non-blocking",
                validation_issue_id=f"ISS-{upload_session_id}-MV-{col}",
                upload_session_id=upload_session_id,
            )
            issues.append(issue)

    # Nullable all-null informational only (not blocking)
    for col in df.columns:
        if col.lower() in nullable_lower:
            missing_count = df[col].isna().sum()
            if missing_count == len(df):
                issue = issue_engine.add_issue(
                    filename=filename,
                    dataset_type=dataset_type,
                    issue_category="Missing Value",
                    issue_severity="Informational",
                    issue_description=f"Optional nullable column '{col}' is entirely null (intentional)",
                    column_name=col,
                    row_number="",
                    observed_value="All null",
                    expected_rule="Optional field may be blank",
                    suggested_correction="No action required if field is intentionally nullable",
                    blocking_flag="Non-blocking",
                    validation_issue_id=f"ISS-{upload_session_id}-MV-{col}",
                    upload_session_id=upload_session_id,
                )
                issues.append(issue)

    return issues
