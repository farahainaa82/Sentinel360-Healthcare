# Phase 2D-1 Evidence and Lineage Specification

**Date:** 2026-07-29

---

## 1. Evidence Integration

Every integrated decision record links to evidence from all upstream phases.

### 1.1 Evidence Types Tracked

| Type | Source Phase | Presence Condition |
|------|-------------|-------------------|
| KPI evidence | 2A / 2B | Risk ranking data available |
| Risk evidence | 2B | Risk score present and non-zero |
| Recommendation evidence | 2C-1 | Representative recommendation present |
| Scenario evidence | 2C-2 | Management scenario package present |
| Financial evidence | 2C-3 | Financial readiness data present |
| Governance evidence | 2C-2F | Closure category present |

### 1.2 Evidence Completeness Score

`evidence_completeness_score = evidence_count / 5.0`

Max score = 1.0 when all 5 evidence types are present.

## 2. Lineage Stages

| Stage | Source | Condition |
|-------|--------|-----------|
| Raw data | Phase 1 Data Foundation | Always |
| Processed data | Phase 1 Data Processing | Always |
| KPI calculation | Phase 2A KPI Analytics | Always |
| Trend and threshold | Phase 2B Early Warning | Always |
| Risk prioritisation | Phase 2B Risk Intelligence | Always |
| Recommendation | Phase 2C-1 Recommendations | Always |
| Scenario modelling | Phase 2C-2 Scenario Modelling | If scenario package exists |
| Financial analysis | Phase 2C-3 Financial Impact | If financial data exists |
| Integrated decision record | Phase 2D-1 | Always |

### 2.1 Lineage Completeness Score

`lineage_completeness_score = actual_stages / 9`

## 3. Orphan Prevention

- Every integrated decision record must have at least one evidence source.
- Every integrated decision record must have a complete lineage chain back to raw data.
- No record may exist without an approval_package_id.
- No record may exist without an episode_id.

## 4. Verification

- 646 evidence records created (one per decision record)
- 646 lineage records created (one per decision record)
- Zero orphan records confirmed

---

*End of Evidence and Lineage Specification*
