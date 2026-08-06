# Data Dictionary — Source and Reference Datasets

## Common Traceability Fields

The following fields appear across multiple source datasets where appropriate:

| Field Name | Business Definition | Data Type | Required | Example Format | Sensitivity | Notes |
|---|---|---|---|---|---|---|
| source_system | Name or code of the originating system | string | Yes | "HR_SYSTEM_01" | Low | Used for audit and future integration mapping |
| upload_id | Unique identifier of the upload event that brought this record into Sentinel360 | string | Yes | "UP_2026_07_25_001" | Low | Links to upload_registry |
| record_version | Version of this record within its dataset | integer | Yes | 1 | Low | Incremented on correction or re-upload |
| data_quality_status | Validation result for this record | string | Yes | "Valid" | Low | Domain: Valid, Warning, Rejected, Pending Review |

---

## 1. hospital_master.csv

### Dataset Overview

| Attribute | Value |
|---|---|
| Dataset name | hospital_master |
| File name | hospital_master.csv |
| Purpose | Identifies hospitals included in the system |
| Grain | One record per hospital |
| Primary key | hospital_id |
| Foreign keys | None |
| Required or optional | Required |
| Refresh frequency | Infrequent; on organisational change |
| Prototype source | Manual upload |
| Future production source | Hospital directory or enterprise master data management |
| Sensitivity | Low |
| Main consumers | All datasets scoped by hospital |

### Field Dictionary

| Field Name | Business Definition | Data Type | Required | Primary Key | Foreign Key | Allowed Values or Domain | Validation Rule | Example Format | Sensitivity | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| hospital_id | Unique identifier for the hospital | string | Yes | Yes | No | Alphanumeric, unique | Must be unique and non-blank | "HSP_001" | Low | System-assigned or mapped from source |
| hospital_name | Official name of the hospital | string | Yes | No | No | Non-empty text | Must not be blank; max 200 characters | "General Hospital" | Low | Do not invent real hospital names |
| hospital_type | Classification of hospital service level | string | Yes | No | No | General, Specialist, Teaching, Community, Other | Must match domain | "General" | Low | Pending approval for final domain |
| region | Geographic or administrative region | string | Optional | No | No | Free text | Max 100 characters | "Central Region" | Low | |
| active_flag | Whether the hospital record is currently active | boolean | Yes | No | No | true, false | Must be boolean | true | Low | |
| effective_start_date | Date from which this record is valid | date | Yes | No | No | ISO 8601 date | Must be a valid date; not in the future | "2024-01-01" | Low | |
| effective_end_date | Date after which this record is no longer valid | date | Optional | No | No | ISO 8601 date or blank | If present, must be >= effective_start_date | "2099-12-31" | Low | May be blank for active records |
| source_system | Originating system | string | Yes | No | No | Free text | Max 100 characters | "DIRECTORY_01" | Low | |
| record_version | Record version | integer | Yes | No | No | Positive integer | Must be >= 1 | 1 | Low | |

### Dataset-Level Validation Rules

- hospital_id must be unique across the dataset.
- hospital_name must not be blank.
- active_flag must be true or false.
- effective_end_date, if present, must be >= effective_start_date.
- At most one active record per hospital_id at any point in time.

### Relationships

- Referenced by department_master.hospital_id.
- Referenced by staff_master.hospital_id.
- Referenced by all operational datasets via hospital_id.

### Known Limitations

- No address or contact fields included in prototype scope.
- Hospital group or network relationship not defined yet.

---

## 2. department_master.csv

### Dataset Overview

| Attribute | Value |
|---|---|
| Dataset name | department_master |
| File name | department_master.csv |
| Purpose | Defines departments, wards or service areas and their hospital relationship |
| Grain | One record per department |
| Primary key | department_id |
| Foreign keys | hospital_id (hospital_master) |
| Required or optional | Required |
| Refresh frequency | Infrequent; on organisational change |
| Prototype source | Manual upload |
| Future production source | Hospital directory or HR organisational structure |
| Sensitivity | Low |
| Main consumers | All datasets scoped by department |

### Field Dictionary

| Field Name | Business Definition | Data Type | Required | Primary Key | Foreign Key | Allowed Values or Domain | Validation Rule | Example Format | Sensitivity | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| department_id | Unique identifier for the department | string | Yes | Yes | No | Alphanumeric, unique | Must be unique and non-blank | "DEPT_ER_001" | Low | |
| hospital_id | Hospital to which the department belongs | string | Yes | No | Yes | hospital_master.hospital_id | Must exist in hospital_master | "HSP_001" | Low | |
| department_name | Name of the department or service area | string | Yes | No | No | Non-empty text | Must not be blank; max 200 characters | "Emergency Department" | Low | |
| department_type | Classification of department function | string | Yes | No | No | Emergency, Outpatient, Inpatient Ward, Intensive Care, Surgical, Diagnostic, Patient Experience, Administration, Other | Must match domain | "Emergency" | Low | |
| parent_department_id | Higher-level department in hierarchy | string | Optional | No | Yes | department_master.department_id | If present, must exist in department_master | "DEPT_OPS_001" | Low | Self-referencing; optional |
| active_flag | Whether the department is currently active | boolean | Yes | No | No | true, false | Must be boolean | true | Low | |
| effective_start_date | Date from which this record is valid | date | Yes | No | No | ISO 8601 date | Must be valid; not in the future | "2024-01-01" | Low | |
| effective_end_date | Date after which this record is no longer valid | date | Optional | No | No | ISO 8601 date or blank | If present, must be >= effective_start_date | "2099-12-31" | Low | |
| source_system | Originating system | string | Yes | No | No | Free text | Max 100 characters | "DIRECTORY_01" | Low | |
| record_version | Record version | integer | Yes | No | No | Positive integer | Must be >= 1 | 1 | Low | |

