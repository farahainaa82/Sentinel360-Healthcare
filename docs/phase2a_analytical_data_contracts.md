# Phase 2A Analytical Data Contracts

## Document Control

| Attribute | Value |
|-----------|-------|
| Document ID | CONTRACT-2A1-001 |
| Version | 1.0.0 |
| Phase | Phase 2A - Analytical Layer |
| Step | 2A-1 |
| Date | 2026-07-27 |
| Status | Approved |

## 1. Contract Overview

This document defines the data contracts between the preparation layer and the analytical layer for Sentinel360 Healthcare.

## 2. Input Contracts

### 2.1 Operational Daily Contract

**Dataset**: `processed_operational_daily.csv`

| Field | Type | Contract |
|-------|------|----------|
| hospital_id | string | Not null, exists in hospital_master |
| department_id | string | Not null, exists in department_master |
| reporting_date | date | Not null, valid date |
| planned_staff_count | numeric | >= 0 or null |
| present_staff_count | numeric | >= 0 or null |
| unapproved_absence_count | numeric | >= 0 or null |
| replacement_staff_count | numeric | >= 0 or null |
| reassigned_staff_count | numeric | >= 0 or null |
| occupied_beds | numeric | >= 0 or null |
| operational_beds | numeric | >= 0 or null |
| complaint_valid_record_count | numeric | >= 0 or null |
| encounter_record_count | numeric | >= 0 or null |
| survey_score_weighted_sum | numeric | >= 0 or null |
| survey_valid_score_record_count | numeric | >= 0 or null |

### 2.2 Patient Encounters Contract

**Dataset**: `processed_patient_encounters.csv`

| Field | Type | Contract |
|-------|------|----------|
| encounter_id | string | Not null, unique |
| hospital_id | string | Not null |
| department_id | string | Not null |
| arrival_to_consultation_minutes | numeric | >= 0 or null |
| official_wait_stage_eligible_flag | boolean | True/False |
| encounter_wait_eligible_flag | boolean | True/False |

## 3. Output Contracts

### 3.1 KPI Daily Output Contract

**Dataset**: `analytical_kpi_daily` (future)

| Field | Type | Contract |
|-------|------|----------|
| analytical_record_id | string | Not null, unique |
| hospital_id | string | Not null |
| department_id | string | Not null |
| reporting_date | date | Not null |
| kpi_id | string | Not null, exists in registry |
| kpi_name | string | Not null |
| numerator_value | numeric | >= 0 or null |
| denominator_value | numeric | >= 0 or null |
| kpi_value | numeric | Calculated or null |
| unit | string | Not null |
| calculation_status | string | One of: Calculated, Insufficient Data, Zero Denominator, Configuration Missing, Rule Pending, Invalid Input, Not Calculated |
| readiness_status | string | One of: Ready, Conditionally Ready, Blocked, Not Applicable |
| threshold_version | string | Not null |
| configuration_version | string | Not null |
| data_confidence_level | string | One of: high, medium, low, insufficient |
| source_dataset | string | Not null |
| calculation_run_id | string | Not null |
| calculated_at | datetime | Not null |

### 3.2 Evidence Output Contract

**Dataset**: `analytical_kpi_evidence` (future)

| Field | Type | Contract |
|-------|------|----------|
| evidence_id | string | Not null, unique |
| analytical_record_id | string | Not null, references analytical_kpi_daily |
| evidence_type | string | numerator or denominator |
| source_dataset | string | Not null |
| source_field | string | Not null |
| source_value | numeric | Value or null |
| source_record_count | integer | >= 0 |
| aggregation_method | string | Not null |
| eligibility_applied | boolean | True/False |

### 3.3 Exclusion Output Contract

**Dataset**: `analytical_kpi_exclusions` (future)

| Field | Type | Contract |
|-------|------|----------|
| exclusion_id | string | Not null, unique |
| analytical_record_id | string | Not null |
| exclusion_reason | string | Not null |
| source_dataset | string | Not null |
| source_record_id | string | Not null |
| field_name | string | Not null |

## 4. Calculation Contract

### 4.1 Calculation Request

```
KPI Calculation Request:
  - kpi_id: string (required)
  - hospital_id: string (optional)
  - department_id: string (optional)
  - reporting_date: date (optional)
  - calculation_run_id: string (required)
```

### 4.2 Calculation Result

```
KPI Calculation Result:
  - kpi_id: string
  - kpi_value: numeric or null
  - numerator_value: numeric or null
  - denominator_value: numeric or null
  - calculation_status: string
  - readiness_status: string
  - evidence: KPINumeratorEvidence + KPIDenominatorEvidence
  - exclusions: List[KPIExclusionRecord]
```

### 4.3 Calculation Rules

1. **Eligibility First**: Apply eligibility rules before aggregation
2. **Exclusion Logging**: Log every excluded record with reason
3. **Null Handling**: Exclude null values unless explicitly configured
4. **Zero Denominator**: Return null KPI value with status "Zero Denominator"
5. **Minimum Denominator**: If denominator < minimum, status = "Insufficient Data"
6. **Threshold Assignment**: Apply thresholds after calculation
7. **Confidence Assessment**: Assess confidence after calculation

## 5. Governance Contract

### 5.1 Preconditions

Before calculation:
- Phase 1 immutability verified
- KPI registry validated
- Source fields confirmed available
- Configuration loaded and validated
- No blocked KPIs

### 5.2 Postconditions

After calculation:
- All output schemas validated
- Lineage records created
- Audit records created
- Issues logged
- Exclusions logged
- Evidence preserved

### 5.3 Invariants

- No preparation layer datasets modified
- No unofficial KPIs calculated
- No hard-coded thresholds used
- All calculations deterministic

## 6. Versioning Contract

| Component | Version Strategy |
|-----------|------------------|
| KPI Definition | Semantic versioning (major.minor.patch) |
| Threshold | Version + effective date range |
| Configuration | File-level version |
| Schema | Schema name + version |
| Calculation Run | UUID with timestamp |

## 7. Error Handling Contract

| Error Type | Behavior |
|------------|----------|
| Missing source dataset | Block KPI, log issue |
| Missing source field | Block KPI, log issue |
| Invalid configuration | Block KPI, log issue |
| Zero denominator | Return null, status = "Zero Denominator" |
| Insufficient data | Return null, status = "Insufficient Data" |
| Invalid input | Return null, status = "Invalid Input" |
| Configuration missing | Return null, status = "Configuration Missing" |
| Rule pending | Return null, status = "Rule Pending" |

## 8. Lineage Contract

Every analytical output record must have:
- Link to source dataset
- Link to source record(s)
- Transformation name and version
- Calculation run ID
- Timestamp

## 9. Audit Contract

Every calculation run must produce:
- Run manifest with metadata
- Record counts per dataset
- Issue count
- Exclusion count
- Start and end timestamps
- Operator identity

## 10. Acceptance Criteria

The analytical layer is ready for calculation when:
- All six KPIs are registered
- All source fields are available
- Configuration is validated
- Phase 1 immutability is confirmed
- No KPI is blocked
- Schemas are defined
- Tests pass
- No calculations have occurred yet
