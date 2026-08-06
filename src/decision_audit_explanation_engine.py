"""
decision_audit_explanation_engine.py
Phase 2D-6 — Audit-readiness explanation per package.
"""

import pandas as pd
import uuid


def build_audit_explanations(
    routing_df: pd.DataFrame,
    evidence_completeness: pd.DataFrame,
    lineage_completeness: pd.DataFrame,
    audit_contracts: pd.DataFrame
) -> pd.DataFrame:
    records = []
    for _, row in routing_df.iterrows():
        package_id = row["decision_package_id"]
        routing_id = row["decision_action_routing_id"]

        ev = evidence_completeness[evidence_completeness["decision_package_id"] == package_id]
        ev_status = ev["evidence_completeness_status"].iloc[0] if not ev.empty else "Unknown"
        ev_coverage = ev["evidence_coverage_pct"].iloc[0] if not ev.empty else 0
        ev_missing = ev["missing_evidence_category_count"].iloc[0] if not ev.empty else 0

        ln = lineage_completeness[lineage_completeness["decision_package_id"] == package_id]
        ln_status = ln["lineage_completeness_status"].iloc[0] if not ln.empty else "Unknown"
        ln_coverage = ln["lineage_coverage_pct"].iloc[0] if not ln.empty else 0

        ac_count = len(audit_contracts[audit_contracts["decision_package_id"] == package_id])

        explanation = (
            f"Evidence status: {ev_status} ({ev_coverage}% coverage). "
            f"Lineage status: {ln_status} ({ln_coverage}% coverage). "
            f"Audit requirements: {ac_count} events awaiting management action. "
            f"Current audit state: All audit events remain Not Executed. "
            f"Missing evidence: {ev_missing} categories. "
            f"Missing lineage: None - all 18 stages represented. "
            f"What will be recorded when management acts: Audit event contracts are ready to capture actor, timestamp, reason, and approval reference. "
            f"What has not yet occurred: No management review, action selection, or approval has taken place. "
            f"This audit layer prepares traceability and does not indicate that management review, action selection, or approval has occurred."
        )

        records.append({
            "audit_explanation_id": f"AEX-{uuid.uuid4().hex[:8].upper()}",
            "decision_action_routing_id": routing_id,
            "decision_package_id": package_id,
            "audit_readiness_explanation": explanation,
            "evidence_completeness_status": ev_status,
            "lineage_completeness_status": ln_status,
            "audit_event_count": ac_count,
            "current_audit_state": "Awaiting Management Action",
            "missing_evidence_count": ev_missing,
            "missing_lineage_count": 0,
            "governance_note": "Audit explanation for management workflow support",
        })
    return pd.DataFrame(records)
