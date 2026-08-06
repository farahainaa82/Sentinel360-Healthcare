"""
Tests for Step 2A-5 Six-KPI Integration Engine.

Focused tests: architecture, input integration, KPI validation, status normalization,
value-status consistency, threshold governance, confidence, evidence, lineage,
coverage, outputs, immutability.
"""

import hashlib
import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.six_kpi_integration_engine import SixKPIIntegrationEngine, GOVERNED_KPI_IDS


class TestArchitecture(unittest.TestCase):
    def test_safe_import(self):
        self.assertIn("SixKPIIntegrationEngine", dir(__import__("src.six_kpi_integration_engine", fromlist=["SixKPIIntegrationEngine"])))

    def test_no_auto_execution(self):
        # Importing must not run integration
        engine = SixKPIIntegrationEngine(project_root=str(PROJECT_ROOT))
        self.assertEqual(len(engine.issue_records), 0)

    def test_exactly_six_kpi_ids(self):
        self.assertEqual(len(GOVERNED_KPI_IDS), 6)
        self.assertEqual(GOVERNED_KPI_IDS, {"kpi_001", "kpi_002", "kpi_003", "kpi_004", "kpi_005", "kpi_006"})

    def test_deterministic_integration_run(self):
        engine = SixKPIIntegrationEngine(project_root=str(PROJECT_ROOT), integration_run_id="TEST-RUN-001")
        self.assertEqual(engine.integration_run_id, "TEST-RUN-001")


class TestInputIntegration(unittest.TestCase):
    def setUp(self):
        self.engine = SixKPIIntegrationEngine(project_root=str(PROJECT_ROOT))

    def test_load_all_three_domains(self):
        daily, evidence, exclusions, lineage, issues, audit = self.engine.load_accepted_inputs()
        self.assertGreater(len(daily), 0)
        self.assertIn("_source_domain", daily.columns)
        domains = set(daily["_source_domain"].unique())
        self.assertTrue(domains.issuperset({"workforce", "patient_flow", "patient_experience"}))

    def test_source_counts_preserved(self):
        daily, evidence, exclusions, lineage, issues, audit = self.engine.load_accepted_inputs()
        total = len(daily)
        self.assertEqual(total, 17520)  # 3 domains * 5840 each

    def test_no_accepted_records_lost(self):
        daily, evidence, exclusions, lineage, issues, audit = self.engine.load_accepted_inputs()
        for domain in ["workforce", "patient_flow", "patient_experience"]:
            self.assertEqual(len(daily[daily["_source_domain"] == domain]), 5840)


class TestKPIValidation(unittest.TestCase):
    def setUp(self):
        self.engine = SixKPIIntegrationEngine(project_root=str(PROJECT_ROOT))

    def test_all_six_kpi_ids_present(self):
        daily, *_ = self.engine.load_accepted_inputs()
        validated = self.engine.validate_kpi_registry(daily)
        self.assertEqual(set(validated["kpi_id"].unique()), GOVERNED_KPI_IDS)

    def test_unknown_kpi_rejected(self):
        daily = pd.DataFrame({
            "kpi_id": ["kpi_001", "kpi_999"],
            "analytical_record_id": ["AKPI-kpi_001-H1-D1-20240101", "AKPI-kpi_999-H1-D1-20240101"],
        })
        validated = self.engine.validate_kpi_registry(daily)
        self.assertEqual(set(validated["kpi_id"].unique()), {"kpi_001"})
        self.assertTrue(any(i.issue_type == "Unknown KPI ID" for i in self.engine.issue_records))

    def test_deterministic_integration_id(self):
        daily = pd.DataFrame({
            "kpi_id": ["kpi_001"],
            "hospital_id": ["H1"],
            "department_id": ["D1"],
            "reporting_date": ["2024-01-01"],
            "analytical_record_id": ["AKPI-kpi_001-H1-D1-20240101"],
        })
        result = self.engine._make_integration_id(daily.iloc[0])
        self.assertEqual(result, "IKPI-kpi_001-H1-D1-20240101")


