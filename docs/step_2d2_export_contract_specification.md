# Step 2D-2 Export Contract Specification

## Export Contracts

Six export contracts are generated per decision package:

1. decision_package_summary
2. full_evidence_package
3. management_review_sheet
4. scenario_comparison_sheet
5. financial_comparison_sheet
6. audit_and_lineage_sheet

## Contract Structure

Each contract record contains:
- export_contract_id
- decision_package_id
- approval_package_id
- contract_name
- required_fields (pipe-delimited)
- contract_status
- governance_note

## Required Fields per Contract

### decision_package_summary
- decision_package_id, approval_package_id, hospital_name, department_name, dominant_kpi_name, package_status, package_readiness, completeness_status, issue_title, management_narrative

### full_evidence_package
- decision_package_id, approval_package_id, evidence_reference_count, lineage_reference_count, evidence_complete, lineage_complete, evidence_ids, lineage_ids, source_phase_list, audit_traceability_status

### management_review_sheet
- decision_package_id, approval_package_id, management_question_id, question_text, question_category, mandatory_flag, blocking_flag, responsible_role, confirmation_id, confirmation_type, current_status

### scenario_comparison_sheet
- decision_package_id, approval_package_id, scenario_family, baseline_available, conservative_available, expected_available, higher_intensity_available, comparator_completeness, comparator_consistency, scenario_tradeoff_summary, scenario_displacement_summary, scenario_dominance_summary

### financial_comparison_sheet
- decision_package_id, approval_package_id, financial_review_required, cost_completeness, estimated_scenario_cost, estimated_financial_benefit, estimated_net_financial_impact, roi_status, payback_status, affordability_status, lower_financial_estimate, central_financial_estimate, upper_financial_estimate, financial_confidence

### audit_and_lineage_sheet
- decision_package_id, approval_package_id, causality_status, contradiction_warning, provisional_warning, evidence_completeness, lineage_completeness, governance_issue_count, package_limitations, source_phase_list, audit_traceability_status

## Governance Constraints

- Contracts are data-only structures.
- No PDF or Streamlit pages are generated in this step.
- All fields are sourced from governed 2D-1 outputs.
