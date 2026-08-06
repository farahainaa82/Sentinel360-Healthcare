# Prerequisite and Blocking Rules

## Prerequisite Model

Prerequisites are created for actions that require conditions before they can proceed. Required fields:

- action_prerequisite_id
- decision_action_routing_id
- action_id
- prerequisite_type
- prerequisite_description
- mandatory_flag
- blocking_flag
- responsible_role
- evidence_required
- current_status
- completion_required_before_action

### Allowed current_status Values

- Pending
- Deferred
- Not Applicable

### Rule: No Prerequisite Marked Completed

No prerequisite may be marked as Completed. All prerequisites remain in Pending status until management acts.

## Blocking Model

Blocking records are created explicitly for every Blocked or Not Permitted action. Required fields:

- action_block_id
- decision_action_routing_id
- action_id
- blocking_condition_id
- blocking_reason
- blocking_severity
- source_phase
- source_record_id
- resolution_required
- responsible_role
- current_status

### Allowed current_status Values

- Active
- Deferred
- Not Applicable

### Rule: No Blocking Condition Marked Resolved

No blocking condition may be marked as Resolved. All blocks remain Active until management acts.

## Blocking Severity Levels

- **Critical** — Mandatory gate failure, prevents action progression
- **Informational** — Action not applicable, not a true block

## Source References

All blocking records must retain:
- source_phase (e.g., "2D-4")
- source_record_id linking to original gate or condition
