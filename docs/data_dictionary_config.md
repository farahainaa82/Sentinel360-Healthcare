# Data Dictionary — Configuration and Assumption Datasets

## Common Configuration Fields

Every configuration dataset includes the following fields:

| Field Name | Business Definition | Data Type | Required | Allowed Values or Domain | Validation Rule | Example Format | Notes |
|---|---|---|---|---|---|---|---|
| configuration_version | Version identifier for this configuration record | string | Yes | Free text | Must be non-blank; max 50 characters | "CONFIG_V1" | Changed on every approved update |
| effective_start_date | Date from which this configuration is valid | date | Yes | ISO 8601 date | Must be valid; not in the future | "2026-01-01" | |
| effective_end_date | Date after which this configuration is no longer valid | date | Optional | ISO 8601 date or blank | If present, must be >= effective_start_date | "2099-12-31" | |
| active_flag | Whether this configuration is currently active | boolean | Yes | true, false | Must be boolean | true | |
| approval_status | Current approval state of the configuration | string | Yes | Draft, Under Review, Approved, Retired | Must match domain | "Approved" | Only Approved may be used for official calculations |
| approved_by_role | Role that approved this configuration | string | Optional | Free text | Max 100 characters | "Medical Director" | |
| approval_date | Date of approval | date | Optional | ISO 8601 date or blank | If present, must be valid | "2026-01-15" | |
| change_reason | Reason for the configuration change | string | Optional | Free text | Max 500 characters | "Updated threshold based on Q1 review" | |
| created_datetime | When the record was created | datetime | Yes | ISO 8601 datetime | Must be valid | "2026-01-10T09:00:00" | |
| updated_datetime | When the record was last updated | datetime | Yes | ISO 8601 datetime | Must be valid; >= created_datetime | "2026-01-15T14:00:00" | |

---

## 1. kpi_definition_config.csv

### Dataset Overview

| Attribute | Value |
|---|---|
| Dataset name | kpi_definition_config |
| File name | kpi_definition_config.csv |
| Purpose | Contains approved KPI definitions, direction of good performance, units and aggregation frequency |
| Grain | One record per KPI |
| Primary key | kpi_id |
| Foreign keys | None |
| Required or optional | Required |
| Refresh frequency | On change |
| Prototype source | Manual upload |
| Future production source | Configuration management |
| Sensitivity | Low |
| Main consumers | All KPI calculations |
| Governance owner | Farah |
| Editability | Viewable; editing restricted to approved configuration workflow |

### Field Dictionary

| Field Name | Business Definition | Data Type | Required | Primary Key | Foreign Key | Allowed Values or Domain | Validation Rule | Example Format | Notes |
|---|---|---|---|---|---|---|---|---|---|
| kpi_id | Unique identifier for the KPI | string | Yes | Yes | No | Alphanumeric, unique | Must be unique and non-blank | "KPI_STAFF_LVL" | |
| kpi_code | Short code for the KPI | string | Yes | No | No | Alphanumeric | Must be unique; max 50 characters | "STAFF_LVL" | |
| kpi_name | Human-readable name | string | Yes | No | No | Non-empty text | Max 200 characters | "Staffing Level" | |
| kpi_description | Detailed description | string | Yes | No | No | Free text | Max 1000 characters | "Ratio of actual to required staff" | |
| business_domain | Domain classification | string | Yes | No | No | Workforce, Operations, Patient Experience | Must match domain | "Workforce" | |
| unit | Unit of measurement | string | Yes | No | No | Count, Percentage, Hours, Minutes, Score, Ratio, FTE, Other | Must match domain | "Ratio" | |
| aggregation_frequency | Standard reporting frequency | string | Yes | No | No | Daily, Weekly, Monthly, Shift, Other | Must match domain | "Daily" | |
| performance_direction | Whether higher or lower is better | string | Yes | No | No | Higher Is Better, Lower Is Better, Target Range | Must match domain | "Target Range" | |
| numerator_definition | Business definition of the numerator | string | Optional | No | No | Free text | Max 1000 characters | "Actual staff count" | Formula pending approval |
| denominator_definition | Business definition of the denominator | string | Optional | No | No | Free text | Max 1000 characters | "Required staff count" | Formula pending approval |
| department_level_flag | Whether the KPI can be calculated at department level | boolean | Yes | No | No | true, false | Must be boolean | true | |
| hospital_level_flag | Whether the KPI can be calculated at hospital level | boolean | Yes | No | No | true, false | Must be boolean | true | |
| minimum_history_periods | Minimum historical observations needed for trend analysis | integer | Optional | No | No | 0 to 999 | If present, must be >= 0 | 30 | |
| missing_data_rule | How to handle missing data | string | Optional | No | No | Exclude, Impute, Flag, Use Available | Must match domain if provided | "Use Available" | |
| owner_role | Role responsible for this KPI definition | string | Optional | No | No | Free text | Max 100 characters | "Medical Director" | |
| configuration_version | Configuration version | string | Yes | No | No | Free text | Max 50 characters | "CONFIG_V1" | Common config field |
| effective_start_date | Valid from | date | Yes | No | No | ISO 8601 date | Must be valid | "2026-01-01" | Common config field |
| effective_end_date | Valid to | date | Optional | No | No | ISO 8601 date or blank | If present, >= effective_start_date | "2099-12-31" | Common config field |
| active_flag | Active flag | boolean | Yes | No | No | true, false | Must be boolean | true | Common config field |
| approval_status | Approval status | string | Yes | No | No | Draft, Under Review, Approved, Retired | Must match domain | "Approved" | Common config field |
| approved_by_role | Approver role | string | Optional | No | No | Free text | Max 100 characters | "Medical Director" | Common config field |
| approval_date | Approval date | date | Optional | No | No | ISO 8601 date or blank | If present, must be valid | "2026-01-15" | Common config field |
| change_reason | Change reason | string | Optional | No | No | Free text | Max 500 characters | "Initial definition" | Common config field |
| created_datetime | Creation timestamp | datetime | Yes | No | No | ISO 8601 datetime | Must be valid | "2026-01-10T09:00:00" | Common config field |
| updated_datetime | Update timestamp | datetime | Yes | No | No | ISO 8601 datetime | Must be >= created_datetime | "2026-01-15T14:00:00" | Common config field |

### Dataset-Level Validation Rules

- kpi_id and kpi_code must each be unique.
- business_domain, unit, aggregation_frequency, performance_direction must match approved domains.
- effective_end_date, if present, must be >= effective_start_date.
- Only records with approval_status = "Approved" and active_flag = true may be used for official calculations.

### Downstream Impact

- All KPI calculations depend on this dataset.
- Changes require recalculation of kpi_observations.

### Unresolved Items

- Exact numerator and denominator formulas pending Phase 1 Step 1F.
- Final domain values for unit and aggregation_frequency pending approval.

