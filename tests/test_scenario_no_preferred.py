"""
Test: No preferred scenario is selected in any 2C-2E output.
Ensures no output contains a 'preferred_scenario' or 'selected_scenario' column.
"""

import os
import sys
import unittest
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from run_scenario_validation_challenge import ValidationRunner


class TestNoPreferredScenario(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = ValidationRunner(smoke_test=True, smoke_packages=3)
        cls.result = cls.runner.run()
        cls.final_dir = cls.runner.final_dir

    def test_no_preferred_column_in_outputs(self):
        forbidden = ["preferred_scenario", "selected_scenario", "recommended_scenario", "chosen_scenario"]
        for fname in os.listdir(self.final_dir):
            if not fname.startswith("analytical_scenario_validation") and not fname.startswith("analytical_scenario_"):
                continue
            if not fname.endswith(".csv"):
                continue
            fpath = os.path.join(self.final_dir, fname)
            if os.path.getsize(fpath) <= 2:
                continue
            try:
                df = pd.read_csv(fpath)
            except Exception:
                continue
            for col in forbidden:
                self.assertNotIn(col, df.columns, f"Forbidden column '{col}' found in {fname}")


if __name__ == "__main__":
    unittest.main()
