"""Test scenario trade-off evidence and lineage.

Verifies evidence linkage and lineage completeness.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd


def test_evidence_records_exist():
    df = pd.read_csv("data/analytical/analytical_scenario_tradeoff_evidence.csv", keep_default_na=False)
    assert len(df) > 0, "Evidence records are empty"
    assert "scenario_run_id" in df.columns
    assert "evidence_type" in df.columns
    print("PASS: Evidence records exist with required columns")


def test_lineage_records_exist():
    df = pd.read_csv("data/analytical/analytical_scenario_tradeoff_lineage.csv", keep_default_na=False)
    assert len(df) > 0, "Lineage records are empty"
    assert "scenario_run_id" in df.columns
    assert "source_file" in df.columns
    print("PASS: Lineage records exist with required columns")


def test_evidence_lineage_match():
    evidence = pd.read_csv("data/analytical/analytical_scenario_tradeoff_evidence.csv", keep_default_na=False)
    lineage = pd.read_csv("data/analytical/analytical_scenario_tradeoff_lineage.csv", keep_default_na=False)
    ev_runs = set(evidence["scenario_run_id"].unique())
    lin_runs = set(lineage["scenario_run_id"].unique())
    assert ev_runs == lin_runs, "Evidence and lineage scenario_run_ids do not match"
    print("PASS: Evidence and lineage scenario_run_ids match")


def test_no_orphan_scenarios():
    impacts = pd.read_csv("data/analytical/analytical_scenario_primary_impacts.csv", keep_default_na=False)
    evidence = pd.read_csv("data/analytical/analytical_scenario_tradeoff_evidence.csv", keep_default_na=False)
    impact_runs = set(impacts["scenario_run_id"].unique())
    evidence_runs = set(evidence["scenario_run_id"].unique())
    orphans = impact_runs - evidence_runs
    assert not orphans, f"Orphan scenarios without evidence: {len(orphans)}"
    print("PASS: No orphan scenarios without evidence")


if __name__ == "__main__":
    test_evidence_records_exist()
    test_lineage_records_exist()
    test_evidence_lineage_match()
    test_no_orphan_scenarios()
