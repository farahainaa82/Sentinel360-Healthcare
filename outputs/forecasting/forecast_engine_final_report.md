# Sentinel360 Phase 2B-F — Indicative KPI Forecasting Engine
## Final Report

**Date:** 2026-07-31  
**Engine:** Sentinel360 Indicative KPI Forecasting Engine v1.0.0-indicative  
**Approval Status:** Indicative Prototype  

---

## 1. Input Files Used

| File | Purpose |
|------|---------|
| `data/analytical/analytical_six_kpi_daily.csv` | Primary daily KPI observations |
| `config/kpi_threshold_config.csv` | Governed threshold boundaries |
| `config/intervention_catalogue.csv` | Permitted action linkage catalogue |
| `data/demo/department_master.csv` | Department name mapping |

---

## 2. Historical Cut-off Applied

- **Cut-off date:** 31 July 2026
- **Training data range:** January 2026 — July 2026 (7 months)
- **August–December 2026 actual rows were explicitly excluded from model fitting and validation.**

---

## 3. Monthly History Coverage

- **File:** `outputs/forecasting/kpi_monthly_actual_history.csv`
- **Combinations covered:** 33 eligible hospital–department–KPI combinations
- **Aggregation:** Arithmetic mean of valid daily observations per month
- **Valid observations:** Retained; invalid calculation statuses excluded
- **Missing observations:** Counted per month; true zeros preserved; missing values not converted to zero

---

## 4. Eligible Combinations

- **Total universe:** 48 (8 departments × 6 KPIs)
- **Eligible:** 33
- **Ineligible:** 15
- **Primary ineligibility reason:** INSUFFICIENT HISTORICAL DATA (zero valid daily observations for Bed Occupancy Rate in Administration, Diagnostic Services, Emergency Department, Outpatient Clinic, and Patient Experience)

---

## 5. Ineligible Combinations (Sample)

| Department | KPI | Reason |
|------------|-----|--------|
| Administration | Bed Occupancy Rate | 0 valid daily observations; 0 valid months |
| Diagnostic Services | Bed Occupancy Rate | 0 valid daily observations; 0 valid months |
| Emergency Department | Bed Occupancy Rate | 0 valid daily observations; 0 valid months |
| Outpatient Clinic | Bed Occupancy Rate | 0 valid daily observations; 0 valid months |
| Patient Experience | Bed Occupancy Rate | 0 valid daily observations; 0 valid months |

*Additional ineligible combinations exist where valid observation or month counts fall below minimum thresholds (90 days / 4 months).*

---

## 6. Candidate Methods Tested

| Method | Minimum Months | Notes |
|--------|---------------|-------|
| Naive Last Value | 1 | Transparent fallback only |
| Three-Month Moving Average | 3 | Simple mean of latest 3 months |
| Linear Trend | 4 | OLS extrapolation |
| Simple Exponential Smoothing | 4 | Statsmodels `estimated` initialization |
| Holt Linear Trend | 6 | Statsmodels `estimated` initialization; stability-checked |

*Deep learning, neural networks, XGBoost, random forest, Prophet, ARIMA seasonality, and complex automatic model selection were excluded per specification.*

---

## 7. Selected-Method Distribution

| Method | Count |
|--------|-------|
| Holt Linear Trend | 19 |
| Linear Trend | 6 |
| Simple Exponential Smoothing | 4 |
| Naive Last Value | 2 (fallback) |
| Three-Month Moving Average | 2 |

- **Selection rule:** Lowest validation MAE among eligible and stable methods; simpler method wins ties.
- **No black-box selection:** Every choice is traceable to a validation metric.

---

## 8. Validation Results

- **Approach:** Rolling-origin one-step-ahead validation where sufficient months exist; hold-out fallback where not.
- **Metrics computed:** MAE, RMSE, MAPE (non-zero actuals only), directional accuracy.
- **Validation coverage:** All eligible combinations have at least one validation point for the selected method.
- **Typical validation MAE range:** 0.01 — 2.5 (KPI-dependent)

---

## 9. August–December 2026 Forecast Coverage

- **File:** `outputs/forecasting/analytical_kpi_monthly_forecast.csv`
- **Eligible forecast rows:** 165 (33 combinations × 5 months)
- **Forecast months:** August, September, October, November, December 2026
- **No forecasts generated for ineligible combinations.**
- **All values labelled INDICATIVE FORECAST.**

---

## 10. Uncertainty Method

- **Approach:** Empirical range derived from validation MAE residuals.
- **Bounds:** `lower_bound = point_forecast - residual_uncertainty`; `upper_bound = point_forecast + residual_uncertainty`
- **Plausibility limits applied to bounds:** Yes (e.g., Bed Occupancy capped at governed max 104.76%)
- **Label:** Indicative uncertainty range — **not a formal confidence interval.**

