"""Test 2C-2C-07: Comparator balance across supported families.

Verifies that Baseline, Conservative, Expected, and Higher Intensity
comparators each produce the same number of completed results for
staffing, absenteeism, and patient-flow families.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd


def test_comparator_balance():
    df = pd.read_csv("data/analytical/analytical_scenario_runs.csv", keep_default_na=False)
    quant_statuses = {"Completed", "Completed with Warnings"}
    supported_families = {
        "Staffing Coverage Adjustment",
        "Absenteeism Contingency",
        "Patient-Flow and Waiting-Time Adjustment",
    }

    subset = df[
        df["scenario_family"].isin(supported_families) &
        df["scenario_execution_status"].isin(quant_statuses)
    ]

    counts = subset.groupby("comparator_type").size().to_dict()
    print(f"Comparator counts: {counts}")

    # All four comparator types should have equal counts
    expected_count = counts.get("Baseline")
    for comp in ["Conservative", "Expected", "Higher Intensity"]:
        actual = counts.get(comp, 0)
        assert actual == expected_count, f"Comparator {comp} has {actual} results, expected {expected_count}"

    print("PASS: All comparator types are balanced")


if __name__ == "__main__":
    test_comparator_balance()
