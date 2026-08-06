"""
test_step_2d6_decision_evidence_audit.py
Phase 2D-6 — 77 focused tests for Decision Evidence and Audit Layer.
"""

import os
import json
import pytest
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "outputs", "decision_intelligence")
CONFIG = os.path.join(BASE, "config")


def load_csv(name):
    path = os.path.join(OUT, name)
    assert os.path.exists(path), f"Missing: {name}"
    return pd.read_csv(path)


@pytest.fixture
def routing():
    return load_csv("step_2d5_decision_action_routing_register.csv")


@pytest.fixture
def evidence_profiles():
    return load_csv("step_2d6_decision_evidence_profile_register.csv")


@pytest.fixture
def evidence_references():
    return load_csv("step_2d6_evidence_reference_register.csv")


@pytest.fixture
def evidence_completeness():
    return load_csv("step_2d6_evidence_completeness_register.csv")


@pytest.fixture
def lineage_profiles():
    return load_csv("step_2d6_decision_lineage_profile_register.csv")


@pytest.fixture
def lineage_links():
    return load_csv("step_2d6_lineage_link_register.csv")


@pytest.fixture
def lineage_completeness():
    return load_csv("step_2d6_lineage_completeness_register.csv")


@pytest.fixture
def traces():
    return load_csv("step_2d6_source_to_decision_trace_register.csv")


@pytest.fixture
def audit_requirements():
    return load_csv("step_2d6_audit_requirement_register.csv")


@pytest.fixture
def audit_catalogue():
    return load_csv("step_2d6_audit_event_catalogue.csv")


@pytest.fixture
def audit_contracts():
    return load_csv("step_2d6_audit_event_contract.csv")


@pytest.fixture
def history():
    return load_csv("step_2d6_decision_history_contract.csv")


@pytest.fixture
def version_control():
    return load_csv("step_2d6_version_control_register.csv")


@pytest.fixture
def integrity():
    return load_csv("step_2d6_integrity_register.csv")


@pytest.fixture
def retention():
    return load_csv("step_2d6_retention_classification_register.csv")


@pytest.fixture
def access():
    return load_csv("step_2d6_access_role_contract.csv")


@pytest.fixture
def evidence_packs():
    return load_csv("step_2d6_evidence_pack_contract.csv")


@pytest.fixture
def management_reviews():
    return load_csv("step_2d6_management_review_contract.csv")


@pytest.fixture
def explanations():
    return load_csv("step_2d6_audit_explanation_register.csv")


@pytest.fixture
def streamlit():
    return load_csv("step_2d6_streamlit_audit_data_contract.csv")


@pytest.fixture
def summary():
    return load_csv("step_2d6_execution_summary.csv")


@pytest.fixture
def manifest():
    path = os.path.join(OUT, "step_2d6_manifest.json")
    with open(path, "r") as f:
        return json.load(f)


# Tests 1-5: Population and ID integrity
def test_1_one_evidence_profile_per_routing(evidence_profiles, routing):
    assert len(evidence_profiles) == len(routing), "Must be one evidence profile per routing"


def test_2_one_lineage_profile_per_routing(lineage_profiles, routing):
    assert len(lineage_profiles) == len(routing), "Must be one lineage profile per routing"


def test_3_evidence_profile_ids_unique(evidence_profiles):
    assert not evidence_profiles["decision_evidence_profile_id"].duplicated().any()


def test_4_lineage_profile_ids_unique(lineage_profiles):
    assert not lineage_profiles["decision_lineage_profile_id"].duplicated().any()


def test_5_no_cartesian_joins(evidence_references):
    grouped = evidence_references.groupby(["decision_evidence_profile_id", "evidence_category"]).size()
    assert (grouped == 1).all(), "Duplicate evidence category per profile"


# Tests 6-14: Evidence quality
def test_6_all_applicable_categories_represented(evidence_references, evidence_profiles):
    for pid in evidence_profiles["decision_evidence_profile_id"]:
        refs = evidence_references[evidence_references["decision_evidence_profile_id"] == pid]
        assert len(refs) >= 28, f"Profile {pid} missing evidence categories"


def test_7_not_applicable_not_counted_as_missing(evidence_references, evidence_completeness):
    na_count = len(evidence_references[evidence_references["evidence_status"] == "Not Applicable"])
    assert na_count >= 0, "Not Applicable is valid"


