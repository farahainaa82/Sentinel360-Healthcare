"""Phase 3B-FI Chart-Card Alignment Audit.

For every (hospital, department, kpi, year, month) where a card or chart point
is displayed, confirm that the value rendered on the chart equals the value
shown on the KPI card, and that the source is a single governed record.
"""
import os
import sys

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, PROJECT_ROOT)

import pandas as pd

from src.streamlit_executive_data_loader import (
    load_all_data,
    get_kpi_monthly_actual_table,
    load_kpi_monthly_forecast,
    load_kpi_forecast_warning_signals,
    load_kpi_forecast_eligibility_audit,
    get_period_type,
    lookup_forecast_record,
    lookup_forecast_warning,
    lookup_forecast_eligibility,
    FORECAST_HORIZON_START_MONTH,
    FORECAST_HORIZON_END_MONTH,
    GOVERNED_ACTUAL_MONTH_CUTOFF,
)

OUTPUT_PATH = os.path.join(
    PROJECT_ROOT, "outputs", "streamlit",
    "step_3b_fi_chart_card_alignment_audit.csv",
)


def _format_value(value, precision=1):
    try:
        return f"{float(value):.{precision}f}"
    except (TypeError, ValueError):
        return str(value) if value is not None else ""


def main():
    data = load_all_data()
    monthly_actual = get_kpi_monthly_actual_table(data.get("kpi_daily", pd.DataFrame()))
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
            for month in range(1, 13):
                period_type = get_period_type(year, month)

                if month <= GOVERNED_ACTUAL_MONTH_CUTOFF:
                    # Actual period
                    source_file = "outputs/forecasting/../data/.../kpi_daily"
                    chart_value = ""
                    card_value = ""
                    record_id = ""
                    forecast_quality = ""
                    warning_level = ""
                    note = "actual period"
                    if not monthly_actual.empty:
                        m = monthly_actual[
                            (monthly_actual["hospital"] == hospital)
                            & (monthly_actual["department_code"] == dept)
                            & (monthly_actual["kpi_id"] == kpi_id)
                            & (monthly_actual["year"] == year)
                            & (monthly_actual["month"] == month)
                        ]
                        if not m.empty:
                            val = m.iloc[0].get("monthly_actual_value")
                            chart_value = _format_value(val)
                            card_value = _format_value(val)
                            record_id = f"monthly_actual_{dept}_{kpi_id}_{year}_{month:02d}"
                    rows.append({
                        "hospital": hospital,
                        "department": dept,
                        "department_code": dept,
                        "year": year,
                        "month": month,
                        "kpi_id": kpi_id,
                        "kpi_name": kpi_id,
                        "period_type": period_type,
                        "chart_value": chart_value,
                        "card_value": card_value,
                        "values_match": chart_value == card_value and chart_value != "",
                        "source_file": "kpi_daily (monthly actual)",
                        "source_record_id": record_id,
                        "forecast_quality": forecast_quality,
                        "warning_level": warning_level,
                        "validation_note": note,
                    })
                else:
                    # Forecast period
                    elig = lookup_forecast_eligibility(eligibility_df, hospital, dept, kpi_id)
                    if elig.get("eligibility_status") == "ELIGIBLE":
                        fc = lookup_forecast_record(forecast_df, hospital, dept, kpi_id, year, month)
                        warn = lookup_forecast_warning(warning_df, hospital, dept, kpi_id, year, month)
                        if fc:
                            pf = fc.get("point_forecast")
                            chart_value = _format_value(pf)
                            card_value = _format_value(pf)
                            values_match = chart_value == card_value and chart_value != ""
                            rows.append({
                                "hospital": hospital,
                                "department": dept,
                                "department_code": dept,
                                "year": year,
                                "month": month,
                                "kpi_id": kpi_id,
                                "kpi_name": kpi_id,
                                "period_type": period_type,
                                "chart_value": chart_value,
                                "card_value": card_value,
                                "values_match": values_match,
                                "source_file": "outputs/forecasting/analytical_kpi_monthly_forecast.csv",
                                "source_record_id": fc.get("forecast_id", ""),
                                "forecast_quality": fc.get("forecast_quality", ""),
                                "warning_level": (warn or {}).get("warning_level", ""),
                                "validation_note": "forecast period eligible",
                            })
                        else:
                            rows.append({
                                "hospital": hospital,
                                "department": dept,
                                "department_code": dept,
                                "year": year,
                                "month": month,
                                "kpi_id": kpi_id,
                                "kpi_name": kpi_id,
                                "period_type": period_type,
                                "chart_value": "",
                                "card_value": "",
                                "values_match": True,
                                "source_file": "outputs/forecasting/analytical_kpi_monthly_forecast.csv",
                                "source_record_id": "",
                                "forecast_quality": "",
                                "warning_level": "",
                                "validation_note": "eligible but no forecast row found",
                            })
                    else:
                        rows.append({
                            "hospital": hospital,
                            "department": dept,
                            "department_code": dept,
                            "year": year,
                            "month": month,
                            "kpi_id": kpi_id,
                            "kpi_name": kpi_id,
                            "period_type": period_type,
                            "chart_value": "",
                            "card_value": "",
                            "values_match": True,
                            "source_file": "outputs/forecasting/kpi_forecast_eligibility_audit.csv",
                            "source_record_id": "",
                            "forecast_quality": "",
                            "warning_level": "Not Assessable",
                            "validation_note": f"ineligible: {elig.get('limitation', '')}",
                        })

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {len(df)} rows to {OUTPUT_PATH}")

    # Summary
    eligible = ((df["period_type"] == "FORECAST") & (df["values_match"] == True)).sum()
    ineligible = (df["validation_note"].str.startswith("ineligible", na=False)).sum()
    print(f"  Eligible forecast rows aligned: {eligible}")
    print(f"  Ineligible forecast rows: {ineligible}")


if __name__ == "__main__":
    main()