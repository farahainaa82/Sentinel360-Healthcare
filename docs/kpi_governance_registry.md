# KPI Governance Registry

## Document Control

| Attribute | Value |
|-----------|-------|
| Document ID | REG-KPI-2A1-001 |
| Version | 1.0.0 |
| Phase | Phase 2A - Analytical Layer |
| Step | 2A-1 |
| Date | 2026-07-27 |
| Status | Approved |

## 1. Approved KPI Definitions

### 1.1 Staffing Level (kpi_001)

| Attribute | Value |
|-----------|-------|
| Domain | Workforce |
| Grain | hospital-department-date |
| Frequency | Daily |
| Numerator | present_staff_count + replacement_staff_count |
| Denominator | planned_staff_count |
| Formula | (numerator / denominator) * 100 |
| Unit | percentage |
| Directionality | higher_is_better |
| Source Dataset | processed_operational_daily |
| Required Fields | planned_staff_count, present_staff_count, replacement_staff_count, reassigned_staff_count |
| Null Treatment | exclude |
| Zero Denominator Treatment | null |
| Minimum Denominator | 1 |
| Threshold Reference | THR-001 |
| Confidence Rule | DC-001 |
| Approval Status | Approved |
| Readiness | Conditionally Ready |

### 1.2 Staff Absenteeism Rate (kpi_002)

| Attribute | Value |
|-----------|-------|
| Domain | Workforce |
| Grain | hospital-department-date |
| Frequency | Daily |
| Numerator | unapproved_absence_count |
| Denominator | planned_staff_count |
| Formula | (numerator / denominator) * 100 |
| Unit | percentage |
| Directionality | lower_is_better |
| Source Dataset | processed_operational_daily |
| Required Fields | planned_staff_count, unapproved_absence_count |
| Null Treatment | exclude |
| Zero Denominator Treatment | null |
| Minimum Denominator | 1 |
| Threshold Reference | THR-002 |
| Confidence Rule | DC-002 |
| Approval Status | Approved |
| Readiness | Conditionally Ready |

### 1.3 Bed Occupancy Rate (kpi_003)

| Attribute | Value |
|-----------|-------|
| Domain | Patient Flow |
| Grain | hospital-department-date |
| Frequency | Daily |
| Numerator | occupied_beds |
| Denominator | operational_beds |
| Formula | (numerator / denominator) * 100 |
| Unit | percentage |
| Directionality | neutral |
| Source Dataset | processed_operational_daily |
| Required Fields | occupied_beds, operational_beds |
| Null Treatment | exclude |
| Zero Denominator Treatment | null |
| Minimum Denominator | 1 |
| Threshold Reference | THR-003 |
| Confidence Rule | DC-003 |
| Approval Status | Approved |
| Readiness | Conditionally Ready |

### 1.4 Average Patient Waiting Time (kpi_004)

| Attribute | Value |
|-----------|-------|
| Domain | Patient Flow |
| Grain | hospital-department-date |
| Frequency | Daily |
| Numerator | SUM(arrival_to_consultation_minutes WHERE eligible) |
| Denominator | COUNT(encounter_id WHERE eligible) |
| Formula | numerator / denominator |
| Unit | minutes |
| Directionality | lower_is_better |
| Source Dataset | processed_patient_encounters |
| Required Fields | arrival_to_consultation_minutes, official_wait_stage_eligible_flag, encounter_wait_eligible_flag |
| Eligibility | official_wait_stage_eligible_flag = True AND encounter_wait_eligible_flag = True |
| Exclusion | negative_wait_minutes |
| Null Treatment | exclude |
| Zero Denominator Treatment | null |
| Minimum Denominator | 1 |
| Threshold Reference | THR-004 |
| Confidence Rule | DC-004 |
| Approval Status | Approved |
| Readiness | Conditionally Ready |

### 1.5 Patient Complaint Rate (kpi_005)

