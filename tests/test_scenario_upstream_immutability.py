"""
Test: Frozen Step 2C-2C and 2C-2D outputs are not modified.
Ensures upstream files retain their original checksums after 2C-2E run.
"""

import os
import sys
import unittest
import hashlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from run_scenario_validation_challenge import ValidationRunner


class TestUpstreamImmutability(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = ValidationRunner(smoke_test=True, smoke_packages=3)
        cls.data_dir = cls.runner.data_dir
        cls.upstream_files = [
            "analytical_scenario_runs.csv",
            "analytical_scenario_baselines.csv",
            "analytical_scenario_comparator_analysis.csv",
            "analytical_scenario_effect_classification.csv",
            "analytical_scenario_dominance.csv",
            "analytical_scenario_sensitivity.csv",
            "analytical_scenario_diminishing_returns.csv",
            "analytical_scenario_risk_displacement.csv",
            "analytical_scenario_management_interpretation.csv",
            "analytical_scenario_confidence.csv",
            "analytical_scenario_evidence.csv",
            "analytical_scenario_governance.csv",
            "analytical_scenario_lineage.csv",
            "analytical_scenario_non_comparable_register.csv",
        ]
        cls.pre_checksums = {}
        for fname in cls.upstream_files:
            fpath = os.path.join(cls.data_dir, fname)
            if os.path.exists(fpath):
                with open(fpath, "rb") as f:
                    cls.pre_checksums[fname] = hashlib.sha256(f.read()).hexdigest()
        # Run the runner
        cls.result = cls.runner.run()
        cls.post_checksums = {}
        for fname in cls.upstream_files:
            fpath = os.path.join(cls.data_dir, fname)
            if os.path.exists(fpath):
                with open(fpath, "rb") as f:
                    cls.post_checksums[fname] = hashlib.sha256(f.read()).hexdigest()

    def test_upstream_files_unchanged(self):
        for fname, pre in self.pre_checksums.items():
            post = self.post_checksums.get(fname)
            self.assertEqual(pre, post, f"Upstream file {fname} was modified by 2C-2E run")


if __name__ == "__main__":
    unittest.main()
