"""Test scenario impact analysis engine.

Verifies primary impact classification and supporting KPI handling.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.scenario_impact_analysis_engine import ScenarioImpactAnalysisEngine


def test_classify_primary_impact():
    engine = ScenarioImpactAnalysisEngine()
    
    # Strong improvement
    result = engine.classify_primary_impact("kpi_001", 20.0, "Increase")
    assert result["impact_classification"] == "Strong Directional Improvement"
    
    # Moderate improvement
    result = engine.classify_primary_impact("kpi_001", 10.0, "Increase")
    assert result["impact_classification"] == "Moderate Directional Improvement"
    
    # No change
    result = engine.classify_primary_impact("kpi_001", 0.0, "No Change")
    assert result["impact_classification"] == "No Material Change"
    
    # Adverse
    result = engine.classify_primary_impact("kpi_001", -10.0, "Decrease")
    assert result["impact_classification"] == "Moderate Adverse Change"
    
    print("PASS: Primary impact classification")


def test_supporting_kpi_unsupported():
    engine = ScenarioImpactAnalysisEngine()
    result = engine.analyse_supporting_kpis("Calculated", ["kpi_003", "kpi_005"])
    assert result["supporting_kpi_status"] == "Monitoring Only"
    print("PASS: Unsupported KPIs flagged as Monitoring Only")


def test_supporting_kpi_quantified():
    engine = ScenarioImpactAnalysisEngine()
    result = engine.analyse_supporting_kpis("Calculated", ["kpi_001", "kpi_002"])
    assert result["supporting_kpi_status"] == "Quantified"
    print("PASS: Supported KPIs flagged as Quantified")


if __name__ == "__main__":
    test_classify_primary_impact()
    test_supporting_kpi_unsupported()
    test_supporting_kpi_quantified()
