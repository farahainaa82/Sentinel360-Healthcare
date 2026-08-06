# Step 2D-4 Transition and Queue Specification

## Transition Rules

Transition rules show how a package may move between readiness states. Rules are created only; no transitions are executed in Step 2D-4.

### Defined Transitions

| Current State | Eligible Next State | Requirements |
|---------------|---------------------|--------------|
| Requires Assumption Validation | Ready with Conditions | Required assumptions validated |
| Requires Baseline Validation | Ready with Conditions | Baseline validation passes |
| Requires Financial Input | Ready with Conditions | Mandatory financial inputs provided and validated |
| Requires Budget Data | Ready with Conditions | Authoritative budget data supplied |
| Ready with Conditions | Ready for Integrated Management Review | All blocking conditions resolved and confirmations completed |
| Monitoring Only | Ready with Conditions | Escalation trigger met and valid intervention package available |
| Non-Quantitative | Ready with Conditions | Sufficient governed quantitative data become available |
| Requires Evidence Completion | Ready with Conditions | Required evidence references provided |
| Requires Lineage Completion | Ready with Conditions | Source-to-decision lineage completed |
| Requires Stakeholder Validation | Ready with Conditions | Stakeholder confirmation received |
| Requires Benefit Validation | Ready with Conditions | Benefit eligibility resolved |
| Requires Additional Scenario Analysis | Ready with Conditions | Additional modelling completed |

### Transition Record Fields

- transition_rule_id
- decision_readiness_id
- current_state
- eligible_next_state
- transition_requirements
- transition_not_executed_flag (always True in 2D-4)
- transition_executed (always False in 2D-4)
- governance_note

## Queue Mapping

Every readiness record maps to exactly one primary queue:

| Final Readiness Status | Primary Queue |
|------------------------|---------------|
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

## Governance

- Exactly one primary queue per record
- Secondary queues may be retained where multiple follow-ups exist
- Queue mapping is configuration-driven
