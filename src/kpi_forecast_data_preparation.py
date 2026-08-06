"""KPI Forecast Data Preparation Module.

Aggregates daily governed KPI observations into monthly historical values
through the historical cut-off (31 July 2026).
"""

import os
import pandas as pd
import numpy as np
from calendar import monthrange
from typing import Optional

CUTOFF_DATE = pd.Timestamp("2026-07-31")
DAILY_PATH = "data/analytical/analytical_six_kpi_daily.csv"
DEPT_MASTER_PATH = "data/demo/department_master.csv"
OUTPUT_DIR = "outputs/forecasting"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "kpi_monthly_actual_history.csv")


def prepare_monthly_history(
    daily_path: str = DAILY_PATH,
    dept_master_path: str = DEPT_MASTER_PATH,
    cutoff: pd.Timestamp = CUTOFF_DATE,
    output_path: str = OUTPUT_FILE,
) -> pd.DataFrame:
    """Prepare monthly historical KPI data from daily observations.

    Parameters
    ----------
    daily_path : str
        Path to the daily KPI CSV.
    dept_master_path : str
        Path to the department master CSV.
    cutoff : pd.Timestamp
        Historical cut-off date (inclusive).
    output_path : str
        Where to write the monthly history CSV.

    Returns
    -------
    pd.DataFrame
        Monthly aggregated actual history.
    """
    df = pd.read_csv(daily_path)
    df["reporting_date"] = pd.to_datetime(df["reporting_date"])
    df = df[df["reporting_date"] <= cutoff]

    dept_master = pd.read_csv(dept_master_path)
    dept_map = dept_master.set_index("department_id")["department_name"].to_dict()
    df["department_name"] = df["department_id"].map(dept_map)

    # Valid numeric observations: calculation_status == Calculated and kpi_value not null
    df["is_valid"] = (df["calculation_status"] == "Calculated") & (df["kpi_value"].notna())

    df["year"] = df["reporting_date"].dt.year
    df["month"] = df["reporting_date"].dt.month
    df["days_in_month"] = df.apply(
        lambda r: monthrange(int(r["year"]), int(r["month"]))[1], axis=1
    )

    group_cols = [
        "hospital_id", "department_id", "department_name",
        "kpi_id", "kpi_name", "unit", "year", "month",
    ]

    # Valid monthly aggregations
    valid_df = df[df["is_valid"]]
    valid_monthly = (
        valid_df.groupby(group_cols)
        .agg(
            monthly_actual_value=("kpi_value", "mean"),
            valid_observation_count=("kpi_value", "count"),
        )
        .reset_index()
    )

    # All rows per month to compute total days in month
    all_days = (
        df.groupby(group_cols)
        .agg(days_in_month=("days_in_month", "first"))
        .reset_index()
    )

    monthly = valid_monthly.merge(all_days, on=group_cols, how="left")
    monthly["missing_observation_count"] = (
        monthly["days_in_month"] - monthly["valid_observation_count"]
    )
    monthly["aggregation_method"] = "arithmetic_mean"
    monthly["calculation_status"] = np.where(
        monthly["valid_observation_count"] > 0, "Aggregated", "Insufficient Data"
    )
    monthly["source_file"] = "data/analytical/analytical_six_kpi_daily.csv"

    # Period boundaries
    monthly["period_start"] = pd.to_datetime(
        monthly[["year", "month"]].assign(day=1)
    )
    monthly["period_end"] = monthly.apply(
        lambda r: pd.Timestamp(
            year=int(r["year"]),
            month=int(r["month"]),
            day=monthrange(int(r["year"]), int(r["month"]))[1],
        ),
        axis=1,
    )

    # Rename for output schema
    monthly = monthly.rename(
        columns={
            "hospital_id": "hospital",
            "department_id": "department_code",
            "department_name": "department",
        }
    )

    output_cols = [
        "hospital", "department", "department_code", "kpi_id", "kpi_name",
        "year", "month", "period_start", "period_end", "monthly_actual_value",
        "unit", "valid_observation_count", "missing_observation_count",
        "aggregation_method", "calculation_status", "source_file",
    ]
    monthly = monthly[output_cols]

    # Exclude months with no valid observations
    monthly = monthly[monthly["calculation_status"] != "Insufficient Data"].reset_index(drop=True)

    os.makedirs(os.path.dirname(output_path) or OUTPUT_DIR, exist_ok=True)
    monthly.to_csv(output_path, index=False)
    return monthly


if __name__ == "__main__":
    prepare_monthly_history()
