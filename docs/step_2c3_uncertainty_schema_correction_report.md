# Phase 2C-3 Uncertainty Schema-Correction Report

**Correction Date:** 2026-07-29
**Scope:** Focused correction of the schema-contract gap between `financial_cost_engine` and `financial_uncertainty_engine`.
**Governance Constraint:** No full pipeline rerun. No frozen Phase 2C-2 files modified. No preferred scenario selected. No unsupported ROI introduced.

---

## 1. Original Schema-Contract Gap

### 1.1 Defect Description

The Phase 2C-3 uncertainty engine executed during the initial run but produced **zero data rows** because:

- `outputs/financial_impact/step_2c3_scenario_cost_components.csv` contains 8,019 records;
- the cost-component output does **not** contain `financial_input_id`;
- the uncertainty engine requires `financial_input_id` to join with `config/financial_assumption_range.csv`;
- therefore no governed financial ranges could be matched.

### 1.2 Classification

**Defect type:** Schema-contract gap — upstream governed key dropped during cost-component serialization.

**Affected modules:**
- `src/financial_cost_engine.py` (missing `financial_input_id` in output)
- `src/financial_uncertainty_engine.py` (expected key absent in input)
- `config/financial_assumption_range.csv` (join target with unmatched key)

---

## 2. Correction Applied

### 2.1 Engine Updates

1. **`src/financial_cost_engine.py`** — Added `financial_input_id` propagation into cost-component output for future pipeline runs.
2. **`src/financial_uncertainty_engine.py`** — Corrected to accept an optional `driver_mapping` DataFrame and merge on `(scenario_run_id, cost_component_name)` to recover `financial_input_id` at runtime.

### 2.2 Join Design

**Preferred key hierarchy used:** `financial_input_id` (Priority 1) — fully populated in driver_mapping and maps 1:1 to assumption_ranges.

**Corrected join path:**
```
cost_components.[scenario_run_id, cost_component_name]
  → driver_mapping.[scenario_run_id, cost_component_name]
  → driver_mapping.financial_input_id
  → assumption_ranges.financial_input_id
```

**Cardinality:** 1:1 between cost_components and driver_mapping on join keys (confirmed: zero duplicate join keys).

**Join type:** LEFT — preserves all cost components even if mapping is missing.

### 2.3 Eligibility Classification

Each of the 8,019 cost components was classified into exactly one category:

| Classification | Count | Description |
|----------------|-------|-------------|
| Eligible — Governed Range Available | 7,845 | Valid financial_input_id, matching range, compatible units, non-zero base cost |
| Ineligible — Not Applicable | 174 | Base cost is zero; no material uncertainty to quantify |
| Ineligible — Missing Financial Input | 0 | No financial_input_id available |
| Ineligible — No Governed Range | 0 | No matching range in assumption_ranges |
| Ineligible — Actual Fixed Value | 0 | Base rate missing or zero |
| Blocked — Ambiguous Range Mapping | 0 | Multiple driver_mapping rows per component |
| Blocked — Unit Mismatch | 0 | Currency or unit incompatibility |
| Blocked — Multiple Active Ranges | 0 | Multiple assumption_ranges per financial_input_id |

### 2.4 Uncertainty Calculation

For eligible records, the engine produces:
- **lower_estimate** = base_cost × (low_rate / base_rate)
- **central_estimate** = base_cost (original calculated cost)
- **upper_estimate** = base_cost × (high_rate / base_rate)
- **range_width** = upper − lower
- **range_percentage** = (range_width / central) × 100

Operational scenario comparators (Conservative, Expected, Higher Intensity) are **kept separate** from financial uncertainty dimensions (Lower, Central, Upper).

---

## 3. Correction Results

### 3.1 Summary

| Metric | Value |
|--------|-------|
| Cost components assessed | 8,019 |
| Governed range mappings found | 11 unique financial_input_ids |
| Unique financial-input mappings | 11 |
| Eligible uncertainty records | 7,845 |
| Ineligible actual-fixed records | 0 |
| Ineligible missing-input records | 0 |
| Records without governed ranges | 0 |
| Ambiguous mappings | 0 |
| Unit mismatches | 0 |
| Uncertainty records produced | 8,019 |
| Packages with uncertainty estimates | 311 |
| Packages without uncertainty estimates | 0 |

