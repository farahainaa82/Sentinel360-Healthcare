"""Schema configuration registry with profile support, versioning, and cache invalidation."""

import os
import hashlib
import pandas as pd
from typing import Dict, List, Optional

# Governed schema version
SCHEMA_VERSION = "3A-DEMO-2.0"

# Module-level caches with checksum keys
_schema_cache: Dict[str, tuple] = {}  # key -> (checksum, df)
_alias_cache: Dict[str, tuple] = {}
_category_cache: Dict[str, tuple] = {}
_value_range_cache: Dict[str, tuple] = {}
_rule_config_cache: Dict[str, tuple] = {}
_required_file_cache: Dict[str, tuple] = {}
_catalogue_cache: Dict[str, tuple] = {}


_CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")


def _file_checksum(path: str) -> str:
    """Compute SHA-256 checksum of file contents."""
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def _load_csv_cached(filename: str, cache_dict: dict) -> pd.DataFrame:
    """Load CSV with checksum-based cache invalidation."""
    path = os.path.join(_CONFIG_DIR, filename)
    checksum = _file_checksum(path)
    if filename in cache_dict:
        old_checksum, df = cache_dict[filename]
        if old_checksum == checksum:
            return df.copy()
    df = pd.read_csv(path, dtype=str)
    df = df.fillna("")
    cache_dict[filename] = (checksum, df.copy())
    return df.copy()


def get_schema_version() -> str:
    """Return current governed schema version."""
    return SCHEMA_VERSION


def load_schema_config(schema_profile: str = "GENERIC_UPLOAD") -> pd.DataFrame:
    """Load schema configuration filtered by schema_profile."""
    df = _load_csv_cached("streamlit_upload_schema_config.csv", _schema_cache)
    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            f"streamlit_schema_registry.load_schema_config expected DataFrame from "
            f"streamlit_upload_schema_config.csv, received {type(df).__name__}"
        )
    if schema_profile and "schema_profile" in df.columns:
        df = df[df["schema_profile"] == schema_profile]
    return df.copy()


def load_alias_config(schema_profile: str = "GENERIC_UPLOAD") -> pd.DataFrame:
    """Load column alias configuration filtered by schema_profile."""
    df = _load_csv_cached("streamlit_upload_column_alias_config.csv", _alias_cache)
    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            f"streamlit_schema_registry.load_alias_config expected DataFrame from "
            f"streamlit_upload_column_alias_config.csv, received {type(df).__name__}"
        )
    if schema_profile and "schema_profile" in df.columns:
        df = df[df["schema_profile"] == schema_profile]
    return df.copy()


def load_category_config(schema_profile: str = "GENERIC_UPLOAD") -> pd.DataFrame:
    """Load category configuration filtered by schema_profile."""
    df = _load_csv_cached("streamlit_upload_category_config.csv", _category_cache)
    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            f"streamlit_schema_registry.load_category_config expected DataFrame from "
            f"streamlit_upload_category_config.csv, received {type(df).__name__}"
        )
    if schema_profile and "schema_profile" in df.columns:
        df = df[df["schema_profile"] == schema_profile]
    return df.copy()


def load_value_range_config(schema_profile: str = "GENERIC_UPLOAD") -> pd.DataFrame:
    """Load value range configuration filtered by schema_profile."""
    df = _load_csv_cached("streamlit_upload_value_range_config.csv", _value_range_cache)
    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            f"streamlit_schema_registry.load_value_range_config expected DataFrame from "
            f"streamlit_upload_value_range_config.csv, received {type(df).__name__}"
        )
    if schema_profile and "schema_profile" in df.columns:
        df = df[df["schema_profile"] == schema_profile]
    return df.copy()


def load_validation_rule_config(schema_profile: str = "GENERIC_UPLOAD") -> pd.DataFrame:
    """Load validation rule configuration filtered by schema_profile."""
    df = _load_csv_cached("streamlit_upload_validation_rule_config.csv", _rule_config_cache)
    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            f"streamlit_schema_registry.load_validation_rule_config expected DataFrame from "
            f"streamlit_upload_validation_rule_config.csv, received {type(df).__name__}"
        )
    if schema_profile and "schema_profile" in df.columns:
        df = df[df["schema_profile"] == schema_profile]
    return df.copy()


def load_required_file_config(schema_profile: str = "GENERIC_UPLOAD") -> pd.DataFrame:
    """Load required file configuration filtered by schema_profile."""
    df = _load_csv_cached("streamlit_upload_required_file_config.csv", _required_file_cache)
    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            f"streamlit_schema_registry.load_required_file_config expected DataFrame from "
            f"streamlit_upload_required_file_config.csv, received {type(df).__name__}"
        )
    if schema_profile and "schema_profile" in df.columns:
        df = df[df["schema_profile"] == schema_profile]
    return df.copy()


