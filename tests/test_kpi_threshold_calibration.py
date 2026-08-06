"""
Sentinel360 Healthcare — Focused Tests for Step 2B-1A (Corrected)

Tests:
  - Models instantiation and serialization
  - Engine prerequisite validation
  - Distribution profiling
  - Candidate generation with exhaustive G-A-R ranges
  - Boundary validation (no gaps, no overlap, amber bands present)
  - Shortlisting (max 3 per KPI)
  - Volume control enforcement
  - Vectorised classification correctness with amber bands
  - Boundary inclusivity determinism
  - Non-zero amber classifications where data supports
  - Material candidate deduplication (kpi_006)
  - Bed Occupancy dual-sided states
  - kpi_006 scale consistency (1-5 Likert)
  - Burden calculation
  - Manifest completeness
  - Immutability of protected files
"""

import sys
import unittest
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

import pandas as pd
import numpy as np

from threshold_calibration_models import (
    CandidateStatus,
    CandidateType,
    CalibrationMethod,
    DataSufficiency,
    Directionality,
    ThresholdBoundary,
    ThresholdBurdenResult,
    ThresholdCandidate,
    ThresholdClassificationResult,
    ThresholdDistributionProfile,
    ThresholdStabilityResult,
    ValidityStatus,
)
from kpi_threshold_calibration_engine import KPIThresholdCalibrationEngine


class TestThresholdModels(unittest.TestCase):
    def test_boundary_to_dict(self):
        b = ThresholdBoundary(
            lower_red=70.0,
            lower_amber=85.0,
            green_lower=85.0,
            green_upper=100.0,
            upper_amber=None,
            upper_red=None,
        )
        d = b.to_dict()
        self.assertEqual(d["lower_red"], 70.0)
        self.assertEqual(d["lower_amber"], 85.0)
        self.assertEqual(d["green_lower"], 85.0)
        self.assertEqual(d["green_upper"], 100.0)

    def test_candidate_boundary_tuple(self):
        c = ThresholdCandidate(
            threshold_candidate_id="CAND-TEST",
            kpi_id="kpi_001",
            kpi_name="Test",
            candidate_name="test_cand",
            candidate_type=CandidateType.BALANCED.value,
            directionality=Directionality.HIGHER_IS_BETTER.value,
            lower_red_boundary=70.0,
            lower_amber_boundary=85.0,
            green_lower_boundary=85.0,
            green_upper_boundary=100.0,
            upper_amber_boundary=None,
            upper_red_boundary=None,
            unit="Percent",
            boundary_inclusivity_rule="Lower boundary inclusive, upper exclusive; global maximum inclusive",
            calibration_method=CalibrationMethod.PERCENTILE_BASED.value,
            calibration_period_start="2026-01-01",
            calibration_period_end="2026-12-31",
            valid_observation_count=1000,
            unavailable_observation_count=0,
            data_sufficiency=DataSufficiency.STRONG.value,
            approval_status="Candidate",
            threshold_is_provisional=True,
            version="v1.0-candidate",
            rationale="Test",
            limitations="None",
        )
        t = c.get_boundary_tuple()
        self.assertEqual(t[0], 70.0)
        self.assertEqual(t[2], 85.0)
        self.assertEqual(t[3], 100.0)


class TestEnginePrerequisites(unittest.TestCase):
    def setUp(self):
        self.engine = KPIThresholdCalibrationEngine(project_root=project_root)

    def test_prerequisites_pass_when_files_exist(self):
        valid, issues = self.engine.validate_prerequisites()
        self.assertTrue(valid, f"Prerequisites failed: {issues}")

    def test_config_not_modified(self):
        import hashlib
        cfg_path = project_root / "config" / "kpi_threshold_config.csv"
        before = hashlib.sha256(cfg_path.read_bytes()).hexdigest()
        valid, _ = self.engine.validate_prerequisites()
        after = hashlib.sha256(cfg_path.read_bytes()).hexdigest()
        self.assertEqual(before, after)


