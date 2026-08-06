"""
Financial Affordability Engine for Phase 2C-3.

Classifies affordability using governed rules.
"""

import pandas as pd
from financial_base_engine import FinancialBaseEngine


class FinancialAffordabilityEngine(FinancialBaseEngine):
    def __init__(self):
        super().__init__()

    def calculate_affordability(self, budget_impact: pd.DataFrame) -> pd.DataFrame:
        self.log("Calculating affordability...")
        if len(budget_impact) == 0:
            return pd.DataFrame()

        df = budget_impact[["scenario_run_id", "approval_package_id", "scenario_family",
                             "comparator_type", "total_scenario_cost", "affordability_classification"]].copy()

        # Since no budget data exists, all are unknown
        df["affordability_classification"] = "Budget Availability Unknown"
        df["affordability_reason"] = "No authoritative budget or spending-limit data supplied"
        df["governance_warning"] = "Do not assume hospital has sufficient funds"

        self.log(f"Affordability: {len(df)} records.")
        return df
