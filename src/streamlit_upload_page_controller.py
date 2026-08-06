"""Page controller: orchestrates all 7 validation layers."""

import os
import hashlib
import pandas as pd
from typing import List, Dict, Tuple

from .streamlit_file_reader import read_uploaded_file, read_file_bytes, detect_file_extension
from .streamlit_dataset_detector import detect_dataset_type
from .streamlit_column_alias_engine import build_alias_map, map_column_names, apply_column_mapping
from .streamlit_file_validator import validate_file
from .streamlit_schema_validator import validate_schema
from .streamlit_datatype_validator import validate_datatypes
from .streamlit_quality_validator import validate_quality
from .streamlit_date_validator import validate_dates
from .streamlit_identifier_validator import validate_identifiers
from .streamlit_referential_validator import validate_referential
from .streamlit_governance_validator import validate_governance
from .streamlit_value_range_validator import validate_value_ranges
from .streamlit_validation_scorecard_engine import build_scorecard, compute_overall_status
from .streamlit_validation_issue_engine import ValidationIssueEngine
from .streamlit_upload_manifest_engine import UploadManifestEngine
from .streamlit_upload_session_manager import UploadSessionManager
from .streamlit_schema_registry import (
    load_schema_config,
    load_alias_config,
    load_category_config,
    load_value_range_config,
    load_validation_rule_config,
    get_schema_version,
)
from .streamlit_upload_logging import log_event, log_exception


MAX_PREVIEW_ROWS = 1000
MAX_FILE_SIZE_MB = 200


def _guard_list_of_dicts(value, name: str, dataset_type: str, schema_profile: str) -> List[Dict]:
    """Type guard: ensure value is a list of dictionaries."""
    if not isinstance(value, list):
        raise TypeError(
            f"streamlit_upload_page_controller expected {name} to be list[dict] for "
            f"dataset_type={dataset_type!r} schema_profile={schema_profile!r}, "
            f"received {type(value).__name__}"
        )
    for item in value:
        if not isinstance(item, dict):
            raise TypeError(
                f"streamlit_upload_page_controller expected {name} items to be dict for "
                f"dataset_type={dataset_type!r} schema_profile={schema_profile!r}, "
                f"received {type(item).__name__}"
            )
    return value


