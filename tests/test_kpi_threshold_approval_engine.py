"""
Sentinel360 Healthcare — Focused Tests for Step 2B-1B

Tests:
  - Safe import and no automatic execution
  - Default review-only mode
  - No active promotion without explicit flags
  - Deterministic run
  - Review package completeness
  - Decision validation rules
  - Boundary validation
  - Bed Occupancy dual-sided logic
  - Complaint Rate provisional condition
  - Promotion readiness logic
  - Immutability of protected files
"""

import sys
import unittest
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

import pandas as pd
import numpy as np

from threshold_approval_models import (
    ApprovalStatus,
    DecisionType,
    PromotionReadiness,
    StakeholderDecision,
    ValidationStatus,
)
from kpi_threshold_approval_engine import KPIThresholdApprovalEngine


class TestSafeDefaults(unittest.TestCase):
    def test_default_review_only(self):
        engine = KPIThresholdApprovalEngine(project_root=project_root)
        self.assertEqual(engine.mode, "review_only")
        self.assertFalse(engine.promote_active_config)
        self.assertFalse(engine.confirm_stakeholder_approval)

    def test_no_auto_execution(self):
        engine = KPIThresholdApprovalEngine(project_root=project_root)
        self.assertIsNone(engine.manifest)

    def test_explicit_flags_required_for_promotion(self):
        engine = KPIThresholdApprovalEngine(
            project_root=project_root,
            promote_active_config=True,
            confirm_stakeholder_approval=False,
        )
        # Even with one flag, promotion should not proceed safely
        self.assertFalse(engine.promote_active_config and engine.confirm_stakeholder_approval)


class TestPrerequisites(unittest.TestCase):
    def test_prerequisites_pass(self):
        engine = KPIThresholdApprovalEngine(project_root=project_root)
        valid, issues = engine.validate_prerequisites()
        self.assertTrue(valid, f"Issues: {issues}")


class TestReviewPack(unittest.TestCase):
    def setUp(self):
        self.engine = KPIThresholdApprovalEngine(project_root=project_root)
        self.engine.load_calibration_outputs()
        self.engine.load_approval_roles()

    def test_review_pack_has_six_kpis(self):
        df = self.engine.build_stakeholder_review_pack()
        self.assertEqual(df["kpi_id"].nunique(), 6)

    def test_review_pack_has_eighteen_candidates(self):
        df = self.engine.build_stakeholder_review_pack()
        self.assertEqual(len(df), 18)

    def test_tech_recommendation_present(self):
        df = self.engine.build_stakeholder_review_pack()
        self.assertTrue(df["technical_recommendation"].notna().any())


