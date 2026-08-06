# KPI Definitions

## Purpose

This document formally defines the six headline Key Performance Indicators (KPIs) for Sentinel360 Healthcare. It establishes the approved business meaning, data requirements, conceptual formulas, aggregation rules, eligibility rules and missing-data treatment for each KPI. All KPI values must be calculated dynamically from source data and configuration. No threshold values are defined in this document.

---

## General KPI Design Principles

The following principles apply consistently across all six KPIs:

1. Every KPI must have a clear business definition.
2. Every KPI must define its numerator and denominator.
3. Every KPI must identify its source datasets.
4. Every KPI must define its grain and aggregation level.
5. Every KPI must support hospital-level calculation.
6. Every KPI should support department-level calculation where data permit.
7. Every KPI must include reporting-period eligibility rules.
8. Every KPI must define missing-data treatment.
9. Every KPI must identify whether higher or lower values represent better performance.
10. Every KPI must be reproducible from the same inputs and configuration.
11. Dashboard values must not be hardcoded.
12. Threshold values must remain configuration-driven.
13. Warning and critical thresholds must not be invented in this step.
14. Calculation logic must not silently replace missing data.
15. Ineligible calculations must return a status such as `Not Available`, `Insufficient Data` or `Data Quality Review Required`.
16. Percentages must be stored as numeric percentage values from 0 to 100.
17. Rates must clearly state their denominator basis.
18. Aggregation must avoid averaging already-aggregated percentages where weighted calculation is required.
19. Every KPI result must retain hospital, department, period and calculation-version traceability.
20. The KPI engine must not claim causality.

---

## KPI Catalogue

| KPI Code | KPI Name | Domain | Performance Direction | Unit |
|---|---|---|---|---|
| WF_STAFF_LEVEL | Staffing Level | Workforce | Higher Is Better | Percent |
| WF_ABSENTEEISM | Staff Absenteeism Rate | Workforce | Lower Is Better | Percent |
| OP_BED_OCCUPANCY | Bed Occupancy Rate | Operations | Lower Is Better (pending approved target range) | Percent |
| OP_WAIT_TIME | Average Patient Waiting Time | Operations | Lower Is Better | Minutes |
| PX_COMPLAINT_RATE | Patient Complaint Rate | Patient Experience | Lower Is Better | Complaints per 1,000 eligible encounters |
| PX_SATISFACTION | Patient Satisfaction Score | Patient Experience | Higher Is Better | Normalised Percent Score |

---

## KPI 1: Staffing Level

### KPI Name
Staffing Level

### KPI Code
WF_STAFF_LEVEL

### Business Domain
Workforce

### Business Question Answered
What proportion of the approved staffing requirement was actually available for service?

### Business Definition
Staffing Level measures the degree to which the hospital or department has sufficient staff available to meet its approved staffing requirement during the reporting period. It compares actual available staff time against the approved required staff time, expressed as a percentage. Higher values indicate greater staffing adequacy relative to the approved plan.

### Performance Direction
Higher Is Better

### Unit
Percent

### Primary Source Datasets
- `staffing_requirement.csv`
- `staff_attendance.csv`

### Supporting Datasets
- `staff_roster.csv`
- `staff_master.csv`
- `staff_role_master.csv`
- `department_master.csv`

### Numerator
Sum of eligible actual available staff hours, derived from attendance records that represent service availability during the reporting period.

### Denominator
Sum of approved required staff hours from the staffing requirement dataset for the same hospital, department, staff role and period.

### Formula

**Conceptual formula:**

```
Staffing Level (%) = (Actual Available Staffing / Approved Required Staffing) * 100
```

**Preferred operational formula:**

```
Staffing Level (%) = (Sum of eligible actual available staff hours / Sum of approved required staff hours) * 100
```

Staff hours are the preferred basis because shifts may have different durations. A staff-count calculation is permitted only when staff-hour data are unavailable and the fallback method is explicitly approved.

### Preferred Calculation Grain
Shift or day, rolled up to the reporting period.

### Supported Aggregation Levels
- Department level (preferred)
- Hospital level (by weighted aggregation across departments)

### Reporting Frequency
Daily, weekly, monthly (configurable).

### Minimum Required Data
- Approved staffing requirement records for the reporting period;
- Attendance records covering the reporting period;
- Required staff hours greater than zero.