---

## 2. kpi_threshold_config.csv

### Dataset Overview

| Attribute | Value |
|---|---|
| Dataset name | kpi_threshold_config |
| File name | kpi_threshold_config.csv |
| Purpose | Contains warning and critical boundaries by KPI and potentially by hospital or department |
| Grain | One record per threshold configuration |
| Primary key | threshold_config_id |
| Foreign keys | kpi_id, hospital_id, department_id |
| Required or optional | Required |
| Refresh frequency | On change |
| Prototype source | Manual upload |
| Future production source | Configuration management |
| Sensitivity | Medium |
| Main consumers | KPI status classification, risk detection |
| Governance owner | Farah |
| Editability | Viewable; editing restricted to approved configuration workflow |

### Field Dictionary

| Field Name | Business Definition | Data Type | Required | Primary Key | Foreign Key | Allowed Values or Domain | Validation Rule | Example Format | Notes |
|---|---|---|---|---|---|---|---|---|---|
| threshold_config_id | Unique identifier for the threshold configuration | string | Yes | Yes | No | Alphanumeric, unique | Must be unique and non-blank | "THR_001" | |
| kpi_id | KPI to which this threshold applies | string | Yes | No | Yes | kpi_definition_config.kpi_id | Must exist in kpi_definition_config | "KPI_STAFF_LVL" | |
| hospital_id | Hospital scope | string | Optional | No | Yes | hospital_master.hospital_id | If present, must exist in hospital_master | "HSP_001" | |
| department_id | Department scope | string | Optional | No | Yes | department_master.department_id | If present, must exist in department_master | "DEPT_ER_001" | |
| threshold_scope | Scope level of the threshold | string | Yes | No | No | Global, Hospital, Department | Must match domain | "Department" | |
| warning_lower_bound | Lower warning boundary | decimal | Optional | No | No | Numeric | If present, must be <= critical_lower_bound | 0.8 | Values pending approval |
| warning_upper_bound | Upper warning boundary | decimal | Optional | No | No | Numeric | If present, must be >= critical_upper_bound | 1.2 | Values pending approval |
| critical_lower_bound | Lower critical boundary | decimal | Optional | No | No | Numeric | If present, must be <= warning_lower_bound | 0.6 | Values pending approval |
| critical_upper_bound | Upper critical boundary | decimal | Optional | No | No | Numeric | If present, must be >= warning_upper_bound | 1.4 | Values pending approval |
| threshold_unit | Unit of the threshold value | string | Yes | No | No | Same domain as kpi_definition_config.unit | Must match approved unit | "Ratio" | |
| threshold_basis | Basis for the threshold | string | Optional | No | No | Historical, Regulatory, Benchmark, Expert Judgement, Other | Must match domain if provided | "Benchmark" | |
| configuration_version | Configuration version | string | Yes | No | No | Free text | Max 50 characters | "CONFIG_V1" | Common config field |
| effective_start_date | Valid from | date | Yes | No | No | ISO 8601 date | Must be valid | "2026-01-01" | Common config field |
| effective_end_date | Valid to | date | Optional | No | No | ISO 8601 date or blank | If present, >= effective_start_date | "2099-12-31" | Common config field |
| active_flag | Active flag | boolean | Yes | No | No | true, false | Must be boolean | true | Common config field |
| approval_status | Approval status | string | Yes | No | No | Draft, Under Review, Approved, Retired | Must match domain | "Approved" | Common config field |
| approved_by_role | Approver role | string | Optional | No | No | Free text | Max 100 characters | "Medical Director" | Common config field |
| approval_date | Approval date | date | Optional | No | No | ISO 8601 date or blank | If present, must be valid | "2026-01-15" | Common config field |
| change_reason | Change reason | string | Optional | No | No | Free text | Max 500 characters | "Initial thresholds" | Common config field |
| created_datetime | Creation timestamp | datetime | Yes | No | No | ISO 8601 datetime | Must be valid | "2026-01-10T09:00:00" | Common config field |
| updated_datetime | Update timestamp | datetime | Yes | No | No | ISO 8601 datetime | Must be >= created_datetime | "2026-01-15T14:00:00" | Common config field |

### Dataset-Level Validation Rules

- threshold_config_id must be unique.
- kpi_id must exist in kpi_definition_config.
- hospital_id and department_id, if present, must exist in respective master datasets.
- threshold_scope must be consistent with presence of hospital_id and department_id.
- warning_lower_bound <= critical_lower_bound when both are present.
- warning_upper_bound >= critical_upper_bound when both are present.
- Only Approved and active records used for calculations.

### Downstream Impact

- kpi_status_results, warning events, risk detection.

### Unresolved Items

- Threshold values pending Farah approval.
- Final boundary definitions pending Phase 1 Step 1F.

---

## 3. anomaly_detection_config.csv

### Dataset Overview

| Attribute | Value |
|---|---|
| Dataset name | anomaly_detection_config |
| File name | anomaly_detection_config.csv |
| Purpose | Contains approved anomaly-method settings |
| Grain | One record per anomaly configuration |
| Primary key | anomaly_config_id |
| Foreign keys | kpi_id |
| Required or optional | Required |
| Refresh frequency | On change |
| Prototype source | Manual upload |
| Future production source | Configuration management |
| Sensitivity | Medium |
| Main consumers | Anomaly detection |
| Governance owner | Farah |
| Editability | Viewable; editing restricted |

### Field Dictionary

