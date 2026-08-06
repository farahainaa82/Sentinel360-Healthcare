# Phase 2A Acceptance Criteria

## Step 2A-6 — Formal Closure

**Version:** 1.0-draft  
**Date:** 2026-07-27  
**Status:** Accepted

---

## 1. Mandatory Checks

The following checks must pass for Step 2A-6 to be accepted:

| # | Check | Criterion |
|---|-------|-----------|
| 1 | Six approved KPIs present | All kpi_001 through kpi_006 exist in integrated dataset |
| 2 | Total integrated records | Exactly 17,520 |
| 3 | Records per KPI | Exactly 2,920 per KPI |
| 4 | Coverage grains | Exactly 2,920 unique hospital-department-date grains |
| 5 | Rows per grain | Exactly 6 KPI rows per grain |
| 6 | Source-integrated reconciliation | Zero count difference for every KPI |
| 7 | Value preservation | Zero unexplained kpi_value mismatch |
| 8 | Duplicate grains | Zero duplicates |
| 9 | Missing rows | Zero missing KPI rows |
| 10 | Value-status consistency | Zero inconsistencies |
| 11 | Threshold governance | All Not Assessed; all provisional; no Green/Amber/Red |
| 12 | Confidence validity | No unavailable record with High confidence |
| 13 | Evidence for calculated | All calculated records have Complete evidence status |
| 14 | Lineage for calculated | All calculated records have Complete lineage status |
| 15 | Schema | All required fields present; valid types; dates parse |
| 16 | Key uniqueness | integration_record_id unique; no duplicate grain |
| 17 | Immutability | All accepted Phase 1 and 2A files unchanged |
| 18 | Regression tests | All focused closure tests pass |
| 19 | Closure outputs | All 24 required outputs generated |
| 20 | Documentation | All required documentation exists |

---

## 2. Expected Record Counts

| KPI | Name | Calculated | Unavailable | Total |
|-----|------|------------|-------------|-------|
| kpi_001 | Staffing Level | 2,920 | 0 | 2,920 |
| kpi_002 | Staff Absenteeism Rate | 2,920 | 0 | 2,920 |
| kpi_003 | Bed Occupancy Rate | 1,095 | 1,825 | 2,920 |
| kpi_004 | Average Patient Waiting Time | 1,095 | 1,825 | 2,920 |
| kpi_005 | Patient Complaint Rate | 984 | 1,936 | 2,920 |
| kpi_006 | Patient Satisfaction Score | 2,383 | 537 | 2,920 |
| **Total** | | **9,397** | **6,123** | **17,520** |

---

## 3. Permitted Warnings

The following warnings are permitted and do not block closure:

1. **Provisional thresholds** — All 17,520 records have threshold_status = Not Assessed and threshold_is_provisional = True. This is expected because threshold boundaries have not been formally approved.
2. **Empty evidence dataset** — The analytical_six_kpi_evidence.csv may be empty if evidence is tracked at the daily record level via evidence_status.
3. **Empty lineage dataset** — The analytical_six_kpi_lineage.csv may be empty if lineage is tracked at the daily record level via lineage_status.
4. **Missing optional prior manifests** — Workforce, patient-flow, and patient-experience domain manifests may not exist as separate JSON files if they were not generated in earlier steps.

---

## 4. Blocking Defects

Any of the following is a blocking defect:

- Missing required source, integrated, or configuration file
- Source-to-integrated count mismatch
- Duplicate hospital-department-date-kpi grain
- Missing KPI row for any grain
- Calculated status with null kpi_value
- Non-calculated status with non-null kpi_value
- Green, Amber, or Red threshold status
- Unavailable record with High confidence
- KPI value mismatch between source and integrated
- Broken lineage for calculated record
- Accepted file changed (immutability failure)
- Missing required field in schema
- Non-unique integration_record_id

---

## 5. Threshold Governance Limitations

- threshold_status = Not Assessed for all 17,520 records
- threshold_is_provisional = True for all 17,520 records
- No Green, Amber, or Red classifications exist
- Threshold version = v1.0-draft
- Stakeholder approval remains pending

This limitation is documented and does not block Phase 2B if Phase 2B supports threshold-independent trends and statistical signals.

---

## 6. Readiness Conditions for Phase 2B

Phase 2B may proceed only if:

1. All blocking defects are resolved (or none exist).
2. Source-to-integrated reconciliation is exact.
3. Schema and key validation pass.
4. Immutability is verified.
5. Regression tests pass.
6. Closure outputs and documentation are generated.

If provisional thresholds remain, Phase 2B readiness is **Ready with Conditions**:
- Threshold-based alerts must remain disabled or marked provisional.
- Trend, anomaly, and relationship analysis may proceed.
- Threshold-breach logic must remain provisional or disabled until approved.
