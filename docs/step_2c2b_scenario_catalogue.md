# Step 2C-2B Scenario Catalogue

**Date:** 2026-07-28  
**Status:** GOVERNED CATALOGUE COMPLETE

---

## 1. Scenario Templates

### 1.1 SCEN-STAFF-001 — Temporary Staffing Coverage

| Attribute | Value |
|-----------|-------|
| **Family** | Staffing Coverage Adjustment |
| **Dominant KPI** | kpi_001 Staffing Level |
| **Status** | Supported |
| **Mode** | Single Intervention |
| **Quantitative** | Yes |
| **Baseline required** | Yes |
| **Comparator required** | Yes |
| **Confidence rule** | RULE-BASELINE-HIGH |
| **Contradiction rule** | RULE-CONTRA-MATERIAL-PENALTY |
| **Provisional rule** | RULE-PROV-NONE |
| **Eligible packages** | 174 Required (kpi_001) |

**Intervention dimensions:**
- Additional covered shifts
- Temporary staff deployment
- Internal staff reassignment
- Reduction in uncovered shifts
- Change in effective staffing coverage

**Assumption set:** ASSUM-STAFF-001 (11 assumptions)

**Comparators:**
- COMP-BASE-001: No-Action Baseline
- COMP-CONS-001: Conservative Staffing Increase
- COMP-EXP-001: Expected Staffing Increase
- COMP-HIGH-001: Higher-Intensity Staffing Increase

---

### 1.2 SCEN-ABS-001 — Absenteeism Contingency Response

| Attribute | Value |
|-----------|-------|
| **Family** | Absenteeism Contingency |
| **Dominant KPI** | kpi_002 Staff Absenteeism Rate |
| **Status** | Supported |
| **Mode** | Single Intervention |
| **Quantitative** | Yes |
| **Baseline required** | Yes |
| **Comparator required** | Yes |
| **Confidence rule** | RULE-BASELINE-HIGH |
| **Contradiction rule** | RULE-CONTRA-MATERIAL-PENALTY |
| **Provisional rule** | RULE-PROV-NONE |
| **Eligible packages** | 165 Required (kpi_002) |

**Intervention dimensions:**
- Assumed reduction in absenteeism
- Contingency roster activation
- Temporary replacement coverage
- Attendance-event recovery
- Reduction in uncovered shifts caused by absence

**Assumption set:** ASSUM-ABS-001 (6 assumptions)

**Comparators:**
- COMP-BASE-002: No-Action Baseline
- COMP-CONS-002: Conservative Absenteeism Reduction
- COMP-EXP-002: Expected Absenteeism Reduction
- COMP-HIGH-002: Higher-Intensity Absenteeism Reduction

---

### 1.3 SCEN-FLOW-001 — Patient Flow Capacity Adjustment

| Attribute | Value |
|-----------|-------|
| **Family** | Patient-Flow and Waiting-Time Adjustment |
| **Dominant KPI** | kpi_004 Average Patient Waiting Time |
| **Status** | Supported with Conditions |
| **Mode** | Single Intervention |
| **Quantitative** | Yes |
| **Baseline required** | Yes |
| **Comparator required** | Yes |
| **Confidence rule** | RULE-BASELINE-PARTIAL-MEDIUM |
| **Contradiction rule** | RULE-CONTRA-MATERIAL-PENALTY |
| **Provisional rule** | RULE-PROV-SUPPORTING-WARNING |
| **Eligible packages** | 7 Required + 11 Recommended (kpi_004) |

**Conditions:**
- kpi_004 baseline must have ≥ 60% data completeness per department.
- kpi_003 is provisional and unavailable; excluded from quantitative model.

**Intervention dimensions:**
- Temporary service-capacity increase
- Queue-throughput adjustment
- Arrival-distribution adjustment
- Routing or triage adjustment
- Temporary resource reallocation

**Assumption set:** ASSUM-FLOW-001 (9 assumptions)

**Comparators:**
- COMP-BASE-003: No-Action Baseline
- COMP-CONS-003: Conservative Flow Adjustment
- COMP-EXP-003: Expected Flow Adjustment
- COMP-HIGH-003: Higher-Intensity Flow Adjustment

---

### 1.4 SCEN-COMB-001 — Combined Staffing and Flow Intervention

| Attribute | Value |
|-----------|-------|
| **Family** | Combined Workforce and Flow Intervention |
| **Dominant KPI** | kpi_001, kpi_002, or kpi_004 |
| **Status** | Supported with Conditions |
| **Mode** | Combined Intervention |
| **Quantitative** | Yes |
| **Baseline required** | Yes |
| **Comparator required** | Yes |
| **Confidence rule** | RULE-COMBINED-PENALTY |
| **Contradiction rule** | RULE-CONTRA-MATERIAL-PENALTY |
| **Provisional rule** | RULE-PROV-SUPPORTING-WARNING |
| **Eligible packages** | Cross-domain packages only (none currently in dataset) |

**Conditions:**
- Cross-domain effects are association-based only (Step 2B-4).
- Fixed interaction adjustment factor (0.5) applied.
- Confidence reduced by 15 points automatically.