def process_uploaded_file(
    file_content,
    filename: str,
    upload_session_id: str = "",
    dataset_type: str = "",
    schema_profile: str = "GENERIC_UPLOAD",
) -> Dict:
    """Process a single uploaded file through all 7 validation layers.

    Args:
        file_content: bytes or file-like object
        filename: original filename
        upload_session_id: session identifier
        dataset_type: confirmed dataset type (optional)
        schema_profile: schema profile to use (GENERIC_UPLOAD or SENTINEL360_SYNTHETIC_DEMO)

    Returns:
        dict with file_info, detected_type, dataset_type, df_preview, issues, scorecard, manifest
    """
    issue_engine = ValidationIssueEngine()
    manifest_engine = UploadManifestEngine()

    # 1. File validation
    try:
        file_issues = validate_file(file_content, filename, max_size_mb=MAX_FILE_SIZE_MB)
    except Exception as e:
        log_exception(upload_session_id, f"File validation failed for {filename}: {e}")
        file_issues = [{"issue_category": "File Read", "issue_severity": "Error", "issue_description": str(e), "blocking_flag": "Blocking"}]

    for fi in file_issues:
        issue_engine.add_issue(
            filename=filename,
            dataset_type=dataset_type or "Unknown",
            issue_category=fi.get("issue_category", "File Validation"),
            issue_severity=fi.get("issue_severity", "Error"),
            issue_description=fi.get("issue_description", "Unknown file issue"),
            column_name=fi.get("column_name", ""),
            blocking_flag=fi.get("blocking_flag", "Blocking"),
            validation_issue_id=f"ISS-{upload_session_id}-FILE",
            upload_session_id=upload_session_id,
        )

    if issue_engine.has_blocking_issues():
        empty_df = pd.DataFrame()
        return {
            "file_info": {"filename": filename, "size_mb": 0, "checksum": ""},
            "detected_type": "Unknown",
            "dataset_type": dataset_type or "Unknown",
            "df_preview": empty_df,
            "issues": issue_engine.get_issues(),
            "scorecard": build_scorecard(issue_engine.get_issues(), dataset_type or "Unknown", empty_df, empty_df),
            "manifest": manifest_engine.build_manifest(),
            "schema_profile": schema_profile,
            "schema_version": get_schema_version(),
        }

    # 2. Read file
    try:
        df, read_error = read_uploaded_file(file_content, filename, max_rows_preview=MAX_PREVIEW_ROWS)
    except Exception as e:
        log_exception(upload_session_id, f"File read failed for {filename}: {e}")
        df, read_error = pd.DataFrame(), f"Unexpected read error: {e}"

    if read_error:
        issue_engine.add_issue(
            filename=filename,
            dataset_type=dataset_type or "Unknown",
            issue_category="File Read",
            issue_severity="Error",
            issue_description=read_error,
            column_name="",
            blocking_flag="Blocking",
            validation_issue_id=f"ISS-{upload_session_id}-READ",
            upload_session_id=upload_session_id,
        )
        empty_df = pd.DataFrame()
        return {
            "file_info": {"filename": filename, "size_mb": 0, "checksum": ""},
            "detected_type": "Unknown",
            "dataset_type": dataset_type or "Unknown",
            "df_preview": empty_df,
            "issues": issue_engine.get_issues(),
            "scorecard": build_scorecard(issue_engine.get_issues(), dataset_type or "Unknown", empty_df, empty_df),
            "manifest": manifest_engine.build_manifest(),
            "schema_profile": schema_profile,
            "schema_version": get_schema_version(),
        }

    # 3. Detect dataset type if not provided
    detected_type, confidence, reason = detect_dataset_type(filename, list(df.columns))
    if not dataset_type:
        dataset_type = detected_type

    # 4. Compute checksum
    try:
        raw_bytes = read_file_bytes(file_content)
        checksum = hashlib.sha256(raw_bytes).hexdigest()
    except Exception:
        checksum = ""

    file_info = {
        "filename": filename,
        "size_mb": len(raw_bytes) / (1024 * 1024),
        "checksum": checksum,
    }

    # 5. Load schema configs
    schema_df = load_schema_config(schema_profile)
    alias_df = load_alias_config(schema_profile)
    value_range_df = load_value_range_config(schema_profile)
    rule_df = load_validation_rule_config(schema_profile)
    category_df = load_category_config(schema_profile)

    # 6. Column alias mapping
    alias_map = build_alias_map(alias_df)
    mapping, _ = map_column_names(df, alias_map, schema_df, dataset_type)
    df_mapped = apply_column_mapping(df, mapping)

    # 7. Run all validations
    run_all_validations(
        df=df_mapped,
        dataset_type=dataset_type,
        filename=filename,
        issue_engine=issue_engine,
        schema_df=schema_df,
        value_range_df=value_range_df,
        rule_df=rule_df,
        category_df=category_df,
        upload_session_id=upload_session_id,
        schema_profile=schema_profile,
    )

    # 8. Deduplicate issues
    issue_engine.deduplicate()

    # 9. Build scorecard and manifest
    scorecard = build_scorecard(issue_engine.get_issues(), dataset_type, schema_df, df_mapped)
    manifest = manifest_engine.to_manifest_dict({"upload_session_id": upload_session_id})

    return {
        "file_info": file_info,
        "detected_type": detected_type,
        "dataset_type": dataset_type,
        "df_preview": df_mapped.head(20),
        "issues": issue_engine.get_issues(),
        "scorecard": scorecard,
        "manifest": manifest,
        "schema_profile": schema_profile,
        "schema_version": get_schema_version(),
        "authoritative_status": "Uploaded — Not Authoritative",
    }