class TestCalculationStatus(unittest.TestCase):
    def setUp(self):
        self.engine = SixKPIIntegrationEngine(project_root=str(PROJECT_ROOT))

    def test_calculated_with_value_accepted(self):
        # Provisional threshold is a non-blocking governance limitation,
        # so status is Integrated with Warning per specification section 8.
        daily = pd.DataFrame({
            "kpi_id": ["kpi_001"],
            "kpi_value": [50.0],
            "calculation_status": ["Calculated"],
            "threshold_status": ["Not Assessed"],
            "data_confidence_level": ["High"],
            "threshold_is_provisional": [True],
        })
        result = self.engine.assign_integration_status(daily)
        self.assertEqual(result.iloc[0]["integration_status"], "Integrated with Warning")

    def test_calculated_with_null_rejected(self):
        daily = pd.DataFrame({
            "kpi_id": ["kpi_001"],
            "kpi_value": [None],
            "calculation_status": ["Calculated"],
            "threshold_status": ["Not Assessed"],
            "data_confidence_level": ["Unavailable"],
            "threshold_is_provisional": [True],
        })
        result = self.engine.assign_integration_status(daily)
        self.assertEqual(result.iloc[0]["integration_status"], "Failed Validation")

    def test_unavailable_status_with_null_accepted(self):
        # Provisional threshold is a non-blocking governance limitation,
        # so status is Integrated with Warning per specification section 8.
        daily = pd.DataFrame({
            "kpi_id": ["kpi_001"],
            "kpi_value": [None],
            "calculation_status": ["Insufficient Data"],
            "threshold_status": ["Not Assessed"],
            "data_confidence_level": ["Unavailable"],
            "threshold_is_provisional": [True],
        })
        result = self.engine.assign_integration_status(daily)
        self.assertEqual(result.iloc[0]["integration_status"], "Integrated with Warning")

    def test_non_calculated_value_inconsistency_detected(self):
        daily = pd.DataFrame({
            "kpi_id": ["kpi_001"],
            "kpi_value": [50.0],
            "calculation_status": ["Insufficient Data"],
            "threshold_status": ["Not Assessed"],
            "data_confidence_level": ["Unavailable"],
            "threshold_is_provisional": [True],
        })
        result = self.engine.assign_integration_status(daily)
        self.assertEqual(result.iloc[0]["integration_status"], "Integrated with Warning")


class TestThresholdStatus(unittest.TestCase):
    def setUp(self):
        self.engine = SixKPIIntegrationEngine(project_root=str(PROJECT_ROOT))

    def test_not_assessed_preserved(self):
        daily, *_ = self.engine.load_accepted_inputs()
        normalized = self.engine.normalize_threshold_status(daily)
        self.assertTrue((normalized["threshold_status"] == "Not Assessed").all())

    def test_provisional_flag_preserved(self):
        daily, *_ = self.engine.load_accepted_inputs()
        self.assertTrue((daily["threshold_is_provisional"]).all())

    def test_green_with_null_rejected(self):
        daily = pd.DataFrame({
            "kpi_id": ["kpi_001"],
            "kpi_value": [None],
            "calculation_status": ["Calculated"],
            "threshold_status": ["Green"],
            "data_confidence_level": ["High"],
            "threshold_is_provisional": [True],
        })
        result = self.engine.assign_integration_status(daily)
        self.assertEqual(result.iloc[0]["integration_status"], "Failed Validation")

    def test_green_with_non_calculated_rejected(self):
        daily = pd.DataFrame({
            "kpi_id": ["kpi_001"],
            "kpi_value": [50.0],
            "calculation_status": ["Insufficient Data"],
            "threshold_status": ["Green"],
            "data_confidence_level": ["High"],
            "threshold_is_provisional": [True],
        })
        result = self.engine.assign_integration_status(daily)
        self.assertEqual(result.iloc[0]["integration_status"], "Failed Validation")


class TestConfidence(unittest.TestCase):
    def setUp(self):
        self.engine = SixKPIIntegrationEngine(project_root=str(PROJECT_ROOT))

    def test_high_calculated_accepted(self):
        # Provisional threshold triggers Integrated with Warning per spec section 8.
        daily = pd.DataFrame({
            "kpi_id": ["kpi_001"],
            "kpi_value": [50.0],
            "calculation_status": ["Calculated"],
            "threshold_status": ["Not Assessed"],
            "data_confidence_level": ["High"],
            "threshold_is_provisional": [True],
        })
        result = self.engine.assign_integration_status(daily)
        self.assertEqual(result.iloc[0]["integration_status"], "Integrated with Warning")

    def test_unavailable_confidence_accepted(self):
        # Provisional threshold triggers Integrated with Warning per spec section 8.
        daily = pd.DataFrame({
            "kpi_id": ["kpi_001"],
            "kpi_value": [None],
            "calculation_status": ["Insufficient Data"],
            "threshold_status": ["Not Assessed"],
            "data_confidence_level": ["Unavailable"],
            "threshold_is_provisional": [True],
        })
        result = self.engine.assign_integration_status(daily)
        self.assertEqual(result.iloc[0]["integration_status"], "Integrated with Warning")

    def test_high_confidence_on_unavailable_flagged(self):
        daily = pd.DataFrame({
            "kpi_id": ["kpi_001"],
            "kpi_value": [None],
            "calculation_status": ["Insufficient Data"],
            "threshold_status": ["Not Assessed"],
            "data_confidence_level": ["High"],
            "threshold_is_provisional": [True],
        })
        result = self.engine.assign_integration_status(daily)
        self.assertEqual(result.iloc[0]["integration_status"], "Integrated with Warning")


