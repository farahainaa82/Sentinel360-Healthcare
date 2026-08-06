# Workforce KPI Engine Specification

**Step:** 2A-2
**Status:** Complete
**Engine Version:** 2A-2-1.0.0
**Configuration Version:** v1.0-draft

---

## 1. Scope

This document specifies the Workforce KPI Engine created in Step 2A-2 of the Sentinel360 Healthcare analytical layer.

The engine calculates exactly two workforce KPIs:

- **kpi_001** — Staffing Level
- **kpi_002** — Staff Absenteeism Rate

No patient-flow, patient-experience, financial, or predictive KPIs are calculated in this step.

---

## 2. Authoritative Inputs

### 2.1 Primary Source Dataset

| Dataset | Path | Grain |
|---------|------|-------|
| processed_operational_daily.csv | data/processed/ | hospital-department-date |

### 2.2 Supporting Inputs

| Dataset | Path | Purpose |
|---------|------|---------|
| processed_workforce_daily.csv | data/processed/ | Cross-reference (not modified) |
| processed_staff_attendance.csv | data/processed/ | Cross-reference (not modified) |
| processed_staff_roster.csv | data/processed/ | Cross-reference (not modified) |
| processed_staffing_requirement.csv | data/processed/ | Cross-reference (not modified) |
| processed_staff_master.csv | data/processed/ | Cross-reference (not modified) |
| processed_staff_role_master.csv | data/processed/ | Cross-reference (not modified) |

### 2.3 Configuration

| Config | Path |
|--------|------|
| KPI Definitions | config/kpi_definition_config.csv |
| Threshold Config | config/kpi_threshold_config.csv |
| Data Confidence | config/data_confidence_config.csv |
| Absence Mapping | config/absence_category_mapping.csv |
| Attendance Mapping | config/attendance_status_mapping.csv |

---

## 3. Formulas

### 3.1 Staffing Level (kpi_001)

```
Staffing Level (%) = (present_staff_count + replacement_staff_count) / planned_staff_count * 100
```

**Numerator:** present_staff_count + replacement_staff_count  
**Denominator:** planned_staff_count  
**Unit:** Percent

Rules:
- Values above 100% are preserved (overstaffing is not capped).
- Replacement staff are included when present.
- Reassigned staff are not double-counted (not included in numerator).
- Null numerator components do not automatically become zero unless one component is available.
- planned_staff_count must be > 0 for the KPI to be calculable.

### 3.2 Staff Absenteeism Rate (kpi_002)

```
Staff Absenteeism Rate (%) = unapproved_absence_count / planned_staff_count * 100
```

**Numerator:** unapproved_absence_count  
**Denominator:** planned_staff_count  
**Unit:** Percent

Rules:
- Only unapproved absence counts toward the numerator.
- Approved leave, training, reassignment, and other governed exclusions are not counted.
- planned_staff_count must be > 0 for the KPI to be calculable.
- Null absence counts do not silently become zero.

---

## 4. Eligibility

A source row is eligible for a KPI if:

1. All required fields are present.
2. planned_staff_count is not null and > 0.
3. For kpi_001: at least one of present_staff_count or replacement_staff_count is not null.
4. For kpi_002: unapproved_absence_count is not null.

---

## 5. Exclusions

Exclusions are recorded when a row is ineligible for a KPI:

| Reason Code | Description |
|-------------|-------------|
| ELIGIBILITY | Row failed eligibility criteria (e.g., zero planned staff, null numerator) |

---

## 6. Null Handling

| Scenario | Behaviour |
|----------|-----------|
| planned_staff_count is null | calculation_status = Insufficient Data; kpi_value = null |
| planned_staff_count is 0 | calculation_status = Zero Denominator; kpi_value = null |
| present_staff_count is null but replacement is available | Use replacement only |
| Both present and replacement are null | calculation_status = Insufficient Data |
| unapproved_absence_count is null | calculation_status = Insufficient Data |

No silent null-to-zero conversion is performed.

---

## 7. Zero-Denominator Handling

When planned_staff_count equals 0:
- calculation_status = Zero Denominator
- kpi_value = null
- The row is excluded with reason "planned_staff_count must be > 0"

---

## 8. Threshold Application

Thresholds are sourced from config/kpi_threshold_config.csv.

Current status:
- All thresholds are version v1.0-draft.
- Approval status is Draft / Pending Stakeholder Validation.
- No bound values are populated.
- Therefore, all threshold statuses are "Not Assessed".
- threshold_is_provisional = True for all results.

---

## 9. Confidence Assessment

Confidence is evaluated per KPI result using:

- Numerator completeness
- Denominator completeness
- Source field validity
- Calculation run ID presence

| Score | Level |
|-------|-------|
| >= 90 | High |
| >= 70 | Medium |
| >= 40 | Low |
| < 40  | Unavailable |

Confidence rule version: v1.0-draft (provisional).

---

## 10. Output Schemas

### 10.1 analytical_workforce_kpi_daily.csv

| Field | Type | Description |
|-------|------|-------------|
| analytical_record_id | string | Deterministic ID: AKPI-{kpi_id}-{hospital_id}-{department_id}-{YYYYMMDD} |
| hospital_id | string | Hospital identifier |
| department_id | string | Department identifier |
| reporting_date | date | Reporting date |
| reporting_month | int | Month from reporting_date |
| reporting_year | int | Year from reporting_date |
| kpi_id | string | kpi_001 or kpi_002 |
| kpi_name | string | Governed KPI name |
| domain | string | Workforce |
| numerator_value | float | Calculated numerator |
| denominator_value | float | Calculated denominator |
| kpi_value | float | Final KPI value (null if not calculated) |
| unit | string | Percent |
| calculation_status | string | Calculated / Insufficient Data / Zero Denominator / Invalid Input / Not Calculated |
| readiness_status | string | Conditionally Ready |
| threshold_status | string | Not Assessed (draft thresholds) |
| threshold_version | string | v1.0-draft |
| threshold_approval_status | string | Draft |
| threshold_is_provisional | bool | True |
| configuration_version | string | v1.0-draft |
| data_confidence_level | string | High / Medium / Low / Unavailable |
| confidence_rule_version | string | v1.0-draft |
| source_dataset | string | processed_operational_daily |
| source_record_id | string | Empty (grain-level calculation) |
| calculation_run_id | string | Run identifier |
| calculated_at | datetime | Calculation timestamp |

### 10.2 Evidence, Exclusions, Lineage, Issues, Audit

See generated files under data/analytical/ for full schemas.

---

## 11. Lineage

Each KPI result generates one lineage record per source row:

- lineage_id: generated UUID
- analytical_record_id: deterministic ID
- source_dataset: processed_operational_daily
- transformation_name: calculate_kpi_001 or calculate_kpi_002
- calculation_run_id: run identifier

---

## 12. Audit

Audit records capture:

- Load events (source row counts)
- Calculation events (result counts)
- Configuration versions
- Threshold versions

---

## 13. Immutability

Phase 1 processed datasets and Step 2A-1 governance outputs are verified before and after execution. Any unexplained change is a blocking failure.

Verified datasets:
- processed_operational_daily.csv
- processed_workforce_daily.csv
- processed_staff_attendance.csv
- processed_staff_roster.csv
- processed_staffing_requirement.csv
- processed_staff_master.csv
- processed_staff_role_master.csv

All verified as unchanged.

---

## 14. Limitations

- Thresholds are draft; no bound values are applied.
- Confidence rules are provisional.
- Only two KPIs are calculated; other KPIs belong to later steps.
- No trend, anomaly, forecast, or recommendation logic is included.
- Source data contains no staffing levels above 100% in the current period.
