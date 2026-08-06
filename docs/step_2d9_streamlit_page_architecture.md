# Streamlit Page Architecture

## Pages Defined

| Page ID | Page Name | Priority | Primary User |
|---|---|---|---|
| PAGE-01 | Data Upload and Validation | Priority 1 | Data Steward |
| PAGE-02 | Executive Overview | Priority 1 | Executive |
| PAGE-03 | KPI Dashboard | Priority 1 | Operational Manager |
| PAGE-04 | Risk and Alerts | Priority 1 | Risk Manager |
| PAGE-05 | Recommendation Summary | Priority 2 | Department Head |
| PAGE-06 | Scenario Lab | Priority 2 | Analyst |
| PAGE-07 | Financial Impact | Priority 2 | CFO |
| PAGE-08 | Integrated Decision | Priority 1 | Executive |
| PAGE-09 | Management Review and Actions | Priority 2 | Management Reviewer |
| PAGE-10 | Reports and Export | Priority 3 | Analyst |
| PAGE-11 | Audit and Traceability | Priority 3 | Auditor |
| PAGE-12 | Configuration and Governance | Priority 4 | System Administrator |

## Governance Rules

- No page preselects a scenario.
- No page preselects an action.
- No page displays a recommendation as approved.
- No page shows guaranteed savings.
- All pages include the management boundary disclaimer.
- User-adjusted assumptions are clearly labeled as simulation inputs.
