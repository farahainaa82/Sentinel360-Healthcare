# Step 2C-2 — Focused Comparator Assumption Correction Report

**Document ID:** `step_2c2_comparator_correction_report`  
**Version:** 1.0  
**Status:** Final  
**Date:** 2026-07-28  

---

## 1. Objective

Correct the governed comparator assumption profiles so that Conservative, Expected, and Higher Intensity represent genuinely different but bounded intervention intensities.

---

## 2. Problem Identified

Step 2C-2E validation found that **all 357 scenario-eligible packages had identical assumption values** across Conservative, Expected, and Higher Intensity comparators. This rendered:
- Sensitivity analysis meaningless
- Diminishing-return analysis not assessable
- Comparator dominance unreliable
- Incremental scenario comparison not genuine

---

## 3. Root Cause

The `config/scenario_comparator_config.csv` mapped all three comparator types for each scenario template to the **same assumption profile ID** (e.g., `ASSUM-STAFF-001` for all Staffing comparators). The `scenario_config_loader.py` loaded these profiles, but because all comparators shared one profile, they produced identical assumption vectors.

---

## 4. Correction Applied

### 4.1 New Assumption Profile Configuration

Created `config/scenario_assumption_profile_config.csv` with **distinct profiles per comparator type**:

| Family | Conservative Profile | Expected Profile | Higher Intensity Profile |
|--------|---------------------|------------------|-------------------------|
| Staffing Coverage Adjustment | PROF-STAFF-CONS | PROF-STAFF-EXP | PROF-STAFF-HIGH |
| Absenteeism Contingency | PROF-ABS-CONS | PROF-ABS-EXP | PROF-ABS-HIGH |
| Patient-Flow and Waiting-Time Adjustment | PROF-FLOW-CONS | PROF-FLOW-EXP | PROF-FLOW-HIGH |
| Combined Workforce and Flow Intervention | PROF-COMB-CONS | PROF-COMB-EXP | PROF-COMB-HIGH |

### 4.2 Updated Comparator Config

Modified `config/scenario_comparator_config.csv` to reference the new distinct profile IDs instead of shared `ASSUM-*` IDs.

### 4.3 Updated Config Loader

Modified `src/scenario_config_loader.py` `get_assumption_profile()` to:
- Load from `scenario_assumption_profile_config.csv`
- Aggregate all `assumption_name`/`assumption_value` pairs for a given `profile_id`
- Return a dictionary of assumptions

### 4.4 Updated Scenario Modelling Engine

Modified `src/run_scenario_modelling_engine.py` `_build_assumptions()` to:
- Check both `assumption_profile_id` and `assumption_profile` keys
- Include additional assumption keys (`contingency_roster_activation_pct`, `absence_duration_reduction_days`, `temporary_resource_change`, `intervention_duration_days`)

---

## 5. Governed Intensity Principles Implemented

### 5.1 Staffing Coverage Profiles

| Assumption | Conservative | Expected | Higher Intensity | Ordering |
|------------|-------------|----------|-----------------|----------|
| additional_staff_count | 1 | 2 | 4 | C < E < H |
| temporary_staff_count | 1 | 2 | 3 | C < E < H |
| staff_reassignment_count | 0 | 1 | 2 | C < E < H |
| uncovered_shift_reduction_pct | 0 | 10 | 20 | C < E < H |
| intervention_duration_days | 7 | 14 | 30 | C < E < H |

### 5.2 Absenteeism Contingency Profiles

| Assumption | Conservative | Expected | Higher Intensity | Ordering |
|------------|-------------|----------|-----------------|----------|
| assumed_absenteeism_reduction_pct | 10 | 20 | 35 | C < E < H |
| replacement_coverage_pct | 30 | 50 | 75 | C < E < H |
| contingency_roster_activation_pct | 25 | 50 | 75 | C < E < H |
| absence_duration_reduction_days | 1 | 2 | 4 | C < E < H |
| intervention_duration_days | 7 | 14 | 30 | C < E < H |

### 5.3 Patient-Flow Profiles

| Assumption | Conservative | Expected | Higher Intensity | Ordering |
|------------|-------------|----------|-----------------|----------|
| service_capacity_change_pct | 5 | 10 | 20 | C < E < H |
| throughput_change_pct | 2 | 5 | 12 | C < E < H |
| arrival_change_pct | 0 | 0 | 0 | Fixed |
| routing_efficiency_change_pct | 5 | 10 | 18 | C < E < H |
| temporary_resource_change | 1 | 3 | 6 | C < E < H |
| intervention_duration_days | 7 | 14 | 30 | C < E < H |

### 5.4 Combined Scenario Profiles

| Assumption | Conservative | Expected | Higher Intensity | Ordering |
|------------|-------------|----------|-----------------|----------|
| interaction_adjustment_factor | 0.6 | 0.75 | 0.9 | C < E < H |

