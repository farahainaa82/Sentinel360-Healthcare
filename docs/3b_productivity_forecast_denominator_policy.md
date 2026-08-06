# Productivity Forecast Denominator Policy

**Document ID:** `docs/3b_productivity_forecast_denominator_policy.md`  
**Version:** v1.0-draft  
**Phase:** 3B — Executive Overview Productivity Governance  
**Governance Status:** Governed Draft / Indicative Prototype  
**Config Source:** `config/productivity_forecast_assumption_config.csv`  

---

## 1. Purpose

This document formally registers the method by which Sentinel360 estimates *required staff-hours* for forecast months when no observed actual data yet exists.

The policy is needed because:
- Forecasting produces a **Staffing Level percentage** (kpi_001) for future months.
- Converting that percentage into an **absolute productive staff-hours** figure requires a denominator: required staff-hours for the same future month.
- Sentinel360 **does not fabricate** forecast denominators from trend extrapolation or hardcoded shift assumptions.
- Instead, the denominator is derived **only from observed actual required staff-hours** using a transparent, governed rule.

---

## 2. Governed Policy Wording

> For forecast months where observed required staff-hours are unavailable, Sentinel360 estimates required staff-hours using the arithmetic mean of the latest `lookback_months` complete actual months for the same hospital and department.
>
> The resulting denominator is held constant across the current forecast horizon and is used only to convert forecast Staffing Level (%) into indicative productive staff-hours.
>
> If fewer than `minimum_complete_months_required` complete actual months are available, forecast productive staff-hours must be reported as **Not Available**.

---

## 3. Source Lineage

| Attribute | Value |
|---|---|
| **Policy ID** | `PFA-001` |
| **Policy Name** | Forecast Required Staff-Hours Estimation |
| **Metric Scope** | kpi_001 / Staffing Level productivity capacity |
| **Method** | `LATEST_COMPLETE_ACTUAL_MONTHS` |
| **Lookback Months** | `3` |
| **Aggregation Method** | `ARITHMETIC_MEAN` |
| **Forecast Horizon Usage** | `HOLD_CONSTANT_ACROSS_CURRENT_FORECAST_HORIZON` |
| **Minimum Complete Months Required** | `3` |
| **Fallback Behaviour** | `NOT_AVAILABLE` |
| **Source Dataset** | `data/analytical/analytical_six_kpi_daily.csv` |
| **Source Field** | `denominator_value` |
| **KPI ID** | `kpi_001` |
| **Unit** | `staff-hours` |

---

## 4. Latest-Three-Complete-Month Logic

The implementation **dynamically derives** the latest complete actual months from the available data. It does **not** hardcode month numbers such as May, June, or July.

### How it works

1. Read `analytical_six_kpi_daily.csv`.
2. Filter to `kpi_id='kpi_001'`, the requested `hospital_id`, `department_id`, and `reporting_year`.
3. Sum `denominator_value` by `reporting_month`.
4. Sort months in descending order (most recent first).
5. Select the top `lookback_months` (currently `3`) months.
6. Compute the arithmetic mean of their totals.
7. Return the mean as the forecast denominator.

### Current 2025 Resolution

For the governed data boundary (Jan–Jul 2025 actuals):
- The latest complete actual months are **May, June, July 2025**.
- These emerge naturally because July is the last month with actual data, and the policy looks back 3 months.
- The policy therefore resolves to:
  ```
  (May denominator total + June denominator total + July denominator total) / 3
  ```
- This same value is held constant for every forecast month: Aug, Sep, Oct, Nov, Dec 2025.

If the actual cutoff were extended to August 2025, the policy would automatically shift to **Jun, Jul, Aug 2025** without any code or config change.

---

## 5. Hold-Constant-Across-Forecast-Horizon Rule

The `forecast_horizon_usage` is set to `HOLD_CONSTANT_ACROSS_CURRENT_FORECAST_HORIZON`.

This means:
- The same calculated denominator (e.g., the May–Jul average) is applied uniformly to **all** forecast months in the current horizon.
- No rolling update is performed month-by-month within the forecast horizon.
- This avoids generating forecast-dependent denominators, which would introduce circular reasoning.

---

## 6. Fallback = Not Available

If a hospital/department combination has fewer than 3 complete actual months:
- The helper returns `status="INSUFFICIENT_MONTHS"`.
- The productive staff-hours card must display **Not Available**.
- No alternative fallback (e.g., last-known, zero, or hardcoded average) is substituted.

---

## 7. What This Policy Explicitly Excludes

### No hardcoded 8-hour shift assumptions
The denominator is sourced directly from `denominator_value` in the analytical layer. This field already represents the sum of required staff-hours as calculated by the KPI pipeline. No per-shift hour constant (such as 8.0) is introduced at the forecast-productivity stage.

### No fabricated forecast denominator
The policy does not extrapolate, trend-extend, or model future required staff-hours. It uses only observed actuals.

### No diagnostic variability threshold as governance
Earlier feasibility analysis computed coefficients of variation (CV) for diagnostic purposes. **CV is not used as a governance gate.** There is no rule such as `CV <= 10%` that blocks or enables the policy. The policy applies uniformly to all departments that meet the minimum-month requirement.

---

## 8. Configuration File

`config/productivity_forecast_assumption_config.csv`

Contains a single governed row (`policy_id = PFA-001`) with all parameters listed in Section 3.

---

## 9. Helper Module

`src/productivity_forecast_denominator_policy.py`

Provides:
- `PolicyConfigLoader` — loads and validates the policy from config.
- `ForecastDenominatorPolicy` — typed dataclass for the policy fields.
- `ForecastDenominatorCalculator` — calculates the denominator using only actual data.
- `DenominatorResult` — structured return with status, months used, and message.

The helper validates:
- policy exists
- `lookback_months` is numeric and >= 1
- `aggregation_method` is supported
- `minimum_complete_months_required` exists and is >= 1
- `fallback_behavior` is recognised
- `source_kpi` = `kpi_001`
- `source_field` = `denominator_value`

No UI code, no Streamlit dependency, no 8-hour shift constant.

---

## 10. Test Coverage

`tests/test_productivity_forecast_denominator_policy.py`

Tests verify:
1. Policy loads from config.
2. `lookback_months` equals `3`.
3. Aggregation method is `ARITHMETIC_MEAN`.
4. Fallback behaviour is `NOT_AVAILABLE`.
5. Latest complete actual month is determined correctly from data.
6. Current 2025 data resolves latest 3 actual months to May–Jul.
7. No literal May/Jun/Jul month policy is required.
8. No 8-hour assumption is used.
9. No 10% CV governance threshold is introduced.
10. Fewer than 3 complete months returns unavailable.
11. Excluded scope (ALL / DEPT-PEX) is handled consistently.

---

## 11. Related Files

| File | Role |
|---|---|
| `config/productivity_forecast_assumption_config.csv` | Governed policy parameters |
| `src/productivity_forecast_denominator_policy.py` | Pure helper (no UI) |
| `tests/test_productivity_forecast_denominator_policy.py` | Targeted test suite |
| `data/analytical/analytical_six_kpi_daily.csv` | Source actual data (denominator_value) |
| `outputs/forecasting/analytical_kpi_monthly_forecast.csv` | Forecast staffing level % (used later, not by this policy) |

---

## 12. Changelog

| Date | Change | Author |
|---|---|---|
| 2026-07-25 | Initial governance config and documentation created | Sentinel360 |
