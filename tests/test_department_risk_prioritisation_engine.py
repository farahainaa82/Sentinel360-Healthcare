"""Tests for Department Risk Prioritisation Engine — Step 2B-3.

Loads pre-generated outputs via module-scoped fixture.
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))


@pytest.fixture(scope="module")
def dept_risk():
    return pd.read_csv(os.path.join(PROJECT_ROOT, "data/analytical/analytical_department_risk_daily.csv"))


@pytest.fixture(scope="module")
def kpi_risk():
    return pd.read_csv(os.path.join(PROJECT_ROOT, "data/analytical/analytical_kpi_risk_scores_daily.csv"))


@pytest.fixture(scope="module")
def ranking():
    return pd.read_csv(os.path.join(PROJECT_ROOT, "data/analytical/analytical_department_risk_ranking.csv"))


@pytest.fixture(scope="module")
def drivers():
    return pd.read_csv(os.path.join(PROJECT_ROOT, "data/analytical/analytical_department_risk_drivers.csv"))


# ------------------------------------------------------------------
# Aggregation integrity
# ------------------------------------------------------------------
class TestAggregation:
    def test_department_count_matches_expected(self, dept_risk):
        # 1 hospital * 8 departments * 365 days = 2920
        assert len(dept_risk) == 2920

    def test_score_range_zero_to_hundred(self, dept_risk):
        assert dept_risk["department_risk_score_normalized"].min() >= 0.0
        assert dept_risk["department_risk_score_normalized"].max() <= 100.0

    def test_assessable_count_matches_kpi(self, dept_risk, kpi_risk):
        # Verify that assessable KPI counts in department match grouped KPI data
        merged = dept_risk.merge(
            kpi_risk.groupby(["hospital_id", "department_id", "reporting_date"]).apply(
                lambda g: (g["calculation_status"] == "Calculated").sum(), include_groups=False
            ).rename("expected_assessable").reset_index(),
            on=["hospital_id", "department_id", "reporting_date"],
            how="left"
        )
        assert (merged["assessable_kpi_count"] == merged["expected_assessable"]).all()

    def test_unavailable_count_correct(self, dept_risk, kpi_risk):
        merged = dept_risk.merge(
            kpi_risk.groupby(["hospital_id", "department_id", "reporting_date"]).apply(
                lambda g: (g["calculation_status"] != "Calculated").sum(), include_groups=False
            ).rename("expected_unavailable").reset_index(),
            on=["hospital_id", "department_id", "reporting_date"],
            how="left"
        )
        assert (merged["unavailable_kpi_count"] == merged["expected_unavailable"]).all()


# ------------------------------------------------------------------
# Severe outlier preservation
# ------------------------------------------------------------------
class TestOutlierPreservation:
    def test_max_kpi_score_not_hidden_by_average(self, dept_risk):
        # For every department, max score should be >= average
        assert (dept_risk["maximum_kpi_risk_score"] >= dept_risk["average_assessable_kpi_risk_score"].fillna(0)).all()

    def test_critical_department_has_severe_conditions(self, dept_risk):
        critical_depts = dept_risk[dept_risk["department_priority_tier"] == "Critical"]
        if len(critical_depts) > 0:
            # Critical tier can arise from aggregation; check at least one severe indicator
            has_severe = (
                (critical_depts["critical_kpi_count"] > 0) |
                (critical_depts["red_kpi_count"] > 0) |
                (critical_depts["maximum_kpi_risk_score"] >= 75)
            )
            assert has_severe.all()


# ------------------------------------------------------------------
# Multi-KPI concurrence
# ------------------------------------------------------------------
class TestConcurrence:
    def test_concurrence_flag_when_multiple_kpis_at_risk(self, dept_risk):
        concurrent = dept_risk[dept_risk["concurrent_risk_flag"] == True]
        if len(concurrent) > 0:
            assert (concurrent["concurrent_kpi_count"] >= 2).all()

    def test_concurrence_score_non_negative(self, dept_risk):
        assert (dept_risk["concurrence_score"].fillna(0) >= 0).all()


# ------------------------------------------------------------------
# Dominant driver
# ------------------------------------------------------------------
class TestDominantDriver:
    def test_dominant_driver_exists_for_assessable(self, dept_risk):
        assessable = dept_risk[dept_risk["assessable_kpi_count"] > 0]
        assert assessable["dominant_kpi_id"].notna().all()

    def test_dominant_driver_score_is_max(self, dept_risk, kpi_risk):
        # For a sample of departments, verify dominant score matches max KPI score
        sample = dept_risk.sample(min(100, len(dept_risk)), random_state=42)
        for _, drow in sample.iterrows():
            hid, did, rdate = drow["hospital_id"], drow["department_id"], drow["reporting_date"]
            kpis = kpi_risk[
                (kpi_risk["hospital_id"] == hid) &
                (kpi_risk["department_id"] == did) &
                (kpi_risk["reporting_date"] == rdate) &
                (kpi_risk["calculation_status"] == "Calculated")
            ]
            if len(kpis) > 0:
                max_score = kpis["kpi_risk_score_normalized"].max()
                assert abs(drow["dominant_kpi_score"] - max_score) < 0.01

    def test_provisional_dominator_flagged(self, dept_risk):
        prov_dom = dept_risk[dept_risk["dominant_driver_is_provisional"] == True]
        if len(prov_dom) > 0:
            assert (prov_dom["provisional_risk_flag"] == True).all()


# ------------------------------------------------------------------
# Priority tier and urgency
# ------------------------------------------------------------------
class TestDepartmentTierUrgency:
    def test_tiers_valid(self, dept_risk):
        valid = {"Stable", "Monitor", "Elevated", "High", "Critical", "Not Assessable"}
        assert set(dept_risk["department_priority_tier"].unique()).issubset(valid)

    def test_urgency_valid(self, dept_risk):
        valid = {"Routine Monitoring", "Review Soon", "Prompt Review", "Immediate Review", "Not Assessable"}
        assert set(dept_risk["urgency_level"].unique()).issubset(valid)

    def test_critical_tier_is_immediate_or_prompt(self, dept_risk):
        critical = dept_risk[dept_risk["department_priority_tier"] == "Critical"]
        if len(critical) > 0:
            assert critical["urgency_level"].isin(["Immediate Review", "Prompt Review"]).all()


# ------------------------------------------------------------------
# Ranking
# ------------------------------------------------------------------
class TestRanking:
    def test_ranking_deterministic_and_complete(self, ranking, dept_risk):
        # Every department-date should have exactly one rank
        assert len(ranking) == len(dept_risk)

    def test_rank_within_hospital_matches_department_count(self, ranking, dept_risk):
        max_rank = ranking.groupby(["hospital_id", "reporting_date"])["rank_within_hospital"].max().reset_index()
        expected = dept_risk.groupby(["hospital_id", "reporting_date"]).size().reset_index(name="expected")
        merged = max_rank.merge(expected, on=["hospital_id", "reporting_date"])
        assert (merged["rank_within_hospital"] == merged["expected"]).all()

    def test_not_assessable_does_not_outrank_assessable(self, ranking):
        # This is implicitly handled by tier ordering; check no rank=1 is Not Assessable
        rank1 = ranking[ranking["rank_within_hospital"] == 1]
        assert (rank1["department_priority_tier"] != "Not Assessable").all()


# ------------------------------------------------------------------
# Governance propagation
# ------------------------------------------------------------------
class TestDepartmentGovernance:
    def test_provisional_flag_propagated(self, dept_risk):
        prov = dept_risk[dept_risk["provisional_risk_flag"] == True]
        if len(prov) > 0:
            assert (prov["provisional_kpi_count"] > 0).all()

    def test_governance_warning_for_provisional(self, dept_risk):
        prov = dept_risk[dept_risk["provisional_risk_flag"] == True]
        if len(prov) > 0:
            assert prov["governance_warning"].str.len().gt(0).all()

    def test_contains_provisional_kpi_matches_provisional_count(self, dept_risk):
        # contains_provisional_kpi should be True whenever provisional_kpi_count > 0
        has_count = dept_risk["provisional_kpi_count"] > 0
        has_flag = dept_risk["contains_provisional_kpi"] == True
        assert (has_count == has_flag).all()

    def test_materiality_categories_valid(self, dept_risk):
        valid = {"None", "Minor", "Material", "Dominant"}
        observed = set(dept_risk["provisional_contribution_materiality"].dropna().unique())
        assert observed.issubset(valid)

    def test_provisional_risk_flag_only_material_or_dominant(self, dept_risk):
        flagged = dept_risk[dept_risk["provisional_risk_flag"] == True]
        assert flagged["provisional_contribution_materiality"].isin(["Material", "Dominant"]).all()

    def test_dominant_driver_is_provisional_implies_materiality_dominant(self, dept_risk):
        dom_prov = dept_risk[dept_risk["dominant_driver_is_provisional"] == True]
        if len(dom_prov) > 0:
            assert (dom_prov["provisional_contribution_materiality"] == "Dominant").all()
            assert (dom_prov["provisional_risk_flag"] == True).all()


# ------------------------------------------------------------------
# Provisional materiality — unit tests with synthetic data
# ------------------------------------------------------------------
class TestProvisionalMateriality:
    """Six targeted scenarios for provisional KPI governance refinement."""

    def _make_engine(self):
        from department_risk_prioritisation_engine import DepartmentRiskPrioritisationEngine
        engine = DepartmentRiskPrioritisationEngine(engine_run_id="TEST-MAT")
        engine.load_configs()
        return engine

    def _make_kpi_df(self, rows):
        return pd.DataFrame(rows)

    def test_provisional_green_non_contributing(self):
        """Provisional KPI present but Green and non-contributing (score 0)."""
        engine = self._make_engine()
        kpi_df = self._make_kpi_df([
            {"hospital_id": "H1", "department_id": "D1", "reporting_date": "2026-01-01",
             "kpi_id": "kpi_003", "kpi_name": "Provisional Green", "threshold_state": "Green",
             "kpi_risk_score_normalized": 0.0, "calculation_status": "Calculated",
             "threshold_is_provisional": True, "confidence_level": "High", "confidence_score": 0.9,
             "watch_condition_flag": False, "watch_severity": "None",
             "repeated_red_flag": False, "repeated_amber_flag": False,
             "operational_trend_interpretation": "Stable", "risk_reason": ""},
            {"hospital_id": "H1", "department_id": "D1", "reporting_date": "2026-01-01",
             "kpi_id": "kpi_001", "kpi_name": "Stable KPI", "threshold_state": "Green",
             "kpi_risk_score_normalized": 5.0, "calculation_status": "Calculated",
             "threshold_is_provisional": False, "confidence_level": "High", "confidence_score": 0.9,
             "watch_condition_flag": False, "watch_severity": "None",
             "repeated_red_flag": False, "repeated_amber_flag": False,
             "operational_trend_interpretation": "Stable", "risk_reason": ""},
        ])
        dept = engine.run(kpi_df)
        row = dept.iloc[0]
        assert row["contains_provisional_kpi"] == True
        assert row["provisional_risk_contribution"] == 0.0
        assert row["provisional_contribution_materiality"] == "None"
        assert row["provisional_risk_flag"] == False
        assert row["dominant_driver_is_provisional"] == False

    def test_provisional_unavailable(self):
        """Provisional KPI unavailable (not assessable)."""
        engine = self._make_engine()
        kpi_df = self._make_kpi_df([
            {"hospital_id": "H1", "department_id": "D1", "reporting_date": "2026-01-01",
             "kpi_id": "kpi_003", "kpi_name": "Provisional Unavailable", "threshold_state": "Green",
             "kpi_risk_score_normalized": 0.0, "calculation_status": "Data Unavailable",
             "threshold_is_provisional": True, "confidence_level": "Insufficient Evidence", "confidence_score": 0.1,
             "watch_condition_flag": False, "watch_severity": "None",
             "repeated_red_flag": False, "repeated_amber_flag": False,
             "operational_trend_interpretation": "Stable", "risk_reason": ""},
            {"hospital_id": "H1", "department_id": "D1", "reporting_date": "2026-01-01",
             "kpi_id": "kpi_001", "kpi_name": "Stable KPI", "threshold_state": "Green",
             "kpi_risk_score_normalized": 5.0, "calculation_status": "Calculated",
             "threshold_is_provisional": False, "confidence_level": "High", "confidence_score": 0.9,
             "watch_condition_flag": False, "watch_severity": "None",
             "repeated_red_flag": False, "repeated_amber_flag": False,
             "operational_trend_interpretation": "Stable", "risk_reason": ""},
        ])
        dept = engine.run(kpi_df)
        row = dept.iloc[0]
        assert row["contains_provisional_kpi"] == True
        assert row["provisional_risk_contribution"] == 0.0
        assert row["provisional_contribution_materiality"] == "None"
        assert row["provisional_risk_flag"] == False

    def test_provisional_minor_contribution(self):
        """Provisional KPI with minor contribution (below minor threshold)."""
        engine = self._make_engine()
        kpi_df = self._make_kpi_df([
            {"hospital_id": "H1", "department_id": "D1", "reporting_date": "2026-01-01",
             "kpi_id": "kpi_003", "kpi_name": "Provisional Minor", "threshold_state": "Amber",
             "kpi_risk_score_normalized": 3.0, "calculation_status": "Calculated",
             "threshold_is_provisional": True, "confidence_level": "High", "confidence_score": 0.9,
             "watch_condition_flag": False, "watch_severity": "None",
             "repeated_red_flag": False, "repeated_amber_flag": False,
             "operational_trend_interpretation": "Stable", "risk_reason": ""},
            {"hospital_id": "H1", "department_id": "D1", "reporting_date": "2026-01-01",
             "kpi_id": "kpi_001", "kpi_name": "Stable KPI", "threshold_state": "Green",
             "kpi_risk_score_normalized": 5.0, "calculation_status": "Calculated",
             "threshold_is_provisional": False, "confidence_level": "High", "confidence_score": 0.9,
             "watch_condition_flag": False, "watch_severity": "None",
             "repeated_red_flag": False, "repeated_amber_flag": False,
             "operational_trend_interpretation": "Stable", "risk_reason": ""},
        ])
        dept = engine.run(kpi_df)
        row = dept.iloc[0]
        assert row["contains_provisional_kpi"] == True
        assert row["provisional_risk_contribution"] == 3.0
        assert row["provisional_contribution_materiality"] == "Minor"
        assert row["provisional_risk_flag"] == False

    def test_provisional_material_affects_score(self):
        """Provisional KPI materially affecting department score but not dominant."""
        engine = self._make_engine()
        kpi_df = self._make_kpi_df([
            {"hospital_id": "H1", "department_id": "D1", "reporting_date": "2026-01-01",
             "kpi_id": "kpi_003", "kpi_name": "Provisional Material", "threshold_state": "Red",
             "kpi_risk_score_normalized": 20.0, "calculation_status": "Calculated",
             "threshold_is_provisional": True, "confidence_level": "High", "confidence_score": 0.9,
             "watch_condition_flag": False, "watch_severity": "None",
             "repeated_red_flag": False, "repeated_amber_flag": False,
             "operational_trend_interpretation": "Stable", "risk_reason": ""},
            {"hospital_id": "H1", "department_id": "D1", "reporting_date": "2026-01-01",
             "kpi_id": "kpi_001", "kpi_name": "Higher Non-Prov", "threshold_state": "Red",
             "kpi_risk_score_normalized": 30.0, "calculation_status": "Calculated",
             "threshold_is_provisional": False, "confidence_level": "High", "confidence_score": 0.95,
             "watch_condition_flag": False, "watch_severity": "None",
             "repeated_red_flag": False, "repeated_amber_flag": False,
             "operational_trend_interpretation": "Stable", "risk_reason": ""},
            {"hospital_id": "H1", "department_id": "D1", "reporting_date": "2026-01-01",
             "kpi_id": "kpi_002", "kpi_name": "Stable KPI", "threshold_state": "Green",
             "kpi_risk_score_normalized": 5.0, "calculation_status": "Calculated",
             "threshold_is_provisional": False, "confidence_level": "High", "confidence_score": 0.9,
             "watch_condition_flag": False, "watch_severity": "None",
             "repeated_red_flag": False, "repeated_amber_flag": False,
             "operational_trend_interpretation": "Stable", "risk_reason": ""},
        ])
        dept = engine.run(kpi_df)
        row = dept.iloc[0]
        assert row["contains_provisional_kpi"] == True
        assert row["provisional_risk_contribution"] == 20.0
        assert row["provisional_contribution_materiality"] == "Material"
        assert row["provisional_risk_flag"] == True

    def test_provisional_dominant_driver(self):
        """Provisional KPI is the dominant risk driver."""
        engine = self._make_engine()
        kpi_df = self._make_kpi_df([
            {"hospital_id": "H1", "department_id": "D1", "reporting_date": "2026-01-01",
             "kpi_id": "kpi_003", "kpi_name": "Provisional Dominant", "threshold_state": "Red",
             "kpi_risk_score_normalized": 25.0, "calculation_status": "Calculated",
             "threshold_is_provisional": True, "confidence_level": "High", "confidence_score": 0.9,
             "watch_condition_flag": False, "watch_severity": "None",
             "repeated_red_flag": False, "repeated_amber_flag": False,
             "operational_trend_interpretation": "Stable", "risk_reason": ""},
            {"hospital_id": "H1", "department_id": "D1", "reporting_date": "2026-01-01",
             "kpi_id": "kpi_001", "kpi_name": "Stable KPI", "threshold_state": "Green",
             "kpi_risk_score_normalized": 5.0, "calculation_status": "Calculated",
             "threshold_is_provisional": False, "confidence_level": "High", "confidence_score": 0.9,
             "watch_condition_flag": False, "watch_severity": "None",
             "repeated_red_flag": False, "repeated_amber_flag": False,
             "operational_trend_interpretation": "Stable", "risk_reason": ""},
        ])
        dept = engine.run(kpi_df)
        row = dept.iloc[0]
        assert row["contains_provisional_kpi"] == True
        assert row["provisional_risk_contribution"] == 25.0
        assert row["provisional_contribution_materiality"] == "Dominant"
        assert row["provisional_risk_flag"] == True
        assert row["dominant_driver_is_provisional"] == True
        assert row["dominant_kpi_id"] == "kpi_003"

    def test_department_no_provisional_contribution(self):
        """Department containing no provisional KPIs at all."""
        engine = self._make_engine()
        kpi_df = self._make_kpi_df([
            {"hospital_id": "H1", "department_id": "D1", "reporting_date": "2026-01-01",
             "kpi_id": "kpi_001", "kpi_name": "Stable KPI", "threshold_state": "Green",
             "kpi_risk_score_normalized": 5.0, "calculation_status": "Calculated",
             "threshold_is_provisional": False, "confidence_level": "High", "confidence_score": 0.9,
             "watch_condition_flag": False, "watch_severity": "None",
             "repeated_red_flag": False, "repeated_amber_flag": False,
             "operational_trend_interpretation": "Stable", "risk_reason": ""},
            {"hospital_id": "H1", "department_id": "D1", "reporting_date": "2026-01-01",
             "kpi_id": "kpi_002", "kpi_name": "Another KPI", "threshold_state": "Green",
             "kpi_risk_score_normalized": 8.0, "calculation_status": "Calculated",
             "threshold_is_provisional": False, "confidence_level": "High", "confidence_score": 0.9,
             "watch_condition_flag": False, "watch_severity": "None",
             "repeated_red_flag": False, "repeated_amber_flag": False,
             "operational_trend_interpretation": "Stable", "risk_reason": ""},
        ])
        dept = engine.run(kpi_df)
        row = dept.iloc[0]
        assert row["contains_provisional_kpi"] == False
        assert row["provisional_risk_contribution"] == 0.0
        assert row["provisional_contribution_materiality"] == "None"
        assert row["provisional_risk_flag"] == False
        assert row["dominant_driver_is_provisional"] == False


# ------------------------------------------------------------------
# Data availability
# ------------------------------------------------------------------
class TestDataAvailability:
    def test_data_availability_status_valid(self, dept_risk):
        valid = {"Complete", "Sufficient", "Limited", "Insufficient"}
        assert set(dept_risk["data_availability_status"].unique()).issubset(valid)

    def test_insufficient_assessable_flagged(self, dept_risk):
        insuff = dept_risk[dept_risk["assessable_kpi_count"] < 4]
        if len(insuff) > 0:
            assert insuff["data_availability_status"].isin(["Limited", "Insufficient"]).all()
