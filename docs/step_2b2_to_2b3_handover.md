# Step 2B-2 to Step 2B-3 Handover

**From:** Step 2B-2 — Threshold Breach & Watch Condition Engine  
**To:** Step 2B-3 (pending)  
**Date:** 2026-07-27  
**Status:** Handover Ready

---

## 1. What Step 2B-2 Delivered

### Engines

| Engine | File | Status |
|--------|------|--------|
| KPI Threshold Breach Engine | `src/kpi_threshold_breach_engine.py` | Production-ready |
| KPI Watch Condition Engine | `src/kpi_watch_condition_engine.py` | Production-ready |
| Safe Runner | `src/run_threshold_breach_watch_engine.py` | Production-ready |

### Models

| Model File | Description |
|------------|-------------|
| `src/threshold_breach_models.py` | Enums and data classes for breach/watch domain |

### Configuration

| Config File | Description |
|-------------|-------------|
| `config/threshold_breach_rule_config.csv` | 7 breach rules |
| `config/watch_condition_rule_config.csv` | 10 watch rules |
| `config/watch_persistence_config.csv` | Persistence parameters |
| `config/watch_confidence_config.csv` | Confidence thresholds |
| `config/provisional_threshold_handling_config.csv` | Provisional handling rules |

### Analytical Outputs (10)

All files in `data/analytical/` prefixed with `analytical_kpi_*` related to threshold, breach, watch, persistence, trend, evidence, lineage, governance, issues, and daily summary.

### Validation Outputs (16)

All files in `outputs/threshold_watch/` covering run summary, reconciliation, manifest, distributions, crosschecks, summaries, issue log, and readiness assessment.

### Tests

| Test File | Tests | Status |
|-----------|-------|--------|
| `tests/test_threshold_breach_watch_engine.py` | 22 | All passed |

---

## 2. Known State

| Metric | Value |
|--------|-------|
| Total source records | 17,520 |
| Classifiable records | 11,397 |
| Unavailable records | 6,123 |
| Actual breach events | 2,464 |
| Actual watch conditions | 9,120 |
| Daily summaries | 2,920 |
| Issues | 0 |

---

## 3. Conditions for Step 2B-3

Step 2B-3 readiness is **Ready with Conditions**. The following conditions must be resolved before full readiness:

1. **kpi_003 (Bed Occupancy) threshold finalization**
   - Current status: Conditionally Approved
   - Required: Stakeholder sign-off to remove provisional flag
   - Impact: Until resolved, breaches will continue to be flagged as `BREACH_PROVISIONAL`

2. **kpi_005 (Staffing Ratio) threshold finalization**
   - Current status: Conditionally Approved
   - Required: Stakeholder sign-off to remove provisional flag
   - Impact: Until resolved, breaches will continue to be flagged as `BREACH_PROVISIONAL`

3. **Review date assignment**
   - Current status: Monitored (no fixed dates)
   - Required: Enter formal review dates in `config/kpi_threshold_stakeholder_decisions.csv`
   - Impact: `REVIEW_DUE` watch conditions depend on explicit dates

---

## 4. Assets Ready for Step 2B-3

| Asset | Location | Notes |
|-------|----------|-------|
| Classified daily records | `data/analytical/analytical_kpi_threshold_classification_daily.csv` | G-A-R per record |
| Breach events | `data/analytical/analytical_kpi_breach_events.csv` | With flags and types |
| Watch conditions | `data/analytical/analytical_kpi_watch_conditions.csv` | With severity |
| Watch persistence | `data/analytical/analytical_kpi_watch_persistence.csv` | Duration tracking |
| Trend integration | `data/analytical/analytical_kpi_breach_trend_integration.csv` | Trend + breach overlay |
| Evidence | `data/analytical/analytical_kpi_watch_evidence.csv` | Audit trail |
| Lineage | `data/analytical/analytical_kpi_watch_lineage.csv` | Provenance |
| Governance | `data/analytical/analytical_kpi_watch_governance.csv` | Flags and review dates |

---

## 5. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Provisional thresholds remain unapproved | Medium | Governance warnings persist | Continue monitoring; escalate to stakeholders |
| Test runtime slows CI/CD | Medium | Feedback loops lengthen | Implement shared fixtures and test separation |
| OneDrive file locking during runs | Low | Write failures | Use local workspace copies for engine execution |

---

## 6. Recommended Step 2B-3 Scope

Based on the current state, Step 2B-3 should address:

1. **Stakeholder approval workflow** for provisional thresholds
2. **Threshold refinement** based on watch-condition feedback
3. **Alerting / notification layer** using watch condition outputs
4. **Dashboard data contracts** for breach and watch visualizations
5. **Performance optimization** of test suite and engine execution

---

## 7. Sign-Off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Step 2B-2 Lead | — | — | — |
| Step 2B-3 Lead | — | — | — |
| Governance | — | — | — |

---

**Step 2B-2 Status:** COMPLETE  
**Step 2B-3 Readiness:** Ready with Conditions