### Dataset-Level Validation Rules

- department_id must be unique.
- hospital_id must exist in hospital_master.
- parent_department_id, if present, must exist in department_master.
- active_flag must be true or false.
- effective_end_date, if present, must be >= effective_start_date.

### Relationships

- References hospital_master.hospital_id.
- Self-references department_master.department_id via parent_department_id.
- Referenced by staff_master.home_department_id.
- Referenced by all operational datasets via department_id.

### Known Limitations

- Single parent hierarchy only; no many-to-many department relationships.
- Department-to-ward breakdown not modelled separately in prototype.

---

## 3. staff_role_master.csv

### Dataset Overview

| Attribute | Value |
|---|---|
| Dataset name | staff_role_master |
| File name | staff_role_master.csv |
| Purpose | Defines staff role categories used across workforce datasets |
| Grain | One record per staff role |
| Primary key | staff_role_id |
| Foreign keys | None |
| Required or optional | Required |
| Refresh frequency | Infrequent; on role definition change |
| Prototype source | Manual upload |
| Future production source | HR information system |
| Sensitivity | Low |
| Main consumers | staff_master, staff_roster, staff_attendance, staffing_requirement |

### Field Dictionary

| Field Name | Business Definition | Data Type | Required | Primary Key | Foreign Key | Allowed Values or Domain | Validation Rule | Example Format | Sensitivity | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| staff_role_id | Unique identifier for the staff role | string | Yes | Yes | No | Alphanumeric, unique | Must be unique and non-blank | "ROLE_NURSE_RN" | Low | |
| staff_role_name | Human-readable name of the role | string | Yes | No | No | Non-empty text | Must not be blank; max 200 characters | "Registered Nurse" | Low | |
| staff_category | Broad employment category | string | Yes | No | No | Doctor, Nurse, Allied Health, Support, Administrative, Other | Must match domain | "Nurse" | Low | |
| clinical_flag | Whether the role is clinical | boolean | Yes | No | No | true, false | Must be boolean | true | Low | |
| active_flag | Whether the role is currently active | boolean | Yes | No | No | true, false | Must be boolean | true | Low | |
| effective_start_date | Date from which this record is valid | date | Yes | No | No | ISO 8601 date | Must be valid; not in the future | "2024-01-01" | Low | |
| effective_end_date | Date after which this record is no longer valid | date | Optional | No | No | ISO 8601 date or blank | If present, must be >= effective_start_date | "2099-12-31" | Low | |
| record_version | Record version | integer | Yes | No | No | Positive integer | Must be >= 1 | 1 | Low | |

### Dataset-Level Validation Rules

- staff_role_id must be unique.
- active_flag must be true or false.
- effective_end_date, if present, must be >= effective_start_date.

### Relationships

- Referenced by staff_master.staff_role_id.
- Referenced by staff_roster.staff_role_id.
- Referenced by staff_attendance.staff_role_id.
- Referenced by staffing_requirement.staff_role_id.

### Known Limitations

- Role-to-skill mapping not included in prototype.
- Pay-grade or band information not included.

---

## 4. staff_master.csv

### Dataset Overview

| Attribute | Value |
|---|---|
| Dataset name | staff_master |
| File name | staff_master.csv |
| Purpose | Contains anonymised staff identity, role and organisational assignment |
| Grain | One anonymised record per staff member |
| Primary key | staff_id |
| Foreign keys | hospital_id, home_department_id, staff_role_id |
| Required or optional | Required for workforce KPIs |
| Refresh frequency | Monthly or on change |
| Prototype source | Manual upload |
| Future production source | HR information system |
| Sensitivity | Medium |
| Main consumers | staff_roster, staff_attendance, staffing_requirement |

### Field Dictionary

| Field Name | Business Definition | Data Type | Required | Primary Key | Foreign Key | Allowed Values or Domain | Validation Rule | Example Format | Sensitivity | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| staff_id | Unique anonymised identifier for the staff member | string | Yes | Yes | No | Alphanumeric, unique | Must be unique and non-blank | "STF_10001" | Medium | Anonymised; no names |
| hospital_id | Primary hospital of employment | string | Yes | No | Yes | hospital_master.hospital_id | Must exist in hospital_master | "HSP_001" | Low | |
| home_department_id | Primary department assignment | string | Yes | No | Yes | department_master.department_id | Must exist in department_master | "DEPT_ER_001" | Low | |
| staff_role_id | Staff role classification | string | Yes | No | Yes | staff_role_master.staff_role_id | Must exist in staff_role_master | "ROLE_NURSE_RN" | Low | |
| employment_type | Type of employment contract | string | Yes | No | No | Permanent, Contract, Temporary, Agency, Part Time, Other | Must match domain | "Permanent" | Low | |
| full_time_equivalent | Full-time equivalent ratio | decimal | Yes | No | No | 0.0 to 1.5 | Must be >= 0 and <= 1.5 | 1.0 | Low | |
| active_flag | Whether the staff member is currently active | boolean | Yes | No | No | true, false | Must be boolean | true | Low | |
| effective_start_date | Employment start or record validity date | date | Yes | No | No | ISO 8601 date | Must be valid; not in the future | "2023-06-01" | Low | |
| effective_end_date | Employment end or record expiry date | date | Optional | No | No | ISO 8601 date or blank | If present, must be >= effective_start_date | "2099-12-31" | Low | |
| source_system | Originating system | string | Yes | No | No | Free text | Max 100 characters | "HR_SYSTEM_01" | Low | |
| record_version | Record version | integer | Yes | No | No | Positive integer | Must be >= 1 | 1 | Low | |

### Dataset-Level Validation Rules

- staff_id must be unique.
- hospital_id must exist in hospital_master.
- home_department_id must exist in department_master.
- staff_role_id must exist in staff_role_master.
- full_time_equivalent must be >= 0 and <= 1.5.
- active_flag must be true or false.
- effective_end_date, if present, must be >= effective_start_date.