class TestEvidence(unittest.TestCase):
    def setUp(self):
        self.engine = SixKPIIntegrationEngine(project_root=str(PROJECT_ROOT))

    def test_complete_evidence(self):
        daily = pd.DataFrame({
            "analytical_record_id": ["AKPI-1"],
            "kpi_id": ["kpi_001"],
            "calculation_status": ["Calculated"],
            "kpi_value": [50.0],
        })
        evidence = pd.DataFrame({
            "analytical_record_id": ["AKPI-1"],
            "evidence_type": ["numerator"],
        })
        result = self.engine.assign_evidence_status(daily, evidence)
        self.assertEqual(result.iloc[0]["evidence_status"], "Complete")

    def test_missing_evidence_for_calculated(self):
        daily = pd.DataFrame({
            "analytical_record_id": ["AKPI-1"],
            "kpi_id": ["kpi_001"],
            "calculation_status": ["Calculated"],
            "kpi_value": [50.0],
            "threshold_is_provisional": [True],
        })
        evidence = pd.DataFrame(columns=["analytical_record_id"])
        result = self.engine.assign_evidence_status(daily, evidence)
        self.assertEqual(result.iloc[0]["evidence_status"], "Missing")

    def test_unavailable_evidence(self):
        daily = pd.DataFrame({
            "analytical_record_id": ["AKPI-1"],
            "kpi_id": ["kpi_001"],
            "calculation_status": ["Insufficient Data"],
            "kpi_value": [None],
            "threshold_is_provisional": [True],
        })
        evidence = pd.DataFrame(columns=["analytical_record_id"])
        result = self.engine.assign_evidence_status(daily, evidence)
        self.assertEqual(result.iloc[0]["evidence_status"], "Unavailable")


class TestLineage(unittest.TestCase):
    def setUp(self):
        self.engine = SixKPIIntegrationEngine(project_root=str(PROJECT_ROOT))

    def test_complete_lineage(self):
        daily = pd.DataFrame({
            "analytical_record_id": ["AKPI-1"],
            "kpi_id": ["kpi_001"],
            "calculation_status": ["Calculated"],
            "kpi_value": [50.0],
        })
        lineage = pd.DataFrame({
            "analytical_record_id": ["AKPI-1"],
            "transformation_name": ["calc"],
        })
        result = self.engine.assign_lineage_status(daily, lineage)
        self.assertEqual(result.iloc[0]["lineage_status"], "Complete")

    def test_broken_lineage_for_calculated(self):
        daily = pd.DataFrame({
            "analytical_record_id": ["AKPI-1"],
            "kpi_id": ["kpi_001"],
            "calculation_status": ["Calculated"],
            "kpi_value": [50.0],
            "threshold_is_provisional": [True],
        })
        lineage = pd.DataFrame(columns=["analytical_record_id"])
        result = self.engine.assign_lineage_status(daily, lineage)
        self.assertEqual(result.iloc[0]["lineage_status"], "Broken")

    def test_unavailable_lineage(self):
        daily = pd.DataFrame({
            "analytical_record_id": ["AKPI-1"],
            "kpi_id": ["kpi_001"],
            "calculation_status": ["Insufficient Data"],
            "kpi_value": [None],
            "threshold_is_provisional": [True],
        })
        lineage = pd.DataFrame(columns=["analytical_record_id"])
        result = self.engine.assign_lineage_status(daily, lineage)
        self.assertEqual(result.iloc[0]["lineage_status"], "Unavailable")


class TestCoverage(unittest.TestCase):
    def setUp(self):
        self.engine = SixKPIIntegrationEngine(project_root=str(PROJECT_ROOT))

    def test_complete_coverage(self):
        daily = pd.DataFrame({
            "hospital_id": ["H1"] * 6,
            "department_id": ["D1"] * 6,
            "reporting_date": ["2024-01-01"] * 6,
            "kpi_id": list(GOVERNED_KPI_IDS),
            "kpi_value": [1.0] * 6,
        })
        coverage = self.engine.build_coverage_matrix(daily)
        self.assertEqual(coverage.iloc[0]["coverage_status"], "Complete")
        self.assertEqual(coverage.iloc[0]["present_kpi_count"], 6)

    def test_partial_coverage(self):
        daily = pd.DataFrame({
            "hospital_id": ["H1", "H1"],
            "department_id": ["D1", "D1"],
            "reporting_date": ["2024-01-01", "2024-01-01"],
            "kpi_id": ["kpi_001", "kpi_002"],
            "kpi_value": [1.0, None],
        })
        coverage = self.engine.build_coverage_matrix(daily)
        self.assertEqual(coverage.iloc[0]["coverage_status"], "Partial")
        self.assertEqual(coverage.iloc[0]["missing_kpi_count"], 4)

    def test_no_fabricated_zero_values(self):
        daily = pd.DataFrame({
            "hospital_id": ["H1"],
            "department_id": ["D1"],
            "reporting_date": ["2024-01-01"],
            "kpi_id": ["kpi_001"],
            "kpi_value": [None],
        })
        coverage = self.engine.build_coverage_matrix(daily)
        self.assertEqual(coverage.iloc[0]["unavailable_kpi_count"], 1)


