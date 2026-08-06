"""
Decision Action Routing Engine for Phase 2D-1.

Determines permitted management actions per integrated decision record.
No action is marked as selected.
"""

import pandas as pd


class DecisionActionRoutingEngine:
    ALLOWED_ACTIONS = [
        "Review Integrated Decision Package",
        "Compare Scenario Options",
        "Validate Assumptions",
        "Validate Baseline",
        "Validate Financial Inputs",
        "Request Additional Scenario",
        "Request Stakeholder Review",
        "Proceed to Limited-Trial Consideration",
        "Continue Monitoring",
        "Defer Decision",
        "Reject Decision Use",
    ]

    def route_actions(self, df: pd.DataFrame) -> pd.DataFrame:
        records = []
        for _, row in df.iterrows():
            actions = self._determine_actions(row)
            records.append({
                "integrated_decision_id": row.get("integrated_decision_id", ""),
                "approval_package_id": row.get("approval_package_id", ""),
                "decision_status": row.get("decision_status", ""),
                "permitted_management_actions": " | ".join(actions),
                "action_count": len(actions),
                "primary_suggested_action": actions[0] if actions else "None",
                "action_selection_status": "Not Selected",
                "governance_note": "Actions are permitted, not pre-selected. Management must choose.",
            })
        return pd.DataFrame(records)

    def _determine_actions(self, row) -> list:
        status = str(row.get("decision_status", ""))
        scenario_ready = str(row.get("scenario_readiness", ""))
        financial_ready = str(row.get("financial_readiness", ""))
        comparator_comp = str(row.get("comparator_completeness", ""))
        has_scenario = pd.notna(row.get("management_scenario_package_id", None)) and str(row.get("management_scenario_package_id", "")) != ""
        has_financial = pd.notna(row.get("financial_readiness", None)) and str(row.get("financial_readiness", "")) != ""
        assumptions_need_review = "Assumption" in status
        baseline_need_review = "Baseline" in status
        financial_need_review = "Financial" in status
        stakeholder_need_review = "Stakeholder" in status

        actions = ["Review Integrated Decision Package"]

        if has_scenario and "Complete" in comparator_comp:
            actions.append("Compare Scenario Options")

        if assumptions_need_review:
            actions.append("Validate Assumptions")

        if baseline_need_review:
            actions.append("Validate Baseline")

        if financial_need_review or (has_financial and "Draft" in financial_ready):
            actions.append("Validate Financial Inputs")

        if not has_scenario or "Additional Scenario" in status:
            actions.append("Request Additional Scenario")

        if stakeholder_need_review:
            actions.append("Request Stakeholder Review")

        if status == "Ready for Integrated Management Review":
            actions.append("Proceed to Limited-Trial Consideration")

        if status in ["Monitoring Only", "Ready with Conditions"]:
            actions.append("Continue Monitoring")

        if status not in ["Ready for Integrated Management Review", "Rejected"]:
            actions.append("Defer Decision")

        if status in ["Rejected", "Not Suitable for Decision Use"]:
            actions.append("Reject Decision Use")

        # Deduplicate while preserving order
        seen = set()
        unique_actions = []
        for a in actions:
            if a not in seen:
                seen.add(a)
                unique_actions.append(a)
        return unique_actions
