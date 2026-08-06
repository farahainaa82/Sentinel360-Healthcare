# Sentinel360 Step 2B-1A — Threshold Candidate Correction Report

## Document Control

| Field | Value |
|-------|-------|
| Step | 2B-1A (Reopened for Focused Correction) |
| Run ID | THCAL-DBEA0A3F3860 |
| Date | 2026-07-27 |
| Status | Approval-Ready for Stakeholder Review |
| Classification Row Limit | 100,000 |
| Actual Classification Rows | 34,191 |
| Volume Control | PASSED |

---

## 1. Executive Summary

This report documents the focused correction of threshold candidates following the failure of the initial stakeholder review pack in approval-readiness review. The corrections address:

1. **Missing Amber bands** for kpi_001, kpi_002, kpi_004, kpi_005, and kpi_006.
2. **Exhaustive, non-overlapping Green-Amber-Red ranges** with explicit boundary inclusivity rules.
3. **kpi_006 scale resolution** from "Normalised Percent Score" to "1-5 Likert Score".
4. **Material candidate deduplication** for kpi_006.
5. **kpi_003 Bed Occupancy** dual-sided mapping with three shortlisted candidates.
6. **0% trend-agreement logic defect** for context-sensitive KPIs.

All corrections have been verified through 24 focused tests and full dry-run classification.

---

## 2. Correction Details by KPI

### 2.1 kpi_001 — Staffing Level (Higher is Better, 0-100%)

| Candidate | lower_red | lower_amber | green_lower | green_upper | Amber Count |
|-----------|-----------|-------------|-------------|-------------|-------------|
| Conservative | 76.47 | 85.71 | 85.71 | 100.0 | 514 (17.6%) |
| Balanced | 80.00 | 84.20 | 84.20 | 100.0 | 292 (10.0%) |
| Sensitive | 85.71 | 100.0 | 100.0 | 100.0 | 1,463 (50.1%) |

**Boundary Inclusivity Rule:** Lower boundary inclusive, upper exclusive; global maximum (100%) inclusive in Green.

### 2.2 kpi_002 — Staff Absenteeism Rate (Lower is Better, 0-50%)

| Candidate | green_lower | green_upper | upper_amber | upper_red | Amber Count |
|-----------|-------------|-------------|-------------|-----------|-------------|
| Conservative | 0.0 | 13.33 | 23.08 | 23.08 | 546 (18.7%) |
| Balanced | 0.0 | 15.00 | 19.05 | 19.05 | 297 (10.2%) |
| Sensitive | 0.0 | 0.0 | 13.33 | 13.33 | 1,232 (42.2%) |

**Boundary Inclusivity Rule:** Lower boundary inclusive, upper exclusive; global maximum (50%) inclusive in Red.

### 2.3 kpi_003 — Bed Occupancy Rate (Context-Sensitive, 71-118%)

| Candidate | lower_red | lower_amber | green_lower | green_upper | upper_amber | upper_red | Amber Count |
|-----------|-----------|-------------|-------------|-------------|-------------|-----------|-------------|
| Conservative | 78.95 | 85.85 | 85.85 | 100.0 | 100.0 | 109.54 | 397 (36.3%) |
| Balanced | 81.72 | 86.12 | 86.12 | 100.16 | 100.16 | 104.76 | 280 (25.6%) |
| Sensitive | 85.85 | 93.33 | 93.33 | 100.0 | 100.0 | 104.76 | 381 (34.8%) |

**Dual-Sided State Mapping:**
- **Lower Red (< lower_red):** Critical Low Utilisation
- **Lower Amber [lower_red, green_lower):** Low Utilisation Caution
- **Green [green_lower, green_upper]:** Normal Operating Band
- **Upper Amber (green_upper, upper_red):** Elevated Occupancy
- **Upper Red [upper_red, max]:** Critical Capacity Pressure

**Trend Agreement Investigation:** The previous 0% trend-agreement for kpi_003 was caused by a logic defect in the `_agree` function, which did not handle `Directionality.CONTEXT_SENSITIVE`. The corrected logic now yields:
- Green status: 100% agreement with trend signals
- High Pressure status: ~91-93% agreement with increase signals
- Low Utilisation status: ~81-84% agreement with decrease signals

### 2.4 kpi_004 — Average Patient Waiting Time (Lower is Better, 26-61 min)

| Candidate | green_lower | green_upper | upper_amber | upper_red | Amber Count |
|-----------|-------------|-------------|-------------|-----------|-------------|
| Conservative | 26.24 | 45.44 | 55.83 | 55.83 | 219 (20.0%) |
| Balanced | 26.24 | 47.24 | 54.09 | 54.09 | 108 (9.9%) |
| Sensitive | 26.24 | 37.25 | 45.44 | 45.44 | 547 (50.0%) |

### 2.5 kpi_005 — Patient Complaint Rate (Lower is Better, 0-75)

| Candidate | green_lower | green_upper | upper_amber | upper_red | Amber Count |
|-----------|-------------|-------------|-------------|-----------|-------------|
| Conservative | 0.0 | 12.20 | 23.81 | 23.81 | 191 (19.4%) |
| Balanced | 0.0 | 14.78 | 19.74 | 19.74 | 109 (11.1%) |
| Sensitive | 0.0 | 0.0 | 12.20 | 12.20 | 202 (20.5%) |

### 2.6 kpi_006 — Patient Satisfaction Score (Higher is Better, 1-5 Likert)

