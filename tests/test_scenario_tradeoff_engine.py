"""Test scenario trade-off engine.

Verifies comparator trade-offs, diminishing returns, and trade-off profiles.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.scenario_tradeoff_engine import ScenarioTradeoffEngine


def test_pairwise_comparison():
    engine = ScenarioTradeoffEngine()
    baseline = {"scenario_run_id": "SR-BL", "approval_package_id": "PKG-001", "episode_id": "EP-001", "scenario_template_id": "SCEN-001", "percentage_change": 0, "final_scenario_confidence": "Low", "assumption_warning_count": 0}
    conservative = {"scenario_run_id": "SR-CONS", "approval_package_id": "PKG-001", "episode_id": "EP-001", "scenario_template_id": "SCEN-001", "percentage_change": 10, "final_scenario_confidence": "Low", "assumption_warning_count": 0}
    
    comparisons = engine.compare_comparators(baseline, conservative, None, None)
    assert len(comparisons) == 1
    assert comparisons[0]["comparator_a"] == "Conservative"
    assert comparisons[0]["comparator_b"] == "Baseline"
    print("PASS: Pairwise comparison created")


def test_diminishing_returns():
    engine = ScenarioTradeoffEngine()
    baseline = {"percentage_change": 0, "final_scenario_confidence": "Low", "assumption_warning_count": 0}
    conservative = {"percentage_change": 10, "final_scenario_confidence": "Low", "assumption_warning_count": 0}
    expected = {"percentage_change": 12, "final_scenario_confidence": "Low", "assumption_warning_count": 0}
    higher = {"percentage_change": 13, "final_scenario_confidence": "Low", "assumption_warning_count": 0}
    
    result = engine.assess_diminishing_returns(baseline, conservative, expected, higher)
    assert result["diminishing_return_classification"] == "Diminishing"
    print("PASS: Diminishing returns detected")


def test_tradeoff_profile():
    engine = ScenarioTradeoffEngine()
    run = {"percentage_change": 15, "final_scenario_confidence": "Moderate", "contradiction_severity": "No Contradiction", "baseline_data_completeness": 0.8, "assumption_warning_count": 0}
    profile = engine.build_tradeoff_profile(run, "Quantified", "No Displacement Identified")
    assert "analytical_trade_off_index" in profile
    assert "trade_off_band" in profile
    assert profile["trade_off_band"] in ["Favourable but Conditional", "Balanced Trade-Off", "Mixed Trade-Off", "Unfavourable Trade-Off", "Insufficient Evidence"]
    print("PASS: Trade-off profile generated")


if __name__ == "__main__":
    test_pairwise_comparison()
    test_diminishing_returns()
    test_tradeoff_profile()
