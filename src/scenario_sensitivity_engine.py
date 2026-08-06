"""Scenario sensitivity analysis engine.

Phase 2C-2D — Assesses outcome stability across comparator intensities.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import pandas as pd


class ScenarioSensitivityEngine:
    """Analyses sensitivity of scenario outcomes to assumption intensity."""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.rules = self._load_rules()

    def _load_rules(self) -> pd.DataFrame:
        path = os.path.join(self.config_dir, "scenario_sensitivity_rule_config.csv")
        if os.path.exists(path):
            return pd.read_csv(path, keep_default_na=False)
        return pd.DataFrame()

    def analyse_sensitivity(
        self,
        scenario_runs: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Analyse sensitivity across comparator intensities for a package/template."""
        if len(scenario_runs) < 2:
            return {
                "sensitivity_classification": "Not Assessable",
                "sensitivity_rationale": "Insufficient comparator coverage (< 2 comparators)",
                "direction_stable": None,
                "magnitude_variation": None,
                "warning_increase": None,
                "confidence_change": None,
            }

        # Sort by comparator intensity
        comparator_order = {"Baseline": 0, "Conservative": 1, "Expected": 2, "Higher Intensity": 3}
        sorted_runs = sorted(
            scenario_runs,
            key=lambda r: comparator_order.get(r.get("comparator_type", "Baseline"), 0)
        )

        directions = [r.get("direction_of_change", "") for r in sorted_runs]
        percentages = [self._to_float(r.get("percentage_change", 0)) for r in sorted_runs]
        warnings = [self._to_float(r.get("assumption_warning_count", 0)) for r in sorted_runs]
        confidences = [r.get("final_scenario_confidence", "") for r in sorted_runs]

        # Direction stability
        unique_directions = set(d for d in directions if d)
        direction_stable = len(unique_directions) == 1

        # Magnitude variation
        if len(percentages) >= 2:
            magnitude_variation = max(percentages) - min(percentages)
            baseline_pct = abs(percentages[0]) if percentages else 0
            magnitude_significant = magnitude_variation > (0.1 * baseline_pct) if baseline_pct > 0 else magnitude_variation > 5
        else:
            magnitude_variation = 0
            magnitude_significant = False

        # Warning increase
        warning_increase = max(warnings) > min(warnings) if warnings else False

        # Confidence change
        confidence_rank = {"High": 4, "Moderate": 3, "Low": 2, "Insufficient Evidence": 1}
        confidence_values = [confidence_rank.get(c, 0) for c in confidences]
        confidence_change = max(confidence_values) != min(confidence_values) if confidence_values else False

        # Direction reversal
        has_improvement = any(d in ("Increase", "Improvement") for d in directions)
        has_adverse = any(d in ("Decrease", "Adverse") for d in directions)
        direction_reversal = has_improvement and has_adverse

        # Classification
        if len(scenario_runs) < 3:
            classification = "Insufficient Comparator Coverage"
            rationale = "Need at least 3 comparators for robust sensitivity assessment"
        elif direction_reversal:
            classification = "Direction Reversal"
            rationale = "Outcome direction reverses across comparator intensities"
        elif not direction_stable:
            classification = "Sensitive to Assumption Intensity"
            rationale = "Outcome direction changes across comparator intensities"
        elif magnitude_significant:
            classification = "Stable with Magnitude Variation"
            rationale = f"Direction stable but magnitude varies by {magnitude_variation:.1f} percentage points"
        else:
            classification = "Stable Direction"
            rationale = "Outcome direction and magnitude are stable across comparator intensities"

        return {
            "sensitivity_classification": classification,
            "sensitivity_rationale": rationale,
            "direction_stable": direction_stable,
            "magnitude_variation": magnitude_variation,
            "magnitude_significant": magnitude_significant,
            "warning_increase": warning_increase,
            "confidence_change": confidence_change,
            "direction_reversal": direction_reversal,
            "comparator_count": len(scenario_runs),
        }

    @staticmethod
    def _to_float(value) -> float:
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
