"""Column alias mapping engine with ambiguous mapping detection."""

import pandas as pd
from typing import Dict, List, Tuple, Any
from .streamlit_schema_registry import load_alias_config


def build_alias_map(alias_df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """Build mapping from alias to canonical info."""
    alias_map = {}
    for _, row in alias_df.iterrows():
        alias = str(row["alias"]).strip().lower()
        canonical = str(row["canonical_name"]).strip()
        alias_map[alias] = {
            "canonical_name": canonical,
            "confidence": str(row.get("alias_confidence", "Moderate")),
            "requires_confirmation": bool(row.get("requires_confirmation", False)),
        }
    return alias_map


def map_column_names(
    df: pd.DataFrame,
    alias_map: Dict[str, Dict[str, Any]],
    schema_df: pd.DataFrame,
    dataset_type: str,
) -> Tuple[Dict[str, str], List[Dict[str, Any]]]:
    """Map DataFrame columns to canonical names.

    Returns (mapping dict, list of ambiguous proposals).
    """
    mapping = {}
    proposals = []
    schema_cols = schema_df[schema_df["dataset_type"] == dataset_type]["field_name"].tolist()
    schema_aliases = {c.lower(): c for c in schema_cols}

    for col in df.columns:
        col_clean = str(col).strip().lower()
        if col_clean in schema_aliases:
            mapping[col] = col_clean
            continue
        if col_clean in alias_map:
            info = alias_map[col_clean]
            canonical = info["canonical_name"]
            if canonical in schema_cols:
                mapping[col] = canonical
                if info["requires_confirmation"]:
                    proposals.append({
                        "original_column": col,
                        "proposed_canonical": canonical,
                        "confidence": info["confidence"],
                        "requires_confirmation": True,
                    })
            else:
                mapping[col] = col
        else:
            mapping[col] = col
    return mapping, proposals


def apply_column_mapping(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
    """Rename DataFrame columns according to mapping."""
    rename_map = {k: v for k, v in mapping.items() if k != v and v != k}
    if rename_map:
        df = df.rename(columns=rename_map)
    return df
