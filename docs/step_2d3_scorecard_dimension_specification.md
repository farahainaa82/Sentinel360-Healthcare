# Step 2D-3 Scorecard Dimension Specification

## Dimension 1 — Operational Risk

| Field | Source | Notes |
|---|---|---|
| operational_risk_score | 2D-2 maximum_risk_score | Preserved |
| risk_tier | 2D-2 risk_tier | Governed band |
| priority_tier | 2D-2 priority_tier | |
| urgency | 2D-2 urgency | |
| breach_status | 2D-2 breach_status | |
| watch_status | 2D-2 watch_status | |
| trend_direction | 2D-2 trend_direction | |
| sustained_movement_flag | 2D-2 sustained_movement_flag | |
| dominant_breach_type | 2D-2 dominant_breach_type | |
| provisional_threshold_flag | 2D-2 provisional_threshold_flag | |

Allowed bands: Critical, High, Elevated, Moderate, Low, Monitoring, Not Assessable

## Dimension 2 — Evidence Strength

| Field | Source | Notes |
|---|---|---|
| evidence_reference_count | 2D-2 evidence_count | |
| evidence_phase_coverage | Static | All applicable phases |
| evidence_completeness | 2D-2 evidence_completeness | |
| evidence_status | Derived | Complete / Partial / Limited / Not Available |
| missing_evidence_flag | Derived | Inverse of completeness |

## Dimension 3 — Lineage Strength

| Field | Source | Notes |
|---|---|---|
| lineage_reference_count | Derived | 1 if complete |
| lineage_stage_coverage | Static | All applicable phases |
| lineage_completeness | 2D-2 lineage_completeness | |
| lineage_status | Derived | Complete / Partial / Incomplete / Not Available |
| orphan_lineage_flag | Derived | Inverse of completeness |

## Dimension 4 — Recommendation Readiness

| Field | Source | Notes |
|---|---|---|
| representative_recommendation_available | 2D-2 | Boolean |
| recommendation_validation_status | 2D-2 | |
| recommendation_confirmation_required | 2D-2 | |
| recommendation_limitation_count | Static | 0 (preserved from upstream) |
| recommendation_governance_warning | 2D-2 | |
| recommendation_readiness | Derived | Governed status |

## Dimension 5 — Scenario Readiness

| Field | Source | Notes |
|---|---|---|
| scenario_required_status | 2D-2 | |
| scenario_readiness | 2D-2 | |
| baseline_available | 2D-2 | Boolean |
| comparator_completeness | 2D-2 | |
| comparator_consistency | 2D-2 | |
| scenario_validation_status | 2D-2 | |
| scenario_confidence | 2D-2 | |
| tradeoff_status | 2D-2 tradeoff_summary | |
| displacement_status | 2D-2 displacement_summary | |
| sensitivity_status | 2D-2 sensitivity_summary | |
| dominance_status | 2D-2 dominance_summary | |

## Dimension 6 — Financial Readiness

| Field | Source | Notes |
|---|---|---|
| financial_review_required | 2D-2 | Boolean |
| financial_readiness | 2D-2 | |
| cost_completeness | 2D-2 | |
| benefit_completeness | 2D-2 | |
| net_impact_available | Derived | Boolean |
| roi_status | 2D-2 | |
| payback_status | 2D-2 | |
| affordability_status | 2D-2 | |
| financial_confidence | 2D-2 | |
| missing_financial_input_flag | 2D-2 | Boolean |

## Dimension 7 — Uncertainty and Sensitivity

| Field | Source | Notes |
|---|---|---|
| lower_financial_estimate | 2D-2 | |
| central_financial_estimate | 2D-2 | |
| upper_financial_estimate | 2D-2 | |
| financial_range_width | Derived | upper - lower |
| primary_uncertainty_driver | 2D-2 | |
| uncertainty_status | Derived | Governed status |
| scenario_sensitivity_status | 2D-2 | |
| financial_sensitivity_status | 2D-2 | |
| break_even_status | Static | Not Assessable |

## Dimension 8 — Governance Burden

| Field | Source | Notes |
|---|---|---|
| contradiction_warning | 2D-2 | Boolean |
| contradiction_severity | 2D-2 | |
| provisional_warning | 2D-2 | Boolean |
| stakeholder_validation_required | 2D-2 | Boolean |
| assumption_validation_required | 2D-2 | Boolean |
| baseline_validation_required | 2D-2 | Boolean |
| financial_validation_required | 2D-2 | Boolean |
| governance_issue_count | 2D-2 | |
| governance_burden_status | Derived | Low / Moderate / High / Blocking / Monitoring Only / Not Assessable |

## Dimension 9 — Management Readiness

| Field | Source | Notes |
|---|---|---|
| package_readiness | 2D-2 | |
| package_completeness | 2D-2 | |
| decision_readiness | 2D-2 | |
| permitted_management_actions | 2D-2 | |
| blocking_condition_count | Derived | Count of active blocking flags |
| management_review_required | 2D-2 | Boolean |
| approval_status | Static | Pending Management Review |
