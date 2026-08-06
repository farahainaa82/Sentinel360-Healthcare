# Step 2B-3 Validation Report

**Run ID:** RISKPRIOR-20260728055229  
**Step:** 2B-3 — Department and KPI Risk Prioritisation Engine  
**Processed At:** 2026-07-28T05:52:29  
**Report Generated:** 2026-07-28  
**Status:** COMPLETE

---

## 1. Executive Summary

Step 2B-3 has been successfully executed. All 73 tests passed. Zero blocking issues. Upstream immutability verified. A focused governance refinement was applied to correct over-flagging of provisional risk at the department level. The step is closed with readiness for Step 2B-4 assessed as **Ready with Conditions**.

---

## 2. Test Results

| Metric | Value |
|--------|-------|
| Test files | 3 |
| Total tests | 73 |
| Passed | 73 |
| Failed | 0 |
| Skipped | 0 |
| Runtime | ~11 seconds |
| Strategy | Module-scoped fixtures loading pre-generated outputs |

### Test Coverage

- **Score Range:** Min/max bounds, no negative components, unavailable handling
- **Threshold Mapping:** Green, Red, Critical Capacity, Low Utilisation
- **Breach Component:** No breach zero, provisional breach scoring
- **Watch Severity:** Critical and informational extremes
- **Persistence:** Repeated amber, repeated red
- **Trend:** Deteriorating and improving directions
- **Confidence:** All levels, unavailable mapping, provisional restriction
- **Governance:** Provisional flagging, adjustment, review date propagation
- **Priority Tier:** Valid tiers, critical capacity trigger
- **Urgency:** Valid levels, critical capacity trigger
- **Evidence/Lineage:** Every record linked
- **Source Reconciliation:** 17,520 total, assessable + unavailable = total
- **Department Aggregation:** Count matching, score range, outlier preservation
- **Concurrence:** Multi-KPI flag and score
- **Dominant Driver:** Existence, score matching, provisional flagging
- **Ranking:** Deterministic, completeness, Not Assessable placement
- **Hospital Summary:** Tier sum, score matching, data availability
- **Immutability:** Upstream checksum verification
- **Provisional Materiality:** Green non-contributing, unavailable, minor, material, dominant, no-provisional scenarios

---

## 3. Performance Observation

| Observation | Detail |
|-------------|--------|
| Engine runtime | < 30 seconds |
| Test runtime | ~16 seconds for 60 tests |
| Design improvement over 2B-2 | Module-scoped fixtures avoid per-test engine re-execution |

---

## 4. Record Reconciliation

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| Total source KPI records | 17,520 | 17,520 | PASS |
| KPI risk records generated | 17,520 | 17,520 | PASS |
| Assessable KPI risk records | 11,397 | 11,397 | PASS |
| Unavailable / Not Assessable | 6,123 | 6,123 | PASS |
| Department-date risk records | 2,920 | 2,920 | PASS |
| Hospital-date summary records | 365 | 365 | PASS |
| Ranked department records | 2,920 | 2,920 | PASS |

---

## 5. Score Range Validation

| Dataset | Minimum | Maximum | In Range |
|---------|---------|---------|----------|
| KPI risk (assessable) | 0.0 | 100.0 | PASS |
| Department risk | 0.0 | 100.0 | PASS |

---

## 6. Component Reconciliation

All component scores sum correctly to the raw score (before confidence and governance adjustments).

Status: PASS

---

## 7. Tier and Urgency Validation

### KPI Tiers

| Tier | Count |
|------|-------|
| No Current Risk | 4,783 |
| Monitor | 4,161 |
| Attention Required | 828 |
| High Priority | 961 |
| Critical Priority | 664 |
| Not Assessable | 6,123 |

### KPI Urgency

| Urgency | Count |
|---------|-------|
| Routine Monitoring | 8,630 |
| Review Soon | 303 |
| Prompt Review | 1,342 |
| Immediate Review | 1,122 |
| Not Assessable | 6,123 |

### Department Tiers

| Tier | Count |
|------|-------|
| Stable | 417 |
| Monitor | 1,035 |
| Elevated | 642 |
| High | 566 |
| Critical | 260 |

### Department Urgency

| Urgency | Count |
|---------|-------|
| Routine Monitoring | 1,113 |
| Review Soon | 480 |
| Prompt Review | 522 |
| Immediate Review | 805 |

---

## 8. Confidence Validation

| Level | KPI Count | Department Count |
|-------|-----------|------------------|
| High | 9,183 | — |
| Moderate | 2,184 | — |
| Low | 30 | — |
| Insufficient Evidence | 6,123 | — |

---

## 9. Provisional Governance Validation (Refined)

| Check | Count | Status |
|-------|-------|--------|
| Provisional KPI risk records | 2,079 | PASS |
| Departments containing provisional KPIs | 2,920 | PASS |
| Departments with provisional risk flag = True (Material/Dominant) | 933 | PASS |
| Departments with provisional dominant drivers | 572 | PASS |
| Provisional contribution — None | 851 | PASS |
| Provisional contribution — Minor | 1,136 | PASS |
| Provisional contribution — Material | 361 | PASS |
| Provisional contribution — Dominant | 572 | PASS |
| Provisional governance preserved | Yes | PASS |
| Config-driven materiality thresholds applied | Yes | PASS |

---

## 10. Evidence and Lineage Validation

| Check | Count | Status |
|-------|-------|--------|
| KPI evidence linked | 17,520 / 17,520 | PASS |
| Department evidence linked | 2,920 / 2,920 | PASS |
| Lineage present for calculated | 11,397 / 11,397 | PASS |

---

## 11. Ranking Validation

| Check | Result | Status |
|-------|--------|--------|
| Deterministic ranking | Yes | PASS |
| Rank within hospital matches dept count | Yes | PASS |
| No cross-date leakage | Yes | PASS |
| Not Assessable does not outrank assessable | Yes | PASS |

---

## 12. Driver Validation

| Check | Result | Status |
|-------|--------|--------|
| Dominant driver exists for assessable departments | Yes | PASS |
| Dominant driver score matches max KPI score | Yes (sampled) | PASS |
| Provisional dominant drivers flagged | Yes | PASS |

---

## 13. Upstream Immutability

| Detail | Value |
|--------|-------|
| Files monitored | 12 |
| Modifications detected | 0 |
| Status | PASS |

---

## 14. Issue Log

No blocking issues.

Warnings:
- 572 departments have a provisional dominant driver
- 361 departments have a provisional material contribution
- 30 KPI records have Low confidence

Technical Debt:
- Step 2B-2 watch-conditions output incorrectly flagged all KPIs as provisional. Mitigated by overriding from `config/kpi_threshold_config.csv` in Step 2B-3. Recommend fixing upstream logic before next refresh.

---

## 15. Closure Statement

Step 2B-3 is **COMPLETE**. All required analytical outputs, validation outputs, tests, and documentation have been produced and verified. A focused governance refinement has been applied to distinguish provisional KPI presence from provisional risk materiality at the department level. No defects remain.

**Step 2B-4 Readiness:** Ready with Conditions
