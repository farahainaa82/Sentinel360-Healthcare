# Step 2B-2 Rule Register

**Step:** 2B-2 — Threshold Breach & Watch Condition Engine  
**Status:** COMPLETE

---

## 1. Breach Rules

**Source:** `config/threshold_breach_rule_config.csv`

| Rule ID | KPI ID | Rule Name | Condition | Breach Type | Priority |
|---------|--------|-----------|-----------|-------------|----------|
| BR001 | kpi_001 | Mortality Rate Upper Red | value > upper_red | BREACH_UPPER_RED | 1 |
| BR002 | kpi_002 | Infection Rate Upper Red | value > upper_red | BREACH_UPPER_RED | 1 |
| BR003 | kpi_003 | Bed Occupancy Critical | value > upper_red or value < lower_red | BREACH_UPPER_RED / BREACH_LOWER_RED | 1 |
| BR004 | kpi_004 | ALOS Upper Red | value > upper_red | BREACH_UPPER_RED | 1 |
| BR005 | kpi_005 | Staffing Ratio Upper Red | value > upper_red | BREACH_UPPER_RED | 1 |
| BR006 | kpi_006 | Patient Experience Lower Red | value < lower_red | BREACH_LOWER_RED | 1 |
| BR007 | (all) | Unavailable Data | calculation_status != 'Calculated' | UNAVAILABLE | 0 |

### Provisional Breach Handling

| KPI | Provisional Flag | Behavior |
|-----|------------------|----------|
| kpi_003 | True | BREACH_PROVISIONAL only when breach_flag == True |
| kpi_005 | True | BREACH_PROVISIONAL only when breach_flag == True |
| Others | False | Specific breach types preserved |

---

## 2. Watch Condition Rules

**Source:** `config/watch_condition_rule_config.csv`

| Rule ID | KPI ID | Rule Name | Trigger Condition | Watch Type | Severity Base |
|---------|--------|-----------|-------------------|------------|---------------|
| WR001 | kpi_001 | Mortality Approaching Upper Amber | value >= green_upper and value < upper_red | APPROACHING_THRESHOLD | HIGH |
| WR002 | kpi_002 | Infection Approaching Upper Amber | value >= green_upper and value < upper_red | APPROACHING_THRESHOLD | HIGH |
| WR003 | kpi_003 | Bed Occupancy Approaching Upper Amber | value >= green_upper and value < upper_red | APPROACHING_THRESHOLD | CRITICAL |
| WR004 | kpi_003 | Bed Occupancy Approaching Lower Amber | value > lower_red and value <= green_lower | APPROACHING_THRESHOLD | MEDIUM |
| WR005 | kpi_004 | ALOS Approaching Upper Amber | value >= green_upper and value < upper_red | APPROACHING_THRESHOLD | MEDIUM |
| WR006 | kpi_005 | Staffing Ratio Approaching Upper Amber | value >= green_upper and value < upper_red | APPROACHING_THRESHOLD | HIGH |
| WR007 | kpi_006 | Patient Experience Approaching Lower Amber | value > lower_red and value <= green_lower | APPROACHING_THRESHOLD | MEDIUM |
| WR008 | (all) | Trend Aligned with Watch | trend_direction matches watch_direction | TREND_ALIGNED | +1 severity level |
| WR009 | (all) | Persistent Watch Condition | consecutive_days >= persistence_threshold | PERSISTENT_CONDITION | +1 severity level |
| WR010 | kpi_003, kpi_005 | Review Date Monitoring | review_date within warning window | REVIEW_DUE | LOW |

---

## 3. Persistence Rules

**Source:** `config/watch_persistence_config.csv`

| Parameter | Value | Description |
|-----------|-------|-------------|
| persistence_window_days | 7 | Maximum days to track a watch condition without reset |
| consecutive_day_threshold | 3 | Days required to escalate to persistent condition |
| reset_on_green | True | Reset persistence if record returns to GREEN |

---

## 4. Confidence Rules

**Source:** `config/watch_confidence_config.csv`

| Parameter | Value | Description |
|-----------|-------|-------------|
| min_confidence_for_watch | 0.7 | Minimum confidence score to flag a watch condition |
| confidence_boost_trend_aligned | 0.15 | Confidence boost when trend aligns |
| max_confidence_cap | 1.0 | Maximum confidence score |

---

## 5. Provisional Threshold Handling Rules

**Source:** `config/provisional_threshold_handling_config.csv`

| Parameter | Value | Description |
|-----------|-------|-------------|
| provisional_kpis | kpi_003, kpi_005 | KPIs with provisional thresholds |
| override_breach_type | True | Override specific breach type with BREACH_PROVISIONAL |
| require_breach_flag | True | Only apply override when breach_flag == True |
| review_warning_days | 30 | Days before review date to trigger warning |

---

## 6. Boundary Inclusivity Rule

**Rule name:** `LOWER_INCLUSIVE_MAX_INCLUSIVE`

**Definition:**
- Lower boundary is inclusive (`>=`)
- Upper boundary is exclusive (`<`)
- Global maximum value is inclusive (`<=`)

**Application:**
- All directionalities (higher-is-better, lower-is-better, context-sensitive)
- All six KPIs
- All threshold candidates

---

## 7. Rule Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-07-27 | Initial rule set created | Step 2B-2 Engine |
| 2026-07-27 | Provisional breach override fixed to require breach_flag == True | Step 2B-2 Engine |

---

## 8. Closure Status

**Step 2B-2:** COMPLETE  
**Step 2B-3 Readiness:** Ready with Conditions
