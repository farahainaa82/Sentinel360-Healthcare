# Streamlit Data Contract Specification

## Datasets Created

| Dataset | Records | Source | Purpose |
|---|---|---|---|
| Executive Overview | 646 | IMB | High-level risk and readiness summary |
| KPI Dashboard | 3,876 | IMB | Six core KPIs per package |
| Risk and Alert | 646 | IMB | Risk register with contributing factors |
| Recommendation | 646 | IMB | Structured recommendations with options |
| Scenario Comparison | 646 | IMB | Baseline, Conservative, Expected, Higher Intensity |
| Financial Impact | 646 | IMB | Cost, benefit, ROI with uncertainty |
| Integrated Decision | 646 | IMB | Consolidated executive headline |
| Management Action Contract | 646 | IMB | Blank controls for review |
| Question and Confirmation | 646 | IMB | Management questions |
| Monitoring and Escalation | 646 | IMB | Monitoring KPIs and escalation paths |
| Audit and Traceability | 646 | IMB | Evidence, lineage, audit status |

## Field Rules

- All datasets retain governed IDs (`decision_package_id`, `integrated_management_brief_id`).
- Missing values remain explicit (empty string, not zero).
- Boolean fields default to `False` where applicable.
- Action and scenario selection fields remain blank.
- Audit event status defaults to `Not Executed`.
