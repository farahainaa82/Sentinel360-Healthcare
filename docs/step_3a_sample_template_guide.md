# Step 3A — Sample Template Guide

## Purpose
Describe how sample templates are generated and used.

## Template Generation
Templates are generated dynamically from `config/streamlit_upload_schema_config.csv`.

## Available Templates
1. Staff Roster
2. Staff Attendance
3. Patient Encounters
4. Bed Occupancy
5. Patient Queue
6. Patient Complaints
7. Patient Survey

## Template Structure
- One header row containing all governed field names (required + optional)
- One example row populated from the `example_value` column in schema config
- A note that the row is illustrative and not real data

## Download Format
- CSV (text/csv)
- Filename: `<dataset_type>_template.csv`

## Usage
Users can download templates before uploading their own data to ensure column names and formats align with Sentinel360 expectations.

## Governance
- Templates are derived from the governed schema configuration.
- No real patient or staff data is ever included.
