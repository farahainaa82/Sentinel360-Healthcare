"""
Financial Readiness Engine for Phase 2C-3.

Assigns each management scenario package one financial readiness category.
"""

import pandas as pd
from financial_base_engine import FinancialBaseEngine


class FinancialReadinessEngine(FinancialBaseEngine):
    def __init__(self):
        super().__init__()

    def calculate_readiness(self, management_packages: pd.DataFrame, cost_summary: pd.DataFrame,
                            benefit_summary: pd.DataFrame, net_impact: pd.DataFrame) -> pd.DataFrame:
        self.log("Calculating financial readiness...")
        if len(management_packages) == 0:
            return pd.DataFrame()

        df = management_packages[["management_scenario_package_id", "approval_package_id",
                                   "scenario_family", "financial_review_required"]].copy()

        # Aggregate cost completeness per package
        if len(cost_summary) > 0:
            pkg_cost = cost_summary.groupby("approval_package_id").agg({
                "cost_completeness_status": lambda s: "Complete with Governed Assumptions" if (s == "Complete with Governed Assumptions").any() else s.iloc[0],
                "total_scenario_cost": "sum",
            }).reset_index()
            df = df.merge(pkg_cost, on="approval_package_id", how="left")
        else:
            df["cost_completeness_status"] = "Not Calculated"
            df["total_scenario_cost"] = 0

        if len(benefit_summary) > 0:
            pkg_ben = benefit_summary.groupby("approval_package_id").agg({
                "benefit_completeness_status": lambda s: "Complete" if (s == "Complete").any() else s.iloc[0],
                "total_estimated_benefit": "sum",
            }).reset_index()
            df = df.merge(pkg_ben, on="approval_package_id", how="left")
        else:
            df["benefit_completeness_status"] = "Not Calculated"
            df["total_estimated_benefit"] = 0

        df["cost_completeness_status"] = df["cost_completeness_status"].fillna("Not Calculated")
        df["benefit_completeness_status"] = df["benefit_completeness_status"].fillna("Not Calculated")
        df["total_scenario_cost"] = df["total_scenario_cost"].fillna(0)
        df["total_estimated_benefit"] = df["total_estimated_benefit"].fillna(0)

        def classify_readiness(row):
            if row["cost_completeness_status"] == "Complete with Governed Assumptions":
                if row["benefit_completeness_status"] == "Complete":
                    return "Ready for Financial Comparison"
                return "Ready with Financial Conditions"
            if row["cost_completeness_status"] == "Partial Cost Estimate":
                return "Partial Financial Estimate Only"
            if row["cost_completeness_status"] == "Insufficient Financial Inputs":
                return "Requires Cost Input"
            if row["financial_review_required"] != "Yes":
                return "Financial Analysis Not Applicable"
            return "Financial Analysis Not Assessable"

        df["financial_readiness"] = df.apply(classify_readiness, axis=1)
        df["financial_readiness_reason"] = df["cost_completeness_status"]
        df["governance_warning"] = "Draft analytical estimate — requires stakeholder validation"

        self.log(f"Financial readiness: {df['financial_readiness'].value_counts().to_dict()}")
        return df
