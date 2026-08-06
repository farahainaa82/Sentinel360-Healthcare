"""
Step 2C-2E Baseline Validation Engine.
Validates baselines against status, completeness, observation count,
and confidence thresholds.
"""

import pandas as pd
from scenario_validation_base_engine import ValidationEngineBase


class BaselineValidationEngine(ValidationEngineBase):
    def __init__(self, **kwargs):
        super().__init__(engine_name="baseline_validation", **kwargs)

    def run(self) -> pd.DataFrame:
        runs = self.load_csv("analytical_scenario_runs.csv")
        baselines = self.load_csv("analytical_scenario_baselines.csv")
        config = self.load_config("scenario_baseline_validity_config.csv")

        # Merge runs with baselines on approval_package_id (governed join)
        merged = self.safe_merge(
            runs,
            baselines,
            on=["approval_package_id"],
            how="left",
            suffixes=("", "_base"),
        )

        results = []
        for _, row in merged.iterrows():
            sid = row["scenario_run_id"]
            pkg = row["approval_package_id"]
            baseline_status = row.get("baseline_status_base", row.get("baseline_status", ""))
            completeness = row.get("baseline_data_completeness_base", row.get("baseline_data_completeness", 0))
            obs_count = row.get("baseline_observation_count", 0)
            baseline_conf = row.get("baseline_confidence", "")

            validation_status = "Valid"
            validation_flags = []

            if baseline_status not in ("Available", "Available with Conditions"):
                validation_status = "Invalid"
                validation_flags.append(f"Baseline status = {baseline_status}")
                self.add_governance(sid, "VAL-003", "Baseline Status Available", True, "Invalid",
                                    f"Status = {baseline_status}")

            if pd.isna(completeness) or completeness < 0.5:
                validation_flags.append(f"Baseline completeness = {completeness}")
                self.add_governance(sid, "VAL-004", "Baseline Data Completeness Threshold", True, "Flagged",
                                    f"Completeness = {completeness}")

            if pd.isna(obs_count) or obs_count < 1:
                validation_flags.append(f"Baseline observation count = {obs_count}")
                self.add_governance(sid, "VAL-005", "Baseline Observation Count", True, "Flagged",
                                    f"Observations = {obs_count}")

            if baseline_conf == "Insufficient Evidence":
                validation_flags.append("Baseline confidence = Insufficient Evidence")
                self.add_governance(sid, "BASE-004", "Baseline Confidence Minimum", True, "Flagged",
                                    "Confidence = Insufficient Evidence")

            if validation_status == "Valid" and validation_flags:
                validation_status = "Valid with Conditions"

            results.append({
                "scenario_run_id": sid,
                "approval_package_id": pkg,
                "episode_id": row.get("episode_id"),
                "scenario_template_id": row.get("scenario_template_id"),
                "baseline_id": row.get("baseline_id"),
                "baseline_status": baseline_status,
                "baseline_data_completeness": completeness,
                "baseline_observation_count": obs_count,
                "baseline_confidence": baseline_conf,
                "validation_status": validation_status,
                "validation_flags": "; ".join(validation_flags) if validation_flags else "",
                "engine_name": self.engine_name,
                "engine_version": self.engine_version,
                "run_timestamp": self.run_timestamp,
            })

            self.add_lineage(sid, "baseline", row.get("baseline_id", ""), "analytical_scenario_baselines.csv")

        df = pd.DataFrame(results)
        self.write_output(df, "analytical_scenario_baseline_validation.csv")
        return df
