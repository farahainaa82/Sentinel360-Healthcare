"""
Step 2C-2E Comparator Consistency Validation Engine.
Checks that Conservative/Expected/Higher Intensity comparators have
distinct assumptions and non-identical scenario values.
"""

import pandas as pd
import numpy as np
from scenario_validation_base_engine import ValidationEngineBase


class ComparatorValidationEngine(ValidationEngineBase):
    def __init__(self, **kwargs):
        super().__init__(engine_name="comparator_validation", **kwargs)

    def run(self) -> pd.DataFrame:
        runs = self.load_csv("analytical_scenario_runs.csv")
        comp = self.load_csv("analytical_scenario_comparator_analysis.csv")

        # Focus on comparable scenarios (exclude baseline-only, blocked, monitoring)
        comparable = runs[~runs["comparator_type"].isin(["Baseline"])].copy()

        # Group by approval_package_id and check distinctness
        pkg_groups = comparable.groupby("approval_package_id")

        results = []
        for pkg_id, group in pkg_groups:
            distinct_assumptions = group["assumption_values_json"].nunique()
            distinct_scenario_values = group["scenario_primary_kpi_value"].nunique()
            distinct_comparators = group["comparator_type"].nunique()

            status = "Consistent"
            flags = []

            if distinct_assumptions <= 1 and len(group) > 1:
                status = "Inconsistent"
                flags.append(f"All {len(group)} comparators have identical assumptions")
                self.add_governance(None, "VAL-008", "Comparator Assumption Distinctness", True, "Inconsistent",
                                    f"Package {pkg_id}: identical assumptions")

            if distinct_scenario_values <= 1 and len(group) > 1:
                status = "Inconsistent"
                flags.append(f"All {len(group)} comparators have identical scenario primary KPI values")
                self.add_governance(None, "VAL-009", "Comparator Value Spread", True, "Inconsistent",
                                    f"Package {pkg_id}: identical values")

            if status == "Consistent" and flags:
                status = "Consistent with Flags"

            results.append({
                "approval_package_id": pkg_id,
                "scenario_template_id": group["scenario_template_id"].iloc[0],
                "comparator_count": len(group),
                "distinct_comparator_types": distinct_comparators,
                "distinct_assumption_sets": distinct_assumptions,
                "distinct_scenario_values": distinct_scenario_values,
                "validation_status": status,
                "validation_flags": "; ".join(flags) if flags else "",
                "engine_name": self.engine_name,
                "engine_version": self.engine_version,
                "run_timestamp": self.run_timestamp,
            })

            self.add_lineage(None, "comparator_analysis", pkg_id, "analytical_scenario_comparator_analysis.csv")

        df = pd.DataFrame(results)
        self.write_output(df, "analytical_scenario_comparator_validation.csv")
        return df