**Assumption set:** ASSUM-COMB-001 (4 assumptions)

**Comparators:**
- COMP-BASE-004: No-Action Baseline
- COMP-CONS-004: Conservative Combined Intervention
- COMP-EXP-004: Expected Combined Intervention
- COMP-HIGH-004: Higher-Intensity Combined Intervention

---

### 1.5 SCEN-BASE-001 — No-Action Baseline Comparator

| Attribute | Value |
|-----------|-------|
| **Family** | No-Action or Baseline Comparator |
| **Dominant KPI** | Any |
| **Status** | Supported |
| **Mode** | No-Action Comparator |
| **Quantitative** | Yes |
| **Baseline required** | Yes |
| **Comparator required** | No (is the comparator) |
| **Confidence rule** | RULE-BASELINE-HIGH |
| **Eligible packages** | All 346 Required + 11 Recommended |

**Required for every scenario-eligible package.**

**Assumption set:** ASSUM-BASE-001

**Comparators:**
- COMP-BASE-005: No-Action Baseline (self-reference)

---

### 1.6 SCEN-MON-001 — Operational Monitoring and Validation

| Attribute | Value |
|-----------|-------|
| **Family** | Monitoring-Only or Validation Scenario |
| **Dominant KPI** | Any |
| **Status** | Monitoring Only |
| **Mode** | Monitoring Only |
| **Quantitative** | No |
| **Baseline required** | Yes |
| **Comparator required** | No |
| **Confidence rule** | RULE-INSUFFICIENT |
| **Eligible packages** | All 646 packages (Required + Recommended + Not Required) |

**Use where package requires:**
- Data validation
- Operational confirmation
- Temporary monitoring
- Threshold review
- No direct intervention assumption

---

### 1.7 Unsupported Templates

| Template ID | Family | Dominant KPI | Status | Reason |
|-------------|--------|--------------|--------|--------|
| SCEN-BED-UNSUPPORTED | Bed-capacity adjustment | kpi_003 | Unsupported | No calculated baseline values |
| SCEN-COMP-UNSUPPORTED | Complaint-management intervention | kpi_005 | Unsupported | Zero-denominator baseline issues |
| SCEN-SAT-UNSUPPORTED | Patient-satisfaction intervention | kpi_006 | Unsupported | Partial Medium-confidence baseline |

These templates are **inactive** (`active_flag=False`). They exist for completeness and future unblocking.

---

## 2. Assumption Definitions Summary

### 2.1 ASSUM-STAFF-001 (Staffing Coverage Adjustment)

| ID | Name | Type | Required |
|----|------|------|----------|
| A001 | baseline_required_staff | Observed Baseline | Yes |
| A002 | baseline_available_staff | Observed Baseline | Yes |
| A003 | baseline_staffing_coverage_pct | Derived Parameter | Yes |
| A004 | additional_staff_count | User-Entered Intervention | Yes |
| A005 | additional_covered_shifts | User-Entered Intervention | No |
| A006 | staff_reassignment_count | User-Entered Intervention | No |
| A007 | temporary_staff_count | User-Entered Intervention | No |
| A008 | uncovered_shift_reduction_pct | User-Entered Intervention | No |
| A009 | intervention_duration_days | User-Entered Intervention | Yes |
| A010 | temporary_staff_productivity_ratio | User-Entered Intervention | Yes |

### 2.2 ASSUM-ABS-001 (Absenteeism Contingency)

| ID | Name | Type | Required |
|----|------|------|----------|
| A101 | baseline_absenteeism_rate | Observed Baseline | Yes |
| A102 | assumed_absenteeism_reduction_pct | User-Entered Intervention | Yes |
| A103 | replacement_coverage_pct | User-Entered Intervention | Yes |
| A104 | contingency_roster_activation_pct | User-Entered Intervention | No |
| A105 | absence_duration_reduction_days | User-Entered Intervention | No |
| A106 | intervention_duration_days | User-Entered Intervention | Yes |

### 2.3 ASSUM-FLOW-001 (Patient-Flow Adjustment)

| ID | Name | Type | Required |
|----|------|------|----------|
| A201 | baseline_avg_wait_min | Observed Baseline | Yes |
| A202 | baseline_arrivals | Observed Baseline | Yes |
| A203 | baseline_service_capacity | Observed Baseline | Yes |
| A204 | service_capacity_change_pct | User-Entered Intervention | No |
| A205 | throughput_change_pct | User-Entered Intervention | No |
| A206 | arrival_change_pct | User-Entered Intervention | No |
| A207 | routing_efficiency_change_pct | User-Entered Intervention | No |
| A208 | temporary_resource_change | User-Entered Intervention | No |
| A209 | intervention_duration_days | User-Entered Intervention | Yes |

### 2.4 ASSUM-COMB-001 (Combined Intervention)

| ID | Name | Type | Required |
|----|------|------|----------|
| A301 | workforce_assumption_set_id | Fixed Governance Parameter | Yes |
| A302 | flow_assumption_set_id | Fixed Governance Parameter | Yes |
| A303 | interaction_assumption | Fixed Governance Parameter | Yes |
| A304 | interaction_adjustment_factor | Fixed Governance Parameter | Yes |

