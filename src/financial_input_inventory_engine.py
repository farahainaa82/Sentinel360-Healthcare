"""
Financial Input Inventory Engine for Phase 2C-3.

Builds the financial-input inventory from 2C-2F requirements and
classifies each input by availability and status.
"""

import os
import pandas as pd
from typing import Dict

from financial_base_engine import FinancialBaseEngine


class FinancialInputInventoryEngine(FinancialBaseEngine):
    def __init__(self):
        super().__init__()

    def build_inventory(self, financial_requirements: pd.DataFrame, input_definitions: pd.DataFrame,
                        runs: pd.DataFrame, management_packages: pd.DataFrame) -> pd.DataFrame:
        self.log("Building financial input inventory...")

        if len(financial_requirements) == 0:
            return pd.DataFrame()

        # Merge with management packages to get management_scenario_package_id
        req = financial_requirements.copy()
        if len(management_packages) > 0 and "management_scenario_package_id" in management_packages.columns:
            mgmt_map = management_packages[["approval_package_id", "management_scenario_package_id"]].copy()
            req = req.merge(mgmt_map, on="approval_package_id", how="left")
        else:
            req["management_scenario_package_id"] = ""

        # Map scenario_run_id from runs (first completed run per package)
        completed = runs[runs["scenario_execution_status"] == "Completed"].copy()
        if len(completed) > 0:
            run_map = completed.groupby("approval_package_id").agg({
                "scenario_run_id": "first",
                "scenario_template_id": "first",
                "comparator_id": "first",
            }).reset_index()
            req = req.merge(run_map, on="approval_package_id", how="left")
        else:
            req["scenario_run_id"] = ""
            req["scenario_template_id"] = ""
            req["comparator_id"] = ""

        # Create financial_input_requirement_id
        req["financial_input_requirement_id"] = req.groupby("approval_package_id").cumcount().apply(
            lambda i: f"FIN-REQ-{req.iloc[i]['approval_package_id']}-{i+1}"
        )

        # Merge with input definitions to check availability
        def_map = input_definitions.set_index("financial_input_id").to_dict("index")

        def classify_input(row):
            input_name = row["required_cost_input"]
            # Find matching definition by name similarity
            matched_id = None
            for fid, fdef in def_map.items():
                if input_name.replace("_", "").lower() in fdef["financial_input_name"].replace(" ", "").lower():
                    matched_id = fid
                    break
                if fdef["financial_input_name"].replace(" ", "").lower() in input_name.replace("_", "").lower():
                    matched_id = fid
                    break

            if matched_id:
                fdef = def_map[matched_id]
                default_val = fdef.get("default_value")
                if pd.notna(default_val) and default_val != "":
                    return "Governed Analytical Assumption", False, matched_id
                else:
                    return "Missing", True, matched_id
            return "Missing", True, ""

        classifications = req.apply(classify_input, axis=1, result_type="expand")
        classifications.columns = ["financial_input_status", "missing_input_flag", "matched_input_id"]
        req = pd.concat([req.reset_index(drop=True), classifications.reset_index(drop=True)], axis=1)

        # Build final inventory columns
        req["financial_driver"] = req["required_cost_input"]
        req["cost_unit"] = req["cost_unit"]
        req["required_period"] = "per intervention period"
        req["expected_input_owner"] = req["input_owner"]
        req["potential_source"] = req["potential_source"]
        req["actual_input_available"] = req["financial_input_status"].apply(lambda s: s != "Missing")
        req["stakeholder_validation_required"] = True
        req["governance_warning"] = req["financial_input_status"].apply(
            lambda s: "Missing input — value not available" if s == "Missing" else "Draft analytical assumption — requires validation"
        )

        keep_cols = [
            "financial_input_requirement_id", "approval_package_id", "management_scenario_package_id",
            "episode_id", "scenario_run_id", "scenario_family", "comparator_id", "intervention_type",
            "required_cost_input", "financial_driver", "cost_unit", "required_period",
            "one_time_or_recurring", "direct_or_indirect", "expected_input_owner", "potential_source",
            "actual_input_available", "financial_input_status", "missing_input_flag",
            "stakeholder_validation_required", "governance_warning", "matched_input_id",
        ]
        available = [c for c in keep_cols if c in req.columns]
        df = req[available].copy()
        self.log(f"Financial input inventory built: {len(df)} rows, {df['missing_input_flag'].sum()} missing.")
        return df
