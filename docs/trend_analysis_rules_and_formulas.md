# Trend Analysis Rules and Formulas

## Step 2B-1 — Phase 2B Diagnostic and Early-Warning Layer

**Version:** 1.0-draft  
**Date:** 2026-07-27  
**Status:** Draft / Provisional

---

## 1. Absolute Change

Formula:
```
absolute_change = current_value - comparison_value
```

Required inputs:
- current_value (calculated)
- comparison_value (calculated or averaged)

Zero handling:
- Zero comparison value does not block absolute change.

Unavailable handling:
- If current or comparison is unavailable, absolute_change is null.

Status outcomes:
- Calculated (both values available)
- Current Value Unavailable
- Comparison Value Unavailable

---

## 2. Percentage Change

Formula:
```
percentage_change = (current_value - comparison_value) / abs(comparison_value) * 100
```

Required inputs:
- current_value
- comparison_value (must be non-zero)

Zero handling:
- If comparison_value = 0, percentage_change is null.
- percentage_change_status = Zero Comparison Value.

Unavailable handling:
- If either value is unavailable, percentage_change is null.

Status outcomes:
- Calculated
- Zero Comparison Value
- Comparison Value Unavailable

---

## 3. Rolling Mean

Formula:
```
rolling_mean = sum(valid_values) / valid_observation_count
```

Required inputs:
- Window of historical values
- Valid observations only (calculation_status = Calculated)

Zero handling:
- Zero values are included as valid observations.

Unavailable handling:
- Unavailable values are excluded from the sum and count.

Minimum history:
- 7-day: 4 valid observations
- 14-day: 7 valid observations
- 30-day: 15 valid observations

Status outcomes:
- Calculated
- Insufficient History
- Insufficient Coverage

---

## 4. Rolling Standard Deviation

Formula:
```
rolling_std = sqrt( sum((x_i - mean)^2) / N )
```

Uses population standard deviation (ddof=0) for consistency.

Required inputs:
- Valid observations within window

Zero handling:
- All identical values produce std = 0.

Unavailable handling:
- Unavailable values excluded.

Status outcomes:
- Calculated
- Zero Historical Variance (if std = 0)
- Insufficient History

---

## 5. Z-Score

Formula:
```
z = (current_value - historical_mean) / historical_standard_deviation
```

Required inputs:
- current_value
- Historical mean and std over rolling window

Zero handling:
- If historical std = 0, z-score is null.
- status = Zero Historical Variance.

Minimum history:
- 8 valid observations in 30-day window

Sensitivity:
- Draft threshold: absolute z >= 2.0

Status outcomes:
- Positive Deviation
- Negative Deviation
- No Signal
- Zero Historical Variance
- Insufficient History

---

## 6. Median Absolute Deviation (MAD) Signal

Formula:
```
MAD = median( abs(x_i - median(x)) )
modified_z = 0.6745 * (current_value - median) / MAD
```

Required inputs:
- Historical values within window

Zero handling:
- If MAD = 0, signal is null.
- status = Zero MAD.

Minimum history:
- 8 valid observations in 30-day window

Sensitivity:
- Draft threshold: absolute modified_z >= 3.5

Status outcomes:
- Positive Deviation
- Negative Deviation
- No Signal
- Zero MAD
- Insufficient History

---

## 7. Trend Slope

Formula:
```
slope = linear regression coefficient over indexed observations
```

Required inputs:
- Minimum 5 valid observations

Zero handling:
- Slope of zero means Stable.

Unavailable handling:
- Unavailable observations break sequence unless window is valid.

Status outcomes:
- Sustained Increase (slope > tolerance)
- Sustained Decrease (slope < -tolerance)
- No Signal (within tolerance)
- Insufficient History

---

## 8. Volatility Change

Formula:
```
current_std = std(window)
previous_std = std(prior_window)
change_ratio = (current_std - previous_std) / previous_std
```

Required inputs:
- Two consecutive rolling windows

Zero handling:
- If previous_std = 0, no ratio calculated.

Status outcomes:
- Volatility Increase (change_ratio > 0.2)
- No Signal
- Insufficient History

---

## 9. Configuration Sources

| Config File | Purpose | Status |
|-------------|---------|--------|
| config/trend_analysis_config.csv | Comparison and rolling rules | Draft v1.0-draft |
| config/statistical_signal_config.csv | Signal methods and sensitivity | Draft v1.0-draft |
| config/trend_confidence_config.csv | Confidence thresholds | Draft v1.0-draft |

All configurations are provisional. No stakeholder approval has been obtained.
