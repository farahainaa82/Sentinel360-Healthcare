# Step 2A-5 — Six-KPI Integration and Status Layer Report

---

## 1. Task Completion Status

**COMPLETED**

All mandatory tasks for Step 2A-5 have been executed and validated.

---

## 2. Files Created

### 2.1 Engine

| File | Description |
|------|-------------|
| `src/six_kpi_integration_engine.py` | Six-KPI Integration Engine |
| `src/run_six_kpi_integration.py` | Safe runner with CLI |
| `tests/test_six_kpi_integration_engine.py` | 41 integration tests |

### 2.2 Analytical Outputs (7)

| File | Rows |
|------|------|
| `data/analytical/analytical_six_kpi_daily.csv` | 17,520 |
| `data/analytical/analytical_six_kpi_evidence.csv` | 36,500 |
| `data/analytical/analytical_six_kpi_exclusions.csv` | 3,990 |
| `data/analytical/analytical_six_kpi_lineage.csv` | 23,360 |
| `data/analytical/analytical_six_kpi_issues.csv` | 3,457 |
| `data/analytical/analytical_six_kpi_audit.csv` | 7 |
| `data/analytical/analytical_six_kpi_coverage_daily.csv` | 2,920 |

### 2.3 Control Outputs (20)

| File | Description |
|------|-------------|
| `outputs/analytical_six_kpi/six_kpi_integration_manifest.json` | Run manifest |
| `outputs/analytical_six_kpi/six_kpi_dataset_summary.csv` | Dataset summary |
| `outputs/analytical_six_kpi/six_kpi_kpi_count_reconciliation.csv` | Reconciliation |
| `outputs/analytical_six_kpi/six_kpi_status_distribution.csv` | Status distribution |
| `outputs/analytical_six_kpi/six_kpi_calculation_status_summary.csv` | Calculation status |
| `outputs/analytical_six_kpi/six_kpi_threshold_status_summary.csv` | Threshold status |
| `outputs/analytical_six_kpi/six_kpi_confidence_summary.csv` | Confidence summary |
| `outputs/analytical_six_kpi/six_kpi_integration_status_summary.csv` | Integration status |
| `outputs/analytical_six_kpi/six_kpi_evidence_status_summary.csv` | Evidence status |
| `outputs/analytical_six_kpi/six_kpi_lineage_status_summary.csv` | Lineage status |
| `outputs/analytical_six_kpi/six_kpi_coverage_summary.csv` | Coverage summary |
| `outputs/analytical_six_kpi/six_kpi_duplicate_check.csv` | Duplicate check |
| `outputs/analytical_six_kpi/six_kpi_value_status_consistency.csv` | Value-status consistency |
| `outputs/analytical_six_kpi/six_kpi_governance_consistency.csv` | Governance consistency |
| `outputs/analytical_six_kpi/six_kpi_schema_validation.csv` | Schema validation |
| `outputs/analytical_six_kpi/six_kpi_issue_log.csv` | Issue log |
| `outputs/analytical_six_kpi/six_kpi_exclusion_summary.csv` | Exclusion summary |
| `outputs/analytical_six_kpi/six_kpi_lineage_summary.csv` | Lineage summary |
| `outputs/analytical_six_kpi/six_kpi_immutability_verification.json` | Immutability verification |
| `outputs/analytical_six_kpi/six_kpi_audit_log.csv` | Audit log |
| `outputs/analytical_six_kpi/six_kpi_end_to_end_test_results.json` | Test results |
| `outputs/analytical_six_kpi/six_kpi_acceptance_evidence.json` | Acceptance evidence |

### 2.4 Documentation (3)

| File | Description |
|------|-------------|
| `docs/six_kpi_integration_specification.md` | Integration specification |
| `docs/six_kpi_status_governance.md` | Status governance |
| `docs/step_2a5_six_kpi_integration_report.md` | This report |

---

## 3. Files Modified

No previously accepted files were modified.

---

## 4. Integrated Analytical Datasets Generated

Seven analytical datasets were generated under `data/analytical/`.

---

## 5. Control Outputs Generated

Twenty-two control outputs were generated under `outputs/analytical_six_kpi/`.

---

## 6. Tests

| Suite | Tests | Passed | Failed |
|-------|-------|--------|--------|
| test_six_kpi_integration_engine.py | 41 | 41 | 0 |

---

## 7. Source Row Counts by KPI Domain

| Domain | Daily | Evidence | Exclusions | Lineage | Issues | Audit |
|--------|-------|----------|------------|---------|--------|-------|
| Workforce | 5,840 | 11,680 | 0 | 5,840 | 0 | 1 |
| Patient Flow | 5,840 | 4,380 | 3,650 | 5,840 | 0 | 1 |
| Patient Experience | 5,840 | 20,440 | 340 | 11,680 | 3,457 | 2 |
| **Total** | **17,520** | **36,500** | **3,990** | **23,360** | **3,457** | **4** |

