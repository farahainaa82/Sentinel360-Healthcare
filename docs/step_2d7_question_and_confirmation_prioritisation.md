# Question and Confirmation Prioritisation

## Overview

Each brief selects the most decision-relevant management questions and summarises required confirmations. The complete question register from 2D-2 is retained; only a priority subset is displayed in the brief.

## Question Selection Rules

### Selection Limit
- Up to 3 blocking questions
- Up to 3 non-blocking questions
- Total: up to 6 questions per brief

### Priority Order
1. Blocking flag (blocking questions first)
2. Mandatory flag (mandatory questions next)
3. Readiness relevance
4. Management action relevance
5. Operational urgency
6. Responsible-role importance

### Governance
- Questions are selected using the priority rules, not merely by file order.
- Source references are retained for traceability.
- The complete question register from 2D-2 is not removed.

## Confirmation Summary Rules

- Required confirmation summary lists all pending confirmations.
- Pending confirmation count is displayed.
- Blocking confirmation count is displayed.
- Responsible roles for confirmations are listed.
- Evidence required for confirmation is noted.
- No confirmation is marked as completed.

## Output

- `step_2d7_management_question_summary_register.csv` (646 rows)
- `step_2d7_confirmation_summary_register.csv` (646 rows)