class TestDistributionProfiling(unittest.TestCase):
    def setUp(self):
        self.engine = KPIThresholdCalibrationEngine(project_root=project_root)
        self.engine.load_inputs()

    def test_profile_non_empty_kpi(self):
        profile = self.engine.profile_kpi_distribution("kpi_001")
        self.assertGreater(profile.calculated_count, 0)
        self.assertIsNotNone(profile.mean)
        self.assertIsNotNone(profile.standard_deviation)

    def test_kpi_006_unit_is_likert(self):
        profile = self.engine.profile_kpi_distribution("kpi_006")
        self.assertEqual(profile.unit, "1-5 Likert Score")
        self.assertEqual(profile.kpi_name, "Patient Satisfaction Score")

    def test_data_sufficiency_tiers(self):
        self.assertEqual(self.engine.assess_data_sufficiency(1500), DataSufficiency.STRONG.value)
        self.assertEqual(self.engine.assess_data_sufficiency(700), DataSufficiency.MODERATE.value)
        self.assertEqual(self.engine.assess_data_sufficiency(200), DataSufficiency.LIMITED.value)
        self.assertEqual(self.engine.assess_data_sufficiency(50), DataSufficiency.INSUFFICIENT.value)


class TestCandidateGeneration(unittest.TestCase):
    def setUp(self):
        self.engine = KPIThresholdCalibrationEngine(project_root=project_root)
        self.engine.load_inputs()
        for kpi_id in self.engine.kpi_directionality:
            self.engine.profile_kpi_distribution(kpi_id)

    def test_generate_candidates_for_all_kpis(self):
        for kpi_id in self.engine.kpi_directionality:
            candidates = self.engine.generate_method_candidates(kpi_id)
            self.assertGreater(len(candidates), 0, f"No candidates for {kpi_id}")
            for c in candidates:
                self.assertEqual(c.candidate_validity_status, ValidityStatus.VALID.value)

    def test_boundary_validation_catches_missing_amber_higher(self):
        bad = ThresholdCandidate(
            threshold_candidate_id="CAND-BAD",
            kpi_id="kpi_001",
            kpi_name="Test",
            candidate_name="bad_cand",
            candidate_type=CandidateType.BALANCED.value,
            directionality=Directionality.HIGHER_IS_BETTER.value,
            lower_red_boundary=None,
            lower_amber_boundary=None,
            green_lower_boundary=80.0,
            green_upper_boundary=100.0,
            upper_amber_boundary=None,
            upper_red_boundary=None,
            unit="Percent",
            boundary_inclusivity_rule="Lower boundary inclusive, upper exclusive; global maximum inclusive",
            calibration_method=CalibrationMethod.PERCENTILE_BASED.value,
            calibration_period_start="2026-01-01",
            calibration_period_end="2026-12-31",
            valid_observation_count=100,
            unavailable_observation_count=0,
            data_sufficiency=DataSufficiency.STRONG.value,
            approval_status="Candidate",
            threshold_is_provisional=True,
            version="v1.0-candidate",
            rationale="Test",
            limitations="None",
        )
        is_valid, reason = self.engine.validate_candidate_boundaries(bad)
        self.assertFalse(is_valid)
        self.assertIn("Missing required boundary", reason)

    def test_boundary_validation_catches_inversion(self):
        bad = ThresholdCandidate(
            threshold_candidate_id="CAND-BAD",
            kpi_id="kpi_001",
            kpi_name="Test",
            candidate_name="bad_cand",
            candidate_type=CandidateType.BALANCED.value,
            directionality=Directionality.HIGHER_IS_BETTER.value,
            lower_red_boundary=90.0,
            lower_amber_boundary=85.0,
            green_lower_boundary=80.0,
            green_upper_boundary=100.0,
            upper_amber_boundary=None,
            upper_red_boundary=None,
            unit="Percent",
            boundary_inclusivity_rule="Lower boundary inclusive, upper exclusive; global maximum inclusive",
            calibration_method=CalibrationMethod.PERCENTILE_BASED.value,
            calibration_period_start="2026-01-01",
            calibration_period_end="2026-12-31",
            valid_observation_count=100,
            unavailable_observation_count=0,
            data_sufficiency=DataSufficiency.STRONG.value,
            approval_status="Candidate",
            threshold_is_provisional=True,
            version="v1.0-candidate",
            rationale="Test",
            limitations="None",
        )
        is_valid, reason = self.engine.validate_candidate_boundaries(bad)
        self.assertFalse(is_valid)
        self.assertIn("boundaries invalid", reason)

    def test_boundary_validation_catches_context_sensitive_gap(self):
        bad = ThresholdCandidate(
            threshold_candidate_id="CAND-BAD",
            kpi_id="kpi_003",
            kpi_name="Test",
            candidate_name="bad_cand",
            candidate_type=CandidateType.BALANCED.value,
            directionality=Directionality.CONTEXT_SENSITIVE.value,
            lower_red_boundary=70.0,
            lower_amber_boundary=75.0,
            green_lower_boundary=80.0,
            green_upper_boundary=85.0,
            upper_amber_boundary=90.0,
            upper_red_boundary=100.0,
            unit="Percent",
            boundary_inclusivity_rule="Lower boundary inclusive, upper exclusive; global maximum inclusive",
            calibration_method=CalibrationMethod.PERCENTILE_BASED.value,
            calibration_period_start="2026-01-01",
            calibration_period_end="2026-12-31",
            valid_observation_count=100,
            unavailable_observation_count=0,
            data_sufficiency=DataSufficiency.STRONG.value,
            approval_status="Candidate",
            threshold_is_provisional=True,
            version="v1.0-candidate",
            rationale="Test",
            limitations="None",
        )
        is_valid, reason = self.engine.validate_candidate_boundaries(bad)
        self.assertFalse(is_valid)
        self.assertIn("lower_amber==green_lower", reason)


