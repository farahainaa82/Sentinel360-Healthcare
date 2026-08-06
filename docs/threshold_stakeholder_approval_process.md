# Sentinel360 — Stakeholder Approval Process

## Step 2B-1B: Stakeholder Review, Approval and Threshold Promotion

---

## 1. Purpose

This document defines the governed process by which provisional threshold candidates (produced in Step 2B-1A) are reviewed, approved, rejected, deferred, or conditionally approved by authorised stakeholders.

No threshold may be promoted to active configuration without explicit stakeholder decision evidence.

---

## 2. Stakeholder Roles

| Role | Responsibility | Can Modify Boundaries | Can Conditionally Approve | Can Reject | Can Defer |
|------|---------------|----------------------|--------------------------|------------|-----------|
| Business Owner | Owns KPI business definition and operational impact | Yes | Yes | Yes | Yes |
| Hospital Operations Representative | Advises on operational feasibility and alert burden | Yes | Yes | Yes | Yes |
| Clinical or Service Representative | Advises on patient safety and service quality | Yes | Yes | Yes | Yes |
| Data or Analytics Owner | Validates statistical rigour and data sufficiency | No | Yes | No | Yes |
| Governance Approver | Ensures compliance with governance policy | No | No | Yes | Yes |

---

## 3. Review Sequence

1. **Technical Calibration Complete** — Step 2B-1A produces candidates, burden analysis, stability results, and trend alignments.
2. **Review Package Generated** — Mode A creates a stakeholder review workbook and decision template.
3. **Stakeholder Review** — Authorised stakeholders examine candidates and record decisions.
4. **Decision Validation** — Mode B validates completeness, boundary correctness, and approver authority.
5. **Staging** — Approved thresholds are assembled into a staged configuration.
6. **Sandbox Reclassification** — Historical records are reclassified using approved thresholds.
7. **Promotion (Optional)** — If both explicit flags are present, the active configuration is updated atomically.
8. **Rollback Evidence** — Backup and rollback instructions are preserved.

---

## 4. Decision Types

| Decision | Description | Permits Promotion |
|----------|-------------|-------------------|
| Approve Candidate | Accept shortlisted candidate unchanged | Yes |
| Approve with Modified Boundaries | Accept with stakeholder-specified boundaries | Yes |
| Conditional Approval | Approve provisionally with documented conditions | Yes (provisional) |
| Reject | Candidate not accepted | No |
| Defer | Decision postponed | No |
| More Evidence Required | Additional evidence needed | No |
| No Decision | No valid decision recorded | No |

---

## 5. Required Fields for Approval

- selected_candidate_id OR complete modified boundaries
- stakeholder_decision
- decision_rationale
- approver_role
- approver_name
- approval_date
- effective_date
- approval_status
- requested_promotion_version

For Conditional Approval, also required:
- conditions_of_approval
- required_review_date

---

## 6. Technical Recommendation vs Stakeholder Authority

- The engine provides a **technical recommendation** (e.g., Hybrid Balanced candidate).
- Stakeholders may accept, reject, or modify this recommendation.
- The technical recommendation is **not** an approval.
- CodeBuddy must never infer approval from the technical recommendation.

---

## 7. Conditional Approval

- Threshold remains provisional.
- Conditions must be documented.
- Review date must be set.
- Operational use may be restricted.
- Step 2B-2 must preserve provisional flags.

---

## 8. Modified Boundaries

- Original candidate is preserved.
- New modified threshold record is created.
- Modified boundaries are validated for non-overlap, no gaps, and correct directionality.
- Historical burden is recalculated for comparison.

---

## 9. Promotion Workflow

### Prerequisites
- All six KPIs have valid approved or conditionally approved decisions, OR
- Explicit partial enablement is accepted.

### Flags Required
- `--promote-active-config`
- `--confirm-stakeholder-approval`

Both must be present. Neither alone is sufficient.

### Atomic Promotion
1. Backup existing active config.
2. Write new config to temporary file.
3. Replace active config atomically.
4. Verify checksum and row count.

---

## 10. Governance Compliance

- No fabricated stakeholder names.
- No fabricated approval dates.
- No automatic approval.
- No promotion without explicit evidence.
- Active config protected in review-only mode.
- All historical files immutable.
