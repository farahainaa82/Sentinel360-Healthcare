"""Data-type validator for numeric, categorical, date, boolean, and identifier fields."""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime


def validate_datatypes(
    df: pd.DataFrame,
    dataset_type: str,
    schema_df: pd.DataFrame,
) -> List[Dict[str, Any]]:
    """Validate data types against schema expectations."""
    issues = []
    df_schema = schema_df[schema_df["dataset_type"] == dataset_type]
    for _, row in df_schema.iterrows():
        col = row["field_name"]
        expected = str(row.get("data_type", "")).lower()
        if col not in df.columns:
            continue
        series = df[col]
        if expected == "numeric" or expected == "integer" or expected == "float":
            non_numeric = series[~series.isna()].apply(lambda x: not _is_numeric(x))
            if non_numeric.any():
                issues.append(_issue("Data Type", "Error", f"Column {col} contains non-numeric values.", blocking=True))
        elif expected == "date" or expected == "datetime" or expected == "timestamp":
            # Sample up to 100 non-null values for date validation
            sample = series.dropna().head(100)
            if len(sample) > 0:
                invalid_dates = sample.apply(lambda x: not _is_date(x))
                invalid_rate = invalid_dates.sum() / len(sample)
                if invalid_rate > 0.1:  # Allow up to 10% unparseable dates
                    issues.append(_issue("Data Type", "Error", f"Column {col} contains invalid dates ({invalid_rate*100:.0f}% of sample).", blocking=True))
        elif expected == "boolean":
            invalid_bool = series[~series.isna()].apply(lambda x: not _is_boolean(x))
            if invalid_bool.any():
                issues.append(_issue("Data Type", "Warning", f"Column {col} contains non-boolean values.", blocking=False))
        elif expected == "categorical" or expected == "string":
            if pd.api.types.is_numeric_dtype(series) and not series.isna().all():
                # Accept numeric if it's boolean-like (0/1) or the column is nullable and all null
                unique_vals = series.dropna().unique()
                is_bool_like = len(unique_vals) <= 2 and all(v in (0, 1, 0.0, 1.0, True, False) for v in unique_vals)
                if not is_bool_like:
                    issues.append(_issue("Data Type", "Warning", f"Column {col} is numeric but expected categorical.", blocking=False))
    return issues


def _is_numeric(val: Any) -> bool:
    try:
        float(val)
        return True
    except (ValueError, TypeError):
        return False


def _is_date(val: Any) -> bool:
    try:
        pd.to_datetime(val, errors="raise")
        return True
    except (ValueError, TypeError):
        return False


def _is_boolean(val: Any) -> bool:
    if isinstance(val, bool):
        return True
    if isinstance(val, (int, float)) and val in (0, 1, 0.0, 1.0):
        return True
    if str(val).lower() in ("true", "false", "yes", "no", "1", "0"):
        return True
    return False


def _issue(category: str, severity: str, description: str, blocking: bool) -> Dict[str, Any]:
    return {
        "issue_category": category,
        "issue_severity": severity,
        "issue_description": description,
        "blocking_flag": "Blocking" if blocking else "Non-blocking",
    }
