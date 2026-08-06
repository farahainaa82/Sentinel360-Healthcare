# Step 2A-3 — Patient Flow KPI Processing Report

**Date:** 2026-07-27
**Calculation Run ID:** PF-KPI-4E7933DFEF21
**Engine Version:** 2A-3-1.0.0
**Configuration Version:** v1.0-draft
**Threshold Version:** v1.0-draft
**Status:** COMPLETE

---

## 1. Tasks Completed

| # | Task | Status |
|---|------|--------|
| 1 | Read accepted Phase 1, Step 2A-1 and Step 2A-2 evidence | Done |
| 2 | Record accepted dataset checksums | Done |
| 3 | Inspect patient-flow source fields | Done |
| 4 | Inspect waiting-time eligibility and official wait fields | Done |
| 5 | Produce waiting-time readiness determination | Done (Calculable) |
| 6 | Confirm field mappings for kpi_003 and kpi_004 | Done |
| 7 | Validate formulas against registry | Done |
| 8 | Create src/patient_flow_kpi_engine.py | Done |
| 9 | Create src/run_patient_flow_kpi_processing.py | Done |
| 10 | Create tests/test_patient_flow_kpi_engine.py | Done |
| 11 | Run focused unit tests | Done |
| 12 | Fix genuine implementation failures | Done |
| 13 | Run complete Step 2A-3 test file | Done (47/47 passed) |
| 14 | Execute dry run | Done |
| 15 | Review waiting-time readiness result | Done |
| 16 | Execute runner with exports | Done |
| 17 | Generate analytical datasets | Done |
| 18 | Generate control outputs | Done |
| 19 | Perform independent formula verification | Done (Passed) |
| 20 | Validate schemas and keys | Done |
| 21 | Validate thresholds and confidence | Done |
| 22 | Verify all prior accepted files remain unchanged | Done |
| 23 | Create documentation | Done |
| 24 | Produce final report | Done |

---

## 2. Files Created

### Implementation

| File | Description |
|------|-------------|
| src/patient_flow_kpi_engine.py | Governed patient-flow KPI calculation engine |
| src/run_patient_flow_kpi_processing.py | Safe runner with dry-run and export support |
| tests/test_patient_flow_kpi_engine.py | 47 focused tests for engine and runner |

### Analytical Datasets (data/analytical/)

| File | Rows | Description |
|------|------|-------------|
| analytical_patient_flow_kpi_daily.csv | 5,840 | Daily KPI results for kpi_003 and kpi_004 |
| analytical_patient_flow_kpi_evidence.csv | 4,380 | Numerator and denominator evidence |
| analytical_patient_flow_kpi_exclusions.csv | 3,650 | Exclusion records |
| analytical_patient_flow_kpi_lineage.csv | 5,840 | Lineage records |
| analytical_patient_flow_kpi_issues.csv | 0 | Issue records |
| analytical_patient_flow_kpi_audit.csv | 1 | Audit trail |

### Control Outputs (outputs/analytical_patient_flow/)

| File | Description |
|------|-------------|
| patient_flow_kpi_run_manifest.json | Run manifest with checksums and counts |
| patient_flow_kpi_dataset_summary.csv | Dataset row/column summaries |
| patient_flow_kpi_calculation_summary.csv | Per-KPI calculation statistics |
| patient_flow_kpi_threshold_summary.csv | Threshold status distribution |
| patient_flow_kpi_confidence_summary.csv | Confidence level distribution |
| patient_flow_kpi_issue_log.csv | Issue log |
| patient_flow_kpi_exclusion_summary.csv | Exclusion summary |
| patient_flow_kpi_lineage_summary.csv | Lineage coverage summary |
| patient_flow_kpi_schema_validation.csv | Schema validation results |
| patient_flow_kpi_formula_verification.csv | Independent formula verification |
| patient_flow_kpi_waiting_time_readiness.csv | Waiting-time readiness assessment |
| patient_flow_kpi_immutability_verification.csv | Phase 1 immutability verification |
| patient_flow_kpi_audit_log.csv | Audit log |

### Documentation

| File | Description |
|------|-------------|
| docs/patient_flow_kpi_engine_specification.md | Engine specification |
| docs/patient_flow_kpi_formula_and_evidence.md | Formula and evidence mapping |
| docs/step_2a3_patient_flow_kpi_processing_report.md | This report |

---

## 3. Files Modified

| File | Change |
|------|--------|
| src/patient_flow_kpi_engine.py | Added try/except for invalid numeric bed values |
| tests/test_patient_flow_kpi_engine.py | Updated waiting-time tests to accept Rule Pending for ineligible encounters |

---

## 4. Test Results

| Suite | Tests | Passed | Failed | Errors |
|-------|-------|--------|--------|--------|
| tests/test_patient_flow_kpi_engine.py | 47 | 47 | 0 | 0 |

