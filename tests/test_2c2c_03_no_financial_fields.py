"""Test 2C-2C-03: No financial fields in scenario outputs.

Verifies that analytical_scenario_runs.csv contains no cost, price,
revenue, or financial-impact columns.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd


def test_no_financial_fields():
    df = pd.read_csv("data/analytical/analytical_scenario_runs.csv", keep_default_na=False)
    forbidden = ["cost", "price", "revenue", "financial", "budget", "expense"]
    bad_cols = [c for c in df.columns if any(f in c.lower() for f in forbidden)]
    assert not bad_cols, f"Forbidden financial columns found: {bad_cols}"
    print("PASS: No financial columns in scenario runs")


if __name__ == "__main__":
    test_no_financial_fields()
