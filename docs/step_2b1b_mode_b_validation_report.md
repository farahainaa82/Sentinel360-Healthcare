# Sentinel360 Step 2B-1B — Mode B Decision Validation and Staging Report

## Document Control

| Field | Value |
|-------|-------|
| Step | 2B-1B Mode B |
| Run ID | THAPP-F44D27A37BE9 |
| Date | 2026-07-27 |
| Mode | Decision Validation + Staging (No Promotion) |
| Promotion Flags | NOT USED |

---

## 1. Executive Summary

Mode B validation and staging completed successfully for all six KPIs. All stakeholder decisions were validated, staged configurations built, and sandbox historical classifications executed. The active threshold configuration (`config/kpi_threshold_config.csv`) was **not modified**.

| Metric | Value |
|--------|-------|
| KPIs Reviewed | 6 |
| Decisions Validated | 6/6 |
| Complete Decisions | 6 |
| Incomplete Decisions | 0 |
| Approved KPIs | 4 |
| Conditionally Approved KPIs | 2 |
| Rejected/Deferred | 0 |
| Blocking Issues | 0 |
| Warnings | 0 |

---

## 2. Decision Validation Results

### 2.1 Validation Summary

| Decision ID | KPI | Decision | Validation | Candidate Exists | Boundary Valid | Approver Valid | Date Valid | Conditional Met |
|-------------|-----|----------|------------|------------------|----------------|----------------|------------|-----------------|
| DEC-001 | kpi_001 | Approve Candidate | Valid | Yes | Yes | Yes | Yes | N/A |
| DEC-002 | kpi_002 | Approve Candidate | Valid | Yes | Yes | Yes | Yes | N/A |
| DEC-003 | kpi_003 | Conditional Approval | Valid | Yes | Yes | Yes | Yes | Yes |
| DEC-004 | kpi_004 | Approve Candidate | Valid | Yes | Yes | Yes | Yes | N/A |
| DEC-005 | kpi_005 | Conditional Approval | Valid | Yes | Yes | Yes | Yes | Yes |
| DEC-006 | kpi_006 | Approve Candidate | Valid | Yes | Yes | Yes | Yes | N/A |

### 2.2 Candidate Verification

All `selected_candidate_id` values were confirmed to exist in `config/kpi_threshold_candidate_config.csv` and belong to the correct KPI:

| KPI | Selected Candidate | Name | Type |
|-----|-------------------|------|------|
| kpi_001 | CAND-9132137F3353 | kpi_001_Hybrid_Candidate_Calibration_Balanced | Balanced |
| kpi_002 | CAND-401D561CEDE3 | kpi_002_Hybrid_Candidate_Calibration_Balanced | Balanced |
| kpi_003 | CAND-302D7A9F11B5 | kpi_003_Hybrid_Candidate_Calibration_Balanced | Balanced |
| kpi_004 | CAND-B80C86F00895 | kpi_004_Hybrid_Candidate_Calibration_Balanced | Balanced |
| kpi_005 | CAND-F76D963AE6DE | kpi_005_Hybrid_Candidate_Calibration_Balanced | Balanced |
| kpi_006 | CAND-A643D6F72D76 | kpi_006_Hybrid_Candidate_Calibration_Balanced | Balanced |

### 2.3 Conditional Approval Validation

**kpi_003 — Bed Occupancy Rate (Conditional Approval)**
- Conditions preserved: "Approved provisionally for prototype use. The dual-sided occupancy model, including Low Utilisation, Normal Operating Band, Elevated Occupancy and Critical Capacity Pressure, and the treatment of occupancy above 100 percent must be operationally validated before hospital deployment."
- Required review date: 2026-09-30
- Threshold marked as provisional (`threshold_is_provisional = True`)
- Version: `v1.0-provisional-approved`

**kpi_005 — Patient Complaint Rate (Conditional Approval)**
- Conditions preserved: "Approved provisionally using valid complaints per 1,000 patient encounters. Denominator accuracy and stability must be confirmed within 90 days. Thresholds must be recalibrated if the denominator methodology changes."
- Required review date: 2026-10-25
- Threshold marked as provisional (`threshold_is_provisional = True`)
- Version: `v1.0-provisional-approved`

---

## 3. Staged Threshold Configuration

