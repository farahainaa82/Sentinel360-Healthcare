# Step 2A-2 — Workforce KPI Processing Report

**Date:** 2026-07-27
**Calculation Run ID:** WF-KPI-AE9BC170EF5F
**Engine Version:** 2A-2-1.0.0
**Configuration Version:** v1.0-draft
**Threshold Version:** v1.0-draft
**Status:** COMPLETE

---

## 1. Tasks Completed

| # | Task | Status |
|---|------|--------|
| 1 | Read Phase 1 and Step 2A-1 acceptance evidence | Done |
| 2 | Record accepted dataset checksums | Done |
| 3 | Inspect workforce source fields | Done |
| 4 | Confirm exact field mappings for kpi_001 and kpi_002 | Done |
| 5 | Validate formulas against registry | Done |
| 6 | Create src/workforce_kpi_engine.py | Done |
| 7 | Create src/run_workforce_kpi_processing.py | Done |
| 8 | Create tests/test_workforce_kpi_engine.py | Done |
| 9 | Run focused unit tests | Done |
| 10 | Fix genuine implementation failures | Done |
| 11 | Run complete Step 2A-2 test file | Done (30/30 passed) |
| 12 | Execute dry run | Done |
| 13 | Execute runner with exports | Done |
| 14 | Generate analytical datasets | Done |
| 15 | Generate control outputs | Done |
| 16 | Perform independent formula verification | Done (Passed) |
| 17 | Validate schemas and keys | Done |
| 18 | Validate threshold and confidence assignments | Done |
| 19 | Verify Phase 1 immutability | Done (All unchanged) |
| 20 | Verify Step 2A-1 immutability | Done (All unchanged) |
| 21 | Create documentation | Done |
| 22 | Produce final report | Done |

---

## 2. Files Created

### Implementation

| File | Description |
|------|-------------|
| src/workforce_kpi_engine.py | Governed workforce KPI calculation engine |
| src/run_workforce_kpi_processing.py | Safe runner with dry-run and export support |
| tests/test_workforce_kpi_engine.py | 30 focused tests for engine and runner |

### Analytical Datasets (data/analytical/)

| File | Rows | Description |
|------|------|-------------|
| analytical_workforce_kpi_daily.csv | 5,840 | Daily KPI results for kpi_001 and kpi_002 |
| analytical_workforce_kpi_evidence.csv | 11,680 | Numerator and denominator evidence |
| analytical_workforce_kpi_exclusions.csv | 0 | Exclusion records (none in this run) |
| analytical_workforce_kpi_lineage.csv | 5,840 | Lineage records |
| analytical_workforce_kpi_issues.csv | 0 | Issue records (none in this run) |
| analytical_workforce_kpi_audit.csv | 1 | Audit trail |

### Control Outputs (outputs/analytical_workforce/)

| File | Description |
|------|-------------|
| workforce_kpi_run_manifest.json | Run manifest with checksums and counts |
| workforce_kpi_dataset_summary.csv | Dataset row/column summaries |
| workforce_kpi_calculation_summary.csv | Per-KPI calculation statistics |
| workforce_kpi_threshold_summary.csv | Threshold status distribution |
| workforce_kpi_confidence_summary.csv | Confidence level distribution |
| workforce_kpi_issue_log.csv | Issue log |
| workforce_kpi_exclusion_summary.csv | Exclusion summary |
| workforce_kpi_lineage_summary.csv | Lineage coverage summary |
| workforce_kpi_schema_validation.csv | Schema validation results |
| workforce_kpi_formula_verification.csv | Independent formula verification |
| workforce_kpi_immutability_verification.csv | Phase 1 immutability verification |
| workforce_kpi_audit_log.csv | Audit log |

### Documentation

| File | Description |
|------|-------------|
| docs/workforce_kpi_engine_specification.md | Engine specification |
| docs/workforce_kpi_formula_and_evidence.md | Formula and evidence mapping |
| docs/step_2a2_workforce_kpi_processing_report.md | This report |

---

## 3. Files Modified

| File | Change |
|------|--------|
| src/kpi_registry.py | Fixed build_registry_from_config to accept Path or DataFrame; fixed import |
| src/analytical_config_loader.py | Fixed import for direct execution |
| src/analytical_governance_validator.py | Fixed imports for direct execution |
| src/run_analytical_architecture_validation.py | Fixed imports for direct execution |

---

## 4. Test Results

| Suite | Tests | Passed | Failed | Errors |
|-------|-------|--------|--------|--------|
| tests/test_workforce_kpi_engine.py | 30 | 30 | 0 | 0 |

Test categories covered:
- Architecture (imports, no auto-execution, only two KPIs)
- Staffing Level (standard, replacement, zero replacement, above 100%, zero denom, null denom, null numerator, no silent conversion, deterministic ID)
- Absenteeism Rate (standard, zero absence, zero denom, null denom, approved exclusion, invalid value, deterministic ID)
- Thresholds (draft status, missing threshold, no hardcoding)
- Confidence (complete evidence, missing numerator, unavailable result)
- Outputs (schema validation, unique IDs, daily grain, two KPIs, evidence preserved, null values, lineage, exclusions, issues, audit)
- Immutability (Phase 1 unchanged, Step 2A-1 unchanged)
- Runner (dry run, export, KPI filter)

---

