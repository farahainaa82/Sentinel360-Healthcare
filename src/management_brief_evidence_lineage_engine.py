"""Brief evidence and lineage cross-reference engine for Step 2D-7."""

import pandas as pd


def create_brief_evidence(briefs_df, evidence_profile_df=None):
    """Create brief-to-evidence cross-reference records."""
    records = []
    for _, row in briefs_df.iterrows():
        records.append({
            "integrated_management_brief_id": row.get("integrated_management_brief_id", ""),
            "decision_package_id": row.get("decision_package_id", ""),
            "decision_evidence_profile_id": row.get("decision_evidence_profile_id", ""),
            "evidence_completeness_status": row.get("evidence_completeness_status", ""),
            "evidence_coverage_pct": row.get("evidence_coverage_pct", ""),
            "critical_missing_evidence_count": row.get("critical_missing_evidence_count", "0"),
            "governance_note": "Brief evidence cross-reference"
        })
    return pd.DataFrame(records)


def create_brief_lineage(briefs_df, lineage_profile_df=None):
    """Create brief-to-lineage cross-reference records."""
    records = []
    for _, row in briefs_df.iterrows():
        records.append({
            "integrated_management_brief_id": row.get("integrated_management_brief_id", ""),
            "decision_package_id": row.get("decision_package_id", ""),
            "decision_lineage_profile_id": row.get("decision_lineage_profile_id", ""),
            "lineage_completeness_status": row.get("lineage_completeness_status", ""),
            "orphaned_lineage_flag": row.get("orphaned_lineage_flag", "False"),
            "governance_note": "Brief lineage cross-reference"
        })
    return pd.DataFrame(records)
