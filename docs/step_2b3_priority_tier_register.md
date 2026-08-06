# Step 2B-3 Priority Tier Register

**Step:** 2B-3 — Department and KPI Risk Prioritisation Engine  
**Status:** COMPLETE

---

## 1. KPI Priority Tiers

| Tier | Score Range | Interpretation |
|------|-------------|----------------|
| No Current Risk | 0 – 15 | Green or normal band; no meaningful adverse watch |
| Monitor | 15 – 35 | Approaching threshold; low-severity watch; isolated Amber |
| Attention Required | 35 – 55 | Repeated Amber; moderate watch; sustained deterioration |
| High Priority | 55 – 75 | Red breach; high watch; repeated Red; escalating severity |
| Critical Priority | 75 – 100 | Critical Capacity Pressure; critical watch; sustained severe breach |
| Not Assessable | NaN | Unavailable or insufficient evidence |

---

## 2. Department Priority Tiers

| Tier | Score Range | Interpretation |
|------|-------------|----------------|
| Stable | 0 – 15 | Low aggregated risk; no severe outliers |
| Monitor | 15 – 35 | One or more KPIs approaching thresholds |
| Elevated | 35 – 55 | Multiple Amber conditions or moderate watch |
| High | 55 – 75 | Red breaches or high watch conditions present |
| Critical | 75 – 100 | Critical conditions or multiple severe concurrent risks |
| Not Assessable | NaN | Insufficient assessable KPIs |

---

## 3. Urgency Levels

| Urgency | Score Range / Triggers | Interpretation |
|---------|------------------------|----------------|
| Routine Monitoring | 0 – 25; no breach; no sustained deterioration | Standard oversight |
| Review Soon | 25 – 45; repeated Amber; approaching threshold | Schedule review |
| Prompt Review | 45 – 70; Red breach; high watch; multiple concurrent risks | Prioritise review |
| Immediate Review | 70 – 100; Critical Capacity; critical watch; rapid escalation | Urgent attention |
| Not Assessable | NaN | Insufficient evidence; do not ignore but do not rank highly |

---

## 4. Confidence Levels

| Level | Criteria |
|-------|----------|
| High | Calculated KPI; valid threshold; complete evidence and lineage; sufficient trend and persistence history; no blocking data-quality issue |
| Moderate | Calculated KPI; valid threshold; partial trend or persistence evidence; no blocking issue |
| Low | Limited history; volatile or incomplete evidence; provisional governance; warning-level data issue |
| Insufficient Evidence | Unavailable KPI; missing critical threshold; broken evidence or lineage |

---

## 5. Data Availability Status

| Status | Criteria |
|--------|----------|
| Complete | All 6 KPIs assessable |
| Sufficient | At least 4 KPIs assessable |
| Limited | 2–3 KPIs assessable |
| Insufficient | 0–1 KPIs assessable |

---

## 6. Configuration Reference

| Config File | Governs |
|-------------|---------|
| `config/risk_priority_tier_config.csv` | Tier score cut-offs |
| `config/risk_urgency_rule_config.csv` | Urgency thresholds and boolean triggers |
| `config/risk_confidence_config.csv` | Confidence thresholds and multipliers |

All configurations are:
- **Version:** v1.0-draft
- **Status:** Technical Rule
- **Effective date:** 2026-07-27
- **Review date:** 2026-12-31

---

## 7. Closure Status

**Step 2B-3:** COMPLETE  
**Step 2B-4 Readiness:** Ready with Conditions
