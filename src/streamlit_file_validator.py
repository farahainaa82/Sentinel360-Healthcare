"""File-level validator (extension, emptiness, encoding, corruption)."""

import io
import pandas as pd
from typing import Dict, List, Any, Optional
from .streamlit_file_reader import detect_file_extension, is_supported_extension, get_excel_sheet_names


def validate_file(
    file_bytes: bytes,
    filename: str,
    max_size_mb: int = 200,
) -> List[Dict[str, Any]]:
    """Validate file-level properties. Return list of issue dicts."""
    issues = []
    ext = detect_file_extension(filename)

    if not ext:
        issues.append(_issue("File Format", "Error", "File has no extension.", filename, True))
    elif not is_supported_extension(ext):
        issues.append(_issue("File Format", "Error", f"Unsupported extension: {ext}", filename, True))

    if len(file_bytes) == 0:
        issues.append(_issue("Empty File", "Error", "File is empty.", filename, True))
        return issues

    if len(file_bytes) > max_size_mb * 1024 * 1024:
        issues.append(_issue("File Format", "Error", f"File exceeds {max_size_mb} MB limit.", filename, True))

    if ext in ("xlsx", "xls"):
        try:
            sheets = get_excel_sheet_names(file_bytes)
            if not sheets:
                issues.append(_issue("Corrupted File", "Error", "Excel workbook has no readable sheets.", filename, True))
        except Exception as e:
            issues.append(_issue("Corrupted File", "Error", f"Cannot read Excel workbook: {e}", filename, True))
    elif ext == "csv":
        try:
            sample = file_bytes[:4096].decode("utf-8", errors="replace")
            if not sample.strip():
                issues.append(_issue("Empty File", "Error", "CSV file contains no readable content.", filename, True))
        except Exception as e:
            issues.append(_issue("Encoding", "Error", f"Encoding error: {e}", filename, True))

    return issues


def _issue(category: str, severity: str, description: str, filename: str, blocking: bool) -> Dict[str, Any]:
    return {
        "issue_category": category,
        "issue_severity": severity,
        "issue_description": description,
        "filename": filename,
        "blocking_flag": "Blocking" if blocking else "Non-Blocking",
    }
