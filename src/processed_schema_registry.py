"""
Sentinel360 Healthcare — Processed Schema Registry

Structured registry for all 19 processed datasets.
Defines schemas, grains, primary keys, fields, types, and implementation steps.

Step: 2D-1
"""

from typing import Any, Dict, List, Optional, Set


ProcessedSchema = Dict[str, Any]


def _build_schema(
    name: str,
    source_datasets: List[str],
    purpose: str,
    grain: str,
    primary_key: str,
    required_fields: List[str],
    optional_fields: List[str],
    date_fields: List[str],
    datetime_fields: List[str],
    numeric_fields: List[str],
    boolean_fields: List[str],
    categorical_fields: Dict[str, List[str]],
    parent_relationships: List[Dict[str, str]],
    downstream_use: List[str],
    transformation_owner: str,
    implementation_step: str,
) -> ProcessedSchema:
    return {
        "processed_dataset_name": name,
        "source_datasets": source_datasets,
        "purpose": purpose,
        "grain": grain,
        "primary_key": primary_key,
        "required_fields": required_fields,
        "optional_fields": optional_fields,
        "date_fields": date_fields,
        "datetime_fields": datetime_fields,
        "numeric_fields": numeric_fields,
        "boolean_fields": boolean_fields,
        "categorical_fields": categorical_fields,
        "parent_relationships": parent_relationships,
        "downstream_use": downstream_use,
        "transformation_owner": transformation_owner,
        "implementation_step": implementation_step,
    }


