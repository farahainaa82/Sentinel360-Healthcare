"""Test 2C-2C-05: Confidence never High.

Verifies that no scenario result has final_scenario_confidence = High,
because provisional KPIs and governance rules should prevent it.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd


def test_confidence_never_high():
    df = pd.read_csv("data/analytical/analytical_scenario_runs.csv", keep_default_na=False)
    high_count = (df["final_scenario_confidence"] == "High").sum()
    assert high_count == 0, f"Found {high_count} results with High confidence"
    print("PASS: No scenario results have High confidence")


if __name__ == "__main__":
    test_confidence_never_high()
