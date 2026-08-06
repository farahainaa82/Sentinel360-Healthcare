# Phase 2D-1 Integrated Decision Model Methodology

**Date:** 2026-07-29
**Phase:** 2D-1 — Integrated Decision Data Model
**Purpose:** Create one governed integrated decision data model connecting operational risk, KPI evidence, recommendations, scenario options, financial impact, uncertainty, governance warnings, management readiness, and audit lineage.

---

## 1. Scope and Principles

Phase 2D-1 is an **integration and reconciliation step**. It does not rerun any previous phase engines. It reads the latest frozen authoritative outputs from Phases 2B, 2C-1, 2C-2, and 2C-3, and joins them into a single decision-support dataset.

**Core principles:**
- One integrated decision record per approval package (646 total)
- Governed identifiers used for all joins
- No Cartesian joins permitted
- No management decisions made
- No preferred scenario selected
- No approval recorded
- Frozen upstream files remain immutable

---

## 2. Authoritative Inputs

| Phase | File | Rows | Role |
|-------|------|------|------|
| 2C-2F | `step_2c2f_package_closure_register.csv` | 646 | Master package list |
| 2C-2F | `step_2c2f_management_scenario_package_register.csv` | 311 | Management scenario summaries |
| 2C-2F | `step_2c2f_scenario_run_closure_register.csv` | 2,711 | Scenario run details |
| 2C-2F | `step_2c2f_comparator_closure_register.csv` | 357 | Comparator consistency |
| 2C-2F | `step_2c2f_deferred_and_non_ready_register.csv` | 335 | Deferred / monitoring packages |
| 2C-3 | `step_2c3_financial_readiness_register.csv` | 311 | Financial readiness |
| 2C-3 | `step_2c3_management_financial_comparison.csv` | 311 | Financial comparison |
| 2C-3 | `step_2c3_financial_confidence_register.csv` | 1,071 | Financial confidence |
| 2C-1 | `step_2c1d_episode_approval_package_register.csv` | 646 | Recommendation details |
| 2B | `analytical_department_risk_ranking.csv` | 2,920 | Risk data |

---

## 3. Integration Architecture

### 3.1 Primary Key

`approval_package_id` — present in all package-level inputs.

### 3.2 Join Design

```
package_closure (646 rows, left)
  ├── management_scenario (311 rows) — LEFT on approval_package_id
  ├── approval_package (646 rows) — LEFT on approval_package_id
  ├── financial_readiness (311 rows) — LEFT on approval_package_id
  ├── financial_comparison (311 rows) — LEFT on approval_package_id
  ├── comparator_closure (357 rows) — AGGREGATE then LEFT on approval_package_id
  ├── scenario_runs (2,711 rows) — AGGREGATE then LEFT on approval_package_id
  └── deferred_non_ready (335 rows) — LEFT on approval_package_id
```

**Cardinality protection:**
- 1:1 joins use unique keys (verified before merge)
- 1:N inputs are aggregated before joining
- Estimated merge size checked before execution

### 3.3 Output Row Count Guarantee

The integration engine guarantees exactly 646 output rows — one per approval package. Any deviation triggers an execution stop.

---

## 4. Field Population

### 4.1 Identity Fields

Populated directly from `package_closure`: approval_package_id, episode_id, hospital_id, hospital_name, department_id, department_name, reporting_date, dominant_kpi_id, dominant_kpi_name, scenario_family.

### 4.2 Risk Fields

Populated from `package_closure`: risk_score, risk_tier, priority_tier, urgency.

### 4.3 Recommendation Fields

Populated from `management_scenario` and `approval_package`: representative_recommendation, recommendation_horizon, recommendation_type, recommendation_validation_status.

### 4.4 Scenario Fields

Populated from `management_scenario`: comparator_completeness, baseline_available, conservative_available, expected_available, higher_intensity_available, scenario_validation_status, scenario_confidence, trade-off/displacement/sensitivity/dominance summaries.

### 4.5 Financial Fields

Populated from `financial_readiness` and `financial_comparison`: financial_review_required, financial_readiness, cost_completeness, estimated costs/benefits/net impact, ROI/payback/affordability status, uncertainty range.

### 4.6 Governance Fields

Computed during integration:
- causality_status = "Not Confirmed" (fixed)
- provisional_warning, contradiction_warning from upstream
- stakeholder_validation_required = True
- assumption_validation_required, baseline_validation_required, financial_validation_required from closure categories
- management_review_required = True
- evidence_available = True
- lineage_available = True
- governance_issue_count from validation
- approval_status = "Pending Management Review"

---

## 5. Execution Controls

1. Single-instance lock file
2. Authority verification with checksums
3. Integration key validation
4. Merge size estimation
5. Temp directory output
6. Atomic move to final
7. Manifest generation after all outputs complete
8. Smoke test before full run

---

*End of Integrated Decision Model Methodology*
