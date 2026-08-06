# Sentinel360 Healthcare — Processed Data Dictionary

**Step:** 2D-1  
**Scope:** Schema definitions for all 19 processed datasets. No data generated yet.

---

## Common Fields

The following fields appear across multiple processed datasets where applicable:

| Field Name | Description | Type | Required | Source / Derivation |
|------------|-------------|------|----------|---------------------|
| processing_run_id | Unique identifier for the processing run | string | Yes | System-generated |
| validation_run_id | Reference to the validation run that approved the source | string | Yes | Validation manifest |
| transformation_version | Version of the transformation logic applied | string | Yes | Config |
| processed_datetime | Timestamp when the record was processed | datetime | Yes | System-generated |
| source_primary_key | Original primary key value from source | string | Yes | Source record |
| source_row_number | Original row number in source file | integer | No | Source file |

---

## A. Reference and Master Datasets

### processed_hospital_master

**Purpose:** Standardised effective-dated hospital reference.
**Grain:** One row per valid effective-dated master record.
**Primary Key:** `hospital_id`
**Implementation Step:** 2D-2

| Field | Description | Type | Required | Source / Derivation | Transformation Rule |
|-------|-------------|------|----------|---------------------|---------------------|
| hospital_id | Unique hospital identifier | string | Yes | hospital_master.hospital_id | TR_REF_STANDARDISE_TEXT |
| hospital_name | Hospital name | string | Yes | hospital_master.hospital_name | TR_REF_STANDARDISE_TEXT |
| hospital_type | Type of hospital | string | Yes | hospital_master.hospital_type | TR_REF_STANDARDISE_TEXT |
| active_flag | Whether the record is currently active | boolean | Yes | Derived from effective dates | TR_REF_ACTIVE_FLAG |
| effective_start_date | Start of record validity | date | Yes | hospital_master.effective_from | TR_REF_STANDARDISE_DATE |
| effective_end_date | End of record validity | date | Yes | hospital_master.effective_to | TR_REF_STANDARDISE_DATE |
| source_system | Source system identifier | string | Yes | hospital_master.source_system | TR_REF_STANDARDISE_TEXT |
| source_record_version | Version of source record | integer | Yes | hospital_master.record_version | Direct |
| processing_run_id | Processing run reference | string | Yes | System-generated | TR_CTRL_RUN_SUMMARY |
| validation_run_id | Validation run reference | string | Yes | Validation manifest | TR_CTRL_RUN_SUMMARY |
| transformation_version | Transformation version | string | Yes | Config | Direct |
| processed_datetime | Processing timestamp | datetime | Yes | System-generated | TR_CTRL_RUN_SUMMARY |

---

### processed_department_master

**Purpose:** Standardised effective-dated department reference.
**Grain:** One row per valid effective-dated master record.
**Primary Key:** `department_id`
**Implementation Step:** 2D-2

| Field | Description | Type | Required | Source / Derivation | Transformation Rule |
|-------|-------------|------|----------|---------------------|---------------------|
| department_id | Unique department identifier | string | Yes | department_master.department_id | TR_REF_STANDARDISE_TEXT |
| hospital_id | Parent hospital identifier | string | Yes | department_master.hospital_id | TR_REF_STANDARDISE_TEXT |
| department_name | Department name | string | Yes | department_master.department_name | TR_REF_STANDARDISE_TEXT |
| department_type | Department classification | string | Yes | department_master.department_type | TR_REF_STANDARDISE_TEXT |
| parent_department_id | Parent department identifier | string | No | department_master.parent_department_id | TR_REF_STANDARDISE_TEXT |
| bed_based_flag | Whether department has beds | boolean | Yes | Derived | TR_REF_ACTIVE_FLAG |
| queue_based_flag | Whether department has queues | boolean | Yes | Derived | TR_REF_ACTIVE_FLAG |
| patient_experience_flag | Whether department captures patient experience | boolean | Yes | Derived | TR_REF_ACTIVE_FLAG |
| active_flag | Whether record is active | boolean | Yes | Derived from effective dates | TR_REF_ACTIVE_FLAG |
| effective_start_date | Start of validity | date | Yes | department_master.effective_from | TR_REF_STANDARDISE_DATE |
| effective_end_date | End of validity | date | Yes | department_master.effective_to | TR_REF_STANDARDISE_DATE |
| processing_run_id | Processing run reference | string | Yes | System-generated | TR_CTRL_RUN_SUMMARY |
| validation_run_id | Validation run reference | string | Yes | Validation manifest | TR_CTRL_RUN_SUMMARY |
| transformation_version | Transformation version | string | Yes | Config | Direct |
| processed_datetime | Processing timestamp | datetime | Yes | System-generated | TR_CTRL_RUN_SUMMARY |

---

### processed_staff_role_master

**Purpose:** Standardised effective-dated staff role reference.
**Grain:** One row per valid effective-dated master record.
**Primary Key:** `staff_role_id`
**Implementation Step:** 2D-2

| Field | Description | Type | Required | Source / Derivation | Transformation Rule |
|-------|-------------|------|----------|---------------------|---------------------|
| staff_role_id | Unique role identifier | string | Yes | staff_role_master.role_id | TR_REF_STANDARDISE_TEXT |
| staff_role_name | Role name | string | Yes | staff_role_master.role_name | TR_REF_STANDARDISE_TEXT |
| staff_category | Broad staff category | string | Yes | staff_role_master.staff_category | TR_REF_STANDARDISE_TEXT |
| clinical_role_flag | Whether role is clinical | boolean | Yes | Derived | TR_REF_ACTIVE_FLAG |
| patient_facing_flag | Whether role is patient-facing | boolean | Yes | Derived | TR_REF_ACTIVE_FLAG |
| active_flag | Whether record is active | boolean | Yes | Derived from effective dates | TR_REF_ACTIVE_FLAG |
| effective_start_date | Start of validity | date | Yes | staff_role_master.effective_from | TR_REF_STANDARDISE_DATE |
| effective_end_date | End of validity | date | Yes | staff_role_master.effective_to | TR_REF_STANDARDISE_DATE |
| processing_run_id | Processing run reference | string | Yes | System-generated | TR_CTRL_RUN_SUMMARY |
| validation_run_id | Validation run reference | string | Yes | Validation manifest | TR_CTRL_RUN_SUMMARY |
| transformation_version | Transformation version | string | Yes | Config | Direct |
| processed_datetime | Processing timestamp | datetime | Yes | System-generated | TR_CTRL_RUN_SUMMARY |

---

### processed_staff_master

**Purpose:** Standardised effective-dated staff reference.
**Grain:** One row per valid effective-dated master record.
**Primary Key:** `staff_id`
**Implementation Step:** 2D-2

