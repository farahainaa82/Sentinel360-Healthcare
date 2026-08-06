"""Scenario confidence engine.

Phase 2C-2C — Calculates scenario confidence from governed factors.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.scenario_models import (
    ScenarioBaseline,
    ScenarioConfidence,
    ScenarioExecutionStatus,
)
from src.scenario_config_loader import ScenarioConfigLoader


class ScenarioConfidenceEngine:
    """Calculates scenario confidence from governed factors only."""

    # No High confidence is allowed in Phase 2C-2
    ALLOWED_CONFIDENCE = {ScenarioConfidence.MODERATE, ScenarioConfidence.LOW, ScenarioConfidence.INSUFFICIENT_EVIDENCE}

    def __init__(self, loader: ScenarioConfigLoader):
        self.loader = loader
        self._rules_cache: Optional[List[Dict[str, Any]]] = None

    def _load_rules(self) -> List[Dict[str, Any]]:
        if self._rules_cache is None:
            self._rules_cache = self.loader.get_confidence_rules()
        return self._rules_cache

    def calculate_confidence(
        self,
        baseline: ScenarioBaseline,
        execution_status: ScenarioExecutionStatus,
        assumption_warning_count: int,
        contradiction_severity: str,
        provisional_kpi_involved: bool,
        partial_flow_coverage: bool = False,
        combined_scenario_penalty: bool = False,
        missing_supporting_kpis: int = 0,
    ) -> ScenarioConfidence:
        """Calculate final scenario confidence from governed factors."""
        rules = self._load_rules()

        # Start from base confidence based on baseline completeness
        if baseline.baseline_data_completeness >= 95.0 and baseline.baseline_confidence in ("High", "Moderate"):
            base = 0.7
        elif baseline.baseline_data_completeness >= 75.0:
            base = 0.5
        elif baseline.baseline_data_completeness >= 50.0:
            base = 0.3
        else:
            base = 0.1

        # Apply multiplicative penalties from confidence rules
        penalties = 1.0
        for rule in rules:
            factor_name = rule.get("factor_name", "")
            penalty_value = rule.get("penalty_value", "")
            try:
                penalty = float(penalty_value)
            except (ValueError, TypeError):
                continue

            apply = False
            if factor_name == "baseline_incomplete" and baseline.baseline_data_completeness < 75.0:
                apply = True
            elif factor_name == "contradiction_material" and contradiction_severity == "Material":
                apply = True
            elif factor_name == "contradiction_major" and contradiction_severity == "Major":
                apply = True
            elif factor_name == "provisional_supporting_kpi" and provisional_kpi_involved:
                apply = True
            elif factor_name == "assumption_soft_limit" and assumption_warning_count > 0:
                apply = True
            elif factor_name == "assumption_hard_limit" and execution_status in (
                ScenarioExecutionStatus.BLOCKED_INVALID_ASSUMPTION,
            ):
                apply = True
            elif factor_name == "partial_patient_flow_coverage" and partial_flow_coverage:
                apply = True
            elif factor_name == "combined_scenario_penalty" and combined_scenario_penalty:
                apply = True
            elif factor_name == "missing_supporting_kpi" and missing_supporting_kpis > 0:
                apply = True
            elif factor_name == "baseline_partial" and baseline.baseline_status.value == "Partial":
                apply = True
            elif factor_name == "baseline_with_conditions" and baseline.baseline_status.value == "Available with Conditions":
                apply = True
            elif factor_name == "baseline_unavailable" and baseline.baseline_status.value in ("Unavailable", "Blocked"):
                apply = True

            if apply:
                penalties *= (1.0 - penalty)

        score = base * penalties

        # Map to allowed confidence levels (no High allowed)
        if score >= 0.5:
            return ScenarioConfidence.MODERATE
        elif score >= 0.25:
            return ScenarioConfidence.LOW
        else:
            return ScenarioConfidence.INSUFFICIENT_EVIDENCE

    def confidence_rationale(
        self,
        baseline: ScenarioBaseline,
        execution_status: ScenarioExecutionStatus,
        assumption_warning_count: int,
        contradiction_severity: str,
        provisional_kpi_involved: bool,
        partial_flow_coverage: bool = False,
        combined_scenario_penalty: bool = False,
        missing_supporting_kpis: int = 0,
    ) -> Dict[str, Any]:
        """Return detailed confidence rationale."""
        confidence = self.calculate_confidence(
            baseline, execution_status, assumption_warning_count, contradiction_severity,
            provisional_kpi_involved, partial_flow_coverage, combined_scenario_penalty, missing_supporting_kpis
        )
        rules = self._load_rules()
        adjustments = []
        for rule in rules:
            factor_name = rule.get("factor_name", "")
            penalty_value = rule.get("penalty_value", "")
            try:
                penalty = float(penalty_value)
            except (ValueError, TypeError):
                continue
            apply = False
            if factor_name == "baseline_incomplete" and baseline.baseline_data_completeness < 75.0:
                apply = True
            elif factor_name == "contradiction_material" and contradiction_severity == "Material":
                apply = True
            elif factor_name == "contradiction_major" and contradiction_severity == "Major":
                apply = True
            elif factor_name == "provisional_supporting_kpi" and provisional_kpi_involved:
                apply = True
            elif factor_name == "assumption_soft_limit" and assumption_warning_count > 0:
                apply = True
            elif factor_name == "assumption_hard_limit" and execution_status == ScenarioExecutionStatus.BLOCKED_INVALID_ASSUMPTION:
                apply = True
            elif factor_name == "partial_patient_flow_coverage" and partial_flow_coverage:
                apply = True
            elif factor_name == "combined_scenario_penalty" and combined_scenario_penalty:
                apply = True
            elif factor_name == "missing_supporting_kpi" and missing_supporting_kpis > 0:
                apply = True
            elif factor_name == "baseline_partial" and baseline.baseline_status.value == "Partial":
                apply = True
            elif factor_name == "baseline_with_conditions" and baseline.baseline_status.value == "Available with Conditions":
                apply = True
            elif factor_name == "baseline_unavailable" and baseline.baseline_status.value in ("Unavailable", "Blocked"):
                apply = True

            if apply:
                adjustments.append({
                    "factor": factor_name,
                    "penalty": penalty,
                    "applied": True,
                })

        return {
            "confidence_base": baseline.baseline_data_completeness,
            "confidence_adjustments": adjustments,
            "confidence_score_internal": confidence,
            "final_scenario_confidence": confidence.value,
            "confidence_rationale": f"Base from completeness {baseline.baseline_data_completeness:.1f}%, "
            f"{len(adjustments)} adjustments applied, result: {confidence.value}",
        }
