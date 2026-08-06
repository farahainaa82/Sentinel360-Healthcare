# Step 3A — Demo Data Usage

## Purpose
Explain how synthetic demo data is integrated into the upload page.

## Demo Data Location
Synthetic datasets are located in `data/demo/` and include:
- staff_roster.csv
- staff_attendance.csv
- patient_encounters.csv
- bed_capacity_records.csv
- patient_queue_records.csv
- patient_complaints.csv
- patient_surveys.csv

## Demo Data Selector
The page provides two options:
1. **Upload My Own Files** — Standard drag-and-drop uploader
2. **Use Existing Synthetic Demo Files** — Checkboxes to select available demo files

## Demo Data Handling
- Demo files are loaded from their existing paths on disk.
- The page shows that they are demo/synthetic data.
- Demo files are validated using the same engine as user-uploaded files.
- Demo files and user-uploaded files are **not mixed silently**.
- The `demo` flag is tracked in session state separately.

## Validation of Demo Files
- All validation layers apply to demo files equally.
- Issues, scorecards, and metadata are generated the same way.
- Demo files are marked as **Not Authoritative** like all uploaded data.

## Sample Templates
- Downloadable CSV templates are generated from governed schema configuration.
- Each template contains headers and one illustrative example row.
- No real patient or staff data is included.
