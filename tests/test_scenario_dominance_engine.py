"""Test scenario dominance engine.

Verifies analytical dominance rules (not management recommendations).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.scenario_dominance_engine import ScenarioDominanceEngine


def test_dominates():
    engine = ScenarioDominanceEngine()
    a = {
        "approval_package_id": "PKG-001",
        "scenario_template_id": "SCEN-001",
        "scenario_family": "Staffing Coverage Adjustment",
        "direction_of_change": "Increase",
        "percentage_change": 15.0,
        "final_scenario_confidence": "Moderate",
        "contradiction_severity": "No Contradiction",
        "assumption_warning_count": 0,
    }
    b = {
        "approval_package_id": "PKG-001",
        "scenario_template_id": "SCEN-001",
        "scenario_family": "Staffing Coverage Adjustment",
        "direction_of_change": "Increase",
        "percentage_change": 5.0,
        "final_scenario_confidence": "Low",
        "contradiction_severity": "Minor",
        "assumption_warning_count": 1,
    }
    result = engine.compare_pairwise(a, b)
    assert result["dominance_classification"] == "Dominates"
    print("PASS: Dominance detected when all conditions met")


def test_dominated():
    engine = ScenarioDominanceEngine()
    a = {
        "approval_package_id": "PKG-001",
        "scenario_template_id": "SCEN-001",
        "scenario_family": "Staffing Coverage Adjustment",
        "direction_of_change": "Decrease",
        "percentage_change": -5.0,
        "final_scenario_confidence": "Low",
        "contradiction_severity": "Minor",
        "assumption_warning_count": 1,
    }
    b = {
        "approval_package_id": "PKG-001",
        "scenario_template_id": "SCEN-001",
        "scenario_family": "Staffing Coverage Adjustment",
        "direction_of_change": "Increase",
        "percentage_change": 10.0,
        "final_scenario_confidence": "Moderate",
        "contradiction_severity": "No Contradiction",
        "assumption_warning_count": 0,
    }
    result = engine.compare_pairwise(a, b)
    assert result["dominance_classification"] == "Dominated"
    print("PASS: Dominated detected when primary KPI is worse")


def test_incomparable():
    engine = ScenarioDominanceEngine()
    a = {
        "approval_package_id": "PKG-001",
        "scenario_template_id": "SCEN-001",
        "scenario_family": "Staffing Coverage Adjustment",
    }
    b = {
        "approval_package_id": "PKG-002",
        "scenario_template_id": "SCEN-002",
        "scenario_family": "Absenteeism Contingency",
    }
    result = engine.compare_pairwise(a, b)
    assert result["dominance_classification"] == "Incomparable"
    print("PASS: Incomparable detected for different packages")


if __name__ == "__main__":
    test_dominates()
    test_dominated()
    test_incomparable()