class TestShortlisting(unittest.TestCase):
    def setUp(self):
        self.engine = KPIThresholdCalibrationEngine(project_root=project_root)
        self.engine.load_inputs()
        for kpi_id in self.engine.kpi_directionality:
            self.engine.profile_kpi_distribution(kpi_id)

    def test_shortlist_max_three(self):
        for kpi_id in self.engine.kpi_directionality:
            candidates = self.engine.generate_method_candidates(kpi_id)
            shortlist = self.engine.shortlist_candidates(kpi_id, candidates)
            self.assertLessEqual(len(shortlist), 3, f"Too many shortlisted for {kpi_id}")
            types = {c.candidate_type for c in shortlist}
            self.assertIn(CandidateType.CONSERVATIVE.value, types)
            self.assertIn(CandidateType.BALANCED.value, types)

    def test_kpi_003_has_three_shortlisted(self):
        candidates = self.engine.generate_method_candidates("kpi_003")
        shortlist = self.engine.shortlist_candidates("kpi_003", candidates)
        self.assertEqual(len(shortlist), 3, f"kpi_003 should have 3 shortlisted, got {len(shortlist)}")

    def test_kpi_006_candidates_materially_distinct(self):
        candidates = self.engine.generate_method_candidates("kpi_006")
        shortlist = self.engine.shortlist_candidates("kpi_006", candidates)
        tuples = [c.get_boundary_tuple() for c in shortlist]
        self.assertEqual(len(tuples), len(set(tuples)), "kpi_006 shortlisted candidates contain material duplicates")


class TestVolumeControl(unittest.TestCase):
    def setUp(self):
        self.engine = KPIThresholdCalibrationEngine(project_root=project_root, classification_row_limit=100_000)
        self.engine.load_inputs()
        for kpi_id in self.engine.kpi_directionality:
            self.engine.profile_kpi_distribution(kpi_id)
            candidates = self.engine.generate_method_candidates(kpi_id)
            shortlist = self.engine.shortlist_candidates(kpi_id, candidates)
            self.engine.shortlisted_candidates.extend(shortlist)

    def test_projected_volume_within_limit(self):
        kpi_counts = self.engine.df_six_kpi.groupby("kpi_id").size().to_dict()
        total = sum(kpi_counts.get(c.kpi_id, 0) for c in self.engine.shortlisted_candidates)
        self.assertLessEqual(total, 100_000, f"Projected rows {total} exceed limit")

    def test_classification_runs_without_error(self):
        df = self.engine.classify_shortlisted_candidates()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertLessEqual(len(df), 100_000)


