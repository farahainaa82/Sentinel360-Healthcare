# Step 2D-3 Scorecard Priority Methodology

## Primary Ordering Factors

1. **Risk tier** — Critical first, then High, Elevated, Moderate, Low, Monitoring, Not Assessable
2. **Urgency** — Immediate Review, Prompt Review, Routine Review
3. **Breach status** — Active breach before watch
4. **Sustained deterioration** — Sustained movement flagged before transient
5. **Management attention requirement** — Required before optional

## Secondary Ordering Factors

- Decision readiness
- Governance burden
- Evidence completeness
- Financial readiness

## Financial Value Exclusion

Financial value is explicitly **not** the primary ordering criterion. A high-risk package requiring validation may still require immediate management attention even if its financial estimate is incomplete.

## Sort Keys

| Field | Purpose |
|---|---|
| primary_sort_key | Numeric rank of risk tier |
| secondary_sort_key | Numeric rank of urgency |
| tertiary_sort_key | Governance burden severity |

## Priority View Fields

- priority_view_id
- decision_package_id
- approval_package_id
- risk_tier
- urgency
- breach_status
- sustained_movement_flag
- management_attention_required
- decision_readiness
- governance_burden_status
- evidence_status
- financial_readiness
- package_readiness
- primary_sort_key
- secondary_sort_key
- priority_ordering_note