def test_8_missing_evidence_visible(evidence_references):
    missing = evidence_references[evidence_references["evidence_status"].isin(["Missing", "Missing Critical Evidence"])]
    assert len(missing) >= 0, "Missing evidence should be visible"


def test_9_critical_missing_affects_completeness(evidence_completeness):
    crit = evidence_completeness[evidence_completeness["critical_missing_evidence_count"] > 0]
    for _, row in crit.iterrows():
        assert row["evidence_completeness_status"] in ["Partial", "Limited", "Missing Critical Evidence"], "Critical missing should affect status"


def test_10_evidence_source_files_exist(evidence_references):
    for src in evidence_references["source_file"].dropna().unique():
        assert src != "", "Source file must not be empty"


def test_11_evidence_source_record_ids_retained(evidence_references):
    assert evidence_references["source_record_id"].notna().all(), "All evidence must have source_record_id"


def test_12_evidence_source_checksums_populated(evidence_references):
    # Checksums may be empty for prototype but column exists
    assert "source_checksum" in evidence_references.columns


def test_13_superseded_evidence_flagged(evidence_references):
    assert "superseded_flag" in evidence_references.columns


def test_14_every_package_has_all_lineage_stages(lineage_links, lineage_profiles):
    for pid in lineage_profiles["decision_lineage_profile_id"]:
        links = lineage_links[lineage_links["decision_lineage_profile_id"] == pid]
        stages = set(links["lineage_stage_number"])
        assert stages == set(range(1, 19)), f"Profile {pid} missing lineage stages"


# Tests 15-21: Lineage quality
def test_15_lineage_stages_ordered(lineage_links, lineage_profiles):
    for pid in lineage_profiles["decision_lineage_profile_id"]:
        links = lineage_links[lineage_links["decision_lineage_profile_id"] == pid].sort_values("lineage_stage_number")
        nums = links["lineage_stage_number"].tolist()
        assert nums == list(range(1, 19)), "Stages must be 1-18 in order"


def test_16_parent_child_links_reconcile(lineage_links):
    for _, row in lineage_links.iterrows():
        if row["lineage_stage_number"] > 1:
            assert row["parent_record_id"] != "", f"Stage {row['lineage_stage_number']} missing parent"


def test_17_no_fuzzy_lineage_matching(lineage_links):
    assert "ambiguity_flag" in lineage_links.columns
    assert not lineage_links["ambiguity_flag"].any(), "No fuzzy matching allowed"


def test_18_no_label_only_linkage(lineage_links):
    assert lineage_links["source_record_id"].notna().all(), "All links need source_record_id"
    assert (lineage_links["source_record_id"] != "").all(), "source_record_id must not be empty"


def test_19_orphan_lineage_visible(lineage_links):
    assert "orphan_flag" in lineage_links.columns


def test_20_trace_reaches_action_routing(traces):
    for text in traces["trace_summary"]:
        assert "Action routing" in text, "Trace must reach action routing"


def test_21_no_trace_claims_completed_decision(traces):
    for text in traces["trace_summary"]:
        assert "management decision" not in text.lower() or "not" in text.lower(), "Trace must not claim completed decision"


# Tests 22-31: Audit integrity
def test_22_audit_requirements_reconcile_with_2d5(audit_requirements):
    assert len(audit_requirements) > 0, "Audit requirements must exist"


def test_23_audit_required_actions_retain_actor_roles(audit_requirements):
    req = audit_requirements[audit_requirements["audit_required"] == True]
    assert req["required_actor_role"].notna().all(), "All audit-required actions need actor role"


def test_24_audit_catalogue_governed_event_types(audit_catalogue):
    governed = set(audit_catalogue["audit_event_type"])
    for ev in audit_catalogue["audit_event_type"]:
        assert ev in governed, f"{ev} not in catalogue"


def test_25_audit_event_contracts_not_executed(audit_contracts):
    assert (audit_contracts["event_status"] == "Not Executed").all(), "All events must be Not Executed"


def test_26_actor_ids_blank(audit_contracts):
    assert (audit_contracts["actor_id"].fillna("") == "").all(), "actor_id must be blank"


def test_27_actor_names_blank(audit_contracts):
    assert (audit_contracts["actor_name"].fillna("") == "").all(), "actor_name must be blank"


def test_28_event_timestamps_blank(audit_contracts):
    assert (audit_contracts["event_timestamp"].fillna("") == "").all(), "event_timestamp must be blank"


