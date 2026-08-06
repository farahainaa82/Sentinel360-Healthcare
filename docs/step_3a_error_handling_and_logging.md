# Step 3A — Error Handling and Logging

## Purpose
Document how errors are caught, logged, and presented to users.

## User-Facing Error Handling
- All file-parsing and validation exceptions are caught.
- User sees `st.error()` or `st.warning()` with a friendly message.
- Raw Python tracebacks are **never** exposed to the user.
- Error messages are short, actionable, and written in plain language.

## Technical Error Logging
- Technical details are written to `logs/streamlit_upload.log`.
- Log format: `timestamp - name - level - message`
- Log levels: INFO, WARNING, ERROR, DEBUG
- Exceptions include full traceback in the log file.

## Graceful Handling Scenarios
| Scenario | User Message | Log Level |
|---|---|---|
| Unsupported file type | "Unsupported file format. Please upload CSV or Excel." | Error |
| Empty file | "File is empty. Please upload a non-empty file." | Error |
| Corrupted workbook | "Cannot read Excel file. It may be corrupted." | Error |
| Missing required columns | "Required columns missing. See issues table." | Warning |
| Invalid data type | "Some fields contain invalid values." | Warning |
| Duplicate identifiers | "Duplicate primary keys detected." | Error |
| Encoding error | "File encoding not recognised." | Error |
| Large file | "File exceeds maximum size." | Error |

## Session Reset Safety
- Reset requires confirmation to prevent accidental data loss.
- Reset does not delete project files, frozen outputs, or configuration.