| Field Name | Business Definition | Data Type | Required | Primary Key | Foreign Key | Allowed Values or Domain | Validation Rule | Example Format | Notes |
|---|---|---|---|---|---|---|---|---|---|
| anomaly_config_id | Unique identifier | string | Yes | Yes | No | Alphanumeric, unique | Must be unique and non-blank | "ANO_001" | |
| kpi_id | KPI to which this applies | string | Yes | No | Yes | kpi_definition_config.kpi_id | Must exist in kpi_definition_config | "KPI_STAFF_LVL" | |
| method_name | Name of the anomaly detection method | string | Yes | No | No | Z-Score, IQR, Moving Average, Other | Must match domain | "Z-Score" | Method pending approval |
| lookback_periods | Number of periods to look back | integer | Yes | No | No | 1 to 999 | Must be >= 1 | 30 | |
| minimum_history_periods | Minimum observations required | integer | Yes | No | No | 1 to 999 | Must be >= 1 and <= lookback_periods | 14 | |
| sensitivity_level | Sensitivity setting | string | Yes | No | No | Low, Medium, High | Must match domain | "Medium" | |
| parameter_json | Additional method parameters in JSON | string | Optional | No | No | Valid JSON | Must be valid JSON if present | "{\"z_threshold\": 2.0}" | Parameters pending approval |
| missing_data_tolerance | Maximum proportion of missing data allowed | decimal | Optional | No | No | 0.0 to 1.0 | If present, must be >= 0 and <= 1 | 0.2 | |
| enabled_flag | Whether this configuration is enabled | boolean | Yes | No | No | true, false | Must be boolean | true | |
| configuration_version | Configuration version | string | Yes | No | No | Free text | Max 50 characters | "CONFIG_V1" | Common config field |
| effective_start_date | Valid from | date | Yes | No | No | ISO 8601 date | Must be valid | "2026-01-01" | Common config field |
| effective_end_date | Valid to | date | Optional | No | No | ISO 8601 date or blank | If present, >= effective_start_date | "2099-12-31" | Common config field |
| active_flag | Active flag | boolean | Yes | No | No | true, false | Must be boolean | true | Common config field |
| approval_status | Approval status | string | Yes | No | No | Draft, Under Review, Approved, Retired | Must match domain | "Approved" | Common config field |
| approved_by_role | Approver role | string | Optional | No | No | Free text | Max 100 characters | "Medical Director" | Common config field |
| approval_date | Approval date | date | Optional | No | No | ISO 8601 date or blank | If present, must be valid | "2026-01-15" | Common config field |
| change_reason | Change reason | string | Optional | No | No | Free text | Max 500 characters | "Initial config" | Common config field |
| created_datetime | Creation timestamp | datetime | Yes | No | No | ISO 8601 datetime | Must be valid | "2026-01-10T09:00:00" | Common config field |
| updated_datetime | Update timestamp | datetime | Yes | No | No | ISO 8601 datetime | Must be >= created_datetime | "2026-01-15T14:00:00" | Common config field |

### Dataset-Level Validation Rules

- anomaly_config_id must be unique.
- kpi_id must exist in kpi_definition_config.
- minimum_history_periods <= lookback_periods.
- Only Approved, active and enabled records used for calculations.

### Downstream Impact

- anomaly_results.

### Unresolved Items

- Final anomaly method and parameters pending Farah approval.

---

## 4. risk_rule_config.csv

### Dataset Overview

| Attribute | Value |
|---|---|
| Dataset name | risk_rule_config |
| File name | risk_rule_config.csv |
| Purpose | Contains approved cross-domain relationship rules |
| Grain | One record per risk rule |
| Primary key | risk_rule_id |
| Foreign keys | source_kpi_id, related_kpi_id |
| Required or optional | Required |
| Refresh frequency | On change |
| Prototype source | Manual upload |
| Future production source | Configuration management |
| Sensitivity | Medium |
| Main consumers | Cross-domain risk analysis |
| Governance owner | Farah |
| Editability | Viewable; editing restricted |

### Field Dictionary

| Field Name | Business Definition | Data Type | Required | Primary Key | Foreign Key | Allowed Values or Domain | Validation Rule | Example Format | Notes |
|---|---|---|---|---|---|---|---|---|---|
| risk_rule_id | Unique identifier for the risk rule | string | Yes | Yes | No | Alphanumeric, unique | Must be unique and non-blank | "RISK_001" | |
| risk_rule_name | Human-readable name | string | Yes | No | No | Non-empty text | Max 200 characters | "Staffing-Bed Occupancy Link" | |
| source_domain | Domain of the source signal | string | Yes | No | No | Workforce, Operations, Patient Experience | Must match domain | "Workforce" | |
| source_kpi_id | KPI that triggers the rule | string | Yes | No | Yes | kpi_definition_config.kpi_id | Must exist in kpi_definition_config | "KPI_STAFF_LVL" | |
| related_domain | Domain of the related signal | string | Yes | No | No | Workforce, Operations, Patient Experience | Must match domain | "Operations" | |
| related_kpi_id | KPI that is related | string | Yes | No | Yes | kpi_definition_config.kpi_id | Must exist in kpi_definition_config | "KPI_BED_OCC" | |
| relationship_type | Type of relationship | string | Yes | No | No | Contributes To, Amplifies, Follows, Co-occurs With, Potentially Related | Must match domain | "Contributes To" | |
| activation_condition | Condition under which the rule activates | string | Optional | No | No | Free text | Max 1000 characters | "Source KPI critical AND related KPI warning" | Expression pending approval |
| evidence_window | Period over which evidence is evaluated | integer | Optional | No | No | 1 to 999 | If present, must be >= 1 | 7 | |
| priority | Rule priority for ordering | integer | Optional | No | No | 1 to 100 | If present, must be >= 1 and <= 100 | 5 | |
| enabled_flag | Whether the rule is enabled | boolean | Yes | No | No | true, false | Must be boolean | true | |
| rule_description | Detailed description | string | Optional | No | No | Free text | Max 1000 characters | "Low staffing may contribute to high bed occupancy" | |
| configuration_version | Configuration version | string | Yes | No | No | Free text | Max 50 characters | "CONFIG_V1" | Common config field |
| effective_start_date | Valid from | date | Yes | No | No | ISO 8601 date | Must be valid | "2026-01-01" | Common config field |
| effective_end_date | Valid to | date | Optional | No | No | ISO 8601 date or blank | If present, >= effective_start_date | "2099-12-31" | Common config field |
| active_flag | Active flag | boolean | Yes | No | No | true, false | Must be boolean | true | Common config field |
| approval_status | Approval status | string | Yes | No | No | Draft, Under Review, Approved, Retired | Must match domain | "Approved" | Common config field |
| approved_by_role | Approver role | string | Optional | No | No | Free text | Max 100 characters | "Medical Director" | Common config field |
| approval_date | Approval date | date | Optional | No | No | ISO 8601 date or blank | If present, must be valid | "2026-01-15" | Common config field |
| change_reason | Change reason | string | Optional | No | No | Free text | Max 500 characters | "Initial rules" | Common config field |
| created_datetime | Creation timestamp | datetime | Yes | No | No | ISO 8601 datetime | Must be valid | "2026-01-10T09:00:00" | Common config field |
| updated_datetime | Update timestamp | datetime | Yes | No | No | ISO 8601 datetime | Must be >= created_datetime | "2026-01-15T14:00:00" | Common config field |

### Dataset-Level Validation Rules

- risk_rule_id must be unique.
- source_kpi_id and related_kpi_id must exist in kpi_definition_config.
- source_kpi_id and related_kpi_id should not be identical unless explicitly allowed.
- Only Approved, active and enabled records used for calculations.

### Downstream Impact

- cross_domain_risk_signals.

### Unresolved Items

- activation_condition syntax and evaluation logic pending approval.

---

## 5. risk_scoring_config.csv

### Dataset Overview