### Eligibility Rules
- Approved staffing requirement must exist for the hospital, department, date, shift and staff role combination.
- Required staff hours must be greater than zero.
- Attendance records must fall within the reporting period.
- Hospital, department, date, shift and staff role must align between requirement and attendance.
- Duplicate attendance records must be resolved before calculation.
- Only active staff records (`is_active = true`) are eligible.
- Cancelled roster assignments must not be included.

### Missing-Data Rule
- If staffing requirement is missing, return `Not Available`.
- If attendance is incomplete, calculate only when completeness meets an approved minimum threshold; otherwise return `Data Quality Review Required`.
- Do not assume missing attendance means absence or presence.

### Exclusion Rules
- Cancelled roster entries.
- Inactive staff records.
- Duplicate unresolved attendance records.

### Department-Level Calculation
Calculate as: eligible actual available staff hours for the department divided by approved required staff hours for the department, multiplied by 100.

### Hospital-Level Aggregation
Use total eligible actual hours across included departments divided by total required hours across included departments. Do not average department percentages without weighting by required hours.

### Trend Interpretation
An increasing Staffing Level may indicate improved attendance, reduced leave or increased hiring relative to requirement. A decreasing trend may indicate rising absenteeism, workforce attrition or increased requirement without corresponding staffing adjustment. Trend must be interpreted alongside Staff Absenteeism Rate.

### Relationship to Other KPIs
- Inversely related to Staff Absenteeism Rate in the workforce domain.
- May be associated with Average Patient Waiting Time in the operations domain.
- These relationships indicate potential association, not proven causality.

### Prototype Limitations
- Partial-attendance weighting is not yet approved.
- Reassigned-staff eligibility mapping is pending configuration approval.
- Cross-department staff allocation is not yet modelled.

### Required Configuration
- `kpi_definition_config`: KPI code `WF_STAFF_LEVEL`
- `kpi_threshold_config`: thresholds for status classification (values pending approval)
- `staffing_requirement`: approved required hours

### Open Approval Items
- Final eligible attendance-status mapping (Present, Partial, Reassigned).
- Partial-attendance weighting rules.
- Fallback count-based staffing formula approval.
- Approved minimum data-completeness percentage.

---

## KPI 2: Staff Absenteeism Rate

### KPI Name
Staff Absenteeism Rate

### KPI Code
WF_ABSENTEEISM

### Business Domain
Workforce

### Business Question Answered
What proportion of scheduled staffing time was lost because scheduled staff were absent?

### Business Definition
Staff Absenteeism Rate measures the percentage of scheduled staff time that was lost due to absence during the reporting period. It compares absent scheduled time against total eligible scheduled time. Lower values indicate better workforce reliability and schedule adherence.

### Performance Direction
Lower Is Better

### Unit
Percent

### Primary Source Datasets
- `staff_roster.csv`
- `staff_attendance.csv`

### Supporting Datasets
- `staff_master.csv`
- `staff_role_master.csv`
- `department_master.csv`

### Numerator
Sum of scheduled hours classified as absence, derived from attendance records matched to scheduled shifts.

### Denominator
Sum of eligible scheduled hours from the staff roster for the reporting period.

### Formula

**Conceptual formula:**

```
Staff Absenteeism Rate (%) = (Absent Scheduled Staff Time / Total Eligible Scheduled Staff Time) * 100
```

**Preferred operational formula:**

```
Staff Absenteeism Rate (%) = (Sum of scheduled hours classified as absence / Sum of eligible scheduled hours) * 100
```

Attendance statuses and absence categories that count as absenteeism must remain configuration-driven.

### Preferred Calculation Grain
Scheduled shift.

### Supported Aggregation Levels
- Department level (preferred)
- Hospital level (by weighted aggregation across departments)

### Reporting Frequency
Daily, weekly, monthly (configurable).

### Minimum Required Data
- Staff roster records for the reporting period;
- Attendance records matched to scheduled shifts;
- Eligible scheduled hours greater than zero.

### Eligibility Rules
- The staff member must have an eligible scheduled assignment.
- Cancelled shifts must be excluded from the denominator.
- Denominator must be greater than zero.
- Absence records must match the scheduled shift (hospital, department, date, shift, staff).
- Duplicate roster or attendance records must be resolved.

### Missing-Data Rule
- If roster data are unavailable, return `Not Available`.
- If attendance status is missing for a scheduled shift, flag `Pending Review` for that record.
- Do not automatically classify missing attendance as absent.

### Exclusion Rules
- Cancelled shifts.
- Unmatched absence records without a corresponding scheduled shift.
- Duplicate unresolved records.

