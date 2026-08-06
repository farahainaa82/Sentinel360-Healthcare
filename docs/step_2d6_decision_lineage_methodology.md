# Decision Lineage Methodology

## Overview

Decision lineage ensures that every decision-action routing package can be traced from its original authoritative source through every transformation stage to the final routed action. Phase 2D-6 creates lineage profiles and lineage links for all 646 decision packages.

## Lineage Profile

Each decision package receives exactly one lineage profile (`decision_lineage_profile_id`). The profile contains:

- `source_system`: The originating analytical system (Sentinel360)
- `source_phase`: The upstream phase that created the package (e.g., 2D-5)
- `source_file`: The authoritative input file name
- `source_record_id`: The unique record identifier in the source file
- `lineage_completeness_status`: Complete, Partial, or Incomplete
- `orphaned_lineage_flag`: True if any stage lacks a parent link

## Lineage Stages

Lineage links represent 18 ordered stages through which source data travels:

| Stage Order | Stage Name | Description |
|---|---|---|
| 1 | Source Data Ingestion | Raw data intake from operational systems |
| 2 | Data Validation | Validation and quality checks |
| 3 | Data Transformation | Conversion to analytical formats |
| 4 | Baseline Calculation | Historical baseline computation |
| 5 | Trend Analysis | Statistical signal detection |
| 6 | Threshold Assessment | Breach and band evaluation |
| 7 | Risk Scoring | Priority tier assignment |
| 8 | Scenario Modelling | What-if scenario generation |
| 9 | Comparator Analysis | Peer and benchmark comparison |
| 10 | Financial Projection | Cost-benefit estimation |
| 11 | Recommendation Generation | Management recommendation formulation |
| 12 | Decision Readiness Scoring | Readiness gate evaluation |
| 13 | Blocking Condition Check | Prerequisite and blocking rule application |
| 14 | Action Eligibility Scoring | Action eligibility determination |
| 15 | Queue Assignment | Routing queue allocation |
| 16 | Escalation Routing | Escalation path determination |
| 17 | Monitoring Action Setup | Monitoring plan assignment |
| 18 | Action Routing Finalisation | Final action routing package assembly |

## Link Structure

Each lineage link contains:

- `parent_record_id`: The upstream record identifier
- `child_record_id`: The downstream record identifier
- `transformation_id`: The transformation applied (if any)
- `formula_id`: The calculation formula used (if any)
- `configuration_id`: The configuration rule applied (if any)
- `link_status`: Linked, Orphaned, or Superseded

## Completeness Rules

1. **Complete**: All 18 stages linked, no orphans, coverage = 100%
2. **Partial**: 1-3 stages missing or orphaned
3. **Incomplete**: More than 3 stages missing

## Governance Constraints

- Every package must have exactly 18 lineage links (one per stage).
- Stage order must be sequential; no gaps or duplicates.
- No fuzzy matching: links require explicit record IDs.
- No label-only linkage: every link must have a parent and child record ID.
- Orphaned stages are flagged but not auto-corrected.

## Output

- `step_2d6_decision_lineage_profile_register.csv` (646 rows)
- `step_2d6_lineage_link_register.csv` (11,628 rows = 18 x 646)
- `step_2d6_lineage_completeness_register.csv` (646 rows)
- `step_2d6_lineage_issue_register.csv` (0 rows)
