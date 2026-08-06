# Step 2C-2B Final Report

**Phase:** Sentinel360 Healthcare — Phase 2C-2  
**Step:** 2C-2B Scenario Catalogue and Assumption Governance  
**Date:** 2026-07-28  
**Status:** COMPLETE

---

## 1. Executive Summary

Step 2C-2B designs the governed scenario catalogue and assumption framework for Phase 2C-2 Scenario Modelling. No scenario calculations were performed. No financial impacts were estimated. No frozen upstream files were modified.

The step delivers:
- 9 scenario templates (6 active, 3 inactive)
- 34 assumption definitions across 5 assumption sets
- 16 assumption range rules with hard limits and soft warnings
- 18 comparator definitions (baseline, conservative, expected, higher-intensity)
- 12 confidence rules
- 15 governance rules
- Complete package-to-scenario mapping for all 646 packages
- 8 identified assumption gaps
- Reconciliation of existing assumption configuration

**Step 2C-2B is accepted. Ready for Step 2C-2C upon authorisation.**

---

## 2. Scenario Templates Created

| Template ID | Family | Status | Quantitative | Active |
|-------------|--------|--------|--------------|--------|
| SCEN-STAFF-001 | Staffing Coverage Adjustment | Supported | Yes | Yes |
| SCEN-ABS-001 | Absenteeism Contingency | Supported | Yes | Yes |
| SCEN-FLOW-001 | Patient-Flow and Waiting-Time Adjustment | Supported with Conditions | Yes | Yes |
| SCEN-COMB-001 | Combined Workforce and Flow Intervention | Supported with Conditions | Yes | Yes |
| SCEN-BASE-001 | No-Action or Baseline Comparator | Supported | Yes | Yes |
| SCEN-MON-001 | Monitoring-Only or Validation Scenario | Monitoring Only | No | Yes |
| SCEN-BED-UNSUPPORTED | Bed-capacity adjustment | Unsupported | No | No |
| SCEN-COMP-UNSUPPORTED | Complaint-management intervention | Unsupported | No | No |
| SCEN-SAT-UNSUPPORTED | Patient-satisfaction intervention | Unsupported | No | No |

**Total active templates:** 6  
**Total inactive templates:** 3

---

## 3. Supported Scenario Families

### 3.1 Supported Now

1. **Staffing Coverage Adjustment** (SCEN-STAFF-001)
   - 174 Required packages (kpi_001 dominant)
   - Full baseline data available
   - 11 assumptions defined

2. **Absenteeism Contingency** (SCEN-ABS-001)
   - 165 Required packages (kpi_002 dominant)
   - Full baseline data available
   - 6 assumptions defined

3. **No-Action or Baseline Comparator** (SCEN-BASE-001)
   - All 357 eligible packages (Required + Recommended)
   - No intervention assumptions

### 3.2 Supported with Conditions

4. **Patient-Flow and Waiting-Time Adjustment** (SCEN-FLOW-001)
   - 7 Required + 11 Recommended packages (kpi_004 dominant)
   - Condition: ≥ 60% kpi_004 baseline completeness per department

5. **Combined Workforce and Flow Intervention** (SCEN-COMB-001)
   - Cross-domain packages only
   - Condition: Association-based effects only; fixed interaction factor (0.5)

### 3.3 Monitoring Only

6. **Monitoring-Only or Validation Scenario** (SCEN-MON-001)
   - All 646 packages
   - No quantitative outputs

### 3.4 Unsupported

7. **Bed-capacity adjustment** (kpi_003) — No calculated baseline
8. **Complaint-management intervention** (kpi_005) — Zero-denominator issues
9. **Patient-satisfaction intervention** (kpi_006) — Partial Medium-confidence baseline

---

## 4. Assumption Definitions

| Assumption Set | Assumptions | User-Entered | Observed Baseline | Fixed Governance |
|----------------|-------------|--------------|-------------------|------------------|
| ASSUM-STAFF-001 | 11 | 7 | 2 | 0 |
| ASSUM-ABS-001 | 6 | 4 | 1 | 0 |
| ASSUM-FLOW-001 | 9 | 6 | 3 | 0 |
| ASSUM-COMB-001 | 4 | 0 | 0 | 4 |
| ASSUM-GOV-001 | 5 | 0 | 0 | 5 |
| **Total** | **35** | **17** | **6** | **9** |

*(Note: ASSUM-BASE-001 and ASSUM-MON-001 have no adjustable assumptions.)*

