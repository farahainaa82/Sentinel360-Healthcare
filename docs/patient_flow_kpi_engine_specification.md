# Patient Flow KPI Engine Specification

**Step:** 2A-3
**Status:** Complete
**Engine Version:** 2A-3-1.0.0
**Configuration Version:** v1.0-draft

---

## 1. Scope

This document specifies the Patient Flow KPI Engine created in Step 2A-3 of the Sentinel360 Healthcare analytical layer.

The engine calculates exactly two patient-flow KPIs:

- **kpi_003** — Bed Occupancy Rate
- **kpi_004** — Average Patient Waiting Time

No workforce, patient-experience, financial, or predictive KPIs are calculated in this step.

---

## 2. Authoritative Inputs

### 2.1 Primary Source Datasets

| Dataset | Path | Grain | Purpose |
|---------|------|-------|---------|
| processed_operational_daily.csv | data/processed/ | hospital-department-date | Bed occupancy data |
| processed_patient_encounters.csv | data/processed/ | encounter-level | Waiting time data |

### 2.2 Supporting Inputs (cross-reference only, not modified)

| Dataset | Path |
|---------|------|
| processed_patient_flow_daily.csv | data/processed/ |
| processed_patient_queue.csv | data/processed/ |
| processed_bed_capacity.csv | data/processed/ |
| processed_service_schedule.csv | data/processed/ |

### 2.3 Configuration

| Config | Path |
|--------|------|
| KPI Definitions | config/kpi_definition_config.csv |
| Threshold Config | config/kpi_threshold_config.csv |
| Data Confidence | config/data_confidence_config.csv |

---

## 3. Formulas

### 3.1 Bed Occupancy Rate (kpi_003)

```
Bed Occupancy Rate (%) = occupied_beds / operational_beds * 100
```

**Numerator:** occupied_beds  
**Denominator:** operational_beds  
**Unit:** Percent

Rules:
- Values above 100% are preserved (overcapacity is not capped).
- operational_beds must be > 0 for calculability.
- Null operational_beds yields Insufficient Data.
- Zero operational_beds yields Zero Denominator.
- Null occupied_beds does not silently become zero.

### 3.2 Average Patient Waiting Time (kpi_004)

```
Average Patient Waiting Time (minutes) = SUM(eligible_wait_minutes) / COUNT(eligible_encounters)
```

**Numerator:** Sum of arrival_to_consultation_minutes for eligible encounters  
**Denominator:** Count of eligible encounters  
**Unit:** Minutes

Rules:
- Only officially eligible encounters are included.
- Eligibility requires: encounter_wait_eligible_flag = True AND exclusion_reason_code is null.
- Negative wait intervals are excluded.
- Null wait-minute values are excluded.
- Queue counts are never used as waiting minutes.
- Unsupported timestamps are not substituted.
- If no eligible encounters exist, the KPI is unavailable.

---

## 4. Eligibility

### 4.1 Bed Occupancy Rate

A source row is eligible if:
1. All required fields are present.
2. operational_beds is not null and > 0.
3. occupied_beds is not null.

### 4.2 Average Patient Waiting Time

An encounter is eligible if:
1. encounter_wait_eligible_flag is True.
2. exclusion_reason_code is null.
3. arrival_to_consultation_minutes is not null and >= 0.

---

## 5. Exclusions

Exclusions are recorded when:

| Reason Code | Description |
|-------------|-------------|
| ELIGIBILITY | Row or encounter failed eligibility criteria |

---

## 6. Null Handling

| Scenario | Behaviour |
|----------|-----------|
| operational_beds is null | Insufficient Data |
| operational_beds is 0 | Zero Denominator |
| occupied_beds is null | Insufficient Data |
| arrival_to_consultation_minutes is null | Excluded from aggregation |
| encounter_wait_eligible_flag is False | Excluded from aggregation |

---

## 7. Zero-Denominator Handling

When operational_beds equals 0:
- calculation_status = Zero Denominator
- kpi_value = null

When no eligible encounters exist for waiting time:
- calculation_status = Insufficient Data
- kpi_value = null

---

## 8. Waiting-Time Readiness Gate

Before calculating kpi_004, the engine assesses readiness:

1. Check if official wait field exists (arrival_to_consultation_minutes).
2. Check if eligibility field exists (encounter_wait_eligible_flag).
3. Count total encounters.
4. Count eligible encounters.
5. Count valid wait-minute records.
6. Count negative intervals.
7. Determine calculation_readiness:
   - Calculable: eligible encounters exist with valid wait minutes.
   - Not Calculable: missing fields, no eligible encounters, or no valid wait minutes.

If Not Calculable:
- Still create a daily kpi_004 result row for each operational grain.
- Set kpi_value = null.
- Set calculation_status = Rule Pending or Insufficient Data.
- Record a structured issue.

---

## 9. Threshold Application

Thresholds are sourced from config/kpi_threshold_config.csv.

Current status:
- All thresholds are version v1.0-draft.
- Approval status is Draft / Pending Stakeholder Validation.
- No bound values are populated.
- Therefore, all threshold statuses are "Not Assessed".
- threshold_is_provisional = True for all results.

---

## 10. Data Confidence

Confidence is evaluated per KPI result using:

- Numerator completeness
- Denominator completeness
- Source field validity
- Calculation run ID presence
- For waiting time: eligibility rule approval status

| Score | Level |
|-------|-------|
| >= 90 | High |
| >= 70 | Medium |
| >= 40 | Low |
| < 40  | Unavailable |

If waiting-time data is unavailable because the eligibility rule is pending, confidence is not High.

---

## 11. Output Schemas

### 11.1 analytical_patient_flow_kpi_daily.csv

| Field | Type | Description |
|-------|------|-------------|
| analytical_record_id | string | Deterministic ID: AKPI-{kpi_id}-{hospital_id}-{department_id}-{YYYYMMDD} |
| hospital_id | string | Hospital identifier |
| department_id | string | Department identifier |
| reporting_date | date | Reporting date |
| reporting_month | int | Month from reporting_date |
| reporting_year | int | Year from reporting_date |
| kpi_id | string | kpi_003 or kpi_004 |
| kpi_name | string | Governed KPI name |
| domain | string | Patient Flow |
| numerator_value | float | Calculated numerator |
| denominator_value | float | Calculated denominator |
| kpi_value | float | Final KPI value (null if not calculated) |
| unit | string | Percent or Minutes |
| calculation_status | string | Calculated / Insufficient Data / Zero Denominator / Invalid Input / Not Calculated / Rule Pending |
| readiness_status | string | Conditionally Ready |
| threshold_status | string | Not Assessed (draft thresholds) |
| threshold_version | string | v1.0-draft |
| threshold_approval_status | string | Draft |
| threshold_is_provisional | bool | True |
| configuration_version | string | v1.0-draft |
| data_confidence_level | string | High / Medium / Low / Unavailable |
| confidence_rule_version | string | v1.0-draft |
| source_dataset | string | processed_operational_daily or processed_patient_encounters |
| source_record_id | string | Empty |
| calculation_run_id | string | Run identifier |
| calculated_at | datetime | Calculation timestamp |

### 11.2 Evidence, Exclusions, Lineage, Issues, Audit

See generated files under data/analytical/ for full schemas.

---

## 12. Lineage

Each KPI result generates one lineage record:

- lineage_id: generated UUID
- analytical_record_id: deterministic ID
- source_dataset: processed_operational_daily (kpi_003) or processed_patient_encounters (kpi_004)
- transformation_name: calculate_kpi_003 or calculate_kpi_004
- calculation_run_id: run identifier

---

## 13. Audit

Audit records capture:

- Load events (source row counts)
- Calculation events (result counts)
- Configuration versions
- Threshold versions
- Waiting-time readiness assessment

---

## 14. Immutability

Phase 1 processed datasets, Step 2A-1 governance outputs, and Step 2A-2 workforce outputs are verified before and after execution. Any unexplained change is a blocking failure.

Verified datasets (12 Phase 1 files + 6 Step 2A-2 files + 8 Step 2A-1 files).

All verified as unchanged.

---

## 15. Limitations

- Thresholds are draft; no bound values are applied.
- Confidence rules are provisional.
- Only two KPIs are calculated; other KPIs belong to later steps.
- No trend, anomaly, forecast, or recommendation logic is included.
- Average Patient Waiting Time is calculated only from eligible encounters with valid wait-minute records.
- 1,825 operational daily rows have no bed occupancy data (null occupied_beds/operational_beds).
