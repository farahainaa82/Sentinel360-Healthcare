# Action Catalogue and Eligibility Rules

## Governed Action Catalogue

The following 18 management actions are permitted in the system:

| ID | Action Name | Category |
|---|---|---|
| A001 | Review Integrated Decision Package | Management Review |
| A002 | Compare Scenario Options | Analytical Review |
| A003 | Validate Assumptions | Validation |
| A004 | Validate Baseline | Validation |
| A005 | Validate Financial Inputs | Financial Review |
| A006 | Validate Benefit Assumptions | Financial Review |
| A007 | Provide Budget Information | Financial Review |
| A008 | Request Additional Scenario | Analytical Review |
| A009 | Request Stakeholder Review | Stakeholder Engagement |
| A010 | Proceed to Limited-Trial Consideration | Management Decision |
| A011 | Continue Monitoring | Monitoring |
| A012 | Escalate for Immediate Management Attention | Escalation |
| A013 | Defer Decision | Management Decision |
| A014 | Reject Decision Use | Management Decision |
| A015 | Request Evidence Completion | Evidence |
| A016 | Request Lineage Completion | Evidence |
| A017 | Route to Non-Quantitative Review | Special Review |
| A018 | No Action - Monitoring Continues | Monitoring |

## Prohibited Actions

The following actions are explicitly prohibited and must never appear:

- Approve Scenario
- Approve Recommendation
- Approve Budget
- Implement Intervention
- Select Best Scenario
- Accept AI Recommendation

## Eligibility States

Every action-package combination receives exactly one of:

- **Allowed** — Action may be considered by management
- **Allowed with Conditions** — Action permitted but prerequisites apply
- **Blocked** — Action cannot proceed due to blocking conditions
- **Not Applicable** — Action does not apply to this readiness state
- **Not Permitted** — Action is explicitly not permitted for this state

## Key Rules by Status

- **Ready for Integrated Management Review**: Review Integrated Decision Package Allowed; Limited-Trial Allowed with Conditions
- **Ready with Conditions**: Review Allowed; Validation actions Allowed; Limited-Trial Blocked if mandatory gates failed
- **Monitoring Only**: Continue Monitoring Allowed; progression actions Blocked or Not Applicable
- **Non-Quantitative**: Route to Non-Quantitative Review Allowed; quantitative comparisons Blocked
- **Rejected**: Only Reject Decision Use Allowed; all others Not Permitted