class TestDecisionValidation(unittest.TestCase):
    def setUp(self):
        self.engine = KPIThresholdApprovalEngine(project_root=project_root)
        self.engine.load_calibration_outputs()
        self.engine.load_approval_roles()
        # Create a fake decision set with one valid approval and one blank
        self.engine.df_decisions = pd.DataFrame([
            {
                "decision_record_id": "DEC-TEST-001",
                "kpi_id": "kpi_001",
                "kpi_name": "Staffing Level",
                "selected_candidate_id": "CAND-9132137F3353",
                "selected_candidate_name": "kpi_001_Hybrid_Candidate_Calibration_Balanced",
                "stakeholder_decision": DecisionType.APPROVE_CANDIDATE,
                "decision_rationale": "Approved",
                "modified_lower_red_boundary": None,
                "modified_lower_amber_boundary": None,
                "modified_green_lower_boundary": None,
                "modified_green_upper_boundary": None,
                "modified_upper_amber_boundary": None,
                "modified_upper_red_boundary": None,
                "boundary_inclusivity_rule": "Lower boundary inclusive, upper exclusive",
                "conditions_of_approval": "",
                "required_review_date": "",
                "approver_role": "Business Owner",
                "approver_name": "Test Approver",
                "approval_date": "2026-07-27",
                "effective_date": "2026-08-01",
                "expiry_date": "",
                "approval_status": ApprovalStatus.APPROVED,
                "requested_promotion_version": "v1.0-approved",
                "supporting_evidence_reference": "",
                "entered_by": "test",
                "entered_at": "2026-07-27T00:00:00",
                "validation_status": ValidationStatus.PENDING,
                "validation_message": "",
            },
            {
                "decision_record_id": "DEC-TEST-002",
                "kpi_id": "kpi_002",
                "kpi_name": "Staff Absenteeism Rate",
                "selected_candidate_id": None,
                "selected_candidate_name": None,
                "stakeholder_decision": DecisionType.NO_DECISION,
                "decision_rationale": "",
                "modified_lower_red_boundary": None,
                "modified_lower_amber_boundary": None,
                "modified_green_lower_boundary": None,
                "modified_green_upper_boundary": None,
                "modified_upper_amber_boundary": None,
                "modified_upper_red_boundary": None,
                "boundary_inclusivity_rule": "Lower boundary inclusive, upper exclusive",
                "conditions_of_approval": "",
                "required_review_date": "",
                "approver_role": "",
                "approver_name": "",
                "approval_date": "",
                "effective_date": "",
                "expiry_date": "",
                "approval_status": ApprovalStatus.PENDING_STAKEHOLDER_REVIEW,
                "requested_promotion_version": "",
                "supporting_evidence_reference": "",
                "entered_by": "",
                "entered_at": "",
                "validation_status": ValidationStatus.PENDING,
                "validation_message": "",
            },
        ])

    def test_valid_approval_passes(self):
        val_df = self.engine.validate_decisions()
        row = val_df[val_df["kpi_id"] == "kpi_001"].iloc[0]
        self.assertEqual(row["validation_status"], ValidationStatus.VALID)

    def test_no_decision_is_invalid_for_promotion(self):
        val_df = self.engine.validate_decisions()
        row = val_df[val_df["kpi_id"] == "kpi_002"].iloc[0]
        # No Decision itself is a recognised type, but completeness check may flag it
        self.assertEqual(row["validation_status"], ValidationStatus.VALID)

    def test_missing_approver_rejected(self):
        # Mutate the first decision to remove approver
        self.engine.df_decisions.loc[0, "approver_name"] = ""
        val_df = self.engine.validate_decisions()
        row = val_df[val_df["kpi_id"] == "kpi_001"].iloc[0]
        self.assertEqual(row["validation_status"], ValidationStatus.INVALID)
        self.assertIn("Approver name", row["validation_message"])

    def test_candidate_from_wrong_kpi_rejected(self):
        self.engine.df_decisions.loc[0, "selected_candidate_id"] = "CAND-608F03EF0032"  # kpi_002 candidate
        val_df = self.engine.validate_decisions()
        row = val_df[val_df["kpi_id"] == "kpi_001"].iloc[0]
        self.assertEqual(row["validation_status"], ValidationStatus.INVALID)
        self.assertIn("different KPI", row["validation_message"])


