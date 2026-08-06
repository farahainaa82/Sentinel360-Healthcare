# Output Register Reference (A-AF)

## Master Register
| File | Rows | Columns | Description |
|------|------|---------|-------------|
| step_2d8_master_validation_register.csv | 646 | 14 | Per-package validation summary |

## Engine Registers (A-Z)
| File | Rows | Description |
|------|------|-------------|
| step_2d8_authority_validation_register.csv | ~27 | File checksum and existence checks |
| step_2d8_population_validation_register.csv | 22 | Row count reconciliation |
| step_2d8_identity_validation_register.csv | 6 | ID uniqueness and integrity |
| step_2d8_kpi_risk_validation_register.csv | 3 | KPI and risk tier consistency |
| step_2d8_scenario_validation_register.csv | 3 | Scenario summary availability |
| step_2d8_financial_validation_register.csv | 3 | Financial value immutability |
| step_2d8_readiness_validation_register.csv | 3 | Readiness status reconciliation |
| step_2d8_action_routing_validation_register.csv | 5 | Action routing boundary checks |
| step_2d8_evidence_validation_register.csv | 2 | Evidence completeness |
| step_2d8_lineage_validation_register.csv | 2 | Lineage completeness |
| step_2d8_audit_validation_register.csv | 3 | Audit status and traceability |
| step_2d8_narrative_validation_register.csv | 4 | Narrative length governance |
| step_2d8_wording_validation_register.csv | 3 | Prohibited and causal terminology |
| step_2d8_contradiction_validation_register.csv | 3 | Contradiction warnings |
| step_2d8_cross_layer_validation_register.csv | 3 | Cross-layer consistency |
| step_2d8_streamlit_validation_register.csv | 4 | Streamlit contract readiness |
| step_2d8_question_validation_register.csv | 2 | Management question completeness |
| step_2d8_confirmation_validation_register.csv | 2 | Confirmation status |
| step_2d8_monitoring_validation_register.csv | 2 | Monitoring triggers |
| step_2d8_governance_validation_register.csv | 3 | Governance and limitations |
| step_2d8_recommendation_validation_register.csv | 3 | Recommendation confidence |
| step_2d8_tradeoff_validation_register.csv | 2 | Tradeoff severity |
| step_2d8_export_contract_validation_register.csv | 3 | Export contract completeness |
| step_2d8_priority_queue_validation_register.csv | 3 | Priority queue ordering |
| step_2d8_section_validation_register.csv | 3 | Section count |
| step_2d8_type_validation_register.csv | 2 | Brief type reconciliation |

## Summary Registers
| File | Rows | Description |
|------|------|-------------|
| step_2d8_execution_summary.csv | 26 | Engine execution timing and status |
| step_2d8_outcome_distribution.csv | 1-7 | Validation outcome counts |

## Manifest
| File | Description |
|------|-------------|
| step_2d8_manifest.json | Full metadata, checksums, and outcome distribution |
