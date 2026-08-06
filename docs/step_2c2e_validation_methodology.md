# Step 2C-2E — Validation Methodology

**Document ID:** `step_2c2e_validation_methodology`  
**Version:** 1.0  
**Status:** Final  
**Date:** 2026-07-28  
**Scope:** Methodology for Step 2C-2E Scenario Validation and Challenge.

---

## 1. Purpose

Step 2C-2E provides a governed validation and challenge layer over the frozen outputs of Step 2C-2C (Scenario Generation and Confidence Scoring) and Step 2C-2D (Scenario Effect Classification, Comparator Analysis, and Trade-off Profiling). It does not modify upstream data, select preferred scenarios, or calculate financial impact.

---

## 2. Validation Architecture

### 2.1 Engine Modules

| # | Engine | Input Files | Output File |
|---|--------|-------------|-------------|
| 1 | Assumption Challenge | scenario_runs, scenario_assumption_validation | analytical_scenario_assumption_challenge.csv |
| 2 | Baseline Validation | scenario_runs, scenario_baselines | analytical_scenario_baseline_validation.csv |
| 3 | Numerical Validation | scenario_runs, scenario_kpi_impacts | analytical_scenario_numerical_validation.csv |
| 4 | Comparator Consistency | scenario_runs, scenario_comparator_analysis | analytical_scenario_comparator_validation.csv |
| 5 | Dominance Validation | scenario_dominance, comparator_validation | analytical_scenario_dominance_validation.csv |
| 6 | Sensitivity Validation | scenario_sensitivity, comparator_validation | analytical_scenario_sensitivity_validation.csv |
| 7 | Diminishing Returns Validation | scenario_diminishing_returns, comparator_validation, scenario_runs | analytical_scenario_diminishing_return_validation.csv |
| 8 | Displacement Validation | scenario_risk_displacement | analytical_scenario_displacement_validation.csv |
| 9 | Management Interpretation Validator | scenario_management_interpretation, wording rules | analytical_scenario_management_interpretation_validation.csv |
| 10 | Governance Validator | scenario_runs, scenario_confidence | analytical_scenario_validation_governance.csv |
| 11 | Scorecard Engine | All validation outputs, scenario_runs | analytical_scenario_validation_scorecard.csv |
| 12 | Evidence Engine | All engine instances (aggregated) | analytical_scenario_validation_evidence.csv, lineage.csv, governance.csv, issues.csv |

### 2.2 Configuration Files

| # | Config File | Rules |
|---|-------------|-------|
| 1 | scenario_validation_rule_config.csv | 20 top-level validation rules |
| 2 | scenario_baseline_validity_config.csv | 8 baseline validity thresholds |
| 3 | scenario_assumption_plausibility_config.csv | 6 assumption plausibility checks |
| 4 | scenario_comparator_consistency_config.csv | 6 comparator consistency checks |
| 5 | scenario_dominance_validation_config.csv | 5 dominance validation checks |
| 6 | scenario_sensitivity_validation_config.csv | 6 sensitivity validation checks |
| 7 | scenario_displacement_validation_config.csv | 6 displacement validation checks |
| 8 | scenario_management_wording_rule_config.csv | 6 management wording rules |

---

## 3. Join Key Governance

All merges enforce:
- Join key existence validation (both sides)
- Cartesian product detection (warn if output > 10x input)
- Explicit suffix handling

Primary join keys:
- `scenario_run_id` — per-scenario traceability
- `approval_package_id` — per-package aggregation
- `episode_id` — clinical episode linkage
- `scenario_template_id` — template-level grouping

---

## 4. Validation Status Taxonomy

### 4.1 Scenario-Level Statuses
- Valid
- Valid with Conditions
- Invalid Baseline
- Failed Assumption Challenge
- Non-Compliant
- Rejected

### 4.2 Package Readiness Levels
- Ready
- Ready with Conditions
- Not Ready
- Rejected

### 4.3 Scorecard Classifications
- Strong Validation (SVI >= 0.85)
- Acceptable with Conditions (SVI >= 0.70)
- Weak Validation (SVI >= 0.50)
- Failed Validation (SVI > 0)
- Not Assessable (SVI = 0)

---

## 5. Special Data Handling

### 5.1 Staffing Family Numerical Reconciliation
The staffing family uses a data model where `absolute_change` equals the sum of staff additions, not `scenario_value - baseline_value`. The numerical validation engine skips arithmetic reconciliation for staffing scenarios and flags this explicitly.

### 5.2 Orphan Assumption Validation Table
`analytical_scenario_assumption_validation.csv` contains no `scenario_run_id` or `approval_package_id`. The assumption challenge engine performs global pool checks and flags this schema limitation rather than attempting an invalid join.

### 5.3 Identical Comparator Assumptions
All 357 packages in the frozen dataset have identical assumptions across Conservative, Expected, and Higher Intensity comparators. The comparator consistency engine flags this as "Inconsistent". Downstream engines (dominance, sensitivity, diminishing returns) consume this flag and downgrade or reclassify accordingly.

---

## 6. Evidence and Lineage

Every engine produces:
- **Lineage records**: source file, source ID, link type
- **Evidence records**: evidence type, source, metadata JSON
- **Governance records**: rule applied, outcome, message
- **Issue records**: issue type, severity, description, recommended action

The Evidence Engine aggregates these into unified outputs.

---

## 7. Output Manifest

The runner generates `step_2c2e_run_manifest.json` containing:
- Step identifier (2C-2E)
- Run timestamp
- Smoke test flag
- Stage timings
- Per-file SHA-256 checksums and sizes

---

**End of Methodology**
