# Step 2B-2 Governance Notes

**Step:** 2B-2 — Threshold Breach & Watch Condition Engine  
**Status:** COMPLETE

---

## 1. Provisional Threshold Governance

Two KPIs operate under provisional thresholds pending further stakeholder review:

| KPI | Name | Approval Status | Threshold Is Provisional | Review Date |
|-----|------|-----------------|--------------------------|-------------|
| kpi_003 | Bed Occupancy Rate | Conditionally Approved | True | Monitored |
| kpi_005 | Staffing Ratio | Conditionally Approved | True | Monitored |

### Impact on Breach Classification

- Provisional records that trigger a breach receive `BREACH_PROVISIONAL` instead of a specific breach type (`BREACH_UPPER_RED` or `BREACH_LOWER_RED`).
- This override **only applies when `breach_flag == True`**. Non-provisional records always retain specific breach types.
- Provisional status is explicitly flagged in `analytical_kpi_watch_governance.csv`.

### Review Date Monitoring

- Watch condition engine monitors upcoming review dates for provisional KPIs.
- Warning window: 30 days before review date.
- Triggered watches are classified as `REVIEW_DUE` with `LOW` severity.

---

## 2. Human-in-the-Loop Requirements

| Decision Point | Required Action | Current Status |
|----------------|-----------------|----------------|
| Approve kpi_003 threshold as final | Stakeholder sign-off | Pending |
| Approve kpi_005 threshold as final | Stakeholder sign-off | Pending |
| Set formal review dates | Enter dates in stakeholder decisions file | Pending |

Until these actions are completed, Step 2B-3 readiness remains **Ready with Conditions**.

---

## 3. Data Quality & Audit

### Immutability Guarantee

- Upstream files are protected by SHA-256 checksum verification.
- Checksums are recorded before and after every engine execution.
- No upstream file modifications occurred during Step 2B-2.

### Audit Trail

- Every classification, breach, and watch output carries lineage metadata.
- Source: `analytical_kpi_watch_lineage.csv` and `analytical_kpi_watch_evidence.csv`.
- Run ID: `THBREACHWATCH-20260727213903`

---

## 4. Issue Management

| Issue ID | Description | Severity | Status |
|----------|-------------|----------|--------|
| None | No issues logged | — | — |

---

## 5. Terminology Governance

To ensure consistent communication with stakeholders:

- **Governed breach output records (17,520):** Total records that received a breach classification output. This includes `NO_BREACH` and `UNAVAILABLE`.
- **Actual breach events (2,464):** Subset where `breach_flag == True`.
- **Governed watch output records (17,520):** Total records that received a watch evaluation output. This includes records with no active watch condition.
- **Actual watch conditions (9,120):** Subset where `watch_condition_flag == True`.

All reports, dashboards, and stakeholder communications must use this precise terminology.

---

## 6. Retention & Versioning

| Artifact | Retention Policy |
|----------|------------------|
| Analytical outputs | Immutable; versioned by run ID |
| Validation outputs | Immutable; versioned by run ID |
| Config files | Versioned; active config backed up before promotion |
| Test results | Recorded in manifest and validation report |

---

## 7. Closure Status

**Step 2B-2:** COMPLETE  
**Step 2B-3 Readiness:** Ready with Conditions