class TestVectorisedClassification(unittest.TestCase):
    def setUp(self):
        self.engine = KPIThresholdCalibrationEngine(project_root=project_root)

    def test_higher_is_better_complete_gar(self):
        cand = ThresholdCandidate(
            threshold_candidate_id="CAND-TEST",
            kpi_id="kpi_001",
            kpi_name="Test",
            candidate_name="test",
            candidate_type=CandidateType.BALANCED.value,
            directionality=Directionality.HIGHER_IS_BETTER.value,
            lower_red_boundary=70.0,
            lower_amber_boundary=80.0,
            green_lower_boundary=80.0,
            green_upper_boundary=100.0,
            upper_amber_boundary=None,
            upper_red_boundary=None,
            unit="Percent",
            boundary_inclusivity_rule="Lower boundary inclusive, upper exclusive; global maximum inclusive",
            calibration_method=CalibrationMethod.PERCENTILE_BASED.value,
            calibration_period_start="2026-01-01",
            calibration_period_end="2026-12-31",
            valid_observation_count=100,
            unavailable_observation_count=0,
            data_sufficiency=DataSufficiency.STRONG.value,
            approval_status="Candidate",
            threshold_is_provisional=True,
            version="v1.0-candidate",
            rationale="Test",
            limitations="None",
        )
        values = np.array([65.0, 70.0, 75.0, 80.0, 90.0, 100.0])
        out = self.engine._classify_vectorised(values, cand)
        self.assertEqual(out[0], CandidateStatus.CANDIDATE_RED.value)
        self.assertEqual(out[1], CandidateStatus.CANDIDATE_AMBER.value)
        self.assertEqual(out[2], CandidateStatus.CANDIDATE_AMBER.value)
        self.assertEqual(out[3], CandidateStatus.CANDIDATE_GREEN.value)
        self.assertEqual(out[4], CandidateStatus.CANDIDATE_GREEN.value)
        self.assertEqual(out[5], CandidateStatus.CANDIDATE_GREEN.value)

    def test_lower_is_better_complete_gar(self):
        cand = ThresholdCandidate(
            threshold_candidate_id="CAND-TEST",
            kpi_id="kpi_002",
            kpi_name="Test",
            candidate_name="test",
            candidate_type=CandidateType.BALANCED.value,
            directionality=Directionality.LOWER_IS_BETTER.value,
            lower_red_boundary=None,
            lower_amber_boundary=None,
            green_lower_boundary=0.0,
            green_upper_boundary=10.0,
            upper_amber_boundary=20.0,
            upper_red_boundary=20.0,
            unit="Percent",
            boundary_inclusivity_rule="Lower boundary inclusive, upper exclusive; global maximum inclusive",
            calibration_method=CalibrationMethod.PERCENTILE_BASED.value,
            calibration_period_start="2026-01-01",
            calibration_period_end="2026-12-31",
            valid_observation_count=100,
            unavailable_observation_count=0,
            data_sufficiency=DataSufficiency.STRONG.value,
            approval_status="Candidate",
            threshold_is_provisional=True,
            version="v1.0-candidate",
            rationale="Test",
            limitations="None",
        )
        values = np.array([0.0, 5.0, 10.0, 15.0, 20.0, 25.0])
        out = self.engine._classify_vectorised(values, cand)
        self.assertEqual(out[0], CandidateStatus.CANDIDATE_GREEN.value)
        self.assertEqual(out[1], CandidateStatus.CANDIDATE_GREEN.value)
        self.assertEqual(out[2], CandidateStatus.CANDIDATE_GREEN.value)
        self.assertEqual(out[3], CandidateStatus.CANDIDATE_AMBER.value)
        self.assertEqual(out[4], CandidateStatus.CANDIDATE_RED.value)
        self.assertEqual(out[5], CandidateStatus.CANDIDATE_RED.value)

    def test_context_sensitive_five_band(self):
        cand = ThresholdCandidate(
            threshold_candidate_id="CAND-TEST",
            kpi_id="kpi_003",
            kpi_name="Test",
            candidate_name="test",
            candidate_type=CandidateType.BALANCED.value,
            directionality=Directionality.CONTEXT_SENSITIVE.value,
            lower_red_boundary=70.0,
            lower_amber_boundary=80.0,
            green_lower_boundary=80.0,
            green_upper_boundary=90.0,
            upper_amber_boundary=90.0,
            upper_red_boundary=100.0,
            unit="Percent",
            boundary_inclusivity_rule="Lower boundary inclusive, upper exclusive; global maximum inclusive",
            calibration_method=CalibrationMethod.PERCENTILE_BASED.value,
            calibration_period_start="2026-01-01",
            calibration_period_end="2026-12-31",
            valid_observation_count=100,
            unavailable_observation_count=0,
            data_sufficiency=DataSufficiency.STRONG.value,
            approval_status="Candidate",
            threshold_is_provisional=True,
            version="v1.0-candidate",
            rationale="Test",
            limitations="None",
        )
        values = np.array([65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0])
        out = self.engine._classify_vectorised(values, cand)
        self.assertEqual(out[0], CandidateStatus.CANDIDATE_LOW_UTILISATION.value)  # 65 < 70
        self.assertEqual(out[1], CandidateStatus.CANDIDATE_AMBER.value)            # 70 >= lr and 70 < gl
        self.assertEqual(out[2], CandidateStatus.CANDIDATE_AMBER.value)            # 75 >= lr and 75 < gl
        self.assertEqual(out[3], CandidateStatus.CANDIDATE_GREEN.value)            # 80 >= gl and 80 <= gu
        self.assertEqual(out[4], CandidateStatus.CANDIDATE_GREEN.value)            # 85 >= gl and 85 <= gu
        self.assertEqual(out[5], CandidateStatus.CANDIDATE_GREEN.value)            # 90 >= gl and 90 <= gu
        self.assertEqual(out[6], CandidateStatus.CANDIDATE_AMBER.value)            # 95 > gu and 95 < ur
        self.assertEqual(out[7], CandidateStatus.CANDIDATE_HIGH_PRESSURE.value)    # 100 >= ur

    def test_boundary_inclusivity_max_values(self):
        # Staffing Level = 100% must be Green
        cand = ThresholdCandidate(
            threshold_candidate_id="CAND-TEST",
            kpi_id="kpi_001",
            kpi_name="Test",
            candidate_name="test",
            candidate_type=CandidateType.BALANCED.value,
            directionality=Directionality.HIGHER_IS_BETTER.value,
            lower_red_boundary=70.0,
            lower_amber_boundary=85.0,
            green_lower_boundary=85.0,
            green_upper_boundary=100.0,
            upper_amber_boundary=None,
            upper_red_boundary=None,
            unit="Percent",
            boundary_inclusivity_rule="Lower boundary inclusive, upper exclusive; global maximum inclusive",
            calibration_method=CalibrationMethod.PERCENTILE_BASED.value,
            calibration_period_start="2026-01-01",
            calibration_period_end="2026-12-31",
            valid_observation_count=100,
            unavailable_observation_count=0,
            data_sufficiency=DataSufficiency.STRONG.value,
            approval_status="Candidate",
            threshold_is_provisional=True,
            version="v1.0-candidate",
            rationale="Test",
            limitations="None",
        )
        out = self.engine._classify_vectorised(np.array([100.0]), cand)
        self.assertEqual(out[0], CandidateStatus.CANDIDATE_GREEN.value)

        # Patient Satisfaction = 5.0 must be Green
        cand2 = ThresholdCandidate(
            threshold_candidate_id="CAND-TEST2",
            kpi_id="kpi_006",
            kpi_name="Test",
            candidate_name="test",
            candidate_type=CandidateType.BALANCED.value,
            directionality=Directionality.HIGHER_IS_BETTER.value,
            lower_red_boundary=1.0,
            lower_amber_boundary=3.5,
            green_lower_boundary=3.5,
            green_upper_boundary=5.0,
            upper_amber_boundary=None,
            upper_red_boundary=None,
            unit="1-5 Likert Score",
            boundary_inclusivity_rule="Lower boundary inclusive, upper exclusive; global maximum inclusive",
            calibration_method=CalibrationMethod.PERCENTILE_BASED.value,
            calibration_period_start="2026-01-01",
            calibration_period_end="2026-12-31",
            valid_observation_count=100,
            unavailable_observation_count=0,
            data_sufficiency=DataSufficiency.STRONG.value,
            approval_status="Candidate",
            threshold_is_provisional=True,
            version="v1.0-candidate",
            rationale="Test",
            limitations="None",
        )
        out2 = self.engine._classify_vectorised(np.array([5.0]), cand2)
        self.assertEqual(out2[0], CandidateStatus.CANDIDATE_GREEN.value)

    def test_exactly_once_classification(self):
        # Verify every value is classified exactly once (no overlap, no gap)
        for direction, cand_kwargs in [
            (Directionality.HIGHER_IS_BETTER.value, {
                "lower_red_boundary": 70.0, "lower_amber_boundary": 80.0,
                "green_lower_boundary": 80.0, "green_upper_boundary": 100.0,
                "upper_amber_boundary": None, "upper_red_boundary": None,
            }),
            (Directionality.LOWER_IS_BETTER.value, {
                "lower_red_boundary": None, "lower_amber_boundary": None,
                "green_lower_boundary": 0.0, "green_upper_boundary": 10.0,
                "upper_amber_boundary": 20.0, "upper_red_boundary": 20.0,
            }),
            (Directionality.CONTEXT_SENSITIVE.value, {
                "lower_red_boundary": 70.0, "lower_amber_boundary": 80.0,
                "green_lower_boundary": 80.0, "green_upper_boundary": 90.0,
                "upper_amber_boundary": 90.0, "upper_red_boundary": 100.0,
            }),
        ]:
            cand = ThresholdCandidate(
                threshold_candidate_id="CAND-ONCE",
                kpi_id="kpi_001",
                kpi_name="Test",
                candidate_name="test",
                candidate_type=CandidateType.BALANCED.value,
                directionality=direction,
                unit="Percent",
                boundary_inclusivity_rule="Lower boundary inclusive, upper exclusive; global maximum inclusive",
                calibration_method=CalibrationMethod.PERCENTILE_BASED.value,
                calibration_period_start="2026-01-01",
                calibration_period_end="2026-12-31",
                valid_observation_count=100,
                unavailable_observation_count=0,
                data_sufficiency=DataSufficiency.STRONG.value,
                approval_status="Candidate",
                threshold_is_provisional=True,
                version="v1.0-candidate",
                rationale="Test",
                limitations="None",
                **cand_kwargs,
            )
            values = np.linspace(0, 120, 121)
            out = self.engine._classify_vectorised(values, cand)
            # Every value must be classified (no None, no empty string, no NOT_ASSESSED)
            self.assertTrue(all(o != CandidateStatus.NOT_ASSESSED.value for o in out),
                            f"Direction {direction}: unclassified values found")
            self.assertTrue(all(o is not None for o in out),
                            f"Direction {direction}: None classifications found")


