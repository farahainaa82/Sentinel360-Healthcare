"""File reading utilities with robust encoding and error handling."""

import os
from io import BytesIO
from typing import Tuple, Optional
import pandas as pd


def detect_file_extension(filename: str) -> str:
    """Return lower-case file extension without dot."""
    _, ext = os.path.splitext(filename)
    return ext.lstrip(".").lower()


def is_supported_extension(ext: str) -> bool:
    """Check if extension is supported."""
    return ext in ("csv", "xlsx", "xls")


def get_excel_sheet_names(content: bytes) -> list:
    """Return sheet names from Excel workbook."""
    try:
        bio = BytesIO(content)
        return pd.ExcelFile(bio).sheet_names
    except Exception:
        return []


def read_file_bytes(content) -> bytes:
    """Normalize input to bytes, ensuring seek(0) if file-like."""
    if isinstance(content, bytes):
        return content
    if hasattr(content, "read"):
        if hasattr(content, "seek"):
            content.seek(0)
        data = content.read()
        if isinstance(data, str):
            data = data.encode("utf-8")
        return data
    if isinstance(content, str):
        return content.encode("utf-8")
    raise TypeError(f"Unsupported content type: {type(content)}")


def read_uploaded_file(content, filename: str, max_rows_preview: int = 1000) -> Tuple[pd.DataFrame, str]:
    """Read uploaded file content into DataFrame.

    Args:
        content: bytes, file-like, or string content
        filename: original filename for extension detection
        max_rows_preview: maximum rows to read for preview

    Returns:
        (DataFrame, error_message)
    """
    try:
        raw_bytes = read_file_bytes(content)
    except Exception as e:
        return pd.DataFrame(), f"Failed to read file bytes: {e}"

    ext = detect_file_extension(filename)
    if not is_supported_extension(ext):
        return pd.DataFrame(), f"Unsupported file extension: {ext}"

    if ext == "csv":
        return _read_csv(raw_bytes, max_rows_preview)
    elif ext in ("xlsx", "xls"):
        return _read_excel(raw_bytes, max_rows_preview)

    return pd.DataFrame(), f"Unsupported file extension: {ext}"


def _read_csv(raw_bytes: bytes, max_rows: int) -> Tuple[pd.DataFrame, str]:
    """Read CSV bytes with encoding fallback."""
    encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252", "iso-8859-1"]
    last_error = ""
    for encoding in encodings:
        try:
            bio = BytesIO(raw_bytes)
            df = pd.read_csv(bio, nrows=max_rows, encoding=encoding, low_memory=False)
            if df.empty:
                # Check if file actually has content
                text = raw_bytes.decode(encoding, errors="replace")
                lines = [l for l in text.splitlines() if l.strip()]
                if len(lines) <= 1:
                    return pd.DataFrame(), "CSV file is empty or contains only a header row"
            return df, ""
        except Exception as e:
            last_error = str(e)
            continue
    return pd.DataFrame(), f"Failed to read CSV with all encodings. Last error: {last_error}"


def _read_excel(raw_bytes: bytes, max_rows: int) -> Tuple[pd.DataFrame, str]:
    """Read Excel bytes."""
    try:
        bio = BytesIO(raw_bytes)
        sheet_names = pd.ExcelFile(bio).sheet_names
        if not sheet_names:
            return pd.DataFrame(), "Excel file contains no sheets"
        bio.seek(0)
        df = pd.read_excel(bio, sheet_name=sheet_names[0], nrows=max_rows)
        return df, ""
    except Exception as e:
        return pd.DataFrame(), f"Failed to read Excel: {e}"
