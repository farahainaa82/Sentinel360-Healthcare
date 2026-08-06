# Step 3B Executive Overview Methodology

## Purpose
Provide a concise, executive-ready view of hospital operational risk, decision readiness, financial impact, and management priorities using frozen Phase 2D handover datasets.

## Scope
- Read-only access to authoritative Phase 2D outputs
- No recalculation of KPIs, risks, or financial values
- No selection of scenarios, actions, recommendations, or budgets
- No management review recorded

## Data Sources
All datasets are loaded from `outputs/decision_intelligence/`:
- step_2d9_executive_overview_dataset.csv
- step_2d9_kpi_dashboard_dataset.csv
- step_2d9_risk_alert_dataset.csv
- step_2d9_financial_impact_dataset.csv
- step_2d9_integrated_decision_dataset.csv
- step_2d9_management_action_contract_dataset.csv
- step_2d9_management_question_confirmation_dataset.csv
- step_2d9_monitoring_escalation_dataset.csv
- step_2d9_audit_traceability_dataset.csv
- step_2d9_recommendation_dataset.csv
- step_2d9_scenario_comparison_dataset.csv
- step_2d9_manifest.json

## Architecture
- Page: pages/02_Executive_Overview.py
- Controller: src/streamlit_executive_page_controller.py
- Engines: 16 focused modules under src/
- Config: 8 CSV files under config/

## Governance
- causality_status: Not Confirmed
- approval_status: Pending Management Review
- All actions require authorised human review.
