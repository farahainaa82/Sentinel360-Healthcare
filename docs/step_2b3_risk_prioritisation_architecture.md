# Step 2B-3 Risk Prioritisation Architecture

**Step:** 2B-3 — Department and KPI Risk Prioritisation Engine  
**Run ID:** RISKPRIOR-20260728055229  
**Status:** COMPLETE

---

## 1. System Overview

Step 2B-3 transforms Step 2B-2 threshold, breach, watch, persistence, trend and governance outputs into actionable risk prioritisation information:

- **KPI-level risk scores:** Normalised 0-100 scores per hospital-department-date-KPI
- **Department-date risk scores:** Aggregated scores with dominant driver identification
- **Hospital-date summaries:** Roll-up of department conditions
- **Deterministic rankings:** Ordered department lists for management review
- **Evidence packs:** Full audit trail for every risk record

The engine answers:
1. Which department needs attention first?
2. Which KPI is driving the risk?
3. How severe is the current condition?
4. Is the condition persistent?
5. Is the condition deteriorating?
6. Is it supported by sufficient evidence?
7. Is any part of the risk based on provisional thresholds?
8. How should departments be ordered for management review?

---

## 2. Data Flow

```
Step 2B-2 Outputs
├── analytical_kpi_watch_conditions.csv      (primary input)
├── analytical_kpi_threshold_classification_daily.csv
├── analytical_kpi_breach_events.csv
├── analytical_kpi_watch_persistence.csv
├── analytical_kpi_breach_trend_integration.csv
├── analytical_kpi_watch_evidence.csv
├── analytical_kpi_watch_lineage.csv
├── analytical_kpi_watch_governance.csv
└── analytical_kpi_watch_daily_summary.csv
         │
         ▼
┌─────────────────────────────────────────────┐
│  KPI Risk Scoring Engine                    │
│  • Component scoring (threshold, breach,    │
│    watch, persistence, trend, sustained,    │
│    statistical signal)                      │
│  • Confidence assignment                    │
│  • Governance adjustment                    │
│  • Normalisation to 0-100                   │
│  • Priority tier and urgency assignment     │
└─────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  Department Risk Prioritisation Engine      │
│  • Aggregation (max, average, concurrence)  │
│  • Dominant / secondary driver identification│
│  • Escalation scoring                       │
│  • Department tier and urgency              │
│  • Deterministic ranking                    │
└─────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  Hospital Risk Summary Engine               │
│  • Department tier counts                   │
│  • Top-three departments and drivers        │
│  • Overall data availability                │
│  • Maximum urgency                          │
└─────────────────────────────────────────────┘
         │
         ▼
12 Analytical Outputs + 18 Validation Outputs
```

---

## 3. Core Engines

### 3.1 KPI Risk Scoring Engine

**File:** `src/kpi_risk_scoring_engine.py`

**Input:** `analytical_kpi_watch_conditions.csv` (primary), merged with classification for boundary consistency.

**Key design:** `threshold_is_provisional` is overridden from the authoritative `config/kpi_threshold_config.csv` to ensure correctness even if Step 2B-2 output contains incorrect values.

**Components (additive, weighted):**
- Threshold severity: Green=0, Amber=20-25, Red=60, Critical Capacity=80, Low Utilisation=15
- Breach: No Breach=0, Provisional Breach=50
- Watch: Informational=5, Low=10, Moderate=20, High=40, Critical=70
- Persistence: base=5, repeated Amber=+10, repeated Red=+20, persistent CCP=+15
- Trend: Improving=-5, Stable=0, Deteriorating=15, Volatile=10
- Sustained movement: 10 if True
- Statistical signal: 10 if True

**Adjustments:**
- Confidence: High=1.0, Moderate=0.95, Low=0.85, Insufficient=0.70
- Governance: Provisional=0.9x, Review Due Soon=0.95x

**Output:** `kpi_risk_score_normalized` (0-100), `kpi_priority_tier`, `urgency_level`, `confidence_level`

### 3.2 Department Risk Prioritisation Engine

**File:** `src/department_risk_prioritisation_engine.py`

**Aggregation formula:**
```
dept_risk_raw = 0.45 * max_kpi_score
              + 0.30 * average_assessable_kpi_score
              + 0.15 * concurrence_score
              + 0.10 * escalation_score
```

**Concurrence rules:**
- Workforce Pressure: kpi_001 + kpi_002
- Capacity-Flow Pressure: kpi_003 + kpi_004
- Flow-Complaint Pressure: kpi_004 + kpi_005
- Complaint-Satisfaction Pressure: kpi_005 + kpi_006
- Staffing-Flow Pressure: kpi_001 + kpi_004

**Dominant driver selection:**
1. Highest normalised KPI risk score
2. Highest confidence score
3. Deterministic KPI ID order

**Ranking:** Deterministic sort by (hospital, date, tier desc, urgency desc, score desc, dept_id asc)

