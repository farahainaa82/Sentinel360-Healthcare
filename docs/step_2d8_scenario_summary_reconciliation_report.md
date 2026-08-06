# Phase 2D-8 Focused Scenario-Summary Reconciliation Report

**Date:** 2026-07-29 21:14:12
**Scope:** Frozen Step 2D-7 outputs with missing scenario summaries for Ready-for-Review packages

## Executive Summary

- **Total Ready-for-Review packages:** 76
- **Affected packages (missing IMB summaries):** 76
- **Recoverable from frozen source:** 76
- **Non-applicable (Monitoring / Non-Quantitative):** 0
- **Unresolved missing sources:** 0
- **Readiness classifications changed:** 76
- **Validation outcomes changed:** 76
- **Final Streamlit-ready count:** 646
- **Streamlit-ready-with-conditions count:** 570
- **Packages requiring focused correction:** 0

## Classification Breakdown

| Classification | Count | Action Taken |
|---|---|---|
| Scenario Summary Recoverable from Frozen Source | 76 | Mapped existing summary from frozen 2C-2/2D-7 source into Step 2D-7 IMB. No recalculation. |

## Test Results

| Test ID | Description | Status | Detail |
|---|---|---|---|
| TEST-01 | Every Ready-for-Review package has scenario summary or governed Not Applicable reason | PASS |  |
| TEST-02 | No scenario value is recalculated | PASS |  |
| TEST-03 | Missing scenario values are not converted to zero | PASS |  |
| TEST-04 | No preferred scenario is selected | PASS |  |
| TEST-05 | Readiness is not upgraded without evidence | PASS |  |
| TEST-06 | Streamlit readiness reflects unresolved missing summaries | PASS |  |
| TEST-07 | Evidence and lineage reconcile to frozen upstream source | PASS |  |
| TEST-08 | Frozen upstream scenario outputs remain unchanged | PASS |  |
| TEST-09 | No Step 2D-9 output is created | PASS |  |

## Governed Principles Applied

1. **No recalculation:** Scenario values from frozen Phase 2C-2 / Step 2D-7 were mapped directly without modification.
2. **No silent upgrades:** Packages with unresolved missing summaries retain a visible condition.
3. **Not Applicable documented:** Monitoring-Only and Non-Quantitative packages display governed reasons.
4. **Upstream frozen:** No Phase 2C-2 files were modified.
5. **Stop before 2D-9:** No Step 2D-9 artifacts were created.

## Affected Packages Detail

### DPKG-PKG-EP-HOSP-001-DEPT-ADM-kpi_001-20260328
- **IMB ID:** IMB-67568966
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 84.55182072829132
- **Expected Availability:** Estimated impact: 15.448179271708682%

### DPKG-PKG-EP-HOSP-001-DEPT-ADM-kpi_001-20260410
- **IMB ID:** IMB-054E896F
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 83.33333333333334
- **Expected Availability:** Estimated impact: 16.666666666666657%

### DPKG-PKG-EP-HOSP-001-DEPT-ADM-kpi_001-20260506
- **IMB ID:** IMB-03B9E920
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 75.0
- **Expected Availability:** Estimated impact: 25.0%

### DPKG-PKG-EP-HOSP-001-DEPT-ADM-kpi_001-20260822
- **IMB ID:** IMB-8D8019FF
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 73.91304347826086
- **Expected Availability:** Estimated impact: 21.739130434782624%

### DPKG-PKG-EP-HOSP-001-DEPT-ADM-kpi_001-20261012
- **IMB ID:** IMB-4BE80CE6
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 80.95238095238095
- **Expected Availability:** Estimated impact: 19.04761904761905%

### DPKG-PKG-EP-HOSP-001-DEPT-ADM-kpi_001-20261021
- **IMB ID:** IMB-7923F3A5
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 75.0
- **Expected Availability:** Estimated impact: 25.0%

### DPKG-PKG-EP-HOSP-001-DEPT-ADM-kpi_001-20261205
- **IMB ID:** IMB-9CAF9BFB
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 79.94987468671678
- **Expected Availability:** Estimated impact: 20.050125313283218%