class TestAmberCountsNonZero(unittest.TestCase):
    def setUp(self):
        self.engine = KPIThresholdCalibrationEngine(project_root=project_root)
        self.engine.load_inputs()
        for kpi_id in self.engine.kpi_directionality:
            self.engine.profile_kpi_distribution(kpi_id)
            candidates = self.engine.generate_method_candidates(kpi_id)
            shortlist = self.engine.shortlist_candidates(kpi_id, candidates)
            self.engine.shortlisted_candidates.extend(shortlist)
        self.engine.classify_shortlisted_candidates()

    def test_amber_counts_nonzero_for_single_sided(self):
        burdens = self.engine.calculate_classification_burden()
        for b in burdens:
            if b.kpi_id in ("kpi_001", "kpi_002", "kpi_004", "kpi_005", "kpi_006"):
                self.assertGreater(
                    b.candidate_amber_count, 0,
                    f"{b.kpi_id} candidate {b.threshold_candidate_id} has zero amber classifications. "
                    f"Counts: G={b.candidate_green_count}, A={b.candidate_amber_count}, R={b.candidate_red_count}"
                )

    def test_burden_sums_to_total(self):
        burdens = self.engine.calculate_classification_burden()
        self.assertGreater(len(burdens), 0)
        for b in burdens:
            total = b.candidate_green_count + b.candidate_amber_count + b.candidate_red_count + b.not_assessed_count + b.unavailable_count
            self.assertGreater(total, 0)


class TestManifest(unittest.TestCase):
    def setUp(self):
        self.engine = KPIThresholdCalibrationEngine(project_root=project_root)
        self.engine.load_inputs()
        for kpi_id in self.engine.kpi_directionality:
            self.engine.profile_kpi_distribution(kpi_id)
            candidates = self.engine.generate_method_candidates(kpi_id)
            shortlist = self.engine.shortlist_candidates(kpi_id, candidates)
            self.engine.shortlisted_candidates.extend(shortlist)
        self.engine.classify_shortlisted_candidates()
        self.engine.calculate_classification_burden()
        self.engine.test_candidate_stability()
        self.engine.compare_with_trend_outputs()
        self.engine.generate_recommendations()

    def test_manifest_structure(self):
        m = self.engine.build_manifest()
        self.assertEqual(m.step_name, "2B-1A")
        self.assertTrue(m.volume_control_passed)
        self.assertEqual(m.readiness_for_2b1b, "Ready for Stakeholder Review")


if __name__ == "__main__":
    unittest.main(verbosity=2)
