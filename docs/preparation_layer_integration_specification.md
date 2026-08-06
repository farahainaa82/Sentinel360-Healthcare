# Preparation Layer Integration Specification

## Document Control

| Attribute | Value |
|-----------|-------|
| Document ID | SPEC-PLI-2D5-001 |
| Version | 1.0.0 |
| Phase | Phase 1 - Preparation Layer |
| Step | 2D-5 |
| Date | 2026-07-27 |
| Status | Approved |

## 1. Purpose

This specification defines the integration, reconciliation and formal closure of the Phase 1 preparation layer. It describes how the three domain daily datasets (workforce, patient-flow, patient-experience) are combined into a single `processed_operational_daily` dataset at hospital-department-date grain, and the validation controls that ensure data integrity.

## 2. Scope

### 2.1 In Scope
- Inventory of all 16 processed datasets
- Schema validation against `processed_schema_registry`
- Business key uniqueness validation
- Daily grain validation (hospital-department-date)
- Hospital and department reference validation
- Date field validation
- Month-year consistency validation
- Cross-domain daily key reconciliation
- Operational daily dataset construction
- Lineage tracking
- Prohibited field detection
- Prior processed dataset immutability verification

### 2.2 Out of Scope
- KPI calculations
- Status classifications
- Trend analysis
- Anomaly detection
- Risk scoring
- Forecasting
- Scenario modelling
- Financial impact analysis
- Recommendations

## 3. Inputs

### 3.1 Required Processed Datasets (16)

| # | Dataset | Domain | Grain |
|---|---------|--------|-------|
| 1 | processed_hospital_master | Reference | hospital |
| 2 | processed_department_master | Reference | department |
| 3 | processed_staff_role_master | Workforce | role |
| 4 | processed_staff_master | Workforce | staff |
| 5 | processed_staff_roster | Workforce | staff-date |
| 6 | processed_staff_attendance | Workforce | staff-date |
| 7 | processed_staffing_requirement | Workforce | department-date |
| 8 | processed_workforce_daily | Workforce | hospital-department-date-staff_role |
| 9 | processed_patient_encounters | Patient Flow | encounter |
| 10 | processed_patient_queue | Patient Flow | queue |
| 11 | processed_bed_capacity | Patient Flow | bed |
| 12 | processed_service_schedule | Patient Flow | schedule |
| 13 | processed_patient_flow_daily | Patient Flow | hospital-department-date |
| 14 | processed_patient_complaints | Patient Experience | complaint |
| 15 | processed_patient_surveys | Patient Experience | survey |
| 16 | processed_patient_experience_daily | Patient Experience | hospital-department-date |

### 3.2 Prior Manifests
- `validation_run_manifest.json`
- `patient_encounter_processing_run_manifest.json`
- `queue_capacity_schedule_processing_run_manifest.json`
- `patient_flow_daily_processing_run_manifest.json`
- `patient_flow_integration_manifest.json`
- `step_2d3_closure_manifest.json`
- `patient_experience_processing_run_manifest.json`

## 4. Processing Logic

### 4.1 Workforce Daily Aggregation

`processed_workforce_daily` contains a `staff_role_id` dimension, so it has multiple rows per hospital-department-date. Before integration, it must be aggregated:

```
GROUP BY hospital_id, department_id, reporting_date
AGGREGATE numeric_fields -> SUM
PRESERVE workforce_daily_id -> FIRST (for lineage)
```

### 4.2 Operational Daily Spine

The operational daily spine is the UNION of all valid keys from the three domain daily datasets:

```
spine_keys = workforce_keys UNION patient_flow_keys UNION patient_experience_keys
```

This ensures every hospital-department-date combination that exists in any domain is represented.

### 4.3 Domain Presence Flags

For each spine row, flags indicate which domains contributed data:

| Flag | True When |
|------|-----------|
| workforce_missing_flag | No workforce data for this h-d-d |
| patient_flow_missing_flag | No patient flow data for this h-d-d |
| patient_experience_missing_flag | No patient experience data for this h-d-d |

### 4.4 Completeness Flags

| Flag | True When |
|------|-----------|
| operational_data_complete_flag | All three domains present |
| partial_domain_record_flag | Only one or two domains present |

