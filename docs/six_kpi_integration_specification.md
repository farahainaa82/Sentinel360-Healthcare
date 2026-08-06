# Six-KPI Integration and Status Layer Specification

**Step:** 2A-5
**Status:** Complete
**Integration Version:** 2A-5-1.0.0
**Configuration Version:** v1.0-draft

---

## 1. Scope

This document specifies the Six-KPI Integration and Status Layer created in Step 2A-5 of the Sentinel360 Healthcare analytical layer.

The integration layer consolidates all six accepted analytical KPI datasets into a single governed structure without recalculating any KPI values.

Integrated KPIs:

- **kpi_001** — Staffing Level
- **kpi_002** — Staff Absenteeism Rate
- **kpi_003** — Bed Occupancy Rate
- **kpi_004** — Average Patient Waiting Time
- **kpi_005** — Patient Complaint Rate
- **kpi_006** — Patient Satisfaction Score

---

## 2. Authoritative Inputs

### 2.1 Accepted Analytical Datasets

| Domain | Daily | Evidence | Exclusions | Lineage | Issues | Audit |
|--------|-------|----------|------------|---------|--------|-------|
| Workforce | analytical_workforce_kpi_daily.csv | analytical_workforce_kpi_evidence.csv | analytical_workforce_kpi_exclusions.csv | analytical_workforce_kpi_lineage.csv | analytical_workforce_kpi_issues.csv | analytical_workforce_kpi_audit.csv |
| Patient Flow | analytical_patient_flow_kpi_daily.csv | analytical_patient_flow_kpi_evidence.csv | analytical_patient_flow_kpi_exclusions.csv | analytical_patient_flow_kpi_lineage.csv | analytical_patient_flow_kpi_issues.csv | analytical_patient_flow_kpi_audit.csv |
| Patient Experience | analytical_patient_experience_kpi_daily.csv | analytical_patient_experience_kpi_evidence.csv | analytical_patient_experience_kpi_exclusions.csv | analytical_patient_experience_kpi_lineage.csv | analytical_patient_experience_kpi_issues.csv | analytical_patient_experience_kpi_audit.csv |

### 2.2 Governance Sources

- config/kpi_definition_config.csv
- config/kpi_threshold_config.csv
- config/data_confidence_config.csv
- outputs/analytical_governance/kpi_governance_registry.csv
- outputs/analytical_governance/kpi_readiness_summary.csv
- outputs/analytical_governance/kpi_source_field_mapping.csv
- outputs/analytical_governance/kpi_configuration_validation.csv
- outputs/analytical_governance/kpi_threshold_validation.csv

---

## 3. Integration Grain

The integrated KPI result grain is:

```
hospital_id + department_id + reporting_date + kpi_id
```

Expected daily records: one record for each applicable KPI.

Deterministic integration record ID format:

```
IKPI-{kpi_id}-{hospital_id}-{department_id}-{YYYYMMDD}
```

The original `analytical_record_id` from the source engine is preserved in a separate column.

---

## 4. Status Dimensions

The integration layer preserves and standardizes ten status dimensions separately:

1. calculation_status
2. readiness_status
3. threshold_status
4. threshold_approval_status
5. threshold_is_provisional
6. data_confidence_level
7. confidence_is_provisional
8. integration_status
9. evidence_status
10. lineage_status

These are not merged into a single ambiguous status field.

---

## 5. Calculation Status Normalization

Accepted statuses are normalized for spelling and capitalization only:

- Calculated
- Insufficient Data
- Zero Denominator
- Configuration Missing
- Rule Pending
- Invalid Input
- Not Calculated

Rules:
- Non-null KPI value should normally have calculation_status = Calculated.
- Null KPI value retains its accepted non-calculated status.
- Null is not automatically converted to Insufficient Data if the source used a different status.

---

## 6. Threshold Status Normalization

Accepted threshold statuses:

- Green
- Amber
- Red
- Not Assessed
- Unavailable
- Configuration Missing

Rules:
- Preserve accepted threshold status.
- Do not recalculate threshold bands.
- No Green, Amber, or Red status may be assigned when:
  - kpi_value is null
  - calculation_status is not Calculated
  - threshold bounds are missing
- Draft thresholds remain visibly provisional.

Current state: all thresholds are v1.0-draft, so all records remain Not Assessed.

---

## 7. Data Confidence Normalization

Accepted confidence levels:

- High
- Medium
- Low
- Unavailable
- Not Assessed

