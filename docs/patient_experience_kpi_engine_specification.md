# Patient Experience KPI Engine Specification

**Step:** 2A-4
**Status:** Complete
**Engine Version:** 2A-4-1.0.0
**Configuration Version:** v1.0-draft

---

## 1. Scope

This document specifies the Patient Experience KPI Engine created in Step 2A-4 of the Sentinel360 Healthcare analytical layer.

The engine calculates exactly two patient-experience KPIs:

- **kpi_005** — Patient Complaint Rate
- **kpi_006** — Patient Satisfaction Score

No workforce, patient-flow, financial, or predictive KPIs are calculated in this step.

---

## 2. Authoritative Inputs

### 2.1 Primary Source Datasets

| Dataset | Path | Grain | Purpose |
|---------|------|-------|---------|
| processed_operational_daily.csv | data/processed/ | hospital-department-date | Daily encounter and survey aggregates |
| processed_patient_complaints.csv | data/processed/ | complaint-level | Complaint records |
| processed_patient_surveys.csv | data/processed/ | survey-level | Survey responses |

### 2.2 Supporting Inputs (cross-reference only, not modified)

| Dataset | Path |
|---------|------|
| processed_patient_experience_daily.csv | data/processed/ |
| processed_hospital_master.csv | data/processed/ |
| processed_department_master.csv | data/processed/ |

### 2.3 Configuration

| Config | Path |
|--------|------|
| KPI Definitions | config/kpi_definition_config.csv |
| Threshold Config | config/kpi_threshold_config.csv |
| Data Confidence | config/data_confidence_config.csv |

---

## 3. Formulas

### 3.1 Patient Complaint Rate (kpi_005)

```
Complaint Rate = (valid_complaint_count / encounter_record_count) * 1000
```

**Numerator:** valid_complaint_count (from operational_daily, complaint-eligible records aggregated daily)  
**Denominator:** encounter_record_count (from operational_daily, daily encounter volume)  
**Unit:** Complaints per 1000 encounters

Rules:
- encounter_record_count must be > 0 for calculability.
- Null encounter_record_count yields Insufficient Data.
- Zero encounter_record_count yields Zero Denominator.
- Null complaint_count does not silently become zero.
- valid_complaint_count is sourced from the governed daily aggregate.

### 3.2 Patient Satisfaction Score (kpi_006)

```
Satisfaction Score = survey_score_weighted_sum / valid_survey_response_count
```

**Numerator:** survey_score_weighted_sum (from operational_daily, sum of score * response_count)  
**Denominator:** valid_survey_response_count (from operational_daily, count of valid survey responses)  
**Unit:** Score (1-5 scale)

Rules:
- Both numerator and denominator must be non-null for calculability.
- Zero response count yields Insufficient Data (not Zero Denominator, because a score without responses is a data-availability problem).
- Response weighting is preserved; each survey row contributes response_count responses.
- Scale is 1-5 (observed and validated in source data).
- Invalid or out-of-range scores are excluded.

---

## 4. Eligibility

### 4.1 Patient Complaint Rate

A source row is eligible if:
1. `encounter_record_count` is not null.
2. `complaint_count` is not null.
3. The row has not been excluded by prior processing.

### 4.2 Patient Satisfaction Score

A source row is eligible if:
1. `survey_score_weighted_sum` is not null.
2. `valid_survey_response_count` is not null and >= 0.
3. The row has not been excluded by prior processing.

---

## 5. Exclusions

Exclusions are recorded when:

| Reason Code | Description |
|-------------|-------------|
| ELIGIBILITY | Row failed eligibility criteria for the KPI |
| NULL_FIELD | Required numerator or denominator field is null |
| INVALID_INPUT | Field value is invalid (e.g., negative response count, non-numeric score) |

---

## 6. Null Handling

| Scenario | Behaviour |
|----------|-----------|
| encounter_record_count is null | Insufficient Data |
| encounter_record_count is 0 | Zero Denominator |
| complaint_count is null | Insufficient Data |
| survey_score_weighted_sum is null | Insufficient Data |
| valid_survey_response_count is null | Insufficient Data |
| valid_survey_response_count is 0 | Insufficient Data |

---

## 7. Zero-Denominator Handling

When encounter_record_count equals 0:
- calculation_status = Zero Denominator
- kpi_value = null
- readiness_status = Not Assessed
- data_confidence_level = Unavailable

---

## 8. Complaint-Denominator Readiness Gate

Before calculating kpi_005, the engine assesses readiness:

1. Check if official denominator field exists (`encounter_record_count`).
2. Check if complaint count field exists (`complaint_count`).
3. Count total eligible complaint records.
4. Count total denominator exposure (sum of encounter_record_count across eligible rows).
5. Count duplicate complaint records.
6. Count invalid complaint records.
7. Determine calculation_readiness:
   - Provisional but Calculable: denominator exists and is provisional.
   - Not Calculable: missing fields or no eligible records.

