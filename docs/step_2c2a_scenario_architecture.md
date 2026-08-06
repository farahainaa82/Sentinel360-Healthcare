# Step 2C-2A Scenario Architecture

**Date:** 2026-07-28  
**Phase:** Sentinel360 Healthcare — Phase 2C-2  
**Step:** 2C-2A Input and Architecture Review  
**Status:** COMPLETE

---

## 1. Supported Scenario Families

### 1.1 Supported Now

#### A. Staffing Coverage Adjustment
- **Rationale:** kpi_001 (Staffing Level) has complete, high-confidence daily data across all 8 departments. The workforce domain is well understood.
- **Intervention levers:** Temporary staff count, deployment duration, productivity factor, implementation delay.
- **Baseline:** `analytical_workforce_kpi_daily.csv` — 5,840 rows, all Calculated, High confidence.
- **Affected KPI:** kpi_001.
- **Supporting KPI:** kpi_002 (absenteeism may reduce if coverage improves, though causation not proven).
- **Output:** Estimated staffing level under intervention; comparison to threshold.

#### B. Absenteeism Contingency
- **Rationale:** kpi_002 (Staff Absenteeism Rate) has complete, high-confidence daily data.
- **Intervention levers:** Contingency coverage ratio, overtime pool size, cross-training availability.
- **Baseline:** `analytical_workforce_kpi_daily.csv` — 5,840 rows, all Calculated, High confidence.
- **Affected KPI:** kpi_002.
- **Supporting KPI:** kpi_001.
- **Output:** Estimated absenteeism rate under contingency protocols.

#### C. No-Action / Baseline Comparison
- **Rationale:** Requires only observed historical data; no intervention assumptions needed.
- **Baseline:** `analytical_six_kpi_daily.csv` — 17,520 integrated rows.
- **Affected KPI:** All six KPIs.
- **Output:** Trend-projected baseline with confidence intervals; scenario deltas computed against this.

### 1.2 Supported with Conditions

#### D. Patient-Flow / Waiting-Time Adjustment
- **Rationale:** kpi_004 (Unplanned Readmission Rate) has partial high-confidence data (2,190 of 2,920 rows). kpi_003 (Bed Occupancy) is largely unavailable.
- **Condition:** Scenario engine must handle missing baseline values gracefully (e.g., department-average imputation, or exclusion of low-data periods).
- **Intervention levers:** Patient redirection percentage, receiving service capacity, rescheduled admissions, released bed capacity.
- **Baseline:** `analytical_patient_flow_kpi_daily.csv` — mixed coverage.
- **Affected KPI:** kpi_004 (primary), kpi_003 (supporting, with strong data-quality warnings).
- **Output:** Estimated readmission rate and occupancy under flow adjustments.

#### E. Patient-Satisfaction Monitoring
- **Rationale:** kpi_006 (Patient Satisfaction Score) has partial medium-confidence data (1,347 of 2,920 rows Calculated). Rest is Unavailable or Insufficient Data.
- **Condition:** Must limit scenario population to departments and dates with valid baseline data; must flag medium-confidence outputs.
- **Intervention levers:** Additional communication support staff, peak-hour coverage, targeted complaint categories.
- **Baseline:** `analytical_patient_experience_kpi_daily.csv` — partial coverage.
- **Affected KPI:** kpi_006.
- **Supporting KPI:** kpi_005 (complaint rate, but largely uncomputable).
- **Output:** Estimated satisfaction score with medium-confidence governance flag.

#### F. Combined Workforce and Flow Intervention
- **Rationale:** Workforce data is solid; patient-flow data is partial. Step 2B-4 identified associations but not causation.
- **Condition:** Cross-domain interaction effects must be treated as **assumed, not proven**. The engine must apply plausibility bounds and flag assumptions.
- **Intervention levers:** Temporary staffing + patient redirection + elective rescheduling.
- **Baseline:** Multiple source files.
- **Affected KPI:** kpi_001, kpi_002, kpi_004.
- **Supporting KPI:** kpi_003, kpi_006.
- **Output:** Multi-KPI impact matrix with confidence degradation for cross-domain linkages.

### 1.3 Insufficient Inputs

#### G. Bed-Capacity Adjustment
- **Rationale:** kpi_003 (Bed Occupancy Rate) has **no calculated values** in the patient-flow file (all 2,920 rows marked Insufficient Data). Numerator and denominator are entirely missing.
- **Blocker:** Without baseline occupancy, any capacity-adjustment scenario is ungrounded.
- **Required to unblock:** Backfill bed-occupancy source data, or establish a proxy model from admissions and discharge data.

