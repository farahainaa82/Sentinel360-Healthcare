"""Staffing scenario calculation engine.

Phase 2C-2C — Staffing Coverage Adjustment scenarios.
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


class StaffingScenarioEngine:
    """Calculate staffing coverage adjustment scenarios."""

    def __init__(self, validator: ScenarioGovernanceValidator):
        self.validator = validator
        self.family = "Staffing Coverage Adjustment"

    def run(
        self,
        baseline: ScenarioBaseline,
        comparator: Dict[str, Any],
        assumptions: Dict[str, Any],
    ) -> Tuple[ScenarioResult, List[AssumptionValidation]]:
        """Run a single staffing scenario comparator."""
        comparator_type = parse_comparator_type(comparator.get("comparator_type", "Baseline"))
        profile_id = comparator.get("assumption_profile_id", "")
        comparator_id = comparator.get("comparator_id", "")

        # Validate assumptions
        validations, all_valid = self.validator.validate_assumptions(assumptions, "staffing")
        hard_violations = [v for v in validations if v.validation_outcome == ValidationOutcome.INVALID]
        soft_warnings = [v for v in validations if v.validation_outcome == ValidationOutcome.VALID_WITH_WARNING]
        missing = [v for v in validations if v.validation_outcome == ValidationOutcome.MISSING]

        # Determine execution status
        if baseline.baseline_status.value in ("Unavailable", "Blocked"):
            execution_status = ScenarioExecutionStatus.BLOCKED_MISSING_BASELINE
        elif baseline.baseline_required_staff is None or baseline.baseline_available_staff is None:
            execution_status = ScenarioExecutionStatus.BLOCKED_MISSING_BASELINE
        elif hard_violations:
            execution_status = ScenarioExecutionStatus.BLOCKED_INVALID_ASSUMPTION
        elif missing:
            execution_status = ScenarioExecutionStatus.BLOCKED_MISSING_ASSUMPTION
        elif soft_warnings:
            execution_status = ScenarioExecutionStatus.COMPLETED_WITH_WARNINGS
        else:
            execution_status = ScenarioExecutionStatus.COMPLETED

        # Calculate scenario values
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
            base_req = baseline.baseline_required_staff or 0.0
            base_avail = baseline.baseline_available_staff or 0.0

            # Staffing inputs
            add_staff = _to_float_assumption(assumptions.get("additional_staff_count"), 0.0)
            temp_staff = _to_float_assumption(assumptions.get("temporary_staff_count"), 0.0)
            reassign_staff = _to_float_assumption(assumptions.get("staff_reassignment_count"), 0.0)

            # Duration scaling (governed model setting)
            days_in_month = _to_float_assumption(assumptions.get("days_in_selected_month"), 30.0)
            duration_days = _to_float_assumption(assumptions.get("intervention_duration_days"), 30.0)
            duration_weight = min(duration_days / days_in_month, 1.0) if days_in_month > 0 else 1.0

            # Reject negative staff counts
            if add_staff < 0 or temp_staff < 0 or reassign_staff < 0:
                execution_status = ScenarioExecutionStatus.BLOCKED_INVALID_ASSUMPTION
                governance_warning = "Negative staff counts are rejected."
            else:
                # Effective intervention staff scaled by duration
                effective_intervention_staff = (add_staff + temp_staff + reassign_staff) * duration_weight
                adjusted_avail = base_avail + effective_intervention_staff
                if base_req > 0:
                    adjusted_coverage = (adjusted_avail / base_req) * 100.0
                else:
                    adjusted_coverage = 0.0

                # Governed ceiling at 100%
                max_coverage = 100.0
                if adjusted_coverage > max_coverage:
                    adjusted_coverage = max_coverage
                    governance_warning = f"Staffing coverage capped at {max_coverage}%."

                base_coverage = baseline.baseline_staffing_coverage_pct or 0.0
                if base_coverage > 0:
                    percentage_change = adjusted_coverage - base_coverage
                absolute_change = adjusted_avail - base_avail
                scenario_kpi_value = adjusted_coverage
                direction = DirectionOfChange.INCREASE if adjusted_coverage > base_coverage else DirectionOfChange.NO_CHANGE if adjusted_coverage == base_coverage else DirectionOfChange.DECREASE

                interpretation = (
                    f"Staffing coverage adjusted from {base_coverage:.2f}% to {adjusted_coverage:.2f}%. "
                    f"Adjusted available staff: {adjusted_avail:.1f} (required: {base_req:.1f})."
                )

        # Build result
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
            assumption_set_id="staffing-default",
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
            calculation_rule_id="staffing-coverage-adjustment",
            comparator_config_version="2C-2B-1.0",
            assumption_config_version="2C-2B-1.0",
            causality_status="Not Confirmed",
            source_file_list=baseline.source_file_list,
            source_record_id_list=baseline.source_record_id_list,
        )

        return result, validations


def _to_float_assumption(val: Any, default: float = 0.0) -> float:
    """Safely convert assumption to float."""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default