# ---------------------------------------------------------------------------
# Transformation rule registry (reserved IDs for future steps)
# ---------------------------------------------------------------------------
TRANSFORMATION_RULES: List[Dict[str, Any]] = [
    # Reference / Master
    {"transformation_rule_id": "TR_REF_STANDARDISE_TEXT", "name": "Standardise Text", "domain": "Reference", "description": "Trim, uppercase, normalise text fields.", "source_datasets": ["*"], "target_datasets": ["processed_hospital_master", "processed_department_master", "processed_staff_role_master", "processed_staff_master"], "implementation_step": "2D-2", "configuration_dependency": "None", "audit_required": True, "active_flag": True},
    {"transformation_rule_id": "TR_REF_STANDARDISE_DATE", "name": "Standardise Date", "domain": "Reference", "description": "Parse and standardise date fields to ISO format.", "source_datasets": ["*"], "target_datasets": ["processed_hospital_master", "processed_department_master", "processed_staff_role_master", "processed_staff_master"], "implementation_step": "2D-2", "configuration_dependency": "None", "audit_required": True, "active_flag": True},
    {"transformation_rule_id": "TR_REF_EFFECTIVE_DATING", "name": "Effective Dating", "domain": "Reference", "description": "Apply effective-start and effective-end dating.", "source_datasets": ["hospital_master", "department_master", "staff_role_master", "staff_master"], "target_datasets": ["processed_hospital_master", "processed_department_master", "processed_staff_role_master", "processed_staff_master"], "implementation_step": "2D-2", "configuration_dependency": "None", "audit_required": True, "active_flag": True},
    {"transformation_rule_id": "TR_REF_ACTIVE_FLAG", "name": "Active Flag Derivation", "domain": "Reference", "description": "Derive active_flag from effective dates and source status.", "source_datasets": ["hospital_master", "department_master", "staff_role_master", "staff_master"], "target_datasets": ["processed_hospital_master", "processed_department_master", "processed_staff_role_master", "processed_staff_master"], "implementation_step": "2D-2", "configuration_dependency": "None", "audit_required": True, "active_flag": True},

    # Workforce
    {"transformation_rule_id": "TR_WF_ROSTER_DATETIME", "name": "Roster Datetime Construction", "domain": "Workforce", "description": "Build planned start and end datetimes from roster date and shift.", "source_datasets": ["staff_roster"], "target_datasets": ["processed_staff_roster"], "implementation_step": "2D-2", "configuration_dependency": "shift_definitions", "audit_required": True, "active_flag": True},
    {"transformation_rule_id": "TR_WF_OVERNIGHT_SHIFT", "name": "Overnight Shift Handling", "domain": "Workforce", "description": "Correctly handle shifts that cross midnight.", "source_datasets": ["staff_roster"], "target_datasets": ["processed_staff_roster"], "implementation_step": "2D-2", "configuration_dependency": "shift_definitions", "audit_required": True, "active_flag": True},
    {"transformation_rule_id": "TR_WF_ATTENDANCE_MAPPING", "name": "Attendance Status Mapping", "domain": "Workforce", "description": "Map raw attendance status to standardised categories using approved mapping.", "source_datasets": ["staff_attendance"], "target_datasets": ["processed_staff_attendance"], "implementation_step": "2D-2", "configuration_dependency": "attendance_status_mapping.csv", "audit_required": True, "active_flag": True},
    {"transformation_rule_id": "TR_WF_ACTUAL_HOURS", "name": "Actual Hours Calculation", "domain": "Workforce", "description": "Compute actual hours worked from start and end datetimes.", "source_datasets": ["staff_attendance"], "target_datasets": ["processed_staff_attendance"], "implementation_step": "2D-2", "configuration_dependency": "None", "audit_required": True, "active_flag": True},
    {"transformation_rule_id": "TR_WF_LOST_HOURS", "name": "Lost Hours Calculation", "domain": "Workforce", "description": "Compute lost scheduled hours due to absence or partial attendance.", "source_datasets": ["staff_attendance", "staff_roster"], "target_datasets": ["processed_staff_attendance"], "implementation_step": "2D-2", "configuration_dependency": "attendance_status_mapping.csv", "audit_required": True, "active_flag": True},
    {"transformation_rule_id": "TR_WF_AVAILABILITY_CONTRIBUTION", "name": "Availability Contribution", "domain": "Workforce", "description": "Determine whether a record contributes to available staff hours.", "source_datasets": ["staff_attendance"], "target_datasets": ["processed_staff_attendance"], "implementation_step": "2D-2", "configuration_dependency": "attendance_status_mapping.csv", "audit_required": True, "active_flag": True},
    {"transformation_rule_id": "TR_WF_ABSENTEEISM_ELIGIBILITY", "name": "Absenteeism Eligibility", "domain": "Workforce", "description": "Flag records eligible for absenteeism numerator based on approved rules.", "source_datasets": ["staff_attendance"], "target_datasets": ["processed_staff_attendance"], "implementation_step": "2D-2", "configuration_dependency": "absence_category_mapping.csv", "audit_required": True, "active_flag": True},
    {"transformation_rule_id": "TR_WF_DEPARTMENT_ATTRIBUTION", "name": "Department Attribution", "domain": "Workforce", "description": "Determine which department a staff record is attributed to.", "source_datasets": ["staff_attendance", "staff_roster"], "target_datasets": ["processed_staff_attendance", "processed_staff_roster"], "implementation_step": "2D-2", "configuration_dependency": "attendance_status_mapping.csv", "audit_required": True, "active_flag": True},
    {"transformation_rule_id": "TR_WF_REASSIGNMENT", "name": "Reassignment Handling", "domain": "Workforce", "description": "Process reassigned staff to destination department.", "source_datasets": ["staff_attendance", "staff_roster"], "target_datasets": ["processed_staff_attendance", "processed_staff_roster"], "implementation_step": "2D-2", "configuration_dependency": "None", "audit_required": True, "active_flag": True},
    {"transformation_rule_id": "TR_WF_REPLACEMENT_REFERENCE", "name": "Replacement Staff Reference", "domain": "Workforce", "description": "Validate and reference replacement staff where populated.", "source_datasets": ["staff_attendance"], "target_datasets": ["processed_staff_attendance"], "implementation_step": "2D-2", "configuration_dependency": "None", "audit_required": True, "active_flag": True},
    {"transformation_rule_id": "TR_WF_MISSING_UNKNOWN", "name": "Missing and Unknown Attendance", "domain": "Workforce", "description": "Preserve missing and unknown attendance without imputation.", "source_datasets": ["staff_attendance"], "target_datasets": ["processed_staff_attendance"], "implementation_step": "2D-2", "configuration_dependency": "attendance_status_mapping.csv", "audit_required": True, "active_flag": True},
    {"transformation_rule_id": "TR_WF_DAILY_AGGREGATION", "name": "Workforce Daily Aggregation", "domain": "Workforce", "description": "Aggregate workforce metrics to daily grain without calculating KPI percentages.", "source_datasets": ["processed_staff_roster", "processed_staff_attendance", "processed_staffing_requirement"], "target_datasets": ["processed_workforce_daily"], "implementation_step": "2D-2", "configuration_dependency": "None", "audit_required": True, "active_flag": True},

    # Patient Flow
    {"transformation_rule_id": "TR_PF_TIMESTAMP_PARSE", "name": "Timestamp Parsing", "domain": "Patient Flow", "description": "Parse and standardise encounter timestamps.", "source_datasets": ["patient_encounters"], "target_datasets": ["processed_patient_encounters"], "implementation_step": "2D-3", "configuration_dependency": "None", "audit_required": True, "active_flag": True},
    {"transformation_rule_id": "TR_PF_WAIT_INTERVALS", "name": "Wait Interval Calculation", "domain": "Patient Flow", "description": "Calculate interval durations in minutes between timestamps.", "source_datasets": ["patient_encounters"], "target_datasets": ["processed_patient_encounters"], "implementation_step": "2D-3", "configuration_dependency": "None", "audit_required": True, "active_flag": True},
    {"transformation_rule_id": "TR_PF_WAIT_ELIGIBILITY", "name": "Wait Eligibility", "domain": "Patient Flow", "description": "Flag encounters eligible for official wait-time calculation.", "source_datasets": ["patient_encounters"], "target_datasets": ["processed_patient_encounters"], "implementation_step": "2D-3", "configuration_dependency": "None", "audit_required": True, "active_flag": True},
    {"transformation_rule_id": "TR_PF_QUEUE_STANDARDISATION", "name": "Queue Standardisation", "domain": "Patient Flow", "description": "Standardise queue stage definitions and counts.", "source_datasets": ["patient_queue_records"], "target_datasets": ["processed_patient_queue"], "implementation_step": "2D-3", "configuration_dependency": "None", "audit_required": True, "active_flag": True},
    {"transformation_rule_id": "TR_PF_BED_STANDARDISATION", "name": "Bed Capacity Standardisation", "domain": "Patient Flow", "description": "Standardise bed capacity fields and exception flags.", "source_datasets": ["bed_capacity_records"], "target_datasets": ["processed_bed_capacity"], "implementation_step": "2D-3", "configuration_dependency": "None", "audit_required": True, "active_flag": True},
    {"transformation_rule_id": "TR_PF_OVERCAPACITY", "name": "Overcapacity Detection", "domain": "Patient Flow", "description": "Detect and flag overcapacity conditions with exception metadata.", "source_datasets": ["bed_capacity_records"], "target_datasets": ["processed_bed_capacity"], "implementation_step": "2D-3", "configuration_dependency": "None", "audit_required": True, "active_flag": True},
    {"transformation_rule_id": "TR_PF_SCHEDULE_STANDARDISATION", "name": "Schedule Standardisation", "domain": "Patient Flow", "description": "Standardise service schedule fields and session flags.", "source_datasets": ["service_schedule"], "target_datasets": ["processed_service_schedule"], "implementation_step": "2D-3", "configuration_dependency": "None", "audit_required": True, "active_flag": True},
    {"transformation_rule_id": "TR_PF_DAILY_AGGREGATION", "name": "Patient Flow Daily Aggregation", "domain": "Patient Flow", "description": "Aggregate patient flow metrics to daily grain without official KPI outputs.", "source_datasets": ["processed_patient_encounters", "processed_patient_queue", "processed_bed_capacity", "processed_service_schedule"], "target_datasets": ["processed_patient_flow_daily"], "implementation_step": "2D-3", "configuration_dependency": "None", "audit_required": True, "active_flag": True},

    # Patient Experience
    {"transformation_rule_id": "TR_PX_COMPLAINT_ELIGIBILITY", "name": "Complaint Eligibility", "domain": "Patient Experience", "description": "Flag complaints eligible for official complaint-rate numerator.", "source_datasets": ["patient_complaints"], "target_datasets": ["processed_patient_complaints"], "implementation_step": "2D-4", "configuration_dependency": "None", "audit_required": True, "active_flag": True},
    {"transformation_rule_id": "TR_PX_SOCIAL_SIGNAL_CLASSIFICATION", "name": "Social Signal Classification", "domain": "Patient Experience", "description": "Separate formal complaints from unverified social-media signals.", "source_datasets": ["patient_complaints"], "target_datasets": ["processed_patient_complaints"], "implementation_step": "2D-4", "configuration_dependency": "None", "audit_required": True, "active_flag": True},
    {"transformation_rule_id": "TR_PX_DUPLICATE_CLASSIFICATION", "name": "Duplicate Classification", "domain": "Patient Experience", "description": "Mark duplicate complaints and link to original.", "source_datasets": ["patient_complaints"], "target_datasets": ["processed_patient_complaints"], "implementation_step": "2D-4", "configuration_dependency": "None", "audit_required": True, "active_flag": True},
    {"transformation_rule_id": "TR_PX_SURVEY_NORMALISATION", "name": "Survey Normalisation", "domain": "Patient Experience", "description": "Normalise survey score to a standard 0-100 scale.", "source_datasets": ["patient_surveys"], "target_datasets": ["processed_patient_surveys"], "implementation_step": "2D-4", "configuration_dependency": "None", "audit_required": True, "active_flag": True},
    {"transformation_rule_id": "TR_PX_SURVEY_ELIGIBILITY", "name": "Survey Eligibility", "domain": "Patient Experience", "description": "Flag survey responses eligible for satisfaction KPI.", "source_datasets": ["patient_surveys"], "target_datasets": ["processed_patient_surveys"], "implementation_step": "2D-4", "configuration_dependency": "None", "audit_required": True, "active_flag": True},
    {"transformation_rule_id": "TR_PX_WEIGHT_STANDARDISATION", "name": "Weight Standardisation", "domain": "Patient Experience", "description": "Standardise response weights.", "source_datasets": ["patient_surveys"], "target_datasets": ["processed_patient_surveys"], "implementation_step": "2D-4", "configuration_dependency": "None", "audit_required": True, "active_flag": True},
    {"transformation_rule_id": "TR_PX_DAILY_AGGREGATION", "name": "Patient Experience Daily Aggregation", "domain": "Patient Experience", "description": "Aggregate patient experience metrics to daily grain without official KPI outputs.", "source_datasets": ["processed_patient_complaints", "processed_patient_surveys"], "target_datasets": ["processed_patient_experience_daily"], "implementation_step": "2D-4", "configuration_dependency": "None", "audit_required": True, "active_flag": True},

    # Control
    {"transformation_rule_id": "TR_CTRL_LINEAGE", "name": "Lineage Construction", "domain": "Control", "description": "Build source-to-processed lineage records.", "source_datasets": ["*"], "target_datasets": ["processing_record_lineage"], "implementation_step": "2D-5", "configuration_dependency": "None", "audit_required": True, "active_flag": True},
    {"transformation_rule_id": "TR_CTRL_EXCLUSION", "name": "Exclusion Register Construction", "domain": "Control", "description": "Build exclusion register from all excluded records.", "source_datasets": ["*"], "target_datasets": ["processing_exclusion_register"], "implementation_step": "2D-5", "configuration_dependency": "None", "audit_required": True, "active_flag": True},
    {"transformation_rule_id": "TR_CTRL_RUN_SUMMARY", "name": "Run Summary Construction", "domain": "Control", "description": "Build processing run summary from dataset results.", "source_datasets": ["*"], "target_datasets": ["processing_run_summary"], "implementation_step": "2D-5", "configuration_dependency": "None", "audit_required": True, "active_flag": True},
]

