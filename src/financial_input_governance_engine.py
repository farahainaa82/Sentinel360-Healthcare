"""
Financial Input Governance Engine for Phase 2C-3.

Creates the financial input governance register with source, owner,
currency, confidence, and validation status for each input.
"""

import pandas as pd
from financial_base_engine import FinancialBaseEngine


class FinancialInputGovernanceEngine(FinancialBaseEngine):
    def __init__(self):
        super().__init__()

    def build_governance_register(self, inventory: pd.DataFrame, input_definitions: pd.DataFrame) -> pd.DataFrame:
        self.log("Building financial input governance register...")
        if len(inventory) == 0:
            return pd.DataFrame()

        def_map = input_definitions.set_index("financial_input_id").to_dict("index")

        records = []
        for _, row in inventory.iterrows():
            matched_id = row.get("matched_input_id", "")
            fdef = def_map.get(matched_id, {}) if matched_id else {}

            status = row["financial_input_status"]
            confidence = "Low"
            if status == "Actual Observed":
                confidence = "Moderate"
            elif status == "Missing":
                confidence = "Very Low"

            records.append({
                "financial_input_requirement_id": row["financial_input_requirement_id"],
                "approval_package_id": row["approval_package_id"],
                "scenario_family": row["scenario_family"],
                "financial_input_id": matched_id,
                "financial_input_name": row["required_cost_input"],
                "input_source": fdef.get("source_reference", "Draft Analytical Assumption"),
                "source_date": "2026-07-29",
                "source_owner": row.get("expected_input_owner", ""),
                "currency": "MYR",
                "unit": row.get("cost_unit", ""),
                "effective_period": row.get("required_period", ""),
                "confidence": confidence,
                "validation_status": "Pending" if status == "Missing" else "Draft Assumption",
                "assumption_flag": status in ["Governed Analytical Assumption", "Derived from Governed Inputs"],
                "provisional_flag": True,
                "evidence_reference": "",
                "lineage_reference": "",
                "governance_warning": row.get("governance_warning", ""),
            })

        df = pd.DataFrame(records)
        self.log(f"Governance register built: {len(df)} rows.")
        return df