Rules:
- Preserve accepted engine confidence.
- Standardize spelling and capitalization only.
- Unavailable KPI records must not be labelled High.
- Preserve confidence-rule version and provisional status.

---

## 8. Integration Status Rules

Controlled values:

- **Integrated** — accepted record, schema valid, recognized KPI ID, consistent statuses, required metadata present.
- **Integrated with Warning** — accepted record with non-blocking governance limitation (provisional threshold, provisional confidence, unavailable result).
- **Excluded** — duplicate record, unsupported KPI ID, unrecoverable key problem, invalid date.
- **Failed Validation** — blocking schema defect, missing required field, KPI value inconsistent with calculation status, unexplained formula or source conflict.

---

## 9. Evidence Status Rules

- **Complete** — expected evidence present and linked.
- **Partial** — some expected evidence exists but one component is unavailable.
- **Unavailable** — KPI itself is unavailable by accepted rule.
- **Missing** — calculated KPI lacks required evidence.
- **Invalid** — evidence references unknown record or is malformed.

---

## 10. Lineage Status Rules

- **Complete** — integrated result links to accepted source analytical result.
- **Partial** — accepted aggregation design prevents record-level source linkage.
- **Unavailable** — KPI result is unavailable and no record-level source contribution exists.
- **Broken** — referenced analytical record does not exist or linkage cannot be reconciled.

---

## 11. Coverage Matrix

The coverage matrix groups by hospital_id, department_id, reporting_date and reports:

- expected_kpi_count (6)
- present_kpi_count
- calculated_kpi_count
- unavailable_kpi_count
- missing_kpi_count
- coverage_percentage
- coverage_status (Complete / Partial / No Applicable Data)

---

## 12. Output Schemas

### 12.1 analytical_six_kpi_daily.csv

| Field | Type | Description |
|-------|------|-------------|
| integration_record_id | string | Deterministic ID |
| analytical_record_id | string | Original source ID |
| hospital_id | string | Hospital identifier |
| department_id | string | Department identifier |
| reporting_date | date | Reporting date |
| reporting_month | int | Month |
| reporting_year | int | Year |
| kpi_id | string | Governed KPI ID |
| kpi_name | string | Governed name |
| domain | string | KPI domain |
| numerator_value | float | Preserved numerator |
| denominator_value | float | Preserved denominator |
| kpi_value | float | Preserved KPI value |
| unit | string | Unit of measure |
| calculation_status | string | Normalized calculation status |
| readiness_status | string | Readiness status |
| threshold_status | string | Threshold status |
| threshold_version | string | Threshold version |
| threshold_approval_status | string | Approval status |
| threshold_is_provisional | bool | Provisional flag |
| data_confidence_level | string | Confidence level |
| confidence_rule_version | string | Confidence rule version |
| confidence_is_provisional | bool | Confidence provisional flag |
| integration_status | string | Integration status |
| evidence_status | string | Evidence status |
| lineage_status | string | Lineage status |
| source_analytical_dataset | string | Source dataset name |
| source_analytical_record_id | string | Source record ID |
| source_calculation_run_id | string | Source run ID |
| integration_run_id | string | Integration run ID |
| integrated_at | datetime | Integration timestamp |

### 12.2 Supporting Outputs

See generated files under data/analytical/ and outputs/analytical_six_kpi/ for full schemas.

---

## 13. Reconciliation

Source-to-integrated reconciliation is performed by KPI ID, reporting:

- source analytical dataset
- source row count
- integrated row count
- calculated count
- unavailable count
- duplicate count
- count difference
- reconciliation status

---

## 14. Immutability

Phase 1, Step 2A-1, Step 2A-2, Step 2A-3, and Step 2A-4 datasets are verified before and after integration. Any unexplained change is a blocking failure.

---

## 15. Limitations

- Thresholds are draft; no bound values are applied.
- Confidence rules are provisional.
- No trend, anomaly, forecast, recommendation, scenario, or financial impact logic is included.
- All integration statuses show Integrated with Warning because all thresholds are provisional.
- Evidence and lineage statuses reflect source availability; some domains have empty issue or exclusion files.

---

## 16. Unresolved Business Rules

The following rules remain Pending Review:

- Official complaint-rate denominator approval
- Complaint inclusion and exclusion rules
- Reopened complaints counting
- Complaint severity weighting
- Complaint status treatment
- Official satisfaction-score scale approval
- Satisfaction-score normalisation method
- Minimum survey response threshold
- Mixed survey scales handling
- Official KPI reporting grain