The staged configuration was built at `outputs/threshold_approval/threshold_approval_staged_config.csv`.

| KPI | Direction | Version | Provisional | Lower Red | Lower Amber | Green Lower | Green Upper | Upper Amber | Upper Red | Unit |
|-----|-----------|---------|-------------|-----------|-------------|-------------|-------------|-------------|-----------|------|
| kpi_001 | Higher is better | v1.0-approved | False | 80.0 | 84.197 | 84.197 | 100.0 | — | — | Percent |
| kpi_002 | Lower is better | v1.0-approved | False | — | — | 0.0 | 15.001 | 19.048 | 19.048 | Percent |
| kpi_003 | Context-sensitive | v1.0-provisional-approved | True | 81.718 | 86.119 | 86.119 | 100.160 | 100.160 | 104.762 | Percent |
| kpi_004 | Lower is better | v1.0-approved | False | — | — | 26.24 | 47.242 | 54.087 | 54.087 | Minutes |
| kpi_005 | Lower is better | v1.0-provisional-approved | True | — | — | 0.0 | 14.779 | 19.744 | 19.744 | Complaints per 1000 |
| kpi_006 | Higher is better | v1.0-approved | False | 2.5 | 2.803 | 2.803 | 5.0 | — | — | 1-5 Likert Score |

---

## 4. Sandbox Historical Classification

### 4.1 Overall Counts

| Status | Count | Percentage |
|--------|-------|------------|
| Green | 8,933 | 50.99% |
| Amber | 1,242 | 7.09% |
| Red | 990 | 5.65% |
| Critical Capacity Pressure | 122 | 0.70% |
| Low Utilisation | 110 | 0.63% |
| Unavailable | 6,123 | 34.95% |
| **Total** | **17,520** | **100%** |

### 4.2 Per-KPI Breakdown

| KPI | Green | Amber | Red | Low Utilisation | Critical Capacity Pressure | Unavailable |
|-----|-------|-------|-----|-----------------|---------------------------|-------------|
| kpi_001 | 2,371 | 292 | 257 | — | — | 0 |
| kpi_002 | 2,330 | 297 | 293 | — | — | 0 |
| kpi_003 | 583 | 280 | — | 110 | 122 | 1,825 |
| kpi_004 | 877 | 108 | 110 | — | — | 1,825 |
| kpi_005 | 776 | 109 | 99 | — | — | 1,936 |
| kpi_006 | 1,996 | 156 | 231 | — | — | 537 |

### 4.3 Bed Occupancy Dual-Sided State Mapping (kpi_003)

| State | Range | Count |
|-------|-------|-------|
| Low Utilisation | `< 81.718%` | 110 |
| Lower Amber | `81.718% – 86.119%` | 280 |
| Normal Operating Band (Green) | `86.119% – 100.160%` | 583 |
| Upper Amber | `100.160% – 104.762%` | 0* |
| Critical Capacity Pressure | `≥ 104.762%` | 122 |

*Note: No records fell in the Upper Amber band in the historical dataset. This is expected because the data distribution has a natural gap between ~100.2% and ~104.8%.

---

## 5. Boundary Case Verification

### 5.1 Boundary Inclusivity Rules

| KPI | Test Value | Expected | Actual | Result |
|-----|------------|----------|--------|--------|
| kpi_001 | 80.0 (exact lower_red) | Amber | Amber | PASS |
| kpi_001 | 84.196… (exact green_lower) | Green | Green | PASS |
| kpi_001 | 100.0 (global max) | Green | Green | PASS |
| kpi_002 | 15.001… (exact green_upper) | Green | Green | PASS |
| kpi_002 | 19.047… (exact upper_red) | Red | Red | PASS |
| kpi_003 | 81.718… (exact lower_red) | Amber | Amber | PASS |
| kpi_003 | 86.119… (exact green_lower) | Green | Green | PASS |
| kpi_003 | 100.160… (exact green_upper) | Green | Green | PASS |
| kpi_003 | 104.762… (exact upper_red) | Critical Capacity Pressure | Critical Capacity Pressure | PASS |
| kpi_006 | 2.5 (exact lower_red) | Amber | Amber | PASS |
| kpi_006 | 2.803… (exact green_lower) | Green | Green | PASS |
| kpi_006 | 5.0 (global max) | Green | Green | PASS |

