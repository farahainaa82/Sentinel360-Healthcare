# Filter, Selector, and Navigation Specification

## Filters

| Filter | Type | Default | Multi-Select | Dependency |
|---|---|---|---|---|
| Hospital | multi-select | All | Yes | None |
| Department | multi-select | All | Yes | Hospital |
| Year | single-select | 2026 | No | None |
| Month | single-select | All | No | Year |
| KPI | multi-select | All | Yes | None |
| Risk Tier | multi-select | All | Yes | None |
| Urgency | multi-select | All | Yes | None |
| Readiness | multi-select | All | Yes | None |
| Management Attention | multi-select | All | Yes | None |
| Primary Queue | multi-select | All | Yes | None |
| Evidence Status | multi-select | All | Yes | None |
| Lineage Status | multi-select | All | Yes | None |
| Scenario Availability | multi-select | All | Yes | None |
| Financial Readiness | multi-select | All | Yes | None |
| Validation Outcome | multi-select | All | Yes | None |
| Approval Status | multi-select | All | Yes | None |

## Navigation

12 navigation items map 1:1 to pages. Drill-down targets:
- Executive Overview -> Integrated Decision
- KPI Dashboard -> Risk and Alerts
- Risk and Alerts -> Integrated Decision
- Recommendation -> Integrated Decision
- Scenario Lab -> Integrated Decision
- Financial Impact -> Integrated Decision
- Management Review -> Integrated Decision
- Audit -> Integrated Decision

## Empty Result Behavior

All filters reset to default `All` value when no results match.