### Department-Level Calculation
Calculate as: absent scheduled hours for the department divided by eligible scheduled hours for the department, multiplied by 100.

### Hospital-Level Aggregation
Use total absent scheduled hours divided by total eligible scheduled hours. Do not average department absenteeism percentages without weighting by scheduled hours.

### Trend Interpretation
An increasing absenteeism rate may indicate deteriorating workforce health, morale or reliability. A decreasing rate may indicate improved attendance management or working conditions. Trend must be interpreted alongside Staffing Level.

### Relationship to Other KPIs
- Inversely related to Staffing Level in the workforce domain.
- May be associated with Average Patient Waiting Time if staffing shortages affect service delivery.
- These relationships indicate potential association, not proven causality.

### Prototype Limitations
- Absenteeism-category mapping is not yet approved.
- Partial absence is not yet modelled.
- Replacement staff logic is pending approval.

### Required Configuration
- `kpi_definition_config`: KPI code `WF_ABSENTEEISM`
- `kpi_threshold_config`: thresholds for status classification (values pending approval)
- `staff_roster`: scheduled shifts

### Open Approval Items
- Final absenteeism-category mapping (Sick Leave, Emergency Leave, Unauthorised, Other).
- Treatment of Annual Leave, Training, Reassigned and Not Scheduled statuses.
- Partial-absence handling rules.
- Replacement-staff logic.

---

## KPI 3: Bed Occupancy Rate

### KPI Name
Bed Occupancy Rate

### KPI Code
OP_BED_OCCUPANCY

### Business Domain
Operations

### Business Question Answered
What proportion of operational bed capacity was occupied during the reporting period?

### Business Definition
Bed Occupancy Rate measures the proportion of operational bed capacity that was occupied over the reporting period. It compares occupied bed capacity against operational bed capacity, expressed as a percentage. The denominator uses operational beds rather than licensed beds. Lower values generally indicate lower capacity pressure, unless an approved target range is later defined.

### Performance Direction
Lower Is Better unless an approved target range is later defined.

### Unit
Percent

### Primary Source Dataset
- `bed_capacity_records.csv`

### Supporting Datasets
- `hospital_master.csv`
- `department_master.csv`

### Numerator
Sum of occupied bed-time during the reporting period.

### Denominator
Sum of operational bed-time during the reporting period.

### Formula

**Conceptual formula:**

```
Bed Occupancy Rate (%) = (Occupied Bed Capacity / Operational Bed Capacity) * 100
```

**Preferred interval-based formula:**

```
Bed Occupancy Rate (%) = (Sum of occupied bed-time / Sum of operational bed-time) * 100
```

Where interval data are unavailable, approved daily snapshots may be used as a fallback.

### Preferred Calculation Grain
Bed-day or interval snapshot.

### Supported Aggregation Levels
- Department or ward level (preferred)
- Hospital level (by weighted aggregation across departments)

### Reporting Frequency
Daily, weekly, monthly (configurable).

### Minimum Required Data
- Bed capacity records for the reporting period;
- Operational bed count greater than zero;
- Occupied bed count available.

### Eligibility Rules
- Operational beds must be greater than zero.
- Occupied beds must be non-negative.
- Invalid capacity records must be rejected or flagged for review.
- Records with unresolved capacity exceptions must be flagged.
- Only departments classified as bed-based service areas are eligible.

### Missing-Data Rule
- If operational bed capacity is missing, return `Not Available`.
- Do not substitute licensed beds without an approved fallback rule.
- Incomplete intervals must reduce confidence or trigger `Data Quality Review Required`.

### Exclusion Rules
- Departments not classified as bed-based service areas.
- Invalid capacity records (negative values, operational beds equal to zero).
- Records with unresolved exceptions.

### Department-Level Calculation
Calculate as: occupied bed-time for the department divided by operational bed-time for the department, multiplied by 100.

### Hospital-Level Aggregation
Use total occupied bed-time divided by total operational bed-time. Do not average ward percentages without weighting by operational bed-time.

### Trend Interpretation
An increasing occupancy rate may indicate rising demand, reduced discharge efficiency or capacity constraints. A decreasing rate may indicate lower admission volume or improved bed turnover. Occupancy must be interpreted alongside waiting time and patient experience metrics.

### Relationship to Other KPIs
- May be associated with Average Patient Waiting Time if high occupancy delays admission.
- May be associated with patient experience metrics if overcrowding affects care quality.
- These relationships indicate potential association, not proven causality.

