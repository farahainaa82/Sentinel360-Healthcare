# Data Validation Test Plan

## Purpose

This document defines the comprehensive validation tests that the Sentinel360 Healthcare prototype must apply to source data, configuration data and calculation outputs. It covers file-level, schema-level, content-level, referential-integrity and configuration-level validation. No tolerance percentages or numerical cut-offs are invented in this document.

---

## Test Catalogue

### 1. File Presence

| Property | Value |
|---|---|
| Test ID | VAL-001 |
| Test Name | Source File Presence |
| Dataset | All source datasets |
| Severity | Critical |
| Validation Type | File existence |
| Failure Condition | Expected source file does not exist in the upload directory |
| Expected System Response | Block processing; return `Not Available` for all dependent KPIs |
| Blocks Processing | Yes |
| Manual Override Allowed | No |
| Override Audit Required | N/A |
| Output Status | Blocked |

---

### 2. File Extension

| Property | Value |
|---|---|
| Test ID | VAL-002 |
| Test Name | File Extension Validation |
| Dataset | All uploaded files |
| Severity | Error |
| Validation Type | Extension check |
| Failure Condition | File extension is not `.csv` |
| Expected System Response | Reject file; request correct format |
| Blocks Processing | Yes |
| Manual Override Allowed | No |
| Override Audit Required | N/A |
| Output Status | Rejected |

---

### 3. File Size

| Property | Value |
|---|---|
| Test ID | VAL-003 |
| Test Name | File Size Sanity Check |
| Dataset | All uploaded files |
| Severity | Warning |
| Validation Type | Size check |
| Failure Condition | File size is zero bytes or unexpectedly large |
| Expected System Response | Flag for review; allow processing if schema passes |
| Blocks Processing | No |
| Manual Override Allowed | Yes |
| Override Audit Required | Yes |
| Output Status | Warning |

---

### 4. Schema Matching

| Property | Value |
|---|---|
| Test ID | VAL-004 |
| Test Name | Schema Column Match |
| Dataset | All source and configuration datasets |
| Severity | Critical |
| Validation Type | Column name verification |
| Failure Condition | Required column is missing or unexpected column is present |
| Expected System Response | Block processing; return `Data Quality Review Required` |
| Blocks Processing | Yes |
| Manual Override Allowed | No |
| Override Audit Required | N/A |
| Output Status | Blocked |

---

### 5. Required Columns

| Property | Value |
|---|---|
| Test ID | VAL-005 |
| Test Name | Required Column Population |
| Dataset | All datasets |
| Severity | Critical |
| Validation Type | Null check |
| Failure Condition | Required column contains null or empty values |
| Expected System Response | Exclude affected records; flag `Data Quality Review Required` if widespread |
| Blocks Processing | Yes (if widespread) |
| Manual Override Allowed | No |
| Override Audit Required | N/A |
| Output Status | Blocked or Rejected |

---

### 6. Data Types

| Property | Value |
|---|---|
| Test ID | VAL-006 |
| Test Name | Data Type Validation |
| Dataset | All datasets |
| Severity | Error |
| Validation Type | Type coercion check |
| Failure Condition | Value cannot be coerced to declared data type |
| Expected System Response | Exclude affected records; flag for review |
| Blocks Processing | No (unless widespread) |
| Manual Override Allowed | No |
| Override Audit Required | N/A |
| Output Status | Rejected (record level) |

---

### 7. Date Validity

| Property | Value |
|---|---|
| Test ID | VAL-007 |
| Test Name | Date Format and Range Validation |
| Dataset | All datasets with date fields |
| Severity | Error |
| Validation Type | Format and range check |
| Failure Condition | Date is not in `YYYY-MM-DD` format or is outside valid range |
| Expected System Response | Exclude affected records; flag for review |
| Blocks Processing | No (unless widespread) |
| Manual Override Allowed | No |
| Override Audit Required | N/A |
| Output Status | Rejected (record level) |

---

### 8. Datetime Validity

