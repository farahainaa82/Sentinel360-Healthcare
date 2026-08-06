"""Test 2C-2C-06: Causality status fixed to Not Confirmed.

Verifies that every scenario run has causality_status = Not Confirmed.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd


def test_causality_not_confirmed():
    df = pd.read_csv("data/analytical/analytical_scenario_runs.csv", keep_default_na=False)
    bad = df[df["causality_status"] != "Not Confirmed"]
    assert len(bad) == 0, f"Found {len(bad)} results with unexpected causality_status"
    print("PASS: All scenario results have causality_status = Not Confirmed")


if __name__ == "__main__":
    test_causality_not_confirmed()
