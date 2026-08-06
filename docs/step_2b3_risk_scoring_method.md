# Step 2B-3 Risk Scoring Method

**Step:** 2B-3 — Department and KPI Risk Prioritisation Engine  
**Status:** COMPLETE

---

## 1. Scoring Philosophy

The KPI risk score is transparent, additive, and configuration-driven. Every component is independently explainable. No black-box machine learning is used. All weights and mappings are governed by configuration files.

---

## 2. Component Scoring

### 2.1 Threshold-Severity Component

Maps the current threshold state to a raw score:

| State | Score | Rationale |
|-------|-------|-----------|
| Green / Normal Operating Band | 0 | No adverse state |
| Lower Amber | 20 | Moderate low-side concern |
| Amber / Upper Amber | 25 | Moderate high-side concern |
| Red | 60 | High severity breach |
| Critical Capacity Pressure | 80 | Maximum severity |
| Low Utilisation | 15 | Context-sensitive; not neutral |
| Unavailable | NaN | Not assessable |

**Config:** `config/risk_severity_weight_config.csv`

### 2.2 Breach Component

| Breach Type | Score | Rationale |
|-------------|-------|-----------|
| No Breach | 0 | No breach contribution |
| Provisional Breach | 50 | Significant but flagged as provisional |
| Unavailable | NaN | Not assessable |

**Config:** `config/risk_severity_weight_config.csv`

### 2.3 Watch-Severity Component

| Watch Severity | Score | Rationale |
|----------------|-------|-----------|
| None / missing | 0 | No watch contribution |
| Informational | 5 | Minimal attention |
| Low | 10 | Small contribution |
| Moderate | 20 | Meaningful contribution |
| High | 40 | Strong contribution |
| Critical | 70 | Maximum watch contribution |

**Config:** `config/risk_severity_weight_config.csv`

### 2.4 Persistence Component

| Condition | Score | Rationale |
|-----------|-------|-----------|
| persistence_count = 0 | 0 | Isolated event |
| persistence_count >= 1 | 5 | Base persistence |
| repeated_amber_flag = True | +10 | Repeated amber escalation |
| repeated_red_flag = True | +20 | Repeated red escalation |
| persistent Critical Capacity | +15 | Sustained maximum pressure |

**Config:** `config/risk_persistence_weight_config.csv`

### 2.5 Trend Component

| Trend Interpretation | Score | Rationale |
|----------------------|-------|-----------|
| Improving | -5 | Slight risk reduction |
| Stable | 0 | Neutral |
| Deteriorating | 15 | Increased contribution |
| Volatile | 10 | Moderate uncertainty |
| Insufficient Evidence | 0 | Neutral |

**Directionality is respected:**
- Higher-is-better KPIs: upward movement = improvement (unless watch says otherwise)
- Lower-is-better KPIs: downward movement = improvement
- Bed Occupancy: movement toward Normal Operating Band = improvement

**Config:** `config/risk_trend_weight_config.csv`

### 2.6 Sustained Movement Component

| Flag | Score |
|------|-------|
| False | 0 |
| True | 10 |

### 2.7 Statistical Signal Component

| Flag | Score |
|------|-------|
| False | 0 |
| True | 10 |

---

## 3. Raw Score Calculation

```
kpi_risk_score_raw = (
    threshold_component_score
  + breach_component_score
  + watch_component_score
  + persistence_component_score
  + trend_component_score
  + sustained_movement_component_score
  + statistical_signal_component_score
) * confidence_adjustment * governance_adjustment
```

Unavailable records receive `NaN` for the raw score and all components.

---

## 4. Confidence Adjustment

| Confidence Level | Multiplier | Rationale |
|------------------|------------|-----------|
| High | 1.00 | Full weight |
| Moderate | 0.95 | Slight reduction |
| Low | 0.85 | Material reduction |
| Insufficient Evidence | 0.70 | Heavy reduction |

**Confidence assignment rules:**
- `Insufficient Evidence`: calculation_status != 'Calculated'
- `High`: Calculated, non-provisional, evidence + lineage present, trend_confidence >= 0.70
- `Moderate`: Calculated, evidence present, partial trend/lineage
- `Low`: Calculated but limited history, volatile, or provisional threshold

**Config:** `config/risk_confidence_config.csv`

---

## 5. Governance Adjustment

| Condition | Multiplier | Rationale |
|-----------|------------|-----------|
| Provisional threshold | 0.90 | Discount for unapproved threshold |
| Review due soon / overdue | 0.95 | Additional caution |

Both multipliers are applied sequentially if conditions overlap.

**Config:** `config/risk_governance_adjustment_config.csv`

---

## 6. Normalisation

Assessable records are linearly scaled to 0-100 using the dataset min/max:

```
normalized = (raw_score - raw_min) / (raw_max - raw_min) * 100
```

If all assessable records have identical raw scores, normalized = 0.

Unavailable records receive `NaN`.

---

## 7. Priority Tier Assignment

| Tier | Normalised Score Range |
|------|------------------------|
| No Current Risk | 0 – 15 |
| Monitor | 15 – 35 |
| Attention Required | 35 – 55 |
| High Priority | 55 – 75 |
| Critical Priority | 75 – 100 |
| Not Assessable | NaN |

**Config:** `config/risk_priority_tier_config.csv`

---

## 8. Urgency Assignment

Urgency is assigned independently from the priority tier, using both the normalised score and specific triggers:

| Urgency | Score Range | Triggers |
|---------|-------------|----------|
| Routine Monitoring | 0 – 25 | No breach, no sustained deterioration |
| Review Soon | 25 – 45 | Repeated Amber, approaching threshold |
| Prompt Review | 45 – 70 | Red breach, high watch, multiple concurrent risks |
| Immediate Review | 70 – 100 | Critical Capacity, critical watch, rapid escalation |
| Not Assessable | NaN | Insufficient evidence |

**Config:** `config/risk_urgency_rule_config.csv`

---

## 9. Department Aggregation

```
dept_risk_raw = 0.45 * max_kpi_risk_score
              + 0.30 * average_assessable_kpi_risk_score
              + 0.15 * concurrence_score
              + 0.10 * escalation_score
```

- **Max KPI weight (0.45):** Ensures severe outliers are not hidden by averaging.
- **Average weight (0.30):** Rewards broad-based good performance.
- **Concurrence weight (0.15):** Elevates departments with multiple concurrent KPI risks.
- **Escalation weight (0.10):** Captures repeated breaches and deteriorating trends.

Normalised to 0-100 using dataset min/max.

**Config:** `config/department_risk_aggregation_config.csv`

---

## 10. Tie-Breaker Rules

For dominant driver selection and ranking:

1. Higher normalised risk score
2. Higher priority tier
3. Critical before Red
4. Red before Amber
5. Greater persistence count
6. Deteriorating before stable
7. Higher confidence level
8. Non-provisional before provisional
9. Deterministic KPI ID / department ID

**Config:** `config/risk_ranking_tiebreaker_config.csv`

---

## 11. Evidence and Lineage

Every KPI risk record and every department risk record receives:
- `evidence_pack_id`: UUID linking to evidence details
- `kpi_risk_record_id` / `department_risk_record_id`: UUID for the risk record
- `engine_run_id`: Run identifier
- `processed_at`: Timestamp

Source record IDs, rule IDs, threshold versions, and lineage IDs are preserved from Step 2B-2.

---

## 12. Closure Status

**Step 2B-3:** COMPLETE  
**Step 2B-4 Readiness:** Ready with Conditions
