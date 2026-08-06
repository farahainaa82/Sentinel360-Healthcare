"""Tests for Contributing Factor Analysis Engine — Step 2B-4."""

import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from relationship_analysis_models import ContributingFactorClassification, ContradictionSeverity


@pytest.fixture(scope="module")
def cf():
    return pd.read_csv("data/analytical/analytical_contributing_factor_scores.csv")


@pytest.fixture(scope="module")
def hypotheses():
    path = "data/analytical/analytical_potential_root_cause_hypotheses.csv"
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=[
            "hypothesis_id", "hospital_id", "department_id", "reporting_date",
            "department_priority_tier", "source_kpi_id", "target_kpi_id",
            "contributing_factor_score_normalized", "confidence_level",
            "causality_status", "stakeholder_validation_required",
            "observed_problem_summary", "potential_contributing_factor",
            "potential_pathway", "evidence_for", "contradiction_severity",
        ])


@pytest.fixture(scope="module")
def network():
    return pd.read_csv("data/analytical/analytical_relationship_network_edges.csv")


class TestContributingFactorScores:
    def test_scores_within_range(self, cf):
        scores = cf["contributing_factor_score_normalized"].dropna()
        if len(scores) > 0:
            assert (scores >= 0).all()
            assert (scores <= 100).all()

    def test_components_within_range(self, cf):
        for col in ["association_component", "cooccurrence_component", "temporal_component",
                    "trend_component", "department_stability_component", "time_stability_component",
                    "plausibility_component", "evidence_quality_component"]:
            vals = cf[col].dropna()
            if len(vals) > 0:
                assert (vals >= 0).all()
                assert (vals <= 100).all()

    def test_classification_categories_valid(self, cf):
        valid = {e.value for e in ContributingFactorClassification}
        assert set(cf["contributing_factor_classification"].unique()).issubset(valid)

    def test_contradiction_severity_valid(self, cf):
        valid = {e.value for e in ContradictionSeverity}
        actual = set(cf["contradiction_severity"].dropna().unique())
        assert actual.issubset(valid)

    def test_major_contradiction_prevents_strong_hypothesis(self, cf):
        major = cf[cf["contradiction_severity"] == "Major"]
        if len(major) > 0:
            assert not (major["contributing_factor_classification"] == "Strong Contributing-Factor Hypothesis").any()

    def test_provisional_flag_consistent(self, cf):
        prov = cf[cf["contains_provisional_kpi"] == True]
        if len(prov) > 0:
            assert prov["provisional_kpi_list"].notna().all()


class TestRootCauseHypotheses:
    def test_causality_status_fixed(self, hypotheses):
        assert (hypotheses["causality_status"] == "Not Confirmed").all()

    def test_stakeholder_validation_required(self, hypotheses):
        assert hypotheses["stakeholder_validation_required"].all()

    def test_high_or_critical_only(self, hypotheses):
        valid_tiers = {"High", "Critical"}
        assert set(hypotheses["department_priority_tier"].unique()).issubset(valid_tiers)

    def test_no_prohibited_causal_language(self, hypotheses):
        bad = ["caused", "directly caused", "root cause confirmed", "proven driver", "responsible for"]
        for text_col in ["observed_problem_summary", "potential_contributing_factor", "potential_pathway"]:
            for phrase in bad:
                assert not hypotheses[text_col].str.lower().str.contains(phrase).any()

    def test_evidence_for_present(self, hypotheses):
        assert hypotheses["evidence_for"].notna().all()


class TestNetworkEdges:
    def test_active_edge_flag_logical(self, network):
        # Active edges should have reasonable scores
        active = network[network["active_edge_flag"] == True]
        if len(active) > 0:
            assert (active["contributing_factor_score"] > 20).all()

    def test_edge_ids_unique(self, network):
        assert network["relationship_edge_id"].nunique() == len(network)

    def test_fifteen_edges(self, network):
        assert len(network) == 15


