# Step 2C-2A Input Inventory

**Date:** 2026-07-28  
**Phase:** Sentinel360 Healthcare — Phase 2C-2  
**Step:** 2C-2A Input and Architecture Review  
**Status:** COMPLETE

---

## 1. Authoritative Scenario-Input Files

### 1.1 Episode Approval Package Register

| Attribute | Value |
|-----------|-------|
| **File path** | `data/scenario_inputs/step_2c1d_episode_approval_package_register.csv` |
| **Availability** | Present |
| **Readability** | Valid CSV; pandas-readable |
| **Row count** | 646 |
| **Column count** | 71 |
| **Duplicate-key count** | 0 (unique on `approval_package_id`) |
| **Missing required fields** | None |
| **Apparent version** | Step 2C-1D calibrated |
| **Suitable for Phase 2C-2** | Yes |

**Key fields for scenario eligibility:**
- `scenario_review_required` (boolean)
- `scenario_review_priority` (Required / Recommended / Not Required)
- `scenario_review_reason`
- `scenario_review_scope`
- `dominant_kpi_id`
- `maximum_priority_tier`
- `provisional_threshold_flag`
- `contradiction_severity`
- `financial_review_required`

### 1.2 Recommendation Approval Linkage Register

| Attribute | Value |
|-----------|-------|
| **File path** | `data/scenario_inputs/step_2c1d_recommendation_approval_linkage_register.csv` |
| **Availability** | Present |
| **Readability** | Valid CSV |
| **Row count** | 2,600 |
| **Column count** | 14 |
| **Duplicate-key count** | 0 (composite key: `approval_package_id` + `recommendation_id`) |
| **Missing required fields** | None |
| **Apparent version** | Step 2C-1D calibrated |
| **Suitable for Phase 2C-2** | Yes |

### 1.3 Validated Recommendation Register

| Attribute | Value |
|-----------|-------|
| **File path** | `data/scenario_inputs/step_2c1c_validated_recommendation_register.csv` |
| **Availability** | Present |
| **Readability** | Valid CSV |
| **Row count** | 2,881 |
| **Column count** | 77 |
| **Duplicate-key count** | 0 (unique on `recommendation_id`) |
| **Missing required fields** | None |
| **Apparent version** | Step 2C-1C corrected |
| **Suitable for Phase 2C-2** | Yes |

### 1.4 Corrected Episode Register

| Attribute | Value |
|-----------|-------|
| **File path** | `data/scenario_inputs/step_2c1c_corrected_episode_register.csv` |
| **Availability** | Present |
| **Readability** | Valid CSV |
| **Row count** | 646 |
| **Column count** | 17 |
| **Duplicate-key count** | 0 (unique on `episode_id`) |
| **Missing required fields** | None |
| **Apparent version** | Step 2C-1C corrected |
| **Suitable for Phase 2C-2** | Yes |

### 1.5 Version Confirmation

All four files are the **most recent corrected and calibrated versions**. No older or uncalibrated copies were found in `data/scenario_inputs/`. The `step_2c1d` prefix confirms calibration, and the `step_2c1c` prefix confirms correction.

---

## 2. Scenario-Eligible Package Inventory

### 2.1 Required (Scenario Engine Population)

| Metric | Value |
|--------|-------|
| **Count** | 346 |
| **Hospitals** | 1 (HOSP-001) |
| **Departments** | 8 |
| **Dominant KPIs** | kpi_001 (174), kpi_002 (165), kpi_004 (7) |
| **Priority tiers** | High (155), Critical (60), Elevated (50), mixed tiers (81) |
| **Recommendation type** | Immediate Stabilisation (100%) |
| **Scenario review scope** | Episode-level operational configuration (100%) |
| **Provisional dominant driver** | None (kpi_001, kpi_002, kpi_004 are all approved) |

### 2.2 Recommended (Optional Review Group)

| Metric | Value |
|--------|-------|
| **Count** | 11 |
| **Hospitals** | 1 (HOSP-001) |
| **Departments** | 3 (DEPT-DIAG, DEPT-ED, DEPT-OPC) |
| **Dominant KPI** | kpi_004 (100%) |
| **Reason** | Multiple alternatives at hospital operations level |
| **Scenario review scope** | NaN (not pre-assigned) |

### 2.3 Not Required (Excluded from Scenario Engine)

