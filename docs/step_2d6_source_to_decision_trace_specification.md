# Source-to-Decision Trace Specification

## Overview

The source-to-decision trace provides a single, verifiable path from every authoritative upstream record to its corresponding action routing decision package. It guarantees that no decision package exists without an identifiable origin.

## Trace Structure

Each trace record (`source_to_decision_trace_id`) links one decision package to its ultimate source:

| Field | Description |
|---|---|
| `decision_package_id` | The action routing package identifier from 2D-5 |
| `source_phase` | The earliest phase contributing to this package |
| `source_file` | The authoritative input file name |
| `source_record_id` | The unique source record identifier |
| `trace_depth` | Number of lineage stages traversed (always 18) |
| `trace_status` | Complete, Partial, or Broken |
| `governance_note` | Audit annotation |

## Trace Validation Rules

1. **Trace must reach action routing**: Every trace must terminate at a valid `step_2d5_decision_action_routing_register.csv` record.
2. **No fabricated completion**: No trace may claim a completed management decision; the trace ends at routing, not execution.
3. **Source record retention**: The original `source_record_id` from the authoritative input register is preserved unchanged.
4. **Checksum linkage**: Where available, source file checksums are referenced to confirm immutability.

## Integrity Checks

- Trace count must equal decision package count (646).
- Every `decision_package_id` in the trace must exist in 2D-5 outputs.
- No trace may reference a source file that does not exist in the authoritative input register.
- `trace_status` is `Complete` when all 18 lineage stages are linked; otherwise `Partial` or `Broken`.

## Governance

- Traces are read-only after creation.
- No trace is modified, deleted, or re-routed.
- Superseded traces are flagged, not removed.

## Output

- `step_2d6_source_to_decision_trace_register.csv` (646 rows)
