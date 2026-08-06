# Phase 2A to Phase 2B Handover

**Date:** 2026-07-27  
**From:** Phase 2A — Analytical Layer  
**To:** Phase 2B — Advanced Analytics (Trends, Anomalies, Signals)  
**Closure Status:** Passed with Warning  
**Readiness:** Ready with Conditions

---

## 1. Accepted Analytical Datasets

The following datasets are formally accepted and frozen for Phase 2B consumption:

| Dataset | Path | Rows | Status |
|---------|------|------|--------|
| Integrated Six-KPI Daily | `data/analytical/analytical_six_kpi_daily.csv` | 17,520 | Frozen |
| Six-KPI Evidence | `data/analytical/analytical_six_kpi_evidence.csv` | Empty | Frozen |
| Six-KPI Exclusions | `data/analytical/analytical_six_kpi_exclusions.csv` | Empty | Frozen |
| Six-KPI Lineage | `data/analytical/analytical_six_kpi_lineage.csv` | Empty | Frozen |
| Six-KPI Issues | `data/analytical/analytical_six_kpi_issues.csv` | Empty | Frozen |
| Six-KPI Audit | `data/analytical/analytical_six_kpi_audit.csv` | 15 | Frozen |
| Six-KPI Coverage Daily | `data/analytical/analytical_six_kpi_coverage_daily.csv` | 2,920 | Frozen |
| Phase 2A Closure Snapshot | `data/analytical/analytical_phase_2a_closure_snapshot.csv` | 6 | Frozen |
| Workforce KPI Daily | `data/analytical/analytical_workforce_kpi_daily.csv` | 5,840 | Frozen |
| Patient Flow KPI Daily | `data/analytical/analytical_patient_flow_kpi_daily.csv` | 5,840 | Frozen |
| Patient Experience KPI Daily | `data/analytical/analytical_patient_experience_kpi_daily.csv` | 5,840 | Frozen |

---

## 2. Frozen Files

Do not modify any of the following accepted files:

- All files in `data/analytical/` listed above
- All source engine files (`src/workforce_kpi_engine.py`, `src/patient_flow_kpi_engine.py`, `src/patient_experience_kpi_engine.py`)
- All integration files (`src/six_kpi_integration_engine.py`, `src/run_six_kpi_integration.py`)
- All architecture files (`src/analytical_models.py`, `src/analytical_contracts.py`, `src/kpi_registry.py`, etc.)
- All configuration files (`config/kpi_definition_config.csv`, `config/kpi_threshold_config.csv`, `config/data_confidence_config.csv`)

---

## 3. Allowed Phase 2B Inputs

Phase 2B may read and analyze:

- `data/analytical/analytical_six_kpi_daily.csv` (authoritative integrated dataset)
- `data/analytical/analytical_six_kpi_coverage_daily.csv` (coverage matrix)
- `data/analytical/analytical_phase_2a_closure_snapshot.csv` (closure summary)
- Domain-specific daily files for drill-down
- `config/kpi_definition_config.csv` for metadata

Phase 2B may create new outputs in `data/analytical/` or `outputs/` provided they do not overwrite accepted Phase 2A files.

---

## 4. Prohibited Modifications

Phase 2B must NOT:

- Modify accepted KPI values
- Recalculate KPI formulas
- Change calculation_status, readiness_status, or data_confidence_level
- Approve or change thresholds without formal governance
- Assign Green, Amber, or Red statuses
- Delete or alter accepted evidence, lineage, exclusion, issue, or audit records
- Modify accepted source datasets (`data/processed/`)
- Change deterministic IDs or business keys

---

## 5. Known Provisional Elements

### Thresholds
- All 17,520 records have threshold_status = Not Assessed
- All thresholds are provisional (threshold_is_provisional = True)
- Threshold version = v1.0-draft
- Stakeholder approval is pending

### Confidence
- Some confidence assignments are provisional (confidence_is_provisional = True)
- Confidence rule version = v1.0-draft

---

## 6. Threshold Limitations

- No Green, Amber, or Red classifications exist.
- Threshold-breach logic must remain disabled or marked provisional.
- Performance classification cannot be used for alerts or scoring until thresholds are approved.
- Trend and anomaly detection should rely on statistical methods rather than threshold breaches.

---

## 7. Known Lineage Limitations

- Workforce daily aggregation may have source_record_id limitations due to aggregation across staff-role records.
- This is a documented limitation from Phase 1 and does not affect the validity of calculated workforce KPIs.
- Partial lineage is accepted where aggregation prevents record-level linkage.

---

## 8. Required Phase 2B Controls

Phase 2B must implement the following controls:

1. **Read-only access** to accepted Phase 2A datasets.
2. **Versioning** for all new analytical outputs.
3. **Audit logging** for all Phase 2B operations.
4. **Configuration control** for any new thresholds or rules.
5. **Immutability verification** before and after each Phase 2B step.
6. **Explicit flagging** of any threshold-dependent output as provisional.

---

## 9. Expected First Phase 2B Step

The recommended first step in Phase 2B is:

**Trend and Statistical-Signal Architecture**

Objectives:
- Establish period-over-period comparison framework
- Define statistical baseline calculation methods
- Design anomaly detection rules independent of threshold classifications
- Create controlled early-warning signal generation
- Ensure all new outputs are versioned and auditable

This step must not:
- Approve thresholds
- Create Green/Amber/Red assignments
- Enable threshold-breach alerts
