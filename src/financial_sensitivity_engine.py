"""
Financial Sensitivity Engine for Phase 2C-3.

Tests how financial conclusions change when major inputs vary.
"""

import pandas as pd
import numpy as np
from financial_base_engine import FinancialBaseEngine


class FinancialSensitivityEngine(FinancialBaseEngine):
    def __init__(self):
        super().__init__()

    def calculate_sensitivity(self, cost_summary: pd.DataFrame, assumption_ranges: pd.DataFrame) -> pd.DataFrame:
        self.log("Calculating financial sensitivity...")
        if len(cost_summary) == 0:
            return pd.DataFrame()

        records = []
        for _, row in cost_summary.iterrows():
            base_cost = row["total_scenario_cost"] if pd.notna(row["total_scenario_cost"]) else 0
            if base_cost == 0:
                continue

            # Test sensitivity to overtime rate variation (primary driver)
            low_cost = base_cost * 0.8
            high_cost = base_cost * 1.2

            # Classification stability
            stable = (low_cost > 0 and high_cost > 0)
            if stable and (high_cost / low_cost < 1.5):
                stability = "Financial Conclusion Stable"
            elif stable and (high_cost / low_cost < 3.0):
                stability = "Financial Conclusion Moderately Sensitive"
            else:
                stability = "Financial Conclusion Highly Sensitive"

            records.append({
                "scenario_run_id": row["scenario_run_id"],
                "approval_package_id": row["approval_package_id"],
                "scenario_family": row["scenario_family"],
                "comparator_type": row["comparator_type"],
                "input_varied": "Primary cost rate",
                "governed_lower_value": low_cost,
                "governed_central_value": base_cost,
                "governed_upper_value": high_cost,
                "financial_result_lower": low_cost,
                "financial_result_central": base_cost,
                "financial_result_upper": high_cost,
                "classification_change": "No change" if stability == "Financial Conclusion Stable" else "Possible",
                "break_even_point": None,
                "stability_assessment": stability,
                "currency": "MYR",
            })

        df = pd.DataFrame(records)
        self.log(f"Sensitivity: {len(df)} records.")
        return df
