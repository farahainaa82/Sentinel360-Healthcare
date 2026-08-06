"""
Test: Dominance downgrade when comparators are identical.
Ensures dominance claims are downgraded to Non-Dominated when values are identical.
"""

import os
import sys
import unittest
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from run_scenario_validation_challenge import ValidationRunner


class TestDominanceDowngrade(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = ValidationRunner(smoke_test=True, smoke_packages=3)
        cls.result = cls.runner.run()
        cls.dom = pd.read_csv(os.path.join(cls.runner.final_dir, "analytical_scenario_dominance_validation.csv"))

    def test_dominance_file_exists(self):
        self.assertTrue(os.path.exists(os.path.join(self.runner.final_dir, "analytical_scenario_dominance_validation.csv")))

    def test_downgrade_logic(self):
        downgraded = self.dom[self.dom["validation_status"] == "Downgraded"]
        for _, row in downgraded.iterrows():
            self.assertEqual(row["validated_classification"], "Non-Dominated")
            self.assertIn("identical", row["validation_flags"].lower())

    def test_original_preserved(self):
        self.assertIn("original_classification", self.dom.columns)
        self.assertIn("validated_classification", self.dom.columns)


if __name__ == "__main__":
    unittest.main()
