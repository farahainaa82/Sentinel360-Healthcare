# Step 2C-2E — Consolidated Input and Schema Inventory

**Document ID:** `step_2c2e_input_schema_inventory`  
**Version:** 1.0  
**Status:** Final  
**Date:** 2026-07-28  
**Scope:** Authoritative inputs from frozen Step 2C-2C and Step 2C-2D outputs. No placeholder or derived 2C-2E files are included.

---

## 1. Inventory Summary

| # | File Key | Filename | Rows | Columns | PK Unique | PK Column(s) |
|---|----------|----------|------|---------|-----------|--------------|
| 1 | scenario_runs | analytical_scenario_runs.csv | 2,711 | 44 | Yes | scenario_run_id |
| 2 | scenario_baselines | analytical_scenario_baselines.csv | 1,640 | 34 | Yes | baseline_id |
| 3 | scenario_assumption_validation | analytical_scenario_assumption_validation.csv | 3,870 | 9 | Yes | validation_id |
| 4 | scenario_confidence | analytical_scenario_confidence.csv | 2,711 | 6 | Yes | scenario_run_id |
| 5 | scenario_comparator_analysis | analytical_scenario_comparator_analysis.csv | 1,785 | 13 | Yes | comparison_id |
| 6 | scenario_effect_classification | analytical_scenario_effect_classification.csv | 1,428 | 13 | Yes | effect_id |
| 7 | scenario_dominance | analytical_scenario_dominance.csv | 2,142 | 9 | Yes | dominance_id |
| 8 | scenario_sensitivity | analytical_scenario_sensitivity.csv | 357 | 11 | Yes | sensitivity_id |
| 9 | scenario_diminishing_returns | analytical_scenario_diminishing_returns.csv | 357 | 6 | Yes | diminishing_return_id |
| 10 | scenario_risk_displacement | analytical_scenario_risk_displacement.csv | 1,950 | 15 | Yes | displacement_id |
| 11 | scenario_management_interpretation | analytical_scenario_management_interpretation.csv | 357 | 17 | Yes | interpretation_id |
| 12 | scenario_evidence | analytical_scenario_evidence.csv | 14,616 | 9 | Yes | evidence_id |
| 13 | scenario_governance | analytical_scenario_governance.csv | 21,420 | 8 | **No** | governance_id |
| 14 | scenario_lineage | analytical_scenario_lineage.csv | 14,616 | 7 | Yes | lineage_id |
| 15 | scenario_non_comparable_register | analytical_scenario_non_comparable_register.csv | 1,283 | 44 | Yes | scenario_run_id |
| 16 | scenario_kpi_impacts | analytical_scenario_kpi_impacts.csv | 2,711 | 9 | Yes | scenario_run_id |
| 17 | scenario_primary_impacts | analytical_scenario_primary_impacts.csv | 1,428 | 16 | Yes | primary_impact_id |
| 18 | scenario_supporting_kpi_impacts | analytical_scenario_supporting_kpi_impacts.csv | 1,428 | 9 | Yes | supporting_impact_id |
| 19 | scenario_tradeoff_profiles | analytical_scenario_tradeoff_profiles.csv | 1,428 | 9 | Yes | profile_id |
| 20 | scenario_tradeoff_evidence | analytical_scenario_tradeoff_evidence.csv | 1,428 | 8 | Yes | evidence_id |
| 21 | scenario_tradeoff_lineage | analytical_scenario_tradeoff_lineage.csv | 1,428 | 7 | Yes | lineage_id |

---

## 2. File-by-File Schema Detail

### 2.1 scenario_runs
- **Filename:** `analytical_scenario_runs.csv`
- **Rows:** 2,711
- **Columns (44):**
  `scenario_run_id`, `approval_package_id`, `episode_id`, `scenario_template_id`, `comparator_id`, `comparator_type`, `scenario_family`, `scenario_mode`, `scenario_run_timestamp`, `engine_version`, `baseline_id`, `baseline_status`, `baseline_value`, `baseline_unit`, `baseline_reference_date`, `baseline_data_completeness`, `assumption_set_id`, `assumption_profile`, `assumption_values_json`, `assumption_validation_status`, `assumption_warning_count`, `primary_kpi_id`, `baseline_primary_kpi_value`, `scenario_primary_kpi_value`, `absolute_change`, `percentage_change`, `direction_of_change`, `operational_interpretation`, `affected_supporting_kpis`, `supporting_kpi_result_status`, `contradiction_severity`, `provisional_warning`, `causality_status`, `final_scenario_confidence`, `governance_warning`, `scenario_execution_status`, `management_review_required`, `source_file_list`, `source_record_id_list`, `recommendation_ids`, `evidence_pack_ids`, `calculation_rule_id`, `comparator_config_version`, `assumption_config_version`
