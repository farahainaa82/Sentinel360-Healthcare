"""Scenario trade-off analysis engine.

Phase 2C-2D — Comparator trade-off, diminishing returns, and multi-criteria profiles.
"""

from __future__ import annotations

import os
import json
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


class ScenarioTradeoffEngine:
    """Analyses trade-offs between comparator intensities."""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.criteria = self._load_criteria()
        self.weights = self._load_weights()

    def _load_criteria(self) -> pd.DataFrame:
        path = os.path.join(self.config_dir, "scenario_tradeoff_criteria_config.csv")
        if os.path.exists(path):
            return pd.read_csv(path, keep_default_na=False)
        return pd.DataFrame()

    def _load_weights(self) -> pd.DataFrame:
        path = os.path.join(self.config_dir, "scenario_tradeoff_weight_config.csv")
        if os.path.exists(path):
            return pd.read_csv(path, keep_default_na=False)
        return pd.DataFrame()

    def compare_comparators(
        self,
        baseline: Dict[str, Any],
        conservative: Optional[Dict[str, Any]],
        expected: Optional[Dict[str, Any]],
        higher: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Create pairwise comparator trade-off records."""
        comparisons = []
        pairs = [
            ("Conservative", conservative, "Baseline", baseline),
            ("Expected", expected, "Conservative", conservative),
            ("Higher Intensity", higher, "Expected", expected),
            ("Expected", expected, "Baseline", baseline),
            ("Higher Intensity", higher, "Baseline", baseline),
        ]

        for comp_a_name, comp_a, comp_b_name, comp_b in pairs:
            if comp_a is None or comp_b is None:
                continue
            comparison = self._create_pairwise_comparison(comp_a_name, comp_a, comp_b_name, comp_b)
            comparisons.append(comparison)

        return comparisons

    def _create_pairwise_comparison(
        self,
        name_a: str,
        comp_a: Dict[str, Any],
        name_b: str,
        comp_b: Dict[str, Any],
    ) -> Dict[str, Any]:
        pct_a = self._to_float(comp_a.get("percentage_change", 0))
        pct_b = self._to_float(comp_b.get("percentage_change", 0))
        incremental = pct_a - pct_b

        conf_a = comp_a.get("final_scenario_confidence", "")
        conf_b = comp_b.get("final_scenario_confidence", "")
        conf_rank = {"High": 4, "Moderate": 3, "Low": 2, "Insufficient Evidence": 1}
        conf_change = conf_rank.get(conf_a, 0) - conf_rank.get(conf_b, 0)

        warn_a = self._to_float(comp_a.get("assumption_warning_count", 0))
        warn_b = self._to_float(comp_b.get("assumption_warning_count", 0))
        warn_change = warn_a - warn_b

        # Classification
        if incremental > 5 and conf_change >= 0 and warn_change <= 1:
            classification = "Incremental Benefit with Limited Additional Risk"
        elif incremental > 5:
            classification = "Incremental Benefit with Additional Trade-Off"
        elif 0 < incremental <= 5:
            classification = "Diminishing Improvement"
        elif incremental == 0:
            classification = "No Material Incremental Benefit"
        elif incremental < 0:
            classification = "Higher Risk without Clear Additional Benefit"
        else:
            classification = "Insufficient Evidence"

        return {
            "comparison_id": f"COMP-{comp_a.get('scenario_run_id', '')}-{name_a}-vs-{name_b}",
            "scenario_run_id_a": comp_a.get("scenario_run_id", ""),
            "scenario_run_id_b": comp_b.get("scenario_run_id", ""),
            "comparator_a": name_a,
            "comparator_b": name_b,
            "approval_package_id": comp_a.get("approval_package_id", ""),
            "episode_id": comp_a.get("episode_id", ""),
            "scenario_template_id": comp_a.get("scenario_template_id", ""),
            "incremental_primary_kpi_change": incremental,
            "confidence_change": conf_change,
            "warning_change": warn_change,
            "comparator_relationship": classification,
            "evidence_basis": f"Pairwise comparison of {name_a} versus {name_b} comparator results",
        }

    def assess_diminishing_returns(
        self,
        baseline: Dict[str, Any],
        conservative: Optional[Dict[str, Any]],
        expected: Optional[Dict[str, Any]],
        higher: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Assess whether increasing intensity produces diminishing returns."""
        comparators = [
            ("Baseline", baseline),
            ("Conservative", conservative),
            ("Expected", expected),
            ("Higher Intensity", higher),
        ]
        comparators = [(n, c) for n, c in comparators if c is not None]

        if len(comparators) < 3:
            return {
                "diminishing_return_classification": "Not Assessable",
                "diminishing_return_rationale": "Insufficient comparator coverage for diminishing-return assessment",
                "incremental_effect_ratios": [],
            }

        # Calculate incremental improvements
        improvements = []
        for i in range(1, len(comparators)):
            name_prev, comp_prev = comparators[i - 1]
            name_curr, comp_curr = comparators[i]
            pct_prev = self._to_float(comp_prev.get("percentage_change", 0))
            pct_curr = self._to_float(comp_curr.get("percentage_change", 0))
            improvement = pct_curr - pct_prev
            improvements.append((name_prev, name_curr, improvement))

        # Calculate ratios (simplified: improvement per intensity step)
        ratios = []
        for prev, curr, imp in improvements:
            ratios.append({
                "from_comparator": prev,
                "to_comparator": curr,
                "incremental_improvement": imp,
                "intensity_step": 1,
                "incremental_effect_ratio": imp,
            })

        # Classify
        if len(ratios) >= 2:
            first = ratios[0]["incremental_effect_ratio"]
            last = ratios[-1]["incremental_effect_ratio"]
            if first > 0 and last < 0:
                classification = "Adverse Reversal"
                rationale = "Higher intensity produces adverse reversal of estimated benefit"
            elif first > 0 and last < first * 0.5:
                classification = "Diminishing"
                rationale = "Incremental improvement decreases significantly with higher intensity"
            elif first > 0 and abs(last - first) < 2:
                classification = "Proportionate"
                rationale = "Incremental improvement remains roughly proportionate across intensities"
            elif first > 0 and last == 0:
                classification = "Flat"
                rationale = "No additional improvement at higher intensity"
            else:
                classification = "Not Assessable"
                rationale = "Inconsistent improvement pattern across intensities"
        else:
            classification = "Not Assessable"
            rationale = "Need at least 2 incremental steps for assessment"

        return {
            "diminishing_return_classification": classification,
            "diminishing_return_rationale": rationale,
            "incremental_effect_ratios": ratios,
        }

    def build_tradeoff_profile(
        self,
        scenario_run: Dict[str, Any],
        supporting_kpi_status: str,
        displacement_risk: str,
    ) -> Dict[str, Any]:
        """Build a multi-criteria trade-off profile for a scenario."""
        # Calculate analytical trade-off index (transparent, not a black box)
        components = {}

        # Primary KPI impact (0-100)
        pct_change = abs(self._to_float(scenario_run.get("percentage_change", 0)))
        components["primary_kpi_impact"] = min(pct_change * 2, 100)  # Scale: 50% change = 100

        # Confidence (0-100)
        conf_rank = {"High": 100, "Moderate": 75, "Low": 50, "Insufficient Evidence": 25}
        components["confidence"] = conf_rank.get(scenario_run.get("final_scenario_confidence", ""), 0)

        # Contradiction penalty (0-100, lower is better)
        contra_rank = {"No Contradiction": 100, "Minor": 75, "Material": 50, "Major": 0}
        components["contradiction"] = contra_rank.get(scenario_run.get("contradiction_severity", ""), 50)

        # Baseline completeness (0-100)
        completeness = self._to_float(scenario_run.get("baseline_data_completeness", 0))
        components["baseline_completeness"] = min(completeness * 100, 100)

        # Assumption warnings (0-100, lower warnings = higher score)
        warnings = self._to_float(scenario_run.get("assumption_warning_count", 0))
        components["assumption_extremity"] = max(100 - warnings * 20, 0)

        # Supporting KPI (0-100)
        if supporting_kpi_status == "Quantified":
            components["supporting_kpi"] = 80
        elif supporting_kpi_status == "Directional Only":
            components["supporting_kpi"] = 50
        else:
            components["supporting_kpi"] = 25

        # Displacement risk (0-100, lower risk = higher score)
        disp_rank = {
            "No Displacement Identified": 100,
            "Possible Within-Department Displacement": 75,
            "Possible Cross-Department Displacement": 60,
            "Possible Cross-KPI Displacement": 50,
            "Material Displacement Risk": 25,
            "Insufficient Evidence": 50,
        }
        components["displacement_risk"] = disp_rank.get(displacement_risk, 50)

        # Calculate weighted index
        weights = {
            "primary_kpi_impact": 0.20,
            "supporting_kpi": 0.10,
            "confidence": 0.15,
            "contradiction": 0.10,
            "baseline_completeness": 0.08,
            "assumption_extremity": 0.07,
            "displacement_risk": 0.08,
        }

        total_weight = sum(weights.values())
        index = sum(components.get(k, 0) * weights.get(k, 0) for k in components) / total_weight if total_weight > 0 else 0

        # Classify trade-off band
        if index >= 70:
            band = "Favourable but Conditional"
        elif index >= 50:
            band = "Balanced Trade-Off"
        elif index >= 30:
            band = "Mixed Trade-Off"
        elif index > 0:
            band = "Unfavourable Trade-Off"
        else:
            band = "Insufficient Evidence"

        return {
            "analytical_trade_off_index": round(index, 2),
            "index_components": components,
            "index_weights": weights,
            "trade_off_band": band,
            "trade_off_rationale": f"Analytical Trade-Off Index = {index:.1f} based on {len(components)} criteria",
        }

    @staticmethod
    def _to_float(value) -> float:
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