| Attribute | Value |
|---|---|
| Dataset name | risk_scoring_config |
| File name | risk_scoring_config.csv |
| Purpose | Contains approved risk-prioritisation components and weights |
| Grain | One record per scoring component |
| Primary key | risk_scoring_component_id |
| Foreign keys | None |
| Required or optional | Required |
| Refresh frequency | On change |
| Prototype source | Manual upload |
| Future production source | Configuration management |
| Sensitivity | Medium |
| Main consumers | Risk prioritisation |
| Governance owner | Farah |
| Editability | Viewable; editing restricted |

### Field Dictionary

| Field Name | Business Definition | Data Type | Required | Primary Key | Foreign Key | Allowed Values or Domain | Validation Rule | Example Format | Notes |
|---|---|---|---|---|---|---|---|---|---|
| risk_scoring_component_id | Unique identifier for the component | string | Yes | Yes | No | Alphanumeric, unique | Must be unique and non-blank | "RSC_001" | |
| component_name | Name of the scoring component | string | Yes | No | No | Non-empty text | Max 200 characters | "Current Severity" | |
| component_description | Description | string | Optional | No | No | Free text | Max 1000 characters | "Severity of the current KPI status" | |
| component_weight | Weight applied to this component | decimal | Optional | No | No | 0.0 to 10.0 | If present, must be >= 0 | Pending approval | Values pending approval |
| minimum_score | Minimum possible score for this component | decimal | Optional | No | No | Numeric | If present, must be <= maximum_score | 0 | |
| maximum_score | Maximum possible score for this component | decimal | Optional | No | No | Numeric | If present, must be >= minimum_score | 10 | |
| scoring_method | How the component is scored | string | Optional | No | No | Direct, Normalised, Ranked, Other | Must match domain if provided | "Direct" | |
| enabled_flag | Whether the component is enabled | boolean | Yes | No | No | true, false | Must be boolean | true | |
| configuration_version | Configuration version | string | Yes | No | No | Free text | Max 50 characters | "CONFIG_V1" | Common config field |
| effective_start_date | Valid from | date | Yes | No | No | ISO 8601 date | Must be valid | "2026-01-01" | Common config field |
| effective_end_date | Valid to | date | Optional | No | No | ISO 8601 date or blank | If present, >= effective_start_date | "2099-12-31" | Common config field |
| active_flag | Active flag | boolean | Yes | No | No | true, false | Must be boolean | true | Common config field |
| approval_status | Approval status | string | Yes | No | No | Draft, Under Review, Approved, Retired | Must match domain | "Approved" | Common config field |
| approved_by_role | Approver role | string | Optional | No | No | Free text | Max 100 characters | "Medical Director" | Common config field |
| approval_date | Approval date | date | Optional | No | No | ISO 8601 date or blank | If present, must be valid | "2026-01-15" | Common config field |
| change_reason | Change reason | string | Optional | No | No | Free text | Max 500 characters | "Initial scoring" | Common config field |
| created_datetime | Creation timestamp | datetime | Yes | No | No | ISO 8601 datetime | Must be valid | "2026-01-10T09:00:00" | Common config field |
| updated_datetime | Update timestamp | datetime | Yes | No | No | ISO 8601 datetime | Must be >= created_datetime | "2026-01-15T14:00:00" | Common config field |

### Dataset-Level Validation Rules

- risk_scoring_component_id must be unique.
- component_weight, minimum_score, maximum_score must be consistent.
- Only Approved, active and enabled records used for calculations.

### Downstream Impact

- risk_register prioritisation.

### Unresolved Items

- Component weights pending Farah approval.
- Final scoring method pending approval.

---

## 6. forecast_config.csv

### Dataset Overview

| Attribute | Value |
|---|---|
| Dataset name | forecast_config |
| File name | forecast_config.csv |
| Purpose | Contains approved forecast methods, history requirements, horizons and confidence rules |
| Grain | One record per forecast configuration |
| Primary key | forecast_config_id |
| Foreign keys | kpi_id |
| Required or optional | Required |
| Refresh frequency | On change |
| Prototype source | Manual upload |
| Future production source | Configuration management |
| Sensitivity | Medium |
| Main consumers | Forecasting |
| Governance owner | Farah |
| Editability | Viewable; editing restricted |

### Field Dictionary

| Field Name | Business Definition | Data Type | Required | Primary Key | Foreign Key | Allowed Values or Domain | Validation Rule | Example Format | Notes |
|---|---|---|---|---|---|---|---|---|---|
| forecast_config_id | Unique identifier | string | Yes | Yes | No | Alphanumeric, unique | Must be unique and non-blank | "FOR_001" | |
| kpi_id | KPI to forecast | string | Yes | No | Yes | kpi_definition_config.kpi_id | Must exist in kpi_definition_config | "KPI_STAFF_LVL" | |
| forecast_horizon | Forecast horizon in periods | integer | Yes | No | No | 1 to 365 | Must be >= 1 | 7 | |
| forecast_unit | Unit of the horizon | string | Yes | No | No | Days, Weeks, Months | Must match domain | "Days" | |
| method_name | Forecasting method | string | Yes | No | No | Moving Average, Exponential Smoothing, ARIMA, Linear Trend, Other | Must match domain | "Moving Average" | Method pending approval |
| minimum_history_periods | Minimum historical observations required | integer | Yes | No | No | 1 to 999 | Must be >= 1 | 30 | |
| training_window | Periods used to train the model | integer | Optional | No | No | 1 to 999 | If present, must be >= minimum_history_periods | 90 | |
| confidence_level | Confidence level for intervals | decimal | Optional | No | No | 0.5 to 0.99 | If present, must be >= 0.5 and <= 0.99 | 0.95 | |
| seasonality_enabled | Whether seasonality is considered | boolean | Optional | No | No | true, false | Must be boolean if present | false | |
| fallback_method | Method used if primary method fails | string | Optional | No | No | Same domain as method_name | Must match domain if provided | "Linear Trend" | |
| low_confidence_rule | Rule for handling low-confidence forecasts | string | Optional | No | No | Suppress, Flag, Show With Warning, Use Fallback | Must match domain if provided | "Flag" | |
| enabled_flag | Whether this configuration is enabled | boolean | Yes | No | No | true, false | Must be boolean | true | |
| configuration_version | Configuration version | string | Yes | No | No | Free text | Max 50 characters | "CONFIG_V1" | Common config field |
| effective_start_date | Valid from | date | Yes | No | No | ISO 8601 date | Must be valid | "2026-01-01" | Common config field |
| effective_end_date | Valid to | date | Optional | No | No | ISO 8601 date or blank | If present, >= effective_start_date | "2099-12-31" | Common config field |
| active_flag | Active flag | boolean | Yes | No | No | true, false | Must be boolean | true | Common config field |
| approval_status | Approval status | string | Yes | No | No | Draft, Under Review, Approved, Retired | Must match domain | "Approved" | Common config field |
| approved_by_role | Approver role | string | Optional | No | No | Free text | Max 100 characters | "Medical Director" | Common config field |
| approval_date | Approval date | date | Optional | No | No | ISO 8601 date or blank | If present, must be valid | "2026-01-15" | Common config field |
| change_reason | Change reason | string | Optional | No | No | Free text | Max 500 characters | "Initial forecast config" | Common config field |
| created_datetime | Creation timestamp | datetime | Yes | No | No | ISO 8601 datetime | Must be valid | "2026-01-10T09:00:00" | Common config field |
| updated_datetime | Update timestamp | datetime | Yes | No | No | ISO 8601 datetime | Must be >= created_datetime | "2026-01-15T14:00:00" | Common config field |