### 3.2 Immutable Outputs Confirmed

| Output | Status |
|--------|--------|
| Cost totals | **Unchanged** — cost components not recalculated |
| Benefit totals | **Unchanged** — benefit components not recalculated |
| Net financial-impact totals | **Unchanged** — net impact not recalculated |
| ROI status | **Unchanged** — ROI register not recalculated |
| Confidence register | **Unchanged** — confidence not affected by uncertainty mapping |
| Readiness register | **Unchanged** — readiness not affected by uncertainty mapping |
| Sensitivity register | **Unchanged** — sensitivity does not consume uncertainty results |
| Break-even register | **Unchanged** — break-even not recalculated |
| Double-counting register | **Unchanged** — double-counting not rerun |

### 3.3 Updated Outputs

- `outputs/financial_impact/step_2c3_financial_uncertainty_register.csv` — 8,019 rows (7,845 eligible)
- `outputs/financial_impact/step_2c3_uncertainty_eligibility_register.csv` — 8,019 rows
- `outputs/financial_impact/step_2c3_uncertainty_schema_correction_register.csv` — 1 row
- `outputs/financial_impact/step_2c3_uncertainty_correction_summary.csv` — 20 metrics
- `outputs/financial_impact/step_2c3_management_financial_comparison.csv` — `uncertainty_range` field updated for all 311 packages
- `outputs/financial_impact/step_2c3_execution_summary.csv` — uncertainty count and test results updated
- `outputs/financial_impact/step_2c3_freeze_manifest.json` — correction timestamp and new checksums added

---

## 4. Remaining Limitations

1. **All assumption ranges remain Draft.** No stakeholder-approved ranges exist. All uncertainty estimates are analytical-draft quality.
2. **174 zero-cost components are ineligible.** These produce no uncertainty estimate because base_cost = 0. This is analytically correct but reduces coverage.
3. **Cost-component unit column is currency-only.** Rate-level units (e.g., "MYR per hour") are not preserved in cost_components.csv. The correction uses driver_mapping for unit-mismatch validation, but future cost-engine runs should preserve rate units.
4. **Stakeholder validation required.** All 7,845 eligible records carry `stakeholder_validation_required = True`.

---

## 5. Stakeholder Validation Requirement

**Yes — stakeholder validation is required.**

All uncertainty estimates are derived from `approval_status = "Draft Analytical Configuration"` ranges. No range has been stakeholder-validated. The governance warning on every eligible record is:

> "Draft analytical estimate — requires stakeholder validation"

Management must not treat these estimates as committed financial forecasts until ranges are reviewed and approved.

---

## 6. Governance Confirmations

| Assertion | Status |
|-----------|--------|
| No full financial pipeline rerun | **Confirmed** — Only uncertainty engine executed |
| Frozen Phase 2C-2 files unchanged | **Confirmed** — No modifications to scenario_modelling outputs |
| No preferred scenario selected | **Confirmed** — No scenario ranking or selection performed |
| No unsupported ROI introduced | **Confirmed** — No new ROI calculations generated |
| All 8,019 components assessed | **Confirmed** |
| Governed IDs used for joins | **Confirmed** — financial_input_id used exclusively |
| No fuzzy or label-only joins | **Confirmed** |
| No Cartesian join | **Confirmed** — row count preserved at 8,019 |
| Lower <= Central <= Upper | **Confirmed** — monotonicity verified across all eligible records |
| Scenario and uncertainty dimensions separate | **Confirmed** |
| Evidence and lineage reconcile | **Confirmed** |
| Phase 2C-2 immutability | **Confirmed** |
| Updated manifest checksums complete | **Confirmed** |

---

## 7. Test Results

**Focused correction tests:** 22/22 passed.
**Original Phase 2C-3 tests:** 50/50 passed.
**Combined:** 72/72 passed.

---

## 8. Required Conclusion

**Phase 2C-3 Financial-Impact Analysis is COMPLETE, GOVERNED, VALIDATED, UNCERTAINTY-ENABLED, CLOSED, FROZEN, and READY FOR MANAGEMENT AND STREAMLIT HANDOVER.**

---

*End of Uncertainty Schema-Correction Report*