### 5.2 Range Exhaustiveness and Gaps

| Property | Verification | Result |
|----------|--------------|--------|
| Exactly-once classification | Every record classified to exactly one status | PASS |
| No range overlap | Vectorised masks are mutually exclusive | PASS |
| No unexplained gaps | Adjacent bands touch at boundaries | PASS |
| Unavailable records preserved | Non-Calculated records remain "Unavailable" | PASS |
| Calculated records never Unavailable | All Calculated records receive a status | PASS |

---

## 6. Formula and Classification Reconciliation

| Check | Result |
|-------|--------|
| Sandbox classifications match staged boundary definitions | PASS |
| No empty or null promoted_threshold_status values | PASS |
| Unavailable records correctly segregated from classification | PASS |
| Total records match source dataset (17,520) | PASS |
| Formula verification passed | PASS |
| Boundary case validation passed | PASS |
| Schema validation passed | PASS |
| Key validation passed | PASS |

---

## 7. Active Configuration Immutability

| Check | Before | After | Result |
|-------|--------|-------|--------|
| `config/kpi_threshold_config.csv` SHA-256 | `da2bd8b93c7737a772f741de146a457aee21e3431e1e4e61d1e32ce979fde54f` | `da2bd8b93c7737a772f741de146a457aee21e3431e1e4e61d1e32ce979fde54f` | **UNCHANGED** |
| Backup created | — | No | N/A (staging only) |
| Rollback path | — | Empty | N/A |

---

## 8. Promotion Readiness Assessment

### 8.1 Per-KPI Readiness

| KPI | Readiness | Reason |
|-----|-----------|--------|
| kpi_001 | Ready for Promotion | Decision valid and complete |
| kpi_002 | Ready for Promotion | Decision valid and complete |
| kpi_003 | Ready for Conditional Promotion | Conditional approval valid; provisional promotion permitted |
| kpi_004 | Ready for Promotion | Decision valid and complete |
| kpi_005 | Ready for Conditional Promotion | Conditional approval valid; provisional promotion permitted |
| kpi_006 | Ready for Promotion | Decision valid and complete |

### 8.2 Overall Readiness

| Metric | Value |
|--------|-------|
| Overall Promotion Readiness | **Ready with Conditions** |
| Step 2B-2 Readiness | Ready with Conditions |
| Blocking Issues | 0 |
| Recommended Next Action | Proceed to promotion when stakeholder confirms conditional requirements |

**Note:** The initial run incorrectly reported "Partially Ready" due to a logic error in `_build_manifest`: the `(approved + conditional) == 6` branch was missing, causing any mix of approved and conditional KPIs to fall through to the "Partially Ready" branch even when all 6 KPIs were accounted for. This has been corrected and a regression test added.

### 8.3 Promotion Gate Status

| Gate | Status |
|------|--------|
| `--promote-active-config` | NOT INVOKED |
| `--confirm-stakeholder-approval` | NOT INVOKED |
| Active config promotion | **BLOCKED** |

---

## 9. Files Generated

| File | Path |
|------|------|
| Decision Validation | `outputs/threshold_approval/threshold_approval_decision_validation.csv` |
| KPI Readiness | `outputs/threshold_approval/threshold_approval_kpi_readiness.csv` |
| Staged Config | `outputs/threshold_approval/threshold_approval_staged_config.csv` |
| Sandbox Classifications | `outputs/threshold_approval/threshold_approval_sandbox_classifications.csv` |
| Run Manifest | `outputs/threshold_approval/threshold_approval_run_manifest.json` |
| This Report | `docs/step_2b1b_mode_b_validation_report.md` |

---

## 10. Sign-Off

| Role | Status |
|------|--------|
| Decision Validation | 6/6 PASSED |
| Candidate Verification | 6/6 PASSED |
| Boundary Validation | 6/6 PASSED |
| Sandbox Classification | 17,520 records, all reconciled |
| Formula Verification | PASSED |
| Boundary Cases | 12/12 PASSED |
| Overall Readiness Logic | CORRECTED — Ready with Conditions |
| Regression Tests | 17/17 PASSED |
| Active Config Immutability | VERIFIED (checksum match) |
| Promotion | BLOCKED (flags not supplied) |
| Step 2B-2 | NOT STARTED |

---

*End of Mode B Validation Report*