### Prototype Limitations
- Temporary closure handling is not yet modelled.
- Interval-gap handling is pending approval.
- Target range for occupancy is not yet defined.

### Required Configuration
- `kpi_definition_config`: KPI code `OP_BED_OCCUPANCY`
- `kpi_threshold_config`: thresholds for status classification (values pending approval)
- `bed_capacity_records`: operational and occupied bed counts

### Open Approval Items
- Approved fallback from interval data to daily snapshots.
- Treatment of temporary bed closures.
- Interval-gap handling rules.
- Approved target range for occupancy (if any).

---

## KPI 4: Average Patient Waiting Time

### KPI Name
Average Patient Waiting Time

### KPI Code
OP_WAIT_TIME

### Business Domain
Operations

### Business Question Answered
How long did patients wait before receiving the defined service?

### Business Definition
Average Patient Waiting Time measures the mean duration between patient arrival and the start of the defined service, for eligible served patients during the reporting period. It is expressed in minutes. Lower values indicate more timely service delivery.

### Performance Direction
Lower Is Better

### Unit
Minutes

### Primary Source Datasets
- `patient_queue_records.csv`
- `patient_encounters.csv`

### Supporting Datasets
- `service_schedule.csv`
- `department_master.csv`

### Numerator
Sum of eligible patient waiting minutes.

### Denominator
Count of eligible served patients.

### Formula

**Conceptual formula:**

```
Average Patient Waiting Time = Total eligible patient waiting minutes / Number of eligible served patients
```

**Preferred record-level calculation:**

```
Waiting Time = Service Start Datetime - Arrival Datetime
Average Patient Waiting Time = Sum of eligible waiting minutes / Count of eligible encounters
```

**When only queue-summary data are available:**

```
Weighted Average Waiting Time = Sum(average_wait_minutes * served_count) / Sum(served_count)
```

Do not calculate an unweighted average across queue summaries.

### Preferred Calculation Grain
Individual patient encounter or queue record.

### Supported Aggregation Levels
- Queue type or encounter type (preferred)
- Department level
- Hospital level (by weighted aggregation)

### Reporting Frequency
Hourly, daily, weekly, monthly (configurable).

### Minimum Required Data
- Arrival and service-start timestamps for eligible encounters;
- At least one eligible served patient;
- Approved minimum encounter count for reliable averaging.

### Eligibility Rules
- Arrival and service-start timestamps must be valid.
- Service-start datetime must not be earlier than arrival datetime.
- Cancelled encounters must be excluded.
- Approved rules must define treatment of patients who left before service.
- Waiting-time outliers must be flagged but not silently removed.
- Waiting stage must be clearly defined by queue type or encounter type.

### Missing-Data Rule
- Missing arrival or service-start timestamps make the encounter ineligible.
- If eligible encounter count is below an approved minimum, return `Insufficient Data`.
- Disclose the proportion of excluded encounters.

### Exclusion Rules
- Cancelled encounters.
- Encounters with invalid timestamps.
- Patients who left before service (pending approved rule).

### Department-Level Calculation
Calculate as: sum of eligible waiting minutes for the department divided by count of eligible encounters for the department.

### Hospital-Level Aggregation
Use all eligible encounter-level waiting minutes divided by all eligible encounters across included departments. Do not average department averages without weighting by eligible patient count.

### Trend Interpretation
An increasing waiting time may indicate insufficient capacity, staffing shortages or process inefficiency. A decreasing trend may indicate improved workflow, additional capacity or reduced demand. Must be interpreted alongside Staffing Level and Bed Occupancy Rate.

### Relationship to Other KPIs
- May be associated with Staffing Level if workforce shortages delay service.
- May be associated with Bed Occupancy Rate if admission delays increase queue time.
- May be associated with Patient Complaint Rate if long waits generate dissatisfaction.
- These relationships indicate potential association, not proven causality.

### Prototype Limitations
- Queue stage for official waiting-time KPI is not yet approved.
- Treatment of left-before-service encounters is pending approval.
- Outlier flagging rules are not yet defined.

### Required Configuration
- `kpi_definition_config`: KPI code `OP_WAIT_TIME`
- `kpi_threshold_config`: thresholds for status classification (values pending approval)
- `patient_queue_records` and `patient_encounters`: timestamps

### Open Approval Items
- Queue stage used for official waiting-time KPI.
- Treatment of patients who left before service.
- Waiting-time outlier thresholds.
- Approved minimum encounter count.

