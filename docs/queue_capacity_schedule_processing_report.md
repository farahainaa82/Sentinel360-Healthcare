# Queue, Bed Capacity and Service Schedule Processing Report

**Step:** 2D-3B  
**Processing Run ID:** PROC-QCS-92010F32B162  
**Validation Run ID:** VAL-C62B370EC6C3  
**Date:** 2026-07-26  
**Transformation Version:** 2D-3B-1.0.0

---

## 1. Files Created

### Processed Datasets
| File | Rows | Status |
|------|------|--------|
| `data/processed/processed_patient_queue.csv` | 1095 | Created |
| `data/processed/processed_bed_capacity.csv` | 1095 | Created |
| `data/processed/processed_service_schedule.csv` | 8760 | Created |

### Control Outputs
| File | Status |
|------|--------|
| `outputs/logs/queue_capacity_schedule_processing_run_manifest.json` | Created |
| `outputs/logs/queue_capacity_schedule_processing_dataset_summary.csv` | Created |
| `outputs/logs/queue_capacity_schedule_processing_issue_log.csv` | Created |
| `outputs/logs/queue_capacity_schedule_processing_lineage.csv` | Created |
| `outputs/logs/queue_capacity_schedule_processing_exclusion_register.csv` | Created |
| `outputs/logs/queue_capacity_schedule_processing_audit_log.csv` | Created |

---

## 2. Source and Processed Row Counts

| Dataset | Source Rows | Processed Rows | Excluded Rows |
|---------|-------------|----------------|---------------|
| patient_queue_records | 1095 | 1095 | 0 |
| bed_capacity_records | 1095 | 1095 | 0 |
| service_schedule | 8760 | 8760 | 0 |

---

## 3. Exclusions and Issues

### Exclusions
- **Total exclusions:** 0
- All source records passed validation and transformation rules.

### Issues by Severity
| Severity | Count |
|----------|-------|
| Information | 1349 |
| Warning | 0 |
| Error | 0 |
| Critical | 0 |

The 1,349 Information-level issues relate to unsupported queue stage values that are preserved in the output for downstream rule refinement.

---

## 4. Queue Transformation Results

- **IDs preserved and unique:** Yes (1095 unique `queue_record_id` values)
- **Queue-stage detail preserved:** Yes (6 distinct stages retained)
- **Queue dates parsed correctly:** Yes
- **Reporting month format (YYYY-MM):** Yes
- **Negative queue counts detected:** Yes (tested and validated)
- **Blank queue values remain null:** Yes
- **Wait values non-negative:** Yes
- **Valid records:** 1095 / 1095 (100%)

---

## 5. Bed-Capacity and Overcapacity Results

- **IDs preserved and unique:** Yes (1095 unique `bed_capacity_record_id` values)
- **Bed counts non-negative:** Yes
- **Negative bed counts detected:** Yes (tested and validated)
- **Occupied beds may exceed operational beds:** Yes
- **Occupied beds capped:** **No** — confirmed explicitly
- **Overcapacity records:** 230
- **Overcapacity flagged correctly:** Yes
- **Overcapacity not automatically invalid:** Yes
- **Valid records:** 1095 / 1095 (100%)

---

## 6. Service-Schedule Results

- **IDs preserved and unique:** Yes (8760 unique `service_schedule_id` values)
- **Service dates parsed correctly:** Yes
- **Session timestamps parsed correctly:** Yes
- **Cross-midnight sessions handled:** Yes (23:00 to 07:00 correctly produces 8 hours)
- **Planned service hours calculated:** Yes (using source `planned_hours` with timestamp fallback)
- **Cancelled sessions:** 38
- **Reduced sessions:** 43
- **Extended sessions:** 0
- **Blank planned capacity remains null:** Yes (0 nulls in this dataset)
- **Valid records:** 8760 / 8760 (100%)

---

## 7. Lineage Coverage

- **Total lineage records:** 10,950
- **Queue lineage:** 1,095 (100% coverage)
- **Bed lineage:** 1,095 (100% coverage)
- **Schedule lineage:** 8,760 (100% coverage)

---

## 8. Checksum Verification

| Check | Result |
|-------|--------|
| Source files unchanged | **Confirmed** |
| Workforce processed outputs unchanged | **Confirmed** |
| `processed_patient_encounters.csv` unchanged | **Confirmed** |
| `processed_patient_flow_daily.csv` created | **No** |

---

## 9. Processed-Schema Validation

| Dataset | Result |
|---------|--------|
| processed_patient_queue | **PASSED** |
| processed_bed_capacity | **PASSED** |
| processed_service_schedule | **PASSED** |

---

## 10. Step 2D-3B Test Result

- **Test file:** `tests/test_queue_capacity_schedule_transformation.py`
- **Tests run:** 61
- **Passed:** 61
- **Failed:** 0
- **Status:** **PASSED**

---

## 11. Prior Accepted Regression Status

- **Step 2D-1:** Processing architecture and processed schemas — accepted
- **Step 2D-2:** Workforce and reference-data transformation — accepted
- **Step 2D-3A:** Patient encounter transformation — accepted (209 tests passed)

No shared architecture, validation, or workforce files were modified during Step 2D-3B. Full cumulative regression testing is deferred to Step 2D-3E.

---

## 12. Unresolved Rules

- Average Patient Waiting Time KPI calculation — deferred to later step
- Bed Occupancy Rate KPI calculation — deferred to later step
- Official wait-stage eligibility rules — pending clinical rule refinement
- Extended session classification — no extended sessions detected in demo data

---

## 13. Known Limitations

- `encounter_derived_flag` is not inferred when absent from source metadata.
- `summary_source_flag` is not inferred when absent from source metadata.
- Overnight session detection (>12 hours) returned 0 in this dataset because all sessions are exactly 8 hours; cross-midnight handling is implemented and tested.
- Extended session count is 0 because no extended sessions exist in the demo source data.

---

## 14. Readiness for Step 2D-3C

Step 2D-3B is **complete** and accepted.

Step 2D-3C will build:

- `processed_patient_flow_daily`

It will combine approved preparation-level fields from:

- `processed_patient_encounters`
- `processed_patient_queue`
- `processed_bed_capacity`
- `processed_service_schedule`

Step 2D-3C will **not** calculate official KPI percentages, KPI status, trends, anomalies, risks, forecasts, scenarios, financial impact or recommendations.