#### H. Complaint-Management Validation
- **Rationale:** kpi_005 (Patient Complaint Rate) has **1,875 Zero Denominator rows** and 598 Insufficient Data rows. The complaints-per-1000-encounters metric is uncomputable for the majority of records.
- **Blocker:** Without a valid baseline complaint rate, intervention effects cannot be estimated.
- **Required to unblock:** Correct source-data ingestion for encounter denominators, or switch to an alternative complaint metric.

### 1.4 Not Suitable for Quantitative Modelling

No families are categorically rejected; however, bed-capacity and complaint-management families are blocked by data gaps rather than conceptual unsuitability.

---

## 2. Required Model Inputs per Supported Family

### 2.1 Staffing Coverage Adjustment

| Input Type | Field | Source File | Status |
|------------|-------|-------------|--------|
| Observed data | `kpi_value` (kpi_001) | `analytical_workforce_kpi_daily.csv` | Available |
| Observed data | `numerator_value`, `denominator_value` | `analytical_workforce_kpi_daily.csv` | Available |
| Approved config | Threshold amber/red boundaries | `config/kpi_threshold_config.csv` | Available |
| User assumption | `TEMP_COUNT` (temporary staff) | `config/scenario_assumption_config.csv` | Placeholder only |
| User assumption | `TEMP_DURATION` (deployment days) | `config/scenario_assumption_config.csv` | Placeholder only |
| User assumption | `TEMP_PRODUCTIVITY` (ratio) | `config/scenario_assumption_config.csv` | Placeholder only |
| User assumption | `TEMP_DELAY` (decision-to-availability days) | `config/scenario_assumption_config.csv` | Placeholder only |
| Derived output | Estimated staffing level % | Scenario engine | Not yet built |
| Derived output | Threshold gap closure % | Scenario engine | Not yet built |

### 2.2 Absenteeism Contingency

| Input Type | Field | Source File | Status |
|------------|-------|-------------|--------|
| Observed data | `kpi_value` (kpi_002) | `analytical_workforce_kpi_daily.csv` | Available |
| Approved config | Threshold boundaries | `config/kpi_threshold_config.csv` | Available |
| User assumption | Contingency coverage ratio | To be defined in 2C-2B | Missing |
| User assumption | Overtime acceptance rate | To be defined in 2C-2B | Missing |
| Derived output | Estimated absenteeism % | Scenario engine | Not yet built |

### 2.3 Patient-Flow Adjustment

| Input Type | Field | Source File | Status |
|------------|-------|-------------|--------|
| Observed data | `kpi_value` (kpi_004) | `analytical_patient_flow_kpi_daily.csv` | Partial (75% coverage) |
| Observed data | `kpi_value` (kpi_003) | `analytical_patient_flow_kpi_daily.csv` | Unavailable |
| Approved config | Threshold boundaries | `config/kpi_threshold_config.csv` | Available |
| User assumption | `REDIR_PCT` | `config/scenario_assumption_config.csv` | Placeholder only |
| User assumption | `REDIR_CAPACITY` | `config/scenario_assumption_config.csv` | Placeholder only |
| User assumption | `RESCHED_COUNT` | `config/scenario_assumption_config.csv` | Placeholder only |
| User assumption | `RESCHED_BEDS` | `config/scenario_assumption_config.csv` | Placeholder only |
| Required assumption | Bed turnover rate | To be defined in 2C-2B | Missing |
| Known limitation | kpi_003 baseline missing | — | Blocks occupancy side of model |

### 2.4 Patient-Satisfaction Monitoring

| Input Type | Field | Source File | Status |
|------------|-------|-------------|--------|
| Observed data | `kpi_value` (kpi_006) | `analytical_patient_experience_kpi_daily.csv` | Partial (46% coverage, Medium confidence) |
| Approved config | Threshold boundaries | `config/kpi_threshold_config.csv` | Available |
| User assumption | `PEAK_STAFF` | `config/scenario_assumption_config.csv` | Placeholder only |
| User assumption | `PEAK_CATEGORY` | `config/scenario_assumption_config.csv` | Placeholder only |
| User assumption | `PEAK_DURATION` | `config/scenario_assumption_config.csv` | Placeholder only |
| Required assumption | Satisfaction elasticity to complaint reduction | To be defined in 2C-2B | Missing |
| Known limitation | kpi_005 baseline largely uncomputable | — | Limits supporting-evidence strength |

---

## 3. Scenario Governance Principles

The future scenario engine must adhere to the following principles. These are **architectural constraints**, not optional guidelines.

### 3.1 Estimation vs. Guarantee
1. **Scenario outputs are estimates, not forecasts guaranteed to occur.**
   - Every scenario output must carry an `estimate_confidence` field.
   - No output may be labelled "Predicted outcome" or "Guaranteed result".

