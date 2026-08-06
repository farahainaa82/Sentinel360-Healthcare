# Decision History and Version Control

## Overview

Phase 2D-6 establishes decision history contracts and version control registers to ensure every decision package has a clear historical state and version lineage. No historical decisions are invented.

## Decision History Contract

Each of the 646 decision packages receives one history contract:

| Field | Value | Notes |
|---|---|---|
| `history_status` | Initial Governed State | Fixed for all records |
| `prior_version` | Blank | No prior version exists |
| `prior_readiness_status` | Blank | No prior readiness recorded |
| `prior_action_routing_status` | Blank | No prior routing recorded |
| `change_reason` | Blank | No change has occurred |
| `change_authority` | Blank | No authority exercised |
| `governance_note` | No historical decisions invented | Fixed annotation |

## Version Control Register

Version control tracks the lifecycle of each authoritative input file:

| Version Status | Description |
|---|---|
| Current | The active, authoritative version |
| Superseded | Replaced by a newer version |
| Draft | Under development, not yet authoritative |
| Frozen | Locked for audit or compliance |
| Archived | Retained for historical reference only |

## Version Control Rules

1. Every authoritative input file from prior phases receives a version record.
2. Files marked `frozen` in 2D-5 retain `Frozen` status.
3. Files superseded by newer outputs receive `Superseded` status.
4. Current analytical outputs receive `Current` status.
5. No version is ever deleted; only status transitions are permitted.

## Superseded Flagging

- Superseded versions are explicitly flagged.
- Checksums of superseded versions are retained for integrity verification.
- Superseded records are excluded from active processing but retained for audit.

## Governance Constraints

- No historical decision is invented: `prior_version` is always blank.
- No readiness status is backdated: `prior_readiness_status` is always blank.
- No action routing is claimed as completed: `prior_action_routing_status` is always blank.
- Version statuses are mutually exclusive: a record cannot be both Current and Superseded.

## Output

- `step_2d6_decision_history_contract.csv` (646 rows)
- `step_2d6_version_control_register.csv` (4,522 rows)