- **Primary Key:** `scenario_run_id` (unique)
- **Join Keys Present:** `scenario_run_id`, `approval_package_id`, `episode_id`, `scenario_template_id`, `comparator_id`, `baseline_id`
- **Expected vs Actual:** All expected fields present. No missing fields.
- **Approved Substitutes:** None required.

### 2.2 scenario_baselines
- **Filename:** `analytical_scenario_baselines.csv`
- **Rows:** 1,640
- **Columns (34):**
  `baseline_id`, `approval_package_id`, `episode_id`, `scenario_template_id`, `hospital_id`, `department_id`, `episode_start_date`, `episode_end_date`, `dominant_kpi_id`, `dominant_kpi_name`, `baseline_kpi_value`, `baseline_kpi_unit`, `supporting_kpi_values_json`, `baseline_required_staff`, `baseline_available_staff`, `baseline_staffing_coverage_pct`, `baseline_absenteeism_rate`, `baseline_avg_wait_min`, `baseline_arrivals`, `baseline_service_capacity`, `source_file_list`, `source_record_id_list`, `baseline_observation_count`, `baseline_data_completeness`, `baseline_confidence`, `baseline_provisional_flag`, `baseline_contradiction_severity`, `baseline_status`, `baseline_created_at`, `baseline_version`, `baseline_aggregation_method`, `baseline_reference_date`, `baseline_window_start`, `baseline_window_end`
- **Primary Key:** `baseline_id` (unique)
- **Join Keys Present:** `approval_package_id`, `episode_id`, `scenario_template_id`, `baseline_id`
- **Expected vs Actual:** All expected fields present. No missing fields.
- **Approved Substitutes:** None required.

### 2.3 scenario_assumption_validation
- **Filename:** `analytical_scenario_assumption_validation.csv`
- **Rows:** 3,870
- **Columns (9):**
  `validation_id`, `assumption_id`, `original_value`, `validated_value`, `validation_outcome`, `validation_message`, `adjustment_applied`, `hard_limit_violated`, `soft_limit_violated`
- **Primary Key:** `validation_id` (unique)
- **Join Keys Present:** None
- **Critical Finding:** This file contains **no `scenario_run_id`**, `approval_package_id`, or any package-level join key. It is an orphan table in the current schema. The Step 2C-2E assumption challenge engine must handle this by validating assumptions at the global level or by mapping through `assumption_set_id` / `assumption_id` if a bridge is available. No such bridge exists in the frozen outputs.
- **Approved Substitute:** Engine will treat assumption validation as a global pool check rather than a per-scenario join.

### 2.4 scenario_confidence
- **Filename:** `analytical_scenario_confidence.csv`
- **Rows:** 2,711
- **Columns (6):**
  `scenario_run_id`, `confidence_base`, `confidence_adjustments`, `confidence_score_internal`, `final_scenario_confidence`, `confidence_rationale`
- **Primary Key:** `scenario_run_id` (unique)
- **Join Keys Present:** `scenario_run_id`
- **Expected vs Actual:** All expected fields present. No missing fields.
- **Approved Substitutes:** None required.

### 2.5 scenario_comparator_analysis
- **Filename:** `analytical_scenario_comparator_analysis.csv`
- **Rows:** 1,785
- **Columns (13):**
  `comparison_id`, `scenario_run_id_a`, `scenario_run_id_b`, `comparator_a`, `comparator_b`, `approval_package_id`, `episode_id`, `scenario_template_id`, `incremental_primary_kpi_change`, `confidence_change`, `warning_change`, `comparator_relationship`, `evidence_basis`
- **Primary Key:** `comparison_id` (unique)
- **Join Keys Present:** `approval_package_id`, `episode_id`, `scenario_template_id`
- **Expected vs Actual:** All expected fields present. No missing fields.
- **Approved Substitutes:** None required.

### 2.6 scenario_effect_classification
- **Filename:** `analytical_scenario_effect_classification.csv`
- **Rows:** 1,428
- **Columns (13):**
  `effect_id`, `scenario_run_id`, `approval_package_id`, `episode_id`, `affected_kpi_id`, `effect_classification`, `effect_direction`, `effect_magnitude_band`, `evidence_basis`, `confidence`, `contradiction_severity`, `provisional_warning`, `monitoring_requirement`
