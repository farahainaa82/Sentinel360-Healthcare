# Step 3A — Streamlit State Management

## Purpose
Document how `st.session_state` is used in the Data Upload and Validation page.

## State Keys
| Key | Type | Purpose |
|---|---|---|
| `upload_session_id` | str | Unique session identifier |
| `upload_timestamp` | str | Session start ISO timestamp |
| `uploaded_files` | dict | Registry of uploaded file bytes |
| `file_metadata` | dict | Metadata record per file |
| `validation_issues` | dict | Issue list per file |
| `validation_scorecards` | dict | Scorecard list per file |
| `confirmed_dataset_types` | dict | User-confirmed type per file |
| `validation_completed` | bool | Whether validation has been run |
| `processing_status` | str | Current processing status |
| `validation_status` | str | Overall validation status |
| `selected_preview_file` | str | Currently selected file for preview |
| `preview_row_count` | int | Number of rows to preview |

## Persistence Rules
- Uploaded data persists when the user changes select boxes or tabs.
- Validation results persist until Reset Upload Session is clicked.
- Session state is not lost on widget interactions because explicit buttons trigger validation and reset, not widget changes.

## Reset Behaviour
- Reset clears only upload-session keys.
- Frozen outputs and project configuration are untouched.
- A new `upload_session_id` and `upload_timestamp` are generated.

## Performance
- Schema configuration is loaded once per session and cached where possible.
- Validation is triggered by an explicit button, not by every widget interaction.
- File bytes are stored in memory; large files are validated in chunks conceptually.