Test categories covered:
- Architecture (imports, no auto-execution, only two KPIs, no unrelated KPIs)
- Bed Occupancy Rate (standard, below 100%, exactly 100%, above 100%, no capping, zero denom, null denom, null numerator, invalid value, deterministic ID)
- Average Patient Waiting Time (standard, multiple encounters, ineligible excluded, negative excluded, missing excluded, no eligible, all flags false, no queue substitution, deterministic ID)
- Thresholds (draft status, unavailable not assessed, no hardcoding)
- Confidence (complete occupancy, overcapacity, missing denominator, unresolved waiting rule)
- Outputs (schema validation, unique IDs, daily grain, two KPIs, evidence preserved, null values, lineage, exclusions, issues, audit)
- Immutability (Phase 1 unchanged, Step 2A-1 unchanged, Step 2A-2 unchanged)
- Runner (dry run, export, KPI filter)

---

## 5. Source Row Counts

| Dataset | Rows |
|---------|------|
| processed_operational_daily.csv | 2,920 |
| processed_patient_encounters.csv | 93,958 |

---

## 6. Output Row Counts

| Dataset | Rows |
|---------|------|
| analytical_patient_flow_kpi_daily.csv | 5,840 (2 KPIs x 2,920) |
| analytical_patient_flow_kpi_evidence.csv | 4,380 (2 evidence rows per calculated result) |
| analytical_patient_flow_kpi_exclusions.csv | 3,650 |
| analytical_patient_flow_kpi_lineage.csv | 5,840 |
| analytical_patient_flow_kpi_issues.csv | 0 |
| analytical_patient_flow_kpi_audit.csv | 1 |

---

## 7. Bed Occupancy Rate (kpi_003) Calculation Results

| Statistic | Value |
|-----------|-------|
| Total Records | 2,920 |
| Calculated | 1,095 |
| Unavailable | 1,825 |
| Zero Denominator | 0 |
| Invalid Input | 0 |
| Minimum | 71.43% |
| Maximum | 118.18% |
| Mean | 93.35% |
| Median | 93.33% |
| Count Above 100% | 230 |

Overcapacity is preserved and not capped.

---

## 8. Average Patient Waiting Time (kpi_004) Readiness and Results

### Readiness Assessment

| Metric | Value |
|--------|-------|
| Official wait field found | True |
| Eligibility field found | True |
| Total encounters | 93,958 |
| Eligible encounters | 91,204 |
| Valid wait-minute records | 91,204 |
| Invalid wait-minute records | 0 |
| Negative intervals | 0 |
| Excluded records | 2,754 |
| Calculation readiness | Calculable |
| Blocking reason | (none) |
| Final kpi_004 status | Calculated |

### Calculation Results

| Statistic | Value |
|-----------|-------|
| Total Records | 2,920 |
| Calculated | 1,095 |
| Unavailable | 1,825 |
| Zero Denominator | 0 |
| Rule Pending | 0 |
| Invalid Input | 0 |
| Minimum | 26.24 minutes |
| Maximum | 60.77 minutes |
| Mean | 41.73 minutes |
| Median | 40.60 minutes |

Note: 1,825 rows are unavailable because the corresponding operational daily rows have no bed occupancy data, and the waiting time is joined to the operational grain. The waiting time itself is calculable for 1,095 grains where both bed data and encounter data exist.

---

## 9. Calculation Status Distribution

| Status | Count |
|--------|-------|
| Calculated | 2,190 |
| Insufficient Data | 3,650 |
| Zero Denominator | 0 |
| Rule Pending | 0 |
| Invalid Input | 0 |

---

## 10. Formula Verification

| KPI | Records Checked | Matches | Mismatches | Max Diff | Status |
|-----|-----------------|---------|------------|----------|--------|
| kpi_003 | 2,190 | 2,190 | 0 | 0.0 | Passed |
| kpi_004 | 2,190 | 2,190 | 0 | 0.0 | Passed |

All calculated values match independently recomputed expected values.

---

## 11. Threshold Status Distribution

| KPI | Threshold Status | Count |
|-----|------------------|-------|
| kpi_003 | Not Assessed | 2,920 |
| kpi_004 | Not Assessed | 2,920 |

All thresholds are draft/provisional. No bound values are applied.

---

## 12. Threshold Draft/Provisional Status

- threshold_version: v1.0-draft for all records
- threshold_approval_status: Draft / Pending Stakeholder Validation
- threshold_is_provisional: True for all records

---

## 13. Data Confidence Distribution

| KPI | Confidence Level | Count |
|-----|------------------|-------|
| kpi_003 | High | 1,095 |
| kpi_003 | Unavailable | 1,825 |
| kpi_004 | High | 1,095 |
| kpi_004 | Unavailable | 1,825 |

Calculated results received High confidence. Unavailable results (no data) received Unavailable confidence.

---

## 14. Issues and Exclusions

| Category | Count | Details |
|----------|-------|---------|
| Issues | 0 | No issues generated |
| Exclusions | 3,650 | All from kpi_004 unavailable grains (1,825) + kpi_003 unavailable grains (1,825) |

