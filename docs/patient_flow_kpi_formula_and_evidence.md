# Patient Flow KPI Formula and Evidence Mapping

**Step:** 2A-3
**Status:** Complete

---

## 1. Bed Occupancy Rate (kpi_003)

| Attribute | Value |
|-----------|-------|
| KPI ID | kpi_003 |
| KPI Name | Bed Occupancy Rate |
| Domain | Patient Flow |
| Formula | occupied_beds / operational_beds * 100 |
| Unit | Percent |

### Numerator

| Property | Value |
|----------|-------|
| Source Field | occupied_beds |
| Source Dataset | processed_operational_daily.csv |
| Aggregation | Direct value |
| Inclusion Rule | Must not be null |
| Null Treatment | Null yields Insufficient Data |

### Denominator

| Property | Value |
|----------|-------|
| Source Field | operational_beds |
| Source Dataset | processed_operational_daily.csv |
| Inclusion Rule | Must be > 0 for calculability |
| Null Treatment | Null yields Insufficient Data |
| Zero Treatment | Zero yields Zero Denominator |

### Evidence

- Numerator evidence record: evidence_type = "numerator", source_field = "occupied_beds"
- Denominator evidence record: evidence_type = "denominator", source_field = "operational_beds"

### Calculation Status Rules

| Condition | Status |
|-----------|--------|
| operational_beds > 0 and occupied_beds not null | Calculated |
| operational_beds = 0 | Zero Denominator |
| operational_beds is null | Insufficient Data |
| occupied_beds is null | Insufficient Data |
| Invalid numeric value | Invalid Input |

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

## 2. Average Patient Waiting Time (kpi_004)

| Attribute | Value |
|-----------|-------|
| KPI ID | kpi_004 |
| KPI Name | Average Patient Waiting Time |
| Domain | Patient Flow |
| Formula | SUM(eligible_wait_minutes) / COUNT(eligible_encounters) |
| Unit | Minutes |

### Numerator

| Property | Value |
|----------|-------|
| Source Field | arrival_to_consultation_minutes |
| Source Dataset | processed_patient_encounters.csv |
| Aggregation | Sum of valid eligible wait minutes |
| Inclusion Rule | Only eligible encounters with non-null, non-negative wait minutes |
| Null Treatment | Excluded from sum |
| Negative Treatment | Excluded from sum |

### Denominator

| Property | Value |
|----------|-------|
| Source Field | eligible_encounter_count |
| Source Dataset | processed_patient_encounters.csv |
| Inclusion Rule | Count of eligible encounters with valid wait minutes |
| Zero Treatment | Zero eligible encounters yields Insufficient Data |

### Evidence

- Numerator evidence record: evidence_type = "numerator", source_field = "arrival_to_consultation_minutes"
- Denominator evidence record: evidence_type = "denominator", source_field = "eligible_encounter_count"

### Calculation Status Rules

| Condition | Status |
|-----------|--------|
| Eligible encounters > 0 and valid wait minutes exist | Calculated |
| Eligible encounters = 0 because rule unresolved | Rule Pending |
| Eligible encounters = 0 but rule approved | Insufficient Data |
| Official wait field missing | Configuration Missing |

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

| Field | kpi_003 | kpi_004 | Source Dataset |
|-------|---------|---------|----------------|
| hospital_id | Required | Required | processed_operational_daily / processed_patient_encounters |
| department_id | Required | Required | processed_operational_daily / processed_patient_encounters |
| reporting_date | Required | - | processed_operational_daily |
| reporting_month | Required | - | processed_operational_daily |
| reporting_year | Required | - | processed_operational_daily |
| occupied_beds | Required | - | processed_operational_daily |
| operational_beds | Required | - | processed_operational_daily |
| encounter_date | - | Required | processed_patient_encounters |
| arrival_to_consultation_minutes | - | Required | processed_patient_encounters |
| encounter_wait_eligible_flag | - | Required | processed_patient_encounters |
| exclusion_reason_code | - | Required | processed_patient_encounters |

---

## 4. Exclusion Reasons

| Reason Code | kpi_003 | kpi_004 | Description |
|-------------|---------|---------|-------------|
| ELIGIBILITY | Yes | Yes | Row/encounter failed eligibility criteria |

---

## 5. Waiting-Time Readiness Assessment

| Metric | Value |
|--------|-------|
| official_wait_field_found | True |
| eligibility_field_found | True |
| total_encounters | 93,958 |
| eligible_encounters | 91,204 |
| valid_wait_minute_records | 91,204 |
| invalid_wait_minute_records | 0 |
| negative_intervals | 0 |
| excluded_records | 2,754 |
| calculation_readiness | Calculable |
| blocking_reason | (none) |
| final_kpi_004_status | Calculated |

---

## 6. Unresolved Rules

The following remain unresolved and are carried forward visibly:

1. **Threshold bound values** are pending stakeholder validation. All thresholds are marked as draft/provisional.
2. **Data confidence weights** are provisional (v1.0-draft).
3. **Waiting-time eligibility rules** have not been formally approved; the encounter_wait_eligible_flag is used as the best available proxy.
