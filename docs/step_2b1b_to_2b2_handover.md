# Sentinel360 — Step 2B-1B to 2B-2 Handover

## Threshold Promotion to Breach-and-Watch Engine

---

## 1. Current State

- Step 2B-1A: Complete — 17 shortlisted candidates, 33,096 provisional classifications.
- Step 2B-1B: Complete — Review preparation mode. No stakeholder decisions recorded.
- Active threshold config: `config/kpi_threshold_config.csv` (v1.0-draft, unchanged).

---

## 2. Approved Thresholds

None. All thresholds remain provisional.

---

## 3. Provisional Thresholds

All 17 shortlisted candidates in `outputs/threshold_calibration/threshold_candidates_shortlisted.csv` are provisional v1.0-candidate.

---

## 4. Disabled KPI Threshold Logic

All six KPIs are disabled for operational breach detection until stakeholder approval is recorded.

---

## 5. Threshold-Breach Rules Permitted in Step 2B-2

Step 2B-2 may implement:
- Classification logic for calculated records.
- Boundary-value handling.
- Dual-sided Bed Occupancy logic.
- Unavailable record exclusion.
- Not Assessed handling.

Step 2B-2 must not:
- Use unapproved thresholds for live alerting.
- Treat provisional thresholds as approved.
- Skip stakeholder decision validation.

---

## 6. Review and Expiry Dates

None set — awaiting stakeholder decisions.

---

## 7. Rollback Location

`config/archive/kpi_threshold_config_v1.0-draft.csv` (created on first promotion).

---

## 8. Recommended Next Action

1. Obtain stakeholder decisions.
2. Validate and promote approved thresholds.
3. Re-run Step 2B-1B in promotion mode.
4. Only then proceed to Step 2B-2.