| Field | Description | Type | Required | Source / Derivation | Transformation Rule |
|-------|-------------|------|----------|---------------------|---------------------|
| staff_id | Unique staff identifier | string | Yes | staff_master.staff_id | TR_REF_STANDARDISE_TEXT |
| hospital_id | Home hospital identifier | string | Yes | staff_master.hospital_id | TR_REF_STANDARDISE_TEXT |
| home_department_id | Home department identifier | string | Yes | staff_master.department_id | TR_REF_STANDARDISE_TEXT |
| staff_role_id | Role identifier | string | Yes | staff_master.role_id | TR_REF_STANDARDISE_TEXT |
| staff_category | Broad staff category | string | Yes | staff_master.staff_category | TR_REF_STANDARDISE_TEXT |
| employment_type | Employment type | string | Yes | staff_master.employment_type | TR_REF_STANDARDISE_TEXT |
| fte_value | Full-time equivalent | decimal | Yes | staff_master.fte_value | Direct |
| employment_start_date | Start of employment | date | Yes | staff_master.employment_start_date | TR_REF_STANDARDISE_DATE |
| employment_end_date | End of employment | date | No | staff_master.employment_end_date | TR_REF_STANDARDISE_DATE |
| active_flag | Whether record is active | boolean | Yes | Derived from effective dates | TR_REF_ACTIVE_FLAG |
| processing_run_id | Processing run reference | string | Yes | System-generated | TR_CTRL_RUN_SUMMARY |
| validation_run_id | Validation run reference | string | Yes | Validation manifest | TR_CTRL_RUN_SUMMARY |
| transformation_version | Transformation version | string | Yes | Config | Direct |
| processed_datetime | Processing timestamp | datetime | Yes | System-generated | TR_CTRL_RUN_SUMMARY |

---

## B. Workforce Datasets

### processed_staff_roster

**Purpose:** Standardised staff roster with shift and assignment detail.
**Grain:** One row per staff, roster date, shift, department and assignment.
**Primary Key:** `roster_record_id`
**Implementation Step:** 2D-2

| Field | Description | Type | Required | Source / Derivation | Transformation Rule |
|-------|-------------|------|----------|---------------------|---------------------|
| roster_record_id | Unique roster record identifier | string | Yes | staff_roster.roster_id | TR_REF_STANDARDISE_TEXT |
| staff_id | Staff identifier | string | Yes | staff_roster.staff_id | TR_REF_STANDARDISE_TEXT |
| hospital_id | Hospital identifier | string | Yes | staff_roster.hospital_id | TR_REF_STANDARDISE_TEXT |
| department_id | Department identifier | string | Yes | staff_roster.department_id | TR_REF_STANDARDISE_TEXT |
| staff_role_id | Role identifier | string | Yes | staff_roster.role_id | TR_REF_STANDARDISE_TEXT |
| roster_date | Date of roster | date | Yes | staff_roster.roster_date | TR_REF_STANDARDISE_DATE |
| reporting_date | Normalised reporting date | date | Yes | Derived from roster_date | TR_REF_STANDARDISE_DATE |
| reporting_month | Month of reporting | string | Yes | Derived from roster_date | TR_REF_STANDARDISE_DATE |
| shift_code | Shift code | string | Yes | staff_roster.shift_code | TR_REF_STANDARDISE_TEXT |
| planned_start_datetime | Planned shift start | datetime | Yes | Derived from roster_date and shift | TR_WF_ROSTER_DATETIME |
| planned_end_datetime | Planned shift end | datetime | Yes | Derived from roster_date and shift | TR_WF_OVERNIGHT_SHIFT |
| planned_hours | Planned shift hours | decimal | Yes | staff_roster.planned_hours | Direct |
| assignment_status | Assignment status | string | Yes | staff_roster.status | TR_REF_STANDARDISE_TEXT |
| original_department_id | Original department before reassignment | string | Yes | staff_roster.department_id | TR_REF_STANDARDISE_TEXT |
| reassigned_department_id | Destination department if reassigned | string | No | Derived | TR_WF_REASSIGNMENT |
| cancelled_flag | Whether assignment is cancelled | boolean | Yes | Derived | TR_REF_ACTIVE_FLAG |
| valid_assignment_flag | Whether assignment passes validation | boolean | Yes | Derived | TR_REF_ACTIVE_FLAG |
| source_primary_key | Source primary key | string | Yes | staff_roster.roster_id | Direct |
| processing_run_id | Processing run reference | string | Yes | System-generated | TR_CTRL_RUN_SUMMARY |
| validation_run_id | Validation run reference | string | Yes | Validation manifest | TR_CTRL_RUN_SUMMARY |
| transformation_version | Transformation version | string | Yes | Config | Direct |
| processed_datetime | Processing timestamp | datetime | Yes | System-generated | TR_CTRL_RUN_SUMMARY |

---

### processed_staff_attendance

**Purpose:** Standardised staff attendance with hours, status and eligibility flags.
**Grain:** One row per staff, attendance date, shift and actual assignment.
**Primary Key:** `attendance_record_id`
**Implementation Step:** 2D-2

| Field | Description | Type | Required | Source / Derivation | Transformation Rule |
|-------|-------------|------|----------|---------------------|---------------------|
| attendance_record_id | Unique attendance record identifier | string | Yes | staff_attendance.attendance_id | TR_REF_STANDARDISE_TEXT |
| roster_record_id | Linked roster record | string | No | staff_attendance.roster_id | TR_REF_STANDARDISE_TEXT |
| staff_id | Staff identifier | string | Yes | staff_attendance.staff_id | TR_REF_STANDARDISE_TEXT |
| hospital_id | Hospital identifier | string | Yes | staff_attendance.hospital_id | TR_REF_STANDARDISE_TEXT |
| home_department_id | Home department identifier | string | Yes | staff_attendance.department_id | TR_REF_STANDARDISE_TEXT |
| actual_department_id | Actual department worked | string | Yes | Derived | TR_WF_DEPARTMENT_ATTRIBUTION |
| staff_role_id | Role identifier | string | Yes | staff_attendance.role_id | TR_REF_STANDARDISE_TEXT |
| attendance_date | Date of attendance | date | Yes | staff_attendance.attendance_date | TR_REF_STANDARDISE_DATE |
| reporting_date | Normalised reporting date | date | Yes | Derived from attendance_date | TR_REF_STANDARDISE_DATE |
| reporting_month | Month of reporting | string | Yes | Derived from attendance_date | TR_REF_STANDARDISE_DATE |
| shift_code | Shift code | string | Yes | staff_attendance.shift_code | TR_REF_STANDARDISE_TEXT |
| attendance_status | Standardised attendance status | string | Yes | staff_attendance.status | TR_WF_ATTENDANCE_MAPPING |
| absence_category | Absence category | string | No | Derived | TR_WF_ABSENTEEISM_ELIGIBILITY |
| scheduled_hours | Scheduled hours for the shift | decimal | No | Derived from roster | TR_WF_LOST_HOURS |
| actual_hours_worked | Actual hours worked | decimal | No | staff_attendance.actual_hours | TR_WF_ACTUAL_HOURS |
| lost_scheduled_hours | Lost hours due to absence | decimal | No | Derived | TR_WF_LOST_HOURS |
| availability_contribution | Hours contributing to availability | decimal | No | Derived | TR_WF_AVAILABILITY_CONTRIBUTION |
| absenteeism_eligible_flag | Whether record is eligible for absenteeism | boolean | Yes | Derived | TR_WF_ABSENTEEISM_ELIGIBILITY |
| absenteeism_hours | Hours counted as absenteeism | decimal | No | Derived | TR_WF_ABSENTEEISM_ELIGIBILITY |
| planned_absence_flag | Whether absence was planned | boolean | Yes | Derived | TR_WF_ABSENTEEISM_ELIGIBILITY |
| replacement_staff_id | Replacement staff identifier | string | No | staff_attendance.replacement_staff_id | TR_WF_REPLACEMENT_REFERENCE |
| reassigned_flag | Whether staff was reassigned | boolean | Yes | Derived | TR_WF_REASSIGNMENT |
| missing_attendance_flag | Whether attendance was missing | boolean | Yes | Derived | TR_WF_MISSING_UNKNOWN |
| unknown_attendance_flag | Whether attendance status is unknown | boolean | Yes | Derived | TR_WF_MISSING_UNKNOWN |
| valid_attendance_flag | Whether record passes validation | boolean | Yes | Derived | TR_REF_ACTIVE_FLAG |
| source_primary_key | Source primary key | string | Yes | staff_attendance.attendance_id | Direct |
| processing_run_id | Processing run reference | string | Yes | System-generated | TR_CTRL_RUN_SUMMARY |
| validation_run_id | Validation run reference | string | Yes | Validation manifest | TR_CTRL_RUN_SUMMARY |
| transformation_version | Transformation version | string | Yes | Config | Direct |
| processed_datetime | Processing timestamp | datetime | Yes | System-generated | TR_CTRL_RUN_SUMMARY |

