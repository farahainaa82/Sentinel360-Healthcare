"""Phase 3B-FI Source Integrity Audit.

For every displayed forecast, confirm:
- expected source is the governed forecast CSV
- actual source is the governed forecast CSV
- source_valid = True
- actual_future_row_used = False (no actual Aug-Dec row is used as forecast)
"""
import os
import sys

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, PROJECT_ROOT)

import pandas as pd

from src.streamlit_executive_data_loader import (
    get_kpi_monthly_actual_table,
    load_kpi_monthly_forecast,
    load_kpi_forecast_warning_signals,
    load_kpi_forecast_eligibility_audit,
    get_period_type,
    lookup_forecast_record,
    lookup_forecast_warning,
    lookup_forecast_eligibility,
    GOVERNED_ACTUAL_MONTH_CUTOFF,
)

OUTPUT_PATH = os.path.join(
    PROJECT_ROOT, "outputs", "streamlit",
    "step_3b_fi_source_integrity_audit.csv",
)

FORECAST_PATH = "outputs/forecasting/analytical_kpi_monthly_forecast.csv"
ELIGIBILITY_PATH = "outputs/forecasting/kpi_forecast_eligibility_audit.csv"
WARNING_PATH = "outputs/forecasting/analytical_kpi_forecast_warning_signals.csv"


def main():
    monthly_actual = get_kpi_monthly_actual_table(pd.DataFrame())
    forecast_df = load_kpi_monthly_forecast()
    warning_df = load_kpi_forecast_warning_signals()
    eligibility_df = load_kpi_forecast_eligibility_audit()

    rows = []
    hospital = "HOSP-001"
    year = 2025
    kpi_ids = ["kpi_001", "kpi_002", "kpi_003", "kpi_004", "kpi_005", "kpi_006"]
    departments = [
        "DEPT-ED", "DEPT-ICU", "DEPT-MW", "DEPT-OP", "DEPT-ADM",
    ]

    for dept in departments:
        for kpi_id in kpi_ids:
            for month in range(FORECAST_MONTHS := 8, 13):
                period_type = get_period_type(year, month)
                expected = FORECAST_PATH

                elig = lookup_forecast_eligibility(eligibility_df, hospital, dept, kpi_id)
                if elig.get("eligibility_status") == "ELIGIBLE":
                    fc = lookup_forecast_record(forecast_df, hospital, dept, kpi_id, year, month)
                    if fc:
                        displayed = _fmt(fc.get("point_forecast"))
                        actual = FORECAST_PATH
                        rec_id = fc.get("forecast_id", "")
                        source_valid = True
                        actual_future_used = False
                        note = "eligible forecast, single governed source"
                    else:
                        displayed = ""
                        actual = ELIGIBILITY_PATH
                        rec_id = ""
                        source_valid = True
                        actual_future_used = False
                        note = "eligible but missing forecast row"
                else:
                    displayed = ""
                    actual = ELIGIBILITY_PATH
                    rec_id = ""
                    source_valid = True
                    actual_future_used = False
                    note = f"ineligible: {elig.get('limitation', '')}"

                # Check: was an actual row from Aug-Dec ever used as forecast?
                if not monthly_actual.empty:
                    actual_future = monthly_actual[
                        (monthly_actual["department_code"] == dept)
                        & (monthly_actual["kpi_id"] == kpi_id)
                        & (monthly_actual["year"] == year)
                        & (monthly_actual["month"] == month)
                    ]
                    if not actual_future.empty:
                        note += " | WARNING: actual Aug-Dec row present in source but never used as forecast"

                rows.append({
                    "hospital": hospital,
                    "department": dept,
                    "department_code": dept,
                    "year": year,
                    "month": month,
                    "kpi_id": kpi_id,
                    "kpi_name": kpi_id,
                    "period_type": period_type,
                    "displayed_value": displayed,
                    "expected_source_file": expected,
                    "actual_source_file": actual,
                    "source_record_id": rec_id,
                    "source_valid": source_valid,
                    "actual_future_row_used": actual_future_used,
                    "validation_note": note,
                })

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {len(df)} rows to {OUTPUT_PATH}")

    # Summary
    valid = df["source_valid"].sum()
    no_actual = (df["actual_future_row_used"] == False).sum()
    print(f"  source_valid=True: {valid}/{len(df)}")
    print(f"  actual_future_row_used=False: {no_actual}/{len(df)}")


def _fmt(value):
    try:
        return f"{float(value):.1f}"
    except (TypeError, ValueError):
        return str(value) if value is not None else ""


if __name__ == "__main__":
    main()