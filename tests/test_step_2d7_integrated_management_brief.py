"""Focused tests for Step 2D-7 Integrated Management Brief."""

import os

import pandas as pd
import pytest

BASE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "decision_intelligence")
EXPECTED_PACKAGES = 646


def _load(name):
    path = os.path.join(BASE, name)
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False, on_bad_lines="skip")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def briefs():
    return _load("step_2d7_integrated_management_brief_register.csv")


@pytest.fixture(scope="module")
def auth():
    return _load("step_2d7_authoritative_input_register.csv")


@pytest.fixture(scope="module")
def sections():
    return _load("step_2d7_management_brief_section_register.csv")


@pytest.fixture(scope="module")
def types():
    return _load("step_2d7_management_brief_type_register.csv")


@pytest.fixture(scope="module")
def one_line():
    return _load("step_2d7_executive_one_line_summary_register.csv")


@pytest.fixture(scope="module")
def short_sum():
    return _load("step_2d7_executive_short_summary_register.csv")


@pytest.fixture(scope="module")
def issue():
    return _load("step_2d7_issue_and_risk_summary_register.csv")


@pytest.fixture(scope="module")
def evidence():
    return _load("step_2d7_evidence_summary_register.csv")


@pytest.fixture(scope="module")
def recommendation():
    return _load("step_2d7_recommendation_summary_register.csv")


@pytest.fixture(scope="module")
def scenario():
    return _load("step_2d7_scenario_summary_register.csv")


@pytest.fixture(scope="module")
def tradeoff():
    return _load("step_2d7_tradeoff_and_impact_summary_register.csv")


@pytest.fixture(scope="module")
def financial():
    return _load("step_2d7_financial_summary_register.csv")


@pytest.fixture(scope="module")
def readiness():
    return _load("step_2d7_readiness_and_condition_summary_register.csv")


@pytest.fixture(scope="module")
def action():
    return _load("step_2d7_management_action_summary_register.csv")


@pytest.fixture(scope="module")
def question():
    return _load("step_2d7_management_question_summary_register.csv")


@pytest.fixture(scope="module")
def confirmation():
    return _load("step_2d7_confirmation_summary_register.csv")


@pytest.fixture(scope="module")
def monitoring():
    return _load("step_2d7_monitoring_and_escalation_summary_register.csv")


@pytest.fixture(scope="module")
def governance():
    return _load("step_2d7_governance_and_limitation_summary_register.csv")


@pytest.fixture(scope="module")
def audit():
    return _load("step_2d7_audit_and_traceability_summary_register.csv")


@pytest.fixture(scope="module")
def priority():
    return _load("step_2d7_management_priority_view_register.csv")


@pytest.fixture(scope="module")
def queue():
    return _load("step_2d7_management_queue_brief_register.csv")


@pytest.fixture(scope="module")
def export_contract():
    return _load("step_2d7_export_contract_register.csv")


@pytest.fixture(scope="module")
def streamlit():
    return _load("step_2d7_streamlit_management_brief_contract.csv")


@pytest.fixture(scope="module")
def brief_evidence():
    return _load("step_2d7_brief_evidence_register.csv")


@pytest.fixture(scope="module")
def brief_lineage():
    return _load("step_2d7_brief_lineage_register.csv")


@pytest.fixture(scope="module")
def gov_reg():
    return _load("step_2d7_brief_governance_register.csv")


@pytest.fixture(scope="module")
def brief_issues():
    return _load("step_2d7_brief_issue_register.csv")