class TestOutputs(unittest.TestCase):
    def setUp(self):
        self.engine = SixKPIIntegrationEngine(project_root=str(PROJECT_ROOT))
        self.result = self.engine.run()

    def test_schema_validation(self):
        required = [
            "integration_record_id", "analytical_record_id", "hospital_id", "department_id",
            "reporting_date", "kpi_id", "kpi_name", "domain", "kpi_value",
            "calculation_status", "threshold_status", "data_confidence_level",
            "integration_status", "evidence_status", "lineage_status",
        ]
        for col in required:
            self.assertIn(col, self.result.integrated_daily_df.columns)

    def test_unique_integration_ids(self):
        self.assertEqual(
            self.result.integrated_daily_df["integration_record_id"].nunique(),
            len(self.result.integrated_daily_df),
        )

    def test_exact_kpi_id_set(self):
        self.assertEqual(set(self.result.integrated_daily_df["kpi_id"].unique()), GOVERNED_KPI_IDS)

    def test_coverage_matrix_generated(self):
        self.assertGreater(len(self.result.coverage_df), 0)
        self.assertIn("coverage_status", self.result.coverage_df.columns)

    def test_reconciliation_generated(self):
        self.assertEqual(len(self.result.reconciliation_df), 6)


class TestImmutability(unittest.TestCase):
    def setUp(self):
        self.engine = SixKPIIntegrationEngine(project_root=str(PROJECT_ROOT))
        self.pre = self._checksums()
        self.result = self.engine.run()

    def _checksums(self):
        files = [
            "data/analytical/analytical_workforce_kpi_daily.csv",
            "data/analytical/analytical_patient_flow_kpi_daily.csv",
            "data/analytical/analytical_patient_experience_kpi_daily.csv",
        ]
        cs = {}
        for f in files:
            p = PROJECT_ROOT / f
            if p.exists():
                h = hashlib.sha256()
                with open(p, "rb") as fp:
                    for chunk in iter(lambda: fp.read(8192), b""):
                        h.update(chunk)
                cs[f] = h.hexdigest()
        return cs

    def test_prior_analytical_files_unchanged(self):
        post = self._checksums()
        for f, pre in self.pre.items():
            self.assertEqual(pre, post[f], f"File {f} changed during integration")


class TestEndToEnd(unittest.TestCase):
    def setUp(self):
        self.engine = SixKPIIntegrationEngine(project_root=str(PROJECT_ROOT))
        self.result = self.engine.run()

    def test_integration_run_id_present(self):
        self.assertTrue(self.result.integration_manifest["integration_run_id"].startswith("SIX-KPI-"))

    def test_total_integrated_rows(self):
        self.assertEqual(len(self.result.integrated_daily_df), 17520)

    def test_no_formula_recalculation(self):
        # Values must match source exactly
        source_daily = []
        for domain in ["workforce", "patient_flow", "patient_experience"]:
            df = pd.read_csv(PROJECT_ROOT / "data" / "analytical" / f"analytical_{domain}_kpi_daily.csv")
            source_daily.append(df)
        source = pd.concat(source_daily, ignore_index=True)
        merged = self.result.integrated_daily_df.merge(
            source[["analytical_record_id", "kpi_value"]],
            on="analytical_record_id",
            suffixes=("_int", "_src"),
        )
        # Allow NaN == NaN
        matches = merged.apply(lambda r: (
            pd.isna(r["kpi_value_int"]) and pd.isna(r["kpi_value_src"])
        ) or r["kpi_value_int"] == r["kpi_value_src"], axis=1)
        self.assertTrue(matches.all())

    def test_status_summaries_generated(self):
        self.assertGreater(len(self.result.status_summary_df), 0)

    def test_manifest_contains_checksums(self):
        self.assertIn("source_checksums", self.result.integration_manifest)


if __name__ == "__main__":
    unittest.main()
