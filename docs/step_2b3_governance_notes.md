# Step 2B-3 Governance Notes

**Step:** 2B-3 — Department and KPI Risk Prioritisation Engine  
**Status:** COMPLETE

---

## 1. Provisional Threshold Governance

Two KPIs operate under provisional thresholds:

| KPI | Name | Approval Status | Threshold Is Provisional | Review Date |
|-----|------|-----------------|--------------------------|-------------|
| kpi_003 | Bed Occupancy Rate | Conditionally Approved | True | 2026-09-30 |
| kpi_005 | Patient Complaint Rate | Conditionally Approved | True | 2026-10-25 |

### Override from Authoritative Config

The Step 2B-2 watch-conditions output incorrectly flagged `threshold_is_provisional = True` for **all** KPIs. Step 2B-3 corrects this by overriding the field from the authoritative `config/kpi_threshold_config.csv` before risk scoring.

### Impact on Risk Scores

- Provisional KPI records receive a governance adjustment multiplier of **0.90**.
- This reduces the raw risk score but preserves visibility.
- Provisional breaches are still flagged with `BREACH_PROVISIONAL`.
- Provisional dominant drivers set `dominant_driver_is_provisional = True`.

### Department-Level Provisional Propagation (Refined)

- Every department-date record includes `provisional_risk_flag`.
- `provisional_kpi_count` indicates how many KPIs in that department-date are provisional.
- `provisional_driver_list` names the specific provisional KPIs.
- Because kpi_003 and kpi_005 exist in all departments, **all** 2,920 department-date records have `contains_provisional_kpi = True`.
- **However**, `provisional_risk_flag` is now refined to `True` only when provisional KPIs make a **material** contribution:

| Materiality | Count | Description |
|-------------|-------|-------------|
| None | 851 | Provisional KPIs are Green, unavailable, or otherwise non-contributing |
| Minor | 1,136 | Provisional contribution exists but is below the configured threshold |
| Material | 361 | Provisional contribution materially affects the department risk score |
| Dominant | 572 | A provisional KPI is the dominant risk driver |

- `provisional_risk_flag = True` only for **Material** (361) and **Dominant** (572) = **933** records.
- This prevents over-flagging departments where provisional KPIs are present but not materially contributing.

### Governance Fields

| Field | Meaning |
|-------|---------|
| `contains_provisional_kpi` | True when any provisional KPI is present in the department-date |
| `provisional_risk_flag` | True only when a provisional KPI makes a material contribution |
| `dominant_driver_is_provisional` | True only when the selected dominant KPI is provisional |
| `provisional_risk_contribution` | Sum of normalized risk scores from assessable provisional KPIs |
| `provisional_contribution_materiality` | None / Minor / Material / Dominant |

### Configuration-Driven Materiality Rules

- **None**: no assessable provisional KPI contribution (score = 0).
- **Minor**: provisional contribution > 0 but < `provisional_minor_threshold` (5.0 score points).
- **Material**: provisional contribution >= `provisional_materiality_threshold` (15.0 score points), or provisional KPI is contributing with score > 15.
- **Dominant**: the selected dominant risk driver is a provisional KPI.

---

## 2. Human-in-the-Loop Requirements

| Decision Point | Required Action | Current Status |
|----------------|-----------------|----------------|
| Finalise kpi_003 threshold | Stakeholder sign-off | Pending (review date: 2026-09-30) |
| Finalise kpi_005 threshold | Stakeholder sign-off | Pending (review date: 2026-10-25) |
| Approve risk scoring weights as policy | Stakeholder sign-off | Not requested (technical rules only) |

Until kpi_003 and kpi_005 are fully approved, Step 2B-4 readiness remains **Ready with Conditions**.

---

## 3. Data Quality & Audit

### Immutability Guarantee

- Upstream files protected by SHA-256 checksum verification.
- 12 files monitored before and after execution.
- No upstream modifications detected in this run.

### Audit Trail

- Every risk record carries `engine_run_id` and `processed_at`.
- Evidence packs link back to Step 2B-2 source records.
- Lineage preserves provenance from watch conditions through to department ranking.

---

## 4. Issue Management

| Issue ID | Description | Severity | Status |
|----------|-------------|----------|--------|
| None | No issues logged | — | — |

### Technical Debt: Upstream Step 2B-2 Provisional-Flag Defect

**Issue:** Step 2B-2 watch-conditions output incorrectly set `threshold_is_provisional = True` for **all** KPIs (17,520 records), instead of only the two provisionally approved KPIs (kpi_003 and kpi_005).

**Mitigation in Step 2B-3:**
- Step 2B-3 uses `config/kpi_threshold_config.csv` as the **authoritative governance source**.
- Before risk scoring, the engine overrides `threshold_is_provisional` from the active config.
- This ensures only kpi_003 and kpi_005 are treated as provisional, regardless of the upstream defect.

**Impact:**
- No downstream scores, tiers, or rankings were computed using the incorrect upstream flag.
- The override is deterministic and reproducible.
- **Remediation recommendation:** Fix the Step 2B-2 watch-conditions generation logic before the next quarterly refresh so the override is no longer necessary.

### Warning Register

| Warning Type | Count | Action |
|--------------|-------|--------|
| Provisional Dominant Driver | 572 | Visible in governance output; requires stakeholder review |
| Provisional Material Contribution | 361 | Visible in governance output; may affect tier/urgency interpretation |
| Low Confidence KPIs | 30 | Investigate data quality for these records |

---

## 5. Terminology

- **Governed risk output records:** All 17,520 source KPI records receive a risk score output.
- **Assessable records:** 11,397 records with `calculation_status == 'Calculated'`.
- **Not Assessable records:** 6,123 records with unavailable or insufficient data.
- **Department-date risk records:** 2,920 aggregated department summaries.
- **Hospital-date summary records:** 365 aggregated hospital summaries.

---

## 6. Closure Status

**Step 2B-3:** COMPLETE  
**Step 2B-4 Readiness:** Ready with Conditions
