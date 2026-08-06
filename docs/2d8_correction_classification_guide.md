# Correction Classification Guide

## Correction Classes

### CC-01: No Correction Required
- **Owner**: Validator
- **Typical Resolution**: Immediate
- **Description**: Package passes all validations without any issues.

### CC-02: Documentation Clarification
- **Owner**: Content Reviewer
- **Typical Resolution**: 1 hour
- **Description**: Minor wording or annotation adjustment needed in documentation.
- **Examples**: Fixing a typo in a summary, adding a footnote.

### CC-03: Display Correction
- **Owner**: UI Engineer
- **Typical Resolution**: 2 hours
- **Description**: Field formatting or display rule adjustment needed for Streamlit.
- **Examples**: Changing a number format, adjusting column width.

### CC-04: Mapping Correction
- **Owner**: Data Engineer
- **Typical Resolution**: 4 hours
- **Description**: Data mapping or join condition needs adjustment.
- **Examples**: Fixing a foreign key mapping, correcting a lookup table.

### CC-05: Rule Configuration Correction
- **Owner**: Rule Administrator
- **Typical Resolution**: 2 hours
- **Description**: Validation rule or threshold configuration needs update.
- **Examples**: Adjusting a confidence threshold, updating a prohibited terms list.

### CC-06: Source Data Review
- **Owner**: Data Steward
- **Typical Resolution**: 1 day
- **Description**: Source data quality issue requiring data team investigation.
- **Examples**: Missing source records, incorrect data types.

### CC-07: Upstream Analytical Review
- **Owner**: Analyst
- **Typical Resolution**: 2 days
- **Description**: Analytical model or calculation requires upstream review.
- **Examples**: Recalculating a KPI, revisiting an assumption.

### CC-08: Governance Review
- **Owner**: Governance Officer
- **Typical Resolution**: 1 day
- **Description**: Policy or governance wording issue requiring governance team review.
- **Examples**: Prohibited term found, incorrect causal language.

## Workflow
1. Validation outcome determines correction class automatically.
2. Owner is notified via the validation register.
3. Correction is applied and package is re-validated.
4. Updated outcome is recorded in the master validation register.
