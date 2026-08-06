# Phase 2D-1 Integration Key Specification

**Date:** 2026-07-29

---

## 1. Governed Key Hierarchy

| Priority | Key | Availability | Used For |
|----------|-----|--------------|----------|
| 1 | approval_package_id | All package-level files | Primary integration key |
| 2 | episode_id | All package-level files | Secondary identity key |
| 3 | management_scenario_package_id | 311 packages | Scenario-to-financial bridge |
| 4 | scenario_run_id | 2,711 runs | Run-level aggregation |
| 5 | comparator_id | Comparator closure | Consistency validation |
| 6 | hospital_id / department_id | All packages | Operational grouping |
| 7 | dominant_kpi_id | All packages | KPI linking |

## 2. Key Validation Results

| Input File | Key Tested | Unique? | Note |
|------------|-----------|---------|------|
| package_closure | approval_package_id | Yes | Master list, 646 unique |
| management_scenario | approval_package_id | Yes | 311 unique |
| scenario_runs | approval_package_id | No (expected) | 2,711 runs across 646 packages |
| scenario_runs | scenario_run_id | Yes | 2,711 unique |
| comparator_closure | approval_package_id | Yes | 357 unique packages |
| deferred_non_ready | approval_package_id | Yes | 335 unique |
| financial_readiness | approval_package_id | Yes | 311 unique |
| financial_comparison | approval_package_id | Yes | 311 unique |
| financial_confidence | approval_package_id | No (expected) | 1,071 records across packages |
| approval_package | approval_package_id | Yes | 646 unique |

## 3. Join Path

```
package_closure.approval_package_id
  → management_scenario.approval_package_id (1:1, 311 matched)
  → approval_package.approval_package_id (1:1, 646 matched)
  → financial_readiness.approval_package_id (1:1, 311 matched)
  → financial_comparison.approval_package_id (1:1, 311 matched)
  → comparator_closure.approval_package_id (1:N, aggregated)
  → scenario_runs.approval_package_id (1:N, aggregated)
  → deferred_non_ready.approval_package_id (1:1, 335 matched)
```

## 4. Cartesian Prevention

- Merge size estimated before execution: 311 rows for package_closure × management_scenario
- Actual output: 646 rows (matches master list)
- No join produced more rows than the left table

---

*End of Integration Key Specification*
