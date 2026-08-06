# Step 2C-2B Assumption Configuration Reconciliation Report

**Date:** 2026-07-28  
**Status:** RECONCILED

---

## 1. Existing Configuration

### File: `config/scenario_assumption_config.csv`

| Attribute | Value |
|-----------|-------|
| **Rows** | 18 |
| **Created** | 2026-07-25 |
| **Version** | v1.0-draft |
| **Approval status** | Draft |
| **Validation status** | Configurable Placeholder |

### Existing Fields

| Field | Assessment |
|-------|------------|
| `scenario_assumption_id` | Unique identifier; reusable |
| `intervention_id` | Maps assumptions to intervention; reusable with mapping update |
| `assumption_code` | Short code (e.g., TEMP_COUNT); **reusable as assumption_name reference** |
| `assumption_name` | Human-readable name; reusable |
| `assumption_description` | Description; reusable with updates |
| `assumption_category` | Category (Resource Count, Service Duration, etc.); reusable |
| `unit` | Unit of measure; reusable |
| `data_type` | Integer, Decimal, Text; reusable |
| `default_value` | **All null** — requires population |
| `minimum_value` | **All null** — requires population |
| `maximum_value` | **All null** — requires population |
| `step_value` | **All null** — requires population |
| `editable_flag` | All `true`; reusable |
| `source_reference` | All null; requires population |
| `confidence_level` | All null; requires population |
| `stakeholder_validation_required` | All `false`; **needs review for user-adjustable assumptions** |
| `configuration_version` | v1.0-draft; requires upgrade |
| `effective_start_date` | 2026-07-25; reusable |
| `effective_end_date` | All null; reusable |
| `approval_status` | All Draft; requires upgrade |
| `validation_status` | All Configurable Placeholder; requires upgrade |
| `created_datetime` | 2026-07-25T00:00:00; reusable |
| `updated_datetime` | 2026-07-25T00:00:00; **requires update** |

### Existing Assumption Codes

| Code | Name | Family | Reusable? |
|------|------|--------|-----------|
| TEMP_COUNT | Temporary Staff Count | Staffing | Yes |
| TEMP_DURATION | Deployment Duration | Staffing | Yes |
| TEMP_PRODUCTIVITY | Productivity Factor | Staffing | Yes — renamed to `temporary_staff_productivity_ratio` in new definition |
| TEMP_DELAY | Implementation Delay | Staffing | Yes — retained but not yet in quantitative model |
| EXT_HOURS_COUNT | Additional Service Hours | Service extension | **Not used in current scenario families** |
| EXT_STAFF_REQ | Additional Staffing Requirement | Service extension | **Not used in current scenario families** |
| EXT_DURATION | Implementation Duration | Service extension | **Not used in current scenario families** |
| REDIR_PCT | Redirection Percentage | Patient flow | Yes |
| REDIR_CAPACITY | Receiving Service Capacity | Patient flow | Yes |
| RESCHED_COUNT | Rescheduled Admissions | Patient flow | Yes |
| RESCHED_BEDS | Released Bed Capacity | Patient flow | Yes |
| RESCHED_DURATION | Rescheduling Duration | Patient flow | Yes |
| CAP_RESTORED | Restored Capacity | Bed capacity | **Blocked — family unsupported** |
| CAP_RESTORE_DURATION | Restoration Duration | Bed capacity | **Blocked — family unsupported** |
| PEAK_STAFF | Additional Support Staff | Patient experience | **Blocked — family unsupported** |
| PEAK_CATEGORY | Affected Complaint Category | Patient experience | **Blocked — family unsupported** |
| PEAK_DURATION | Implementation Duration | Patient experience | **Blocked — family unsupported** |

---

## 2. New Configuration Files Created

Six new configuration files have been created for Step 2C-2B:

1. `config/scenario_catalogue.csv` — Scenario template definitions
2. `config/scenario_assumption_definition.csv` — Assumption definitions with types and governance rules
3. `config/scenario_assumption_range_config.csv` — Allowed ranges for user-adjustable assumptions
4. `config/scenario_comparator_config.csv` — Baseline, conservative, expected, and higher-intensity comparators
5. `config/scenario_confidence_rule_config.csv` — Confidence calculation rules
6. `config/scenario_governance_rule_config.csv` — Governance enforcement rules

---

## 3. Reconciliation Decisions

### 3.1 Retained: `config/scenario_assumption_config.csv`

**Decision:** Retain, do not deprecate.  
**Rationale:** The existing file contains institutional knowledge (assumption codes, descriptions, categories) that should not be lost. It can serve as a source of reference descriptions for assumption fields.

**Action required:**
- Populate `default_value`, `minimum_value`, `maximum_value`, and `step_value` from `scenario_assumption_range_config.csv`.
- Update `stakeholder_validation_required` to `true` for assumptions classified as "Draft Analytical Range".
- Upgrade `approval_status` from Draft to Pending Validation once ranges are stakeholder-approved.
- Update `configuration_version` to v2.0-reconciled.

### 3.2 Migrated: Assumption codes to new definition file

| Old Code | New Assumption ID | New Name | Status |
|----------|-------------------|----------|--------|
| TEMP_COUNT | A004 | additional_staff_count | Migrated |
| TEMP_DURATION | A009 | intervention_duration_days | Migrated |
| TEMP_PRODUCTIVITY | A010 | temporary_staff_productivity_ratio | Migrated |
| REDIR_PCT | A206 | arrival_change_pct | Partially migrated (concept similar) |
| REDIR_CAPACITY | A208 | temporary_resource_change | Partially migrated |
| RESCHED_COUNT | — | — | Not directly mapped; concept absorbed into flow assumptions |
| RESCHED_BEDS | — | — | Not directly mapped |

### 3.3 Blocked: Unused assumptions

Assumptions for `EXT_HOURS_COUNT`, `EXT_STAFF_REQ`, `EXT_DURATION`, `CAP_RESTORED`, `CAP_RESTORE_DURATION`, `PEAK_STAFF`, `PEAK_CATEGORY`, and `PEAK_DURATION` are **not used** in any supported scenario family. They remain in the existing config for future use but are not referenced by the new scenario catalogue.

### 3.4 New assumptions not in existing config

The following assumptions were newly defined in `scenario_assumption_definition.csv` and do not exist in the existing config:

- `baseline_required_staff` (A001)
- `baseline_available_staff` (A002)
- `baseline_staffing_coverage_pct` (A003)
- `additional_covered_shifts` (A005)
- `staff_reassignment_count` (A006)
- `uncovered_shift_reduction_pct` (A008)
- `baseline_absenteeism_rate` (A101)
- `assumed_absenteeism_reduction_pct` (A102)
- `replacement_coverage_pct` (A103)
- `contingency_roster_activation_pct` (A104)
- `absence_duration_reduction_days` (A105)
- `baseline_avg_wait_min` (A201)
- `baseline_arrivals` (A202)
- `baseline_service_capacity` (A203)
- `service_capacity_change_pct` (A204)
- `throughput_change_pct` (A205)
- `routing_efficiency_change_pct` (A207)
- All governance assumptions (G001–G005)

These will be added to `scenario_assumption_config.csv` during a future migration step if a single unified config is desired.

---

## 4. Recommended Future Action

| Priority | Action | Target Step |
|----------|--------|-------------|
| High | Populate missing default/min/max/step values in `scenario_assumption_config.csv` from `scenario_assumption_range_config.csv` | 2C-2C |
| Medium | Add new assumptions (A001–G005) to `scenario_assumption_config.csv` or formally deprecate it in favour of the new files | 2C-2C |
| Low | Remove blocked assumptions (EXT_*, CAP_*, PEAK_*) or mark them `active_flag=False` | 2C-2E |

---

## 5. Sign-Off

| Item | Status |
|------|--------|
| Existing config retained | Yes |
| New config files created | Yes (6 files) |
| Reconciliation documented | Yes |
| No silent overwrite | Confirmed |
