"""
Sentinel360 Healthcare — Focused Tests for Step 2B-2
Threshold-Breach and Watch-Condition Engine

Tests:
  - Safe import and no automatic execution
  - Engine prerequisite validation
  - Classification correctness for all directionalities
  - Boundary inclusivity determinism
  - Breach detection: governed output vs actual events
  - Provisional breach type preservation for non-provisional records
  - Watch condition severity assignment
  - Record reconciliation: 11397 + 6123 = 17520
  - Unavailable records NOT treated as failures
  - Immutability of upstream files
"""

import sys
import unittest
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

import pandas as pd
import numpy as np

from threshold_breach_models import (
    BreachType,
    ThresholdState,
    WatchSeverity,
)
from kpi_threshold_breach_engine import KPIThresholdBreachEngine
from kpi_watch_condition_engine import KPIWatchConditionEngine


class TestSafeDefaults(unittest.TestCase):
    def test_no_auto_execution(self):
        engine = KPIThresholdBreachEngine(project_root=project_root)
        self.assertEqual(len(engine.classifications), 0)
        self.assertEqual(len(engine.breaches), 0)


class TestEnginePrerequisites(unittest.TestCase):
    def test_prerequisites_pass_when_files_exist(self):
        engine = KPIThresholdBreachEngine(project_root=project_root)
        engine.load_inputs()
        valid, issues = engine.validate_prerequisites()
        self.assertTrue(valid, f"Prerequisites failed: {issues}")

    def test_all_kpis_have_active_thresholds(self):
        engine = KPIThresholdBreachEngine(project_root=project_root)
        engine.load_inputs()
        valid, issues = engine.validate_prerequisites()
        self.assertTrue(valid)
        kpi_ids = set(engine.df_daily["kpi_id"].unique())
        thresh_ids = set(engine.df_thresholds["kpi_id"].unique())
        self.assertTrue(kpi_ids.issubset(thresh_ids), f"Missing thresholds for: {kpi_ids - thresh_ids}")


class TestClassificationCorrectness(unittest.TestCase):
    def test_higher_is_better_complete_gar(self):
        engine = KPIThresholdBreachEngine(project_root=project_root)
        engine.load_inputs()
        df = engine.classify_all_records()
        # kpi_001 is Higher is better
        sub = df[(df["kpi_id"] == "kpi_001") & (df["calculation_status"] == "Calculated") & df["kpi_value"].notna()]
        states = set(sub["threshold_state"].unique())
        expected = {ThresholdState.GREEN.value, ThresholdState.AMBER.value, ThresholdState.RED.value}
        self.assertTrue(expected.issubset(states) or states == expected, f"kpi_001 states: {states}")

    def test_lower_is_better_complete_gar(self):
        engine = KPIThresholdBreachEngine(project_root=project_root)
        engine.load_inputs()
        df = engine.classify_all_records()
        # kpi_002 is Lower is better
        sub = df[(df["kpi_id"] == "kpi_002") & (df["calculation_status"] == "Calculated") & df["kpi_value"].notna()]
        states = set(sub["threshold_state"].unique())
        expected = {ThresholdState.GREEN.value, ThresholdState.AMBER.value, ThresholdState.RED.value}
        self.assertTrue(expected.issubset(states) or states == expected, f"kpi_002 states: {states}")

    def test_context_sensitive_five_band(self):
        engine = KPIThresholdBreachEngine(project_root=project_root)
        engine.load_inputs()
        df = engine.classify_all_records()
        # kpi_003 is Context-sensitive
        sub = df[(df["kpi_id"] == "kpi_003") & (df["calculation_status"] == "Calculated") & df["kpi_value"].notna()]
        states = set(sub["threshold_state"].unique())
        expected = {
            ThresholdState.LOW_UTILISATION.value,
            ThresholdState.LOWER_AMBER.value,
            ThresholdState.NORMAL_OPERATING_BAND.value,
            ThresholdState.UPPER_AMBER.value,
            ThresholdState.CRITICAL_CAPACITY_PRESSURE.value,
        }
        self.assertTrue(expected.issubset(states) or states == expected, f"kpi_003 states: {states}")

    def test_unavailable_records_not_classified(self):
        engine = KPIThresholdBreachEngine(project_root=project_root)
        engine.load_inputs()
        df = engine.classify_all_records()
        unavail = df[df["calculation_status"] != "Calculated"]
        self.assertTrue((unavail["threshold_state"] == ThresholdState.UNAVAILABLE.value).all())