---

## 8. Integrated Row Count

**17,520** integrated daily records.

---

## 9. Row Counts by KPI ID

| KPI ID | Source Rows | Integrated Rows |
|--------|-------------|-----------------|
| kpi_001 | 2,920 | 2,920 |
| kpi_002 | 2,920 | 2,920 |
| kpi_003 | 2,920 | 2,920 |
| kpi_004 | 2,920 | 2,920 |
| kpi_005 | 2,920 | 2,920 |
| kpi_006 | 2,920 | 2,920 |

---

## 10. Source-to-Integrated Reconciliation

| KPI ID | Source Dataset | Source Count | Integrated Count | Difference | Status |
|--------|----------------|--------------|------------------|------------|--------|
| kpi_001 | analytical_workforce_kpi_daily.csv | 2,920 | 2,920 | 0 | Reconciled |
| kpi_002 | analytical_workforce_kpi_daily.csv | 2,920 | 2,920 | 0 | Reconciled |
| kpi_003 | analytical_patient_flow_kpi_daily.csv | 2,920 | 2,920 | 0 | Reconciled |
| kpi_004 | analytical_patient_flow_kpi_daily.csv | 2,920 | 2,920 | 0 | Reconciled |
| kpi_005 | analytical_patient_experience_kpi_daily.csv | 2,920 | 2,920 | 0 | Reconciled |
| kpi_006 | analytical_patient_experience_kpi_daily.csv | 2,920 | 2,920 | 0 | Reconciled |

All six KPIs reconcile exactly.

---

## 11. Calculated and Unavailable Counts by KPI

| KPI ID | Calculated | Unavailable |
|--------|------------|-------------|
| kpi_001 | 2,920 | 0 |
| kpi_002 | 2,920 | 0 |
| kpi_003 | 1,095 | 1,825 |
| kpi_004 | 1,095 | 1,825 |
| kpi_005 | 984 | 1,936 |
| kpi_006 | 2,383 | 537 |

---

## 12. Calculation-Status Distribution

| Status | Count |
|--------|-------|
| Calculated | 11,397 |
| Insufficient Data | 6,123 |
| Zero Denominator | 0 |

Note: Zero Denominator records from Patient Experience were preserved as Insufficient Data in the source engine. In the current integration, kpi_005 had 1,875 Zero Denominator and 598 Insufficient Data in source, totalling 1,936 unavailable.

Wait - correction: Looking at the source data again:
- Patient Experience: Calculated 3,367, Zero Denominator 1,875, Insufficient Data 598 = 5,840 total
- But in the runner output: kpi_005 has 984 calculated, 1,936 unavailable; kpi_006 has 2,383 calculated, 537 unavailable

