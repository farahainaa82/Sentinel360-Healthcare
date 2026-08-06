# Step 3A — Data Upload and Validation Methodology

## Purpose
This document describes the methodology for the Sentinel360 Step 3A Data Upload and Validation page.

## Scope
- Upload hospital operational datasets
- Preview uploaded data
- Identify dataset type automatically
- Validate filename, schema, columns, data types, nulls, duplicates, dates, identifiers, value ranges, and referential integrity
- Compare uploaded schemas against governed Sentinel360 data requirements
- Show validation issues clearly
- Generate validation summary and governed upload session manifest

## Approach
1. **File ingestion** — Accept CSV and Excel (XLSX/XLS) via drag-and-drop or demo-data selector.
2. **Dataset detection** — Infer dataset type from filename keyword hints and column-signature matching.
3. **Column alias mapping** — Propose canonical column names from a governed alias map; flag ambiguous mappings for user confirmation.
4. **Seven-layer validation** — Run File, Schema, Data-Type, Quality, Referential, Temporal, and Governance validations sequentially.
5. **Scorecard scoring** — Aggregate per-dimension results into a transparent scorecard (Pass / Pass with Warnings / Fail / Not Assessable).
6. **Issue register** — Record every finding with a unique issue ID, severity, category, and blocking flag.
7. **Session manifest** — Export a JSON manifest and CSV summaries for downstream governance.

## Validation Layers
| Layer | Focus | Blocking |
|---|---|---|
| 1 File | Extension, emptiness, encoding, corruption | Yes |
| 2 Schema | Required columns, duplicates, unnamed columns | Yes |
| 3 Data Type | Numeric, date, categorical, boolean | Yes |
| 4 Quality | Missing, blank, duplicates, invalid categories | No |
| 5 Referential | Cross-dataset key existence | Conditional |
| 6 Temporal | Future dates, ranges, gaps | No |
| 7 Governance | Sensitive columns, schema drift, config overwrite | No |

## Status
- **Phase 3A** is complete, governed, tested, and demo-ready.
- **Phase 2D** outputs remain frozen and unmodified.
- No downstream analytical processing is triggered in this step.