---

### processed_staffing_requirement

**Purpose:** Standardised staffing requirement by department, date, shift and role.
**Grain:** One row per hospital, department, date, shift and staff role.
**Primary Key:** `staffing_requirement_id`
**Implementation Step:** 2D-2

| Field | Description | Type | Required | Source / Derivation | Transformation Rule |
|-------|-------------|------|----------|---------------------|---------------------|
| staffing_requirement_id | Unique requirement identifier | string | Yes | staffing_requirement.requirement_id | TR_REF_STANDARDISE_TEXT |
| hospital_id | Hospital identifier | string | Yes | staffing_requirement.hospital_id | TR_REF_STANDARDISE_TEXT |
| department_id | Department identifier | string | Yes | staffing_requirement.department_id | TR_REF_STANDARDISE_TEXT |
| staff_role_id | Role identifier | string | Yes | staffing_requirement.role_id | TR_REF_STANDARDISE_TEXT |
| requirement_date | Date of requirement | date | Yes | staffing_requirement.requirement_date | TR_REF_STANDARDISE_DATE |
| reporting_date | Normalised reporting date | date | Yes | Derived from requirement_date | TR_REF_STANDARDISE_DATE |
| reporting_month | Month of reporting | string | Yes | Derived from requirement_date | TR_REF_STANDARDISE_DATE |
| shift_code | Shift code | string | Yes | staffing_requirement.shift_code | TR_REF_STANDARDISE_TEXT |
| required_staff_count | Required number of staff | integer | Yes | staffing_requirement.required_staff_count | Direct |
| required_staff_hours | Required staff hours | decimal | Yes | staffing_requirement.required_hours | Direct |
| requirement_status | Status of requirement | string | Yes | Derived | TR_REF_ACTIVE_FLAG |
| valid_requirement_flag | Whether requirement passes validation | boolean | Yes | Derived | TR_REF_ACTIVE_FLAG |
| source_primary_key | Source primary key | string | Yes | staffing_requirement.requirement_id | Direct |
| processing_run_id | Processing run reference | string | Yes | System-generated | TR_CTRL_RUN_SUMMARY |
| validation_run_id | Validation run reference | string | Yes | Validation manifest | TR_CTRL_RUN_SUMMARY |
| transformation_version | Transformation version | string | Yes | Config | Direct |
| processed_datetime | Processing timestamp | datetime | Yes | System-generated | TR_CTRL_RUN_SUMMARY |

---

### processed_workforce_daily

**Purpose:** Daily workforce analytical preparation without official KPI percentages.
**Grain:** One row per hospital, department, reporting date and staff role.
**Primary Key:** `workforce_daily_id`
**Implementation Step:** 2D-2

| Field | Description | Type | Required | Source / Derivation | Transformation Rule |
|-------|-------------|------|----------|---------------------|---------------------|
| workforce_daily_id | Unique daily record identifier | string | Yes | System-generated | TR_WF_DAILY_AGGREGATION |
| hospital_id | Hospital identifier | string | Yes | processed_staff_attendance.hospital_id | TR_WF_DAILY_AGGREGATION |
| department_id | Department identifier | string | Yes | processed_staff_attendance.actual_department_id | TR_WF_DAILY_AGGREGATION |
| staff_role_id | Role identifier | string | Yes | processed_staff_attendance.staff_role_id | TR_WF_DAILY_AGGREGATION |
| reporting_date | Reporting date | date | Yes | processed_staff_attendance.reporting_date | TR_WF_DAILY_AGGREGATION |
| reporting_month | Month of reporting | string | Yes | Derived from reporting_date | TR_WF_DAILY_AGGREGATION |
| rostered_staff_count | Count of rostered staff | integer | Yes | Derived from processed_staff_roster | TR_WF_DAILY_AGGREGATION |
| rostered_hours | Sum of planned roster hours | decimal | Yes | Derived from processed_staff_roster | TR_WF_DAILY_AGGREGATION |
| required_staff_count | Required staff count | integer | Yes | Derived from processed_staffing_requirement | TR_WF_DAILY_AGGREGATION |
| required_staff_hours | Required staff hours | decimal | Yes | Derived from processed_staffing_requirement | TR_WF_DAILY_AGGREGATION |
| verified_available_staff_count | Count of verified available staff | integer | Yes | Derived from processed_staff_attendance | TR_WF_DAILY_AGGREGATION |
| verified_available_hours | Sum of available hours | decimal | Yes | Derived from processed_staff_attendance | TR_WF_DAILY_AGGREGATION |
| absent_event_count | Count of absent events | integer | Yes | Derived from processed_staff_attendance | TR_WF_DAILY_AGGREGATION |
| absent_hours | Sum of absent hours | decimal | Yes | Derived from processed_staff_attendance | TR_WF_DAILY_AGGREGATION |
| planned_leave_event_count | Count of planned leave events | integer | Yes | Derived from processed_staff_attendance | TR_WF_DAILY_AGGREGATION |
| planned_leave_hours | Sum of planned leave hours | decimal | Yes | Derived from processed_staff_attendance | TR_WF_DAILY_AGGREGATION |
| partial_attendance_event_count | Count of partial attendance events | integer | Yes | Derived from processed_staff_attendance | TR_WF_DAILY_AGGREGATION |
| late_attendance_event_count | Count of late attendance events | integer | Yes | Derived from processed_staff_attendance | TR_WF_DAILY_AGGREGATION |
| reassigned_in_count | Count of staff reassigned in | integer | Yes | Derived from processed_staff_attendance | TR_WF_DAILY_AGGREGATION |
| reassigned_out_count | Count of staff reassigned out | integer | Yes | Derived from processed_staff_attendance | TR_WF_DAILY_AGGREGATION |
| replacement_staff_count | Count of replacement staff | integer | Yes | Derived from processed_staff_attendance | TR_WF_DAILY_AGGREGATION |
| missing_attendance_count | Count of missing attendance records | integer | Yes | Derived from processed_staff_attendance | TR_WF_DAILY_AGGREGATION |
| unknown_attendance_count | Count of unknown attendance records | integer | Yes | Derived from processed_staff_attendance | TR_WF_DAILY_AGGREGATION |
| eligible_record_count | Count of eligible source records | integer | Yes | Derived | TR_WF_DAILY_AGGREGATION |
| excluded_record_count | Count of excluded source records | integer | Yes | Derived | TR_WF_DAILY_AGGREGATION |
| data_completeness_count | Count of complete records | integer | Yes | Derived | TR_WF_DAILY_AGGREGATION |
| processing_run_id | Processing run reference | string | Yes | System-generated | TR_CTRL_RUN_SUMMARY |
| validation_run_id | Validation run reference | string | Yes | Validation manifest | TR_CTRL_RUN_SUMMARY |
| transformation_version | Transformation version | string | Yes | Config | Direct |
| processed_datetime | Processing timestamp | datetime | Yes | System-generated | TR_CTRL_RUN_SUMMARY |

