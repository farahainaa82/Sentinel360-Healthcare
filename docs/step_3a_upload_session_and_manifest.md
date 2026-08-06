# Step 3A — Upload Session and Manifest

## Upload Session Model
Each Streamlit session creates one upload session with the following fields:

- `upload_session_id` — Unique session identifier (e.g., S3A-A1B2C3D4E5F6)
- `session_start_timestamp` — ISO timestamp when the session began
- `user_display_name` — Current user identity (default: Demo User)
- `file_count` — Number of uploaded files
- `total_row_count` — Sum of rows across all files
- `accepted_file_count` — Files with Accepted status
- `warning_file_count` — Files with Accepted with Warnings status
- `rejected_file_count` — Files with Rejected status
- `validation_status` — Overall validation state
- `processing_status` — New Data Uploaded / Validation Pending / Processing Required / Processing Complete
- `session_manifest_version` — 1.0
- `source_type` — Web Upload
- `governance_note` — Uploaded data is not authoritative until governed processing is completed

## File Metadata Model
One record per uploaded file:

- `upload_file_id` — Unique file identifier within the session
- `upload_session_id` — Parent session ID
- `original_filename` — Name as uploaded
- `detected_dataset_type` — Type inferred by the detection engine
- `confirmed_dataset_type` — Type confirmed by the user
- `file_extension` — csv, xlsx, or xls
- `file_size_bytes` — File size
- `sheet_name` — Excel sheet name (if applicable)
- `row_count` — Number of rows
- `column_count` — Number of columns
- `file_checksum` — SHA-256 hash of file content
- `encoding` — Detected encoding
- `upload_timestamp` — ISO timestamp
- `validation_status` — Accepted / Accepted with Warnings / Rejected / Not Yet Validated
- `authoritative_status` — Always "Uploaded — Not Authoritative"

## Manifest Export
- CSV validation summary
- CSV issue register
- JSON upload session manifest including all files and issues

## Reset Behaviour
- Clears upload session state, previews, metadata, issues, and results
- Creates a new upload session ID
- Does **not** delete project files, frozen outputs, or configuration
- Requires confirmation before executing