class TestEngineInternals:
    """Unit tests for internal engine logic not covered by output-data tests."""

    @pytest.fixture(scope="class")
    def engine(self):
        from contributing_factor_analysis_engine import ContributingFactorAnalysisEngine
        return ContributingFactorAnalysisEngine()

    def test_detect_contradictions_severity_upgrades(self, engine):
        """Ensure severity upgrades from MINOR -> MATERIAL -> MAJOR correctly."""
        row = pd.Series({
            "pearson_correlation": -0.5,
            "trend_agreement_rate": 0.2,
            "paired_observation_count": 365,
        })
        lag_row = pd.DataFrame()
        stab_row = pd.DataFrame([{"direction_consistency_rate": 0.2}])
        flag, sev, summary = engine._detect_contradictions(row, lag_row, stab_row)
        assert flag is True
        assert sev == "Material"
        assert "Opposite direction correlation" in summary
        assert "Pooled direction differs from most departments" in summary

    def test_detect_contradictions_no_contradiction(self, engine):
        row = pd.Series({
            "pearson_correlation": 0.8,
            "trend_agreement_rate": 0.9,
            "paired_observation_count": 365,
        })
        lag_row = pd.DataFrame()
        stab_row = pd.DataFrame([{"direction_consistency_rate": 0.9}])
        flag, sev, summary = engine._detect_contradictions(row, lag_row, stab_row)
        assert flag is False
        assert sev == "No Contradiction"
        assert summary == ""

    def test_detect_contradictions_low_observations(self, engine):
        row = pd.Series({
            "pearson_correlation": 0.8,
            "trend_agreement_rate": 0.9,
            "paired_observation_count": 5,
        })
        lag_row = pd.DataFrame()
        stab_row = pd.DataFrame([{"direction_consistency_rate": 0.9}])
        flag, sev, summary = engine._detect_contradictions(row, lag_row, stab_row)
        assert flag is True
        assert sev == "Minor"
        assert "Very limited observation count" in summary

    def test_classify_cf_major_contradiction(self, engine):
        assert engine._classify_cf(80, "Major") == ContributingFactorClassification.WEAK_ASSOCIATION
        assert engine._classify_cf(10, "Major") == ContributingFactorClassification.NO_SUPPORTED_RELATIONSHIP

    def test_classify_cf_score_bands(self, engine):
        # Thresholds from config: plausible_min=40.0, strong_min=65.0
        assert engine._classify_cf(15, "None") == ContributingFactorClassification.NO_SUPPORTED_RELATIONSHIP
        assert engine._classify_cf(25, "None") == ContributingFactorClassification.WEAK_ASSOCIATION
        assert engine._classify_cf(37, "None") == ContributingFactorClassification.SUPPORTED_ASSOCIATION
        assert engine._classify_cf(45, "None") == ContributingFactorClassification.PLAUSIBLE_CONTRIBUTING_FACTOR
        assert engine._classify_cf(70, "None") == ContributingFactorClassification.STRONG_CONTRIBUTING_FACTOR_HYPOTHESIS

    def test_provisional_governance(self, engine):
        flag, mat, lst = engine._provisional_governance("kpi_001", "kpi_003")
        assert flag is True
        assert mat == "Material"
        assert "kpi_003" in lst

        flag, mat, lst = engine._provisional_governance("kpi_001", "kpi_002")
        assert flag is False
        assert mat == "No Contradiction"

    def test_network_edges_prefers_pooled_grain(self, engine):
        cf_df = pd.DataFrame([
            {"relationship_id": "r1", "hospital_id": "H1", "department_id": "ALL", "source_kpi_id": "kpi_001", "source_kpi_name": "A", "target_kpi_id": "kpi_002", "target_kpi_name": "B", "association_component": 50, "contributing_factor_score_normalized": 60, "contributing_factor_classification": "Plausible Contributing Factor", "confidence_level": "Moderate", "provisional_relationship_flag": False, "contradiction_flag": False},
            {"relationship_id": "r1", "hospital_id": "H1", "department_id": "DEPT-X", "source_kpi_id": "kpi_001", "source_kpi_name": "A", "target_kpi_id": "kpi_002", "target_kpi_name": "B", "association_component": 30, "contributing_factor_score_normalized": 40, "contributing_factor_classification": "Weak Association", "confidence_level": "Low", "provisional_relationship_flag": False, "contradiction_flag": False},
        ])
        edges = engine.build_network_edges(cf_df)
        assert len(edges) == 1
        assert edges.iloc[0]["contributing_factor_score"] == 60
        assert edges.iloc[0]["relationship_strength"] == "Plausible Contributing Factor"
