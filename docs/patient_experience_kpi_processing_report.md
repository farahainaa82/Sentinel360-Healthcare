# Patient Experience KPI Processing Report

## Step 2A-4

---

## 1. Processing Run ID

`PEX-KPI-DCF120177644`

## 2. Processing Date and Time

- **Started**: 2026-07-27T14:43:24
- **Completed**: 2026-07-27T14:44:05

## 3. Source Files

| Source File | Rows |
|-------------|------|
| `data/processed/processed_operational_daily.csv` | 2,920 |
| `data/processed/processed_patient_complaints.csv` | 1,465 |
| `data/processed/processed_patient_surveys.csv` | 5,244 |

## 4. Source Row Counts

- **Operational daily**: 2,920
- **Patient complaints**: 1,465
- **Patient surveys**: 5,244
- **Total source rows**: 9,629

## 5. Source Checksums

| File | SHA-256 |
|------|---------|
| `processed_operational_daily.csv` | Baseline verified unchanged |
| `processed_patient_complaints.csv` | Baseline verified unchanged |
| `processed_patient_surveys.csv` | Baseline verified unchanged |

Source files were confirmed unchanged after processing.

## 6. KPI Result Counts

| KPI | ID | Records |
|-----|----|---------|
| Patient Complaint Rate | kpi_005 | 2,920 |
| Patient Satisfaction Score | kpi_006 | 2,920 |
| **Total** | | **5,840** |

## 7. Calculation Status Breakdown

| Status | Count |
|--------|-------|
| Calculated | 3,367 |
| Zero Denominator | 1,875 |
| Insufficient Data | 598 |
| Rule Pending | 0 |
| Invalid Input | 0 |

## 8. Complaint-Denominator Readiness

| Attribute | Value |
|-----------|-------|
| Denominator definition | encounter_record_count |
| Denominator source | processed_operational_daily.csv |
| Denominator field | encounter_record_count |
| Denominator unit | encounters |
| Approval status | Draft |
| Total eligible complaint records | 1,465 |
| Total denominator exposure | 93,958 |
| Duplicate complaint count | 0 |
| Invalid complaint count | 0 |
| Calculation readiness | Provisional but Calculable |
| Provisional status | True |

## 9. Satisfaction-Weighting Readiness

| Attribute | Value |
|-----------|-------|
| Score field | satisfaction_score_numeric |
| Response count field | response_count |
| Score scale | 1-5 |
| Score scale source | Observed and validated |
| Total survey responses | 24,181 |
| Total weighted score sum | 84,671 |
| Total valid score records | 2,621 |
| Total invalid score records | 0 |
| Calculation readiness | Calculable |

## 10. Exclusion Counts

340 exclusions generated.

## 11. Issue Counts by Severity

| Severity | Count |
|----------|-------|
| Information | 0 |
| Warning | 0 |
| Error | 0 |
| Critical | 0 |

Issues are generated as structured records, not by severity count. Total issue records: 3,457.

## 12. Formula Verification

| Metric | Value |
|--------|-------|
| Records checked | 3,367 |
| Matches | 3,367 |
| Mismatches | 0 |
| Max absolute difference | 0.0 |
| Unavailable records | 598 |
| Zero denominator records | 1,875 |
| Verification status | **Passed** |

## 13. Output Files

### 13.1 Analytical Outputs (6)

| File | Rows |
|------|------|
| `data/analytical/analytical_patient_experience_kpi_daily.csv` | 5,840 |
| `data/analytical/analytical_patient_experience_kpi_evidence.csv` | 5,840 |
| `data/analytical/analytical_patient_experience_kpi_exclusions.csv` | 340 |
| `data/analytical/analytical_patient_experience_kpi_lineage.csv` | 11,680 |
| `data/analytical/analytical_patient_experience_kpi_issues.csv` | 3,457 |
| `data/analytical/analytical_patient_experience_kpi_audit.csv` | 7 |

### 13.2 Control Outputs (14)

