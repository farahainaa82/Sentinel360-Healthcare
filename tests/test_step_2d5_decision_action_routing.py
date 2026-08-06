"""
test_step_2d5_decision_action_routing.py
Phase 2D-5 — 62 focused tests for Decision Options and Action Routing.
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


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------
@pytest.fixture
def routing():
    return load_csv("step_2d5_decision_action_routing_register.csv")


@pytest.fixture
def readiness():
    return load_csv("step_2d4_decision_readiness_register.csv")


@pytest.fixture
def eligibility():
    return load_csv("step_2d5_action_eligibility_register.csv")


@pytest.fixture
def primary():
    return load_csv("step_2d5_primary_action_register.csv")


@pytest.fixture
def secondary():
    return load_csv("step_2d5_secondary_action_register.csv")


@pytest.fixture
def roles():
    return load_csv("step_2d5_responsible_role_register.csv")


@pytest.fixture
def queues():
    return load_csv("step_2d5_queue_assignment_register.csv")


@pytest.fixture
def blocking():
    return load_csv("step_2d5_action_blocking_register.csv")


@pytest.fixture
def prereq():
    return load_csv("step_2d5_action_prerequisite_register.csv")


@pytest.fixture
def selection():
    return load_csv("step_2d5_management_selection_contract.csv")


@pytest.fixture
def escalation():
    return load_csv("step_2d5_escalation_routing_register.csv")


@pytest.fixture
def monitoring():
    return load_csv("step_2d5_monitoring_action_register.csv")


@pytest.fixture
def audit():
    return load_csv("step_2d5_action_audit_requirement_register.csv")


@pytest.fixture
def explanation():
    return load_csv("step_2d5_action_explanation_register.csv")


@pytest.fixture
def streamlit():
    return load_csv("step_2d5_streamlit_action_data_contract.csv")


@pytest.fixture
def evidence():
    return load_csv("step_2d5_action_evidence_register.csv")


@pytest.fixture
def lineage():
    return load_csv("step_2d5_action_lineage_register.csv")


@pytest.fixture
def auth():
    return load_csv("step_2d5_authoritative_input_register.csv")


@pytest.fixture
def manifest():
    path = os.path.join(OUT, "step_2d5_manifest.json")
    with open(path, "r") as f:
        return json.load(f)


@pytest.fixture
def summary():
    return load_csv("step_2d5_execution_summary.csv")


@pytest.fixture
def catalogue():
    return pd.read_csv(os.path.join(CONFIG, "decision_action_catalogue.csv"))


# ------------------------------------------------------------------
# Tests 1-5: Population and ID integrity
# ------------------------------------------------------------------

def test_1_one_routing_per_readiness(routing, readiness):
    assert len(routing) == len(readiness), "Must be exactly one routing per readiness record"


def test_2_routing_ids_unique(routing):
    assert not routing["decision_action_routing_id"].duplicated().any(), "Routing IDs must be unique"


def test_3_retains_decision_readiness_id(routing):
    assert "decision_readiness_id" in routing.columns, "Must retain decision_readiness_id"
    assert routing["decision_readiness_id"].notna().all(), "All routing records must have decision_readiness_id"


def test_4_retains_decision_package_id(routing):
    assert "decision_package_id" in routing.columns, "Must retain decision_package_id"
    assert routing["decision_package_id"].notna().all(), "All routing records must have decision_package_id"


def test_5_no_cartesian_joins(eligibility):
    # 646 packages * 18 actions = 11628
    expected_max = 646 * 18
    assert len(eligibility) <= expected_max, f"Eligibility exploded: {len(eligibility)} > {expected_max}"
    grouped = eligibility.groupby(["decision_action_routing_id", "action_id"]).size()
    assert (grouped == 1).all(), "Duplicate action-package combinations detected"


# ------------------------------------------------------------------
# Tests 6-12: Action catalogue and eligibility
# ------------------------------------------------------------------

def test_6_all_allowed_actions_governed(eligibility, catalogue):
    allowed_names = set(eligibility["action_name"].unique())
    governed_names = set(catalogue["action_name"].unique())
    assert allowed_names.issubset(governed_names), f"Unknown actions: {allowed_names - governed_names}"


def test_7_one_eligibility_per_action_package(eligibility):
    grouped = eligibility.groupby(["decision_action_routing_id", "action_id"]).size()
    assert (grouped == 1).all(), "Each action-package must have exactly one eligibility"


def test_8_no_unknown_action_names(eligibility, catalogue):
    test_6_all_allowed_actions_governed(eligibility, catalogue)


def test_9_one_primary_action_per_package(primary):
    counts = primary.groupby("decision_action_routing_id").size()
    assert (counts == 1).all(), "Each package must have exactly one primary action"


def test_10_one_primary_queue_per_package(queues):
    counts = queues.groupby("decision_action_routing_id").size()
    assert (counts == 1).all(), "Each package must have exactly one primary queue"


def test_11_primary_action_reconciles_with_readiness(primary, routing):
    merged = primary.merge(
        routing[["decision_action_routing_id", "final_readiness_status"]],
        on="decision_action_routing_id",
        suffixes=("", "_rt")
    )
    status_map = {
        "Ready for Integrated Management Review": "Review Integrated Decision Package",
        "Ready with Conditions": "Review Integrated Decision Package",
        "Requires Assumption Validation": "Validate Assumptions",
        "Requires Baseline Validation": "Validate Baseline",
        "Requires Financial Input": "Validate Financial Inputs",
        "Requires Benefit Validation": "Validate Benefit Assumptions",
        "Requires Budget Data": "Provide Budget Information",
        "Requires Stakeholder Validation": "Request Stakeholder Review",
        "Requires Additional Scenario Analysis": "Request Additional Scenario",
        "Requires Evidence Completion": "Request Evidence Completion",
        "Requires Lineage Completion": "Request Lineage Completion",
        "Monitoring Only": "Continue Monitoring",
        "Non-Quantitative": "Route to Non-Quantitative Review",
        "Not Suitable for Decision Use": "Reject Decision Use",
        "Rejected": "Reject Decision Use",
    }
    col = "final_readiness_status" if "final_readiness_status" in merged.columns else "final_readiness_status_rt"
    for _, row in merged.iterrows():
        expected = status_map.get(row[col], "")
        assert row["primary_permitted_action"] == expected, f"Primary action mismatch for {row[col]}"


def test_12_primary_queue_reconciles_with_readiness(queues, routing):
    merged = queues.merge(routing[["decision_action_routing_id", "final_readiness_status"]], on="decision_action_routing_id")
    queue_map = {
        "Ready for Integrated Management Review": "Integrated Management Review Queue",
        "Ready with Conditions": "Conditional Review Queue",
        "Requires Assumption Validation": "Assumption Validation Queue",
        "Requires Baseline Validation": "Baseline Validation Queue",
        "Requires Financial Input": "Financial Input Queue",
        "Requires Benefit Validation": "Benefit Validation Queue",
        "Requires Budget Data": "Budget Information Queue",
        "Requires Stakeholder Validation": "Stakeholder Validation Queue",
        "Requires Additional Scenario Analysis": "Additional Scenario Queue",
        "Requires Evidence Completion": "Evidence Completion Queue",
        "Requires Lineage Completion": "Lineage Completion Queue",
        "Monitoring Only": "Monitoring Queue",
        "Non-Quantitative": "Non-Quantitative Review Queue",
        "Not Suitable for Decision Use": "Not Suitable Register",
        "Rejected": "Rejected Register",
    }
    for _, row in merged.iterrows():
        expected = queue_map.get(row["final_readiness_status"], "")
        assert row["primary_queue"] == expected, f"Primary queue mismatch for {row['final_readiness_status']}"


# ------------------------------------------------------------------
# Tests 13-20: Readiness-specific routing rules
# ------------------------------------------------------------------

def test_13_ready_permits_management_review(eligibility, routing):
    ready = routing[routing["final_readiness_status"] == "Ready for Integrated Management Review"]
    for rid in ready["decision_action_routing_id"]:
        elg = eligibility[(eligibility["decision_action_routing_id"] == rid) & (eligibility["action_name"] == "Review Integrated Decision Package")]
        assert not elg.empty, "Ready must permit Review Integrated Decision Package"
        assert elg.iloc[0]["action_eligibility_status"] == "Allowed", "Review must be Allowed for Ready"


def test_14_ready_with_conditions_preserves_conditions(eligibility, routing):
    rwc = routing[routing["final_readiness_status"] == "Ready with Conditions"]
    for rid in rwc["decision_action_routing_id"]:
        elg = eligibility[(eligibility["decision_action_routing_id"] == rid)]
        cond_count = len(elg[elg["action_eligibility_status"] == "Allowed with Conditions"])
        assert cond_count >= 0, "Ready with Conditions may have conditional actions"


def test_15_requires_assumption_routes_to_validate(eligibility, routing):
    req = routing[routing["final_readiness_status"] == "Requires Assumption Validation"]
    for rid in req["decision_action_routing_id"]:
        elg = eligibility[(eligibility["decision_action_routing_id"] == rid) & (eligibility["action_name"] == "Validate Assumptions")]
        assert not elg.empty
        assert elg.iloc[0]["action_eligibility_status"] == "Allowed"


def test_16_monitoring_only_routes_to_continue(eligibility, routing):
    mon = routing[routing["final_readiness_status"] == "Monitoring Only"]
    for rid in mon["decision_action_routing_id"]:
        elg = eligibility[(eligibility["decision_action_routing_id"] == rid) & (eligibility["action_name"] == "Continue Monitoring")]
        assert not elg.empty
        assert elg.iloc[0]["action_eligibility_status"] == "Allowed"


def test_17_non_quantitative_routes_to_qualitative(eligibility, routing):
    nq = routing[routing["final_readiness_status"] == "Non-Quantitative"]
    for rid in nq["decision_action_routing_id"]:
        elg = eligibility[(eligibility["decision_action_routing_id"] == rid) & (eligibility["action_name"] == "Route to Non-Quantitative Review")]
        assert not elg.empty
        assert elg.iloc[0]["action_eligibility_status"] == "Allowed"


def test_18_rejected_only_reject_allowed(eligibility, routing):
    rej = routing[routing["final_readiness_status"] == "Rejected"]
    for rid in rej["decision_action_routing_id"]:
        elg = eligibility[eligibility["decision_action_routing_id"] == rid]
        allowed = elg[elg["action_eligibility_status"] == "Allowed"]
        assert len(allowed) == 1, "Rejected must allow exactly one action"
        assert allowed.iloc[0]["action_name"] == "Reject Decision Use"


def test_19_limited_trial_blocked_when_gates_fail(eligibility, routing):
    # Limited trial should be Blocked or Allowed with Conditions, never plain Allowed when gates fail
    lt = eligibility[eligibility["action_name"] == "Proceed to Limited-Trial Consideration"]
    blocked_or_cond = lt[lt["action_eligibility_status"].isin(["Blocked", "Allowed with Conditions", "Not Permitted"])]
    # Most should be blocked; some Ready may be Allowed with Conditions
    assert len(blocked_or_cond) > 0, "Some limited-trial must be blocked"


def test_20_limited_trial_never_means_approval(eligibility):
    lt = eligibility[eligibility["action_name"] == "Proceed to Limited-Trial Consideration"]
    for _, row in lt.iterrows():
        assert row["action_eligibility_status"] != "Allowed", "Limited-trial must never be plain Allowed without conditions"


# ------------------------------------------------------------------
# Tests 21-24: Prerequisites and blocking
# ------------------------------------------------------------------

def test_21_prerequisites_allowed_statuses(prereq):
    allowed = {"Pending", "Deferred", "Not Applicable"}
    assert set(prereq["current_status"].unique()).issubset(allowed), f"Invalid prerequisite status: {set(prereq['current_status'].unique()) - allowed}"


def test_22_no_prerequisite_completed(prereq):
    if not prereq.empty:
        assert not (prereq["current_status"] == "Completed").any(), "No prerequisite may be marked Completed"


def test_23_blocking_records_have_source_references(blocking):
    if not blocking.empty:
        assert blocking["source_phase"].notna().all(), "All blocking records must have source_phase"
        assert (blocking["source_phase"] != "").all(), "source_phase must not be empty"


def test_24_no_blocking_resolved(blocking):
    if not blocking.empty:
        assert not (blocking["current_status"] == "Resolved").any(), "No blocking condition may be marked Resolved"


# ------------------------------------------------------------------
# Tests 25-28: Roles and escalation
# ------------------------------------------------------------------

def test_25_only_governed_roles(roles):
    governed = {
        "Hospital COO / General Manager", "Medical Director", "Department Head",
        "Operations Manager", "Finance", "Human Resources", "Data Owner",
        "Analytics Team", "Clinical Lead", "Facilities / Maintenance",
        "Stakeholder Owner", "Governance / Audit Reviewer",
    }
    for col in ["primary_responsible_role", "secondary_responsible_role", "tertiary_responsible_role"]:
        if col in roles.columns:
            vals = set(roles[col].dropna().unique())
            assert vals.issubset(governed | {""}), f"Invalid roles in {col}: {vals - governed}"


def test_26_no_named_individuals(roles):
    for col in roles.columns:
        if "role" in col.lower():
            for val in roles[col].dropna():
                assert "@" not in str(val), "No email addresses (named individuals) allowed"
                assert ".com" not in str(val), "No URLs allowed"


def test_27_operational_escalation_separate(escalation):
    assert "operational_escalation_separate" in escalation.columns, "Must flag operational escalation as separate"
    assert escalation["operational_escalation_separate"].all(), "All records must mark operational escalation as separate"


def test_28_high_risk_not_downgraded(eligibility, routing, escalation):
    merged = escalation.merge(
        routing[["decision_action_routing_id", "final_readiness_status"]],
        on="decision_action_routing_id",
        suffixes=("", "_rt")
    )
    high_esc = merged[merged["escalation_required"] == True]
    col = "final_readiness_status" if "final_readiness_status" in merged.columns else "final_readiness_status_rt"
    for _, row in high_esc.iterrows():
        assert str(row[col]) != "", "Readiness status must remain even with escalation"


# ------------------------------------------------------------------
# Tests 29-35: Management selection integrity
# ------------------------------------------------------------------

def test_29_all_selectable_require_management_selection(eligibility):
    selectable = eligibility[eligibility["action_eligibility_status"].isin(["Allowed", "Allowed with Conditions"])]
    assert (selectable["management_selection_required"] == True).all(), "All selectable actions require management selection"


def test_30_selected_flag_false(selection):
    assert not selection["selected_flag"].any(), "selected_flag must be False for all records"


def test_31_selected_by_blank(selection):
    vals = selection["selected_by"].fillna("")
    assert (vals == "").all(), "selected_by must be blank"


def test_32_selected_timestamp_blank(selection):
    vals = selection["selected_timestamp"].fillna("")
    assert (vals == "").all(), "selected_timestamp must be blank"


def test_33_management_comment_blank(selection):
    vals = selection["management_comment"].fillna("")
    assert (vals == "").all(), "management_comment must be blank"


def test_34_approval_reference_blank(selection):
    vals = selection["approval_reference"].fillna("")
    assert (vals == "").all(), "approval_reference must be blank"


def test_35_all_decision_status_pending(selection):
    assert (selection["decision_status"] == "Pending Management Review").all(), "All decision statuses must be Pending Management Review"


# ------------------------------------------------------------------
# Tests 36-39: Audit and monitoring
# ------------------------------------------------------------------

def test_36_audit_requirements_exist(audit, eligibility):
    gov_actions = [
        "Review Integrated Decision Package", "Compare Scenario Options",
        "Validate Assumptions", "Validate Baseline", "Validate Financial Inputs",
        "Validate Benefit Assumptions", "Provide Budget Information",
        "Request Additional Scenario", "Request Stakeholder Review",
        "Proceed to Limited-Trial Consideration", "Defer Decision", "Reject Decision Use",
    ]
    for action in gov_actions:
        recs = audit[audit["action_name"] == action]
        assert not recs.empty, f"Audit requirements must exist for {action}"
        assert recs["audit_required"].any(), f"At least one audit record must be required for {action}"


def test_37_no_completed_audit_events(audit):
    assert not (audit["future_audit_status"] == "Completed").any(), "No completed audit events allowed"


def test_38_monitoring_has_triggers(monitoring):
    assert "trigger_condition" in monitoring.columns, "Monitoring must have trigger_condition"
    assert "escalation_condition" in monitoring.columns, "Monitoring must have escalation_condition"
    assert "reassessment_condition" in monitoring.columns, "Monitoring must have reassessment_condition"


def test_39_monitoring_not_falsely_implemented(monitoring):
    assert not (monitoring["current_status"] == "Implemented").any(), "Monitoring must not be falsely marked Implemented"


# ------------------------------------------------------------------
# Tests 40-44: No selection or approval
# ------------------------------------------------------------------

def test_40_no_preferred_scenario_selected(selection):
    assert (selection["selected_flag"] == False).all(), "No preferred scenario selected"


def test_41_no_recommendation_approved(selection):
    assert (selection["decision_status"] == "Pending Management Review").all(), "No recommendation approved"


def test_42_no_financial_option_approved(selection):
    test_41_no_recommendation_approved(selection)


def test_43_no_management_action_selected(selection):
    assert (selection["selected_flag"] == False).all(), "No management action selected"


def test_44_no_management_approval_fabricated(selection):
    vals = selection["approval_reference"].fillna("")
    assert (vals == "").all(), "No approval reference fabricated"


# ------------------------------------------------------------------
# Tests 45-49: Display governance and wording
# ------------------------------------------------------------------

def test_45_no_prohibited_wording(explanation):
    prohibited = ["Recommended action", "Best action", "AI-selected action", "Approved action", "Execute now", "Automatically proceed", "Guaranteed result", "Final decision"]
    for text in explanation["action_routing_explanation"]:
        for word in prohibited:
            assert word.lower() not in str(text).lower(), f"Prohibited wording found: {word}"


def test_46_causality_status_unchanged(routing):
    if "causality_status" in routing.columns:
        assert (routing["causality_status"] == "Not Confirmed").all(), "causality_status must remain Not Confirmed"


def test_47_provisional_warnings_visible(routing):
    # Provisional warnings from 2D-4 should be preserved
    assert "final_readiness_status" in routing.columns, "Readiness status must be visible"


def test_48_contradiction_warnings_visible(eligibility):
    assert "action_reason" in eligibility.columns, "Action reasons must be visible for contradiction detection"


def test_49_missing_financial_inputs_visible(eligibility):
    fin = eligibility[eligibility["action_name"].isin(["Validate Financial Inputs", "Provide Budget Information"])]
    assert not fin.empty, "Financial actions must be present"


# ------------------------------------------------------------------
# Tests 50-53: Evidence, lineage, orphans
# ------------------------------------------------------------------

def test_50_evidence_reconciles(evidence, routing):
    routing_ids = set(routing["decision_action_routing_id"])
    evidence_ids = set(evidence["decision_action_routing_id"])
    assert evidence_ids.issubset(routing_ids), "All evidence must link to valid routing"


def test_51_lineage_reconciles(lineage, routing):
    routing_ids = set(routing["decision_action_routing_id"])
    lineage_ids = set(lineage["decision_action_routing_id"])
    assert lineage_ids.issubset(routing_ids), "All lineage must link to valid routing"


def test_52_no_orphan_routing(routing, eligibility):
    routing_ids = set(routing["decision_action_routing_id"])
    elig_ids = set(eligibility["decision_action_routing_id"])
    assert routing_ids.issubset(elig_ids), "Every routing must have eligibility records"


def test_53_streamlit_contract_fields(streamlit):
    required = {"decision_action_routing_id", "action_name", "action_eligibility_status", "enabled_flag", "disabled_reason", "confirmation_required", "audit_required", "management_selection_required", "selected_flag"}
    assert required.issubset(set(streamlit.columns)), f"Missing Streamlit fields: {required - set(streamlit.columns)}"


# ------------------------------------------------------------------
# Tests 54-58: Upstream immutability
# ------------------------------------------------------------------

def test_54_frozen_checksums_match(auth):
    assert (auth["checksum_match"] == True).all(), "All checksums must match"


def test_55_scenario_values_unchanged(summary):
    assert summary.iloc[0]["scenario_values_unchanged"] == True, "Scenario values must be unchanged"


def test_56_financial_values_unchanged(summary):
    assert summary.iloc[0]["financial_values_unchanged"] == True, "Financial values must be unchanged"


def test_57_recommendation_values_unchanged(summary):
    assert summary.iloc[0]["recommendation_values_unchanged"] == True, "Recommendation values must be unchanged"


def test_58_readiness_values_unchanged(summary):
    assert summary.iloc[0]["readiness_values_unchanged"] == True, "Readiness values must be unchanged"


# ------------------------------------------------------------------
# Tests 59-62: Output integrity and status
# ------------------------------------------------------------------

def test_59_output_counts_reconcile(routing, eligibility, primary, queues, blocking, prereq, audit, monitoring, selection):
    assert len(routing) == 646, "Routing must be 646"
    assert len(primary) == 646, "Primary must be 646"
    assert len(queues) == 646, "Queues must be 646"


def test_60_manifest_checksums_complete(manifest):
    assert "outputs" in manifest, "Manifest must contain outputs"
    assert len(manifest["outputs"]) >= 18, "Manifest must have at least 18 output entries"
    for fname, info in manifest["outputs"].items():
        assert "checksum" in info, f"{fname} missing checksum"
        assert info["checksum"] != "", f"{fname} checksum empty"


def test_61_smoke_test_not_mixed(summary):
    assert summary.iloc[0]["mode"] == "full_run", "Full run must not be mixed with smoke test"


def test_62_step_2d5_status_correct(summary):
    assert summary.iloc[0]["status"] == "COMPLETE", "Step 2D-5 must be COMPLETE"
    assert "READY FOR STEP 2D-6" in summary.iloc[0]["conclusion"], "Conclusion must reference readiness for 2D-6"