### DPKG-PKG-EP-HOSP-001-DEPT-ADM-kpi_002-20260524
- **IMB ID:** IMB-DC313032
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 17.857142857142854
- **Expected Availability:** Estimated impact: -19.999999999999996%

### DPKG-PKG-EP-HOSP-001-DEPT-ADM-kpi_002-20260529
- **IMB ID:** IMB-B16AC730
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 15.789473684210526
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-ADM-kpi_002-20260611
- **IMB ID:** IMB-65B007AB
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 23.809523809523807
- **Expected Availability:** Estimated impact: -19.99999999999999%

### DPKG-PKG-EP-HOSP-001-DEPT-ADM-kpi_002-20260814
- **IMB ID:** IMB-7E694674
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 21.052631578947366
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-ADM-kpi_002-20261019
- **IMB ID:** IMB-42E27596
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 18.181818181818183
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-ADM-kpi_002-20261121
- **IMB ID:** IMB-A201D5E5
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 16.666666666666664
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-DIAG-kpi_001-20260108
- **IMB ID:** IMB-B504AD7E
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 78.57142857142857
- **Expected Availability:** Estimated impact: 21.42857142857143%

### DPKG-PKG-EP-HOSP-001-DEPT-DIAG-kpi_001-20260417
- **IMB ID:** IMB-8FBCBB00
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 76.92307692307693
- **Expected Availability:** Estimated impact: 23.076923076923062%

### DPKG-PKG-EP-HOSP-001-DEPT-DIAG-kpi_001-20260423
- **IMB ID:** IMB-AC26D40C
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 78.4090909090909
- **Expected Availability:** Estimated impact: 21.590909090909093%

### DPKG-PKG-EP-HOSP-001-DEPT-DIAG-kpi_001-20260520
- **IMB ID:** IMB-03A5CBFA
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 76.92307692307693
- **Expected Availability:** Estimated impact: 23.076923076923062%

### DPKG-PKG-EP-HOSP-001-DEPT-DIAG-kpi_001-20261023
- **IMB ID:** IMB-5E70F27C
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 78.57142857142857
- **Expected Availability:** Estimated impact: 21.42857142857143%

### DPKG-PKG-EP-HOSP-001-DEPT-DIAG-kpi_002-20260122
- **IMB ID:** IMB-90F8EAE1
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 33.33333333333333
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-DIAG-kpi_002-20260426
- **IMB ID:** IMB-88D1EAA2
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 24.03846153846154
- **Expected Availability:** Estimated impact: -19.999999999999996%

### DPKG-PKG-EP-HOSP-001-DEPT-DIAG-kpi_002-20260921
- **IMB ID:** IMB-2B355530
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 15.384615384615383
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-DIAG-kpi_002-20260930
- **IMB ID:** IMB-186319C6
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 11.794871794871796
- **Expected Availability:** Estimated impact: -20.000000000000004%

### DPKG-PKG-EP-HOSP-001-DEPT-DIAG-kpi_002-20261015
- **IMB ID:** IMB-0350210E
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 21.428571428571427
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-DIAG-kpi_002-20261202
- **IMB ID:** IMB-63E130E8
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 16.666666666666664
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-ED-kpi_001-20260522
- **IMB ID:** IMB-0884C637
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 70.0
- **Expected Availability:** Estimated impact: 30.0%

### DPKG-PKG-EP-HOSP-001-DEPT-ED-kpi_001-20260930
- **IMB ID:** IMB-F6C736A7
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 75.0
- **Expected Availability:** Estimated impact: 25.0%

### DPKG-PKG-EP-HOSP-001-DEPT-ED-kpi_001-20261113
- **IMB ID:** IMB-833250CD
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 73.33333333333333
- **Expected Availability:** Estimated impact: 26.66666666666667%

### DPKG-PKG-EP-HOSP-001-DEPT-ED-kpi_002-20261005
- **IMB ID:** IMB-21AACEF1
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 15.384615384615383
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-ED-kpi_002-20261102
- **IMB ID:** IMB-C2E556F1
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 15.384615384615383
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-ED-kpi_002-20261109
- **IMB ID:** IMB-72F9988E
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 15.384615384615383
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-ED-kpi_002-20261127
- **IMB ID:** IMB-B8D4CC46
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 20.0
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-ED-kpi_004-20260716
- **IMB ID:** IMB-E9D2C951
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 54.31849080383408
- **Expected Availability:** Estimated impact: 12.07792207792209%

