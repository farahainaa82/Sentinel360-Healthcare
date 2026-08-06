# Product Scope — Sentinel360 Healthcare

## 1. Purpose

Sentinel360 Healthcare is a human-supervised, agentic executive early-warning and decision-support system for hospital operational performance. It provides the hospital leadership team with timely, evidence-based insight into operational health, connected risks and intervention options, while ensuring every consequential action is authorised by an accountable human decision-maker.

## 2. Problem Statement

Hospital operations are complex, interdependent and time-sensitive. Workforce shortages, capacity constraints, lengthening waits and rising complaints often develop as connected patterns rather than isolated incidents. Leadership needs:

- A single, current operational picture;
- Early warning of deterioration before it becomes a crisis;
- Transparent scenario comparisons to evaluate trade-offs;
- A clear, auditable path from recommendation to approved action to outcome review.

Existing tools often fragment data across HR, scheduling, bed-management and patient-experience systems, leaving leadership to synthesise manually.

## 3. Product-Scope Statement

Sentinel360 ingests operational data, validates it, calculates headline KPIs, detects anomalies and deterioration, forecasts short-term trajectories, compares intervention scenarios, estimates impact, ranks recommendations and presents them to authorised decision-makers for approval, modification or rejection. It logs every decision, tracks implementation and enables later outcome review.

## 4. Target Users and Their Roles

| Role | Primary or Supporting | Typical Approval Authority |
|---|---|---|
| Hospital Chief Operating Officer / General Manager | Primary | Executive; all domains |
| Medical Director | Primary | Clinical and operational governance |
| Nursing Director | Operational decision owner | Staffing and workforce interventions |
| Department Head | Operational decision owner | Capacity, scheduling and flow interventions |
| Patient Experience Lead | Informed stakeholder | Reviews patient-experience recommendations; does not approve staffing or clinical actions unless formally authorised |
| Authorised operational managers | Action owners | Domain-specific implementation and tracking |

Approval authority depends on the recommendation type. Staffing interventions require an authorised operational or nursing approver. Expenditure-related actions require an authorised financial or executive approver.

## 5. Management Decisions Supported

- Whether to escalate an operational issue immediately
- Whether to approve a temporary staffing intervention
- Whether to extend clinic hours or redirect patient flow
- Whether to reschedule elective admissions
- Whether to restore temporary capacity
- Whether to deploy peak-hour communication support
- Whether to approve an expenditure estimate attached to an intervention
- Who will own an approved action and by when
- Whether later performance improved after an intervention

## 6. Decision Horizons

| Horizon | Description |
|---|---|
| Immediate escalation | Real-time threshold breach requiring urgent attention |
| Next 7 days | Short-term operational planning horizon |
| Indicative next 30 days | Medium-term outlook; lower confidence than the 7-day forecast and explicitly labelled as indicative |
| Monthly executive review | Scheduled governance review of trends, decisions and outcomes |

## 7. Included Functions

1. Receive hospital operational data through file upload or future data pipeline.
2. Validate data structure, completeness and quality.
3. Calculate the six headline KPIs dynamically from raw data.
4. Detect threshold breaches, anomalies and deterioration patterns.
5. Identify connected risks across workforce, operations and patient experience.
6. Produce short-term forecasts (7-day and indicative 30-day).
7. Compare management intervention scenarios.
8. Estimate operational and financial impact using transparent configurable assumptions.
9. Rank and recommend management actions.
10. Allow authorised users to approve, modify or reject recommendations.
11. Record the decision, reason and approver.
12. Assign an action owner and target timeline.
13. Track implementation status.
14. Review whether later performance improved after an intervention.
15. Generate executive summaries and downloadable management reports.

## 8. Excluded Functions

- Direct electronic health record (EHR) integration in the prototype phase
- Direct HR, payroll or scheduling-system integration in the prototype phase
- Autonomous staff hiring, deployment or scheduling changes
- Autonomous patient redirection or admission rescheduling
- Autonomous expenditure approval or financial transaction execution
- Clinical diagnosis or treatment recommendation
- Direct patient communication (SMS, email, call)
- Production-grade identity and access management
- Real-time clinical alarm or pager integration

