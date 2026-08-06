# Configuration Guide

## Config Files (11 total)

### 1. decision_intelligence_validation_rule_config.csv
- **Purpose**: Defines all 32 validation rules with severity and check type
- **Columns**: rule_id, rule_name, rule_dimension, severity, check_type, description

### 2. decision_intelligence_validation_display_governance.csv
- **Purpose**: Display rules for Streamlit handover
- **Columns**: field_name, display_rule, applicable_brief_types, max_length, required

### 3. decision_intelligence_validation_outcome_scale.csv
- **Purpose**: Governed outcome levels for validation results
- **Columns**: outcome_level, outcome_label, description, streamlit_ready

### 4. decision_intelligence_validation_correction_classification.csv
- **Purpose**: Correction classes with owners and resolution times
- **Columns**: correction_id, correction_class, description, owner, typical_resolution_time

### 5. decision_intelligence_validation_streamlit_readiness.csv
- **Purpose**: Streamlit readiness criteria per component
- **Columns**: component, readiness_criterion, critical_for_handover

### 6. decision_intelligence_validation_prohibited_terms.csv
- **Purpose**: Terms that must not appear in governed text fields
- **Columns**: term, severity, context_check

### 7. decision_intelligence_validation_allowed_terms.csv
- **Purpose**: Terms that must appear where required
- **Columns**: term, context, required

### 8. decision_intelligence_validation_section_requirements.csv
- **Purpose**: Section requirements for management briefs
- **Columns**: section_name, section_code, required_for_all, max_length

### 9. decision_intelligence_validation_evidence_thresholds.csv
- **Purpose**: Minimum evidence counts per category
- **Columns**: evidence_category, minimum_required_count, critical_for_readiness

### 10. decision_intelligence_validation_lineage_thresholds.csv
- **Purpose**: Minimum lineage stages required
- **Columns**: lineage_stage, minimum_required, required_for_all

### 11. decision_intelligence_validation_kpi_risk_rules.csv
- **Purpose**: KPI/Risk escalation and alignment rules
- **Columns**: rule_id, rule_name, condition, required_attention_level

## Modifying Configurations
1. Edit the relevant CSV file in `config/`
2. Re-run the 2D-8 validation
3. Verify changes via the outcome distribution register
