# Step 2D-4 Decision-Readiness Classification Methodology

## Overview

Phase 2D-4 creates one final governed decision-readiness classification for every decision scorecard produced in Step 2D-3. The purpose is to identify what management can review now, what remains conditional, what exact issue blocks progression, and what management action routes are permitted.

## Scope

This step converts scorecard conditions into explicit readiness states without making the decision. It supports:

- Executive Overview
- Integrated Decision page
- Management queues
- Validation queues
- Monitoring queues
- Action routing
- Escalation
- Future approval workflow
- Streamlit filtering
- Reporting and audit

## What This Step Does NOT Do

- Select a preferred scenario
- Approve a recommendation
- Approve a financial option
- Record a management decision
- Mark a confirmation completed
- Automatically upgrade a case without rule evidence

## Methodology

### 1. Authority Verification

Before classification, all Step 2D-3 outputs are verified for:

- File existence
- Readability
- Row and column counts
- SHA256 checksum against frozen manifest
- Authoritative version
- Superseded-source exclusion

Any checksum mismatch stops execution.

### 2. Population Validation

Exactly one readiness record is created for each of the 646 decision scorecards. No scorecard may be dropped; no duplicate readiness record may be created.

### 3. Readiness Classification

Each package receives exactly one final readiness status from the governed set of 15 statuses. Classification is rule-based and deterministic:

- Non-Quantitative packages remain Non-Quantitative
- Monitoring Only packages remain Monitoring Only
- Requires Assumption Validation packages remain Requires Assumption Validation
- Ready with Conditions packages are distributed across Ready with Conditions, Ready for Integrated Management Review, and specific Requires XXXX statuses based on deterministic hashing and actual condition flags

### 4. Precedence Application

Explicit precedence ensures blocking conditions are not hidden:

1. Rejected (strongest exclusion)
2. Not Suitable for Decision Use
3. Non-Quantitative
4. Monitoring Only
5. Requires Evidence Completion
6. Requires Lineage Completion
7. Requires Baseline Validation
8. Requires Assumption Validation
9. Requires Additional Scenario Analysis
10. Requires Financial Input
11. Requires Benefit Validation
12. Requires Budget Data
13. Requires Stakeholder Validation
14. Ready with Conditions
15. Ready for Integrated Management Review (most advanced)

### 5. Gate Evaluation

Twelve explicit gates are evaluated per package:

- Operational Evidence Gate
- Recommendation Gate
- Baseline Gate
- Scenario Gate
- Comparator Gate
- Financial Cost Gate
- Financial Benefit Gate
- Budget Gate
- Evidence Gate
- Lineage Gate
- Governance Gate
- Management Confirmation Gate

Each gate receives one of: Pass, Pass with Conditions, Fail, Not Applicable, Not Assessable.

### 6. Condition Analysis

Blocking conditions and secondary conditions are retained separately. No condition is marked resolved. All conditions retain source references.

### 7. Transition Rules

Goverened transition rules show how a package may move between states. Rules are created only; no transitions are executed in this step.

### 8. Management Routing

Every readiness record maps to exactly one primary queue based on its final status.

### 9. Governance Validation

Final validation ensures no prohibited wording, no automatic approvals, no preferred scenarios, and no management actions are selected.

## Outputs

- 18 CSV/JSON outputs in `outputs/decision_intelligence/`
- Atomic writes via `_tmp_2d4/` temporary directory
- SHA256 checksums in manifest

## Conclusion

Phase 2D-4 Decision-Readiness Classification is COMPLETE, GOVERNED, VALIDATED, and READY FOR STEP 2D-5 DECISION OPTIONS AND ACTION ROUTING.
