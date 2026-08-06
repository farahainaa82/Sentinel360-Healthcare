"""
decision_lineage_completeness_engine.py
Phase 2D-6 — Lineage completeness assessment per package.
"""

import pandas as pd
import uuid


def assess_lineage_completeness(
    lineage_profiles: pd.DataFrame,
    lineage_links: pd.DataFrame
) -> pd.DataFrame:
    records = []
    for _, profile in lineage_profiles.iterrows():
        profile_id = profile["decision_lineage_profile_id"]
        package_id = profile["decision_package_id"]

        links = lineage_links[lineage_links["decision_lineage_profile_id"] == profile_id]
        total = len(links)
        completed = len(links[links["link_status"].isin(["Complete", "Complete with Conditions"])])
        conditional = len(links[links["link_status"] == "Complete with Conditions"])
        missing = len(links[links["link_status"].isin(["Missing", "Incomplete"])])
        orphan = len(links[links["orphan_flag"] == True])
        not_applicable = len(links[links["link_status"] == "Not Applicable"])

        effective_total = total - not_applicable
        coverage = (completed / effective_total * 100) if effective_total > 0 else 0

        if coverage >= 90:
            status = "Complete"
        elif coverage >= 80:
            status = "Complete with Conditions"
        elif coverage >= 60:
            status = "Partial"
        elif coverage >= 35:
            status = "Incomplete"
        else:
            status = "Orphaned"

        records.append({
            "lineage_completeness_id": f"LNC-{uuid.uuid4().hex[:8].upper()}",
            "decision_lineage_profile_id": profile_id,
            "decision_package_id": package_id,
            "expected_stage_count": 18,
            "completed_stage_count": completed,
            "conditional_stage_count": conditional,
            "missing_stage_count": missing,
            "orphan_stage_count": orphan,
            "lineage_coverage_pct": round(coverage, 1),
            "lineage_completeness_status": status,
            "audit_traceability_status": "Traceable" if status in ["Complete", "Complete with Conditions", "Partial"] else "Limited Traceability",
            "governance_note": "Lineage completeness assessed from link records",
        })
    return pd.DataFrame(records)
