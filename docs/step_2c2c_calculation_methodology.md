# Phase 2C-2C Calculation Methodology

## 1. Overview

This document describes the calculation methodology for the Phase 2C-2C Baseline and Intervention Calculation Engine. The engine constructs immutable baselines from observed analytical data and calculates scenario outcomes for three supported intervention families:

- Staffing Coverage Adjustment
- Absenteeism Contingency
- Patient-Flow and Waiting-Time Adjustment

## 2. Baseline Construction

### 2.1 Data Sources

Baselines are constructed from:
- `episode_register.csv`: Episode metadata and date ranges
- `six_kpi_daily.csv`: Daily KPI observations
- `package_scenario_mapping.csv`: Package-to-template mappings

### 2.2 Episode Date Range Filtering

For each package-scenario mapping, the engine:
1. Looks up the episode in the episode register
2. Extracts `episode_start_date` and `episode_end_date`
3. Filters `six_kpi_daily` to records within `[start_date, end_date]`
4. Computes mean, median, and standard deviation per KPI

### 2.3 Baseline Status Assignment

| Condition | Status |
|-----------|--------|
| All required KPIs present with ≥30 days data | Available |
| Some KPIs missing or <30 days data | Available with Conditions |
| Episode not found in register | Missing |
| Dominant KPI is unsupported (kpi_003, kpi_005, kpi_006) | Missing |

### 2.4 Derived KPIs

- **kpi_004 (Arrivals per Capacity)**: `numerator / denominator` from six_kpi_daily
- **kpi_005 and kpi_006**: Flagged as provisional; preserved in baseline but excluded from quantitative scenarios

## 3. Comparator Types

Four comparator types are supported:

| Comparator | Purpose |
|-----------|---------|
| Baseline | No-action reference point |
| Conservative | Modest intervention assumptions |
| Expected | Standard intervention assumptions |
| Higher Intensity | Aggressive intervention assumptions |

Comparator types are normalised via `parse_comparator_type()` to handle spelling variations (e.g., "Higher-Intensity" → "Higher Intensity").

## 4. Scenario Calculation Rules

### 4.1 Staffing Coverage Adjustment

**Inputs:**
- `additional_staff_count`: FTE added
- `temporary_staff_count`: Temporary FTE
- `staff_reassignment_count`: Reassigned FTE
- `uncovered_shift_reduction_pct`: Reduction in uncovered shifts

**Calculation:**
- Effective staff increase = `additional_staff_count + temporary_staff_count + staff_reassignment_count`
- Coverage improvement = `effective_staff_increase / baseline_staff_count * 100`
- Uncovered shift reduction applied as percentage point change

### 4.2 Absenteeism Contingency

**Inputs:**
- `assumed_absenteeism_reduction_pct`: Target reduction in absenteeism rate
- `replacement_coverage_pct`: Percentage of absent shifts covered

**Calculation:**
- New absenteeism rate = `baseline_rate * (1 - reduction_pct / 100)`
- Effective coverage = `new_rate * (1 - replacement_coverage_pct / 100)`

### 4.3 Patient-Flow and Waiting-Time Adjustment

**Inputs:**
- `arrival_change_pct`: Change in patient arrivals
- `service_capacity_change_pct`: Change in service capacity
- `throughput_change_pct`: Change in throughput
- `routing_efficiency_change_pct`: Change in routing efficiency

**Calculation:**
- New wait time = `baseline_wait * (1 + arrival_change_pct/100) / (1 + capacity_change_pct/100)`
- Throughput and routing efficiency applied as multiplicative factors

### 4.4 Combined Workforce and Flow Intervention

Combines staffing and flow assumptions with an interaction adjustment factor to avoid double-counting benefits.

## 5. Confidence Calculation

Confidence is calculated per scenario using:

1. **Base confidence**: Derived from baseline data completeness (0–100)
2. **Adjustments:**
   - `-20` if provisional KPI involved
   - `-15` if partial flow coverage
   - `-10` if combined scenario penalty
   - `-25` if material contradiction
   - `-15` if assumption warnings
3. **Floor**: 0 (never negative)
4. **Ceiling**: Never High for provisional or contradictory scenarios

| Score Range | Confidence Level |
|-------------|------------------|
| 70–100 | Moderate (capped at Moderate if provisional) |
| 40–69 | Low |
| 0–39 | Insufficient Evidence |

## 6. Governance Rules

1. **Material contradiction** → reduces confidence by 25 points
2. **Major contradiction** → blocks execution entirely
3. **Provisional KPIs** (kpi_003, kpi_005) → preserve warnings, cap confidence at Moderate
4. **No High confidence** allowed for any scenario with provisional or contradictory baselines
5. **Causality status** fixed to "Not Confirmed" for all scenarios

## 7. Output Files

The engine produces 12 output files:

1. `analytical_scenario_baselines.csv` — All constructed baselines
2. `analytical_scenario_runs.csv` — All scenario execution results
3. `analytical_scenario_kpi_impacts.csv` — KPI-level impact summaries
4. `analytical_scenario_assumption_validation.csv` — Assumption validation records
5. `analytical_scenario_confidence.csv` — Confidence scores and rationale
6. `analytical_scenario_non_quantitative_register.csv` — Monitoring-only and blocked records
7. `analytical_scenario_evidence.csv` — Evidence linkage records
8. `analytical_scenario_lineage.csv` — Data lineage records
9. `analytical_scenario_governance.csv` — Governance check records
10. `analytical_scenario_issues.csv` — Issue records (empty if no issues)
11. `step_2c2c_run_manifest.json` — Run manifest with timing metrics
12. `step_2c2c_execution_summary.csv` — Execution summary

## 8. Performance Optimisations

- Baseline lookup dictionary pre-built before scenario loops
- Confidence rationale uses cached baseline references (no rebuild)
- All outputs written in batch after calculations complete
- Single-instance execution lock prevents duplicate runs
- Progress logging for each output file with row counts and timing

## 9. No Financial Calculations

As specified, the engine does **not** calculate:
- Cost estimates
- Revenue impact
- Budget implications
- ROI or NPV

All results are operational metrics only.
