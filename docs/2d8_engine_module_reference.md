# Engine Module Reference

## Module List (26 engines)

| # | Module | Purpose | Output Register |
|---|--------|---------|-----------------|
| 1 | decision_intelligence_validation_authority_engine | Checksum and file verification | step_2d8_authority_validation_register.csv |
| 2 | decision_intelligence_validation_population_engine | Row count reconciliation | step_2d8_population_validation_register.csv |
| 3 | decision_intelligence_validation_identity_engine | ID uniqueness and integrity | step_2d8_identity_validation_register.csv |
| 4 | decision_intelligence_validation_kpi_risk_engine | KPI and risk tier consistency | step_2d8_kpi_risk_validation_register.csv |
| 5 | decision_intelligence_validation_scenario_engine | Scenario summary availability | step_2d8_scenario_validation_register.csv |
| 6 | decision_intelligence_validation_financial_engine | Financial value immutability | step_2d8_financial_validation_register.csv |
| 7 | decision_intelligence_validation_readiness_engine | Readiness status reconciliation | step_2d8_readiness_validation_register.csv |
| 8 | decision_intelligence_validation_action_routing_engine | Action routing boundary checks | step_2d8_action_routing_validation_register.csv |
| 9 | decision_intelligence_validation_evidence_engine | Evidence completeness | step_2d8_evidence_validation_register.csv |
| 10 | decision_intelligence_validation_lineage_engine | Lineage completeness | step_2d8_lineage_validation_register.csv |
| 11 | decision_intelligence_validation_audit_engine | Audit status and traceability | step_2d8_audit_validation_register.csv |
| 12 | decision_intelligence_validation_narrative_engine | Narrative length governance | step_2d8_narrative_validation_register.csv |
| 13 | decision_intelligence_validation_wording_engine | Prohibited and causal terminology | step_2d8_wording_validation_register.csv |
| 14 | decision_intelligence_validation_contradiction_engine | Contradiction warnings | step_2d8_contradiction_validation_register.csv |
| 15 | decision_intelligence_validation_cross_layer_engine | Cross-layer consistency | step_2d8_cross_layer_validation_register.csv |
| 16 | decision_intelligence_validation_streamlit_engine | Streamlit contract readiness | step_2d8_streamlit_validation_register.csv |
| 17 | decision_intelligence_validation_question_engine | Management question completeness | step_2d8_question_validation_register.csv |
| 18 | decision_intelligence_validation_confirmation_engine | Confirmation status | step_2d8_confirmation_validation_register.csv |
| 19 | decision_intelligence_validation_monitoring_engine | Monitoring triggers | step_2d8_monitoring_validation_register.csv |
| 20 | decision_intelligence_validation_governance_engine | Governance and limitations | step_2d8_governance_validation_register.csv |
| 21 | decision_intelligence_validation_recommendation_engine | Recommendation confidence | step_2d8_recommendation_validation_register.csv |
| 22 | decision_intelligence_validation_tradeoff_engine | Tradeoff severity | step_2d8_tradeoff_validation_register.csv |
| 23 | decision_intelligence_validation_export_contract_engine | Export contract completeness | step_2d8_export_contract_validation_register.csv |
| 24 | decision_intelligence_validation_priority_queue_engine | Priority queue ordering | step_2d8_priority_queue_validation_register.csv |
| 25 | decision_intelligence_validation_section_engine | Section count | step_2d8_section_validation_register.csv |
| 26 | decision_intelligence_validation_type_engine | Brief type reconciliation | step_2d8_type_validation_register.csv |

## Common Interface
Every engine exposes:
- `validate()`: Runs validation checks and returns a DataFrame
- `build_register()`: Alias for validate()
- `get_required_columns()`: Returns list of expected output columns
