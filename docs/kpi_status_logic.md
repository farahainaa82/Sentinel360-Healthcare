# KPI Status Logic

## Purpose

This document defines the formal status-classification framework for Sentinel360 Healthcare KPIs. Status classification translates calculated KPI values into management-readable states using approved, effective-dated threshold configuration. It establishes the rules for assigning statuses, handling missing data, evaluating trends and communicating confidence to decision-makers.

No numerical threshold values are defined in this document. All boundary values remain pending approval and must be supplied through configuration.

---

## 1. Approved Status Categories

The following status categories are approved for use across all six headline KPIs:

| Status | Meaning |
|---|---|
| Normal | The calculated KPI value is within the approved acceptable range for the hospital, department and reporting period. |
| Watch | The value remains within or near the acceptable boundary but shows emerging risk, deterioration or connected-domain exposure that warrants management attention. |
| Warning | The value breaches the approved warning boundary. Management review and potential intervention are indicated. |
| Critical | The value breaches the approved critical boundary. Immediate management attention and escalation are required. |
| Not Available | Required source data or the denominator is unavailable. No KPI value can be calculated. |
| Insufficient Data | Data exist but do not meet the minimum quantity, volume or history requirements for a reliable calculation. |
| Data Quality Review Required | The calculation is blocked or qualified by unresolved validation issues, duplicates, schema failures or master-data misalignment. |

### Status Descriptions

**Normal**
The KPI has been calculated successfully, data quality is acceptable and the value falls within the approved acceptable range. No immediate management action is required based on this KPI alone. Normal status does not eliminate the need for ongoing monitoring.

**Watch**
Watch is a proactive status that signals emerging concern before a threshold breach occurs. It may be triggered by approved rules such as approaching a warning boundary, persistent deterioration, repeated volatility, connected-domain warning, forecast threshold crossing or low-confidence early signal. Watch must not be created from an invented numerical threshold. All Watch rules must be configuration-driven and traceable.

**Warning**
The KPI value has crossed the approved warning boundary in the adverse direction. This status indicates that performance has degraded to a level requiring management review. Intervention planning should be considered. Warning status must be based on an approved, effective-dated threshold configuration.

**Critical**
The KPI value has crossed the approved critical boundary in the adverse direction. This status indicates severe performance degradation requiring immediate management attention, escalation and likely intervention. Critical status must be based on an approved, effective-dated threshold configuration.

**Not Available**
The KPI cannot be calculated because required source data, the denominator or an approved threshold is missing. This status is informational and does not imply good or bad performance. The missing input must be identified and disclosed.

**Insufficient Data**
Some data exist but the volume, completeness or history does not meet the approved minimum for reliable calculation. This status protects against misleading conclusions from sparse or immature data. The shortfall must be identified and disclosed.

**Data Quality Review Required**
The calculation encountered unresolved data-quality failures that prevent a trustworthy result. Examples include critical schema violations, unresolvable duplicate records, master-data misalignment or validation rule breaches. This status blocks the KPI until the quality issue is resolved.

---

## 2. Threshold Direction Logic

KPI performance direction determines how calculated values are compared against thresholds. Three patterns are supported:

### A. Higher Is Better

For KPIs where higher values indicate better performance (e.g., Staffing Level, Patient Satisfaction Score):

- **Normal:** Value is at or above the approved acceptable boundary.
- **Warning:** Value is below the approved warning boundary.
- **Critical:** Value is below the approved critical boundary.

The warning boundary is positioned between the critical boundary and the acceptable boundary. Watch may be assigned when the value is approaching the warning boundary from above.

### B. Lower Is Better

For KPIs where lower values indicate better performance (e.g., Staff Absenteeism Rate, Bed Occupancy Rate, Average Patient Waiting Time, Patient Complaint Rate):

- **Normal:** Value is at or below the approved acceptable boundary.
- **Warning:** Value is above the approved warning boundary.
- **Critical:** Value is above the approved critical boundary.

The warning boundary is positioned between the acceptable boundary and the critical boundary. Watch may be assigned when the value is approaching the warning boundary from below.

### C. Target Range

For KPIs where an approved target range defines acceptable performance (e.g., Bed Occupancy Rate if an approved range is later defined):

- **Normal:** Value is within the approved lower and upper range.
- **Warning:** Value is outside the approved warning range (either below the lower warning boundary or above the upper warning boundary).
- **Critical:** Value is outside the approved critical range (either below the lower critical boundary or above the upper critical boundary).

Watch may be assigned when the value is approaching either boundary of the warning range.

**Important:** No numerical values for boundaries are defined in this document. All boundary values are pending approval and must be stored in `kpi_threshold_config`.

---

## 3. Threshold Precedence

