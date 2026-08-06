# Phase 2C-2C Validation Report

## 1. Executive Summary

The Phase 2C-2C Baseline and Intervention Calculation Engine was validated through:
- 8 focused automated tests
- Smoke test with single-package execution
- Full production run across 1,640 package-scenario mappings
- Manual inspection of output files and data quality

**Result: PASS** — All validation criteria met.

## 2. Test Results

| Test ID | Description | Status |
|---------|-------------|--------|
| 2C-2C-01 | Baseline lookup consistency | PASS |
| 2C-2C-02 | Comparator type parsing | PASS |
| 2C-2C-03 | No financial fields | PASS |
| 2C-2C-04 | Unsupported KPIs blocked | PASS |
| 2C-2C-05 | Confidence never High | PASS |
| 2C-2C-06 | Causality Not Confirmed | PASS |
| 2C-2C-07 | Comparator balance | PASS |
| 2C-2C-08 | Manifest integrity | PASS |

## 3. Output Verification

### 3.1 File Inventory

| File | Rows | Status |
|------|------|--------|
| analytical_scenario_baselines.csv | 1,640 | Valid |
| analytical_scenario_runs.csv | 2,711 | Valid |
| analytical_scenario_kpi_impacts.csv | 2,711 | Valid |
| analytical_scenario_assumption_validation.csv | 3,870 | Valid |
| analytical_scenario_confidence.csv | 2,711 | Valid |
| analytical_scenario_non_quantitative_register.csv | 1,283 | Valid |
| analytical_scenario_evidence.csv | 14,616 | Valid |
| analytical_scenario_lineage.csv | 14,616 | Valid |
| analytical_scenario_governance.csv | 21,420 | Valid |
| analytical_scenario_issues.csv | 0 | Valid (no issues) |
| step_2c2c_run_manifest.json | — | Valid |
| step_2c2c_execution_summary.csv | — | Valid |

### 3.2 Data Quality Checks

- **No financial columns**: Verified — zero cost/price/revenue/financial columns in scenario runs
- **Unsupported KPIs blocked**: Verified — kpi_003, kpi_005, kpi_006 have zero quantitative results
- **Confidence distribution**: 72 Moderate, 1,356 Low, 1,283 Insufficient Evidence, 0 High
- **Causality**: 100% "Not Confirmed"
- **Comparator balance**: All four comparator types produce exactly 357 completed results each

## 4. Scenario Execution Breakdown

| Family | Completed | Blocked | Monitoring Only |
|--------|-----------|---------|-----------------|
| Staffing Coverage Adjustment | 696 | 0 | 0 |
| Absenteeism Contingency | 660 | 0 | 0 |
| Patient-Flow and Waiting-Time Adjustment | 72 | 0 | 0 |
| Combined Workforce and Flow Intervention | 0 | 0 | 0 |
| Monitoring Only / No-Action | 0 | 0 | 560 |
| Unsupported Families | 0 | 723 | 0 |

**Total scenarios attempted**: 2,711
**Total completed**: 1,428
**Total blocked**: 723
**Total monitoring-only**: 560

## 5. Performance Metrics

| Phase | Time (seconds) |
|-------|----------------|
| Input loading | 0.52 |
| Baseline construction | 17.44 |
| Scenario calculations | 3.13 |
| Output writing | <1.0 |
| **Total execution** | **~22** |

The engine completes a full run in approximately 22 seconds after the O(n²) confidence-loop performance fix.

## 6. Known Limitations

1. **Combined scenarios**: Zero completed results because no packages map to SCEN-COMB-001 in the current dataset.
2. **Patient-flow scenarios**: Only 72 completed results due to limited packages mapping to SCEN-FLOW-001.
3. **Provisional warnings**: Zero in current run because provisional KPIs are excluded from quantitative modelling.
4. **Material contradictions**: Zero in current run.

## 7. Governance Compliance

| Rule | Status |
|------|--------|
| No financial calculations | PASS |
| No High confidence for provisional/contradictory | PASS |
| Causality fixed to Not Confirmed | PASS |
| Unsupported KPIs excluded | PASS |
| Material contradiction reduces confidence | PASS (mechanism verified) |
| Major contradiction blocks execution | PASS (mechanism verified) |

## 8. Conclusion

The Phase 2C-2C engine is validated and ready for production use. All outputs are correct, all governance rules are enforced, and performance is acceptable for the dataset size.

**Signed off**: Step 2C-2C Validation
**Date**: 2026-07-28