## 9. Human-in-the-Loop Boundaries

Sentinel360 must not autonomously:

- Hire or deploy staff
- Change staff or clinical schedules
- Reschedule admissions
- Redirect patients
- Approve expenditure
- Make clinical decisions
- Contact patients
- Execute operational interventions

Every recommendation must be presented for human review. The human user must be able to:

- Approve
- Modify
- Reject
- Record a reason
- Assign an owner
- Set a target timeline

All recommendations and decisions must be auditable.

## 10. Approval and Audit Requirements

- Every recommendation requires a recorded human decision.
- The approver identity, timestamp, decision and reason must be logged.
- Modifications to a recommendation must be recorded as a distinct decision event.
- Rejections must include a reason.
- Action assignments must record owner and target timeline.
- Implementation status updates must be timestamped.
- Outcome reviews must reference the original decision and action log.
- Reports must be reproducible from logged data.

## 11. Agentic AI Positioning

Sentinel360 is agentic in the sense that it closes the loop from observation through analysis, recommendation, human approval, action tracking and outcome review. The system actively proposes and explains, but it does not act without human authorisation. The agentic claim depends on the completeness of the observe-analyse-recommend-approve-track-review loop, not on autonomous execution.

## 12. Responsibility Boundary

### A. Deterministic Python analytics

- Data validation
- KPI calculation
- Threshold checks
- Statistical anomaly detection
- Forecast calculations and confidence intervals
- Scenario calculations
- Financial calculations
- Scenario scoring and ranking

### B. AI-assisted interpretation

- Explanation of connected risks
- Management interpretation
- Recommendation narrative
- Executive summary
- Action brief
- Outcome-review narrative

### C. Human management decision

- Validate operational context
- Approve, modify or reject
- Authorise expenditure
- Assign responsibility
- Execute the action
- Review the result

## 13. Initial Intervention Families

| Family | Description |
|---|---|
| Temporary staffing support | Additional nursing or support staff for a defined period |
| Extended clinic hours | Opening additional hours or additional sessions |
| Patient redirection | Guiding patients to alternative clinics or services |
| Elective admission rescheduling | Delaying non-urgent admissions to free capacity |
| Temporary capacity restoration | Opening additional beds, bays or zones |
| Peak-hour communication support | Additional front-desk or call-handling resource |
| No immediate intervention | Monitor and review; no action at this time |

## 14. Incremental Implementation Approach

The full product scope is approved, but implementation will be incremental.

Initial implementation may use:

- Local CSV or lightweight local storage for decision and action logs
- Transparent prototype assumptions for scenarios and financial impact
- Before-versus-after outcome comparison without claiming formal causal proof
- Predefined management roles instead of full production authentication
- One intervention family implemented first before expanding the scenario catalogue

## 15. Prototype Limitations

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

## 16. Product Success Criteria

Sentinel360 will be considered successfully scoped and ready for progression when it demonstrates:

- Valid file upload and validation
- Dynamic calculation of all six headline KPIs
- Detection of threshold breach and deterioration patterns
- Connected-risk explanation grounded in data
- 7-day operational forecast
- Indicative 30-day outlook
- Scenario comparison for at least one intervention family
- Transparent financial-impact calculation with configurable assumptions
- Ranked recommendation with evidence-based narrative
- Human approve, modify and reject paths with decision logging
- Action tracking with owner and timeline
- Later outcome review showing before-versus-after movement
- Executive summary and downloadable management report generation
- A complete end-to-end demo from upload to management decision

## 17. Scope-Control Rules

- All numerical outputs must be dynamically calculated and never hardcoded.
- Recommendation narratives must be grounded in calculated evidence.
- Thresholds and financial assumptions must be configurable and transparent.
- No autonomous execution of staffing, financial, clinical or communication actions.
- Every recommendation must present a clear human-approval path.
- Outcome review must describe association and movement, not causal proof.
- The agentic claim depends on the complete observe-analyse-recommend-approve-track-review loop.

## 18. Explicit Product Boundaries

Sentinel360 is **not**:

- A clinical decision system
- A hospital information system replacement
- A complaint-management platform
- An autonomous workforce-management system
- An autonomous financial approval system
