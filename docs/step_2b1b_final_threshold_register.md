# Sentinel360 — Final Threshold Register (Step 2B-1B)

## Register Control

| Field | Value |
|-------|-------|
| Register Version | v1.0-mixed-governance |
| Effective Date | 2026-07-28 |
| Promotion Run ID | THAPP-32EDF6F03C19 |
| Total KPIs | 6 |
| Fully Approved | 4 |
| Conditionally Approved | 2 |
| Provisional | 2 |

---

## Threshold Register

### kpi_001 — Staffing Level

| Attribute | Value |
|-----------|-------|
| KPI ID | kpi_001 |
| KPI Name | Staffing Level |
| Directionality | Higher is better |
| Unit | Percent |
| Green Range | [84.197, 100.000] |
| Amber Range | [80.000, 84.197) |
| Red Range | [0, 80.000) |
| Boundary Inclusivity | Lower boundary inclusive, upper exclusive; global maximum inclusive |
| Version | v1.0-approved |
| Approval Status | Approved |
| Provisional | No |
| Effective Date | 2026-07-28 |
| Decision Record | DEC-001 |
| Source Candidate | CAND-9132137F3353 (Balanced) |

### kpi_002 — Staff Absenteeism Rate

| Attribute | Value |
|-----------|-------|
| KPI ID | kpi_002 |
| KPI Name | Staff Absenteeism Rate |
| Directionality | Lower is better |
| Unit | Percent |
| Green Range | [0.000, 15.001] |
| Amber Range | (15.001, 19.048) |
| Red Range | [19.048, 50.000] |
| Boundary Inclusivity | Lower boundary inclusive, upper exclusive; global maximum inclusive |
| Version | v1.0-approved |
| Approval Status | Approved |
| Provisional | No |
| Effective Date | 2026-07-28 |
| Decision Record | DEC-002 |
| Source Candidate | CAND-401D561CEDE3 (Balanced) |

### kpi_003 — Bed Occupancy Rate

| Attribute | Value |
|-----------|-------|
| KPI ID | kpi_003 |
| KPI Name | Bed Occupancy Rate |
| Directionality | Context-sensitive |
| Unit | Percent |
| Low Utilisation | < 81.718% |
| Lower Amber | [81.718%, 86.119%) |
| Normal Operating Band (Green) | [86.119%, 100.160%] |
| Upper Amber | (100.160%, 104.762%) |
| Critical Capacity Pressure | ≥ 104.762% |
| Boundary Inclusivity | Lower boundary inclusive, upper exclusive; global maximum inclusive |
| Version | v1.0-provisional-approved |
| Approval Status | Conditionally Approved |
| Provisional | **Yes** |
| Effective Date | 2026-07-28 |
| Review Date | 2026-09-30 |
| Decision Record | DEC-003 |
| Source Candidate | CAND-302D7A9F11B5 (Balanced) |
| Conditions | Operational validation of dual-sided model and >100% occupancy treatment required |

### kpi_004 — Average Patient Waiting Time

| Attribute | Value |
|-----------|-------|
| KPI ID | kpi_004 |
| KPI Name | Average Patient Waiting Time |
| Directionality | Lower is better |
| Unit | Minutes |
| Green Range | [26.240, 47.242] |
| Amber Range | (47.242, 54.087) |
| Red Range | [54.087, 61.000] |
| Boundary Inclusivity | Lower boundary inclusive, upper exclusive; global maximum inclusive |
| Version | v1.0-approved |
| Approval Status | Approved |
| Provisional | No |
| Effective Date | 2026-07-28 |
| Decision Record | DEC-004 |
| Source Candidate | CAND-B80C86F00895 (Balanced) |

### kpi_005 — Patient Complaint Rate

| Attribute | Value |
|-----------|-------|
| KPI ID | kpi_005 |
| KPI Name | Patient Complaint Rate |
| Directionality | Lower is better |
| Unit | Complaints per 1000 encounters |
| Green Range | [0.000, 14.779] |
| Amber Range | (14.779, 19.744) |
| Red Range | [19.744, 75.000] |
| Boundary Inclusivity | Lower boundary inclusive, upper exclusive; global maximum inclusive |
| Version | v1.0-provisional-approved |
| Approval Status | Conditionally Approved |
| Provisional | **Yes** |
| Effective Date | 2026-07-28 |
| Review Date | 2026-10-25 |
| Decision Record | DEC-005 |
| Source Candidate | CAND-F76D963AE6DE (Balanced) |
| Conditions | Confirm complaint denominator stability within 90 days; recalibrate if methodology changes |

### kpi_006 — Patient Satisfaction Score

| Attribute | Value |
|-----------|-------|
| KPI ID | kpi_006 |
| KPI Name | Patient Satisfaction Score |
| Directionality | Higher is better |
| Unit | 1-5 Likert Score |
| Green Range | [2.803, 5.000] |
| Amber Range | [2.500, 2.803) |
| Red Range | [1.000, 2.500) |
| Boundary Inclusivity | Lower boundary inclusive, upper exclusive; global maximum inclusive |
| Version | v1.0-approved |
| Approval Status | Approved |
| Provisional | No |
| Effective Date | 2026-07-28 |
| Decision Record | DEC-006 |
| Source Candidate | CAND-A643D6F72D76 (Balanced) |

---

## Classification Burden Summary (Historical)

| KPI | Green | Amber | Red | Low Utilisation | Critical Capacity Pressure | Unavailable |
|-----|-------|-------|-----|-----------------|---------------------------|-------------|
| kpi_001 | 2,371 | 292 | 257 | — | — | 0 |
| kpi_002 | 2,330 | 297 | 293 | — | — | 0 |
| kpi_003 | 583 | 280 | — | 110 | 122 | 1,825 |
| kpi_004 | 877 | 108 | 110 | — | — | 1,825 |
| kpi_005 | 776 | 109 | 99 | — | — | 1,936 |
| kpi_006 | 1,996 | 156 | 231 | — | — | 537 |
| **Total** | **8,933** | **1,242** | **990** | **110** | **122** | **6,123** |

---

*End of Threshold Register*
