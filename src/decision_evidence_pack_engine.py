"""
decision_evidence_pack_engine.py
Phase 2D-6 — Export-ready evidence-pack contracts.
"""

import pandas as pd
import uuid


def build_evidence_pack_contracts(
    routing_df: pd.DataFrame,
    pack_config: pd.DataFrame
) -> pd.DataFrame:
    records = []
    for _, row in routing_df.iterrows():
        package_id = row["decision_package_id"]
        for _, cfg in pack_config.iterrows():
            records.append({
                "evidence_pack_id": f"EVK-{uuid.uuid4().hex[:8].upper()}",
                "decision_package_id": package_id,
                "evidence_pack_type": cfg["evidence_pack_type"],
                "included_section": cfg["included_section"],
                "section_order": cfg["section_order"],
                "source_register": f"step_2d6_{cfg['included_section'].lower().replace(' ', '_')}_register.csv",
                "source_record_count": 0,
                "export_eligible": cfg["export_eligible"],
                "missing_section_flag": False,
                "sensitive_section_flag": cfg["sensitive_section_flag"],
                "governance_warning": "Sensitive section" if cfg["sensitive_section_flag"] else "",
            })
    return pd.DataFrame(records)
