"""
Sentinel360 Healthcare — Processing Models

Typed dataclasses for the processing layer.
Defines structured models for processing runs, dataset results, issues,
lineage records, and exclusion records.

Step: 2D-1
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ProcessingRun:
    """Represents a single processing execution."""

    processing_run_id: str
    validation_run_id: str
    source_type: str
    input_directory: str
    output_directory: str
    processing_started_datetime: datetime = field(default_factory=datetime.now)
    processing_completed_datetime: Optional[datetime] = None
    processing_engine_version: str = "1.0.0"
    configuration_version: str = ""
    transformation_version: str = "1.0.0"
    source_dataset_count: int = 0
    processed_dataset_count: int = 0
    source_record_count: int = 0
    processed_record_count: int = 0
    excluded_record_count: int = 0
    warning_count: int = 0
    error_count: int = 0
    run_status: str = "Not Started"
    processing_allowed_flag: bool = False
    created_by: str = "system"
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "processing_run_id": self.processing_run_id,
            "validation_run_id": self.validation_run_id,
            "source_type": self.source_type,
            "input_directory": self.input_directory,
            "output_directory": self.output_directory,
            "processing_started_datetime": self.processing_started_datetime.isoformat(),
            "processing_completed_datetime": self.processing_completed_datetime.isoformat() if self.processing_completed_datetime else None,
            "processing_engine_version": self.processing_engine_version,
            "configuration_version": self.configuration_version,
            "transformation_version": self.transformation_version,
            "source_dataset_count": self.source_dataset_count,
            "processed_dataset_count": self.processed_dataset_count,
            "source_record_count": self.source_record_count,
            "processed_record_count": self.processed_record_count,
            "excluded_record_count": self.excluded_record_count,
            "warning_count": self.warning_count,
            "error_count": self.error_count,
            "run_status": self.run_status,
            "processing_allowed_flag": self.processing_allowed_flag,
            "created_by": self.created_by,
            "notes": self.notes,
        }


@dataclass
class ProcessingDatasetResult:
    """Result of processing a single source dataset into a processed dataset."""

    processing_run_id: str
    validation_run_id: str
    source_dataset_name: str
    processed_dataset_name: str
    source_row_count: int = 0
    processed_row_count: int = 0
    excluded_row_count: int = 0
    transformed_field_count: int = 0
    warning_count: int = 0
    error_count: int = 0
    dataset_status: str = "Not Processed"
    output_file_name: str = ""
    transformation_version: str = "1.0.0"
    processed_datetime: Optional[datetime] = None
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "processing_run_id": self.processing_run_id,
            "validation_run_id": self.validation_run_id,
            "source_dataset_name": self.source_dataset_name,
            "processed_dataset_name": self.processed_dataset_name,
            "source_row_count": self.source_row_count,
            "processed_row_count": self.processed_row_count,
            "excluded_row_count": self.excluded_row_count,
            "transformed_field_count": self.transformed_field_count,
            "warning_count": self.warning_count,
            "error_count": self.error_count,
            "dataset_status": self.dataset_status,
            "output_file_name": self.output_file_name,
            "transformation_version": self.transformation_version,
            "processed_datetime": self.processed_datetime.isoformat() if self.processed_datetime else None,
            "notes": self.notes,
        }


@dataclass
class ProcessingIssue:
    """An issue observed during processing of a dataset."""

    processing_run_id: str
    issue_id: str
    source_dataset_name: str = ""
    processed_dataset_name: str = ""
    source_primary_key: str = ""
    source_row_number: int = 0
    field_name: str = ""
    issue_type: str = ""
    severity: str = "Information"
    issue_description: str = ""
    source_value: str = ""
    processed_value: str = ""
    resolution_action: str = ""
    exclusion_flag: bool = False
    blocks_processing: bool = False
    created_datetime: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "processing_run_id": self.processing_run_id,
            "issue_id": self.issue_id,
            "source_dataset_name": self.source_dataset_name,
            "processed_dataset_name": self.processed_dataset_name,
            "source_primary_key": self.source_primary_key,
            "source_row_number": self.source_row_number,
            "field_name": self.field_name,
            "issue_type": self.issue_type,
            "severity": self.severity,
            "issue_description": self.issue_description,
            "source_value": self.source_value,
            "processed_value": self.processed_value,
            "resolution_action": self.resolution_action,
            "exclusion_flag": self.exclusion_flag,
            "blocks_processing": self.blocks_processing,
            "created_datetime": self.created_datetime.isoformat(),
        }


@dataclass
class ProcessingLineageRecord:
    """Traceability link between a source record and a processed record."""

    processing_run_id: str
    lineage_id: str
    validation_run_id: str = ""
    source_dataset_name: str = ""
    source_file_name: str = ""
    source_primary_key_field: str = ""
    source_primary_key_value: str = ""
    source_row_number: int = 0
    processed_dataset_name: str = ""
    processed_primary_key_field: str = ""
    processed_primary_key_value: str = ""
    transformation_rule_id: str = ""
    transformation_description: str = ""
    source_fields_used: str = ""
    processed_fields_created: str = ""
    exclusion_flag: bool = False
    exclusion_reason_code: str = ""
    transformation_version: str = "1.0.0"
    configuration_version: str = ""
    processed_datetime: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "processing_run_id": self.processing_run_id,
            "lineage_id": self.lineage_id,
            "validation_run_id": self.validation_run_id,
            "source_dataset_name": self.source_dataset_name,
            "source_file_name": self.source_file_name,
            "source_primary_key_field": self.source_primary_key_field,
            "source_primary_key_value": self.source_primary_key_value,
            "source_row_number": self.source_row_number,
            "processed_dataset_name": self.processed_dataset_name,
            "processed_primary_key_field": self.processed_primary_key_field,
            "processed_primary_key_value": self.processed_primary_key_value,
            "transformation_rule_id": self.transformation_rule_id,
            "transformation_description": self.transformation_description,
            "source_fields_used": self.source_fields_used,
            "processed_fields_created": self.processed_fields_created,
            "exclusion_flag": self.exclusion_flag,
            "exclusion_reason_code": self.exclusion_reason_code,
            "transformation_version": self.transformation_version,
            "configuration_version": self.configuration_version,
            "processed_datetime": self.processed_datetime.isoformat(),
        }


@dataclass
class ProcessingExclusionRecord:
    """Record of a source record excluded during processing."""

    processing_run_id: str
    exclusion_id: str
    source_dataset_name: str = ""
    source_primary_key_field: str = ""
    source_primary_key_value: str = ""
    source_row_number: int = 0
    exclusion_reason_code: str = ""
    exclusion_reason_description: str = ""
    validation_issue_id: str = ""
    manual_override_id: str = ""
    exclusion_stage: str = ""
    excluded_by_rule: str = ""
    reversible_flag: bool = False
    created_datetime: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "processing_run_id": self.processing_run_id,
            "exclusion_id": self.exclusion_id,
            "source_dataset_name": self.source_dataset_name,
            "source_primary_key_field": self.source_primary_key_field,
            "source_primary_key_value": self.source_primary_key_value,
            "source_row_number": self.source_row_number,
            "exclusion_reason_code": self.exclusion_reason_code,
            "exclusion_reason_description": self.exclusion_reason_description,
            "validation_issue_id": self.validation_issue_id,
            "manual_override_id": self.manual_override_id,
            "exclusion_stage": self.exclusion_stage,
            "excluded_by_rule": self.excluded_by_rule,
            "reversible_flag": self.reversible_flag,
            "created_datetime": self.created_datetime.isoformat(),
        }
