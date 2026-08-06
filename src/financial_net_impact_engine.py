"""
Financial Net Impact Engine for Phase 2C-3.

Calculates net financial impact = benefit - cost where both are available.
"""

import pandas as pd
from financial_base_engine import FinancialBaseEngine


class FinancialNetImpactEngine(FinancialBaseEngine):
    def __init__(self):
        super().__init__()

    def calculate_net_impact(self, cost_summary: pd.DataFrame, benefit_summary: pd.DataFrame) -> pd.DataFrame:
        self.log("Calculating net financial impact...")
        if len(cost_summary) == 0:
            return pd.DataFrame()

        df = cost_summary[["scenario_run_id", "approval_package_id", "scenario_family",
                            "comparator_type", "total_scenario_cost", "cost_completeness_status"]].copy()

        if len(benefit_summary) > 0:
            ben = benefit_summary[["scenario_run_id", "total_estimated_benefit", "benefit_completeness_status"]].copy()
            df = df.merge(ben, on="scenario_run_id", how="left")
        else:
            df["total_estimated_benefit"] = 0
            df["benefit_completeness_status"] = "Not Calculated"

        df["total_estimated_benefit"] = df["total_estimated_benefit"].fillna(0)
        df["benefit_completeness_status"] = df["benefit_completeness_status"].fillna("Not Calculated")

        # Only calculate net when cost is complete and benefit is at least present
        def calc_net(row):
            if row["cost_completeness_status"] in ["Insufficient Financial Inputs"]:
                return None
            cost = row["total_scenario_cost"] if pd.notna(row["total_scenario_cost"]) else 0
            benefit = row["total_estimated_benefit"] if pd.notna(row["total_estimated_benefit"]) else 0
            return benefit - cost

        df["net_financial_impact"] = df.apply(calc_net, axis=1)
        df["currency"] = "MYR"
        df["net_impact_status"] = df.apply(lambda r: (
            "Calculated" if pd.notna(r["net_financial_impact"]) else "Not Calculated"
        ), axis=1)
        df["governance_warning"] = df.apply(lambda r: (
            "Partial estimate — benefit incomplete" if r["benefit_completeness_status"] == "Partial" else (
                "Cost incomplete — net not reliable" if r["cost_completeness_status"] != "Complete with Governed Assumptions" else ""
            )
        ), axis=1)

        self.log(f"Net impact: {len(df)} runs, {(df['net_impact_status']=='Calculated').sum()} calculated.")
        return df
