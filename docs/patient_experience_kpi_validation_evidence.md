# Patient Experience KPI Validation Evidence

## Step 2A-4

---

## 1. Validation Run ID

`PEX-KPI-DCF120177644`

## 2. Validation Date

2026-07-27

## 3. Scope

This document records the validation evidence for the Patient Experience KPI Engine (Step 2A-4).

Validation covers:
- Formula correctness
- Null handling
- Zero-denominator handling
- Governance flag preservation
- Immutability of prior steps
- Output schema conformance
- Deterministic ID generation
- Unique ID constraints

---

## 4. Formula Verification Evidence

### 4.1 Method

An independent recomputation pass recalculates every kpi_005 and kpi_006 value from raw source fields and compares it to the engine-calculated value.

Tolerance: 1e-9 absolute difference.

### 4.2 Results

| Metric | Value |
|--------|-------|
| Records checked | 3,367 |
| Matches | 3,367 |
| Mismatches | 0 |
| Max absolute difference | 0.0 |
| Unavailable records | 598 |
| Zero denominator records | 1,875 |
| Status | **Passed** |

### 4.3 Conclusion

All calculable records produce values that match independent recomputation. No formula defect is present.

---

## 5. Null Handling Evidence

### 5.1 Test Cases

| Scenario | kpi_005 Expected | kpi_006 Expected | Result |
|----------|------------------|------------------|--------|
| Null denominator | Insufficient Data | — | Pass |
| Null complaint count | Insufficient Data | — | Pass |
| Null weighted sum | — | Insufficient Data | Pass |
| Null response count | — | Insufficient Data | Pass |
| Zero encounters | Zero Denominator | — | Pass |

### 5.2 Production Output Verification

- 598 records with Insufficient Data: all kpi_value fields are null.
- 1,875 records with Zero Denominator: all kpi_value fields are null.
- No non-null kpi_value exists for non-Calculated status.

### 5.3 Conclusion

Null handling conforms to specification.

---

## 6. Zero-Denominator Evidence

### 6.1 Test Cases

| Condition | Expected Status | Expected kpi_value | Result |
|-----------|-----------------|--------------------|--------|
| encounter_record_count = 0 | Zero Denominator | null | Pass |

### 6.2 Production Output Verification

- 1,875 Zero Denominator records confirmed.
- All have kpi_value = null.
- All have data_confidence_level = Unavailable.
- All have readiness_status = Not Assessed.

### 6.3 Conclusion

Zero-denominator handling conforms to specification.

---

## 7. Governance Flag Preservation Evidence

### 7.1 Threshold Flags

| Attribute | Expected | Actual | Result |
|-----------|----------|--------|--------|
| threshold_status | Not Assessed (all) | Not Assessed (all) | Pass |
| threshold_version | v1.0-draft (all) | v1.0-draft (all) | Pass |
| threshold_approval_status | Draft (all) | Draft (all) | Pass |
| threshold_is_provisional | True (all) | True (all) | Pass |

### 7.2 Confidence Flags

| Attribute | Expected | Actual | Result |
|-----------|----------|--------|--------|
| Calculated records | Medium | Medium | Pass |
| Zero Denominator records | Unavailable | Unavailable | Pass |
| Insufficient Data records | Unavailable | Unavailable | Pass |
| confidence_rule_version | v1.0-draft (all) | v1.0-draft (all) | Pass |

### 7.3 Configuration Version

| Attribute | Expected | Actual | Result |
|-----------|----------|--------|--------|
| configuration_version | v1.0-draft (all) | v1.0-draft (all) | Pass |

### 7.4 Conclusion

All governance flags are preserved exactly as specified.

---

## 8. Immutability Evidence

### 8.1 Phase 1 Datasets

| Dataset | Baseline Checksum | Current Checksum | Match |
|---------|-------------------|------------------|-------|
| processed_staff_roster.csv | Verified | Verified | Yes |
| processed_staff_attendance.csv | Verified | Verified | Yes |
| processed_staffing_requirement.csv | Verified | Verified | Yes |
| processed_workforce_daily.csv | Verified | Verified | Yes |
| processed_patient_encounters.csv | Verified | Verified | Yes |
| processed_patient_queue.csv | Verified | Verified | Yes |
| processed_bed_capacity.csv | Verified | Verified | Yes |
| processed_service_schedule.csv | Verified | Verified | Yes |
| processed_patient_flow_daily.csv | Verified | Verified | Yes |
| processed_hospital_master.csv | Verified | Verified | Yes |
| processed_department_master.csv | Verified | Verified | Yes |
| processed_operational_daily.csv | Verified | Verified | Yes |

### 8.2 Step 2A-1 Governance Outputs

| Dataset | Baseline Checksum | Current Checksum | Match |
|---------|-------------------|------------------|-------|
| kpi_definition_config.csv | Verified | Verified | Yes |
| kpi_threshold_config.csv | Verified | Verified | Yes |
| data_confidence_config.csv | Verified | Verified | Yes |
| role_approval_config.csv | Verified | Verified | Yes |
| recommendation_rule_config.csv | Verified | Verified | Yes |
| trend_rule_config.csv | Verified | Verified | Yes |
| forecast_config.csv | Verified | Verified | Yes |
| scenario_assumption_config.csv | Verified | Verified | Yes |

### 8.3 Step 2A-2 Workforce KPI Outputs

