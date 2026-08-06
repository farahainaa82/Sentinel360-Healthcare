# Workforce KPI Formula and Evidence Mapping

**Step:** 2A-2
**Status:** Complete

---

## 1. Staffing Level (kpi_001)

| Attribute | Value |
|-----------|-------|
| KPI ID | kpi_001 |
| KPI Name | Staffing Level |
| Domain | Workforce |
| Formula | (present_staff_count + replacement_staff_count) / planned_staff_count * 100 |
| Unit | Percent |

### Numerator

| Property | Value |
|----------|-------|
| Source Fields | present_staff_count, replacement_staff_count |
| Source Dataset | processed_operational_daily.csv |
| Aggregation | Sum of present + replacement |
| Inclusion Rule | Both fields are included when available; replacement staff may be zero |
| Null Treatment | If both are null, KPI is not calculable (Insufficient Data) |

### Denominator

| Property | Value |
|----------|-------|
| Source Field | planned_staff_count |
| Source Dataset | processed_operational_daily.csv |
| Inclusion Rule | Must be > 0 for calculability |
| Null Treatment | Null planned_staff_count yields Insufficient Data |
| Zero Treatment | Zero planned_staff_count yields Zero Denominator |

### Evidence

- Numerator evidence record: evidence_type = "numerator", source_field = "present_staff_count + replacement_staff_count"
- Denominator evidence record: evidence_type = "denominator", source_field = "planned_staff_count"

### Calculation Status Rules

| Condition | Status |
|-----------|--------|
| planned_staff_count > 0 and (present or replacement not null) | Calculated |
| planned_staff_count = 0 | Zero Denominator |
| planned_staff_count is null | Insufficient Data |
| Both present and replacement are null | Insufficient Data |
| Missing required field | Invalid Input |

### Threshold

| Property | Value |
|----------|-------|
| Source | config/kpi_threshold_config.csv |
| Version | v1.0-draft |
| Approval Status | Draft / Pending Stakeholder Validation |
| Bound Values | None populated |
| Applied Status | Not Assessed |
| Is Provisional | True |

### Confidence

| Property | Value |
|----------|-------|
| Source | config/data_confidence_config.csv |
| Rule Version | v1.0-draft |
| High Threshold | >= 90 |
| Medium Threshold | >= 70 |
| Low Threshold | >= 40 |

---

## 2. Staff Absenteeism Rate (kpi_002)

| Attribute | Value |
|-----------|-------|
| KPI ID | kpi_002 |
| KPI Name | Staff Absenteeism Rate |
| Domain | Workforce |
| Formula | unapproved_absence_count / planned_staff_count * 100 |
| Unit | Percent |

### Numerator

| Property | Value |
|----------|-------|
| Source Field | unapproved_absence_count |
| Source Dataset | processed_operational_daily.csv |
| Aggregation | Direct value |
| Inclusion Rule | Only unapproved absences are counted |
| Null Treatment | Null yields Insufficient Data |

### Denominator

| Property | Value |
|----------|-------|
| Source Field | planned_staff_count |
| Source Dataset | processed_operational_daily.csv |
| Inclusion Rule | Must be > 0 for calculability |
| Null Treatment | Null yields Insufficient Data |
| Zero Treatment | Zero yields Zero Denominator |

### Evidence

- Numerator evidence record: evidence_type = "numerator", source_field = "unapproved_absence_count"
- Denominator evidence record: evidence_type = "denominator", source_field = "planned_staff_count"

### Calculation Status Rules

| Condition | Status |
|-----------|--------|
| planned_staff_count > 0 and unapproved_absence_count not null | Calculated |
| planned_staff_count = 0 | Zero Denominator |
| planned_staff_count is null | Insufficient Data |
| unapproved_absence_count is null | Insufficient Data |
| Missing required field | Invalid Input |

### Threshold

| Property | Value |
|----------|-------|
| Source | config/kpi_threshold_config.csv |
| Version | v1.0-draft |
| Approval Status | Draft / Pending Stakeholder Validation |
| Bound Values | None populated |
| Applied Status | Not Assessed |
| Is Provisional | True |

### Confidence

| Property | Value |
|----------|-------|
| Source | config/data_confidence_config.csv |
| Rule Version | v1.0-draft |
| High Threshold | >= 90 |
| Medium Threshold | >= 70 |
| Low Threshold | >= 40 |

---

## 3. Source Field Availability Summary

| Field | kpi_001 | kpi_002 | Source Dataset |
|-------|---------|---------|----------------|
| hospital_id | Required | Required | processed_operational_daily |
| department_id | Required | Required | processed_operational_daily |
| reporting_date | Required | Required | processed_operational_daily |
| reporting_month | Required | Required | processed_operational_daily |
| reporting_year | Required | Required | processed_operational_daily |
| planned_staff_count | Required | Required | processed_operational_daily |
| present_staff_count | Required | - | processed_operational_daily |
| replacement_staff_count | Required | - | processed_operational_daily |
| reassigned_staff_count | Required (not in formula) | - | processed_operational_daily |
| unapproved_absence_count | - | Required | processed_operational_daily |

---

## 4. Exclusion Reasons

| Reason Code | kpi_001 | kpi_002 | Description |
|-------------|---------|---------|-------------|
| ELIGIBILITY | Yes | Yes | Row failed eligibility (zero/null planned, null numerator) |

---

## 5. Unresolved Rules

The following business rules remain unresolved and are carried forward as draft:

- Threshold bound values are pending stakeholder validation.
- Data confidence weights are provisional.
- Absence category mapping is not yet validated against operational practice.
- Approved absence classifications may require refinement.
