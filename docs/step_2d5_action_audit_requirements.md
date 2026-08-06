# Action Audit Requirements

## Audit-Required Actions

The following actions require audit records:

- Review Integrated Decision Package
- Compare Scenario Options
- Validate Assumptions
- Validate Baseline
- Validate Financial Inputs
- Validate Benefit Assumptions
- Provide Budget Information
- Request Additional Scenario
- Request Stakeholder Review
- Proceed to Limited-Trial Consideration
- Defer Decision
- Reject Decision Use

## Non-Audit Actions

The following actions do not require audit records:

- Continue Monitoring
- No Action - Monitoring Continues

## Audit Fields

- audit_required (boolean)
- audit_event_type (e.g., "Decision Package Review")
- required_actor_role (governed role)
- evidence_attachment_required (boolean)
- reason_required (boolean)
- timestamp_required (boolean)
- approval_reference_required (boolean)
- future_audit_status (always "Awaiting Management Action")

## Governance Rule: No Completed Audit Events

No audit record may be created with status "Completed". All audit requirements remain in "Awaiting Management Action" status until management acts.
