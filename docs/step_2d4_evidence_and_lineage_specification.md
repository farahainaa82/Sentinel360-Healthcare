# Step 2D-4 Evidence and Lineage Specification

## Evidence Reconciliation

Evidence records from Step 2D-3 are reconciled into readiness-specific evidence records:

- readiness_evidence_id
- decision_readiness_id
- decision_scorecard_id
- decision_package_id
- evidence_phase
- evidence_type
- evidence_status
- source_reference
- reconciliation_status
- governance_note

## Lineage Reconciliation

Lineage records from Step 2D-3 are reconciled into readiness-specific lineage records:

- readiness_lineage_id
- decision_readiness_id
- decision_scorecard_id
- decision_package_id
- lineage_phase
- lineage_type
- lineage_status
- source_reference
- reconciliation_status
- governance_note

## Rules

- One evidence record per readiness record minimum
- One lineage record per readiness record minimum
- Evidence references must reconcile with upstream phases
- Lineage references must trace back to authoritative sources
- No orphan readiness records may exist
- Evidence-completion defects are not hidden under generic statuses
- Lineage-completion defects are not hidden under generic statuses

## Validation

- Evidence records count must match readiness records count
- Lineage records count must match readiness records count
- All records must link to valid decision_readiness_id
