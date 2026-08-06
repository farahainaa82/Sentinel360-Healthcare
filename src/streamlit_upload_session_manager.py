"""Upload session manager for Sentinel360 Streamlit upload page."""

import uuid
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional


class UploadSessionManager:
    """Manages upload session state and metadata."""

    @staticmethod
    def create_session(user_display_name: str = "Demo User") -> Dict[str, Any]:
        """Create a new upload session record."""
        session_id = f"S3A-{uuid.uuid4().hex[:12].upper()}"
        return {
            "upload_session_id": session_id,
            "session_start_timestamp": datetime.now().isoformat(),
            "user_display_name": user_display_name,
            "file_count": 0,
            "total_row_count": 0,
            "accepted_file_count": 0,
            "warning_file_count": 0,
            "rejected_file_count": 0,
            "validation_status": "Not Yet Validated",
            "processing_status": "New Data Uploaded",
            "session_manifest_version": "1.0",
            "source_type": "Web Upload",
            "governance_note": "Uploaded data is not authoritative until governed processing is completed.",
        }

    @staticmethod
    def update_session_counts(session: Dict[str, Any], files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Recalculate session counts from file metadata."""
        if not session:
            return session
        session["file_count"] = len(files)
        session["total_row_count"] = sum(f.get("row_count", 0) for f in files)
        session["accepted_file_count"] = sum(1 for f in files if f.get("validation_status") == "Accepted")
        session["warning_file_count"] = sum(1 for f in files if f.get("validation_status") == "Accepted with Warnings")
        session["rejected_file_count"] = sum(1 for f in files if f.get("validation_status") == "Rejected")
        return session

    @staticmethod
    def compute_file_checksum(content_bytes: bytes) -> str:
        """Compute SHA-256 checksum of file bytes."""
        return hashlib.sha256(content_bytes).hexdigest()

    @staticmethod
    def get_overall_session_status(session: Dict[str, Any], files: List[Dict[str, Any]]) -> str:
        """Determine overall upload session readiness."""
        if not files:
            return "Not Assessable"
        statuses = [f.get("validation_status") for f in files]
        if any(s == "Rejected" for s in statuses):
            return "Correction Required"
        if all(s == "Accepted" for s in statuses):
            return "All Required Files Ready"
        if any(s == "Accepted with Warnings" for s in statuses) and all(s in ("Accepted", "Accepted with Warnings") for s in statuses):
            return "Ready with Warnings"
        return "Incomplete Required Dataset Set"
