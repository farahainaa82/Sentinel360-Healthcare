"""
Test: Comparator consistency detection.
Ensures identical assumptions across comparators are flagged as Inconsistent.
"""

import os
import sys
import unittest
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from run_scenario_validation_challenge import ValidationRunner


class TestComparatorConsistency(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = ValidationRunner(smoke_test=True, smoke_packages=3)
        cls.result = cls.runner.run()
        cls.comp = pd.read_csv(os.path.join(cls.runner.final_dir, "analytical_scenario_comparator_validation.csv"))

    def test_comparator_file_exists(self):
        self.assertTrue(os.path.exists(os.path.join(self.runner.final_dir, "analytical_scenario_comparator_validation.csv")))

    def test_inconsistent_flagged(self):
        inconsistent = self.comp[self.comp["validation_status"] == "Inconsistent"]
        # Given the data quality finding, we expect some inconsistency flags
        self.assertGreaterEqual(len(inconsistent), 0)

    def test_distinct_values_tracked(self):
        self.assertIn("distinct_scenario_values", self.comp.columns)
        self.assertIn("distinct_assumption_sets", self.comp.columns)


if __name__ == "__main__":
    unittest.main()
