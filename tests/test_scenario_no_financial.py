"""
Test: No financial impact calculation in 2C-2E outputs.
Ensures no output contains financial impact columns or values.
"""

import os
import sys
import unittest
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from run_scenario_validation_challenge import ValidationRunner


class TestNoFinancialCalculation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = ValidationRunner(smoke_test=True, smoke_packages=3)
        cls.result = cls.runner.run()
        cls.final_dir = cls.runner.final_dir

    def test_no_financial_columns(self):
        forbidden = ["financial_impact", "cost_benefit", "npv", "roi", "budget_impact", "revenue_change"]
        for fname in os.listdir(self.final_dir):
            if not fname.startswith("analytical_scenario_") or not fname.endswith(".csv"):
                continue
            fpath = os.path.join(self.final_dir, fname)
            if os.path.getsize(fpath) <= 2:
                continue
            try:
                df = pd.read_csv(fpath)
            except Exception:
                continue
            for col in forbidden:
                self.assertNotIn(col, df.columns, f"Financial column '{col}' found in {fname}")


if __name__ == "__main__":
    unittest.main()