def load_dataset_catalogue(schema_profile: str = "GENERIC_UPLOAD") -> pd.DataFrame:
    """Load dataset catalogue filtered by schema_profile."""
    df = _load_csv_cached("streamlit_upload_dataset_catalogue.csv", _catalogue_cache)
    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            f"streamlit_schema_registry.load_dataset_catalogue expected DataFrame from "
            f"streamlit_upload_dataset_catalogue.csv, received {type(df).__name__}"
        )
    if schema_profile and "schema_profile" in df.columns:
        df = df[df["schema_profile"] == schema_profile]
    return df.copy()


def get_required_columns(dataset_type: str, schema_profile: str = "GENERIC_UPLOAD") -> List[str]:
    """Return required columns for a dataset type and schema profile."""
    df = load_schema_config(schema_profile)
    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            f"streamlit_schema_registry.load_schema_config expected DataFrame for "
            f"schema_profile={schema_profile!r}, received {type(df).__name__}"
        )
    sub = df[(df["dataset_type"] == dataset_type) & (df["required_field"].str.lower() == "yes")]
    cols = sub["field_name"].tolist()
    if not isinstance(cols, list):
        raise TypeError(
            f"streamlit_schema_registry.get_required_columns expected list for "
            f"dataset_type={dataset_type!r} schema_profile={schema_profile!r}, "
            f"received {type(cols).__name__}"
        )
    return cols


def get_optional_columns(dataset_type: str, schema_profile: str = "GENERIC_UPLOAD") -> List[str]:
    """Return optional columns for a dataset type and schema profile."""
    df = load_schema_config(schema_profile)
    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            f"streamlit_schema_registry.load_schema_config expected DataFrame for "
            f"schema_profile={schema_profile!r}, received {type(df).__name__}"
        )
    sub = df[(df["dataset_type"] == dataset_type) & (df["required_field"].str.lower() != "yes")]
    cols = sub["field_name"].tolist()
    if not isinstance(cols, list):
        raise TypeError(
            f"streamlit_schema_registry.get_optional_columns expected list for "
            f"dataset_type={dataset_type!r} schema_profile={schema_profile!r}, "
            f"received {type(cols).__name__}"
        )
    return cols


def get_expected_columns(dataset_type: str, schema_profile: str = "GENERIC_UPLOAD") -> List[str]:
    """Return all expected columns for a dataset type and schema profile."""
    df = load_schema_config(schema_profile)
    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            f"streamlit_schema_registry.load_schema_config expected DataFrame for "
            f"schema_profile={schema_profile!r}, received {type(df).__name__}"
        )
    sub = df[df["dataset_type"] == dataset_type]
    cols = sub["field_name"].tolist()
    if not isinstance(cols, list):
        raise TypeError(
            f"streamlit_schema_registry.get_expected_columns expected list for "
            f"dataset_type={dataset_type!r} schema_profile={schema_profile!r}, "
            f"received {type(cols).__name__}"
        )
    return cols


def get_nullable_columns(dataset_type: str, schema_profile: str = "GENERIC_UPLOAD") -> List[str]:
    """Return columns explicitly marked as nullable for a dataset type and schema profile."""
    df = load_schema_config(schema_profile)
    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            f"streamlit_schema_registry.load_schema_config expected DataFrame for "
            f"schema_profile={schema_profile!r}, received {type(df).__name__}"
        )
    sub = df[(df["dataset_type"] == dataset_type) & (df["nullable"].str.lower() == "yes")]
    cols = sub["field_name"].tolist()
    if not isinstance(cols, list):
        raise TypeError(
            f"streamlit_schema_registry.get_nullable_columns expected list for "
            f"dataset_type={dataset_type!r} schema_profile={schema_profile!r}, "
            f"received {type(cols).__name__}"
        )
    return cols


def get_primary_identifier(dataset_type: str, schema_profile: str = "GENERIC_UPLOAD") -> Optional[str]:
    """Return the primary identifier column for a dataset type and schema profile."""
    mapping = {
        "Staff Roster": "roster_id",
        "Staff Attendance": "attendance_id",
        "Patient Encounters": "encounter_id",
        "Bed Occupancy": "record_id",
        "Patient Queue": "queue_id",
        "Patient Complaints": "complaint_id",
        "Patient Survey": "survey_id",
    }
    result = mapping.get(dataset_type)
    if result is not None and not isinstance(result, str):
        raise TypeError(
            f"streamlit_schema_registry.get_primary_identifier expected str or None for "
            f"dataset_type={dataset_type!r} schema_profile={schema_profile!r}, "
            f"received {type(result).__name__}"
        )
    return result


def invalidate_all_caches():
    """Clear all module-level caches. Useful for testing or forced reload."""
    global _schema_cache, _alias_cache, _category_cache, _value_range_cache
    global _rule_config_cache, _required_file_cache, _catalogue_cache
    _schema_cache.clear()
    _alias_cache.clear()
    _category_cache.clear()
    _value_range_cache.clear()
    _rule_config_cache.clear()
    _required_file_cache.clear()
    _catalogue_cache.clear()