### Relationships

- References hospital_master.hospital_id.
- References department_master.department_id.
- References staff_role_master.staff_role_id.
- Referenced by staff_roster.staff_id.
- Referenced by staff_attendance.staff_id.

### Known Limitations

- No staff name, contact or address fields in prototype.
- Single home department only; no secondary assignment modelled.

---

## 5. staff_roster.csv

### Dataset Overview

| Attribute | Value |
|---|---|
| Dataset name | staff_roster |
| File name | staff_roster.csv |
| Purpose | Contains planned staff assignment by date, shift, role and department |
| Grain | One planned assignment per staff member, date and shift |
| Primary key | roster_id |
| Foreign keys | hospital_id, department_id, staff_id, staff_role_id |
| Required or optional | Required for workforce KPIs |
| Refresh frequency | Daily or per roster cycle |
| Prototype source | File upload |
| Future production source | Workforce management or scheduling system |
| Sensitivity | Medium |
| Main consumers | processed_staffing_daily, KPI calculation |

### Field Dictionary

| Field Name | Business Definition | Data Type | Required | Primary Key | Foreign Key | Allowed Values or Domain | Validation Rule | Example Format | Sensitivity | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| roster_id | Unique identifier for the roster entry | string | Yes | Yes | No | Alphanumeric, unique | Must be unique and non-blank | "ROS_20260725_001" | Low | |
| hospital_id | Hospital where the shift is planned | string | Yes | No | Yes | hospital_master.hospital_id | Must exist in hospital_master | "HSP_001" | Low | |
| department_id | Department where the shift is planned | string | Yes | No | Yes | department_master.department_id | Must exist in department_master | "DEPT_ER_001" | Low | |
| staff_id | Staff member assigned | string | Yes | No | Yes | staff_master.staff_id | Must exist in staff_master | "STF_10001" | Medium | |
| staff_role_id | Role for this assignment | string | Yes | No | Yes | staff_role_master.staff_role_id | Must exist in staff_role_master | "ROLE_NURSE_RN" | Low | |
| roster_date | Date of the planned shift | date | Yes | No | No | ISO 8601 date | Must be valid; not in the distant future | "2026-07-25" | Low | |
| shift_code | Identifier for the shift period | string | Yes | No | No | Morning, Afternoon, Night, Custom codes | Max 50 characters | "MORNING" | Low | |
| planned_start_datetime | Planned start of the shift | datetime | Yes | No | No | ISO 8601 datetime | Must be valid; <= planned_end_datetime | "2026-07-25T07:00:00" | Low | |
| planned_end_datetime | Planned end of the shift | datetime | Yes | No | No | ISO 8601 datetime | Must be valid; >= planned_start_datetime | "2026-07-25T15:00:00" | Low | |
| planned_hours | Planned duration in hours | decimal | Yes | No | No | 0 to 24 | Must be >= 0 and <= 24 | 8.0 | Low | |
| roster_status | Status of the roster entry | string | Yes | No | No | Planned, Confirmed, Cancelled, Reassigned | Must match domain | "Confirmed" | Low | |
| source_system | Originating system | string | Yes | No | No | Free text | Max 100 characters | "SCHED_SYSTEM_01" | Low | |
| upload_id | Upload event identifier | string | Yes | No | No | Free text | Max 100 characters | "UP_2026_07_25_001" | Low | |
| record_version | Record version | integer | Yes | No | No | Positive integer | Must be >= 1 | 1 | Low | |

### Dataset-Level Validation Rules

- roster_id must be unique.
- hospital_id, department_id, staff_id, staff_role_id must exist in their respective master datasets.
- planned_start_datetime must be <= planned_end_datetime.
- planned_hours must be >= 0 and <= 24.
- roster_date must be a valid date.
- No duplicate active roster entries for the same staff_id, roster_date and shift_code unless one is Cancelled.

### Relationships

- References hospital_master.hospital_id.
- References department_master.department_id.
- References staff_master.staff_id.
- References staff_role_master.staff_role_id.

### Known Limitations

- No break or meal-period detail.
- No overtime or on-call flag in prototype.

---

## 6. staff_attendance.csv

### Dataset Overview

| Attribute | Value |
|---|---|
| Dataset name | staff_attendance |
| File name | staff_attendance.csv |
| Purpose | Contains actual attendance or absence events |
| Grain | One actual attendance record per staff member, date and shift |
| Primary key | attendance_id |
| Foreign keys | hospital_id, department_id, staff_id, staff_role_id, replacement_staff_id |
| Required or optional | Required for workforce KPIs |
| Refresh frequency | Daily |
| Prototype source | File upload |
| Future production source | Time and attendance or HR system |
| Sensitivity | Medium |
| Main consumers | processed_attendance_daily, KPI calculation |

### Field Dictionary

