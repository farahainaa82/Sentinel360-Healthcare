# Sentinel360 Healthcare

## Project Overview

Sentinel360 Healthcare is a human-supervised, agentic executive early-warning and decision-support system for hospital operational performance. It dynamically monitors operational data, calculates KPIs, detects connected risks, forecasts deterioration, evaluates intervention scenarios, estimates operational and financial impact, recommends management actions, records authorised human decisions, tracks implementation and reviews subsequent outcomes.

## Product Positioning

Sentinel360 may detect, analyse, forecast, simulate, rank and recommend.

Sentinel360 must not autonomously execute staffing, financial, patient-flow, clinical or communication actions.

All operational and financial actions require authorised human approval.

## Target Users

| Role | Responsibility |
|---|---|
| Hospital Chief Operating Officer / General Manager | Primary user; executive oversight and escalation approval |
| Medical Director | Primary user; clinical and operational governance |
| Nursing Director | Operational decision owner; staffing intervention approver |
| Department Head | Operational decision owner; capacity and scheduling decisions |
| Patient Experience Lead | Informed stakeholder; reviews and contributes to patient-experience recommendations |
| Authorised operational managers | Action owners and implementation tracking |

Approval authority depends on the recommendation type:

- Staffing interventions require an authorised operational or nursing approver.
- Expenditure-related actions require an authorised financial or executive approver.
- The Patient Experience Lead may review and contribute but should not approve staffing or clinical actions unless formally authorised.

## Six Headline KPIs

| # | KPI | Purpose |
|---|---|---|
| 1 | Staffing Level | Workforce availability against demand |
| 2 | Staff Absenteeism Rate | Workforce reliability indicator |
| 3 | Bed Occupancy Rate | Capacity utilisation |
| 4 | Average Patient Waiting Time | Access and flow performance |
| 5 | Patient Complaint Rate | Service quality signal |
| 6 | Patient Satisfaction Score | Overall experience measure |

## Core System Workflow

1. **Observe** — Ingest and validate hospital operational data.
2. **Analyse** — Calculate KPIs, detect anomalies and identify connected risks.
3. **Forecast** — Generate short-term forecasts and an indicative 30-day outlook.
4. **Simulate** — Compare management intervention scenarios with transparent assumptions.
5. **Recommend** — Rank and recommend actions with evidence-based narrative.
6. **Decide** — Human approves, modifies or rejects with recorded reason.
7. **Act** — Assign owner, set timeline and track implementation.
8. **Review** — Compare before-versus-after performance to assess movement.

## Included Capabilities

- File upload or future data-pipeline ingestion
- Data structure, completeness and quality validation
- Dynamic calculation of six headline KPIs
- Threshold breach, anomaly and deterioration detection
- Connected-risk identification across workforce, operations and patient experience
- Short-term forecasts (7-day and indicative 30-day)
- Management intervention scenario comparison
- Operational and financial impact estimation with transparent configurable assumptions
- Ranked management-action recommendations
- Authorised user approval, modification and rejection paths
- Decision logging with reason and approver identity
- Action-owner assignment and target-timeline setting
- Implementation status tracking
- Before-versus-after outcome review
- Executive summaries and downloadable management reports

## Human-in-the-Loop Principle

Sentinel360 must not autonomously:

- Hire or deploy staff
- Change staff or clinical schedules
- Reschedule admissions
- Redirect patients
- Approve expenditure
- Make clinical decisions
- Contact patients
- Execute operational interventions

Every recommendation is presented for human review. The human user must be able to:

- Approve
- Modify
- Reject
- Record a reason
- Assign an owner
- Set a target timeline

All recommendations and decisions are auditable.

## System Responsibility Boundary

| Layer | Responsibility |
|---|---|
| **A. Deterministic Python analytics** | Data validation; KPI calculation; threshold checks; statistical anomaly detection; forecast calculations and confidence intervals; scenario calculations; financial calculations; scenario scoring and ranking. |
| **B. AI-assisted interpretation** | Explanation of connected risks; management interpretation; recommendation narrative; executive summary; action brief; outcome-review narrative. |
| **C. Human management decision** | Validate operational context; approve, modify or reject; authorise expenditure; assign responsibility; execute the action; review the result. |

## Prototype Limitations

- Synthetic or anonymised data only
- File upload before live system integration
- No direct EHR, HR, finance or scheduling-system connection
- Scenario impacts are management-planning estimates, not guaranteed outcomes
- Financial estimates are not audited accounting values
- 30-day forecasts are indicative and potentially lower-confidence than 7-day forecasts
- Outcome review shows association and before-versus-after movement, not proven causality
- Recommendations require human validation
- No autonomous clinical or operational execution
- Desktop web prototype
- No direct patient communication
- No production-grade identity, security or role-management implementation yet

## High-Level Development Phases

| Phase | Focus |
|---|---|
| Phase 1 | Product and Data Foundation — scope definition, data models, validation framework, KPI engine |
| Phase 2 | Detection, Forecasting and Scenario Engine — anomaly detection, forecasting, scenario comparison |
| Phase 3 | Recommendation, Decision and Tracking — ranked recommendations, approval workflow, action tracking |
| Phase 4 | Reporting, Integration and Hardening — executive reports, data-pipeline readiness, security review |

## Key Technical Principles

- All numerical outputs must be dynamically calculated and never hardcoded.
- Recommendation narratives must be grounded in calculated evidence.
- The agentic claim depends on the complete observe-analyse-recommend-approve-track-review loop.

## Current Project Status

**Phase 1 — Product and Data Foundation**

Scope defined; folder structure and foundational documentation in place. Analytics, UI and data layers will be built incrementally in subsequent steps.