## 5. Source Row Counts

| Dataset | Rows |
|---------|------|
| processed_operational_daily.csv | 2,920 |

---

## 6. Output Row Counts

| Dataset | Rows |
|---------|------|
| analytical_workforce_kpi_daily.csv | 5,840 (2 KPIs x 2,920 rows) |
| analytical_workforce_kpi_evidence.csv | 11,680 (2 evidence rows per KPI result) |
| analytical_workforce_kpi_lineage.csv | 5,840 (1 per KPI result) |
| analytical_workforce_kpi_exclusions.csv | 0 |
| analytical_workforce_kpi_issues.csv | 0 |
| analytical_workforce_kpi_audit.csv | 1 |

---

## 7. Staffing Level (kpi_001) Calculation Results

| Statistic | Value |
|-----------|-------|
| Total Records | 2,920 |
| Calculated | 2,920 |
| Unavailable | 0 |
| Zero Denominator | 0 |
| Invalid Input | 0 |
| Minimum | 40.00% |
| Maximum | 100.00% |
| Mean | 86.93% |
| Median | 90.00% |
| Count Above 100% | 0 |

Note: No values exceed 100% in the current source data period. The engine preserves values above 100% when they occur.

---

## 8. Staff Absenteeism Rate (kpi_002) Calculation Results

| Statistic | Value |
|-----------|-------|
| Total Records | 2,920 |
| Calculated | 2,920 |
| Unavailable | 0 |
| Zero Denominator | 0 |
| Invalid Input | 0 |
| Minimum | 0.00% |
| Maximum | 30.00% |
| Mean | 9.66% |
| Median | 10.00% |
| Count Equal to 0% | 292 |

---

## 9. Calculation Status Distribution

| Status | Count |
|--------|-------|
| Calculated | 5,840 |
| Insufficient Data | 0 |
| Zero Denominator | 0 |
| Invalid Input | 0 |
| Not Calculated | 0 |

---

## 10. Formula Verification

| KPI | Records Checked | Matches | Mismatches | Max Diff | Status |
|-----|-----------------|---------|------------|----------|--------|
| kpi_001 | 2,920 | 2,920 | 0 | 0.0 | Passed |
| kpi_002 | 2,920 | 2,920 | 0 | 0.0 | Passed |

All calculated values match independently recomputed expected values.

---

## 11. Threshold Status Distribution

| KPI | Threshold Status | Count |
|-----|------------------|-------|
| kpi_001 | Not Assessed | 2,920 |
| kpi_002 | Not Assessed | 2,920 |

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
| kpi_001 | High | 2,920 |
| kpi_002 | High | 2,920 |

All calculated results received High confidence due to complete numerator/denominator evidence and valid source data.

---

## 14. Issues and Exclusions

| Category | Count | Details |
|----------|-------|---------|
| Issues | 0 | No issues generated |
| Exclusions | 0 | No exclusions generated (all rows eligible) |

---

## 15. Lineage Coverage

| Dataset | Lineage Records |
|---------|-----------------|
| processed_operational_daily.csv | 5,840 |

Every KPI result has a corresponding lineage record.

---

## 16. Schema and Key Validation

| Dataset | Schema Valid | Key Unique |
|---------|--------------|------------|
| analytical_workforce_kpi_daily.csv | Yes | Yes (analytical_record_id) |
| analytical_workforce_kpi_evidence.csv | Yes | N/A |
| analytical_workforce_kpi_exclusions.csv | Yes | N/A |
| analytical_workforce_kpi_lineage.csv | Yes | N/A |
| analytical_workforce_kpi_issues.csv | Yes | N/A |
| analytical_workforce_kpi_audit.csv | Yes | N/A |

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

**Result:** All Phase 1 datasets unchanged.

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

**Result:** All Step 2A-1 governance outputs unchanged.

---

## 19. Unresolved Rules

The following remain unresolved and are carried forward visibly:

1. **Threshold bound values** are pending stakeholder validation. All thresholds are marked as draft/provisional.
2. **Data confidence weights** are provisional (v1.0-draft).
3. **Absence category mapping** has not been validated against operational practice.
4. **Approved absence classifications** may require refinement.

---

## 20. Warnings

- No warnings generated.

---

## 21. Failures

- No failures.

---

## 22. Final Step 2A-2 Status

**PASSED**

All acceptance criteria met:
- Only kpi_001 and kpi_002 calculated
- Formulas match governed definitions
- Numerator and denominator evidence preserved
- Unavailable results remain null (none occurred)
- Zero denominators handled correctly (none occurred)
- Values above 100% preserved (none in source data)
- Draft threshold status visible
- Confidence status visible
- Output schemas pass
- Analytical record IDs unique
- Daily grain valid
- Formula verification passed
- Lineage and audit outputs generated
- Phase 1 data unchanged
- Step 2A-1 governance outputs unchanged
- Tests passed (30/30)
- Unresolved rules reported
- No Step 2A-3 KPI calculated

---

## 23. Readiness for Step 2A-3

Step 2A-2 is complete. The workforce KPI engine is ready for:
- Integration with patient-flow KPIs (Step 2A-3)
- Combined analytical_kpi_daily.csv generation (future step)
- Threshold stakeholder validation
- Confidence rule refinement

**Do not proceed to Step 2A-3 without explicit instruction.**
