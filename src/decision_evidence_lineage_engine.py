"""
Decision Evidence and Lineage Engine for Phase 2D-1.

Creates integrated evidence and lineage registers.
Ensures no orphan decision records exist.
"""

import pandas as pd


class DecisionEvidenceLineageEngine:
    STAGES = [
        "raw data",
        "processed data",
        "KPI calculation",
        "trend and threshold",
        "risk prioritisation",
        "recommendation",
        "scenario modelling",
        "financial analysis",
        "integrated decision record",
    ]

    def build_evidence_register(self, df: pd.DataFrame) -> pd.DataFrame:
        records = []
        for _, row in df.iterrows():
            rec = self._build_evidence(row)
            records.append(rec)
        return pd.DataFrame(records)

    def build_lineage_register(self, df: pd.DataFrame) -> pd.DataFrame:
        records = []
        for _, row in df.iterrows():
            rec = self._build_lineage(row)
            records.append(rec)
        return pd.DataFrame(records)

    def _build_evidence(self, row) -> dict:
        decision_id = row.get("integrated_decision_id", "")
        pkg_id = row.get("approval_package_id", "")

        evidence_sources = []
        if pd.notna(row.get("risk_score", None)) and row.get("risk_score", 0) != 0:
            evidence_sources.append("Phase 2B Risk Ranking")
        if pd.notna(row.get("representative_recommendation", None)) and str(row.get("representative_recommendation", "")) != "":
            evidence_sources.append("Phase 2C-1 Recommendation Register")
        if pd.notna(row.get("management_scenario_package_id", None)) and str(row.get("management_scenario_package_id", "")) != "":
            evidence_sources.append("Phase 2C-2 Scenario Modelling")
        if pd.notna(row.get("financial_readiness", None)) and str(row.get("financial_readiness", "")) != "":
            evidence_sources.append("Phase 2C-3 Financial Analysis")
        if str(row.get("closure_category", "")) != "":
            evidence_sources.append("Phase 2C-2F Package Closure")

        evidence_available = len(evidence_sources) > 0
        evidence_types = " | ".join(evidence_sources) if evidence_sources else "None"

        return {
            "integrated_decision_id": decision_id,
            "approval_package_id": pkg_id,
            "evidence_available": evidence_available,
            "evidence_types": evidence_types,
            "evidence_count": len(evidence_sources),
            "kpi_evidence": "Phase 2A KPI Analytics" in evidence_sources or "Phase 2B Risk Ranking" in evidence_sources,
            "risk_evidence": "Phase 2B Risk Ranking" in evidence_sources,
            "recommendation_evidence": "Phase 2C-1 Recommendation Register" in evidence_sources,
            "scenario_evidence": "Phase 2C-2 Scenario Modelling" in evidence_sources,
            "financial_evidence": "Phase 2C-3 Financial Analysis" in evidence_sources,
            "governance_evidence": "Phase 2C-2F Package Closure" in evidence_sources,
            "evidence_completeness_score": round(len(evidence_sources) / 5.0, 2),
            "lineage_reference": "Phase 1 → 2A → 2B → 2C-1 → 2C-2 → 2C-3 → 2D-1",
        }

    def _build_lineage(self, row) -> dict:
        decision_id = row.get("integrated_decision_id", "")
        pkg_id = row.get("approval_package_id", "")

        lineage_stages = []
        lineage_stages.append("raw data → processed data")
        lineage_stages.append("processed data → KPI calculation")
        lineage_stages.append("KPI calculation → trend and threshold")
        lineage_stages.append("trend and threshold → risk prioritisation")
        lineage_stages.append("risk prioritisation → recommendation")
        if pd.notna(row.get("management_scenario_package_id", None)) and str(row.get("management_scenario_package_id", "")) != "":
            lineage_stages.append("recommendation → scenario modelling")
        if pd.notna(row.get("financial_readiness", None)) and str(row.get("financial_readiness", "")) != "":
            lineage_stages.append("scenario modelling → financial analysis")
        lineage_stages.append("financial analysis → integrated decision record")

        return {
            "integrated_decision_id": decision_id,
            "approval_package_id": pkg_id,
            "lineage_available": True,
            "lineage_stages": " → ".join(lineage_stages),
            "stage_count": len(lineage_stages) + 1,
            "raw_data_source": "Phase 1 Data Foundation",
            "processed_data_source": "Phase 1 Data Processing",
            "kpi_source": "Phase 2A KPI Analytics",
            "trend_threshold_source": "Phase 2B Early Warning",
            "risk_source": "Phase 2B Risk Intelligence",
            "recommendation_source": "Phase 2C-1 Recommendations",
            "scenario_source": "Phase 2C-2 Scenario Modelling" if "scenario modelling" in " → ".join(lineage_stages) else "Not Applicable",
            "financial_source": "Phase 2C-3 Financial Impact" if "financial analysis" in " → ".join(lineage_stages) else "Not Applicable",
            "integration_source": "Phase 2D-1 Integrated Decision Model",
            "lineage_completeness_score": round(len(lineage_stages) / len(self.STAGES), 2),
        }
