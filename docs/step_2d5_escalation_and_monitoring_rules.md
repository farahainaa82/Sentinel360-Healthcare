# Escalation and Monitoring Rules

## Escalation Routing Principles

1. **Operational escalation remains separate from analytical readiness**
2. High operational risk may require escalation even when analytical readiness is blocked
3. Escalation does not override or downgrade readiness status

## Escalation Statuses

- Immediate Management Attention
- Priority Review
- Standard Review
- Monitoring
- No Escalation
- Not Assessable

## Timeframe Categories

- Immediate
- Urgent
- Priority
- Routine
- Monitoring
- Not Applicable

## Escalation by Readiness Status

| Readiness Status | Default Escalation | Timeframe |
|---|---|---|
| Ready for Integrated Management Review | Standard Review | Routine |
| Ready with Conditions | Priority Review | Priority |
| Requires Assumption Validation | Standard Review | Routine |
| Monitoring Only | Monitoring | Monitoring |
| Non-Quantitative | Standard Review | Routine |
| Rejected | No Escalation | Not Applicable |

## Monitoring Action Model

Required fields:
- monitoring_action_id
- decision_action_routing_id
- monitoring_required
- monitoring_kpi
- monitoring_frequency
- trigger_condition
- escalation_condition
- reassessment_condition
- responsible_role
- reporting_requirement
- current_status

### Allowed current_status Values

- Pending Setup
- Active Monitoring Route
- Deferred
- Not Applicable

### Prototype Default

All monitoring actions default to "Pending Setup" unless an existing source explicitly confirms active monitoring.