- **Primary Key:** `effect_id` (unique)
- **Join Keys Present:** `scenario_run_id`, `approval_package_id`, `episode_id`
- **Expected vs Actual:** All expected fields present. No missing fields.
- **Approved Substitutes:** None required.

### 2.7 scenario_dominance
- **Filename:** `analytical_scenario_dominance.csv`
- **Rows:** 2,142
- **Columns (9):**
  `dominance_id`, `scenario_run_id_a`, `scenario_run_id_b`, `approval_package_id`, `scenario_template_id`, `dominance_classification`, `dominance_rationale`, `conditions_met_json`, `conditions_failed_json`
- **Primary Key:** `dominance_id` (unique)
- **Join Keys Present:** `approval_package_id`, `scenario_template_id`
- **Expected vs Actual:** All expected fields present. No missing fields.
- **Approved Substitutes:** None required.

### 2.8 scenario_sensitivity
- **Filename:** `analytical_scenario_sensitivity.csv`
- **Rows:** 357
- **Columns (11):**
  `sensitivity_id`, `approval_package_id`, `scenario_template_id`, `sensitivity_classification`, `sensitivity_rationale`, `direction_stable`, `magnitude_variation`, `warning_increase`, `confidence_change`, `direction_reversal`, `comparator_count`
- **Primary Key:** `sensitivity_id` (unique)
- **Join Keys Present:** `approval_package_id`, `scenario_template_id`
- **Expected vs Actual:** All expected fields present. No missing fields.
- **Approved Substitutes:** None required.

### 2.9 scenario_diminishing_returns
- **Filename:** `analytical_scenario_diminishing_returns.csv`
- **Rows:** 357
- **Columns (6):**
  `diminishing_return_id`, `approval_package_id`, `scenario_template_id`, `diminishing_return_classification`, `diminishing_return_rationale`, `incremental_effect_ratios_json`
- **Primary Key:** `diminishing_return_id` (unique)
- **Join Keys Present:** `approval_package_id`, `scenario_template_id`
- **Expected vs Actual:** All expected fields present. No missing fields.
- **Approved Substitutes:** None required.

### 2.10 scenario_risk_displacement
- **Filename:** `analytical_scenario_risk_displacement.csv`
- **Rows:** 1,950
- **Columns (15):**
  `displacement_id`, `scenario_run_id`, `approval_package_id`, `episode_id`, `source_kpi_id`, `improved_kpi_id`, `potentially_affected_kpi_id`, `source_department_id`, `potentially_affected_department_id`, `displacement_type`, `displacement_classification`, `evidence_basis`, `confidence`, `required_monitoring`, `management_confirmation_required`
- **Primary Key:** `displacement_id` (unique)
- **Join Keys Present:** `scenario_run_id`, `approval_package_id`, `episode_id`
- **Expected vs Actual:** All expected fields present. No missing fields.
- **Approved Substitutes:** None required.

### 2.11 scenario_management_interpretation
- **Filename:** `analytical_scenario_management_interpretation.csv`
- **Rows:** 357
- **Columns (17):**
  `interpretation_id`, `approval_package_id`, `scenario_template_id`, `episode_id`, `scenario_family`, `comparator_summary`, `primary_kpi_effect`, `supporting_kpi_effects`, `adverse_effects`, `displacement_risk`, `assumption_drivers`, `management_validation_required`, `sensitivity_classification`, `diminishing_return_classification`, `trade_off_band`, `management_readiness`, `interpretation_text`
- **Primary Key:** `interpretation_id` (unique)
- **Join Keys Present:** `approval_package_id`, `episode_id`, `scenario_template_id`
- **Expected vs Actual:** All expected fields present. No missing fields.
- **Approved Substitutes:** None required.

### 2.12 scenario_evidence
- **Filename:** `analytical_scenario_evidence.csv`
- **Rows:** 14,616
- **Columns (9):**
  `evidence_id`, `scenario_run_id`, `evidence_type`, `source_type`, `source_id`, `source_file`, `link_type`, `recorded_at`, `metadata_json`
- **Primary Key:** `evidence_id` (unique)
- **Join Keys Present:** `scenario_run_id`
- **Expected vs Actual:** All expected fields present. No missing fields.
- **Approved Substitutes:** None required.

