# Step 2D-2 Monitoring Requirements Specification

## Generation Rules

1. Monitoring requirements are generated for packages with statuses:
   - Monitoring Only
   - Ready with Conditions
   - Requires Assumption Validation
2. Monitoring is not generated for Non-Quantitative packages unless explicitly required.
3. No exact future dates are invented.

## Monitoring Frequency by Status

| Package Status | Monitoring Frequency |
|---|---|
| Monitoring Only | Weekly |
| Requires Assumption Validation | Bi-weekly |
| Ready with Conditions | Monthly |

## Monitoring Record Fields

- monitoring_id
- decision_package_id
- approval_package_id
- monitoring_required
- monitoring_frequency
- monitoring_kpi
- trigger_condition
- escalation_condition
- responsible_role
- reassessment_condition
- next_review_requirement

## Trigger and Escalation Conditions

- Trigger: KPI threshold breach or trend deterioration
- Escalation: Repeated breach or risk tier increase
- Reassessment: Status change or new evidence

## Governance Constraints

- Exact calendar dates are not invented.
- Review schedules are expressed as relative frequencies.
- Responsible roles are assigned from existing governance roles.