def run_all_validations(
    df: pd.DataFrame,
    dataset_type: str,
    filename: str,
    issue_engine,
    schema_df: pd.DataFrame,
    value_range_df: pd.DataFrame,
    rule_df: pd.DataFrame,
    category_df: pd.DataFrame,
    upload_session_id: str = "",
    schema_profile: str = "GENERIC_UPLOAD",
    reference_data=None,
) -> None:
    """Run all 7 validation layers."""
    # Layer 1: Schema
    if not schema_df.empty:
        validate_schema(df, dataset_type, filename, issue_engine, upload_session_id, schema_profile)

    # Layer 2: Data types
    if not schema_df.empty:
        try:
            dt_issues = validate_datatypes(df, dataset_type, schema_df)
            dt_issues = _guard_list_of_dicts(dt_issues, "dt_issues", dataset_type, schema_profile)
            for i in dt_issues:
                issue_engine.add_issue(
                    filename=filename,
                    dataset_type=dataset_type,
                    issue_category=i.get("issue_category", "Data Type"),
                    issue_severity=i.get("issue_severity", "Error"),
                    issue_description=i.get("issue_description", ""),
                    column_name=i.get("column_name", ""),
                    blocking_flag=i.get("blocking_flag", "Non-blocking"),
                    validation_issue_id=f"ISS-{upload_session_id}-DT",
                    upload_session_id=upload_session_id,
                )
        except Exception as e:
            log_exception(upload_session_id, f"Datatype validation error: {e}")

    # Layer 3: Quality (missing values, nullable handling)
    try:
        validate_quality(df, dataset_type, filename, issue_engine, upload_session_id, schema_profile)
    except Exception as e:
        log_exception(upload_session_id, f"Quality validation error: {e}")

    # Layer 4: Value ranges
    if not value_range_df.empty:
        try:
            vr_issues = validate_value_ranges(df, dataset_type, value_range_df)
            vr_issues = _guard_list_of_dicts(vr_issues, "vr_issues", dataset_type, schema_profile)
            for i in vr_issues:
                issue_engine.add_issue(
                    filename=filename,
                    dataset_type=dataset_type,
                    issue_category=i.get("issue_category", "Value Range"),
                    issue_severity=i.get("issue_severity", "Error"),
                    issue_description=i.get("issue_description", ""),
                    column_name=i.get("column_name", ""),
                    blocking_flag=i.get("blocking_flag", "Non-blocking"),
                    validation_issue_id=f"ISS-{upload_session_id}-VR",
                    upload_session_id=upload_session_id,
                )
        except Exception as e:
            log_exception(upload_session_id, f"Value range validation error: {e}")

    # Layer 5: Dates
    if not schema_df.empty:
        try:
            date_issues = validate_dates(df, dataset_type, schema_df)
            date_issues = _guard_list_of_dicts(date_issues, "date_issues", dataset_type, schema_profile)
            for i in date_issues:
                issue_engine.add_issue(
                    filename=filename,
                    dataset_type=dataset_type,
                    issue_category=i.get("issue_category", "Invalid Date"),
                    issue_severity=i.get("issue_severity", "Error"),
                    issue_description=i.get("issue_description", ""),
                    column_name=i.get("column_name", ""),
                    blocking_flag=i.get("blocking_flag", "Non-blocking"),
                    validation_issue_id=f"ISS-{upload_session_id}-DATE",
                    upload_session_id=upload_session_id,
                )
        except Exception as e:
            log_exception(upload_session_id, f"Date validation error: {e}")

    # Layer 6: Identifiers (primary ID uniqueness only)
    try:
        validate_identifiers(df, dataset_type, filename, issue_engine, upload_session_id)
    except Exception as e:
        log_exception(upload_session_id, f"Identifier validation error: {e}")

    # Layer 7: Referential
    try:
        ref_issues = validate_referential(df, dataset_type, schema_df, reference_data)
        ref_issues = _guard_list_of_dicts(ref_issues, "ref_issues", dataset_type, schema_profile)
        for i in ref_issues:
            issue_engine.add_issue(
                filename=filename,
                dataset_type=dataset_type,
                issue_category=i.get("issue_category", "Referential Integrity"),
                issue_severity=i.get("issue_severity", "Error"),
                issue_description=i.get("issue_description", ""),
                column_name=i.get("column_name", ""),
                blocking_flag=i.get("blocking_flag", "Non-blocking"),
                validation_issue_id=f"ISS-{upload_session_id}-REF",
                upload_session_id=upload_session_id,
            )
    except Exception as e:
        log_exception(upload_session_id, f"Referential validation error: {e}")

    # Layer 8: Governance
    try:
        gov_issues = validate_governance(df, dataset_type, schema_df)
        gov_issues = _guard_list_of_dicts(gov_issues, "gov_issues", dataset_type, schema_profile)
        for i in gov_issues:
            issue_engine.add_issue(
                filename=filename,
                dataset_type=dataset_type,
                issue_category=i.get("issue_category", "Governance"),
                issue_severity=i.get("issue_severity", "Warning"),
                issue_description=i.get("issue_description", ""),
                column_name=i.get("column_name", ""),
                blocking_flag=i.get("blocking_flag", "Non-blocking"),
                validation_issue_id=f"ISS-{upload_session_id}-GOV",
                upload_session_id=upload_session_id,
            )
    except Exception as e:
        log_exception(upload_session_id, f"Governance validation error: {e}")