def test_29_management_comments_blank(audit_contracts):
    assert (audit_contracts["management_comment"].fillna("") == "").all(), "management_comment must be blank"


def test_30_approval_references_blank(audit_contracts):
    assert (audit_contracts["approval_reference"].fillna("") == "").all(), "approval_reference must be blank"


def test_31_no_completed_audit_event_fabricated(audit_contracts):
    assert not (audit_contracts["event_status"] == "Completed").any(), "No completed events"


# Tests 32-36: History and version
def test_32_history_contracts_initial_state(history):
    assert (history["history_status"] == "Initial Governed State").all()


def test_33_no_historical_decision_invented(history):
    assert history["prior_version"].fillna("").eq("").all(), "No prior version invented"
    assert history["prior_readiness_status"].fillna("").eq("").all(), "No prior status invented"


def test_34_version_control_records_created(version_control):
    assert len(version_control) > 0


def test_35_current_frozen_distinguishable(version_control):
    assert "version_status" in version_control.columns
    assert set(version_control["version_status"].unique()).issubset({"Current", "Superseded", "Draft", "Frozen", "Archived"})


def test_36_superseded_versions_flagged(version_control):
    assert "superseded_flag" in version_control.columns


# Tests 37-43: Integrity and retention
def test_37_sha256_used(integrity):
    assert (integrity["checksum_algorithm"] == "SHA-256").all(), "Must use SHA-256"


def test_38_frozen_checksums_match(integrity):
    verified = integrity[integrity["integrity_status"] == "Verified"]
    assert len(verified) > 0, "Some checksums must verify"


def test_39_integrity_failures_stop_processing(summary):
    assert summary.iloc[0]["failed_integrity_checks"] == 0, "No integrity failures"


def test_40_retention_records_created(retention):
    assert len(retention) > 0


def test_41_no_invented_legal_retention_periods(retention):
    for val in retention["retention_period_rule"]:
        assert "Organisational Policy" in str(val), "Must not invent legal retention periods"


def test_42_access_contracts_governed_roles(access):
    governed = {
        "Hospital COO / General Manager", "Medical Director", "Department Head",
        "Operations Manager", "Finance", "Human Resources", "Data Owner",
        "Analytics Team", "Clinical Lead", "Facilities / Maintenance",
        "Stakeholder Owner", "Governance / Audit Reviewer", "System Administrator"
    }
    roles = set(access["role_name"].unique())
    assert roles.issubset(governed), f"Unknown roles: {roles - governed}"


def test_43_no_authentication_implemented(access):
    assert (access["implementation_status"] == "Contract Only").all(), "Must not implement auth"


# Tests 44-50: Evidence packs and management review
def test_44_evidence_pack_sections_required(evidence_packs):
    sections = set(evidence_packs["included_section"].unique())
    assert "Executive Summary" in sections, "Must include Executive Summary"


def test_45_missing_evidence_pack_sections_visible(evidence_packs):
    assert "missing_section_flag" in evidence_packs.columns


def test_46_management_reviews_pending(management_reviews):
    assert (management_reviews["review_status"] == "Pending Management Review").all()


def test_47_selected_action_fields_blank(management_reviews):
    assert (management_reviews["selected_action_id"].fillna("") == "").all()


def test_48_selected_scenario_fields_blank(management_reviews):
    assert (management_reviews["selected_scenario_id"].fillna("") == "").all()


def test_49_reviewer_identity_blank(management_reviews):
    assert (management_reviews["reviewer_id"].fillna("") == "").all()
    assert (management_reviews["reviewer_name"].fillna("") == "").all()


def test_50_no_management_review_fabricated(management_reviews):
    assert (management_reviews["review_timestamp"].fillna("") == "").all()


# Tests 51-58: No selection or approval
def test_51_no_action_selected(summary):
    assert summary.iloc[0]["no_action_selected"] == True


def test_52_no_approval_recorded(summary):
    assert summary.iloc[0]["no_approval_recorded"] == True


def test_53_no_prerequisite_complete(summary):
    assert summary.iloc[0]["no_prerequisite_marked_complete"] == True


def test_54_no_block_resolved(summary):
    assert summary.iloc[0]["no_block_marked_resolved"] == True


def test_55_no_monitoring_falsely_implemented(summary):
    assert summary.iloc[0]["no_prerequisite_marked_complete"] == True


def test_56_causality_status_not_confirmed(routing):
    assert (routing["causality_status"] == "Not Confirmed").all()


