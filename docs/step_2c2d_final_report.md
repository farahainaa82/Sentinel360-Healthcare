# Phase 2C-2D Final Report — Multi-KPI Impact and Trade-Off Analysis

## 1. Project Context

**Phase**: 2C-2D  
**Objective**: Build a governed Multi-KPI Impact and Trade-Off Analysis layer that compares completed scenario results without selecting a preferred scenario.  
**Date**: 2026-07-28  
**Engine Version**: 2C-2D-1.0

## 2. Scope

### In Scope
- Primary KPI impact classification
- Supporting KPI impact assessment
- Benefit and adverse effect classification
- Risk displacement analysis
- Comparator trade-off analysis
- Diminishing-return assessment
- Scenario dominance analysis
- Multi-criteria trade-off profiles
- Sensitivity analysis
- Management interpretation generation
- Evidence linkage and lineage

### Out of Scope
- Financial impact calculations
- Preferred scenario selection
- Scenario approval or implementation
- Step 2C-2E Scenario Validation and Challenge
- Streamlit integration

## 3. Architecture

```
ScenarioTradeoffAnalysisRunner
├── ScenarioImpactAnalysisEngine      # Primary and supporting KPI classification
├── ScenarioDisplacementEngine        # Risk displacement detection
├── ScenarioDominanceEngine           # Analytical dominance evaluation
├── ScenarioSensitivityEngine         # Sensitivity across comparators
└── ScenarioTradeoffEngine            # Trade-offs, diminishing returns, profiles
```

## 4. Key Design Decisions

1. **No preferred scenario**: The engine never selects, recommends, or approves a scenario.
2. **Configuration-driven**: All impact bands, weights, and rules are loaded from CSV configs.
3. **Transparent scoring**: The Analytical Trade-Off Index shows all components and weights.
4. **Non-comparable register**: Blocked and monitoring-only records are preserved, not excluded.
5. **Cautious language**: All effects are described as "estimated", "possible", or "analytical approximation".

## 5. Execution Results

### 5.1 Scale
- **Scenario runs reviewed**: 2,711
- **Quantitatively comparable**: 1,428
- **Non-comparable**: 1,283
- **Approval packages reviewed**: 357
- **Episodes reviewed**: 357
- **Comparator pairs analysed**: 1,785
- **Dominance comparisons**: 2,142

### 5.2 Performance
- **Total execution time**: ~4 seconds
- **Input loading**: ~0.09 seconds
- **Trade-off calculations**: ~3.96 seconds
- **Output writing**: ~0.41 seconds

### 5.3 Quality
- **Zero financial columns**: Verified
- **Zero unsupported KPI quantitative impacts**: Verified
- **Zero High confidence results**: Verified
- **100% Not Confirmed causality**: Verified
- **No preferred scenario selected**: Verified

## 6. Files Produced

### Analytical Outputs (data/analytical/)
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

### Control Outputs (outputs/scenario_modelling/)
17. step_2c2d_run_manifest.json
18. step_2c2d_execution_summary.csv

### Documentation (docs/)
19. step_2c2d_tradeoff_methodology.md
20. step_2c2d_validation_report.md
21. step_2c2d_management_tradeoff_brief.md
22. step_2c2d_final_report.md
23. step_2c2d_upstream_immutability_report.md

## 7. Test Coverage

Nine focused tests verify:
- Primary impact classification
- Supporting KPI handling (unsupported and quantified)
- Displacement detection (baseline, staffing, absenteeism)
- Dominance rules (dominates, dominated, incomparable)
- Sensitivity analysis (stable, reversal, insufficient)
- Trade-off engine (pairwise, diminishing returns, profiles)
- Output integrity (files exist, no financial fields, non-comparable register)
- Governance (no High confidence, causality fixed, unsupported KPIs blocked)
- Evidence and lineage (records exist, match, no orphans)
- Comparator balance (no self-comparisons, expected pairs, diminishing returns)

All tests pass.

## 8. Sign-Off

**Phase 2C-2D is complete.**

- Engine implemented and validated
- All outputs produced and verified
- All tests passing
- Documentation complete
- Ready for Step 2C-2E

**Date**: 2026-07-28
