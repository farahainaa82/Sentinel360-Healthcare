# Step 2D-3 Decision Scorecard — Methodology

## Overview

Phase 2D-3 creates one governed executive decision scorecard for each of the 646 decision packages produced in Step 2D-2. The scorecard summarises operational risk, evidence strength, lineage strength, recommendation readiness, scenario readiness, financial readiness, uncertainty, governance burden, and management readiness in a single structured view.

## Principles

1. **Upstream Immutability**: No upstream phase is rerun. All inputs are read-only.
2. **Single-Instance Execution**: A file-based lock prevents duplicate processes.
3. **Atomic Output Writes**: All outputs are written to a temporary directory and moved atomically.
4. **No Cartesian Joins**: Every merge is validated for row-count preservation.
5. **Governance-First**: No preferred scenario, no approved recommendation, no selected action, no fabricated approval, no opaque AI score.

## Input Authority

All inputs are sourced from `outputs/decision_intelligence/step_2d2_*` files. Before assembly, every file is verified for existence, readability, row/column counts, and SHA-256 checksum against the 2D-2 manifest. If any checksum mismatch is detected, execution stops immediately.

## Scorecard Dimensions

The scorecard contains nine governed dimensions:

1. **Operational Risk** — risk tier, priority, urgency, breach status, trend direction
2. **Evidence Strength** — evidence reference count, completeness, status
3. **Lineage Strength** — lineage reference count, completeness, status
4. **Recommendation Readiness** — availability, validation status, limitations
5. **Scenario Readiness** — baseline availability, comparator completeness, confidence
6. **Financial Readiness** — cost completeness, ROI status, affordability, confidence
7. **Uncertainty and Sensitivity** — lower/central/upper estimates, range width, drivers
8. **Governance Burden** — contradiction warnings, provisional warnings, validation requirements
9. **Management Readiness** — package readiness, decision readiness, permitted actions

## Display Levels

Each dimension maps to a transparent display level:

- Strong
- Adequate
- Conditional
- Limited
- Blocking
- Not Applicable
- Not Assessable

No hidden proprietary score is calculated. No "AI confidence score" is created.

## Condition Flags

Thirteen explicit condition flags are created per scorecard:

- provisional_threshold_condition
- contradiction_condition
- assumption_validation_condition
- baseline_validation_condition
- financial_input_condition
- stakeholder_validation_condition
- scenario_completeness_condition
- evidence_completeness_condition
- lineage_completeness_condition
- uncertainty_condition
- monitoring_condition
- non_quantitative_condition
- blocking_condition

Each flag contains status, severity, reason, required action, responsible role, and source reference.

## Priority Ordering

Primary ordering uses:
1. Risk tier
2. Urgency
3. Breach status
4. Sustained deterioration
5. Management attention requirement

Financial value is never the primary ordering criterion.

## Smoke Test

Before the full run, a smoke test validates four representative packages (one per primary status). The full run proceeds only if the smoke test passes.

## Conclusion

Phase 2D-3 Decision Scorecard is COMPLETE, GOVERNED, VALIDATED, and READY FOR STEP 2D-4 DECISION-READINESS CLASSIFICATION.
