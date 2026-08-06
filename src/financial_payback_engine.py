"""
Financial Payback Engine for Phase 2C-3.

Calculates payback period only where eligible.
"""

import pandas as pd
import numpy as np
from financial_base_engine import FinancialBaseEngine


class FinancialPaybackEngine(FinancialBaseEngine):
    def __init__(self):
        super().__init__()

    def calculate_payback(self, cost_summary: pd.DataFrame, benefit_summary: pd.DataFrame) -> pd.DataFrame:
        self.log("Calculating payback period...")
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

        def classify_payback(row):
            if row["cost_completeness_status"] != "Complete with Governed Assumptions":
                return "Not Calculated — Incomplete Cost", None, ""
            if row["benefit_completeness_status"] not in ["Complete", "Partial"]:
                return "Not Calculated — Incomplete Benefit", None, ""
            cost = row["total_scenario_cost"]
            benefit = row["total_estimated_benefit"]
            if pd.isna(cost) or cost <= 0:
                return "Not Calculated — Zero Cost", None, ""
            if pd.isna(benefit) or benefit <= 0:
                return "Not Calculated — Zero Benefit", None, ""
            payback = cost / benefit
            if np.isfinite(payback):
                return "Calculated", payback, "months"
            return "Not Calculated — Invalid", None, ""

        payback_result = df.apply(classify_payback, axis=1, result_type="expand")
        payback_result.columns = ["payback_status", "payback_period", "payback_unit"]
        df = pd.concat([df, payback_result], axis=1)

        self.log(f"Payback: {(df['payback_status']=='Calculated').sum()} calculated.")
        return df
