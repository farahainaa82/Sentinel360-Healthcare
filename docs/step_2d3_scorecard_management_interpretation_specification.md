# Step 2D-3 Scorecard Management Interpretation Specification

## Interpretation Structure

Each scorecard receives one short management interpretation with seven sections:

1. **Current risk** — operational risk tier and urgency
2. **Analytical readiness** — overall decision readiness status
3. **Main recommendation condition** — recommendation readiness
4. **Main scenario condition** — scenario readiness
5. **Main financial condition** — financial readiness
6. **Main governance warning** — governance burden status
7. **Permitted next management action** — from permitted actions list

## Permitted Wording

- Indicates
- Suggests
- Appears to
- Estimated
- Requires validation
- Ready with Conditions
- Monitoring required
- Not Confirmed
- Pending Management Review

## Prohibited Wording

- Best option
- Optimal scenario
- Guaranteed
- Proven
- Approved
- Will improve
- Will save
- Recommended by AI

## Interpretation Record Fields

- interpretation_id
- decision_package_id
- approval_package_id
- management_interpretation
- interpretation_version
- wording_compliance

## Governance Constraints

- No interpretation may imply automatic approval.
- No interpretation may select a preferred scenario.
- All interpretations must use permitted wording only.