**Note:** `staffing_level_percent` and `absenteeism_rate_percent` are NOT present. These are calculated by the downstream KPI engine.

---

## C. Patient Flow and Capacity Datasets

### processed_patient_encounters

**Purpose:** Standardised patient encounter with timestamps and wait eligibility.
**Grain:** One row per encounter.
**Primary Key:** `encounter_id`
**Implementation Step:** 2D-3

| Field | Description | Type | Required | Source / Derivation | Transformation Rule |
|-------|-------------|------|----------|---------------------|---------------------|
| encounter_id | Unique encounter identifier | string | Yes | patient_encounters.encounter_id | TR_REF_STANDARDISE_TEXT |
| hospital_id | Hospital identifier | string | Yes | patient_encounters.hospital_id | TR_REF_STANDARDISE_TEXT |
| department_id | Department identifier | string | Yes | patient_encounters.department_id | TR_REF_STANDARDISE_TEXT |
| encounter_date | Date of encounter | date | Yes | patient_encounters.encounter_date | TR_REF_STANDARDISE_DATE |
| reporting_date | Normalised reporting date | date | Yes | Derived from encounter_date | TR_REF_STANDARDISE_DATE |
| reporting_month | Month of reporting | string | Yes | Derived from encounter_date | TR_REF_STANDARDISE_DATE |
| encounter_type | Type of encounter | string | Yes | patient_encounters.encounter_type | TR_REF_STANDARDISE_TEXT |
| arrival_datetime | Arrival timestamp | datetime | Yes | patient_encounters.arrival_datetime | TR_PF_TIMESTAMP_PARSE |
| triage_datetime | Triage timestamp | datetime | No | patient_encounters.triage_datetime | TR_PF_TIMESTAMP_PARSE |
| consultation_start_datetime | Consultation start timestamp | datetime | No | patient_encounters.service_start_datetime | TR_PF_TIMESTAMP_PARSE |
| service_end_datetime | Service end timestamp | datetime | No | patient_encounters.service_end_datetime | TR_PF_TIMESTAMP_PARSE |
| disposition_status | Final disposition | string | Yes | patient_encounters.status | TR_REF_STANDARDISE_TEXT |
| cancelled_flag | Whether encounter was cancelled | boolean | Yes | Derived | TR_PF_WAIT_ELIGIBILITY |
| left_before_service_flag | Whether patient left before service | boolean | Yes | Derived | TR_PF_WAIT_ELIGIBILITY |
| completed_service_flag | Whether service was completed | boolean | Yes | Derived | TR_PF_WAIT_ELIGIBILITY |
| arrival_to_triage_minutes | Minutes from arrival to triage | decimal | No | Derived | TR_PF_WAIT_INTERVALS |
| arrival_to_consultation_minutes | Minutes from arrival to consultation | decimal | No | Derived | TR_PF_WAIT_INTERVALS |
| triage_to_consultation_minutes | Minutes from triage to consultation | decimal | No | Derived | TR_PF_WAIT_INTERVALS |
| consultation_to_service_end_minutes | Minutes from consultation to end | decimal | No | Derived | TR_PF_WAIT_INTERVALS |
| official_wait_stage_eligible_flag | Eligible for official wait KPI | boolean | Yes | Derived | TR_PF_WAIT_ELIGIBILITY |
| encounter_wait_eligible_flag | Eligible for encounter wait | boolean | Yes | Derived | TR_PF_WAIT_ELIGIBILITY |
| exclusion_reason_code | Reason for exclusion if applicable | string | No | Derived | TR_CTRL_EXCLUSION |
| source_primary_key | Source primary key | string | Yes | patient_encounters.encounter_id | Direct |
| processing_run_id | Processing run reference | string | Yes | System-generated | TR_CTRL_RUN_SUMMARY |
| validation_run_id | Validation run reference | string | Yes | Validation manifest | TR_CTRL_RUN_SUMMARY |
| transformation_version | Transformation version | string | Yes | Config | Direct |
| processed_datetime | Processing timestamp | datetime | Yes | System-generated | TR_CTRL_RUN_SUMMARY |

---

### processed_patient_queue

**Purpose:** Standardised patient queue by stage and date.
**Grain:** One row per hospital, department, queue date and queue stage.
**Primary Key:** `queue_record_id`
**Implementation Step:** 2D-3

| Field | Description | Type | Required | Source / Derivation | Transformation Rule |
|-------|-------------|------|----------|---------------------|---------------------|
| queue_record_id | Unique queue record identifier | string | Yes | patient_queue_records.queue_id | TR_REF_STANDARDISE_TEXT |
| hospital_id | Hospital identifier | string | Yes | patient_queue_records.hospital_id | TR_REF_STANDARDISE_TEXT |
| department_id | Department identifier | string | Yes | patient_queue_records.department_id | TR_REF_STANDARDISE_TEXT |
| queue_date | Date of queue record | date | Yes | patient_queue_records.queue_date | TR_REF_STANDARDISE_DATE |
| reporting_date | Normalised reporting date | date | Yes | Derived from queue_date | TR_REF_STANDARDISE_DATE |
| reporting_month | Month of reporting | string | Yes | Derived from queue_date | TR_REF_STANDARDISE_DATE |
| queue_stage | Stage of queue | string | Yes | patient_queue_records.queue_type | TR_PF_QUEUE_STANDARDISATION |
| arrivals_count | Number of arrivals | integer | Yes | patient_queue_records.arrivals_count | Direct |
| served_count | Number served | integer | Yes | patient_queue_records.served_count | Direct |
| waiting_patient_count | Patients waiting | integer | Yes | patient_queue_records.waiting_count | Direct |
| average_wait_minutes | Average wait time | decimal | Yes | patient_queue_records.avg_wait_minutes | Direct |
| median_wait_minutes | Median wait time | decimal | Yes | patient_queue_records.median_wait_minutes | Direct |
| maximum_wait_minutes | Maximum wait time | decimal | Yes | patient_queue_records.max_wait_minutes | Direct |
| summary_source_flag | Whether record is from summary source | boolean | Yes | Derived | TR_PF_QUEUE_STANDARDISATION |
| encounter_derived_flag | Whether record is derived from encounters | boolean | Yes | Derived | TR_PF_QUEUE_STANDARDISATION |
| valid_queue_record_flag | Whether record passes validation | boolean | Yes | Derived | TR_REF_ACTIVE_FLAG |
| source_primary_key | Source primary key | string | Yes | patient_queue_records.queue_id | Direct |
| processing_run_id | Processing run reference | string | Yes | System-generated | TR_CTRL_RUN_SUMMARY |
| validation_run_id | Validation run reference | string | Yes | Validation manifest | TR_CTRL_RUN_SUMMARY |
| transformation_version | Transformation version | string | Yes | Config | Direct |
| processed_datetime | Processing timestamp | datetime | Yes | System-generated | TR_CTRL_RUN_SUMMARY |

