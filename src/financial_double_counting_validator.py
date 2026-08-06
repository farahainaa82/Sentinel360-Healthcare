"""
Financial Double-Counting Validator for Phase 2C-3.

Identifies potential duplicate benefits and costs.
"""

import pandas as pd
from financial_base_engine import FinancialBaseEngine


class FinancialDoubleCountingValidator(FinancialBaseEngine):
    def __init__(self):
        super().__init__()

    def validate(self, cost_components: pd.DataFrame, benefit_components: pd.DataFrame) -> pd.DataFrame:
        self.log("Validating double-counting...")
        issues = []

        # Check for duplicate cost components within same run
        if len(cost_components) > 0:
            dup_cost = cost_components.groupby(["scenario_run_id", "cost_component_name"]).size().reset_index(name="count")
            dup_cost = dup_cost[dup_cost["count"] > 1]
            for _, row in dup_cost.iterrows():
                issues.append({
                    "issue_id": f"DC-COST-{row['scenario_run_id']}-{row['cost_component_name'][:20]}",
                    "scenario_run_id": row["scenario_run_id"],
                    "issue_type": "Duplicate Cost Component",
                    "description": f"Cost component '{row['cost_component_name']}' appears {row['count']} times for same run",
                    "severity": "Medium",
                    "governance_warning": "Review for duplicate counting",
                })

        # Check for duplicate benefit components within same run
        if len(benefit_components) > 0:
            dup_ben = benefit_components.groupby(["scenario_run_id", "benefit_type"]).size().reset_index(name="count")
            dup_ben = dup_ben[dup_ben["count"] > 1]
            for _, row in dup_ben.iterrows():
                issues.append({
                    "issue_id": f"DC-BEN-{row['scenario_run_id']}-{row['benefit_type'][:20]}",
                    "scenario_run_id": row["scenario_run_id"],
                    "issue_type": "Duplicate Benefit Component",
                    "description": f"Benefit component '{row['benefit_type']}' appears {row['count']} times for same run",
                    "severity": "Medium",
                    "governance_warning": "Review for duplicate counting",
                })

        # Check for cost and benefit using same underlying driver
        if len(cost_components) > 0 and len(benefit_components) > 0:
            merged = cost_components.merge(benefit_components, on="scenario_run_id", how="inner", suffixes=("_cost", "_ben"))
            # Flag if same assumption drives both cost and benefit
            same_assumption = merged[merged["assumption_name"] == merged["source_scenario_effect"]]
            for _, row in same_assumption.iterrows():
                issues.append({
                    "issue_id": f"DC-SAME-{row['scenario_run_id']}-{row['assumption_name'][:20]}",
                    "scenario_run_id": row["scenario_run_id"],
                    "issue_type": "Same Driver for Cost and Benefit",
                    "description": f"Assumption '{row['assumption_name']}' drives both cost and benefit",
                    "severity": "High",
                    "governance_warning": "Potential double-counting — same operational driver used for cost and benefit",
                })

        df = pd.DataFrame(issues)
        self.log(f"Double-counting validation: {len(df)} issues.")
        return df
