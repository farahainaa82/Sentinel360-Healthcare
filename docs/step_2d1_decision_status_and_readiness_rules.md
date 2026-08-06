# Phase 2D-1 Decision Status and Readiness Rules

**Date:** 2026-07-29

---

## 1. Decision Status Categories

Every approval package receives exactly one of the following statuses:

| Status | Count | Rule |
|--------|-------|------|
| Ready for Integrated Management Review | 0 | Strict: all analysis complete, comparator consistency verified, no governance issues |
| Ready with Conditions | 311 | Core analysis available, one or more conditions remain |
| Requires Assumption Validation | 46 | Assumption-related closure category |
| Requires Baseline Validation | 0 | Baseline-related closure category |
| Requires Financial Input | 0 | Financial readiness not confirmed |
| Requires Stakeholder Validation | 0 | Explicit stakeholder validation flag |
| Requires Additional Scenario Analysis | 0 | No management scenario package available |
| Monitoring Only | 280 | Monitoring closure category |
| Non-Quantitative | 9 | Non-quantitative closure category |
| Not Suitable for Decision Use | 0 | Explicitly excluded |
| Rejected | 0 | Explicitly rejected |

**Total:** 646 packages, 646 statuses assigned.

## 2. Status Assignment Hierarchy

1. Rejected / Not Suitable — highest priority exclusion
2. Monitoring Only — passive observation
3. Non-Quantitative — narrative only
4. Requires Assumption Validation — upstream assumption issue
5. Requires Baseline Validation — upstream baseline issue
6. Requires Financial Input — incomplete financial analysis
7. Requires Stakeholder Validation — pending stakeholder review
8. Requires Additional Scenario Analysis — missing scenario package
9. Ready for Integrated Management Review — strict full readiness
10. Ready with Conditions — default for packages with partial analysis

## 3. Readiness Scoring

Readiness is scored from 0.0 to 1.0 across six dimensions:

| Dimension | Weight | Criterion |
|-----------|--------|-----------|
| Risk evidence | 0.20 | risk_score present and non-zero |
| Recommendation evidence | 0.15 | representative_recommendation present |
| Scenario evidence | 0.20 | management_scenario_package_id present |
| Financial evidence | 0.20 | financial_readiness present |
| Governance clean | 0.15 | governance_issue_count == 0 |
| Comparator completeness | 0.10 | comparator_completeness == "Complete" |

**Readiness categories:**
- Fully Ready: score >= 0.90 AND status == "Ready for Integrated Management Review"
- Substantially Ready: score >= 0.70
- Partially Ready: score >= 0.50
- Limited Readiness: score >= 0.30
- Not Ready: score < 0.30

## 4. Conditions Tracking

Each package lists remaining conditions:
- Unresolved governance issues
- Scenario package not yet available
- Financial analysis incomplete
- Comparator completeness not confirmed
- Financial inputs remain draft

---

*End of Decision Status and Readiness Rules*
