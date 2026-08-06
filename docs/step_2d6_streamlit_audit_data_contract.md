# Streamlit Audit Data Contract

## Overview

The Streamlit audit data contract prepares all 2D-6 outputs for future display in a Streamlit management dashboard. It flattens and normalises complex audit structures into UI-ready rows without altering underlying values.

## Data Contract Structure

The contract creates one row per evidence reference per decision package, augmented with lineage, audit, and governance fields:

| Field Group | Fields | Source |
|---|---|---|
| Identity | `decision_package_id`, `evidence_reference_id` | Evidence reference engine |
| Evidence | `evidence_category`, `evidence_status`, `evidence_description` | Evidence profile |
| Lineage | `lineage_stage_name`, `link_status`, `parent_record_id` | Lineage link |
| Audit | `audit_event_type`, `event_status`, `required_actor_role` | Audit event contract |
| Governance | `approval_status`, `causality_status`, `provisional_flag` | Management review |
| Display | `display_priority`, `display_colour`, `display_icon` | Display governance config |

## Display Governance

Display attributes are governed by `config/decision_audit_display_governance.csv`:

| Status | Colour | Icon | Priority |
|---|---|---|---|
| Complete | Green | check-circle | 1 |
| Complete with Conditions | Amber | alert-circle | 2 |
| Partial | Orange | alert-triangle | 3 |
| Incomplete | Red | x-circle | 4 |
| Not Executed | Grey | clock | 5 |
| Pending Management Review | Blue | hourglass | 6 |
| Not Confirmed | Purple | help-circle | 7 |

## Flattening Rules

1. One row per evidence reference (18,088 references) with repeated decision package fields.
2. Streamlit-specific columns (display_colour, display_icon) are added; no source columns removed.
3. All 646 decision packages are represented.
4. No computed values are altered; only presentation attributes are added.

## Prohibited Wording

The contract enforces that no UI text implies:

- A decision has been made ("approved", "rejected", "executed")
- Causality has been confirmed ("caused by", "due to", "result of")
- Financial values are final ("actual cost", "realised benefit")
- Recommendations are mandatory ("must", "shall", "required to act")

## UI Field Availability

All fields required for a future Streamlit interface are present:

- Filter fields: decision_package_id, evidence_category, lineage_stage_name, audit_event_type
- Sort fields: display_priority, evidence_coverage_pct, lineage_completeness_pct
- Search fields: evidence_description, governance_note, audit_explanation
- Tooltip fields: provisional_flag, contradiction_flag, orphan_lineage_flag

## Output

- `step_2d6_streamlit_audit_data_contract.csv` (54,910 rows)
