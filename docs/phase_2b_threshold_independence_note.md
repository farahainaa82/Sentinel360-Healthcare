# Phase 2B Threshold Independence Note

**Date:** 2026-07-27  
**Step:** 2B-1 — Trend and Statistical-Signal Architecture  
**Status:** Draft / Provisional

---

## 1. Why Trend Analysis Can Proceed Without Approved Thresholds

Performance thresholds (Green, Amber, Red) require stakeholder approval of boundary values. Until that approval is obtained, threshold-breach logic cannot produce governed operational classifications.

However, statistical trend analysis does not require approved thresholds. It relies on:
- Historical data patterns
- Mathematical deviations (z-score, MAD)
- Period-over-period changes
- Rolling averages and volatility
- Sustained directional movement
- Trend slopes

These methods are purely analytical and describe data behaviour without asserting performance quality.

---

## 2. Statistical vs Operational Classifications

### Statistical Outputs (Created in Step 2B-1)
- Mathematical trend direction (Increasing, Decreasing, Stable)
- Z-score and MAD deviations
- Volatility changes
- Sustained movement sequences
- Trend slopes

These are **descriptive** and do not imply good or bad performance.

### Operational Classifications (Not Created in Step 2B-1)
- Green, Amber, Red thresholds
- Threshold-breach alerts
- Final early-warning scores
- Management recommendations

These require **approved thresholds** and are deferred until stakeholder governance is complete.

---

## 3. Phase 2B Functions That Remain Disabled

The following functions are intentionally not implemented in Step 2B-1:

- Threshold-breach detection
- Green/Amber/Red assignment
- Final risk scoring
- Automated alert generation
- Management recommendation engine
- Financial impact calculation
- Scenario modelling

---

## 4. Conditions Required Before Threshold-Breach Logic Begins

Before Step 2B can transition to threshold-dependent outputs, the following must occur:

1. Stakeholder approval of KPI threshold boundaries
2. Promotion of threshold configuration from Draft to Approved
3. Validation that approved thresholds do not conflict with historical data
4. Governance sign-off on alert rules and escalation paths
5. Configuration version update from v1.0-draft to approved version

---

## 5. Current Provisional Elements

| Element | Status | Version |
|---------|--------|---------|
| Trend analysis rules | Draft | v1.0-draft |
| Statistical signal sensitivity | Draft | v1.0-draft |
| Trend confidence thresholds | Draft | v1.0-draft |
| Business movement interpretation | Provisional | — |
| Threshold configuration | Draft | v1.0-draft |

---

## 6. Allowed Activities During Threshold Independence

Phase 2B may proceed with:
- Period-over-period comparisons
- Trend direction analysis
- Statistical deviation detection
- Volatility monitoring
- Sustained movement identification
- Signal candidate generation
- Evidence and lineage capture

These activities produce analytical value and prepare the foundation for future threshold-dependent alerting.
