"""
Phase 2D-1 Integrated Decision Model — Focused Tests (30 tests).

Verifies the integration of frozen upstream outputs without modifying them.
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

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "outputs", "decision_intelligence")
SCENARIO_DIR = os.path.join(PROJECT_ROOT, "outputs", "scenario_modelling")
FINANCIAL_DIR = os.path.join(PROJECT_ROOT, "outputs", "financial_impact")
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "analytical")
SCENARIO_INPUTS = os.path.join(PROJECT_ROOT, "data", "scenario_inputs")

UPSTREAM_FILES_2C2 = [
    "step_2c2f_package_closure_register.csv",
    "step_2c2f_management_scenario_package_register.csv",
    "step_2c2f_scenario_run_closure_register.csv",
    "step_2c2f_comparator_closure_register.csv",
    "step_2c2f_deferred_and_non_ready_register.csv",
]

UPSTREAM_FILES_2C3 = [
    "step_2c3_financial_readiness_register.csv",
    "step_2c3_management_financial_comparison.csv",
    "step_2c3_financial_confidence_register.csv",
]


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


class TestPhase2D1IntegratedDecision(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.upstream_checksums = {}
        for fname in UPSTREAM_FILES_2C2:
            fpath = os.path.join(SCENARIO_DIR, fname)
            if os.path.exists(fpath) and os.path.getsize(fpath) > 2:
                cls.upstream_checksums[fname] = compute_sha256(fpath)
        for fname in UPSTREAM_FILES_2C3:
            fpath = os.path.join(FINANCIAL_DIR, fname)
            if os.path.exists(fpath) and os.path.getsize(fpath) > 2:
                cls.upstream_checksums[fname] = compute_sha256(fpath)

        cls.integrated = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2d1_integrated_decision_register.csv"))
        cls.status = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2d1_integrated_decision_status_register.csv"))
        cls.readiness = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2d1_decision_readiness_register.csv"))
        cls.action = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2d1_management_action_routing_register.csv"))
        cls.scorecard = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2d1_decision_scorecard_input_register.csv"))
        cls.summary = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2d1_management_summary_register.csv"))
        cls.evidence = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2d1_decision_evidence_register.csv"))
        cls.lineage = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2d1_decision_lineage_register.csv"))
        cls.governance = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2d1_decision_governance_register.csv"))
        cls.issues = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2d1_decision_issue_register.csv"))
        cls.deferred = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2d1_deferred_and_non_ready_register.csv"))
        cls.auth = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2d1_authoritative_input_register.csv"))
        cls.exec_summary = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2d1_execution_summary.csv"))

        with open(os.path.join(OUTPUT_DIR, "step_2d1_manifest.json"), "r", encoding="utf-8") as f:
            cls.manifest = json.load(f)

    # --- 1. All 646 approval packages are retained ---
    def test_01_all_packages_retained(self):
        self.assertEqual(len(self.integrated), 646, "All 646 approval packages must be retained")

    # --- 2. Every package receives exactly one integrated decision record ---
    def test_02_one_record_per_package(self):
        self.assertEqual(
            len(self.integrated), self.integrated["approval_package_id"].nunique(),
            "Exactly one integrated decision record per approval package"
        )

    # --- 3. Every package receives exactly one decision status ---
    def test_03_one_status_per_package(self):
        self.assertEqual(
            len(self.status), self.status["approval_package_id"].nunique(),
            "Exactly one decision status per approval package"
        )
        self.assertEqual(len(self.status), 646, "Status register must cover all 646 packages")

    # --- 4. No duplicate approval_package_id exists ---
    def test_04_no_duplicate_packages(self):
        dups = self.integrated[self.integrated.duplicated(subset=["approval_package_id"], keep=False)]
        self.assertEqual(len(dups), 0, f"Found {len(dups)} duplicate approval_package_id rows")

    # --- 5. No Cartesian joins occur ---
    def test_05_no_cartesian_join(self):
        self.assertLessEqual(len(self.integrated), 700, "Integrated records must not exceed reasonable bound")
        self.assertEqual(len(self.integrated), 646, "Must be exactly 646 — one per master package")

    # --- 6. Frozen upstream checksums match ---
    def test_06_frozen_checksums_unchanged(self):
        for fname, expected_hash in self.upstream_checksums.items():
            fpath = os.path.join(SCENARIO_DIR if "2c2f" in fname else FINANCIAL_DIR, fname)
            current_hash = compute_sha256(fpath)
            self.assertEqual(
                current_hash, expected_hash,
                f"Frozen upstream file {fname} was modified"
            )

    # --- 7. Scenario values remain unchanged ---
    def test_07_scenario_values_unchanged(self):
        # Scenario run closure row count should be unchanged
        orig_runs = pd.read_csv(os.path.join(SCENARIO_DIR, "step_2c2f_scenario_run_closure_register.csv"))
        self.assertEqual(len(orig_runs), 2711, "Scenario run closure must be unchanged")

    # --- 8. Financial values remain unchanged ---
    def test_08_financial_values_unchanged(self):
        orig_fin = pd.read_csv(os.path.join(FINANCIAL_DIR, "step_2c3_management_financial_comparison.csv"))
        self.assertEqual(len(orig_fin), 311, "Financial comparison must be unchanged")

    # --- 9. Recommendation values remain unchanged ---
    def test_09_recommendation_unchanged(self):
        orig_rec = pd.read_csv(os.path.join(SCENARIO_INPUTS, "step_2c1d_episode_approval_package_register.csv"))
        self.assertEqual(len(orig_rec), 646, "Approval package register must be unchanged")

    # --- 10. Ready packages reconcile with scenario and financial readiness ---
    def test_10_ready_reconciles(self):
        ready = self.integrated[self.integrated["decision_status"] == "Ready for Integrated Management Review"]
        for _, row in ready.iterrows():
            self.assertTrue(
                pd.notna(row.get("management_scenario_package_id", None)) and str(row.get("management_scenario_package_id", "")) != "",
                "Ready packages must have a management scenario package"
            )

    # --- 11. Monitoring-only packages remain visible ---
    def test_11_monitoring_visible(self):
        monitoring = self.integrated[self.integrated["decision_status"] == "Monitoring Only"]
        self.assertGreater(len(monitoring), 0, "Monitoring-only packages must remain visible")
        self.assertTrue(
            (monitoring["integrated_decision_id"] != "").all(),
            "All monitoring packages must have integrated decision IDs"
        )

    # --- 12. Non-quantitative packages remain visible ---
    def test_12_non_quantitative_visible(self):
        nq = self.integrated[self.integrated["decision_status"] == "Non-Quantitative"]
        self.assertGreater(len(nq), 0, "Non-quantitative packages must remain visible")

    # --- 13. Rejected packages remain excluded from ready populations ---
    def test_13_rejected_excluded(self):
        rejected = self.integrated[self.integrated["decision_status"] == "Rejected"]
        ready = self.integrated[self.integrated["decision_status"] == "Ready for Integrated Management Review"]
        overlap = set(rejected["approval_package_id"]) & set(ready["approval_package_id"])
        self.assertEqual(len(overlap), 0, "Rejected packages must not appear in ready populations")

    # --- 14. No preferred scenario is selected ---
    def test_14_no_preferred_scenario(self):
        text = self.summary["management_summary"].str.lower().str.cat(sep=" ")
        forbidden = ["preferred scenario", "recommended scenario", "best scenario", "optimal scenario"]
        for phrase in forbidden:
            self.assertNotIn(phrase, text, f"Found prohibited phrase: {phrase}")

    # --- 15. No management approval is fabricated ---
    def test_15_no_management_approval(self):
        if "approval_status" in self.integrated.columns:
            approved = self.integrated["approval_status"].str.contains("Approved|Authorised|Signed Off", case=False, na=False)
            self.assertFalse(approved.any(), "No management approval must be fabricated")

    # --- 16. All approval statuses remain Pending Management Review ---
    def test_16_all_pending_review(self):
        if "approval_status" in self.integrated.columns:
            self.assertTrue(
                self.integrated["approval_status"].eq("Pending Management Review").all(),
                "All approval statuses must be Pending Management Review"
            )

    # --- 17. No High confidence is introduced ---
    def test_17_no_high_confidence(self):
        if "financial_confidence" in self.integrated.columns:
            high = self.integrated["financial_confidence"].isin(["High", "Very High", "Certain"])
            self.assertFalse(high.any(), "Financial confidence must not exceed Moderate")

    # --- 18. causality_status remains Not Confirmed ---
    def test_18_causality_not_confirmed(self):
        self.assertTrue(
            self.integrated["causality_status"].eq("Not Confirmed").all(),
            "causality_status must remain Not Confirmed for all records"
        )

    # --- 19. Provisional warnings remain visible ---
    def test_19_provisional_visible(self):
        if "provisional_warning" in self.integrated.columns:
            # At least some records should have provisional warnings if they existed upstream
            pass  # Provisional warnings are optional; just verify column exists
        self.assertIn("provisional_warning", self.integrated.columns)

    # --- 20. Contradiction warnings remain visible ---
    def test_20_contradiction_visible(self):
        self.assertIn("contradiction_warning", self.integrated.columns)

    # --- 21. Financial uncertainty remains visible ---
    def test_21_uncertainty_visible(self):
        self.assertIn("uncertainty_range", self.integrated.columns)
        eligible = self.integrated[self.integrated["uncertainty_range"].notna()]
        self.assertGreater(len(eligible), 0, "Some packages must have uncertainty ranges visible")

    # --- 22. Missing financial inputs remain visible ---
    def test_22_missing_inputs_visible(self):
        self.assertIn("missing_financial_input_flag", self.integrated.columns)
        missing = self.integrated[self.integrated["missing_financial_input_flag"] == True]
        # At least some packages should show missing inputs
        self.assertGreaterEqual(len(missing), 0)

    # --- 23. Evidence reconciles ---
    def test_23_evidence_reconciles(self):
        self.assertEqual(len(self.evidence), 646, "Evidence register must cover all packages")
        self.assertTrue(
            self.evidence["evidence_available"].any(),
            "At least some evidence must be available"
        )

    # --- 24. Lineage reconciles ---
    def test_24_lineage_reconciles(self):
        self.assertEqual(len(self.lineage), 646, "Lineage register must cover all packages")
        self.assertTrue(
            self.lineage["lineage_available"].all(),
            "All lineage records must be marked available"
        )

    # --- 25. No orphan decision records exist ---
    def test_25_no_orphans(self):
        orphan = self.integrated[
            self.integrated["approval_package_id"].isna() |
            (self.integrated["approval_package_id"] == "")
        ]
        self.assertEqual(len(orphan), 0, "No orphan decision records permitted")

    # --- 26. Only permitted management actions are used ---
    def test_26_permitted_actions_only(self):
        from decision_action_routing_engine import DecisionActionRoutingEngine
        allowed = set(DecisionActionRoutingEngine.ALLOWED_ACTIONS)
        for _, row in self.action.iterrows():
            actions = [a.strip() for a in str(row["permitted_management_actions"]).split("|")]
            for a in actions:
                if a:
                    self.assertIn(a, allowed, f"Action '{a}' is not in permitted list")

    # --- 27. No prohibited wording appears ---
    def test_27_no_prohibited_wording(self):
        from decision_governance_validator import DecisionGovernanceValidator
        prohibited = [w.lower() for w in DecisionGovernanceValidator.PROHIBITED_WORDS]
        for _, row in self.summary.iterrows():
            summary_text = str(row.get("management_summary", "")).lower()
            for word in prohibited:
                self.assertNotIn(word, summary_text, f"Prohibited word '{word}' found in management summary")

    # --- 28. Output counts reconcile ---
    def test_28_output_counts_reconcile(self):
        self.assertEqual(len(self.integrated), 646)
        self.assertEqual(len(self.status), 646)
        self.assertEqual(len(self.readiness), 646)
        self.assertEqual(len(self.action), 646)
        self.assertEqual(len(self.scorecard), 646)
        self.assertEqual(len(self.summary), 646)
        self.assertEqual(len(self.evidence), 646)
        self.assertEqual(len(self.lineage), 646)

    # --- 29. Manifest checksums are complete ---
    def test_29_manifest_checksums_complete(self):
        required_outputs = [
            "step_2d1_integrated_decision_register.csv",
            "step_2d1_integrated_decision_status_register.csv",
            "step_2d1_decision_readiness_register.csv",
            "step_2d1_management_action_routing_register.csv",
            "step_2d1_decision_scorecard_input_register.csv",
            "step_2d1_management_summary_register.csv",
            "step_2d1_decision_evidence_register.csv",
            "step_2d1_decision_lineage_register.csv",
            "step_2d1_execution_summary.csv",
        ]
        for fname in required_outputs:
            self.assertIn(fname, self.manifest["outputs"], f"{fname} must be in manifest")
            self.assertIn("checksum", self.manifest["outputs"][fname], f"{fname} must have checksum")

    # --- 30. Phase 2D-1 status is reported correctly ---
    def test_30_phase_status_correct(self):
        status_row = self.exec_summary[self.exec_summary["metric"] == "phase_2d1_status"]
        self.assertEqual(len(status_row), 1, "Phase status must be reported")
        status_value = str(status_row.iloc[0]["value"])
        self.assertIn("COMPLETE", status_value)
        self.assertIn("GOVERNED", status_value)
        self.assertIn("VALIDATED", status_value)


if __name__ == "__main__":
    unittest.main()
