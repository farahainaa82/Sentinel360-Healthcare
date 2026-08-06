# Step 2B-3 to Step 2B-4 Handover

**From:** Step 2B-3 — Department and KPI Risk Prioritisation Engine  
**To:** Step 2B-4 (pending)  
**Date:** 2026-07-28  
**Status:** Handover Ready

---

## 1. What Step 2B-3 Delivered

### Engines

| Engine | File | Status |
|--------|------|--------|
| KPI Risk Scoring Engine | `src/kpi_risk_scoring_engine.py` | Production-ready |
| Department Risk Prioritisation Engine | `src/department_risk_prioritisation_engine.py` | Production-ready |
| Hospital Risk Summary Engine | `src/hospital_risk_summary_engine.py` | Production-ready |
| Safe Runner | `src/run_risk_prioritisation_engine.py` | Production-ready |

### Models

| Model File | Description |
|------------|-------------|
| `src/risk_prioritisation_models.py` | Enums for confidence, tier, urgency, data availability, issues |

### Configuration (10 files)

All in `config/` with version `v1.0-draft` and status `Technical Rule`.

### Analytical Outputs (12)

All files in `data/analytical/` prefixed with `analytical_kpi_risk_*`, `analytical_department_risk_*`, `analytical_hospital_risk_*`, and `analytical_risk_prioritisation_issues.csv`.

### Validation Outputs (18)

All files in `outputs/risk_prioritisation/`.

### Tests

| Test File | Tests | Status |
|-----------|-------|--------|
| `tests/test_kpi_risk_scoring_engine.py` | 30 | Passed |
| `tests/test_department_risk_prioritisation_engine.py` | 18 | Passed |
| `tests/test_hospital_risk_summary_engine.py` | 12 | Passed |

---

## 2. Known State

| Metric | Value |
|--------|-------|
| Total source KPI records | 17,520 |
| KPI risk records | 17,520 |
| Assessable KPI risk records | 11,397 |
| Unavailable / Not Assessable | 6,123 |
| Department-date risk records | 2,920 |
| Hospital-date summary records | 365 |
| Ranked department records | 2,920 |

---

## 3. Conditions for Step 2B-4

Step 2B-4 readiness is **Ready with Conditions**. The following conditions must be resolved before full readiness:

1. **kpi_003 (Bed Occupancy) threshold finalization**
   - Current status: Conditionally Approved
   - Required: Stakeholder sign-off to remove provisional flag
   - Review date: 2026-09-30

2. **kpi_005 (Patient Complaint Rate) threshold finalization**
   - Current status: Conditionally Approved
   - Required: Stakeholder sign-off to remove provisional flag
   - Review date: 2026-10-25

3. **Risk weight policy approval**
   - Current status: Technical Rule (v1.0-draft)
   - Required: Stakeholder approval if weights are to become operational policy

---

## 4. Assets Ready for Step 2B-4

| Asset | Location | Notes |
|-------|----------|-------|
| KPI risk scores | `data/analytical/analytical_kpi_risk_scores_daily.csv` | 0-100 per KPI |
| KPI risk components | `data/analytical/analytical_kpi_risk_components.csv` | Audit trail |
| Department risk | `data/analytical/analytical_department_risk_daily.csv` | Aggregated scores |
| Department ranking | `data/analytical/analytical_department_risk_ranking.csv` | Deterministic order |
| Department drivers | `data/analytical/analytical_department_risk_drivers.csv` | Dominant/secondary |
| Department concurrence | `data/analytical/analytical_department_risk_concurrence.csv` | Concurrent KPI groups |
| Department confidence | `data/analytical/analytical_department_risk_confidence.csv` | Data availability |
| Department governance | `data/analytical/analytical_department_risk_governance.csv` | Provisional flags |
| Evidence packs | `data/analytical/analytical_department_risk_evidence.csv` | Full audit |
| Lineage | `data/analytical/analytical_department_risk_lineage.csv` | Provenance |
| Hospital summaries | `data/analytical/analytical_hospital_risk_daily_summary.csv` | Roll-up views |

---

## 5. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Provisional thresholds remain unapproved | Medium | Governance warnings persist | Continue monitoring; escalate to stakeholders before review dates |
| Low-confidence KPIs (30 records) | Low | May affect ranking precision | Investigate source data quality |
| All departments flagged provisional | High | Flag loses discrimination | Accept as data reality (kpi_003 and kpi_005 in all depts); use `provisional_driver_list` for detail |

---

## 6. Recommended Step 2B-4 Scope

Based on current state, Step 2B-4 should address:

1. **Relationship analysis** between concurrent KPI groups
2. **Temporal pattern analysis** across the 365-day window
3. **Alerting / notification layer** using urgency and priority tiers
4. **Dashboard data contracts** for risk visualisations
5. **Management review queue** generation from deterministic rankings

---

## 7. Sign-Off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Step 2B-3 Lead | — | — | — |
| Step 2B-4 Lead | — | — | — |
| Governance | — | — | — |

---

**Step 2B-3 Status:** COMPLETE  
**Step 2B-4 Readiness:** Ready with Conditions
