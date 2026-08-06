# Step 2C-2A Final Report

**Phase:** Sentinel360 Healthcare — Phase 2C-2  
**Step:** 2C-2A Input and Architecture Review  
**Date:** 2026-07-28  
**Status:** COMPLETE

---

## 1. Executive Summary

This report documents the completion of Step 2C-2A, the input and architecture review for Phase 2C-2 Scenario Modelling. No scenario calculations were performed. No financial impacts were estimated. No frozen upstream files were modified.

The review confirms that:
- All four authoritative scenario-input files are present, valid, and suitable for downstream use.
- 346 approval packages require scenario review and form the initial engine population.
- 11 packages are recommended for optional review.
- 289 packages are excluded from scenario execution but retained for audit.
- No existing scenario engine, simulation code, or Streamlit UI exists.
- Three scenario families are ready for immediate modelling; three are conditionally supported; two are blocked by data gaps.

**Step 2C-2A is accepted. The project is ready for Step 2C-2B (Scenario Catalogue and Assumption Governance).**

---

## 2. Authoritative Files Reviewed

| File | Rows | Columns | Duplicates | Version | Suitable |
|------|------|---------|------------|---------|----------|
| `step_2c1d_episode_approval_package_register.csv` | 646 | 71 | 0 | 2C-1D calibrated | Yes |
| `step_2c1d_recommendation_approval_linkage_register.csv` | 2,600 | 14 | 0 | 2C-1D calibrated | Yes |
| `step_2c1c_validated_recommendation_register.csv` | 2,881 | 77 | 0 | 2C-1C corrected | Yes |
| `step_2c1c_corrected_episode_register.csv` | 646 | 17 | 0 | 2C-1C corrected | Yes |

Only the most recent corrected and calibrated files were used. No older versions were found in `data/scenario_inputs/`.

---

## 3. Scenario-Eligible Packages

### 3.1 Required (Included in Scenario Engine)

- **Count:** 346
- **Dominant KPIs:** kpi_001 Staffing Level (174), kpi_002 Staff Absenteeism Rate (165), kpi_004 Unplanned Readmission Rate (7)
- **Priority tiers:** High (155), Critical (60), Elevated (50), mixed tiers (81)
- **Scope:** Episode-level operational configuration
- **Provisional dominant driver:** None

### 3.2 Recommended (Optional Review Group)

- **Count:** 11
- **Dominant KPI:** kpi_004 (100%)
- **Departments:** DEPT-DIAG, DEPT-ED, DEPT-OPC
- **Reason:** Multiple alternatives at hospital operations level

### 3.3 Not Required (Excluded from Scenario Engine)

- **Count:** 289
- **Dominant KPIs:** kpi_006 Patient Satisfaction Score (176), kpi_003 Bed Occupancy Rate (58), kpi_005 Patient Complaint Rate (46), kpi_004 (9)
- **Retention:** Excluded records remain in the eligibility register with `scenario_engine_status = Exclude`. No records were deleted.

---

## 4. Existing Scenario Resources

### 4.1 Found

- `config/scenario_assumption_config.csv` — 18 placeholder assumptions (Draft status, no default values). **Not yet operationally suitable.**
- `data/analytical/analytical_six_kpi_daily.csv` — 17,520 integrated rows, partial coverage.
- `data/analytical/analytical_workforce_kpi_daily.csv` — 5,840 rows, full coverage, High confidence.
- `data/analytical/analytical_patient_flow_kpi_daily.csv` — 5,840 rows, mixed coverage.
- `data/analytical/analytical_patient_experience_kpi_daily.csv` — 5,840 rows, mixed coverage.
- Supporting analytical files (risk, threshold, trend, relationship) — extensive, read-only.

### 4.2 Not Found

- Scenario engine (no `src/scenario*.py`)
- Simulation code (no Monte Carlo or discrete-event models)
- Streamlit Scenario Lab (no `pages/scenario*.py` or `app.py`)
- Scenario test suite (no `tests/test_scenario*.py`)
- Dedicated scenario baseline files (no `scenario_baselines_v1.csv`)

---

## 5. Supported Scenario Families

### 5.1 Supported Now (3 families)

1. **Staffing Coverage Adjustment** — Full baseline data for kpi_001; intervention assumptions partially defined.
2. **Absenteeism Contingency** — Full baseline data for kpi_002; intervention assumptions need definition.
3. **No-Action / Baseline Comparison** — Can be constructed from observed historical data alone.

### 5.2 Supported with Conditions (3 families)

4. **Patient-Flow / Waiting-Time Adjustment** — kpi_004 has partial data (75% coverage); kpi_003 is largely unavailable.
5. **Patient-Satisfaction Monitoring** — kpi_006 has partial data (46% coverage, Medium confidence).
6. **Combined Workforce and Flow Intervention** — Workforce side solid; flow side partial; cross-domain effects are assumed, not causal.

### 5.3 Insufficient Inputs (2 families)

7. **Bed-Capacity Adjustment** — kpi_003 has **zero** calculated baseline values across all records.
8. **Complaint-Management Validation** — kpi_005 has **1,875 Zero Denominator** rows; baseline complaint rate is uncomputable for the majority.

### 5.4 Not Suitable for Quantitative Modelling

None. All families are conceptually suitable; two are blocked by data gaps rather than by conceptual limitations.

