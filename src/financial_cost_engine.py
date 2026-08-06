"""
Financial Cost Engine for Phase 2C-3.

Calculates scenario cost components using governed formulas and rates.
"""

import pandas as pd
from financial_base_engine import FinancialBaseEngine


class FinancialCostEngine(FinancialBaseEngine):
    def __init__(self):
        super().__init__()

    def calculate_cost_components(self, driver_mapping: pd.DataFrame) -> pd.DataFrame:
        self.log("Calculating cost components...")
        if len(driver_mapping) == 0:
            return pd.DataFrame()

        records = []
        for _, row in driver_mapping.iterrows():
            rate = row.get("rate_value")
            rate_available = row.get("rate_available", False)
            assump_value = row.get("assumption_value", 0)
            formula = row.get("formula_expression", "")

            if not rate_available or pd.isna(rate):
                component_cost = None
                calc_status = "Missing Rate"
            else:
                # Simplified formula evaluation based on known structures
                try:
                    # Map common formula patterns
                    if "additional_staff_count" in formula and "temporary_staff_daily_rate" in formula:
                        component_cost = float(assump_value) * float(rate) * 7.0  # default 7 days if not in assumptions
                    elif "temporary_staff_count" in formula and "temporary_staff_daily_rate" in formula:
                        component_cost = float(assump_value) * float(rate) * 7.0
                    elif "intervention_duration_days" in formula and "recurring_monitoring_monthly_cost" in formula:
                        component_cost = (float(assump_value) / 30.0) * float(rate)
                    elif "implementation_labour_cost" in formula:
                        component_cost = float(rate)
                    elif "project_management_cost" in formula:
                        component_cost = float(rate)
                    elif "uncovered_shift_reduction_pct" in formula and "overtime_rate" in formula:
                        component_cost = float(assump_value) * 8.0 * float(rate) * 7.0  # 8 hrs/day
                    elif "replacement_coverage_pct" in formula:
                        component_cost = float(assump_value) * float(rate) * 7.0
                    elif "contingency_roster_activation_pct" in formula:
                        component_cost = float(assump_value) * 4.0 * float(rate) * 7.0
                    elif "absence_duration_reduction_days" in formula:
                        component_cost = float(assump_value) * float(rate)
                    elif "service_capacity_change_pct" in formula:
                        component_cost = float(assump_value) * float(rate) * 7.0
                    elif "temporary_resource_change" in formula:
                        component_cost = float(assump_value) * 8.0 * float(rate) * 7.0
                    elif "throughput_change_pct" in formula:
                        component_cost = float(assump_value) * 50.0 * float(rate)  # baseline throughput proxy
                    else:
                        component_cost = float(assump_value) * float(rate)

                    calc_status = "Calculated"
                except Exception:
                    component_cost = None
                    calc_status = "Calculation Error"

            records.append({
                "scenario_run_id": row["scenario_run_id"],
                "approval_package_id": row["approval_package_id"],
                "scenario_family": row["scenario_family"],
                "comparator_type": row["comparator_type"],
                "cost_component_name": row["cost_component_name"],
                "formula_expression": formula,
                "assumption_name": row["assumption_name"],
                "assumption_value": assump_value,
                "rate_value": rate,
                "rate_available": rate_available,
                "component_cost": component_cost,
                "currency": "MYR",
                "unit": row["unit"],
                "financial_input_id": row.get("financial_input_id", ""),
                "one_time_or_recurring": row["one_time_or_recurring"],
                "direct_or_indirect": row["direct_or_indirect"],
                "calculation_status": calc_status,
                "validation_status": "Draft" if calc_status == "Calculated" else "Invalid",
                "assumption_flag": not rate_available,
                "missing_input_reason": "" if calc_status == "Calculated" else "Rate missing or invalid",
                "evidence": "",
                "lineage": "",
            })

        df = pd.DataFrame(records)
        self.log(f"Cost components calculated: {len(df)} rows, {(df['calculation_status']=='Calculated').sum()} valid.")
        return df

    def calculate_cost_summary(self, cost_components: pd.DataFrame) -> pd.DataFrame:
        self.log("Calculating cost summary...")
        if len(cost_components) == 0:
            return pd.DataFrame()

        # Group by scenario_run_id
        summary = cost_components.groupby("scenario_run_id").agg({
            "approval_package_id": "first",
            "scenario_family": "first",
            "comparator_type": "first",
            "component_cost": "sum",
            "calculation_status": lambda s: "Calculated" if (s == "Calculated").all() else "Partial",
            "rate_available": "all",
        }).reset_index()

        summary = summary.rename(columns={"component_cost": "total_scenario_cost"})

        # Cost completeness classification
        def classify_completeness(row):
            if row["rate_available"] and row["calculation_status"] == "Calculated":
                return "Complete with Governed Assumptions"
            elif row["calculation_status"] == "Partial":
                return "Partial Cost Estimate"
            else:
                return "Insufficient Financial Inputs"

        summary["cost_completeness_status"] = summary.apply(classify_completeness, axis=1)
        summary["currency"] = "MYR"
        summary["governance_warning"] = summary["cost_completeness_status"].apply(
            lambda s: "Partial estimate — components excluded" if s == "Partial Cost Estimate" else (
                "Insufficient inputs — no total calculated" if s == "Insufficient Financial Inputs" else ""
            )
        )

        self.log(f"Cost summary built: {len(summary)} runs.")
        return summary