### Dataset-Level Validation Rules

- forecast_config_id must be unique.
- kpi_id must exist in kpi_definition_config.
- minimum_history_periods >= 1.
- training_window, if present, must be >= minimum_history_periods.
- Only Approved, active and enabled records used for calculations.

### Downstream Impact

- forecast_results.

### Unresolved Items

- Final forecast model and parameters pending Farah approval.

---

## 7. intervention_catalogue.csv

### Dataset Overview

| Attribute | Value |
|---|---|
| Dataset name | intervention_catalogue |
| File name | intervention_catalogue.csv |
| Purpose | Contains approved management intervention options |
| Grain | One record per intervention |
| Primary key | intervention_id |
| Foreign keys | applicable_kpi_id |
| Required or optional | Required |
| Refresh frequency | On change |
| Prototype source | Manual upload |
| Future production source | Configuration management |
| Sensitivity | Low |
| Main consumers | Scenario generation, recommendation rules |
| Governance owner | Farah |
| Editability | Viewable; editing restricted |

### Field Dictionary

| Field Name | Business Definition | Data Type | Required | Primary Key | Foreign Key | Allowed Values or Domain | Validation Rule | Example Format | Notes |
|---|---|---|---|---|---|---|---|---|---|
| intervention_id | Unique identifier for the intervention | string | Yes | Yes | No | Alphanumeric, unique | Must be unique and non-blank | "INT_001" | |
| intervention_code | Short code | string | Yes | No | No | Alphanumeric | Must be unique; max 50 characters | "TEMP_STAFF" | |
| intervention_name | Human-readable name | string | Yes | No | No | Non-empty text | Max 200 characters | "Temporary Staffing Support" | |
| intervention_family | Family grouping | string | Yes | No | No | Temporary Staffing, Extended Clinic Hours, Patient Redirection, Elective Admission Rescheduling, Temporary Capacity Restoration, Peak-Hour Communication Support, Monitor Only, No Immediate Intervention | Must match domain | "Temporary Staffing" | |
| intervention_description | Detailed description | string | Optional | No | No | Free text | Max 1000 characters | "Deploy additional nursing staff" | |
| applicable_domain | Domain where this applies | string | Yes | No | No | Workforce, Operations, Patient Experience, Multi-Domain | Must match domain | "Workforce" | |
| applicable_kpi_id | KPI most directly affected | string | Optional | No | Yes | kpi_definition_config.kpi_id | If present, must exist in kpi_definition_config | "KPI_STAFF_LVL" | |
| required_approval_role | Role required to approve this intervention | string | Yes | No | No | Free text | Max 100 characters | "Nursing Director" | |
| minimum_lead_time | Minimum lead time in days | integer | Optional | No | No | 0 to 999 | If present, must be >= 0 | 1 | |
| expected_duration_unit | Typical duration unit | string | Optional | No | No | Hours, Days, Weeks, Months | Must match domain if provided | "Days" | |
| compatible_intervention_codes | Comma-separated list of compatible intervention codes | string | Optional | No | No | Free text | Max 500 characters | "EXT_CLINIC" | |
| incompatible_intervention_codes | Comma-separated list of incompatible intervention codes | string | Optional | No | No | Free text | Max 500 characters | "" | |
| active_flag | Whether the intervention is active | boolean | Yes | No | No | true, false | Must be boolean | true | |
| configuration_version | Configuration version | string | Yes | No | No | Free text | Max 50 characters | "CONFIG_V1" | Common config field |
| effective_start_date | Valid from | date | Yes | No | No | ISO 8601 date | Must be valid | "2026-01-01" | Common config field |
| effective_end_date | Valid to | date | Optional | No | No | ISO 8601 date or blank | If present, >= effective_start_date | "2099-12-31" | Common config field |
| approval_status | Approval status | string | Yes | No | No | Draft, Under Review, Approved, Retired | Must match domain | "Approved" | Common config field |
| approved_by_role | Approver role | string | Optional | No | No | Free text | Max 100 characters | "Medical Director" | Common config field |
| approval_date | Approval date | date | Optional | No | No | ISO 8601 date or blank | If present, must be valid | "2026-01-15" | Common config field |
| change_reason | Change reason | string | Optional | No | No | Free text | Max 500 characters | "Initial catalogue" | Common config field |
| created_datetime | Creation timestamp | datetime | Yes | No | No | ISO 8601 datetime | Must be valid | "2026-01-10T09:00:00" | Common config field |
| updated_datetime | Update timestamp | datetime | Yes | No | No | ISO 8601 datetime | Must be >= created_datetime | "2026-01-15T14:00:00" | Common config field |

### Dataset-Level Validation Rules

- intervention_id and intervention_code must each be unique.
- applicable_kpi_id, if present, must exist in kpi_definition_config.
- compatible_intervention_codes and incompatible_intervention_codes must reference valid intervention_code values if provided.
- Only Approved and active records used for scenario generation.

### Downstream Impact

- scenario_definitions, recommendation_evidence.

### Unresolved Items

- Compatibility rules may be formalised in a later step.

---

## 8. scenario_assumption_config.csv

### Dataset Overview

| Attribute | Value |
|---|---|
| Dataset name | scenario_assumption_config |
| File name | scenario_assumption_config.csv |
| Purpose | Contains operational assumptions used by scenario simulations |
| Grain | One record per assumption |
| Primary key | scenario_assumption_id |
| Foreign keys | intervention_id |
| Required or optional | Required |
| Refresh frequency | On change |
| Prototype source | Manual upload |
| Future production source | Configuration management |
| Sensitivity | Medium |
| Main consumers | Scenario simulation |
| Governance owner | Farah |
| Editability | Authorised users may adjust through UI; changes are versioned |

### Field Dictionary

