"""
Test: Package Readiness classification validity.
Ensures readiness classifications are from controlled vocabulary.
Ensures scorecard linkage exists.
"""

import os
import sys
import unittest
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from run_scenario_validation_challenge import ValidationRunner


class TestPackageReadiness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = ValidationRunner(smoke_test=True, smoke_packages=3)
        cls.result = cls.runner.run()
        cls.pr = pd.read_csv(os.path.join(cls.runner.final_dir, "analytical_scenario_package_readiness.csv"))

    def test_readiness_file_exists(self):
        self.assertTrue(os.path.exists(os.path.join(self.runner.final_dir, "analytical_scenario_package_readiness.csv")))

    def test_readiness_not_empty(self):
        self.assertGreater(len(self.pr), 0)

    def test_readiness_values_valid(self):
        allowed = {"Ready", "Ready with Conditions", "Not Ready", "Rejected"}
        invalid = set(self.pr["package_readiness"].unique()) - allowed
        self.assertEqual(len(invalid), 0, f"Invalid readiness values: {invalid}")

    def test_scorecard_linkage(self):
        self.assertIn("scenario_validation_index", self.pr.columns)
        self.assertTrue(self.pr["scenario_validation_index"].notna().all())


if __name__ == "__main__":
    unittest.main()
