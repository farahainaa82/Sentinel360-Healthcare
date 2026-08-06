"""
Sentinel360 Healthcare — Threshold Calibration Models

Step: 2B-1A — KPI Threshold Calibration and Validation

Provides governed data models for threshold candidate generation,
validation, classification, burden testing, stability analysis,
trend alignment, and stakeholder review.

All candidates remain provisional. No approved thresholds are created here.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# 1. Controlled Enums
# ---------------------------------------------------------------------------

class Directionality(str, Enum):
    HIGHER_IS_BETTER = "Higher is better"
    LOWER_IS_BETTER = "Lower is better"
    CONTEXT_SENSITIVE = "Context-sensitive"


class DataSufficiency(str, Enum):
    STRONG = "Strong"
    MODERATE = "Moderate"
    LIMITED = "Limited"
    INSUFFICIENT = "Insufficient"


class CandidateType(str, Enum):
    CONSERVATIVE = "Conservative"
    BALANCED = "Balanced"
    SENSITIVE = "Sensitive"


class CandidateStatus(str, Enum):
    CANDIDATE_GREEN = "Candidate Green"
    CANDIDATE_AMBER = "Candidate Amber"
    CANDIDATE_RED = "Candidate Red"
    CANDIDATE_LOW_UTILISATION = "Candidate Low Utilisation"
    CANDIDATE_HIGH_PRESSURE = "Candidate High Pressure"
    NOT_ASSESSED = "Not Assessed"
    UNAVAILABLE = "Unavailable"


class CalibrationMethod(str, Enum):
    EXISTING_DRAFT_REVIEW = "Existing Draft Threshold Review"
    PERCENTILE_BASED = "Percentile-Based Calibration"
    MEAN_SD = "Mean and Standard-Deviation Calibration"
    MEDIAN_MAD = "Median and MAD Calibration"
    HISTORICAL_BURDEN = "Historical Classification-Burden Calibration"
    TREND_LINKED = "Trend-Linked Sensitivity Review"
    DOMAIN_BENCHMARK = "Domain-Benchmark Placeholder Review"
    HYBRID = "Hybrid Candidate Calibration"


class StabilityStatus(str, Enum):
    STABLE = "Stable"
    MODERATELY_STABLE = "Moderately Stable"
    UNSTABLE = "Unstable"
    NOT_ASSESSABLE = "Not Assessable"


class AgreementStatus(str, Enum):
    AGREEMENT = "Agreement"
    DISAGREEMENT = "Disagreement"
    CONTEXT_REVIEW = "Context Review"
    UNAVAILABLE = "Unavailable"


class ClassificationBurdenLevel(str, Enum):
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    VERY_HIGH = "Very High"


class RecommendationStrength(str, Enum):
    STRONG = "Strong Technical Candidate"
    MODERATE = "Moderate Technical Candidate"
    WEAK = "Weak Technical Candidate"
    INSUFFICIENT = "Insufficient Evidence"


class ApprovalStatus(str, Enum):
    CANDIDATE = "Candidate"
    PENDING_REVIEW = "Pending Stakeholder Review"
    NOT_ASSESSED = "Not Assessed"


class ValidityStatus(str, Enum):
    VALID = "Valid"
    INVALID = "Invalid"
    DUPLICATE = "Duplicate"
    NOT_APPLICABLE = "Not Applicable"


class InclusivityRule(str, Enum):
    LOWER_INCLUSIVE = "Lower boundary inclusive, upper exclusive"
    UPPER_INCLUSIVE = "Upper boundary inclusive, lower exclusive"
    BOTH_INCLUSIVE = "Both boundaries inclusive"
    BOTH_EXCLUSIVE = "Both boundaries exclusive"
    LOWER_INCLUSIVE_MAX_INCLUSIVE = "Lower boundary inclusive, upper exclusive; global maximum inclusive"


# ---------------------------------------------------------------------------
# 2. Boundary Model
# ---------------------------------------------------------------------------

@dataclass
class ThresholdBoundary:
    lower_red: Optional[float] = None
    lower_amber: Optional[float] = None
    green_lower: Optional[float] = None
    green_upper: Optional[float] = None
    upper_amber: Optional[float] = None
    upper_red: Optional[float] = None
    inclusivity_rule: str = "Lower boundary inclusive, upper exclusive"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# 3. Distribution Profile
# ---------------------------------------------------------------------------

@dataclass
class ThresholdDistributionProfile:
    profile_record_id: str
    kpi_id: str
    kpi_name: str
    unit: str
    calculated_count: int
    unavailable_count: int
    availability_percentage: float
    minimum: Optional[float]
    maximum: Optional[float]
    mean: Optional[float]
    median: Optional[float]
    standard_deviation: Optional[float]
    mad: Optional[float]
    percentile_01: Optional[float]
    percentile_05: Optional[float]
    percentile_10: Optional[float]
    percentile_25: Optional[float]
    percentile_50: Optional[float]
    percentile_75: Optional[float]
    percentile_90: Optional[float]
    percentile_95: Optional[float]
    percentile_99: Optional[float]
    interquartile_range: Optional[float]
    skewness: Optional[float]
    zero_count: int
    above_100_count: int
    distinct_value_count: int
    hospital_variation: Optional[float]
    department_variation: Optional[float]
    monthly_variation: Optional[float]
    data_sufficiency: str
    sufficiency_reason: str
    calibration_run_id: str
    calculated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# 4. Threshold Candidate
# ---------------------------------------------------------------------------

@dataclass
class ThresholdCandidate:
    threshold_candidate_id: str
    kpi_id: str
    kpi_name: str
    candidate_name: str
    candidate_type: str
    directionality: str
    lower_red_boundary: Optional[float]
    lower_amber_boundary: Optional[float]
    green_lower_boundary: Optional[float]
    green_upper_boundary: Optional[float]
    upper_amber_boundary: Optional[float]
    upper_red_boundary: Optional[float]
    unit: str
    boundary_inclusivity_rule: str
    calibration_method: str
    calibration_period_start: str
    calibration_period_end: str
    valid_observation_count: int
    unavailable_observation_count: int
    data_sufficiency: str
    approval_status: str
    threshold_is_provisional: bool
    version: str
    rationale: str
    limitations: str
    candidate_validity_status: str = "Valid"
    rejection_reason: Optional[str] = None
    duplicate_of_candidate_id: Optional[str] = None
    technical_score: Optional[float] = None
    score_components: Optional[Dict[str, float]] = None
    recommendation_strength: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def get_boundary_tuple(self) -> tuple:
        """Return a hashable tuple of boundaries for deduplication."""
        return (
            round(self.lower_red_boundary, 6) if self.lower_red_boundary is not None else None,
            round(self.lower_amber_boundary, 6) if self.lower_amber_boundary is not None else None,
            round(self.green_lower_boundary, 6) if self.green_lower_boundary is not None else None,
            round(self.green_upper_boundary, 6) if self.green_upper_boundary is not None else None,
            round(self.upper_amber_boundary, 6) if self.upper_amber_boundary is not None else None,
            round(self.upper_red_boundary, 6) if self.upper_red_boundary is not None else None,
        )


# ---------------------------------------------------------------------------
# 5. Classification Result (row-level)
# ---------------------------------------------------------------------------

@dataclass
class ThresholdClassificationResult:
    candidate_classification_id: str
    threshold_candidate_id: str
    integration_record_id: str
    hospital_id: str
    department_id: str
    reporting_date: str
    kpi_id: str
    kpi_value: Optional[float]
    calculation_status: str
    candidate_threshold_status: str
    classification_reason: str
    threshold_is_provisional: bool
    calibration_run_id: str
    classified_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# 6. Burden Result
# ---------------------------------------------------------------------------

@dataclass
class ThresholdBurdenResult:
    burden_record_id: str
    threshold_candidate_id: str
    kpi_id: str
    candidate_green_count: int
    candidate_amber_count: int
    candidate_red_count: int
    not_assessed_count: int
    unavailable_count: int
    green_percentage: float
    amber_percentage: float
    red_percentage: float
    amber_plus_red_percentage: float
    potential_alert_days: int
    status_transition_count: int
    maximum_consecutive_amber: int
    maximum_consecutive_red: int
    classification_burden_level: str
    calibration_run_id: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# 7. Stability Result
# ---------------------------------------------------------------------------

@dataclass
class ThresholdStabilityResult:
    stability_record_id: str
    threshold_candidate_id: str
    kpi_id: str
    test_dimension: str
    test_segment: str
    candidate_green_percentage: float
    candidate_amber_percentage: float
    candidate_red_percentage: float
    deviation_from_full_period: float
    stability_status: str
    stability_reason: str
    calibration_run_id: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# 8. Trend Alignment Result
# ---------------------------------------------------------------------------

@dataclass
class ThresholdTrendAlignment:
    alignment_record_id: str
    threshold_candidate_id: str
    kpi_id: str
    candidate_threshold_status: str
    business_movement_interpretation: str
    agreement_status: str
    record_count: int
    agreement_percentage: float
    context_review_count: int
    calibration_run_id: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# 9. Recommendation
# ---------------------------------------------------------------------------

@dataclass
class ThresholdRecommendation:
    recommendation_id: str
    kpi_id: str
    preferred_candidate_id: str
    preferred_candidate_name: str
    technical_recommendation: str
    recommendation_strength: str
    alternative_candidate_id: Optional[str]
    data_sufficiency: str
    stability_status: str
    classification_burden_level: str
    benchmark_status: str
    stakeholder_approval_required: bool
    approval_status: str
    limitations: str
    calibration_run_id: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# 10. Evidence, Issue, and Audit Records
# ---------------------------------------------------------------------------

@dataclass
class ThresholdEvidenceRecord:
    evidence_record_id: str
    kpi_id: str
    evidence_category: str
    evidence_description: str
    supporting_value: Optional[str]
    source_dataset: str
    calibration_run_id: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ThresholdIssueRecord:
    issue_record_id: str
    kpi_id: Optional[str]
    issue_category: str
    issue_severity: str
    issue_description: str
    recommended_action: Optional[str]
    blocking: bool
    calibration_run_id: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ThresholdAuditRecord:
    audit_record_id: str
    audit_phase: str
    audit_action: str
    entity_type: str
    entity_id: str
    audit_result: str
    details: Optional[str]
    calibration_run_id: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# 11. Calibration Manifest
# ---------------------------------------------------------------------------

@dataclass
class ThresholdCalibrationManifest:
    calibration_run_id: str
    step_name: str
    step_version: str
    executed_at: str
    project_root: str
    prerequisites_valid: bool
    prerequisite_issues: List[str]
    kpis_processed: List[str]
    distribution_profiles_generated: int
    candidates_generated: int
    candidates_valid: int
    candidates_invalid: int
    candidates_duplicate: int
    candidates_shortlisted: int
    classification_rows_generated: int
    classification_row_limit: int
    volume_control_passed: bool
    burden_results_generated: int
    stability_results_generated: int
    trend_alignment_results_generated: int
    recommendations_generated: int
    evidence_records_generated: int
    issue_records_generated: int
    audit_records_generated: int
    schema_validation_passed: bool
    key_validation_passed: bool
    formula_verification_passed: bool
    immutability_verification_passed: bool
    readiness_for_2b1b: str
    blocking_issues_count: int
    warnings_count: int
    computational_volume_report: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# 12. Existing Config Review Record
# ---------------------------------------------------------------------------

@dataclass
class ExistingThresholdReviewRecord:
    review_record_id: str
    kpi_id: str
    kpi_name: str
    review_aspect: str
    review_finding: str
    defect_found: bool
    recommended_correction: Optional[str]
    calibration_run_id: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