| Dataset | Baseline Checksum | Current Checksum | Match |
|---------|-------------------|------------------|-------|
| analytical_workforce_kpi_daily.csv | Verified | Verified | Yes |
| analytical_workforce_kpi_evidence.csv | Verified | Verified | Yes |
| analytical_workforce_kpi_exclusions.csv | Verified | Verified | Yes |
| analytical_workforce_kpi_lineage.csv | Verified | Verified | Yes |
| analytical_workforce_kpi_issues.csv | Verified | Verified | Yes |
| analytical_workforce_kpi_audit.csv | Verified | Verified | Yes |

### 8.4 Step 2A-3 Patient Flow KPI Outputs

| Dataset | Baseline Checksum | Current Checksum | Match |
|---------|-------------------|------------------|-------|
| analytical_patient_flow_kpi_daily.csv | Verified | Verified | Yes |
| analytical_patient_flow_kpi_evidence.csv | Verified | Verified | Yes |
| analytical_patient_flow_kpi_exclusions.csv | Verified | Verified | Yes |
| analytical_patient_flow_kpi_lineage.csv | Verified | Verified | Yes |
| analytical_patient_flow_kpi_issues.csv | Verified | Verified | Yes |
| analytical_patient_flow_kpi_audit.csv | Verified | Verified | Yes |

### 8.5 Conclusion

All prior datasets remain unchanged. No immutability violation detected.

---

## 9. Schema Conformance Evidence

### 9.1 Daily Output Schema

| Field | Required | Present | Nulls Allowed | Correct |
|-------|----------|---------|---------------|---------|
| analytical_record_id | Yes | Yes | No | Yes |
| hospital_id | Yes | Yes | No | Yes |
| department_id | Yes | Yes | No | Yes |
| reporting_date | Yes | Yes | No | Yes |
| kpi_id | Yes | Yes | No | Yes |
| kpi_name | Yes | Yes | No | Yes |
| domain | Yes | Yes | No | Yes |
| numerator_value | Yes | Yes | Yes | Yes |
| denominator_value | Yes | Yes | Yes | Yes |
| kpi_value | Yes | Yes | Yes | Yes |
| unit | Yes | Yes | No | Yes |
| calculation_status | Yes | Yes | No | Yes |
| readiness_status | Yes | Yes | No | Yes |
| threshold_status | Yes | Yes | No | Yes |
| threshold_version | Yes | Yes | No | Yes |
| threshold_approval_status | Yes | Yes | No | Yes |
| threshold_is_provisional | Yes | Yes | No | Yes |
| configuration_version | Yes | Yes | No | Yes |
| data_confidence_level | Yes | Yes | No | Yes |
| confidence_rule_version | Yes | Yes | No | Yes |
| source_dataset | Yes | Yes | No | Yes |
| source_record_id | Yes | Yes | No | Yes |
| calculation_run_id | Yes | Yes | No | Yes |
| calculated_at | Yes | Yes | No | Yes |

### 9.2 Conclusion

All required fields are present and conform to specification.

---

## 10. Deterministic ID Evidence

### 10.1 Format

```
AKPI-{kpi_id}-{hospital_id}-{department_id}-{YYYYMMDD}
```

### 10.2 Uniqueness

- Total records: 5,840
- Unique analytical_record_id values: 5,840
- Duplicate count: 0

### 10.3 Conclusion

ID generation is deterministic and unique.

---

## 11. Test Evidence

### 11.1 Test Suite Results

| Suite | Tests | Passed | Failed | Coverage |
|-------|-------|--------|--------|----------|
| test_patient_experience_kpi_engine.py | 38 | 38 | 0 | Architecture, formulas, null handling, zero denominator, governance flags, deterministic IDs, immutability, end-to-end |

### 11.2 Key Test Cases

| Test | Purpose | Result |
|------|---------|--------|
| test_complaint_rate_standard_calculation | Standard complaint rate formula | Pass |
| test_complaint_rate_zero_denominator | Zero encounter count handling | Pass |
| test_satisfaction_score_standard_calculation | Standard satisfaction score formula | Pass |
| test_satisfaction_score_zero_responses | Zero response handling | Pass |
| test_threshold_provisional_preserved | Draft threshold visibility | Pass |
| test_confidence_not_fabricated | No fabricated confidence | Pass |
| test_formula_verification_passes | Independent recomputation | Pass |
| test_immutability_verification | Prior step integrity | Pass |

### 11.3 Conclusion

All tests pass. No regression detected.

---

## 12. Acceptance Criteria

| Criterion | Evidence | Status |
|-----------|----------|--------|
| Only kpi_005 and kpi_006 calculated | Output contains exactly these two KPIs | Pass |
| No workforce or patient-flow KPIs | Output contains no kpi_001-kpi_004 | Pass |
| Complaint rate uses per-1000 unit | Unit column correct | Pass |
| Satisfaction score uses 1-5 scale | Unit column correct | Pass |
| Unavailable values remain null | All non-Calculated kpi_value fields are null | Pass |
| Draft and provisional status visible | All threshold and confidence flags correct | Pass |
| Formula verification passes | 3,367/3,367 matches | Pass |
| Immutability verified | All prior datasets unchanged | Pass |
| Tests pass | 38/38 passed | Pass |

---

## 13. Sign-Off

| Role | Status |
|------|--------|
| Automated formula verification | Passed |
| Automated immutability check | Passed |
| Automated schema validation | Passed |
| Test suite | Passed |
| Governance flag audit | Passed |

**Overall Validation Status: Passed**

Step 2A-4 is validated and accepted for progression.
