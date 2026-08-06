"""
Sentinel360 Healthcare — Validation Configuration Loader

Loads schema, relationship and rule registries from approved documentation.
All field names must match the actual exported synthetic demo data.
Discrepancies with the data dictionary are reported as Pending Review.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Approved dataset definitions aligned to ACTUAL demo-export column names
# ---------------------------------------------------------------------------

DATASET_NAMES = [
    "hospital_master",
    "department_master",
    "staff_role_master",
    "staff_master",
    "staff_roster",
    "staff_attendance",
    "staffing_requirement",
    "patient_encounters",
    "patient_queue_records",
    "bed_capacity_records",
    "patient_complaints",
    "patient_surveys",
    "service_schedule",
]

# Column definitions: (column_name, required_bool)
SCHEMA_REGISTRY: Dict[str, List[Tuple[str, bool]]] = {
    "hospital_master": [
        ("hospital_id", True),
        ("hospital_name", True),
        ("hospital_short_name", True),
        ("hospital_type", True),
        ("bed_licensed_total", True),
        ("region", True),
        ("country", True),
        ("status", True),
        ("effective_from", True),
        ("effective_to", True),
        ("source_system", True),
        ("record_version", True),
        ("record_created_datetime", True),
        ("record_updated_datetime", True),
    ],
    "department_master": [
        ("department_id", True),
        ("hospital_id", True),
        ("department_name", True),
        ("department_type", True),
        ("parent_department_id", False),
        ("bed_licensed", True),
        ("bed_staffed", True),
        ("bed_operational", True),
        ("is_active", True),
        ("effective_from", True),
        ("effective_to", True),
        ("source_system", True),
        ("record_version", True),
        ("record_created_datetime", True),
        ("record_updated_datetime", True),
    ],
    "staff_role_master": [
        ("role_id", True),
        ("role_name", True),
        ("staff_category", True),
        ("is_clinical", True),
        ("is_active", True),
        ("effective_from", True),
        ("effective_to", True),
        ("source_system", True),
        ("record_version", True),
        ("record_created_datetime", True),
        ("record_updated_datetime", True),
    ],
    "staff_master": [
        ("staff_id", True),
        ("hospital_id", True),
        ("department_id", True),
        ("role_id", True),
        ("staff_name", False),
        ("email", False),
        ("phone_number", False),
        ("ic_number", False),
        ("address", False),
        ("employment_type", True),
        ("fte_value", True),
        ("is_active", True),
        ("employment_start_date", True),
        ("employment_end_date", False),
        ("source_system", True),
        ("record_version", True),
        ("record_created_datetime", True),
        ("record_updated_datetime", True),
    ],
    "staff_roster": [
        ("roster_id", True),
        ("staff_id", True),
        ("hospital_id", True),
        ("department_id", True),
        ("role_id", True),
        ("roster_date", True),
        ("shift_code", True),
        ("planned_start_datetime", True),
        ("planned_end_datetime", True),
        ("planned_hours", True),
        ("status", True),
        ("version", True),
        ("source_system", True),
        ("record_created_datetime", True),
        ("record_updated_datetime", True),
    ],
    "staff_attendance": [
        ("attendance_id", True),
        ("staff_id", True),
        ("hospital_id", True),
        ("department_id", True),
        ("role_id", True),
        ("roster_id", False),
        ("attendance_date", True),
        ("shift_code", True),
        ("status", True),
        ("actual_start_datetime", False),
        ("actual_end_datetime", False),
        ("actual_hours", False),
        ("replacement_staff_id", False),
        ("notes", False),
        ("source_system", True),
        ("created_at", True),
    ],
    "staffing_requirement": [
        ("requirement_id", True),
        ("hospital_id", True),
        ("department_id", True),
        ("role_id", True),
        ("requirement_date", True),
        ("shift_code", True),
        ("required_staff_count", True),
        ("required_hours", True),
        ("source_system", True),
        ("created_at", True),
    ],
    "patient_encounters": [
        ("encounter_id", True),
        ("hospital_id", True),
        ("department_id", True),
        ("patient_id", True),
        ("encounter_date", True),
        ("encounter_type", True),
        ("arrival_datetime", True),
        ("service_start_datetime", False),
        ("service_end_datetime", False),
        ("status", True),
        ("cancellation_reason", False),
        ("triage_category", False),
        ("source_system", True),
        ("record_created_datetime", True),
    ],
    "patient_queue_records": [
        ("queue_id", True),
        ("hospital_id", True),
        ("department_id", True),
        ("queue_date", True),
        ("queue_type", True),
        ("period_start", True),
        ("period_end", True),
        ("arrivals_count", True),
        ("served_count", True),
        ("waiting_count", True),
        ("avg_wait_minutes", True),
        ("median_wait_minutes", True),
        ("max_wait_minutes", True),
        ("source_system", True),
        ("created_at", True),
    ],
    "bed_capacity_records": [
        ("record_id", True),
        ("hospital_id", True),
        ("department_id", True),
        ("record_date", True),
        ("bed_licensed", True),
        ("bed_staffed", True),
        ("bed_operational", True),
        ("bed_occupied", True),
        ("bed_unavailable", True),
        ("bed_reserved", True),
        ("occupancy_rate", True),
        ("exception_flag", True),
        ("exception_reason", False),
        ("source_system", True),
        ("created_at", True),
    ],
    "patient_complaints": [
        ("complaint_id", True),
        ("hospital_id", True),
        ("department_id", False),
        ("encounter_id", False),
        ("complaint_received_date", True),
        ("complaint_channel", True),
        ("complaint_category", True),
        ("severity", True),
        ("description", False),
        ("status", True),
        ("resolution_date", False),
        ("outcome_category", False),
        ("duplicate_flag", True),
        ("duplicate_of_complaint_id", False),
        ("source_system", True),
        ("created_at", True),
    ],
    "patient_surveys": [
        ("survey_id", True),
        ("hospital_id", True),
        ("department_id", False),
        ("encounter_id", False),
        ("survey_date", True),
        ("survey_type", True),
        ("scale_id", True),
        ("score_value", False),
        ("response_weight", False),
        ("is_complete", True),
        ("source_system", True),
        ("created_at", True),
    ],
    "service_schedule": [
        ("schedule_id", True),
        ("hospital_id", True),
        ("department_id", True),
        ("service_date", True),
        ("planned_start_time", True),
        ("planned_end_time", True),
        ("planned_hours", True),
        ("planned_capacity", True),
        ("schedule_status", True),
        ("shift_code", True),
        ("source_system", True),
        ("created_at", True),
    ],
}

# Primary keys aligned to actual columns
PRIMARY_KEYS: Dict[str, str] = {
    "hospital_master": "hospital_id",
    "department_master": "department_id",
    "staff_role_master": "role_id",
    "staff_master": "staff_id",
    "staff_roster": "roster_id",
    "staff_attendance": "attendance_id",
    "staffing_requirement": "requirement_id",
    "patient_encounters": "encounter_id",
    "patient_queue_records": "queue_id",
    "bed_capacity_records": "record_id",
    "patient_complaints": "complaint_id",
    "patient_surveys": "survey_id",
    "service_schedule": "schedule_id",
}

# Field-type registries
DATE_FIELDS: Dict[str, List[str]] = {
    "hospital_master": ["effective_from", "effective_to"],
    "department_master": ["effective_from", "effective_to"],
    "staff_role_master": ["effective_from", "effective_to"],
    "staff_master": ["employment_start_date", "employment_end_date"],
    "staff_roster": ["roster_date"],
    "staff_attendance": ["attendance_date"],
    "staffing_requirement": ["requirement_date"],
    "patient_encounters": ["encounter_date"],
    "patient_queue_records": ["queue_date"],
    "bed_capacity_records": ["record_date"],
    "patient_complaints": ["complaint_received_date", "resolution_date"],
    "patient_surveys": ["survey_date"],
    "service_schedule": ["service_date"],
}

DATETIME_FIELDS: Dict[str, List[str]] = {
    "hospital_master": ["record_created_datetime", "record_updated_datetime"],
    "department_master": ["record_created_datetime", "record_updated_datetime"],
    "staff_role_master": ["record_created_datetime", "record_updated_datetime"],
    "staff_master": ["record_created_datetime", "record_updated_datetime"],
    "staff_roster": ["planned_start_datetime", "planned_end_datetime", "record_created_datetime", "record_updated_datetime"],
    "staff_attendance": ["actual_start_datetime", "actual_end_datetime", "created_at"],
    "staffing_requirement": ["created_at"],
    "patient_encounters": ["arrival_datetime", "service_start_datetime", "service_end_datetime", "record_created_datetime"],
    "patient_queue_records": ["period_start", "period_end", "created_at"],
    "bed_capacity_records": ["created_at"],
    "patient_complaints": ["created_at"],
    "patient_surveys": ["created_at"],
    "service_schedule": ["created_at"],
}

NUMERIC_FIELDS: Dict[str, List[str]] = {
    "hospital_master": ["bed_licensed_total", "record_version"],
    "department_master": ["bed_licensed", "bed_staffed", "bed_operational", "record_version"],
    "staff_master": ["fte_value", "record_version"],
    "staff_roster": ["planned_hours", "version"],
    "staff_attendance": ["actual_hours"],
    "staffing_requirement": ["required_staff_count", "required_hours"],
    "patient_queue_records": ["arrivals_count", "served_count", "waiting_count", "avg_wait_minutes", "median_wait_minutes", "max_wait_minutes"],
    "bed_capacity_records": ["bed_licensed", "bed_staffed", "bed_operational", "bed_occupied", "bed_unavailable", "bed_reserved", "occupancy_rate"],
    "patient_surveys": ["score_value", "response_weight"],
    "service_schedule": ["planned_hours", "planned_capacity"],
}

BOOLEAN_FIELDS: Dict[str, List[str]] = {
    "department_master": ["is_active"],
    "staff_role_master": ["is_clinical", "is_active"],
    "staff_master": ["is_active"],
    "patient_surveys": ["is_complete"],
    "bed_capacity_records": ["exception_flag"],
    "patient_complaints": ["duplicate_flag"],
}

CATEGORICAL_FIELDS: Dict[str, Dict[str, List[str]]] = {
    "hospital_master": {
        "hospital_type": ["General Hospital", "Specialist Hospital", "Community Hospital", "University Hospital"],
        "status": ["Active", "Inactive", "Suspended"],
    },
    "department_master": {
        "department_type": ["Clinical", "Support", "Administrative", "Diagnostic"],
    },
    "staff_role_master": {
        "staff_category": ["Doctor", "Nurse", "Allied Health", "Support", "Administrative", "Other"],
    },
    "staff_master": {
        "employment_type": ["Full-Time", "Part-Time", "Contract"],
    },
    "staff_roster": {
        "shift_code": ["MORNING", "EVENING", "NIGHT"],
        "status": ["Active", "Cancelled", "Draft"],
    },
    "staff_attendance": {
        "shift_code": ["MORNING", "EVENING", "NIGHT"],
        "status": ["Present", "Absent", "Late", "Partial", "Leave", "Training", "Reassigned", "Not Scheduled"],
    },
    "staffing_requirement": {
        "shift_code": ["MORNING", "EVENING", "NIGHT"],
    },
    "patient_encounters": {
        "encounter_type": ["Scheduled Visit", "Walk-In", "Emergency", "Follow-up", "Referral"],
        "status": ["Completed", "Cancelled", "Left Before Service", "In Progress"],
        "triage_category": ["Critical", "Urgent", "Semi-Urgent", "Non-Urgent"],
    },
    "patient_queue_records": {
        "queue_type": ["Registration", "Triage", "Consultation", "Pharmacy", "Radiology", "Billing"],
    },
    "bed_capacity_records": {},
    "patient_complaints": {
        "complaint_channel": ["Walk-In", "Phone", "Email", "Formal Letter", "Online Portal", "Social Media", "Third Party"],
        "complaint_category": ["Waiting Time", "Staff Behaviour", "Facilities", "Billing", "Clinical Care", "Communication", "Safety", "Other"],
        "severity": ["Low", "Medium", "High", "Critical"],
        "status": ["Received", "Under Review", "Investigating", "Resolved", "Closed", "Escalated"],
    },
    "patient_surveys": {
        "survey_type": ["Inpatient Satisfaction", "Outpatient Satisfaction", "Emergency Satisfaction"],
        "scale_id": ["SCALE-5PT", "SCALE-10PT", "SCALE-NPS"],
    },
    "service_schedule": {
        "schedule_status": ["Planned", "Active", "Reduced", "Cancelled", "Extended"],
        "shift_code": ["MORNING", "EVENING", "NIGHT"],
    },
}

# Foreign-key relationships: (child_dataset, child_field, parent_dataset, parent_field, mandatory_bool)
RELATIONSHIP_REGISTRY: List[Tuple[str, str, str, str, bool]] = [
    ("department_master", "hospital_id", "hospital_master", "hospital_id", True),
    ("staff_master", "hospital_id", "hospital_master", "hospital_id", True),
    ("staff_master", "department_id", "department_master", "department_id", True),
    ("staff_master", "role_id", "staff_role_master", "role_id", True),
    ("staff_roster", "staff_id", "staff_master", "staff_id", True),
    ("staff_roster", "hospital_id", "hospital_master", "hospital_id", True),
    ("staff_roster", "department_id", "department_master", "department_id", True),
    ("staff_roster", "role_id", "staff_role_master", "role_id", True),
    ("staff_attendance", "staff_id", "staff_master", "staff_id", True),
    ("staff_attendance", "hospital_id", "hospital_master", "hospital_id", True),
    ("staff_attendance", "department_id", "department_master", "department_id", True),
    ("staff_attendance", "role_id", "staff_role_master", "role_id", True),
    ("staff_attendance", "roster_id", "staff_roster", "roster_id", False),
    ("staff_attendance", "replacement_staff_id", "staff_master", "staff_id", False),
    ("staffing_requirement", "hospital_id", "hospital_master", "hospital_id", True),
    ("staffing_requirement", "department_id", "department_master", "department_id", True),
    ("staffing_requirement", "role_id", "staff_role_master", "role_id", True),
    ("patient_encounters", "hospital_id", "hospital_master", "hospital_id", True),
    ("patient_encounters", "department_id", "department_master", "department_id", True),
    ("patient_queue_records", "hospital_id", "hospital_master", "hospital_id", True),
    ("patient_queue_records", "department_id", "department_master", "department_id", True),
    ("bed_capacity_records", "hospital_id", "hospital_master", "hospital_id", True),
    ("bed_capacity_records", "department_id", "department_master", "department_id", True),
    ("patient_complaints", "hospital_id", "hospital_master", "hospital_id", True),
    ("patient_complaints", "department_id", "department_master", "department_id", False),
    ("patient_complaints", "encounter_id", "patient_encounters", "encounter_id", False),
    ("patient_surveys", "hospital_id", "hospital_master", "hospital_id", True),
    ("patient_surveys", "department_id", "department_master", "department_id", False),
    ("patient_surveys", "encounter_id", "patient_encounters", "encounter_id", False),
    ("service_schedule", "hospital_id", "hospital_master", "hospital_id", True),
    ("service_schedule", "department_id", "department_master", "department_id", True),
]

# Validation rule metadata: (test_id, dataset_name, field_name, issue_type, severity, blocks_processing, manual_override_allowed, description)
VALIDATION_RULE_REGISTRY: List[Dict[str, Any]] = []


def _build_rule_registry() -> List[Dict[str, Any]]:
    """Build the validation-rule registry programmatically."""
    rules: List[Dict[str, Any]] = []
    counter = 0

    def add_rule(dataset: str, field: str, issue_type: str, severity: str, blocks: bool, override: bool, description: str) -> None:
        nonlocal counter
        counter += 1
        rules.append({
            "test_id": f"RULE-{counter:04d}",
            "dataset_name": dataset,
            "field_name": field,
            "issue_type": issue_type,
            "severity": severity,
            "blocks_processing": blocks,
            "manual_override_allowed": override,
            "description": description,
        })

    # File-level rules
    for ds in DATASET_NAMES:
        add_rule(ds, "", "FILE_MISSING", "Critical", True, False, f"Required file {ds}.csv is missing.")
        add_rule(ds, "", "FILE_UNREADABLE", "Critical", True, False, f"File {ds}.csv is not readable.")
        add_rule(ds, "", "FILE_EMPTY", "Error", True, False, f"File {ds}.csv is empty.")

    # Schema rules
    for ds, cols in SCHEMA_REGISTRY.items():
        for col, required in cols:
            if required:
                add_rule(ds, col, "COLUMN_MISSING", "Critical", True, False, f"Required column {col} is missing.")
            else:
                add_rule(ds, col, "COLUMN_MISSING_OPTIONAL", "Warning", False, True, f"Optional column {col} is missing.")
        add_rule(ds, "", "UNEXPECTED_COLUMN", "Warning", False, True, "Unexpected column detected.")
        add_rule(ds, PRIMARY_KEYS[ds], "PRIMARY_KEY_MISSING", "Critical", True, False, "Primary key value is null or blank.")
        add_rule(ds, PRIMARY_KEYS[ds], "PRIMARY_KEY_DUPLICATE", "Critical", True, False, "Primary key value is duplicated.")

    # Data-type rules
    for ds, fields in DATE_FIELDS.items():
        for f in fields:
            add_rule(ds, f, "INVALID_DATE", "Error", True, False, f"Field {f} is not a valid date.")
    for ds, fields in DATETIME_FIELDS.items():
        for f in fields:
            add_rule(ds, f, "INVALID_DATETIME", "Error", True, False, f"Field {f} is not a valid datetime.")
    for ds, fields in NUMERIC_FIELDS.items():
        for f in fields:
            add_rule(ds, f, "INVALID_NUMERIC", "Error", True, False, f"Field {f} is not a valid number.")
    for ds, fields in BOOLEAN_FIELDS.items():
        for f in fields:
            add_rule(ds, f, "INVALID_BOOLEAN", "Error", True, False, f"Field {f} is not a valid boolean.")

    # Required-value completeness
    for ds, cols in SCHEMA_REGISTRY.items():
        for col, required in cols:
            if required and col not in (DATE_FIELDS.get(ds, []) + DATETIME_FIELDS.get(ds, []) + NUMERIC_FIELDS.get(ds, []) + BOOLEAN_FIELDS.get(ds, [])):
                add_rule(ds, col, "REQUIRED_VALUE_MISSING", "Error", True, False, f"Required field {col} has missing value.")

    # Domain-value rules
    for ds, field_map in CATEGORICAL_FIELDS.items():
        for field, domain in field_map.items():
            add_rule(ds, field, "INVALID_DOMAIN", "Error", True, False, f"Field {field} value not in approved domain.")

    # Foreign-key rules
    for child, child_field, parent, parent_field, mandatory in RELATIONSHIP_REGISTRY:
        sev = "Critical" if mandatory else "Error"
        blocks = mandatory
        add_rule(child, child_field, "ORPHAN_FOREIGN_KEY", sev, blocks, not blocks,
                 f"Field {child_field} references {parent}.{parent_field} but value not found.")

    # Numeric/logical range rules
    add_rule("staff_roster", "planned_hours", "NEGATIVE_VALUE", "Error", True, False, "Planned hours cannot be negative.")
    add_rule("staff_attendance", "actual_hours", "NEGATIVE_VALUE", "Error", True, False, "Actual hours cannot be negative.")
    add_rule("staffing_requirement", "required_staff_count", "NEGATIVE_VALUE", "Error", True, False, "Required staff count cannot be negative.")
    add_rule("staffing_requirement", "required_hours", "NEGATIVE_VALUE", "Error", True, False, "Required hours cannot be negative.")
    add_rule("patient_queue_records", "arrivals_count", "NEGATIVE_VALUE", "Error", True, False, "Arrivals count cannot be negative.")
    add_rule("patient_queue_records", "served_count", "NEGATIVE_VALUE", "Error", True, False, "Served count cannot be negative.")
    add_rule("patient_queue_records", "waiting_count", "NEGATIVE_VALUE", "Error", True, False, "Waiting count cannot be negative.")
    add_rule("patient_queue_records", "avg_wait_minutes", "NEGATIVE_VALUE", "Error", True, False, "Average wait minutes cannot be negative.")
    add_rule("patient_queue_records", "median_wait_minutes", "NEGATIVE_VALUE", "Error", True, False, "Median wait minutes cannot be negative.")
    add_rule("patient_queue_records", "max_wait_minutes", "NEGATIVE_VALUE", "Error", True, False, "Max wait minutes cannot be negative.")
    add_rule("bed_capacity_records", "bed_licensed", "NEGATIVE_VALUE", "Error", True, False, "Licensed beds cannot be negative.")
    add_rule("bed_capacity_records", "bed_staffed", "NEGATIVE_VALUE", "Error", True, False, "Staffed beds cannot be negative.")
    add_rule("bed_capacity_records", "bed_operational", "NEGATIVE_VALUE", "Error", True, False, "Operational beds cannot be negative.")
    add_rule("bed_capacity_records", "bed_occupied", "NEGATIVE_VALUE", "Error", True, False, "Occupied beds cannot be negative.")
    add_rule("bed_capacity_records", "bed_unavailable", "NEGATIVE_VALUE", "Error", True, False, "Unavailable beds cannot be negative.")
    add_rule("bed_capacity_records", "bed_reserved", "NEGATIVE_VALUE", "Error", True, False, "Reserved beds cannot be negative.")
    add_rule("patient_surveys", "response_weight", "NEGATIVE_VALUE", "Error", True, False, "Response weight cannot be negative.")
    add_rule("service_schedule", "planned_hours", "NEGATIVE_VALUE", "Error", True, False, "Planned hours cannot be negative.")
    add_rule("service_schedule", "planned_capacity", "NEGATIVE_VALUE", "Error", True, False, "Planned capacity cannot be negative.")

    # Logical ordering rules
    add_rule("staff_master", "employment_end_date", "DATE_ORDER", "Error", True, False,
             "Employment end date must be after start date.")
    add_rule("staff_roster", "planned_end_datetime", "DATETIME_ORDER", "Error", True, False,
             "Planned end datetime must be after planned start datetime.")
    add_rule("staff_attendance", "actual_end_datetime", "DATETIME_ORDER", "Error", True, False,
             "Actual end datetime must be after actual start datetime.")
    add_rule("patient_encounters", "service_start_datetime", "DATETIME_ORDER", "Error", True, False,
             "Service start must not be before arrival.")
    add_rule("patient_encounters", "service_end_datetime", "DATETIME_ORDER", "Error", True, False,
             "Service end must not be before service start.")
    add_rule("patient_queue_records", "period_end", "DATETIME_ORDER", "Error", True, False,
             "Period end must be after period start.")
    add_rule("service_schedule", "planned_end_time", "TIME_ORDER", "Error", True, False,
             "Planned end time must be after planned start time.")

    # Bed-capacity specific
    add_rule("bed_capacity_records", "bed_operational", "BED_LOGIC", "Error", True, False,
             "Operational beds should not normally exceed licensed beds.")
    add_rule("bed_capacity_records", "exception_reason", "BED_EXCEPTION", "Error", True, False,
             "Occupied beds above operational capacity requires exception reason when exception flag is true.")

    # Queue consistency
    add_rule("patient_queue_records", "served_count", "QUEUE_LOGIC", "Warning", False, True,
             "Served count should not exceed arrivals count.")
    add_rule("patient_queue_records", "max_wait_minutes", "QUEUE_LOGIC", "Warning", False, True,
             "Max wait minutes should not be lower than average wait minutes.")

    # Survey scale logic
    add_rule("patient_surveys", "score_value", "SURVEY_SCALE", "Error", True, False,
             "Survey score must lie within declared scale minimum and maximum.")

    # Privacy / prohibited fields
    add_rule("", "", "PROHIBITED_FIELD", "Critical", True, False,
             "Prohibited direct-identifier column detected.")

    # Configuration readiness
    add_rule("", "", "CONFIG_MISSING", "Warning", False, True,
             "Required configuration file not found.")

    return rules


VALIDATION_RULE_REGISTRY = _build_rule_registry()

# Prohibited column-name fragments (case-insensitive)
PROHIBITED_FIELD_FRAGMENTS = [
    "patient_name", "patient_full_name", "staff_name", "identity_card",
    "ic_number", "national_id", "passport_number", "address",
    "telephone", "phone_number", "email", "diagnosis",
    "clinical_note", "medical_record_number", "next_of_kin",
]

# Datasets that are allowed to be empty
ALLOWED_EMPTY_DATASETS: List[str] = []

# Mandatory datasets (missing file blocks run)
MANDATORY_DATASETS = DATASET_NAMES.copy()

# Bed-based department types (for bed-capacity validation)
BED_BASED_DEPARTMENT_TYPES = ["Clinical"]

# Approved date range for generated demo data
APPROVED_DATE_RANGE = ("2026-01-01", "2026-12-31")


# ---------------------------------------------------------------------------
# Public loader API
# ---------------------------------------------------------------------------

def load_dataset_schema_registry() -> Dict[str, Dict[str, Any]]:
    """Return a structured schema registry for all datasets."""
    registry: Dict[str, Dict[str, Any]] = {}
    for ds in DATASET_NAMES:
        cols = SCHEMA_REGISTRY.get(ds, [])
        registry[ds] = {
            "columns": [c[0] for c in cols],
            "required_columns": [c[0] for c in cols if c[1]],
            "optional_columns": [c[0] for c in cols if not c[1]],
            "primary_key": PRIMARY_KEYS.get(ds),
            "date_fields": DATE_FIELDS.get(ds, []),
            "datetime_fields": DATETIME_FIELDS.get(ds, []),
            "numeric_fields": NUMERIC_FIELDS.get(ds, []),
            "boolean_fields": BOOLEAN_FIELDS.get(ds, []),
            "categorical_fields": list(CATEGORICAL_FIELDS.get(ds, {}).keys()),
            "domain_values": CATEGORICAL_FIELDS.get(ds, {}),
        }
    return registry


def load_relationship_registry() -> List[Dict[str, Any]]:
    """Return relationship registry as list of dicts."""
    return [
        {
            "relationship_id": f"REL-{i+1:04d}",
            "child_dataset": r[0],
            "child_field": r[1],
            "parent_dataset": r[2],
            "parent_field": r[3],
            "mandatory": r[4],
        }
        for i, r in enumerate(RELATIONSHIP_REGISTRY)
    ]


def load_validation_rule_registry() -> List[Dict[str, Any]]:
    """Return the full validation-rule registry."""
    return VALIDATION_RULE_REGISTRY.copy()


def validate_registry_integrity() -> Tuple[bool, List[str]]:
    """Validate the internal registries and return (ok, messages)."""
    errors: List[str] = []

    # All 13 datasets defined
    for ds in DATASET_NAMES:
        if ds not in SCHEMA_REGISTRY:
            errors.append(f"Schema registry missing dataset: {ds}")

    # Primary keys exist in schema
    for ds, pk in PRIMARY_KEYS.items():
        cols = [c[0] for c in SCHEMA_REGISTRY.get(ds, [])]
        if pk not in cols:
            errors.append(f"Primary key {pk} not in schema for {ds}")

    # FK child fields exist
    for child, child_field, parent, parent_field, mandatory in RELATIONSHIP_REGISTRY:
        child_cols = [c[0] for c in SCHEMA_REGISTRY.get(child, [])]
        parent_cols = [c[0] for c in SCHEMA_REGISTRY.get(parent, [])]
        if child_field not in child_cols:
            errors.append(f"FK child field {child}.{child_field} missing from schema")
        if parent_field not in parent_cols:
            errors.append(f"FK parent field {parent}.{parent_field} missing from schema")

    # Unique test IDs
    test_ids = [r["test_id"] for r in VALIDATION_RULE_REGISTRY]
    if len(test_ids) != len(set(test_ids)):
        errors.append("Duplicate test IDs detected in rule registry")

    # Valid severity values
    valid_severities = {"Information", "Warning", "Error", "Critical"}
    for r in VALIDATION_RULE_REGISTRY:
        if r["severity"] not in valid_severities:
            errors.append(f"Invalid severity '{r['severity']}' in rule {r['test_id']}")
        if not isinstance(r["blocks_processing"], bool):
            errors.append(f"Non-boolean blocks_processing in rule {r['test_id']}")
        if not isinstance(r["manual_override_allowed"], bool):
            errors.append(f"Non-boolean manual_override_allowed in rule {r['test_id']}")

    return len(errors) == 0, errors


def get_rules_for_dataset(dataset_name: str) -> List[Dict[str, Any]]:
    """Return all rules applicable to a given dataset."""
    return [r for r in VALIDATION_RULE_REGISTRY if r["dataset_name"] == dataset_name or r["dataset_name"] == ""]


def get_rule_by_test_id(test_id: str) -> Optional[Dict[str, Any]]:
    """Return a single rule by test identifier."""
    for r in VALIDATION_RULE_REGISTRY:
        if r["test_id"] == test_id:
            return r
    return None
