# Phase 3B — Management Review and Financial Context Repair Report

**Date:** 2026-08-01  
**Scope:** Fix Management Review and Financial Impact sections to respond correctly to selected hospital, department, year, and month.  
**Constraints:** Phase 3B-FI not started. Forecasting outputs not modified. Frozen analytical outputs not modified. Step 3C not started.

---

## 1. Root Cause of Repeated Management Content

### Problem
The **Management Review Required** section showed the same "ROUTINE MONITORING — STABLE OPERATIONS" message across all departments and months, even when selected-month KPI cards showed Warning or Critical statuses.

### Root Causes Identified
1. **Dominant issue evaluation did not filter by selected month.** `build_executive_page_state()` built `all_kpi_statuses` from `get_kpi_monthly_actual_table()` filtered only by `year`, not by `month`. For non-ALL departments it used `rows.iloc[-1]`, which always returned the **last month of the year** (December), not the selected month. This caused the dominant KPI evaluation to use the wrong month's values.
2. **Dominant issue was computed from monthly table, not from cards.** `get_kpi_monthly_actual_table()` was missing some KPI/department combinations (e.g., `kpi_003` for `DEPT-ED`), causing the dominant issue to be silently dropped even when the KPI cards showed Critical values.
3. **`operational_status` was derived from `primary_pkg` (risk_alert) instead of from the selected-month KPI cards.** The `primary_pkg` was selected as the latest risk_alert package without filtering by month, so `operational_status` was always based on a stale or unrelated package.
4. **`select_dominant_issue()` only included severity >= 2.0.** When all evaluated KPIs were Green (severity 1.0), it returned `None`, which then caused the page to always show the stable-operations branch.

### Fix
- Replaced the monthly-table-based `all_kpi_statuses` build with a **card-based build**: the dominant issue is now computed directly from `all_kpi_cards`, ensuring it reflects the exact same values and statuses shown on the KPI cards.
- Added `STATUS_TEXT_TO_STATUS` mapping so `select_dominant_issue()` receives proper `Red`/`Amber`/`Green` status codes derived from the cards' `threshold_status` display text.
- Changed `operational_status` derivation to use `_derive_operational_status_from_cards(primary_kpi_cards)`, which evaluates the cards' `severity_score` directly.
- Updated the page rendering logic to show **"ROUTINE MONITORING — STABLE OPERATIONS"** only when no dominant issue exists, and to display the actual dominant KPI name, value, status, and action when one exists.

---

## 2. Root Cause of Repeated Financial Content

### Problem
The **Financial Impact** section showed the same content across departments and months, or showed no content at all, because it was not keyed to the selected context.

### Root Causes Identified
1. **`primary_pkg` selected from risk_alert without year/month filtering.** `build_executive_page_state()` filtered risk_alert by department but not by selected year and month. `select_primary_package()` then sorted by date and returned the **latest package** for that department, regardless of the selected month.
2. **`_build_financial_impact_block()` did not filter financial records by selected context.** It looked up financial records by `decision_package_id` but did not validate that the record matched the selected hospital, department, year, or month. It also used a `str.contains(dept_id)` fallback that could match packages from other months.
3. **No explicit "Not Yet Quantified" fallback.** When no matching financial record existed, the block returned a generic readiness message rather than a context-specific "Not Yet Quantified for Selected Context" message.

### Fix
- Added **year and month filtering** to risk_alert before `select_primary_package()` is called.
- Created a `_filter_by_context()` helper inside `_build_financial_impact_block()` that filters both `integrated_decision_df` and `financial_df` by `department_id` and `reporting_date` year/month.
- Disabled the `str.contains(dept_id)` fallback when `selected_context` is provided, preventing cross-month matches.
- Updated `02_Executive_Overview.py` to render an explicit fallback block:
  - **Status:** Not Yet Quantified for Selected Context
  - **Reason:** No financial estimate is linked to the selected department, month, and management action.
  - **Next step:** Create or link a validated financial estimate for this selected management context.

---

## 3. Canonical Selected Context Object

A `selected_context` dict is now created in `build_executive_page_state()` and returned as part of the page state:

```python
{
    "hospital_id": hospital_id,
    "hospital_name": hospital_id,
    "department_id": kpi_dept,
    "department_name": dept_name,
    "selected_year": year,
    "selected_month": month,
    "selected_period_start": selected_date,
    "selected_period_end": selected_date,
    "period_type": "monthly",
    "relevant_kpi_ids": ["kpi_001", ..., "kpi_006"],
    "scenario_id": None,
}
```

This object is passed to `_build_financial_impact_block()` and used for all context-scoped lookups.

---

## 4. Package Matching Policy

For the selected hospital, department, year, and month:

