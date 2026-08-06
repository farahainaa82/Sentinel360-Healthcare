"""
Test: Validation Register completeness and key presence.
Ensures every scenario run has a validation register entry.
Ensures no scenario_run_id is duplicated inappropriately.
"""

import os
import sys
import unittest
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from run_scenario_validation_challenge import ValidationRunner


class TestValidationRegister(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = ValidationRunner(smoke_test=True, smoke_packages=3)
        cls.result = cls.runner.run()
        cls.reg = pd.read_csv(os.path.join(cls.runner.final_dir, "analytical_scenario_validation_register.csv"))
        cls.runs = pd.read_csv(os.path.join(cls.runner.data_dir, "analytical_scenario_runs.csv"))

    def test_register_exists(self):
        self.assertTrue(os.path.exists(os.path.join(self.runner.final_dir, "analytical_scenario_validation_register.csv")))

    def test_register_not_empty(self):
        self.assertGreater(len(self.reg), 0)

    def test_all_runs_present(self):
        smoke_pkg_ids = self.runs["approval_package_id"].unique()[:3]
        smoke_runs = self.runs[self.runs["approval_package_id"].isin(smoke_pkg_ids)]
        missing = set(smoke_runs["scenario_run_id"]) - set(self.reg["scenario_run_id"])
        self.assertEqual(len(missing), 0, f"Missing scenario_run_ids: {missing}")

    def test_required_columns(self):
        required = ["scenario_run_id", "approval_package_id", "baseline_validation_status",
                    "numerical_validation_status", "assumption_challenge_status", "overall_validation_status"]
        for col in required:
            self.assertIn(col, self.reg.columns, f"Missing column: {col}")

    def test_no_duplicate_scenario_run_ids(self):
        dups = self.reg[self.reg.duplicated("scenario_run_id", keep=False)]
        self.assertEqual(len(dups), 0, f"Duplicate scenario_run_ids found: {len(dups)}")


if __name__ == "__main__":
    unittest.main()