If Not Calculable:
- Still create a daily kpi_005 result row for each operational grain.
- Set kpi_value = null.
- Set calculation_status = Insufficient Data or Zero Denominator.
- Record a structured issue.

---

## 9. Satisfaction-Weighting Readiness Gate

Before calculating kpi_006, the engine assesses readiness:

1. Check if weighted sum field exists (`survey_score_weighted_sum`).
2. Check if response count field exists (`valid_survey_response_count`).
3. Count total survey responses.
4. Count total weighted score sum.
5. Count valid and invalid score records.
6. Determine calculation_readiness:
   - Calculable: weighted sum and response count exist.
   - Not Calculable: missing fields.

---

## 10. Threshold Application

Thresholds are sourced from config/kpi_threshold_config.csv.

Current status:
- All thresholds are version v1.0-draft.
- Approval status is Draft / Pending Stakeholder Validation.
- No bound values are populated.
- Therefore, all threshold statuses are "Not Assessed".
- threshold_is_provisional = True for all results.

---

## 11. Data Confidence

Confidence is evaluated per KPI result using:

- Numerator completeness
- Denominator completeness
- Source field validity
- Calculation run ID presence

| Level | Condition |
|-------|-----------|
| Medium | calculation_status = Calculated |
| Unavailable | calculation_status = Zero Denominator or Insufficient Data |

Confidence rule version: v1.0-draft

---

## 12. Output Schemas

### 12.1 analytical_patient_experience_kpi_daily.csv

| Field | Type | Description |
|-------|------|-------------|
| analytical_record_id | string | Deterministic ID: AKPI-{kpi_id}-{hospital_id}-{department_id}-{YYYYMMDD} |
| hospital_id | string | Hospital identifier |
| department_id | string | Department identifier |
| reporting_date | date | Reporting date |
| reporting_month | int | Month from reporting_date |
| reporting_year | int | Year from reporting_date |
| kpi_id | string | kpi_005 or kpi_006 |
| kpi_name | string | Governed KPI name |
| domain | string | Patient Experience |
| numerator_value | float | Calculated numerator |
| denominator_value | float | Calculated denominator |
| kpi_value | float | Final KPI value (null if not calculated) |
| unit | string | Complaints per 1000 encounters or Score (1-5 scale) |
| calculation_status | string | Calculated / Insufficient Data / Zero Denominator / Invalid Input / Not Calculated / Rule Pending |
| readiness_status | string | Calculable / Provisional but Calculable / Not Calculable / PX Data Unavailable |
| threshold_status | string | Not Assessed (draft thresholds) |
| threshold_version | string | v1.0-draft |
| threshold_approval_status | string | Draft |
| threshold_is_provisional | bool | True |
| configuration_version | string | v1.0-draft |
| data_confidence_level | string | Medium / Unavailable |
| confidence_rule_version | string | v1.0-draft |
| source_dataset | string | processed_operational_daily.csv |
| source_record_id | string | Empty |
| calculation_run_id | string | Run identifier |
| calculated_at | datetime | Calculation timestamp |

### 12.2 Evidence, Exclusions, Lineage, Issues, Audit

See generated files under data/analytical/ for full schemas.

---

## 13. Lineage

Each KPI result generates two lineage records (one for numerator, one for denominator):

- lineage_id: generated UUID
- analytical_record_id: deterministic ID
- source_dataset: processed_operational_daily.csv
- transformation_name: calculate_kpi_005 or calculate_kpi_006
- calculation_run_id: run identifier

---

## 14. Audit

Audit records capture:

- Load events (source row counts)
- Calculation events (result counts)
- Configuration versions
- Threshold versions
- Complaint-denominator readiness assessment
- Satisfaction-weighting readiness assessment
- Formula verification results

---

## 15. Immutability

Phase 1 processed datasets, Step 2A-1 governance outputs, Step 2A-2 workforce outputs, and Step 2A-3 patient-flow outputs are verified before and after execution. Any unexplained change is a blocking failure.

Verified datasets (12 Phase 1 files + 6 Step 2A-2 files + 8 Step 2A-1 files + 6 Step 2A-3 files).

All verified as unchanged.

---

## 16. Limitations

- Thresholds are draft; no bound values are applied.
- Confidence rules are provisional.
- Only two KPIs are calculated; other KPIs belong to later steps.
- No trend, anomaly, forecast, or recommendation logic is included.
- operational_daily survey aggregation truncates weighted sums to integers (known Phase 1 characteristic).
- 598 operational daily rows have null PX data (no complaint or survey records for that grain).
- All thresholds and confidence rules are provisional (v1.0-draft).
