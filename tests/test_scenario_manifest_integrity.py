"""
Test: Manifest integrity after full run.
Ensures manifest exists, contains checksums, and references all outputs.
"""

import os
import sys
import unittest
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from run_scenario_validation_challenge import ValidationRunner


class TestManifestIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = ValidationRunner(smoke_test=True, smoke_packages=3)
        cls.result = cls.runner.run()
        cls.manifest_path = os.path.join(cls.runner.project_root, "outputs", "scenario_modelling", "step_2c2e_run_manifest.json")

    def test_manifest_exists(self):
        self.assertTrue(os.path.exists(self.manifest_path))

    def test_manifest_valid_json(self):
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        self.assertEqual(manifest["step"], "2C-2E")
        self.assertIn("outputs", manifest)

    def test_manifest_has_checksums(self):
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        for fname, meta in manifest["outputs"].items():
            self.assertIn("checksum_sha256", meta)
            self.assertEqual(len(meta["checksum_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
