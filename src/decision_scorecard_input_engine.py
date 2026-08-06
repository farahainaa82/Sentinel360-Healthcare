"""
Decision Scorecard Input Engine for Phase 2D-1.

Creates a scorecard-ready structure for each integrated decision record.
Does not create a single "best option" score or rank scenarios automatically.
"""

import pandas as pd
import numpy as np


class DecisionScorecardInputEngine:
    def build_scorecard(self, df: pd.DataFrame) -> pd.DataFrame:
        records = []
        for _, row in df.iterrows():
            rec = self._build_row(row)
            records.append(rec)
        return pd.DataFrame(records)

    def _build_row(self, row) -> dict:
        pkg_id = row.get("approval_package_id", "")
        decision_id = row.get("integrated_decision_id", "")

        # Operational risk score (0-100)
        risk_score = row.get("risk_score", 0)
        if pd.isna(risk_score):
            risk_score = 0
        try:
            risk_score = float(risk_score)
        except (ValueError, TypeError):
            risk_score = 0

        # Readiness components
        rec_ready = 1.0 if pd.notna(row.get("representative_recommendation", None)) and str(row.get("representative_recommendation", "")) != "" else 0.0
        scenario_ready = 1.0 if pd.notna(row.get("management_scenario_package_id", None)) and str(row.get("management_scenario_package_id", "")) != "" else 0.0
        comparator_ready = 1.0 if "Complete" in str(row.get("comparator_completeness", "")) else 0.0
        financial_ready = 1.0 if pd.notna(row.get("financial_readiness", None)) and str(row.get("financial_readiness", "")) != "" else 0.0

        # Trade-off and displacement
        tradeoff = str(row.get("scenario_tradeoff_summary", ""))
        tradeoff_severity = 0.5 if "trade" in tradeoff.lower() else 0.0
        displacement = str(row.get("scenario_displacement_summary", ""))
        displacement_risk = 0.5 if "displace" in displacement.lower() else 0.0

        # Financial confidence
        conf = str(row.get("scenario_confidence", ""))
        if "Moderate" in conf:
            fin_conf = 0.5
        elif "Low" in conf:
            fin_conf = 0.3
        elif "High" in conf:
            fin_conf = 0.8
        else:
            fin_conf = 0.2

        # Cost completeness
        cost_comp = str(row.get("cost_completeness_status", ""))
        cost_complete = 1.0 if "Complete" in cost_comp else 0.5 if "Partial" in cost_comp else 0.0

        # Governance burden
        gov_count = row.get("governance_issue_count", 0)
        if pd.isna(gov_count):
            gov_count = 0
        try:
            gov_count = int(gov_count)
        except (ValueError, TypeError):
            gov_count = 0
        gov_burden = min(gov_count / 5.0, 1.0)

        # Evidence completeness
        evidence_complete = 1.0 if str(row.get("evidence_available", "")).lower() == "true" else 0.5
        lineage_complete = 1.0 if str(row.get("lineage_available", "")).lower() == "true" else 0.5

        # Overall decision readiness (weighted average)
        overall = (
            0.15 * min(risk_score / 100.0, 1.0) +
            0.10 * rec_ready +
            0.15 * scenario_ready +
            0.10 * comparator_ready +
            0.15 * financial_ready +
            0.10 * cost_complete +
            0.10 * (1.0 - gov_burden) +
            0.10 * evidence_complete +
            0.05 * lineage_complete
        )

        return {
            "integrated_decision_id": decision_id,
            "approval_package_id": pkg_id,
            "operational_risk_score": round(risk_score, 2),
            "recommendation_readiness": round(rec_ready, 2),
            "scenario_readiness": round(scenario_ready, 2),
            "comparator_consistency": round(comparator_ready, 2),
            "tradeoff_severity": round(tradeoff_severity, 2),
            "displacement_risk": round(displacement_risk, 2),
            "financial_readiness": round(financial_ready, 2),
            "cost_completeness": round(cost_complete, 2),
            "financial_confidence_score": round(fin_conf, 2),
            "governance_burden": round(gov_burden, 2),
            "evidence_completeness": round(evidence_complete, 2),
            "lineage_completeness": round(lineage_complete, 2),
            "overall_decision_readiness": round(overall, 3),
            "scorecard_note": "Individual component scores for decision support. Not a single best-option ranking.",
        }
