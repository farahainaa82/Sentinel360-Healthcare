# Role and Queue Routing Specification

## Governed Roles

The following roles are permitted for assignment. No named individuals may be assigned.

- Hospital COO / General Manager
- Medical Director
- Department Head
- Operations Manager
- Finance
- Human Resources
- Data Owner
- Analytics Team
- Clinical Lead
- Facilities / Maintenance
- Stakeholder Owner
- Governance / Audit Reviewer

## Role Assignment by Action Type

| Action | Primary Role | Secondary Role |
|---|---|---|
| Review Integrated Decision Package | Hospital COO / General Manager | Medical Director |
| Compare Scenario Options | Analytics Team | Medical Director |
| Validate Assumptions | Analytics Team | Stakeholder Owner |
| Validate Baseline | Data Owner | Department Head |
| Validate Financial Inputs | Finance | |
| Validate Benefit Assumptions | Finance | Analytics Team |
| Provide Budget Information | Finance | |
| Request Additional Scenario | Analytics Team | |
| Request Stakeholder Review | Stakeholder Owner | Department Head |
| Proceed to Limited-Trial Consideration | Hospital COO / General Manager | Medical Director |
| Continue Monitoring | Operations Manager | Department Head |
| Escalate for Immediate Management Attention | Hospital COO / General Manager | |
| Defer Decision | Hospital COO / General Manager | |
| Reject Decision Use | Hospital COO / General Manager | Governance / Audit Reviewer |
| Request Evidence Completion | Data Owner | |
| Request Lineage Completion | Data Owner | |
| Route to Non-Quantitative Review | Clinical Lead | |

## Primary Queues

| Readiness Status | Primary Queue |
|---|---|
| Ready for Integrated Management Review | Integrated Management Review Queue |
| Ready with Conditions | Conditional Review Queue |
| Requires Assumption Validation | Assumption Validation Queue |
| Requires Baseline Validation | Baseline Validation Queue |
| Requires Financial Input | Financial Input Queue |
| Requires Benefit Validation | Benefit Validation Queue |
| Requires Budget Data | Budget Information Queue |
| Requires Stakeholder Validation | Stakeholder Validation Queue |
| Requires Additional Scenario Analysis | Additional Scenario Queue |
| Requires Evidence Completion | Evidence Completion Queue |
| Requires Lineage Completion | Lineage Completion Queue |
| Monitoring Only | Monitoring Queue |
| Non-Quantitative | Non-Quantitative Review Queue |
| Not Suitable for Decision Use | Not Suitable Register |
| Rejected | Rejected Register |

## Queue Status

All queue assignments default to "Pending Routing" unless a prior governed source confirms actual routing.