1. Filter risk_alert by `department_id` (fallback to `affected_department` name match).
2. Filter risk_alert by `reporting_date` year and month.
3. Call `select_primary_package()` on the filtered set.
4. If no package matches, `primary_pkg` is `None` — **no silent fallback** to global/latest/All Departments.
5. Financial lookup uses the exact `decision_package_id` from `primary_pkg`, filtered by the same selected context.

---

## 5. Files Changed

| File | Changes |
|------|---------|
| `pages/02_Executive_Overview.py` | Updated management review display logic; added explicit "Not Yet Quantified for Selected Context" financial fallback; uses `selected_context` from state. |
| `src/streamlit_executive_page_controller.py` | Fixed `build_executive_page_state()` to filter by month, derive `operational_status` from cards, create `selected_context`, filter risk_alert by year/month; added `_derive_operational_status_from_cards()`; updated `_build_financial_impact_block()` with context filtering and disabled cross-month fallback; updated `_build_financial_block()` signature. |
| `tests/test_step_3b_executive_overview.py` | Added `TestManagementAndFinancialContextAlignment` with 14 new tests covering context keys, dominant KPI alignment, value/status equality, action matching, financial lookup scoping, no cross-department/month fallback, explicit missing-context message, and reconciliation integrity. |
| `scripts/run_management_context_audit.py` | New audit script generating `step_3b_management_context_alignment_audit.csv`. |
| `scripts/run_financial_context_audit.py` | New audit script generating `step_3b_financial_context_alignment_audit.csv`. |

---

## 6. Management Alignment Audit Result

**File:** `outputs/streamlit/step_3b_management_context_alignment_audit.csv`

- **Rows:** 63 (9 departments × 7 months)
- **Mismatches:** 0
- **Validation:** All management review dominant KPIs, values, and statuses match the corresponding KPI card values for the selected department and month.

---

## 7. Financial Alignment Audit Result

**File:** `outputs/streamlit/step_3b_financial_context_alignment_audit.csv`

- **Rows:** 63 (9 departments × 7 months)
- **Fallbacks used:** 0
- **Validation:** No cross-department or cross-month financial fallback detected. Financial records are correctly scoped to the selected context.

---

## 8. Tests Passed

```
python -m py_compile pages/02_Executive_Overview.py          # OK
python -m py_compile src/streamlit_executive_page_controller.py  # OK
python -m py_compile src/streamlit_executive_data_loader.py      # OK
python -m py_compile src/streamlit_executive_visualisation_engine.py  # OK
pytest tests/test_step_3b_executive_overview.py -q               # 53 passed
```

New tests added:
1. `test_management_review_key_includes_department_code`
2. `test_management_review_key_includes_selected_year_and_month`
3. `test_dominant_kpi_comes_from_selected_month_card_state`
4. `test_management_value_equals_card_value`
5. `test_management_status_equals_card_status`
6. `test_action_matches_selected_kpi_and_status`
7. `test_financial_lookup_includes_department_code`
8. `test_financial_lookup_includes_selected_year_and_month`
9. `test_no_cross_department_financial_fallback`
10. `test_no_cross_month_financial_fallback`
11. `test_no_automatic_all_departments_fallback`
12. `test_missing_financial_context_shows_not_yet_quantified`
13. `test_reconciliation_logic_remains_intact`
14. `test_existing_phase_3b_tests_still_pass`

---

## 9. Browser Acceptance

Streamlit was restarted on port 8502 and tested via Playwright for:

- Emergency Department — January, March, July
- Intensive Care Unit — January, March, July
- Medical Ward — January, March, July
- Admissions — January, March, July
- All Departments — January, March, July

**Screenshots:** `outputs/streamlit/browser_acceptance_mgmt_fin_*.png`

**Confirmed:**
- KPI cards change by month.
- Management Review changes with selected department and month.
- Dominant issue matches the cards (e.g., ED July shows "Average Patient Waiting Time (Red)").
- Action text is context-specific.
- Financial values appear only when a matching context exists; otherwise the explicit fallback is shown.
- No department reuses another department's RM values.
- No month reuses another month's financial package.
- All Departments is not used as a fallback for specific departments.

---

## 10. Confirmations

- **Forecast integration was not started.** No forecasting module or output was modified.
- **Frozen analytical outputs were not modified.** No pre-computed CSVs, JSONs, or analytical artifacts were altered.
- **Step 3C was not started.** No new major feature development was initiated.

---

## 11. Summary

Management Review and Financial Impact sections are now fully aligned to the selected hospital–department–year–month context. The dominant issue is derived from the same selected-month KPI cards visible on the page, the operational status reflects actual card severities, and financial lookups are scoped to the exact selected context with no silent fallbacks.
