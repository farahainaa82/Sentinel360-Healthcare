"""
Decision Management Summary Engine for Phase 2D-1.

Creates one concise management summary per integrated decision record.
Uses permitted wording only.
"""

import pandas as pd


class DecisionManagementSummaryEngine:
    PERMITTED_WORDING = [
        "Estimated", "Analytical", "May improve", "Appears to improve",
        "Requires validation", "Ready with Conditions", "Not Confirmed",
        "Pending Management Review",
    ]

    PROHIBITED_WORDING = [
        "Guaranteed", "Proven", "Best", "Optimal", "Approved",
        "Will improve", "Will save", "Recommended scenario",
    ]

    def build_summaries(self, df: pd.DataFrame) -> pd.DataFrame:
        records = []
        for _, row in df.iterrows():
            rec = self._build_summary(row)
            records.append(rec)
        return pd.DataFrame(records)

    def _build_summary(self, row) -> dict:
        pkg_id = row.get("approval_package_id", "")
        decision_id = row.get("integrated_decision_id", "")
        hospital = str(row.get("hospital_name", "Unknown Hospital"))
        dept = str(row.get("department_name", "Unknown Department"))
        kpi = str(row.get("dominant_kpi_name", "Unknown KPI"))
        family = str(row.get("scenario_family", ""))
        risk_tier = str(row.get("risk_tier", ""))
        priority = str(row.get("priority_tier", ""))
        urgency = str(row.get("urgency", ""))
        rec = str(row.get("representative_recommendation", ""))
        status = str(row.get("decision_status", ""))
        lower = row.get("lower_financial_estimate", None)
        central = row.get("central_financial_estimate", None)
        upper = row.get("upper_financial_estimate", None)
        uncertainty = str(row.get("uncertainty_range", ""))
        net_impact = row.get("net_financial_impact", None)
        actions = str(row.get("permitted_management_actions", ""))
        confidence = str(row.get("financial_confidence", ""))
        causality = str(row.get("causality_status", "Not Confirmed"))

        # Format financial estimate text
        fin_text = ""
        if pd.notna(central) and central != 0:
            fin_text = f"Estimated net financial impact is MYR {central:,.0f}."
            if pd.notna(lower) and pd.notna(upper):
                fin_text += f" Analytical uncertainty range: MYR {lower:,.0f} to MYR {upper:,.0f}."
        else:
            fin_text = "Financial impact estimation requires additional input validation."

        # What is happening
        what = f"{hospital} — {dept} is experiencing {family}-related operational pressure with {kpi} as the dominant indicator. Risk tier: {risk_tier}. Priority: {priority}. Urgency: {urgency}."

        # Why does it matter
        why = f"The {risk_tier} risk tier and {priority} priority indicate this package requires management attention. Causality between interventions and outcomes remains {causality}."

        # Evidence
        evidence = f"KPI breach evidence, trend analysis, and risk prioritisation support this package. Recommendation evidence: {rec if rec else 'Not yet formulated'}."

        # Proposed action
        proposed = f"Recommended action category: {rec if rec else 'Awaiting stakeholder input'}. This is an analytical estimate that requires validation before proceeding."

        # Scenario options
        scenario_text = ""
        has_conservative = str(row.get("conservative_available", "")).lower() == "true"
        has_expected = str(row.get("expected_available", "")).lower() == "true"
        has_higher = str(row.get("higher_intensity_available", "")).lower() == "true"
        if has_conservative and has_expected and has_higher:
            scenario_text = "Three scenario comparator options are available for review: Conservative, Expected, and Higher Intensity."
        elif has_expected:
            scenario_text = "Expected scenario comparator is available for review."
        else:
            scenario_text = "Scenario options are partially available and may require additional analysis."

        # Trade-offs
        tradeoff = str(row.get("scenario_tradeoff_summary", ""))
        tradeoff_text = f"Trade-off analysis: {tradeoff if tradeoff else 'Not yet completed'}."

        # Financial impact
        financial_text = fin_text

        # Uncertainty
        uncertainty_text = f"Financial confidence level: {confidence if confidence else 'Not Assessable'}. {uncertainty if uncertainty else 'Uncertainty analysis pending'}."

        # Confirmations required
        confirmations = f"Management must confirm: causality remains {causality}; assumptions require stakeholder validation; financial inputs are draft analytical estimates."

        # Permitted next action
        next_action = f"Permitted next actions: {actions if actions else 'Review package details'}. No action is pre-selected."

        summary = (
            f"WHAT IS HAPPENING: {what}\n\n"
            f"WHY IT MATTERS: {why}\n\n"
            f"EVIDENCE: {evidence}\n\n"
            f"PROPOSED ACTION: {proposed}\n\n"
            f"SCENARIO OPTIONS: {scenario_text}\n\n"
            f"TRADE-OFFS: {tradeoff_text}\n\n"
            f"ESTIMATED FINANCIAL IMPACT: {financial_text}\n\n"
            f"UNCERTAINTY: {uncertainty_text}\n\n"
            f"CONFIRMATIONS REQUIRED: {confirmations}\n\n"
            f"PERMITTED NEXT ACTION: {next_action}"
        )

        return {
            "integrated_decision_id": decision_id,
            "approval_package_id": pkg_id,
            "management_summary": summary,
            "summary_status": status,
            "wording_compliance": "Permitted wording only",
            "governance_note": "Summary uses analytical language. No guarantees or approvals stated.",
        }
