"""
Financial Confidence Engine for Phase 2C-3.

Assigns financial confidence levels based on input authority and completeness.
"""

import pandas as pd
from financial_base_engine import FinancialBaseEngine


class FinancialConfidenceEngine(FinancialBaseEngine):
    def __init__(self):
        super().__init__()

    def calculate_confidence(self, cost_summary: pd.DataFrame, benefit_summary: pd.DataFrame,
                             input_inventory: pd.DataFrame) -> pd.DataFrame:
        self.log("Calculating financial confidence...")
        if len(cost_summary) == 0:
            return pd.DataFrame()

        df = cost_summary[["scenario_run_id", "approval_package_id", "scenario_family",
                            "comparator_type", "cost_completeness_status"]].copy()

        # Count missing inputs per run
        if len(input_inventory) > 0 and "scenario_run_id" in input_inventory.columns:
            missing_counts = input_inventory.groupby("scenario_run_id")["missing_input_flag"].sum().reset_index()
            missing_counts = missing_counts.rename(columns={"missing_input_flag": "missing_input_count"})
            df = df.merge(missing_counts, on="scenario_run_id", how="left")
        else:
            df["missing_input_count"] = 0

        df["missing_input_count"] = df["missing_input_count"].fillna(0)

        def classify_confidence(row):
            if row["cost_completeness_status"] == "Insufficient Financial Inputs":
                return "Very Low"
            if float(row["missing_input_count"].iloc[0]) > 2:
                return "Very Low"
            if row["cost_completeness_status"] == "Partial Cost Estimate":
                return "Low"
            if float(row["missing_input_count"].iloc[0]) > 0:
                return "Low"
            return "Moderate"

        df["financial_confidence"] = df.apply(classify_confidence, axis=1)
        df["governance_warning"] = df["financial_confidence"].apply(
            lambda c: "High uncertainty — many missing inputs" if c == "Very Low" else (
                "Moderate uncertainty — some assumptions used" if c == "Low" else ""
            )
        )

        self.log(f"Confidence: {df['financial_confidence'].value_counts().to_dict()}")
        return df
