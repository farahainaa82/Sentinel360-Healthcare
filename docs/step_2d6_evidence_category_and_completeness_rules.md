# Evidence Category and Completeness Rules

## Overview

Each of the 646 decision packages is assessed against 28 governed evidence categories. This document defines the categories and the rules for determining evidence completeness.

## Evidence Categories

The 28 evidence categories are defined in `config/decision_evidence_category_config.csv`:

| Category | Priority | Description |
|---|---|---|
| Scenario Definition | Critical | Defined scenarios with assumptions |
| Financial Model | Critical | Cost-benefit and financial projections |
| Baseline Data | Critical | Historical baseline metrics |
| Stakeholder Map | Critical | Identified stakeholders and roles |
| Risk Assessment | Critical | Documented risks and mitigations |
| Benefit Realisation Plan | Critical | Expected benefits and measurement |
| Recommendation Rationale | Critical | Reasoning behind recommendations |
| Assumption Register | Critical | Documented assumptions |
| Sensitivity Analysis | Critical | Sensitivity and scenario range |
| Decision Criteria | Critical | Criteria for decision evaluation |
| Operational Impact | Critical | Impact on operations |
| Budget Allocation | High | Budget and funding details |
| Timeline | High | Projected timelines |
| Resource Plan | High | Resource requirements |
| Compliance Check | High | Regulatory compliance |
| Quality Metrics | High | Quality indicators |
| Patient Safety Review | High | Patient safety impact |
| Clinical Evidence | High | Clinical data and evidence |
| Staff Impact | High | Staffing implications |
| Training Plan | Medium | Training requirements |
| Communication Plan | Medium | Communication strategy |
| Change Management | Medium | Change management approach |
| Performance KPIs | Medium | Key performance indicators |
| Monitoring Protocol | Medium | Ongoing monitoring plan |
| Escalation Trigger | Medium | Escalation conditions |
| Governance Review | Medium | Governance approval status |
| Audit Trail | Medium | Audit record requirements |
| Version Control | Medium | Document version history |

## Completeness Rules

1. **Complete**: All critical categories present, coverage = 100%.
2. **Complete with Conditions**: All critical categories present, some conditional categories flagged.
3. **Partial**: One or more critical categories missing, coverage < 100%.
4. **Limited**: Multiple critical categories missing.

## Assessment Method

- `expected_evidence_category_count` = 28
- `available_evidence_category_count` = categories with Present status
- `conditional_evidence_category_count` = categories flagged conditional
- `missing_evidence_category_count` = 28 - available
- `evidence_coverage_pct` = available / 28 * 100
- `critical_missing_evidence_count` = missing categories with Priority = Critical

## Governance

- Missing evidence is logged but not invented.
- Not Applicable categories are excluded from missing counts.
- All assessments are rule-based, not subjective.