| Attribute | Value |
|-----------|-------|
| Domain | Patient Experience |
| Grain | hospital-department-date |
| Frequency | Daily |
| Numerator | complaint_valid_record_count |
| Denominator | encounter_record_count |
| Formula | (numerator / denominator) * 1000 |
| Unit | rate_per_1000 |
| Directionality | lower_is_better |
| Source Dataset | processed_operational_daily |
| Required Fields | complaint_valid_record_count, encounter_record_count |
| Null Treatment | exclude |
| Zero Denominator Treatment | null |
| Minimum Denominator | 1 |
| Threshold Reference | THR-005 |
| Confidence Rule | DC-005 |
| Approval Status | Approved |
| Readiness | Conditionally Ready |

### 1.6 Patient Satisfaction Score (kpi_006)

| Attribute | Value |
|-----------|-------|
| Domain | Patient Experience |
| Grain | hospital-department-date |
| Frequency | Daily |
| Numerator | survey_score_weighted_sum |
| Denominator | survey_valid_score_record_count |
| Formula | numerator / denominator |
| Unit | score |
| Directionality | higher_is_better |
| Source Dataset | processed_operational_daily |
| Required Fields | survey_score_weighted_sum, survey_valid_score_record_count |
| Null Treatment | exclude |
| Zero Denominator Treatment | null |
| Minimum Denominator | 1 |
| Threshold Reference | THR-006 |
| Confidence Rule | DC-006 |
| Approval Status | Approved |
| Readiness | Conditionally Ready |

## 2. Readiness Summary

| KPI ID | Name | Readiness Status | Blocking Reason |
|--------|------|------------------|-----------------|
| kpi_001 | Staffing Level | Conditionally Ready | Threshold config in draft status |
| kpi_002 | Staff Absenteeism Rate | Conditionally Ready | Threshold config in draft status |
| kpi_003 | Bed Occupancy Rate | Conditionally Ready | Threshold config in draft status |
| kpi_004 | Average Patient Waiting Time | Conditionally Ready | Threshold config in draft status |
| kpi_005 | Patient Complaint Rate | Conditionally Ready | Threshold config in draft status |
| kpi_006 | Patient Satisfaction Score | Conditionally Ready | Threshold config in draft status |

## 3. Source Field Mapping

| KPI ID | Source Dataset | Numerator Field | Denominator Field |
|--------|----------------|-----------------|-------------------|
| kpi_001 | processed_operational_daily | present_staff_count + replacement_staff_count | planned_staff_count |
| kpi_002 | processed_operational_daily | unapproved_absence_count | planned_staff_count |
| kpi_003 | processed_operational_daily | occupied_beds | operational_beds |
| kpi_004 | processed_patient_encounters | SUM(arrival_to_consultation_minutes WHERE eligible) | COUNT(encounter_id WHERE eligible) |
| kpi_005 | processed_operational_daily | complaint_valid_record_count | encounter_record_count |
| kpi_006 | processed_operational_daily | survey_score_weighted_sum | survey_valid_score_record_count |

## 4. Threshold Configuration

Threshold configuration exists in `config/kpi_threshold_config.csv` but is currently in draft status (v1.0-draft). All thresholds are placeholders pending stakeholder validation.

## 5. Configuration Version

| Config File | Version | Status |
|-------------|---------|--------|
| kpi_definition_config.csv | v1.0-draft | Draft |
| kpi_threshold_config.csv | v1.0-draft | Draft |
| data_confidence_config.csv | v1.0-draft | Draft |

## 6. Governance Rules

- No unofficial KPIs are permitted
- All KPIs must have configuration-backed definitions
- Thresholds must not be hard-coded in calculation logic
- Source fields must be validated before calculation
- Blocked KPIs cannot be calculated
- All calculations must produce evidence and lineage

## 7. Unresolved Rules

- Threshold values require stakeholder validation
- Final approval status pending for all threshold configurations
- Data confidence rules are draft placeholders

## 8. Approval Chain

| Role | Responsibility |
|------|----------------|
| Data Engineer | Maintain registry and configurations |
| Data Steward | Validate source field mappings |
| Clinical Stakeholder | Approve threshold values |
| QA Lead | Verify calculation correctness |
