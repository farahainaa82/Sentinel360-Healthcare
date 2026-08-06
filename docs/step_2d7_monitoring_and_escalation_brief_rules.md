# Monitoring and Escalation Brief Rules

## Overview

Monitoring briefs and escalation summaries provide clear guidance on when and how management should reassess a package.

## Monitoring Brief Rules

For packages with `final_readiness_status = "Monitoring Only"`:

- Emphasise current watch or trend condition.
- Explain why active intervention review is not yet required.
- List KPIs to monitor.
- Define trigger conditions for escalation.
- Define reassessment requirements.
- Name responsible role.
- Do not frame Monitoring Only as a failed package.

## Escalation Rules

- `escalation_required` is derived from 2D-5 escalation routing.
- `escalation_status` is unchanged from upstream.
- `escalation_reason` is unchanged from upstream.
- No escalation is fabricated.
- No escalation is marked as completed.

## General Monitoring Fields

| Field | Description |
|---|---|
| `monitoring_required` | True/False from upstream |
| `monitoring_kpis` | List of KPIs to watch |
| `monitoring_frequency` | How often to review |
| `trigger_condition` | Condition that triggers action |
| `escalation_condition` | Condition that triggers escalation |
| `reassessment_condition` | Condition for reassessment |
| `monitoring_responsible_role` | Role accountable for monitoring |

## Output

- `step_2d7_monitoring_and_escalation_summary_register.csv` (646 rows)
