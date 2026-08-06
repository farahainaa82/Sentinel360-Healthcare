# Step 2D-3 Streamlit Scorecard Data Contract

## Contract Overview

Seven Streamlit-ready data contracts are generated per decision scorecard:

1. executive_overview_card
2. risk_card
3. recommendation_card
4. scenario_card
5. financial_card
6. governance_card
7. management_action_card

## Executive Overview Card

Fields:
- decision_scorecard_id
- hospital
- department
- dominant_kpi
- risk_tier
- urgency
- decision_readiness
- top_warning
- top_action
- reporting_date

## Risk Card

Fields:
- risk_score
- risk_tier
- threshold_status
- trend_direction
- sustained_movement_flag
- breach_status
- watch_status

## Recommendation Card

Fields:
- representative_recommendation
- recommendation_readiness
- recommendation_confirmation_required
- recommendation_warning

## Scenario Card

Fields:
- comparator_completeness
- comparator_consistency
- scenario_readiness
- scenario_confidence
- tradeoff_summary
- displacement_summary

## Financial Card

Fields:
- cost_completeness
- central_financial_estimate
- lower_financial_estimate
- upper_financial_estimate
- financial_confidence
- financial_readiness
- affordability_status

## Governance Card

Fields:
- causality_status
- contradiction_warning
- provisional_warning
- required_validation
- governance_burden_status

## Management Action Card

Fields:
- permitted_next_action
- blocking_condition
- top_management_question
- approval_status

## Governance Constraints

- Contracts are data-only structures.
- No Streamlit pages are generated in this step.
- All fields are sourced from governed 2D-2 outputs.