---

## KPI 5: Patient Complaint Rate

### KPI Name
Patient Complaint Rate

### KPI Code
PX_COMPLAINT_RATE

### Business Domain
Patient Experience

### Business Question Answered
How many valid patient complaints were recorded relative to service activity?

### Business Definition
Patient Complaint Rate measures the number of valid patient complaints per 1,000 eligible patient encounters during the reporting period. It compares complaint volume against service activity to provide a normalised measure of patient dissatisfaction. Lower values indicate fewer complaints relative to patient volume.

### Performance Direction
Lower Is Better

### Unit
Complaints per 1,000 eligible patient encounters

### Primary Source Datasets
- `patient_complaints.csv`
- `patient_encounters.csv`

### Supporting Datasets
- `department_master.csv`
- `hospital_master.csv`

### Numerator
Number of eligible valid complaints within the reporting period.

### Denominator
Number of eligible patient encounters for the same hospital, department and reporting period.

### Formula

```
Patient Complaint Rate = (Number of eligible valid complaints / Number of eligible patient encounters) * 1,000
```

**Numerator eligibility:**
Include valid complaint records within the reporting period. Exclude or separately handle: Duplicate, Rejected, Invalid and Test records. Final complaint-status eligibility must remain configuration-driven.

**Denominator eligibility:**
Use eligible patient encounters for the same hospital, department and reporting period.

### Preferred Calculation Grain
Individual complaint and individual encounter.

### Supported Aggregation Levels
- Department level (preferred)
- Hospital level (by weighted aggregation across departments)

### Reporting Frequency
Daily, weekly, monthly (configurable).

### Minimum Required Data
- Valid complaint records for the reporting period;
- Eligible encounter records for the reporting period;
- Denominator greater than zero.

### Eligibility Rules
- Denominator must be greater than zero.
- Complaint date must fall within the reporting period.
- Duplicate complaints must not be counted twice.
- Optional encounter linkage may be missing.
- Complaints without encounter linkage may still be counted when hospital, department and period are valid.

### Missing-Data Rule
- If encounter volume is unavailable, return `Not Available`.
- Do not replace encounter denominator with survey responses.
- Disclose unresolved duplicate or rejected complaint records.

### Exclusion Rules
- Duplicate complaints (pending resolution).
- Rejected or invalid complaints.
- Test records.
- Complaints outside the reporting period.

### Department-Level Calculation
Calculate as: valid complaints for the department divided by eligible encounters for the department, multiplied by 1,000.

### Hospital-Level Aggregation
Use total valid complaints divided by total eligible encounters, multiplied by 1,000. Do not average department complaint rates without denominator weighting by encounter count.

### Trend Interpretation
An increasing complaint rate may indicate deteriorating service quality, capacity pressure or communication failures. A decreasing rate may indicate service improvements or better expectation management. Must be interpreted alongside Patient Satisfaction Score and Average Patient Waiting Time.

### Relationship to Other KPIs
- May be associated with Average Patient Waiting Time if long waits generate complaints.
- May be inversely associated with Patient Satisfaction Score.
- These relationships indicate potential association, not proven causality.

### Prototype Limitations
- Complaint eligibility statuses are pending configuration approval.
- Duplicate-complaint resolution logic is not yet defined.
- Social-media complaints are not yet included.

### Required Configuration
- `kpi_definition_config`: KPI code `PX_COMPLAINT_RATE`
- `kpi_threshold_config`: thresholds for status classification (values pending approval)
- `patient_complaints`: complaint records and status
- `patient_encounters`: encounter volume

### Open Approval Items
- Final complaint eligibility statuses.
- Duplicate-complaint resolution rules.
- Treatment of complaints without encounter linkage.
- Social-media complaint inclusion rules.

---

## KPI 6: Patient Satisfaction Score

### KPI Name
Patient Satisfaction Score

### KPI Code
PX_SATISFACTION

### Business Domain
Patient Experience

### Business Question Answered
What was the weighted patient satisfaction result for the reporting period?

### Business Definition
Patient Satisfaction Score measures the normalised, weighted average of valid patient survey responses for the reporting period. The source survey scale may vary by instrument, so all scores are normalised to a 0-100 percent scale before aggregation. Higher values indicate greater patient satisfaction.

### Performance Direction
Higher Is Better

### Unit
Normalised Percent Score

### Primary Source Dataset
- `patient_surveys.csv`