### 3.2 Non-Causality Preservation
2. **Association does not prove causation.**
   - Cross-KPI effects must use language such as "Estimated association effect" or "Plausible impact based on observed correlation".
   - Step 2B-4 relationship strengths may inform bounds but must not be treated as causal elasticities.

### 3.3 Assumption Visibility
3. **Scenario assumptions must be visible.**
   - Every assumption used in a scenario run must be recorded in an `assumption_log` output.
   - Assumptions must be traceable back to `scenario_assumption_config.csv` or user entry.

### 3.4 Data Immutability
4. **User-entered assumptions must not overwrite observed data.**
   - Observed baselines must be stored in immutable columns (e.g., `baseline_kpi_value`).
   - Scenario-adjusted values must be stored in separate columns (e.g., `scenario_kpi_value`).

### 3.5 Traceability
5. **Baseline and scenario values must remain separately traceable.**
   - Every scenario output row must contain both baseline and scenario values.
   - Delta columns (`delta_value`, `delta_percent`) must be derived, not primary storage.

### 3.6 Provisional KPI Governance
6. **Provisional KPI warnings for kpi_003 and kpi_005 must be preserved.**
   - Any scenario involving kpi_003 or kpi_005 must carry `provisional_kpi_warning = True`.
   - Scenario confidence must be capped at "Moderate" when provisional KPIs are primary affected KPIs.

### 3.7 Contradiction Awareness
7. **Material contradictions must reduce scenario confidence.**
   - If a department's contributing-factor record has `contradiction_severity = Material` or `Major`, the scenario confidence for that department must be downgraded.
   - Major contradictions must prevent Strong Hypothesis classification in scenario narratives.

### 3.8 No Automatic Approval
8. **No management recommendation may be automatically approved.**
   - The scenario engine may produce estimated effects; it may not produce approval decisions.
   - All scenario outputs must require explicit human review before entering the approval workflow.

### 3.9 Financial Calculation Boundary
9. **No financial impact may be calculated in Step 2C-2.**
   - Cost, revenue, or budget impact fields must not appear in Step 2C-2 outputs.
   - Financial review (Step 2C-3) is a separate phase with separate authority.

### 3.10 Reproducibility and Audit
10. **Scenario runs must be reproducible and auditable.**
    - Every run must generate a unique `scenario_run_id`.
    - Inputs, assumptions, code version, and timestamp must be persisted.
    - Rerunning the same inputs must produce identical outputs (deterministic engine).

---

## 4. Proposed Phase 2C-2 Structure

### Step 2C-2A — Input and Architecture Review
**Status:** COMPLETE (this document).  
**Deliverables:** Input inventory, scenario architecture, eligibility register, gap register, final report.

### Step 2C-2B — Scenario Catalogue and Assumption Governance
**Not yet started.**  
**Scope:**
- Build the scenario assumption catalogue from the 18 placeholder assumptions.
- Populate default values, min/max bounds, and validation rules.
- Create assumption governance: editable vs. locked, stakeholder validation requirements.
- Define scenario templates for each supported family.
- Establish user-entry UI specification (CLI or Streamlit).

### Step 2C-2C — Baseline and Intervention Calculation Engine
**Not yet started.**  
**Scope:**
- Build the deterministic scenario calculation engine.
- Implement baseline extraction from analytical daily files.
- Implement intervention-effect formulas (plausibility-bounded, not causal).
- Handle missing baseline values (imputation rules or exclusion).
- Generate per-department, per-KPI scenario outputs.

### Step 2C-2D — Multi-KPI Impact and Trade-Off Analysis
**Not yet started.**  
**Scope:**
- Compute cross-KPI impact matrices using Step 2B-4 relationship strengths.
- Apply contradiction severity penalties to cross-KPI confidence.
- Generate trade-off summaries (e.g., staffing increase vs. satisfaction change).
- Produce scenario narrative text with governed non-causality language.

### Step 2C-2E — Scenario Validation and Challenge
**Not yet started.**  
**Scope:**
- Validate scenario outputs against sanity bounds (e.g., staffing cannot exceed 200% of establishment).
- Challenge extreme assumptions (out-of-bounds warnings).
- Compare scenario deltas to historically observed variability.
- Produce validation report with pass/fail status per scenario run.

### Step 2C-2F — Scenario Closure and Handover
**Not yet started.**  
**Scope:**
- Freeze validated scenario outputs.
- Generate scenario run manifest and checksums.
- Hand over to Step 2C-3 (Financial Review) and Step 2C-4 (Approval Decision).
- Archive assumptions and intermediate calculations.

---

## 5. Technology and Data-Flow Architecture

### 5.1 Proposed Engine Components