---

### processed_bed_capacity

**Purpose:** Standardised bed capacity with overcapacity detection.
**Grain:** One row per hospital, department and reporting date.
**Primary Key:** `bed_capacity_record_id`
**Implementation Step:** 2D-3

| Field | Description | Type | Required | Source / Derivation | Transformation Rule |
|-------|-------------|------|----------|---------------------|---------------------|
| bed_capacity_record_id | Unique record identifier | string | Yes | bed_capacity_records.record_id | TR_REF_STANDARDISE_TEXT |
| hospital_id | Hospital identifier | string | Yes | bed_capacity_records.hospital_id | TR_REF_STANDARDISE_TEXT |
| department_id | Department identifier | string | Yes | bed_capacity_records.department_id | TR_REF_STANDARDISE_TEXT |
| reporting_date | Reporting date | date | Yes | bed_capacity_records.record_date | TR_REF_STANDARDISE_DATE |
| reporting_month | Month of reporting | string | Yes | Derived from reporting_date | TR_REF_STANDARDISE_DATE |
| licensed_beds | Licensed bed count | integer | Yes | bed_capacity_records.bed_licensed | Direct |
| staffed_beds | Staffed bed count | integer | Yes | bed_capacity_records.bed_staffed | Direct |
| operational_beds | Operational bed count | integer | Yes | bed_capacity_records.bed_operational | Direct |
| occupied_beds | Occupied bed count | integer | Yes | bed_capacity_records.bed_occupied | Direct |
| unavailable_beds | Unavailable bed count | integer | Yes | bed_capacity_records.bed_unavailable | Direct |
| reserved_beds | Reserved bed count | integer | Yes | bed_capacity_records.bed_reserved | Direct |
| beds_above_operational_capacity | Beds above operational capacity | integer | Yes | Derived | TR_PF_OVERCAPACITY |
| overcapacity_flag | Whether overcapacity exists | boolean | Yes | Derived | TR_PF_OVERCAPACITY |
| overcapacity_exception_flag | Whether exception is approved | boolean | Yes | Derived from exception_flag | TR_PF_OVERCAPACITY |
| overcapacity_reason | Reason for overcapacity | string | No | bed_capacity_records.exception_reason | TR_PF_OVERCAPACITY |
| valid_bed_record_flag | Whether record passes validation | boolean | Yes | Derived | TR_REF_ACTIVE_FLAG |
| source_primary_key | Source primary key | string | Yes | bed_capacity_records.record_id | Direct |
| processing_run_id | Processing run reference | string | Yes | System-generated | TR_CTRL_RUN_SUMMARY |
| validation_run_id | Validation run reference | string | Yes | Validation manifest | TR_CTRL_RUN_SUMMARY |
| transformation_version | Transformation version | string | Yes | Config | Direct |
| processed_datetime | Processing timestamp | datetime | Yes | System-generated | TR_CTRL_RUN_SUMMARY |

**Note:** `bed_occupancy_rate_kpi` is NOT present. Calculated downstream.

---

### processed_service_schedule

**Purpose:** Standardised service schedule with session flags.
**Grain:** One row per service session or approved source schedule record.
**Primary Key:** `service_schedule_id`
**Implementation Step:** 2D-3

| Field | Description | Type | Required | Source / Derivation | Transformation Rule |
|-------|-------------|------|----------|---------------------|---------------------|
| service_schedule_id | Unique schedule identifier | string | Yes | service_schedule.schedule_id | TR_REF_STANDARDISE_TEXT |
| hospital_id | Hospital identifier | string | Yes | service_schedule.hospital_id | TR_REF_STANDARDISE_TEXT |
| department_id | Department identifier | string | Yes | service_schedule.department_id | TR_REF_STANDARDISE_TEXT |
| service_date | Date of service | date | Yes | service_schedule.service_date | TR_REF_STANDARDISE_DATE |
| reporting_date | Normalised reporting date | date | Yes | Derived from service_date | TR_REF_STANDARDISE_DATE |
| reporting_month | Month of reporting | string | Yes | Derived from service_date | TR_REF_STANDARDISE_DATE |
| service_type | Type of service | string | Yes | Derived | TR_PF_SCHEDULE_STANDARDISATION |
| session_start_datetime | Session start timestamp | datetime | Yes | Derived from date and time | TR_PF_SCHEDULE_STANDARDISATION |
| session_end_datetime | Session end timestamp | datetime | Yes | Derived from date and time | TR_PF_SCHEDULE_STANDARDISATION |
| planned_service_hours | Planned hours of service | decimal | Yes | service_schedule.planned_hours | Direct |
| planned_capacity | Planned capacity | integer | Yes | service_schedule.planned_capacity | Direct |
| schedule_status | Status of schedule | string | Yes | service_schedule.schedule_status | TR_REF_STANDARDISE_TEXT |
| reduced_session_flag | Whether session is reduced | boolean | Yes | Derived | TR_PF_SCHEDULE_STANDARDISATION |
| cancelled_session_flag | Whether session is cancelled | boolean | Yes | Derived | TR_PF_SCHEDULE_STANDARDISATION |
| extended_session_flag | Whether session is extended | boolean | Yes | Derived | TR_PF_SCHEDULE_STANDARDISATION |
| valid_schedule_flag | Whether record passes validation | boolean | Yes | Derived | TR_REF_ACTIVE_FLAG |
| source_primary_key | Source primary key | string | Yes | service_schedule.schedule_id | Direct |
| processing_run_id | Processing run reference | string | Yes | System-generated | TR_CTRL_RUN_SUMMARY |
| validation_run_id | Validation run reference | string | Yes | Validation manifest | TR_CTRL_RUN_SUMMARY |
| transformation_version | Transformation version | string | Yes | Config | Direct |
| processed_datetime | Processing timestamp | datetime | Yes | System-generated | TR_CTRL_RUN_SUMMARY |

---

### processed_patient_flow_daily

**Purpose:** Daily patient-flow and capacity preparation without official KPI outputs.
**Grain:** One row per hospital, department and reporting date.
**Primary Key:** `patient_flow_daily_id`
**Implementation Step:** 2D-3

