# Phase 2D-5 — Decision Options and Action Routing Methodology

## Overview

Phase 2D-5 converts 646 decision-readiness records from Phase 2D-4 into governed action-option and routing packages. This step does not select, approve, or execute any action. It determines which management actions are allowed, blocked, or conditional for each readiness state.

## Core Principles

1. **Rule-based only**: All action eligibility is determined by configuration, not by AI selection.
2. **No Cartesian joins**: Every merge uses governed identifiers only.
3. **Single-instance lock**: Execution lock prevents duplicate processes.
4. **Atomic writes**: All outputs written to tmp first, then moved atomically.
5. **Smoke test before full run**: 5-sample validation before processing all 646 records.

## Input Sources

- `step_2d4_decision_readiness_register.csv` (646 records)
- `step_2d4_readiness_gate_register.csv`
- `step_2d4_blocking_condition_register.csv`
- `step_2d4_secondary_condition_register.csv`
- `step_2d4_operational_escalation_register.csv`
- `step_2d4_readiness_evidence_register.csv`
- `step_2d4_readiness_lineage_register.csv`

## Process Flow

1. Authority verification (checksums, frozen status)
2. Readiness reconciliation (retain all IDs)
3. Action routing population (646 packages)
4. Action eligibility evaluation (18 actions × 646 = 11,628 records)
5. Prerequisite creation (3,713 records)
6. Blocking record creation (504 records)
7. Primary and secondary action assignment
8. Responsible role routing
9. Escalation routing (separate from analytical readiness)
10. Monitoring action model
11. Management selection contracts (all flags False)
12. Audit requirement assignment
13. Queue assignment
14. Explanation generation
15. Streamlit data contract generation
16. Evidence and lineage reconciliation
17. Governance validation
18. Output writing and manifest generation

## Governance Constraints

- `approval_status` = Pending Management Review for all records
- `causality_status` = Not Confirmed for all records
- `selected_flag` = False for all records
- No prohibited action names (Approve, Select Best, Implement, etc.)
- No prerequisite marked Completed
- No blocking condition marked Resolved
- No monitoring marked Implemented

## Outputs

21 CSV/JSON files under `outputs/decision_intelligence/`, prefixed `step_2d5_`.
