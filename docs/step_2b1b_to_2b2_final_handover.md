# Sentinel360 — Step 2B-1B to Step 2B-2 Final Handover

## Handover Control

| Field | Value |
|-------|-------|
| From | Step 2B-1B (Stakeholder Review, Approval and Threshold Promotion) |
| To | Step 2B-2 (Diagnostic and Early-Warning Layer — Threshold Monitoring and Alerting) |
| Handover Date | 2026-07-27 |
| Promotion Run ID | THAPP-32EDF6F03C19 |
| Overall Governance Version | v1.0-mixed-governance |
| Step 2B-2 Readiness | Ready with Conditions |

---

## 1. Step 2B-1B Completion Summary

Step 2B-1B has been completed in full:

- **Mode A (Review Preparation):** Complete — 18 candidates reviewed across 6 KPIs
- **Mode B (Decision Validation + Active Promotion):** Complete — 6 decisions validated, staged config promoted

| Metric | Value |
|--------|-------|
| KPIs with Active Thresholds | 6 |
| Fully Approved | 4 |
| Conditionally Approved | 2 |
| Provisional Thresholds | 2 |
| Blocking Issues | 0 |

---

## 2. Active Threshold Configuration

The authoritative active threshold configuration is:

**`config/kpi_threshold_config.csv`**

Checksum: `29addaf81430734f16e434e022c3d7a98c5ff1a25d2ed4e70f718b27cfd5b2d0`

This file contains the promoted thresholds with complete boundary definitions, approval statuses, and governance metadata.

---

## 3. Threshold Summary for Step 2B-2

### 3.1 Fully Approved Thresholds (No Conditions)

These thresholds are ready for immediate use in monitoring and alerting:

| KPI | Name | Direction | Green | Amber | Red | Unit |
|-----|------|-----------|-------|-------|-----|------|
| kpi_001 | Staffing Level | Higher is better | ≥ 84.197% | 80.0% – 84.197% | < 80.0% | Percent |
| kpi_002 | Staff Absenteeism Rate | Lower is better | ≤ 15.001% | 15.001% – 19.048% | ≥ 19.048% | Percent |
| kpi_004 | Average Patient Waiting Time | Lower is better | ≤ 47.242 min | 47.242 – 54.087 min | ≥ 54.087 min | Minutes |
| kpi_006 | Patient Satisfaction Score | Higher is better | ≥ 2.803 | 2.500 – 2.803 | < 2.500 | 1-5 Likert |

### 3.2 Conditionally Approved Thresholds (With Monitoring)

These thresholds are active but require ongoing monitoring of their conditions:

| KPI | Name | Condition | Review Date |
|-----|------|-----------|-------------|
| kpi_003 | Bed Occupancy Rate | Operational validation of dual-sided model and >100% occupancy | 2026-09-30 |
| kpi_005 | Patient Complaint Rate | Confirm denominator stability; recalibrate if methodology changes | 2026-10-25 |

---

## 4. Key Artifacts for Step 2B-2

| Artifact | Path | Purpose |
|----------|------|---------|
| Active Threshold Config | `config/kpi_threshold_config.csv` | Source of truth for all threshold boundaries |
| Final Threshold Register | `docs/step_2b1b_final_threshold_register.md` | Human-readable threshold documentation |
| Promotion Report | `docs/step_2b1b_threshold_promotion_report.md` | Complete promotion audit trail |
| Post-Promotion Classification | `outputs/threshold_approval/threshold_approval_post_promotion_classification.csv` | Historical classification with promoted thresholds |
| Staged Config | `outputs/threshold_approval/threshold_approval_staged_config.csv` | Snapshot of staged configuration at promotion time |
| Decision Validation | `outputs/threshold_approval/threshold_approval_decision_validation.csv` | Validated stakeholder decisions |
| KPI Readiness | `outputs/threshold_approval/threshold_approval_kpi_readiness.csv` | Per-KPI readiness assessment |

---

## 5. Classification Rules for Step 2B-2

### 5.1 Higher is Better (kpi_001, kpi_006)

```
Red:    [min, lower_red)
Amber:  [lower_red, green_lower)
Green:  [green_lower, max]   (max inclusive)
```

### 5.2 Lower is Better (kpi_002, kpi_004, kpi_005)

```
Green:  [min, green_upper]   (green_upper inclusive)
Amber:  (green_upper, upper_red)
Red:    [upper_red, max]     (upper_red inclusive)
```

### 5.3 Context-Sensitive (kpi_003)

```
Low Utilisation:              [min, lower_red)
Amber (Low):                  [lower_red, green_lower)
Green (Normal Operating Band): [green_lower, green_upper]
Amber (High):                 (green_upper, upper_red)
Critical Capacity Pressure:   [upper_red, max]
```

---

## 6. Conditional Monitoring Requirements

Step 2B-2 must implement monitoring for the following conditional requirements:

### 6.1 kpi_003 Bed Occupancy Rate

- **Alert trigger:** Track when occupancy exceeds 100.160% (upper green boundary)
- **Escalation:** Critical Capacity Pressure at ≥ 104.762%
- **Underutilisation alert:** Low Utilisation at < 81.718%
- **Operational validation required by:** 2026-09-30

### 6.2 kpi_005 Patient Complaint Rate

- **Denominator tracking:** Monitor patient encounter count for stability
- **Alert trigger:** Track when complaint rate exceeds 14.779 per 1000 encounters
- **Recalibration trigger:** If denominator methodology changes
- **Review required by:** 2026-10-25

---

## 7. Immutability Preservation

The following files must remain unchanged during Step 2B-2:

| File/Directory | Status |
|----------------|--------|
| Phase 1 outputs | Preserved |
| Phase 2A outputs | Preserved |
| Step 2B-1 outputs | Preserved |
| Step 2B-1A outputs | Preserved |
| Stakeholder decision file | Preserved |
| Staging evidence | Preserved |
| Backup (`config/archive/kpi_threshold_config_pre_2b1b_promotion.csv`) | Preserved |

---

## 8. Step 2B-2 Readiness

| Readiness Item | Status |
|----------------|--------|
| Active thresholds defined | Ready |
| Boundary values validated | Ready |
| Classification rules documented | Ready |
| Conditional monitoring requirements defined | Ready |
| Historical classification baseline established | Ready |
| Test suite passing | Ready |
| Backup and rollback path verified | Ready |
| Governance version recorded | Ready |

**Overall Step 2B-2 Readiness: Ready with Conditions**

---

## 9. Recommended Step 2B-2 Tasks

1. Implement real-time threshold monitoring using `config/kpi_threshold_config.csv`
2. Build alerting logic for Green/Amber/Red transitions
3. Implement dual-sided state reporting for kpi_003
4. Add conditional monitoring dashboards for kpi_003 and kpi_005
5. Schedule conditional review reminders for 2026-09-30 and 2026-10-25
6. Establish recalibration workflow for kpi_005 denominator changes

---

*End of Handover Document*