### 3.3 Hospital Risk Summary Engine

**File:** `src/hospital_risk_summary_engine.py`

Aggregates department records into hospital-date summaries with tier counts, top-three departments, and maximum urgency.

---

## 4. Configuration Files

| Config | Purpose |
|--------|---------|
| `config/kpi_risk_weight_config.csv` | Component weights per KPI |
| `config/risk_severity_weight_config.csv` | State/severity to score mappings |
| `config/risk_persistence_weight_config.csv` | Persistence scoring rules |
| `config/risk_trend_weight_config.csv` | Trend interpretation scoring |
| `config/risk_confidence_config.csv` | Confidence thresholds and multipliers |
| `config/department_risk_aggregation_config.csv` | Aggregation weights |
| `config/risk_priority_tier_config.csv` | Tier cut-offs |
| `config/risk_urgency_rule_config.csv` | Urgency thresholds and triggers |
| `config/risk_governance_adjustment_config.csv` | Provisional/review-due adjustments |
| `config/risk_ranking_tiebreaker_config.csv` | Tie-breaker priority order |

---

## 5. Models & Enums

**File:** `src/risk_prioritisation_models.py`

| Enum | Values |
|------|--------|
| `ConfidenceLevel` | High, Moderate, Low, Insufficient Evidence |
| `PriorityTier` | No Current Risk, Monitor, Attention Required, High Priority, Critical Priority, Not Assessable |
| `UrgencyLevel` | Routine Monitoring, Review Soon, Prompt Review, Immediate Review, Not Assessable |
| `DataAvailabilityStatus` | Complete, Sufficient, Limited, Insufficient |
| `IssueCategory` | 16 categories covering missing records, invalid weights, broken links, etc. |
| `IssueSeverity` | Warning, Blocking |

---

## 6. Analytical Outputs (12)

| File | Description |
|------|-------------|
| `analytical_kpi_risk_scores_daily.csv` | KPI-level risk scores, tiers, urgency |
| `analytical_kpi_risk_components.csv` | Component-level breakdown for audit |
| `analytical_department_risk_daily.csv` | Department-date risk aggregation |
| `analytical_department_risk_ranking.csv` | Deterministic department rankings |
| `analytical_department_risk_drivers.csv` | Dominant and secondary driver details |
| `analytical_department_risk_concurrence.csv` | Multi-KPI concurrence records |
| `analytical_department_risk_confidence.csv` | Department confidence and data availability |
| `analytical_department_risk_governance.csv` | Provisional flags and governance warnings |
| `analytical_department_risk_evidence.csv` | Evidence pack linkage |
| `analytical_department_risk_lineage.csv` | Data lineage records |
| `analytical_hospital_risk_daily_summary.csv` | Hospital-date summaries |
| `analytical_risk_prioritisation_issues.csv` | Issue log (empty if clean) |

---

## 7. Validation Outputs (18)

All files in `outputs/risk_prioritisation/`:

1. `risk_prioritisation_run_summary.csv`
2. `risk_prioritisation_schema_validation.csv`
3. `risk_prioritisation_key_validation.csv`
4. `risk_prioritisation_source_reconciliation.csv`
5. `risk_prioritisation_score_range_validation.csv`
6. `risk_prioritisation_component_reconciliation.csv`
7. `risk_prioritisation_tier_validation.csv`
8. `risk_prioritisation_urgency_validation.csv`
9. `risk_prioritisation_ranking_validation.csv`
10. `risk_prioritisation_driver_validation.csv`
11. `risk_prioritisation_confidence_validation.csv`
12. `risk_prioritisation_provisional_governance_validation.csv`
13. `risk_prioritisation_evidence_validation.csv`
14. `risk_prioritisation_lineage_validation.csv`
15. `risk_prioritisation_immutability_verification.csv`
16. `risk_prioritisation_issue_log.csv`
17. `risk_prioritisation_warning_register.csv`
18. `risk_prioritisation_run_manifest.json`

---

## 8. Key Metrics

| Metric | Value |
|--------|-------|
| Total source KPI records | 17,520 |
| KPI risk records generated | 17,520 |
| Assessable KPI risk records | 11,397 |
| Unavailable / Not Assessable | 6,123 |
| Department-date risk records | 2,920 |
| Hospital-date summary records | 365 |
| Ranked department records | 2,920 |
| KPI risk score minimum | 0.0 |
| KPI risk score maximum | 100.0 |
| Department risk score minimum | 0.0 |
| Department risk score maximum | 100.0 |

---

## 9. Performance Characteristics

| Characteristic | Observation |
|----------------|-------------|
| Engine runtime | < 30 seconds |
| Test runtime | ~16 seconds (60 tests) |
| Design | Module-scoped fixtures, pre-generated outputs |

---

## 10. Closure Status

**Step 2B-3:** COMPLETE  
**Step 2B-4 Readiness:** Ready with Conditions
