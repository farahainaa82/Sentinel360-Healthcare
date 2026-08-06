# Step 2B-2 Validation Report

**Run ID:** THBREACHWATCH-20260727213903  
**Step:** 2B-2 — Threshold Breach & Watch Condition Engine  
**Processed At:** 2026-07-27T21:39:03.477840  
**Report Generated:** 2026-07-27  
**Status:** COMPLETE

---

## 1. Executive Summary

The Step 2B-2 threshold breach and watch-condition engine was executed successfully against all 17,520 source records. All 22 tests passed. Zero issues were logged. Upstream immutability was verified. The step is closed and readiness for Step 2B-3 is **Ready with Conditions**.

---

## 2. Test Results

| Metric | Value |
|--------|-------|
| Test file | `tests/test_threshold_breach_watch_engine.py` |
| Total tests | 22 |
| Passed | 22 |
| Failed | 0 |
| Skipped | 0 |
| Runtime | 1,735 seconds (~28 min 55 s) |
| Execution mode | `pytest -vv -x` |

### Test Coverage

- **Safe Defaults:** No auto-execution
- **Engine Prerequisites:** All 6 KPIs have active thresholds; prerequisite checks pass
- **Classification Correctness:** Context-sensitive five-band, higher-is-better G-A-R, lower-is-better G-A-R, unavailable handling
- **Breach Detection:** Governed output = source records, actual breaches subset, provisional/non-provisional logic, unavailable breach type
- **Watch Conditions:** Governed output = source records, actual watches subset, no `None` severity, prerequisites pass
- **Record Reconciliation:** Breach/watch counts, source record match, classifiable + unavailable = total
- **Immutability:** Upstream files unchanged after run

---

## 3. Performance Observation

| Observation | Detail |
|-------------|--------|
| Symptom | Test suite runtime ~29 minutes |
| Severity | Non-blocking |
| Root cause | Each test independently reloads all inputs and re-runs full breach and watch engine logic over 17,520 records |
| Impact on correctness | None |
| Impact on closure | None |

---

## 4. Future Optimization Opportunities

1. **Shared pytest fixtures:** Use module-scoped or session-scoped fixtures for input datasets.
2. **Cached inputs:** Load source data once per test session and share across tests.
3. **Reuse classified outputs:** Cache `classify_all_records()` result and reuse in downstream assertions.
4. **Optimize checksum scans:** Avoid repeated full-directory SHA-256 scans in immutability tests.
5. **Test separation:** Mark slow integration tests with `@pytest.mark.slow` and run fast unit tests separately.

---

## 5. Record Reconciliation

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| Total source records | 17,520 | 17,520 | PASS |
| Classifiable/calculated records | 11,397 | 11,397 | PASS |
| Unavailable/unclassifiable records | 6,123 | 6,123 | PASS |
| Governed breach output records | 17,520 | 17,520 | PASS |
| Actual breach events | 2,464 | 2,464 | PASS |
| Governed watch output records | 17,520 | 17,520 | PASS |
| Actual watch conditions | 9,120 | 9,120 | PASS |

**Reconciliation formula:** 11,397 + 6,123 = 17,520

---

## 6. Terminology Clarification

To prevent confusion between total governed outputs and actual triggered events:

- **Governed breach output records (17,520):** Every source record receives a breach classification output, even if the classification is `NO_BREACH`.
- **Actual breach events (2,464):** Only records where `breach_flag == True`. This is a subset of the governed output.
- **Governed watch output records (17,520):** Every source record receives a watch evaluation output, even if no watch condition is met.
- **Actual watch conditions (9,120):** Only records where `watch_condition_flag == True`. This is a subset of the governed output.

---

## 7. Evidence and Lineage Validation

| Output | Generated | Status |
|--------|-----------|--------|
| analytical_kpi_watch_evidence.csv | Yes | PASS |
| analytical_kpi_watch_lineage.csv | Yes | PASS |
| analytical_kpi_watch_governance.csv | Yes | PASS |

---

## 8. Upstream Immutability

| Detail | Value |
|--------|-------|
| Method | SHA-256 checksums before and after engine execution |
| Files monitored | 5 |
| Modifications detected | 0 |
| Status | PASS |

---

## 9. Issue Log

No issues logged in this run.

---

## 10. Closure Statement

Step 2B-2 is **COMPLETE**. All required analytical outputs, validation outputs, tests, and documentation have been produced and verified. No defects remain. No analytical outputs require regeneration.

**Step 2B-3 Readiness:** Ready with Conditions
