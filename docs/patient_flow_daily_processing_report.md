# Patient Flow Daily Processing Report

## Step 2D-3C

---

## 1. Processing Run ID

`PROC-PFD-0F1A2B3C4D5E`

---

## 2. Input Processing Run IDs

| Step | Run ID |
|------|--------|
| 2D-3A (Patient Encounters) | `PROC-ENC-001` |
| 2D-3B (Queue, Bed, Schedule) | `PROC-QCS-001` |

---

## 3. Files Created

| File | Path |
|------|------|
| Processed dataset | `data/processed/processed_patient_flow_daily.csv` |
| Run manifest | `outputs/logs/patient_flow_daily_processing_run_manifest.json` |
| Dataset summary | `outputs/logs/patient_flow_daily_processing_dataset_summary.csv` |
| Issue log | `outputs/logs/patient_flow_daily_processing_issue_log.csv` |
| Lineage | `outputs/logs/patient_flow_daily_processing_lineage.csv` |
| Exclusion register | `outputs/logs/patient_flow_daily_processing_exclusion_register.csv` |
| Audit log | `outputs/logs/patient_flow_daily_processing_audit_log.csv` |

---

## 4. Input Row Counts

| Dataset | Rows |
|---------|------|
| processed_patient_encounters | 93,958 |
| processed_patient_queue | 1,095 |
| processed_bed_capacity | 1,095 |
| processed_service_schedule | 8,760 |
| **Total** | **104,908** |

---

## 5. Output Row Count

**2,920** daily rows

---

## 6. Daily Grain Uniqueness

- `patient_flow_daily_id` is unique across all 2,920 rows.
- No duplicate `hospital_id` + `department_id` + `reporting_date` combinations.

---

## 7. Encounter Aggregation Results

| Field | Total |
|-------|-------|
| encounter_count | 93,958 |
| completed_encounter_count | 91,204 |
| cancelled_encounter_count | 1,394 |
| left_before_service_count | 1,360 |
| official_wait_eligible_encounter_count | 0 |
| total_arrival_to_consultation_minutes | null (all rows) |

Note: `official_wait_stage_eligible_flag` is `False` for all encounters in the source data, so no wait-minute totals are accumulated. This is analytically correct — null is preserved where no eligible input exists.

---

## 8. Queue Aggregation Results

- Queue data covers 1,095 daily grain rows (3 departments × 365 days).
- All queue groups contain a single record per grain; no multi-stage ambiguity was detected.
- `summary_source_flag` is available where applicable.
- No ambiguous queue aggregation issues were logged.

---

## 9. Ambiguous Queue-Group Count

**0** — No ambiguous multi-stage queue groups exist in the current processed input.

---

## 10. Queue Double-Count Protection Result

- All queue daily groups have exactly one source record.
- No double-counting risk was encountered.
- The builder's logic correctly prefers `summary_source_flag == True` when present.

---

## 11. Bed-Capacity Selection Result

- Bed data covers 1,095 daily grain rows (3 departments × 365 days).
- All bed daily groups contain exactly one record per grain.
- No duplicate bed snapshots were detected.
- Single-record groups were used directly.

---

## 12. Duplicate Bed-Snapshot Count

**0**

---

## 13. Confirmation That Occupied Beds Were Not Capped

- `occupied_beds` exceeds `operational_beds` in **230** rows.
- Occupied beds were never capped.
- The maximum `occupied_beds` value was preserved without reduction.

---

## 14. Overcapacity-Row Count

**230** rows where `occupied_beds > operational_beds`.

---

## 15. Service-Schedule Aggregation Result

- Service schedule data covers 8,760 rows.
- Daily aggregation produced counts for all 2,920 spine rows.

---

## 16. Cancelled, Reduced and Extended-Session Totals

| Field | Total |
|-------|-------|
| planned_service_session_count | 8,722 |
| cancelled_service_session_count | 38 |
| reduced_service_session_count | 43 |
| extended_service_session_count | 0 |

---

## 17. Cross-Midnight Handling Result

- Cross-midnight sessions were already handled in Step 2D-3B.
- The daily aggregation does not duplicate overnight sessions across dates.
- Each session is counted under its assigned `reporting_date` only.

---

## 18. Null-Versus-Zero Verification