When evaluating a KPI, the following precedence order must be applied:

```
Data Quality Review Required
→ Not Available
→ Insufficient Data
→ Critical
→ Warning
→ Watch
→ Normal
```

### Rationale

Data eligibility must be assessed before numerical status classification because:

1. A calculation based on poor-quality data can mislead management regardless of the numerical value.
2. Missing data must be disclosed before any performance judgment is offered.
3. Insufficient sample size can produce unstable or unrepresentative values.
4. Only after data quality, availability and volume are confirmed should the numerical value be compared against thresholds.

This precedence ensures that management receives an honest assessment of whether the KPI can be trusted before being asked to respond to its value.

---

## 4. Watch-Status Logic

Watch is the most context-sensitive status. It must not be created from an invented numerical threshold. Watch may be assigned through approved, configuration-driven rules such as:

- **Approaching a warning boundary:** The KPI value is within an approved tolerance of the warning boundary, moving in the adverse direction.
- **Persistent deterioration:** The KPI has moved adversely for an approved number of consecutive periods, even if still within the normal range.
- **Repeated volatility:** The KPI has oscillated across an approved magnitude for an approved number of periods, indicating instability.
- **Connected-domain warning:** Another KPI in a connected domain has reached Warning or Critical, and this KPI is trending adversely (e.g., rising absenteeism when staffing level is already low).
- **Forecast threshold crossing:** A forecast model projects that this KPI will cross a warning or critical boundary within an approved horizon.
- **Low-confidence early signal:** Data are sparse or new, but the available signal suggests adverse movement.

All Watch rules must be:
- Stored in configuration (`kpi_threshold_config` or a dedicated Watch-rule configuration).
- Traceable to a specific rule identifier.
- Reviewable and auditable.
- Approved by human management before activation.

Watch status must be accompanied by a clear reason explaining which rule triggered it.

---

## 5. Department and Hospital Thresholds

The framework supports three levels of threshold specificity:

| Level | Scope | Precedence |
|---|---|---|
| Global | Applies to all hospitals and departments unless overridden. | Lowest |
| Hospital-specific | Applies to a specific hospital, overriding the global threshold. | Medium |
| Department-specific | Applies to a specific department within a hospital, overriding both. | Highest |

### Precedence Rule

```
Department-specific threshold
→ Hospital-specific threshold
→ Global threshold
```

If a department-specific threshold exists and is active, it takes precedence. If not, the hospital-specific threshold is used. If neither exists, the global threshold applies.

### Effective Dating

Only active, approved and effective-dated threshold records may be used. A threshold record is eligible if:
- `is_active = true`
- `approval_status = Approved`
- Reporting period falls within `effective_date` to `expiry_date` (if expiry_date is set)

If multiple eligible records exist at the same specificity level, the most recent `effective_date` takes precedence.

---

## 6. Boundary Inclusivity

The exact treatment of boundary values must be explicitly defined. For every threshold boundary, the configuration must specify whether the comparison uses:

- Greater than (`>`)
- Greater than or equal to (`>=`)
- Less than (`<`)
- Less than or equal to (`<=`)

This applies to all boundaries: acceptable, warning and critical.

**Example (conceptual, no values assigned):**

For a Lower Is Better KPI with a warning boundary of `W` and critical boundary of `C`:
- If boundary inclusivity is `>=` for warning: values equal to `W` trigger Warning.
- If boundary inclusivity is `>` for warning: values must exceed `W` to trigger Warning.

The exact inclusivity setting for each KPI and each boundary must be stored in configuration or approved in Phase 1, Step 1G. Do not make an undocumented assumption.

---

## 7. Missing Threshold Handling

If an approved threshold is unavailable for a KPI at the required level (department, hospital or global):

1. Calculate the KPI value if the underlying data are valid and eligible.
2. Set the threshold status to `Not Available`.
3. Mark `Manual Review Required`.
4. Do not assign `Normal`, `Warning` or `Critical`.

This ensures that:
- A valid KPI value is still available for manual review.
- The absence of a threshold is disclosed.
- No default or invented threshold is silently applied.

---

## 8. Persistence Logic

Persistence tracks how long a KPI has remained in an adverse status. The following conceptual fields are defined for future implementation:

| Field | Purpose |
|---|---|
| `consecutive_warning_periods` | Count of consecutive reporting periods in Warning status. |
| `consecutive_critical_periods` | Count of consecutive reporting periods in Critical status. |
| `consecutive_breach_periods` | Count of consecutive periods in either Warning or Critical. |
| `deterioration_streak` | Count of consecutive periods with adverse trend direction. |
| `improvement_streak` | Count of consecutive periods with favourable trend direction. |
| `status_change_date` | Date when the KPI last changed status category. |

