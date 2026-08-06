"""
Sentinel360 Healthcare — Analytical Models

Defines typed data models for the analytical layer.
No actual KPI calculation is performed in Step 2A-1.

Step: 2A-1
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# 1. KPI Definition
# ---------------------------------------------------------------------------

@dataclass
class KPIDefinition:
    """Governed definition of an approved KPI."""

    kpi_id: str = ""
    kpi_name: str = ""
    domain: str = ""
    description: str = ""
    numerator_definition: str = ""
    denominator_definition: str = ""
    formula_text: str = ""
    unit: str = ""
    directionality: str = ""  # e.g. "higher_is_better", "lower_is_better", "neutral"
    grain: str = ""  # e.g. "hospital-department-date", "hospital-department-month"
    calculation_frequency: str = ""
    authoritative_input_dataset: str = ""
    required_fields: List[str] = field(default_factory=list)
    eligibility_rules: List[str] = field(default_factory=list)
    exclusion_rules: List[str] = field(default_factory=list)
    null_treatment: str = ""
    zero_denominator_treatment: str = ""
    minimum_denominator: Optional[float] = None
    threshold_config_reference: str = ""
    data_confidence_rule_reference: str = ""
    config_version: str = ""
    approval_requirement: str = ""
    readiness_status: str = "Not Applicable"  # Ready, Conditionally Ready, Blocked, Not Applicable
    unresolved_rules: List[str] = field(default_factory=list)
    effective_date: Optional[date] = None
    approval_status: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kpi_id": self.kpi_id,
            "kpi_name": self.kpi_name,
            "domain": self.domain,
            "description": self.description,
            "numerator_definition": self.numerator_definition,
            "denominator_definition": self.denominator_definition,
            "formula_text": self.formula_text,
            "unit": self.unit,
            "directionality": self.directionality,
            "grain": self.grain,
            "calculation_frequency": self.calculation_frequency,
            "authoritative_input_dataset": self.authoritative_input_dataset,
            "required_fields": self.required_fields,
            "eligibility_rules": self.eligibility_rules,
            "exclusion_rules": self.exclusion_rules,
            "null_treatment": self.null_treatment,
            "zero_denominator_treatment": self.zero_denominator_treatment,
            "minimum_denominator": self.minimum_denominator,
            "threshold_config_reference": self.threshold_config_reference,
            "data_confidence_rule_reference": self.data_confidence_rule_reference,
            "config_version": self.config_version,
            "approval_requirement": self.approval_requirement,
            "readiness_status": self.readiness_status,
            "unresolved_rules": self.unresolved_rules,
            "effective_date": str(self.effective_date) if self.effective_date else None,
            "approval_status": self.approval_status,
        }


# ---------------------------------------------------------------------------
# 2. KPI Calculation Request / Result / Status
# ---------------------------------------------------------------------------

@dataclass
class KPICalculationRequest:
    """Request to calculate a KPI for a specific scope."""

    kpi_id: str = ""
    hospital_id: Optional[str] = None
    department_id: Optional[str] = None
    reporting_date: Optional[date] = None
    reporting_month: Optional[int] = None
    reporting_year: Optional[int] = None
    calculation_run_id: str = ""
    requested_at: Optional[datetime] = None


@dataclass
class KPINumeratorEvidence:
    """Evidence supporting the numerator value."""

    source_field: str = ""
    source_value: Optional[float] = None
    source_record_count: int = 0
    aggregation_method: str = ""
    eligibility_applied: bool = False


@dataclass
class KPIDenominatorEvidence:
    """Evidence supporting the denominator value."""

    source_field: str = ""
    source_value: Optional[float] = None
    source_record_count: int = 0
    aggregation_method: str = ""
    eligibility_applied: bool = False


@dataclass
class KPIExclusionRecord:
    """Record of why a data point was excluded from KPI calculation."""

    exclusion_reason: str = ""
    source_dataset: str = ""
    source_record_id: str = ""
    field_name: str = ""
    field_value: Any = None


@dataclass
class KPICalculationResult:
    """Result of a KPI calculation attempt."""

    kpi_id: str = ""
    kpi_name: str = ""
    hospital_id: Optional[str] = None
    department_id: Optional[str] = None
    reporting_date: Optional[date] = None
    numerator_value: Optional[float] = None
    denominator_value: Optional[float] = None
    kpi_value: Optional[float] = None
    unit: str = ""
    calculation_status: str = "Not Calculated"  # Calculated, Insufficient Data, Zero Denominator, Configuration Missing, Rule Pending, Invalid Input, Not Calculated
    readiness_status: str = ""
    numerator_evidence: Optional[KPINumeratorEvidence] = None
    denominator_evidence: Optional[KPIDenominatorEvidence] = None
    exclusion_records: List[KPIExclusionRecord] = field(default_factory=list)
    calculation_run_id: str = ""
    calculated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kpi_id": self.kpi_id,
            "kpi_name": self.kpi_name,
            "hospital_id": self.hospital_id,
            "department_id": self.department_id,
            "reporting_date": str(self.reporting_date) if self.reporting_date else None,
            "numerator_value": self.numerator_value,
            "denominator_value": self.denominator_value,
            "kpi_value": self.kpi_value,
            "unit": self.unit,
            "calculation_status": self.calculation_status,
            "readiness_status": self.readiness_status,
            "calculation_run_id": self.calculation_run_id,
            "calculated_at": str(self.calculated_at) if self.calculated_at else None,
        }


# ---------------------------------------------------------------------------
# 3. Threshold
# ---------------------------------------------------------------------------

@dataclass
class ThresholdAssignment:
    """A threshold value assignment for a KPI."""

    threshold_id: str = ""
    kpi_id: str = ""
    threshold_name: str = ""
    threshold_value: Optional[float] = None
    threshold_direction: str = ""  # e.g. "above", "below", "between"
    severity: str = ""  # e.g. "critical", "warning", "info"
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    approved_by: str = ""
    approval_date: Optional[date] = None


@dataclass
class ThresholdVersion:
    """Versioned threshold configuration."""

    version_id: str = ""
    kpi_id: str = ""
    version_number: str = ""
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    thresholds: List[ThresholdAssignment] = field(default_factory=list)
    approved: bool = False


# ---------------------------------------------------------------------------
# 4. Data Confidence
# ---------------------------------------------------------------------------

@dataclass
class DataConfidenceResult:
    """Result of assessing data confidence for a KPI calculation."""

    kpi_id: str = ""
    confidence_level: str = ""  # high, medium, low, insufficient
    confidence_score: Optional[float] = None
    completeness_pct: Optional[float] = None
    freshness_days: Optional[int] = None
    validation_passed: bool = False
    issues: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 5. Analytical Issue
# ---------------------------------------------------------------------------

@dataclass
class AnalyticalIssue:
    """Structured issue record for the analytical layer."""

    issue_id: str = ""
    issue_type: str = ""  # Critical, Error, Warning, Information
    severity: str = ""
    issue_description: str = ""
    source_dataset: str = ""
    kpi_id: str = ""
    field_name: str = ""
    resolution_status: str = "Open"
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "issue_type": self.issue_type,
            "severity": self.severity,
            "issue_description": self.issue_description,
            "source_dataset": self.source_dataset,
            "kpi_id": self.kpi_id,
            "field_name": self.field_name,
            "resolution_status": self.resolution_status,
            "created_at": str(self.created_at) if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# 6. Lineage and Audit
# ---------------------------------------------------------------------------

@dataclass
class AnalyticalLineageRecord:
    """Lineage record for analytical outputs."""

    output_record_id: str = ""
    output_dataset: str = ""
    source_dataset: str = ""
    source_record_id: str = ""
    transformation_name: str = ""
    transformation_version: str = ""
    kpi_id: str = ""
    calculation_run_id: str = ""
    processed_datetime: Optional[datetime] = None


@dataclass
class AnalyticalAuditRecord:
    """Audit record for analytical layer operations."""

    audit_id: str = ""
    operation: str = ""
    dataset_name: str = ""
    record_count: int = 0
    calculation_run_id: str = ""
    performed_by: str = ""
    performed_at: Optional[datetime] = None
    notes: str = ""


# ---------------------------------------------------------------------------
# 7. Configuration Provenance
# ---------------------------------------------------------------------------

@dataclass
class ConfigurationProvenance:
    """Provenance record for configuration used in analytical processing."""

    config_file: str = ""
    config_version: str = ""
    loaded_at: Optional[datetime] = None
    checksum: str = ""
    row_count: int = 0
    validated: bool = False
    validation_issues: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 8. Calculation Run Manifest
# ---------------------------------------------------------------------------

@dataclass
class CalculationRunManifest:
    """Manifest for an analytical calculation run."""

    calculation_run_id: str = ""
    run_type: str = ""  # e.g. "validation", "calculation", "governance_check"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: str = ""
    kpi_ids: List[str] = field(default_factory=list)
    issue_count: int = 0
    exclusion_count: int = 0
    output_datasets: List[str] = field(default_factory=list)
    phase1_immutability_verified: bool = False
    phase1_checksums_match: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "calculation_run_id": self.calculation_run_id,
            "run_type": self.run_type,
            "start_time": str(self.start_time) if self.start_time else None,
            "end_time": str(self.end_time) if self.end_time else None,
            "status": self.status,
            "kpi_ids": self.kpi_ids,
            "issue_count": self.issue_count,
            "exclusion_count": self.exclusion_count,
            "output_datasets": self.output_datasets,
            "phase1_immutability_verified": self.phase1_immutability_verified,
            "phase1_checksums_match": self.phase1_checksums_match,
        }


# ---------------------------------------------------------------------------
# 9. Schema Validation Result
# ---------------------------------------------------------------------------

@dataclass
class SchemaValidationResult:
    """Result of validating an analytical output schema."""

    schema_name: str = ""
    required_fields_present: List[str] = field(default_factory=list)
    required_fields_missing: List[str] = field(default_factory=list)
    optional_fields_present: List[str] = field(default_factory=list)
    extra_fields: List[str] = field(default_factory=list)
    valid: bool = False