### 2.13 scenario_governance
- **Filename:** `analytical_scenario_governance.csv`
- **Rows:** 21,420
- **Columns (8):**
  `governance_id`, `scenario_run_id`, `rule_id`, `rule_name`, `rule_applied`, `rule_outcome`, `message`, `applied_at`
- **Primary Key:** `governance_id` (**NOT unique** — duplicates exist)
- **Join Keys Present:** `scenario_run_id`
- **Expected vs Actual:** All expected fields present. No missing fields.
- **Approved Substitutes:** None required.
- **Note:** PK non-uniqueness is expected for governance logs (multiple rules per run).

### 2.14 scenario_lineage
- **Filename:** `analytical_scenario_lineage.csv`
- **Rows:** 14,616
- **Columns (7):**
  `lineage_id`, `scenario_run_id`, `source_type`, `source_id`, `source_file`, `link_type`, `recorded_at`
- **Primary Key:** `lineage_id` (unique)
- **Join Keys Present:** `scenario_run_id`
- **Expected vs Actual:** All expected fields present. No missing fields.
- **Approved Substitutes:** None required.

### 2.15 scenario_non_comparable_register
- **Filename:** `analytical_scenario_non_comparable_register.csv`
- **Rows:** 1,283
- **Columns (44):** Same schema as `scenario_runs`
- **Primary Key:** `scenario_run_id` (unique)
- **Join Keys Present:** `scenario_run_id`, `approval_package_id`, `episode_id`, `scenario_template_id`, `comparator_id`, `baseline_id`
- **Expected vs Actual:** All expected fields present. No missing fields.
- **Approved Substitutes:** None required.

### 2.16 scenario_kpi_impacts
- **Filename:** `analytical_scenario_kpi_impacts.csv`
- **Rows:** 2,711
- **Columns (9):**
  `scenario_run_id`, `primary_kpi_id`, `baseline_value`, `scenario_value`, `absolute_change`, `percentage_change`, `direction_of_change`, `affected_supporting_kpis`, `supporting_kpi_result_status`
- **Primary Key:** `scenario_run_id` (unique)
- **Join Keys Present:** `scenario_run_id`
- **Expected vs Actual:** All expected fields present. No missing fields.
- **Approved Substitutes:** None required.

### 2.17 scenario_primary_impacts
- **Filename:** `analytical_scenario_primary_impacts.csv`
- **Rows:** 1,428
- **Columns (16):**
  `primary_impact_id`, `scenario_run_id`, `approval_package_id`, `episode_id`, `primary_kpi_id`, `baseline_primary_kpi_value`, `scenario_primary_kpi_value`, `absolute_change`, `percentage_change`, `direction_of_change`, `comparator_type`, `scenario_family`, `final_scenario_confidence`, `impact_classification`, `effect_direction`, `evidence_language`
- **Primary Key:** `primary_impact_id` (unique)
- **Join Keys Present:** `scenario_run_id`, `approval_package_id`, `episode_id`
- **Expected vs Actual:** All expected fields present. No missing fields.
- **Approved Substitutes:** None required.

### 2.18 scenario_supporting_kpi_impacts
- **Filename:** `analytical_scenario_supporting_kpi_impacts.csv`
- **Rows:** 1,428
- **Columns (9):**
  `supporting_impact_id`, `scenario_run_id`, `approval_package_id`, `episode_id`, `supporting_kpi_status`, `expected_direction_if_any`, `evidence_basis`, `uncertainty`, `monitoring_requirement`
- **Primary Key:** `supporting_impact_id` (unique)
- **Join Keys Present:** `scenario_run_id`, `approval_package_id`, `episode_id`
- **Expected vs Actual:** All expected fields present. No missing fields.
- **Approved Substitutes:** None required.

### 2.19 scenario_tradeoff_profiles
- **Filename:** `analytical_scenario_tradeoff_profiles.csv`
- **Rows:** 1,428
- **Columns (9):**
  `profile_id`, `scenario_run_id`, `approval_package_id`, `episode_id`, `analytical_trade_off_index`, `index_components_json`, `index_weights_json`, `trade_off_band`, `trade_off_rationale`
- **Primary Key:** `profile_id` (unique)
- **Join Keys Present:** `scenario_run_id`, `approval_package_id`, `episode_id`
- **Expected vs Actual:** All expected fields present. No missing fields.
- **Approved Substitutes:** None required.