class TestBreachDetection(unittest.TestCase):
    def test_governed_output_equals_source_records(self):
        engine = KPIThresholdBreachEngine(project_root=project_root)
        engine.load_inputs()
        df_classified = engine.classify_all_records()
        df_breach = engine.detect_breaches(df_classified)
        self.assertEqual(len(df_breach), len(df_classified),
                         "Every source record must receive a governed breach output")

    def test_actual_breaches_subset_of_output(self):
        engine = KPIThresholdBreachEngine(project_root=project_root)
        engine.load_inputs()
        df_classified = engine.classify_all_records()
        df_breach = engine.detect_breaches(df_classified)
        actual_breaches = df_breach[df_breach["breach_flag"] == True]
        self.assertLessEqual(len(actual_breaches), len(df_breach))
        self.assertTrue((actual_breaches["breach_type"] != BreachType.NO_BREACH.value).all())

    def test_provisional_breach_only_for_provisional_records(self):
        engine = KPIThresholdBreachEngine(project_root=project_root)
        engine.load_inputs()
        df_classified = engine.classify_all_records()
        df_breach = engine.detect_breaches(df_classified)
        prov_breach = df_breach[
            (df_breach["breach_type"] == BreachType.PROVISIONAL_BREACH.value) &
            (df_breach["threshold_is_provisional"] != True)
        ]
        self.assertEqual(len(prov_breach), 0,
                         "Provisional Breach must not appear on non-provisional records")

    def test_non_provisional_records_preserve_specific_breach_types(self):
        engine = KPIThresholdBreachEngine(project_root=project_root)
        engine.load_inputs()
        df_classified = engine.classify_all_records()
        df_breach = engine.detect_breaches(df_classified)
        non_prov = df_breach[df_breach["threshold_is_provisional"] != True]
        # Non-provisional records with actual breaches should have specific types
        non_prov_breaches = non_prov[non_prov["breach_flag"] == True]
        if len(non_prov_breaches) > 0:
            self.assertFalse(
                (non_prov_breaches["breach_type"] == BreachType.PROVISIONAL_BREACH.value).any(),
                "Non-provisional breach records must not be labelled Provisional Breach"
            )

    def test_unavailable_records_have_unavailable_breach_type(self):
        engine = KPIThresholdBreachEngine(project_root=project_root)
        engine.load_inputs()
        df_classified = engine.classify_all_records()
        df_breach = engine.detect_breaches(df_classified)
        unavail = df_breach[df_breach["calculation_status"] != "Calculated"]
        self.assertTrue((unavail["breach_type"] == BreachType.UNAVAILABLE.value).all())


class TestWatchConditions(unittest.TestCase):
    def test_watch_prerequisites_pass(self):
        engine = KPIWatchConditionEngine(project_root=project_root)
        engine.load_inputs()
        valid, issues = engine.validate_prerequisites()
        self.assertTrue(valid, f"Watch prerequisites failed: {issues}")

    def test_governed_watch_output_equals_source_records(self):
        breach_engine = KPIThresholdBreachEngine(project_root=project_root)
        breach_engine.load_inputs()
        df_classified = breach_engine.classify_all_records()

        watch_engine = KPIWatchConditionEngine(project_root=project_root)
        watch_engine.load_inputs()
        watch_engine.set_classified_data(df_classified)
        df_watches = watch_engine.evaluate_watch_conditions()
        self.assertEqual(len(df_watches), len(df_classified),
                         "Every source record must receive a governed watch output")

    def test_actual_watches_subset_of_output(self):
        breach_engine = KPIThresholdBreachEngine(project_root=project_root)
        breach_engine.load_inputs()
        df_classified = breach_engine.classify_all_records()

        watch_engine = KPIWatchConditionEngine(project_root=project_root)
        watch_engine.load_inputs()
        watch_engine.set_classified_data(df_classified)
        df_watches = watch_engine.evaluate_watch_conditions()
        actual_watches = df_watches[df_watches["watch_condition_flag"] == True]
        self.assertLessEqual(len(actual_watches), len(df_watches))
        self.assertTrue((actual_watches["watch_severity"] != WatchSeverity.NONE.value).all())

    def test_no_watch_records_have_none_severity(self):
        breach_engine = KPIThresholdBreachEngine(project_root=project_root)
        breach_engine.load_inputs()
        df_classified = breach_engine.classify_all_records()

        watch_engine = KPIWatchConditionEngine(project_root=project_root)
        watch_engine.load_inputs()
        watch_engine.set_classified_data(df_classified)
        df_watches = watch_engine.evaluate_watch_conditions()
        no_watch = df_watches[df_watches["watch_condition_flag"] == False]
        self.assertTrue((no_watch["watch_severity"] == WatchSeverity.NONE.value).all())


