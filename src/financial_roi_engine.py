"""
Financial ROI Engine for Phase 2C-3.

Calculates ROI only where eligibility conditions pass.
"""

import pandas as pd
import numpy as np
from financial_base_engine import FinancialBaseEngine


class FinancialROIEngine(FinancialBaseEngine):
    def __init__(self):
        super().__init__()

    def calculate_roi(self, net_impact: pd.DataFrame, cost_summary: pd.DataFrame,
                      benefit_summary: pd.DataFrame) -> pd.DataFrame:
        self.log("Calculating ROI...")
        if len(cost_summary) == 0:
            return pd.DataFrame()

        df = cost_summary[["scenario_run_id", "approval_package_id", "scenario_family",
                            "comparator_type", "total_scenario_cost", "cost_completeness_status"]].copy()

        # Merge benefit
        if len(benefit_summary) > 0:
            ben = benefit_summary[["scenario_run_id", "total_estimated_benefit", "benefit_completeness_status"]].copy()
            df = df.merge(ben, on="scenario_run_id", how="left")
        else:
            df["total_estimated_benefit"] = 0
            df["benefit_completeness_status"] = "Not Calculated"

        df["total_estimated_benefit"] = df["total_estimated_benefit"].fillna(0)

        # Eligibility check
        def classify_roi(row):
            if row["cost_completeness_status"] != "Complete with Governed Assumptions":
                return "ROI Not Calculated — Incomplete Cost", None
            if row["benefit_completeness_status"] not in ["Complete", "Partial"]:
                return "ROI Not Calculated — Incomplete Benefit", None
            cost = row["total_scenario_cost"]
            if pd.isna(cost) or cost == 0:
                return "ROI Not Calculated — Governance Restriction", None
            benefit = row["total_estimated_benefit"] if pd.notna(row["total_estimated_benefit"]) else 0
            roi = ((benefit - cost) / cost) * 100
            if np.isfinite(roi):
                return "ROI Calculated — Governed Inputs", roi
            return "ROI Not Calculated — Governance Restriction", None

        roi_result = df.apply(classify_roi, axis=1, result_type="expand")
        roi_result.columns = ["roi_status", "roi_percent"]
        df = pd.concat([df, roi_result], axis=1)

        self.log(f"ROI: {(df['roi_status']=='ROI Calculated — Governed Inputs').sum()} calculated.")
        return df
