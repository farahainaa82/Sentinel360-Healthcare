"""Test scenario trade-off governance rules.

Verifies confidence, contradiction, and provisional KPI handling.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd


def test_no_high_confidence():
    df = pd.read_csv("data/analytical/analytical_scenario_primary_impacts.csv", keep_default_na=False)
    high_count = (df["final_scenario_confidence"] == "High").sum()
    assert high_count == 0, f"Found {high_count} High confidence results"
    print("PASS: No High confidence results")


def test_causality_not_confirmed():
    runs = pd.read_csv("data/analytical/analytical_scenario_runs.csv", keep_default_na=False)
    bad = runs[runs["causality_status"] != "Not Confirmed"]
    assert len(bad) == 0, f"Found {len(bad)} results with unexpected causality_status"
    print("PASS: All causality_status = Not Confirmed")


def test_unsupported_kpis_not_quantified():
    impacts = pd.read_csv("data/analytical/analytical_scenario_primary_impacts.csv", keep_default_na=False)
    unsupported = {"kpi_003", "kpi_005", "kpi_006"}
    bad = impacts[impacts["primary_kpi_id"].isin(unsupported)]
    assert len(bad) == 0, f"Found {len(bad)} quantitative impacts for unsupported KPIs"
    print("PASS: No unsupported KPIs in quantitative impacts")


def test_no_preferred_scenario_in_manifest():
    import json
    with open("outputs/scenario_modelling/step_2c2d_run_manifest.json") as f:
        manifest = json.load(f)
    assert manifest.get("no_preferred_scenario_selected") is True
    print("PASS: Manifest confirms no preferred scenario selected")


if __name__ == "__main__":
    test_no_high_confidence()
    test_causality_not_confirmed()
    test_unsupported_kpis_not_quantified()
    test_no_preferred_scenario_in_manifest()
