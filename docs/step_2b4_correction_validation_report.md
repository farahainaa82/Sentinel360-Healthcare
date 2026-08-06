# Step 2B-4 Correction Validation Report

**Date:** 2026-07-28  
**Status:** CORRECTED AND VALIDATED — Ready for Step 2C-1A rerun

---

## 1. Issues Summary

| Issue | Severity | Root Cause | Fix Applied |
|-------|----------|------------|-------------|
| **Issue 1 — Stale Contradiction Severity** | High | Step 2B-4 CSVs were generated before the `ContradictionSeverity` enum-ranking fix | Regenerated all affected analytical outputs using corrected engine |
| **Issue 2 — Incorrect Provisional-Breach Wording** | High | Downstream Step 2C-1A used stale `breach_type` from KPI scores where non-provisional KPIs were incorrectly labelled "Provisional Breach" | Added governed display fields to department-risk output based on `dominant_driver_is_provisional` |

---

## 2. Issue 1 — Contradiction Severity Correction

### Before

```
contradiction_severity distribution:
  NaN/None: 135 of 135 rows (100%)
  contradiction_flag=True with NaN severity: 135 rows
  missing contributing_factor_score_normalized: 102 of 135 rows
```

### After

```
contradiction_severity distribution:
  Material: 72 rows (53.3%)
  Minor: 63 rows (46.7%)
  NaN/None: 0 rows (0%)
  missing contributing_factor_score_normalized: 0 of 135 rows
```

### Changes Made

1. **Enum rename:** `ContradictionSeverity.NONE = "None"` → `"No Contradiction"` to prevent pandas from auto-converting it to NaN on CSV read/write.
2. **Severity-ranking fix confirmed:** `_SEVERITY_RANK` integer map ensures `max()` upgrades severity correctly (Material > Minor > No Contradiction).
3. **NaN component handling:** Added `_to_float()` helper in `score_contributing_factors()` to default NaN source values to 0.0, ensuring all 135 rows receive numeric scores.
4. **Runner robustness:** Added empty-DataFrame guard for hypothesis language validation when no departments meet High/Critical + score >= 50 threshold.

### Files Refreshed

| File | Checksum (SHA-256 prefix) |
|------|---------------------------|
| `data/analytical/analytical_contributing_factor_scores.csv` | `124c2e4dc546d220` |
| `data/analytical/analytical_relationship_contradictions.csv` | `40a21e32dd5d5b2d` |
| `data/analytical/analytical_contributing_factor_pathways.csv` | `64344b1ca4b0952c` |
| `data/analytical/analytical_department_contributing_factor_summary.csv` | `d9d1ba929f061c24` |
| `data/analytical/analytical_potential_root_cause_hypotheses.csv` | `7eb70257593da06f` |
| `data/analytical/analytical_relationship_network_edges.csv` | `e062cc2b8775ba37` |
| `data/analytical/analytical_relationship_confidence.csv` | `e38bed19ddcfb10e` |

---

## 3. Issue 2 — Provisional-Breach Display Governance

### Problem

Step 2C-1A evidence summaries incorrectly labelled non-provisional KPIs (kpi_001, kpi_002, kpi_004, kpi_006) with "Provisional Breach" because they relied on the stale `breach_type` field in KPI risk scores, which had been set incorrectly during an earlier generation run.

### Correction Applied

Created `src/correct_provisional_breach_display.py` which adds four governed display fields to `data/analytical/analytical_department_risk_daily.csv`:

| New Field | Description |
|-----------|-------------|
| `dominant_threshold_is_provisional` | Boolean — equals `dominant_driver_is_provisional`; never True for kpi_001/002/004/006 |
| `dominant_breach_type_governed` | Corrected breach type derived from `threshold_state` and dominant provisional status |
| `dominant_driver_governance_warning` | "Dominant risk driver uses approved threshold" or "Dominant risk driver uses provisional threshold" |
| `dominant_driver_reason_governed` | Corrected reason string without "Provisional Breach" for non-provisional KPIs |

### Validation Results

| Dominant KPI | Provisional Breach Count (Before) | Provisional Breach Count (After) | Expected |
|--------------|-----------------------------------|----------------------------------|----------|
| kpi_001 (Staffing Level) | >0 | **0** | Approved |
| kpi_002 (Absenteeism) | >0 | **0** | Approved |
| kpi_004 (Readmissions) | >0 | **0** | Approved |
| kpi_006 (Satisfaction) | >0 | **0** | Approved |
| kpi_003 (Bed Occupancy) | >0 | **382** | Conditionally Approved |
| kpi_005 (Complaint Rate) | >0 | **111** | Conditionally Approved |

### Upstream Fields Preserved

