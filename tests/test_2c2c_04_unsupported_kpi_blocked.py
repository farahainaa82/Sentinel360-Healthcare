"""Test 2C-2C-04: Unsupported KPIs blocked from quantitative results.

Verifies that kpi_003, kpi_005, kpi_006 never appear in Completed
or Completed-with-Warnings scenario runs.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd


def test_unsupported_kpis_blocked():
    df = pd.read_csv("data/analytical/analytical_scenario_runs.csv", keep_default_na=False)
    quant_statuses = {"Completed", "Completed with Warnings"}
    unsupported = {"kpi_003", "kpi_005", "kpi_006"}

    bad = df[df["scenario_execution_status"].isin(quant_statuses) & df["primary_kpi_id"].isin(unsupported)]
    assert len(bad) == 0, f"Found {len(bad)} quantitative results for unsupported KPIs"
    print("PASS: No unsupported KPIs have quantitative scenario results")


if __name__ == "__main__":
    test_unsupported_kpis_blocked()
