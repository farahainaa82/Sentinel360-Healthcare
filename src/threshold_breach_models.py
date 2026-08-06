"""
Sentinel360 Healthcare — Step 2B-2 Threshold Breach and Watch-Condition Models
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ThresholdState(str, Enum):
    GREEN = "Green"
    AMBER = "Amber"
    RED = "Red"
    LOW_UTILISATION = "Low Utilisation"
    LOWER_AMBER = "Lower Amber"
    NORMAL_OPERATING_BAND = "Normal Operating Band"
    UPPER_AMBER = "Upper Amber"
    CRITICAL_CAPACITY_PRESSURE = "Critical Capacity Pressure"
    NOT_ASSESSED = "Not Assessed"
    UNAVAILABLE = "Unavailable"


class BreachType(str, Enum):
    NO_BREACH = "No Breach"
    AMBER_CONDITION = "Amber Condition"
    RED_BREACH = "Red Breach"
    CRITICAL_CAPACITY_BREACH = "Critical Capacity Breach"
    LOW_UTILISATION_CONDITION = "Low Utilisation Condition"
    PROVISIONAL_BREACH = "Provisional Breach"
    UNAVAILABLE = "Unavailable"
    NOT_ASSESSED = "Not Assessed"


class WatchConditionType(str, Enum):
    NONE = "None"
    REPEATED_AMBER = "Repeated Amber"
    APPROACHING_THRESHOLD = "Approaching Threshold"
    DETERIORATING_TREND = "Deteriorating Trend"
    SUSTAINED_DETERIORATION = "Sustained Deterioration"
    AMBER_PLUS_DETERIORATING_TREND = "Amber Plus Deteriorating Trend"
    REPEATED_RED = "Repeated Red"
    ESCALATING_SEVERITY = "Escalating Severity"
    RECOVERY_WATCH = "Recovery Watch"
    PROVISIONAL_WATCH = "Provisional Watch"
    REVIEW_DUE_GOVERNANCE_WATCH = "Review-Due Governance Watch"


class WatchSeverity(str, Enum):
    NONE = "None"
    INFORMATIONAL = "Informational"
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    CRITICAL = "Critical"


class OperationalUseStatus(str, Enum):
    FULLY_OPERATIONAL = "Fully Operational"
    PROTOTYPE_USE_WITH_CONDITIONS = "Prototype Use with Conditions"
    NOT_FOR_CURRENT_OPERATIONAL_USE = "Not for Current Operational Use"


class ReviewDueStatus(str, Enum):
    NOT_APPLICABLE = "Not Applicable"
    NOT_YET_DUE = "Not Yet Due"
    DUE_SOON = "Due Soon"
    OVERDUE = "Overdue"


class TrendInterpretation(str, Enum):
    IMPROVING = "Improving"
    STABLE = "Stable"
    DETERIORATING = "Deteriorating"
    VOLATILE = "Volatile"
    INSUFFICIENT_EVIDENCE = "Insufficient Evidence"
    NOT_APPLICABLE = "Not Applicable"


class IssueCategory(str, Enum):
    MISSING_KPI_RECORD = "Missing KPI Record"
    MISSING_ACTIVE_THRESHOLD = "Missing Active Threshold"
    INVALID_THRESHOLD_VERSION = "Invalid Threshold Version"
    INACTIVE_THRESHOLD = "Inactive Threshold"
    EXPIRED_THRESHOLD = "Expired Threshold"
    MISSING_TREND_EVIDENCE = "Missing Trend Evidence"
    INSUFFICIENT_PERSISTENCE_HISTORY = "Insufficient Persistence History"
    BOUNDARY_CLASSIFICATION_ERROR = "Boundary Classification Error"
    DUPLICATE_WATCH_RECORD = "Duplicate Watch Record"
    GOVERNANCE_METADATA_MISSING = "Governance Metadata Missing"
    PROVISIONAL_REVIEW_OVERDUE = "Provisional Review Overdue"
    SOURCE_LINEAGE_MISSING = "Source Lineage Missing"


class IssueSeverity(str, Enum):
    WARNING = "Warning"
    BLOCKING = "Blocking"


@dataclass
class ThresholdClassificationResult:
    classification_record_id: str
    integration_record_id: str
    hospital_id: str
    department_id: str
    reporting_date: str
    kpi_id: str
    kpi_name: str
    kpi_value: Optional[float]
    kpi_unit: str
    calculation_status: str
    threshold_state: str
    threshold_version: str
    threshold_source: str
    approval_status: str
    threshold_is_provisional: bool
    lower_red_boundary: Optional[float]
    lower_amber_boundary: Optional[float]
    green_lower_boundary: Optional[float]
    green_upper_boundary: Optional[float]
    upper_amber_boundary: Optional[float]
    upper_red_boundary: Optional[float]
    boundary_inclusivity_rule: str
    decision_record_id: str
    effective_date: str
    required_review_date: Optional[str]
    engine_run_id: str
    processed_at: str


@dataclass
class BreachEventResult:
    breach_record_id: str
    classification_record_id: str
    integration_record_id: str
    hospital_id: str
    department_id: str
    reporting_date: str
    kpi_id: str
    kpi_name: str
    kpi_value: Optional[float]
    threshold_state: str
    breach_type: str
    breach_flag: bool
    threshold_version: str
    approval_status: str
    threshold_is_provisional: bool
    operational_use_status: str
    governance_warning: str
    engine_run_id: str
    processed_at: str


@dataclass
class WatchConditionResult:
    watch_record_id: str
    classification_record_id: str
    integration_record_id: str
    hospital_id: str
    department_id: str
    reporting_date: str
    kpi_id: str
    kpi_name: str
    kpi_value: Optional[float]
    kpi_unit: str
    calculation_status: str
    threshold_state: str
    breach_type: str
    breach_flag: bool
    threshold_version: str
    threshold_source: str
    approval_status: str
    threshold_is_provisional: bool
    watch_condition_flag: bool
    watch_condition_type: str
    watch_severity: str
    watch_rule_id: str
    watch_rule_version: str
    watch_summary: str
    persistence_count: int
    qualifying_observation_count: int
    observation_window: int
    repeated_amber_flag: bool
    repeated_red_flag: bool
    trend_direction: str
    operational_trend_interpretation: str
    trend_confidence: str
    sustained_movement_flag: bool
    statistical_signal_flag: bool
    boundary_reference: str
    distance_to_boundary: Optional[float]
    distance_measure_type: str
    approaching_threshold_flag: bool
    operational_use_status: str
    governance_warning: str
    required_review_date: Optional[str]
    review_due_status: str
    source_kpi_record_id: str
    source_threshold_record_id: str
    source_trend_record_id: str
    evidence_record_id: str
    lineage_record_id: str
    engine_run_id: str
    processed_at: str
    issue_flag: bool


@dataclass
class WatchIssueResult:
    issue_record_id: str
    hospital_id: str
    department_id: str
    reporting_date: str
    kpi_id: str
    issue_category: str
    issue_severity: str
    issue_description: str
    engine_run_id: str
    processed_at: str


@dataclass
class DailySummaryResult:
    summary_record_id: str
    hospital_id: str
    department_id: str
    reporting_date: str
    kpi_count: int
    calculated_kpi_count: int
    green_count: int
    amber_count: int
    red_count: int
    critical_capacity_pressure_count: int
    low_utilisation_count: int
    watch_condition_count: int
    high_watch_count: int
    critical_watch_count: int
    provisional_watch_count: int
    unavailable_count: int
    max_observed_watch_severity: str
    summary_status: str
    engine_run_id: str
    processed_at: str
