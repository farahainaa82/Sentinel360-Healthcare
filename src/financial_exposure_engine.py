"""
Financial Exposure Engine for Phase 2C-3.

Estimates do-nothing financial exposure where supported by operational evidence.
"""

import pandas as pd
from financial_base_engine import FinancialBaseEngine


class FinancialExposureEngine(FinancialBaseEngine):
    def __init__(self):
        super().__init__()

    def calculate_exposure(self, runs: pd.DataFrame, input_definitions: pd.DataFrame) -> pd.DataFrame:
        self.log("Calculating do-nothing financial exposure...")
        completed = runs[runs["scenario_execution_status"] == "Completed"].copy()
        if len(completed) == 0:
            return pd.DataFrame()

        # Baseline exposure: assume continued overtime pressure at baseline
        def_map = input_definitions.set_index("financial_input_id").to_dict("index")
        overtime_rate = def_map.get("FIN-OVERTIME-HOUR", {}).get("default_value", 25.0)
        temp_rate = def_map.get("FIN-TEMP-STAFF-DAY", {}).get("default_value", 120.0)

        records = []
        for _, run in completed.iterrows():
            # Estimate continued operational burden without intervention
            baseline_val = run.get("baseline_primary_kpi_value", 0)
            if pd.isna(baseline_val):
                baseline_val = 0

            # Exposure from continued overtime (simplified: 2 hrs/day for 30 days)
            exposure_overtime = 2.0 * 30.0 * float(overtime_rate)
            # Exposure from temporary coverage (simplified: 1 temp staff for 30 days)
            exposure_temp = 1.0 * 30.0 * float(temp_rate)
            total_exposure = exposure_overtime + exposure_temp

            records.append({
                "scenario_run_id": run["scenario_run_id"],
                "approval_package_id": run["approval_package_id"],
                "scenario_family": run["scenario_family"],
                "comparator_type": run["comparator_type"],
                "exposure_category": "Estimated Operational Financial Exposure",
                "exposure_description": "Continued overtime pressure and temporary coverage without intervention",
                "estimated_exposure_value": total_exposure,
                "currency": "MYR",
                "period": "per month",
                "assumption_flag": True,
                "governance_warning": "Analytical estimate only — not confirmed as definite cost",
                "evidence": "Baseline scenario operational interpretation",
                "lineage": "Derived from scenario runs",
            })

        df = pd.DataFrame(records)
        self.log(f"Exposure: {len(df)} records.")
        return df
