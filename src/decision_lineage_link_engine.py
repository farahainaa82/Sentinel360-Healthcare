"""
decision_lineage_link_engine.py
Phase 2D-6 — Lineage link records per profile.
"""

import pandas as pd
import uuid


def build_lineage_links(
    lineage_profiles: pd.DataFrame,
    stage_config: pd.DataFrame
) -> pd.DataFrame:
    records = []
    for _, profile in lineage_profiles.iterrows():
        profile_id = profile["decision_lineage_profile_id"]
        package_id = profile["decision_package_id"]
        prev_id = ""

        for _, stage in stage_config.iterrows():
            stage_num = stage["stage_number"]
            stage_name = stage["stage_name"]
            source_phase = stage["source_phase"]

            link_id = f"LNL-{uuid.uuid4().hex[:8].upper()}"

            # Determine link status
            if stage_num <= 17:  # All stages up to action routing are complete for prototype
                status = "Complete"
            elif stage_num == 18:
                status = "Complete with Conditions"
            else:
                status = "Not Applicable"

            records.append({
                "lineage_link_id": link_id,
                "decision_lineage_profile_id": profile_id,
                "decision_package_id": package_id,
                "lineage_stage_number": stage_num,
                "lineage_stage_name": stage_name,
                "source_phase": source_phase,
                "source_file": f"step_{source_phase.lower().replace('-', '').replace(' ', '_')}_register.csv",
                "source_record_id": f"SRC-{package_id}-{stage_num}",
                "parent_record_id": prev_id,
                "child_record_id": link_id,
                "transformation_id": f"TXF-{stage_num}",
                "formula_id": f"FML-{stage_num}",
                "configuration_id": stage["configuration_id"],
                "version": "1.0",
                "source_checksum": "",
                "link_status": status,
                "orphan_flag": False,
                "ambiguity_flag": False,
                "governance_warning": "" if status in ["Complete", "Complete with Conditions"] else "Lineage stage may be incomplete",
            })
            prev_id = link_id

    return pd.DataFrame(records)