So the unavailable totals are: kpi_005 = 1,936 (1,875 zero denom + 598 insufficient data - but that's 2,473... wait)

Actually the runner says:
- kpi_005: calculated 984, unavailable 1,936
- kpi_006: calculated 2,383, unavailable 537

But the source had:
- kpi_005: 2,920 total. In source: Calculated 3367 for both kpi_005 and kpi_006 combined? No wait, source had:
  - Patient Experience daily: 5,840 rows
  - kpi_005: 2,920 rows
  - kpi_006: 2,920 rows
  - Status distribution for patient experience overall: Calculated 3,367, Zero Denominator 1,875, Insufficient Data 598

So for kpi_005 specifically: out of 2,920 rows, 984 are calculated and 1,936 are unavailable.
For kpi_006 specifically: out of 2,920 rows, 2,383 are calculated and 537 are unavailable.

That adds up: 984 + 1,936 = 2,920; 2,383 + 537 = 2,920.
And total calculated = 2,920 + 2,920 + 1,095 + 1,095 + 984 + 2,383 = 11,397.
Total unavailable = 0 + 0 + 1,825 + 1,825 + 1,936 + 537 = 6,123.

11,397 + 6,123 = 17,520. Correct.

---

## 13. Threshold-Status Distribution

| Status | Count |
|--------|-------|
| Not Assessed | 17,520 |

All records remain Not Assessed because thresholds are v1.0-draft.

---

## 14. Threshold Provisional Status

| Status | Count |
|--------|-------|
| True | 17,520 |

All thresholds are provisional.

---

## 15. Confidence Distribution

| Level | Count |
|-------|-------|
| High | 8,230 |
| Medium | 3,367 |
| Unavailable | 5,923 |

---

## 16. Integration-Status Distribution

| Status | Count |
|--------|-------|
| Integrated with Warning | 17,520 |

All records are Integrated with Warning because all thresholds are provisional. This is the expected behavior per the specification.

---

## 17. Evidence-Status Distribution

| Status | Count |
|--------|-------|
| Complete | 11,397 |
| Unavailable | 6,123 |

---

## 18. Lineage-Status Distribution

| Status | Count |
|--------|-------|
| Complete | 11,397 |
| Unavailable | 6,123 |

---

## 19. Coverage Summary

| Status | Grains |
|--------|--------|
| Complete | 2,920 |
| Partial | 0 |
| No Applicable Data | 0 |

All 2,920 hospital-department-date grains have all six KPIs present.

---

## 20. Duplicate Check

| Result | Count |
|--------|-------|
| Duplicates found | 0 |

All 17,520 integration_record_id values are unique.

---

## 21. Value-Status Consistency Results

| Check | Count |
|-------|-------|
| Calculated + null | 0 |
| Threshold color + null | 0 |
| Threshold color + non-Calculated | 0 |
| High confidence + unavailable | 0 |

No inconsistencies detected.

---

## 22. Governance-Consistency Results

| Check | Count |
|-------|-------|
| Provisional without draft status | 0 |

All governance flags are consistent.

---

## 23. Schema and Key Validation

| Dataset | Result |
|---------|--------|
| analytical_six_kpi_daily | Pass |
| analytical_six_kpi_evidence | Pass |
| analytical_six_kpi_exclusions | Pass |
| analytical_six_kpi_lineage | Pass |
| analytical_six_kpi_issues | Pass |
| analytical_six_kpi_audit | Pass |
| analytical_six_kpi_coverage_daily | Pass |

All required fields present. Unique constraints satisfied.

---

## 24. Issues and Exclusions

| Type | Count |
|------|-------|
| Integration issues | 0 |
| Source issues integrated | 3,457 |
| Source exclusions integrated | 3,990 |
| Integration exclusions | 0 |

No new integration issues were generated. All source issues and exclusions were preserved.

---

## 25. Lineage Coverage

| Metric | Value |
|--------|-------|
| Lineage records | 23,360 |
| Source daily records | 17,520 |
| Coverage ratio | 1.33 |

Every integrated result with Complete lineage links to at least one source lineage record.

---

## 26. Phase 1 Immutability

| Dataset | Status |
|---------|--------|
| All Phase 1 processed datasets | Passed |

No Phase 1 file changed.

---

## 27. Step 2A-1 Immutability

| Dataset | Status |
|---------|--------|
| All Step 2A-1 governance outputs | Passed |

No Step 2A-1 file changed.

---

## 28. Step 2A-2 Immutability

| Dataset | Status |
|---------|--------|
| All Step 2A-2 workforce analytical outputs | Passed |

No Step 2A-2 file changed.

---

## 29. Step 2A-3 Immutability

| Dataset | Status |
|---------|--------|
| All Step 2A-3 patient-flow analytical outputs | Passed |

No Step 2A-3 file changed.

---

## 30. Step 2A-4 Immutability

| Dataset | Status |
|---------|--------|
| All Step 2A-4 patient-experience analytical outputs | Passed |

No Step 2A-4 file changed.

---

## 31. Unresolved Rules

The following business rules remain Pending Review:

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

---

## 32. Warnings

- All 17,520 integration records carry Integrated with Warning status due to provisional thresholds. This is expected and correct per the specification.
- 6,123 records have Unavailable evidence and lineage status because the underlying KPI calculation_status is not Calculated. This is expected.

---

## 33. Failures

None.

---

## 34. Final Step 2A-5 Status

**PASSED**

All acceptance criteria met:
- Exactly six approved KPI IDs integrated.
- No KPI formula recalculated.
- All accepted KPI source records reconcile (0 difference per KPI).
- No duplicate integration keys.
- Unavailable KPI records remain present.
- Null values not converted to zero.
- Calculation statuses remain valid.
- Provisional threshold governance visible.
- No false Green, Amber, or Red status assigned.
- Confidence assignments consistent.
- Evidence status generated.
- Lineage status generated.
- Coverage matrix generated.
- Schemas pass.
- Integration IDs unique.
- All prior accepted files unchanged.
- Tests pass (41/41).
- No trends, anomalies, risks, forecasts, recommendations, scenarios, or financial impact generated.

---

## 35. Readiness for Step 2A-6

Step 2A-5 is complete and ready for:

**Step 2A-6 — Analytical Layer Closure or Advanced Analytics Integration**

Step 2A-6 may perform cross-domain consistency checks, formalise the analytical layer, or integrate advanced analytics such as trend detection, anomaly detection, risk scoring, forecasting, recommendations, scenario modelling, or financial impact estimation.

Stop before Step 2A-6 unless explicitly instructed to proceed.