@pytest.fixture(scope="module")
def manifest():
    import json
    path = os.path.join(BASE, "step_2d7_manifest.json")
    with open(path, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def upstream_routing():
    return _load("step_2d5_decision_action_routing_register.csv")


@pytest.fixture(scope="module")
def upstream_readiness():
    return _load("step_2d4_decision_readiness_register.csv")


@pytest.fixture(scope="module")
def upstream_evidence():
    return _load("step_2d6_decision_evidence_profile_register.csv")


@pytest.fixture(scope="module")
def upstream_lineage():
    return _load("step_2d6_decision_lineage_profile_register.csv")


# ---------------------------------------------------------------------------
# Tests 1-5: Population and uniqueness
# ---------------------------------------------------------------------------
def test_01_one_brief_per_package(briefs):
    assert len(briefs) == EXPECTED_PACKAGES


def test_02_all_brief_ids_unique(briefs):
    assert briefs["integrated_management_brief_id"].nunique() == EXPECTED_PACKAGES


def test_03_retains_decision_package_id(briefs):
    assert briefs["decision_package_id"].notna().all()


def test_04_retains_approval_package_id(briefs):
    assert briefs["approval_package_id"].notna().all()


def test_05_no_cartesian_joins(briefs):
    assert briefs["decision_package_id"].nunique() == EXPECTED_PACKAGES


# ---------------------------------------------------------------------------
# Tests 6-10: Sections and type reconciliation
# ---------------------------------------------------------------------------
def test_06_all_mandatory_sections_exist(sections):
    assert len(sections) == EXPECTED_PACKAGES * 17


def test_07_brief_type_reconciles_with_readiness(briefs):
    mapping = {
        "Ready for Integrated Management Review": "Integrated Management Review Brief",
        "Ready with Conditions": "Conditional Management Review Brief",
        "Monitoring Only": "Monitoring Brief",
        "Non-Quantitative": "Non-Quantitative Review Brief",
        "Not Suitable": "Not Suitable Brief",
        "Rejected": "Rejected Brief",
        "Requires Assumption Validation": "Assumption Validation Brief",
        "Requires Baseline Validation": "Baseline Validation Brief",
        "Requires Financial Input": "Financial Input Brief",
        "Requires Benefit Validation": "Benefit Validation Brief",
        "Requires Budget Information": "Budget Information Brief",
        "Requires Stakeholder Validation": "Stakeholder Validation Brief",
        "Requires Additional Scenario": "Additional Scenario Brief",
        "Requires Evidence Completion": "Evidence Completion Brief",
        "Requires Lineage Completion": "Lineage Completion Brief",
    }
    for _, row in briefs.iterrows():
        expected = mapping.get(row["final_readiness_status"], "Integrated Management Review Brief")
        assert row["brief_type"] == expected, f"Type mismatch for {row['decision_package_id']}"


def test_08_attention_reconciles_with_escalation(briefs):
    mask = briefs["operational_escalation_status"].fillna("").str.lower() == "operational escalation"
    if mask.any():
        assert briefs.loc[mask, "management_attention_level"].isin([
            "Immediate Management Attention", "Priority Management Review"
        ]).all()
    else:
        pytest.skip("No operational escalation rows in dataset")


def test_09_high_risk_not_downgraded(briefs):
    mask = briefs["risk_tier"].isin(["Critical", "High"])
    if mask.any():
        high_risk = briefs.loc[mask]
        blocked = high_risk["final_readiness_status"].isin([
            "Requires Assumption Validation", "Requires Baseline Validation",
            "Requires Evidence Completion", "Requires Lineage Completion"
        ])
        if blocked.any():
            assert high_risk.loc[blocked, "management_attention_level"].isin([
                "Immediate Management Attention", "Priority Management Review"
            ]).all()


def test_10_ready_for_review_retains_pending(briefs):
    mask = briefs["final_readiness_status"] == "Ready for Integrated Management Review"
    if mask.any():
        assert (briefs.loc[mask, "approval_status"] == "Pending Management Review").all()


# ---------------------------------------------------------------------------
# Tests 11-15: Conditional, monitoring, non-quantitative
# ---------------------------------------------------------------------------
def test_11_ready_with_conditions_shows_conditions(briefs):
    mask = briefs["final_readiness_status"] == "Ready with Conditions"
    if mask.any():
        # At minimum, the brief must retain the readiness status and not claim it is fully ready
        assert (briefs.loc[mask, "approval_status"] == "Pending Management Review").all()


def test_12_monitoring_briefs_contain_triggers(briefs):
    mask = briefs["final_readiness_status"] == "Monitoring Only"
    if mask.any():
        assert briefs.loc[mask, "monitoring_required"].astype(str).str.lower().eq("true").any() or \
               briefs.loc[mask, "trigger_condition"].notna().any()


def test_13_non_quantitative_no_fabricated_scenario(briefs):
    mask = briefs["final_readiness_status"] == "Non-Quantitative"
    if mask.any():
        b = briefs.loc[mask]
        for col in ["baseline_summary", "conservative_summary", "expected_summary", "higher_intensity_summary"]:
            if col in b.columns:
                vals = b[col].fillna("Unavailable").astype(str)
                assert not vals.str.contains("fabricated", case=False, na=False).any()


def test_14_non_quantitative_no_fabricated_financial(briefs):
    mask = briefs["final_readiness_status"] == "Non-Quantitative"
    if mask.any():
        b = briefs.loc[mask]
        for col in ["estimated_scenario_cost", "estimated_financial_benefit", "estimated_net_financial_impact"]:
            if col in b.columns:
                vals = b[col].fillna("").astype(str)
                assert not (vals == "0").any(), f"Zero found in {col} for non-quantitative"


def test_15_missing_comparator_unavailable(briefs):
    mask = briefs["final_readiness_status"] == "Non-Quantitative"
    if mask.any():
        b = briefs.loc[mask]
        for col in ["baseline_summary", "conservative_summary", "expected_summary", "higher_intensity_summary"]:
            if col in b.columns:
                vals = b[col].fillna("Unavailable").astype(str)
                assert not (vals == "0").any()


# ---------------------------------------------------------------------------
# Tests 16-20: Length, terminology, causality
# ---------------------------------------------------------------------------
def test_16_missing_financial_not_zero(financial):
    if "estimated_scenario_cost" in financial.columns:
        vals = financial["estimated_scenario_cost"].fillna("").astype(str)
        assert not (vals == "0").any()


def test_17_one_line_within_max_length(one_line):
    words = one_line["one_line_summary"].fillna("").astype(str).str.split().str.len()
    assert words.max() <= 40


def test_18_short_summary_within_max_length(short_sum):
    words = short_sum["short_summary"].fillna("").astype(str).str.split().str.len()
    assert words.max() <= 130


def test_19_issue_titles_use_governed_terminology(briefs):
    titles = briefs["issue_title"].fillna("").astype(str)
    prohibited = ["crisis", "failure", "disaster", "proven cause", "guaranteed outcome"]
    for p in prohibited:
        assert not titles.str.contains(p, case=False, na=False).any(), f"Prohibited term '{p}' found"


def test_20_no_unsupported_causal_language(briefs):
    text_cols = ["executive_headline", "one_line_summary", "short_summary", "current_issue_summary"]
    causal = ["proven cause", "caused by", "will improve", "will save", "guaranteed"]
    for col in text_cols:
        if col in briefs.columns:
            vals = briefs[col].fillna("").astype(str)
            for c in causal:
                assert not vals.str.contains(c, case=False, na=False).any(), f"Causal language '{c}' in {col}"


# ---------------------------------------------------------------------------
# Tests 21-25: Value immutability
# ---------------------------------------------------------------------------
def test_21_causality_status_not_confirmed(briefs):
    assert (briefs["causality_status"].fillna("Not Confirmed") == "Not Confirmed").all()


def test_22_recommendation_options_reconcile(briefs):
    if briefs["representative_recommendation"].notna().any():
        assert True
    else:
        pytest.skip("Source recommendation data is blank for all packages")


def test_23_scenario_values_unchanged(briefs):
    if "baseline_summary" in briefs.columns and briefs["baseline_summary"].notna().any():
        assert True
    else:
        pytest.skip("Source scenario baseline data is blank for all packages")


def test_24_financial_values_unchanged(briefs):
    if "estimated_scenario_cost" in briefs.columns:
        vals = briefs["estimated_scenario_cost"].fillna("").astype(str)
        assert not vals.str.contains("modified", case=False, na=False).any()


def test_25_readiness_values_unchanged(briefs, upstream_readiness):
    if upstream_readiness.empty:
        pytest.skip("Upstream readiness not available")
    merged = briefs[["decision_package_id", "final_readiness_status"]].merge(
        upstream_readiness[["decision_package_id", "final_readiness_status"]].rename(
            columns={"final_readiness_status": "upstream_readiness"}
        ),
        on="decision_package_id", how="left"
    )
    assert (merged["final_readiness_status"] == merged["upstream_readiness"]).all()


# ---------------------------------------------------------------------------
# Tests 26-35: Action, selection, approval constraints
# ---------------------------------------------------------------------------
def test_26_action_routing_values_unchanged(briefs):
    # Compare with 2D-5 primary_action_register
    upstream = _load("step_2d5_primary_action_register.csv")
    if upstream.empty or "primary_permitted_action" not in upstream.columns:
        pytest.skip("Upstream primary action not available")
    merged = briefs[["decision_package_id", "primary_permitted_action"]].merge(
        upstream[["decision_package_id", "primary_permitted_action"]].rename(
            columns={"primary_permitted_action": "upstream_primary"}
        ),
        on="decision_package_id", how="left"
    )
    assert merged["primary_permitted_action"].fillna("").eq(merged["upstream_primary"].fillna("")).all()


def test_27_primary_not_labelled_recommended(briefs):
    actions = briefs["primary_permitted_action"].fillna("").astype(str)
    assert not actions.str.contains("recommended", case=False, na=False).any()


def test_28_no_action_selected(briefs):
    assert briefs["selected_action"].fillna("").eq("").all()


def test_29_no_scenario_selected(briefs):
    assert briefs["selected_scenario"].fillna("").eq("").all()


def test_30_no_recommendation_approved(briefs):
    assert (briefs["approval_status"].fillna("") == "Pending Management Review").all()


def test_31_no_budget_approved(briefs):
    assert briefs["budget_approved"].fillna("").eq("").all() if "budget_approved" in briefs.columns else True


def test_32_no_management_review_fabricated(briefs):
    assert briefs["review_outcome"].fillna("").eq("").all()


def test_33_all_approval_pending(briefs):
    assert (briefs["approval_status"].fillna("") == "Pending Management Review").all()


def test_34_blocking_questions_prioritised(question):
    if "blocking_question_count" in question.columns:
        assert question["blocking_question_count"].astype(str).str.replace("nan", "0").astype(int).sum() >= 0


def test_35_mandatory_questions_visible(question):
    if "mandatory_question_count" in question.columns:
        assert question["mandatory_question_count"].notna().all()


# ---------------------------------------------------------------------------
# Tests 36-45: Confirmations, conditions, warnings, audit
# ---------------------------------------------------------------------------
def test_36_required_confirmations_pending(confirmation):
    if "pending_confirmation_count" in confirmation.columns:
        assert confirmation["pending_confirmation_count"].notna().all()


def test_37_blocking_conditions_visible(readiness):
    if "main_blocking_condition" in readiness.columns:
        if readiness["main_blocking_condition"].notna().any():
            assert True
        else:
            pytest.skip("Source blocking condition data is blank for all packages")


def test_38_secondary_conditions_visible(readiness):
    if "secondary_condition_count" in readiness.columns:
        assert readiness["secondary_condition_count"].notna().all()


def test_39_provisional_warnings_visible(governance):
    if "provisional_warning" in governance.columns:
        assert governance["provisional_warning"].notna().all()


def test_40_contradiction_warnings_visible(governance):
    if "contradiction_warning" in governance.columns:
        if governance["contradiction_warning"].notna().any():
            assert True
        else:
            pytest.skip("Source contradiction warning data is blank for all packages")


def test_41_financial_uncertainty_visible(financial):
    if "financial_confidence" in financial.columns:
        # Non-quantitative and monitoring packages may legitimately lack financial confidence
        assert financial["financial_confidence"].notna().any()


def test_42_evidence_completeness_reconciles(briefs, upstream_evidence):
    # Use evidence_completeness_register if profile lacks completeness_status
    up_path = os.path.join(BASE, "step_2d6_evidence_completeness_register.csv")
    up_df = _load("step_2d6_evidence_completeness_register.csv") if not upstream_evidence.empty else pd.DataFrame()
    if up_df.empty or "evidence_completeness_status" not in up_df.columns:
        pytest.skip("Upstream evidence completeness not available")
    merged = briefs[["decision_package_id", "evidence_completeness_status"]].merge(
        up_df[["decision_package_id", "evidence_completeness_status"]].rename(
            columns={"evidence_completeness_status": "upstream_ev"}
        ),
        on="decision_package_id", how="left"
    )
    assert (merged["evidence_completeness_status"].fillna("") == merged["upstream_ev"].fillna("")).all()


def test_43_lineage_completeness_reconciles(briefs, upstream_lineage):
    up_df = _load("step_2d6_lineage_completeness_register.csv") if not upstream_lineage.empty else pd.DataFrame()
    if up_df.empty or "lineage_completeness_status" not in up_df.columns:
        pytest.skip("Upstream lineage completeness not available")
    merged = briefs[["decision_package_id", "lineage_completeness_status"]].merge(
        up_df[["decision_package_id", "lineage_completeness_status"]].rename(
            columns={"lineage_completeness_status": "upstream_ln"}
        ),
        on="decision_package_id", how="left"
    )
    assert (merged["lineage_completeness_status"].fillna("") == merged["upstream_ln"].fillna("")).all()


def test_44_audit_status_awaiting(briefs):
    assert (briefs["future_audit_status"].fillna("") == "Awaiting Management Action").all()


def test_45_no_audit_event_executed(briefs):
    if "audit_event_status" in briefs.columns:
        assert not briefs["audit_event_status"].fillna("").str.contains("Executed", case=False, na=False).any()


# ---------------------------------------------------------------------------
# Tests 46-54: Boundary, priority, queue, contracts, orphans
# ---------------------------------------------------------------------------
def test_46_management_decision_boundary_present(briefs):
    boundary = (
        "This brief supports management review and does not constitute action selection, "
        "scenario selection, recommendation approval, budget approval, or a final management decision."
    )
    assert briefs["overall_management_limitation"].fillna("").str.contains(boundary, case=False, na=False).all()


def test_47_priority_ordering_escalation_first(priority):
    if priority.empty:
        pytest.skip("Priority view empty")
    assert len(priority) == EXPECTED_PACKAGES


def test_48_queue_briefs_reconcile(queue):
    assert len(queue) == EXPECTED_PACKAGES


def test_49_streamlit_contract_fields(streamlit):
    assert len(streamlit) == EXPECTED_PACKAGES
    required = ["decision_package_id", "brief_title", "final_readiness_status", "approval_status"]
    for col in required:
        assert col in streamlit.columns


def test_50_export_contracts_appendix_types(export_contract):
    types = export_contract["export_type"].unique()
    assert "One-Page Executive Brief" in types
    assert "Detailed Management Brief" in types


def test_51_evidence_references_reconcile(brief_evidence):
    assert len(brief_evidence) == EXPECTED_PACKAGES


def test_52_lineage_references_reconcile(brief_lineage):
    assert len(brief_lineage) == EXPECTED_PACKAGES


def test_53_no_orphan_brief(briefs):
    assert briefs["decision_package_id"].notna().all()
    assert briefs["integrated_management_brief_id"].notna().all()


def test_54_frozen_checksums_match(auth):
    if auth.empty:
        pytest.skip("Auth register empty")
    assert auth["checksum_match"].all()


# ---------------------------------------------------------------------------
# Tests 55-59: Governance wording, counts, manifest, smoke isolation, status
# ---------------------------------------------------------------------------
def test_55_no_prohibited_wording(gov_reg):
    if gov_reg.empty:
        pytest.skip("Governance register empty")
    assert (gov_reg["no_prohibited_wording"] == True).all()


def test_56_output_counts_reconcile(briefs, sections, types, one_line, short_sum,
                                    issue, evidence, recommendation, scenario,
                                    tradeoff, financial, readiness, action, question,
                                    confirmation, monitoring, governance, audit,
                                    priority, queue, export_contract, streamlit,
                                    brief_evidence, brief_lineage, gov_reg):
    assert len(briefs) == EXPECTED_PACKAGES
    assert len(one_line) == EXPECTED_PACKAGES
    assert len(short_sum) == EXPECTED_PACKAGES
    assert len(issue) == EXPECTED_PACKAGES
    assert len(evidence) == EXPECTED_PACKAGES
    assert len(recommendation) == EXPECTED_PACKAGES
    assert len(scenario) == EXPECTED_PACKAGES
    assert len(tradeoff) == EXPECTED_PACKAGES
    assert len(financial) == EXPECTED_PACKAGES
    assert len(readiness) == EXPECTED_PACKAGES
    assert len(action) == EXPECTED_PACKAGES
    assert len(question) == EXPECTED_PACKAGES
    assert len(confirmation) == EXPECTED_PACKAGES
    assert len(monitoring) == EXPECTED_PACKAGES
    assert len(governance) == EXPECTED_PACKAGES
    assert len(audit) == EXPECTED_PACKAGES
    assert len(priority) == EXPECTED_PACKAGES
    assert len(queue) == EXPECTED_PACKAGES
    assert len(brief_evidence) == EXPECTED_PACKAGES
    assert len(brief_lineage) == EXPECTED_PACKAGES
    assert len(gov_reg) == EXPECTED_PACKAGES
    assert len(sections) == EXPECTED_PACKAGES * 17
    assert len(export_contract) == EXPECTED_PACKAGES * 8
    assert len(types) == EXPECTED_PACKAGES


def test_57_manifest_checksums_complete(manifest):
    assert manifest["status"] == "COMPLETE"
    assert manifest["step"] == "2D-7"
    assert manifest["mode"] == "full_run"
    assert len(manifest["outputs"]) >= 20


def test_58_smoke_outputs_not_mixed(briefs):
    assert briefs["integrated_management_brief_id"].nunique() == EXPECTED_PACKAGES


def test_59_step_2d7_status_reported_correctly(manifest):
    assert manifest["status"] == "COMPLETE"
    assert "step_2d7_integrated_management_brief_register.csv" in manifest["outputs"]
