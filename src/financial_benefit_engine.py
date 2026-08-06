"""
Financial Benefit Engine for Phase 2C-3.

Calculates benefit components and eligibility for avoided costs.
"""

import pandas as pd
from financial_base_engine import FinancialBaseEngine


class FinancialBenefitEngine(FinancialBaseEngine):
    def __init__(self):
        super().__init__()

    def calculate_benefit_eligibility(self, cost_summary: pd.DataFrame, runs: pd.DataFrame,
                                       comparator_validation: pd.DataFrame) -> pd.DataFrame:
        self.log("Calculating benefit eligibility...")
        if len(cost_summary) == 0:
            return pd.DataFrame()

        # Merge with comparator validation
        comp = comparator_validation[["approval_package_id", "validation_status"]].copy()
        comp = comp.rename(columns={"validation_status": "comparator_consistency"})
        df = cost_summary.merge(comp, on="approval_package_id", how="left")
        df["comparator_consistency"] = df["comparator_consistency"].fillna("Not Assessed")

        # Eligibility conditions
        def classify_eligibility(row):
            if row["comparator_consistency"] != "Consistent":
                return "Not Eligible", "Inconsistent comparators"
            if row["cost_completeness_status"] in ["Insufficient Financial Inputs", "Partial Cost Estimate"]:
                return "Not Eligible", "Incomplete cost data"
            if row["total_scenario_cost"] <= 0:
                return "Not Eligible", "Zero or negative cost"
            return "Eligible", "All conditions pass"

        elig = df.apply(classify_eligibility, axis=1, result_type="expand")
        elig.columns = ["benefit_eligibility", "benefit_eligibility_reason"]
        df = pd.concat([df, elig], axis=1)

        self.log(f"Benefit eligibility: {(df['benefit_eligibility']=='Eligible').sum()} eligible, {(df['benefit_eligibility']=='Not Eligible').sum()} not eligible.")
        return df

    def calculate_benefit_components(self, eligible_summary: pd.DataFrame, cost_components: pd.DataFrame,
                                      input_definitions: pd.DataFrame) -> pd.DataFrame:
        self.log("Calculating benefit components...")
        if len(eligible_summary) == 0 or len(cost_components) == 0:
            return pd.DataFrame()

        eligible_runs = set(eligible_summary[eligible_summary["benefit_eligibility"] == "Eligible"]["scenario_run_id"])
        comp = cost_components[cost_components["scenario_run_id"].isin(eligible_runs)].copy()
        if len(comp) == 0:
            return pd.DataFrame()

        # Define benefit mapping: cost component -> avoided cost component
        benefit_map = {
            "Additional Staff Cost": ("FIN-AVOID-TEMP-DAY", "Avoided Temporary Staff Cost"),
            "Temporary Staff Cost": ("FIN-AVOID-TEMP-DAY", "Avoided Temporary Staff Cost"),
            "Contingency Overtime Cost": ("FIN-AVOID-OT-HOUR", "Avoided Overtime Cost"),
            "Additional Shift Cost": ("FIN-AVOID-OT-HOUR", "Avoided Shift Cost"),
            "Capacity Adjustment Cost": ("FIN-QUEUE-REDUCT-VAL", "Queue Reduction Benefit"),
            "External Service Cost": ("FIN-QUEUE-REDUCT-VAL", "Service Improvement Benefit"),
        }

        def_map = input_definitions.set_index("financial_input_id").to_dict("index")

        records = []
        for _, row in comp.iterrows():
            cost_name = row["cost_component_name"]
            if cost_name not in benefit_map:
                continue

            benefit_input_id, benefit_name = benefit_map[cost_name]
            fdef = def_map.get(benefit_input_id, {})
            rate = fdef.get("default_value", None)

            if pd.isna(rate) or rate == "":
                benefit_value = None
                calc_status = "Missing Rate"
            else:
                # Estimate benefit as a fraction of cost (simplified model)
                cost = row["component_cost"] if pd.notna(row["component_cost"]) else 0
                benefit_value = cost * 0.3  # Assume 30% of cost is potentially avoidable
                calc_status = "Calculated"

            records.append({
                "scenario_run_id": row["scenario_run_id"],
                "approval_package_id": row["approval_package_id"],
                "scenario_family": row["scenario_family"],
                "comparator_type": row["comparator_type"],
                "benefit_component_id": f"BEN-{row['scenario_run_id']}-{benefit_name.replace(' ', '')}",
                "benefit_type": benefit_name,
                "calculation_eligibility": "Eligible",
                "source_scenario_effect": cost_name,
                "unit_cost": rate,
                "period": "per intervention period",
                "estimated_value": benefit_value,
                "uncertainty_band": "Low-High",
                "assumption_flag": True,
                "causality_warning": "Not Confirmed — analytical estimate only",
                "evidence": "",
                "lineage": "",
                "governance_warning": "Draft assumption — requires stakeholder validation",
                "calculation_status": calc_status,
            })

        df = pd.DataFrame(records)
        self.log(f"Benefit components: {len(df)} rows, {(df['calculation_status']=='Calculated').sum()} valid.")
        return df

    def calculate_benefit_summary(self, benefit_components: pd.DataFrame) -> pd.DataFrame:
        self.log("Calculating benefit summary...")
        if len(benefit_components) == 0:
            return pd.DataFrame()

        summary = benefit_components.groupby("scenario_run_id").agg({
            "approval_package_id": "first",
            "scenario_family": "first",
            "comparator_type": "first",
            "estimated_value": "sum",
            "calculation_status": lambda s: "Calculated" if (s == "Calculated").all() else "Partial",
        }).reset_index()

        summary = summary.rename(columns={"estimated_value": "total_estimated_benefit"})
        summary["benefit_completeness_status"] = summary["calculation_status"].apply(
            lambda s: "Complete" if s == "Calculated" else "Partial"
        )
        summary["currency"] = "MYR"
        summary["governance_warning"] = summary["calculation_status"].apply(
            lambda s: "Partial benefit estimate" if s == "Partial" else ""
        )

        self.log(f"Benefit summary: {len(summary)} runs.")
        return summary
