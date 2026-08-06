"""Test scenario sensitivity engine.

Verifies sensitivity classifications across comparator intensities.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.scenario_sensitivity_engine import ScenarioSensitivityEngine


def test_stable_direction():
    engine = ScenarioSensitivityEngine()
    runs = [
        {"comparator_type": "Baseline", "direction_of_change": "Increase", "percentage_change": 0, "assumption_warning_count": 0, "final_scenario_confidence": "Low"},
        {"comparator_type": "Conservative", "direction_of_change": "Increase", "percentage_change": 1, "assumption_warning_count": 0, "final_scenario_confidence": "Low"},
        {"comparator_type": "Expected", "direction_of_change": "Increase", "percentage_change": 2, "assumption_warning_count": 0, "final_scenario_confidence": "Low"},
        {"comparator_type": "Higher Intensity", "direction_of_change": "Increase", "percentage_change": 3, "assumption_warning_count": 0, "final_scenario_confidence": "Low"},
    ]
    result = engine.analyse_sensitivity(runs)
    assert result["sensitivity_classification"] == "Stable Direction"
    print("PASS: Stable direction when all comparators show increase with small magnitude")


def test_direction_reversal():
    engine = ScenarioSensitivityEngine()
    runs = [
        {"comparator_type": "Baseline", "direction_of_change": "Increase", "percentage_change": 0, "assumption_warning_count": 0, "final_scenario_confidence": "Low"},
        {"comparator_type": "Conservative", "direction_of_change": "Increase", "percentage_change": 5, "assumption_warning_count": 0, "final_scenario_confidence": "Low"},
        {"comparator_type": "Expected", "direction_of_change": "Decrease", "percentage_change": -3, "assumption_warning_count": 1, "final_scenario_confidence": "Low"},
    ]
    result = engine.analyse_sensitivity(runs)
    assert result["sensitivity_classification"] == "Direction Reversal"
    print("PASS: Direction reversal detected")


def test_insufficient_coverage():
    engine = ScenarioSensitivityEngine()
    runs = [
        {"comparator_type": "Baseline", "direction_of_change": "Increase", "percentage_change": 0, "assumption_warning_count": 0, "final_scenario_confidence": "Low"},
    ]
    result = engine.analyse_sensitivity(runs)
    assert result["sensitivity_classification"] == "Not Assessable"
    print("PASS: Not assessable with only one comparator")


if __name__ == "__main__":
    test_stable_direction()
    test_direction_reversal()
    test_insufficient_coverage()
