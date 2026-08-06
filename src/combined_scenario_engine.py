"""Combined workforce and flow scenario calculation engine.

Phase 2C-2C — Combined Workforce and Flow Intervention scenarios.
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
from src.staffing_scenario_engine import StaffingScenarioEngine
from src.patient_flow_scenario_engine import PatientFlowScenarioEngine


class CombinedScenarioEngine:
    """Calculate combined workforce and flow scenarios."""

    def __init__(
        self,
        validator: ScenarioGovernanceValidator,
        staffing_engine: StaffingScenarioEngine,
        flow_engine: PatientFlowScenarioEngine,
    ):
        self.validator = validator
        self.staffing_engine = staffing_engine
        self.flow_engine = flow_engine
        self.family = "Combined Workforce and Flow Intervention"

    def run(
        self,
        workforce_baseline: ScenarioBaseline,
        flow_baseline: ScenarioBaseline,
        comparator: Dict[str, Any],
        assumptions: Dict[str, Any],
    ) -> Tuple[ScenarioResult, List[AssumptionValidation]]:
        """Run a single combined scenario comparator."""
        comparator_type = parse_comparator_type(comparator.get("comparator_type", "Baseline"))
        profile_id = comparator.get("assumption_profile_id", "")
        comparator_id = comparator.get("comparator_id", "")

        validations, all_valid = self.validator.validate_assumptions(assumptions, "combined")
        hard_violations = [v for v in validations if v.validation_outcome == ValidationOutcome.INVALID]
        soft_warnings = [v for v in validations if v.validation_outcome == ValidationOutcome.VALID_WITH_WARNING]
        missing = [v for v in validations if v.validation_outcome == ValidationOutcome.MISSING]

        # Check eligibility
        if workforce_baseline.baseline_status.value in ("Unavailable", "Blocked"):
            execution_status = ScenarioExecutionStatus.BLOCKED_MISSING_BASELINE
            governance_warning = "Workforce baseline unavailable."
        elif flow_baseline.baseline_status.value in ("Unavailable", "Blocked"):
            execution_status = ScenarioExecutionStatus.BLOCKED_MISSING_BASELINE
            governance_warning = "Patient-flow baseline unavailable."
        elif hard_violations:
            execution_status = ScenarioExecutionStatus.BLOCKED_INVALID_ASSUMPTION
            governance_warning = ""
        elif missing:
            execution_status = ScenarioExecutionStatus.BLOCKED_MISSING_ASSUMPTION
            governance_warning = ""
        elif soft_warnings:
            execution_status = ScenarioExecutionStatus.COMPLETED_WITH_WARNINGS
            governance_warning = ""
        else:
            execution_status = ScenarioExecutionStatus.COMPLETED
            governance_warning = ""

        scenario_kpi_value: Optional[float] = None
        absolute_change: Optional[float] = None
        percentage_change: Optional[float] = None
        direction = DirectionOfChange.UNCERTAIN
        interpretation = ""
        interaction_warning = ""

        if execution_status in (
            ScenarioExecutionStatus.COMPLETED,
            ScenarioExecutionStatus.COMPLETED_WITH_WARNINGS,
        ):
            # Run both components separately (not used for output, but conceptually validated)
            staffing_result, _ = self.staffing_engine.run(workforce_baseline, comparator, assumptions)
            flow_result, _ = self.flow_engine.run(flow_baseline, comparator, assumptions)

            # Apply interaction adjustment
            interaction_factor = _to_float(assumptions.get("interaction_adjustment_factor"), 1.0)
            penalty = _to_float(assumptions.get("combined_scenario_confidence_penalty"), 0.0)

            # Combined result uses a configured interaction assumption, not naive multiplication
            # If the primary KPI is flow-based, apply interaction to the flow result
            if flow_baseline.dominant_kpi_id == "kpi_004":
                base_val = flow_baseline.baseline_avg_wait_min or 0.0
                flow_val = flow_result.scenario_primary_kpi_value or base_val
                # Interaction adjustment: staffing changes may reduce wait times further
                adjusted_val = flow_val * interaction_factor
                # But we don't want to over-claim - apply conservative dampening if interaction > 1
                if interaction_factor > 1.0 and adjusted_val < base_val:
                    adjusted_val = base_val - (base_val - adjusted_val) / interaction_factor
                scenario_kpi_value = adjusted_val
                absolute_change = adjusted_val - base_val
                if base_val > 0:
                    percentage_change = (adjusted_val - base_val) / base_val * 100.0
                direction = DirectionOfChange.DECREASE if adjusted_val < base_val else DirectionOfChange.NO_CHANGE if adjusted_val == base_val else DirectionOfChange.INCREASE
                interpretation = (
                    f"Combined scenario: workforce component + flow component with interaction factor {interaction_factor:.2f}. "
                    f"Workforce result: {staffing_result.scenario_primary_kpi_value or 0.0:.2f} coverage. "
                    f"Flow result: {flow_val:.1f} min wait. Combined: {adjusted_val:.1f} min."
                )
                interaction_warning = (
                    "Combined result is not a causal prediction. Independent effects may not be additive."
                )
            else:
                # Default to staffing primary if flow primary not defined
                base_val = workforce_baseline.baseline_staffing_coverage_pct or 0.0
                staff_val = staffing_result.scenario_primary_kpi_value or base_val
                adjusted_val = staff_val * interaction_factor
                scenario_kpi_value = adjusted_val
                absolute_change = adjusted_val - base_val
                if base_val > 0:
                    percentage_change = (adjusted_val - base_val) / base_val * 100.0
                direction = DirectionOfChange.INCREASE if adjusted_val > base_val else DirectionOfChange.NO_CHANGE if adjusted_val == base_val else DirectionOfChange.DECREASE
                interpretation = (
                    f"Combined scenario: workforce component with interaction factor {interaction_factor:.2f}. "
                    f"Combined result: {adjusted_val:.2f}%."
                )
                interaction_warning = "Combined result is not a causal prediction."

            if penalty > 0:
                governance_warning += f" Combined-scenario confidence penalty applied: {penalty:.1f}%."

        result = ScenarioResult(
            scenario_run_id=f"SR-{workforce_baseline.baseline_id}-{flow_baseline.baseline_id}-{comparator_id}",
            approval_package_id=workforce_baseline.approval_package_id,
            episode_id=workforce_baseline.episode_id,
            scenario_template_id=workforce_baseline.scenario_template_id,
            comparator_id=comparator_id,
            comparator_type=comparator_type,
            scenario_family=self.family,
            scenario_mode=comparator.get("scenario_mode", "Baseline"),
            scenario_run_timestamp=datetime.utcnow().isoformat(),
            engine_version="2C-2C-1.0",
            baseline_id=workforce_baseline.baseline_id,
            baseline_status=workforce_baseline.baseline_status.value,
            baseline_value=workforce_baseline.baseline_kpi_value,
            baseline_unit=workforce_baseline.baseline_kpi_unit,
            baseline_reference_date=workforce_baseline.baseline_reference_date,
            baseline_data_completeness=workforce_baseline.baseline_data_completeness,
            assumption_set_id="combined-default",
            assumption_profile=profile_id,
            assumption_values_json=json.dumps(assumptions),
            assumption_validation_status="All Valid" if all_valid else "Issues Found",
            assumption_warning_count=len(soft_warnings),
            primary_kpi_id=flow_baseline.dominant_kpi_id or workforce_baseline.dominant_kpi_id,
            baseline_primary_kpi_value=flow_baseline.baseline_kpi_value or workforce_baseline.baseline_kpi_value,
            scenario_primary_kpi_value=scenario_kpi_value,
            absolute_change=absolute_change,
            percentage_change=percentage_change,
            direction_of_change=direction,
            operational_interpretation=interpretation,
            governance_warning=governance_warning + " " + interaction_warning,
            scenario_execution_status=execution_status,
            calculation_rule_id="combined-interaction-adjustment",
            comparator_config_version="2C-2B-1.0",
            assumption_config_version="2C-2B-1.0",
            causality_status="Not Confirmed",
            source_file_list=workforce_baseline.source_file_list + flow_baseline.source_file_list,
            source_record_id_list=workforce_baseline.source_record_id_list + flow_baseline.source_record_id_list,
        )

        return result, validations


def _to_float(val: Any, default: float = 0.0) -> float:
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default