### 4.5 Operational Daily Identifier

Deterministic ID generation:

```
OPD-{hospital_id}-{department_id}-{YYYYMMDD}
```

## 5. Schema

### 5.1 processed_operational_daily

| Field | Type | Required | Source |
|-------|------|----------|--------|
| operational_daily_id | string | Yes | Derived |
| hospital_id | string | Yes | Spine |
| department_id | string | Yes | Spine |
| reporting_date | date | Yes | Spine |
| reporting_month | integer | Yes | Derived from date |
| reporting_year | integer | Yes | Derived from date |
| planned_staff_count | numeric | No | Workforce |
| present_staff_count | numeric | No | Workforce |
| unapproved_absence_count | numeric | No | Workforce |
| approved_leave_count | numeric | No | Workforce |
| reassigned_staff_count | numeric | No | Workforce |
| replacement_staff_count | numeric | No | Workforce |
| workforce_missing_flag | boolean | Yes | Derived |
| encounter_record_count | numeric | No | Patient Flow |
| completed_encounter_count | numeric | No | Patient Flow |
| cancelled_encounter_count | numeric | No | Patient Flow |
| lwbs_encounter_count | numeric | No | Patient Flow |
| queue_count_total | numeric | No | Patient Flow |
| occupied_beds | numeric | No | Patient Flow |
| operational_beds | numeric | No | Patient Flow |
| licensed_beds | numeric | No | Patient Flow |
| overcapacity_count | numeric | No | Patient Flow |
| scheduled_session_count | numeric | No | Patient Flow |
| cancelled_session_count | numeric | No | Patient Flow |
| reduced_session_count | numeric | No | Patient Flow |
| extended_session_count | numeric | No | Patient Flow |
| patient_flow_missing_flag | boolean | Yes | Derived |
| complaint_record_count | numeric | No | Patient Experience |
| complaint_valid_record_count | numeric | No | Patient Experience |
| complaint_high_severity_count | numeric | No | Patient Experience |
| complaint_medium_severity_count | numeric | No | Patient Experience |
| complaint_low_severity_count | numeric | No | Patient Experience |
| complaint_open_source_count | numeric | No | Patient Experience |
| complaint_resolved_source_count | numeric | No | Patient Experience |
| survey_record_count | numeric | No | Patient Experience |
| survey_response_count_total | numeric | No | Patient Experience |
| survey_valid_score_record_count | numeric | No | Patient Experience |
| survey_score_sum | numeric | No | Patient Experience |
| survey_score_weighted_sum | numeric | No | Patient Experience |
| patient_experience_missing_flag | boolean | Yes | Derived |
| operational_data_complete_flag | boolean | Yes | Derived |
| partial_domain_record_flag | boolean | Yes | Derived |
| cross_domain_reference_valid_flag | boolean | Yes | Derived |
| cross_domain_date_valid_flag | boolean | Yes | Derived |
| unresolved_rule_flag | boolean | Yes | Derived |
| processing_run_id | string | Yes | Closure run |
| processed_datetime | datetime | Yes | Closure run |
| transformation_version | string | Yes | Closure run |

## 6. Validation Rules

### 6.1 Schema Validation
- All required fields must be present
- No unexpected fields (optional fields allowed)

### 6.2 Business Key Validation
- Unique constraint on `operational_daily_id`
- Unique constraint on `(hospital_id, department_id, reporting_date)`

### 6.3 Reference Validation
- `hospital_id` must exist in `processed_hospital_master`
- `department_id` must exist in `processed_department_master`
- `department_id` must belong to `hospital_id` in `processed_department_master`

### 6.4 Date Validation
- `reporting_date` must be a valid date
- `reporting_month` must match month extracted from `reporting_date`
- `reporting_year` must match year extracted from `reporting_date`

### 6.5 Prohibited Fields
The following analytical fields must NOT be present in any processed dataset:
- kpi_value, kpi_status, kpi_score
- trend_direction, trend_magnitude
- anomaly_flag, anomaly_score
- risk_level, risk_score
- forecast_value, forecast_confidence
- scenario_id, scenario_name
- financial_impact, cost_benefit_ratio
- recommendation_text, action_priority

