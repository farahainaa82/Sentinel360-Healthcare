# Analytical Layer Validation Specification

## Step 2A-6 — Phase 2A Closure

**Version:** 1.0-draft  
**Date:** 2026-07-27  
**Status:** Accepted

---

## 1. Scope

This document defines the formal validation and closure process for the Phase 2A Analytical Layer of the Sentinel360 Healthcare analytics platform.

The closure process validates the full analytical architecture, all six governed KPIs, integration outputs, schemas, keys, statuses, evidence, lineage, audit records, configuration consistency, coverage completeness, and immutability of all prior accepted steps.

No KPI recalculation, threshold approval, trend generation, anomaly detection, or risk scoring occurs during this step.

---

## 2. Validation Domains

The closure process validates the following 23 domains:

1. Architecture
2. KPI Registry
3. Source Datasets
4. KPI Results
5. Formula Evidence
6. Integration Reconciliation
7. Calculation Statuses
8. Readiness Statuses
9. Threshold Governance
10. Data Confidence
11. Evidence Completeness
12. Lineage Completeness
13. Exclusions
14. Issues
15. Audit Records
16. Coverage
17. Schemas
18. Business Keys
19. Deterministic IDs
20. Immutability
21. Regression Results
22. Documentation Completeness
23. Readiness for Phase 2B

Each domain produces a structured result with a controlled closure status and severity.

---

## 3. Authoritative Inputs

### Phase 1
- `data/processed/processed_operational_daily.csv`
- Accepted Phase 1 closure reports and manifests

### Step 2A-1 — Architecture
- `src/analytical_models.py`
- `src/analytical_contracts.py`
- `src/analytical_config_loader.py`
- `src/kpi_registry.py`
- `src/analytical_schema_registry.py`
- `src/analytical_governance_validator.py`
- `src/run_analytical_architecture_validation.py`
- `tests/test_analytical_architecture.py`
- `config/kpi_definition_config.csv`
- `config/kpi_threshold_config.csv`
- `config/data_confidence_config.csv`

### Step 2A-2 — Workforce
- `src/workforce_kpi_engine.py`
- `src/run_workforce_kpi_processing.py`
- `tests/test_workforce_kpi_engine.py`
- `data/analytical/analytical_workforce_kpi_daily.csv`

### Step 2A-3 — Patient Flow
- `src/patient_flow_kpi_engine.py`
- `src/run_patient_flow_kpi_processing.py`
- `tests/test_patient_flow_kpi_engine.py`
- `data/analytical/analytical_patient_flow_kpi_daily.csv`

### Step 2A-4 — Patient Experience
- `src/patient_experience_kpi_engine.py`
- `src/run_patient_experience_kpi_processing.py`
- `tests/test_patient_experience_kpi_engine.py`
- `data/analytical/analytical_patient_experience_kpi_daily.csv`

### Step 2A-5 — Integration
- `src/six_kpi_integration_engine.py`
- `src/run_six_kpi_integration.py`
- `tests/test_six_kpi_integration_engine.py`
- `data/analytical/analytical_six_kpi_daily.csv`
- `data/analytical/analytical_six_kpi_evidence.csv`
- `data/analytical/analytical_six_kpi_exclusions.csv`
- `data/analytical/analytical_six_kpi_lineage.csv`
- `data/analytical/analytical_six_kpi_issues.csv`
- `data/analytical/analytical_six_kpi_audit.csv`
- `data/analytical/analytical_six_kpi_coverage_daily.csv`

---

## 4. Closure Status Rules

Controlled closure statuses:

- **Passed** — all required checks pass; no unresolved warning exists.
- **Passed with Warning** — all blocking checks pass; only approved provisional governance limitations remain.
- **Failed** — at least one blocking validation fails.
- **Not Applicable** — check does not apply and the reason is documented.

Controlled severity levels:

- **Information** — informational finding only.
- **Warning** — governance limitation or known issue that does not block closure.
- **Blocking** — defect that prevents closure or Phase 2B readiness.

