"""Test Step 2C-2D output integrity.

Verifies that all required outputs exist and contain expected data.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd


def test_outputs_exist():
    required_files = [
        "analytical_scenario_primary_impacts.csv",
        "analytical_scenario_supporting_kpi_impacts.csv",
        "analytical_scenario_effect_classification.csv",
        "analytical_scenario_tradeoffs.csv",
        "analytical_scenario_risk_displacement.csv",
        "analytical_scenario_comparator_analysis.csv",
        "analytical_scenario_diminishing_returns.csv",
        "analytical_scenario_dominance.csv",
        "analytical_scenario_sensitivity.csv",
        "analytical_scenario_tradeoff_profiles.csv",
        "analytical_scenario_management_interpretation.csv",
        "analytical_scenario_tradeoff_evidence.csv",
        "analytical_scenario_tradeoff_lineage.csv",
        "analytical_scenario_non_comparable_register.csv",
    ]
    missing = []
    for fname in required_files:
        path = os.path.join("data", "analytical", fname)
        if not os.path.exists(path):
            missing.append(fname)
    assert not missing, f"Missing outputs: {missing}"
    print("PASS: All required outputs exist")


def test_no_financial_fields():
    df = pd.read_csv("data/analytical/analytical_scenario_primary_impacts.csv", keep_default_na=False)
    forbidden = [c for c in df.columns if any(f in c.lower() for f in ["cost", "price", "revenue", "financial", "budget"])]
    assert not forbidden, f"Financial columns found: {forbidden}"
    print("PASS: No financial columns in primary impacts")


def test_non_comparable_register():
    df = pd.read_csv("data/analytical/analytical_scenario_non_comparable_register.csv", keep_default_na=False)
    assert len(df) > 0, "Non-comparable register is empty"
    blocked = df[df["scenario_execution_status"].str.contains("Blocked", na=False)]
    monitoring = df[df["scenario_execution_status"] == "Monitoring Only"]
    assert len(blocked) + len(monitoring) == len(df), "Non-comparable register contains unexpected statuses"
    print("PASS: Non-comparable register contains blocked and monitoring-only records")


def test_manifest_integrity():
    import json
    with open("outputs/scenario_modelling/step_2c2d_run_manifest.json") as f:
        manifest = json.load(f)
    assert "quantitatively_comparable_runs" in manifest
    assert manifest["quantitatively_comparable_runs"] > 0
    assert manifest.get("no_preferred_scenario_selected") is True
    assert manifest.get("no_financial_calculations") is True
    print("PASS: Manifest integrity verified")


if __name__ == "__main__":
    test_outputs_exist()
    test_no_financial_fields()
    test_non_comparable_register()
    test_manifest_integrity()
