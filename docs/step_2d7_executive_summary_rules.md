# Executive Summary Rules

## Overview

Each brief must produce three levels of executive summary: a one-line summary, a short summary, and the full structured brief.

## A. One-Line Summary

- **Maximum target**: 35 words
- **Content**: Department, dominant KPI, risk tier, readiness status, and pending review status
- **Example**: "Medical Ward: Staffing Coverage shows elevated risk; readiness Requires Baseline Validation; awaiting management review."
- **Governance**: Must not contain prohibited wording. Must not imply a decision has been made.

## B. Short Summary

- **Maximum target**: 120 words
- **Content**: Department, KPI, risk tier, readiness, primary permitted action, and explicit statement that no selection or approval has occurred
- **Governance**: Must include the boundary statement that no scenario or action has been selected and no recommendation has been approved.
- **Example**: "Medical Ward is experiencing operational conditions related to Staffing Coverage. The current risk tier is under assessment. Analytical readiness status: Requires Baseline Validation. Primary permitted action: Validate Baseline. No scenario or action has been selected. No recommendation has been approved. Management review is required before any decision."

## C. Full Management Brief

- Structured fields plus concise narrative for each of the 17 sections.
- No uncontrolled long-form essays.
- Suitable for a hospital executive dashboard.
- All values drawn from authoritative upstream outputs.

## Length Enforcement

The narrative engine truncates summaries that exceed word targets:
- One-line: truncated to 35 words + period
- Short: truncated to 120 words + period

Tests verify that actual summary lengths remain within configured maximums.