| Field Name | Business Definition | Data Type | Required | Primary Key | Foreign Key | Allowed Values or Domain | Validation Rule | Example Format | Sensitivity | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| attendance_id | Unique identifier for the attendance record | string | Yes | Yes | No | Alphanumeric, unique | Must be unique and non-blank | "ATT_20260725_001" | Low | |
| hospital_id | Hospital where attendance is recorded | string | Yes | No | Yes | hospital_master.hospital_id | Must exist in hospital_master | "HSP_001" | Low | |
| department_id | Department where attendance is recorded | string | Yes | No | Yes | department_master.department_id | Must exist in department_master | "DEPT_ER_001" | Low | |
| staff_id | Staff member | string | Yes | No | Yes | staff_master.staff_id | Must exist in staff_master | "STF_10001" | Medium | |
| staff_role_id | Role for this attendance record | string | Yes | No | Yes | staff_role_master.staff_role_id | Must exist in staff_role_master | "ROLE_NURSE_RN" | Low | |
| attendance_date | Date of attendance | date | Yes | No | No | ISO 8601 date | Must be valid | "2026-07-25" | Low | |
| shift_code | Shift identifier | string | Yes | No | No | Morning, Afternoon, Night, Custom codes | Max 50 characters | "MORNING" | Low | |
| attendance_status | Attendance outcome | string | Yes | No | No | Present, Absent, Late, Partial, Leave, Training, Reassigned, Not Scheduled | Must match domain | "Present" | Low | |
| actual_start_datetime | Actual start time | datetime | Optional | No | No | ISO 8601 datetime | If present, must be valid; <= actual_end_datetime | "2026-07-25T07:05:00" | Low | |
| actual_end_datetime | Actual end time | datetime | Optional | No | No | ISO 8601 datetime | If present, must be valid; >= actual_start_datetime | "2026-07-25T15:00:00" | Low | |
| actual_hours | Actual hours worked | decimal | Optional | No | No | 0 to 24 | If present, must be >= 0 and <= 24 | 7.92 | Low | |
| absence_category | Category of absence if absent | string | Optional | No | No | Sick Leave, Emergency Leave, Annual Leave, Unauthorised, Other, Not Applicable | Required if attendance_status is Absent or Leave; otherwise Not Applicable | "Not Applicable" | Medium | No medical details |
| replacement_staff_id | Staff member who replaced the absent worker | string | Optional | No | Yes | staff_master.staff_id | If present, must exist in staff_master | "STF_10002" | Medium | |
| source_system | Originating system | string | Yes | No | No | Free text | Max 100 characters | "TNA_SYSTEM_01" | Low | |
| upload_id | Upload event identifier | string | Yes | No | No | Free text | Max 100 characters | "UP_2026_07_25_001" | Low | |
| record_version | Record version | integer | Yes | No | No | Positive integer | Must be >= 1 | 1 | Low | |

### Dataset-Level Validation Rules

- attendance_id must be unique.
- hospital_id, department_id, staff_id, staff_role_id must exist in master datasets.
- replacement_staff_id, if present, must exist in staff_master.
- actual_start_datetime <= actual_end_datetime when both are present.
- actual_hours must be >= 0 and <= 24 when present.
- absence_category must be provided when attendance_status is Absent or Leave.
- absence_category should be "Not Applicable" when attendance_status is Present, Late, Partial, Training, Reassigned or Not Scheduled.

### Relationships

- References hospital_master.hospital_id.
- References department_master.department_id.
- References staff_master.staff_id.
- References staff_role_master.staff_role_id.
- Optionally references staff_master.staff_id via replacement_staff_id.

### Known Limitations

- No medical or disability detail.
- No overtime pay calculation fields.

---

## 7. staffing_requirement.csv

### Dataset Overview

| Attribute | Value |
|---|---|
| Dataset name | staffing_requirement |
| File name | staffing_requirement.csv |
| Purpose | Contains required staffing levels by department, date, shift and role |
| Grain | One staffing requirement per hospital, department, date, shift and staff role |
| Primary key | staffing_requirement_id |
| Foreign keys | hospital_id, department_id, staff_role_id |
| Required or optional | Required for Staffing Level KPI |
| Refresh frequency | Daily or per roster cycle |
| Prototype source | File upload |
| Future production source | Workforce planning or scheduling system |
| Sensitivity | Low |
| Main consumers | processed_staffing_daily, KPI calculation |

### Field Dictionary

| Field Name | Business Definition | Data Type | Required | Primary Key | Foreign Key | Allowed Values or Domain | Validation Rule | Example Format | Sensitivity | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| staffing_requirement_id | Unique identifier for the requirement record | string | Yes | Yes | No | Alphanumeric, unique | Must be unique and non-blank | "REQ_20260725_001" | Low | |
| hospital_id | Hospital | string | Yes | No | Yes | hospital_master.hospital_id | Must exist in hospital_master | "HSP_001" | Low | |
| department_id | Department | string | Yes | No | Yes | department_master.department_id | Must exist in department_master | "DEPT_ER_001" | Low | |
| requirement_date | Date for which the requirement applies | date | Yes | No | No | ISO 8601 date | Must be valid | "2026-07-25" | Low | |
| shift_code | Shift identifier | string | Yes | No | No | Morning, Afternoon, Night, Custom codes | Max 50 characters | "MORNING" | Low | |
| staff_role_id | Required role | string | Yes | No | Yes | staff_role_master.staff_role_id | Must exist in staff_role_master | "ROLE_NURSE_RN" | Low | |
| required_staff_count | Number of staff required | integer | Yes | No | No | 0 to 999 | Must be >= 0 | 5 | Low | |
| required_staff_hours | Total staff hours required | decimal | Optional | No | No | 0 to 9999 | If present, must be >= 0 | 40.0 | Low | |
| requirement_basis | Basis for the requirement | string | Optional | No | No | Historical Demand, Regulatory, Budget, Clinical Protocol, Other | Must match domain if provided | "Historical Demand" | Low | |
| approved_by_role | Role that approved this requirement | string | Optional | No | No | Free text | Max 100 characters | "Nursing Director" | Low | |
| effective_start_date | Date from which this requirement is valid | date | Yes | No | No | ISO 8601 date | Must be valid | "2026-07-25" | Low | |
| effective_end_date | Date after which this requirement expires | date | Optional | No | No | ISO 8601 date or blank | If present, must be >= effective_start_date | "2026-12-31" | Low | |
| configuration_version | Version of the configuration that produced this requirement | string | Yes | No | No | Free text | Max 50 characters | "CONFIG_V1" | Low | |

### Dataset-Level Validation Rules

