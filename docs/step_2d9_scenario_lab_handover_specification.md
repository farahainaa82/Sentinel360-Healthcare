# Scenario Lab Handover Specification

## Functionality

- Package selector
- Hospital and department selectors
- Scenario display: Baseline, Conservative, Expected, Higher Intensity
- Scenario assumptions visible
- Comparator availability shown
- KPI impact summary
- Trade-offs and displacement risk
- Financial impact where available
- Confidence level
- Validation warning
- Reset and comparison controls

## Critical Constraints

- **No preferred scenario preselected.**
- **No missing comparator shown as zero.**
- **No values recalculated outside governed engines.**
- User-adjusted assumptions must be clearly labeled as simulation inputs.
- Simulated outputs must remain separate from authoritative frozen results.

## Data Source

Frozen Step 2D-7 scenario summaries mapped from Phase 2C-2 / Step 2D-7 sources.
