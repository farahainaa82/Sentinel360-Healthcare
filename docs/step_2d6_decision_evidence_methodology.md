# Phase 2D-6 — Decision Evidence and Audit Methodology

## Overview

Phase 2D-6 creates a governed evidence, lineage, audit, and traceability layer for all 646 decision-action routing packages produced in Phase 2D-5. This step does not create, approve, or execute any management decision. It ensures every decision package can be traced, justified, versioned, and audited.

## Core Principles

1. **Traceability**: Every output must link back to its authoritative sources.
2. **No fabricated decisions**: No management decision, approval, or completed event is invented.
3. **Rule-based governance**: All evidence categories, lineage stages, and audit requirements are configuration-driven.
4. **Upstream immutability**: Phase 2D-4 and 2D-5 files are never modified.
5. **Single-instance lock**: Execution lock prevents duplicate processes.
6. **Atomic writes**: All outputs written to tmp first, then moved atomically.
7. **Smoke test before full run**: 5-sample validation before processing all 646 records.

## Input Sources

- `step_2d5_authoritative_input_register.csv` (17 files)
- `step_2d5_decision_action_routing_register.csv` (646 records)
- `step_2d5_action_eligibility_register.csv` (11,628 records)
- `step_2d5_action_prerequisite_register.csv` (3,713 records)
- `step_2d5_action_blocking_register.csv` (504 records)
- `step_2d5_primary_action_register.csv` (646 records)
- `step_2d5_secondary_action_register.csv` (1,938 records)
- `step_2d5_responsible_role_register.csv` (646 records)
- `step_2d5_escalation_routing_register.csv` (646 records)
- `step_2d5_monitoring_action_register.csv` (646 records)
- `step_2d5_management_selection_contract.csv` (646 records)
- `step_2d5_action_audit_requirement_register.csv` (11,628 records)
- `step_2d5_action_explanation_register.csv` (646 records)
- `step_2d5_queue_assignment_register.csv` (646 records)
- `step_2d5_streamlit_action_data_contract.csv` (12,274 records)
- `step_2d5_action_evidence_register.csv` (646 records)
- `step_2d5_action_lineage_register.csv` (646 records)
- `step_2d5_execution_summary.csv`
- `step_2d5_manifest.json`

## Process Flow

1. Authority verification (checksums, frozen status)
2. Evidence profile creation (646 packages)
3. Evidence reference creation (28 categories x 646 = 18,088 records)
4. Evidence completeness assessment
5. Lineage profile creation (646 packages)
6. Lineage link creation (18 stages x 646 = 11,628 records)
7. Lineage completeness assessment
8. Source-to-decision trace generation
9. Audit requirement integration (from 2D-5)
10. Audit event catalogue loading (24 event types)
11. Audit event contract creation (all Not Executed)
12. Decision history contract creation (Initial Governed State)
13. Version control registration (Current/Superseded/Frozen)
14. Integrity (SHA-256) verification
15. Retention classification
16. Access role contract creation
17. Evidence pack contract creation
18. Management review contract creation (Pending Management Review)
19. Audit explanation generation
20. Streamlit audit data contract generation
21. Governance validation
22. Output writing and manifest generation

## Governance Constraints

- `approval_status` = Pending Management Review for all records
- `causality_status` = Not Confirmed for all records
- `event_status` = Not Executed for all audit event contracts
- `history_status` = Initial Governed State for all history contracts
- `version_status` = Current or Superseded (never claims Final)
- No completed audit events created
- No management review fabricated
- No action selected

## Outputs

26 CSV/JSON files under `outputs/decision_intelligence/`, prefixed `step_2d6_`.