### DPKG-PKG-EP-HOSP-001-DEPT-ICU-kpi_001-20260528
- **IMB ID:** IMB-13E70BCB
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 80.0
- **Expected Availability:** Estimated impact: 20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-ICU-kpi_001-20260922
- **IMB ID:** IMB-172B064A
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 72.72727272727273
- **Expected Availability:** Estimated impact: 27.272727272727263%

### DPKG-PKG-EP-HOSP-001-DEPT-ICU-kpi_002-20260126
- **IMB ID:** IMB-C1C3E1E2
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 20.0
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-ICU-kpi_002-20260522
- **IMB ID:** IMB-701A2435
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 19.032051282051285
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-ICU-kpi_002-20260615
- **IMB ID:** IMB-E01D65F0
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 18.465909090909093
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-ICU-kpi_002-20260718
- **IMB ID:** IMB-D59EBD35
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 33.33333333333333
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-ICU-kpi_002-20261207
- **IMB ID:** IMB-6BC23402
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 16.666666666666668
- **Expected Availability:** Estimated impact: -19.999999999999996%

### DPKG-PKG-EP-HOSP-001-DEPT-MED-kpi_001-20260502
- **IMB ID:** IMB-6B454D57
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 82.35294117647058
- **Expected Availability:** Estimated impact: 17.64705882352942%

### DPKG-PKG-EP-HOSP-001-DEPT-MED-kpi_001-20260916
- **IMB ID:** IMB-65659028
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 85.51645658263305
- **Expected Availability:** Estimated impact: 14.483543417366946%

### DPKG-PKG-EP-HOSP-001-DEPT-MED-kpi_002-20260209
- **IMB ID:** IMB-6E77FE59
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 20.0
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-MED-kpi_002-20260505
- **IMB ID:** IMB-C72DFD31
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 20.833333333333336
- **Expected Availability:** Estimated impact: -20.000000000000004%

### DPKG-PKG-EP-HOSP-001-DEPT-MED-kpi_002-20260601
- **IMB ID:** IMB-C249D542
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 20.0
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-MED-kpi_002-20260624
- **IMB ID:** IMB-1E1235B6
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 25.0
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-OPC-kpi_001-20260622
- **IMB ID:** IMB-3B9DA56D
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 80.37153322867609
- **Expected Availability:** Estimated impact: 19.628466771323914%

### DPKG-PKG-EP-HOSP-001-DEPT-OPC-kpi_001-20261223
- **IMB ID:** IMB-CC8A3007
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 70.83333333333333
- **Expected Availability:** Estimated impact: 29.16666666666667%

### DPKG-PKG-EP-HOSP-001-DEPT-OPC-kpi_002-20260118
- **IMB ID:** IMB-B018B677
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 20.0
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-OPC-kpi_002-20260421
- **IMB ID:** IMB-7F9439AE
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 37.5
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-OPC-kpi_002-20260704
- **IMB ID:** IMB-1487EEE7
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 16.666666666666664
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-OPC-kpi_002-20261009
- **IMB ID:** IMB-E9C7C886
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 18.181818181818183
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-OPC-kpi_002-20261030
- **IMB ID:** IMB-85A3369E
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 15.384615384615383
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-OPC-kpi_002-20261226
- **IMB ID:** IMB-64A6A46F
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 17.613636363636363
- **Expected Availability:** Estimated impact: -19.999999999999996%

### DPKG-PKG-EP-HOSP-001-DEPT-OPC-kpi_004-20260509
- **IMB ID:** IMB-DD372116
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 48.41558441558441
- **Expected Availability:** Estimated impact: 12.077922077922084%

### DPKG-PKG-EP-HOSP-001-DEPT-OPC-kpi_004-20260602
- **IMB ID:** IMB-B20F8E28
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 55.48675934738411
- **Expected Availability:** Estimated impact: 12.077922077922084%