---

## 5. Assumption Range Governance

- **16 range rules** created
- **All user-adjustable assumptions** have hard limits
- **All user-adjustable assumptions** have soft warning limits
- **All ranges** classified as Draft Analytical Range
- **Stakeholder validation required** for 11 of 16 rules

---

## 6. Package Mapping Results

### 6.1 All Packages Mapped

| Priority | Packages | Templates per Package | Total Rows |
|----------|----------|----------------------|------------|
| Required | 346 | 3 | 1,038 |
| Recommended | 11 | 3 | 33 |
| Not Required | 289 | 2 | 569 |
| **Total** | **646** | — | **1,640** |

### 6.2 Execution Readiness

| Readiness | Count |
|-----------|-------|
| Ready | 696 |
| Ready with Conditions | 18 |
| Monitoring Only | 646 |
| Unsupported | 280 |

### 6.3 Required Packages by Readiness

| Dominant KPI | Ready | Ready with Conditions | Monitoring Only |
|--------------|-------|----------------------|-----------------|
| kpi_001 | 522 | 0 | 174 |
| kpi_002 | 495 | 0 | 165 |
| kpi_004 | 0 | 7 | 7 |

*(Each package maps to Baseline + Intervention + Monitoring templates.)*

### 6.4 Recommended Packages by Readiness

| Dominant KPI | Ready | Ready with Conditions | Monitoring Only |
|--------------|-------|----------------------|-----------------|
| kpi_004 | 11 | 11 | 11 |

### 6.5 Not Required Packages by Readiness

| Dominant KPI | Monitoring Only | Unsupported |
|--------------|-----------------|-------------|
| kpi_006 | 176 | 176 |
| kpi_003 | 58 | 58 |
| kpi_005 | 46 | 46 |
| kpi_004 | 9 | 0 |

*(Not Required packages get Monitoring Only + Unsupported for dominant KPI.)*

---

## 7. Baseline Requirements

- **12 baseline requirements** defined across 6 scenario templates
- All quantitative templates require immutable baseline extraction
- kpi_001 and kpi_002: 100% completeness threshold
- kpi_004: 60% completeness threshold
- kpi_003: Optional (warn and exclude from model)

---

## 8. Assumption Gaps

| ID | Family | Gap | Impact |
|----|--------|-----|--------|
| GAP-001 | Absenteeism | No dedicated absenteeism-intervention config | Moderate |
| GAP-002 | Absenteeism | Absence duration reduction not parameterised | Low |
| GAP-003 | Patient Flow | Service capacity baseline not consistently recorded | High |
| GAP-004 | Patient Flow | No empirical anchor for routing efficiency change | Moderate |
| GAP-005 | Combined | Interaction factor is placeholder (0.5) | High |
| GAP-006 | Combined | No workforce-to-flow conversion ratio | High |
| GAP-007 | All | No validated trend projection model | Moderate |
| GAP-008 | All | No seasonal decomposition | Low |

---

## 9. Comparator Definitions

- **18 comparators** created across 6 scenario templates
- Every quantitative template has: Baseline, Conservative, Expected, Higher Intensity
- No comparator labelled Best Case, Guaranteed, or Optimal
- Monitoring-Only templates have a single Monitoring Only comparator

---

## 10. Confidence Rules

- **12 confidence rules** created
- Factors: baseline completeness, contradiction severity, provisional involvement, assumption extremity, missing data, combined complexity
- **No High confidence allowed** in Phase 2C-2
- Major contradiction blocks execution
- Provisional primary KPI blocks execution

---

## 11. Governance Rules

- **15 governance rules** created
- Hard enforcement on: baseline immutability, no auto-approval, no financial calculation, reproducibility
- All fixed governance parameters reject user changes

---

## 12. Existing Assumption Configuration Reconciliation

| Decision | Detail |
|----------|--------|
| Retained | `config/scenario_assumption_config.csv` (18 rows) |
| Not overwritten | Confirmed |
| Reusable fields | assumption_code, assumption_name, assumption_description, assumption_category, unit, data_type |
| Missing values | default_value, minimum_value, maximum_value, step_value (all null) |
| Blocked assumptions | EXT_HOURS, CAP_RESTORED, PEAK_STAFF (unused in supported families) |
| New assumptions | 35 definitions in new files not in existing config |
| Recommended action | Populate missing values in existing config from new range config during 2C-2C |

---

## 13. Deliverables

