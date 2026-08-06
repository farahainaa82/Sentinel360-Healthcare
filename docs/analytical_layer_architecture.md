# Analytical Layer Architecture

## Document Control

| Attribute | Value |
|-----------|-------|
| Document ID | ARCH-2A1-001 |
| Version | 1.0.0 |
| Phase | Phase 2A - Analytical Layer |
| Step | 2A-1 |
| Date | 2026-07-27 |
| Status | Approved |

## 1. Purpose

This document defines the governed analytical foundation for Sentinel360 Healthcare. It establishes the separation between the preparation layer (Phase 1) and the analytical layer (Phase 2A), and documents the architecture for KPI definition, governance, validation, and future calculation.

## 2. Layer Separation

### 2.1 Preparation Layer (Phase 1)

The preparation layer is formally closed and immutable. It contains:
- 16 validated processed datasets
- Cross-domain operational daily dataset (`processed_operational_daily.csv`)
- Schema registry, manifests, and audit trails
- All datasets are read-only for the analytical layer

### 2.2 Analytical Layer (Phase 2A)

The analytical layer consumes prepared data and produces:
- KPI calculations
- Evidence and exclusion records
- Threshold assignments
- Confidence assessments
- Lineage and audit records

The analytical layer must never modify preparation layer outputs.

## 3. Analytical Input Contracts

### 3.1 Contract Principles
- All KPI calculations must use governed definitions
- Source fields must be explicitly mapped and validated
- Thresholds must be configuration-driven
- No hard-coded business rules

### 3.2 Input Datasets

| Dataset | Grain | Primary Use |
|---------|-------|-------------|
| processed_operational_daily | hospital-department-date | Staffing, absenteeism, occupancy, complaints, satisfaction |
| processed_patient_encounters | encounter | Waiting time eligibility |

## 4. Configuration Precedence

Configuration is the authoritative source for:
- KPI definitions
- Threshold values
- Data-confidence rules
- Eligibility and exclusion rules

Configuration files (in `config/`):
- `kpi_definition_config.csv`
- `kpi_threshold_config.csv`
- `data_confidence_config.csv`

## 5. KPI Registry

The KPI registry contains exactly six approved KPIs:

| KPI ID | Name | Domain | Grain |
|--------|------|--------|-------|
| kpi_001 | Staffing Level | Workforce | hospital-department-date |
| kpi_002 | Staff Absenteeism Rate | Workforce | hospital-department-date |
| kpi_003 | Bed Occupancy Rate | Patient Flow | hospital-department-date |
| kpi_004 | Average Patient Waiting Time | Patient Flow | hospital-department-date |
| kpi_005 | Patient Complaint Rate | Patient Experience | hospital-department-date |
| kpi_006 | Patient Satisfaction Score | Patient Experience | hospital-department-date |

## 6. Analytical Schemas

Nine analytical output schemas are defined:

1. `analytical_kpi_daily` - Daily KPI values
2. `analytical_kpi_monthly` - Monthly aggregated KPI values
3. `analytical_kpi_evidence` - Numerator/denominator evidence
4. `analytical_kpi_exclusions` - Excluded records
5. `analytical_kpi_lineage` - Source-to-target lineage
6. `analytical_kpi_issues` - Calculation issues
7. `analytical_kpi_audit` - Audit trail
8. `analytical_kpi_run_manifest` - Run metadata
9. `analytical_kpi_readiness` - KPI readiness status

## 7. Eligibility and Exclusion Handling

### 7.1 Eligibility Rules
- Defined in KPI configuration
- Applied before aggregation
- Documented in evidence records

### 7.2 Exclusion Rules
- Records excluded from calculation are logged
- Exclusion reasons are configuration-driven
- Exclusion counts are reported

## 8. Threshold Governance

### 8.1 Threshold Sources
- `kpi_threshold_config.csv` is the authoritative source
- Thresholds are versioned and effective-dated
- Approval status is tracked

### 8.2 Threshold Assignment
- Thresholds are assigned at calculation time
- Multiple thresholds per KPI are supported
- Severity levels: critical, warning, info

## 9. Confidence Assessment

Data confidence is assessed using:
- Completeness percentage
- Freshness (days since update)
- Validation pass/fail status

Confidence levels: high, medium, low, insufficient

## 10. Audit and Lineage

### 10.1 Lineage
- Every analytical output record has lineage
- Links to source dataset and source record
- Transformation name and version tracked

### 10.2 Audit
- Every calculation run produces an audit trail
- Record counts, timestamps, and operator tracked
- Issues and exclusions logged

## 11. Readiness Gating

KPI readiness statuses:
- **Ready** - All requirements met, calculation permitted
- **Conditionally Ready** - Minor issues, calculation permitted with warnings
- **Blocked** - Critical issues, calculation prohibited
- **Not Applicable** - KPI not relevant for current scope

Calculation is gated by:
- Phase 1 immutability verification
- No blocked KPIs
- All governance checks passed

## 12. Future Calculation Flow

Step 2A-2 (not started) will:
1. Load governed KPI definitions
2. Apply eligibility and exclusion rules
3. Calculate numerator and denominator
4. Compute KPI value
5. Assign thresholds
6. Assess confidence
7. Generate evidence, exclusions, lineage
8. Produce analytical outputs
9. Create audit trail

## 13. Files

### 13.1 Implementation Files
- `src/analytical_models.py`
- `src/analytical_contracts.py`
- `src/analytical_config_loader.py`
- `src/kpi_registry.py`
- `src/analytical_schema_registry.py`
- `src/analytical_governance_validator.py`
- `src/run_analytical_architecture_validation.py`

### 13.2 Test Files
- `tests/test_analytical_architecture.py`

### 13.3 Governance Outputs
- `outputs/analytical_governance/analytical_architecture_manifest.json`
- `outputs/analytical_governance/kpi_governance_registry.csv`
- `outputs/analytical_governance/kpi_readiness_summary.csv`
- `outputs/analytical_governance/kpi_source_field_mapping.csv`
- `outputs/analytical_governance/kpi_configuration_validation.csv`
- `outputs/analytical_governance/kpi_threshold_validation.csv`
- `outputs/analytical_governance/analytical_schema_summary.csv`
- `outputs/analytical_governance/analytical_governance_issue_log.csv`
- `outputs/analytical_governance/analytical_governance_audit_log.csv`
- `outputs/analytical_governance/phase1_immutability_verification.csv`