| Field | Description | Type | Required | Source / Derivation | Transformation Rule |
|-------|-------------|------|----------|---------------------|---------------------|
| patient_flow_daily_id | Unique daily record identifier | string | Yes | System-generated | TR_PF_DAILY_AGGREGATION |
| hospital_id | Hospital identifier | string | Yes | processed_patient_encounters.hospital_id | TR_PF_DAILY_AGGREGATION |
| department_id | Department identifier | string | Yes | processed_patient_encounters.department_id | TR_PF_DAILY_AGGREGATION |
| reporting_date | Reporting date | date | Yes | processed_patient_encounters.reporting_date | TR_PF_DAILY_AGGREGATION |
| reporting_month | Month of reporting | string | Yes | Derived from reporting_date | TR_PF_DAILY_AGGREGATION |
| encounter_count | Total encounters | integer | Yes | Derived from processed_patient_encounters | TR_PF_DAILY_AGGREGATION |
| completed_encounter_count | Completed encounters | integer | Yes | Derived from processed_patient_encounters | TR_PF_DAILY_AGGREGATION |
| cancelled_encounter_count | Cancelled encounters | integer | Yes | Derived from processed_patient_encounters | TR_PF_DAILY_AGGREGATION |
| left_before_service_count | Left before service count | integer | Yes | Derived from processed_patient_encounters | TR_PF_DAILY_AGGREGATION |
| official_wait_eligible_encounter_count | Eligible for wait KPI | integer | Yes | Derived from processed_patient_encounters | TR_PF_DAILY_AGGREGATION |
| total_arrival_to_consultation_minutes | Sum of arrival-to-consultation minutes | decimal | Yes | Derived from processed_patient_encounters | TR_PF_DAILY_AGGREGATION |
| queue_arrivals_count | Queue arrivals | integer | Yes | Derived from processed_patient_queue | TR_PF_DAILY_AGGREGATION |
| queue_served_count | Queue served | integer | Yes | Derived from processed_patient_queue | TR_PF_DAILY_AGGREGATION |
| queue_waiting_patient_count | Queue waiting patients | integer | Yes | Derived from processed_patient_queue | TR_PF_DAILY_AGGREGATION |
| queue_average_wait_minutes | Queue average wait | decimal | Yes | Derived from processed_patient_queue | TR_PF_DAILY_AGGREGATION |
| licensed_beds | Licensed beds | integer | Yes | Derived from processed_bed_capacity | TR_PF_DAILY_AGGREGATION |
| staffed_beds | Staffed beds | integer | Yes | Derived from processed_bed_capacity | TR_PF_DAILY_AGGREGATION |
| operational_beds | Operational beds | integer | Yes | Derived from processed_bed_capacity | TR_PF_DAILY_AGGREGATION |
| occupied_beds | Occupied beds | integer | Yes | Derived from processed_bed_capacity | TR_PF_DAILY_AGGREGATION |
| unavailable_beds | Unavailable beds | integer | Yes | Derived from processed_bed_capacity | TR_PF_DAILY_AGGREGATION |
| reserved_beds | Reserved beds | integer | Yes | Derived from processed_bed_capacity | TR_PF_DAILY_AGGREGATION |
| beds_above_operational_capacity | Beds above capacity | integer | Yes | Derived from processed_bed_capacity | TR_PF_DAILY_AGGREGATION |
| overcapacity_flag | Overcapacity flag | boolean | Yes | Derived from processed_bed_capacity | TR_PF_DAILY_AGGREGATION |
| planned_service_session_count | Planned sessions | integer | Yes | Derived from processed_service_schedule | TR_PF_DAILY_AGGREGATION |
| cancelled_service_session_count | Cancelled sessions | integer | Yes | Derived from processed_service_schedule | TR_PF_DAILY_AGGREGATION |
| reduced_service_session_count | Reduced sessions | integer | Yes | Derived from processed_service_schedule | TR_PF_DAILY_AGGREGATION |
| extended_service_session_count | Extended sessions | integer | Yes | Derived from processed_service_schedule | TR_PF_DAILY_AGGREGATION |
| processing_run_id | Processing run reference | string | Yes | System-generated | TR_CTRL_RUN_SUMMARY |
| validation_run_id | Validation run reference | string | Yes | Validation manifest | TR_CTRL_RUN_SUMMARY |
| transformation_version | Transformation version | string | Yes | Config | Direct |
| processed_datetime | Processing timestamp | datetime | Yes | System-generated | TR_CTRL_RUN_SUMMARY |

**Note:** `average_patient_waiting_time_kpi` and `bed_occupancy_rate_kpi` are NOT present.

---

## D. Patient Experience Datasets

### processed_patient_complaints

**Purpose:** Standardised patient complaint with eligibility and classification flags.
**Grain:** One row per valid complaint event.
**Primary Key:** `complaint_id`
**Implementation Step:** 2D-4

| Field | Description | Type | Required | Source / Derivation | Transformation Rule |
|-------|-------------|------|----------|---------------------|---------------------|
| complaint_id | Unique complaint identifier | string | Yes | patient_complaints.complaint_id | TR_REF_STANDARDISE_TEXT |
| hospital_id | Hospital identifier | string | Yes | patient_complaints.hospital_id | TR_REF_STANDARDISE_TEXT |
| department_id | Department identifier | string | No | patient_complaints.department_id | TR_REF_STANDARDISE_TEXT |
| encounter_id | Encounter identifier | string | No | patient_complaints.encounter_id | TR_REF_STANDARDISE_TEXT |
| complaint_received_date | Date complaint received | date | Yes | patient_complaints.complaint_received_date | TR_REF_STANDARDISE_DATE |
| reporting_date | Normalised reporting date | date | Yes | Derived from complaint_received_date | TR_REF_STANDARDISE_DATE |
| reporting_month | Month of reporting | string | Yes | Derived from complaint_received_date | TR_REF_STANDARDISE_DATE |
| complaint_channel | Channel of complaint | string | Yes | patient_complaints.complaint_channel | TR_REF_STANDARDISE_TEXT |
| complaint_category | Category of complaint | string | Yes | patient_complaints.complaint_category | TR_REF_STANDARDISE_TEXT |
| complaint_severity | Severity level | string | Yes | patient_complaints.severity | TR_REF_STANDARDISE_TEXT |
| complaint_status | Status of complaint | string | Yes | patient_complaints.status | TR_REF_STANDARDISE_TEXT |
| formal_complaint_flag | Whether complaint is formal | boolean | Yes | Derived | TR_PX_COMPLAINT_ELIGIBILITY |
| unverified_social_signal_flag | Whether from unverified social media | boolean | Yes | Derived | TR_PX_SOCIAL_SIGNAL_CLASSIFICATION |
| validated_social_complaint_flag | Whether validated social complaint | boolean | Yes | Derived | TR_PX_SOCIAL_SIGNAL_CLASSIFICATION |
| duplicate_flag | Whether duplicate | boolean | Yes | patient_complaints.duplicate_flag | TR_PX_DUPLICATE_CLASSIFICATION |
| original_complaint_id | Original complaint if duplicate | string | No | patient_complaints.duplicate_of_complaint_id | TR_PX_DUPLICATE_CLASSIFICATION |
| rejected_flag | Whether complaint was rejected | boolean | Yes | Derived | TR_PX_COMPLAINT_ELIGIBILITY |
| invalid_flag | Whether complaint is invalid | boolean | Yes | Derived | TR_PX_COMPLAINT_ELIGIBILITY |
| encounter_linked_flag | Whether linked to an encounter | boolean | Yes | Derived | TR_PX_COMPLAINT_ELIGIBILITY |
| valid_complaint_kpi_eligible_flag | Eligible for complaint KPI | boolean | Yes | Derived | TR_PX_COMPLAINT_ELIGIBILITY |
| exclusion_reason_code | Reason for exclusion | string | No | Derived | TR_CTRL_EXCLUSION |
| source_primary_key | Source primary key | string | Yes | patient_complaints.complaint_id | Direct |
| processing_run_id | Processing run reference | string | Yes | System-generated | TR_CTRL_RUN_SUMMARY |
| validation_run_id | Validation run reference | string | Yes | Validation manifest | TR_CTRL_RUN_SUMMARY |
| transformation_version | Transformation version | string | Yes | Config | Direct |
| processed_datetime | Processing timestamp | datetime | Yes | System-generated | TR_CTRL_RUN_SUMMARY |

