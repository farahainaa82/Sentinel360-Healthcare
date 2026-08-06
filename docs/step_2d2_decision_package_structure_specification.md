# Step 2D-2 Decision Package Structure Specification

## Package Identity (Section A)

| Field | Source | Notes |
|---|---|---|
| decision_package_id | Derived | `DPKG-` + approval_package_id |
| integrated_decision_id | 2D-1 integrated_decision_register | |
| approval_package_id | 2D-1 integrated_decision_register | Anchor key |
| episode_id | 2D-1 | |
| hospital_id | 2D-1 | |
| hospital_name | 2D-1 | |
| department_id | 2D-1 | |
| department_name | 2D-1 | |
| reporting_date | 2D-1 | |
| dominant_kpi_id | 2D-1 | |
| dominant_kpi_name | 2D-1 | |
| scenario_family | 2D-1 | |
| package_version | Static | "1.0" |
| package_status | 2D-1 decision_status | |
| approval_status | Static | "Pending Management Review" |

## Executive Issue Summary (Section B)

| Field | Source | Notes |
|---|---|---|
| issue_title | 2D-1 | |
| issue_summary | 2D-1 | |
| what_is_happening | 2D-1 | |
| why_it_matters | 2D-1 | |
| current_operational_risk | 2D-1 | |
| urgency | 2D-1 | |
| priority_tier | 2D-1 | |
| current_status | 2D-1 | |
| management_attention_reason | 2D-1 | |

## KPI and Risk Evidence (Section C)

| Field | Source | Notes |
|---|---|---|
| current_kpi_value | 2D-1 | |
| threshold_status | 2D-1 | |
| breach_status | 2D-1 | |
| watch_status | 2D-1 | |
| trend_direction | 2D-1 | |
| sustained_movement_flag | 2D-1 | |
| risk_score | 2D-1 | |
| risk_tier | 2D-1 | |
| dominant_breach_type | 2D-1 | |
| contributing_factor_summary | 2D-1 | |
| contradiction_severity | 2D-1 | |
| provisional_threshold_flag | 2D-1 | |
| operational_evidence_summary | 2D-1 | |

## Recommendation Options (Section D)

| Field | Source | Notes |
|---|---|---|
| representative_recommendation | 2D-1 | |
| recommendation_type | 2D-1 | |
| recommendation_horizon | 2D-1 | |
| immediate_action | 2D-1 | |
| near_term_action | 2D-1 | |
| preventive_action | 2D-1 | |
| recommendation_validation_status | 2D-1 | |
| recommendation_confirmation_required | 2D-1 | |
| recommendation_limitations | 2D-1 | |
| recommendation_governance_warning | 2D-1 | |

## Scenario Options (Section E)

| Field | Source | Notes |
|---|---|---|
| scenario_required_status | 2D-1 | |
| scenario_readiness | 2D-1 | |
| baseline_available | 2D-1 | |
| conservative_available | 2D-1 | |
| expected_available | 2D-1 | |
| higher_intensity_available | 2D-1 | |
| baseline_summary | 2D-1 | |
| conservative_summary | 2D-1 | |
| expected_summary | 2D-1 | |
| higher_intensity_summary | 2D-1 | |
| comparator_completeness | 2D-1 | |
| comparator_consistency | 2D-1 | |
| scenario_validation_status | 2D-1 | |
| scenario_confidence | 2D-1 | |

## KPI Impact and Trade-offs (Section F)

| Field | Source | Notes |
|---|---|---|
| primary_kpi_effect_summary | 2D-1 | |
| supporting_kpi_effect_summary | 2D-1 | |
| tradeoff_summary | 2D-1 | |
| displacement_summary | 2D-1 | |
| sensitivity_summary | 2D-1 | |
| dominance_summary | 2D-1 | |
| diminishing_return_summary | 2D-1 | |
| scenario_limitations | 2D-1 | |
| scenario_governance_warning | 2D-1 | |

## Financial Impact (Section G)

| Field | Source | Notes |
|---|---|---|
| financial_review_required | 2D-1 | |
| financial_readiness | 2D-1 | |
| cost_completeness | 2D-1 | |
| estimated_scenario_cost | 2D-1 | |
| estimated_financial_benefit | 2D-1 | |
| estimated_net_financial_impact | 2D-1 | |
| roi_status | 2D-1 | |
| payback_status | 2D-1 | |
| affordability_status | 2D-1 | |
| lower_financial_estimate | 2D-1 | |
| central_financial_estimate | 2D-1 | |
| upper_financial_estimate | 2D-1 | |
| financial_confidence | 2D-1 | |
| missing_financial_input_flag | 2D-1 | |
| financial_limitations | 2D-1 | |
| financial_governance_warning | 2D-1 | |

## Governance and Limitations (Section H)

| Field | Source | Notes |
|---|---|---|
| causality_status | Static | "Not Confirmed" |
| contradiction_warning | 2D-1 | |
| provisional_warning | 2D-1 | |
| stakeholder_validation_required | 2D-1 | |
| assumption_validation_required | 2D-1 | |
| baseline_validation_required | 2D-1 | |
| financial_validation_required | 2D-1 | |
| evidence_completeness | 2D-1 | |
| lineage_completeness | 2D-1 | |
| governance_issue_count | 2D-1 | |
| package_limitations | 2D-1 | |

## Management Questions (Section I)

Each question contains:
- management_question_id
- question_text
- question_category
- required_response_type
- mandatory_flag
- responsible_role
- blocking_flag
- source_reference

## Required Confirmations (Section J)

Each confirmation contains:
- confirmation_id
- confirmation_type
- confirmation_description
- responsible_role
- required_before_action
- current_status (Pending / Not Required / Deferred)
- evidence_required
- governance_warning

## Permitted Management Actions (Section K)

Each action contains:
- management_action_id
- action_name
- action_allowed
- action_reason
- prerequisite
- blocking_condition
- audit_required

No action is marked as selected.

## Monitoring Requirements (Section L)

Each monitoring record contains:
- monitoring_id
- monitoring_required
- monitoring_frequency
- monitoring_kpi
- trigger_condition
- escalation_condition
- responsible_role
- reassessment_condition
- next_review_requirement

## Evidence and Lineage (Section M)

Each package links to:
- evidence_reference_count
- lineage_reference_count
- evidence_complete
- lineage_complete
- evidence_ids
- lineage_ids
- source_phase_list
- audit_traceability_status
