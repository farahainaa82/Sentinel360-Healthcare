# Sentinel360 — Step 2B-1A Final Report

## KPI Threshold Calibration and Validation

**Report Date:** 2026-07-27  
**Step:** 2B-1A  
**Version:** v1.0-candidate  
**Status:** Complete — Ready for Stakeholder Review (2B-1B)

---

## 1. Objective

Generate, validate, and shortlist provisional threshold candidates for six Sentinel360 KPIs using historical data. Ensure computational volume controls, immutability of prior-phase files, and deterministic boundary logic. Produce outputs for stakeholder review without claiming approval.

---

## 2. Scope

| KPI ID | Name | Directionality | Observations | Sufficiency |
|--------|------|----------------|--------------|-------------|
| kpi_001 | Staffing Level | Higher is better | 2,920 | Strong |
| kpi_002 | Staff Absenteeism Rate | Lower is better | 2,920 | Strong |
| kpi_003 | Bed Occupancy Rate | Context-sensitive | 1,095 | Strong |
| kpi_004 | Average Patient Waiting Time | Lower is better | 1,095 | Strong |
| kpi_005 | Patient Complaint Rate | Lower is better | 984 | Moderate |
| kpi_006 | Patient Satisfaction Score | Higher is better | 2,383 | Strong |

---

## 3. Methods Applied

1. **Percentile-Based Calibration** — p10/p25/p40/p50/p60/p75/p90/p95
2. **Mean-SD Calibration** — mean ± (0.5 / 1.0 / 1.5) SD
3. **Median-MAD Calibration** — median ± (1.0 / 1.5 / 2.0) MAD
4. **Hybrid Calibration** — blend of percentile and mean-SD balanced

---

## 4. Candidate Generation Results

| KPI | Generated | Valid | Invalid | Duplicate | Shortlisted |
|-----|-----------|-------|---------|-----------|-------------|
| kpi_001 | 10 | 10 | 0 | 0 | 3 |
| kpi_002 | 10 | 10 | 0 | 0 | 3 |
| kpi_003 | 10 | 10 | 0 | 0 | 2 |
| kpi_004 | 10 | 10 | 0 | 0 | 3 |
| kpi_005 | 7 | 7 | 0 | 0 | 3 |
| kpi_006 | 10 | 9 | 0 | 1 | 3 |
| **Total** | **57** | **56** | **0** | **1** | **17** |

---

## 5. Computational Volume Control

- **Projected classification rows:** 33,096
- **Limit:** 100,000
- **Status:** PASS
- **Method:** Only shortlisted candidates were classified at record level. No intermediate candidate classifications were exported.

---

## 6. Classification Burden Overview

| KPI | Conservative | Balanced | Sensitive |
|-----|--------------|----------|-----------|
| kpi_001 | Low (8.8%) | Moderate (18.8%) | Very High (46.4%) |
| kpi_002 | Low (9.9%) | Moderate (20.2%) | Very High (47.1%) |
| kpi_003 | Very High (45.9%) | Very High (46.8%) | — |
| kpi_004 | Moderate (10.0%) | Moderate (19.9%) | Very High (50.0%) |
| kpi_005 | Moderate (10.1%) | Moderate (21.1%) | Moderate (24.7%) |
| kpi_006 | Low (9.7%) | Moderate (16.2%) | Moderate (16.2%) |

*Amber+Red % = percentage of records classified as non-green.*

---

## 7. Stability and Trend Alignment

- **Stability tests:** 221 (hospital and monthly segments)
- **Trend alignments:** 38 records
- **Overall stability:** No unstable segments flagged as blocking.

---

## 8. Validation Results

| Check | Status |
|-------|--------|
| Schema validation | PASS |
| Key validation | PASS |
| Formula verification (50-sample spot-check) | PASS |
| Immutability verification | PASS |
| Volume audit | PASS |

---

## 9. Governance Compliance

| Requirement | Status |
|-------------|--------|
| Maximum 3 shortlisted candidates per KPI | COMPLIANT |
| Only shortlisted candidates classified | COMPLIANT |
| No intermediate classifications exported | COMPLIANT |
| Vectorised processing | COMPLIANT |
| Hard stop at 100,000 rows | COMPLIANT |
| No config overwrite | COMPLIANT |
| Phase 1 / 2A / 2B-1 files immutable | COMPLIANT |
| All candidates provisional (v1.0-candidate) | COMPLIANT |
| No stakeholder approval claimed | COMPLIANT |
| Stopped before 2B-1B | COMPLIANT |

---

## 10. Issues and Warnings

| ID | Severity | Category | Description | Blocking |
|----|----------|----------|-------------|----------|
| ISS-... | Warning | Shortlisting | Duplicate boundary skipped for kpi_006 sensitive candidate | No |
| ISS-... | Warning | Shortlisting | No Sensitive candidate for kpi_003 (only 2 shortlisted) | No |
| ISS-... | Info | Shortlisting | Info-level notes on candidate selection | No |
| ISS-... | Info | Shortlisting | Info-level notes on candidate selection | No |

*Total: 0 blocking issues, 4 warnings/info records.*

---

## 11. Recommendations

| KPI | Preferred Candidate | Strength | Rationale |
|-----|---------------------|----------|-----------|
| kpi_001 | Hybrid Balanced | Strong | Strong data, moderate burden |
| kpi_002 | Hybrid Balanced | Strong | Strong data, moderate burden |
| kpi_003 | Hybrid Balanced | Strong | Strong data; context-sensitive requires review |
| kpi_004 | Hybrid Balanced | Strong | Strong data, moderate burden |
| kpi_005 | Hybrid Balanced | Moderate | Moderate data sufficiency |
| kpi_006 | Hybrid Balanced | Strong | Strong data, moderate burden |

---

## 12. Files Produced

### Source Code
- `src/threshold_calibration_models.py` — Data models and enums
- `src/kpi_threshold_calibration_engine.py` — Calibration engine
- `src/run_kpi_threshold_calibration.py` — Safe runner
- `src/validate_threshold_calibration.py` — Validation suite
- `tests/test_kpi_threshold_calibration.py` — Focused tests

### Outputs (`outputs/threshold_calibration/`)
- `threshold_distribution_profiles.csv`
- `threshold_candidates_all.csv`
- `threshold_candidates_shortlisted.csv`
- `threshold_classification_results.csv`
- `threshold_burden_results.csv`
- `threshold_stability_results.csv`
- `threshold_trend_alignment.csv`
- `threshold_recommendations.csv`
- `threshold_evidence_records.csv`
- `threshold_issue_records.csv`
- `threshold_audit_records.csv`
- `threshold_calibration_manifest.json`
- `threshold_validation_report.json`

### Documentation
- `docs/step_2b1a_stakeholder_review_pack.md`
- `docs/step_2b1a_final_report.md` (this file)

---

## 13. Sign-off

This report confirms that Step 2B-1A technical calibration is complete. **No thresholds are approved.** The outputs are ready for stakeholder review in Step 2B-1B.

**Next Step:** Step 2B-1B — Stakeholder Review and Approval.