```
┌─────────────────────────────────────────────────────────────┐
│  Phase 2C-2B: Scenario Catalogue & Assumption Governance   │
│  ─────────────────────────────────────────────────────────  │
│  User inputs → Assumption Validator → Assumption Log       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 2C-2C: Baseline & Intervention Calculation Engine   │
│  ─────────────────────────────────────────────────────────  │
│  Baseline Loader → Intervention Formula → Scenario Output  │
│  (reads analytical_*.csv)    (plausibility bounded)        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 2C-2D: Multi-KPI Impact & Trade-Off Analysis        │
│  ─────────────────────────────────────────────────────────  │
│  Relationship Loader → Impact Matrix → Trade-Off Report    │
│  (reads contributing_factor_scores, network_edges)         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 2C-2E: Scenario Validation & Challenge              │
│  ─────────────────────────────────────────────────────────  │
│  Sanity Checker → Historical Comparator → Validation Report │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 2C-2F: Scenario Closure & Handover                  │
│  ─────────────────────────────────────────────────────────  │
│  Manifest Generator → Checksum Writer → Archive             │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Data Sources (Read-Only)

| Source | Consumed By | Purpose |
|--------|-------------|---------|
| `analytical_workforce_kpi_daily.csv` | Baseline Loader | kpi_001, kpi_002 baselines |
| `analytical_patient_flow_kpi_daily.csv` | Baseline Loader | kpi_003, kpi_004 baselines |
| `analytical_patient_experience_kpi_daily.csv` | Baseline Loader | kpi_005, kpi_006 baselines |
| `analytical_department_risk_daily.csv` | Baseline Loader | Department tier, urgency, dominant KPI |
| `analytical_contributing_factor_scores.csv` | Impact Matrix | Cross-KPI effect bounds |
| `analytical_relationship_network_edges.csv` | Impact Matrix | Network propagation structure |
| `config/scenario_assumption_config.csv` | Assumption Validator | User-adjustable parameters |
| `config/kpi_threshold_config.csv` | Intervention Formula | Threshold boundaries |

### 5.3 Proposed Outputs

| Output | Produced By | Purpose |
|--------|-------------|---------|
| `scenario_assumption_log.csv` | Assumption Validator | Audit trail of assumptions |
| `scenario_baseline_extract.csv` | Baseline Loader | Immutable baseline snapshot |
| `scenario_intervention_output.csv` | Intervention Formula | Per-department, per-KPI estimates |
| `scenario_impact_matrix.csv` | Impact Matrix | Cross-KPI effect summary |
| `scenario_trade_off_report.csv` | Trade-Off Report | Narrative comparison |
| `scenario_validation_report.csv` | Validation Report | Pass/fail and warnings |
| `scenario_run_manifest.json` | Manifest Generator | Run metadata and checksums |

---

## 6. Risk and Limitation Register

| ID | Risk | Mitigation | Phase Addressed |
|----|------|------------|-----------------|
| R1 | kpi_003 baseline entirely missing | Exclude bed-capacity scenarios until data backfilled | 2C-2B (catalogue) |
| R2 | kpi_005 baseline largely uncomputable | Exclude complaint-management scenarios until denominator fixed | 2C-2B (catalogue) |
| R3 | Cross-domain effects assumed, not causal | Apply plausibility bounds; flag as "association-based estimate" | 2C-2C, 2C-2D |
| R4 | Scenario assumption placeholders have no defaults | Require user entry or engineered defaults before any run | 2C-2B |
| R5 | No existing scenario engine or tests | Build engine and test suite from first principles | 2C-2C |
| R6 | Medium-confidence kpi_006 baselines | Cap scenario confidence at Moderate for satisfaction scenarios | 2C-2C, 2C-2E |
| R7 | Provisional KPIs (kpi_003, kpi_005) in supporting roles | Preserve warnings; do not allow them as primary affected KPIs until unblocked | 2C-2B |

---

## 7. Readiness for Step 2C-2B

| Criterion | Status |
|-----------|--------|
| Authoritative inputs verified | Yes (4 files, 0 duplicates) |
| Scenario eligibility defined | Yes (346 Required, 11 Recommended, 289 Excluded) |
| Existing resources inventoried | Yes (no engine exists; baselines partially available) |
| Supported families identified | Yes (3 Now, 3 with Conditions, 2 Insufficient) |
| Required inputs listed per family | Yes |
| Governance principles defined | Yes (10 principles) |
| Proposed step structure documented | Yes (2C-2A through 2C-2F) |
| Technology architecture proposed | Yes |
| Risk register created | Yes |

**Step 2C-2A is COMPLETE. Ready to proceed to Step 2C-2B upon authorisation.**