### 2.5 ASSUM-GOV-001 (Governance)

| ID | Name | Type | Value |
|----|------|------|-------|
| G001 | contradiction_confidence_multiplier | Fixed Governance Parameter | 0.85 |
| G002 | provisional_confidence_multiplier | Fixed Governance Parameter | 0.75 |
| G003 | missing_data_confidence_multiplier | Fixed Governance Parameter | 0.80 |
| G004 | assumption_extremity_penalty | Fixed Governance Parameter | 5 points |
| G005 | combined_scenario_confidence_penalty | Fixed Governance Parameter | 15 points |

---

## 3. Comparator Definitions

Every quantitative scenario family has four comparators:

| Type | Intensity | Purpose |
|------|-----------|---------|
| **Baseline** | 0 | Reference condition (no intervention) |
| **Conservative** | 1 | Low-regret trial with modest assumptions |
| **Expected** | 2 | Plausible intervention aligned with package rationale |
| **Higher Intensity** | 3 | Stress-test or upper-bound exploration |

**No comparator is labelled Best Case or Guaranteed Outcome.**

---

## 4. Confidence Rules

| Rule | Factor | Condition | Effect |
|------|--------|-----------|--------|
| RULE-BASELINE-HIGH | Baseline | High-confidence calculated baseline | No reduction |
| RULE-BASELINE-PARTIAL-MEDIUM | Baseline | Partial Medium-confidence baseline | Moderate reduction (×0.85) |
| RULE-COMBINED-PENALTY | Complexity | Combined intervention | Moderate reduction (×0.80) |
| RULE-CONTRA-MINOR | Contradiction | Minor severity | Minor reduction (×0.95) |
| RULE-CONTRA-MATERIAL-PENALTY | Contradiction | Material severity | Material reduction (×0.80) |
| RULE-CONTRA-MAJOR-BLOCK | Contradiction | Major severity | Blocks execution |
| RULE-PROV-SUPPORTING-WARNING | Provisional | Provisional KPI as supporting | Minor reduction (×0.90) |
| RULE-PROV-BLOCKED | Provisional | Provisional KPI as primary | Blocks execution |
| RULE-ASSUM-EXTREME | Assumption | At soft warning limit | Minor reduction (×0.90) |
| RULE-MISSING-DATA | Data | Supporting data < 60% complete | Moderate reduction (×0.85) |
| RULE-INSUFFICIENT | Overall | Monitoring or unsupported | Insufficient Evidence |

**No High confidence is allowed in Phase 2C-2.** Maximum: Moderate.

---

## 5. Governance Rules

| Rule | Description | Enforcement |
|------|-------------|-------------|
| RULE-BASELINE-IMMUTABLE | Baselines must never be overwritten | Hard — reject run |
| RULE-NO-HIGH-CONFIDENCE | No High scenario confidence allowed | Hard — cap at Moderate |
| RULE-NO-AUTO-APPROVAL | No automatic management approval | Hard — block mechanism |
| RULE-NO-FINANCIAL-2C2 | No financial calculation in 2C-2 | Hard — reject output |
| RULE-PROV-PRESERVE-WARNING | Provisional KPI warning must persist | Hard — auto-flag |
| RULE-REPRODUCIBLE | Every run must have unique ID and metadata | Hard — reject if incomplete |

---

## 6. Package Mapping Summary

| Priority | Packages | Ready | Ready with Conditions | Monitoring Only | Unsupported |
|----------|----------|-------|----------------------|-----------------|-------------|
| Required | 346 | 685 | 7 | 346 | 0 |
| Recommended | 11 | 11 | 11 | 11 | 0 |
| Not Required | 289 | 0 | 0 | 289 | 280 |

*Note: Each package may map to multiple scenario templates, so row counts exceed package counts.*

---

## 7. Assumption Gaps

| ID | Family | Gap | Impact | Resolution |
|----|--------|-----|--------|------------|
| GAP-001 | Absenteeism | No dedicated absenteeism-intervention config | Moderate | Define in 2C-2B |
| GAP-002 | Absenteeism | Absence duration reduction not parameterised | Low | Add assumption |
| GAP-003 | Patient Flow | Service capacity baseline not consistently recorded | High | Derive or add to pipeline |
| GAP-004 | Patient Flow | No empirical anchor for routing efficiency change | Moderate | Conservative default |
| GAP-005 | Combined | Interaction factor is placeholder (0.5) | High | Retain as fixed governance |
| GAP-006 | Combined | No workforce-to-flow conversion ratio | High | Use 2B-4 association as bound |
| GAP-007 | All | No validated trend projection model | Moderate | Use historical average |
| GAP-008 | All | No seasonal decomposition | Low | Document as limitation |

---

## 8. Version

**Catalogue version:** v1.0  
**Active templates:** 6 (4 quantitative, 2 non-quantitative)  
**Inactive templates:** 3 (unsupported families)  
**Total templates:** 9
