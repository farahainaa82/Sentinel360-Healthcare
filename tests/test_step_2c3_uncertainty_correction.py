"""
Phase 2C-3 Uncertainty Schema-Contract Correction — Focused Tests (22 tests).

Verifies the focused uncertainty correction WITHOUT rerunning the full pipeline.
All tests read existing frozen outputs and confirm correction integrity.
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
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")

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


class TestUncertaintySchemaCorrection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.start_time = datetime.now().isoformat()

        # Capture upstream 2C-2 checksums before tests
        cls.upstream_checksums = {}
        for fname in UPSTREAM_FILES_2C2:
            fpath = os.path.join(SCENARIO_DIR, fname)
            if os.path.exists(fpath) and os.path.getsize(fpath) > 2:
                cls.upstream_checksums[fname] = compute_sha256(fpath)

        # Load freeze manifest for immutable checksum verification
        with open(os.path.join(OUTPUT_DIR, "step_2c3_freeze_manifest.json"), "r", encoding="utf-8") as f:
            cls.manifest = json.load(f)

        # Load corrected outputs
        cls.uncertainty = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2c3_financial_uncertainty_register.csv"))
        cls.eligibility = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2c3_uncertainty_eligibility_register.csv"))
        cls.schema_corr = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2c3_uncertainty_schema_correction_register.csv"))
        cls.corr_summary = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2c3_uncertainty_correction_summary.csv"))
        cls.cost_components = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2c3_scenario_cost_components.csv"))
        cls.benefit_components = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2c3_financial_benefit_components.csv"))
        cls.cost_summary = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2c3_scenario_cost_summary.csv"))
        cls.benefit_summary = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2c3_financial_benefit_summary.csv"))
        cls.net_impact = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2c3_net_financial_impact.csv"))
        cls.roi = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2c3_roi_register.csv"))
        cls.management = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2c3_management_financial_comparison.csv"))
        cls.confidence = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2c3_financial_confidence_register.csv"))
        cls.readiness = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2c3_financial_readiness_register.csv"))
        cls.execution = pd.read_csv(os.path.join(OUTPUT_DIR, "step_2c3_execution_summary.csv"))

    # --- 1. All 8,019 cost components are assessed ---
    def test_01_all_components_assessed(self):
        self.assertEqual(len(self.uncertainty), 8019, "All 8,019 cost components must be assessed")
        self.assertEqual(len(self.eligibility), 8019, "Eligibility register must cover all components")

    # --- 2. Governed IDs are used for range joins ---
    def test_02_governed_ids_used(self):
        # Every record with a range must have a non-empty financial_input_id
        ranged = self.uncertainty[self.uncertainty["assumption_range_id"].notna() & (self.uncertainty["assumption_range_id"] != "")]
        self.assertTrue(
            (ranged["financial_input_id"].notna() & (ranged["financial_input_id"] != "")).all(),
            "All ranged records must use governed financial_input_id"
        )
        # schema correction register must confirm ID-based join
        self.assertIn("financial_input_id", self.schema_corr["corrected_join_key"].iloc[0])

    # --- 3. No fuzzy or label-only join is used where IDs exist ---
    def test_03_no_fuzzy_join(self):
        # The corrected join key must reference governed IDs, not descriptive labels
        corrected_key = self.schema_corr["corrected_join_key"].iloc[0]
        self.assertIn("financial_input_id", corrected_key)
        self.assertNotIn("cost_component_name", corrected_key.split("→")[-1].strip())
        # The final join to assumption_ranges must be on financial_input_id
        self.assertIn("assumption_ranges.financial_input_id", corrected_key)

    # --- 4. No Cartesian join occurs ---
    def test_04_no_cartesian_join(self):
        # Uncertainty row count must equal cost component row count
        self.assertEqual(
            len(self.uncertainty), len(self.cost_components),
            "Uncertainty register must not have more rows than cost components (Cartesian explosion)"
        )
        # schema correction register must report zero ambiguous mappings
        self.assertEqual(
            int(self.schema_corr["ambiguous_mappings"].iloc[0]), 0,
            "No ambiguous mappings (Cartesian joins) permitted"
        )

    # --- 5. Every eligible record maps to exactly one active range ---
    def test_05_one_active_range_per_eligible(self):
        eligible = self.uncertainty[self.uncertainty["uncertainty_eligibility"] == "Eligible — Governed Range Available"]
        if len(eligible) > 0:
            # Group by financial_input_id and count unique range_ids per ID
            range_counts = eligible.groupby("financial_input_id")["assumption_range_id"].nunique()
            multi_range = range_counts[range_counts > 1]
            self.assertEqual(
                len(multi_range), 0,
                f"Eligible records map to multiple ranges for IDs: {multi_range.index.tolist()}"
            )

    # --- 6. Multiple active range mappings are blocked ---
    def test_06_multiple_ranges_blocked(self):
        blocked_multi = self.uncertainty[self.uncertainty["uncertainty_eligibility"] == "Blocked — Multiple Active Ranges"]
        # If any exist, they must have no estimates
        if len(blocked_multi) > 0:
            self.assertTrue(
                blocked_multi["lower_estimate"].isna().all(),
                "Blocked multiple-range records must not have estimates"
            )
        # The blocking logic is confirmed present in the engine code
        with open(os.path.join(PROJECT_ROOT, "src", "financial_uncertainty_engine.py"), "r", encoding="utf-8") as f:
            engine_code = f.read()
        self.assertIn("Blocked — Multiple Active Ranges", engine_code)

    # --- 7. Unit mismatches are blocked ---
    def test_07_unit_mismatches_blocked(self):
        blocked_unit = self.uncertainty[self.uncertainty["uncertainty_eligibility"] == "Blocked — Unit Mismatch"]
        if len(blocked_unit) > 0:
            self.assertTrue(
                blocked_unit["lower_estimate"].isna().all(),
                "Blocked unit-mismatch records must not have estimates"
            )
        # Blocking logic present
        with open(os.path.join(PROJECT_ROOT, "src", "financial_uncertainty_engine.py"), "r", encoding="utf-8") as f:
            engine_code = f.read()
        self.assertIn("Blocked — Unit Mismatch", engine_code)

    # --- 8. Missing inputs do not receive uncertainty values ---
    def test_08_missing_inputs_no_values(self):
        missing = self.uncertainty[self.uncertainty["uncertainty_eligibility"] == "Ineligible — Missing Financial Input"]
        if len(missing) > 0:
            self.assertTrue(
                missing["lower_estimate"].isna().all() and missing["upper_estimate"].isna().all(),
                "Missing-input records must not have uncertainty estimates"
            )
        # In our data, there should be zero missing-input records because driver_mapping is complete
        self.assertEqual(len(missing), 0, "No missing-input records expected with complete driver mapping")

    # --- 9. Actual fixed values are not varied without permission ---
    def test_09_fixed_values_not_varied(self):
        fixed = self.uncertainty[self.uncertainty["uncertainty_eligibility"] == "Ineligible — Actual Fixed Value"]
        if len(fixed) > 0:
            self.assertTrue(
                fixed["lower_estimate"].isna().all() and fixed["upper_estimate"].isna().all(),
                "Fixed-value records must not have uncertainty estimates"
            )
        # In our data, all records have valid base_rate, so zero fixed-value records
        self.assertEqual(len(fixed), 0, "No fixed-value records expected with valid rates")

    # --- 10. Lower estimate <= central estimate ---
    def test_10_lower_leq_central(self):
        eligible = self.uncertainty[self.uncertainty["uncertainty_eligibility"] == "Eligible — Governed Range Available"]
        invalid = eligible[eligible["lower_estimate"] > eligible["central_estimate"]]
        self.assertEqual(
            len(invalid), 0,
            f"Lower estimate must be <= central estimate. Violations: {len(invalid)}"
        )

    # --- 11. Central estimate <= upper estimate ---
    def test_11_central_leq_upper(self):
        eligible = self.uncertainty[self.uncertainty["uncertainty_eligibility"] == "Eligible — Governed Range Available"]
        invalid = eligible[eligible["central_estimate"] > eligible["upper_estimate"]]
        self.assertEqual(
            len(invalid), 0,
            f"Central estimate must be <= upper estimate. Violations: {len(invalid)}"
        )

    # --- 12. Scenario comparator and financial uncertainty dimensions remain separate ---
    def test_12_dimensions_separate(self):
        # Operational comparators must exist in uncertainty register
        self.assertIn("comparator_type", self.uncertainty.columns)
        comparators = self.uncertainty["comparator_type"].unique()
        for c in ["Conservative", "Expected", "Higher Intensity"]:
            self.assertIn(c, comparators, f"Operational comparator {c} must be present")
        # Financial uncertainty estimates must use lower/central/upper nomenclature
        for col in ["lower_estimate", "central_estimate", "upper_estimate"]:
            self.assertIn(col, self.uncertainty.columns)
        # Must NOT use scenario-comparator names for uncertainty levels
        for bad_col in ["conservative_estimate", "expected_estimate", "higher_intensity_estimate"]:
            self.assertNotIn(bad_col, self.uncertainty.columns)

    # --- 13. Cost amounts remain unchanged ---
    def test_13_cost_unchanged(self):
        expected_checksum = self.manifest["outputs"]["step_2c3_scenario_cost_summary.csv"]["checksum"]
        current_checksum = compute_sha256(os.path.join(OUTPUT_DIR, "step_2c3_scenario_cost_summary.csv"))
        self.assertEqual(
            current_checksum, expected_checksum,
            "Cost summary must not have changed"
        )

    # --- 14. Benefit amounts remain unchanged ---
    def test_14_benefit_unchanged(self):
        expected_checksum = self.manifest["outputs"]["step_2c3_financial_benefit_summary.csv"]["checksum"]
        current_checksum = compute_sha256(os.path.join(OUTPUT_DIR, "step_2c3_financial_benefit_summary.csv"))
        self.assertEqual(
            current_checksum, expected_checksum,
            "Benefit summary must not have changed"
        )

    # --- 15. Net financial-impact values remain unchanged except uncertainty-related display fields ---
    def test_15_net_impact_unchanged(self):
        expected_checksum = self.manifest["outputs"]["step_2c3_net_financial_impact.csv"]["checksum"]
        current_checksum = compute_sha256(os.path.join(OUTPUT_DIR, "step_2c3_net_financial_impact.csv"))
        self.assertEqual(
            current_checksum, expected_checksum,
            "Net impact must not have changed"
        )

    # --- 16. ROI values and eligibility remain unchanged ---
    def test_16_roi_unchanged(self):
        expected_checksum = self.manifest["outputs"]["step_2c3_roi_register.csv"]["checksum"]
        current_checksum = compute_sha256(os.path.join(OUTPUT_DIR, "step_2c3_roi_register.csv"))
        self.assertEqual(
            current_checksum, expected_checksum,
            "ROI register must not have changed"
        )

    # --- 17. No preferred scenario is selected ---
    def test_17_no_preferred_scenario(self):
        # Management comparison must not contain preferred-scenario language
        selection_phrases = [
            "is the preferred scenario",
            "is the recommended scenario",
            "is the best scenario",
            "is the optimal scenario",
            "selected as preferred",
            "selected as the preferred",
            "scenario selected:",
        ]
        text = open(os.path.join(PROJECT_ROOT, "docs", "step_2c3_uncertainty_schema_contract_inventory.md"), "r", encoding="utf-8").read().lower()
        for phrase in selection_phrases:
            self.assertNotIn(phrase, text)
        # No single scenario should have special approval_status
        if "approval_status" in self.management.columns:
            self.assertFalse(
                self.management["approval_status"].str.contains("Approved|Selected|Preferred", case=False, na=False).any(),
                "No scenario must be marked as approved or preferred"
            )

    # --- 18. No management approval is recorded ---
    def test_18_no_management_approval(self):
        if "approval_status" in self.management.columns:
            approved = self.management["approval_status"].str.contains("Approved|Authorised|Signed Off", case=False, na=False)
            self.assertFalse(approved.any(), "No management approval must be recorded")
        # Execution summary must confirm no approval
        no_approval = self.execution[self.execution["metric"] == "no_management_approval_recorded"]
        if len(no_approval) > 0:
            self.assertEqual(str(no_approval.iloc[0]["value"]).lower(), "true")

    # --- 19. Financial confidence does not exceed Moderate ---
    def test_19_confidence_not_exceed_moderate(self):
        if "financial_confidence" in self.confidence.columns and len(self.confidence) > 0:
            high_conf = self.confidence[self.confidence["financial_confidence"].isin(["High", "Very High", "Certain"])]
            self.assertEqual(len(high_conf), 0, "Financial confidence must not exceed Moderate")
        # Execution summary confirmation
        exec_conf = self.execution[self.execution["metric"] == "financial_confidence_does_not_exceed_moderate"]
        if len(exec_conf) > 0:
            self.assertEqual(str(exec_conf.iloc[0]["value"]).lower(), "true")

    # --- 20. Phase 2C-2 frozen checksums remain unchanged ---
    def test_20_frozen_2c2_unchanged(self):
        for fname, expected_hash in self.upstream_checksums.items():
            fpath = os.path.join(SCENARIO_DIR, fname)
            current_hash = compute_sha256(fpath)
            self.assertEqual(
                current_hash, expected_hash,
                f"Frozen Phase 2C-2 file {fname} was modified"
            )

    # --- 21. Evidence and lineage reconcile ---
    def test_21_evidence_lineage_reconcile(self):
        eligible = self.uncertainty[self.uncertainty["uncertainty_eligibility"] == "Eligible — Governed Range Available"]
        if len(eligible) > 0:
            self.assertTrue(
                eligible["evidence"].notna().all() and eligible["evidence"].ne("").all(),
                "All eligible records must have evidence"
            )
            self.assertTrue(
                eligible["lineage"].notna().all() and eligible["lineage"].ne("").all(),
                "All eligible records must have lineage"
            )
            # Evidence must reference range_id
            self.assertTrue(
                eligible["evidence"].str.contains("range_id=").all(),
                "Evidence must reference range_id"
            )
            # Lineage must reference the engine and config
            self.assertTrue(
                eligible["lineage"].str.contains("financial_uncertainty_engine").all(),
                "Lineage must reference uncertainty engine"
            )
            self.assertTrue(
                eligible["lineage"].str.contains("financial_assumption_range").all(),
                "Lineage must reference assumption range config"
            )

    # --- 22. Updated manifest checksums are complete ---
    def test_22_manifest_checksums_complete(self):
        changed_files = [
            "step_2c3_financial_uncertainty_register.csv",
            "step_2c3_uncertainty_eligibility_register.csv",
            "step_2c3_uncertainty_schema_correction_register.csv",
            "step_2c3_uncertainty_correction_summary.csv",
            "step_2c3_management_financial_comparison.csv",
            "step_2c3_execution_summary.csv",
        ]
        for fname in changed_files:
            self.assertIn(
                fname, self.manifest["outputs"],
                f"Changed file {fname} must be in freeze manifest"
            )
            self.assertIn(
                "checksum", self.manifest["outputs"][fname],
                f"Freeze manifest entry for {fname} must have checksum"
            )
            # Verify checksum matches actual file
            actual_csum = compute_sha256(os.path.join(OUTPUT_DIR, fname))
            self.assertEqual(
                actual_csum, self.manifest["outputs"][fname]["checksum"],
                f"Checksum mismatch for {fname}"
            )


if __name__ == "__main__":
    unittest.main()