---

## 5. Blocking vs Warning Findings

### Blocking findings include:
- Missing required file
- Source-to-integrated count mismatch
- Duplicate hospital-department-date-kpi grain
- Missing KPI row for a grain
- Calculated KPI with null value
- Unavailable KPI with High confidence
- Green, Amber, or Red threshold status
- KPI value mismatch between source and integrated
- Broken lineage for calculated record
- Immutability failure (accepted file changed)
- Schema violation (missing required field)
- Non-unique integration_record_id

### Warning findings include:
- Provisional thresholds (expected)
- Empty evidence/lineage dataset when daily status is adequate
- Missing optional prior manifest
- Empty audit dataset
- Missing optional documentation (unless strict mode)

---

## 6. Reconciliation

Formal reconciliation is performed across:
- Source KPI engine output
- Integrated six-KPI output
- Accepted count from Step 2A-5
- Closure validation count

For each KPI, the following are reported:
- kpi_id, kpi_name, source_dataset
- source_row_count, integrated_row_count, closure_row_count
- calculated_count, unavailable_count
- duplicate_count, missing_count
- count_difference, reconciliation_status

Any unexplained count difference is blocking.

---

## 7. Status Validation

### Calculation Status
Valid statuses: Calculated, Insufficient Data, Zero Denominator, Configuration Missing, Rule Pending, Invalid Input.

Validation rules:
- Calculated status requires non-null kpi_value
- Non-calculated status requires null kpi_value
- Unavailable records must not have High confidence

### Threshold Governance
- All records must have threshold_status = Not Assessed
- All records must have threshold_is_provisional = True
- No Green, Amber, or Red may exist
- Draft thresholds must not be marked approved

### Confidence Governance
- Valid levels: High, Medium, Low, Unavailable
- Unavailable results must not have High confidence
- Confidence rule version must be preserved

---

## 8. Evidence Validation

For each calculated KPI, evidence must exist supporting:
- Numerator value
- Denominator value
- Formula multiplier or weighting (where applicable)

For unavailable KPIs, explanatory evidence must document the cause (e.g., eligibility, zero denominator, missing input).

Calculated KPI with missing mandatory evidence is blocking.

---

## 9. Lineage Validation

All integrated KPI records must link to accepted source analytical records via:
- source_analytical_dataset
- source_analytical_record_id
- source_calculation_run_id

Calculated KPI with unexplained broken lineage is blocking.
Documented aggregation limitations (e.g., workforce daily aggregation) are treated as non-blocking warnings.

---

## 10. Coverage Validation

The six-KPI coverage matrix must satisfy:
- 2,920 coverage records
- 6 expected KPIs per hospital-department-date grain
- 6 present KPI records per grain
- 0 missing KPI records
- coverage_percentage = 100%
- coverage_status = Complete for all grains

Unavailable KPI rows are valid and count as present. Missing KPI row is blocking.

---

## 11. Schema Validation

Required checks:
- Required fields exist
- Field names match contracts
- Data types are valid
- Dates parse correctly
- reporting_month matches reporting_date
- reporting_year matches reporting_date
- KPI IDs are valid
- Units match KPI registry
- integration_record_id is unique
- No duplicate hospital-department-date-kpi_id grain

---

## 12. Immutability

Before closure:
1. Record SHA-256 checksums for all accepted files.
2. Run validation and closure.
3. Record checksums again.
4. Compare before and after.

Only new Step 2A-6 closure files may be created. Any unexplained accepted-file change is blocking.

---

## 13. Readiness Decision

Phase 2B readiness may be:
- **Ready** — no blocking defects; no unresolved warning affecting trend or anomaly analysis.
- **Ready with Conditions** — no blocking defects; provisional thresholds remain; threshold-based alerts must remain disabled or marked provisional; trend and anomaly development may proceed.
- **Not Ready** — source reconciliation failure, duplicate records, broken schema, missing KPI rows, calculated values without evidence, broken lineage, immutability failure, or unresolved KPI-value mismatch.
