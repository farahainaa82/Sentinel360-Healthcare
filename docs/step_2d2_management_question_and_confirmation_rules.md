# Step 2D-2 Management Question and Confirmation Rules

## Management Questions

### Generation Rules

1. Questions are generated per package based on `decision_status`.
2. Every question must have a `source_reference` pointing to Step 2D-1.
3. Blocking questions must have `mandatory_flag = True`.
4. Non-blocking questions may be optional.
5. Irrelevant questions are not generated.

### Status-Specific Question Selection

| Decision Status | Generated Question Categories |
|---|---|
| Ready with Conditions | Risk Validation, Trade-off Assessment (mandatory) |
| Monitoring Only | Risk Validation, Monitoring Assessment |
| Requires Assumption Validation | Assumption Validation, Baseline Validation, Scenario Validation, Financial Validation |
| Non-Quantitative | Risk Validation, Stakeholder Engagement |

### Question Categories

- Risk Validation
- Assumption Validation
- Baseline Validation
- Scenario Validation
- Financial Validation
- Trade-off Assessment
- Trial Assessment
- Monitoring Assessment
- Stakeholder Engagement

## Required Confirmations

### Generation Rules

1. Confirmations are generated per package based on `decision_status`.
2. No confirmation is ever marked as "Completed".
3. Allowed statuses: Pending, Not Required, Deferred.
4. Each confirmation specifies the responsible role and required evidence.

### Status-Specific Confirmation Selection

| Decision Status | Generated Confirmations |
|---|---|
| Ready with Conditions | Risk Acknowledgement, Assumption Acceptance, Governance Review |
| Monitoring Only | Risk Acknowledgement |
| Requires Assumption Validation | Assumption Acceptance, Financial Validation |
| Non-Quantitative | Stakeholder Alignment |

### Confirmation Types

- Risk Acknowledgement
- Assumption Acceptance
- Financial Validation
- Stakeholder Alignment
- Governance Review

## Governance Constraints

- No fabricated management responses.
- No confirmation may be pre-completed.
- All blocking confirmations must be resolved before any action can proceed.
