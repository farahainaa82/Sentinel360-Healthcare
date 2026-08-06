"""Tests for KPI Relationship Analysis Engine — Step 2B-4."""

import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from relationship_analysis_models import RelationshipDirection, RelationshipStrength, DataSufficiency


@pytest.fixture(scope="module")
def pairwise():
    return pd.read_csv("data/analytical/analytical_kpi_pairwise_relationships.csv")


@pytest.fixture(scope="module")
def stability():
    return pd.read_csv("data/analytical/analytical_kpi_department_relationship_stability.csv")


# ------------------------------------------------------------------
# Source preparation
# ------------------------------------------------------------------
class TestSourcePreparation:
    def test_six_kpi_coverage(self, pairwise):
        kpi_ids = set(pairwise["source_kpi_id"].unique()) | set(pairwise["target_kpi_id"].unique())
        assert kpi_ids == {"kpi_001", "kpi_002", "kpi_003", "kpi_004", "kpi_005", "kpi_006"}

    def test_fifteen_unique_pairs(self, pairwise):
        ids = pairwise[pairwise["grain"] == "hospital"]["relationship_id"].nunique()
        assert ids == 15

    def test_no_duplicate_pair_date_records(self, pairwise):
        for grain, group in pairwise.groupby("grain"):
            assert group["relationship_record_id"].nunique() == len(group)

    def test_unavailable_values_not_zero(self, pairwise):
        zero_obs = pairwise[pairwise["paired_observation_count"] == 0]
        if len(zero_obs) > 0:
            assert zero_obs["pearson_correlation"].isna().all()


# ------------------------------------------------------------------
# Association
# ------------------------------------------------------------------
class TestAssociation:
    def test_pearson_within_bounds(self, pairwise):
        valid = pairwise["pearson_correlation"].dropna()
        assert ((valid >= -1) & (valid <= 1)).all()

    def test_spearman_within_bounds(self, pairwise):
        valid = pairwise["spearman_correlation"].dropna()
        assert ((valid >= -1) & (valid <= 1)).all()

    def test_adversity_correlation_within_bounds(self, pairwise):
        valid = pairwise["adversity_correlation"].dropna()
        assert ((valid >= -1) & (valid <= 1)).all()

    def test_direction_categories_valid(self, pairwise):
        valid = {e.value for e in RelationshipDirection}
        assert set(pairwise["raw_relationship_direction"].unique()).issubset(valid)
        assert set(pairwise["adversity_relationship_direction"].unique()).issubset(valid)

    def test_strength_categories_valid(self, pairwise):
        valid = {e.value for e in RelationshipStrength}
        assert set(pairwise["raw_relationship_strength"].unique()).issubset(valid)
        assert set(pairwise["adversity_relationship_strength"].unique()).issubset(valid)


# ------------------------------------------------------------------
# Operational adversity
# ------------------------------------------------------------------
class TestOperationalAdversity:
    def test_adversity_direction_present(self, pairwise):
        assert "adversity_relationship_direction" in pairwise.columns
        assert "adversity_correlation" in pairwise.columns

    def test_raw_and_adversity_distinguished(self, pairwise):
        diff = pairwise[pairwise["raw_relationship_direction"] != pairwise["adversity_relationship_direction"]]
        if len(diff) > 0:
            assert diff["raw_relationship_direction"].notna().all()
            assert diff["adversity_relationship_direction"].notna().all()


# ------------------------------------------------------------------
# Co-occurrence
# ------------------------------------------------------------------
class TestCooccurrence:
    def test_cooccurrence_rates_within_bounds(self, pairwise):
        rates = pairwise["adverse_cooccurrence_rate"].dropna()
        assert ((rates >= 0) & (rates <= 1)).all()

    def test_conditional_rates_within_bounds(self, pairwise):
        rates = pairwise["conditional_adverse_rate"].dropna()
        assert ((rates >= 0) & (rates <= 1)).all()

    def test_counts_non_negative(self, pairwise):
        for col in ["both_assessable_count", "both_green_count", "both_amber_or_worse_count", "both_red_or_worse_count"]:
            assert (pairwise[col] >= 0).all()


# ------------------------------------------------------------------
# Trend alignment
# ------------------------------------------------------------------
class TestTrendAlignment:
    def test_trend_agreement_within_bounds(self, pairwise):
        rates = pairwise["trend_agreement_rate"].dropna()
        assert ((rates >= 0) & (rates <= 1)).all()

    def test_trend_counts_non_negative(self, pairwise):
        assert (pairwise["both_deteriorating_count"] >= 0).all()
        assert (pairwise["opposing_trend_count"] >= 0).all()


# ------------------------------------------------------------------
# Department stability
# ------------------------------------------------------------------
class TestDepartmentStability:
    def test_stability_categories_valid(self, stability):
        valid = {"Stable Across Departments", "Moderately Stable", "Department-Specific", "Unstable", "Insufficient Evidence"}
        assert set(stability["department_stability"].unique()).issubset(valid)

    def test_consistency_rate_within_bounds(self, stability):
        rates = stability["direction_consistency_rate"].dropna()
        assert ((rates >= 0) & (rates <= 1)).all()

    def test_departments_assessed_non_negative(self, stability):
        assert (stability["departments_assessed"] >= 0).all()


# ------------------------------------------------------------------
# Confidence
# ------------------------------------------------------------------
class TestConfidence:
    def test_confidence_categories_valid(self, pairwise):
        valid = {"High", "Moderate", "Low", "Insufficient Evidence"}
        assert set(pairwise["confidence_level"].unique()).issubset(valid)

    def test_high_confidence_has_sufficient_obs(self, pairwise):
        high = pairwise[pairwise["confidence_level"] == "High"]
        if len(high) > 0:
            assert (high["paired_observation_count"] >= 10).all()


# ------------------------------------------------------------------
# Governance
# ------------------------------------------------------------------
class TestGovernance:
    def test_engine_run_id_present(self, pairwise):
        assert pairwise["engine_run_id"].notna().all()

    def test_processed_at_present(self, pairwise):
        assert pairwise["processed_at"].notna().all()
