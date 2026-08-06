"""
Sentinel360 Healthcare — Validation Models

Typed dataclasses for the data-validation engine audit trail.
No analytical outputs or KPI calculations.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ValidationRun:
    """Top-level record for a single validation execution."""

    validation_run_id: str
    validation_started_datetime: datetime
    validation_completed_datetime: Optional[datetime] = None
    input_directory: str = ""
    source_type: str = ""
    dataset_count_expected: int = 0
    dataset_count_found: int = 0
    validation_engine_version: str = "1.0.0"
    configuration_version: str = "1.0.0"
    run_status: str = "Pending"
    blocking_issue_count: int = 0
    critical_issue_count: int = 0
    error_issue_count: int = 0
    warning_issue_count: int = 0
    information_issue_count: int = 0
    manual_override_count: int = 0
    created_by: str = "system"
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "validation_run_id": self.validation_run_id,
            "validation_started_datetime": self.validation_started_datetime.isoformat() if self.validation_started_datetime else None,
            "validation_completed_datetime": self.validation_completed_datetime.isoformat() if self.validation_completed_datetime else None,
            "input_directory": self.input_directory,
            "source_type": self.source_type,
            "dataset_count_expected": self.dataset_count_expected,
            "dataset_count_found": self.dataset_count_found,
            "validation_engine_version": self.validation_engine_version,
            "configuration_version": self.configuration_version,
            "run_status": self.run_status,
            "blocking_issue_count": self.blocking_issue_count,
            "critical_issue_count": self.critical_issue_count,
            "error_issue_count": self.error_issue_count,
            "warning_issue_count": self.warning_issue_count,
            "information_issue_count": self.information_issue_count,
            "manual_override_count": self.manual_override_count,
            "created_by": self.created_by,
            "notes": self.notes,
        }


@dataclass
class DatasetValidationResult:
    """Per-dataset summary produced by the engine."""

    validation_run_id: str
    dataset_name: str
    file_name: str = ""
    file_found_flag: bool = False
    file_readable_flag: bool = False
    row_count: int = 0
    column_count: int = 0
    expected_column_count: int = 0
    missing_required_column_count: int = 0
    unexpected_column_count: int = 0
    missing_required_value_count: int = 0
    duplicate_primary_key_count: int = 0
    invalid_data_type_count: int = 0
    invalid_date_count: int = 0
    invalid_datetime_count: int = 0
    invalid_numeric_count: int = 0
    invalid_domain_value_count: int = 0
    orphan_reference_count: int = 0
    blocking_issue_count: int = 0
    warning_issue_count: int = 0
    dataset_status: str = "Not Available"
    processing_allowed_flag: bool = False
    validation_started_datetime: Optional[datetime] = None
    validation_completed_datetime: Optional[datetime] = None
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "validation_run_id": self.validation_run_id,
            "dataset_name": self.dataset_name,
            "file_name": self.file_name,
            "file_found_flag": self.file_found_flag,
            "file_readable_flag": self.file_readable_flag,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "expected_column_count": self.expected_column_count,
            "missing_required_column_count": self.missing_required_column_count,
            "unexpected_column_count": self.unexpected_column_count,
            "missing_required_value_count": self.missing_required_value_count,
            "duplicate_primary_key_count": self.duplicate_primary_key_count,
            "invalid_data_type_count": self.invalid_data_type_count,
            "invalid_date_count": self.invalid_date_count,
            "invalid_datetime_count": self.invalid_datetime_count,
            "invalid_numeric_count": self.invalid_numeric_count,
            "invalid_domain_value_count": self.invalid_domain_value_count,
            "orphan_reference_count": self.orphan_reference_count,
            "blocking_issue_count": self.blocking_issue_count,
            "warning_issue_count": self.warning_issue_count,
            "dataset_status": self.dataset_status,
            "processing_allowed_flag": self.processing_allowed_flag,
            "validation_started_datetime": self.validation_started_datetime.isoformat() if self.validation_started_datetime else None,
            "validation_completed_datetime": self.validation_completed_datetime.isoformat() if self.validation_completed_datetime else None,
            "notes": self.notes,
        }


@dataclass
class ValidationIssue:
    """A single validation-rule failure or observation."""

    validation_run_id: str
    issue_id: str
    test_id: str
    dataset_name: str
    field_name: str = ""
    issue_type: str = ""
    severity: str = "Information"
    issue_outcome: str = "Observed"
    issue_description: str = ""
    failure_condition: str = ""
    observed_value: str = ""
    expected_rule: str = ""
    affected_record_count: int = 0
    blocks_processing: bool = False
    manual_override_allowed: bool = False
    manual_override_required: bool = False
    audit_required: bool = True
    issue_status: str = "Open"
    created_datetime: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "validation_run_id": self.validation_run_id,
            "issue_id": self.issue_id,
            "test_id": self.test_id,
            "dataset_name": self.dataset_name,
            "field_name": self.field_name,
            "issue_type": self.issue_type,
            "severity": self.severity,
            "issue_outcome": self.issue_outcome,
            "issue_description": self.issue_description,
            "failure_condition": self.failure_condition,
            "observed_value": self.observed_value,
            "expected_rule": self.expected_rule,
            "affected_record_count": self.affected_record_count,
            "blocks_processing": self.blocks_processing,
            "manual_override_allowed": self.manual_override_allowed,
            "manual_override_required": self.manual_override_required,
            "audit_required": self.audit_required,
            "issue_status": self.issue_status,
            "created_datetime": self.created_datetime.isoformat(),
        }


@dataclass
class RecordValidationIssue:
    """Record-level example of a validation issue."""

    validation_run_id: str
    record_issue_id: str
    issue_id: str
    dataset_name: str
    primary_key_field: str = ""
    primary_key_value: str = ""
    row_number: int = 0
    field_name: str = ""
    observed_value: str = ""
    issue_description: str = ""
    severity: str = "Information"
    blocks_processing: bool = False
    resolution_status: str = "Open"
    created_datetime: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "validation_run_id": self.validation_run_id,
            "record_issue_id": self.record_issue_id,
            "issue_id": self.issue_id,
            "dataset_name": self.dataset_name,
            "primary_key_field": self.primary_key_field,
            "primary_key_value": self.primary_key_value,
            "row_number": self.row_number,
            "field_name": self.field_name,
            "observed_value": self.observed_value,
            "issue_description": self.issue_description,
            "severity": self.severity,
            "blocks_processing": self.blocks_processing,
            "resolution_status": self.resolution_status,
            "created_datetime": self.created_datetime.isoformat(),
        }


@dataclass
class RelationshipValidationResult:
    """Result of a parent-child referential-integrity check."""

    validation_run_id: str
    relationship_id: str
    child_dataset: str
    child_field: str
    parent_dataset: str
    parent_field: str
    populated_child_value_count: int = 0
    valid_reference_count: int = 0
    null_reference_count: int = 0
    orphan_reference_count: int = 0
    relationship_status: str = "Not Checked"
    blocks_processing: bool = False
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "validation_run_id": self.validation_run_id,
            "relationship_id": self.relationship_id,
            "child_dataset": self.child_dataset,
            "child_field": self.child_field,
            "parent_dataset": self.parent_dataset,
            "parent_field": self.parent_field,
            "populated_child_value_count": self.populated_child_value_count,
            "valid_reference_count": self.valid_reference_count,
            "null_reference_count": self.null_reference_count,
            "orphan_reference_count": self.orphan_reference_count,
            "relationship_status": self.relationship_status,
            "blocks_processing": self.blocks_processing,
            "notes": self.notes,
        }


@dataclass
class ManualOverrideRecord:
    """Governed manual override for a validation issue."""

    override_id: str
    validation_run_id: str
    issue_id: str
    dataset_name: str
    override_status: str = "Requested"
    override_reason: str = ""
    requested_by: str = ""
    approved_by: str = ""
    approval_role: str = ""
    request_datetime: Optional[datetime] = None
    approval_datetime: Optional[datetime] = None
    expiry_datetime: Optional[datetime] = None
    affected_record_count: int = 0
    original_blocks_processing: bool = False
    processing_allowed_after_override: bool = False
    audit_reference: str = ""
    comments: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "override_id": self.override_id,
            "validation_run_id": self.validation_run_id,
            "issue_id": self.issue_id,
            "dataset_name": self.dataset_name,
            "override_status": self.override_status,
            "override_reason": self.override_reason,
            "requested_by": self.requested_by,
            "approved_by": self.approved_by,
            "approval_role": self.approval_role,
            "request_datetime": self.request_datetime.isoformat() if self.request_datetime else None,
            "approval_datetime": self.approval_datetime.isoformat() if self.approval_datetime else None,
            "expiry_datetime": self.expiry_datetime.isoformat() if self.expiry_datetime else None,
            "affected_record_count": self.affected_record_count,
            "original_blocks_processing": self.original_blocks_processing,
            "processing_allowed_after_override": self.processing_allowed_after_override,
            "audit_reference": self.audit_reference,
            "comments": self.comments,
        }


@dataclass
class ValidationAuditEvent:
    """Immutable audit event for the validation run."""

    audit_event_id: str
    validation_run_id: str
    event_datetime: datetime
    event_type: str
    dataset_name: str = ""
    issue_id: str = ""
    user_or_process: str = "system"
    previous_status: str = ""
    new_status: str = ""
    event_description: str = ""
    source_reference: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "audit_event_id": self.audit_event_id,
            "validation_run_id": self.validation_run_id,
            "event_datetime": self.event_datetime.isoformat(),
            "event_type": self.event_type,
            "dataset_name": self.dataset_name,
            "issue_id": self.issue_id,
            "user_or_process": self.user_or_process,
            "previous_status": self.previous_status,
            "new_status": self.new_status,
            "event_description": self.event_description,
            "source_reference": self.source_reference,
        }