| File | Description |
|------|-------------|
| `outputs/analytical_patient_experience/patient_experience_kpi_run_manifest.json` | Run manifest |
| `outputs/analytical_patient_experience/patient_experience_kpi_calculation_summary.csv` | Calculation summary |
| `outputs/analytical_patient_experience/patient_experience_kpi_evidence_summary.csv` | Evidence summary |
| `outputs/analytical_patient_experience/patient_experience_kpi_exclusion_summary.csv` | Exclusion summary |
| `outputs/analytical_patient_experience/patient_experience_kpi_lineage_summary.csv` | Lineage summary |
| `outputs/analytical_patient_experience/patient_experience_kpi_issue_summary.csv` | Issue summary |
| `outputs/analytical_patient_experience/patient_experience_kpi_audit_summary.csv` | Audit summary |
| `outputs/analytical_patient_experience/patient_experience_kpi_formula_verification.csv` | Formula verification |
| `outputs/analytical_patient_experience/patient_experience_kpi_readiness_assessment.csv` | Readiness assessment |
| `outputs/analytical_patient_experience/patient_experience_kpi_threshold_status.csv` | Threshold status |
| `outputs/analytical_patient_experience/patient_experience_kpi_data_confidence.csv` | Data confidence |
| `outputs/analytical_patient_experience/patient_experience_kpi_immutability_verification.json` | Immutability verification |
| `outputs/analytical_patient_experience/patient_experience_kpi_end_to_end_test_results.json` | Test results |
| `outputs/analytical_patient_experience/patient_experience_kpi_acceptance_evidence.json` | Acceptance evidence |

## 14. Schema Results

| Dataset | Result |
|---------|--------|
| analytical_patient_experience_kpi_daily | Pass |
| analytical_patient_experience_kpi_evidence | Pass |
| analytical_patient_experience_kpi_exclusions | Pass |
| analytical_patient_experience_kpi_lineage | Pass |
| analytical_patient_experience_kpi_issues | Pass |
| analytical_patient_experience_kpi_audit | Pass |

## 15. Daily-Grain Result

- **Daily IDs unique**: Yes
- **Hospital-department-date grain unique**: Yes
- **Deterministic ID format**: `AKPI-{kpi_id}-{hospital_id}-{department_id}-{YYYYMMDD}`

## 16. Lineage Coverage

- **Lineage records**: 11,680
- **Coverage**: 100% of KPI results (2 records per result: numerator and denominator)

## 17. Source Immutability

Source checksums matched before and after processing.

## 18. Prior Analytical-Data Immutability

All prior accepted analytical datasets were confirmed unchanged:
- analytical_workforce_kpi_daily.csv
- analytical_workforce_kpi_evidence.csv
- analytical_workforce_kpi_exclusions.csv
- analytical_workforce_kpi_lineage.csv
- analytical_workforce_kpi_issues.csv
- analytical_workforce_kpi_audit.csv
- analytical_patient_flow_kpi_daily.csv
- analytical_patient_flow_kpi_evidence.csv
- analytical_patient_flow_kpi_exclusions.csv
- analytical_patient_flow_kpi_lineage.csv
- analytical_patient_flow_kpi_issues.csv
- analytical_patient_flow_kpi_audit.csv

## 19. Test Results

| Test Suite | Tests | Passed | Failed |
|------------|-------|--------|--------|
| test_patient_experience_kpi_engine.py | 38 | 38 | 0 |

## 20. Governance Status

| Attribute | Value |
|-----------|-------|
| Threshold version | v1.0-draft |
| Threshold approval status | Draft |
| Threshold is provisional | True (all records) |
| Confidence rule version | v1.0-draft |
| Configuration version | v1.0-draft |

## 21. Known Limitations

- operational_daily survey aggregation truncates weighted sums to integers (known Phase 1 characteristic).
- 598 operational daily rows have null PX data (no complaint or survey records for that grain).
- All thresholds and confidence rules are provisional (v1.0-draft).
- No trend, anomaly, forecast, or recommendation logic is included.

## 22. Unresolved Business Rules

The following rules remain Pending Review and do not block analytical calculation:

- Official complaint-rate denominator approval
- Complaint inclusion and exclusion rules for official KPI
- Whether reopened complaints count once or multiple times
- Official complaint severity weighting
- Official complaint status treatment
- Official satisfaction-score scale approval
- Satisfaction-score normalisation method
- Minimum survey response threshold
- Handling of mixed survey scales
- Official KPI reporting grain

## 23. Final Processing Status

**Completed**

All mandatory checks pass:
- All required files exist
- All three source datasets loaded
- 6 analytical datasets exported
- 14 control outputs exported
- Schemas pass
- Daily grain passes
- Formula verification passes
- Source checksums pass
- Prior analytical datasets remain unchanged
- Tests pass
- Unresolved rules are documented
- Governance status is preserved

## 24. Readiness for Next Step

Step 2A-4 is complete and ready for:

**Step 2A-5 — Integration of Remaining KPIs or Analytical Layer Closure**

Step 2A-5 may integrate additional KPIs, perform cross-domain consistency checks, or formally close the analytical layer.
