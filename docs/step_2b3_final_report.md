# Step 2B-3 Final Report

**Step:** 2B-3 — Department and KPI Risk Prioritisation Engine  
**Run ID:** RISKPRIOR-20260728055229  
**Governance Refinement Run ID:** RISKPRIOR-20260728074812  
**Processed At:** 2026-07-28T05:52:29  
**Governance Refinement At:** 2026-07-28T07:48:12  
**Closure Date:** 2026-07-28  
**Status:** COMPLETE — Governance Refined

---

## 1. Execution Status

Step 2B-3 executed successfully. All engines, outputs, tests, and documentation are complete.

---

## 2. Files Created

### Source Code
- `src/risk_prioritisation_models.py`
- `src/kpi_risk_scoring_engine.py`
- `src/department_risk_prioritisation_engine.py`
- `src/hospital_risk_summary_engine.py`
- `src/run_risk_prioritisation_engine.py`

### Configuration (10 files)
- `config/kpi_risk_weight_config.csv`
- `config/risk_severity_weight_config.csv`
- `config/risk_persistence_weight_config.csv`
- `config/risk_trend_weight_config.csv`
- `config/risk_confidence_config.csv`
- `config/department_risk_aggregation_config.csv`
- `config/risk_priority_tier_config.csv`
- `config/risk_urgency_rule_config.csv`
- `config/risk_governance_adjustment_config.csv`
- `config/risk_ranking_tiebreaker_config.csv`

### Tests
- `tests/test_kpi_risk_scoring_engine.py`
- `tests/test_department_risk_prioritisation_engine.py`
- `tests/test_hospital_risk_summary_engine.py`

### Analytical Outputs (12)
- `data/analytical/analytical_kpi_risk_scores_daily.csv`
- `data/analytical/analytical_kpi_risk_components.csv`
- `data/analytical/analytical_department_risk_daily.csv`
- `data/analytical/analytical_department_risk_ranking.csv`
- `data/analytical/analytical_department_risk_drivers.csv`
- `data/analytical/analytical_department_risk_concurrence.csv`
- `data/analytical/analytical_department_risk_confidence.csv`
- `data/analytical/analytical_department_risk_governance.csv`
- `data/analytical/analytical_department_risk_evidence.csv`
- `data/analytical/analytical_department_risk_lineage.csv`
- `data/analytical/analytical_hospital_risk_daily_summary.csv`
- `data/analytical/analytical_risk_prioritisation_issues.csv`

### Validation Outputs (18)
All files in `outputs/risk_prioritisation/`.

### Documentation (6)
- `docs/step_2b3_risk_prioritisation_architecture.md`
- `docs/step_2b3_risk_scoring_method.md`
- `docs/step_2b3_priority_tier_register.md`
- `docs/step_2b3_validation_report.md`
- `docs/step_2b3_governance_notes.md`
- `docs/step_2b3_to_2b4_handover.md`

---

## 3. Files Modified

No accepted upstream files were modified. Permitted modifications:
- New source code files
- New configuration files
- New test files
- New analytical outputs
- New validation outputs
- New documentation

---

## 4–8. Test Results

| Metric | Value |
|--------|-------|
| Tests collected | 73 |
| Tests passed | 73 |
| Tests failed | 0 |
| Tests skipped | 0 |
| Test runtime | ~11 seconds |

---

## 9–15. Record Counts

| Metric | Value |
|--------|-------|
| Source Step 2B-2 KPI records | 17,520 |
| KPI risk records generated | 17,520 |
| Classifiable KPI risk records | 11,397 |
| Unavailable or Not Assessable records | 6,123 |
| Department-date risk records | 2,920 |
| Hospital-date summary records | 365 |
| Ranked department records | 2,920 |

---

## 16–19. Score Ranges

| Metric | Value |
|--------|-------|
| KPI risk-score minimum | 0.0 |
| KPI risk-score maximum | 100.0 |
| Department risk-score minimum | 0.0 |
| Department risk-score maximum | 100.0 |

---

## 20–25. KPI Priority Tier Counts

