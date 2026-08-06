"""
Step 2C-2E Displacement Validation Engine.
Validates displacement risk classifications for evidence support,
classification validity, and management confirmation requirements.
"""

import pandas as pd
from scenario_validation_base_engine import ValidationEngineBase


class DisplacementValidationEngine(ValidationEngineBase):
    def __init__(self, **kwargs):
        super().__init__(engine_name="displacement_validation", **kwargs)

    def run(self) -> pd.DataFrame:
        displacement = self.load_csv("analytical_scenario_risk_displacement.csv")
        config = self.load_config("scenario_displacement_validation_config.csv")

        results = []
        for _, row in displacement.iterrows():
            did = row["displacement_id"]
            sid = row.get("scenario_run_id", "")
            pkg = row.get("approval_package_id", "")
            eid = row.get("episode_id", "")
            classification = str(row.get("displacement_classification", ""))
            evidence_basis = str(row.get("evidence_basis", ""))
            confidence = str(row.get("confidence", ""))
            mgmt_req = str(row.get("management_confirmation_required", "")).lower() == "true"
            monitoring = str(row.get("required_monitoring", ""))

            flags = []
            validation_status = "Supported"

            # Evidence presence check
            if not evidence_basis or evidence_basis.strip() == "":
                flags.append("Missing evidence basis")
                validation_status = "Weakly Supported"
                self.add_governance(sid, "DISP-001", "Displacement Evidence Presence", True, "Flagged",
                                    f"Displacement {did}: no evidence basis")

            # Classification allowlist check
            allowed_classes = ["Confirmed", "Suspected", "Ruled Out", "Monitoring Required"]
            if classification not in allowed_classes:
                flags.append(f"Unknown displacement classification: {classification}")
                if validation_status == "Supported":
                    validation_status = "Plausible with Conditions"
                self.add_governance(sid, "DISP-002", "Displacement Classification Allowlist", True, "Flagged",
                                    f"Unknown class: {classification}")

            # Management confirmation for high-confidence displacement
            if confidence in ("Moderate", "High") and not mgmt_req:
                flags.append("Moderate/High confidence displacement lacks management confirmation requirement")
                if validation_status == "Supported":
                    validation_status = "Plausible with Conditions"
                self.add_governance(sid, "DISP-003", "Management Confirmation Required", True, "Flagged",
                                    f"Confidence={confidence} but mgmt_req=False")

            # Required monitoring field
            if not monitoring or monitoring.strip() == "":
                flags.append("Missing required monitoring specification")
                if validation_status == "Supported":
                    validation_status = "Plausible with Conditions"
                self.add_governance(sid, "DISP-004", "Required Monitoring Field", True, "Flagged",
                                    "Monitoring field empty")

            results.append({
                "displacement_id": did,
                "scenario_run_id": sid,
                "approval_package_id": pkg,
                "episode_id": eid,
                "displacement_classification": classification,
                "evidence_basis_present": "Yes" if evidence_basis and evidence_basis.strip() != "" else "No",
                "confidence": confidence,
                "management_confirmation_required": mgmt_req,
                "required_monitoring_present": "Yes" if monitoring and monitoring.strip() != "" else "No",
                "validation_status": validation_status,
                "validation_flags": "; ".join(flags) if flags else "",
                "engine_name": self.engine_name,
                "engine_version": self.engine_version,
                "run_timestamp": self.run_timestamp,
            })

            self.add_lineage(sid, "displacement", did, "analytical_scenario_risk_displacement.csv")

        df = pd.DataFrame(results)
        self.write_output(df, "analytical_scenario_displacement_validation.csv")
        return df
