# Workforce Processing Report

## Step 2D-2 — Sentinel360 Healthcare

---

## 1. Processing Run ID

**PROC-5a10f77897bf**

---

## 2. Validation Run ID

**VAL-C62B370EC6C3**

---

## 3. Source Datasets Processed

| Dataset | Source Rows |
|---------|-------------|
| hospital_master | 1 |
| department_master | 8 |
| staff_role_master | 9 |
| staff_master | 180 |
| staff_roster | 41,495 |
| staff_attendance | 41,495 |
| staffing_requirement | 78,840 |

**Total source rows: 162,028**

---

## 4. Processed Row Counts

| Dataset | Processed Rows |
|---------|---------------|
| processed_hospital_master | 1 |
| processed_department_master | 8 |
| processed_staff_role_master | 9 |
| processed_staff_master | 180 |
| processed_staff_roster | 41,495 |
| processed_staff_attendance | 41,495 |
| processed_staffing_requirement | 78,840 |
| processed_workforce_daily | 26,280 |

**Total processed rows: 188,308**

---

## 5. Excluded Row Counts

| Dataset | Excluded Rows |
|---------|--------------|
| processed_hospital_master | 0 |
| processed_department_master | 0 |
| processed_staff_role_master | 0 |
| processed_staff_master | 0 |
| processed_staff_roster | 0 |
| processed_staff_attendance | 0 |
| processed_staffing_requirement | 0 |
| processed_workforce_daily | 0 |

**Total excluded rows: 0**

---

## 6. Issue Counts

| Severity | Count |
|----------|-------|
| Information | 0 |
| Warning | 0 |
| Error | 0 |
| Critical | 0 |

**Total issues: 0**

---

## 7. Configuration Versions

- Transformation Version: 2D-2.1.0
- Engine Version: 1.0.0
- Configuration: attendance_status_mapping.csv, absence_category_mapping.csv

---

## 8. Attendance Mapping Result

| Status | Count |
|--------|-------|
| Present | 35,131 |
| Absent | 2,527 |
| Late | 1,530 |
| Partial | 1,019 |
| Leave | 847 |
| Training | 441 |

**Total mapped: 41,495**

---

## 9. Absence Mapping Result

- Planned absence count: 0
- Absenteeism eligible count: 3,546
- Operational absenteeism hours: derived from lost_scheduled_hours for eligible records

---

## 10. Missing and Unknown Attendance Treatment

- Missing attendance count: 0
- Unknown attendance count: 0
- All source attendance records were successfully mapped to known statuses.
- No blank source statuses were present in the demo data.

---

## 11. Overnight Shift Result

- Overnight shift (N) count in demo data: 0
- All roster shifts in demo data are day shifts (M, A, E).
- Overnight handling logic is validated and ready for night-shift data.

---

## 12. Reassignment Result

- Reassigned records: 0
- No reassigned department IDs were present in the demo attendance data.
- Reassignment logic is validated structurally.

---

## 13. Replacement Staff Result

- Replacement staff references: 0
- No replacement_staff_id values were populated in the demo data.
- Replacement validation logic is validated structurally.

---

## 14. Workforce Daily Output Summary

| Metric | Value |
|--------|-------|
| Daily rows | 26,280 |
| Date range | 2026-01-01 to 2026-12-31 |
| Unique grain | 26,280 (no duplicates) |
| Rostered staff total | 41,495 |
| Verified available staff total | 37,680 |
| Absent events total | 3,546 |
| Missing attendance total | 0 |
| Unknown attendance total | 0 |

---

## 15. Lineage Coverage

- All 8 processed datasets have lineage records.
- Lineage covers 162,028 source records.
- Each processed record has at least one lineage row.

---

## 16. Source Checksum Verification

- All source checksums verified before and after processing.
- No source files were modified during processing.

---

## 17. Processed Schema Validation

- All 8 processed datasets passed schema validation.
- No prohibited fields (KPI, risk, forecast, scenario, financial, recommendation) were found.
- Primary key uniqueness verified where applicable.

---

## 18. Test Results

- `tests/test_workforce_transformation.py`: **69 passed, 0 failed**

---

## 19. Unresolved Rules

- None.

---

## 20. Known Limitations

- Workforce daily aggregation does not calculate KPI percentages.
- Demo data contains no overnight shifts; night-shift logic is code-validated.
- Demo data contains no reassigned or replacement records; logic is code-validated.
- Effective dates with unparseable values result in nulls.

---

## 21. Readiness for Step 2D-3

Step 2D-2 is complete and ready for Step 2D-3.

Prepared for Step 2D-3:

- Validated processed workforce datasets
- Daily workforce preparation totals
- Attendance and absence classification
- Department attribution
- Reassignment and replacement tracking
- Lineage and exclusion registers

Step 2D-3 is Patient Flow and Capacity Transformation and will process:

- processed_patient_encounters
- processed_patient_queue
- processed_bed_capacity
- processed_service_schedule
- processed_patient_flow_daily

Official KPI percentages, KPI status, trends, anomalies, risks, forecasts, scenarios and recommendations remain out of scope until their dedicated later steps.

---

## 22. Output Files

### Processed Datasets

- `data/processed/processed_hospital_master.csv`
- `data/processed/processed_department_master.csv`
- `data/processed/processed_staff_role_master.csv`
- `data/processed/processed_staff_master.csv`
- `data/processed/processed_staff_roster.csv`
- `data/processed/processed_staff_attendance.csv`
- `data/processed/processed_staffing_requirement.csv`
- `data/processed/processed_workforce_daily.csv`

### Control Outputs

- `outputs/logs/workforce_processing_run_manifest.json`
- `outputs/logs/workforce_processing_dataset_summary.csv`
- `outputs/logs/workforce_processing_issue_log.csv`
- `outputs/logs/workforce_processing_lineage.csv`
- `outputs/logs/workforce_processing_exclusion_register.csv`
- `outputs/logs/workforce_processing_audit_log.csv`
