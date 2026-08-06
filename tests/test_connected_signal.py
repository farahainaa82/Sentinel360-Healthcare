"""
Connected Signal Engine — Targeted Tests (CS-2 Spec §23).

A–P contract checks as specified in the Connected Signal Step 2 implementation.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from typing import Any, Dict

import pandas as pd
from pandas import DataFrame

from src import connected_signal_engine as cs_engine
from src.ai_connected_signal_synthesis import (
    AIConnectedSignalSynthesisResult,
    AIConnectedSignalSynthesisService,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_config_csv(tmpdir: str) -> str:
    path = os.path.join(tmpdir, "connected_signal_config.csv")
    df = DataFrame(
        [
            {
                "relationship_id": "CS_001",
                "from_kpi_id": "kpi_002",
                "from_kpi_name": "Staff Absenteeism Rate",
                "to_kpi_id": "kpi_001",
                "to_kpi_name": "Staffing Level",
                "expected_direction": "INVERSE",
                "enabled": "True",
            },
            {
                "relationship_id": "CS_002",
                "from_kpi_id": "kpi_001",
                "from_kpi_name": "Staffing Level",
                "to_kpi_id": "kpi_004",
                "to_kpi_name": "Average Patient Waiting Time",
                "expected_direction": "INVERSE",
                "enabled": "True",
            },
            {
                "relationship_id": "CS_003",
                "from_kpi_id": "kpi_003",
                "from_kpi_name": "Bed Occupancy Rate",
                "to_kpi_id": "kpi_004",
                "to_kpi_name": "Average Patient Waiting Time",
                "expected_direction": "POSITIVE",
                "enabled": "True",
            },
            {
                "relationship_id": "CS_004",
                "from_kpi_id": "kpi_004",
                "from_kpi_name": "Average Patient Waiting Time",
                "to_kpi_id": "kpi_005",
                "to_kpi_name": "Patient Complaint Rate",
                "expected_direction": "POSITIVE",
                "enabled": "True",
            },
            {
                "relationship_id": "CS_005",
                "from_kpi_id": "kpi_004",
                "from_kpi_name": "Average Patient Waiting Time",
                "to_kpi_id": "kpi_006",
                "to_kpi_name": "Patient Satisfaction Score",
                "expected_direction": "INVERSE",
                "enabled": "True",
            },
            {
                "relationship_id": "CS_006",
                "from_kpi_id": "kpi_005",
                "from_kpi_name": "Patient Complaint Rate",
                "to_kpi_id": "kpi_006",
                "to_kpi_name": "Patient Satisfaction Score",
                "expected_direction": "INVERSE",
                "enabled": "True",
            },
        ]
    )
    df.to_csv(path, index=False)
    return path


def _make_kpi_def_csv(tmpdir: str) -> str:
    path = os.path.join(tmpdir, "kpi_definition_config.csv")
    df = DataFrame(
        [
            {"kpi_id": "kpi_001", "kpi_name": "Staffing Level", "performance_direction": "Higher Is Better"},
            {"kpi_id": "kpi_002", "kpi_name": "Staff Absenteeism Rate", "performance_direction": "Lower Is Better"},
            {"kpi_id": "kpi_003", "kpi_name": "Bed Occupancy Rate", "performance_direction": "Lower Is Better"},
            {"kpi_id": "kpi_004", "kpi_name": "Average Patient Waiting Time", "performance_direction": "Lower Is Better"},
            {"kpi_id": "kpi_005", "kpi_name": "Patient Complaint Rate", "performance_direction": "Lower Is Better"},
            {"kpi_id": "kpi_006", "kpi_name": "Patient Satisfaction Score", "performance_direction": "Higher Is Better"},
        ]
    )
    df.to_csv(path, index=False)
    return path


def _make_actual_history_csv(tmpdir: str) -> str:
    """Create a 7-month actual history (Jan–Jul) for all 6 KPIs."""
    path = os.path.join(tmpdir, "kpi_monthly_actual_history.csv")
    rows = []
    for month in range(1, 8):
        # Staffing Level (Higher Is Better) — declining
        rows.append(
            {
                "hospital": "HOSP-001",
                "department": "TEST-DEPT",
                "department_code": "TEST-DEPT",
                "kpi_id": "kpi_001",
                "kpi_name": "Staffing Level",
                "year": 2025,
                "month": month,
                "period_start": f"2025-{month:02d}-01",
                "period_end": f"2025-{month:02d}-28",
                "monthly_actual_value": 100 - (month - 1) * 5,
                "unit": "%",
                "valid_observation_count": 30,
                "missing_observation_count": 0,
                "aggregation_method": "mean",
                "calculation_status": "complete",
                "source_file": "test",
            }
        )
        # Absenteeism (Lower Is Better) — rising
        rows.append(
            {
                "hospital": "HOSP-001",
                "department": "TEST-DEPT",
                "department_code": "TEST-DEPT",
                "kpi_id": "kpi_002",
                "kpi_name": "Staff Absenteeism Rate",
                "year": 2025,
                "month": month,
                "period_start": f"2025-{month:02d}-01",
                "period_end": f"2025-{month:02d}-28",
                "monthly_actual_value": 5 + (month - 1) * 3,
                "unit": "%",
                "valid_observation_count": 30,
                "missing_observation_count": 0,
                "aggregation_method": "mean",
                "calculation_status": "complete",
                "source_file": "test",
            }
        )
        # Waiting Time (Lower Is Better) — rising
        rows.append(
            {
                "hospital": "HOSP-001",
                "department": "TEST-DEPT",
                "department_code": "TEST-DEPT",
                "kpi_id": "kpi_004",
                "kpi_name": "Average Patient Waiting Time",
                "year": 2025,
                "month": month,
                "period_start": f"2025-{month:02d}-01",
                "period_end": f"2025-{month:02d}-28",
                "monthly_actual_value": 20 + (month - 1) * 4,
                "unit": "minutes",
                "valid_observation_count": 30,
                "missing_observation_count": 0,
                "aggregation_method": "mean",
                "calculation_status": "complete",
                "source_file": "test",
            }
        )
        # Patient Satisfaction (Higher Is Better) — declining
        rows.append(
            {
                "hospital": "HOSP-001",
                "department": "TEST-DEPT",
                "department_code": "TEST-DEPT",
                "kpi_id": "kpi_006",
                "kpi_name": "Patient Satisfaction Score",
                "year": 2025,
                "month": month,
                "period_start": f"2025-{month:02d}-01",
                "period_end": f"2025-{month:02d}-28",
                "monthly_actual_value": 85 - (month - 1) * 4,
                "unit": "score",
                "valid_observation_count": 30,
                "missing_observation_count": 0,
                "aggregation_method": "mean",
                "calculation_status": "complete",
                "source_file": "test",
            }
        )
    df = DataFrame(rows)
    df.to_csv(path, index=False)
    return path


def _make_forecast_csv(tmpdir: str) -> str:
    """Create forecast for Aug 2025 that continues the adverse directions."""
    path = os.path.join(tmpdir, "analytical_kpi_monthly_forecast.csv")
    rows = [
        # Staffing Level continues down (adverse for Higher Is Better)
        {
            "forecast_id": "FC001",
            "hospital": "HOSP-001",
            "department": "Test Department",
            "department_code": "TEST-DEPT",
            "kpi_id": "kpi_001",
            "kpi_name": "Staffing Level",
            "forecast_year": 2025,
            "forecast_month": 8,
            "point_forecast": 60.0,
            "lower_bound": 55.0,
            "upper_bound": 65.0,
            "forecast_method": "test",
            "forecast_method_category": "test",
            "forecast_source_kpi_id": "kpi_001",
            "forecast_rationale": "test",
            "forecast_confidence": "moderate",
            "forecast_run_timestamp": "2025-07-31",
            "forecast_horizon": 1,
            "model_identifier": "test",
            "model_version": "v1",
        },
        # Waiting Time continues up (adverse for Lower Is Better)
        {
            "forecast_id": "FC002",
            "hospital": "HOSP-001",
            "department": "Test Department",
            "department_code": "TEST-DEPT",
            "kpi_id": "kpi_004",
            "kpi_name": "Average Patient Waiting Time",
            "forecast_year": 2025,
            "forecast_month": 8,
            "point_forecast": 55.0,
            "lower_bound": 50.0,
            "upper_bound": 60.0,
            "forecast_method": "test",
            "forecast_method_category": "test",
            "forecast_source_kpi_id": "kpi_004",
            "forecast_rationale": "test",
            "forecast_confidence": "moderate",
            "forecast_run_timestamp": "2025-07-31",
            "forecast_horizon": 1,
            "model_identifier": "test",
            "model_version": "v1",
        },
        # Patient Satisfaction continues down (adverse for Higher Is Better)
        {
            "forecast_id": "FC003",
            "hospital": "HOSP-001",
            "department": "Test Department",
            "department_code": "TEST-DEPT",
            "kpi_id": "kpi_006",
            "kpi_name": "Patient Satisfaction Score",
            "forecast_year": 2025,
            "forecast_month": 8,
            "point_forecast": 50.0,
            "lower_bound": 45.0,
            "upper_bound": 55.0,
            "forecast_method": "test",
            "forecast_method_category": "test",
            "forecast_source_kpi_id": "kpi_006",
            "forecast_rationale": "test",
            "forecast_confidence": "moderate",
            "forecast_run_timestamp": "2025-07-31",
            "forecast_horizon": 1,
            "model_identifier": "test",
            "model_version": "v1",
        },
        # Staff Absenteeism continues up (adverse for Lower Is Better)
        {
            "forecast_id": "FC004",
            "hospital": "HOSP-001",
            "department": "Test Department",
            "department_code": "TEST-DEPT",
            "kpi_id": "kpi_002",
            "kpi_name": "Staff Absenteeism Rate",
            "forecast_year": 2025,
            "forecast_month": 8,
            "point_forecast": 26.0,
            "lower_bound": 22.0,
            "upper_bound": 30.0,
            "forecast_method": "test",
            "forecast_method_category": "test",
            "forecast_source_kpi_id": "kpi_002",
            "forecast_rationale": "test",
            "forecast_confidence": "moderate",
            "forecast_run_timestamp": "2025-07-31",
            "forecast_horizon": 1,
            "model_identifier": "test",
            "model_version": "v1",
        },
    ]
    df = DataFrame(rows)
    df.to_csv(path, index=False)
    return path


# ---------------------------------------------------------------------------
# Test suite
# ---------------------------------------------------------------------------
class TestConnectedSignalHistoricalWindow(unittest.TestCase):
    """A. Jan–Jul only used for forecast-period historical association.
    B. Aug–Dec never included in historical correlation.
    C. Selected ACTUAL month only uses history up to that month.
    """

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.cfg = _make_config_csv(self.tmpdir)
        self.kpi_def = _make_kpi_def_csv(self.tmpdir)
        self.actual = _make_actual_history_csv(self.tmpdir)
        self.forecast = _make_forecast_csv(self.tmpdir)

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _run(self, year: int, month: int) -> Dict[str, Any]:
        return cs_engine.run_connected_signal(
            hospital_id="HOSP-001",
            department_id="TEST-DEPT",
            selected_year=year,
            selected_month=month,
            actual_history_path=self.actual,
            forecast_path=self.forecast,
            config_path=self.cfg,
            kpi_definition_path=self.kpi_def,
        )

    # A. Jan–Jul only used for forecast-period historical association
    def test_forecast_period_uses_jan_jul_only(self) -> None:
        result = self._run(2025, 8)
        self.assertTrue(result["is_forecast_period"])
        rels = result["relationships"]
        for rel in rels:
            if rel["observation_count"] > 0:
                self.assertEqual(rel["observation_count"], 7)

    # B. Aug–Dec never included in historical correlation
    def test_forecast_month_aug_not_in_actual_history(self) -> None:
        result = self._run(2025, 8)
        rels = result["relationships"]
        for rel in rels:
            if rel["observation_count"] > 0:
                self.assertEqual(rel["observation_count"], 7)
                # 7 months means Jan–Jul, not Aug

    # C. Selected ACTUAL month only uses history up to that month
    def test_actual_april_uses_jan_apr(self) -> None:
        result = self._run(2025, 4)
        self.assertFalse(result["is_forecast_period"])
        rels = result["relationships"]
        for rel in rels:
            if rel["observation_count"] > 0:
                self.assertEqual(rel["observation_count"], 4)

    def test_actual_july_uses_jan_jul(self) -> None:
        result = self._run(2025, 7)
        self.assertFalse(result["is_forecast_period"])
        rels = result["relationships"]
        for rel in rels:
            if rel["observation_count"] > 0:
                self.assertEqual(rel["observation_count"], 7)


class TestConnectedSignalSupportRules(unittest.TestCase):
    """D. n < 5 → insufficient evidence.
    E. n=7 + abs(r)>=0.80 + direction match → supported.
    F. n=7 + abs(r)<0.80 → not supported.
    G. Sign mismatch → not supported.
    """

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.cfg = _make_config_csv(self.tmpdir)
        self.kpi_def = _make_kpi_def_csv(self.tmpdir)
        self.actual = _make_actual_history_csv(self.tmpdir)
        self.forecast = _make_forecast_csv(self.tmpdir)

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _run(self, year: int, month: int) -> Dict[str, Any]:
        return cs_engine.run_connected_signal(
            hospital_id="HOSP-001",
            department_id="TEST-DEPT",
            selected_year=year,
            selected_month=month,
            actual_history_path=self.actual,
            forecast_path=self.forecast,
            config_path=self.cfg,
            kpi_definition_path=self.kpi_def,
        )

    # D. n < 5 → insufficient evidence
    def test_n_less_than_5_insufficient(self) -> None:
        result = self._run(2025, 4)
        rels = result["relationships"]
        for rel in rels:
            self.assertEqual(rel["strength_label"], "INSUFFICIENT EVIDENCE")
            self.assertFalse(rel["supported"])

    # E. n=7 + abs(r)>=0.80 + direction match → supported
    def test_n_7_strong_inverse_supported(self) -> None:
        result = self._run(2025, 7)
        rels = {r["relationship_id"]: r for r in result["relationships"]}
        # Staffing Level (declining) vs Absenteeism (rising) = inverse, should be strong
        cs_001 = rels.get("CS_001")
        self.assertIsNotNone(cs_001)
        self.assertTrue(cs_001["supported"])
        self.assertEqual(cs_001["strength_label"], "STRONG OBSERVED PATTERN")
        self.assertGreaterEqual(abs(cs_001["association_value"]), 0.80)
        self.assertEqual(cs_001["observed_direction"], "INVERSE")

    # F. n=7 + abs(r)<0.80 → not supported
    def test_n_7_weak_not_supported(self) -> None:
        # Create a dataset with weak correlation for a pair
        tmpdir = tempfile.mkdtemp()
        cfg = _make_config_csv(tmpdir)
        kpi_def = _make_kpi_def_csv(tmpdir)
        # Make a noisy history where correlation is weak
        rows = []
        for month in range(1, 8):
            rows.append(
                {
                    "hospital": "HOSP-001",
                    "department": "WEAK-DEPT",
                    "department_code": "WEAK-DEPT",
                    "kpi_id": "kpi_001",
                    "kpi_name": "Staffing Level",
                    "year": 2025,
                    "month": month,
                    "period_start": f"2025-{month:02d}-01",
                    "period_end": f"2025-{month:02d}-28",
                    "monthly_actual_value": [100, 95, 98, 97, 96, 99, 94][month - 1],
                    "unit": "%",
                    "valid_observation_count": 30,
                    "missing_observation_count": 0,
                    "aggregation_method": "mean",
                    "calculation_status": "complete",
                    "source_file": "test",
                }
            )
            rows.append(
                {
                    "hospital": "HOSP-001",
                    "department": "WEAK-DEPT",
                    "department_code": "WEAK-DEPT",
                    "kpi_id": "kpi_002",
                    "kpi_name": "Staff Absenteeism Rate",
                    "year": 2025,
                    "month": month,
                    "period_start": f"2025-{month:02d}-01",
                    "period_end": f"2025-{month:02d}-28",
                    "monthly_actual_value": [5, 6, 5, 7, 6, 5, 7][month - 1],
                    "unit": "%",
                    "valid_observation_count": 30,
                    "missing_observation_count": 0,
                    "aggregation_method": "mean",
                    "calculation_status": "complete",
                    "source_file": "test",
                }
            )
        df = DataFrame(rows)
        actual_path = os.path.join(tmpdir, "actual.csv")
        df.to_csv(actual_path, index=False)
        result = cs_engine.run_connected_signal(
            hospital_id="HOSP-001",
            department_id="WEAK-DEPT",
            selected_year=2025,
            selected_month=7,
            actual_history_path=actual_path,
            config_path=cfg,
            kpi_definition_path=kpi_def,
        )
        rels = {r["relationship_id"]: r for r in result["relationships"]}
        cs_001 = rels.get("CS_001")
        self.assertIsNotNone(cs_001)
        self.assertFalse(cs_001["supported"])
        self.assertLess(abs(cs_001["association_value"]), 0.80)
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)

    # G. Sign mismatch → not supported
    def test_sign_mismatch_not_supported(self) -> None:
        # Create a dataset where correlation is positive but expected is INVERSE
        tmpdir = tempfile.mkdtemp()
        cfg = _make_config_csv(tmpdir)
        kpi_def = _make_kpi_def_csv(tmpdir)
        rows = []
        for month in range(1, 8):
            rows.append(
                {
                    "hospital": "HOSP-001",
                    "department": "MISMATCH-DEPT",
                    "department_code": "MISMATCH-DEPT",
                    "kpi_id": "kpi_001",
                    "kpi_name": "Staffing Level",
                    "year": 2025,
                    "month": month,
                    "period_start": f"2025-{month:02d}-01",
                    "period_end": f"2025-{month:02d}-28",
                    "monthly_actual_value": 100 + (month - 1) * 5,
                    "unit": "%",
                    "valid_observation_count": 30,
                    "missing_observation_count": 0,
                    "aggregation_method": "mean",
                    "calculation_status": "complete",
                    "source_file": "test",
                }
            )
            rows.append(
                {
                    "hospital": "HOSP-001",
                    "department": "MISMATCH-DEPT",
                    "department_code": "MISMATCH-DEPT",
                    "kpi_id": "kpi_002",
                    "kpi_name": "Staff Absenteeism Rate",
                    "year": 2025,
                    "month": month,
                    "period_start": f"2025-{month:02d}-01",
                    "period_end": f"2025-{month:02d}-28",
                    "monthly_actual_value": 5 + (month - 1) * 3,
                    "unit": "%",
                    "valid_observation_count": 30,
                    "missing_observation_count": 0,
                    "aggregation_method": "mean",
                    "calculation_status": "complete",
                    "source_file": "test",
                }
            )
        df = DataFrame(rows)
        actual_path = os.path.join(tmpdir, "actual.csv")
        df.to_csv(actual_path, index=False)
        result = cs_engine.run_connected_signal(
            hospital_id="HOSP-001",
            department_id="MISMATCH-DEPT",
            selected_year=2025,
            selected_month=7,
            actual_history_path=actual_path,
            config_path=cfg,
            kpi_definition_path=kpi_def,
        )
        rels = {r["relationship_id"]: r for r in result["relationships"]}
        cs_001 = rels.get("CS_001")
        self.assertIsNotNone(cs_001)
        self.assertEqual(cs_001["observed_direction"], "POSITIVE")
        self.assertEqual(cs_001["expected_direction"], "INVERSE")
        self.assertFalse(cs_001["supported"])
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


class TestConnectedSignalChains(unittest.TestCase):
    """H. Chain requires every edge supported.
    I. Forecast continuation does not affect historical correlation.
    N. No supported chain state.
    """

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.cfg = _make_config_csv(self.tmpdir)
        self.kpi_def = _make_kpi_def_csv(self.tmpdir)
        self.actual = _make_actual_history_csv(self.tmpdir)
        self.forecast = _make_forecast_csv(self.tmpdir)

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _run(self, year: int, month: int) -> Dict[str, Any]:
        return cs_engine.run_connected_signal(
            hospital_id="HOSP-001",
            department_id="TEST-DEPT",
            selected_year=year,
            selected_month=month,
            actual_history_path=self.actual,
            forecast_path=self.forecast,
            config_path=self.cfg,
            kpi_definition_path=self.kpi_def,
        )

    # H. Chain requires every edge supported
    def test_chain_only_if_all_edges_supported(self) -> None:
        result = self._run(2025, 7)
        chains = result.get("connected_chains", [])
        if chains:
            primary = result["primary_chain"]
            self.assertIsNotNone(primary)
            edges = primary["edges"]
            for edge in edges:
                self.assertTrue(edge["supported"])

    # I. Forecast continuation does not affect historical correlation
    def test_forecast_does_not_affect_correlation(self) -> None:
        result_jul = self._run(2025, 7)
        result_aug = self._run(2025, 8)
        rels_jul = {r["relationship_id"]: r for r in result_jul["relationships"]}
        rels_aug = {r["relationship_id"]: r for r in result_aug["relationships"]}
        for rid in rels_jul:
            self.assertEqual(
                rels_jul[rid]["association_value"],
                rels_aug[rid]["association_value"],
                f"Correlation changed for {rid} between Jul and Aug",
            )

    # N. No supported chain state
    def test_no_chain_fallback(self) -> None:
        tmpdir = tempfile.mkdtemp()
        cfg = _make_config_csv(tmpdir)
        kpi_def = _make_kpi_def_csv(tmpdir)
        # Only one KPI — no pairs possible
        rows = []
        for month in range(1, 8):
            rows.append(
                {
                    "hospital": "HOSP-001",
                    "department": "NO-CHAIN",
                    "department_code": "NO-CHAIN",
                    "kpi_id": "kpi_001",
                    "kpi_name": "Staffing Level",
                    "year": 2025,
                    "month": month,
                    "period_start": f"2025-{month:02d}-01",
                    "period_end": f"2025-{month:02d}-28",
                    "monthly_actual_value": 100 - month * 5,
                    "unit": "%",
                    "valid_observation_count": 30,
                    "missing_observation_count": 0,
                    "aggregation_method": "mean",
                    "calculation_status": "complete",
                    "source_file": "test",
                }
            )
        df = DataFrame(rows)
        actual_path = os.path.join(tmpdir, "actual.csv")
        df.to_csv(actual_path, index=False)
        result = cs_engine.run_connected_signal(
            hospital_id="HOSP-001",
            department_id="NO-CHAIN",
            selected_year=2025,
            selected_month=7,
            actual_history_path=actual_path,
            config_path=cfg,
            kpi_definition_path=kpi_def,
        )
        self.assertIsNone(result["primary_chain"])
        self.assertEqual(result["connected_chains"], [])
        html = cs_engine.build_connected_signal_card_html(result, period_badge_html="ACTUAL")
        self.assertIn("No sufficiently strong connected signal", html)
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


class TestConnectedSignalForecastContinuation(unittest.TestCase):
    """J. Forecast continuation CONTINUES.
    K. Forecast continuation PARTIAL.
    L. Forecast continuation NOT_CONTINUING.
    """

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.cfg = _make_config_csv(self.tmpdir)
        self.kpi_def = _make_kpi_def_csv(self.tmpdir)
        self.actual = _make_actual_history_csv(self.tmpdir)

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _run(self, forecast_csv: str) -> Dict[str, Any]:
        return cs_engine.run_connected_signal(
            hospital_id="HOSP-001",
            department_id="TEST-DEPT",
            selected_year=2025,
            selected_month=8,
            actual_history_path=self.actual,
            forecast_path=forecast_csv,
            config_path=self.cfg,
            kpi_definition_path=self.kpi_def,
        )

    # J. Forecast continuation CONTINUES
    def test_continuation_continues(self) -> None:
        forecast_path = _make_forecast_csv(self.tmpdir)
        result = self._run(forecast_path)
        fc = result.get("forecast_continuation")
        self.assertIsNotNone(fc)
        self.assertEqual(fc["continuation_status"], "CONTINUES")

    # K. Forecast continuation PARTIAL
    def test_continuation_partial(self) -> None:
        # Make forecast where only some KPIs continue the adverse direction
        rows = [
            {
                "forecast_id": "FC001",
                "hospital": "HOSP-001",
                "department": "Test Department",
                "department_code": "TEST-DEPT",
                "kpi_id": "kpi_001",
                "kpi_name": "Staffing Level",
                "forecast_year": 2025,
                "forecast_month": 8,
                "point_forecast": 60.0,
                "lower_bound": 55.0,
                "upper_bound": 65.0,
                "forecast_method": "test",
                "forecast_method_category": "test",
                "forecast_source_kpi_id": "kpi_001",
                "forecast_rationale": "test",
                "forecast_confidence": "moderate",
                "forecast_run_timestamp": "2025-07-31",
                "forecast_horizon": 1,
                "model_identifier": "test",
                "model_version": "v1",
            },
            # Waiting Time REVERSES (goes down instead of up)
            {
                "forecast_id": "FC002",
                "hospital": "HOSP-001",
                "department": "Test Department",
                "department_code": "TEST-DEPT",
                "kpi_id": "kpi_004",
                "kpi_name": "Average Patient Waiting Time",
                "forecast_year": 2025,
                "forecast_month": 8,
                "point_forecast": 30.0,
                "lower_bound": 25.0,
                "upper_bound": 35.0,
                "forecast_method": "test",
                "forecast_method_category": "test",
                "forecast_source_kpi_id": "kpi_004",
                "forecast_rationale": "test",
                "forecast_confidence": "moderate",
                "forecast_run_timestamp": "2025-07-31",
                "forecast_horizon": 1,
                "model_identifier": "test",
                "model_version": "v1",
            },
            # Patient Satisfaction continues down
            {
                "forecast_id": "FC003",
                "hospital": "HOSP-001",
                "department": "Test Department",
                "department_code": "TEST-DEPT",
                "kpi_id": "kpi_006",
                "kpi_name": "Patient Satisfaction Score",
                "forecast_year": 2025,
                "forecast_month": 8,
                "point_forecast": 50.0,
                "lower_bound": 45.0,
                "upper_bound": 55.0,
                "forecast_method": "test",
                "forecast_method_category": "test",
                "forecast_source_kpi_id": "kpi_006",
                "forecast_rationale": "test",
                "forecast_confidence": "moderate",
                "forecast_run_timestamp": "2025-07-31",
                "forecast_horizon": 1,
                "model_identifier": "test",
                "model_version": "v1",
            },
        ]
        df = DataFrame(rows)
        forecast_path = os.path.join(self.tmpdir, "partial_forecast.csv")
        df.to_csv(forecast_path, index=False)
        result = self._run(forecast_path)
        fc = result.get("forecast_continuation")
        self.assertIsNotNone(fc)
        self.assertEqual(fc["continuation_status"], "PARTIAL")

    # L. Forecast continuation NOT_CONTINUING
    def test_continuation_not_continuing(self) -> None:
        # Make forecast where ALL KPIs reverse direction
        rows = [
            # Staffing Level goes UP (reverses)
            {
                "forecast_id": "FC001",
                "hospital": "HOSP-001",
                "department": "Test Department",
                "department_code": "TEST-DEPT",
                "kpi_id": "kpi_001",
                "kpi_name": "Staffing Level",
                "forecast_year": 2025,
                "forecast_month": 8,
                "point_forecast": 90.0,
                "lower_bound": 85.0,
                "upper_bound": 95.0,
                "forecast_method": "test",
                "forecast_method_category": "test",
                "forecast_source_kpi_id": "kpi_001",
                "forecast_rationale": "test",
                "forecast_confidence": "moderate",
                "forecast_run_timestamp": "2025-07-31",
                "forecast_horizon": 1,
                "model_identifier": "test",
                "model_version": "v1",
            },
            # Waiting Time goes DOWN (reverses)
            {
                "forecast_id": "FC002",
                "hospital": "HOSP-001",
                "department": "Test Department",
                "department_code": "TEST-DEPT",
                "kpi_id": "kpi_004",
                "kpi_name": "Average Patient Waiting Time",
                "forecast_year": 2025,
                "forecast_month": 8,
                "point_forecast": 30.0,
                "lower_bound": 25.0,
                "upper_bound": 35.0,
                "forecast_method": "test",
                "forecast_method_category": "test",
                "forecast_source_kpi_id": "kpi_004",
                "forecast_rationale": "test",
                "forecast_confidence": "moderate",
                "forecast_run_timestamp": "2025-07-31",
                "forecast_horizon": 1,
                "model_identifier": "test",
                "model_version": "v1",
            },
            # Patient Satisfaction goes UP (reverses)
            {
                "forecast_id": "FC003",
                "hospital": "HOSP-001",
                "department": "Test Department",
                "department_code": "TEST-DEPT",
                "kpi_id": "kpi_006",
                "kpi_name": "Patient Satisfaction Score",
                "forecast_year": 2025,
                "forecast_month": 8,
                "point_forecast": 80.0,
                "lower_bound": 75.0,
                "upper_bound": 85.0,
                "forecast_method": "test",
                "forecast_method_category": "test",
                "forecast_source_kpi_id": "kpi_006",
                "forecast_rationale": "test",
                "forecast_confidence": "moderate",
                "forecast_run_timestamp": "2025-07-31",
                "forecast_horizon": 1,
                "model_identifier": "test",
                "model_version": "v1",
            },
        ]
        df = DataFrame(rows)
        forecast_path = os.path.join(self.tmpdir, "not_continuing_forecast.csv")
        df.to_csv(forecast_path, index=False)
        result = self._run(forecast_path)
        fc = result.get("forecast_continuation")
        self.assertIsNotNone(fc)
        self.assertEqual(fc["continuation_status"], "NOT_CONTINUING")


class TestConnectedSignalGovernance(unittest.TestCase):
    """M. causality_confirmed always false.
    """

    def test_causality_confirmed_always_false(self) -> None:
        tmpdir = tempfile.mkdtemp()
        cfg = _make_config_csv(tmpdir)
        kpi_def = _make_kpi_def_csv(tmpdir)
        actual = _make_actual_history_csv(tmpdir)
        result = cs_engine.run_connected_signal(
            hospital_id="HOSP-001",
            department_id="TEST-DEPT",
            selected_year=2025,
            selected_month=7,
            actual_history_path=actual,
            config_path=cfg,
            kpi_definition_path=kpi_def,
        )
        gov = result.get("governance", {})
        self.assertFalse(gov.get("causality_confirmed"))
        self.assertEqual(gov.get("relationship_type"), "exploratory historical association")
        self.assertTrue(gov.get("actual_data_only"))
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


class TestConnectedSignalAIFailure(unittest.TestCase):
    """O. AI failure does not break card.
    """

    def test_ai_failure_returns_deterministic_fallback_message(self) -> None:
        """CS-3 contract: when Hy3 / the AI service is unavailable, the
        service NEVER returns an empty message -- a deterministic
        fallback (or no-chain sentence) is returned so the Connected
        Signal card cannot be blank. The status reflects the failure
        cause (NOT_CONFIGURED here) but the message is non-empty.
        """
        service = AIConnectedSignalSynthesisService()
        # No provider configured -> NOT_CONFIGURED; message should
        # still be non-empty so the card is never blank.
        result = service.synthesize({"primary_chain": {}})
        self.assertEqual(result.status, "NOT_CONFIGURED")
        self.assertNotEqual(result.message, "")
        self.assertIsInstance(result.message, str)

    def test_card_builds_with_empty_ai_interpretation(self) -> None:
        tmpdir = tempfile.mkdtemp()
        cfg = _make_config_csv(tmpdir)
        kpi_def = _make_kpi_def_csv(tmpdir)
        actual = _make_actual_history_csv(tmpdir)
        result = cs_engine.run_connected_signal(
            hospital_id="HOSP-001",
            department_id="TEST-DEPT",
            selected_year=2025,
            selected_month=7,
            actual_history_path=actual,
            config_path=cfg,
            kpi_definition_path=kpi_def,
        )
        html = cs_engine.build_connected_signal_card_html(
            result,
            period_badge_html="ACTUAL",
            ai_interpretation="",
        )
        self.assertNotEqual(html, "")
        self.assertIn("Connected Signal", html)
        # Ensure AI failure does not cause a crash — html is well-formed
        self.assertTrue(html.startswith("<div"))
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


class TestProductivityEnginePreserved(unittest.TestCase):
    """P. Productivity engine files untouched.
    """

    def test_productivity_engine_file_exists(self) -> None:
        engine_path = os.path.join(
            os.path.dirname(__file__), "..", "src", "productivity_indicator_engine.py"
        )
        self.assertTrue(os.path.isfile(engine_path))

    def test_productivity_policy_file_exists(self) -> None:
        policy_path = os.path.join(
            os.path.dirname(__file__), "..", "src", "productivity_forecast_denominator_policy.py"
        )
        self.assertTrue(os.path.isfile(policy_path))

    def test_productivity_engine_importable(self) -> None:
        from src.productivity_indicator_engine import get_productivity_capacity
        self.assertTrue(callable(get_productivity_capacity))


class TestConnectedSignalCardHTML(unittest.TestCase):
    """Card rendering contract checks."""

    def test_no_correlation_coefficients_in_html(self) -> None:
        tmpdir = tempfile.mkdtemp()
        cfg = _make_config_csv(tmpdir)
        kpi_def = _make_kpi_def_csv(tmpdir)
        actual = _make_actual_history_csv(tmpdir)
        result = cs_engine.run_connected_signal(
            hospital_id="HOSP-001",
            department_id="TEST-DEPT",
            selected_year=2025,
            selected_month=7,
            actual_history_path=actual,
            config_path=cfg,
            kpi_definition_path=kpi_def,
        )
        html = cs_engine.build_connected_signal_card_html(result, period_badge_html="ACTUAL")
        self.assertNotIn("Spearman", html)
        self.assertNotIn("r =", html)
        self.assertNotIn("p-value", html)
        self.assertNotIn("correlation", html)
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)

    def test_causality_footer_present(self) -> None:
        tmpdir = tempfile.mkdtemp()
        cfg = _make_config_csv(tmpdir)
        kpi_def = _make_kpi_def_csv(tmpdir)
        actual = _make_actual_history_csv(tmpdir)
        result = cs_engine.run_connected_signal(
            hospital_id="HOSP-001",
            department_id="TEST-DEPT",
            selected_year=2025,
            selected_month=7,
            actual_history_path=actual,
            config_path=cfg,
            kpi_definition_path=kpi_def,
        )
        html = cs_engine.build_connected_signal_card_html(result, period_badge_html="ACTUAL")
        self.assertIn("Causality is not confirmed", html)
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


class TestConnectedSignalRealData(unittest.TestCase):
    """Integration tests against the governed real data files."""

    def test_real_data_runs_without_error(self) -> None:
        result = cs_engine.run_connected_signal(
            hospital_id="HOSP-001",
            department_id="Administration",
            selected_year=2025,
            selected_month=7,
        )
        self.assertIn(result["status"], ("OK", "INSUFFICIENT_DATA"))
        self.assertIsInstance(result["relationships"], list)
        self.assertIn("governance", result)
        self.assertFalse(result["governance"]["causality_confirmed"])

    def test_real_data_forecast_continuation_runs(self) -> None:
        result = cs_engine.run_connected_signal(
            hospital_id="HOSP-001",
            department_id="Emergency Department",
            selected_year=2025,
            selected_month=8,
        )
        self.assertIn(result["status"], ("OK", "INSUFFICIENT_DATA"))
        if result.get("primary_chain"):
            self.assertIn("forecast_continuation", result)
            fc = result["forecast_continuation"]
            self.assertIn(fc["continuation_status"], ("CONTINUES", "PARTIAL", "NOT_CONTINUING", "NOT_APPLICABLE"))


if __name__ == "__main__":
    unittest.main()
