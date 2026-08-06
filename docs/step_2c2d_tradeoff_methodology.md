# Phase 2C-2D Trade-Off Analysis Methodology

## 1. Overview

This document describes the methodology for the Phase 2C-2D Multi-KPI Impact and Trade-Off Analysis layer. The purpose is to compare completed scenario results from Step 2C-2C and identify primary effects, supporting effects, benefits, adverse effects, risk displacement, and operational trade-offs without selecting a preferred scenario.

## 2. Analysis Population

### 2.1 Quantitatively Comparable Runs

Only scenario runs with execution statuses **Completed** or **Completed with Warnings** are quantitatively compared.

### 2.2 Non-Comparable Register

Records with the following statuses are retained in a separate non-comparable register:
- Blocked — Missing Baseline
- Blocked — Missing Assumption
- Blocked — Invalid Assumption
- Blocked — Unsupported Family
- Blocked — Governance Rule
- Monitoring Only
- Validation Required
- Not Selected

## 3. Supported Quantitative Families

- Staffing Coverage Adjustment
- Absenteeism Contingency
- Patient-Flow and Waiting-Time Adjustment
- Combined Workforce and Flow Intervention
- No-Action or Baseline Comparator

Excluded KPIs: kpi_003, kpi_005, kpi_006 (provisional only).

## 4. Primary KPI Impact Analysis

Impact bands are configuration-driven:

| Band | Threshold | Classification |
|------|-----------|----------------|
| Strong Improvement | >= 15% | Strong Directional Improvement |
| Moderate Improvement | 5% to <15% | Moderate Directional Improvement |
| Small Improvement | 1% to <5% | Small Directional Improvement |
| No Change | -1% to 1% | No Material Change |
| Small Adverse | -5% to -1% | Small Adverse Change |
| Moderate Adverse | -15% to -5% | Moderate Adverse Change |
| Strong Adverse | <= -15% | Strong Adverse Change |

All language uses cautious phrasing: "estimated directional improvement", "scenario-based difference", "analytical approximation".

## 5. Supporting KPI Impacts

| Status | Description |
|--------|-------------|
| Quantified | Governed numerical result from Step 2C-2C |
| Directional Only | Direction known but magnitude not quantified |
| Monitoring Only | Unsupported KPI; no quantitative modelling |
| Unsupported | kpi_003, kpi_005, kpi_006 |
| Unavailable | No supporting KPI data |

## 6. Effect Classification

Each effect is classified as:
- Benefit
- Adverse Effect
- Neutral
- Uncertain
- Not Quantified

Benefits and adverse effects are stored in separate records. Uncertain effects are not merged into benefits.

## 7. Risk Displacement Analysis

Displacement classifications:
- No Displacement Identified
- Possible Within-Department Displacement
- Possible Cross-Department Displacement
- Possible Cross-KPI Displacement
- Material Displacement Risk
- Insufficient Evidence

All displacement claims are qualified with "possible" unless directly observed.

## 8. Comparator Trade-Off Analysis

Pairwise comparisons:
- Conservative versus Baseline
- Expected versus Conservative
- Higher Intensity versus Expected
- Expected versus Baseline
- Higher Intensity versus Baseline

Relationship classifications:
- Incremental Benefit with Limited Additional Risk
- Incremental Benefit with Additional Trade-Off
- Diminishing Improvement
- No Material Incremental Benefit
- Higher Risk without Clear Additional Benefit
- Incomparable
- Insufficient Evidence

## 9. Diminishing-Return Analysis

Incremental effect ratio = change in KPI effect / change in intervention intensity.

Classifications:
- Proportionate
- Diminishing
- Flat
- Adverse Reversal
- Not Assessable

## 10. Scenario Dominance Analysis

A scenario is analytically dominant only when it has:
- Equal or better primary KPI impact
- No worse quantified supporting KPI impact
- Equal or higher confidence
- No greater contradiction severity
- No greater material displacement risk
- No greater governance burden
- Equal or lower assumption intensity

Classifications:
- Dominates
- Weakly Dominates
- Non-Dominated
- Dominated
- Incomparable

This is analytical dominance, not a management recommendation.

## 11. Multi-Criteria Trade-Off Profile

Analytical Trade-Off Index (transparent, not a black box):

| Criterion | Weight |
|-----------|--------|
| Primary KPI Impact | 0.20 |
| Supporting KPI Impact | 0.10 |
| Confidence | 0.15 |
| Contradiction | 0.10 |
| Baseline Completeness | 0.08 |
| Assumption Extremity | 0.07 |
| Displacement Risk | 0.08 |

Trade-off bands:
- Favourable but Conditional (>= 70)
- Balanced Trade-Off (50-69)
- Mixed Trade-Off (30-49)
- Unfavourable Trade-Off (< 30)

## 12. Confidence and Governance

- causality_status = "Not Confirmed" (fixed)
- No High confidence permitted
- Material contradiction reduces confidence
- Major contradiction blocks comparison
- Provisional KPIs (kpi_003, kpi_005) preserve warnings

## 13. No Financial Calculations

The engine does not calculate cost, revenue, budget, ROI, or NPV.

## 14. Output Files

The engine produces 18 output files:
1. analytical_scenario_primary_impacts.csv
2. analytical_scenario_supporting_kpi_impacts.csv
3. analytical_scenario_effect_classification.csv
4. analytical_scenario_tradeoffs.csv
5. analytical_scenario_risk_displacement.csv
6. analytical_scenario_comparator_analysis.csv
7. analytical_scenario_diminishing_returns.csv
8. analytical_scenario_dominance.csv
9. analytical_scenario_sensitivity.csv
10. analytical_scenario_tradeoff_profiles.csv
11. analytical_scenario_management_interpretation.csv
12. analytical_scenario_tradeoff_evidence.csv
13. analytical_scenario_tradeoff_lineage.csv
14. analytical_scenario_tradeoff_governance.csv
15. analytical_scenario_tradeoff_issues.csv
16. analytical_scenario_non_comparable_register.csv
17. step_2c2d_run_manifest.json
18. step_2c2d_execution_summary.csv
