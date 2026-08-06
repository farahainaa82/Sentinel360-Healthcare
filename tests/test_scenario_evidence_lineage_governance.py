"""
Test: Evidence, lineage, governance, and issues outputs exist and are non-empty.
Ensures every engine run produces traceability records.
"""

import os
import sys
import unittest
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from run_scenario_validation_challenge import ValidationRunner


class TestEvidenceLineageGovernance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = ValidationRunner(smoke_test=True, smoke_packages=3)
        cls.result = cls.runner.run()
        cls.final_dir = cls.runner.final_dir

    def test_evidence_exists(self):
        path = os.path.join(self.final_dir, "analytical_scenario_validation_evidence.csv")
        self.assertTrue(os.path.exists(path))
        df = pd.read_csv(path)
        self.assertGreater(len(df), 0)

    def test_lineage_exists(self):
        path = os.path.join(self.final_dir, "analytical_scenario_validation_lineage.csv")
        self.assertTrue(os.path.exists(path))
        df = pd.read_csv(path)
        self.assertGreater(len(df), 0)

    def test_governance_exists(self):
        path = os.path.join(self.final_dir, "analytical_scenario_validation_governance.csv")
        self.assertTrue(os.path.exists(path))
        df = pd.read_csv(path)
        self.assertGreater(len(df), 0)

    def test_issues_exists(self):
        path = os.path.join(self.final_dir, "analytical_scenario_validation_issues.csv")
        self.assertTrue(os.path.exists(path))
        df = pd.read_csv(path)
        self.assertGreater(len(df), 0)


if __name__ == "__main__":
    unittest.main()
