# Financial Display Governance

## Overview

Financial information is displayed only when applicable. Missing or blocked financial data is shown with governed placeholder text, not zero.

## Currency and Units

- Currency: **RM** (Malaysian Ringgit)
- Units and periods are governed by upstream configuration.
- Lower–Central–Upper ranges are displayed where available.

## Missing Value Display

| Situation | Display Text |
|---|---|
| Missing scenario cost | Not Available |
| Missing financial benefit | Not Available |
| Missing ROI | Not Assessable |
| Missing payback | Not Assessable |
| Missing affordability | Budget Data Required |
| Missing comparator | Unavailable |
| Blocked financial | Not Assessable |

## Prohibited Display

- Do not display `RM0` for missing inputs.
- Do not display ROI where blocked.
- Do not display payback where blocked.
- Do not make affordability claims without budget data.
- Do not describe any scenario as financially optimal.
- Do not claim guaranteed savings.

## Allowed Wording

- Estimated
- Potential
- May improve
- Appears to improve
- Requires validation
- Not Confirmed

## Output

- `step_2d7_financial_summary_register.csv` (646 rows)
- `step_2d7_tradeoff_and_impact_summary_register.csv` (646 rows)