- staffing_requirement_id must be unique.
- hospital_id, department_id, staff_role_id must exist in master datasets.
- required_staff_count must be >= 0.
- required_staff_hours, if present, must be >= 0.
- effective_end_date, if present, must be >= effective_start_date.
- No duplicate active requirements for the same hospital_id, department_id, requirement_date, shift_code and staff_role_id.

### Relationships

- References hospital_master.hospital_id.
- References department_master.department_id.
- References staff_role_master.staff_role_id.

### Known Limitations

- No skill-level or qualification-level breakdown within role.
- Requirement approval workflow not automated in prototype.

---

## 8. patient_encounters.csv

### Dataset Overview

| Attribute | Value |
|---|---|
| Dataset name | patient_encounters |
| File name | patient_encounters.csv |
| Purpose | Contains patient activity volume required as denominators and demand signals |
| Grain | One anonymised patient encounter |
| Primary key | encounter_id |
| Foreign keys | hospital_id, department_id |
| Required or optional | Required for Bed Occupancy Rate and demand denominators |
| Refresh frequency | Daily |
| Prototype source | File upload |
| Future production source | Patient administration or appointment system |
| Sensitivity | Medium |
| Main consumers | processed_patient_activity_daily, KPI calculation |

### Field Dictionary

| Field Name | Business Definition | Data Type | Required | Primary Key | Foreign Key | Allowed Values or Domain | Validation Rule | Example Format | Sensitivity | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| encounter_id | Unique anonymised identifier for the patient encounter | string | Yes | Yes | No | Alphanumeric, unique | Must be unique and non-blank | "ENC_20260725_001" | Medium | Anonymised |
| hospital_id | Hospital where the encounter occurred | string | Yes | No | Yes | hospital_master.hospital_id | Must exist in hospital_master | "HSP_001" | Low | |
| department_id | Department where the encounter occurred | string | Yes | No | Yes | department_master.department_id | Must exist in department_master | "DEPT_ER_001" | Low | |
| encounter_date | Date of the encounter | date | Yes | No | No | ISO 8601 date | Must be valid | "2026-07-25" | Low | |
| arrival_datetime | Date and time of patient arrival | datetime | Yes | No | No | ISO 8601 datetime | Must be valid | "2026-07-25T08:30:00" | Low | |
| service_start_datetime | Date and time service began | datetime | Optional | No | No | ISO 8601 datetime | If present, must be >= arrival_datetime | "2026-07-25T09:00:00" | Low | |
| service_end_datetime | Date and time service ended | datetime | Optional | No | No | ISO 8601 datetime | If present, must be >= service_start_datetime | "2026-07-25T10:30:00" | Low | |
| discharge_datetime | Date and time of discharge | datetime | Optional | No | No | ISO 8601 datetime | If present, must be >= arrival_datetime | "2026-07-25T11:00:00" | Low | |
| encounter_type | Type of encounter | string | Yes | No | No | Emergency, Outpatient, Inpatient, Day Care, Diagnostic, Other | Must match domain | "Emergency" | Low | |
| arrival_mode | How the patient arrived | string | Optional | No | No | Walk In, Ambulance, Referral, Scheduled, Other | Must match domain if provided | "Walk In" | Low | |
| encounter_status | Status of the encounter | string | Yes | No | No | Completed, Admitted, Discharged, Transferred, Cancelled, Left Before Service, Other | Must match domain | "Completed" | Low | |
| source_system | Originating system | string | Yes | No | No | Free text | Max 100 characters | "PAS_SYSTEM_01" | Low | |
| upload_id | Upload event identifier | string | Yes | No | No | Free text | Max 100 characters | "UP_2026_07_25_001" | Low | |
| record_version | Record version | integer | Yes | No | No | Positive integer | Must be >= 1 | 1 | Low | |

### Dataset-Level Validation Rules

- encounter_id must be unique.
- hospital_id, department_id must exist in master datasets.
- arrival_datetime <= service_start_datetime <= service_end_datetime <= discharge_datetime, where all are present.
- encounter_date must be a valid date.
- No patient names, diagnoses or clinical notes included.

### Relationships

- References hospital_master.hospital_id.
- References department_master.department_id.
- Referenced optionally by patient_complaints.encounter_id.
- Referenced optionally by patient_surveys.encounter_id.

### Known Limitations

- No clinical diagnosis or procedure codes.
- No patient demographics in prototype.

---

## 9. patient_queue_records.csv

### Dataset Overview

| Attribute | Value |
|---|---|
| Dataset name | patient_queue_records |
| File name | patient_queue_records.csv |
| Purpose | Contains waiting-time and queue-volume information |
| Grain | One queue observation or summary per department and defined time interval |
| Primary key | queue_record_id |
| Foreign keys | hospital_id, department_id |
| Required or optional | Required for Average Patient Waiting Time |
| Refresh frequency | Daily or per shift |
| Prototype source | File upload |
| Future production source | Queue management or patient flow system |
| Sensitivity | Low |
| Main consumers | processed_queue_daily, KPI calculation |

### Field Dictionary

