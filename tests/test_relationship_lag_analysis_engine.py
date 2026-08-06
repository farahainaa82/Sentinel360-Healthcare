"""Tests for Relationship Lag Analysis Engine — Step 2B-4."""

import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from relationship_analysis_models import TemporalInterpretation


@pytest.fixture(scope="module")
def lag():
    return pd.read_csv("data/analytical/analytical_kpi_lag_relationships.csv")


class TestLagAnalysis:
    def test_lag_correlation_within_bounds(self, lag):
        valid = lag["lagged_correlation"].dropna()
        assert ((valid >= -1) & (valid <= 1)).all()

    def test_temporal_interpretation_valid(self, lag):
        valid = {e.value for e in TemporalInterpretation}
        assert set(lag["temporal_interpretation"].unique()).issubset(valid)

    def test_lag_values_non_negative(self, lag):
        assert (lag["best_supported_lag"] >= 0).all()

    def test_observation_count_non_negative(self, lag):
        assert (lag["lagged_observation_count"] >= 0).all()

    def test_no_future_leakage(self, lag):
        # Lag must be non-negative (target shifted backward)
        assert (lag["best_supported_lag"] >= 0).all()

    def test_source_target_coverage(self, lag):
        kpi_ids = set(lag["source_kpi_id"].unique()) | set(lag["target_kpi_id"].unique())
        assert kpi_ids == {"kpi_001", "kpi_002", "kpi_003", "kpi_004", "kpi_005", "kpi_006"}
