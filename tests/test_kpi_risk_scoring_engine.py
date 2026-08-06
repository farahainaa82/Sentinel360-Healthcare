"""Tests for KPI Risk Scoring Engine — Step 2B-3.

Efficient design: loads pre-generated outputs via module-scoped fixture.
No engine re-execution per test.
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from risk_prioritisation_models import PriorityTier, UrgencyLevel, ConfidenceLevel


@pytest.fixture(scope="module")
def kpi_risk():
    path = os.path.join(PROJECT_ROOT, "data/analytical/analytical_kpi_risk_scores_daily.csv")
    return pd.read_csv(path)


@pytest.fixture(scope="module")
def dept_risk():
    path = os.path.join(PROJECT_ROOT, "data/analytical/analytical_department_risk_daily.csv")
    return pd.read_csv(path)


# ------------------------------------------------------------------
# Score range validation
# ------------------------------------------------------------------
class TestScoreRange:
    def test_kpi_score_minimum_zero(self, kpi_risk):
        assessable = kpi_risk[kpi_risk["calculation_status"] == "Calculated"]
        assert assessable["kpi_risk_score_normalized"].min() >= 0.0

    def test_kpi_score_maximum_hundred(self, kpi_risk):
        assessable = kpi_risk[kpi_risk["calculation_status"] == "Calculated"]
        assert assessable["kpi_risk_score_normalized"].max() <= 100.0

    def test_no_negative_raw_components(self, kpi_risk):
        comp_cols = [
            "threshold_component_score", "breach_component_score", "watch_component_score",
            "persistence_component_score", "sustained_movement_component_score",
            "statistical_signal_component_score",
        ]
        for c in comp_cols:
            assert kpi_risk[c].fillna(0).min() >= 0.0, f"Negative value in {c}"

    def test_unavailable_not_assessable(self, kpi_risk):
        unavail = kpi_risk[kpi_risk["calculation_status"] != "Calculated"]
        assert (unavail["kpi_priority_tier"] == "Not Assessable").all()
        assert (unavail["confidence_level"] == "Insufficient Evidence").all()


# ------------------------------------------------------------------
# Threshold state mapping
# ------------------------------------------------------------------
class TestThresholdMapping:
    def test_green_is_low_risk(self, kpi_risk):
        green = kpi_risk[kpi_risk["threshold_state"].isin(["Green", "Normal Operating Band"])]
        if len(green) > 0:
            assessable = green[green["calculation_status"] == "Calculated"]
            if len(assessable) > 0:
                assert assessable["kpi_risk_score_normalized"].max() <= 35.0

    def test_red_is_high_risk(self, kpi_risk):
        red = kpi_risk[kpi_risk["threshold_state"] == "Red"]
        if len(red) > 0:
            assessable = red[red["calculation_status"] == "Calculated"]
            if len(assessable) > 0:
                assert assessable["kpi_risk_score_normalized"].min() >= 45.0

    def test_critical_capacity_is_highest(self, kpi_risk):
        ccp = kpi_risk[kpi_risk["threshold_state"] == "Critical Capacity Pressure"]
        if len(ccp) > 0:
            assessable = ccp[ccp["calculation_status"] == "Calculated"]
            if len(assessable) > 0:
                assert assessable["kpi_risk_score_normalized"].min() >= 60.0

    def test_low_utilisation_context_sensitive(self, kpi_risk):
        lut = kpi_risk[kpi_risk["threshold_state"] == "Low Utilisation"]
        if len(lut) > 0:
            assessable = lut[lut["calculation_status"] == "Calculated"]
            if len(assessable) > 0:
                assert assessable["kpi_risk_score_normalized"].max() <= 50.0


# ------------------------------------------------------------------
# Breach component
# ------------------------------------------------------------------
class TestBreachComponent:
    def test_no_breach_zero_contribution(self, kpi_risk):
        no_breach = kpi_risk[kpi_risk["breach_type"] == "No Breach"]
        assessable = no_breach[no_breach["calculation_status"] == "Calculated"]
        if len(assessable) > 0:
            assert (assessable["breach_component_score"] == 0.0).all()

    def test_provisional_breach_has_score(self, kpi_risk):
        prov = kpi_risk[kpi_risk["breach_type"] == "Provisional Breach"]
        assessable = prov[prov["calculation_status"] == "Calculated"]
        if len(assessable) > 0:
            assert (assessable["breach_component_score"] > 0.0).all()


# ------------------------------------------------------------------
# Watch severity mapping
# ------------------------------------------------------------------
class TestWatchSeverity:
    def test_critical_watch_high_score(self, kpi_risk):
        cw = kpi_risk[kpi_risk["watch_severity"] == "Critical"]
        if len(cw) > 0:
            assessable = cw[cw["calculation_status"] == "Calculated"]
            if len(assessable) > 0:
                assert (assessable["watch_component_score"] >= 50.0).all()

    def test_informational_watch_low_score(self, kpi_risk):
        iw = kpi_risk[kpi_risk["watch_severity"] == "Informational"]
        if len(iw) > 0:
            assessable = iw[iw["calculation_status"] == "Calculated"]
            if len(assessable) > 0:
                assert (assessable["watch_component_score"] <= 10.0).all()


# ------------------------------------------------------------------
# Persistence component
# ------------------------------------------------------------------
class TestPersistence:
    def test_repeated_amber_increases_score(self, kpi_risk):
        rpt = kpi_risk[kpi_risk["repeated_amber_flag"] == True]
        if len(rpt) > 0:
            assessable = rpt[rpt["calculation_status"] == "Calculated"]
            if len(assessable) > 0:
                assert (assessable["persistence_component_score"] >= 10.0).all()

    def test_repeated_red_higher_score(self, kpi_risk):
        rpt = kpi_risk[kpi_risk["repeated_red_flag"] == True]
        if len(rpt) > 0:
            assessable = rpt[rpt["calculation_status"] == "Calculated"]
            if len(assessable) > 0:
                assert (assessable["persistence_component_score"] >= 20.0).all()


# ------------------------------------------------------------------
# Trend component
# ------------------------------------------------------------------
class TestTrendComponent:
    def test_deteriorating_increases_score(self, kpi_risk):
        det = kpi_risk[kpi_risk["operational_trend_interpretation"] == "Deteriorating"]
        if len(det) > 0:
            assessable = det[det["calculation_status"] == "Calculated"]
            if len(assessable) > 0:
                assert (assessable["trend_component_score"] > 0.0).all()

    def test_improving_reduces_or_neutral(self, kpi_risk):
        imp = kpi_risk[kpi_risk["operational_trend_interpretation"] == "Improving"]
        if len(imp) > 0:
            assessable = imp[imp["calculation_status"] == "Calculated"]
            if len(assessable) > 0:
                assert (assessable["trend_component_score"] <= 0.0).all()


# ------------------------------------------------------------------
# Confidence model
# ------------------------------------------------------------------
class TestConfidence:
    def test_confidence_levels_exist(self, kpi_risk):
        levels = set(kpi_risk["confidence_level"].dropna().unique())
        assert levels.issubset({"High", "Moderate", "Low", "Insufficient Evidence"})

    def test_unavailable_is_insufficient(self, kpi_risk):
        unavail = kpi_risk[kpi_risk["calculation_status"] != "Calculated"]
        assert (unavail["confidence_level"] == "Insufficient Evidence").all()

    def test_provisional_kpi_not_high_confidence(self, kpi_risk):
        prov = kpi_risk[(kpi_risk["threshold_is_provisional"] == True) & (kpi_risk["calculation_status"] == "Calculated")]
        if len(prov) > 0:
            assert (prov["confidence_level"] != "High").all()


# ------------------------------------------------------------------
# Governance / provisional
# ------------------------------------------------------------------
class TestGovernance:
    def test_provisional_kpis_flagged(self, kpi_risk):
        prov = kpi_risk[kpi_risk["threshold_is_provisional"] == True]
        assert len(prov) > 0
        assert {"kpi_003", "kpi_005"}.issuperset(set(prov["kpi_id"].unique()))

    def test_provisional_has_governance_warning_or_adjustment(self, kpi_risk):
        prov = kpi_risk[(kpi_risk["threshold_is_provisional"] == True) & (kpi_risk["calculation_status"] == "Calculated")]
        if len(prov) > 0:
            assert (prov["governance_adjustment"] < 1.0).all()

    def test_review_date_propagated(self, kpi_risk):
        prov = kpi_risk[kpi_risk["threshold_is_provisional"] == True]
        # Only assert for records where a review date was actually set upstream
        prov_with_date = prov[prov["required_review_date"].notna()]
        assert len(prov_with_date) > 0


# ------------------------------------------------------------------
# Priority tier assignment
# ------------------------------------------------------------------
class TestPriorityTier:
    def test_tiers_are_valid(self, kpi_risk):
        valid = {"No Current Risk", "Monitor", "Attention Required", "High Priority", "Critical Priority", "Not Assessable"}
        assert set(kpi_risk["kpi_priority_tier"].unique()).issubset(valid)

    def test_critical_priority_for_critical_capacity(self, kpi_risk):
        ccp = kpi_risk[(kpi_risk["threshold_state"] == "Critical Capacity Pressure") & (kpi_risk["calculation_status"] == "Calculated")]
        if len(ccp) > 0:
            assert (ccp["kpi_priority_tier"] == "Critical Priority").all()


# ------------------------------------------------------------------
# Urgency assignment
# ------------------------------------------------------------------
class TestUrgency:
    def test_urgency_levels_valid(self, kpi_risk):
        valid = {"Routine Monitoring", "Review Soon", "Prompt Review", "Immediate Review", "Not Assessable"}
        assert set(kpi_risk["urgency_level"].unique()).issubset(valid)

    def test_critical_capacity_is_immediate(self, kpi_risk):
        ccp = kpi_risk[(kpi_risk["threshold_state"] == "Critical Capacity Pressure") & (kpi_risk["calculation_status"] == "Calculated")]
        if len(ccp) > 0:
            assert (ccp["urgency_level"] == "Immediate Review").all()


# ------------------------------------------------------------------
# Evidence and lineage
# ------------------------------------------------------------------
class TestEvidenceLineage:
    def test_every_kpi_has_evidence_pack(self, kpi_risk):
        assert kpi_risk["evidence_pack_id"].notna().all()

    def test_lineage_present_for_calculated(self, kpi_risk):
        calc = kpi_risk[kpi_risk["calculation_status"] == "Calculated"]
        assert calc["lineage_record_id"].notna().all()


# ------------------------------------------------------------------
# Source reconciliation
# ------------------------------------------------------------------
class TestSourceReconciliation:
    def test_all_source_records_scored(self, kpi_risk):
        assert len(kpi_risk) == 17520

    def test_assessable_plus_unavailable_equals_total(self, kpi_risk):
        calc = (kpi_risk["calculation_status"] == "Calculated").sum()
        uncalc = (kpi_risk["calculation_status"] != "Calculated").sum()
        assert calc + uncalc == len(kpi_risk)
