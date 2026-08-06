# Sentinel360 — Decision Validation Rules

## Step 2B-1B

---

## 1. Completeness Checks

For every KPI decision record:

| Field | Required For | Rule |
|-------|-------------|------|
| kpi_id | All | Must be one of the six governed KPIs |
| stakeholder_decision | All | Must be a recognised decision type |
| selected_candidate_id | Approve Candidate | Must exist in shortlist and belong to KPI |
| modified_green_lower_boundary | Approve with Modified Boundaries | Required for single-sided and context-sensitive |
| modified_green_upper_boundary | Approve with Modified Boundaries | Required for single-sided and context-sensitive |
| approver_name | Approve, Conditional, Modified | Must be non-empty |
| approval_date | Approve, Conditional, Modified | Must be non-empty |
| effective_date | Approve, Conditional, Modified | Must be non-empty |
| conditions_of_approval | Conditional Approval | Must be non-empty |
| required_review_date | Conditional Approval | Must be non-empty |

---

## 2. Boundary Validation

- Boundaries must be monotonic (no inversions).
- Green zone must have lower < upper.
- Context-sensitive KPIs require all six boundary fields or explicit justification.
- No overlapping bands unless documented and approved.
- Boundary inclusivity must be deterministic (lower inclusive, upper exclusive).

---

## 3. Approval Validation

- Approver role must be in the approval role register.
- Approver name must be present for all approval-like decisions.
- Approval date must not be in the future.
- Effective date must be on or after approval date.
- Expiry date, if provided, must be after effective date.

---

## 4. Invalid Decisions

A decision is invalid if:
- Unrecognised decision type.
- Selected candidate does not exist.
- Selected candidate belongs to a different KPI.
- Missing approver for approval-like decision.
- Missing approval date.
- Missing effective date.
- Modified boundaries incomplete.
- Conditional approval missing conditions or review date.
- Boundary values are non-monotonic.

Invalid decisions must not be promoted.

---

## 5. Unresolved Decisions

A KPI is unresolved if:
- No decision record exists.
- Decision type is No Decision.
- Decision is invalid.
- Decision is Defer or More Evidence Required.

Unresolved KPIs remain in Pending Stakeholder Review status.

---

## 6. Promotion Readiness

| Condition | Readiness |
|-----------|-----------|
| All six KPIs approved | Ready |
| All six approved or conditionally approved | Ready with Conditions |
| Some approved, others unresolved | Partially Ready |
| No decisions | Awaiting Stakeholder Decision |
| Any invalid approval | Not Ready |