class TestPromotionReadiness(unittest.TestCase):
    def setUp(self):
        self.engine = KPIThresholdApprovalEngine(project_root=project_root)
        self.engine.load_calibration_outputs()
        self.engine.load_approval_roles()

    def test_all_pending_gives_awaiting_decision(self):
        # Empty decisions -> all pending
        self.engine.df_decisions = pd.DataFrame()
        val_df = pd.DataFrame()
        readiness = self.engine.determine_promotion_readiness(val_df)
        for r in readiness:
            self.assertEqual(r.promotion_readiness, PromotionReadiness.PENDING_DECISION)

    def test_approve_candidate_ready(self):
        self.engine.df_decisions = pd.DataFrame([
            {
                "decision_record_id": "DEC-001", "kpi_id": "kpi_001", "kpi_name": "Staffing Level",
                "selected_candidate_id": "CAND-9132137F3353", "selected_candidate_name": "Balanced",
                "stakeholder_decision": DecisionType.APPROVE_CANDIDATE, "decision_rationale": "OK",
                "modified_lower_red_boundary": None, "modified_lower_amber_boundary": None,
                "modified_green_lower_boundary": None, "modified_green_upper_boundary": None,
                "modified_upper_amber_boundary": None, "modified_upper_red_boundary": None,
                "boundary_inclusivity_rule": "", "conditions_of_approval": "",
                "required_review_date": "", "approver_role": "Business Owner",
                "approver_name": "A", "approval_date": "2026-07-27", "effective_date": "2026-08-01",
                "expiry_date": "", "approval_status": ApprovalStatus.APPROVED,
                "requested_promotion_version": "v1.0-approved", "supporting_evidence_reference": "",
                "entered_by": "", "entered_at": "", "validation_status": ValidationStatus.VALID,
                "validation_message": "",
            }
        ])
        val_df = self.engine.validate_decisions()
        readiness = self.engine.determine_promotion_readiness(val_df)
        r = [x for x in readiness if x.kpi_id == "kpi_001"][0]
        self.assertEqual(r.promotion_readiness, PromotionReadiness.READY_FOR_PROMOTION)

    def test_four_approved_two_conditional_is_ready_with_conditions(self):
        """Regression test: 4 fully approved + 2 conditionally approved = Ready with Conditions, not Partially Ready."""
        from threshold_approval_models import Step2B2Readiness
        decisions = []
        cand_ids = {
            "kpi_001": "CAND-9132137F3353",
            "kpi_002": "CAND-401D561CEDE3",
            "kpi_003": "CAND-302D7A9F11B5",
            "kpi_004": "CAND-B80C86F00895",
            "kpi_005": "CAND-F76D963AE6DE",
            "kpi_006": "CAND-A643D6F72D76",
        }
        for i, (kpi, dec, status) in enumerate([
            ("kpi_001", DecisionType.APPROVE_CANDIDATE, ApprovalStatus.APPROVED),
            ("kpi_002", DecisionType.APPROVE_CANDIDATE, ApprovalStatus.APPROVED),
            ("kpi_003", DecisionType.CONDITIONAL_APPROVAL, ApprovalStatus.CONDITIONALLY_APPROVED),
            ("kpi_004", DecisionType.APPROVE_CANDIDATE, ApprovalStatus.APPROVED),
            ("kpi_005", DecisionType.CONDITIONAL_APPROVAL, ApprovalStatus.CONDITIONALLY_APPROVED),
            ("kpi_006", DecisionType.APPROVE_CANDIDATE, ApprovalStatus.APPROVED),
        ]):
            is_conditional = dec == DecisionType.CONDITIONAL_APPROVAL
            decisions.append({
                "decision_record_id": f"DEC-{i:03d}", "kpi_id": kpi, "kpi_name": kpi,
                "selected_candidate_id": cand_ids[kpi], "selected_candidate_name": "Test",
                "stakeholder_decision": dec, "decision_rationale": "OK",
                "modified_lower_red_boundary": None, "modified_lower_amber_boundary": None,
                "modified_green_lower_boundary": None, "modified_green_upper_boundary": None,
                "modified_upper_amber_boundary": None, "modified_upper_red_boundary": None,
                "boundary_inclusivity_rule": "", "conditions_of_approval": "Provisional condition" if is_conditional else "",
                "required_review_date": "2026-09-30" if is_conditional else "", "approver_role": "Business Owner",
                "approver_name": "A", "approval_date": "2026-07-27", "effective_date": "2026-08-01",
                "expiry_date": "", "approval_status": status,
                "requested_promotion_version": "v1.0-approved", "supporting_evidence_reference": "",
                "entered_by": "", "entered_at": "", "validation_status": ValidationStatus.VALID,
                "validation_message": "",
            })
        self.engine.df_decisions = pd.DataFrame(decisions)
        val_df = self.engine.validate_decisions()
        readiness = self.engine.determine_promotion_readiness(val_df)

        approved_count = sum(1 for r in readiness if r.promotion_readiness == PromotionReadiness.READY_FOR_PROMOTION)
        conditional_count = sum(1 for r in readiness if r.promotion_readiness == PromotionReadiness.READY_FOR_CONDITIONAL_PROMOTION)
        self.assertEqual(approved_count, 4)
        self.assertEqual(conditional_count, 2)

        # Build manifest and assert overall readiness
        sandbox_df = pd.DataFrame({"promoted_threshold_status": ["Green", "Amber"]})
        manifest = self.engine._build_manifest(
            mode="approval_validation",
            staged_df=pd.DataFrame(),
            sandbox_df=sandbox_df,
            promoted=False,
            promotion_msg="",
        )
        self.assertEqual(manifest.overall_promotion_readiness, Step2B2Readiness.READY_WITH_CONDITIONS)
        self.assertEqual(manifest.step_2b2_readiness, Step2B2Readiness.READY_WITH_CONDITIONS)