These fields support:
- Evaluation of persistent problems versus transient spikes.
- Triggering of Watch rules based on duration.
- Reporting of how long a situation has been adverse.

The exact calculation windows and reset conditions are pending approval.

---

## 9. Trend Direction

Trend direction describes the movement of the KPI value over time, interpreted in the context of the KPI's performance direction.

| Trend Direction | Meaning |
|---|---|
| Improving | The KPI is moving in the favourable direction relative to its performance direction. |
| Stable | The KPI has not moved beyond an approved tolerance. |
| Worsening | The KPI is moving in the adverse direction relative to its performance direction. |
| Volatile | The KPI has oscillated beyond an approved magnitude across recent periods. |
| Not Available | Insufficient history to determine trend. |

### Interpretation by Performance Direction

**Higher Is Better (e.g., Staffing Level, Patient Satisfaction Score):**
- Increasing value → may be Improving.
- Decreasing value → may be Worsening.

**Lower Is Better (e.g., Staff Absenteeism Rate, Bed Occupancy Rate, Waiting Time, Complaint Rate):**
- Increasing value → may be Worsening.
- Decreasing value → may be Improving.

Trend direction must not use raw increase or decrease alone without considering the KPI's performance direction. An "increase" in Absenteeism is adverse; an "increase" in Satisfaction is favourable.

---

## 10. Deterioration Logic

Deterioration identifies adverse movement beyond simple period-to-period change. Deterioration may later be based on:

- **Adverse month-on-month movement:** The KPI has moved in the adverse direction by more than an approved tolerance.
- **Repeated adverse movement:** The KPI has moved adversely for an approved number of consecutive periods.
- **Movement toward a warning boundary:** The KPI is approaching a warning boundary and the distance has reduced by more than an approved tolerance.
- **Warning-to-critical transition:** The KPI has moved from Warning to Critical.
- **Forecast exposure:** A forecast indicates that the KPI is projected to reach Warning or Critical within an approved horizon.

Deterioration logic must be configuration-driven and must not rely on invented numerical tolerances.

---

## 11. Anomaly versus Threshold Distinction

It is essential to distinguish between threshold status and anomaly detection:

| Aspect | Threshold Status | Anomaly Detection |
|---|---|---|
| Comparison basis | Approved business boundary | Expected statistical behaviour |
| Nature | Rule-based | Model-based |
| Trigger | Value crosses a configured boundary | Value deviates from predicted distribution |
| Possible scenarios | A KPI may breach a threshold without being anomalous (e.g., gradual deterioration). | A KPI may be anomalous without breaching a threshold (e.g., unexpected spike within normal range). |

### Key Rules

- Threshold breach compares performance against an approved business boundary.
- Anomaly detection compares an observation against expected statistical behaviour.
- A KPI may breach a threshold without being anomalous.
- A KPI may be anomalous without breaching a threshold.
- Both threshold status and anomaly flag must be stored separately in the KPI output.
- Anomaly detection must not override threshold status in the precedence order.

---

## 12. Status-Confidence Logic

Confidence describes the reliability of the KPI calculation and its status classification.

| Confidence Level | Meaning |
|---|---|
| High | Data are complete, volume is adequate, quality checks pass and the calculation is straightforward. |
| Medium | Minor data gaps or quality issues exist, but the calculation remains usable with disclosure. |
| Low | Significant data gaps, low volume or quality concerns reduce reliability; the result should be interpreted cautiously. |
| Not Available | No confidence assessment is possible due to missing data or blocked calculation. |

### Confidence Factors

Confidence may consider:
- Data completeness percentage.
- Denominator volume relative to approved minimum.
- Survey-response volume (for satisfaction).
- History sufficiency for trend calculation.
- Data quality validation results.
- Model confidence (for forecast-related Watch rules).
- Assumption confidence (for fallback methods).

Confidence scoring values and algorithms are pending approval.

---

## 13. Status Explanation Requirements

Every displayed status should be accompanied by structured evidence to enable informed management decisions:

| Evidence Element | Description |
|---|---|
| Latest KPI value | The calculated numerical value. |
| Unit | The unit of measurement (percent, minutes, etc.). |
| Threshold basis | Which threshold was applied (global, hospital-specific, department-specific). |
| Breached boundary | If applicable, which boundary was crossed (warning, critical). |
| Magnitude beyond boundary | How far the value is from the boundary (if applicable). |
| Previous-period value | The KPI value for the prior reporting period. |
| Trend direction | Improving, Stable, Worsening, Volatile or Not Available. |
| Persistence | Consecutive periods in the current or adverse status. |
| Anomaly flag | Whether the value is flagged as anomalous. |
| Data confidence | High, Medium, Low or Not Available. |
| Analytical limitation | Any caveats, fallback methods or unresolved data issues. |

