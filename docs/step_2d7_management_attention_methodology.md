# Management Attention Methodology

## Overview

Every brief is assigned a `management_attention_level` based on operational escalation status, risk tier, urgency, and final readiness status.

## Attention Levels

| Level | Description |
|---|---|
| Immediate Management Attention | Operational escalation active OR critical risk with immediate urgency |
| Priority Management Review | High risk with ready-for-review or ready-with-conditions status |
| Standard Management Review | Moderate risk, ready for review |
| Conditional Review | Blocked readiness statuses requiring validation |
| Monitoring | Monitoring Only packages |
| Non-Quantitative Review | Non-Quantitative packages |
| Not Suitable | Not Suitable packages |
| Rejected | Rejected packages |

## Mapping Rules

1. **Operational Escalation** takes precedence: any package with `operational_escalation_status = "Operational Escalation"` receives `Immediate Management Attention`.
2. **Critical Risk + Immediate Urgency** also receives `Immediate Management Attention`.
3. **High Risk** packages receive at least `Priority Management Review` even if readiness is blocked.
4. **Ready for Integrated Management Review** with moderate risk receives `Standard Management Review`.
5. **Ready with Conditions** maps to `Conditional Review` or `Priority Management Review` depending on risk.
6. **Blocked statuses** (Requires Assumption Validation, Requires Baseline Validation, etc.) map to `Conditional Review`.
7. **Monitoring Only** maps to `Monitoring`.
8. **Non-Quantitative** maps to `Non-Quantitative Review`.

## Governance

- High-risk packages are never downgraded merely because analytical readiness is blocked.
- A Critical or High risk package may still require Immediate Management Attention while remaining `Requires Assumption Validation`.
- Attention levels are derived from existing governed values, not invented.
