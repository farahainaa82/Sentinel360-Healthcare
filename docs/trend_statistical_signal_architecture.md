# Trend and Statistical-Signal Architecture

## Step 2B-1 — Phase 2B Diagnostic and Early-Warning Layer

**Version:** 1.0-draft  
**Date:** 2026-07-27  
**Status:** Draft / Provisional

---

## 1. Scope

This document defines the governed trend and statistical-signal architecture for the Sentinel360 Healthcare analytics platform.

The architecture analyses KPI movement over time without relying on stakeholder-approved performance thresholds. It supports current-versus-previous-period comparisons, rolling statistics, mathematical trend direction, provisional business movement interpretation, sustained movement detection, and threshold-independent statistical signals.

---

## 2. Accepted Inputs

Primary source:
- `data/analytical/analytical_six_kpi_daily.csv` (17,520 integrated KPI records)

Supporting sources:
- `data/analytical/analytical_six_kpi_coverage_daily.csv`
- `data/analytical/analytical_phase_2a_closure_snapshot.csv`
- `config/kpi_definition_config.csv`
- `config/kpi_threshold_config.csv`
- `config/data_confidence_config.csv`

---

## 3. Analytical Grain

Primary grain: hospital_id + department_id + kpi_id + reporting_date

Derived period grains:
- Daily
- Weekly (future)
- Monthly (future)

Each trend output includes:
- period_type
- period_start_date
- period_end_date
- current_period_value
- comparison_period_value
- comparison_period_type

---

## 4. Comparison Types

1. Previous Available Day
2. Previous Calendar Day
3. Previous Week
4. Previous Month
5. Same Period Previous Month
6. Rolling 7-Day Average
7. Rolling 14-Day Average
8. Rolling 30-Day Average
9. Rolling 3-Month Average
10. Baseline Period Average

Before implementing each comparison, the engine validates whether source history supports it. Unavailable values are never filled with zero.

---

## 5. Minimum-History Rules

Configured in `config/trend_analysis_config.csv`:

| Comparison | Min Valid Obs | Window |
|------------|---------------|--------|
| Previous period | 2 | — |
| 7-day rolling | 4 | 7 |
| 14-day rolling | 7 | 14 |
| 30-day rolling | 15 | 30 |
| 3-month rolling | 2 | 3 months |
| Linear slope | 5 | — |
| Volatility | 5 | — |
| Z-score | 8 | 30 days |
| Sustained movement | 3 consecutive | — |

All rules have approval_status = Draft and version = v1.0-draft.

---

## 6. Mathematical Trend Direction

Purely mathematical:
- Increasing (absolute change > tolerance)
- Decreasing (absolute change < -tolerance)
- Stable (within tolerance)
- Insufficient History
- Unavailable

---

## 7. Business Movement Interpretation

Governed by KPI directionality:

| KPI | Directionality |
|-----|----------------|
| kpi_001 Staffing Level | Higher is better |
| kpi_002 Staff Absenteeism Rate | Lower is better |
| kpi_003 Bed Occupancy Rate | Context-sensitive |
| kpi_004 Average Patient Waiting Time | Lower is better |
| kpi_005 Patient Complaint Rate | Lower is better |
| kpi_006 Patient Satisfaction Score | Higher is better |

For kpi_003, the interpretation is always "Context Review" because occupancy requires approved operating ranges.

All interpretations have interpretation_status = Provisional.

---

## 8. Sustained Movement

Minimum three consecutive valid observations moving in the same mathematical direction. Unavailable observations break the sequence. Each record includes:
- sequence_start_date
- sequence_end_date
- consecutive_observation_count
- cumulative_absolute_change
- cumulative_percentage_change

---

## 9. Statistical Signals

Threshold-independent methods:
1. Rolling z-score
2. Median absolute deviation (MAD) signal
3. Trend slope
4. Volatility change
5. Sustained movement
6. Change-point candidate
7. Period-over-period deterioration
8. Period-over-period improvement

Signal types are analytical only. No Green, Amber, or Red. No final alerts.

---

## 10. Confidence Model

Trend confidence is separate from KPI data confidence:
- High: >=15 valid obs, >=75% coverage, High source confidence
- Medium: >=8 valid obs, >=50% coverage
- Low: >=4 valid obs, >=25% coverage
- Unavailable: below minimum thresholds

Configured in `config/trend_confidence_config.csv` with Draft approval status.

---

## 11. Evidence and Lineage

Every calculated trend or signal preserves:
- Current and comparison analytical record IDs
- History window and source dates
- Source KPI values
- Observations used and excluded
- Calculation method and configuration version
- Source integration run ID and trend calculation run ID

---

## 12. Missing and Unavailable Data

Rules:
- Do not convert missing to zero
- Do not interpolate
- Do not forward-fill or backfill
- Preserve accepted calculation_status
- Record history coverage and excluded dates

Controlled history statuses: Complete, Partial, Sparse, Insufficient, Unavailable.

---

## 13. Limitations

- All threshold configurations remain v1.0-draft and provisional.
- No Green, Amber, or Red classifications are generated.
- Business movement interpretations are provisional.
- Statistical signals are candidates, not final alerts.
- Trend slope does not imply causality.
- Volatility increase is a signal, not automatically deterioration.