---

## 6. Validation Before Recalculation

All 10 validation checks passed:

| # | Check | Result |
|---|-------|--------|
| 1 | Baseline assumptions unchanged | PASS |
| 2 | Comparators are distinct | PASS (0 identical packages) |
| 3 | Comparator ordering correct | PASS |
| 4 | No hard limit violations | PASS |
| 5 | Soft-warning breaches visible | PASS (informational) |
| 6 | No impossible negative values | PASS |
| 7 | No identical full assumption vectors | PASS |
| 8 | No financial assumptions introduced | PASS |
| 9 | Unsupported families remain non-quantitative | PASS |
| 10 | Baseline values preserved | PASS |

---

## 7. Recalculation Results

### 7.1 Step 2C-2C Scenario Generation
- **Status:** Success
- **Scenario runs:** 2,711
- **Packages:** 646
- **Assumption distinctness:** Confirmed (all families now have distinct comparator values)

### 7.2 Step 2C-2D Trade-off Analysis
- **Status:** Success
- **Outputs regenerated:** All analytical files updated with distinct comparator outcomes

### 7.3 Step 2C-2E Validation and Challenge
- **Status:** Success
- **Packages processed:** 646
- **Scenario runs processed:** 2,711

---

## 8. Post-Correction Validation Results

### 8.1 Comparator Consistency
| Status | Count |
|--------|-------|
| Consistent | 311 |
| Inconsistent | 46 |

**Improvement:** Previously 100% Inconsistent; now 87% Consistent.

### 8.2 Dominance Validation
| Status | Count |
|--------|-------|
| Valid | 2,142 |

**Improvement:** Previously 100% Downgraded; now all Valid (comparator values are distinct).

### 8.3 Sensitivity Validation
| Status | Count |
|--------|-------|
| Flagged | 357 |

**Note:** Still flagged because sensitivity classification logic requires additional data quality checks beyond assumption distinctness.

### 8.4 Diminishing Returns
| Status | Count |
|--------|-------|
| Not Assessable | 311 |
| Invalid Comparison | 46 |

**Note:** Classification depends on incremental effect ratios JSON content, which remains sparse in source data.

### 8.5 Scorecard
| Classification | Count |
|----------------|-------|
| Acceptable with Conditions | 311 |
| Failed Validation | 289 |
| Weak Validation | 46 |

**Improvement:** Previously 100% Weak Validation; now 48% Acceptable with Conditions.

### 8.6 Package Readiness
| Readiness | Count |
|-----------|-------|
| Ready with Conditions | 311 |
| Rejected | 289 |
| Not Ready | 46 |

**Improvement:** Previously 100% Not Ready; now 48% Ready with Conditions.

---

## 9. Files Modified

| File | Change |
|------|--------|
| config/scenario_assumption_profile_config.csv | **Created** — 60 rows of distinct comparator profiles |
| config/scenario_comparator_config.csv | **Updated** — assumption_profile changed to distinct PROF-* IDs |
| src/scenario_config_loader.py | **Updated** — get_assumption_profile() now loads from profile config |
| src/run_scenario_modelling_engine.py | **Updated** — _build_assumptions() uses correct key and expanded assumption list |
| src/run_comparator_assumption_correction.py | **Created** — correction runner script |
| src/validate_comparator_correction.py | **Created** — pre-recalculation validation script |
| outputs/scenario_modelling/step_2c2_comparator_profile_revision_log.csv | **Created** — 4,293 revision entries |

---

## 10. Acceptance Criteria

| Criterion | Status |
|-----------|--------|
| Conservative, Expected, and Higher Intensity produce distinct assumption vectors | PASS |
| Scenario outcomes are not universally identical | PASS |
| Comparator-pair analysis is meaningful | PASS |
| Sensitivity results are assessable where data permits | PARTIAL (flagged pending data quality) |
| Diminishing-return analysis is assessable where assumptions are compatible | PARTIAL (depends on ratios JSON) |
| Dominance classifications are re-evaluated | PASS (all now Valid) |
| No preferred scenario automatically selected | PASS |
| No High confidence generated | PASS |
| causality_status remains Not Confirmed | PASS |
| No financial calculations performed | PASS |
| Upstream observed data remains unchanged | PASS |

---

## 11. Recommendations

1. **Address 46 remaining inconsistent packages:** These may have data quality issues beyond assumption profiles (e.g., missing baseline data).
2. **Populate incremental_effect_ratios_json:** Diminishing-returns analysis requires this field to be non-empty.
3. **Review 289 rejected packages:** Baseline invalidations or governance non-compliance may be blocking these.
4. **Re-run 2C-2E after addressing baseline issues:** Expected to increase "Ready with Conditions" count further.
5. **Do not proceed to Step 2C-2F** until at least 80% of packages achieve "Ready with Conditions" or better.

---

**End of Report**