### DPKG-PKG-EP-HOSP-001-DEPT-OPC-kpi_004-20260629
- **IMB ID:** IMB-DE6809A8
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 55.3536873800953
- **Expected Availability:** Estimated impact: 12.077922077922084%

### DPKG-PKG-EP-HOSP-001-DEPT-OPC-kpi_004-20260716
- **IMB ID:** IMB-C214655F
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 54.93961578400831
- **Expected Availability:** Estimated impact: 12.07792207792209%

### DPKG-PKG-EP-HOSP-001-DEPT-OPC-kpi_004-20260721
- **IMB ID:** IMB-8131CC19
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 55.4471983614125
- **Expected Availability:** Estimated impact: 12.077922077922086%

### DPKG-PKG-EP-HOSP-001-DEPT-PEX-kpi_001-20260421
- **IMB ID:** IMB-7C1CF550
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 76.92307692307693
- **Expected Availability:** Estimated impact: 23.076923076923062%

### DPKG-PKG-EP-HOSP-001-DEPT-PEX-kpi_001-20260521
- **IMB ID:** IMB-6725EF95
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 75.0
- **Expected Availability:** Estimated impact: 25.0%

### DPKG-PKG-EP-HOSP-001-DEPT-PEX-kpi_001-20260710
- **IMB ID:** IMB-D057EAE6
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 82.84860972360973
- **Expected Availability:** Estimated impact: 17.151390276390273%

### DPKG-PKG-EP-HOSP-001-DEPT-PEX-kpi_001-20260915
- **IMB ID:** IMB-B43D0E86
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 72.72727272727273
- **Expected Availability:** Estimated impact: 27.272727272727263%

### DPKG-PKG-EP-HOSP-001-DEPT-PEX-kpi_002-20260209
- **IMB ID:** IMB-BCEAEA0F
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 16.666666666666664
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-PEX-kpi_002-20260302
- **IMB ID:** IMB-2260F12B
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 20.555555555555557
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-PEX-kpi_002-20260406
- **IMB ID:** IMB-F823ED18
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 20.0
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-PEX-kpi_002-20260519
- **IMB ID:** IMB-B153EAEC
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 16.666666666666664
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-PEX-kpi_002-20260613
- **IMB ID:** IMB-7A5A568B
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 16.102564102564102
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-PEX-kpi_002-20260728
- **IMB ID:** IMB-2EC732D3
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 20.94017094017094
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-SURG-kpi_001-20260305
- **IMB ID:** IMB-1C93F6E5
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 70.0
- **Expected Availability:** Estimated impact: 30.0%

### DPKG-PKG-EP-HOSP-001-DEPT-SURG-kpi_002-20260214
- **IMB ID:** IMB-E83A65A3
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 18.181818181818183
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-SURG-kpi_002-20260304
- **IMB ID:** IMB-8122725A
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 15.384615384615383
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-SURG-kpi_002-20260509
- **IMB ID:** IMB-25673786
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 16.536796536796537
- **Expected Availability:** Estimated impact: -19.999999999999996%

### DPKG-PKG-EP-HOSP-001-DEPT-SURG-kpi_002-20260908
- **IMB ID:** IMB-5F092CDC
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 30.0
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-SURG-kpi_002-20261004
- **IMB ID:** IMB-300F2670
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 15.09920634920635
- **Expected Availability:** Estimated impact: -19.999999999999996%

### DPKG-PKG-EP-HOSP-001-DEPT-SURG-kpi_002-20261018
- **IMB ID:** IMB-817F1E61
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 17.994505494505493
- **Expected Availability:** Estimated impact: -20.0%

### DPKG-PKG-EP-HOSP-001-DEPT-SURG-kpi_002-20261030
- **IMB ID:** IMB-99CB09FD
- **Classification:** Scenario Summary Recoverable from Frozen Source
- **Reason:** Scenario summary exists in frozen 2D-7 source but was not mapped to Step 2D-7 IMB output.
- **Scenario Family:** No-Action or Baseline Comparator
- **Baseline Availability:** Baseline value: 24.722222222222214
- **Expected Availability:** Estimated impact: -20.0%