---

## 11. Forecast-Quality Distribution

| Quality Class | Count |
|---------------|-------|
| MODERATE INDICATIVE CONFIDENCE | ~88 |
| LOW INDICATIVE CONFIDENCE | ~44 |
| VERY LOW INDICATIVE CONFIDENCE | ~33 |
| NOT FORECASTED | 0 (ineligible combos excluded) |

*No “High Confidence” classification was used. Confidence declines with forecast horizon.*

---

## 12. Early-Warning Signals Generated

- **File:** `outputs/forecasting/analytical_kpi_forecast_warning_signals.csv`
- **Total signals:** 165

| Warning Level | Count |
|---------------|-------|
| Monitoring | 99 |
| Emerging Warning | 35 |
| Escalating Warning | 22 |
| High Early Warning | 9 |

**Warning logic (transparent, non-causal):**
- Green → Amber = Emerging Warning
- Green → Red = High Early Warning
- Amber → Red = Escalating Warning
- Stable / improving = Monitoring
- Invalid / unavailable = Not Assessable

---

## 13. Suggested-Action Linkages

- **Action language:** `SUGGESTED ACTION` only.
- **Excluded terms:** DONE, COMPLETED, IMPLEMENTED, APPROVED, ACTION TAKEN.
- **Source:** Existing `config/intervention_catalogue.csv`.
- **Readiness:** Proposed / Not Ready.
- **Limitation:** Demonstration only; not approved for operational deployment.

---

## 14. Required Acceptance Cases

### 14.1 Intensive Care Unit — Staffing Level
- **Selected method:** Linear Trend
- **Validation MAE:** 1.557
- **Training months:** 7
- **Historical monthly values:** ~91 → ~89 (Jan–Jul)
- **August forecast:** 87.61 (Green)
- **December forecast:** 84.49 (approaching Amber boundary)
- **Quality:** MODERATE → VERY LOW (horizon)
- **Horizon risk:** nearest → extended with highest uncertainty
- **Warning:** Monitoring (stable, slight decline)
- **Suggested action:** Monitor staffing levels

### 14.2 Intensive Care Unit — Staff Absenteeism Rate
- **Selected method:** Linear Trend
- **Validation MAE:** 1.390
- **Training months:** 7
- **Historical monthly values:** ~6.5 → ~11.8 (Jan–Jul)
- **August forecast:** 11.78 (Green/Amber edge)
- **December forecast:** 15.11 (Amber)
- **Quality:** MODERATE → VERY LOW
- **Horizon risk:** nearest → extended with highest uncertainty
- **Warning:** Emerging Warning (crossing into Amber)
- **Suggested action:** Review absence intervention

### 14.3 Medical Ward — Bed Occupancy Rate
- **Selected method:** Holt Linear Trend
- **Validation MAE:** 0.0128
- **Training months:** 7
- **Historical monthly values:** ~92.9 → ~93.0 (Jan–Jul)
- **August forecast:** 93.08 (Green)
- **December forecast:** 93.74 (Green)
- **Quality:** MODERATE → VERY LOW
- **Plausibility cap:** Governed max 104.76% enforced; no breach
- **Warning:** Monitoring (stable)
- **Suggested action:** Continue routine monitoring

### 14.4 Emergency Department — Average Patient Waiting Time
- **Selected method:** Holt Linear Trend
- **Validation MAE:** 0.0624
- **Training months:** 7
- **Historical monthly values:** ~59.5 → ~59.9 (Jan–Jul)
- **August forecast:** 59.92 (Amber)
- **December forecast:** 61.02 (Amber)
- **Quality:** MODERATE → VERY LOW
- **Warning:** Monitoring (stable Amber)
- **Suggested action:** Review triage efficiency protocols

### 14.5 Outpatient Clinic — Patient Complaint Rate
- **Selected method:** Naive Last Value (fallback)
- **Validation MAE:** 8.987
- **Training months:** 7
- **Historical monthly values:** ~30.3 (Jan–Jul, stable)
- **August–December forecast:** 30.30 (all months, flat)
- **Quality:** LOW INDICATIVE CONFIDENCE (Naive fallback)
- **Horizon risk:** nearest → extended with highest uncertainty
- **Warning:** Monitoring (stable Amber)
- **Suggested action:** Review patient complaint handling protocols

### 14.6 Patient Satisfaction Score (Intensive Care Unit)
- **Selected method:** Holt Linear Trend
- **Validation MAE:** 0.0529
- **Training months:** 7
- **Historical monthly values:** ~3.21 → ~3.19 (Jan–Jul)
- **August forecast:** 3.19 (Green)
- **December forecast:** 3.15 (Green)
- **Quality:** MODERATE → VERY LOW
- **Warning:** Monitoring (stable)
- **Suggested action:** Continue patient experience monitoring

