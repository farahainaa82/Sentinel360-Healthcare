# Step 2D-4 Streamlit Readiness Data Contract

## Contract Structure

Five contract types are created for Streamlit display:

### A. Readiness Summary

- decision_readiness_id
- decision_package_id
- hospital
- department
- dominant_kpi
- risk_tier
- urgency
- final_readiness_status
- primary_queue
- main_blocking_condition
- next_required_action
- responsible_role
- approval_status

### B. Readiness Gates

- gate_name
- gate_status
- blocking_flag
- failure_reason
- required_resolution

### C. Conditions

- condition_type
- severity
- blocking_flag
- current_status
- responsible_role

### D. Transition Guidance

- current_state
- eligible_next_state
- transition_requirements
- transition_not_executed_flag

### E. Escalation

- operational_escalation_status
- readiness_status
- management_attention_required

## Usage Notes

- Do not build Streamlit pages in this step
- Contracts are ready for downstream Streamlit development
- All fields are governed and validated
- No preferred scenario or approved recommendation is included
