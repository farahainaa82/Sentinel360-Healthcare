# Phase 2D-1 Management Action Routing Specification

**Date:** 2026-07-29

---

## 1. Allowed Management Actions

| Action | Description |
|--------|-------------|
| Review Integrated Decision Package | Standard first step for all packages |
| Compare Scenario Options | Available when comparator completeness is confirmed |
| Validate Assumptions | Available when assumption validation is required |
| Validate Baseline | Available when baseline validation is required |
| Validate Financial Inputs | Available when financial inputs are draft or incomplete |
| Request Additional Scenario | Available when scenario package is missing or incomplete |
| Request Stakeholder Review | Available when stakeholder validation is required |
| Proceed to Limited-Trial Consideration | Available only for Ready for Integrated Management Review |
| Continue Monitoring | Available for Monitoring Only and Ready with Conditions |
| Defer Decision | Available when package is not fully ready |
| Reject Decision Use | Available for Rejected and Not Suitable packages |

## 2. Action Selection Rules

**No action is pre-selected.**

Every package has:
- `action_selection_status` = "Not Selected"
- `permitted_management_actions` = pipe-delimited list of allowed actions
- `action_count` = number of permitted actions
- `primary_suggested_action` = first action in the permitted list (for display ordering only)

## 3. Action Routing by Status

| Status | Typical Actions |
|--------|-----------------|
| Ready for Integrated Management Review | Review, Compare, Proceed to Trial, Continue Monitoring |
| Ready with Conditions | Review, Compare, Validate Assumptions, Validate Financial, Continue Monitoring, Defer |
| Requires Assumption Validation | Review, Validate Assumptions, Request Stakeholder, Defer |
| Monitoring Only | Review, Continue Monitoring, Defer |
| Non-Quantitative | Review, Continue Monitoring, Defer |
| Rejected | Review, Reject Decision Use |

## 4. Governance

- Actions are **permitted**, not pre-selected.
- Management must actively choose.
- No approval is recorded at this stage.
- All action routes carry governance note: "Actions are permitted, not pre-selected. Management must choose."

---

*End of Management Action Routing Specification*