### Supporting Datasets
- `patient_encounters.csv`
- `department_master.csv`
- `hospital_master.csv`

### Numerator
Sum of normalised response scores multiplied by response weight.

### Denominator
Sum of response weights.

### Formula

**Normalisation formula (per response):**

```
Normalised Satisfaction Score (%) = ((Observed Score - Scale Minimum) / (Scale Maximum - Scale Minimum)) * 100
```

**Aggregation formula (multiple eligible responses):**

```
Weighted Patient Satisfaction Score (%) = Sum(normalised response score * response weight) / Sum(response weight)
```

Where every response has equal weight, `response_weight` equals 1.

### Preferred Calculation Grain
Individual survey response.

### Supported Aggregation Levels
- Department level (preferred)
- Hospital level (by weighted aggregation across departments)

### Reporting Frequency
Weekly, monthly (configurable).

### Minimum Required Data
- Valid survey responses for the reporting period;
- Scale minimum and maximum for each response;
- At least one valid eligible response.

### Eligibility Rules
- Response status must be `Valid`.
- Scale minimum and maximum must be available.
- Scale maximum must be greater than scale minimum.
- Score must fall within the declared scale.
- Duplicate and incomplete responses must be excluded.
- Response weight must be positive.

### Missing-Data Rule
- If no valid eligible response exists, return `Insufficient Data`.
- If the valid response count is below an approved minimum, label `Low Confidence`.
- Do not infer missing responses.
- Disclose survey-response volume alongside the KPI.

### Exclusion Rules
- Incomplete responses.
- Duplicate responses.
- Responses with invalid scale.
- Responses with negative or zero weight.
- Responses outside the reporting period.

### Department-Level Calculation
Calculate as: sum of weighted normalised scores for the department divided by sum of weights for the department.

### Hospital-Level Aggregation
Use weighted eligible responses across departments. Do not average department satisfaction scores without response weighting.

### Trend Interpretation
An increasing satisfaction score may indicate improved care quality, communication or environment. A decreasing score may indicate service deterioration or unmet expectations. Must be interpreted alongside Patient Complaint Rate and Average Patient Waiting Time.

### Relationship to Other KPIs
- May be inversely associated with Patient Complaint Rate.
- May be associated with Average Patient Waiting Time if wait duration affects satisfaction.
- These relationships indicate potential association, not proven causality.

### Prototype Limitations
- Survey minimum-response rule is pending approval.
- Mixed survey-scale handling is approved conceptually but not yet configured.
- Very low response volumes may produce unstable scores.

### Required Configuration
- `kpi_definition_config`: KPI code `PX_SATISFACTION`
- `kpi_threshold_config`: thresholds for status classification (values pending approval)
- `patient_surveys`: survey responses with scale and weight

### Open Approval Items
- Survey minimum-response rule for reliable calculation.
- Low-confidence labelling threshold.
- Handling of mixed survey scales within the same reporting period.
- Department attribution when department is not supplied.

---

## Cross-KPI Interpretation

The six headline KPIs must first be calculated independently from their respective source datasets. Each KPI has its own numerator, denominator, eligibility rules and missing-data treatment.

After independent calculation, cross-domain relationships may be evaluated to identify patterns of connected deterioration or improvement. These relationships are observational and must not be described as proven causality. Potential associations that may be explored in later phases include:

- Higher absenteeism with lower staffing level: workforce stress may simultaneously reduce availability and increase absence.
- Lower staffing level with longer waiting time: reduced service capacity may delay patient service.
- Higher waiting time with higher complaint rate: extended waits may generate patient dissatisfaction expressed as complaints.
- Higher complaint rate with lower satisfaction: expressed dissatisfaction may correlate with lower overall satisfaction scores.
- Higher occupancy with longer waiting time: capacity pressure may delay admissions and service.
- Capacity pressure with worsening patient experience: operational strain may degrade the patient experience across multiple metrics.

Any cross-KPI analysis must:
- State clearly that association does not prove causation.
- Identify the time lag between cause and effect (if any).
- Control for confounding variables where possible.
- Be reviewed by human management before action.

---

## Document Control

| Property | Value |
|---|---|
| Document Version | 1.0 |
| Phase | Phase 1, Step 1F |
| Status | Draft - Pending Approval |
| Next Review | Phase 1, Step 1G |
| Unresolved Items | Threshold values; attendance-status mapping; partial-attendance weighting; absenteeism-category mapping; fallback formulas; queue-stage definition; complaint eligibility; survey minimum-response rule |
