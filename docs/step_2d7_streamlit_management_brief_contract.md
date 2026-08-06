# Streamlit Management Brief Contract

## Overview

The Streamlit management brief contract prepares all 2D-7 brief data for future display in a Streamlit executive dashboard. It preserves all source columns and adds display metadata.

## Panel Structure

The contract supports the following future Streamlit panels:

### A. Header Panel
- brief_title, hospital, department, dominant_kpi, risk_tier, urgency, management_attention_level, final_readiness_status, approval_status

### B. Issue Panel
- what_is_happening, why_it_matters, current_kpi_status, trend_direction, top_operational_warning

### C. Recommendation Panel
- representative_recommendation, immediate_action_option, near_term_action_option, preventive_action_option, recommendation_readiness, recommendation_warning

### D. Scenario Panel
- baseline_summary, conservative_summary, expected_summary, higher_intensity_summary, scenario_readiness, scenario_confidence, main_tradeoff, displacement_risk

### E. Financial Panel
- cost_completeness, estimated_scenario_cost, estimated_financial_benefit, estimated_net_financial_impact, lower/central/upper estimates, financial_confidence, affordability_status, financial_warning

### F. Readiness Panel
- final_readiness_status, main_blocking_condition, top_secondary_conditions, failed_gates, required_resolution, responsible_role

### G. Action Panel
- primary_permitted_action, secondary_permitted_actions, blocked_action_summary, primary_queue, escalation_status, monitoring_required

### H. Management Question Panel
- top_management_questions, blocking_question_count, required_confirmations, responsible_roles

### I. Governance Panel
- causality_status, provisional_warning, contradiction_warning, stakeholder_validation_required, evidence_completeness_status, lineage_completeness_status, audit_traceability_status

### J. Management Decision Form Contract
- selected_action, selected_scenario, review_outcome, management_comment, conditions_imposed, reviewer_role, approval_reference, confirmation_checkbox

All selection and review fields remain blank.

## Display Metadata

- `display_colour`: Grey by default (governed by status)
- `display_icon`: Clock by default
- `display_priority`: 1 by default

## Governance

- No Streamlit pages are built in this step.
- All fields required for future UI are present.
- Filter, sort, search, and tooltip fields are explicitly included.
- No prohibited wording is introduced.

## Output

- `step_2d7_streamlit_management_brief_contract.csv` (646 rows)
