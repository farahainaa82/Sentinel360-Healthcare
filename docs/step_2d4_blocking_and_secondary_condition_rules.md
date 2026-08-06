# Step 2D-4 Blocking and Secondary Condition Rules

## Blocking Conditions

Blocking conditions represent active issues that prevent readiness advancement. Each blocking condition record contains:

- blocking_condition_id
- decision_readiness_id
- condition_type
- condition_category
- condition_description
- severity
- blocking_flag
- source_phase
- source_record_id
- responsible_role
- required_resolution
- resolution_evidence_required
- current_status
- transition_enabled_after_resolution

## Allowed Current Status

- Pending
- Deferred
- Not Applicable

Do not mark conditions as resolved in this step.

## Condition Types

| Condition Type | Category | Typical Severity |
|----------------|----------|------------------|
| assumption_validation_condition | Blocking | High |
| baseline_validation_condition | Blocking | High |
| financial_input_condition | Blocking | Moderate |
| stakeholder_validation_condition | Blocking | Moderate |
| scenario_completeness_condition | Blocking | Moderate |
| evidence_completeness_condition | Blocking | High |
| lineage_completeness_condition | Blocking | High |
| blocking_condition | Blocking | High |

## Secondary Conditions

Secondary non-blocking conditions remain visible after final status assignment:

- provisional_threshold_condition
- contradiction_condition
- uncertainty_condition
- monitoring_condition
- non_quantitative_condition

## Rules

- Create one condition record per condition
- Do not hide secondary conditions after final status assignment
- All pending confirmations remain pending
- No condition is marked resolved
- Blocking conditions retain source references
