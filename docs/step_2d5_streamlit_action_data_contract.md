# Streamlit Action Data Contract

## Overview

The Streamlit action data contract provides ready-to-use data structures for the Integrated Decision page. This step does not build Streamlit pages; it only generates the data contract.

## Panel A: Action Summary

Fields:
- decision_action_routing_id
- decision_package_id
- final_readiness_status
- primary_permitted_action
- primary_queue
- responsible_role
- escalation_status
- approval_status

## Panel B: Action Button Model

Fields:
- action_id
- action_name
- action_eligibility_status
- enabled_flag (UI eligibility only)
- disabled_reason
- confirmation_required
- audit_required
- management_selection_required
- selected_flag (must remain False)

## Panel C: Prerequisite Panel

Fields:
- prerequisite_type
- prerequisite_description
- blocking_flag
- responsible_role
- current_status
- evidence_required

## Panel D: Blocking Panel

Fields:
- blocking_reason
- blocking_severity
- resolution_required
- responsible_role

## Panel E: Monitoring Panel

Fields:
- monitoring_required
- monitoring_kpi
- monitoring_frequency
- trigger_condition
- escalation_condition
- reassessment_condition

## Panel F: Management Selection Form

Fields:
- selected_action
- selected_by
- management_comment
- decision_status
- confirmation_checkbox
- audit_reference

## Key Rules

- enabled_flag indicates UI eligibility only
- selected_flag must remain False in all records
- No action is pre-selected
- All approval statuses remain Pending Management Review
