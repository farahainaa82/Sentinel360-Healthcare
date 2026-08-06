# Integrated Management Brief Methodology

## Overview

Phase 2D-7 creates one concise, governed, executive-ready Integrated Management Brief for each of the 646 decision-action routing packages produced in Phase 2D-5. The brief synthesises operational issues, risk, evidence, recommendations, scenarios, financial impact, readiness, actions, questions, monitoring, and governance into a single management-review document.

## Objectives

1. Synthesise all upstream analytical outputs into one brief per decision package.
2. Maintain strict governance: no decisions made, no actions selected, no approvals recorded.
3. Support executive dashboards, management queues, downloadable reports, and future Streamlit display.
4. Preserve full traceability to source evidence, lineage, and audit records.

## Execution Controls

- Single-instance execution lock prevents duplicate processes.
- Authority verification with SHA-256 checksums halts processing on any mismatch.
- Population validation ensures no Cartesian joins occur.
- Progress and elapsed-time logging for every major stage.
- Atomic tmp-to-final output moves.
- Manifest generated only after all outputs complete.

## Source Data Integration

The brief builder joins the following authoritative sources:

| Source Phase | File | Key Columns Used |
|---|---|---|
| 2D-2 | decision_package_register.csv | Issue narrative, scenario summaries, financial estimates, recommendations, conditions |
| 2D-3 | decision_scorecard_register.csv | Scorecard dimensions, priority view |
| 2D-4 | decision_readiness_register.csv | Final readiness, gates, blocking conditions |
| 2D-4 | blocking_condition_register.csv | Blocking and secondary conditions |
| 2D-5 | decision_action_routing_register.csv | Package identity, routing status, queue, escalation |
| 2D-5 | primary_action_register.csv | Primary permitted actions |
| 2D-5 | responsible_role_register.csv | Responsible roles |
| 2D-5 | escalation_routing_register.csv | Escalation status and reason |
| 2D-5 | monitoring_action_register.csv | Monitoring requirements |
| 2D-5 | queue_assignment_register.csv | Primary and secondary queues |
| 2D-5 | action_explanation_register.csv | Action explanations |
| 2D-5 | management_selection_contract.csv | Management questions and confirmations |
| 2D-6 | decision_evidence_profile_register.csv | Evidence completeness |
| 2D-6 | evidence_completeness_register.csv | Evidence coverage and gaps |
| 2D-6 | decision_lineage_profile_register.csv | Lineage completeness |
| 2D-6 | lineage_completeness_register.csv | Lineage stage coverage |
| 2D-6 | audit_explanation_register.csv | Audit narrative |
| 2D-6 | management_review_contract.csv | Review status (all pending) |
| 2D-6 | source_to_decision_trace_register.csv | Traceability status |

## Brief Generation Pipeline

1. **Authority Verification**: Validate all 21+ input files exist, are readable, and match frozen checksums.
2. **Core Brief Construction**: Start with 2D-5 routing register (646 rows). Left join all upstream sources on `decision_package_id`.
3. **Population Validation**: Verify row count remains exactly 646 after each major join.
4. **Section Synthesis**: Apply engine functions to generate all 17 governed sections (A–Q).
5. **Type Assignment**: Map `final_readiness_status` to `brief_type` using configuration.
6. **Attention Assignment**: Map risk tier, urgency, and escalation to `management_attention_level`.
7. **Derived Output Creation**: Generate priority view, queue briefs, export contracts, Streamlit contract, evidence/lineage cross-references, and governance validation.
8. **Output Writing**: Write all 29 outputs atomically from tmp to final paths.
9. **Manifest Generation**: Generate JSON manifest with checksums and row counts.

## Governance Principles

- No preferred scenario is selected.
- No management action is selected.
- No recommendation is approved.
- No budget is approved.
- No management review is recorded.
- All approval statuses remain `Pending Management Review`.
- `causality_status` remains `Not Confirmed`.
- Upstream values are never modified.
- Prohibited wording ("AI Recommendation", "Best Scenario", "Optimal Action", etc.) is flagged and rejected.

## Output

- 29 required output files under `outputs/decision_intelligence/`.
- All 646 decision packages have exactly one integrated management brief.
- 54/59 tests passed; 5 skipped due to blank upstream source data.
