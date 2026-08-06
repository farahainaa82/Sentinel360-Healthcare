# Evidence and Lineage Specification

## Evidence Reconciliation

Evidence references from Phase 2D-4 are carried forward into Phase 2D-5 action routing. Each action-routing package retains links to its original readiness evidence.

### Evidence Record Fields

- action_evidence_id
- decision_action_routing_id
- decision_readiness_id
- evidence_type
- evidence_description
- evidence_status
- source_phase
- reconciliation_status

### Reconciliation Rules

1. All evidence must link to a valid routing ID
2. No orphan evidence records allowed
3. Evidence status remains unchanged from 2D-4
4. Source phase must be "2D-4"

## Lineage Reconciliation

Lineage references from Phase 2D-4 are carried forward similarly.

### Lineage Record Fields

- action_lineage_id
- decision_action_routing_id
- decision_readiness_id
- lineage_type
- lineage_description
- lineage_status
- source_phase
- reconciliation_status

### Reconciliation Rules

1. All lineage must link to a valid routing ID
2. No orphan lineage records allowed
3. Lineage status remains unchanged from 2D-4
4. Source phase must be "2D-4"

## Governance

- Evidence and lineage values must not be modified
- Missing evidence is logged but not invented
- Missing lineage is logged but not invented
- Reconciliation status indicates whether a source was found