### Configuration Files (6)
1. `config/scenario_catalogue.csv`
2. `config/scenario_assumption_definition.csv`
3. `config/scenario_assumption_range_config.csv`
4. `config/scenario_comparator_config.csv`
5. `config/scenario_confidence_rule_config.csv`
6. `config/scenario_governance_rule_config.csv`

### Output Files (4)
7. `outputs/scenario_modelling/step_2c2b_package_scenario_mapping.csv` (1,640 rows)
8. `outputs/scenario_modelling/step_2c2b_scenario_baseline_requirement_register.csv` (12 requirements)
9. `outputs/scenario_modelling/step_2c2b_assumption_gap_register.csv` (8 gaps)
10. `outputs/scenario_modelling/step_2c2b_assumption_audit_template.csv` (empty template)

### Documentation (4)
11. `docs/step_2c2b_assumption_config_reconciliation.md`
12. `docs/step_2c2b_scenario_catalogue.md`
13. `docs/step_2c2b_governance_notes.md`
14. `docs/step_2c2b_final_report.md` (this document)

---

## 14. Validation Checklist

| # | Criterion | Status |
|---|-----------|--------|
| 1 | All 346 Required packages mapped | Yes |
| 2 | All 11 Recommended packages mapped separately | Yes |
| 3 | All 289 Not Required packages remain excluded | Yes |
| 4 | No unsupported family is quantitatively modelled | Yes |
| 5 | Every quantitative scenario has a baseline comparator | Yes |
| 6 | Every user-entered assumption has a governed range | Yes |
| 7 | Invalid values have a defined action | Yes |
| 8 | Baselines remain immutable | Yes (governance rule) |
| 9 | Assumptions do not overwrite observed data | Yes (governance rule) |
| 10 | Material contradictions reduce confidence | Yes (×0.80) |
| 11 | Major contradictions block scenario execution | Yes |
| 12 | Provisional KPIs retain warnings | Yes |
| 13 | kpi_003 and kpi_005 are not quantitatively modelled | Yes (templates inactive) |
| 14 | No High scenario confidence is allowed | Yes (capped at Moderate) |
| 15 | No scenario outputs are calculated | Yes |
| 16 | No financial values are calculated | Yes |
| 17 | Frozen upstream files remain unchanged | Yes (read-only) |
| 18 | Existing scenario_assumption_config.csv reconciled, not overwritten | Yes |
| 19 | Configuration files are structurally valid | Yes |
| 20 | Package counts reconcile (346 + 11 + 289 = 646) | Yes |

---

## 15. Readiness for Step 2C-2C

| Criterion | Status |
|-----------|--------|
| Scenario catalogue complete | Yes |
| Assumption definitions complete | Yes |
| Assumption ranges defined | Yes |
| Comparator definitions complete | Yes |
| Confidence rules defined | Yes |
| Governance rules defined | Yes |
| Package mapping complete | Yes |
| Baseline requirements documented | Yes |
| Assumption gaps identified | Yes |
| Audit template created | Yes |
| Existing config reconciled | Yes |
| No scenario calculations performed | Yes |
| No financial calculations performed | Yes |

**Step 2C-2B is ACCEPTED. Ready for Step 2C-2C (Baseline and Intervention Calculation Engine) upon authorisation.**

---

## 16. Sign-Off

| Item | Value |
|------|-------|
| Scenario templates created | 9 (6 active, 3 inactive) |
| Supported families | 3 |
| Supported-with-conditions families | 2 |
| Monitoring-only families | 1 |
| Unsupported families | 3 |
| Assumption definitions created | 35 |
| User-adjustable assumptions | 17 |
| Fixed governance assumptions | 9 |
| Assumption ranges requiring stakeholder validation | 11 of 16 |
| Required packages mapped | 346 |
| Recommended packages mapped | 11 |
| Packages Ready | 696 template rows |
| Packages Ready with Conditions | 18 template rows |
| Packages Monitoring Only | 646 template rows |
| Packages Unsupported | 280 template rows |
| Baseline requirements created | 12 |
| Assumption gaps identified | 8 |
| Comparator definitions created | 18 |
| Confidence rules created | 12 |
| Governance rules created | 15 |
| Existing assumption configuration reconciliation | Retained, not overwritten |
| No scenario calculations | Confirmed |
| No financial calculations | Confirmed |
| Source immutability | Confirmed (read-only) |
| Documentation complete | 4 files |

**Step 2C-2B COMPLETE. Stop before Step 2C-2C.**
