# Phase 2C-3 Uncertainty Schema Contract Inventory

**Date:** 2026-07-29
**Scope:** Schema review of cost-component, driver-mapping, assumption-range, and uncertainty-engine contracts for the focused uncertainty correction.

---

## 1. Files Reviewed

| File | Role | Rows | Key Purpose |
|------|------|------|-------------|
| `outputs/financial_impact/step_2c3_scenario_cost_components.csv` | Cost output | 8,019 | Per-component calculated costs |
| `outputs/financial_impact/step_2c3_cost_driver_mapping.csv` | Mapping output | 8,019 | Links assumptions to cost drivers and financial inputs |
| `config/financial_assumption_range.csv` | Config | 15 | Governed low/central/high ranges per financial input |
| `src/financial_cost_engine.py` | Engine | — | Calculates cost components from driver mapping |
| `src/financial_uncertainty_engine.py` | Engine | — | Calculates uncertainty from cost components and ranges |
| `src/run_financial_impact_analysis_2c3.py` | Runner | — | Orchestrates full Phase 2C-3 pipeline |

---

## 2. Column Inventory

### 2.1 step_2c3_scenario_cost_components.csv

| Column | Type | Primary Key | Foreign Key | Source |
|--------|------|-------------|-------------|--------|
| scenario_run_id | string | Part of PK | → scenario_run_closure | Runner |
| approval_package_id | string | — | → management_package | Runner |
| scenario_family | string | — | — | Runner |
| comparator_type | string | — | — | Runner |
| cost_component_name | string | Part of PK | — | Runner |
| formula_expression | string | — | — | Runner |
| assumption_name | string | — | — | Runner |
| assumption_value | float | — | — | Runner |
| rate_value | float | — | — | Runner |
| rate_available | bool | — | — | Runner |
| component_cost | float | — | — | Runner |
| currency | string | — | — | Runner |
| unit | string | — | — | Runner |
| one_time_or_recurring | string | — | — | Runner |
| direct_or_indirect | string | — | — | Runner |
| calculation_status | string | — | — | Runner |
| validation_status | string | — | — | Runner |
| assumption_flag | bool | — | — | Runner |
| missing_input_reason | string | — | — | Runner |
| evidence | string | — | — | Runner |
| lineage | string | — | — | Runner |

**Primary key:** (scenario_run_id, cost_component_name)
**Missing field:** `financial_input_id` — required for join to assumption_ranges.

### 2.2 step_2c3_cost_driver_mapping.csv

| Column | Type | Primary Key | Foreign Key | Source |
|--------|------|-------------|-------------|--------|
| scenario_run_id | string | Part of PK | — | financial_cost_driver_mapper.py |
| approval_package_id | string | — | — | financial_cost_driver_mapper.py |
| scenario_family | string | — | — | financial_cost_driver_mapper.py |
| comparator_type | string | — | — | financial_cost_driver_mapper.py |
| assumption_name | string | — | — | financial_cost_driver_mapper.py |
| assumption_value | float | — | — | financial_cost_driver_mapper.py |
| financial_input_id | string | — | → financial_assumption_range | financial_cost_driver_mapper.py |
| cost_component_name | string | Part of PK | — | financial_cost_driver_mapper.py |
| formula_expression | string | — | — | financial_cost_driver_mapper.py |
| rate_value | float | — | — | financial_cost_driver_mapper.py |
| rate_available | bool | — | — | financial_cost_driver_mapper.py |
| unit | string | — | — | financial_cost_driver_mapper.py |
| one_time_or_recurring | string | — | — | financial_cost_driver_mapper.py |
| direct_or_indirect | string | — | — | financial_cost_driver_mapper.py |
| mapping_id | string | — | — | financial_cost_driver_mapper.py |

**Primary key:** (scenario_run_id, cost_component_name)
**Available foreign key:** `financial_input_id` — present and populated for all 8,019 rows.

### 2.3 config/financial_assumption_range.csv

| Column | Type | Primary Key | Foreign Key | Source |
|--------|------|-------------|-------------|--------|
| range_id | string | PK | — | Manual config |
| financial_input_id | string | — | → financial_input_definition | Manual config |
| allowed_minimum | float | — | — | Manual config |
| allowed_maximum | float | — | — | Manual config |
| default_central | float | — | — | Manual config |
| default_low | float | — | — | Manual config |
| default_high | float | — | — | Manual config |
| unit | string | — | — | Manual config |
| currency_code | string | — | — | Manual config |
| configuration_version | string | — | — | Manual config |
| approval_status | string | — | — | Manual config |
| governance_note | string | — | — | Manual config |

