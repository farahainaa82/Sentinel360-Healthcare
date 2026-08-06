"""
Step 2C-2E Validation Governance Validator.
Validates governance compliance including:
- No High confidence without confirmed causality
- Causality status preservation
- Contradiction severity handling
- Confidence ceiling enforcement
"""

import pandas as pd
from scenario_validation_base_engine import ValidationEngineBase


class ValidationGovernanceValidator(ValidationEngineBase):
    def __init__(self, **kwargs):
        super().__init__(engine_name="governance_validator", **kwargs)

    def run(self) -> pd.DataFrame:
        runs = self.load_csv("analytical_scenario_runs.csv")
        confidence = self.load_csv("analytical_scenario_confidence.csv")

        # Merge runs with confidence on scenario_run_id
        merged = self.safe_merge(
            runs,
            confidence,
            on=["scenario_run_id"],
            how="left",
            suffixes=("", "_conf"),
        )

        results = []
        for _, row in merged.iterrows():
            sid = row["scenario_run_id"]
            pkg = row["approval_package_id"]
            final_conf = str(row.get("final_scenario_confidence", ""))
            causality = str(row.get("causality_status", ""))
            contradiction = str(row.get("contradiction_severity", ""))

            flags = []
            governance_status = "Compliant"

            # Rule: No High confidence without confirmed causality
            if final_conf == "High" and causality != "Confirmed":
                flags.append("High confidence without confirmed causality")
                governance_status = "Non-Compliant"
                self.add_governance(sid, "VAL-015", "Confidence Ceiling", True, "Flagged",
                                    f"Confidence=High but causality={causality}")

            # Rule: Causality must be documented
            if causality == "Not Confirmed":
                flags.append("Causality not confirmed")
                self.add_governance(sid, "VAL-016", "Causality Confirmation Required", True, "Flagged",
                                    "causality_status = Not Confirmed")

            # Rule: Contradiction severity handling
            if contradiction == "High":
                flags.append("High contradiction severity requires management review")
                self.add_governance(sid, "VAL-017", "Contradiction Severity Check", True, "Flagged",
                                    "contradiction_severity = High")

            # Rule: Provisional warning tracking
            provisional = str(row.get("provisional_warning", ""))
            if provisional and provisional.strip() != "" and provisional.lower() != "false":
                flags.append(f"Provisional warning present: {provisional}")
                self.add_governance(sid, "VAL-018", "Provisional Warning Flag", True, "Flagged",
                                    f"Provisional warning: {provisional}")

            if governance_status == "Compliant" and flags:
                governance_status = "Compliant with Flags"

            results.append({
                "scenario_run_id": sid,
                "approval_package_id": pkg,
                "episode_id": row.get("episode_id", ""),
                "final_scenario_confidence": final_conf,
                "causality_status": causality,
                "contradiction_severity": contradiction,
                "provisional_warning": provisional,
                "governance_status": governance_status,
                "governance_flags": "; ".join(flags) if flags else "",
                "engine_name": self.engine_name,
                "engine_version": self.engine_version,
                "run_timestamp": self.run_timestamp,
            })

            self.add_lineage(sid, "governance", sid, "analytical_scenario_governance.csv")

        df = pd.DataFrame(results)
        self.write_output(df, "analytical_scenario_validation_governance.csv")
        return df
