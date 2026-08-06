# Sentinel360 Step 2B-1B — Active Threshold Promotion Report

## Document Control

| Field | Value |
|-------|-------|
| Step | 2B-1B Mode B (Active Promotion) |
| Run ID | THAPP-32EDF6F03C19 |
| Date | 2026-07-27 |
| Status | Complete |
| Overall Governance Version | v1.0-mixed-governance |

---

## 1. Executive Summary

Active threshold promotion executed successfully for all six KPIs. The validated staged configuration was promoted atomically to `config/kpi_threshold_config.csv` with full governance controls. Four KPIs were fully approved and two were conditionally approved. No rollback was required.

| Metric | Value |
|--------|-------|
| KPIs Promoted | 6 |
| Fully Approved | 4 |
| Conditionally Approved | 2 |
| Provisional KPIs | 2 |
| Blocking Issues | 0 |
| Warnings | 0 |
| Rollback Required | No |

---

## 2. Promotion Governance

### 2.1 Required Controls

| Control | Status |
|---------|--------|
| `--promote-active-config` | **USED** |
| `--confirm-stakeholder-approval` | **USED** |
| Both flags present | Yes |

### 2.2 Pre-Promotion Backup

| Property | Value |
|----------|-------|
| Backup path | `config/archive/kpi_threshold_config_pre_2b1b_promotion.csv` |
| Backup checksum | `da2bd8b93c7737a772f741de146a457aee21e3431e1e4e61d1e32ce979fde54f` |
| Original checksum | `da2bd8b93c7737a772f741de146a457aee21e3431e1e4e61d1e32ce979fde54f` |
| Backup verified | **YES** |

---

## 3. Promoted Threshold Register

| KPI | Name | Direction | Version | Provisional | Status | Green Lower | Green Upper | Lower Red | Upper Red | Unit |
|-----|------|-----------|---------|-------------|--------|-------------|-------------|-----------|-----------|------|
| kpi_001 | Staffing Level | Higher is better | v1.0-approved | No | Approved | 84.197 | 100.000 | 80.0 | — | Percent |
| kpi_002 | Staff Absenteeism Rate | Lower is better | v1.0-approved | No | Approved | 0.0 | 15.001 | — | 19.048 | Percent |
| kpi_003 | Bed Occupancy Rate | Context-sensitive | v1.0-provisional-approved | **Yes** | Conditionally Approved | 86.119 | 100.160 | 81.718 | 104.762 | Percent |
| kpi_004 | Average Patient Waiting Time | Lower is better | v1.0-approved | No | Approved | 26.240 | 47.242 | — | 54.087 | Minutes |
| kpi_005 | Patient Complaint Rate | Lower is better | v1.0-provisional-approved | **Yes** | Conditionally Approved | 0.0 | 14.779 | — | 19.744 | Complaints per 1000 |
| kpi_006 | Patient Satisfaction Score | Higher is better | v1.0-approved | No | Approved | 2.803 | 5.000 | 2.5 | — | 1-5 Likert Score |

---

## 4. Conditional Approvals

### 4.1 kpi_003 — Bed Occupancy Rate

- **Condition:** Dual-sided occupancy model must be operationally validated before hospital deployment. Treatment of occupancy above 100% requires sign-off.
- **Review Date:** 2026-09-30
- **State Mapping:**
  - Low Utilisation: `< 81.718%`
  - Normal Operating Band: `86.119% – 100.160%`
  - Elevated Occupancy: `100.160% – 104.762%`
  - Critical Capacity Pressure: `≥ 104.762%`

### 4.2 kpi_005 — Patient Complaint Rate

- **Condition:** Denominator (patient encounters) accuracy and stability must be confirmed within 90 days. Recalibration required if denominator methodology changes.
- **Review Date:** 2026-10-25

---

## 5. Post-Promotion Validation

### 5.1 Active Configuration Verification

| Check | Result |
|-------|--------|
| Schema (25 columns) | PASS |
| Row count (6) | PASS |
| Six KPI coverage | PASS |
| Versions correct | PASS |
| Provisional flags correct | PASS |
| Boundary values exact | PASS |
| Boundary inclusivity rules | PASS |
| Decision record linkage | PASS |
| Effective dates | PASS |
| Review dates (conditional) | PASS |

### 5.2 Staged-to-Active Equivalence

| Comparison | Result |
|------------|--------|
| Column count | Exact match |
| Row count | Exact match |
| All boundary values | Exact match |
| All metadata fields | Exact match |
| Permitted differences | None (only promotion_run_id and created_at are operational metadata) |

### 5.3 Post-Promotion Sandbox Classification

| Status | Count | Expected | Match |
|--------|-------|----------|-------|
| Green | 8,933 | 8,933 | YES |
| Amber | 1,242 | 1,242 | YES |
| Red | 990 | 990 | YES |
| Critical Capacity Pressure | 122 | 122 | YES |
| Low Utilisation | 110 | 110 | YES |
| Unavailable | 6,123 | 6,123 | YES |
| **Total** | **17,520** | **17,520** | **YES** |

### 5.4 Boundary Case Verification

| KPI | Test Value | Expected | Actual | Result |
|-----|------------|----------|--------|--------|
| kpi_001 | 80.0 (lower_red) | Amber | Amber | PASS |
| kpi_001 | 84.197 (green_lower) | Green | Green | PASS |
| kpi_001 | 100.0 (max) | Green | Green | PASS |
| kpi_002 | 15.001 (green_upper) | Green | Green | PASS |
| kpi_002 | 19.048 (upper_red) | Red | Red | PASS |
| kpi_003 | 81.718 (lower_red) | Amber | Amber | PASS |
| kpi_003 | 86.119 (green_lower) | Green | Green | PASS |
| kpi_003 | 100.160 (green_upper) | Green | Green | PASS |
| kpi_003 | 104.762 (upper_red) | Critical Capacity Pressure | Critical Capacity Pressure | PASS |
| kpi_006 | 2.5 (lower_red) | Amber | Amber | PASS |
| kpi_006 | 2.803 (green_lower) | Green | Green | PASS |
| kpi_006 | 5.0 (max) | Green | Green | PASS |

---

## 6. Test Results

| Suite | Tests | Passed | Failed |
|-------|-------|--------|--------|
| Threshold Calibration | 24 | 24 | 0 |
| Threshold Approval | 17 | 17 | 0 |
| **Total** | **41** | **41** | **0** |

---

## 7. Rollback Status

| Property | Value |
|----------|-------|
| Rollback required | No |
| Rollback executed | No |
| Backup integrity | Verified |
| Restoration path | `config/archive/kpi_threshold_config_pre_2b1b_promotion.csv` |

---

## 8. Final Status

| Milestone | Status |
|-----------|--------|
| Step 2B-1B Mode A (Review Preparation) | Complete |
| Step 2B-1B Mode B (Decision Validation) | Complete |
| Step 2B-1B Overall | **Complete** |
| Active Config Promotion | **Complete** |
| Overall Promotion Readiness | Ready with Conditions |
| Step 2B-2 Readiness | Ready with Conditions |

---

## 9. Next Steps

1. **Step 2B-2** is ready to begin when explicitly instructed.
2. Conditional KPIs (kpi_003, kpi_005) require review by their respective dates.
3. No further action required for fully approved KPIs.

---

*End of Promotion Report*
