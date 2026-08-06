"""
Decision Readiness Engine for Phase 2D-1.

Assesses decision readiness per integrated decision record.
"""

import pandas as pd
import numpy as np


class DecisionReadinessEngine:
    def assess_readiness(self, df: pd.DataFrame) -> pd.DataFrame:
        records = []
        for _, row in df.iterrows():
            rec = self._assess_row(row)
            records.append(rec)
        return pd.DataFrame(records)

    def _assess_row(self, row) -> dict:
        pkg_id = row.get("approval_package_id", "")
        decision_id = row.get("integrated_decision_id", "")
        status = row.get("decision_status", "")

        # Evidence availability
        risk_evidence = pd.notna(row.get("risk_score", None)) and row.get("risk_score", 0) != 0
        rec_evidence = pd.notna(row.get("representative_recommendation", None)) and str(row.get("representative_recommendation", "")) != ""
        scenario_evidence = pd.notna(row.get("management_scenario_package_id", None)) and str(row.get("management_scenario_package_id", "")) != ""
        financial_evidence = pd.notna(row.get("financial_readiness", None)) and str(row.get("financial_readiness", "")) != ""
        gov_clean = int(row.get("governance_issue_count", 0) or 0) == 0

        # Readiness scoring (0-1)
        readiness_score = 0.0
        if risk_evidence:
            readiness_score += 0.20
        if rec_evidence:
            readiness_score += 0.15
        if scenario_evidence:
            readiness_score += 0.20
        if financial_evidence:
            readiness_score += 0.20
        if gov_clean:
            readiness_score += 0.15
        if str(row.get("comparator_completeness", "")).lower() in ["complete", "sufficient", "all three comparators present"]:
            readiness_score += 0.10

        # Readiness category
        if readiness_score >= 0.90 and status == "Ready for Integrated Management Review":
            readiness_category = "Fully Ready"
        elif readiness_score >= 0.70:
            readiness_category = "Substantially Ready"
        elif readiness_score >= 0.50:
            readiness_category = "Partially Ready"
        elif readiness_score >= 0.30:
            readiness_category = "Limited Readiness"
        else:
            readiness_category = "Not Ready"

        # Conditions
        conditions = []
        if not gov_clean:
            conditions.append("Unresolved governance issues remain")
        if not scenario_evidence:
            conditions.append("Scenario package not yet available")
        if not financial_evidence:
            conditions.append("Financial analysis incomplete")
        if str(row.get("comparator_completeness", "")).lower() not in ["complete", "sufficient", "all three comparators present"]:
            conditions.append("Comparator completeness not confirmed")
        if "Draft" in str(row.get("financial_readiness", "")):
            conditions.append("Financial inputs remain draft")

        conditions_str = "; ".join(conditions) if conditions else "None"

        return {
            "integrated_decision_id": decision_id,
            "approval_package_id": pkg_id,
            "decision_status": status,
            "risk_evidence_available": risk_evidence,
            "recommendation_evidence_available": rec_evidence,
            "scenario_evidence_available": scenario_evidence,
            "financial_evidence_available": financial_evidence,
            "governance_clean": gov_clean,
            "readiness_score": round(readiness_score, 3),
            "readiness_category": readiness_category,
            "remaining_conditions": conditions_str,
        }