---

## 6. Missing Inputs

| Missing Input | Affected Family | Impact | Resolution Path |
|---------------|----------------|--------|-----------------|
| kpi_003 baseline values | Bed-capacity adjustment | Blocks entire family | Backfill bed-occupancy source data or build proxy model |
| kpi_005 valid denominators | Complaint-management validation | Blocks entire family | Correct encounter-denominator ingestion or change metric |
| Default assumption values | All intervention families | Requires user entry for every run | Populate `scenario_assumption_config.csv` in 2C-2B |
| Absenteeism-intervention assumptions | Absenteeism contingency | No dedicated config exists | Define in 2C-2B |
| Cross-domain causal model | Combined intervention | Effects are assumed, not proven | Use plausibility bounds and confidence degradation |
| Scenario engine | All families | No calculation capability | Build in 2C-2C |

---

## 7. Governance Limitations

1. **No automatic approval.** The scenario engine may estimate effects; it must not produce approval decisions.
2. **No financial calculation in 2C-2.** Cost or revenue fields are out of scope for this step.
3. **Provisional KPI warnings.** kpi_003 and kpi_005 are Conditionally Approved. Any scenario involving them must carry a governance warning and cap confidence at Moderate.
4. **Non-causality language.** Cross-KPI effects from Step 2B-4 are associations. Scenario narratives must use "estimated association effect" or "plausible impact," not "caused by."
5. **Material contradiction penalty.** Departments with Material or Major contradictions in their contributing-factor records must receive downgraded scenario confidence.
6. **Data immutability.** Observed baselines must never be overwritten by scenario assumptions.

---

## 8. Proposed Phase 2C-2 Architecture

| Step | Name | Status | Scope |
|------|------|--------|-------|
| 2C-2A | Input and Architecture Review | **COMPLETE** | Verify inputs, define eligibility, inventory resources, propose structure |
| 2C-2B | Scenario Catalogue and Assumption Governance | Not started | Build assumption catalogue, populate defaults, define templates, specify UI |
| 2C-2C | Baseline and Intervention Calculation Engine | Not started | Build deterministic engine, implement formulas, handle missing data |
| 2C-2D | Multi-KPI Impact and Trade-Off Analysis | Not started | Cross-KPI impact matrices, trade-off narratives, confidence degradation |
| 2C-2E | Scenario Validation and Challenge | Not started | Sanity checks, historical comparison, validation report |
| 2C-2F | Scenario Closure and Handover | Not started | Freeze outputs, generate manifest, archive, hand over to 2C-3 / 2C-4 |

---

## 9. Deliverables Produced

1. `docs/step_2c2a_input_inventory.md` — Authoritative file verification, eligibility inventory, existing resources, data quality.
2. `docs/step_2c2a_scenario_architecture.md` — Supported families, required inputs, governance principles, proposed structure, technology architecture, risk register.
3. `outputs/scenario_modelling/step_2c2a_scenario_eligibility_register.csv` — 646 rows with `scenario_engine_status` (Include / Optional Review / Exclude).
4. `outputs/scenario_modelling/step_2c2a_input_gap_register.csv` — 8 scenario families with source-field availability, baseline status, adjustable inputs, assumptions, limitations, and support classification.
5. `docs/step_2c2a_final_report.md` — This document.

---

## 10. Acceptance Criteria

| Criterion | Evidence | Status |
|-----------|----------|--------|
| Authoritative files verified | 4 files reviewed, 0 duplicates, all suitable | Met |
| Scenario eligibility defined | 346 Required, 11 Recommended, 289 Excluded | Met |
| Existing resources inventoried | No engine found; baselines partially available | Met |
| Supported families identified | 3 Now, 3 Conditional, 2 Insufficient | Met |
| Required inputs listed | Per-family input tables in architecture doc | Met |
| Governance principles defined | 10 principles documented | Met |
| Proposed structure documented | 2C-2A through 2C-2F defined | Met |
| No scenario calculations performed | No engine run, no formulas created | Met |
| No financial impact calculated | No cost/revenue fields generated | Met |
| Frozen files not modified | All inspections read-only | Met |

---

## 11. Readiness for Step 2C-2B

| Criterion | Status |
|-----------|--------|
| Inputs verified | Yes |
| Eligibility register produced | Yes |
| Gap register produced | Yes |
| Governance principles established | Yes |
| Architecture proposed | Yes |
| Risk register created | Yes |

**Step 2C-2A is ACCEPTED. The project is ready for Step 2C-2B upon authorisation.**

---

## 12. Sign-Off

| Item | Status |
|------|--------|
| Authoritative files reviewed | Yes |
| Total approval packages accounted for | 646 (346 + 11 + 289) |
| Required scenario packages identified | 346 |
| Recommended scenario packages identified | 11 |
| Not Required packages identified | 289 |
| Existing scenario resources found | Yes (limited) |
| Supported scenario families | 3 |
| Conditionally supported scenario families | 3 |
| Unsupported scenario families | 2 (data gaps) |
| Missing inputs catalogued | Yes |
| Governance limitations documented | Yes |
| Proposed step structure | 2C-2A through 2C-2F |
| Documentation complete | 5 files produced |

**Step 2C-2A COMPLETE. Stop before Step 2C-2B.**
