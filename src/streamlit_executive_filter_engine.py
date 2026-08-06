"""
streamlit_executive_filter_engine.py
Filter engine for Executive Overview.
"""

from typing import Dict, List, Optional
import pandas as pd

from .streamlit_executive_data_loader import load_executive_overview_dataset
from .streamlit_executive_logging import log_event


def _unique_sorted(series: pd.Series) -> List[str]:
    vals = series.dropna().astype(str).unique().tolist()
    vals = [v for v in vals if v.strip()]
    vals.sort()
    return vals


def get_filter_options(df: pd.DataFrame) -> Dict[str, List[str]]:
    if df.empty:
        return {}
    options: Dict[str, List[str]] = {}
    for col in [
        "hospital_name",
        "department_name",
        "year",
        "month",
        "reporting_date",
        "dominant_kpi_name",
        "urgency",
        "readiness_status",
        "management_attention_level",
        "primary_queue",
    ]:
        if col in df.columns:
            options[col] = _unique_sorted(df[col])
    return options


def apply_filters(
    df: pd.DataFrame,
    filters: Dict[str, Optional[List[str]]],
) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    mask = pd.Series(True, index=df.index)
    for col, selected in filters.items():
        if selected is None or not selected:
            continue
        if col not in df.columns:
            continue
        # Handle "All" sentinel
        if isinstance(selected, list) and "All" in selected:
            continue
        mask &= df[col].astype(str).isin([str(s) for s in selected])
    filtered = df[mask].copy()
    log_event("FILTER_APPLIED", f"rows_before={len(df)} rows_after={len(filtered)}")
    return filtered


def reset_filters() -> Dict[str, Optional[List[str]]]:
    return {}