**Scale Resolution:** The data distribution confirms values range from 1.0 to 5.0 with fractional steps (e.g., 2.5, 3.67). The unit has been corrected from "Normalised Percent Score" to "1-5 Likert Score". All boundaries are now expressed on the 1-5 scale.

| Candidate | lower_red | lower_amber | green_lower | green_upper | Amber Count |
|-----------|-----------|-------------|-------------|-------------|-------------|
| Conservative | 2.0 | 3.0 | 3.0 | 5.0 | 374 (15.7%) |
| Balanced | 2.5 | 2.80 | 2.80 | 5.0 | 156 (6.5%) |
| Sensitive | 3.0 | 3.67 | 3.67 | 5.0 | 1,339 (56.2%) |

**Material Distinctness Verification:**
- Conservative vs Balanced: Different lower_red (2.0 vs 2.5) and green_lower (3.0 vs 2.80) → materially distinct
- Conservative vs Sensitive: Different lower_red (2.0 vs 3.0) and green_lower (3.0 vs 3.67) → materially distinct
- Balanced vs Sensitive: Different lower_red (2.5 vs 3.0) and green_lower (2.80 vs 3.67) → materially distinct

Historical classification distributions confirm all three produce different Green/Amber/Red counts.

---

## 3. Verification Results

### 3.1 Boundary Inclusivity

| Test Case | Expected | Result |
|-----------|----------|--------|
| Staffing Level = 100% | Green | PASS |
| Patient Satisfaction = 5.0 | Green | PASS |
| Exact lower_red boundary | Amber (lower inclusive) | PASS |
| Exact green_lower boundary | Green (lower inclusive) | PASS |
| Exact upper_red boundary | Red (lower inclusive) | PASS |

### 3.2 Classification Properties

| Property | Verification | Result |
|----------|--------------|--------|
| Exactly-once classification | Every record classified to exactly one status | PASS |
| No range overlap | Vectorised masks are mutually exclusive | PASS |
| No unexplained gaps | Adjacent bands touch at boundaries | PASS |
| Amber counts non-zero | All 18 candidates have amber_count > 0 | PASS |
| Unavailable records preserved | NaN values remain "Unavailable" | PASS |

### 3.3 Volume and Performance Controls

| Control | Limit | Actual | Result |
|---------|-------|--------|--------|
| Max candidates per KPI | 3 | 3 | PASS |
| Classify only shortlisted | Yes | 18 candidates | PASS |
| Classification row limit | 100,000 | 34,191 | PASS |
| Vectorised processing | Yes | NumPy/pandas | PASS |

---

## 4. Files Regenerated

| File | Path |
|------|------|
| Candidate Config | `config/kpi_threshold_candidate_config.csv` |
| Analytical Candidates | `outputs/analytical_kpi_threshold_candidates.csv` |
| Analytical Classifications | `outputs/analytical_kpi_candidate_classifications.csv` |
| Analytical Burden | `outputs/analytical_kpi_threshold_burden.csv` |
| Analytical Recommendations | `outputs/analytical_kpi_threshold_recommendations.csv` |
| Stakeholder Review Pack | `outputs/threshold_calibration/threshold_calibration_stakeholder_review_pack.csv` |
| Distribution Profiles | `outputs/threshold_calibration/threshold_distribution_profiles.csv` |
| Shortlisted Candidates | `outputs/threshold_calibration/threshold_candidates_shortlisted.csv` |
| Classification Results | `outputs/threshold_calibration/threshold_classification_results.csv` |
| Burden Results | `outputs/threshold_calibration/threshold_burden_results.csv` |
| Trend Alignment | `outputs/threshold_calibration/threshold_trend_alignment.csv` |
| Recommendations | `outputs/threshold_calibration/threshold_recommendations.csv` |
| Manifest | `outputs/threshold_calibration/threshold_calibration_manifest.json` |

---

## 5. Test Summary

| Test Suite | Tests | Passed | Failed |
|------------|-------|--------|--------|
| Focused Threshold Calibration | 24 | 24 | 0 |

Test categories covered:
- Models and boundary serialization
- Engine prerequisites and immutability
- Distribution profiling and data sufficiency
- Candidate generation with G-A-R ranges
- Boundary validation (no gaps, no overlap)
- Shortlisting (max 3 per KPI, kpi_003 gets 3)
- Volume control enforcement
- Vectorised classification correctness
- Boundary inclusivity determinism
- Exactly-once classification
- Non-zero amber counts
- Material candidate deduplication
- Bed Occupancy dual-sided states
- kpi_006 scale consistency
- Burden calculation
- Manifest completeness

---

## 6. Outstanding Items and Next Steps

1. **Stakeholder Review Required:** All 6 KPIs are in "Pending Stakeholder Review" status. No approvals have been fabricated.
2. **Step 2B-1B Mode B:** Awaiting explicit stakeholder decisions before promotion.
3. **Promotion Gate:** Active configuration will NOT be modified without both `--promote-active-config` and `--confirm-stakeholder-approval` flags.
4. **Step 2B-2:** Deferred until stakeholder approval is complete.

---

## 7. Sign-Off

| Role | Status |
|------|--------|
| Calibration Engine | CORRECTED and VERIFIED |
| Classification Logic | CORRECTED and VERIFIED |
| Boundary Validation | CORRECTED and VERIFIED |
| Trend Alignment | CORRECTED and VERIFIED |
| Test Suite | 24/24 PASSED |
| Volume Control | PASSED |
| Active Config | UNCHANGED (checksum verified) |
| Promotion Status | BLOCKED pending stakeholder decision |

---

*End of Report*
