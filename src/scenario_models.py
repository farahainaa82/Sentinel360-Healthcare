"""Scenario modelling data models and enumerations.

Phase 2C-2C — Baseline and Intervention Calculation Engine.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class BaselineStatus(str, Enum):
    AVAILABLE = "Available"
    AVAILABLE_WITH_CONDITIONS = "Available with Conditions"
    PARTIAL = "Partial"
    UNAVAILABLE = "Unavailable"
    BLOCKED = "Blocked"


class ScenarioExecutionStatus(str, Enum):
    COMPLETED = "Completed"
    COMPLETED_WITH_WARNINGS = "Completed with Warnings"
    BLOCKED_MISSING_BASELINE = "Blocked — Missing Baseline"
    BLOCKED_MISSING_ASSUMPTION = "Blocked — Missing Assumption"
    BLOCKED_INVALID_ASSUMPTION = "Blocked — Invalid Assumption"
    BLOCKED_UNSUPPORTED_FAMILY = "Blocked — Unsupported Family"
    BLOCKED_GOVERNANCE_RULE = "Blocked — Governance Rule"
    MONITORING_ONLY = "Monitoring Only"
    VALIDATION_REQUIRED = "Validation Required"
    NOT_SELECTED = "Not Selected"


class ScenarioConfidence(str, Enum):
    MODERATE = "Moderate"
    LOW = "Low"
    INSUFFICIENT_EVIDENCE = "Insufficient Evidence"


class ComparatorType(str, Enum):
    BASELINE = "Baseline"
    CONSERVATIVE = "Conservative"
    EXPECTED = "Expected"
    HIGHER_INTENSITY = "Higher Intensity"


def parse_comparator_type(value: str) -> ComparatorType:
    """Normalise any comparator-type string to the canonical enum value."""
    mapping = {
        "baseline": ComparatorType.BASELINE,
        "conservative": ComparatorType.CONSERVATIVE,
        "expected": ComparatorType.EXPECTED,
        "higher intensity": ComparatorType.HIGHER_INTENSITY,
        "higher-intensity": ComparatorType.HIGHER_INTENSITY,
    }
    return mapping.get(value.strip().lower(), ComparatorType.BASELINE)


class ValidationOutcome(str, Enum):
    VALID = "Valid"
    VALID_WITH_WARNING = "Valid with Warning"
    INVALID = "Invalid"
    MISSING = "Missing"
    BLOCKED = "Blocked"


class DirectionOfChange(str, Enum):
    INCREASE = "Increase"
    DECREASE = "Decrease"
    NO_CHANGE = "No Change"
    UNCERTAIN = "Uncertain"


@dataclass
class ScenarioBaseline:
    """Immutable baseline record for a scenario package."""

    baseline_id: str
    approval_package_id: str
    episode_id: str
    scenario_template_id: str
    hospital_id: str
    department_id: str
    episode_start_date: str
    episode_end_date: str
    dominant_kpi_id: str
    dominant_kpi_name: str
    baseline_kpi_value: Optional[float]
    baseline_kpi_unit: str
    supporting_kpi_values: Dict[str, Any] = field(default_factory=dict)
    baseline_required_staff: Optional[float] = None
    baseline_available_staff: Optional[float] = None
    baseline_staffing_coverage_pct: Optional[float] = None
    baseline_absenteeism_rate: Optional[float] = None
    baseline_avg_wait_min: Optional[float] = None
    baseline_arrivals: Optional[float] = None
    baseline_service_capacity: Optional[float] = None
    source_file_list: List[str] = field(default_factory=list)
    source_record_id_list: List[str] = field(default_factory=list)
    baseline_observation_count: int = 0
    baseline_data_completeness: float = 0.0
    baseline_confidence: str = "Unavailable"
    baseline_provisional_flag: bool = False
    baseline_contradiction_severity: str = "No Contradiction"
    baseline_status: BaselineStatus = BaselineStatus.UNAVAILABLE
    baseline_created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    baseline_version: str = "2C-2C-1.0"
    baseline_aggregation_method: str = "episode-period mean"
    baseline_reference_date: Optional[str] = None
    baseline_window_start: Optional[str] = None
    baseline_window_end: Optional[str] = None


@dataclass
class AssumptionValidation:
    """Validation result for a single assumption."""

    assumption_id: str
    assumption_name: str
    original_value: Any
    validated_value: Any
    validation_outcome: ValidationOutcome
    validation_message: str
    adjustment_applied: str = "None"
    hard_limit_violated: bool = False
    soft_limit_violated: bool = False


@dataclass
class ScenarioResult:
    """Calculated scenario result for a single comparator."""

    scenario_run_id: str
    approval_package_id: str
    episode_id: str
    scenario_template_id: str
    comparator_id: str
    comparator_type: ComparatorType
    scenario_family: str
    scenario_mode: str
    scenario_run_timestamp: str
    engine_version: str
    baseline_id: str
    baseline_status: str
    baseline_value: Optional[float]
    baseline_unit: str
    baseline_reference_date: Optional[str] = None
    baseline_data_completeness: float = 0.0
    assumption_set_id: str = ""
    assumption_profile: str = ""
    assumption_values_json: str = "{}"
    assumption_validation_status: str = ""
    assumption_warning_count: int = 0
    primary_kpi_id: str = ""
    baseline_primary_kpi_value: Optional[float] = None
    scenario_primary_kpi_value: Optional[float] = None
    absolute_change: Optional[float] = None
    percentage_change: Optional[float] = None
    direction_of_change: DirectionOfChange = DirectionOfChange.UNCERTAIN
    operational_interpretation: str = ""
    affected_supporting_kpis: List[str] = field(default_factory=list)
    supporting_kpi_result_status: str = ""
    contradiction_severity: str = "No Contradiction"
    provisional_warning: bool = False
    causality_status: str = "Not Confirmed"
    final_scenario_confidence: ScenarioConfidence = ScenarioConfidence.INSUFFICIENT_EVIDENCE
    governance_warning: str = ""
    scenario_execution_status: ScenarioExecutionStatus = ScenarioExecutionStatus.NOT_SELECTED
    management_review_required: bool = False
    source_file_list: List[str] = field(default_factory=list)
    source_record_id_list: List[str] = field(default_factory=list)
    recommendation_ids: List[str] = field(default_factory=list)
    evidence_pack_ids: List[str] = field(default_factory=list)
    calculation_rule_id: str = ""
    comparator_config_version: str = ""
    assumption_config_version: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_run_id": self.scenario_run_id,
            "approval_package_id": self.approval_package_id,
            "episode_id": self.episode_id,
            "scenario_template_id": self.scenario_template_id,
            "comparator_id": self.comparator_id,
            "comparator_type": self.comparator_type.value,
            "scenario_family": self.scenario_family,
            "scenario_mode": self.scenario_mode,
            "scenario_run_timestamp": self.scenario_run_timestamp,
            "engine_version": self.engine_version,
            "baseline_id": self.baseline_id,
            "baseline_status": self.baseline_status,
            "baseline_value": self.baseline_value,
            "baseline_unit": self.baseline_unit,
            "baseline_reference_date": self.baseline_reference_date,
            "baseline_data_completeness": self.baseline_data_completeness,
            "assumption_set_id": self.assumption_set_id,
            "assumption_profile": self.assumption_profile,
            "assumption_values_json": self.assumption_values_json,
            "assumption_validation_status": self.assumption_validation_status,
            "assumption_warning_count": self.assumption_warning_count,
            "primary_kpi_id": self.primary_kpi_id,
            "baseline_primary_kpi_value": self.baseline_primary_kpi_value,
            "scenario_primary_kpi_value": self.scenario_primary_kpi_value,
            "absolute_change": self.absolute_change,
            "percentage_change": self.percentage_change,
            "direction_of_change": self.direction_of_change.value,
            "operational_interpretation": self.operational_interpretation,
            "affected_supporting_kpis": self.affected_supporting_kpis,
            "supporting_kpi_result_status": self.supporting_kpi_result_status,
            "contradiction_severity": self.contradiction_severity,
            "provisional_warning": self.provisional_warning,
            "causality_status": self.causality_status,
            "final_scenario_confidence": self.final_scenario_confidence.value,
            "governance_warning": self.governance_warning,
            "scenario_execution_status": self.scenario_execution_status.value,
            "management_review_required": self.management_review_required,
            "source_file_list": self.source_file_list,
            "source_record_id_list": self.source_record_id_list,
            "recommendation_ids": self.recommendation_ids,
            "evidence_pack_ids": self.evidence_pack_ids,
            "calculation_rule_id": self.calculation_rule_id,
            "comparator_config_version": self.comparator_config_version,
            "assumption_config_version": self.assumption_config_version,
        }


@dataclass
class EvidenceRecord:
    """Evidence and lineage record for a scenario run."""

    evidence_id: str
    scenario_run_id: str
    evidence_type: str
    source_type: str
    source_id: str
    source_file: str
    link_type: str
    recorded_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata_json: str = "{}"


@dataclass
class GovernanceRecord:
    """Governance record for a scenario run."""

    governance_id: str
    scenario_run_id: str
    rule_id: str
    rule_name: str
    rule_applied: bool
    rule_outcome: str
    message: str
    applied_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class IssueRecord:
    """Issue record for scenario execution."""

    issue_id: str
    scenario_run_id: str
    issue_type: str
    severity: str
    message: str
    package_id: str
    episode_id: str
    template_id: str
    comparator_id: str
    detected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    resolution_status: str = "Open"
