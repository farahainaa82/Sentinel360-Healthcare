# Step 3B Filter and Period Logic

## Filters
- Hospital, Department, Year, Month, Reporting Date
- KPI, Risk Tier, Urgency, Readiness Status
- Management Attention Level, Primary Queue, Validation Outcome

## Defaults
- All hospitals, all departments, latest year/month, all KPIs, all risk tiers, all readiness statuses

## Behaviour
- Apply Filters updates session state and reruns the page
- Reset Filters clears all selections
- Filters persist in st.session_state["executive_filters"]
- Empty results show a warning and stop rendering

## Period Handling
- No prior-period comparison unless authoritative data exists
- No fabrication of trends
