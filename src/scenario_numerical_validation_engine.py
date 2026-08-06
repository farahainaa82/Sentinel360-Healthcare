"""
Step 2C-2E Numerical Validation Engine.
Checks numerical reconciliation:
- scenario_value vs baseline + absolute_change
- percentage_change vs (scenario - baseline) / baseline * 100
Handles staffing family quirk where absolute_change = sum of additions.
"""

import pandas as pd
import numpy as np
from scenario_validation_base_engine import ValidationEngineBase


class NumericalValidationEngine(ValidationEngineBase):
    def __init__(self, **kwargs):
        super().__init__(engine_name="numerical_validation", **kwargs)

    def run(self) -> pd.DataFrame:
        runs = self.load_csv("analytical_scenario_runs.csv")
        kpi = self.load_csv("analytical_scenario_kpi_impacts.csv")

        merged = self.safe_merge(runs, kpi, on=["scenario_run_id"], how="left", suffixes=("", "_kpi"))

        results = []
        for _, row in merged.iterrows():
            sid = row["scenario_run_id"]
            pkg = row["approval_package_id"]
            family = str(row.get("scenario_family", "")).lower()
            baseline = row.get("baseline_primary_kpi_value", 0)
            scenario = row.get("scenario_primary_kpi_value", 0)
            abs_change = row.get("absolute_change", 0)
            pct_change = row.get("percentage_change", 0)

            validation_status = "Valid"
            validation_flags = []

            # Staffing family special case
            if "staff" in family:
                abs_reconciled = True
                abs_diff = np.nan
                pct_reconciled = True
                pct_diff = np.nan
                validation_flags.append("Staffing family: numerical reconciliation skipped (absolute_change = sum of additions, not scenario - baseline)")
                self.add_governance(sid, "VAL-006", "Numerical Reconciliation", True, "Skipped",
                                    "Staffing family special case")
            else:
                expected_scenario = baseline + abs_change
                abs_diff = abs(scenario - expected_scenario)
                abs_reconciled = abs_diff <= 0.01

                if baseline != 0:
                    expected_pct = ((scenario - baseline) / baseline) * 100
                    pct_diff = abs(pct_change - expected_pct)
                    pct_reconciled = pct_diff <= 0.1
                else:
                    expected_pct = np.nan
                    pct_diff = np.nan
                    pct_reconciled = True  # Cannot compute

                if not abs_reconciled:
                    validation_flags.append(f"Absolute reconciliation failed: |{scenario} - ({baseline}+{abs_change})| = {abs_diff:.4f}")
                    self.add_governance(sid, "VAL-006", "Numerical Reconciliation", True, "Failed",
                                        f"Diff = {abs_diff:.4f}")

                if not pct_reconciled:
                    validation_flags.append(f"Percentage reconciliation failed: |{pct_change}% - {expected_pct:.2f}%| = {pct_diff:.4f}")
                    self.add_governance(sid, "VAL-007", "Percentage Change Reconciliation", True, "Failed",
                                        f"Diff = {pct_diff:.4f}")

            if validation_status == "Valid" and validation_flags:
                validation_status = "Valid with Conditions"

            results.append({
                "scenario_run_id": sid,
                "approval_package_id": pkg,
                "episode_id": row.get("episode_id"),
                "scenario_template_id": row.get("scenario_template_id"),
                "scenario_family": row.get("scenario_family"),
                "baseline_value": baseline,
                "scenario_value": scenario,
                "absolute_change": abs_change,
                "percentage_change": pct_change,
                "abs_reconciled": abs_reconciled,
                "abs_difference": round(abs_diff, 6) if not pd.isna(abs_diff) else None,
                "pct_reconciled": pct_reconciled,
                "pct_difference": round(pct_diff, 6) if not pd.isna(pct_diff) else None,
                "validation_status": validation_status,
                "validation_flags": "; ".join(validation_flags) if validation_flags else "",
                "engine_name": self.engine_name,
                "engine_version": self.engine_version,
                "run_timestamp": self.run_timestamp,
            })

            self.add_lineage(sid, "kpi_impacts", sid, "analytical_scenario_kpi_impacts.csv")

        df = pd.DataFrame(results)
        self.write_output(df, "analytical_scenario_numerical_validation.csv")
        return df