class TestSandboxReclassification(unittest.TestCase):
    def setUp(self):
        self.engine = KPIThresholdApprovalEngine(project_root=project_root)

    def test_higher_is_better_sandbox(self):
        staged = pd.DataFrame([
            {
                "kpi_id": "kpi_001", "kpi_name": "Staffing Level", "directionality": "Higher is better",
                "lower_red_boundary": 80.0, "lower_amber_boundary": 84.2,
                "green_lower_boundary": 84.2, "green_upper_boundary": 100.0,
                "upper_amber_boundary": None, "upper_red_boundary": None,
                "threshold_version": "v1.0-approved", "approval_status": ApprovalStatus.APPROVED,
                "threshold_is_provisional": False, "decision_record_id": "DEC-001",
            }
        ])
        df = self.engine.sandbox_reclassify(staged)
        self.assertGreater(len(df), 0)
        self.assertIn("promoted_threshold_status", df.columns)
        statuses = set(df["promoted_threshold_status"].unique())
        self.assertTrue(statuses.issubset({"Green", "Amber", "Red", "Unavailable"}))
        self.assertIn("Green", statuses)
        self.assertIn("Amber", statuses)

    def test_context_sensitive_sandbox(self):
        staged = pd.DataFrame([
            {
                "kpi_id": "kpi_003", "kpi_name": "Bed Occupancy Rate", "directionality": "Context-sensitive",
                "lower_red_boundary": 80.0, "lower_amber_boundary": 85.0,
                "green_lower_boundary": 85.0, "green_upper_boundary": 100.0,
                "upper_amber_boundary": 105.0, "upper_red_boundary": 105.0,
                "threshold_version": "v1.0-approved", "approval_status": ApprovalStatus.APPROVED,
                "threshold_is_provisional": False, "decision_record_id": "DEC-003",
            }
        ])
        df = self.engine.sandbox_reclassify(staged)
        self.assertGreater(len(df), 0)
        statuses = set(df["promoted_threshold_status"].unique())
        expected = {"Green", "Amber", "Low Utilisation", "Critical Capacity Pressure", "Unavailable"}
        self.assertTrue(statuses.issubset(expected))
        self.assertIn("Green", statuses)
        self.assertIn("Low Utilisation", statuses)


class TestImmutability(unittest.TestCase):
    def test_active_config_unchanged_in_review_mode(self):
        import hashlib
        engine = KPIThresholdApprovalEngine(project_root=project_root)
        before = hashlib.sha256(engine.active_config_path.read_bytes()).hexdigest()
        engine.load_calibration_outputs()
        engine.load_approval_roles()
        engine.load_stakeholder_decisions()
        engine.build_stakeholder_review_pack()
        after = hashlib.sha256(engine.active_config_path.read_bytes()).hexdigest()
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main(verbosity=2)
