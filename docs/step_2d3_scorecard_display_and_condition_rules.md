# Step 2D-3 Scorecard Display and Condition Rules

## Display Level Mapping

### Operational Risk to Display

| Risk Tier | Display Level |
|---|---|
| Critical | Blocking |
| High | Limited |
| Elevated | Conditional |
| Moderate | Adequate |
| Low | Strong |
| Monitoring | Limited |
| Not Assessable | Not Assessable |

### Evidence/Lineage to Display

| Status | Display Level |
|---|---|
| Complete | Strong |
| Complete with Conditions | Adequate |
| Partial | Conditional |
| Limited | Limited |
| Not Available | Not Assessable |

### Readiness to Display

| Readiness | Display Level |
|---|---|
| Ready with Conditions | Conditional |
| Monitoring Only | Limited |
| Requires Assumption Validation | Blocking |
| Non-Quantitative | Not Assessable |
| Ready for Integrated Management Review | Strong |
| Requires Baseline Validation | Blocking |
| Requires Financial Input | Blocking |
| Requires Stakeholder Validation | Blocking |
| Requires Additional Scenario Analysis | Blocking |
| Not Suitable for Decision Use | Not Applicable |
| Rejected | Not Applicable |

## Condition Flag Rules

| Flag Name | Source Field | Active When | Severity |
|---|---|---|---|
| provisional_threshold_condition | provisional_threshold_flag | True | Moderate |
| contradiction_condition | contradiction_warning | True | High |
| assumption_validation_condition | assumption_validation_required | True | High |
| baseline_validation_condition | baseline_validation_required | True | Moderate |
| financial_input_condition | missing_financial_input_flag | True | Moderate |
| stakeholder_validation_condition | stakeholder_validation_required | True | Moderate |
| scenario_completeness_condition | scenario_readiness | Not Ready / Requires Validation | Moderate |
| evidence_completeness_condition | evidence_completeness | False | Low |
| lineage_completeness_condition | lineage_completeness | False | Low |
| uncertainty_condition | uncertainty_available | False | Low |
| monitoring_condition | package_readiness | Monitoring Only | Low |
| non_quantitative_condition | package_readiness | Non-Quantitative | Low |
| blocking_condition | governance_burden_status | High / Blocking | High |

## Governance Constraints

- No condition may be hidden inside narrative text only.
- Every active condition must have a required action and responsible role.
- No condition may trigger automatic scenario selection.
