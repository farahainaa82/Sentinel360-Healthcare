"""
Financial Evidence and Lineage Engine for Phase 2C-3.

Creates evidence and lineage registers for financial calculations.
"""

import pandas as pd
from financial_base_engine import FinancialBaseEngine


class FinancialEvidenceLineageEngine(FinancialBaseEngine):
    def __init__(self):
        super().__init__()

    def build_evidence(self, cost_components: pd.DataFrame) -> pd.DataFrame:
        self.log("Building financial evidence register...")
        if len(cost_components) == 0:
            return pd.DataFrame()

        records = []
        for _, row in cost_components.iterrows():
            records.append({
                "evidence_id": f"EVID-FIN-{row['scenario_run_id']}-{row['cost_component_name'][:20]}",
                "scenario_run_id": row["scenario_run_id"],
                "approval_package_id": row["approval_package_id"],
                "evidence_type": "Financial Calculation",
                "evidence_description": f"{row['cost_component_name']} calculated using {row['formula_expression']}",
                "source_file": "financial_cost_driver_mapping.csv",
                "source_field": "formula_expression",
                "validation_status": row["calculation_status"],
                "assumption_flag": row["assumption_flag"],
                "governance_warning": row.get("missing_input_reason", ""),
            })

        df = pd.DataFrame(records)
        self.log(f"Evidence: {len(df)} records.")
        return df

    def build_lineage(self, cost_components: pd.DataFrame) -> pd.DataFrame:
        self.log("Building financial lineage register...")
        if len(cost_components) == 0:
            return pd.DataFrame()

        records = []
        for _, row in cost_components.iterrows():
            records.append({
                "lineage_id": f"LIN-FIN-{row['scenario_run_id']}-{row['cost_component_name'][:20]}",
                "scenario_run_id": row["scenario_run_id"],
                "approval_package_id": row["approval_package_id"],
                "upstream_phase": "2C-2C",
                "upstream_file": "analytical_scenario_runs.csv",
                "upstream_field": "assumption_values_json",
                "downstream_phase": "2C-3",
                "downstream_file": "step_2c3_scenario_cost_components.csv",
                "transformation": "Cost component calculation via financial_cost_driver_mapping",
                "governance_warning": "",
            })

        df = pd.DataFrame(records)
        self.log(f"Lineage: {len(df)} records.")
        return df
