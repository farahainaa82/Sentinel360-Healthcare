# Export Contract Specification

## Overview

Phase 2D-7 creates governed export-ready data structures for future PDF, DOCX, or other format generation. No actual documents are generated in this step.

## Export Appendix Types

Each brief receives one contract record per appendix type:

| Export Type | Appendix | Required |
|---|---|---|
| One-Page Executive Brief | Executive Summary | Yes |
| Detailed Management Brief | Full Brief | Yes |
| Scenario Comparison Appendix | Scenario Details | Yes |
| Financial Comparison Appendix | Financial Details | Yes |
| Evidence Summary Appendix | Evidence Details | Yes |
| Lineage and Audit Appendix | Audit Details | Yes |
| Monitoring Appendix | Monitoring Details | Yes |
| Validation Requirements Appendix | Validation Details | Yes |

## Contract Structure

Each export contract record contains:

- `integrated_management_brief_id`
- `decision_package_id`
- `export_type`
- `export_appendix`
- `display_order`
- `available_flag`
- `governance_note`

## Governance

- Export contracts are preparatory only.
- No PDF, DOCX, or Streamlit pages are built in this step.
- All appendix types are marked as available if source data exists.
- Missing data appendices are still created but flagged for attention.

## Output

- `step_2d7_export_contract_register.csv` (5,168 rows = 646 x 8)