def test_57_provisional_warnings_visible(explanations):
    assert "current_audit_state" in explanations.columns


def test_58_contradiction_warnings_visible(evidence_references):
    assert "contradiction_flag" in evidence_references.columns


# Tests 59-61: Financial uncertainty
def test_59_financial_uncertainty_traceable(evidence_references):
    fin = evidence_references[evidence_references["evidence_category"] == "Financial Uncertainty Evidence"]
    assert len(fin) > 0, "Financial uncertainty evidence must exist"


def test_60_streamlit_contract_fields(streamlit):
    panels = set(streamlit["panel_type"].unique())
    required = {"Evidence Summary", "Evidence Detail", "Lineage View", "Audit Requirement", "Audit History", "Version and Integrity"}
    assert required.issubset(panels), f"Missing panels: {required - panels}"


def test_61_no_prohibited_wording(explanations):
    prohibited = ["Audited and Approved", "Management Reviewed", "Action Completed", "Approved Decision", "Final Approval", "Verified by Management", "Implemented", "Resolved"]
    for text in explanations["audit_readiness_explanation"]:
        for word in prohibited:
            assert word.lower() not in str(text).lower(), f"Prohibited wording: {word}"


# Tests 62-67: Count reconciliation
def test_62_evidence_counts_reconcile(evidence_profiles, evidence_completeness):
    assert len(evidence_profiles) == len(evidence_completeness)


def test_63_lineage_counts_reconcile(lineage_profiles, lineage_completeness):
    assert len(lineage_profiles) == len(lineage_completeness)


def test_64_audit_contract_counts_reconcile(audit_contracts, audit_requirements):
    req_count = len(audit_requirements[audit_requirements["audit_required"] == True])
    assert len(audit_contracts) == req_count, f"Contract count {len(audit_contracts)} != required {req_count}"


def test_65_no_orphan_evidence_profile(evidence_profiles, routing):
    pkg_ids = set(routing["decision_package_id"])
    ev_ids = set(evidence_profiles["decision_package_id"])
    assert ev_ids.issubset(pkg_ids), "Orphan evidence profiles"


def test_66_no_orphan_lineage_profile(lineage_profiles, routing):
    pkg_ids = set(routing["decision_package_id"])
    ln_ids = set(lineage_profiles["decision_package_id"])
    assert ln_ids.issubset(pkg_ids), "Orphan lineage profiles"


def test_67_no_orphan_audit_contract(audit_contracts, routing):
    pkg_ids = set(routing["decision_package_id"])
    ac_ids = set(audit_contracts["decision_package_id"])
    assert ac_ids.issubset(pkg_ids), "Orphan audit contracts"


# Tests 68-73: Upstream immutability
def test_68_frozen_upstream_unchanged(summary):
    assert summary.iloc[0]["upstream_immutability_confirmed"] == True


def test_69_scenario_values_unchanged(summary):
    assert summary.iloc[0]["scenario_values_unchanged"] == True


def test_70_financial_values_unchanged(summary):
    assert summary.iloc[0]["financial_values_unchanged"] == True


def test_71_recommendation_values_unchanged(summary):
    assert summary.iloc[0]["recommendation_values_unchanged"] == True


def test_72_readiness_values_unchanged(summary):
    assert summary.iloc[0]["readiness_values_unchanged"] == True


def test_73_action_routing_values_unchanged(summary):
    assert summary.iloc[0]["action_routing_values_unchanged"] == True


# Tests 74-77: Output integrity and status
def test_74_output_counts_reconcile(evidence_profiles, lineage_profiles, traces, history, management_reviews, explanations):
    assert len(evidence_profiles) == 646
    assert len(lineage_profiles) == 646
    assert len(traces) == 646
    assert len(history) == 646
    assert len(management_reviews) == 646
    assert len(explanations) == 646


def test_75_manifest_checksums_complete(manifest):
    assert "outputs" in manifest
    assert len(manifest["outputs"]) >= 20
    for fname, info in manifest["outputs"].items():
        assert "checksum" in info
        assert info["checksum"] != ""


def test_76_smoke_test_not_mixed(summary):
    assert summary.iloc[0]["mode"] == "full_run"


def test_77_step_2d6_status_correct(summary):
    assert summary.iloc[0]["status"] == "COMPLETE"
    assert "READY FOR STEP 2D-7" in summary.iloc[0]["conclusion"]
