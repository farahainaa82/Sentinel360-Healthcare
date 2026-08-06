# Step 2D-3 Evidence and Lineage Specification

## Evidence Assembly

Every scorecard must link to:

- Decision package evidence (Phase 2D-2)
- KPI evidence (Phase 2B)
- Risk evidence (Phase 2B)
- Recommendation evidence (Phase 2C-1)
- Scenario evidence (Phase 2C-2)
- Financial evidence (Phase 2C-3)
- Governance evidence (Phase 2D-1)

## Evidence Record Fields

- evidence_record_id
- decision_package_id
- approval_package_id
- evidence_reference_count
- evidence_complete
- evidence_ids
- source_phase_list
- audit_traceability_status

## Lineage Assembly

Every scorecard must have a traceable lineage record linking back through all upstream phases.

## Lineage Record Fields

- lineage_record_id
- decision_package_id
- approval_package_id
- lineage_reference_count
- lineage_complete
- lineage_ids
- source_phase_list
- audit_traceability_status

## No-Orphan Rule

No scorecard may exist without at least one evidence and one lineage reference. Missing evidence must remain visible and must affect scorecard completeness.

## Source Phase List

The canonical source_phase_list for all scorecards is:
`Phase 2B|Phase 2C-1|Phase 2C-2|Phase 2C-3|Phase 2D-1|Phase 2D-2`
