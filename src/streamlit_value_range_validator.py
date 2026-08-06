"""Value-range validator for numeric fields and dataset-specific rules."""

import pandas as pd
import numpy as np
from typing import Dict, List, Any


def validate_value_ranges(
    df: pd.DataFrame,
    dataset_type: str,
    value_range_df: pd.DataFrame,
) -> List[Dict[str, Any]]:
    """Validate value ranges against configured rules."""
    issues = []
    rules = value_range_df[value_range_df["dataset_type"] == dataset_type]

    for _, rule in rules.iterrows():
        col = rule["field_name"]
        if col not in df.columns:
            continue
        series = pd.to_numeric(df[col], errors="coerce")
        min_val = rule.get("min_value")
        max_val = rule.get("max_value")
        inclusive_min = bool(rule.get("inclusive_min", True))
        inclusive_max = bool(rule.get("inclusive_max", True))

        if min_val is not None and not pd.isna(min_val):
            min_val = float(min_val)
            if inclusive_min:
                below = series < min_val
            else:
                below = series <= min_val
            if below.any():
                issues.append(_issue("Value Range", "Error", f"Column {col}: {below.sum()} values below minimum {min_val}.", blocking=True, column=col, count=int(below.sum())))

        if max_val is not None and not pd.isna(max_val):
            max_val = float(max_val)
            if inclusive_max:
                above = series > max_val
            else:
                above = series >= max_val
            if above.any():
                issues.append(_issue("Value Range", "Warning", f"Column {col}: {above.sum()} values above maximum {max_val}.", blocking=False, column=col, count=int(above.sum())))

    if dataset_type == "Bed Occupancy":
        if "beds_total" in df.columns and "beds_occupied" in df.columns:
            total = pd.to_numeric(df["beds_total"], errors="coerce")
            occupied = pd.to_numeric(df["beds_occupied"], errors="coerce")
            over = occupied > total
            if over.any():
                issues.append(_issue("Value Range", "Error", f"beds_occupied exceeds beds_total in {over.sum()} rows.", blocking=True, column="beds_occupied", count=int(over.sum())))

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
