# Step 2D-2 Evidence and Lineage Specification

## Evidence Assembly

Every package must reconcile to at least one evidence reference from each applicable phase:

- Phase 2B (KPI, trend, threshold, risk evidence)
- Phase 2C-1 (recommendation evidence)
- Phase 2C-2 (scenario evidence)
- Phase 2C-3 (financial evidence)
- Phase 2D-1 (integrated decision evidence)

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

Every package must have a traceable lineage record linking back to upstream phases.

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

No package may exist without at least one evidence and one lineage reference. Missing evidence must remain visible and must affect package completeness.

## Source Phase List

The canonical source_phase_list for all packages is:
`Phase 2B|Phase 2C-1|Phase 2C-2|Phase 2C-3|Phase 2D-1`