# ---------------------------------------------------------------------------
# Processed dataset schemas
# ---------------------------------------------------------------------------
_PROCESSED_SCHEMAS: Dict[str, ProcessedSchema] = {
    # A. Reference and Master Datasets (Step 2D-2)
    "processed_hospital_master": _build_schema(
        name="processed_hospital_master",
        source_datasets=["hospital_master"],
        purpose="Standardised effective-dated hospital reference.",
        grain="One row per valid effective-dated master record.",
        primary_key="hospital_id",
        required_fields=[
            "hospital_id", "hospital_name", "hospital_type", "active_flag",
            "effective_start_date", "effective_end_date", "source_system",
            "source_record_version", "processing_run_id", "validation_run_id",
            "transformation_version", "processed_datetime",
        ],
        optional_fields=["source_primary_key", "source_row_number"],
        date_fields=["effective_start_date", "effective_end_date"],
        datetime_fields=["processed_datetime"],
        numeric_fields=["source_record_version"],
        boolean_fields=["active_flag"],
        categorical_fields={
            "hospital_type": ["Public", "Private", "Specialist", "Teaching"],
        },
        parent_relationships=[],
        downstream_use=["processed_department_master", "processed_staff_master", "processed_workforce_daily", "processed_patient_flow_daily", "processed_patient_experience_daily"],
        transformation_owner="system",
        implementation_step="2D-2",
    ),
    "processed_department_master": _build_schema(
        name="processed_department_master",
        source_datasets=["department_master"],
        purpose="Standardised effective-dated department reference.",
        grain="One row per valid effective-dated master record.",
        primary_key="department_id",
        required_fields=[
            "department_id", "hospital_id", "department_name", "department_type",
            "parent_department_id", "bed_based_flag", "queue_based_flag",
            "patient_experience_flag", "active_flag", "effective_start_date",
            "effective_end_date", "processing_run_id", "validation_run_id",
            "transformation_version", "processed_datetime",
        ],
        optional_fields=["source_primary_key", "source_row_number"],
        date_fields=["effective_start_date", "effective_end_date"],
        datetime_fields=["processed_datetime"],
        numeric_fields=[],
        boolean_fields=["bed_based_flag", "queue_based_flag", "patient_experience_flag", "active_flag"],
        categorical_fields={
            "department_type": ["Emergency", "Inpatient", "Outpatient", "Surgical", "Diagnostic", "Administrative", "Support"],
        },
        parent_relationships=[
            {"parent_dataset": "processed_hospital_master", "parent_field": "hospital_id", "child_field": "hospital_id"},
        ],
        downstream_use=["processed_staff_master", "processed_staff_roster", "processed_staff_attendance", "processed_staffing_requirement", "processed_patient_encounters", "processed_patient_queue", "processed_bed_capacity", "processed_service_schedule", "processed_workforce_daily", "processed_patient_flow_daily", "processed_patient_experience_daily"],
        transformation_owner="system",
        implementation_step="2D-2",
    ),
    "processed_staff_role_master": _build_schema(
        name="processed_staff_role_master",
        source_datasets=["staff_role_master"],
        purpose="Standardised effective-dated staff role reference.",
        grain="One row per valid effective-dated master record.",
        primary_key="staff_role_id",
        required_fields=[
            "staff_role_id", "staff_role_name", "staff_category", "clinical_role_flag",
            "patient_facing_flag", "active_flag", "effective_start_date",
            "effective_end_date", "processing_run_id", "validation_run_id",
            "transformation_version", "processed_datetime",
        ],
        optional_fields=["source_primary_key", "source_row_number"],
        date_fields=["effective_start_date", "effective_end_date"],
        datetime_fields=["processed_datetime"],
        numeric_fields=[],
        boolean_fields=["clinical_role_flag", "patient_facing_flag", "active_flag"],
        categorical_fields={
            "staff_category": ["Doctor", "Nurse", "Allied Health", "Support", "Administrative", "Other"],
        },
        parent_relationships=[],
        downstream_use=["processed_staff_master", "processed_staff_roster", "processed_staff_attendance", "processed_staffing_requirement", "processed_workforce_daily"],
        transformation_owner="system",
        implementation_step="2D-2",
    ),
    "processed_staff_master": _build_schema(
        name="processed_staff_master",
        source_datasets=["staff_master"],
        purpose="Standardised effective-dated staff reference.",
        grain="One row per valid effective-dated master record.",
        primary_key="staff_id",
        required_fields=[
            "staff_id", "hospital_id", "home_department_id", "staff_role_id",
            "staff_category", "employment_type", "fte_value", "employment_start_date",
            "employment_end_date", "active_flag", "processing_run_id",
            "validation_run_id", "transformation_version", "processed_datetime",
        ],
        optional_fields=["source_primary_key", "source_row_number"],
        date_fields=["employment_start_date", "employment_end_date"],
        datetime_fields=["processed_datetime"],
        numeric_fields=["fte_value"],
        boolean_fields=["active_flag"],
        categorical_fields={
            "staff_category": ["Doctor", "Nurse", "Allied Health", "Support", "Administrative", "Other"],
            "employment_type": ["Full-time", "Part-time", "Contract", "Temporary", "Locum"],
        },
        parent_relationships=[
            {"parent_dataset": "processed_hospital_master", "parent_field": "hospital_id", "child_field": "hospital_id"},
            {"parent_dataset": "processed_department_master", "parent_field": "department_id", "child_field": "home_department_id"},
            {"parent_dataset": "processed_staff_role_master", "parent_field": "staff_role_id", "child_field": "staff_role_id"},
        ],
        downstream_use=["processed_staff_roster", "processed_staff_attendance", "processed_workforce_daily"],
        transformation_owner="system",
        implementation_step="2D-2",
    ),

    # B. Workforce Datasets (Step 2D-2)
    "processed_staff_roster": _build_schema(
        name="processed_staff_roster",
        source_datasets=["staff_roster"],
        purpose="Standardised staff roster with shift and assignment detail.",
        grain="One row per staff, roster date, shift, department and assignment.",
        primary_key="roster_record_id",
        required_fields=[
            "roster_record_id", "staff_id", "hospital_id", "department_id",
            "staff_role_id", "roster_date", "reporting_date", "reporting_month",
            "shift_code", "planned_start_datetime", "planned_end_datetime",
            "planned_hours", "assignment_status", "original_department_id",
            "reassigned_department_id", "cancelled_flag", "valid_assignment_flag",
            "source_primary_key", "processing_run_id", "validation_run_id",
            "transformation_version", "processed_datetime",
        ],
        optional_fields=["source_row_number"],
        date_fields=["roster_date", "reporting_date"],
        datetime_fields=["planned_start_datetime", "planned_end_datetime", "processed_datetime"],
        numeric_fields=["planned_hours"],
        boolean_fields=["cancelled_flag", "valid_assignment_flag"],
        categorical_fields={
            "assignment_status": ["Scheduled", "Confirmed", "Reassigned", "Cancelled"],
            "shift_code": ["M", "A", "N", "E", "WE", "ON", "OFF"],
        },
        parent_relationships=[
            {"parent_dataset": "processed_staff_master", "parent_field": "staff_id", "child_field": "staff_id"},
            {"parent_dataset": "processed_department_master", "parent_field": "department_id", "child_field": "department_id"},
            {"parent_dataset": "processed_staff_role_master", "parent_field": "staff_role_id", "child_field": "staff_role_id"},
        ],
        downstream_use=["processed_staff_attendance", "processed_workforce_daily"],
        transformation_owner="system",
        implementation_step="2D-2",
    ),
    "processed_staff_attendance": _build_schema(
        name="processed_staff_attendance",
        source_datasets=["staff_attendance"],
        purpose="Standardised staff attendance with hours, status and eligibility flags.",
        grain="One row per staff, attendance date, shift and actual assignment.",
        primary_key="attendance_record_id",
        required_fields=[
            "attendance_record_id", "roster_record_id", "staff_id", "hospital_id",
            "home_department_id", "actual_department_id", "staff_role_id",
            "attendance_date", "reporting_date", "reporting_month", "shift_code",
            "attendance_status", "absence_category", "scheduled_hours",
            "actual_hours_worked", "lost_scheduled_hours", "availability_contribution",
            "absenteeism_eligible_flag", "absenteeism_hours", "planned_absence_flag",
            "replacement_staff_id", "reassigned_flag", "missing_attendance_flag",
            "unknown_attendance_flag", "valid_attendance_flag", "source_primary_key",
            "processing_run_id", "validation_run_id", "transformation_version",
            "processed_datetime",
        ],
        optional_fields=["source_row_number"],
        date_fields=["attendance_date", "reporting_date"],
        datetime_fields=["processed_datetime"],
        numeric_fields=["scheduled_hours", "actual_hours_worked", "lost_scheduled_hours", "availability_contribution", "absenteeism_hours"],
        boolean_fields=[
            "absenteeism_eligible_flag", "planned_absence_flag", "reassigned_flag",
            "missing_attendance_flag", "unknown_attendance_flag", "valid_attendance_flag",
        ],
        categorical_fields={
            "attendance_status": ["Present", "Partial", "Reassigned", "Late", "Training", "Leave", "Absent", "Not Scheduled", "Missing", "Unknown"],
            "absence_category": ["Sick Leave", "Emergency Leave", "Annual Leave", "Unauthorised", "Training", "Reassigned", "Not Scheduled", "Other", "Not Applicable", "Unknown"],
            "shift_code": ["M", "A", "N", "E", "WE", "ON", "OFF"],
        },
        parent_relationships=[
            {"parent_dataset": "processed_staff_master", "parent_field": "staff_id", "child_field": "staff_id"},
            {"parent_dataset": "processed_staff_roster", "parent_field": "roster_record_id", "child_field": "roster_record_id"},
            {"parent_dataset": "processed_department_master", "parent_field": "department_id", "child_field": "actual_department_id"},
            {"parent_dataset": "processed_staff_role_master", "parent_field": "staff_role_id", "child_field": "staff_role_id"},
        ],
        downstream_use=["processed_workforce_daily"],
        transformation_owner="system",
        implementation_step="2D-2",
    ),
    "processed_staffing_requirement": _build_schema(
        name="processed_staffing_requirement",
        source_datasets=["staffing_requirement"],
        purpose="Standardised staffing requirement by department, date, shift and role.",
        grain="One row per hospital, department, date, shift and staff role.",
        primary_key="staffing_requirement_id",
        required_fields=[
            "staffing_requirement_id", "hospital_id", "department_id", "staff_role_id",
            "requirement_date", "reporting_date", "reporting_month", "shift_code",
            "required_staff_count", "required_staff_hours", "requirement_status",
            "valid_requirement_flag", "source_primary_key", "processing_run_id",
            "validation_run_id", "transformation_version", "processed_datetime",
        ],
        optional_fields=["source_row_number"],
        date_fields=["requirement_date", "reporting_date"],
        datetime_fields=["processed_datetime"],
        numeric_fields=["required_staff_count", "required_staff_hours"],
        boolean_fields=["valid_requirement_flag"],
        categorical_fields={
            "requirement_status": ["Active", "Superseded", "Draft", "Cancelled"],
            "shift_code": ["M", "A", "N", "E", "WE", "ON", "OFF"],
        },
        parent_relationships=[
            {"parent_dataset": "processed_hospital_master", "parent_field": "hospital_id", "child_field": "hospital_id"},
            {"parent_dataset": "processed_department_master", "parent_field": "department_id", "child_field": "department_id"},
            {"parent_dataset": "processed_staff_role_master", "parent_field": "staff_role_id", "child_field": "staff_role_id"},
        ],
        downstream_use=["processed_workforce_daily"],
        transformation_owner="system",
        implementation_step="2D-2",
    ),
    "processed_workforce_daily": _build_schema(
        name="processed_workforce_daily",
        source_datasets=["processed_staff_roster", "processed_staff_attendance", "processed_staffing_requirement"],
        purpose="Daily workforce analytical preparation without official KPI percentages.",
        grain="One row per hospital, department, reporting date and staff role where role-level detail is retained.",
        primary_key="workforce_daily_id",
        required_fields=[
            "workforce_daily_id", "hospital_id", "department_id", "staff_role_id",
            "reporting_date", "reporting_month", "rostered_staff_count", "rostered_hours",
            "required_staff_count", "required_staff_hours", "verified_available_staff_count",
            "verified_available_hours", "absent_event_count", "absent_hours",
            "planned_leave_event_count", "planned_leave_hours", "partial_attendance_event_count",
            "late_attendance_event_count", "reassigned_in_count", "reassigned_out_count",
            "replacement_staff_count", "missing_attendance_count", "unknown_attendance_count",
            "eligible_record_count", "excluded_record_count", "data_completeness_count",
            "processing_run_id", "validation_run_id", "transformation_version",
            "processed_datetime",
        ],
        optional_fields=[],
        date_fields=["reporting_date"],
        datetime_fields=["processed_datetime"],
        numeric_fields=[
            "rostered_staff_count", "rostered_hours", "required_staff_count", "required_staff_hours",
            "verified_available_staff_count", "verified_available_hours", "absent_event_count",
            "absent_hours", "planned_leave_event_count", "planned_leave_hours",
            "partial_attendance_event_count", "late_attendance_event_count",
            "reassigned_in_count", "reassigned_out_count", "replacement_staff_count",
            "missing_attendance_count", "unknown_attendance_count", "eligible_record_count",
            "excluded_record_count", "data_completeness_count",
        ],
        boolean_fields=[],
        categorical_fields={},
        parent_relationships=[
            {"parent_dataset": "processed_hospital_master", "parent_field": "hospital_id", "child_field": "hospital_id"},
            {"parent_dataset": "processed_department_master", "parent_field": "department_id", "child_field": "department_id"},
            {"parent_dataset": "processed_staff_role_master", "parent_field": "staff_role_id", "child_field": "staff_role_id"},
        ],
        downstream_use=["KPI engine (future)"],
        transformation_owner="system",
        implementation_step="2D-2",
    ),

    # C. Patient Flow and Capacity Datasets (Step 2D-3)
    "processed_patient_encounters": _build_schema(
        name="processed_patient_encounters",
        source_datasets=["patient_encounters"],
        purpose="Standardised patient encounter with timestamps and wait eligibility.",
        grain="One row per encounter.",
        primary_key="encounter_id",
        required_fields=[
            "encounter_id", "hospital_id", "department_id", "encounter_date",
            "reporting_date", "reporting_month", "encounter_type", "arrival_datetime",
            "triage_datetime", "consultation_start_datetime", "service_end_datetime",
            "disposition_status", "cancelled_flag", "left_before_service_flag",
            "completed_service_flag", "arrival_to_triage_minutes", "arrival_to_consultation_minutes",
            "triage_to_consultation_minutes", "consultation_to_service_end_minutes",
            "official_wait_stage_eligible_flag", "encounter_wait_eligible_flag",
            "exclusion_reason_code", "source_primary_key", "processing_run_id",
            "validation_run_id", "transformation_version", "processed_datetime",
        ],
        optional_fields=["source_row_number"],
        date_fields=["encounter_date", "reporting_date"],
        datetime_fields=["arrival_datetime", "triage_datetime", "consultation_start_datetime", "service_end_datetime", "processed_datetime"],
        numeric_fields=[
            "arrival_to_triage_minutes", "arrival_to_consultation_minutes",
            "triage_to_consultation_minutes", "consultation_to_service_end_minutes",
        ],
        boolean_fields=["cancelled_flag", "left_before_service_flag", "completed_service_flag", "official_wait_stage_eligible_flag", "encounter_wait_eligible_flag"],
        categorical_fields={
            "encounter_type": ["Emergency", "Outpatient", "Inpatient", "Surgical", "Diagnostic"],
            "disposition_status": ["Admitted", "Discharged", "Transferred", "Left", "Deceased"],
        },
        parent_relationships=[
            {"parent_dataset": "processed_hospital_master", "parent_field": "hospital_id", "child_field": "hospital_id"},
            {"parent_dataset": "processed_department_master", "parent_field": "department_id", "child_field": "department_id"},
        ],
        downstream_use=["processed_patient_flow_daily"],
        transformation_owner="system",
        implementation_step="2D-3",
    ),
    "processed_patient_queue": _build_schema(
        name="processed_patient_queue",
        source_datasets=["patient_queue_records"],
        purpose="Standardised patient queue by stage and date.",
        grain="One row per hospital, department, queue date and queue stage.",
        primary_key="queue_record_id",
        required_fields=[
            "queue_record_id", "hospital_id", "department_id", "queue_date",
            "reporting_date", "reporting_month", "queue_stage", "arrivals_count",
            "served_count", "waiting_patient_count", "average_wait_minutes",
            "median_wait_minutes", "maximum_wait_minutes", "summary_source_flag",
            "encounter_derived_flag", "valid_queue_record_flag", "source_primary_key",
            "processing_run_id", "validation_run_id", "transformation_version",
            "processed_datetime",
        ],
        optional_fields=["source_row_number"],
        date_fields=["queue_date", "reporting_date"],
        datetime_fields=["processed_datetime"],
        numeric_fields=["arrivals_count", "served_count", "waiting_patient_count", "average_wait_minutes", "median_wait_minutes", "maximum_wait_minutes"],
        boolean_fields=["summary_source_flag", "encounter_derived_flag", "valid_queue_record_flag"],
        categorical_fields={
            "queue_stage": ["Triage", "Registration", "Consultation", "Treatment", "Pharmacy", "Discharge"],
        },
        parent_relationships=[
            {"parent_dataset": "processed_hospital_master", "parent_field": "hospital_id", "child_field": "hospital_id"},
            {"parent_dataset": "processed_department_master", "parent_field": "department_id", "child_field": "department_id"},
        ],
        downstream_use=["processed_patient_flow_daily"],
        transformation_owner="system",
        implementation_step="2D-3",
    ),
    "processed_bed_capacity": _build_schema(
        name="processed_bed_capacity",
        source_datasets=["bed_capacity_records"],
        purpose="Standardised bed capacity with overcapacity detection.",
        grain="One row per hospital, department and reporting date.",
        primary_key="bed_capacity_record_id",
        required_fields=[
            "bed_capacity_record_id", "hospital_id", "department_id", "reporting_date",
            "reporting_month", "licensed_beds", "staffed_beds", "operational_beds",
            "occupied_beds", "unavailable_beds", "reserved_beds",
            "beds_above_operational_capacity", "overcapacity_flag",
            "overcapacity_exception_flag", "overcapacity_reason", "valid_bed_record_flag",
            "source_primary_key", "processing_run_id", "validation_run_id",
            "transformation_version", "processed_datetime",
        ],
        optional_fields=["source_row_number"],
        date_fields=["reporting_date"],
        datetime_fields=["processed_datetime"],
        numeric_fields=["licensed_beds", "staffed_beds", "operational_beds", "occupied_beds", "unavailable_beds", "reserved_beds", "beds_above_operational_capacity"],
        boolean_fields=["overcapacity_flag", "overcapacity_exception_flag", "valid_bed_record_flag"],
        categorical_fields={},
        parent_relationships=[
            {"parent_dataset": "processed_hospital_master", "parent_field": "hospital_id", "child_field": "hospital_id"},
            {"parent_dataset": "processed_department_master", "parent_field": "department_id", "child_field": "department_id"},
        ],
        downstream_use=["processed_patient_flow_daily"],
        transformation_owner="system",
        implementation_step="2D-3",
    ),
    "processed_service_schedule": _build_schema(
        name="processed_service_schedule",
        source_datasets=["service_schedule"],
        purpose="Standardised service schedule with session flags.",
        grain="One row per service session or approved source schedule record.",
        primary_key="service_schedule_id",
        required_fields=[
            "service_schedule_id", "hospital_id", "department_id", "service_date",
            "reporting_date", "reporting_month", "service_type", "session_start_datetime",
            "session_end_datetime", "planned_service_hours", "planned_capacity",
            "schedule_status", "reduced_session_flag", "cancelled_session_flag",
            "extended_session_flag", "valid_schedule_flag", "source_primary_key",
            "processing_run_id", "validation_run_id", "transformation_version",
            "processed_datetime",
        ],
        optional_fields=["source_row_number"],
        date_fields=["service_date", "reporting_date"],
        datetime_fields=["session_start_datetime", "session_end_datetime", "processed_datetime"],
        numeric_fields=["planned_service_hours", "planned_capacity"],
        boolean_fields=["reduced_session_flag", "cancelled_session_flag", "extended_session_flag", "valid_schedule_flag"],
        categorical_fields={
            "service_type": ["Outpatient Clinic", "Surgical Session", "Diagnostic Session", "Emergency Cover"],
            "schedule_status": ["Scheduled", "Confirmed", "Reduced", "Cancelled", "Extended"],
        },
        parent_relationships=[
            {"parent_dataset": "processed_hospital_master", "parent_field": "hospital_id", "child_field": "hospital_id"},
            {"parent_dataset": "processed_department_master", "parent_field": "department_id", "child_field": "department_id"},
        ],
        downstream_use=["processed_patient_flow_daily"],
        transformation_owner="system",
        implementation_step="2D-3",
    ),
    "processed_patient_flow_daily": _build_schema(
        name="processed_patient_flow_daily",
        source_datasets=["processed_patient_encounters", "processed_patient_queue", "processed_bed_capacity", "processed_service_schedule"],
        purpose="Daily patient-flow and capacity preparation without official KPI outputs.",
        grain="One row per hospital, department and reporting date.",
        primary_key="patient_flow_daily_id",
        required_fields=[
            "patient_flow_daily_id", "hospital_id", "department_id", "reporting_date",
            "reporting_month", "encounter_count", "completed_encounter_count",
            "cancelled_encounter_count", "left_before_service_count",
            "official_wait_eligible_encounter_count", "total_arrival_to_consultation_minutes",
            "queue_arrivals_count", "queue_served_count", "queue_waiting_patient_count",
            "queue_average_wait_minutes", "licensed_beds", "staffed_beds",
            "operational_beds", "occupied_beds", "unavailable_beds", "reserved_beds",
            "beds_above_operational_capacity", "overcapacity_flag",
            "planned_service_session_count", "cancelled_service_session_count",
            "reduced_service_session_count", "extended_service_session_count",
            "processing_run_id", "validation_run_id", "transformation_version",
            "processed_datetime",
        ],
        optional_fields=[],
        date_fields=["reporting_date"],
        datetime_fields=["processed_datetime"],
        numeric_fields=[
            "encounter_count", "completed_encounter_count", "cancelled_encounter_count",
            "left_before_service_count", "official_wait_eligible_encounter_count",
            "total_arrival_to_consultation_minutes", "queue_arrivals_count",
            "queue_served_count", "queue_waiting_patient_count",
            "queue_average_wait_minutes", "licensed_beds", "staffed_beds",
            "operational_beds", "occupied_beds", "unavailable_beds", "reserved_beds",
            "beds_above_operational_capacity", "planned_service_session_count",
            "cancelled_service_session_count", "reduced_service_session_count",
            "extended_service_session_count",
        ],
        boolean_fields=["overcapacity_flag"],
        categorical_fields={},
        parent_relationships=[
            {"parent_dataset": "processed_hospital_master", "parent_field": "hospital_id", "child_field": "hospital_id"},
            {"parent_dataset": "processed_department_master", "parent_field": "department_id", "child_field": "department_id"},
        ],
        downstream_use=["KPI engine (future)"],
        transformation_owner="system",
        implementation_step="2D-3",
    ),

    # D. Patient Experience Datasets (Step 2D-4)
    "processed_patient_complaints": _build_schema(
        name="processed_patient_complaints",
        source_datasets=["patient_complaints"],
        purpose="Validated patient complaint with preparation-level flags and preserved source values.",
        grain="One row per complaint source record.",
        primary_key="complaint_id",
        required_fields=[
            "complaint_id", "source_record_id", "hospital_id", "department_id",
            "encounter_id", "source_file", "source_row_number", "source_checksum",
            "processing_run_id", "processed_datetime", "transformation_version",
            "complaint_date", "complaint_month", "complaint_year", "complaint_date_valid_flag",
            "complaint_channel", "complaint_category", "complaint_subcategory",
            "complaint_severity", "complaint_text_present_flag", "complaint_status_source",
            "resolution_date", "resolution_date_valid_flag", "complaint_resolved_source_flag",
            "complaint_open_source_flag", "complaint_record_valid_flag",
            "complaint_count_eligible_flag", "complaint_daily_aggregation_eligible_flag",
            "complaint_category_supported_flag", "complaint_channel_supported_flag",
            "complaint_severity_supported_flag", "unresolved_rule_flag", "exclusion_reason_code",
        ],
        optional_fields=["hospital_ref_valid_flag", "department_ref_valid_flag"],
        date_fields=["complaint_date", "resolution_date"],
        datetime_fields=["processed_datetime"],
        numeric_fields=["complaint_month", "complaint_year"],
        boolean_fields=[
            "complaint_date_valid_flag", "complaint_text_present_flag",
            "complaint_resolved_source_flag", "complaint_open_source_flag",
            "complaint_record_valid_flag", "complaint_count_eligible_flag",
            "complaint_daily_aggregation_eligible_flag", "complaint_category_supported_flag",
            "complaint_channel_supported_flag", "complaint_severity_supported_flag",
            "unresolved_rule_flag", "hospital_ref_valid_flag", "department_ref_valid_flag",
        ],
        categorical_fields={
            "complaint_channel": ["Formal Letter", "Third Party", "Online Portal", "Email", "Social Media", "Walk-In", "Phone"],
            "complaint_category": ["Facilities", "Waiting Time", "Staff Behaviour", "Other", "Clinical Care", "Safety", "Communication", "Billing"],
            "complaint_severity": ["Low", "Medium", "High", "Critical"],
            "complaint_status_source": ["Escalated", "Received", "Resolved", "Investigating", "Under Review", "Closed"],
        },
        parent_relationships=[
            {"parent_dataset": "processed_hospital_master", "parent_field": "hospital_id", "child_field": "hospital_id"},
            {"parent_dataset": "processed_department_master", "parent_field": "department_id", "child_field": "department_id"},
        ],
        downstream_use=["processed_patient_experience_daily"],
        transformation_owner="system",
        implementation_step="2D-4",
    ),
    "processed_patient_surveys": _build_schema(
        name="processed_patient_surveys",
        source_datasets=["patient_surveys"],
        purpose="Validated patient survey response with preserved scores and preparation-level flags.",
        grain="One row per survey source record.",
        primary_key="survey_id",
        required_fields=[
            "survey_id", "source_record_id", "hospital_id", "department_id",
            "encounter_id", "source_file", "source_row_number", "source_checksum",
            "processing_run_id", "processed_datetime", "transformation_version",
            "survey_date", "survey_month", "survey_year", "survey_date_valid_flag",
            "survey_channel", "survey_type", "response_count",
            "satisfaction_score_source", "satisfaction_score_numeric",
            "satisfaction_scale_min", "satisfaction_scale_max",
            "satisfaction_score_valid_flag", "satisfaction_score_normalised_flag",
            "survey_response_present_flag", "survey_record_valid_flag",
            "survey_aggregation_eligible_flag", "survey_score_eligible_flag",
            "survey_response_count_eligible_flag", "survey_channel_supported_flag",
            "survey_type_supported_flag", "unresolved_rule_flag", "exclusion_reason_code",
        ],
        optional_fields=["hospital_ref_valid_flag", "department_ref_valid_flag"],
        date_fields=["survey_date"],
        datetime_fields=["processed_datetime"],
        numeric_fields=[
            "survey_month", "survey_year", "response_count",
            "satisfaction_score_numeric", "satisfaction_scale_min", "satisfaction_scale_max",
        ],
        boolean_fields=[
            "survey_date_valid_flag", "satisfaction_score_valid_flag",
            "satisfaction_score_normalised_flag", "survey_response_present_flag",
            "survey_record_valid_flag", "survey_aggregation_eligible_flag",
            "survey_score_eligible_flag", "survey_response_count_eligible_flag",
            "survey_channel_supported_flag", "survey_type_supported_flag",
            "unresolved_rule_flag", "hospital_ref_valid_flag", "department_ref_valid_flag",
        ],
        categorical_fields={
            "survey_type": ["Outpatient Satisfaction"],
        },
        parent_relationships=[
            {"parent_dataset": "processed_hospital_master", "parent_field": "hospital_id", "child_field": "hospital_id"},
            {"parent_dataset": "processed_department_master", "parent_field": "department_id", "child_field": "department_id"},
        ],
        downstream_use=["processed_patient_experience_daily"],
        transformation_owner="system",
        implementation_step="2D-4",
    ),
    "processed_patient_experience_daily": _build_schema(
        name="processed_patient_experience_daily",
        source_datasets=["processed_patient_complaints", "processed_patient_surveys"],
        purpose="Daily patient-experience preparation aggregates without official KPI outputs.",
        grain="One row per hospital, department and reporting date.",
        primary_key="patient_experience_daily_id",
        required_fields=[
            "patient_experience_daily_id", "hospital_id", "department_id",
            "reporting_date", "reporting_month", "reporting_year",
            "complaint_record_count", "complaint_valid_record_count",
            "complaint_excluded_record_count", "complaint_high_severity_count",
            "complaint_medium_severity_count", "complaint_low_severity_count",
            "complaint_open_source_count", "complaint_resolved_source_count",
            "complaint_channel_distinct_count", "complaint_category_distinct_count",
            "complaint_count_available_flag", "survey_record_count",
            "survey_response_count_total", "survey_valid_score_record_count",
            "survey_invalid_score_record_count", "survey_score_sum",
            "survey_score_weighted_sum", "survey_score_min", "survey_score_max",
            "survey_score_source_scale_count", "survey_score_available_flag",
            "survey_response_count_available_flag", "complaint_source_present_flag",
            "survey_source_present_flag", "patient_experience_data_complete_flag",
            "unresolved_rule_flag", "processing_run_id", "processed_datetime",
            "transformation_version",
        ],
        optional_fields=[],
        date_fields=["reporting_date"],
        datetime_fields=["processed_datetime"],
        numeric_fields=[
            "reporting_month", "reporting_year", "complaint_record_count",
            "complaint_valid_record_count", "complaint_excluded_record_count",
            "complaint_high_severity_count", "complaint_medium_severity_count",
            "complaint_low_severity_count", "complaint_open_source_count",
            "complaint_resolved_source_count", "complaint_channel_distinct_count",
            "complaint_category_distinct_count", "survey_record_count",
            "survey_response_count_total", "survey_valid_score_record_count",
            "survey_invalid_score_record_count", "survey_score_sum",
            "survey_score_weighted_sum", "survey_score_min", "survey_score_max",
            "survey_score_source_scale_count",
        ],
        boolean_fields=[
            "complaint_count_available_flag", "survey_score_available_flag",
            "survey_response_count_available_flag", "complaint_source_present_flag",
            "survey_source_present_flag", "patient_experience_data_complete_flag",
            "unresolved_rule_flag",
        ],
        categorical_fields={},
        parent_relationships=[
            {"parent_dataset": "processed_hospital_master", "parent_field": "hospital_id", "child_field": "hospital_id"},
            {"parent_dataset": "processed_department_master", "parent_field": "department_id", "child_field": "department_id"},
        ],
        downstream_use=["KPI engine (future)"],
        transformation_owner="system",
        implementation_step="2D-4",
    ),

    # E. Control and Lineage Datasets (Step 2D-5)
    "processing_record_lineage": _build_schema(
        name="processing_record_lineage",
        source_datasets=["*"],
        purpose="Source-to-processed traceability for every record.",
        grain="One row per source-to-processed record relationship.",
        primary_key="lineage_id",
        required_fields=[
            "processing_run_id", "lineage_id", "validation_run_id",
            "source_dataset_name", "source_file_name", "source_primary_key_field",
            "source_primary_key_value", "source_row_number", "processed_dataset_name",
            "processed_primary_key_field", "processed_primary_key_value",
            "transformation_rule_id", "transformation_description", "source_fields_used",
            "processed_fields_created", "exclusion_flag", "exclusion_reason_code",
            "transformation_version", "configuration_version", "processed_datetime",
        ],
        optional_fields=[],
        date_fields=[],
        datetime_fields=["processed_datetime"],
        numeric_fields=["source_row_number"],
        boolean_fields=["exclusion_flag"],
        categorical_fields={},
        parent_relationships=[],
        downstream_use=["Audit", "Investigation"],
        transformation_owner="system",
        implementation_step="2D-5",
    ),
    "processing_exclusion_register": _build_schema(
        name="processing_exclusion_register",
        source_datasets=["*"],
        purpose="Register of all excluded source records with reasons.",
        grain="One row per excluded source record and exclusion reason.",
        primary_key="exclusion_id",
        required_fields=[
            "processing_run_id", "exclusion_id", "source_dataset_name",
            "source_primary_key_field", "source_primary_key_value", "source_row_number",
            "exclusion_reason_code", "exclusion_reason_description", "validation_issue_id",
            "manual_override_id", "exclusion_stage", "excluded_by_rule",
            "reversible_flag", "created_datetime",
        ],
        optional_fields=[],
        date_fields=[],
        datetime_fields=["created_datetime"],
        numeric_fields=["source_row_number"],
        boolean_fields=["reversible_flag"],
        categorical_fields={
            "exclusion_reason_code": [
                "Validation Failure", "Missing Mandatory Data", "Invalid Relationship",
                "Invalid Date or Timestamp", "Invalid Logical Value", "Duplicate Record",
                "Ineligible Business Record", "Unsupported Source Status",
                "Manual Exclusion", "Pending Stakeholder Rule", "Other",
            ],
        },
        parent_relationships=[],
        downstream_use=["Audit", "Investigation"],
        transformation_owner="system",
        implementation_step="2D-5",
    ),
    "processing_run_summary": _build_schema(
        name="processing_run_summary",
        source_datasets=["*"],
        purpose="Summary of every processed dataset per processing run.",
        grain="One row per processed dataset per processing run.",
        primary_key="processing_run_id",
        required_fields=[
            "processing_run_id", "validation_run_id", "source_dataset_name",
            "processed_dataset_name", "source_row_count", "processed_row_count",
            "excluded_row_count", "transformed_field_count", "warning_count",
            "error_count", "dataset_status", "output_file_name", "transformation_version",
            "processed_datetime", "processing_run_status", "processing_allowed_flag",
            "source_checksum", "processed_checksum", "output_schema_version",
        ],
        optional_fields=["notes"],
        date_fields=[],
        datetime_fields=["processed_datetime"],
        numeric_fields=["source_row_count", "processed_row_count", "excluded_row_count", "transformed_field_count", "warning_count", "error_count"],
        boolean_fields=["processing_allowed_flag"],
        categorical_fields={
            "dataset_status": ["Not Processed", "Processed", "Processed with Warnings", "Partially Processed", "Failed", "Blocked"],
            "processing_run_status": ["Not Started", "In Progress", "Passed", "Passed with Warnings", "Failed", "Blocked"],
        },
        parent_relationships=[],
        downstream_use=["Audit", "Run comparison"],
        transformation_owner="system",
        implementation_step="2D-5",
    ),
    "processed_operational_daily": _build_schema(
        name="processed_operational_daily",
        source_datasets=["processed_workforce_daily", "processed_patient_flow_daily", "processed_patient_experience_daily"],
        purpose="Integrated preparation-level operational daily table for Phase 2 KPI input.",
        grain="One row per hospital, department and reporting date.",
        primary_key="operational_daily_id",
        required_fields=[
            "operational_daily_id", "hospital_id", "department_id",
            "reporting_date", "reporting_month", "reporting_year",
            "processing_run_id", "processed_datetime", "transformation_version",
        ],
        optional_fields=[
            "planned_staff_count", "available_staff_count", "present_staff_count",
            "absent_staff_count", "approved_leave_count", "unapproved_absence_count",
            "reassigned_staff_count", "replacement_staff_count",
            "staffing_requirement_available_flag", "workforce_source_present_flag", "workforce_data_complete_flag",
            "encounter_record_count", "completed_encounter_count", "cancelled_encounter_count", "lwbs_encounter_count",
            "queue_record_count", "queue_count_total", "occupied_beds", "operational_beds", "licensed_beds",
            "overcapacity_count", "scheduled_session_count", "cancelled_session_count",
            "reduced_session_count", "extended_session_count",
            "patient_flow_source_present_flag", "patient_flow_data_complete_flag",
            "complaint_record_count", "complaint_valid_record_count",
            "complaint_high_severity_count", "complaint_medium_severity_count", "complaint_low_severity_count",
            "complaint_open_source_count", "complaint_resolved_source_count",
            "survey_record_count", "survey_response_count_total", "survey_valid_score_record_count",
            "survey_score_sum", "survey_score_weighted_sum",
            "patient_experience_source_present_flag", "patient_experience_data_complete_flag",
            "operational_data_complete_flag", "workforce_missing_flag", "patient_flow_missing_flag",
            "patient_experience_missing_flag", "partial_domain_record_flag",
            "cross_domain_reference_valid_flag", "cross_domain_date_valid_flag", "unresolved_rule_flag",
        ],
        date_fields=["reporting_date"],
        datetime_fields=["processed_datetime"],
        numeric_fields=[
            "planned_staff_count", "available_staff_count", "present_staff_count",
            "absent_staff_count", "approved_leave_count", "unapproved_absence_count",
            "reassigned_staff_count", "replacement_staff_count",
            "encounter_record_count", "completed_encounter_count", "cancelled_encounter_count", "lwbs_encounter_count",
            "queue_record_count", "queue_count_total", "occupied_beds", "operational_beds", "licensed_beds",
            "overcapacity_count", "scheduled_session_count", "cancelled_session_count",
            "reduced_session_count", "extended_session_count",
            "complaint_record_count", "complaint_valid_record_count",
            "complaint_high_severity_count", "complaint_medium_severity_count", "complaint_low_severity_count",
            "complaint_open_source_count", "complaint_resolved_source_count",
            "survey_record_count", "survey_response_count_total", "survey_valid_score_record_count",
            "survey_score_sum", "survey_score_weighted_sum",
            "reporting_month", "reporting_year",
        ],
        boolean_fields=[
            "staffing_requirement_available_flag", "workforce_source_present_flag", "workforce_data_complete_flag",
            "patient_flow_source_present_flag", "patient_flow_data_complete_flag",
            "patient_experience_source_present_flag", "patient_experience_data_complete_flag",
            "operational_data_complete_flag", "workforce_missing_flag", "patient_flow_missing_flag",
            "patient_experience_missing_flag", "partial_domain_record_flag",
            "cross_domain_reference_valid_flag", "cross_domain_date_valid_flag", "unresolved_rule_flag",
        ],
        categorical_fields={},
        parent_relationships=[
            {"parent_dataset": "processed_hospital_master", "parent_field": "hospital_id", "child_field": "hospital_id"},
            {"parent_dataset": "processed_department_master", "parent_field": "department_id", "child_field": "department_id"},
        ],
        downstream_use=["Phase 2 KPI engine"],
        transformation_owner="system",
        implementation_step="2D-5",
    ),
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_processed_schema_registry() -> Dict[str, ProcessedSchema]:
    """Return the full processed-schema registry."""
    return dict(_PROCESSED_SCHEMAS)


def get_processed_schema(dataset_name: str) -> Optional[ProcessedSchema]:
    """Return the schema for a single processed dataset, or None."""
    return _PROCESSED_SCHEMAS.get(dataset_name)


def list_processed_datasets() -> List[str]:
    """Return a sorted list of all processed dataset names."""
    return sorted(_PROCESSED_SCHEMAS.keys())


def list_transformation_rules() -> List[Dict[str, Any]]:
    """Return the full transformation-rule registry."""
    return list(TRANSFORMATION_RULES)


def get_transformation_rule(rule_id: str) -> Optional[Dict[str, Any]]:
    """Return a single transformation rule by ID, or None."""
    for rule in TRANSFORMATION_RULES:
        if rule["transformation_rule_id"] == rule_id:
            return dict(rule)
    return None


def get_step_dataset_mapping() -> Dict[str, List[str]]:
    """Return mapping of implementation step to processed dataset names."""
    mapping: Dict[str, List[str]] = {"2D-2": [], "2D-3": [], "2D-4": [], "2D-5": []}
    for name, schema in _PROCESSED_SCHEMAS.items():
        step = schema.get("implementation_step", "")
        if step in mapping:
            mapping[step].append(name)
    return mapping


def get_processed_dataset_dependencies(dataset_name: str) -> List[str]:
    """Return downstream datasets that depend on the given processed dataset."""
    schema = _PROCESSED_SCHEMAS.get(dataset_name)
    if schema is None:
        return []
    return list(schema.get("downstream_use", []))


def validate_processed_schema_registry() -> List[str]:
    """Validate the processed schema registry and return a list of error messages."""
    errors: List[str] = []

    # 1. All 19 datasets exist
    if len(_PROCESSED_SCHEMAS) != 19:
        errors.append(f"Expected 19 processed datasets, found {len(_PROCESSED_SCHEMAS)}")

    # 2. Every primary key exists in its field list
    for name, schema in _PROCESSED_SCHEMAS.items():
        pk = schema.get("primary_key", "")
        all_fields = schema.get("required_fields", []) + schema.get("optional_fields", [])
        if pk and pk not in all_fields:
            errors.append(f"Primary key '{pk}' not found in fields for {name}")

    # 3. Required and optional fields do not overlap
    for name, schema in _PROCESSED_SCHEMAS.items():
        overlap = set(schema.get("required_fields", [])) & set(schema.get("optional_fields", []))
        if overlap:
            errors.append(f"Required and optional fields overlap in {name}: {overlap}")

    # 4. Every data-type field exists
    for name, schema in _PROCESSED_SCHEMAS.items():
        all_fields = set(schema.get("required_fields", []) + schema.get("optional_fields", []))
        for field_type in ["date_fields", "datetime_fields", "numeric_fields", "boolean_fields"]:
            for f in schema.get(field_type, []):
                if f and f not in all_fields:
                    errors.append(f"{field_type} field '{f}' not in field list for {name}")
        for cat_field in schema.get("categorical_fields", {}):
            if cat_field not in all_fields:
                errors.append(f"Categorical field '{cat_field}' not in field list for {name}")

    # 5. Every parent relationship field exists
    for name, schema in _PROCESSED_SCHEMAS.items():
        all_fields = set(schema.get("required_fields", []) + schema.get("optional_fields", []))
        for rel in schema.get("parent_relationships", []):
            child_field = rel.get("child_field", "")
            if child_field and child_field not in all_fields:
                errors.append(f"Parent relationship child_field '{child_field}' not in field list for {name}")

    # 6. Source dataset references exist in approved source registry (or are processed datasets)
    from src.validation_config_loader import load_dataset_schema_registry

    source_registry = load_dataset_schema_registry()
    approved_sources = set(source_registry.keys())
    approved_processed = set(_PROCESSED_SCHEMAS.keys())
    for name, schema in _PROCESSED_SCHEMAS.items():
        for src in schema.get("source_datasets", []):
            if src == "*":
                continue
            if src not in approved_sources and src not in approved_processed:
                errors.append(f"Source dataset '{src}' for {name} not found in approved source or processed registry")

    # 7. Implementation steps are valid
    valid_steps = {"2D-2", "2D-3", "2D-4", "2D-5"}
    for name, schema in _PROCESSED_SCHEMAS.items():
        step = schema.get("implementation_step", "")
        if step not in valid_steps:
            errors.append(f"Invalid implementation_step '{step}' for {name}")

    # 8. Identifiers are unique
    names = list(_PROCESSED_SCHEMAS.keys())
    if len(names) != len(set(names)):
        errors.append("Processed dataset names are not unique")

    # 9. Transformation rule IDs are unique
    rule_ids = [r["transformation_rule_id"] for r in TRANSFORMATION_RULES]
    if len(rule_ids) != len(set(rule_ids)):
        errors.append("Transformation rule IDs are not unique")

    # 10. All transformation rules reference valid target datasets
    for rule in TRANSFORMATION_RULES:
        for target in rule.get("target_datasets", []):
            if target != "*" and target not in approved_processed:
                errors.append(f"Transformation rule {rule['transformation_rule_id']} targets unknown dataset {target}")

    return errors