| Field Name | Business Definition | Data Type | Required | Primary Key | Foreign Key | Allowed Values or Domain | Validation Rule | Example Format | Notes |
|---|---|---|---|---|---|---|---|---|---|
| scenario_assumption_id | Unique identifier | string | Yes | Yes | No | Alphanumeric, unique | Must be unique and non-blank | "SA_001" | |
| intervention_id | Intervention to which this applies | string | Yes | No | Yes | intervention_catalogue.intervention_id | Must exist in intervention_catalogue | "INT_001" | |
| assumption_code | Short code for the assumption | string | Yes | No | No | Alphanumeric | Must be unique within intervention; max 50 characters | "STAFF_ADDED" | |
| assumption_name | Human-readable name | string | Yes | No | No | Non-empty text | Max 200 characters | "Additional Staff Count" | |
| assumption_description | Detailed description | string | Optional | No | No | Free text | Max 1000 characters | "Number of additional staff deployed" | |
| assumption_category | Category of assumption | string | Yes | No | No | Disruption, Demand, Capacity, Workforce, Mitigation, Duration, Operational Effect, Other | Must match domain | "Workforce" | |
| unit | Unit of measurement | string | Yes | No | No | Count, Percentage, Hours, Days, FTE, Ratio, Other | Must match domain | "Count" | |
| default_value | Default value for planning | decimal | Optional | No | No | Numeric | Pending approval | Pending approval | Values pending approval |
| minimum_value | Minimum allowed value | decimal | Optional | No | No | Numeric | If present, must be <= default_value and <= maximum_value | 0 | |
| maximum_value | Maximum allowed value | decimal | Optional | No | No | Numeric | If present, must be >= default_value and >= minimum_value | 100 | |
| step_value | Increment step for UI controls | decimal | Optional | No | No | Numeric | If present, must be > 0 | 1 | |
| data_type | Data type of the value | string | Yes | No | No | Integer, Decimal, Boolean, String | Must match domain | "Integer" | |
| editable_flag | Whether users may edit this assumption | boolean | Yes | No | No | true, false | Must be boolean | true | |
| source_reference | Reference to source or justification | string | Optional | No | No | Free text | Max 500 characters | "Workforce planning estimate" | |
| confidence_level | Confidence in the assumption | string | Optional | No | No | High, Medium, Low | Must match domain if provided | "Medium" | |
| configuration_version | Configuration version | string | Yes | No | No | Free text | Max 50 characters | "CONFIG_V1" | Common config field |
| effective_start_date | Valid from | date | Yes | No | No | ISO 8601 date | Must be valid | "2026-01-01" | Common config field |
| effective_end_date | Valid to | date | Optional | No | No | ISO 8601 date or blank | If present, >= effective_start_date | "2099-12-31" | Common config field |
| active_flag | Active flag | boolean | Yes | No | No | true, false | Must be boolean | true | Common config field |
| approval_status | Approval status | string | Yes | No | No | Draft, Under Review, Approved, Retired | Must match domain | "Approved" | Common config field |
| approved_by_role | Approver role | string | Optional | No | No | Free text | Max 100 characters | "Medical Director" | Common config field |
| approval_date | Approval date | date | Optional | No | No | ISO 8601 date or blank | If present, must be valid | "2026-01-15" | Common config field |
| change_reason | Change reason | string | Optional | No | No | Free text | Max 500 characters | "Initial assumptions" | Common config field |
| created_datetime | Creation timestamp | datetime | Yes | No | No | ISO 8601 datetime | Must be valid | "2026-01-10T09:00:00" | Common config field |
| updated_datetime | Update timestamp | datetime | Yes | No | No | ISO 8601 datetime | Must be >= created_datetime | "2026-01-15T14:00:00" | Common config field |

### Dataset-Level Validation Rules

- scenario_assumption_id must be unique.
- intervention_id must exist in intervention_catalogue.
- assumption_code must be unique within an intervention.
- minimum_value <= default_value <= maximum_value when all are present.
- Only Approved and active records used for calculations.

### Downstream Impact

- scenario_results.

### Unresolved Items

- Default values pending Farah approval.

---

## 9. financial_assumption_config.csv

### Dataset Overview

| Attribute | Value |
|---|---|
| Dataset name | financial_assumption_config |
| File name | financial_assumption_config.csv |
| Purpose | Contains cost, loss, benefit and valuation assumptions |
| Grain | One record per financial assumption |
| Primary key | financial_assumption_id |
| Foreign keys | intervention_id |
| Required or optional | Required |
| Refresh frequency | On change |
| Prototype source | Manual upload |
| Future production source | Configuration management |
| Sensitivity | High |
| Main consumers | Financial-impact calculation |
| Governance owner | Farah |
| Editability | Authorised users may adjust through UI; changes are versioned and flagged |

### Field Dictionary

| Field Name | Business Definition | Data Type | Required | Primary Key | Foreign Key | Allowed Values or Domain | Validation Rule | Example Format | Notes |
|---|---|---|---|---|---|---|---|---|---|
| financial_assumption_id | Unique identifier | string | Yes | Yes | No | Alphanumeric, unique | Must be unique and non-blank | "FA_001" | |
| intervention_id | Intervention to which this applies | string | Yes | No | Yes | intervention_catalogue.intervention_id | Must exist in intervention_catalogue | "INT_001" | |
| assumption_code | Short code | string | Yes | No | No | Alphanumeric | Must be unique within intervention; max 50 characters | "COST_STAFF" | |
| assumption_name | Human-readable name | string | Yes | No | No | Non-empty text | Max 200 characters | "Temporary Staff Cost" | |
| financial_category | Category of financial impact | string | Yes | No | No | Intervention Cost, Labour Cost, Capacity Cost, Revenue Exposure, Avoided Loss, Service Recovery Benefit, Other | Must match domain | "Labour Cost" | |
| unit | Unit of measurement | string | Yes | No | No | Currency, Currency Per Hour, Currency Per Day, Percentage, Count, Other | Must match domain | "Currency Per Day" | |
| default_value | Default value | decimal | Optional | No | No | Numeric | Pending approval | Pending approval | Values pending approval |
| minimum_value | Minimum allowed value | decimal | Optional | No | No | Numeric | If present, must be <= default_value and <= maximum_value | 0 | |
| maximum_value | Maximum allowed value | decimal | Optional | No | No | Numeric | If present, must be >= default_value and >= minimum_value | 100000 | |
| currency_code | Currency | string | Yes | No | No | ISO 4217 or custom | Must be non-blank; max 10 characters | "MYR" | Prototype currency |
| source_reference | Reference to source or justification | string | Optional | No | No | Free text | Max 500 characters | "Finance estimate" | |
| confidence_level | Confidence in the assumption | string | Optional | No | No | High, Medium, Low | Must match domain if provided | "Medium" | |
| editable_flag | Whether users may edit this assumption | boolean | Yes | No | No | true, false | Must be boolean | true | |
| configuration_version | Configuration version | string | Yes | No | No | Free text | Max 50 characters | "CONFIG_V1" | Common config field |
| effective_start_date | Valid from | date | Yes | No | No | ISO 8601 date | Must be valid | "2026-01-01" | Common config field |
| effective_end_date | Valid to | date | Optional | No | No | ISO 8601 date or blank | If present, >= effective_start_date | "2099-12-31" | Common config field |
| active_flag | Active flag | boolean | Yes | No | No | true, false | Must be boolean | true | Common config field |
| approval_status | Approval status | string | Yes | No | No | Draft, Under Review, Approved, Retired | Must match domain | "Approved" | Common config field |
| approved_by_role | Approver role | string | Optional | No | No | Free text | Max 100 characters | "Medical Director" | Common config field |
| approval_date | Approval date | date | Optional | No | No | ISO 8601 date or blank | If present, must be valid | "2026-01-15" | Common config field |
| change_reason | Change reason | string | Optional | No | No | Free text | Max 500 characters | "Initial assumptions" | Common config field |
| created_datetime | Creation timestamp | datetime | Yes | No | No | ISO 8601 datetime | Must be valid | "2026-01-10T09:00:00" | Common config field |
| updated_datetime | Update timestamp | datetime | Yes | No | No | ISO 8601 datetime | Must be >= created_datetime | "2026-01-15T14:00:00" | Common config field |