| Property | Value |
|---|---|
| Test ID | VAL-008 |
| Test Name | Datetime Format Validation |
| Dataset | All datasets with datetime fields |
| Severity | Error |
| Validation Type | Format check |
| Failure Condition | Datetime is not in `YYYY-MM-DDTHH:MM:SS` format |
| Expected System Response | Exclude affected records; flag for review |
| Blocks Processing | No (unless widespread) |
| Manual Override Allowed | No |
| Override Audit Required | N/A |
| Output Status | Rejected (record level) |

---

### 9. Required-Field Completeness

| Property | Value |
|---|---|
| Test ID | VAL-009 |
| Test Name | Required Field Completeness Percentage |
| Dataset | All source datasets |
| Severity | Warning |
| Validation Type | Percentage calculation |
| Failure Condition | Completeness percentage is below approved minimum (configurable) |
| Expected System Response | Calculate with reduced confidence; disclose gap |
| Blocks Processing | No |
| Manual Override Allowed | Yes |
| Override Audit Required | Yes |
| Output Status | Warning |

---

### 10. Duplicate Identifiers

| Property | Value |
|---|---|
| Test ID | VAL-010 |
| Test Name | Primary Key Uniqueness |
| Dataset | All datasets with primary keys |
| Severity | Critical |
| Validation Type | Uniqueness check |
| Failure Condition | Duplicate primary key values exist |
| Expected System Response | Block processing; return `Data Quality Review Required` |
| Blocks Processing | Yes |
| Manual Override Allowed | No |
| Override Audit Required | N/A |
| Output Status | Blocked |

---

### 11. Referential Integrity

| Property | Value |
|---|---|
| Test ID | VAL-011 |
| Test Name | Foreign Key Referential Integrity |
| Dataset | All datasets with foreign keys |
| Severity | Error |
| Validation Type | FK existence check |
| Failure Condition | Foreign key value does not exist in parent dataset |
| Expected System Response | Exclude affected records; flag for review |
| Blocks Processing | No (unless widespread) |
| Manual Override Allowed | No |
| Override Audit Required | N/A |
| Output Status | Rejected (record level) |

---

### 12. Hospital Consistency

| Property | Value |
|---|---|
| Test ID | VAL-012 |
| Test Name | Hospital Identifier Consistency |
| Dataset | All datasets |
| Severity | Error |
| Validation Type | Reference check |
| Failure Condition | `hospital_id` does not exist in `hospital_master` |
| Expected System Response | Exclude affected records |
| Blocks Processing | No (unless widespread) |
| Manual Override Allowed | No |
| Override Audit Required | N/A |
| Output Status | Rejected (record level) |

---

### 13. Department Consistency

| Property | Value |
|---|---|
| Test ID | VAL-013 |
| Test Name | Department Identifier Consistency |
| Dataset | All datasets with department references |
| Severity | Error |
| Validation Type | Reference check |
| Failure Condition | `department_id` does not exist in `department_master` or does not belong to stated `hospital_id` |
| Expected System Response | Exclude affected records |
| Blocks Processing | No (unless widespread) |
| Manual Override Allowed | No |
| Override Audit Required | N/A |
| Output Status | Rejected (record level) |

---

### 14. Staff-Role Consistency

| Property | Value |
|---|---|
| Test ID | VAL-014 |
| Test Name | Staff Role Identifier Consistency |
| Dataset | `staff_master`, `staff_roster`, `staffing_requirement` |
| Severity | Error |
| Validation Type | Reference check |
| Failure Condition | `staff_role_id` does not exist in `staff_role_master` |
| Expected System Response | Exclude affected records |
| Blocks Processing | No (unless widespread) |
| Manual Override Allowed | No |
| Override Audit Required | N/A |
| Output Status | Rejected (record level) |

---

### 15. Employment-Period Validity

| Property | Value |
|---|---|
| Test ID | VAL-015 |
| Test Name | Staff Employment Period Validity |
| Dataset | `staff_master`, `staff_attendance`, `staff_roster` |
| Severity | Error |
| Validation Type | Date range check |
| Failure Condition | Attendance or roster date falls outside staff employment period |
| Expected System Response | Exclude affected records |
| Blocks Processing | No (unless widespread) |
| Manual Override Allowed | No |
| Override Audit Required | N/A |
| Output Status | Rejected (record level) |

