# Step 2D-4 Role and Escalation Rules

## Responsible Roles

Governed roles used for assignment:

| Role | Typical Assignment |
|------|-------------------|
| Hospital COO / General Manager | Ready for Integrated Management Review, Rejected |
| Medical Director | Not Suitable for Decision Use |
| Department Head | Ready with Conditions |
| Operations Manager | Default / Monitoring Only |
| Finance | Financial-related statuses |
| Human Resources | Workforce matters |
| Data Owner | Evidence/Lineage completion |
| Analytics Team | Assumption/Scenario validation |
| Clinical Lead | Non-Quantitative |
| Facilities / Maintenance | Infrastructure |
| Stakeholder Owner | Stakeholder validation |

## Role Assignment Rules

- Assign roles based on the blocking condition
- Do not invent named individuals
- Use governed role names only
- Each readiness record has one primary responsible role

## Escalation Rules

Escalation is based on existing risk tier and urgency from Step 2D-3:

| Risk Tier | Urgency | Escalation Status | Attention Required |
|-----------|---------|-------------------|-------------------|
| High | Any | Immediate Management Attention | Yes |
| Moderate | High | Priority Review | Yes |
| Moderate | Moderate | Standard Review | No |
| Low | Moderate | Standard Review | No |
| Low | Low | Monitoring | No |
| Not Assessable | Any | Not Assessable | No |

## Key Principle

Operational escalation remains separate from analytical readiness. High operational risk may require immediate management attention even when readiness is blocked. Do not downgrade urgency because the package requires validation.