| Metric | Value |
|--------|-------|
| **Count** | 289 |
| **Hospitals** | 1 (HOSP-001) |
| **Departments** | 8 |
| **Dominant KPIs** | kpi_006 (176), kpi_003 (58), kpi_005 (46), kpi_004 (9) |
| **Exclusion basis** | Lower operational impact or monitoring-only priority |

### 2.4 Exclusion Rationale

The 289 Not Required packages are **retained in the eligibility register** with `scenario_engine_status = Exclude`. They are not deleted. This preserves auditability and allows future reclassification if priorities change.

---

## 3. Existing Scenario Resources

### 3.1 Configuration

| File | Status | Assessment |
|------|--------|------------|
| `config/scenario_assumption_config.csv` | Present | 18 placeholder assumptions (Draft, no default values). Not yet populated with operational defaults. **Not suitable for direct use** without further configuration. |

### 3.2 Source Code

| Resource | Status | Assessment |
|----------|--------|------------|
| Scenario engine | **Not found** | No `src/scenario*.py` files exist |
| Simulation code | **Not found** | No Monte Carlo, discrete-event, or system-dynamics code exists |
| Streamlit Scenario Lab | **Not found** | No `pages/scenario*.py` or `app.py` exists |
| Scenario tests | **Not found** | No `tests/test_scenario*.py` files exist |

### 3.3 Baseline Data

| File | Status | Assessment |
|------|--------|------------|
| `data/analytical/analytical_six_kpi_daily.csv` | Present | 17,520 rows; all 6 KPIs integrated. **Partial coverage** (11,397 Calculated; 4,248 Insufficient Data; 1,875 Zero Denominator). |
| `data/analytical/analytical_workforce_kpi_daily.csv` | Present | 5,840 rows; kpi_001 and kpi_002. **Full coverage, High confidence.** |
| `data/analytical/analytical_patient_flow_kpi_daily.csv` | Present | 5,840 rows; kpi_003 and kpi_004. **Mixed coverage** (kpi_003 mostly Unavailable; kpi_004 partial). |
| `data/analytical/analytical_patient_experience_kpi_daily.csv` | Present | 5,840 rows; kpi_005 and kpi_006. **Mixed coverage** (kpi_005 mostly Zero Denominator; kpi_006 partial Medium confidence). |

### 3.4 Supporting Analytical Data

| File | Relevance |
|------|-----------|
| `analytical_department_risk_daily.csv` | Department context, tiers, urgency |
| `analytical_kpi_risk_scores_daily.csv` | Risk scores by KPI |
| `analytical_kpi_threshold_classification_daily.csv` | Threshold states for baseline derivation |
| `analytical_kpi_rolling_statistics.csv` | Trend and variance inputs |
| `analytical_contributing_factor_scores.csv` | Relationship strength for cross-KPI effects |
| `analytical_relationship_network_edges.csv` | Network structure for intervention propagation |
| `analytical_department_contributing_factor_summary.csv` | Best supported relationships per department |

### 3.5 Summary

**No existing scenario engine, simulation code, or Streamlit UI exists.** The project has rich baseline and relationship data for workforce KPIs, partial data for patient-flow and experience KPIs, and a placeholder assumption configuration. Phase 2C-2B will need to build the scenario assumption catalogue from first principles, using the existing analytical data as baselines.

---

## 4. Data Quality by KPI

| KPI | Domain | Total Rows | Calculated | Insufficient Data | Zero Denominator | Confidence | Scenario Readiness |
|-----|--------|------------|------------|-------------------|------------------|------------|-------------------|
| kpi_001 | Workforce | 2,920 | 2,920 | 0 | 0 | High | Excellent |
| kpi_002 | Workforce | 2,920 | 2,920 | 0 | 0 | High | Excellent |
| kpi_003 | Patient Flow | 2,920 | 0 | 2,920 | 0 | Unavailable | Poor |
| kpi_004 | Patient Flow | 2,920 | 2,190 | 730 | 0 | High (where available) | Moderate |
| kpi_005 | Patient Experience | 2,920 | 0 | 598 | 1,875 | Unavailable / Zero Denominator | Poor |
| kpi_006 | Patient Experience | 2,920 | 1,347 | 1,875 | 0 | Medium | Moderate |

*Row counts inferred from domain files (2,920 = 8 departments × 365 days).*

---

## 5. Frozen-Upstream Integrity

No frozen Phase 1, Phase 2A, Phase 2B, Step 2C-1, or Step 2C-1D files were modified during this review. All inspections were read-only.