| Field Name | Business Definition | Data Type | Required | Primary Key | Foreign Key | Allowed Values or Domain | Validation Rule | Example Format | Sensitivity | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| queue_record_id | Unique identifier for the queue record | string | Yes | Yes | No | Alphanumeric, unique | Must be unique and non-blank | "QUE_20260725_001" | Low | |
| hospital_id | Hospital | string | Yes | No | Yes | hospital_master.hospital_id | Must exist in hospital_master | "HSP_001" | Low | |
| department_id | Department | string | Yes | No | Yes | department_master.department_id | Must exist in department_master | "DEPT_ER_001" | Low | |
| queue_date | Date of the queue observation | date | Yes | No | No | ISO 8601 date | Must be valid | "2026-07-25" | Low | |
| interval_start_datetime | Start of the observation interval | datetime | Yes | No | No | ISO 8601 datetime | Must be valid; <= interval_end_datetime | "2026-07-25T08:00:00" | Low | |
| interval_end_datetime | End of the observation interval | datetime | Yes | No | No | ISO 8601 datetime | Must be valid; >= interval_start_datetime | "2026-07-25T09:00:00" | Low | |
| queue_type | Type of queue or service point | string | Yes | No | No | Registration, Triage, Consultation, Diagnostic, Pharmacy, Admission, Other | Must match domain | "Consultation" | Low | |
| arrivals_count | Number of patients who arrived in the interval | integer | Yes | No | No | 0 to 99999 | Must be >= 0 | 45 | Low | |
| served_count | Number of patients served in the interval | integer | Yes | No | No | 0 to 99999 | Must be >= 0; <= arrivals_count + opening backlog | 42 | Low | |
| waiting_patient_count | Patients waiting at interval end | integer | Yes | No | No | 0 to 99999 | Must be >= 0 | 8 | Low | |
| average_wait_minutes | Average waiting time in minutes | decimal | Yes | No | No | 0 to 9999 | Must be >= 0 | 35.5 | Low | |
| median_wait_minutes | Median waiting time in minutes | decimal | Optional | No | No | 0 to 9999 | If present, must be >= 0 | 28.0 | Low | |
| maximum_wait_minutes | Maximum waiting time in minutes | decimal | Optional | No | No | 0 to 9999 | If present, must be >= median and >= average | 120.0 | Low | |
| source_system | Originating system | string | Yes | No | No | Free text | Max 100 characters | "QUEUE_SYSTEM_01" | Low | |
| upload_id | Upload event identifier | string | Yes | No | No | Free text | Max 100 characters | "UP_2026_07_25_001" | Low | |
| record_version | Record version | integer | Yes | No | No | Positive integer | Must be >= 1 | 1 | Low | |

### Dataset-Level Validation Rules

- queue_record_id must be unique.
- hospital_id, department_id must exist in master datasets.
- interval_start_datetime <= interval_end_datetime.
- arrivals_count, served_count, waiting_patient_count must be >= 0.
- average_wait_minutes, median_wait_minutes, maximum_wait_minutes must be >= 0 when present.
- maximum_wait_minutes >= average_wait_minutes when both are present.
- No overlapping intervals for the same hospital_id, department_id, queue_date and queue_type unless explicitly allowed.

### Relationships

- References hospital_master.hospital_id.
- References department_master.department_id.

### Known Limitations

- No individual patient queue position tracking.
- No queue abandonment count in prototype.

---

## 10. bed_capacity_records.csv

### Dataset Overview

| Attribute | Value |
|---|---|
| Dataset name | bed_capacity_records |
| File name | bed_capacity_records.csv |
| Purpose | Contains available, occupied, unavailable and operational bed information |
| Grain | One bed-capacity observation per hospital, department and date or interval |
| Primary key | bed_record_id |
| Foreign keys | hospital_id, department_id |
| Required or optional | Required for Bed Occupancy Rate |
| Refresh frequency | Daily |
| Prototype source | File upload |
| Future production source | Bed management or patient administration system |
| Sensitivity | Low |
| Main consumers | processed_bed_capacity_daily, KPI calculation |

### Field Dictionary

| Field Name | Business Definition | Data Type | Required | Primary Key | Foreign Key | Allowed Values or Domain | Validation Rule | Example Format | Sensitivity | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| bed_record_id | Unique identifier for the bed capacity record | string | Yes | Yes | No | Alphanumeric, unique | Must be unique and non-blank | "BED_20260725_001" | Low | |
| hospital_id | Hospital | string | Yes | No | Yes | hospital_master.hospital_id | Must exist in hospital_master | "HSP_001" | Low | |
| department_id | Department or ward | string | Yes | No | Yes | department_master.department_id | Must exist in department_master | "DEPT_WARD_A" | Low | |
| record_date | Date of the observation | date | Yes | No | No | ISO 8601 date | Must be valid | "2026-07-25" | Low | |
| interval_start_datetime | Start of observation interval | datetime | Optional | No | No | ISO 8601 datetime | If present, must be <= interval_end_datetime | "2026-07-25T00:00:00" | Low | |
| interval_end_datetime | End of observation interval | datetime | Optional | No | No | ISO 8601 datetime | If present, must be >= interval_start_datetime | "2026-07-25T23:59:59" | Low | |
| licensed_beds | Total beds licensed for the department | integer | Yes | No | No | 0 to 9999 | Must be >= 0 | 50 | Low | |
| staffed_beds | Beds with staff available to support | integer | Yes | No | No | 0 to 9999 | Must be >= 0 and <= licensed_beds | 48 | Low | |
| operational_beds | Beds currently available for use | integer | Yes | No | No | 0 to 9999 | Must be >= 0 and <= licensed_beds | 45 | Low | |
| occupied_beds | Beds currently in use | integer | Yes | No | No | 0 to 9999 | Must be >= 0 and <= operational_beds unless exception flagged | 42 | Low | |
| unavailable_beds | Beds out of service | integer | Yes | No | No | 0 to 9999 | Must be >= 0 | 3 | Low | |
| reserved_beds | Beds held for specific purposes | integer | Yes | No | No | 0 to 9999 | Must be >= 0 | 2 | Low | |
| capacity_exception_flag | Whether an exception applies to normal capacity rules | boolean | Yes | No | No | true, false | Must be boolean | false | Low | |
| capacity_exception_reason | Description of the exception | string | Optional | No | No | Free text | Required if capacity_exception_flag is true; max 500 characters | "Maintenance" | Low | |
| source_system | Originating system | string | Yes | No | No | Free text | Max 100 characters | "BED_SYSTEM_01" | Low | |
| upload_id | Upload event identifier | string | Yes | No | No | Free text | Max 100 characters | "UP_2026_07_25_001" | Low | |
| record_version | Record version | integer | Yes | No | No | Positive integer | Must be >= 1 | 1 | Low | |

