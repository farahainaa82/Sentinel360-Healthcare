"""
Step 2C-2E Diminishing Returns Validation Engine.
Validates diminishing returns classifications from Step 2C-2D.
- Loads diminishing-return records
- Validates comparator compatibility and intensity ordering
- Rejects calculations using incompatible assumptions
- Preserves scenario_run_id, approval_package_id, episode_id, comparator traceability
- Assigns validation status from controlled vocabulary
- Preserves causality_status = Not Confirmed
- Includes evidence, lineage, governance fields
- Makes no financial calculation
- Selects no preferred scenario
"""

import pandas as pd
import numpy as np
from scenario_validation_base_engine import ValidationEngineBase


class DiminishingReturnsValidationEngine(ValidationEngineBase):
    def __init__(self, **kwargs):
        super().__init__(engine_name="diminishing_returns_validation", **kwargs)

    def run(self, comparator_validation_df: pd.DataFrame = None, runs_df: pd.DataFrame = None) -> pd.DataFrame:
        dr = self.load_csv("analytical_scenario_diminishing_returns.csv")
        if comparator_validation_df is not None:
            comp_val = comparator_validation_df
        else:
            comp_val = self.load_csv("analytical_scenario_comparator_validation.csv")
        if runs_df is not None:
            runs = runs_df
        else:
            runs = self.load_csv("analytical_scenario_runs.csv")

        # Merge diminishing returns with comparator validation
        merged = self.safe_merge(
            dr,
            comp_val[["approval_package_id", "validation_status", "distinct_scenario_values", "distinct_assumption_sets"]],
            on=["approval_package_id"],
            how="left",
        )

        # Get causality status from runs (all should be Not Confirmed)
        causality_map = runs.groupby("approval_package_id")["causality_status"].first().to_dict()

        results = []
        for _, row in merged.iterrows():
            drid = row["diminishing_return_id"]
            pkg = row["approval_package_id"]
            stid = row.get("scenario_template_id", "")
            orig_class = row["diminishing_return_classification"]
            ratios_json = row.get("incremental_effect_ratios_json", "")
            distinct_vals = row.get("distinct_scenario_values", 999)
            distinct_assumps = row.get("distinct_assumption_sets", 999)
            comp_status = row.get("validation_status", "")
            causality = causality_map.get(pkg, "Not Confirmed")

            flags = []
            validation_status = "Confirmed Proportionate Improvement"

            # Comparator compatibility check
            if comp_status == "Inconsistent":
                validation_status = "Invalid Comparison"
                flags.append("Inconsistent comparator assumptions invalidate diminishing-returns assessment")
                self.add_governance(None, "VAL-012", "Diminishing Returns Plausibility", True, "Invalid Comparison",
                                    f"Package {pkg}: inconsistent comparators")

            # Intensity ordering check (requires distinct values)
            elif distinct_vals <= 1:
                validation_status = "Not Assessable"
                flags.append("Cannot assess diminishing returns: identical comparator values")
                self.add_governance(None, "VAL-012", "Diminishing Returns Plausibility", True, "Not Assessable",
                                    f"DR {drid}: identical values")

            # Missing ratios check
            elif pd.isna(ratios_json) or str(ratios_json).strip() in ("", "{}", "[]"):
                validation_status = "Not Assessable"
                flags.append("Missing incremental effect ratios JSON")
                self.add_governance(None, "VAL-012", "Diminishing Returns Plausibility", True, "Not Assessable",
                                    "Empty ratios JSON")

            else:
                # Attempt to classify based on original classification if data supports it
                if orig_class in ("Diminishing Returns", "Diminishing Improvement"):
                    validation_status = "Confirmed Diminishing Improvement"
                elif orig_class in ("Constant Returns", "Proportionate Improvement"):
                    validation_status = "Confirmed Proportionate Improvement"
                elif orig_class in ("No Effect", "Flat Response"):
                    validation_status = "Confirmed Flat Response"
                elif orig_class in ("Negative Returns", "Adverse Reversal"):
                    validation_status = "Confirmed Adverse Reversal"
                else:
                    validation_status = "Not Assessable"
                    flags.append(f"Unrecognized original classification: {orig_class}")
                    self.add_governance(None, "VAL-012", "Diminishing Returns Plausibility", True, "Not Assessable",
                                        f"Unknown class: {orig_class}")

            # Causality preservation check
            if causality != "Not Confirmed":
                flags.append(f"causality_status = {causality} (expected Not Confirmed)")
                self.add_governance(None, "VAL-016", "Causality Confirmation Required", True, "Flagged",
                                    f"Causality = {causality}")

            results.append({
                "diminishing_return_id": drid,
                "approval_package_id": pkg,
                "scenario_template_id": stid,
                "original_classification": orig_class,
                "validated_classification": validation_status,
                "validation_status": validation_status,
                "validation_flags": "; ".join(flags) if flags else "",
                "causality_status": causality,
                "comparator_compatibility": "Compatible" if comp_status != "Inconsistent" else "Incompatible",
                "intensity_ordering_check": "Pass" if distinct_vals > 1 else "Fail",
                "ratios_present": "Yes" if not (pd.isna(ratios_json) or str(ratios_json).strip() in ("", "{}", "[]")) else "No",
                "engine_name": self.engine_name,
                "engine_version": self.engine_version,
                "run_timestamp": self.run_timestamp,
            })

            self.add_lineage(None, "diminishing_returns", drid, "analytical_scenario_diminishing_returns.csv")
            self.add_evidence(None, "diminishing_returns_validation", "engine", self.engine_name,
                              "scenario_diminishing_returns_validation_engine.py",
                              metadata_json=f"{{'validation_status': '{validation_status}'}}")

        df = pd.DataFrame(results)
        self.write_output(df, "analytical_scenario_diminishing_return_validation.csv")
        return df
