"""Absenteeism scenario calculation engine.

Phase 2C-2C — Absenteeism Contingency scenarios.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from src.scenario_models import (
    AssumptionValidation,
    ComparatorType,
    DirectionOfChange,
    ScenarioBaseline,
    ScenarioConfidence,
    ScenarioExecutionStatus,
    ScenarioResult,
    ValidationOutcome,
    parse_comparator_type,
)
from src.scenario_governance_validator import ScenarioGovernanceValidator


class AbsenteeismScenarioEngine:
    """Calculate absenteeism contingency scenarios."""

    def __init__(self, validator: ScenarioGovernanceValidator):
        self.validator = validator
        self.family = "Absenteeism Contingency"

    def run(
        self,
        baseline: ScenarioBaseline,
        comparator: Dict[str, Any],
        assumptions: Dict[str, Any],
    ) -> Tuple[ScenarioResult, List[AssumptionValidation]]:
        """Run a single absenteeism scenario comparator."""
        comparator_type = parse_comparator_type(comparator.get("comparator_type", "Baseline"))
        profile_id = comparator.get("assumption_profile_id", "")
        comparator_id = comparator.get("comparator_id", "")

        validations, all_valid = self.validator.validate_assumptions(assumptions, "absenteeism")
        hard_violations = [v for v in validations if v.validation_outcome == ValidationOutcome.INVALID]
        soft_warnings = [v for v in validations if v.validation_outcome == ValidationOutcome.VALID_WITH_WARNING]
        missing = [v for v in validations if v.validation_outcome == ValidationOutcome.MISSING]

        if baseline.baseline_status.value in ("Unavailable", "Blocked"):
            execution_status = ScenarioExecutionStatus.BLOCKED_MISSING_BASELINE
        elif baseline.baseline_absenteeism_rate is None:
            execution_status = ScenarioExecutionStatus.BLOCKED_MISSING_BASELINE
        elif hard_violations:
            execution_status = ScenarioExecutionStatus.BLOCKED_INVALID_ASSUMPTION
        elif missing:
            execution_status = ScenarioExecutionStatus.BLOCKED_MISSING_ASSUMPTION
        elif soft_warnings:
            execution_status = ScenarioExecutionStatus.COMPLETED_WITH_WARNINGS
        else:
            execution_status = ScenarioExecutionStatus.COMPLETED

        scenario_kpi_value: Optional[float] = None
        absolute_change: Optional[float] = None
        percentage_change: Optional[float] = None
        direction = DirectionOfChange.UNCERTAIN
        interpretation = ""
        governance_warning = ""

        if execution_status in (
            ScenarioExecutionStatus.COMPLETED,
            ScenarioExecutionStatus.COMPLETED_WITH_WARNINGS,
        ):
            base_abs = baseline.baseline_absenteeism_rate or 0.0

            # Absenteeism assumptions
            abs_reduction_pct = _to_float(assumptions.get("assumed_absenteeism_reduction_pct"), 0.0)
            replacement_coverage_pct = _to_float(assumptions.get("replacement_coverage_pct"), 0.0)

            # Reject negative reduction > 100% (invalid assumption)
            if abs_reduction_pct < 0 or abs_reduction_pct > 100:
                execution_status = ScenarioExecutionStatus.BLOCKED_INVALID_ASSUMPTION
                governance_warning = "absenteeism_reduction_pct must be 0-100."
            else:
                adjusted_abs = base_abs * (1 - abs_reduction_pct / 100.0)
                # Do not allow below zero
                if adjusted_abs < 0:
                    adjusted_abs = 0.0
                    governance_warning = "Adjusted absenteeism floored at 0%."

                estimated_coverage = replacement_coverage_pct
                residual_exposure = base_abs - adjusted_abs
                coverage_gap = max(0.0, residual_exposure - estimated_coverage)

                scenario_kpi_value = adjusted_abs
                absolute_change = adjusted_abs - base_abs
                if base_abs > 0:
                    percentage_change = (adjusted_abs - base_abs) / base_abs * 100.0
                direction = DirectionOfChange.DECREASE if adjusted_abs < base_abs else DirectionOfChange.NO_CHANGE if adjusted_abs == base_abs else DirectionOfChange.INCREASE

                interpretation = (
                    f"Absenteeism adjusted from {base_abs:.2f}% to {adjusted_abs:.2f}%. "
                    f"Reduction: {abs_reduction_pct:.1f}%. Replacement coverage: {estimated_coverage:.1f}%. "
                    f"Residual exposure: {residual_exposure:.2f}%."
                )

        result = ScenarioResult(
            scenario_run_id=f"SR-{baseline.baseline_id}-{comparator_id}",
            approval_package_id=baseline.approval_package_id,
            episode_id=baseline.episode_id,
            scenario_template_id=baseline.scenario_template_id,
            comparator_id=comparator_id,
            comparator_type=comparator_type,
            scenario_family=self.family,
            scenario_mode=comparator.get("scenario_mode", "Baseline"),
            scenario_run_timestamp=datetime.utcnow().isoformat(),
            engine_version="2C-2C-1.0",
            baseline_id=baseline.baseline_id,
            baseline_status=baseline.baseline_status.value,
            baseline_value=baseline.baseline_kpi_value,
            baseline_unit=baseline.baseline_kpi_unit,
            baseline_reference_date=baseline.baseline_reference_date,
            baseline_data_completeness=baseline.baseline_data_completeness,
            assumption_set_id="absenteeism-default",
            assumption_profile=profile_id,
            assumption_values_json=json.dumps(assumptions),
            assumption_validation_status="All Valid" if all_valid else "Issues Found",
            assumption_warning_count=len(soft_warnings),
            primary_kpi_id=baseline.dominant_kpi_id,
            baseline_primary_kpi_value=baseline.baseline_kpi_value,
            scenario_primary_kpi_value=scenario_kpi_value,
            absolute_change=absolute_change,
            percentage_change=percentage_change,
            direction_of_change=direction,
            operational_interpretation=interpretation,
            governance_warning=governance_warning,
            scenario_execution_status=execution_status,
            calculation_rule_id="absenteeism-contingency",
            comparator_config_version="2C-2B-1.0",
            assumption_config_version="2C-2B-1.0",
            causality_status="Not Confirmed",
            source_file_list=baseline.source_file_list,
            source_record_id_list=baseline.source_record_id_list,
        )

        return result, validations


def _to_float(val: Any, default: float = 0.0) -> float:
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default