---

### 16. Roster-Attendance Reconciliation

| Property | Value |
|---|---|
| Test ID | VAL-016 |
| Test Name | Roster and Attendance Record Reconciliation |
| Dataset | `staff_roster`, `staff_attendance` |
| Severity | Warning |
| Validation Type | Reconciliation check |
| Failure Condition | Scheduled shift exists without matching attendance record |
| Expected System Response | Flag `Pending Review`; calculate completeness; lower confidence |
| Blocks Processing | No |
| Manual Override Allowed | Yes |
| Override Audit Required | Yes |
| Output Status | Pending Review |

---

### 17. Negative-Value Checks

| Property | Value |
|---|---|
| Test ID | VAL-017 |
| Test Name | Negative Value Detection |
| Dataset | All datasets with numeric fields |
| Severity | Error |
| Validation Type | Range check |
| Failure Condition | Negative value in a field that must be non-negative |
| Expected System Response | Exclude affected records; flag as data error |
| Blocks Processing | No (unless widespread) |
| Manual Override Allowed | No |
| Override Audit Required | N/A |
| Output Status | Rejected (record level) |

---

### 18. Logical Range Checks

| Property | Value |
|---|---|
| Test ID | VAL-018 |
| Test Name | Logical Range Validation |
| Dataset | All datasets with bounded numeric fields |
| Severity | Warning |
| Validation Type | Range check |
| Failure Condition | Value falls outside logically expected range (e.g., percentage > 100) |
| Expected System Response | Flag for review; allow calculation with disclosure |
| Blocks Processing | No |
| Manual Override Allowed | Yes |
| Override Audit Required | Yes |
| Output Status | Warning |

---

### 19. Bed-Capacity Consistency

| Property | Value |
|---|---|
| Test ID | VAL-019 |
| Test Name | Bed Capacity Logical Consistency |
| Dataset | `bed_capacity_records` |
| Severity | Warning |
| Validation Type | Logical check |
| Failure Condition | `occupied_beds` > `operational_beds` |
| Expected System Response | Flag overcapacity; preserve calculated ratio; do not cap |
| Blocks Processing | No |
| Manual Override Allowed | No |
| Override Audit Required | N/A |
| Output Status | Warning |

---

### 20. Queue-Period Consistency

| Property | Value |
|---|---|
| Test ID | VAL-020 |
| Test Name | Queue Record Period Consistency |
| Dataset | `patient_queue_records` |
| Severity | Error |
| Validation Type | Date check |
| Failure Condition | Queue record date does not fall within the reporting period |
| Expected System Response | Exclude affected records |
| Blocks Processing | No (unless widespread) |
| Manual Override Allowed | No |
| Override Audit Required | N/A |
| Output Status | Rejected (record level) |

---

### 21. Encounter-Time Consistency

| Property | Value |
|---|---|
| Test ID | VAL-021 |
| Test Name | Encounter Timestamp Consistency |
| Dataset | `patient_encounters`, `patient_queue_records` |
| Severity | Error |
| Validation Type | Timestamp comparison |
| Failure Condition | `service_start_datetime` < `arrival_datetime` |
| Expected System Response | Exclude affected records; flag as data error |
| Blocks Processing | No (unless widespread) |
| Manual Override Allowed | No |
| Override Audit Required | N/A |
| Output Status | Rejected (record level) |

---

### 22. Complaint-Status Validity

| Property | Value |
|---|---|
| Test ID | VAL-022 |
| Test Name | Complaint Status Validity |
| Dataset | `patient_complaints` |
| Severity | Error |
| Validation Type | Domain check |
| Failure Condition | `complaint_status` is not in approved domain |
| Expected System Response | Exclude affected records |
| Blocks Processing | No (unless widespread) |
| Manual Override Allowed | No |
| Override Audit Required | N/A |
| Output Status | Rejected (record level) |

---

### 23. Survey-Scale Validity