### Dataset-Level Validation Rules

- bed_record_id must be unique.
- hospital_id, department_id must exist in master datasets.
- All bed counts must be >= 0.
- staffed_beds <= licensed_beds.
- operational_beds <= licensed_beds.
- occupied_beds <= operational_beds unless capacity_exception_flag is true.
- unavailable_beds + operational_beds + reserved_beds should approximate licensed_beds; flagged as warning if not.
- capacity_exception_reason required when capacity_exception_flag is true.

### Relationships

- References hospital_master.hospital_id.
- References department_master.department_id.

### Known Limitations

- No individual bed-level tracking in prototype.
- No bed-type breakdown (e.g., ICU, paediatric).

---

## 11. patient_complaints.csv

### Dataset Overview

| Attribute | Value |
|---|---|
| Dataset name | patient_complaints |
| File name | patient_complaints.csv |
| Purpose | Contains complaint events or aggregated complaint records |
| Grain | One complaint event |
| Primary key | complaint_id |
| Foreign keys | hospital_id, department_id, encounter_id |
| Required or optional | Required for Patient Complaint Rate |
| Refresh frequency | Daily |
| Prototype source | File upload |
| Future production source | Patient experience or complaints management system |
| Sensitivity | Medium |
| Main consumers | processed_complaints_daily, KPI calculation |

### Field Dictionary

| Field Name | Business Definition | Data Type | Required | Primary Key | Foreign Key | Allowed Values or Domain | Validation Rule | Example Format | Sensitivity | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| complaint_id | Unique identifier for the complaint | string | Yes | Yes | No | Alphanumeric, unique | Must be unique and non-blank | "CMP_20260725_001" | Medium | |
| hospital_id | Hospital where the complaint is directed | string | Yes | No | Yes | hospital_master.hospital_id | Must exist in hospital_master | "HSP_001" | Low | |
| department_id | Department associated with the complaint | string | Yes | No | Yes | department_master.department_id | Must exist in department_master | "DEPT_ER_001" | Low | |
| encounter_id | Related patient encounter | string | Optional | No | Yes | patient_encounters.encounter_id | If present, must exist in patient_encounters | "ENC_20260725_001" | Medium | Optional linkage |
| complaint_date | Date the complaint was received | date | Yes | No | No | ISO 8601 date | Must be valid | "2026-07-25" | Low | |
| complaint_channel | Channel through which the complaint was received | string | Yes | No | No | Web Form, Email, Telephone, Counter, Survey, Social Media, Other | Must match domain | "Telephone" | Low | |
| complaint_category | Category of the complaint | string | Yes | No | No | Waiting Time, Communication, Staff Conduct, Facilities, Billing, Access, Service Quality, Other | Must match domain | "Waiting Time" | Low | |
| complaint_severity | Severity level | string | Yes | No | No | Low, Medium, High, Critical | Must match domain | "Medium" | Low | |
| complaint_status | Current status of the complaint | string | Yes | No | No | Open, Under Review, Resolved, Closed, Rejected, Duplicate | Must match domain | "Under Review" | Low | |
| resolution_date | Date the complaint was resolved | date | Optional | No | No | ISO 8601 date | If present, must be >= complaint_date | "2026-07-28" | Low | |
| recurring_issue_flag | Whether this is a recurring issue | boolean | Yes | No | No | true, false | Must be boolean | false | Low | |
| complaint_theme_code | Coded theme for analysis | string | Optional | No | No | Free text | Max 50 characters | "THEME_WAIT_01" | Low | |
| text_available_flag | Whether free-text content exists externally | boolean | Optional | No | No | true, false | Must be boolean if present | false | Low | No text stored in prototype |
| source_system | Originating system | string | Yes | No | No | Free text | Max 100 characters | "PX_SYSTEM_01" | Low | |
| upload_id | Upload event identifier | string | Yes | No | No | Free text | Max 100 characters | "UP_2026_07_25_001" | Low | |
| record_version | Record version | integer | Yes | No | No | Positive integer | Must be >= 1 | 1 | Low | |

### Dataset-Level Validation Rules

- complaint_id must be unique.
- hospital_id, department_id must exist in master datasets.
- encounter_id, if present, must exist in patient_encounters.
- resolution_date, if present, must be >= complaint_date.
- No personally identifiable complaint content stored in prototype.

### Relationships

- References hospital_master.hospital_id.
- References department_master.department_id.
- Optionally references patient_encounters.encounter_id.

### Known Limitations

- No free-text complaint detail in prototype.
- No complainant contact information.

---

## 12. patient_surveys.csv

### Dataset Overview

| Attribute | Value |
|---|---|
| Dataset name | patient_surveys |
| File name | patient_surveys.csv |
| Purpose | Contains patient satisfaction responses or aggregated survey records |
| Grain | One anonymised survey response or approved aggregated record |
| Primary key | survey_response_id |
| Foreign keys | hospital_id, department_id, encounter_id |
| Required or optional | Required for Patient Satisfaction Score |
| Refresh frequency | Daily or per survey cycle |
| Prototype source | File upload |
| Future production source | Patient experience or survey platform |
| Sensitivity | Low |
| Main consumers | processed_satisfaction_daily, KPI calculation |

### Field Dictionary

