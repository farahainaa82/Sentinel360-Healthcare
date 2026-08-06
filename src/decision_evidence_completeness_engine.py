"""
decision_evidence_completeness_engine.py
Phase 2D-6 — Evidence completeness assessment per package.
"""

import pandas as pd
import uuid


def assess_evidence_completeness(
    evidence_profiles: pd.DataFrame,
    evidence_references: pd.DataFrame,
    completeness_config: pd.DataFrame
) -> pd.DataFrame:
    records = []
    for _, profile in evidence_profiles.iterrows():
        profile_id = profile["decision_evidence_profile_id"]
        package_id = profile["decision_package_id"]

        refs = evidence_references[evidence_references["decision_evidence_profile_id"] == profile_id]
        total = len(refs)
        available = len(refs[refs["evidence_status"].isin(["Available", "Available with Conditions"])])
        conditional = len(refs[refs["evidence_status"] == "Available with Conditions"])
        missing = len(refs[refs["evidence_status"].isin(["Missing", "Missing Critical Evidence"])])
        critical_missing = len(refs[refs["evidence_status"] == "Missing Critical Evidence"])
        not_applicable = len(refs[refs["evidence_status"] == "Not Applicable"])

        effective_total = total - not_applicable
        coverage = (available / effective_total * 100) if effective_total > 0 else 0

        # Determine completeness status
        if coverage >= 90:
            status = "Complete"
        elif coverage >= 75:
            status = "Complete with Conditions"
        elif coverage >= 55:
            status = "Partial"
        elif coverage >= 40:
            status = "Limited"
        else:
            status = "Missing Critical Evidence"

        records.append({
            "evidence_completeness_id": f"EVC-{uuid.uuid4().hex[:8].upper()}",
            "decision_evidence_profile_id": profile_id,
            "decision_package_id": package_id,
            "expected_evidence_category_count": 28,
            "available_evidence_category_count": available,
            "conditional_evidence_category_count": conditional,
            "missing_evidence_category_count": missing,
            "critical_missing_evidence_count": critical_missing,
            "evidence_coverage_pct": round(coverage, 1),
            "evidence_completeness_status": status,
            "management_use_limitation": "None" if status in ["Complete", "Complete with Conditions"] else f"Limited by {missing} missing evidence categories",
            "governance_note": "Evidence completeness assessed from available references",
        })
    return pd.DataFrame(records)
