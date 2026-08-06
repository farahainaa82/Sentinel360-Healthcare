# Step 2D-2 Management Action Rules

## Permitted Actions

The following 11 management actions are permitted in every decision package:

1. Review Integrated Decision Package
2. Compare Scenario Options
3. Validate Assumptions
4. Validate Baseline
5. Validate Financial Inputs
6. Request Additional Scenario
7. Request Stakeholder Review
8. Proceed to Limited-Trial Consideration
9. Continue Monitoring
10. Defer Decision
11. Reject Decision Use

## Action Attributes

Each action record contains:
- management_action_id
- action_name
- action_allowed (boolean)
- action_reason
- prerequisite
- blocking_condition
- audit_required
- action_selected (always False)

## Status-Specific Allowance Adjustments

| Action | Adjustment Rule |
|---|---|
| Proceed to Limited-Trial Consideration | Allowed only when package readiness is "Package Ready with Conditions" |
| Continue Monitoring | Always allowed; default for Monitoring Only |
| Reject Decision Use | Always allowed; intended for Not Suitable packages |

## Governance Constraints

- No action may be pre-selected.
- All actions that proceed beyond review require audit logging.
- Blocking conditions must be documented for restricted actions.