### Dataset-Level Validation Rules

- financial_assumption_id must be unique.
- intervention_id must exist in intervention_catalogue.
- assumption_code must be unique within an intervention.
- minimum_value <= default_value <= maximum_value when all are present.
- currency_code must be non-blank.
- Only Approved and active records used for calculations.

### Downstream Impact

- financial_impact_results.

### Unresolved Items

- Default monetary values pending Farah approval.
- Currency code set to MYR for prototype but not yet approved.

---

## 10. recommendation_rule_config.csv

### Dataset Overview

| Attribute | Value |
|---|---|
| Dataset name | recommendation_rule_config |
| File name | recommendation_rule_config.csv |
| Purpose | Contains rules for mapping evidence and ranked scenarios into structured recommendations |
| Grain | One record per recommendation rule |
| Primary key | recommendation_rule_id |
| Foreign keys | applicable_kpi_id, recommended_intervention_id |
| Required or optional | Required |
| Refresh frequency | On change |
| Prototype source | Manual upload |
| Future production source | Configuration management |
| Sensitivity | Medium |
| Main consumers | Recommendation evidence generation |
| Governance owner | Farah |
| Editability | Viewable; editing restricted |

### Field Dictionary

| Field Name | Business Definition | Data Type | Required | Primary Key | Foreign Key | Allowed Values or Domain | Validation Rule | Example Format | Notes |
|---|---|---|---|---|---|---|---|---|---|
| recommendation_rule_id | Unique identifier | string | Yes | Yes | No | Alphanumeric, unique | Must be unique and non-blank | "REC_001" | |
| rule_name | Human-readable name | string | Yes | No | No | Non-empty text | Max 200 characters | "Low Staffing Trigger" | |
| rule_priority | Priority for rule ordering | integer | Yes | No | No | 1 to 100 | Must be >= 1 and <= 100 | 10 | |
| triggering_condition | Condition that triggers the rule | string | Optional | No | No | Free text | Max 1000 characters | "KPI_STAFF_LVL critical for 3 days" | Expression pending approval |
| applicable_domain | Domain where rule applies | string | Yes | No | No | Workforce, Operations, Patient Experience, Multi-Domain | Must match domain | "Workforce" | |
| applicable_kpi_id | KPI that triggers the rule | string | Optional | No | Yes | kpi_definition_config.kpi_id | If present, must exist in kpi_definition_config | "KPI_STAFF_LVL" | |
| minimum_data_confidence | Minimum confidence required | string | Optional | No | No | High, Medium, Low | Must match domain if provided | "Medium" | |
| required_scenario_result_flag | Whether a scenario result is required | boolean | Optional | No | No | true, false | Must be boolean if present | true | |
| recommended_intervention_id | Default intervention to recommend | string | Optional | No | Yes | intervention_catalogue.intervention_id | If present, must exist in intervention_catalogue | "INT_001" | |
| escalation_level | Escalation level | string | Optional | No | No | Normal, Urgent, Critical | Must match domain if provided | "Normal" | |
| enabled_flag | Whether the rule is enabled | boolean | Yes | No | No | true, false | Must be boolean | true | |
| configuration_version | Configuration version | string | Yes | No | No | Free text | Max 50 characters | "CONFIG_V1" | Common config field |
| effective_start_date | Valid from | date | Yes | No | No | ISO 8601 date | Must be valid | "2026-01-01" | Common config field |
| effective_end_date | Valid to | date | Optional | No | No | ISO 8601 date or blank | If present, >= effective_start_date | "2099-12-31" | Common config field |
| active_flag | Active flag | boolean | Yes | No | No | true, false | Must be boolean | true | Common config field |
| approval_status | Approval status | string | Yes | No | No | Draft, Under Review, Approved, Retired | Must match domain | "Approved" | Common config field |
| approved_by_role | Approver role | string | Optional | No | No | Free text | Max 100 characters | "Medical Director" | Common config field |
| approval_date | Approval date | date | Optional | No | No | ISO 8601 date or blank | If present, must be valid | "2026-01-15" | Common config field |
| change_reason | Change reason | string | Optional | No | No | Free text | Max 500 characters | "Initial rules" | Common config field |
| created_datetime | Creation timestamp | datetime | Yes | No | No | ISO 8601 datetime | Must be valid | "2026-01-10T09:00:00" | Common config field |
| updated_datetime | Update timestamp | datetime | Yes | No | No | ISO 8601 datetime | Must be >= created_datetime | "2026-01-15T14:00:00" | Common config field |

### Dataset-Level Validation Rules

- recommendation_rule_id must be unique.
- applicable_kpi_id and recommended_intervention_id, if present, must exist in respective catalogues.
- Only Approved, active and enabled records used for calculations.

### Downstream Impact

- recommendation_evidence.

### Unresolved Items

- triggering_condition syntax pending approval.

---

## 11. outcome_review_config.csv

### Dataset Overview

| Attribute | Value |
|---|---|
| Dataset name | outcome_review_config |
| File name | outcome_review_config.csv |
| Purpose | Contains rules for comparison windows and outcome classification |
| Grain | One record per outcome review configuration |
| Primary key | outcome_config_id |
| Foreign keys | intervention_id, monitored_kpi_id |
| Required or optional | Required |
| Refresh frequency | On change |
| Prototype source | Manual upload |
| Future production source | Configuration management |
| Sensitivity | Low |
| Main consumers | Outcome review |
| Governance owner | Farah |
| Editability | Viewable; editing restricted |

### Field Dictionary

