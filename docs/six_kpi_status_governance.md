# Six-KPI Status Governance

## Step 2A-5

---

## 1. Status Dimensions

The integration layer maintains ten separate status dimensions. Each dimension is governed independently and must not be merged into an ambiguous composite field.

### 1.1 calculation_status

Represents the outcome of the KPI calculation engine.

| Value | Meaning |
|-------|---------|
| Calculated | Formula executed successfully; value is available. |
| Insufficient Data | Required source data was missing or incomplete. |
| Zero Denominator | Denominator was zero; division impossible. |
| Configuration Missing | Required configuration was not found. |
| Rule Pending | Business rule not yet approved or defined. |
| Invalid Input | Source data failed validity checks. |
| Not Calculated | Explicitly skipped or not applicable. |

Rules:
- A non-null KPI value should normally have calculation_status = Calculated.
- A null KPI value must retain its accepted non-calculated status.
- Do not convert unavailable records to zero.

### 1.2 readiness_status

Represents the readiness of the KPI for reporting.

| Value | Meaning |
|-------|---------|
| Calculable | All required inputs and configurations are present. |
| Provisional but Calculable | Denominator or configuration is provisional but usable. |
| Not Calculable | Missing required inputs or configurations. |
| PX Data Unavailable | Patient experience data not available for grain. |

### 1.3 threshold_status

Represents the position of the KPI value relative to governed thresholds.

| Value | Meaning |
|-------|---------|
| Green | Within acceptable range. |
| Amber | Warning range. |
| Red | Critical range. |
| Not Assessed | Thresholds not yet applied or bounds missing. |
| Unavailable | Threshold configuration unavailable. |
| Configuration Missing | Threshold config missing. |

Rules:
- No Green, Amber, or Red may be assigned when kpi_value is null.
- No Green, Amber, or Red may be assigned when calculation_status is not Calculated.
- Draft thresholds must remain visibly provisional.

Current state: all records are Not Assessed because thresholds are v1.0-draft.

### 1.4 threshold_approval_status

Represents the governance approval state of the threshold configuration.

| Value | Meaning |
|-------|---------|
| Draft | Under development; not approved. |
| Pending Stakeholder Validation | Awaiting review. |
| Approved | Formally approved. |
| Rejected | Formally rejected. |

Current state: Draft for all records.

### 1.5 threshold_is_provisional

Boolean flag indicating whether the threshold is provisional.

Current state: True for all records.

### 1.6 data_confidence_level

Represents the assessed confidence in the KPI result.

| Value | Meaning |
|-------|---------|
| High | Strong evidence, complete data, valid formulas. |
| Medium | Acceptable evidence, minor gaps. |
| Low | Significant gaps or concerns. |
| Unavailable | KPI not calculated; confidence cannot be assessed. |
| Not Assessed | Confidence rules not yet applied. |

Rules:
- Unavailable KPI records must not be labelled High.
- Preserve confidence-rule version.

### 1.7 confidence_is_provisional

Boolean flag indicating whether the confidence rule is provisional.

Current state: True for all records.

### 1.8 integration_status

Represents the outcome of the integration process.

| Value | Meaning |
|-------|---------|
| Integrated | Accepted record; all validations passed. |
| Integrated with Warning | Accepted record; non-blocking limitation exists. |
| Excluded | Duplicate, unknown KPI, or unrecoverable key problem. |
| Failed Validation | Blocking schema defect or inconsistency. |

Rules:
- Provisional threshold is a warning, not a failure.
- Unavailable result is a warning, not a failure.
- Calculated + null is a blocking failure.
- Threshold color + null is a blocking failure.

### 1.9 evidence_status

Represents the completeness of evidence for the integrated result.

| Value | Meaning |
|-------|---------|
| Complete | Expected evidence present and linked. |
| Partial | Some evidence exists but one component is unavailable. |
| Unavailable | KPI unavailable; evidence correctly records why. |
| Missing | Calculated KPI lacks required evidence. |
| Invalid | Evidence references unknown record or is malformed. |

### 1.10 lineage_status

Represents the completeness of lineage for the integrated result.

| Value | Meaning |
|-------|---------|
| Complete | Integrated result links to accepted source. |
| Partial | Aggregation design prevents record-level linkage. |
| Unavailable | KPI unavailable; no record-level source contribution. |
| Broken | Referenced analytical record does not exist. |

---

## 2. Permitted Status Combinations

### 2.1 Normal Operating States

| calculation_status | threshold_status | data_confidence_level | integration_status |
|--------------------|------------------|-----------------------|--------------------|
| Calculated | Not Assessed | High / Medium / Low | Integrated / Integrated with Warning |
| Insufficient Data | Not Assessed | Unavailable | Integrated with Warning |
| Zero Denominator | Not Assessed | Unavailable | Integrated with Warning |

### 2.2 Prohibited Combinations

| Condition | Reason |
|-----------|--------|
| Calculated + null kpi_value | Blocking inconsistency |
| Green/Amber/Red + null kpi_value | Threshold color requires a value |
| Green/Amber/Red + non-Calculated | Threshold color requires calculated status |
| High confidence + unavailable KPI | Unavailable results cannot be High confidence |

---

## 3. Provisional Governance Treatment

All thresholds, confidence rules, and configurations are currently v1.0-draft.

Requirements:
- provisional flag must be True.
- approval status must be Draft or Pending Stakeholder Validation.
- no provisional threshold may be presented as formally approved.
- integration status may be Integrated with Warning due to provisional governance.

---

## 4. Status Normalization Rules

During integration:
- Spelling and capitalization are standardized.
- Accepted statuses are not reinterpreted.
- Inconsistencies are logged as structured issues.
- No status is fabricated.

---

## 5. Issue Severity Mapping

| Issue Type | Default Severity |
|------------|------------------|
| Unknown KPI ID | Error |
| Duplicate Integration Key | Error |
| Value Status Inconsistency | Error |
| Threshold Status Inconsistency | Error |
| Confidence Inconsistency | Warning |
| Missing Evidence | Warning |
| Broken Lineage | Error |

---

## 6. Coverage Status Definitions

| Status | Condition |
|--------|-----------|
| Complete | All 6 KPIs present for grain. |
| Partial | 1-5 KPIs present for grain. |
| No Applicable Data | 0 KPIs present for grain. |
| Failed | Blocking validation failure for grain. |

Current state: Complete for all 2,920 grains.

---

## 7. Audit Trail

Every status assignment is auditable through:
- integration_run_id
- source_calculation_run_id
- source_analytical_dataset
- source_analytical_record_id
- integration timestamp

---

## 8. Change Control

Status dimensions may only be modified by:
- Re-running the integration engine with updated source data.
- Formal governance approval changing threshold or confidence rules.
- Explicit exclusion or inclusion rule changes.

No manual editing of integrated status fields is permitted.
