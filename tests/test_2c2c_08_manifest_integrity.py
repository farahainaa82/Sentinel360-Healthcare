"""Test 2C-2C-08: Manifest integrity and timing metrics.

Verifies that the run manifest exists, contains all required fields,
and that timing metrics are present and positive.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json


def test_manifest_integrity():
    with open("outputs/scenario_modelling/step_2c2c_run_manifest.json") as f:
        manifest = json.load(f)

    required_keys = [
        "scenario_runs_attempted",
        "scenario_runs_completed",
        "no_financial_calculations",
        "readiness_for_2c2d",
        "run_timestamp",
        "engine_version",
    ]
    for key in required_keys:
        assert key in manifest, f"Missing key in manifest: {key}"

    assert manifest["scenario_runs_attempted"] > 0, "No scenario runs attempted"
    assert manifest["no_financial_calculations"] is True, "Financial calculations flag is not True"
    assert "timing_seconds" in manifest, "Missing timing_seconds in manifest"
    timing = manifest["timing_seconds"]
    for phase in ["input_loading", "baseline_construction", "scenario_calculations", "output_writing", "total_execution"]:
        assert phase in timing, f"Missing timing phase: {phase}"
        assert timing[phase] >= 0, f"Negative timing for {phase}"

    print("PASS: Manifest integrity and timing metrics verified")


if __name__ == "__main__":
    test_manifest_integrity()
