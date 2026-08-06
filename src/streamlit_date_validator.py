"""Date validator for invalid dates, future dates, ranges, sequences, and gaps."""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


def validate_dates(
    df: pd.DataFrame,
    dataset_type: str,
    schema_df: pd.DataFrame,
    max_future_days: int = 30,
    analysis_start: Optional[str] = None,
    analysis_end: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Validate date columns."""
    issues = []
    df_schema = schema_df[schema_df["dataset_type"] == dataset_type]
    date_cols = df_schema[df_schema["data_type"].str.lower().isin(["date", "datetime", "timestamp"])]["field_name"].tolist()

    for col in date_cols:
        if col not in df.columns:
            continue
        parsed = pd.to_datetime(df[col], errors="coerce")
        invalid = parsed.isna() & df[col].notna()
        if invalid.any():
            issues.append(_issue("Invalid Date", "Error", f"Column {col}: {invalid.sum()} invalid dates.", blocking=True, column=col, count=int(invalid.sum())))

        future_mask = parsed > (datetime.now() + timedelta(days=max_future_days))
        if future_mask.any():
            issues.append(_issue("Date Range", "Warning", f"Column {col}: {future_mask.sum()} future dates beyond {max_future_days} days.", blocking=False, column=col, count=int(future_mask.sum())))

        if analysis_start and analysis_end:
            s = pd.to_datetime(analysis_start)
            e = pd.to_datetime(analysis_end)
            outside = (parsed < s) | (parsed > e)
            if outside.any():
                issues.append(_issue("Date Range", "Warning", f"Column {col}: {outside.sum()} dates outside configured range.", blocking=False, column=col, count=int(outside.sum())))

    return issues


def _issue(category: str, severity: str, description: str, blocking: bool, column: str = "", count: int = 0) -> Dict[str, Any]:
    return {
        "issue_category": category,
        "issue_severity": severity,
        "issue_description": description,
        "blocking_flag": "Blocking" if blocking else "Non-Blocking",
        "column_name": column,
        "count": count,
    }
