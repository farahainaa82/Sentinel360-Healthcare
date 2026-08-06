# Phase 2C-2C Final Report — Baseline and Intervention Calculation Engine

## 1. Project Context

**Phase**: 2C-2C  
**Objective**: Build a baseline and intervention calculation engine that constructs immutable baselines from observed analytical data and calculates scenario outcomes for healthcare workforce and patient-flow interventions.  
**Date**: 2026-07-28  
**Engine Version**: 2C-2C-1.0

## 2. Scope

### In Scope
- Baseline construction from episode registers and daily KPI data
- Scenario calculation for three supported families:
  - Staffing Coverage Adjustment
  - Absenteeism Contingency
  - Patient-Flow and Waiting-Time Adjustment
- Four comparator types: Baseline, Conservative, Expected, Higher Intensity
- Confidence scoring with governance-rule adjustments
- Evidence linkage and data lineage tracking
- Assumption validation and governance checking
- Output generation (10 analytical files + manifest + summary)

### Out of Scope
- Financial impact calculations (cost, revenue, budget)
- Step 2C-2D Multi-KPI Trade-Off Analysis
- Real-time streaming or incremental updates
- Machine learning or predictive modelling

## 3. Architecture

```
ScenarioModellingEngineRunner
├── ScenarioConfigLoader          # Loads all config CSVs
├── ScenarioBaselineEngine        # Builds baselines from observed data
├── ScenarioGovernanceValidator   # Checks governance rules
├── ScenarioConfidenceEngine      # Calculates confidence scores
├── ScenarioEvidenceEngine        # Creates evidence and lineage records
├── StaffingScenarioEngine        # Staffing family calculations
├── AbsenteeismScenarioEngine     # Absenteeism family calculations
├── PatientFlowScenarioEngine     # Patient-flow family calculations
└── CombinedScenarioEngine        # Combined family calculations
```

## 4. Key Design Decisions

1. **Immutable baselines**: Baselines are constructed once per run and never modified during scenario calculations.
2. **Lookup dictionary**: Baselines are stored in a dictionary keyed by `package_id|episode_id|template_id` for O(1) access.
3. **Shared comparator normalisation**: `parse_comparator_type()` centralises spelling variation handling.
4. **Batch output writing**: All outputs are collected in memory and written once at the end.
5. **Single-instance lock**: Prevents duplicate engine processes via a filesystem lock.
6. **No financial fields**: Explicitly excluded from all outputs to maintain operational focus.

## 5. Execution Results

### 5.1 Scale
- **Packages assessed**: 1,640
- **Baselines built**: 1,640
- **Scenario runs attempted**: 2,711
- **Scenario runs completed**: 1,428
- **Evidence records created**: 14,616
- **Governance records created**: 21,420

### 5.2 Performance
- **Total execution time**: ~22 seconds
- **Baseline construction**: ~17 seconds
- **Scenario calculations**: ~3 seconds
- **Output writing**: <1 second

### 5.3 Quality
- **Zero financial columns**: Verified
- **Zero unsupported KPI quantitative results**: Verified
- **Zero High confidence results**: Verified
- **100% Not Confirmed causality**: Verified
- **Balanced comparators**: 357 completed results per comparator type

## 6. Files Produced

### Analytical Outputs (data/analytical/)
1. `analytical_scenario_baselines.csv`
2. `analytical_scenario_runs.csv`
3. `analytical_scenario_kpi_impacts.csv`
4. `analytical_scenario_assumption_validation.csv`
5. `analytical_scenario_confidence.csv`
6. `analytical_scenario_non_quantitative_register.csv`
7. `analytical_scenario_evidence.csv`
8. `analytical_scenario_lineage.csv`
9. `analytical_scenario_governance.csv`
10. `analytical_scenario_issues.csv`

### Control Outputs (outputs/scenario_modelling/)
11. `step_2c2c_run_manifest.json`
12. `step_2c2c_execution_summary.csv`

### Documentation (docs/)
13. `step_2c2c_calculation_methodology.md`
14. `step_2c2c_validation_report.md`
15. `step_2c2c_final_report.md`

## 7. Test Coverage

Eight focused tests verify:
- Baseline lookup consistency
- Comparator type parsing
- Absence of financial fields
- Unsupported KPI blocking
- Confidence capping
- Causality fixation
- Comparator balance
- Manifest integrity

All tests pass.

## 8. Readiness for Next Phase

The engine is marked as **"Ready for Step 2C-2D Multi-KPI Impact and Trade-Off Analysis"**.

Prerequisites for 2C-2D:
- Combined scenario mappings (SCEN-COMB-001) need to be added to package mappings
- Multi-KPI trade-off logic needs to be implemented
- Financial calculations remain out of scope unless explicitly requested

## 9. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Large dataset causes slow baseline construction | Medium | Medium | Baseline lookup dictionary already optimises access; further optimisation would require caching |
| OneDrive file-lock contention | Low | High | Single-instance lock prevents concurrent writes; outputs written atomically |
| Unsupported KPIs accidentally included | Low | High | Test 2C-2C-04 blocks this; governance validator enforces at runtime |
| Duplicate engine processes | Low | Medium | Filesystem lock prevents this; tested in smoke test |

## 10. Sign-Off

**Phase 2C-2C is complete.**

- Engine implemented and validated
- All outputs produced and verified
- All tests passing
- Documentation complete
- Ready for Step 2C-2D

**Date**: 2026-07-28