| Property | Value |
|---|---|
| Test ID | VAL-023 |
| Test Name | Survey Scale Validity |
| Dataset | `patient_surveys` |
| Severity | Error |
| Validation Type | Logical check |
| Failure Condition | `scale_maximum` <= `scale_minimum` |
| Expected System Response | Exclude affected records; flag `Data Quality Review Required` |
| Blocks Processing | No (unless widespread) |
| Manual Override Allowed | No |
| Override Audit Required | N/A |
| Output Status | Rejected (record level) |

---

### 24. Source Freshness

| Property | Value |
|---|---|
| Test ID | VAL-024 |
| Test Name | Source Data Freshness |
| Dataset | All source datasets |
| Severity | Information |
| Validation Type | Recency check |
| Failure Condition | Most recent record is older than approved freshness threshold |
| Expected System Response | Disclose last record date; reduce confidence |
| Blocks Processing | No |
| Manual Override Allowed | Yes |
| Override Audit Required | Yes |
| Output Status | Information |

---

### 25. Historical Sufficiency

| Property | Value |
|---|---|
| Test ID | VAL-025 |
| Test Name | Historical Data Sufficiency |
| Dataset | All source datasets |
| Severity | Warning |
| Validation Type | Volume check |
| Failure Condition | Available history is below approved minimum for trend or anomaly calculation |
| Expected System Response | Return `Not Available` for trend or anomaly; calculate current KPI if possible |
| Blocks Processing | No |
| Manual Override Allowed | No |
| Override Audit Required | N/A |
| Output Status | Insufficient Data |

---

### 26. Configuration Availability

| Property | Value |
|---|---|
| Test ID | VAL-026 |
| Test Name | Required Configuration Availability |
| Dataset | All configuration files |
| Severity | Critical |
| Validation Type | File existence |
| Failure Condition | Required configuration file is missing |
| Expected System Response | Block processing; return `Not Available` |
| Blocks Processing | Yes |
| Manual Override Allowed | No |
| Override Audit Required | N/A |
| Output Status | Blocked |

---

### 27. Configuration Approval Status

| Property | Value |
|---|---|
| Test ID | VAL-027 |
| Test Name | Configuration Record Approval Status |
| Dataset | All configuration files |
| Severity | Critical |
| Validation Type | Status check |
| Failure Condition | Active configuration record has `approval_status` not equal to `Approved` |
| Expected System Response | Block activation; use previous approved version if available |
| Blocks Processing | Yes |
| Manual Override Allowed | No |
| Override Audit Required | N/A |
| Output Status | Blocked |

---

### 28. Configuration Effective Date

| Property | Value |
|---|---|
| Test ID | VAL-028 |
| Test Name | Configuration Effective Date Validity |
| Dataset | All configuration files |
| Severity | Error |
| Validation Type | Date check |
| Failure Condition | Reporting date falls outside `effective_start_date` to `effective_end_date` |
| Expected System Response | Exclude record from eligibility; search for next eligible version |
| Blocks Processing | No |
| Manual Override Allowed | No |
| Override Audit Required | N/A |
| Output Status | Not Available |

---

### 29. Threshold Availability

| Property | Value |
|---|---|
| Test ID | VAL-029 |
| Test Name | Approved Threshold Availability |
| Dataset | `kpi_threshold_config` |
| Severity | Warning |
| Validation Type | Existence check |
| Failure Condition | No approved threshold exists for KPI at required scope level |
| Expected System Response | Calculate KPI value; set threshold status to `Not Available`; require manual review |
| Blocks Processing | No |
| Manual Override Allowed | Yes |
| Override Audit Required | Yes |
| Output Status | Not Available |

---

### 30. Scenario-Assumption Availability

| Property | Value |
|---|---|
| Test ID | VAL-030 |
| Test Name | Scenario Assumption Availability |
| Dataset | `scenario_assumption_config` |
| Severity | Warning |
| Validation Type | Completeness check |
| Failure Condition | Required scenario assumption has blank value and is not optional |
| Expected System Response | Skip scenario; return `Not Available` for scenario result |
| Blocks Processing | No |
| Manual Override Allowed | Yes |
| Override Audit Required | Yes |
| Output Status | Not Available |

---

