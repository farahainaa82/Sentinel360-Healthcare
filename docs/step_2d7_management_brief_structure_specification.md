# Management Brief Structure Specification

## Overview

Each Integrated Management Brief contains 17 governed sections (A–Q). Every section is required and must be present for the brief to be considered complete.

## Section A — Executive Headline

| Field | Description |
|---|---|
| `brief_title` | Auto-generated: "Integrated Management Brief: [Department] [KPI] [Condition]" |
| `brief_subtitle` | Status and pending review indicator |
| `executive_headline` | What, where, and why management attention is required |
| `management_attention_level` | Mapped from risk, urgency, and escalation |
| `final_readiness_status` | Unchanged from 2D-4 |

## Section B — What Is Happening

Operational issue summary using existing governed values: KPI status, breach, watch, trend, risk score, risk tier, urgency, priority tier.

## Section C — Why It Matters

Cautious analytical wording describing operational significance, service consequence, workforce consequence, patient experience consequence, and financial exposure. No direct causality is claimed.

## Section D — Evidence Summary

Evidence completeness status, coverage percentage, critical missing count, key evidence summary, conditions, warnings, and trace status.

## Section E — Contributing Factors

Contributing factor summary with contradiction severity and causality status (always `Not Confirmed`).

## Section F — Recommendation Options

Representative recommendation, immediate/near-term/preventive action options, readiness, validation status, confirmation requirements, and limitations.

## Section G — Scenario Options

Baseline, conservative, expected, and higher-intensity scenario summaries. Missing comparators display as `Unavailable`.

## Section H — Trade-off and Impact Summary

Primary and supporting KPI effects, main trade-off, displacement risk, sensitivity, dominance, diminishing returns, and limitations.

## Section I — Financial Summary

Financial readiness, cost completeness, estimated cost/benefit/net impact, ROI, payback, affordability, lower/central/upper estimates, confidence, missing input flag, and limitations. Missing values display as `Not Available` or `Budget Data Required`.

## Section J — Readiness and Conditions

Final readiness status, explanation, main blocking condition, blocking/secondary condition counts, top secondary conditions, failed gates, pass-with-condition gates, required resolution, and responsible role.

## Section K — Permitted Management Actions

Primary permitted action, secondary permitted actions, blocked action summary, primary/secondary queues, responsible role, escalation required, escalation status, and escalation reason.

## Section L — Management Questions

Top management questions (up to 3 blocking + 3 non-blocking), blocking question count, mandatory question count, responsible roles, and required response types.

## Section M — Required Confirmations

Required confirmation summary, pending confirmation count, blocking confirmation count, responsible roles, and evidence required.

## Section N — Monitoring and Escalation

Monitoring required, KPIs, frequency, trigger condition, escalation condition, reassessment condition, responsible role, and management attention required.

## Section O — Governance and Limitations

Provisional warning, contradiction warning, stakeholder/assumption/baseline/financial validation requirements, governance burden status, evidence/lineage/audit limitations, and overall management limitation sentence.

## Section P — Audit and Traceability

Evidence completeness status, lineage completeness status, audit traceability status, integrity status, package version, source manifest, pending audit requirements, and future audit status (`Awaiting Management Action`).

## Section Q — Management Decision Boundary

Explicit boundary statement confirming:
- No preferred scenario selected
- No action selected
- No recommendation approved
- No budget approved
- No management review recorded
- Approval status remains `Pending Management Review`

Required closing sentence:
> "This brief supports management review and does not constitute action selection, scenario selection, recommendation approval, budget approval, or a final management decision."