**Primary key:** range_id
**Join key:** financial_input_id
**Note:** All 15 rows have `approval_status = "Draft Analytical Configuration"`.

---

## 3. Current Join Path (Defective)

```
financial_uncertainty_engine.calculate_uncertainty()
  ├── cost_components (8,019 rows)
  │     └── NO financial_input_id column
  ├── assumption_ranges (15 rows)
        └── keyed by financial_input_id

Attempted join: cost_components.financial_input_id → assumption_ranges.financial_input_id
Result: EMPTY — financial_input_id is absent from cost_components.
```

**Defect classification:** Schema-contract gap — upstream key dropped during cost-component serialization.

---

## 4. Required Corrected Join Path

```
financial_uncertainty_engine.calculate_uncertainty()
  ├── cost_components (8,019 rows)
  │     └── PK: (scenario_run_id, cost_component_name)
  ├── driver_mapping (8,019 rows)
  │     └── PK: (scenario_run_id, cost_component_name)
  │     └── FK: financial_input_id (populated for all rows)
  ├── assumption_ranges (15 rows)
        └── keyed by financial_input_id

Corrected join:
  cost_components.[scenario_run_id, cost_component_name]
    → driver_mapping.[scenario_run_id, cost_component_name]
    → driver_mapping.financial_input_id
    → assumption_ranges.financial_input_id
```

**Join type:** LEFT (preserves all cost components, even if mapping is missing).
**Cardinality:** 1:1 between cost_components and driver_mapping on (scenario_run_id, cost_component_name).
**Validation:** No duplicate join keys in driver_mapping (confirmed: max duplicates = 1).

---

## 5. Missing Fields and Replacement Sources

| Missing Field in cost_components | Replacement Source | Replacement Module | Replacement Path |
|----------------------------------|--------------------|--------------------|------------------|
| `financial_input_id` | `driver_mapping.financial_input_id` | `financial_uncertainty_engine.py` | Enrich at runtime via merge on (scenario_run_id, cost_component_name) |
| `mapping_id` | `driver_mapping.mapping_id` | `financial_uncertainty_engine.py` | Available in same merge; retained for lineage |
| `rate_unit` (descriptive) | `driver_mapping.unit` | `financial_uncertainty_engine.py` | Used for unit-mismatch validation vs assumption_ranges.unit |

**Future-proofing:** `financial_cost_engine.py` has been updated to emit `financial_input_id` in cost-components output for subsequent pipeline runs.

---

## 6. Governed ID Hierarchy (Preferred Key Order)

| Priority | Key | Availability | Used? |
|----------|-----|--------------|-------|
| 1 | financial_input_id | Present in driver_mapping | **Yes** |
| 2 | financial_input_requirement_id | Not present in current outputs | No |
| 3 | financial_driver_id + unit + scenario_family | financial_input_id is sufficient | No |
| 4 | cost_driver_mapping_id | Present as mapping_id | Auxiliary lineage only |
| 5 | configuration_id | Not explicitly mapped | No |

**Decision:** Use `financial_input_id` (priority 1) as the governed join key. It is fully populated and maps 1:1 to assumption_ranges.

---

## 7. Preservation Requirements

The corrected relationship preserves:

| Field | Preserved? | Source |
|-------|-----------|--------|
| approval_package_id | Yes | cost_components |
| scenario_run_id | Yes | cost_components |
| comparator_id (comparator_type) | Yes | cost_components |
| financial_input_requirement_id | N/A — not in current schema | — |
| financial_input_id | Yes | driver_mapping → propagated |
| cost_component_id | N/A — not explicitly assigned | cost_component_name used |
| financial_driver | N/A — not explicitly assigned | financial_input_id used |
| formula_id | N/A — not explicitly assigned | formula_expression retained |
| assumption_range_id | Yes | assumption_ranges.range_id |
| evidence_id | Yes | Generated per record |
| lineage_id | Yes | Generated per record |

---

## 8. Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Cartesian explosion on merge | Very Low | Join keys are unique in driver_mapping |
| Fuzzy / label-only join | None | Governed IDs used exclusively |
| Many-to-many join | None | 1:1 cardinality confirmed |
| Unit mismatch false positive | Low | Currency-code compatibility check implemented |
| Zero-cost components misclassified | Low | Explicit "Ineligible — Not Applicable" classification for base_cost == 0 |

---

*End of Schema Contract Inventory*