### 2.20 scenario_tradeoff_evidence
- **Filename:** `analytical_scenario_tradeoff_evidence.csv`
- **Rows:** 1,428
- **Columns (8):**
  `evidence_id`, `scenario_run_id`, `evidence_type`, `source_type`, `source_id`, `source_file`, `link_type`, `recorded_at`
- **Primary Key:** `evidence_id` (unique)
- **Join Keys Present:** `scenario_run_id`
- **Expected vs Actual:** All expected fields present. No missing fields.
- **Approved Substitutes:** None required.

### 2.21 scenario_tradeoff_lineage
- **Filename:** `analytical_scenario_tradeoff_lineage.csv`
- **Rows:** 1,428
- **Columns (7):**
  `lineage_id`, `scenario_run_id`, `source_type`, `source_id`, `source_file`, `link_type`, `recorded_at`
- **Primary Key:** `lineage_id` (unique)
- **Join Keys Present:** `scenario_run_id`
- **Expected vs Actual:** All expected fields present. No missing fields.
- **Approved Substitutes:** None required.

---

## 3. Join Key Governance Matrix

| Join Key | Files Present In | Files Missing From |
|----------|-----------------|-------------------|
| `scenario_run_id` | scenario_runs, scenario_confidence, scenario_effect_classification, scenario_risk_displacement, scenario_evidence, scenario_governance, scenario_lineage, scenario_kpi_impacts, scenario_primary_impacts, scenario_supporting_kpi_impacts, scenario_tradeoff_profiles, scenario_tradeoff_evidence, scenario_tradeoff_lineage, scenario_non_comparable_register | scenario_baselines, scenario_assumption_validation, scenario_comparator_analysis, scenario_dominance, scenario_sensitivity, scenario_diminishing_returns, scenario_management_interpretation |
| `approval_package_id` | scenario_runs, scenario_baselines, scenario_comparator_analysis, scenario_effect_classification, scenario_dominance, scenario_sensitivity, scenario_diminishing_returns, scenario_risk_displacement, scenario_management_interpretation, scenario_primary_impacts, scenario_supporting_kpi_impacts, scenario_tradeoff_profiles, scenario_non_comparable_register | scenario_assumption_validation, scenario_confidence, scenario_evidence, scenario_governance, scenario_lineage, scenario_kpi_impacts, scenario_tradeoff_evidence, scenario_tradeoff_lineage |
| `episode_id` | scenario_runs, scenario_baselines, scenario_comparator_analysis, scenario_effect_classification, scenario_risk_displacement, scenario_management_interpretation, scenario_primary_impacts, scenario_supporting_kpi_impacts, scenario_tradeoff_profiles, scenario_non_comparable_register | scenario_assumption_validation, scenario_confidence, scenario_dominance, scenario_sensitivity, scenario_diminishing_returns, scenario_evidence, scenario_governance, scenario_lineage, scenario_kpi_impacts, scenario_tradeoff_evidence, scenario_tradeoff_lineage |
| `scenario_template_id` | scenario_runs, scenario_baselines, scenario_comparator_analysis, scenario_dominance, scenario_sensitivity, scenario_diminishing_returns, scenario_management_interpretation, scenario_non_comparable_register | scenario_assumption_validation, scenario_confidence, scenario_effect_classification, scenario_risk_displacement, scenario_evidence, scenario_governance, scenario_lineage, scenario_kpi_impacts, scenario_primary_impacts, scenario_supporting_kpi_impacts, scenario_tradeoff_profiles, scenario_tradeoff_evidence, scenario_tradeoff_lineage |
| `comparator_id` | scenario_runs, scenario_non_comparable_register | (all others) |
| `baseline_id` | scenario_runs, scenario_baselines, scenario_non_comparable_register | (all others) |

---

## 4. Confidence Field Mapping

| Source File | Confidence Column | Data Type | Sample Values |
|-------------|-------------------|-----------|---------------|
| scenario_runs | `final_scenario_confidence` | string | Insufficient Evidence, Low, Moderate |
| scenario_confidence | `confidence_base` | float | 0.0, 50.0, 100.0 |
| scenario_confidence | `confidence_score_internal` | string | Insufficient Evidence, Low, Moderate |
| scenario_confidence | `final_scenario_confidence` | string | Insufficient Evidence, Low, Moderate |
| scenario_effect_classification | `confidence` | string | Low, Moderate |
| scenario_risk_displacement | `confidence` | string | Low, Moderate |
| scenario_primary_impacts | `final_scenario_confidence` | string | Low, Moderate |
| scenario_non_comparable_register | `final_scenario_confidence` | string | Insufficient Evidence |

