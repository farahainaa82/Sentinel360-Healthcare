"""Test scenario displacement engine.

Verifies risk displacement detection rules.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.scenario_displacement_engine import ScenarioDisplacementEngine


def test_baseline_no_displacement():
    engine = ScenarioDisplacementEngine()
    scenario = {
        "scenario_run_id": "SR-001",
        "approval_package_id": "PKG-001",
        "episode_id": "EP-001",
        "scenario_family": "Staffing Coverage Adjustment",
        "comparator_type": "Baseline",
        "primary_kpi_id": "kpi_001",
        "final_scenario_confidence": "Low",
        "assumption_values_json": "{}",
    }
    baseline = {}
    results = engine.analyse_displacement(scenario, baseline)
    assert len(results) == 1
    assert results[0]["displacement_classification"] == "No Displacement Identified"
    print("PASS: Baseline comparator has no displacement")


def test_staffing_cross_kpi_displacement():
    engine = ScenarioDisplacementEngine()
    scenario = {
        "scenario_run_id": "SR-002",
        "approval_package_id": "PKG-001",
        "episode_id": "EP-001",
        "scenario_family": "Staffing Coverage Adjustment",
        "comparator_type": "Conservative",
        "primary_kpi_id": "kpi_001",
        "final_scenario_confidence": "Low",
        "assumption_values_json": '{"additional_staff_count": 2.0, "temporary_staff_count": 1.0}',
    }
    baseline = {}
    results = engine.analyse_displacement(scenario, baseline)
    classifications = [r["displacement_classification"] for r in results]
    assert "Possible Cross-KPI Displacement" in classifications
    print("PASS: Staffing increase triggers cross-KPI displacement")


def test_absenteeism_low_replacement():
    engine = ScenarioDisplacementEngine()
    scenario = {
        "scenario_run_id": "SR-003",
        "approval_package_id": "PKG-001",
        "episode_id": "EP-001",
        "scenario_family": "Absenteeism Contingency",
        "comparator_type": "Expected",
        "primary_kpi_id": "kpi_002",
        "final_scenario_confidence": "Low",
        "assumption_values_json": '{"assumed_absenteeism_reduction_pct": 20.0, "replacement_coverage_pct": 30.0}',
    }
    baseline = {}
    results = engine.analyse_displacement(scenario, baseline)
    classifications = [r["displacement_classification"] for r in results]
    assert "Possible Within-Department Displacement" in classifications
    print("PASS: Low replacement coverage triggers within-department displacement")


if __name__ == "__main__":
    test_baseline_no_displacement()
    test_staffing_cross_kpi_displacement()
    test_absenteeism_low_replacement()
