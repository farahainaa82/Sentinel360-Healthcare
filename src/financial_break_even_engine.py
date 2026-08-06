"""
Financial Break-Even Engine for Phase 2C-3.

Calculates break-even points where valid.
"""

import pandas as pd
import numpy as np
from financial_base_engine import FinancialBaseEngine


class FinancialBreakEvenEngine(FinancialBaseEngine):
    def __init__(self):
        super().__init__()

    def calculate_break_even(self, cost_summary: pd.DataFrame, benefit_summary: pd.DataFrame) -> pd.DataFrame:
        self.log("Calculating break-even...")
        if len(cost_summary) == 0:
            return pd.DataFrame()

        df = cost_summary[["scenario_run_id", "approval_package_id", "scenario_family",
                            "comparator_type", "total_scenario_cost", "cost_completeness_status"]].copy()

        if len(benefit_summary) > 0:
            ben = benefit_summary[["scenario_run_id", "total_estimated_benefit"]].copy()
            df = df.merge(ben, on="scenario_run_id", how="left")
        else:
            df["total_estimated_benefit"] = 0

        df["total_estimated_benefit"] = df["total_estimated_benefit"].fillna(0)

        records = []
        for _, row in df.iterrows():
            cost = row["total_scenario_cost"] if pd.notna(row["total_scenario_cost"]) else 0
            benefit = row["total_estimated_benefit"] if pd.notna(row["total_estimated_benefit"]) else 0

            if cost <= 0 or benefit <= 0 or cost == benefit:
                status = "Not Calculated — Invalid Parameters"
                value = None
                measure = ""
            else:
                # Break-even in months
                monthly_benefit = benefit / 12.0
                if monthly_benefit > 0:
                    value = cost / monthly_benefit
                    if np.isfinite(value):
                        status = "Calculated"
                        measure = "months"
                    else:
                        status = "Not Calculated — Invalid"
                        value = None
                        measure = ""
                else:
                    status = "Not Calculated — Zero Benefit"
                    value = None
                    measure = ""

            records.append({
                "scenario_run_id": row["scenario_run_id"],
                "approval_package_id": row["approval_package_id"],
                "scenario_family": row["scenario_family"],
                "comparator_type": row["comparator_type"],
                "break_even_status": status,
                "break_even_value": value,
                "break_even_measure": measure,
                "governance_warning": "Break-even depends on sustained benefit — not confirmed",
            })

        df = pd.DataFrame(records)
        self.log(f"Break-even: {(df['break_even_status']=='Calculated').sum()} calculated.")
        return df