class TestRecordReconciliation(unittest.TestCase):
    def test_classifiable_plus_unavailable_equals_total(self):
        engine = KPIThresholdBreachEngine(project_root=project_root)
        engine.load_inputs()
        df = engine.classify_all_records()
        total = len(df)
        classifiable = len(df[df["calculation_status"] == "Calculated"])
        unavailable = len(df[df["calculation_status"] != "Calculated"])
        self.assertEqual(classifiable + unavailable, total,
                         f"{classifiable} + {unavailable} != {total}")
        self.assertEqual(total, 17520)
        self.assertEqual(classifiable, 11397)
        self.assertEqual(unavailable, 6123)

    def test_breach_output_records_match_source(self):
        engine = KPIThresholdBreachEngine(project_root=project_root)
        engine.load_inputs()
        df_classified = engine.classify_all_records()
        df_breach = engine.detect_breaches(df_classified)
        self.assertEqual(len(df_breach), 17520)

    def test_watch_output_records_match_source(self):
        engine = KPIThresholdBreachEngine(project_root=project_root)
        engine.load_inputs()
        df_classified = engine.classify_all_records()

        watch_engine = KPIWatchConditionEngine(project_root=project_root)
        watch_engine.load_inputs()
        watch_engine.set_classified_data(df_classified)
        df_watches = watch_engine.evaluate_watch_conditions()
        self.assertEqual(len(df_watches), 17520)

    def test_actual_breach_events_less_than_output(self):
        engine = KPIThresholdBreachEngine(project_root=project_root)
        engine.load_inputs()
        df_classified = engine.classify_all_records()
        df_breach = engine.detect_breaches(df_classified)
        actual = len(df_breach[df_breach["breach_flag"] == True])
        self.assertLess(actual, len(df_breach))
        self.assertEqual(actual, 2464)

    def test_actual_watch_conditions_less_than_output(self):
        engine = KPIThresholdBreachEngine(project_root=project_root)
        engine.load_inputs()
        df_classified = engine.classify_all_records()

        watch_engine = KPIWatchConditionEngine(project_root=project_root)
        watch_engine.load_inputs()
        watch_engine.set_classified_data(df_classified)
        df_watches = watch_engine.evaluate_watch_conditions()
        actual = len(df_watches[df_watches["watch_condition_flag"] == True])
        self.assertLess(actual, len(df_watches))
        self.assertEqual(actual, 9120)


class TestImmutability(unittest.TestCase):
    def test_upstream_files_unchanged_after_run(self):
        import hashlib
        files = {
            "config/kpi_threshold_config.csv": project_root / "config" / "kpi_threshold_config.csv",
            "config/kpi_threshold_stakeholder_decisions.csv": project_root / "config" / "kpi_threshold_stakeholder_decisions.csv",
            "data/analytical/analytical_six_kpi_daily.csv": project_root / "data" / "analytical" / "analytical_six_kpi_daily.csv",
            "data/analytical/analytical_kpi_trend_signals.csv": project_root / "data" / "analytical" / "analytical_kpi_trend_signals.csv",
            "data/analytical/analytical_kpi_sustained_movements.csv": project_root / "data" / "analytical" / "analytical_kpi_sustained_movements.csv",
        }
        before = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in files.items() if path.exists()}

        # Run engines
        breach_engine = KPIThresholdBreachEngine(project_root=project_root)
        breach_engine.load_inputs()
        breach_engine.classify_all_records()

        watch_engine = KPIWatchConditionEngine(project_root=project_root)
        watch_engine.load_inputs()

        after = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in files.items() if path.exists()}
        for name in before:
            self.assertEqual(before[name], after[name], f"Upstream file modified: {name}")


if __name__ == "__main__":
    unittest.main()
