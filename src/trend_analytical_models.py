"""
Sentinel360 Healthcare — Trend Analytical Models

Governed data models for trend and statistical-signal analysis.
Does not break Phase 2A analytical contracts.

Step: 2B-1
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# 1. Period Comparison Result
# ---------------------------------------------------------------------------

@dataclass
class PeriodComparisonResult:
    comparison_record_id: str = ""
    hospital_id: str = ""
    department_id: str = ""
    kpi_id: str = ""
    kpi_name: str = ""
    domain: str = ""
    unit: str = ""
    period_type: str = "Daily"
    comparison_type: str = ""
    current_period_start: Optional[date] = None
    current_period_end: Optional[date] = None
    comparison_period_start: Optional[date] = None
    comparison_period_end: Optional[date] = None
    current_value: Optional[float] = None
    comparison_value: Optional[float] = None
    absolute_change: Optional[float] = None
    percentage_change: Optional[float] = None
    percentage_change_status: str = ""  # e.g. Calculated, Zero Comparison Value, Comparison Unavailable
    mathematical_trend_direction: str = ""  # Increasing, Decreasing, Stable, Insufficient History, Unavailable
    business_movement_interpretation: str = ""  # Improvement, Deterioration, Stable, Context Review, Insufficient History, Unavailable, Provisional
    interpretation_status: str = ""  # Confirmed, Provisional
    interpretation_reason: str = ""
    calculation_status: str = "Not Calculated"
    history_status: str = ""
    observations_used: int = 0
    coverage_percentage: Optional[float] = None
    source_data_confidence: str = ""
    trend_confidence_level: str = "Unavailable"
    trend_confidence_reason: str = ""
    configuration_version: str = "v1.0-draft"
    trend_run_id: str = ""
    calculated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "comparison_record_id": self.comparison_record_id,
            "hospital_id": self.hospital_id,
            "department_id": self.department_id,
            "kpi_id": self.kpi_id,
            "kpi_name": self.kpi_name,
            "domain": self.domain,
            "unit": self.unit,
            "period_type": self.period_type,
            "comparison_type": self.comparison_type,
            "current_period_start": str(self.current_period_start) if self.current_period_start else None,
            "current_period_end": str(self.current_period_end) if self.current_period_end else None,
            "comparison_period_start": str(self.comparison_period_start) if self.comparison_period_start else None,
            "comparison_period_end": str(self.comparison_period_end) if self.comparison_period_end else None,
            "current_value": self.current_value,
            "comparison_value": self.comparison_value,
            "absolute_change": self.absolute_change,
            "percentage_change": self.percentage_change,
            "percentage_change_status": self.percentage_change_status,
            "mathematical_trend_direction": self.mathematical_trend_direction,
            "business_movement_interpretation": self.business_movement_interpretation,
            "interpretation_status": self.interpretation_status,
            "interpretation_reason": self.interpretation_reason,
            "calculation_status": self.calculation_status,
            "history_status": self.history_status,
            "observations_used": self.observations_used,
            "coverage_percentage": self.coverage_percentage,
            "source_data_confidence": self.source_data_confidence,
            "trend_confidence_level": self.trend_confidence_level,
            "trend_confidence_reason": self.trend_confidence_reason,
            "configuration_version": self.configuration_version,
            "trend_run_id": self.trend_run_id,
            "calculated_at": str(self.calculated_at) if self.calculated_at else None,
        }


# ---------------------------------------------------------------------------
# 2. Rolling Statistic Result
# ---------------------------------------------------------------------------

@dataclass
class RollingStatisticResult:
    rolling_record_id: str = ""
    hospital_id: str = ""
    department_id: str = ""
    kpi_id: str = ""
    reporting_date: Optional[date] = None
    rolling_window: int = 0
    rolling_mean: Optional[float] = None
    rolling_median: Optional[float] = None
    rolling_minimum: Optional[float] = None
    rolling_maximum: Optional[float] = None
    rolling_standard_deviation: Optional[float] = None
    rolling_valid_observation_count: int = 0
    rolling_expected_observation_count: int = 0
    rolling_coverage_percentage: Optional[float] = None
    calculation_status: str = "Not Calculated"
    history_status: str = ""
    trend_run_id: str = ""
    calculated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rolling_record_id": self.rolling_record_id,
            "hospital_id": self.hospital_id,
            "department_id": self.department_id,
            "kpi_id": self.kpi_id,
            "reporting_date": str(self.reporting_date) if self.reporting_date else None,
            "rolling_window": self.rolling_window,
            "rolling_mean": self.rolling_mean,
            "rolling_median": self.rolling_median,
            "rolling_minimum": self.rolling_minimum,
            "rolling_maximum": self.rolling_maximum,
            "rolling_standard_deviation": self.rolling_standard_deviation,
            "rolling_valid_observation_count": self.rolling_valid_observation_count,
            "rolling_expected_observation_count": self.rolling_expected_observation_count,
            "rolling_coverage_percentage": self.rolling_coverage_percentage,
            "calculation_status": self.calculation_status,
            "history_status": self.history_status,
            "trend_run_id": self.trend_run_id,
            "calculated_at": str(self.calculated_at) if self.calculated_at else None,
        }


# ---------------------------------------------------------------------------
# 3. Statistical Signal Result
# ---------------------------------------------------------------------------

@dataclass
class StatisticalSignalResult:
    signal_record_id: str = ""
    hospital_id: str = ""
    department_id: str = ""
    reporting_date: Optional[date] = None
    kpi_id: str = ""
    signal_method: str = ""
    signal_type: str = ""  # No Signal, Positive Deviation, Negative Deviation, Sustained Increase, Sustained Decrease, Volatility Increase, Potential Change Point, Improvement Candidate, Deterioration Candidate, Insufficient History, Unavailable
    signal_value: Optional[float] = None
    signal_direction: str = ""  # positive, negative, both, none
    signal_strength: str = ""  # strong, moderate, weak, none
    signal_status: str = ""
    interpretation_status: str = ""
    observations_used: int = 0
    history_window: int = 0
    history_status: str = ""
    coverage_percentage: Optional[float] = None
    trend_confidence_level: str = "Unavailable"
    sensitivity_value: Optional[float] = None
    sensitivity_approval_status: str = "Draft"
    configuration_version: str = "v1.0-draft"
    trend_run_id: str = ""
    calculated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_record_id": self.signal_record_id,
            "hospital_id": self.hospital_id,
            "department_id": self.department_id,
            "reporting_date": str(self.reporting_date) if self.reporting_date else None,
            "kpi_id": self.kpi_id,
            "signal_method": self.signal_method,
            "signal_type": self.signal_type,
            "signal_value": self.signal_value,
            "signal_direction": self.signal_direction,
            "signal_strength": self.signal_strength,
            "signal_status": self.signal_status,
            "interpretation_status": self.interpretation_status,
            "observations_used": self.observations_used,
            "history_window": self.history_window,
            "history_status": self.history_status,
            "coverage_percentage": self.coverage_percentage,
            "trend_confidence_level": self.trend_confidence_level,
            "sensitivity_value": self.sensitivity_value,
            "sensitivity_approval_status": self.sensitivity_approval_status,
            "configuration_version": self.configuration_version,
            "trend_run_id": self.trend_run_id,
            "calculated_at": str(self.calculated_at) if self.calculated_at else None,
        }


# ---------------------------------------------------------------------------
# 4. Sustained Movement Result
# ---------------------------------------------------------------------------

@dataclass
class SustainedMovementResult:
    movement_record_id: str = ""
    hospital_id: str = ""
    department_id: str = ""
    kpi_id: str = ""
    movement_type: str = ""  # Sustained Increase, Sustained Decrease, Reversal, No Sustained Movement, Insufficient History
    sequence_start_date: Optional[date] = None
    sequence_end_date: Optional[date] = None
    consecutive_observation_count: int = 0
    starting_value: Optional[float] = None
    ending_value: Optional[float] = None
    cumulative_absolute_change: Optional[float] = None
    cumulative_percentage_change: Optional[float] = None
    calculation_status: str = "Not Calculated"
    interpretation_status: str = ""
    trend_confidence_level: str = "Unavailable"
    trend_run_id: str = ""
    calculated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "movement_record_id": self.movement_record_id,
            "hospital_id": self.hospital_id,
            "department_id": self.department_id,
            "kpi_id": self.kpi_id,
            "movement_type": self.movement_type,
            "sequence_start_date": str(self.sequence_start_date) if self.sequence_start_date else None,
            "sequence_end_date": str(self.sequence_end_date) if self.sequence_end_date else None,
            "consecutive_observation_count": self.consecutive_observation_count,
            "starting_value": self.starting_value,
            "ending_value": self.ending_value,
            "cumulative_absolute_change": self.cumulative_absolute_change,
            "cumulative_percentage_change": self.cumulative_percentage_change,
            "calculation_status": self.calculation_status,
            "interpretation_status": self.interpretation_status,
            "trend_confidence_level": self.trend_confidence_level,
            "trend_run_id": self.trend_run_id,
            "calculated_at": str(self.calculated_at) if self.calculated_at else None,
        }


# ---------------------------------------------------------------------------
# 5. Trend Evidence Record
# ---------------------------------------------------------------------------

@dataclass
class TrendEvidenceRecord:
    trend_evidence_id: str = ""
    result_record_id: str = ""
    result_type: str = ""  # period_comparison, rolling_statistic, signal, sustained_movement
    kpi_id: str = ""
    evidence_role: str = ""  # current, comparison, history, excluded
    source_analytical_record_id: str = ""
    source_reporting_date: Optional[date] = None
    source_kpi_value: Optional[float] = None
    observation_included: bool = False
    exclusion_reason: str = ""
    trend_run_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trend_evidence_id": self.trend_evidence_id,
            "result_record_id": self.result_record_id,
            "result_type": self.result_type,
            "kpi_id": self.kpi_id,
            "evidence_role": self.evidence_role,
            "source_analytical_record_id": self.source_analytical_record_id,
            "source_reporting_date": str(self.source_reporting_date) if self.source_reporting_date else None,
            "source_kpi_value": self.source_kpi_value,
            "observation_included": self.observation_included,
            "exclusion_reason": self.exclusion_reason,
            "trend_run_id": self.trend_run_id,
        }


# ---------------------------------------------------------------------------
# 6. Trend Lineage Record
# ---------------------------------------------------------------------------

@dataclass
class TrendLineageRecord:
    trend_lineage_id: str = ""
    result_record_id: str = ""
    result_type: str = ""
    kpi_id: str = ""
    source_analytical_dataset: str = ""
    source_analytical_record_id: str = ""
    source_integration_run_id: str = ""
    transformation_name: str = ""
    configuration_version: str = "v1.0-draft"
    trend_run_id: str = ""
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trend_lineage_id": self.trend_lineage_id,
            "result_record_id": self.result_record_id,
            "result_type": self.result_type,
            "kpi_id": self.kpi_id,
            "source_analytical_dataset": self.source_analytical_dataset,
            "source_analytical_record_id": self.source_analytical_record_id,
            "source_integration_run_id": self.source_integration_run_id,
            "transformation_name": self.transformation_name,
            "configuration_version": self.configuration_version,
            "trend_run_id": self.trend_run_id,
            "created_at": str(self.created_at) if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# 7. Trend Issue Record
# ---------------------------------------------------------------------------

@dataclass
class TrendIssueRecord:
    trend_issue_id: str = ""
    severity: str = ""  # Critical, Error, Warning, Information
    issue_type: str = ""
    hospital_id: str = ""
    department_id: str = ""
    kpi_id: str = ""
    reporting_date: Optional[date] = None
    message: str = ""
    source_record_id: str = ""
    trend_run_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trend_issue_id": self.trend_issue_id,
            "severity": self.severity,
            "issue_type": self.issue_type,
            "hospital_id": self.hospital_id,
            "department_id": self.department_id,
            "kpi_id": self.kpi_id,
            "reporting_date": str(self.reporting_date) if self.reporting_date else None,
            "message": self.message,
            "source_record_id": self.source_record_id,
            "trend_run_id": self.trend_run_id,
        }


# ---------------------------------------------------------------------------
# 8. Trend Audit Record
# ---------------------------------------------------------------------------

@dataclass
class TrendAuditRecord:
    audit_id: str = ""
    event_type: str = ""
    event_status: str = ""
    kpi_id: str = ""
    trend_run_id: str = ""
    configuration_version: str = "v1.0-draft"
    event_time: Optional[datetime] = None
    details: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "event_type": self.event_type,
            "event_status": self.event_status,
            "kpi_id": self.kpi_id,
            "trend_run_id": self.trend_run_id,
            "configuration_version": self.configuration_version,
            "event_time": str(self.event_time) if self.event_time else None,
            "details": self.details,
        }


# ---------------------------------------------------------------------------
# 9. Trend Run Manifest
# ---------------------------------------------------------------------------

@dataclass
class TrendRunManifest:
    trend_run_id: str = ""
    run_type: str = "trend_and_signal_processing"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: str = ""
    kpi_ids: List[str] = field(default_factory=list)
    period_types: List[str] = field(default_factory=list)
    comparison_types: List[str] = field(default_factory=list)
    signal_methods: List[str] = field(default_factory=list)
    issue_count: int = 0
    exclusion_count: int = 0
    output_datasets: List[str] = field(default_factory=list)
    phase2a_immutability_verified: bool = False
    configuration_files: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trend_run_id": self.trend_run_id,
            "run_type": self.run_type,
            "start_time": str(self.start_time) if self.start_time else None,
            "end_time": str(self.end_time) if self.end_time else None,
            "status": self.status,
            "kpi_ids": self.kpi_ids,
            "period_types": self.period_types,
            "comparison_types": self.comparison_types,
            "signal_methods": self.signal_methods,
            "issue_count": self.issue_count,
            "exclusion_count": self.exclusion_count,
            "output_datasets": self.output_datasets,
            "phase2a_immutability_verified": self.phase2a_immutability_verified,
            "configuration_files": self.configuration_files,
        }
