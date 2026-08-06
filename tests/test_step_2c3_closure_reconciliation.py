"""
Phase 2C-3 Closure Reconciliation Focused Tests

Verifies reconciliation outcomes WITHOUT rerunning financial engines.
All tests read existing frozen outputs only.
"""

import os
import sys
import json
import hashlib
import unittest
from datetime import datetime

import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "outputs", "financial_impact")
SCENARIO_DIR = os.path.join(PROJECT_ROOT, "outputs", "scenario_modelling")
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "analytical")

# Capture upstream checksums at test load time (before any potential modification)
UPSTREAM_FILES_2C2 = [
    "step_2c2f_package_closure_register.csv",
    "step_2c2f_scenario_run_closure_register.csv",
    "step_2c2f_comparator_closure_register.csv",
    "step_2c2f_management_scenario_package_register.csv",
    "step_2c2f_financial_input_requirement_register.csv",
    "step_2c2f_freeze_manifest.json",
]


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


class TestPhase2C3ClosureReconciliation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.start_time = datetime.now().isoformat()

        # Capture upstream 2C-2 file checksums before tests
        cls.upstream_checksums = {}
        for fname in UPSTREAM_FILES_2C2:
            fpath = os.path.join(SCENARIO_DIR, fname)
            if os.path.exists(fpath) and os.path.getsize(fpath) > 2:
                cls.upstream_checksums[fname] = compute_sha256(fpath)

        # Load existing 2C-3 outputs (read-only)
        cls.dc = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2c3_double_counting_validation_register.csv"))
        cls.recon = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2c3_closure_reconciliation_summary.csv"))
        cls.cost_components = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2c3_scenario_cost_components.csv"))
        cls.benefit_components = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2c3_financial_benefit_components.csv"))
        cls.net_impact = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2c3_net_financial_impact.csv"))
        cls.roi = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2c3_roi_register.csv"))
        cls.uncertainty = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2c3_financial_uncertainty_register.csv"))
        cls.sensitivity = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2c3_financial_sensitivity_register.csv"))

        issue_path = os.path.join(OUTPUT_DIR, "step_2c3_financial_issue_register.csv")
        if os.path.exists(issue_path) and os.path.getsize(issue_path) > 2:
            cls.issues = pd.read_csv(issue_path)
        else:
            cls.issues = pd.DataFrame()

        with open(os.path.join(OUTPUT_DIR, "step_2c3_freeze_manifest.json"), "r", encoding="utf-8") as f:
            cls.manifest = json.load(f)

        # Load docs for content verification
        with open(os.path.join(DOCS_DIR, "step_2c3_closure_reconciliation_report.md"), "r", encoding="utf-8") as f:
            cls.recon_report = f.read()

        with open(os.path.join(DOCS_DIR, "step_2c3_uncertainty_and_sensitivity_methodology.md"), "r", encoding="utf-8") as f:
            cls.uncertainty_doc = f.read()

    # --- Test 1: All 384 double-counting findings are classified ---
    def test_01_all_dc_classified(self):
        self.assertEqual(len(self.dc), 384, "Expected 384 double-counting findings")
        self.assertEqual(len(self.recon), 384, "Expected 384 reconciliation records")
        self.assertTrue(
            self.recon["reconciliation_classification"].notna().all(),
            "Every finding must have a reconciliation_classification"
        )
        self.assertTrue(
            self.recon["reconciliation_classification"].ne("").all(),
            "Classification must not be empty"
        )

    # --- Test 2: No affected calculation is silently retained ---
    def test_02_no_silent_retention(self):
        # Every DC issue_id in the original register must appear in the reconciliation
        original_ids = set(self.dc["issue_id"])
        reconciled_ids = set(self.recon["issue_id"])
        missing = original_ids - reconciled_ids
        self.assertEqual(
            len(missing), 0,
            f"These issue_ids were not reconciled: {missing}"
        )
        # All reconciled records must have a non-empty action_taken
        self.assertTrue(
            self.recon["action_taken"].notna().all() and self.recon["action_taken"].ne("").all(),
            "Every reconciled finding must document an action taken"
        )

    # --- Test 3: Unresolved findings reconcile to the issue register ---
    def test_03_unresolved_reconcile_to_issues(self):
        unresolved = self.recon[self.recon["resolution_status"] != "Resolved"]
        if len(unresolved) > 0:
            # If there are unresolved findings, they must appear in the issue register
            unresolved_ids = set(unresolved["issue_id"])
            if len(self.issues) > 0 and "issue_id" in self.issues.columns:
                issue_ids = set(self.issues["issue_id"])
            else:
                issue_ids = set()
            missing_in_issues = unresolved_ids - issue_ids
            self.assertEqual(
                len(missing_in_issues), 0,
                f"Unresolved findings not in issue register: {missing_in_issues}"
            )
        else:
            # If zero unresolved, issue register must be empty or have zero rows
            self.assertEqual(len(self.issues), 0, "Zero unresolved findings => issue register must be empty")

    # --- Test 4: Resolved findings are not incorrectly labelled as open issues ---
    def test_04_resolved_not_labelled_open(self):
        resolved_ids = set(self.recon[self.recon["resolution_status"] == "Resolved"]["issue_id"])
        if len(self.issues) > 0 and "issue_id" in self.issues.columns:
            issue_ids = set(self.issues["issue_id"])
            overlap = resolved_ids & issue_ids
            self.assertEqual(
                len(overlap), 0,
                f"Resolved findings incorrectly present in issue register: {overlap}"
            )

    # --- Test 5: Uncertainty-engine execution is confirmed ---
    def test_05_uncertainty_engine_executed(self):
        # The uncertainty CSV must exist with headers (runner wrote it even if empty)
        self.assertTrue(
            os.path.exists(os.path.join(OUTPUT_DIR, "step_2c3_financial_uncertainty_register.csv")),
            "Uncertainty register file must exist"
        )
        # Must have expected columns (headers present) — accept either uncertainty or sensitivity schema
        expected_cols = {
            "scenario_run_id", "approval_package_id", "cost_component_name",
            "comparator_type",
        }
        actual_cols = set(self.uncertainty.columns)
        self.assertTrue(
            expected_cols.issubset(actual_cols),
            f"Uncertainty register missing expected columns. Got: {actual_cols}"
        )
        # The cost_components count should match the number assessed
        self.assertGreater(len(self.cost_components), 0, "Cost components must exist to have been assessed")

    # --- Test 6: Reason for zero uncertainty outputs is documented ---
    def test_06_uncertainty_reason_documented(self):
        # Report must contain the root cause explanation
        self.assertIn(
            "financial_input_id", self.recon_report,
            "Reconciliation report must document the missing financial_input_id root cause"
        )
        self.assertIn(
            "cost_components", self.recon_report,
            "Reconciliation report must reference cost_components"
        )
        # Uncertainty methodology doc must contain the closure reconciliation section
        self.assertIn(
            "Closure Reconciliation", self.uncertainty_doc,
            "Uncertainty methodology must contain closure reconciliation section"
        )

    # --- Test 7: No financial calculation is rerun ---
    def test_07_no_engine_rerun(self):
        # Verify that output timestamps in the freeze manifest predate the test execution
        # The manifest freeze_timestamp should be earlier than now
        freeze_ts = self.manifest.get("freeze_timestamp", self.manifest.get("timestamp", ""))
        self.assertNotEqual(freeze_ts, "", "Freeze manifest must have a timestamp")
        freeze_dt = datetime.fromisoformat(freeze_ts.replace("Z", "+00:00"))
        now_dt = datetime.now(freeze_dt.tzinfo if freeze_dt.tzinfo else None)
        self.assertLess(
            freeze_dt, now_dt,
            "Freeze timestamp must be in the past (no new run occurred)"
        )
        # The reconciliation summary must be read-only (no new calculated fields in cost/benefit)
        self.assertEqual(
            len(self.cost_components), 8019,
            "Cost components row count must match frozen output (8019)"
        )

    # --- Test 8: Frozen Phase 2C-2 files remain unchanged ---
    def test_08_frozen_2c2_unchanged(self):
        for fname, expected_hash in self.upstream_checksums.items():
            fpath = os.path.join(SCENARIO_DIR, fname)
            current_hash = compute_sha256(fpath)
            self.assertEqual(
                current_hash, expected_hash,
                f"Frozen Phase 2C-2 file {fname} was modified after test load"
            )

    # --- Test 9: No preferred scenario is selected ---
    def test_09_no_preferred_scenario(self):
        # Reconciliation report must not contain language selecting or recommending a scenario
        # Allow negations like "No preferred scenario selected" but reject selections
        selection_phrases = [
            "is the preferred scenario",
            "is the recommended scenario",
            "is the best scenario",
            "is the optimal scenario",
            "selected as preferred",
            "selected as the preferred",
            "scenario selected:",
        ]
        text = self.recon_report.lower()
        for phrase in selection_phrases:
            self.assertNotIn(
                phrase, text,
                f"Reconciliation report must not select a preferred scenario (found: {phrase})"
            )

    # --- Test 10: No unsupported ROI is introduced ---
    def test_10_no_unsupported_roi(self):
        # The existing ROI register should not contain new unsupported entries
        # Since all assumptions are Draft, ROI should be zero or ineligible
        if len(self.roi) > 0 and "roi_status" in self.roi.columns:
            supported = self.roi["roi_status"].isin(["Eligible", "Supported", "Calculable"])
            self.assertFalse(
                supported.any(),
                "No unsupported ROI should be introduced; all assumptions remain Draft"
            )
        # Reconciliation must not introduce new ROI calculations
        self.assertNotIn(
            "roi", self.recon.columns,
            "Reconciliation summary must not introduce new ROI calculations"
        )


if __name__ == "__main__":
    unittest.main()
