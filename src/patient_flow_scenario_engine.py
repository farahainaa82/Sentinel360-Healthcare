"""Patient flow scenario calculation engine.

Phase 2C-2C — Patient-Flow and Waiting-Time Adjustment scenarios.
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


class PatientFlowScenarioEngine:
    """Calculate patient-flow scenario scenarios using simplified operational estimates."""

    def __init__(self, validator: ScenarioGovernanceValidator):
        self.validator = validator
        self.family = "Patient-Flow and Waiting-Time Adjustment"

    def run(
        self,
        baseline: ScenarioBaseline,
        comparator: Dict[str, Any],
        assumptions: Dict[str, Any],
    ) -> Tuple[ScenarioResult, List[AssumptionValidation]]:
        """Run a single patient-flow scenario comparator."""
        comparator_type = parse_comparator_type(comparator.get("comparator_type", "Baseline"))
        profile_id = comparator.get("assumption_profile_id", "")
        comparator_id = comparator.get("comparator_id", "")

        validations, all_valid = self.validator.validate_assumptions(assumptions, "patient_flow")
        hard_violations = [v for v in validations if v.validation_outcome == ValidationOutcome.INVALID]
        soft_warnings = [v for v in validations if v.validation_outcome == ValidationOutcome.VALID_WITH_WARNING]
        missing = [v for v in validations if v.validation_outcome == ValidationOutcome.MISSING]

        if baseline.baseline_status.value in ("Unavailable", "Blocked"):
            execution_status = ScenarioExecutionStatus.BLOCKED_MISSING_BASELINE
        elif baseline.baseline_avg_wait_min is None:
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
            base_wait = baseline.baseline_avg_wait_min or 0.0
            base_arrivals = baseline.baseline_arrivals or 0.0
            base_capacity = baseline.baseline_service_capacity or 0.0

            # Flow assumptions
            arrival_change = _to_float(assumptions.get("arrival_change_pct"), 0.0)
            capacity_change = _to_float(assumptions.get("service_capacity_change_pct"), 0.0)
            throughput_change = _to_float(assumptions.get("throughput_change_pct"), 0.0)
            routing_eff_change = _to_float(assumptions.get("routing_efficiency_change_pct"), 0.0)
            max_wait_reduction = _to_float(assumptions.get("max_wait_time_reduction_pct", 50.0), 50.0)

            # Adjusted demand and capacity
            adjusted_demand = base_arrivals * (1 + arrival_change / 100.0) if base_arrivals > 0 else 0.0
            adjusted_capacity = base_capacity
            if base_capacity > 0:
                adjusted_capacity = base_capacity * (1 + capacity_change / 100.0) * (1 + throughput_change / 100.0)

            # Simplified operational estimate: wait-time change proportional to demand/capacity ratio
            if base_capacity > 0 and base_arrivals > 0 and base_wait > 0:
                old_ratio = base_arrivals / base_capacity
                new_ratio = adjusted_demand / adjusted_capacity if adjusted_capacity > 0 else 999.0
                ratio_change = new_ratio / old_ratio
                # Wait time increases when ratio increases (more demand per capacity)
                # Bound the change by max_wait_reduction (cannot improve more than configured)
                wait_change_pct = (ratio_change - 1.0) * 100.0
                # Routing efficiency provides an additional reduction in wait time
                wait_change_pct = wait_change_pct - routing_eff_change
                # Cap reduction
                if wait_change_pct < -max_wait_reduction:
                    wait_change_pct = -max_wait_reduction
                    governance_warning = f"Wait-time reduction capped at {max_wait_reduction}%."
                # Do not permit negative waiting time
                adjusted_wait = base_wait * (1 + wait_change_pct / 100.0)
                if adjusted_wait < 0:
                    adjusted_wait = 0.0
                    governance_warning = "Adjusted wait time floored at 0 minutes."
            else:
                adjusted_wait = base_wait
                governance_warning = "Insufficient baseline data for simplified wait-time estimate."
                wait_change_pct = 0.0

            scenario_kpi_value = adjusted_wait
            absolute_change = adjusted_wait - base_wait
            if base_wait > 0:
                percentage_change = (adjusted_wait - base_wait) / base_wait * 100.0
            direction = DirectionOfChange.DECREASE if adjusted_wait < base_wait else DirectionOfChange.NO_CHANGE if adjusted_wait == base_wait else DirectionOfChange.INCREASE

            interpretation = (
                f"Simplified Operational Scenario Estimate: average wait adjusted from {base_wait:.1f} min "
                f"to {adjusted_wait:.1f} min. Demand/capacity ratio changed. "
                f"This is an analytical approximation, not a guaranteed forecast."
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
            assumption_set_id="patient-flow-default",
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
            calculation_rule_id="patient-flow-simplified-estimate",
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