---

### processed_patient_surveys

**Purpose:** Standardised patient survey response with normalised score and eligibility.
**Grain:** One row per valid survey response.
**Primary Key:** `survey_response_id`
**Implementation Step:** 2D-4

| Field | Description | Type | Required | Source / Derivation | Transformation Rule |
|-------|-------------|------|----------|---------------------|---------------------|
| survey_response_id | Unique survey response identifier | string | Yes | patient_surveys.survey_id | TR_REF_STANDARDISE_TEXT |
| hospital_id | Hospital identifier | string | Yes | patient_surveys.hospital_id | TR_REF_STANDARDISE_TEXT |
| department_id | Department identifier | string | No | patient_surveys.department_id | TR_REF_STANDARDISE_TEXT |
| encounter_id | Encounter identifier | string | No | patient_surveys.encounter_id | TR_REF_STANDARDISE_TEXT |
| response_date | Date of response | date | Yes | patient_surveys.survey_date | TR_REF_STANDARDISE_DATE |
| reporting_date | Normalised reporting date | date | Yes | Derived from response_date | TR_REF_STANDARDISE_DATE |
| reporting_month | Month of reporting | string | Yes | Derived from response_date | TR_REF_STANDARDISE_DATE |
| survey_type | Type of survey | string | Yes | patient_surveys.survey_type | TR_REF_STANDARDISE_TEXT |
| raw_score | Raw score value | decimal | No | patient_surveys.score_value | Direct |
| scale_minimum | Minimum of scale | decimal | Yes | Derived from scale_id | TR_PX_SURVEY_NORMALISATION |
| scale_maximum | Maximum of scale | decimal | Yes | Derived from scale_id | TR_PX_SURVEY_NORMALISATION |
| normalised_score | Score normalised to 0-100 | decimal | No | Derived | TR_PX_SURVEY_NORMALISATION |
| response_weight | Weight of response | decimal | No | patient_surveys.response_weight | TR_PX_WEIGHT_STANDARDISATION |
| response_status | Status of response | string | Yes | Derived from is_complete | TR_PX_SURVEY_ELIGIBILITY |
| complete_response_flag | Whether response is complete | boolean | Yes | patient_surveys.is_complete | TR_PX_SURVEY_ELIGIBILITY |
| duplicate_flag | Whether duplicate | boolean | Yes | Derived | TR_PX_DUPLICATE_CLASSIFICATION |
| valid_response_flag | Whether response passes validation | boolean | Yes | Derived | TR_PX_SURVEY_ELIGIBILITY |
| low_confidence_source_flag | Whether source has low confidence | boolean | Yes | Derived | TR_PX_SURVEY_ELIGIBILITY |
| exclusion_reason_code | Reason for exclusion | string | No | Derived | TR_CTRL_EXCLUSION |
| source_primary_key | Source primary key | string | Yes | patient_surveys.survey_id | Direct |
| processing_run_id | Processing run reference | string | Yes | System-generated | TR_CTRL_RUN_SUMMARY |
| validation_run_id | Validation run reference | string | Yes | Validation manifest | TR_CTRL_RUN_SUMMARY |
| transformation_version | Transformation version | string | Yes | Config | Direct |
| processed_datetime | Processing timestamp | datetime | Yes | System-generated | TR_CTRL_RUN_SUMMARY |

**Note:** `patient_satisfaction_score` is NOT present. Calculated downstream by the KPI engine.

---

### processed_patient_experience_daily

**Purpose:** Daily patient experience preparation without official KPI outputs.
**Grain:** One row per hospital, department and reporting date.
**Primary Key:** `patient_experience_daily_id`
**Implementation Step:** 2D-4

| Field | Description | Type | Required | Source / Derivation | Transformation Rule |
|-------|-------------|------|----------|---------------------|---------------------|
| patient_experience_daily_id | Unique daily record identifier | string | Yes | System-generated | TR_PX_DAILY_AGGREGATION |
| hospital_id | Hospital identifier | string | Yes | processed_patient_complaints.hospital_id | TR_PX_DAILY_AGGREGATION |
| department_id | Department identifier | string | Yes | processed_patient_complaints.department_id | TR_PX_DAILY_AGGREGATION |
| reporting_date | Reporting date | date | Yes | processed_patient_complaints.reporting_date | TR_PX_DAILY_AGGREGATION |
| reporting_month | Month of reporting | string | Yes | Derived from reporting_date | TR_PX_DAILY_AGGREGATION |
| formal_complaint_count | Count of formal complaints | integer | Yes | Derived from processed_patient_complaints | TR_PX_DAILY_AGGREGATION |
| unverified_social_signal_count | Count of unverified social signals | integer | Yes | Derived from processed_patient_complaints | TR_PX_DAILY_AGGREGATION |
| duplicate_complaint_count | Count of duplicate complaints | integer | Yes | Derived from processed_patient_complaints | TR_PX_DAILY_AGGREGATION |
| rejected_complaint_count | Count of rejected complaints | integer | Yes | Derived from processed_patient_complaints | TR_PX_DAILY_AGGREGATION |
| invalid_complaint_count | Count of invalid complaints | integer | Yes | Derived from processed_patient_complaints | TR_PX_DAILY_AGGREGATION |
| linked_complaint_count | Count of encounter-linked complaints | integer | Yes | Derived from processed_patient_complaints | TR_PX_DAILY_AGGREGATION |
| unlinked_complaint_count | Count of unlinked complaints | integer | Yes | Derived from processed_patient_complaints | TR_PX_DAILY_AGGREGATION |
| survey_response_count | Count of survey responses | integer | Yes | Derived from processed_patient_surveys | TR_PX_DAILY_AGGREGATION |
| valid_survey_response_count | Count of valid responses | integer | Yes | Derived from processed_patient_surveys | TR_PX_DAILY_AGGREGATION |
| incomplete_survey_response_count | Count of incomplete responses | integer | Yes | Derived from processed_patient_surveys | TR_PX_DAILY_AGGREGATION |
| duplicate_survey_response_count | Count of duplicate responses | integer | Yes | Derived from processed_patient_surveys | TR_PX_DAILY_AGGREGATION |
| total_normalised_satisfaction_score | Sum of normalised scores | decimal | Yes | Derived from processed_patient_surveys | TR_PX_DAILY_AGGREGATION |
| total_response_weight | Sum of response weights | decimal | Yes | Derived from processed_patient_surveys | TR_PX_DAILY_AGGREGATION |
| weighted_normalised_score_sum | Sum of weighted normalised scores | decimal | Yes | Derived from processed_patient_surveys | TR_PX_DAILY_AGGREGATION |
| eligible_encounter_count_reference | Reference count of eligible encounters | integer | Yes | Derived | TR_PX_DAILY_AGGREGATION |
| processing_run_id | Processing run reference | string | Yes | System-generated | TR_CTRL_RUN_SUMMARY |
| validation_run_id | Validation run reference | string | Yes | Validation manifest | TR_CTRL_RUN_SUMMARY |
| transformation_version | Transformation version | string | Yes | Config | Direct |
| processed_datetime | Processing timestamp | datetime | Yes | System-generated | TR_CTRL_RUN_SUMMARY |

