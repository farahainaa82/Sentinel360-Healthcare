"""
Sentinel360 Healthcare — Step 2B-1B Stakeholder Approval Models

Governed data classes for stakeholder review, decision recording,
validation, and threshold promotion.

All thresholds remain provisional until explicit stakeholder approval.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Enums as controlled string values
# ---------------------------------------------------------------------------

class DecisionType:
    APPROVE_CANDIDATE = "Approve Candidate"
    APPROVE_WITH_MODIFIED_BOUNDARIES = "Approve with Modified Boundaries"
    CONDITIONAL_APPROVAL = "Conditional Approval"
    REJECT = "Reject"
    DEFER = "Defer"
    MORE_EVIDENCE_REQUIRED = "More Evidence Required"
    NO_DECISION = "No Decision"


class ApprovalStatus:
    DRAFT = "Draft"
    CANDIDATE = "Candidate"
    PENDING_STAKEHOLDER_REVIEW = "Pending Stakeholder Review"
    CONDITIONALLY_APPROVED = "Conditionally Approved"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    DEFERRED = "Deferred"
    SUPERSEDED = "Superseded"
    EXPIRED = "Expired"


class PromotionReadiness:
    READY_FOR_PROMOTION = "Ready for Promotion"
    READY_FOR_CONDITIONAL_PROMOTION = "Ready for Conditional Promotion"
    PENDING_DECISION = "Pending Decision"
    INVALID_DECISION = "Invalid Decision"
    REJECTED = "Rejected"
    DEFERRED = "Deferred"
    MORE_EVIDENCE_REQUIRED = "More Evidence Required"


class ValidationStatus:
    PENDING = "Pending"
    VALID = "Valid"
    INVALID = "Invalid"
    INCOMPLETE = "Incomplete"


class Step2B2Readiness:
    READY = "Ready"
    READY_WITH_CONDITIONS = "Ready with Conditions"
    PARTIALLY_READY = "Partially Ready"
    NOT_READY = "Not Ready"
    AWAITING_STAKEHOLDER_DECISION = "Awaiting Stakeholder Decision"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ApprovalRole:
    approval_role_id: str
    approval_role_name: str
    responsibility: str
    approval_required: bool
    sequence_order: int
    can_modify_boundary: bool
    can_conditionally_approve: bool
    can_reject: bool
    can_defer: bool
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "approval_role_id": self.approval_role_id,
            "approval_role_name": self.approval_role_name,
            "responsibility": self.responsibility,
            "approval_required": self.approval_required,
            "sequence_order": self.sequence_order,
            "can_modify_boundary": self.can_modify_boundary,
            "can_conditionally_approve": self.can_conditionally_approve,
            "can_reject": self.can_reject,
            "can_defer": self.can_defer,
            "notes": self.notes,
        }


@dataclass
class StakeholderDecision:
    decision_record_id: str
    kpi_id: str
    kpi_name: str
    selected_candidate_id: Optional[str]
    selected_candidate_name: Optional[str]
    stakeholder_decision: str
    decision_rationale: str = ""
    modified_lower_red_boundary: Optional[float] = None
    modified_lower_amber_boundary: Optional[float] = None
    modified_green_lower_boundary: Optional[float] = None
    modified_green_upper_boundary: Optional[float] = None
    modified_upper_amber_boundary: Optional[float] = None
    modified_upper_red_boundary: Optional[float] = None
    boundary_inclusivity_rule: str = "Lower boundary inclusive, upper exclusive"
    conditions_of_approval: str = ""
    required_review_date: str = ""
    approver_role: str = ""
    approver_name: str = ""
    approval_date: str = ""
    effective_date: str = ""
    expiry_date: str = ""
    approval_status: str = ApprovalStatus.PENDING_STAKEHOLDER_REVIEW
    requested_promotion_version: str = ""
    supporting_evidence_reference: str = ""
    entered_by: str = ""
    entered_at: str = ""
    validation_status: str = ValidationStatus.PENDING
    validation_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_record_id": self.decision_record_id,
            "kpi_id": self.kpi_id,
            "kpi_name": self.kpi_name,
            "selected_candidate_id": self.selected_candidate_id,
            "selected_candidate_name": self.selected_candidate_name,
            "stakeholder_decision": self.stakeholder_decision,
            "decision_rationale": self.decision_rationale,
            "modified_lower_red_boundary": self.modified_lower_red_boundary,
            "modified_lower_amber_boundary": self.modified_lower_amber_boundary,
            "modified_green_lower_boundary": self.modified_green_lower_boundary,
            "modified_green_upper_boundary": self.modified_green_upper_boundary,
            "modified_upper_amber_boundary": self.modified_upper_amber_boundary,
            "modified_upper_red_boundary": self.modified_upper_red_boundary,
            "boundary_inclusivity_rule": self.boundary_inclusivity_rule,
            "conditions_of_approval": self.conditions_of_approval,
            "required_review_date": self.required_review_date,
            "approver_role": self.approver_role,
            "approver_name": self.approver_name,
            "approval_date": self.approval_date,
            "effective_date": self.effective_date,
            "expiry_date": self.expiry_date,
            "approval_status": self.approval_status,
            "requested_promotion_version": self.requested_promotion_version,
            "supporting_evidence_reference": self.supporting_evidence_reference,
            "entered_by": self.entered_by,
            "entered_at": self.entered_at,
            "validation_status": self.validation_status,
            "validation_message": self.validation_message,
        }


@dataclass
class ThresholdApprovalRecord:
    approval_record_id: str
    kpi_id: str
    kpi_name: str
    threshold_candidate_id: Optional[str]
    candidate_name: Optional[str]
    stakeholder_decision: str
    approval_status: str
    threshold_version: str
    previous_version: str
    effective_date: str
    approval_date: str
    approved_by: str
    approver_role: str
    decision_record_id: str
    source_candidate_id: Optional[str]
    threshold_is_provisional: bool
    conditions_of_approval: str
    required_review_date: str
    promotion_run_id: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "approval_record_id": self.approval_record_id,
            "kpi_id": self.kpi_id,
            "kpi_name": self.kpi_name,
            "threshold_candidate_id": self.threshold_candidate_id,
            "candidate_name": self.candidate_name,
            "stakeholder_decision": self.stakeholder_decision,
            "approval_status": self.approval_status,
            "threshold_version": self.threshold_version,
            "previous_version": self.previous_version,
            "effective_date": self.effective_date,
            "approval_date": self.approval_date,
            "approved_by": self.approved_by,
            "approver_role": self.approver_role,
            "decision_record_id": self.decision_record_id,
            "source_candidate_id": self.source_candidate_id,
            "threshold_is_provisional": self.threshold_is_provisional,
            "conditions_of_approval": self.conditions_of_approval,
            "required_review_date": self.required_review_date,
            "promotion_run_id": self.promotion_run_id,
            "created_at": self.created_at,
        }


@dataclass
class ThresholdModificationRecord:
    modification_record_id: str
    decision_record_id: str
    kpi_id: str
    original_candidate_id: str
    modified_lower_red_boundary: Optional[float]
    modified_lower_amber_boundary: Optional[float]
    modified_green_lower_boundary: Optional[float]
    modified_green_upper_boundary: Optional[float]
    modified_upper_amber_boundary: Optional[float]
    modified_upper_red_boundary: Optional[float]
    modification_rationale: str
    validation_status: str
    validation_message: str
    promotion_run_id: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "modification_record_id": self.modification_record_id,
            "decision_record_id": self.decision_record_id,
            "kpi_id": self.kpi_id,
            "original_candidate_id": self.original_candidate_id,
            "modified_lower_red_boundary": self.modified_lower_red_boundary,
            "modified_lower_amber_boundary": self.modified_lower_amber_boundary,
            "modified_green_lower_boundary": self.modified_green_lower_boundary,
            "modified_green_upper_boundary": self.modified_green_upper_boundary,
            "modified_upper_amber_boundary": self.modified_upper_amber_boundary,
            "modified_upper_red_boundary": self.modified_upper_red_boundary,
            "modification_rationale": self.modification_rationale,
            "validation_status": self.validation_status,
            "validation_message": self.validation_message,
            "promotion_run_id": self.promotion_run_id,
            "created_at": self.created_at,
        }


@dataclass
class PromotionReadinessResult:
    readiness_record_id: str
    kpi_id: str
    kpi_name: str
    stakeholder_decision: str
    promotion_readiness: str
    readiness_reason: str
    missing_fields: str
    decision_valid: bool
    candidate_valid: bool
    boundary_valid: bool
    approver_valid: bool
    date_valid: bool
    conditional_requirements_met: bool
    promotion_run_id: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "readiness_record_id": self.readiness_record_id,
            "kpi_id": self.kpi_id,
            "kpi_name": self.kpi_name,
            "stakeholder_decision": self.stakeholder_decision,
            "promotion_readiness": self.promotion_readiness,
            "readiness_reason": self.readiness_reason,
            "missing_fields": self.missing_fields,
            "decision_valid": self.decision_valid,
            "candidate_valid": self.candidate_valid,
            "boundary_valid": self.boundary_valid,
            "approver_valid": self.approver_valid,
            "date_valid": self.date_valid,
            "conditional_requirements_met": self.conditional_requirements_met,
            "promotion_run_id": self.promotion_run_id,
            "created_at": self.created_at,
        }


@dataclass
class ThresholdPromotionRecord:
    promotion_record_id: str
    kpi_id: str
    kpi_name: str
    threshold_version: str
    previous_version: str
    promotion_status: str
    active_config_modified: bool
    backup_path: str
    rollback_path: str
    promotion_run_id: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "promotion_record_id": self.promotion_record_id,
            "kpi_id": self.kpi_id,
            "kpi_name": self.kpi_name,
            "threshold_version": self.threshold_version,
            "previous_version": self.previous_version,
            "promotion_status": self.promotion_status,
            "active_config_modified": self.active_config_modified,
            "backup_path": self.backup_path,
            "rollback_path": self.rollback_path,
            "promotion_run_id": self.promotion_run_id,
            "created_at": self.created_at,
        }


@dataclass
class ThresholdVersionRecord:
    version_record_id: str
    kpi_id: str
    kpi_name: str
    threshold_version: str
    previous_version: str
    version_type: str
    effective_date: str
    approval_status: str
    threshold_is_provisional: bool
    approved_by: str
    approval_date: str
    decision_record_id: str
    source_candidate_id: str
    promotion_run_id: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version_record_id": self.version_record_id,
            "kpi_id": self.kpi_id,
            "kpi_name": self.kpi_name,
            "threshold_version": self.threshold_version,
            "previous_version": self.previous_version,
            "version_type": self.version_type,
            "effective_date": self.effective_date,
            "approval_status": self.approval_status,
            "threshold_is_provisional": self.threshold_is_provisional,
            "approved_by": self.approved_by,
            "approval_date": self.approval_date,
            "decision_record_id": self.decision_record_id,
            "source_candidate_id": self.source_candidate_id,
            "promotion_run_id": self.promotion_run_id,
            "created_at": self.created_at,
        }


@dataclass
class ApprovalEvidenceRecord:
    evidence_record_id: str
    kpi_id: str
    evidence_category: str
    evidence_description: str
    supporting_value: Optional[str]
    source_dataset: str
    promotion_run_id: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_record_id": self.evidence_record_id,
            "kpi_id": self.kpi_id,
            "evidence_category": self.evidence_category,
            "evidence_description": self.evidence_description,
            "supporting_value": self.supporting_value,
            "source_dataset": self.source_dataset,
            "promotion_run_id": self.promotion_run_id,
            "created_at": self.created_at,
        }


@dataclass
class ApprovalIssueRecord:
    issue_record_id: str
    kpi_id: Optional[str]
    issue_category: str
    issue_severity: str
    issue_description: str
    recommended_action: str
    blocking: bool
    promotion_run_id: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_record_id": self.issue_record_id,
            "kpi_id": self.kpi_id,
            "issue_category": self.issue_category,
            "issue_severity": self.issue_severity,
            "issue_description": self.issue_description,
            "recommended_action": self.recommended_action,
            "blocking": self.blocking,
            "promotion_run_id": self.promotion_run_id,
            "created_at": self.created_at,
        }


@dataclass
class ApprovalAuditRecord:
    audit_record_id: str
    audit_phase: str
    audit_action: str
    entity_type: str
    entity_id: str
    audit_result: str
    details: Optional[str]
    promotion_run_id: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "audit_record_id": self.audit_record_id,
            "audit_phase": self.audit_phase,
            "audit_action": self.audit_action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "audit_result": self.audit_result,
            "details": self.details,
            "promotion_run_id": self.promotion_run_id,
            "created_at": self.created_at,
        }


@dataclass
class ThresholdPromotionManifest:
    promotion_run_id: str
    step_name: str
    step_version: str
    executed_at: str
    project_root: str
    mode: str
    prerequisites_valid: bool
    prerequisite_issues: List[str]
    kpis_reviewed: List[str]
    candidates_presented: int
    decisions_received: int
    complete_decisions: int
    incomplete_decisions: int
    approved_kpis: int
    conditionally_approved_kpis: int
    rejected_kpis: int
    deferred_kpis: int
    more_evidence_kpis: int
    modified_boundary_decisions: int
    decision_validation_passed: bool
    bed_occupancy_approval_result: str
    complaint_denominator_condition: str
    promotion_readiness_by_kpi: Dict[str, str]
    overall_promotion_readiness: str
    staged_threshold_version: str
    active_threshold_version_before: str
    active_threshold_version_after: str
    active_config_modified: bool
    backup_created: bool
    backup_path: str
    rollback_path: str
    sandbox_classification_count: int
    green_count: int
    amber_count: int
    red_count: int
    not_assessed_count: int
    unavailable_count: int
    formula_verification_passed: bool
    boundary_case_validation_passed: bool
    schema_validation_passed: bool
    key_validation_passed: bool
    phase_1_immutability_passed: bool
    phase_2a_immutability_passed: bool
    step_2b1_immutability_passed: bool
    step_2b1a_immutability_passed: bool
    active_config_immutability_or_promotion_result: str
    warnings_count: int
    blocking_issues_count: int
    unresolved_decisions: List[str]
    final_status: str
    step_2b2_readiness: str
    recommended_next_action: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "promotion_run_id": self.promotion_run_id,
            "step_name": self.step_name,
            "step_version": self.step_version,
            "executed_at": self.executed_at,
            "project_root": self.project_root,
            "mode": self.mode,
            "prerequisites_valid": self.prerequisites_valid,
            "prerequisite_issues": self.prerequisite_issues,
            "kpis_reviewed": self.kpis_reviewed,
            "candidates_presented": self.candidates_presented,
            "decisions_received": self.decisions_received,
            "complete_decisions": self.complete_decisions,
            "incomplete_decisions": self.incomplete_decisions,
            "approved_kpis": self.approved_kpis,
            "conditionally_approved_kpis": self.conditionally_approved_kpis,
            "rejected_kpis": self.rejected_kpis,
            "deferred_kpis": self.deferred_kpis,
            "more_evidence_kpis": self.more_evidence_kpis,
            "modified_boundary_decisions": self.modified_boundary_decisions,
            "decision_validation_passed": self.decision_validation_passed,
            "bed_occupancy_approval_result": self.bed_occupancy_approval_result,
            "complaint_denominator_condition": self.complaint_denominator_condition,
            "promotion_readiness_by_kpi": self.promotion_readiness_by_kpi,
            "overall_promotion_readiness": self.overall_promotion_readiness,
            "staged_threshold_version": self.staged_threshold_version,
            "active_threshold_version_before": self.active_threshold_version_before,
            "active_threshold_version_after": self.active_threshold_version_after,
            "active_config_modified": self.active_config_modified,
            "backup_created": self.backup_created,
            "backup_path": self.backup_path,
            "rollback_path": self.rollback_path,
            "sandbox_classification_count": self.sandbox_classification_count,
            "green_count": self.green_count,
            "amber_count": self.amber_count,
            "red_count": self.red_count,
            "not_assessed_count": self.not_assessed_count,
            "unavailable_count": self.unavailable_count,
            "formula_verification_passed": self.formula_verification_passed,
            "boundary_case_validation_passed": self.boundary_case_validation_passed,
            "schema_validation_passed": self.schema_validation_passed,
            "key_validation_passed": self.key_validation_passed,
            "phase_1_immutability_passed": self.phase_1_immutability_passed,
            "phase_2a_immutability_passed": self.phase_2a_immutability_passed,
            "step_2b1_immutability_passed": self.step_2b1_immutability_passed,
            "step_2b1a_immutability_passed": self.step_2b1a_immutability_passed,
            "active_config_immutability_or_promotion_result": self.active_config_immutability_or_promotion_result,
            "warnings_count": self.warnings_count,
            "blocking_issues_count": self.blocking_issues_count,
            "unresolved_decisions": self.unresolved_decisions,
            "final_status": self.final_status,
            "step_2b2_readiness": self.step_2b2_readiness,
            "recommended_next_action": self.recommended_next_action,
        }
