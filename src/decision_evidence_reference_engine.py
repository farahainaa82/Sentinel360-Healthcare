"""
decision_evidence_reference_engine.py
Phase 2D-6 — Evidence reference records per profile.
"""

import pandas as pd
import uuid


def build_evidence_references(
    evidence_profiles: pd.DataFrame,
    category_config: pd.DataFrame,
    routing_df: pd.DataFrame
) -> pd.DataFrame:
    records = []
    for _, profile in evidence_profiles.iterrows():
        package_id = profile["decision_package_id"]
        profile_id = profile["decision_evidence_profile_id"]
        readiness_status = profile["final_readiness_status"]

        for _, cat in category_config.iterrows():
            category = cat["evidence_category"]
            source_phase = cat["source_phase"]

            # Determine status based on category and readiness
            if category in ["Monitoring Evidence", "Action Eligibility Evidence", "Audit Evidence"]:
                status = "Available"
            elif category in ["Decision Integration Evidence", "Decision Package Evidence", "Readiness Evidence"]:
                status = "Available"
            elif category == "Financial Uncertainty Evidence" and "Financial" not in readiness_status and "Budget" not in readiness_status and "Benefit" not in readiness_status:
                status = "Not Applicable"
            elif category == "Scenario Validation Evidence" and "Scenario" not in readiness_status:
                status = "Not Applicable"
            elif category == "Monitoring Evidence" and readiness_status == "Monitoring Only":
                status = "Available"
            else:
                status = "Available with Conditions"

            records.append({
                "evidence_reference_id": f"EVR-{uuid.uuid4().hex[:8].upper()}",
                "decision_evidence_profile_id": profile_id,
                "decision_package_id": package_id,
                "evidence_category": category,
                "evidence_type": cat.get("evidence_category_description", ""),
                "source_phase": source_phase,
                "source_step": cat.get("source_step", ""),
                "source_file": f"step_{source_phase.lower().replace('-', '').replace(' ', '_')}_register.csv",
                "source_record_id": f"SRC-{package_id}",
                "source_field": "",
                "source_value_reference": "",
                "evidence_description": f"Evidence for {category} from {source_phase}",
                "evidence_status": status,
                "authority_status": "Verified",
                "validation_status": "Pending",
                "provisional_flag": status == "Available with Conditions",
                "contradiction_flag": False,
                "stakeholder_validation_required": False,
                "evidence_timestamp": "",
                "source_checksum": "",
                "current_version": "1.0",
                "superseded_flag": False,
                "governance_warning": "" if status != "Missing" else "Evidence missing for this category",
            })
    return pd.DataFrame(records)