**Note:** `complaint_rate` and `patient_satisfaction_score` are NOT present. Calculated downstream.

---

## E. Control and Lineage Datasets

### processing_record_lineage

**Purpose:** Source-to-processed traceability for every record.
**Grain:** One row per source-to-processed record relationship.
**Primary Key:** `lineage_id`
**Implementation Step:** 2D-5

| Field | Description | Type | Required | Source / Derivation | Transformation Rule |
|-------|-------------|------|----------|---------------------|---------------------|
| processing_run_id | Processing run reference | string | Yes | System-generated | TR_CTRL_LINEAGE |
| lineage_id | Unique lineage identifier | string | Yes | System-generated | TR_CTRL_LINEAGE |
| validation_run_id | Validation run reference | string | Yes | Validation manifest | TR_CTRL_LINEAGE |
| source_dataset_name | Source dataset name | string | Yes | Source metadata | TR_CTRL_LINEAGE |
| source_file_name | Source file name | string | Yes | Source metadata | TR_CTRL_LINEAGE |
| source_primary_key_field | Source primary key field name | string | Yes | Schema registry | TR_CTRL_LINEAGE |
| source_primary_key_value | Source primary key value | string | Yes | Source record | TR_CTRL_LINEAGE |
| source_row_number | Source row number | integer | Yes | Source file | TR_CTRL_LINEAGE |
| processed_dataset_name | Processed dataset name | string | Yes | Schema registry | TR_CTRL_LINEAGE |
| processed_primary_key_field | Processed primary key field name | string | Yes | Schema registry | TR_CTRL_LINEAGE |
| processed_primary_key_value | Processed primary key value | string | Yes | Processed record | TR_CTRL_LINEAGE |
| transformation_rule_id | Transformation rule applied | string | Yes | Transformation registry | TR_CTRL_LINEAGE |
| transformation_description | Description of transformation | string | Yes | Transformation registry | TR_CTRL_LINEAGE |
| source_fields_used | Source fields used | string | Yes | Transformation logic | TR_CTRL_LINEAGE |
| processed_fields_created | Processed fields created | string | Yes | Transformation logic | TR_CTRL_LINEAGE |
| exclusion_flag | Whether record was excluded | boolean | Yes | Derived | TR_CTRL_LINEAGE |
| exclusion_reason_code | Reason for exclusion | string | No | Derived | TR_CTRL_EXCLUSION |
| transformation_version | Transformation version | string | Yes | Config | Direct |
| configuration_version | Configuration version | string | Yes | Config | Direct |
| processed_datetime | Processing timestamp | datetime | Yes | System-generated | TR_CTRL_LINEAGE |

---

### processing_exclusion_register

**Purpose:** Register of all excluded source records with reasons.
**Grain:** One row per excluded source record and exclusion reason.
**Primary Key:** `exclusion_id`
**Implementation Step:** 2D-5

| Field | Description | Type | Required | Source / Derivation | Transformation Rule |
|-------|-------------|------|----------|---------------------|---------------------|
| processing_run_id | Processing run reference | string | Yes | System-generated | TR_CTRL_EXCLUSION |
| exclusion_id | Unique exclusion identifier | string | Yes | System-generated | TR_CTRL_EXCLUSION |
| source_dataset_name | Source dataset name | string | Yes | Source metadata | TR_CTRL_EXCLUSION |
| source_primary_key_field | Source primary key field name | string | Yes | Schema registry | TR_CTRL_EXCLUSION |
| source_primary_key_value | Source primary key value | string | Yes | Source record | TR_CTRL_EXCLUSION |
| source_row_number | Source row number | integer | Yes | Source file | TR_CTRL_EXCLUSION |
| exclusion_reason_code | Standardised exclusion reason code | string | Yes | Derived | TR_CTRL_EXCLUSION |
| exclusion_reason_description | Human-readable exclusion reason | string | Yes | Derived | TR_CTRL_EXCLUSION |
| validation_issue_id | Linked validation issue | string | No | Validation output | TR_CTRL_EXCLUSION |
| manual_override_id | Linked manual override | string | No | Override register | TR_CTRL_EXCLUSION |
| exclusion_stage | Stage where exclusion occurred | string | Yes | Derived | TR_CTRL_EXCLUSION |
| excluded_by_rule | Transformation rule that caused exclusion | string | Yes | Derived | TR_CTRL_EXCLUSION |
| reversible_flag | Whether exclusion can be reversed | boolean | Yes | Derived | TR_CTRL_EXCLUSION |
| created_datetime | Record creation timestamp | datetime | Yes | System-generated | TR_CTRL_EXCLUSION |

---

### processing_run_summary

**Purpose:** Summary of every processed dataset per processing run.
**Grain:** One row per processed dataset per processing run.
**Primary Key:** `processing_run_id` (composite with dataset)
**Implementation Step:** 2D-5

| Field | Description | Type | Required | Source / Derivation | Transformation Rule |
|-------|-------------|------|----------|---------------------|---------------------|
| processing_run_id | Processing run reference | string | Yes | System-generated | TR_CTRL_RUN_SUMMARY |
| validation_run_id | Validation run reference | string | Yes | Validation manifest | TR_CTRL_RUN_SUMMARY |
| source_dataset_name | Source dataset name | string | Yes | Source metadata | TR_CTRL_RUN_SUMMARY |
| processed_dataset_name | Processed dataset name | string | Yes | Schema registry | TR_CTRL_RUN_SUMMARY |
| source_row_count | Count of source rows | integer | Yes | Source file | TR_CTRL_RUN_SUMMARY |
| processed_row_count | Count of processed rows | integer | Yes | Processed output | TR_CTRL_RUN_SUMMARY |
| excluded_row_count | Count of excluded rows | integer | Yes | Exclusion register | TR_CTRL_RUN_SUMMARY |
| transformed_field_count | Count of transformed fields | integer | Yes | Schema registry | TR_CTRL_RUN_SUMMARY |
| warning_count | Count of warnings | integer | Yes | Issue log | TR_CTRL_RUN_SUMMARY |
| error_count | Count of errors | integer | Yes | Issue log | TR_CTRL_RUN_SUMMARY |
| dataset_status | Processing status of dataset | string | Yes | Derived | TR_CTRL_RUN_SUMMARY |
| output_file_name | Name of output file | string | Yes | Derived | TR_CTRL_RUN_SUMMARY |
| transformation_version | Transformation version | string | Yes | Config | Direct |
| processed_datetime | Processing timestamp | datetime | Yes | System-generated | TR_CTRL_RUN_SUMMARY |
| processing_run_status | Overall run status | string | Yes | Derived | TR_CTRL_RUN_SUMMARY |
| processing_allowed_flag | Whether processing was allowed | boolean | Yes | Validation gate | TR_CTRL_RUN_SUMMARY |
| source_checksum | Checksum of source file | string | Yes | Source file | TR_CTRL_RUN_SUMMARY |
| processed_checksum | Checksum of processed file | string | Yes | Processed file | TR_CTRL_RUN_SUMMARY |
| output_schema_version | Version of output schema | string | Yes | Schema registry | TR_CTRL_RUN_SUMMARY |
| notes | Additional notes | string | No | Free text | TR_CTRL_RUN_SUMMARY |