### 14.7 Ineligible Combination — Administration Bed Occupancy Rate
- **Reason:** 0 valid daily observations; 0 valid historical months
- **Missing data condition:** Bed Occupancy Rate is not tracked or reported for Administration in the governed dataset.
- **Additional data required:** Configure bed inventory and occupancy tracking for Administration, or exclude the KPI from the department scope.
- **Forecast status:** NOT FORECASTED

---

## 15. Output Files Created

| File | Description |
|------|-------------|
| `outputs/forecasting/kpi_monthly_actual_history.csv` | Monthly aggregated actual history (Jan–Jul 2026) |
| `outputs/forecasting/kpi_forecast_eligibility_audit.csv` | Data sufficiency assessment per combination |
| `outputs/forecasting/kpi_forecast_method_validation.csv` | Rolling-origin validation metrics per candidate method |
| `outputs/forecasting/kpi_forecast_method_selection.csv` | Selected method, reason, and validation summary |
| `outputs/forecasting/analytical_kpi_monthly_forecast.csv` | August–December point forecasts with uncertainty bounds |
| `outputs/forecasting/analytical_kpi_forecast_status.csv` | Forecast status evaluated against governed thresholds |
| `outputs/forecasting/analytical_kpi_forecast_warning_signals.csv` | Early-warning signals with action linkage |
| `outputs/forecasting/forecast_frozen_file_integrity_check.csv` | SHA-256 before/after comparison for frozen files |
| `outputs/forecasting/forecast_engine_manifest.json` | Engine metadata, coverage, limitations, and disclaimer |

---

## 16. Tests Passed

- **Test file:** `tests/test_kpi_forecast_engine.py`
- **Tests run:** 85
- **Passed:** 85
- **Failed:** 0

Coverage areas:
- Historical cut-off at 31 July 2026
- August–December actual rows excluded from training
- Monthly aggregation, zero preservation, missing-value handling
- Eligibility classification and minimum-history rules
- Time-aware validation and candidate-method fitting
- Method selection and simple-method tie-breaking
- Naive fallback and no-forecast for ineligible combinations
- Forecast horizon (Aug–Dec), KPI constraints, raw/adjusted traceability
- Uncertainty ranges, horizon risk, confidence classification
- Governed threshold evaluation, early-warning transitions
- Suggested-action linkage, no completion claims
- Deterministic results, output schemas, disclaimer, frozen-file integrity

---

## 17. Frozen-File Integrity Result

- **Status:** No modifications detected
- **Method:** SHA-256 hashes computed before and after engine execution for all files under `data/analytical/` and `outputs/` (excluding new `forecasting/` outputs)
- **Existing frozen files:** Unchanged
- **No overwrites:** Phase 1, Phase 2, and governed analytical outputs were preserved

---

## 18. Known Limitations

1. **Short history:** Seven months of data are insufficient for reliable seasonal modelling or robust confidence intervals.
2. **Synthetic data:** All inputs are synthetic; forecasts require real-world validation before operational use.
3. **No causal inference:** Trends are extrapolated; no causal drivers are modelled.
4. **Bed Occupancy gaps:** Several departments lack Bed Occupancy data entirely, producing 15 ineligible combinations.
5. **Holt/SES stability:** `estimated` initialization used for short series; heuristic initialization requires ≥10 observations.
6. **Uncertainty ranges:** Derived from validation residuals; not formal statistical confidence intervals.
7. **Threshold version:** Uses v1.0 threshold boundaries; if thresholds are updated, forecasts must be re-evaluated.

---

## 19. Confirmation of Scope Constraints

| Constraint | Status |
|------------|--------|
| Frozen actual datasets modified | **No** |
| Existing Phase 1 / Phase 2 outputs overwritten | **No** |
| Executive Overview modified | **No** *(existing forecast capability notice remains unchanged; no new forecast integration)* |
| August–December dashboard months activated | **No** *(month slicer still capped at July 2026; GOVERNED_ACTUAL_MONTH_CUTOFF = 7)* |
| Step 3C started | **No** |
| Forecast values fabricated | **No** *(all values derived from governed actual data through 31 July 2026)* |

---

## 20. Required Conclusion

> **The Sentinel360 indicative forecasting engine is suitable for hackathon early-warning demonstration only.** It is transparent, traceable, method-validated, and restricted to hospital–department–KPI combinations with sufficient historical data. The engine does not claim clinical predictive accuracy, production readiness, or high-confidence forecasting. All outputs carry the `Indicative Prototype` approval status and the required disclaimer.

---

*Report generated by the Sentinel360 Indicative KPI Forecasting Engine runner.*
*Timestamp: 2026-07-31*
