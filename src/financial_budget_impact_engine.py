"""
Financial Budget Impact Engine for Phase 2C-3.

Calculates budget requirements where cost data exists.
"""

import pandas as pd
from financial_base_engine import FinancialBaseEngine


class FinancialBudgetImpactEngine(FinancialBaseEngine):
    def __init__(self):
        super().__init__()

    def calculate_budget_impact(self, cost_summary: pd.DataFrame) -> pd.DataFrame:
        self.log("Calculating budget impact...")
        if len(cost_summary) == 0:
            return pd.DataFrame()

        df = cost_summary[["scenario_run_id", "approval_package_id", "scenario_family",
                            "comparator_type", "total_scenario_cost", "cost_completeness_status"]].copy()

        df["one_time_budget_requirement"] = df.apply(
            lambda r: r["total_scenario_cost"] * 0.3 if r["cost_completeness_status"] == "Complete with Governed Assumptions" else None,
            axis=1
        )
        df["recurring_budget_requirement"] = df.apply(
            lambda r: r["total_scenario_cost"] * 0.7 if r["cost_completeness_status"] == "Complete with Governed Assumptions" else None,
            axis=1
        )
        df["first_month_impact"] = df["total_scenario_cost"]
        df["intervention_period_impact"] = df["total_scenario_cost"]
        df["annualised_budget_impact"] = df.apply(
            lambda r: r["total_scenario_cost"] * 12 if r["cost_completeness_status"] == "Complete with Governed Assumptions" else None,
            axis=1
        )
        df["budget_data_available"] = False
        df["affordability_classification"] = "Budget Availability Unknown"
        df["governance_warning"] = "No authoritative budget data available — affordability not assessed"
        df["currency"] = "MYR"

        self.log(f"Budget impact: {len(df)} records.")
        return df
