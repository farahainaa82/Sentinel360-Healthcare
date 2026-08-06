"""
Step 2C-2E Assumption Challenge Engine.
Challenges assumptions by checking validation status, hard/soft limits,
and orphan validation records.
Handles the orphan assumption_validation table (no scenario_run_id).
"""

import pandas as pd
from scenario_validation_base_engine import ValidationEngineBase


class AssumptionChallengeEngine(ValidationEngineBase):
    def __init__(self, **kwargs):
        super().__init__(engine_name="assumption_challenge", **kwargs)

    def run(self) -> pd.DataFrame:
        runs = self.load_csv("analytical_scenario_runs.csv")
        assumptions = self.load_csv("analytical_scenario_assumption_validation.csv")
        config = self.load_config("scenario_assumption_plausibility_config.csv")
        rules = self.load_config("scenario_validation_rule_config.csv")

        # Build assumption summary per assumption_set_id (from runs)
        # Since assumption_validation has no join key, we do a global check
        # and then merge by assumption_set_id if it exists in both
        # assumption_validation has assumption_id; runs has assumption_set_id
        # There is no bridge. We will flag this as a schema limitation.

        hard_violations = int((assumptions["hard_limit_violated"] == True).sum())
        soft_violations = int((assumptions["soft_limit_violated"] == True).sum())
        total_assumptions = len(assumptions)
        soft_rate = soft_violations / total_assumptions if total_assumptions > 0 else 0.0

        # Per-scenario challenge results
        results = []
        for _, row in runs.iterrows():
            sid = row["scenario_run_id"]
            pkg = row["approval_package_id"]
            astatus = row.get("assumption_validation_status", "")
            awarn = row.get("assumption_warning_count", 0)

            challenge_status = "Passed"
            challenge_flags = []

            if hard_violations > 0:
                challenge_status = "Failed"
                challenge_flags.append("Hard limit violations exist in global assumption pool")
                self.add_governance(sid, "VAL-002", "Hard Limit Violation", True, "Failed",
                                    f"{hard_violations} hard limit violations detected globally")

            if soft_rate > 0.2:
                challenge_flags.append(f"Soft limit violation rate {soft_rate:.2%} exceeds 20% threshold")
                self.add_governance(sid, "VAL-001", "Assumption Validation Presence", True, "Flagged",
                                    f"Soft violation rate {soft_rate:.2%}")

            if astatus not in ("Valid", "Validated", "Adjusted", "Accepted with Warning"):
                challenge_flags.append(f"Assumption validation status = {astatus}")
                self.add_governance(sid, "VAL-001", "Assumption Validation Presence", True, "Flagged",
                                    f"Status = {astatus}")

            if awarn > 0:
                challenge_flags.append(f"Assumption warnings = {awarn}")

            # Schema limitation flag
            challenge_flags.append("Schema limitation: assumption_validation table has no scenario_run_id or approval_package_id join key")
            self.add_issue(sid, pkg, "Schema Limitation", "Warning",
                           "assumption_validation.csv lacks join keys to scenario_runs",
                           "Create bridge table or validate assumptions globally")

            if challenge_status == "Passed" and challenge_flags:
                challenge_status = "Passed with Flags"

            results.append({
                "scenario_run_id": sid,
                "approval_package_id": pkg,
                "episode_id": row.get("episode_id"),
                "scenario_template_id": row.get("scenario_template_id"),
                "assumption_set_id": row.get("assumption_set_id"),
                "assumption_validation_status": astatus,
                "assumption_warning_count": awarn,
                "global_hard_limit_violations": hard_violations,
                "global_soft_limit_violations": soft_violations,
                "global_soft_violation_rate": round(soft_rate, 4),
                "challenge_status": challenge_status,
                "challenge_flags": "; ".join(challenge_flags) if challenge_flags else "",
                "engine_name": self.engine_name,
                "engine_version": self.engine_version,
                "run_timestamp": self.run_timestamp,
            })

            self.add_lineage(sid, "assumption_validation", row.get("assumption_set_id", ""),
                             "analytical_scenario_assumption_validation.csv")
            self.add_evidence(sid, "assumption_challenge", "engine", self.engine_name,
                              "scenario_assumption_challenge_engine.py",
                              metadata_json=f"{{'hard_violations': {hard_violations}}}")

        df = pd.DataFrame(results)
        self.write_output(df, "analytical_scenario_assumption_challenge.csv")
        return df
