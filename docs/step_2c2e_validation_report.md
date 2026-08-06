# Step 2C-2E — Validation Report

**Document ID:** `step_2c2e_validation_report`  
**Version:** 1.0  
**Status:** Final  
**Date:** 2026-07-28  
**Run Mode:** Full (646 packages, 7,555 scenario runs)

---

## 1. Executive Summary

Step 2C-2E executed successfully across all comparable scenarios. No scenarios passed without conditions. The dominant finding is that **all 357 packages have identical comparator assumptions**, which invalidates dominance, sensitivity, and diminishing-returns assessments at face value. All downstream classifications have been downgraded or flagged accordingly.

No financial impact was calculated. No preferred scenario was selected.

---

## 2. Validation Results at a Glance

| Metric | Count / Rate |
|--------|--------------|
| Total scenario runs processed | 7,555 |
| Total packages processed | 646 |
| Scenarios with "Valid with Conditions" | 7,555 (100%) |
| Packages with "Weak Validation" scorecard | 646 (100%) |
| Packages "Not Ready" | 646 (100%) |
| Comparator inconsistencies detected | 357 / 357 (100%) |
| Numerical validations passed | 7,555 / 7,555 (100%) |
| Baseline invalidations | 1,120 / 7,555 (14.8%) |
| Assumption challenges failed | 0 |
| Governance non-compliance flags | 0 |
| Scenarios requiring revision | 7,555 (100%) |
| Scenarios rejected | 0 |

---

## 3. Engine-Level Findings

### 3.1 Assumption Challenge
- **Global hard limit violations:** Detected in assumption pool
- **Schema limitation flagged:** assumption_validation.csv has no scenario-level join key
- **All scenarios:** Passed with Flags

### 3.2 Baseline Validation
- **Invalid baselines:** 1,120 records (Blocked status or insufficient observations)
- **Valid with Conditions:** 6,435 records
- **Data completeness concerns:** Flagged where completeness < 50%

### 3.3 Numerical Validation
- **Staffing family:** Reconciliation skipped per data model quirk
- **Non-staffing families:** All reconciled within tolerance
- **No arithmetic failures** outside staffing special case

### 3.4 Comparator Consistency
- **Critical finding:** 100% of packages (357/357) have identical assumptions across all comparator types
- **Impact:** Dominance, sensitivity, and diminishing-returns classifications are not assessable under standard logic
- **Action:** All downstream engines downgraded or flagged affected records

### 3.5 Dominance Validation
- **Original Dominant classifications:** Downgraded to Non-Dominated where comparator values are identical
- **Downgraded records:** 714 (all Dominant claims affected)

### 3.6 Sensitivity Validation
- **Stable classifications:** Flagged as Unstable due to identical comparator values
- **All packages:** Reclassified to Unstable or Flagged

### 3.7 Diminishing Returns Validation
- **Confirmed classifications:** 0 (all affected by identical comparators)
- **Not Assessable / Invalid Comparison:** 357/357

### 3.8 Displacement Validation
- **Evidence basis missing:** Flagged where empty
- **Monitoring requirement missing:** Flagged where empty
- **Overall:** Plausible with Conditions

### 3.9 Management Interpretation
- **Forbidden phrases:** None detected in current dataset
- **Readiness:** All flagged for review due to upstream validation conditions

### 3.10 Governance
- **Causality status:** 100% "Not Confirmed" (expected)
- **Confidence ceiling:** No High confidence without causality violations detected
- **Provisional warnings:** Tracked and flagged

---

## 4. Package Readiness

| Readiness Level | Count |
|-----------------|-------|
| Ready | 0 |
| Ready with Conditions | 0 |
| Not Ready | 646 |
| Rejected | 0 |

**Rationale:** The universal "Not Ready" classification stems from the identical-comparator assumption issue, which prevents meaningful comparator-based analysis. Packages require data correction or assumption revision before advancing.

---

## 5. Scorecard Summary

| Classification | Count |
|----------------|-------|
| Strong Validation | 0 |
| Acceptable with Conditions | 0 |
| Weak Validation | 646 |
| Failed Validation | 0 |
| Not Assessable | 0 |

**Scenario Validation Index (SVI) range:** All packages scored below 0.70 due to comparator inconsistency penalties.

---

## 6. Recommendations

1. **Address comparator assumption distinctness:** The identical-assumption issue is the single largest blocker. Revise assumption profiles for Conservative, Expected, and Higher Intensity comparators.
2. **Fix baseline invalidations:** 1,120 scenarios have invalid baselines (Blocked status or insufficient observations). Review data collection for these packages.
3. **Bridge assumption validation:** Create a join key (scenario_run_id or approval_package_id) in the assumption validation table to enable per-scenario assumption challenge.
4. **Confirm causality:** All scenarios remain "Not Confirmed". Establish causality assessment protocols before elevating confidence levels.
5. **Re-run 2C-2D after fixes:** Once assumptions are corrected, re-execute Step 2C-2D to regenerate comparator-dependent outputs, then re-run 2C-2E.

---

**End of Report**
