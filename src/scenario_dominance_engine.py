"""Scenario dominance analysis engine.

Phase 2C-2D — Analytical scenario dominance, not management recommendation.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


class ScenarioDominanceEngine:
    """Evaluates analytical dominance between scenarios for the same package/template."""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.rules = self._load_rules()

    def _load_rules(self) -> pd.DataFrame:
        path = os.path.join(self.config_dir, "scenario_dominance_rule_config.csv")
        if os.path.exists(path):
            return pd.read_csv(path, keep_default_na=False)
        return pd.DataFrame()

    def compare_pairwise(
        self,
        scenario_a: Dict[str, Any],
        scenario_b: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compare two scenarios and return dominance classification."""
        if not self._is_comparable(scenario_a, scenario_b):
            return {
                "dominance_classification": "Incomparable",
                "dominance_rationale": "Scenarios are not comparable (different package, template, or family)",
                "dominance_conditions_met": [],
                "dominance_conditions_failed": ["Different comparison context"],
            }

        conditions_met = []
        conditions_failed = []

        # Primary KPI: A must be equal or better
        if self._primary_kpi_better_or_equal(scenario_a, scenario_b):
            conditions_met.append("Primary KPI equal or better")
        else:
            conditions_failed.append("Primary KPI worse")

        # Confidence: A must be equal or higher
        if self._confidence_better_or_equal(scenario_a, scenario_b):
            conditions_met.append("Confidence equal or higher")
        else:
            conditions_failed.append("Confidence lower")

        # Contradiction: A must be equal or lower
        if self._contradiction_better_or_equal(scenario_a, scenario_b):
            conditions_met.append("Contradiction severity equal or lower")
        else:
            conditions_failed.append("Contradiction severity higher")

        # Assumption warnings: A must be equal or lower
        if self._assumptions_better_or_equal(scenario_a, scenario_b):
            conditions_met.append("Assumption warnings equal or lower")
        else:
            conditions_failed.append("Assumption warnings higher")

        # Determine classification
        if not conditions_failed:
            # All conditions met — check if strictly better in at least one
            if self._strictly_better_in_any(scenario_a, scenario_b):
                classification = "Dominates"
                rationale = "Scenario A dominates Scenario B on all criteria and is strictly better in at least one"
            else:
                classification = "Weakly Dominates"
                rationale = "Scenario A weakly dominates Scenario B (equal on all criteria)"
        elif len(conditions_failed) == 1 and "Primary KPI" not in conditions_failed[0]:
            # Only one minor condition failed
            classification = "Non-Dominated"
            rationale = f"Scenario A is non-dominated; fails on: {', '.join(conditions_failed)}"
        else:
            classification = "Dominated"
            rationale = f"Scenario A is dominated by Scenario B; fails on: {', '.join(conditions_failed)}"

        return {
            "dominance_classification": classification,
            "dominance_rationale": rationale,
            "dominance_conditions_met": conditions_met,
            "dominance_conditions_failed": conditions_failed,
        }

    def _is_comparable(self, a: Dict[str, Any], b: Dict[str, Any]) -> bool:
        return (
            a.get("approval_package_id") == b.get("approval_package_id") and
            a.get("scenario_template_id") == b.get("scenario_template_id") and
            a.get("scenario_family") == b.get("scenario_family")
        )

    def _primary_kpi_better_or_equal(self, a: Dict[str, Any], b: Dict[str, Any]) -> bool:
        dir_a = a.get("direction_of_change", "")
        dir_b = b.get("direction_of_change", "")
        pct_a = self._to_float(a.get("percentage_change", 0))
        pct_b = self._to_float(b.get("percentage_change", 0))

        # Improvement is better
        if dir_a in ("Increase", "Improvement") and dir_b not in ("Increase", "Improvement"):
            return True
        if dir_a == dir_b:
            return pct_a >= pct_b
        if dir_a in ("No Change", "Uncertain") and dir_b in ("Decrease", "Adverse"):
            return True
        return False

    def _confidence_better_or_equal(self, a: Dict[str, Any], b: Dict[str, Any]) -> bool:
        rank = {"High": 4, "Moderate": 3, "Low": 2, "Insufficient Evidence": 1}
        conf_a = rank.get(a.get("final_scenario_confidence", ""), 0)
        conf_b = rank.get(b.get("final_scenario_confidence", ""), 0)
        return conf_a >= conf_b

    def _contradiction_better_or_equal(self, a: Dict[str, Any], b: Dict[str, Any]) -> bool:
        rank = {"No Contradiction": 0, "Minor": 1, "Material": 2, "Major": 3}
        contra_a = rank.get(a.get("contradiction_severity", ""), 0)
        contra_b = rank.get(b.get("contradiction_severity", ""), 0)
        return contra_a <= contra_b

    def _assumptions_better_or_equal(self, a: Dict[str, Any], b: Dict[str, Any]) -> bool:
        warn_a = self._to_float(a.get("assumption_warning_count", 0))
        warn_b = self._to_float(b.get("assumption_warning_count", 0))
        return warn_a <= warn_b

    def _strictly_better_in_any(self, a: Dict[str, Any], b: Dict[str, Any]) -> bool:
        # Check if A is strictly better in at least one dimension
        if self._to_float(a.get("percentage_change", 0)) > self._to_float(b.get("percentage_change", 0)):
            if a.get("direction_of_change") == b.get("direction_of_change"):
                return True
        if self._confidence_better_or_equal(a, b) and a.get("final_scenario_confidence") != b.get("final_scenario_confidence"):
            return True
        if self._contradiction_better_or_equal(a, b) and a.get("contradiction_severity") != b.get("contradiction_severity"):
            return True
        return False

    @staticmethod
    def _to_float(value) -> float:
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