---

## 14. Status Examples (Conceptual, No Numerical Thresholds)

### Example 1: Staffing Level

> The calculated Staffing Level value is below the approved warning boundary and has deteriorated for three consecutive reporting periods. The status is Warning. Trend direction is Worsening. Persistence shows three consecutive breach periods. Data confidence is High. The threshold applied is the department-specific approved threshold effective from the start of the current quarter.

### Example 2: Patient Complaint Rate

> The Patient Complaint Rate remains inside the warning range but a forecast model projects that it will cross the critical boundary within the next seven days. The status is Watch due to forecast threshold crossing. Trend direction is Worsening. Data confidence is Medium due to a 15% gap in encounter records for the current period.

### Example 3: Bed Occupancy Rate

> The Bed Occupancy Rate is currently within the normal range based on its own numerical value. However, Average Patient Waiting Time has reached Critical and Staffing Level has reached Warning, indicating connected-domain pressure. The Bed Occupancy status is elevated to Watch due to connected-domain warning. Data confidence is High.

### Example 4: Patient Satisfaction Score

> The Patient Satisfaction Score cannot be calculated because no valid survey responses were received for the reporting period. The status is Insufficient Data. Data confidence is Not Available. Management is advised to review survey collection processes.

---

## 15. Status-Classification Pseudocode

The following pseudocode describes the conceptual logic for assigning a status. It is not executable code.

```
function classify_kpi_status(kpi_calculation_result):

    # Step 1: Validate eligibility
    validate_eligibility(kpi_calculation_result)

    # Step 2: Data quality check (highest precedence)
    if unresolved_critical_data_quality_failure exists:
        status = "Data Quality Review Required"
        reason = "Unresolved critical validation failure"
        confidence = "Not Available"
        return build_status_output(status, reason, confidence)

    # Step 3: Input availability check
    elif required_input_or_denominator is unavailable:
        status = "Not Available"
        reason = "Required data or denominator missing"
        confidence = "Not Available"
        return build_status_output(status, reason, confidence)

    # Step 4: Minimum data volume check
    elif minimum_sample_or_history_requirement is not met:
        status = "Insufficient Data"
        reason = "Data volume below approved minimum"
        confidence = "Low"
        return build_status_output(status, reason, confidence)

    # Step 5: Numerical status classification
    else:
        # Load approved effective threshold
        threshold = load_approved_effective_threshold(
            kpi_code = kpi_calculation_result.kpi_code,
            hospital_id = kpi_calculation_result.hospital_id,
            department_id = kpi_calculation_result.department_id,
            reporting_period = kpi_calculation_result.reporting_period
        )

        if no approved threshold exists:
            status = "Not Available"
            manual_review = true
            reason = "No approved threshold available"
            confidence = assess_confidence(kpi_calculation_result)
            return build_status_output(status, reason, confidence, manual_review)

        else:
            # Classify based on performance direction and threshold
            status = classify_numerical_status(
                kpi_value = kpi_calculation_result.kpi_value,
                performance_direction = kpi_calculation_result.performance_direction,
                threshold = threshold
            )

            # Evaluate configured Watch rules
            watch_reason = evaluate_watch_rules(
                kpi_calculation_result = kpi_calculation_result,
                threshold = threshold
            )

            if watch_reason is not null and status is less severe than "Watch":
                status = "Watch"
                reason = watch_reason
            else:
                reason = build_threshold_reason(status, threshold)

            confidence = assess_confidence(kpi_calculation_result)
            trend = calculate_trend_direction(kpi_calculation_result)
            persistence = calculate_persistence(kpi_calculation_result)
            anomaly = detect_anomaly(kpi_calculation_result)

            return build_status_output(
                status = status,
                reason = reason,
                confidence = confidence,
                trend = trend,
                persistence = persistence,
                anomaly = anomaly,
                threshold_version = threshold.version,
                calculation_version = kpi_calculation_result.calculation_version
            )
```

### Return Object Structure

The status-classification function must return:

- `numerical_status`: The assigned status category.
- `management_status`: Human-readable summary of the status and reason.
- `status_reason`: Detailed explanation of why this status was assigned.
- `confidence`: High, Medium, Low or Not Available.
- `threshold_version`: Identifier of the threshold configuration used.
- `calculation_version`: Identifier of the calculation version.

---

## Document Control

| Property | Value |
|---|---|
| Document Version | 1.0 |
| Phase | Phase 1, Step 1F |
| Status | Draft - Pending Approval |
| Next Review | Phase 1, Step 1G |
| Unresolved Items | Threshold values; boundary inclusivity rules; Watch-rule definitions; trend tolerances; anomaly detection method; confidence scoring algorithm; persistence window definitions |
