# Step 2B-1 — Trend and Statistical-Signal Report

**Phase:** 2B — Diagnostic and Early-Warning Layer  
**Step:** 2B-1 — Trend and Statistical-Signal Architecture  
**Date:** 2026-07-27  
**Status:** Complete — Ready for Step 2B-1A

---

## 1. Tasks Completed

- Inspected six-KPI data date ranges and history density.
- Created draft trend-analysis configuration (`config/trend_analysis_config.csv`).
- Created draft statistical-signal configuration (`config/statistical_signal_config.csv`).
- Created draft trend-confidence configuration (`config/trend_confidence_config.csv`).
- Created `src/trend_analytical_models.py` with governed data models.
- Created `src/trend_statistical_signal_engine.py` with full engine capabilities.
- Created `src/run_trend_statistical_signal_processing.py` safe runner.
- Created `tests/test_trend_statistical_signal_engine.py` with 31 focused tests.
- Ran syntax checks — all passed.
- Ran focused tests — 31 passed, 0 failed.
- Ran controlled regression smoke tests for Steps 2A-1 through 2A-6 — 244 passed, 0 failed.
- Executed dry run — reviewed history coverage and minimum-history results.
- Executed export — generated 8 analytical datasets and 24 control outputs.
- Performed formula verification — all formulas verified with zero mismatches.
- Validated schemas, keys, evidence, and lineage — all passed.
- Verified Phase 1 and Phase 2A immutability — all unchanged.
- Created documentation triplet and threshold-independence note.

---

## 2. Files Created

- `config/trend_analysis_config.csv`
- `config/statistical_signal_config.csv`
- `config/trend_confidence_config.csv`
- `src/trend_analytical_models.py`
- `src/trend_statistical_signal_engine.py`
- `src/run_trend_statistical_signal_processing.py`
- `tests/test_trend_statistical_signal_engine.py`
- `data/analytical/analytical_kpi_period_comparisons.csv`
- `data/analytical/analytical_kpi_rolling_statistics.csv`
- `data/analytical/analytical_kpi_trend_signals.csv`
- `data/analytical/analytical_kpi_sustained_movements.csv`
- `data/analytical/analytical_kpi_trend_evidence.csv`
- `data/analytical/analytical_kpi_trend_lineage.csv`
- `data/analytical/analytical_kpi_trend_issues.csv`
- `data/analytical/analytical_kpi_trend_audit.csv`
- `outputs/trend_statistical_signals/` (24 files)
- `docs/trend_statistical_signal_architecture.md`
- `docs/trend_analysis_rules_and_formulas.md`
- `docs/step_2b1_trend_statistical_signal_report.md`
- `docs/phase_2b_threshold_independence_note.md`

---

## 3. Files Modified

None. All accepted Phase 1 and Phase 2A files remain immutable.

---

## 4. Source Counts

| Metric | Value |
|--------|-------|
| Phase 2A input records | 17,520 |
| Hospitals | 1 |
| Departments | 8 |
| Date range | 2026-01-01 to 2026-12-31 |
| Unique grains (h+d+kpi) | 48 |

---

## 5. History Coverage by KPI

| KPI | Total Rows | Calculated Rows | Unavailable Rows |
|-----|------------|-----------------|------------------|
| kpi_001 | 2,920 | 2,920 | 0 |
| kpi_002 | 2,920 | 2,920 | 0 |
| kpi_003 | 2,920 | 1,095 | 1,825 |
| kpi_004 | 2,920 | 1,095 | 1,825 |
| kpi_005 | 2,920 | 984 | 1,936 |
| kpi_006 | 2,920 | 2,383 | 537 |

---

## 6. Period Comparison Counts

| Comparison Type | Records |
|-----------------|---------|
| Baseline Period Average | 17,520 |
| Previous Available Day | 17,520 |
| Previous Calendar Day | 17,520 |
| Previous Month | 17,520 |
| Previous Week | 17,520 |
| Rolling 14-Day Average | 17,520 |
| Rolling 30-Day Average | 17,520 |
| Rolling 7-Day Average | 17,520 |
| **Total** | **140,160** |

---

## 7. Rolling Statistic Counts

| Rolling Window | Records |
|----------------|---------|
| 7-day | 12,457 |
| 14-day | 11,295 |
| 30-day | 10,439 |
| **Total** | **34,191** |

---

## 8. Signal Counts

| Signal Method | Records |
|---------------|---------|
| z_score | 11,133 |
| mad_signal | 11,133 |
| trend_slope | 11,232 |
| volatility_change | 11,133 |
| **Total** | **44,631** |

---

## 9. Sustained Movement Counts

| Movement Type | Count |
|---------------|-------|
| Sustained Decrease | 1,046 |
| Sustained Increase | 1,039 |
| **Total** | **2,085** |

