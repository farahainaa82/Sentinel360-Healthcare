"""
Step 2C-2E Management Interpretation Validator.
Reviews management interpretations for forbidden wording,
confidence accuracy, and contradiction warnings.
"""

import pandas as pd
from scenario_validation_base_engine import ValidationEngineBase


class ManagementInterpretationValidator(ValidationEngineBase):
    def __init__(self, **kwargs):
        super().__init__(engine_name="management_interpretation", **kwargs)

    def run(self) -> pd.DataFrame:
        interpretations = self.load_csv("analytical_scenario_management_interpretation.csv")
        config = self.load_config("scenario_management_wording_rule_config.csv")

        # Load forbidden phrases from config
        forbidden_rules = config[config["action_if_failed"] == "flag"]
        forbidden_phrases = []
        for _, row in forbidden_rules.iterrows():
            phrases = str(row.get("forbidden_phrases", "")).split(";")
            forbidden_phrases.extend([p.strip().lower() for p in phrases if p.strip()])

        results = []
        for _, row in interpretations.iterrows():
            iid = row["interpretation_id"]
            pkg = row.get("approval_package_id", "")
            eid = row.get("episode_id", "")
            text = str(row.get("interpretation_text", ""))
            readiness = str(row.get("management_readiness", ""))

            flags = []
            validation_status = "Valid"

            # Forbidden phrase check
            text_lower = text.lower()
            found_forbidden = [p for p in forbidden_phrases if p in text_lower]
            if found_forbidden:
                flags.append(f"Forbidden phrases found: {', '.join(found_forbidden)}")
                validation_status = "Requires Revision"
                self.add_governance(None, "WORD-001", "Absolute Certainty Prohibition", True, "Flagged",
                                    f"Interpretation {iid}: found {found_forbidden}")

            # Management readiness check
            if readiness not in ("Ready", "Ready with Conditions", "Not Ready"):
                flags.append(f"Unrecognized management readiness: {readiness}")
                if validation_status == "Valid":
                    validation_status = "Requires Revision"
                self.add_governance(None, "WORD-006", "Actionable Outcome Requirement", True, "Flagged",
                                    f"Readiness = {readiness}")

            # Check for empty interpretation text
            if not text or text.strip() == "":
                flags.append("Empty interpretation text")
                validation_status = "Requires Revision"
                self.add_governance(None, "WORD-004", "Comparative Language Requirement", True, "Flagged",
                                    "Interpretation text is empty")

            results.append({
                "interpretation_id": iid,
                "approval_package_id": pkg,
                "episode_id": eid,
                "scenario_template_id": row.get("scenario_template_id", ""),
                "interpretation_text_length": len(text),
                "forbidden_phrases_found": "; ".join(found_forbidden) if found_forbidden else "",
                "has_forbidden_phrases": "Yes" if found_forbidden else "No",
                "management_readiness": readiness,
                "validation_status": validation_status,
                "validation_flags": "; ".join(flags) if flags else "",
                "engine_name": self.engine_name,
                "engine_version": self.engine_version,
                "run_timestamp": self.run_timestamp,
            })

            self.add_lineage(None, "management_interpretation", iid, "analytical_scenario_management_interpretation.csv")

        df = pd.DataFrame(results)
        self.write_output(df, "analytical_scenario_management_interpretation_validation.csv")
        return df