| Field | Nulls | Zeros | Rule |
|-------|-------|-------|------|
| encounter_count | 0 | 1,825 | Count: zero when no encounters |
| completed_encounter_count | 0 | 1,825 | Count: zero when none |
| cancelled_encounter_count | 0 | 1,825 | Count: zero when none |
| left_before_service_count | 0 | 1,825 | Count: zero when none |
| official_wait_eligible_encounter_count | 0 | 2,920 | Count: zero when none |
| planned_service_session_count | 0 | 1,825 | Count: zero when none |
| cancelled_service_session_count | 0 | 1,825 | Count: zero when none |
| total_arrival_to_consultation_minutes | 2,920 | 0 | Measurement: null when no eligible data |
| queue_average_wait_minutes | 1,825 | 0 | Measurement: null when no queue data |
| licensed_beds | 0 | 0 | Measurement: present for all rows |

Rules applied correctly.

---

## 19. Issue Counts

| Severity | Count |
|----------|-------|
| Information | 0 |
| Warning | 0 |
| Error | 0 |
| Critical | 0 |

No issues were generated. This is expected because:
- All input schemas passed validation.
- No duplicate bed snapshots exist.
- No ambiguous queue stages exist.
- No duplicate daily identifiers exist.

---

## 20. Exclusion Counts

**0** exclusions.

---

## 21. Lineage Coverage

| Metric | Value |
|--------|-------|
| Total lineage records | 6,205 |
| Unique daily IDs covered | 2,920 (100%) |
| Sources represented | 4/4 |

Every daily row has lineage from at least one contributing domain. Multi-source rows have lineage from each domain that contributed data.

---

## 22. Input-Checksum Verification

All four processed input files were verified unchanged after processing:

| File | Checksum Verified |
|------|-------------------|
| processed_patient_encounters.csv | Yes |
| processed_patient_queue.csv | Yes |
| processed_bed_capacity.csv | Yes |
| processed_service_schedule.csv | Yes |

---

## 23. Processed-Schema Result

The output schema was validated against `processed_patient_flow_daily` in the schema registry.

- All required fields present.
- All numeric fields are numeric.
- All boolean fields are boolean.
- No unapproved fields were added.

**Result: Passed**

---

## 24. Step 2D-3C Test Result

All 50 tests in `tests/test_patient_flow_daily_builder.py` passed.

Test coverage includes:
- Safe imports and no automatic execution
- Manifest gate pass and block
- Checksum mismatch blocking
- Daily grain uniqueness
- Deterministic IDs
- Encounter aggregation (counts and wait-minute totals)
- Queue double-count protection and ambiguity handling
- Bed snapshot handling and no-capping logic
- Service session aggregation
- Null-versus-zero rules
- Schema compliance
- Lineage coverage
- Input immutability
- Absence of forbidden KPI, status, trend, anomaly, risk, forecast, scenario, financial and recommendation fields

---

## 25. Prior Accepted Regression Status

Steps 2D-1, 2D-2, 2D-3A and 2D-3B were previously accepted and verified.
No shared prior implementation files were modified during Step 2D-3C.
Full cumulative regression testing is deferred to Step 2D-3E.

---

## 26. Unresolved Rules

- Queue aggregation for multi-stage groups without an explicit summary flag: **Pending Review**
- Duplicate bed-snapshot selection logic: **Pending Review**

These rules do not affect the current dataset because no such cases exist in the current inputs.

---

## 27. Known Limitations

- Queue aggregation relies on explicit `summary_source_flag`; ambiguous multi-stage groups are set to null.
- Duplicate bed snapshots are not resolved; fields are set to null.
- No weighted average for queue wait times is calculated.
- `official_wait_stage_eligible_flag` is uniformly `False` in the current encounter data, so `total_arrival_to_consultation_minutes` remains null for all daily rows.

---

## 28. Readiness for Step 2D-3D

**Step 2D-3C is complete and accepted.**

Step 2D-3D will consolidate patient-flow processing controls, verify cross-step lineage and perform integration checks across:
- processed_patient_encounters
- processed_patient_queue
- processed_bed_capacity
- processed_service_schedule
- processed_patient_flow_daily

Step 2D-3D will not calculate official KPI percentages or KPI status.