---

## 5. Causality Field Mapping

| Source File | Causality Column | Data Type | Sample Values |
|-------------|------------------|-----------|---------------|
| scenario_runs | `causality_status` | string | Not Confirmed |
| scenario_non_comparable_register | `causality_status` | string | Not Confirmed |

**Note:** All comparable and non-comparable scenarios currently carry `causality_status = "Not Confirmed"`. No confirmed causal links exist in the frozen dataset.

---

## 6. Baseline Status Mapping

| Source File | Baseline Status Column | Sample Values |
|-------------|------------------------|---------------|
| scenario_runs | `baseline_status` | Available with Conditions, Blocked, Available |
| scenario_baselines | `baseline_status` | Available with Conditions, Blocked, Available |
| scenario_non_comparable_register | `baseline_status` | Available with Conditions, Blocked, Available |

---

## 7. Comparator Status Mapping

| Source File | Comparator Column | Sample Values |
|-------------|-------------------|---------------|
| scenario_runs | `comparator_id` | COMP-BASE-001, COMP-CONS-001, COMP-EXP-001, COMP-HIGH-001, -BLOCKED, -MON |
| scenario_runs | `comparator_type` | Baseline, Conservative, Expected, Higher Intensity |
| scenario_runs | `comparator_config_version` | 2C-2B-1.0 |
| scenario_non_comparable_register | `comparator_id` | -BLOCKED, -MON |
| scenario_non_comparable_register | `comparator_type` | Baseline |

---

## 8. Non-Comparable Register Structure

- **Filename:** `analytical_scenario_non_comparable_register.csv`
- **Rows:** 1,283
- **Schema:** Identical to `scenario_runs` (44 columns)
- **Key Difference:** These are scenarios that failed comparability criteria in Step 2C-2C. They are excluded from Step 2C-2D downstream analysis but retained for audit.
- **Comparator Profile:** Only Baseline comparators (`-BLOCKED`, `-MON`) appear; no Conservative/Expected/Higher Intensity comparators.
- **Confidence Profile:** All entries have `final_scenario_confidence = "Insufficient Evidence"`.
- **Causality Profile:** All entries have `causality_status = "Not Confirmed"`.

---

## 9. Missing Fields and Approved Substitutes

| File | Expected Field | Status | Approved Substitute / Handling |
|------|---------------|--------|-------------------------------|
| scenario_assumption_validation | `scenario_run_id` | **Missing** | Engine will validate assumptions globally; no per-scenario join possible. |
| scenario_assumption_validation | `approval_package_id` | **Missing** | Same as above. |
| scenario_comparator_analysis | `scenario_run_id` (single) | **Missing** | Uses `scenario_run_id_a` and `scenario_run_id_b` for pairwise joins. |
| scenario_dominance | `scenario_run_id` (single) | **Missing** | Uses `scenario_run_id_a` and `scenario_run_id_b` for pairwise joins. |
| scenario_governance | Unique `governance_id` | **Not unique** | Expected behavior; treat as event log, not entity table. |

---

## 10. Critical Data Quality Findings

1. **Orphan Assumption Validation Table:** `scenario_assumption_validation` has no join keys to `scenario_run_id` or `approval_package_id`. This prevents per-scenario assumption challenge unless an external bridge table is introduced. The Step 2C-2E engine will flag this as a schema limitation.

2. **Uniform Causality:** 100% of scenarios (comparable and non-comparable) have `causality_status = "Not Confirmed"`. The causality challenge engine will flag every scenario accordingly.

3. **Governance ID Duplicates:** `scenario_governance` contains duplicate `governance_id` values. This is expected for a rule-application log but must be handled with aggregation rather than direct joins.

4. **Non-Comparable Baseline-Only:** The non-comparable register contains only Baseline comparator types, confirming that comparability failure occurs before comparator expansion.

---

## 11. File Provenance

All files listed in this inventory were produced by:
- **Step 2C-2C:** Scenario Generation and Confidence Scoring (frozen at 2026-07-28 19:14)
- **Step 2C-2D:** Scenario Effect Classification, Comparator Analysis, Dominance, Sensitivity, Diminishing Returns, Risk Displacement, Management Interpretation, and Trade-off Profiling (frozen at 2026-07-28 19:50)

No Step 2C-2E files are included in this inventory.

---

**End of Inventory**
