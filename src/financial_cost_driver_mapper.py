"""
Financial Cost Driver Mapper for Phase 2C-3.

Maps scenario assumptions to financial cost drivers using the
financial_cost_driver_mapping configuration.
"""

import pandas as pd
from financial_base_engine import FinancialBaseEngine


class FinancialCostDriverMapper(FinancialBaseEngine):
    def __init__(self):
        super().__init__()

    def build_cost_driver_mapping(self, runs: pd.DataFrame, mapping_config: pd.DataFrame,
                                   input_definitions: pd.DataFrame) -> pd.DataFrame:
        self.log("Building cost driver mapping...")
        if len(runs) == 0 or len(mapping_config) == 0:
            return pd.DataFrame()

        completed = runs[runs["scenario_execution_status"] == "Completed"].copy()
        if len(completed) == 0:
            return pd.DataFrame()

        # Parse assumption values JSON
        from financial_base_engine import parse_assumption_values_json
        completed["assumption_dict"] = completed["assumption_values_json"].apply(parse_assumption_values_json)

        # Derive family from assumption_set_id
        family_map = {
            "staffing-default": "Staffing Coverage Adjustment",
            "absenteeism-default": "Absenteeism Contingency",
            "patient-flow-default": "Patient-Flow and Waiting-Time Adjustment",
        }
        completed["derived_family"] = completed["assumption_set_id"].map(family_map).fillna(completed["scenario_family"])

        # Build def_map
        def_map = input_definitions.set_index("financial_input_id").to_dict("index")

        records = []
        for _, run in completed.iterrows():
            family = run["derived_family"]
            assumptions = run["assumption_dict"]

            # Find applicable mappings
            applicable = mapping_config[
                (mapping_config["scenario_family"] == family) |
                (mapping_config["scenario_family"] == "All")
            ].copy()

            for _, mmap in applicable.iterrows():
                assump_name = mmap["assumption_name"]
                assump_value = assumptions.get(assump_name, None)

                # Skip if assumption not present in this run
                if assump_value is None:
                    continue

                fin_input_id = mmap["financial_input_id"]
                fdef = def_map.get(fin_input_id, {})
                rate = fdef.get("default_value", None)
                rate_available = pd.notna(rate) and rate != ""

                records.append({
                    "scenario_run_id": run["scenario_run_id"],
                    "approval_package_id": run["approval_package_id"],
                    "scenario_family": family,
                    "comparator_type": run["comparator_type"],
                    "assumption_name": assump_name,
                    "assumption_value": assump_value,
                    "financial_input_id": fin_input_id,
                    "cost_component_name": mmap["cost_component_name"],
                    "formula_expression": mmap["formula_expression"],
                    "rate_value": rate if rate_available else None,
                    "rate_available": rate_available,
                    "unit": mmap["unit"],
                    "one_time_or_recurring": mmap["one_time_or_recurring"],
                    "direct_or_indirect": mmap["direct_or_indirect"],
                    "mapping_id": mmap["mapping_id"],
                })

        df = pd.DataFrame(records)
        self.log(f"Cost driver mapping built: {len(df)} rows for {df['scenario_run_id'].nunique()} runs.")
        return df
