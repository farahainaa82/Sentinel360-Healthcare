# Step 2D-4 Readiness Status and Precedence Rules

## Final Decision-Readiness States

Exactly one of the following statuses is assigned per package:

| Status | Category | Blocking |
|--------|----------|----------|
| Ready for Integrated Management Review | Advanced | No |
| Ready with Conditions | Conditional | No |
| Requires Assumption Validation | Blocking | Yes |
| Requires Baseline Validation | Blocking | Yes |
| Requires Financial Input | Blocking | Yes |
| Requires Benefit Validation | Blocking | Yes |
| Requires Budget Data | Blocking | Yes |
| Requires Stakeholder Validation | Blocking | Yes |
| Requires Additional Scenario Analysis | Blocking | Yes |
| Requires Evidence Completion | Blocking | Yes |
| Requires Lineage Completion | Blocking | Yes |
| Monitoring Only | Deferred | No |
| Non-Quantitative | Exclusion | No |
| Not Suitable for Decision Use | Exclusion | Yes |
| Rejected | Exclusion | Yes |

## Precedence Rules

Precedence is applied from strongest exclusion (1) to most advanced readiness (15):

1. Rejected
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
15. Ready for Integrated Management Review

A package can retain multiple condition flags, but only one final readiness state.

## Classification Logic

- Non-Quantitative packages map directly to Non-Quantitative
- Monitoring Only packages map directly to Monitoring Only
- Requires Assumption Validation packages map directly to Requires Assumption Validation
- Ready with Conditions packages are evaluated for specific blocking conditions; if none apply, they are distributed across Ready with Conditions and Ready for Integrated Management Review using deterministic hashing

## Governance Notes

- Ready for Integrated Management Review does not mean approved
- Monitoring Only is a valid governed outcome, not a failure
- Non-Quantitative cases are not converted to Ready with Conditions merely because a narrative exists
- Rejected is never overwritten by another status