| Tier | Count |
|------|-------|
| No Current Risk | 4,783 |
| Monitor | 4,161 |
| Attention Required | 828 |
| High Priority | 961 |
| Critical Priority | 664 |
| Not Assessable | 6,123 |

---

## 26–31. Department Priority Tier Counts

| Tier | Count |
|------|-------|
| Stable | 417 |
| Monitor | 1,035 |
| Elevated | 642 |
| High | 566 |
| Critical | 260 |
| Not Assessable | 0 |

---

## 32–35. Urgency Counts (Department)

| Urgency | Count |
|---------|-------|
| Routine Monitoring | 1,113 |
| Review Soon | 480 |
| Prompt Review | 522 |
| Immediate Review | 805 |

---

## 36–39. Confidence Counts (KPI)

| Confidence | Count |
|------------|-------|
| High | 9,183 |
| Moderate | 2,184 |
| Low | 30 |
| Insufficient Evidence | 6,123 |

---

## 40–42. Provisional Governance (Refined)

| Metric | Count |
|--------|-------|
| Provisional KPI risk count | 2,079 |
| Departments containing provisional KPIs | 2,920 |
| Departments with provisional risk flag = True (Material or Dominant) | 933 |
| Departments with provisional dominant drivers | 572 |
| Provisional contribution — None | 851 |
| Provisional contribution — Minor | 1,136 |
| Provisional contribution — Material | 361 |
| Provisional contribution — Dominant | 572 |

---

## 43. Multi-KPI Concurrence

| Metric | Count |
|--------|-------|
| Concurrence flag = True | 1,584 |

---

## 44–47. Validation Results

| Check | Result |
|-------|--------|
| Dominant-driver validation | PASS |
| Ranking validation | PASS |
| Tie-break validation | PASS |
| Score-reconciliation result | PASS |

---

## 48–50. Linkage Results

| Check | Result |
|-------|--------|
| Evidence-linkage result | PASS (17,520 / 17,520) |
| Lineage-linkage result | PASS (11,397 / 11,397) |
| Source-record reconciliation | PASS (17,520 = 17,520) |

---

## 51–53. Upstream Immutability

| Check | Result |
|-------|--------|
| Upstream checksum before | Recorded for 12 files |
| Upstream checksum after | Verified against before |
| Upstream immutability result | PASS (0 modifications) |

---

## 54–55. Issues and Warnings

| Type | Count | Description |
|------|-------|-------------|
| Warnings | 3 | 572 provisional dominant drivers; 361 provisional material contributions; 30 low-confidence KPIs |
| Blocking issues | 0 | None |
| Technical debt | 1 | Step 2B-2 provisional-flag defect (mitigated by config override) |

---

## 56. Final Step 2B-3 Status

**COMPLETE**

---

## 57. Step 2B-4 Readiness

**Ready with Conditions**

Conditions:
1. Final stakeholder approval for kpi_003 (Bed Occupancy) threshold
2. Final stakeholder approval for kpi_005 (Patient Complaint Rate) threshold
3. Risk weight configurations remain v1.0-draft until approved as policy

---

## 58. Governance Refinement Summary

A focused governance refinement was applied after the initial Step 2B-3 completion:

- **Problem:** All 2,920 department-date records had `provisional_risk_flag = True` because provisional KPIs kpi_003 and kpi_005 exist in every department.
- **Solution:** Introduced configuration-driven materiality rules (`provisional_minor_threshold = 5.0`, `provisional_materiality_threshold = 15.0`) and five refined governance fields (`contains_provisional_kpi`, `provisional_risk_flag`, `dominant_driver_is_provisional`, `provisional_risk_contribution`, `provisional_contribution_materiality`).
- **Result:** `provisional_risk_flag = True` reduced from 2,920 to 933 records (Material or Dominant only).
- **Constraints honoured:** No KPI scores, department scores, rankings, tiers, urgency, dominant-driver selection, evidence results, or upstream Step 2B-2 files were modified.

## 59. Recommended Next Action

Proceed to Step 2B-4 relationship analysis and temporal pattern investigation when stakeholder conditions are resolved or accepted as ongoing governance items.

Do not begin Step 2B-4 without explicit instruction.

---

*End of Step 2B-3 Final Report*