### 31. Financial-Assumption Availability

| Property | Value |
|---|---|
| Test ID | VAL-031 |
| Test Name | Financial Assumption Availability |
| Dataset | `financial_assumption_config` |
| Severity | Warning |
| Validation Type | Completeness check |
| Failure Condition | Required financial assumption has blank value and is not optional |
| Expected System Response | Skip financial calculation; return `Not Available` |
| Blocks Processing | No |
| Manual Override Allowed | Yes |
| Override Audit Required | Yes |
| Output Status | Not Available |

---

## Severity Definitions

| Severity | Meaning | Action Required |
|---|---|---|
| Information | Advisory only; does not affect processing. | Review at convenience. |
| Warning | Potential issue detected; processing continues with reduced confidence or disclosure. | Review recommended. |
| Error | Specific record or subset is invalid; excluded from calculation. | Review and correct source data. |
| Critical | System cannot proceed without resolution. | Immediate attention required. |

---

## Output Status Definitions

| Status | Meaning |
|---|---|
| Valid | Data passed all applicable validations. |
| Warning | Data passed with warnings or reduced confidence. |
| Rejected | Specific records failed validation and were excluded. |
| Pending Review | Data requires manual review before final classification. |
| Blocked | Processing cannot continue due to critical validation failure. |
| Insufficient Data | Data exist but do not meet minimum requirements. |
| Not Available | Required data or configuration is missing. |

---

## Test-Summary Matrix

| Test ID | Test Name | Dataset | Severity | Blocks Processing |
|---|---|---|---|---|
| VAL-001 | Source File Presence | All source | Critical | Yes |
| VAL-002 | File Extension Validation | All uploaded | Error | Yes |
| VAL-003 | File Size Sanity Check | All uploaded | Warning | No |
| VAL-004 | Schema Column Match | All datasets | Critical | Yes |
| VAL-005 | Required Column Population | All datasets | Critical | Yes (if widespread) |
| VAL-006 | Data Type Validation | All datasets | Error | No |
| VAL-007 | Date Format and Range | All with dates | Error | No |
| VAL-008 | Datetime Format | All with datetimes | Error | No |
| VAL-009 | Required Field Completeness | All source | Warning | No |
| VAL-010 | Primary Key Uniqueness | All with PKs | Critical | Yes |
| VAL-011 | Foreign Key Integrity | All with FKs | Error | No |
| VAL-012 | Hospital Identifier Consistency | All | Error | No |
| VAL-013 | Department Identifier Consistency | All with dept | Error | No |
| VAL-014 | Staff Role Consistency | Staff datasets | Error | No |
| VAL-015 | Employment Period Validity | Staff datasets | Error | No |
| VAL-016 | Roster-Attendance Reconciliation | Roster, attendance | Warning | No |
| VAL-017 | Negative Value Detection | All numeric | Error | No |
| VAL-018 | Logical Range Validation | All bounded numeric | Warning | No |
| VAL-019 | Bed Capacity Consistency | Bed capacity | Warning | No |
| VAL-020 | Queue Record Period | Queue records | Error | No |
| VAL-021 | Encounter Timestamp Consistency | Encounters, queue | Error | No |
| VAL-022 | Complaint Status Validity | Complaints | Error | No |
| VAL-023 | Survey Scale Validity | Surveys | Error | No |
| VAL-024 | Source Data Freshness | All source | Information | No |
| VAL-025 | Historical Data Sufficiency | All source | Warning | No |
| VAL-026 | Configuration Availability | All config | Critical | Yes |
| VAL-027 | Configuration Approval Status | All config | Critical | Yes |
| VAL-028 | Configuration Effective Date | All config | Error | No |
| VAL-029 | Approved Threshold Availability | Threshold config | Warning | No |
| VAL-030 | Scenario Assumption Availability | Scenario config | Warning | No |
| VAL-031 | Financial Assumption Availability | Financial config | Warning | No |

---

## Document Control

| Property | Value |
|---|---|
| Document Version | 1.0 |
| Phase | Phase 1, Step 1H |
| Status | Draft |
| Tolerance Values | Pending approval in configuration |
