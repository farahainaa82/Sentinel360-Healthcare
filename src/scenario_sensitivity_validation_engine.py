"""
Step 2C-2E Sensitivity Validation Engine.
Validates sensitivity classifications. Flags false stability when
comparators are identical.
"""

import pandas as pd
from scenario_validation_base_engine import ValidationEngineBase


class SensitivityValidationEngine(ValidationEngineBase):
    def __init__(self, **kwargs):
        super().__init__(engine_name="sensitivity_validation", **kwargs)

    def run(self, comparator_validation_df: pd.DataFrame = None) -> pd.DataFrame:
        sensitivity = self.load_csv("analytical_scenario_sensitivity.csv")
        if comparator_validation_df is not None:
            comp_val = comparator_validation_df
        else:
            comp_val = self.load_csv("analytical_scenario_comparator_validation.csv")

        merged = self.safe_merge(
            sensitivity,
            comp_val[["approval_package_id", "validation_status", "distinct_scenario_values"]],
            on=["approval_package_id"],
            how="left",
        )

        results = []
        for _, row in merged.iterrows():
            sid = row["sensitivity_id"]
            pkg = row["approval_package_id"]
            orig_class = row["sensitivity_classification"]
            distinct_vals = row.get("distinct_scenario_values", 999)
            direction_stable = row.get("direction_stable", False)

            validated_class = orig_class
            flags = []

            if distinct_vals <= 1 and orig_class == "Stable":
                validated_class = "Unstable"
                flags.append("Sensitivity flagged as unstable: identical comparator values provide no variation to assess stability")
                self.add_governance(None, "VAL-011", "Sensitivity Stability Check", True, "Flagged",
                                    f"Sensitivity {sid}: identical values -> unstable")

            if orig_class not in ("Stable", "Unstable", "Highly Sensitive", "Non-Comparable"):
                flags.append(f"Unknown sensitivity classification: {orig_class}")
                self.add_governance(None, "SENS-006", "Sensitivity Classification Allowlist", True, "Flagged",
                                    f"Unknown class: {orig_class}")

            if not direction_stable and orig_class == "Stable":
                flags.append("Direction not stable but classification is Stable")
                self.add_governance(None, "SENS-001", "Direction Stability Check", True, "Flagged",
                                    "direction_stable=False but class=Stable")

            results.append({
                "sensitivity_id": sid,
                "approval_package_id": pkg,
                "scenario_template_id": row.get("scenario_template_id"),
                "original_classification": orig_class,
                "validated_classification": validated_class,
                "validation_status": "Flagged" if flags else "Valid",
                "validation_flags": "; ".join(flags) if flags else "",
                "engine_name": self.engine_name,
                "engine_version": self.engine_version,
                "run_timestamp": self.run_timestamp,
            })

            self.add_lineage(None, "sensitivity", sid, "analytical_scenario_sensitivity.csv")

        df = pd.DataFrame(results)
        self.write_output(df, "analytical_scenario_sensitivity_validation.csv")
        return df