| Field Name | Business Definition | Data Type | Required | Primary Key | Foreign Key | Allowed Values or Domain | Validation Rule | Example Format | Sensitivity | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| survey_response_id | Unique identifier for the survey response | string | Yes | Yes | No | Alphanumeric, unique | Must be unique and non-blank | "SUR_20260725_001" | Low | |
| hospital_id | Hospital | string | Yes | No | Yes | hospital_master.hospital_id | Must exist in hospital_master | "HSP_001" | Low | |
| department_id | Department | string | Yes | No | Yes | department_master.department_id | Must exist in department_master | "DEPT_ER_001" | Low | |
| encounter_id | Related encounter | string | Optional | No | Yes | patient_encounters.encounter_id | If present, must exist in patient_encounters | "ENC_20260725_001" | Medium | |
| survey_date | Date of the survey response | date | Yes | No | No | ISO 8601 date | Must be valid | "2026-07-25" | Low | |
| survey_type | Type of survey instrument | string | Yes | No | No | Discharge, Outpatient, Emergency, General, Other | Must match domain | "Discharge" | Low | |
| satisfaction_score | Aggregated or overall satisfaction score | decimal | Yes | No | No | Numeric | Must be >= score_scale_min and <= score_scale_max | 4.2 | Low | |
| score_scale_min | Minimum possible score | decimal | Yes | No | No | Numeric | Must be < score_scale_max | 1.0 | Low | Configurable scale |
| score_scale_max | Maximum possible score | decimal | Yes | No | No | Numeric | Must be > score_scale_min | 5.0 | Low | Configurable scale |
| response_weight | Weight applied to this response in aggregation | decimal | Optional | No | No | 0.0 to 10.0 | If present, must be >= 0 | 1.0 | Low | |
| response_status | Status of the response | string | Yes | No | No | Valid, Invalid, Incomplete, Duplicate | Must match domain | "Valid" | Low | |
| source_system | Originating system | string | Yes | No | No | Free text | Max 100 characters | "SURVEY_SYSTEM_01" | Low | |
| upload_id | Upload event identifier | string | Yes | No | No | Free text | Max 100 characters | "UP_2026_07_25_001" | Low | |
| record_version | Record version | integer | Yes | No | No | Positive integer | Must be >= 1 | 1 | Low | |

### Dataset-Level Validation Rules

- survey_response_id must be unique.
- hospital_id, department_id must exist in master datasets.
- encounter_id, if present, must exist in patient_encounters.
- satisfaction_score must be >= score_scale_min and <= score_scale_max.
- score_scale_min < score_scale_max.
- response_weight, if present, must be >= 0.

### Relationships

- References hospital_master.hospital_id.
- References department_master.department_id.
- Optionally references patient_encounters.encounter_id.

### Known Limitations

- No individual question-level responses in prototype.
- Score scale is configurable but not yet approved.

---

## 13. service_schedule.csv

### Dataset Overview

| Attribute | Value |
|---|---|
| Dataset name | service_schedule |
| File name | service_schedule.csv |
| Purpose | Contains planned operating hours, clinic sessions or service availability |
| Grain | One planned service session per department and date |
| Primary key | service_schedule_id |
| Foreign keys | hospital_id, department_id |
| Required or optional | Optional for baseline; recommended for scenario simulation |
| Refresh frequency | Daily or per schedule cycle |
| Prototype source | File upload |
| Future production source | Scheduling or service-management system |
| Sensitivity | Low |
| Main consumers | processed_service_availability_daily, scenario simulation |

### Field Dictionary

| Field Name | Business Definition | Data Type | Required | Primary Key | Foreign Key | Allowed Values or Domain | Validation Rule | Example Format | Sensitivity | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| service_schedule_id | Unique identifier for the schedule entry | string | Yes | Yes | No | Alphanumeric, unique | Must be unique and non-blank | "SCH_20260725_001" | Low | |
| hospital_id | Hospital | string | Yes | No | Yes | hospital_master.hospital_id | Must exist in hospital_master | "HSP_001" | Low | |
| department_id | Department | string | Yes | No | Yes | department_master.department_id | Must exist in department_master | "DEPT_OPC_001" | Low | |
| service_date | Date of the planned service | date | Yes | No | No | ISO 8601 date | Must be valid | "2026-07-25" | Low | |
| service_type | Type of service session | string | Yes | No | No | Clinic, Emergency, Diagnostic, Surgical, Other | Must match domain | "Clinic" | Low | |
| planned_start_datetime | Planned start time | datetime | Yes | No | No | ISO 8601 datetime | Must be valid; <= planned_end_datetime | "2026-07-25T08:00:00" | Low | |
| planned_end_datetime | Planned end time | datetime | Yes | No | No | ISO 8601 datetime | Must be valid; >= planned_start_datetime | "2026-07-25T17:00:00" | Low | |
| planned_service_hours | Planned duration in hours | decimal | Yes | No | No | 0 to 24 | Must be >= 0 and <= 24 | 9.0 | Low | |
| planned_capacity | Planned patient capacity | integer | Optional | No | No | 0 to 99999 | If present, must be >= 0 | 120 | Low | |
| schedule_status | Status of the session | string | Yes | No | No | Planned, Open, Reduced, Cancelled, Extended, Closed | Must match domain | "Open" | Low | |
| source_system | Originating system | string | Yes | No | No | Free text | Max 100 characters | "SCHED_SYSTEM_01" | Low | |
| upload_id | Upload event identifier | string | Yes | No | No | Free text | Max 100 characters | "UP_2026_07_25_001" | Low | |
| record_version | Record version | integer | Yes | No | No | Positive integer | Must be >= 1 | 1 | Low | |

### Dataset-Level Validation Rules

- service_schedule_id must be unique.
- hospital_id, department_id must exist in master datasets.
- planned_start_datetime <= planned_end_datetime.
- planned_service_hours must be >= 0 and <= 24.
- planned_capacity, if present, must be >= 0.
- No duplicate active schedules for the same hospital_id, department_id, service_date and service_type unless one is Cancelled.

### Relationships

- References hospital_master.hospital_id.
- References department_master.department_id.

### Known Limitations

- No room or resource-level scheduling detail.
- No appointment-level detail in prototype.