---

## 10. Mathematical Trend-Direction Distribution

| Direction | Count |
|-----------|-------|
| Decreasing | 41,407 |
| Increasing | 41,737 |
| Stable | 5,803 |
| Insufficient History | 2,229 |
| Unavailable | 48,984 |

---

## 11. Business Movement Interpretation Distribution

| Interpretation | Count |
|----------------|-------|
| Improvement | 37,824 |
| Deterioration | 36,827 |
| Stable | 5,647 |
| Context Review | 8,649 |
| Insufficient History | 2,229 |
| Unavailable | 48,984 |

---

## 12. Insufficient-History Counts

| Category | Count |
|----------|-------|
| Insufficient history (comparisons) | 66 |

---

## 13. Zero-Comparison Counts

| Category | Count |
|----------|-------|
| Zero comparison value | 5,643 |

---

## 14. Zero-Variance Counts

| Category | Count |
|----------|-------|
| Zero historical variance (signals) | 0 |

---

## 15. Trend-Confidence Distribution

| Confidence Level | Count |
|------------------|-------|
| High | 15,246 |
| Medium | 17,980 |
| Low | 11,780 |
| Unavailable | 95,154 |

---

## 16. Formula Verification

| Metric | Value |
|--------|-------|
| Records checked | 140,160 |
| Matches | 140,160 |
| Mismatches | 0 |
| Maximum absolute difference | 0 |
| Verification status | Passed |

---

## 17. Evidence Validation

| Check | Result |
|-------|--------|
| Evidence present | Passed |
| Evidence rows | 183,552 |

---

## 18. Lineage Validation

| Check | Result |
|-------|--------|
| Lineage present | Passed |
| Lineage rows | 140,160 |

---

## 19. Schema Validation

| Check | Result |
|-------|--------|
| Required fields | Passed |
| Valid types | Passed |

---

## 20. Key Validation

| Check | Result |
|-------|--------|
| Unique IDs | Passed |
| Valid grains | Passed |

---

## 21. Issues and Exclusions

| Type | Count |
|------|-------|
| Issues | 0 |
| Exclusions | 0 |

---

## 22. Immutability

| Check | Result |
|-------|--------|
| Phase 1 files | Unchanged |
| Phase 2A files | Unchanged |
| Closure snapshot | Unchanged |

---

## 23. Warnings

1. All trend-analysis rules remain provisional (Draft v1.0-draft).
2. All statistical-signal sensitivities remain provisional (Draft v1.0-draft).
3. All business movement interpretations are provisional.
4. No Green, Amber, or Red classifications were generated.

---

## 24. Blocking Issues

None.

---

## 25. Provisional Analytical Rules

- Previous period comparison: min 2 valid observations
- 7-day rolling average: min 4 valid observations
- 14-day rolling average: min 7 valid observations
- 30-day rolling average: min 15 valid observations
- Z-score sensitivity: absolute z >= 2.0
- MAD sensitivity: absolute modified_z >= 3.5
- Sustained movement: min 3 consecutive valid observations
- Trend confidence thresholds: Draft v1.0-draft

---

## 26. Threshold-Independent Outputs Created

- Period comparisons with mathematical direction
- Rolling statistics (mean, median, min, max, std)
- Z-score signals
- MAD signals
- Trend slope signals
- Volatility change signals
- Sustained movement records
- Evidence and lineage records

---

## 27. Functions Intentionally Not Created

- Green, Amber, Red classifications
- Threshold-breach alerts
- Final early-warning scores
- Management recommendations
- Financial impact calculations
- Scenario modelling

---

## 28. Final Step 2B-1 Status

**COMPLETE**

All acceptance criteria met:
- Exactly six governed KPIs supported
- Only accepted Phase 2A values used
- No KPI formula recalculation
- Period comparisons generated correctly
- Rolling statistics generated correctly
- Unavailable values not converted to zero
- Minimum-history rules enforced
- Mathematical direction separate from business interpretation
- Occupancy interpretation remains context-sensitive
- Sustained movements generated
- Z-score, MAD, slope, and volatility logic valid
- No Green, Amber, or Red generated
- Evidence and lineage exist
- Formulas verify with zero mismatches
- Schemas pass
- Keys unique
- All prior files unchanged
- Tests pass

---

## 29. Readiness for Step 2B-1A

**Ready**

The trend and statistical-signal architecture is established and validated. Step 2B-1A may proceed with:
- Signal aggregation
- Signal prioritisation
- Candidate alert generation
- Threshold-independent early-warning candidate identification

---

## 30. Recommended Next Step

Proceed to **Step 2B-1A** — Signal Aggregation and Candidate Early-Warning Identification.
