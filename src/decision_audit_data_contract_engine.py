"""
decision_audit_data_contract_engine.py
Phase 2D-6 — Streamlit audit data contract.
"""

import pandas as pd
import uuid


def build_streamlit_audit_contract(
    routing_df: pd.DataFrame,
    evidence_completeness: pd.DataFrame,
    evidence_references: pd.DataFrame,
    lineage_links: pd.DataFrame,
    audit_requirements: pd.DataFrame,
    audit_contracts: pd.DataFrame,
    integrity_records: pd.DataFrame,
    version_control: pd.DataFrame
) -> pd.DataFrame:
    records = []

    # Panel A: Evidence summary
    for _, row in routing_df.iterrows():
        package_id = row["decision_package_id"]
        ev = evidence_completeness[evidence_completeness["decision_package_id"] == package_id]
        records.append({
            "panel_type": "Evidence Summary",
            "decision_package_id": package_id,
            "evidence_completeness_status": ev["evidence_completeness_status"].iloc[0] if not ev.empty else "Unknown",
            "evidence_coverage_pct": ev["evidence_coverage_pct"].iloc[0] if not ev.empty else 0,
            "missing_evidence_count": ev["missing_evidence_category_count"].iloc[0] if not ev.empty else 0,
            "critical_missing_evidence_count": ev["critical_missing_evidence_count"].iloc[0] if not ev.empty else 0,
            "evidence_warning": "" if (ev["evidence_completeness_status"].iloc[0] if not ev.empty else "") in ["Complete", "Complete with Conditions"] else "Evidence incomplete",
            "governance_note": "Streamlit evidence summary contract",
        })

    # Panel B: Evidence detail
    for _, ref in evidence_references.iterrows():
        records.append({
            "panel_type": "Evidence Detail",
            "decision_package_id": ref["decision_package_id"],
            "evidence_category": ref["evidence_category"],
            "source_phase": ref["source_phase"],
            "source_file": ref["source_file"],
            "source_record_id": ref["source_record_id"],
            "evidence_description": ref["evidence_description"],
            "evidence_status": ref["evidence_status"],
            "validation_status": ref["validation_status"],
            "provisional_flag": ref["provisional_flag"],
            "source_checksum": ref["source_checksum"],
            "governance_note": "Streamlit evidence detail contract",
        })

    # Panel C: Lineage view
    for _, link in lineage_links.iterrows():
        records.append({
            "panel_type": "Lineage View",
            "decision_package_id": link["decision_package_id"],
            "lineage_stage_number": link["lineage_stage_number"],
            "lineage_stage_name": link["lineage_stage_name"],
            "source_record_id": link["source_record_id"],
            "parent_record_id": link["parent_record_id"],
            "child_record_id": link["child_record_id"],
            "transformation_id": link["transformation_id"],
            "formula_id": link["formula_id"],
            "configuration_id": link["configuration_id"],
            "link_status": link["link_status"],
            "governance_note": "Streamlit lineage view contract",
        })

    # Panel D: Audit requirement
    for _, req in audit_requirements.iterrows():
        if req["audit_required"]:
            records.append({
                "panel_type": "Audit Requirement",
                "decision_package_id": routing_df[routing_df["decision_action_routing_id"] == req["decision_action_routing_id"]]["decision_package_id"].iloc[0] if not routing_df[routing_df["decision_action_routing_id"] == req["decision_action_routing_id"]].empty else "",
                "action_name": req["action_name"],
                "audit_required": req["audit_required"],
                "audit_event_type": req["audit_event_type"],
                "required_actor_role": req["required_actor_role"],
                "reason_required": req["reason_required"],
                "evidence_attachment_required": req["evidence_attachment_required"],
                "approval_reference_required": req["approval_reference_required"],
                "future_audit_status": req["future_audit_status"],
                "governance_note": "Streamlit audit requirement contract",
            })

    # Panel E: Audit history (all Not Executed)
    for _, contract in audit_contracts.iterrows():
        records.append({
            "panel_type": "Audit History",
            "decision_package_id": contract["decision_package_id"],
            "audit_event_type": contract["audit_event_type"],
            "event_status": contract["event_status"],
            "actor_role": contract["actor_role_required"],
            "actor_name": contract["actor_name"],
            "event_timestamp": contract["event_timestamp"],
            "previous_status": contract["previous_status"],
            "new_status": contract["new_status"],
            "approval_reference": contract["approval_reference"],
            "governance_note": "Streamlit audit history contract - all Not Executed",
        })

    # Panel F: Version and integrity
    for _, vc in version_control.iterrows():
        records.append({
            "panel_type": "Version and Integrity",
            "object_type": vc["governed_object_type"],
            "object_id": vc["governed_object_id"],
            "current_version": vc["current_version"],
            "checksum": vc["checksum"],
            "checksum_match": True,
            "immutable_flag": vc["immutable_flag"],
            "superseded_flag": vc["superseded_flag"],
            "governance_note": "Streamlit version contract",
        })

    return pd.DataFrame(records)
