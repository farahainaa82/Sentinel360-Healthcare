"""
Step 2C-2E Dominance Validation Engine.
Validates dominance classifications. Downgrades dominance claims
when comparator values are identical (detected by comparator engine).
"""

import pandas as pd
from scenario_validation_base_engine import ValidationEngineBase


class DominanceValidationEngine(ValidationEngineBase):
    def __init__(self, **kwargs):
        super().__init__(engine_name="dominance_validation", **kwargs)

    def run(self, comparator_validation_df: pd.DataFrame = None) -> pd.DataFrame:
        dominance = self.load_csv("analytical_scenario_dominance.csv")
        if comparator_validation_df is not None:
            comp_val = comparator_validation_df
        else:
            comp_val = self.load_csv("analytical_scenario_comparator_validation.csv")

        # Merge to know if package had identical comparators
        merged = self.safe_merge(
            dominance,
            comp_val[["approval_package_id", "validation_status", "distinct_scenario_values"]],
            on=["approval_package_id"],
            how="left",
        )

        results = []
        for _, row in merged.iterrows():
            did = row["dominance_id"]
            pkg = row["approval_package_id"]
            orig_class = row["dominance_classification"]
            comp_status = row.get("validation_status", "")
            distinct_vals = row.get("distinct_scenario_values", 999)

            validated_class = orig_class
            flags = []

            if orig_class == "Dominant" and distinct_vals <= 1:
                validated_class = "Non-Dominated"
                flags.append("Downgraded: identical comparator values invalidate dominance claim")
                self.add_governance(None, "VAL-010", "Dominance Classification Plausibility", True, "Downgraded",
                                    f"Dominance {did} downgraded due to identical values")

            if orig_class not in ("Dominant", "Non-Dominated", "Incomparable"):
                flags.append(f"Unknown dominance classification: {orig_class}")
                self.add_governance(None, "DOM-002", "Dominance Classification Allowlist", True, "Flagged",
                                    f"Unknown class: {orig_class}")

            if pd.isna(row.get("dominance_rationale")) or str(row.get("dominance_rationale", "")).strip() == "":
                flags.append("Missing dominance rationale")
                self.add_governance(None, "DOM-004", "Dominance Rationale Presence", True, "Flagged",
                                    "Rationale is empty")

            results.append({
                "dominance_id": did,
                "approval_package_id": pkg,
                "scenario_template_id": row.get("scenario_template_id"),
                "scenario_run_id_a": row.get("scenario_run_id_a"),
                "scenario_run_id_b": row.get("scenario_run_id_b"),
                "original_classification": orig_class,
                "validated_classification": validated_class,
                "validation_status": "Downgraded" if validated_class != orig_class else "Valid",
                "validation_flags": "; ".join(flags) if flags else "",
                "engine_name": self.engine_name,
                "engine_version": self.engine_version,
                "run_timestamp": self.run_timestamp,
            })

            self.add_lineage(row.get("scenario_run_id_a"), "dominance", did, "analytical_scenario_dominance.csv")

        df = pd.DataFrame(results)
        self.write_output(df, "analytical_scenario_dominance_validation.csv")
        return df
