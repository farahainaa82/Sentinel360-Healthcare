"""Upload manifest engine for session and file metadata records."""

import uuid
import pandas as pd
from typing import Dict, List, Any
from datetime import datetime


class UploadManifestEngine:
    """Manages upload session manifest and file metadata records."""

    def __init__(self, session_id: str = ""):
        self.session_id = session_id
        self.files: List[Dict[str, Any]] = []

    def add_file_metadata(
        self,
        original_filename: str,
        detected_dataset_type: str,
        confirmed_dataset_type: str,
        file_extension: str,
        file_size_bytes: int,
        sheet_name: str = "",
        row_count: int = 0,
        column_count: int = 0,
        file_checksum: str = "",
        encoding: str = "utf-8",
        validation_status: str = "Not Yet Validated",
        authoritative_status: str = "Uploaded — Not Authoritative",
    ) -> Dict[str, Any]:
        """Add a file metadata record."""
        file_id = f"FIL-{self.session_id}-{len(self.files)+1:04d}"
        record = {
            "upload_file_id": file_id,
            "upload_session_id": self.session_id,
            "original_filename": original_filename,
            "detected_dataset_type": detected_dataset_type,
            "confirmed_dataset_type": confirmed_dataset_type,
            "file_extension": file_extension,
            "file_size_bytes": file_size_bytes,
            "sheet_name": sheet_name,
            "row_count": row_count,
            "column_count": column_count,
            "file_checksum": file_checksum,
            "encoding": encoding,
            "upload_timestamp": datetime.now().isoformat(),
            "validation_status": validation_status,
            "authoritative_status": authoritative_status,
        }
        self.files.append(record)
        return record

    def to_manifest_dict(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Export full session manifest as dictionary."""
        return {
            "upload_session_id": session.get("upload_session_id", self.session_id),
            "session_start_timestamp": session.get("session_start_timestamp", ""),
            "user_display_name": session.get("user_display_name", "Demo User"),
            "file_count": len(self.files),
            "total_row_count": sum(f.get("row_count", 0) for f in self.files),
            "accepted_file_count": sum(1 for f in self.files if f.get("validation_status") == "Accepted"),
            "warning_file_count": sum(1 for f in self.files if f.get("validation_status") == "Accepted with Warnings"),
            "rejected_file_count": sum(1 for f in self.files if f.get("validation_status") == "Rejected"),
            "validation_status": session.get("validation_status", "Not Yet Validated"),
            "processing_status": session.get("processing_status", "New Data Uploaded"),
            "session_manifest_version": session.get("session_manifest_version", "1.0"),
            "source_type": session.get("source_type", "Web Upload"),
            "governance_note": session.get("governance_note", ""),
            "files": self.files,
        }

    def to_dataframe(self) -> pd.DataFrame:
        """Export file metadata as DataFrame."""
        if not self.files:
            return pd.DataFrame(columns=[
                "upload_file_id", "upload_session_id", "original_filename",
                "detected_dataset_type", "confirmed_dataset_type", "file_extension",
                "file_size_bytes", "sheet_name", "row_count", "column_count",
                "file_checksum", "encoding", "upload_timestamp", "validation_status", "authoritative_status"
            ])
        return pd.DataFrame(self.files)

    def clear(self):
        """Clear all file records."""
        self.files = []
