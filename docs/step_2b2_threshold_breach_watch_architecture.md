# Step 2B-2 Threshold Breach & Watch Condition Architecture

**Step:** 2B-2  
**Scope:** Threshold breach detection, watch condition evaluation, persistence, trend integration, and provisional governance  
**Status:** COMPLETE

---

## 1. System Overview

Step 2B-2 consumes the six integrated KPIs from the analytical layer and evaluates each record against human-approved active thresholds. It produces:

- **Breach classifications:** Green/Amber/Red state assignments with breach-flag logic
- **Watch conditions:** Approaching-threshold alerts, persistence tracking, severity scoring
- **Trend integration:** Overlay of trend signals onto breach/watch contexts
- **Governance outputs:** Provisional threshold handling, review-date monitoring, issue logging

---

## 2. Data Flow

```
┌─────────────────────────────────────┐
│  analytical_six_kpi_daily.csv       │
│  (17,520 source records)            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  kpi_threshold_config.csv           │
│  (active human-approved thresholds) │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  KPI Threshold Breach Engine        │
│  • classify_all_records()           │
│  • detect_breaches()                │
│  • vectorised G-A-R classification  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  KPI Watch Condition Engine         │
│  • evaluate_watch_conditions()      │
│  • persistence logic                │
│  • trend integration                │
│  • severity assignment              │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  10 analytical outputs              │
│  16 validation outputs              │
└─────────────────────────────────────┘
```

---

## 3. Core Engines

### 3.1 KPI Threshold Breach Engine

**File:** `src/kpi_threshold_breach_engine.py`

**Key functions:**
- `classify_all_records()` — vectorised classification of all source records
- `detect_breaches()` — applies breach rules and provisional governance

**Classification logic:**
- **Higher-is-better:** `lower_red < green_lower <= value <= green_upper < upper_red`
- **Lower-is-better:** `lower_red < green_lower <= value <= green_upper < upper_red`
- **Context-sensitive (kpi_003):** Five bands — Low Utilisation, Lower Amber, Normal Operating Band, Upper Amber, Critical Capacity Pressure

**Boundary inclusivity rule:** `LOWER_INCLUSIVE_MAX_INCLUSIVE` — lower boundary inclusive, upper exclusive, global maximum inclusive.

### 3.2 KPI Watch Condition Engine

**File:** `src/kpi_watch_condition_engine.py`

**Key functions:**
- `evaluate_watch_conditions()` — evaluates approaching-threshold logic, persistence, trend integration, severity

**Persistence:**
- Groups by `(hospital_id, department_id, kpi_id)`
- Tracks watch start date, duration, consecutive days
- Applies persistence parameters from `config/watch_persistence_config.csv`

**Trend integration:**
- Merges trend signals from `analytical_kpi_trend_signals.csv`
- Enhances watch severity when trend direction aligns with watch direction

**Severity levels:** `Low`, `Medium`, `High`, `Critical`

---

## 4. Configuration Files

| Config | Purpose |
|--------|---------|
| `config/threshold_breach_rule_config.csv` | 7 breach rules |
| `config/watch_condition_rule_config.csv` | 10 watch rules |
| `config/watch_persistence_config.csv` | Persistence parameters |
| `config/watch_confidence_config.csv` | Confidence thresholds |
| `config/provisional_threshold_handling_config.csv` | Provisional handling rules |

---

## 5. Models & Enums

**File:** `src/threshold_breach_models.py`

| Enum | Values |
|------|--------|
| `ThresholdState` | `GREEN`, `AMBER_LOWER`, `AMBER_UPPER`, `RED_LOWER`, `RED_UPPER`, `UNAVAILABLE` |
| `BreachType` | `NO_BREACH`, `BREACH_LOWER_RED`, `BREACH_UPPER_RED`, `BREACH_PROVISIONAL`, `UNAVAILABLE` |
| `WatchConditionType` | `APPROACHING_THRESHOLD`, `TREND_ALIGNED`, `PERSISTENT_CONDITION`, `REVIEW_DUE` |
| `WatchSeverity` | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `TrendInterpretation` | `IMPROVING`, `STABLE`, `WORSENING`, `VOLATILE` |
| `ReviewDueStatus` | `NOT_DUE`, `DUE_SOON`, `OVERDUE` |
| `OperationalUseStatus` | `ACTIVE`, `PROVISIONAL`, `DEPRECATED` |
| `GovernanceWarning` | `NONE`, `PROVISIONAL_THRESHOLD`, `REVIEW_OVERDUE` |

