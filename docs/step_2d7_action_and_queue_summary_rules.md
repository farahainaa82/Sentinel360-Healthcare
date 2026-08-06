# Action and Queue Summary Rules

## Overview

Each brief summarises the permitted management actions, blocked actions, responsible roles, queues, and escalation requirements. No action is selected or recommended.

## Action Summary Rules

### Permitted Actions
- **Primary permitted action**: The action with highest routing priority. Displayed as "Primary permitted action", not "Recommended action".
- **Secondary permitted actions**: Additional permitted actions with lower priority.
- **Blocked actions**: Actions that are blocked, with reason summary.

### Prohibited Terminology
- Do not use: "recommended action", "best action", "AI-selected action".
- Use: "primary permitted action", "routing priority", "management selection required".

### Selection State
- `selected_action` field is always blank.
- `selected_scenario` field is always blank.
- No action is marked as chosen.

## Queue Summary Rules

Each brief maps to one primary queue based on `final_readiness_status`:

| Readiness Status | Primary Queue |
|---|---|
| Ready for Integrated Management Review | Integrated Management Review Queue |
| Ready with Conditions | Conditional Review Queue |
| Requires Assumption Validation | Assumption Validation Queue |
| Requires Baseline Validation | Baseline Validation Queue |
| Requires Financial Input | Financial Input Queue |
| Requires Benefit Validation | Benefit Validation Queue |
| Requires Budget Information | Budget Information Queue |
| Requires Stakeholder Validation | Stakeholder Validation Queue |
| Requires Additional Scenario | Additional Scenario Queue |
| Requires Evidence Completion | Evidence Completion Queue |
| Requires Lineage Completion | Lineage Completion Queue |
| Monitoring Only | Monitoring Queue |
| Non-Quantitative | Non-Quantitative Review Queue |
| Not Suitable | Not Suitable Register |
| Rejected | Rejected Register |

## Output

- `step_2d7_management_action_summary_register.csv` (646 rows)
- `step_2d7_management_queue_brief_register.csv` (646 rows)