| Field Name | Business Definition | Data Type | Required | Primary Key | Foreign Key | Allowed Values or Domain | Validation Rule | Example Format | Notes |
|---|---|---|---|---|---|---|---|---|---|
| outcome_config_id | Unique identifier | string | Yes | Yes | No | Alphanumeric, unique | Must be unique and non-blank | "OUT_001" | |
| intervention_id | Intervention to which this applies | string | Yes | No | Yes | intervention_catalogue.intervention_id | Must exist in intervention_catalogue | "INT_001" | |
| monitored_kpi_id | KPI to monitor | string | Yes | No | Yes | kpi_definition_config.kpi_id | Must exist in kpi_definition_config | "KPI_STAFF_LVL" | |
| baseline_window | Period before action for baseline | integer | Yes | No | No | 1 to 365 | Must be >= 1 | 7 | |
| post_action_window | Period after action for comparison | integer | Yes | No | No | 1 to 365 | Must be >= 1 | 14 | |
| comparison_method | Method for comparing before and after | string | Yes | No | No | Absolute Change, Percentage Change, Trend Direction, Other | Must match domain | "Percentage Change" | |
| improvement_direction | Direction that indicates improvement | string | Yes | No | No | Increase, Decrease, Move To Target | Must match domain | "Move To Target" | |
| minimum_change_rule | Minimum change to register as improved | string | Optional | No | No | Free text | Max 500 characters | "5% change or movement across threshold" | Rule pending approval |
| insufficient_data_rule | Rule for insufficient data | string | Optional | No | No | Free text | Max 500 characters | "Less than 5 observations" | Rule pending approval |
| configuration_version | Configuration version | string | Yes | No | No | Free text | Max 50 characters | "CONFIG_V1" | Common config field |
| effective_start_date | Valid from | date | Yes | No | No | ISO 8601 date | Must be valid | "2026-01-01" | Common config field |
| effective_end_date | Valid to | date | Optional | No | No | ISO 8601 date or blank | If present, >= effective_start_date | "2099-12-31" | Common config field |
| active_flag | Active flag | boolean | Yes | No | No | true, false | Must be boolean | true | Common config field |
| approval_status | Approval status | string | Yes | No | No | Draft, Under Review, Approved, Retired | Must match domain | "Approved" | Common config field |
| approved_by_role | Approver role | string | Optional | No | No | Free text | Max 100 characters | "Medical Director" | Common config field |
| approval_date | Approval date | date | Optional | No | No | ISO 8601 date or blank | If present, must be valid | "2026-01-15" | Common config field |
| change_reason | Change reason | string | Optional | No | No | Free text | Max 500 characters | "Initial config" | Common config field |
| created_datetime | Creation timestamp | datetime | Yes | No | No | ISO 8601 datetime | Must be valid | "2026-01-10T09:00:00" | Common config field |
| updated_datetime | Update timestamp | datetime | Yes | No | No | ISO 8601 datetime | Must be >= created_datetime | "2026-01-15T14:00:00" | Common config field |

### Dataset-Level Validation Rules

- outcome_config_id must be unique.
- intervention_id and monitored_kpi_id must exist in respective catalogues.
- baseline_window and post_action_window must be >= 1.
- Only Approved and active records used for calculations.

### Downstream Impact

- outcome_reviews.

### Unresolved Items

- minimum_change_rule and insufficient_data_rule expressions pending approval.

---

## 12. role_approval_config.csv

### Dataset Overview

| Attribute | Value |
|---|---|
| Dataset name | role_approval_config |
| File name | role_approval_config.csv |
| Purpose | Defines which management roles may approve which intervention types |
| Grain | One record per role-intervention combination |
| Primary key | role_approval_id |
| Foreign keys | intervention_family |
| Required or optional | Required |
| Refresh frequency | On change |
| Prototype source | Manual upload |
| Future production source | Configuration management |
| Sensitivity | Medium |
| Main consumers | Decision validation, workflow routing |
| Governance owner | Farah |
| Editability | Viewable; editing restricted |

### Field Dictionary

| Field Name | Business Definition | Data Type | Required | Primary Key | Foreign Key | Allowed Values or Domain | Validation Rule | Example Format | Notes |
|---|---|---|---|---|---|---|---|---|---|
| role_approval_id | Unique identifier | string | Yes | Yes | No | Alphanumeric, unique | Must be unique and non-blank | "RA_001" | |
| management_role | Management role | string | Yes | No | No | Hospital Chief Operating Officer, General Manager, Medical Director, Nursing Director, Department Head, Patient Experience Lead, Authorised Operational Manager, Other | Must match domain | "Nursing Director" | |
| intervention_family | Intervention family | string | Yes | No | No | Temporary Staffing, Extended Clinic Hours, Patient Redirection, Elective Admission Rescheduling, Temporary Capacity Restoration, Peak-Hour Communication Support, Monitor Only, No Immediate Intervention | Must match domain | "Temporary Staffing" | |
| approval_permission | Permission level | string | Yes | No | No | View, Recommend, Modify, Approve, Reject, Assign, Close | Must match domain | "Approve" | |
| expenditure_limit | Maximum expenditure this role may approve | decimal | Optional | No | No | Numeric | If present, must be >= 0 | Pending approval | Values pending approval |
| escalation_role | Role to escalate to if limit exceeded | string | Optional | No | No | Free text | Max 100 characters | "Hospital Chief Operating Officer" | |
| active_flag | Whether this configuration is active | boolean | Yes | No | No | true, false | Must be boolean | true | |
| configuration_version | Configuration version | string | Yes | No | No | Free text | Max 50 characters | "CONFIG_V1" | Common config field |
| effective_start_date | Valid from | date | Yes | No | No | ISO 8601 date | Must be valid | "2026-01-01" | Common config field |
| effective_end_date | Valid to | date | Optional | No | No | ISO 8601 date or blank | If present, >= effective_start_date | "2099-12-31" | Common config field |
| approval_status | Approval status | string | Yes | No | No | Draft, Under Review, Approved, Retired | Must match domain | "Approved" | Common config field |
| approved_by_role | Approver role | string | Optional | No | No | Free text | Max 100 characters | "Medical Director" | Common config field |
| approval_date | Approval date | date | Optional | No | No | ISO 8601 date or blank | If present, must be valid | "2026-01-15" | Common config field |
| change_reason | Change reason | string | Optional | No | No | Free text | Max 500 characters | "Initial role config" | Common config field |
| created_datetime | Creation timestamp | datetime | Yes | No | No | ISO 8601 datetime | Must be valid | "2026-01-10T09:00:00" | Common config field |
| updated_datetime | Update timestamp | datetime | Yes | No | No | ISO 8601 datetime | Must be >= created_datetime | "2026-01-15T14:00:00" | Common config field |

### Dataset-Level Validation Rules

- role_approval_id must be unique.
- management_role and intervention_family must match approved domains.
- expenditure_limit, if present, must be >= 0.
- Only Approved and active records used for decision validation.

### Downstream Impact

- decision_records validation, action workflow routing.

### Unresolved Items

- Expenditure limits pending Farah approval.
