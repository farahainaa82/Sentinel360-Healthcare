# Patient Experience Processing Report

## Step 2D-4

---

## 1. Processing Run ID

`PROC-PEX-A295C4F2E233`

## 2. Processing Date and Time

- **Started**: 2026-07-26T21:50:13
- **Completed**: 2026-07-26T21:50:30

## 3. Source Files

| Source File | Rows |
|-------------|------|
| `data/demo/patient_complaints.csv` | 1,465 |
| `data/demo/patient_surveys.csv` | 5,244 |

## 4. Source Row Counts

- **Patient complaints**: 1,465
- **Patient surveys**: 5,244
- **Total source rows**: 6,709

## 5. Source Checksums

| File | SHA-256 |
|------|---------|
| `patient_complaints.csv` | `4a3f9430e969cdb6c67c257f45e535f0fc87d0e13638d13fab35e2f14d6f5749` |
| `patient_surveys.csv` | `abda74db75741729279c403e66181b5464451fc12af22b76e43e6e8dc8d1e58b` |

Source files were confirmed unchanged after processing.

## 6. Processed Complaint Row Count

1,465 rows exported to `data/processed/processed_patient_complaints.csv`

## 7. Processed Survey Row Count

5,244 rows exported to `data/processed/processed_patient_surveys.csv`

## 8. Daily Patient-Experience Row Count

2,621 rows exported to `data/processed/processed_patient_experience_daily.csv`

## 9. Exclusion Counts

0 exclusions generated.

All source records passed validation and were retained.

## 10. Issue Counts by Severity

| Severity | Count |
|----------|-------|
| Information | 0 |
| Warning | 0 |
| Error | 0 |
| Critical | 0 |

## 11. Complaint-Category Summary

| Category | Count |
|----------|-------|
| Staff Behaviour | 203 |
| Waiting Time | 189 |
| Facilities | 188 |
| Communication | 181 |
| Safety | 180 |
| Billing | 179 |
| Other | 175 |
| Clinical Care | 170 |

## 12. Complaint-Channel Summary

| Channel | Count |
|---------|-------|
| Third Party | 224 |
| Walk-In | 222 |
| Phone | 215 |
| Formal Letter | 210 |
| Social Media | 206 |
| Online Portal | 200 |
| Email | 188 |

## 13. Complaint-Severity Summary

| Severity | Count |
|----------|-------|
| Medium | 603 |
| Low | 530 |
| High | 265 |
| Critical | 67 |

## 14. Survey-Channel Summary

Survey channel is not present in the source dataset. `survey_channel` is null for all records.

## 15. Survey-Type Summary

| Type | Count |
|------|-------|
| Outpatient Satisfaction | 5,244 |

## 16. Survey-Score Scale Summary

| Scale ID | Min | Max | Records |
|----------|-----|-----|---------|
| SCALE-5PT | 1 | 5 | 5,244 |

## 17. Response-Count Summary

- All source records have `response_weight` = 1.0.
- No missing response counts.
- No negative response counts.

## 18. Duplicate-Key Results

- **Duplicate complaint IDs**: 0
- **Duplicate survey IDs**: 0

## 19. Reference-Validation Results

| Relationship | Total | Valid | Invalid | Orphans | Status |
|--------------|-------|-------|---------|---------|--------|
| complaints_to_hospital | 1,465 | 1,465 | 0 | 0 | OK |
| complaints_to_department | 1,465 | 1,465 | 0 | 0 | OK |
| surveys_to_hospital | 5,244 | 5,244 | 0 | 0 | OK |
| surveys_to_department | 5,244 | 5,244 | 0 | 0 | OK |

## 20. Schema Results

| Dataset | Result |
|---------|--------|
| processed_patient_complaints | Pass |
| processed_patient_surveys | Pass |
| processed_patient_experience_daily | Pass |

## 21. Daily-Grain Result

- **Daily IDs unique**: Yes
- **Hospital-department-date grain unique**: Yes
- **Deterministic ID format**: `PEX-{hospital_id}-{department_id}-{YYYYMMDD}`

## 22. Lineage Coverage

- **Record-level lineage records**: 13,418
- **Complaint output coverage**: 100%
- **Survey output coverage**: 100%
- **Daily output coverage**: 100%

## 23. Relationship Results

| Relationship | Total Records | Valid | Invalid | Orphans | Status |
|--------------|---------------|-------|---------|---------|--------|
| daily_to_complaints | 2,621 | 1,166 | 0 | 0 | OK |
| daily_to_surveys | 2,621 | 2,441 | 0 | 0 | OK |

## 24. Source Immutability

Source checksums matched before and after processing:
- `patient_complaints.csv`: unchanged
- `patient_surveys.csv`: unchanged

## 25. Prior Processed-Data Immutability

All prior accepted processed datasets were confirmed unchanged:
- processed_staff_roster.csv
- processed_staff_attendance.csv
- processed_staffing_requirement.csv
- processed_workforce_daily.csv
- processed_patient_encounters.csv
- processed_patient_queue.csv
- processed_bed_capacity.csv
- processed_service_schedule.csv
- processed_patient_flow_daily.csv

## 26. Test Results

| Test Suite | Tests | Passed | Failed |
|------------|-------|--------|--------|
| test_patient_experience_transformation.py | 73 | 73 | 0 |
| test_processing_architecture.py | 50 | 50 | 0 |
| test_step_2d3_closure.py | 45 | 45 | 0 |

## 27. Unresolved Business Rules

The following rules remain Pending Review and do not block preparation-level processing:

- Official complaint-rate denominator
- Complaint inclusion and exclusion rules for official KPI
- Whether reopened complaints count once or multiple times
- Official complaint severity weighting
- Official complaint status treatment
- Official satisfaction-score scale
- Satisfaction-score normalisation method
- Satisfaction-score weighting by response count
- Minimum survey response threshold
- Handling of mixed survey scales
- Official KPI reporting grain
- Treatment of missing departments
- Treatment of anonymous surveys
- Relationship between survey responses and encounters

## 28. Known Limitations

- Survey channel is not present in the source dataset; `survey_channel` is null for all records.
- Survey score normalisation is not applied because official scale rules are unresolved.
- All source response weights are 1.0 in the demo data.
- No encounter-linked surveys exist in the demo data.

## 29. Final Processing Status

**Completed**

All mandatory checks pass:
- All required files exist
- Both source datasets processed
- All three processed datasets exported
- Schemas pass
- Business keys pass
- Daily grain passes
- Source checksums pass
- Prior processed datasets remain unchanged
- Tests pass
- Unresolved official KPI rules are documented

## 30. Readiness for Next Step

Step 2D-4 is complete and ready for:

**Step 2D-5 — Final Processing Integration and Preparation-Layer Closure**

Step 2D-5 may consolidate workforce, patient-flow and patient-experience processed datasets; verify cross-domain references; verify combined lineage; verify all preparation-level schemas; and formally close the processing layer. Step 2D-5 must still not calculate official KPI values or KPI status.