## 7. Outputs

### 7.1 Primary Output
- `data/processed/processed_operational_daily.csv`

### 7.2 Control Outputs
- `outputs/logs/preparation_layer_closure_manifest.json`
- `outputs/logs/preparation_layer_checksum_verification.csv`
- `outputs/logs/preparation_layer_file_inventory.csv`
- `outputs/logs/preparation_layer_schema_summary.csv`
- `outputs/logs/preparation_layer_business_key_summary.csv`
- `outputs/logs/preparation_layer_daily_grain_summary.csv`
- `outputs/logs/preparation_layer_reference_summary.csv`
- `outputs/logs/preparation_layer_cross_domain_reconciliation.csv`
- `outputs/logs/preparation_layer_lineage_summary.csv`
- `outputs/logs/preparation_layer_lineage_gap_log.csv`
- `outputs/logs/preparation_layer_issue_summary.csv`
- `outputs/logs/preparation_layer_exclusion_summary.csv`
- `outputs/logs/preparation_layer_dataset_summary.csv`
- `outputs/logs/preparation_layer_closure_audit_log.csv`
- `outputs/logs/preparation_layer_test_summary.csv`

## 8. Acceptance Criteria

| Criterion | Target |
|-----------|--------|
| All 16 processed datasets present | 100% |
| Schema validation pass rate | 100% |
| Business key uniqueness | 100% |
| Hospital reference validity | 100% |
| Department reference validity | 100% |
| Date validation pass rate | 100% |
| Prohibited fields detected | 0 |
| Prior dataset immutability | 100% |
| Lineage coverage | 100% |
| Operational daily grain uniqueness | 100% |
| Closure status | Passed or Passed with Warnings |

## 9. Closure Status Rules

| Condition | Status |
|-----------|--------|
| Any Critical issue | Blocked |
| Any Error issue + no Critical | Failed |
| Only Warnings/Information | Passed with Warnings |
| No issues at all | Passed |
| Prior datasets changed | Blocked |
| Missing required files | Blocked |
| Step 2D-3 not accepted | Blocked |
| Step 2D-4 not accepted | Blocked |

## 10. Lineage

### 10.1 Source to Target Mapping

| Target Field | Source Dataset | Source Field |
|--------------|----------------|--------------|
| operational_daily_id | Derived | hospital_id + department_id + reporting_date |
| hospital_id | Spine | hospital_id |
| department_id | Spine | department_id |
| reporting_date | Spine | reporting_date |
| planned_staff_count | processed_workforce_daily | planned_staff_count (SUM) |
| encounter_record_count | processed_patient_flow_daily | encounter_record_count |
| complaint_record_count | processed_patient_experience_daily | complaint_record_count |

### 10.2 Lineage Record Structure

| Field | Description |
|-------|-------------|
| output_record_id | operational_daily_id |
| source_dataset | Name of source dataset |
| source_record_id | Primary key of source record |
| transformation_name | Name of transformation step |
| transformation_version | Version identifier |
| processing_run_id | Closure run identifier |
| processed_datetime | Timestamp |

## 11. Known Design Considerations

### 11.1 Workforce Daily Dimension
`processed_workforce_daily` includes `staff_role_id`, creating multiple rows per hospital-department-date. During operational daily construction, these are aggregated by SUM for numeric measures. The `workforce_daily_id` is preserved via FIRST for lineage tracking. This design is intentional and documented.

### 11.2 Lineage Reference Warnings
When workforce daily records are aggregated, some lineage rows will have empty `source_record_id` values because the aggregated row represents multiple source records. The validator reports this as a Warning (not Error) because it is an expected consequence of the aggregation design.

## 12. Related Documents

- `docs/step_2d3_closure_specification.md`
- `docs/step_2d3_final_acceptance_report.md`
- `docs/workforce_transformation_specification.md`
- `docs/patient_flow_daily_specification.md`
- `docs/patient_experience_transformation_specification.md`
- `docs/processing_lineage_specification.md`

## 13. Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Data Engineer | Auto-generated | 2026-07-27 | N/A |
| QA Lead | Auto-generated | 2026-07-27 | N/A |
| Data Steward | Auto-generated | 2026-07-27 | N/A |