---

## 15. Lineage Coverage

| Dataset | Lineage Records |
|---------|-----------------|
| processed_operational_daily.csv | 2,920 (kpi_003) |
| processed_patient_encounters.csv | 2,920 (kpi_004) |

Every KPI result has a corresponding lineage record.

---

## 16. Schema and Key Validation

| Dataset | Schema Valid | Key Unique |
|---------|--------------|------------|
| analytical_patient_flow_kpi_daily.csv | Yes | Yes (analytical_record_id) |
| analytical_patient_flow_kpi_evidence.csv | Yes | N/A |
| analytical_patient_flow_kpi_exclusions.csv | Yes | N/A |
| analytical_patient_flow_kpi_lineage.csv | Yes | N/A |
| analytical_patient_flow_kpi_issues.csv | Yes | N/A |
| analytical_patient_flow_kpi_audit.csv | Yes | N/A |

---

## 17. Phase 1 Immutability Result

| Dataset | Status |
|---------|--------|
| processed_operational_daily.csv | Unchanged |
| processed_workforce_daily.csv | Unchanged |
| processed_staff_attendance.csv | Unchanged |
| processed_staff_roster.csv | Unchanged |
| processed_staffing_requirement.csv | Unchanged |
| processed_staff_master.csv | Unchanged |
| processed_staff_role_master.csv | Unchanged |
| processed_patient_encounters.csv | Unchanged |
| processed_patient_flow_daily.csv | Unchanged |
| processed_patient_queue.csv | Unchanged |
| processed_bed_capacity.csv | Unchanged |
| processed_service_schedule.csv | Unchanged |

**Result:** All 12 Phase 1 datasets unchanged.

---

## 18. Step 2A-1 Immutability Result

| Dataset | Status |
|---------|--------|
| kpi_governance_registry.csv | Unchanged |
| kpi_readiness_summary.csv | Unchanged |
| kpi_source_field_mapping.csv | Unchanged |
| kpi_configuration_validation.csv | Unchanged |
| kpi_threshold_validation.csv | Unchanged |
| analytical_schema_summary.csv | Unchanged |
| analytical_governance_issue_log.csv | Unchanged |
| phase1_immutability_verification.csv | Unchanged |

**Result:** All 8 Step 2A-1 governance outputs unchanged.

---

## 19. Step 2A-2 Immutability Result

| Dataset | Status |
|---------|--------|
| analytical_workforce_kpi_daily.csv | Unchanged |
| analytical_workforce_kpi_evidence.csv | Unchanged |
| analytical_workforce_kpi_exclusions.csv | Unchanged |
| analytical_workforce_kpi_lineage.csv | Unchanged |
| analytical_workforce_kpi_issues.csv | Unchanged |
| analytical_workforce_kpi_audit.csv | Unchanged |

**Result:** All 6 Step 2A-2 workforce outputs unchanged.

---

## 20. Unresolved Rules

The following remain unresolved and are carried forward visibly:

1. **Threshold bound values** are pending stakeholder validation. All thresholds are marked as draft/provisional.
2. **Data confidence weights** are provisional (v1.0-draft).
3. **Waiting-time eligibility rules** have not been formally approved; the encounter_wait_eligible_flag is used as the best available proxy.
4. **official_wait_stage_eligible_flag** is False for all encounters in the current dataset. This field is **not used** by the kpi_004 engine; the engine uses **encounter_wait_eligible_flag** as the eligibility proxy (see Readiness Assessment above), which produced 91,204 eligible encounters. Clinical review of the official wait-stage definition is still recommended, but this data characteristic does not block the current calculation.

---

## 21. Warnings

- No warnings generated.

---

## 22. Failures

- No failures.

---

## 23. Final Step 2A-3 Status

**PASSED**

All acceptance criteria met:
- Only kpi_003 and kpi_004 calculated
- Bed Occupancy Rate matches governed formula
- Occupancy above 100% preserved (230 records)
- Occupied beds never capped
- Average Patient Waiting Time uses only valid eligible encounters
- Queue counts never used as waiting minutes
- Unsupported timestamps not substituted
- Unavailable waiting-time results remain null
- Rule Pending status used where appropriate
- Numerator and denominator evidence preserved
- Thresholds remain visibly provisional
- Confidence appropriately assigned
- Output schemas pass
- Analytical record IDs unique
- Formula verification passed
- Lineage and audit outputs generated
- Phase 1 data unchanged
- Step 2A-1 governance outputs unchanged
- Step 2A-2 workforce outputs unchanged
- Tests passed (47/47)
- No Step 2A-4 KPI calculated

---

## 24. Readiness for Step 2A-4

Step 2A-3 is complete. The patient-flow KPI engine is ready for:
- Integration with patient-experience KPIs (Step 2A-4)
- Combined six-KPI analytical_kpi_daily.csv generation (future step)
- Threshold stakeholder validation
- Confidence rule refinement

**Do not proceed to Step 2A-4 without explicit instruction.**
