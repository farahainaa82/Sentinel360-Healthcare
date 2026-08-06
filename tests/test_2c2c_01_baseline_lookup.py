"""Test 2C-2C-01: Baseline lookup key construction.

Verifies that baseline keys are built consistently between baseline engine
and scenario runner so no baselines are silently skipped.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
from src.scenario_config_loader import ScenarioConfigLoader
from src.scenario_baseline_engine import ScenarioBaselineEngine


def test_baseline_lookup_consistency():
    loader = ScenarioConfigLoader()
    configs = loader.get_all_configs()
    mapping_df = configs["package_scenario_mapping"]
    episode_df = configs["episode_register"]

    engine = ScenarioBaselineEngine(loader)
    baselines = engine.build_all_baselines_for_all_mappings(mapping_df, episode_df)

    lookup = {}
    for bl in baselines:
        key = f"{bl.approval_package_id}|{bl.episode_id}|{bl.scenario_template_id}"
        lookup[key] = bl

    missing = 0
    for _, row in mapping_df.iterrows():
        key = f"{row['approval_package_id']}|{row['episode_id']}|{row['scenario_template_id']}"
        if key not in lookup:
            missing += 1

    assert missing == 0, f"{missing} mappings missing from baseline lookup"
    assert len(baselines) == len(mapping_df), "Baseline count mismatch"
    print("PASS: All mappings have consistent baseline lookup keys")


if __name__ == "__main__":
    test_baseline_lookup_consistency()
