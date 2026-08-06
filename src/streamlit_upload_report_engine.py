"""Upload report engine for CSV and JSON downloads."""

import json
import io
import pandas as pd
from typing import Dict, List, Any


class UploadReportEngine:
    """Generates downloadable validation reports and summaries."""

    @staticmethod
    def build_validation_summary(files: List[Dict[str, Any]], issues: List[Dict[str, Any]]) -> pd.DataFrame:
        """Build validation summary DataFrame from file metadata and issues."""
        rows = []
        for f in files:
            fname = f["original_filename"]
            fissues = [i for i in issues if i["filename"] == fname]
            blocking = [i for i in fissues if i.get("blocking_flag") == "Blocking"]
            warnings = [i for i in fissues if i.get("issue_severity") == "Warning" and i.get("blocking_flag") != "Blocking"]
            errors = [i for i in fissues if i.get("issue_severity") == "Error"]
            rows.append({
                "filename": fname,
                "dataset_type": f.get("confirmed_dataset_type", ""),
                "row_count": f.get("row_count", 0),
                "column_count": f.get("column_count", 0),
                "schema_status": "Pass" if not any(i["issue_category"] in ("Missing Column", "Schema") for i in errors) else "Fail",
                "data_type_status": "Pass" if not any(i["issue_category"] == "Data Type" for i in errors) else "Fail",
                "missing_value_status": "Pass" if not any(i["issue_category"] == "Missing Value" for i in fissues) else "Warning",
                "duplicate_status": "Pass" if not any(i["issue_category"] == "Duplicate Record" for i in fissues) else "Warning",
                "date_validation_status": "Pass" if not any(i["issue_category"] in ("Invalid Date", "Date Range") for i in errors) else "Fail",
                "identifier_status": "Pass" if not any(i["issue_category"] == "Invalid Identifier" for i in errors) else "Fail",
                "value_range_status": "Pass" if not any(i["issue_category"] == "Value Range" for i in errors) else "Fail",
                "referential_integrity_status": "Not Assessable" if any(i["issue_category"] == "Referential Integrity" and i["issue_severity"] == "Informational" for i in fissues) else ("Pass" if not any(i["issue_category"] == "Referential Integrity" for i in errors) else "Fail"),
                "overall_status": f.get("validation_status", "Not Yet Validated"),
                "issue_count": len(fissues),
                "warning_count": len(warnings),
                "error_count": len(errors),
                "blocking_count": len(blocking),
            })
        return pd.DataFrame(rows)

    @staticmethod
    def to_csv(df: pd.DataFrame) -> str:
        """Convert DataFrame to CSV string."""
        return df.to_csv(index=False)

    @staticmethod
    def to_json(data: Dict[str, Any]) -> str:
        """Convert dict to JSON string."""
        return json.dumps(data, indent=2, default=str)

    @staticmethod
    def build_manifest_json(session: Dict[str, Any], files: List[Dict[str, Any]], issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build full upload session manifest."""
        return {
            "upload_session_id": session.get("upload_session_id", ""),
            "session_start_timestamp": session.get("session_start_timestamp", ""),
            "user_display_name": session.get("user_display_name", ""),
            "file_count": len(files),
            "total_row_count": sum(f.get("row_count", 0) for f in files),
            "accepted_file_count": sum(1 for f in files if f.get("validation_status") == "Accepted"),
            "warning_file_count": sum(1 for f in files if f.get("validation_status") == "Accepted with Warnings"),
            "rejected_file_count": sum(1 for f in files if f.get("validation_status") == "Rejected"),
            "validation_status": session.get("validation_status", ""),
            "processing_status": session.get("processing_status", ""),
            "session_manifest_version": session.get("session_manifest_version", "1.0"),
            "source_type": session.get("source_type", "Web Upload"),
            "governance_note": session.get("governance_note", ""),
            "files": files,
            "issues": issues,
        }