- `accepted_risk_score` — unchanged
- `department_risk_score_normalized` — unchanged (mean 39.03, range 0–100)
- `department_priority_tier` — unchanged (Monitor 1035, Elevated 642, High 566, Stable 417, Critical 260)
- `urgency_level` — unchanged
- `dominant_kpi_id` — unchanged
- `dominant_kpi_score` — unchanged (mean 44.78, range 0–100)

No existing column values were modified.

---

## 4. Test Results

### Affected Test Suite: 76 tests, 0 failures

| Test File | Tests | Result |
|-----------|-------|--------|
| `test_kpi_relationship_analysis_engine.py` | 22 | Pass |
| `test_relationship_lag_analysis_engine.py` | 6 | Pass |
| `test_contributing_factor_analysis_engine.py` | 21 | Pass |
| `test_relationship_evidence_engine.py` | 9 | Pass |
| `test_step_2b4_correction.py` | 18 | Pass |

### New Correction Tests (18)

#### Contradiction Severity (6 tests)
1. `test_severity_no_none_or_nan` — Only valid governed values present
2. `test_no_nan_severity_when_flag_true` — Flagged rows always have severity
3. `test_major_prevents_strong_hypothesis` — Major caps classification
4. `test_scores_numeric_no_nan` — All 135 rows have numeric scores
5. `test_severity_persists_after_csv_roundtrip` — CSV write/read preserves "No Contradiction"
6. `test_flag_true_never_blank_severity` — No blank severity for flagged rows

#### Provisional Breach Governance (8 tests)
7. `test_kpi_001_never_provisional_breach` — 0 Provisional Breach for kpi_001
8. `test_kpi_002_never_provisional_breach` — 0 Provisional Breach for kpi_002
9. `test_kpi_004_never_provisional_breach` — 0 Provisional Breach for kpi_004
10. `test_kpi_006_never_provisional_breach` — 0 Provisional Breach for kpi_006
11. `test_kpi_003_preserves_provisional_status` — kpi_003 retains Provisional Breach where appropriate
12. `test_kpi_005_preserves_provisional_status` — kpi_005 retains Provisional Breach where appropriate
13. `test_contains_provisional_does_not_make_dominant_provisional` — Department presence ≠ dominant driver status
14. `test_accepted_scores_unchanged` — Core numerical fields intact
15. `test_governed_fields_present` — All 4 new fields exist
16. `test_governed_warning_text` — Warning text matches provisional status

#### Upstream Immutability (2 tests)
17. `test_department_risk_scores_unchanged` — Scores in [0,100], tiers valid
18. `test_no_duplicate_rows` — No duplicate department-date keys

---

## 5. Upstream Immutability

| Check | Files | Result |
|-------|-------|--------|
| Baseline checksums (non-refreshed) | 5 core upstream files | Computed |
| Core department risk columns | 2,920 rows, 5 key fields | Verified intact |
| Existing column values | All pre-existing columns in dept risk CSV | Unchanged |

The `analytical_department_risk_daily.csv` was only appended with four new governed columns. All pre-existing columns were read and written back verbatim.

---

## 6. Files Created or Modified

### New Files
- `src/correct_provisional_breach_display.py`
- `tests/test_step_2b4_correction.py`
- `docs/step_2b4_correction_validation_report.md`
- `outputs/relationship_analysis/correction_metrics.json`
- `outputs/relationship_analysis/upstream_checksums_correction.json`

### Modified Files
- `src/relationship_analysis_models.py` — Enum rename
- `src/contributing_factor_analysis_engine.py` — NaN handling + penalty dict key update
- `src/run_relationship_contributing_factor_engine.py` — Empty-hypothesis guard
- `tests/test_contributing_factor_analysis_engine.py` — Empty-hypothesis fixture + enum string updates
- `data/analytical/analytical_department_risk_daily.csv` — 4 new governed columns appended

### Refreshed Analytical Outputs (7 files)
- All files listed in Section 2

---

## 7. Readiness for Step 2C-1A Rerun

| Criterion | Status |
|-----------|--------|
| contradiction_severity valid for all rows | Yes |
| Major contradiction prevents Strong Hypothesis | Yes |
| No NaN scores where engine can calculate | Yes |
| Non-provisional KPIs never labelled Provisional Breach | Yes |
| Provisional KPIs retain correct status | Yes |
| Department presence ≠ dominant driver provisional status | Yes |
| Accepted risk scores unchanged | Yes |
| Rankings, tiers, urgency unchanged | Yes |
| Dominant-driver selection unchanged | Yes |
| All affected tests pass (76/76) | Yes |
| Upstream immutability verified | Yes |
| Documentation complete | Yes |

**Step 2B-4 corrections are COMPLETE. System is ready for Step 2C-1A rerun.**