---

## 6. Outputs

### 6.1 Analytical Outputs (10)

| File | Description |
|------|-------------|
| `analytical_kpi_threshold_classification_daily.csv` | Daily G-A-R classification per record |
| `analytical_kpi_breach_events.csv` | Breach events with type and flag |
| `analytical_kpi_watch_conditions.csv` | Watch condition evaluations |
| `analytical_kpi_watch_persistence.csv` | Watch persistence tracking |
| `analytical_kpi_breach_trend_integration.csv` | Trend signals merged with breaches |
| `analytical_kpi_watch_evidence.csv` | Watch evidence audit trail |
| `analytical_kpi_watch_lineage.csv` | Data lineage for watch outputs |
| `analytical_kpi_watch_governance.csv` | Governance flags and review dates |
| `analytical_kpi_watch_issues.csv` | Issue log (empty if clean) |
| `analytical_kpi_watch_daily_summary.csv` | Daily aggregated summaries |

### 6.2 Validation Outputs (16)

| File | Description |
|------|-------------|
| `threshold_watch_run_summary.csv` | High-level run metrics |
| `threshold_watch_record_reconciliation.csv` | Record count reconciliation |
| `threshold_watch_run_manifest.json` | Machine-readable run manifest |
| `threshold_watch_classification_distribution.csv` | G-A-R distribution |
| `threshold_watch_breach_distribution.csv` | Breach type distribution |
| `threshold_watch_watch_severity_distribution.csv` | Watch severity distribution |
| `threshold_watch_kpi_level_summary.csv` | Per-KPI summary |
| `threshold_watch_hospital_level_summary.csv` | Per-hospital summary |
| `threshold_watch_provisional_governance_summary.csv` | Provisional threshold summary |
| `threshold_watch_daily_summary_stats.csv` | Daily summary statistics |
| `threshold_watch_classification_vs_breach_crosscheck.csv` | Cross-validation |
| `threshold_watch_unavailable_records_analysis.csv` | Unavailable record analysis |
| `threshold_watch_trend_integration_summary.csv` | Trend integration summary |
| `threshold_watch_persistence_summary.csv` | Persistence summary |
| `threshold_watch_issue_log.csv` | Issue log |
| `threshold_watch_step_2b2_readiness_assessment.csv` | Readiness assessment |

---

## 7. Provisional Governance

Two KPIs retain provisional thresholds:

| KPI | Status | Review Date |
|-----|--------|-------------|
| kpi_003 (Bed Occupancy) | Conditionally Approved | Monitored |
| kpi_005 (Staffing Ratio) | Conditionally Approved | Monitored |

Provisional breaches are flagged with `BREACH_PROVISIONAL` only when `breach_flag == True`. Non-provisional records retain specific breach types.

---

## 8. Key Metrics

| Metric | Value |
|--------|-------|
| Total source records | 17,520 |
| Classifiable records | 11,397 |
| Unavailable records | 6,123 |
| Actual breach events | 2,464 |
| Actual watch conditions | 9,120 |
| Daily summaries | 2,920 |
| Issues | 0 |

---

## 9. Performance Characteristics

| Characteristic | Observation |
|----------------|-------------|
| Test runtime | ~29 minutes (22 tests) |
| Cause | Each test independently reloads inputs and re-runs engine logic |
| Severity | Non-blocking |
| Future optimization | Shared fixtures, cached datasets, test separation |

---

## 10. Closure Status

**Step 2B-2:** COMPLETE  
**Step 2B-3 Readiness:** Ready with Conditions
