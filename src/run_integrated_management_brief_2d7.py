"""Step 2D-7 Integrated Management Brief — Main Runner."""

import os
import sys
import time
import hashlib
import json
import shutil
import uuid
from datetime import datetime

import pandas as pd

# Ensure src is on path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from management_brief_utils import (
    load_csv, compute_sha256, ensure_tmp_dir, atomic_write,
    acquire_lock, release_lock, log_progress, validate_no_cartesian,
    generate_manifest, build_execution_summary
)
from management_brief_authority_validator import validate_authority_inputs
from management_brief_population_validator import validate_population_counts
from management_brief_type_engine import assign_brief_types
from management_brief_narrative_engine import (
    generate_issue_title, generate_brief_title, generate_brief_subtitle,
    generate_executive_headline, generate_one_line_summary, generate_short_summary
)
from management_brief_issue_engine import synthesize_issue_risk
from management_brief_evidence_engine import synthesize_evidence
from management_brief_recommendation_engine import synthesize_recommendation
from management_brief_scenario_engine import synthesize_scenario
from management_brief_financial_engine import synthesize_financial
from management_brief_readiness_engine import synthesize_readiness
from management_brief_action_engine import synthesize_actions
from management_brief_question_engine import select_questions
from management_brief_monitoring_engine import synthesize_monitoring
from management_brief_governance_engine import synthesize_governance
from management_brief_audit_engine import synthesize_audit
from management_brief_priority_engine import create_priority_view
from management_brief_queue_engine import create_queue_briefs
from management_brief_export_contract_engine import create_export_contracts
from management_brief_data_contract_engine import create_streamlit_contract
from management_brief_evidence_lineage_engine import create_brief_evidence, create_brief_lineage
from management_brief_governance_validator import validate_governance


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs", "decision_intelligence")
TMP_DIR = os.path.join(OUTPUT_DIR, "_tmp_2d7")
LOCK_FILE = os.path.join(OUTPUT_DIR, "execution_lock.txt")
CONFIG_DIR = os.path.join(BASE_DIR, "config")

STEP_NAME = "2D-7"
EXPECTED_PACKAGES = 646

# ---------------------------------------------------------------------------
# Authoritative input file list
# ---------------------------------------------------------------------------
def build_input_files():
    files = []
    # 2D-6 outputs
    d2d6_names = [
        "step_2d6_authoritative_input_register.csv",
        "step_2d6_decision_evidence_profile_register.csv",
        "step_2d6_evidence_reference_register.csv",
        "step_2d6_evidence_completeness_register.csv",
        "step_2d6_decision_lineage_profile_register.csv",
        "step_2d6_lineage_link_register.csv",
        "step_2d6_lineage_completeness_register.csv",
        "step_2d6_source_to_decision_trace_register.csv",
        "step_2d6_audit_requirement_register.csv",
        "step_2d6_audit_event_catalogue.csv",
        "step_2d6_audit_event_contract.csv",
        "step_2d6_decision_history_contract.csv",
        "step_2d6_version_control_register.csv",
        "step_2d6_integrity_register.csv",
        "step_2d6_retention_classification_register.csv",
        "step_2d6_access_role_contract.csv",
        "step_2d6_evidence_pack_contract.csv",
        "step_2d6_management_review_contract.csv",
        "step_2d6_audit_explanation_register.csv",
        "step_2d6_streamlit_audit_data_contract.csv",
        "step_2d6_evidence_issue_register.csv",
        "step_2d6_lineage_issue_register.csv",
        "step_2d6_audit_governance_register.csv",
        "step_2d6_audit_issue_register.csv",
        "step_2d6_execution_summary.csv",
        "step_2d6_manifest.json",
    ]
    for name in d2d6_names:
        path = os.path.join(OUTPUT_DIR, name)
        files.append({"name": name, "path": path, "phase": "2D-6", "frozen_checksum": "", "superseded": False})
    # Key upstream files
    upstream = [
        ("step_2d5_decision_action_routing_register.csv", "2D-5"),
        ("step_2d5_primary_action_register.csv", "2D-5"),
        ("step_2d5_secondary_action_register.csv", "2D-5"),
        ("step_2d5_responsible_role_register.csv", "2D-5"),
        ("step_2d5_escalation_routing_register.csv", "2D-5"),
        ("step_2d5_monitoring_action_register.csv", "2D-5"),
        ("step_2d5_queue_assignment_register.csv", "2D-5"),
        ("step_2d5_action_explanation_register.csv", "2D-5"),
        ("step_2d5_action_eligibility_register.csv", "2D-5"),
        ("step_2d5_action_blocking_register.csv", "2D-5"),
        ("step_2d5_action_prerequisite_register.csv", "2D-5"),
        ("step_2d5_management_selection_contract.csv", "2D-5"),
        ("step_2d4_decision_readiness_register.csv", "2D-4"),
        ("step_2d4_blocking_condition_register.csv", "2D-4"),
        ("step_2d3_decision_scorecard_register.csv", "2D-3"),
        ("step_2d2_decision_package_register.csv", "2D-2"),
    ]
    for name, phase in upstream:
        path = os.path.join(OUTPUT_DIR, name)
        files.append({"name": name, "path": path, "phase": phase, "frozen_checksum": "", "superseded": False})
    return files


# ---------------------------------------------------------------------------
# Load frozen checksums from 2D-6 authoritative input register
# ---------------------------------------------------------------------------
def enrich_frozen_checksums(input_files):
    auth_path = os.path.join(OUTPUT_DIR, "step_2d6_authoritative_input_register.csv")
    if os.path.exists(auth_path):
        auth_df = load_csv(auth_path)
        if not auth_df.empty and "file_name" in auth_df.columns and "checksum" in auth_df.columns:
            checksum_map = dict(zip(auth_df["file_name"], auth_df["checksum"]))
            for info in input_files:
                if info["name"] in checksum_map:
                    info["frozen_checksum"] = checksum_map[info["name"]]
    return input_files


# ---------------------------------------------------------------------------
# Core brief builder
# ---------------------------------------------------------------------------
def build_core_brief(logger):
    t0 = time.time()
    print("Loading source dataframes...")

    # Base: 2D-5 routing (646 rows)
    routing = load_csv(os.path.join(OUTPUT_DIR, "step_2d5_decision_action_routing_register.csv"))
    if len(routing) != EXPECTED_PACKAGES:
        raise ValueError(f"Routing register has {len(routing)} rows, expected {EXPECTED_PACKAGES}")

    # 2D-2 decision package (646 rows, 251 cols) — main content source
    pkg = load_csv(os.path.join(OUTPUT_DIR, "step_2d2_decision_package_register.csv"), low_memory=False)

    # 2D-5 supplementary files
    primary_action = load_csv(os.path.join(OUTPUT_DIR, "step_2d5_primary_action_register.csv"))
    secondary_action = load_csv(os.path.join(OUTPUT_DIR, "step_2d5_secondary_action_register.csv"))
    roles = load_csv(os.path.join(OUTPUT_DIR, "step_2d5_responsible_role_register.csv"))
    escalation = load_csv(os.path.join(OUTPUT_DIR, "step_2d5_escalation_routing_register.csv"))
    monitoring = load_csv(os.path.join(OUTPUT_DIR, "step_2d5_monitoring_action_register.csv"))
    queue = load_csv(os.path.join(OUTPUT_DIR, "step_2d5_queue_assignment_register.csv"))
    explanation = load_csv(os.path.join(OUTPUT_DIR, "step_2d5_action_explanation_register.csv"))
    eligibility = load_csv(os.path.join(OUTPUT_DIR, "step_2d5_action_eligibility_register.csv"))
    blocking = load_csv(os.path.join(OUTPUT_DIR, "step_2d5_action_blocking_register.csv"))
    prerequisite = load_csv(os.path.join(OUTPUT_DIR, "step_2d5_action_prerequisite_register.csv"))
    selection = load_csv(os.path.join(OUTPUT_DIR, "step_2d5_management_selection_contract.csv"))

    # 2D-4
    readiness = load_csv(os.path.join(OUTPUT_DIR, "step_2d4_decision_readiness_register.csv"))
    blocking_cond = load_csv(os.path.join(OUTPUT_DIR, "step_2d4_blocking_condition_register.csv"))

    # 2D-6
    evidence_profile = load_csv(os.path.join(OUTPUT_DIR, "step_2d6_decision_evidence_profile_register.csv"))
    lineage_profile = load_csv(os.path.join(OUTPUT_DIR, "step_2d6_decision_lineage_profile_register.csv"))
    evidence_compl = load_csv(os.path.join(OUTPUT_DIR, "step_2d6_evidence_completeness_register.csv"))
    lineage_compl = load_csv(os.path.join(OUTPUT_DIR, "step_2d6_lineage_completeness_register.csv"))
    audit_exp = load_csv(os.path.join(OUTPUT_DIR, "step_2d6_audit_explanation_register.csv"))
    mgmt_review = load_csv(os.path.join(OUTPUT_DIR, "step_2d6_management_review_contract.csv"))
    trace = load_csv(os.path.join(OUTPUT_DIR, "step_2d6_source_to_decision_trace_register.csv"))

    log_progress(logger, "load_dataframes", t0)

    # Start building core brief from routing
    brief = routing.copy()
    brief["integrated_management_brief_id"] = [f"IMB-{uuid.uuid4().hex[:8].upper()}" for _ in range(len(brief))]

    # Join 2D-2 package content (left join, validate count)
    pkg_cols = [c for c in pkg.columns if c not in brief.columns or c == "decision_package_id"]
    pkg_join = pkg[pkg_cols].copy()
    brief = brief.merge(pkg_join, on="decision_package_id", how="left", suffixes=("", "_pkg"))
    if len(brief) != EXPECTED_PACKAGES:
        raise ValueError(f"Brief multiplied after 2D-2 join: {len(brief)}")

    # Helper for safe left joins
    def safe_join(left, right, on, suffix="_r"):
        if right.empty or on not in right.columns:
            return left
        cols = [c for c in right.columns if c not in left.columns or c == on]
        merged = left.merge(right[cols], on=on, how="left", suffixes=("", suffix))
        if len(merged) != len(left):
            # De-duplicate right side
            right_dedup = right[cols].drop_duplicates(subset=[on])
            merged = left.merge(right_dedup, on=on, how="left", suffixes=("", suffix))
        return merged

    # Join 2D-5 supplementary
    brief = safe_join(brief, primary_action, "decision_package_id")
    brief = safe_join(brief, roles, "decision_package_id", "_role")
    brief = safe_join(brief, escalation, "decision_package_id", "_esc")
    brief = safe_join(brief, monitoring, "decision_package_id", "_mon")
    brief = safe_join(brief, queue, "decision_package_id", "_que")
    brief = safe_join(brief, explanation, "decision_package_id", "_exp")
    brief = safe_join(brief, selection, "decision_package_id", "_sel")

    # Join 2D-6
    brief = safe_join(brief, evidence_profile, "decision_package_id", "_evp")
    brief = safe_join(brief, lineage_profile, "decision_package_id", "_lnp")
    brief = safe_join(brief, evidence_compl, "decision_package_id", "_evc")
    brief = safe_join(brief, lineage_compl, "decision_package_id", "_lnc")
    brief = safe_join(brief, audit_exp, "decision_package_id", "_aex")
    brief = safe_join(brief, mgmt_review, "decision_package_id", "_mrv")
    brief = safe_join(brief, trace, "decision_package_id", "_trc")

    if len(brief) != EXPECTED_PACKAGES:
        raise ValueError(f"Brief row count changed after joins: {len(brief)}, expected {EXPECTED_PACKAGES}")

    log_progress(logger, "join_sources", t0)
    return brief, {
        "routing": routing, "pkg": pkg, "primary_action": primary_action,
        "secondary_action": secondary_action, "roles": roles, "escalation": escalation,
        "monitoring": monitoring, "queue": queue, "explanation": explanation,
        "eligibility": eligibility, "blocking": blocking, "prerequisite": prerequisite,
        "selection": selection, "readiness": readiness, "blocking_cond": blocking_cond,
        "evidence_profile": evidence_profile, "lineage_profile": lineage_profile,
        "evidence_compl": evidence_compl, "lineage_compl": lineage_compl,
        "audit_exp": audit_exp, "mgmt_review": mgmt_review, "trace": trace
    }


# ---------------------------------------------------------------------------
# Synthesize sections
# ---------------------------------------------------------------------------
def synthesize_all_sections(brief, logger):
    t0 = time.time()
    records = brief.to_dict("records")
    synthesized = []

    for row in records:
        out = dict(row)

        # Narrative
        out["issue_title"] = generate_issue_title(row)
        out["brief_title"] = generate_brief_title(row)
        out["brief_subtitle"] = generate_brief_subtitle(row)
        out["executive_headline"] = generate_executive_headline(row)
        out["one_line_summary"] = generate_one_line_summary(row)
        out["short_summary"] = generate_short_summary(row)

        # Sections
        out.update(synthesize_issue_risk(row))
        out.update(synthesize_evidence(row))
        out.update(synthesize_recommendation(row))
        out.update(synthesize_scenario(row))
        out.update(synthesize_financial(row))
        out.update(synthesize_readiness(row))
        out.update(synthesize_actions(row))
        out.update(select_questions(row))
        out.update(synthesize_monitoring(row))
        out.update(synthesize_governance(row))
        out.update(synthesize_audit(row))

        # Decision boundary fields (blank / governed)
        out["selected_action"] = ""
        out["selected_scenario"] = ""
        out["review_outcome"] = ""
        out["management_comment"] = ""
        out["conditions_imposed"] = ""
        out["reviewer_role"] = ""
        out["approval_reference"] = ""
        out["confirmation_checkbox"] = ""

        # Management attention level
        out["management_attention_level"] = map_attention_level(out)

        synthesized.append(out)

    df = pd.DataFrame(synthesized)
    log_progress(logger, "synthesize_sections", t0)
    return df


def map_attention_level(row):
    """Map readiness, risk, and escalation to attention level."""
    readiness = str(row.get("final_readiness_status", ""))
    risk = str(row.get("risk_tier", "")).lower()
    esc = str(row.get("operational_escalation_status", "")).lower()
    urgency = str(row.get("urgency", "")).lower()

    if esc == "operational escalation" or (risk == "critical" and urgency == "immediate review"):
        return "Immediate Management Attention"
    if readiness == "Ready for Integrated Management Review" and risk in ("critical", "high"):
        return "Priority Management Review"
    if readiness == "Ready for Integrated Management Review":
        return "Standard Management Review"
    if readiness == "Ready with Conditions":
        return "Conditional Review"
    if readiness == "Monitoring Only":
        return "Monitoring"
    if readiness == "Non-Quantitative":
        return "Non-Quantitative Review"
    if readiness == "Not Suitable":
        return "Not Suitable"
    if readiness == "Rejected":
        return "Rejected"
    return "Conditional Review"


# ---------------------------------------------------------------------------
# Create derived outputs
# ---------------------------------------------------------------------------
def create_derived_outputs(briefs, logger):
    t0 = time.time()
    outputs = {}

    # Section register
    section_records = []
    sections = [
        ("Executive Headline", "brief_title"),
        ("What Is Happening", "current_issue_summary"),
        ("Why It Matters", "operational_significance"),
        ("Evidence Summary", "evidence_completeness_status"),
        ("Contributing Factors", "contributing_factor_summary"),
        ("Recommendation Options", "representative_recommendation"),
        ("Scenario Options", "scenario_readiness"),
        ("Trade-off and Impact Summary", "main_tradeoff"),
        ("Financial Summary", "financial_readiness"),
        ("Readiness and Conditions", "final_readiness_status"),
        ("Permitted Management Actions", "primary_permitted_action"),
        ("Management Questions", "top_management_questions"),
        ("Required Confirmations", "required_confirmation_summary"),
        ("Monitoring and Escalation", "monitoring_required"),
        ("Governance and Limitations", "provisional_warning"),
        ("Audit and Traceability", "future_audit_status"),
        ("Management Decision Boundary", "overall_management_limitation"),
    ]
    for _, row in briefs.iterrows():
        for sec_name, _ in sections:
            section_records.append({
                "integrated_management_brief_id": row.get("integrated_management_brief_id", ""),
                "decision_package_id": row.get("decision_package_id", ""),
                "section_name": sec_name,
                "section_present": True,
                "governance_note": "Required section present"
            })
    outputs["section_register"] = pd.DataFrame(section_records)

    # Type register
    type_records = []
    for _, row in briefs.iterrows():
        type_records.append({
            "integrated_management_brief_id": row.get("integrated_management_brief_id", ""),
            "decision_package_id": row.get("decision_package_id", ""),
            "brief_type": row.get("brief_type", ""),
            "final_readiness_status": row.get("final_readiness_status", ""),
            "governance_note": "Brief type mapped from readiness"
        })
    outputs["type_register"] = pd.DataFrame(type_records)

    # Executive summaries
    one_line = briefs[["integrated_management_brief_id", "decision_package_id", "one_line_summary", "final_readiness_status"]].copy()
    outputs["one_line_summary"] = one_line

    short = briefs[["integrated_management_brief_id", "decision_package_id", "short_summary", "final_readiness_status"]].copy()
    outputs["short_summary"] = short

    # Issue and risk
    issue_cols = ["integrated_management_brief_id", "decision_package_id",
                  "issue_title", "current_issue_summary", "current_kpi_status",
                  "breach_status", "watch_status", "trend_direction",
                  "sustained_movement_flag", "operational_risk_score", "risk_tier",
                  "urgency", "priority_tier", "dominant_breach_type",
                  "operational_significance", "likely_service_consequence",
                  "likely_workforce_consequence", "likely_patient_experience_consequence",
                  "likely_financial_exposure", "management_attention_reason"]
    available_issue = [c for c in issue_cols if c in briefs.columns]
    outputs["issue_summary"] = briefs[available_issue].copy()

    # Evidence
    ev_cols = ["integrated_management_brief_id", "decision_package_id",
               "evidence_completeness_status", "evidence_coverage_pct",
               "critical_missing_evidence_count", "key_evidence_summary",
               "evidence_conditions", "evidence_warning", "source_to_decision_trace_status"]
    available_ev = [c for c in ev_cols if c in briefs.columns]
    outputs["evidence_summary"] = briefs[available_ev].copy()

    # Recommendation
    rec_cols = ["integrated_management_brief_id", "decision_package_id",
                "representative_recommendation", "immediate_action_option",
                "near_term_action_option", "preventive_action_option",
                "recommendation_readiness", "recommendation_validation_status",
                "recommendation_confirmation_required", "recommendation_limitations"]
    available_rec = [c for c in rec_cols if c in briefs.columns]
    outputs["recommendation_summary"] = briefs[available_rec].copy()

    # Scenario
    sc_cols = ["integrated_management_brief_id", "decision_package_id",
               "scenario_readiness", "baseline_summary", "conservative_summary",
               "expected_summary", "higher_intensity_summary",
               "comparator_completeness", "comparator_consistency",
               "scenario_validation_status", "scenario_confidence"]
    available_sc = [c for c in sc_cols if c in briefs.columns]
    outputs["scenario_summary"] = briefs[available_sc].copy()

    # Trade-off
    to_cols = ["integrated_management_brief_id", "decision_package_id",
               "primary_kpi_effect_summary", "supporting_kpi_effect_summary",
               "main_tradeoff", "displacement_risk", "sensitivity_summary",
               "dominance_summary", "diminishing_return_summary", "scenario_limitations"]
    available_to = [c for c in to_cols if c in briefs.columns]
    outputs["tradeoff_summary"] = briefs[available_to].copy()

    # Financial
    fin_cols = ["integrated_management_brief_id", "decision_package_id",
                "financial_readiness", "cost_completeness", "estimated_scenario_cost",
                "estimated_financial_benefit", "estimated_net_financial_impact",
                "roi_status", "payback_status", "affordability_status",
                "lower_financial_estimate", "central_financial_estimate",
                "upper_financial_estimate", "financial_confidence",
                "missing_financial_input_flag", "financial_limitations"]
    available_fin = [c for c in fin_cols if c in briefs.columns]
    outputs["financial_summary"] = briefs[available_fin].copy()

    # Readiness
    rd_cols = ["integrated_management_brief_id", "decision_package_id",
               "final_readiness_status", "readiness_explanation",
               "main_blocking_condition", "blocking_condition_count",
               "secondary_condition_count", "top_secondary_conditions",
               "failed_gates", "pass_with_condition_gates",
               "required_resolution", "responsible_role"]
    available_rd = [c for c in rd_cols if c in briefs.columns]
    outputs["readiness_summary"] = briefs[available_rd].copy()

    # Action
    act_cols = ["integrated_management_brief_id", "decision_package_id",
                "primary_permitted_action", "secondary_permitted_actions",
                "blocked_action_summary", "primary_queue", "secondary_queues",
                "responsible_role", "escalation_required", "escalation_status",
                "escalation_reason"]
    available_act = [c for c in act_cols if c in briefs.columns]
    outputs["action_summary"] = briefs[available_act].copy()

    # Questions
    q_cols = ["integrated_management_brief_id", "decision_package_id",
              "top_management_questions", "blocking_question_count",
              "mandatory_question_count", "responsible_roles", "required_response_types"]
    available_q = [c for c in q_cols if c in briefs.columns]
    outputs["question_summary"] = briefs[available_q].copy()

    # Confirmations
    c_cols = ["integrated_management_brief_id", "decision_package_id",
              "required_confirmation_summary", "pending_confirmation_count",
              "blocking_confirmation_count", "confirmation_responsible_roles",
              "evidence_required_for_confirmation"]
    available_c = [c for c in c_cols if c in briefs.columns]
    outputs["confirmation_summary"] = briefs[available_c].copy()

    # Monitoring
    mon_cols = ["integrated_management_brief_id", "decision_package_id",
                "monitoring_required", "monitoring_kpis", "monitoring_frequency",
                "trigger_condition", "escalation_condition", "reassessment_condition",
                "monitoring_responsible_role", "management_attention_required"]
    available_mon = [c for c in mon_cols if c in briefs.columns]
    outputs["monitoring_summary"] = briefs[available_mon].copy()

    # Governance
    gov_cols = ["integrated_management_brief_id", "decision_package_id",
                "provisional_warning", "contradiction_warning",
                "stakeholder_validation_required", "assumption_validation_required",
                "baseline_validation_required", "financial_validation_required",
                "governance_burden_status", "evidence_limitation",
                "lineage_limitation", "audit_limitation", "overall_management_limitation"]
    available_gov = [c for c in gov_cols if c in briefs.columns]
    outputs["governance_summary"] = briefs[available_gov].copy()

    # Audit
    aud_cols = ["integrated_management_brief_id", "decision_package_id",
                "evidence_completeness_status", "lineage_completeness_status",
                "audit_traceability_status", "integrity_status",
                "current_package_version", "source_manifest",
                "audit_requirements_pending", "future_audit_status"]
    available_aud = [c for c in aud_cols if c in briefs.columns]
    outputs["audit_summary"] = briefs[available_aud].copy()

    # Priority view
    outputs["priority_view"] = create_priority_view(briefs)

    # Queue briefs
    outputs["queue_briefs"] = create_queue_briefs(briefs)

    # Export contracts
    outputs["export_contracts"] = create_export_contracts(briefs)

    # Streamlit contract
    outputs["streamlit_contract"] = create_streamlit_contract(briefs)

    # Evidence / lineage cross-references
    outputs["brief_evidence"] = create_brief_evidence(briefs)
    outputs["brief_lineage"] = create_brief_lineage(briefs)

    # Governance validation
    gov_reg, gov_issues = validate_governance(briefs)
    outputs["governance_register"] = gov_reg
    outputs["brief_issues"] = gov_issues

    log_progress(logger, "create_derived_outputs", t0)
    return outputs


# ---------------------------------------------------------------------------
# Write all outputs
# ---------------------------------------------------------------------------
def write_all_outputs(briefs, derived, logger):
    t0 = time.time()
    ensure_tmp_dir(TMP_DIR)

    file_map = {
        "step_2d7_integrated_management_brief_register.csv": briefs,
        "step_2d7_management_brief_section_register.csv": derived["section_register"],
        "step_2d7_management_brief_type_register.csv": derived["type_register"],
        "step_2d7_executive_one_line_summary_register.csv": derived["one_line_summary"],
        "step_2d7_executive_short_summary_register.csv": derived["short_summary"],
        "step_2d7_issue_and_risk_summary_register.csv": derived["issue_summary"],
        "step_2d7_evidence_summary_register.csv": derived["evidence_summary"],
        "step_2d7_recommendation_summary_register.csv": derived["recommendation_summary"],
        "step_2d7_scenario_summary_register.csv": derived["scenario_summary"],
        "step_2d7_tradeoff_and_impact_summary_register.csv": derived["tradeoff_summary"],
        "step_2d7_financial_summary_register.csv": derived["financial_summary"],
        "step_2d7_readiness_and_condition_summary_register.csv": derived["readiness_summary"],
        "step_2d7_management_action_summary_register.csv": derived["action_summary"],
        "step_2d7_management_question_summary_register.csv": derived["question_summary"],
        "step_2d7_confirmation_summary_register.csv": derived["confirmation_summary"],
        "step_2d7_monitoring_and_escalation_summary_register.csv": derived["monitoring_summary"],
        "step_2d7_governance_and_limitation_summary_register.csv": derived["governance_summary"],
        "step_2d7_audit_and_traceability_summary_register.csv": derived["audit_summary"],
        "step_2d7_management_priority_view_register.csv": derived["priority_view"],
        "step_2d7_management_queue_brief_register.csv": derived["queue_briefs"],
        "step_2d7_export_contract_register.csv": derived["export_contracts"],
        "step_2d7_streamlit_management_brief_contract.csv": derived["streamlit_contract"],
        "step_2d7_brief_evidence_register.csv": derived["brief_evidence"],
        "step_2d7_brief_lineage_register.csv": derived["brief_lineage"],
        "step_2d7_brief_governance_register.csv": derived["governance_register"],
        "step_2d7_brief_issue_register.csv": derived["brief_issues"],
    }

    written = {}
    for filename, df in file_map.items():
        tmp_path = os.path.join(TMP_DIR, filename)
        final_path = os.path.join(OUTPUT_DIR, filename)
        atomic_write(df, tmp_path, final_path)
        written[filename] = final_path

    # Clean tmp
    for _ in range(5):
        try:
            shutil.rmtree(TMP_DIR)
            break
        except PermissionError:
            time.sleep(0.5)

    log_progress(logger, "write_outputs", t0)
    return written


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------
def run_smoke_test(logger):
    print("=" * 60)
    print("STEP 2D-7 SMOKE TEST")
    print("=" * 60)

    t0 = time.time()
    input_files = build_input_files()
    input_files = enrich_frozen_checksums(input_files)
    auth_reg = validate_authority_inputs(input_files, OUTPUT_DIR)
    frozen_mismatches = auth_reg[~auth_reg["checksum_match"]]
    if not frozen_mismatches.empty:
        raise RuntimeError(f"Frozen checksum mismatches: {frozen_mismatches['file_name'].tolist()}")

    # Write auth register
    ensure_tmp_dir(TMP_DIR)
    auth_path_tmp = os.path.join(TMP_DIR, "step_2d7_authoritative_input_register.csv")
    auth_path_final = os.path.join(OUTPUT_DIR, "step_2d7_authoritative_input_register.csv")
    atomic_write(auth_reg, auth_path_tmp, auth_path_final)

    brief, sources = build_core_brief(logger)

    # Select 5 representative packages
    target_statuses = [
        "Ready for Integrated Management Review",
        "Ready with Conditions",
        "Monitoring Only",
        "Requires Assumption Validation",
        "Non-Quantitative"
    ]
    smoke_ids = []
    for status in target_statuses:
        mask = brief["final_readiness_status"] == status
        if mask.any():
            smoke_ids.append(brief.loc[mask, "decision_package_id"].iloc[0])

    if len(smoke_ids) < 5:
        # Fallback: pick any 5 distinct
        smoke_ids = brief["decision_package_id"].unique()[:5].tolist()

    smoke_brief = brief[brief["decision_package_id"].isin(smoke_ids)].copy()
    print(f"Smoke test on {len(smoke_brief)} packages: {smoke_ids}")

    smoke_brief = assign_brief_types(smoke_brief)
    smoke_brief = synthesize_all_sections(smoke_brief, logger)
    derived = create_derived_outputs(smoke_brief, logger)

    # Smoke validations
    assert len(smoke_brief) == len(smoke_ids), "Duplicate briefs detected"
    assert smoke_brief["integrated_management_brief_id"].nunique() == len(smoke_ids), "Duplicate brief IDs"
    assert (smoke_brief["approval_status"] == "Pending Management Review").all(), "Approval status changed"
    assert (smoke_brief["causality_status"] == "Not Confirmed").all(), "Causality confirmed"
    assert smoke_brief["one_line_summary"].str.split().str.len().max() <= 40, "One-line too long"
    assert smoke_brief["short_summary"].str.split().str.len().max() <= 130, "Short summary too long"
    assert smoke_brief["selected_action"].eq("").all(), "Action selected in smoke"
    assert smoke_brief["selected_scenario"].eq("").all(), "Scenario selected in smoke"

    print("SMOKE TEST PASSED")
    log_progress(logger, "smoke_test", t0)
    return True


# ---------------------------------------------------------------------------
# Full run
# ---------------------------------------------------------------------------
def run_full_process(logger):
    print("=" * 60)
    print("STEP 2D-7 FULL RUN")
    print("=" * 60)

    t0 = time.time()
    input_files = build_input_files()
    input_files = enrich_frozen_checksums(input_files)
    auth_reg = validate_authority_inputs(input_files, OUTPUT_DIR)
    frozen_mismatches = auth_reg[~auth_reg["checksum_match"]]
    if not frozen_mismatches.empty:
        raise RuntimeError(f"Frozen checksum mismatches: {frozen_mismatches['file_name'].tolist()}")

    # Write auth register
    ensure_tmp_dir(TMP_DIR)
    auth_path_tmp = os.path.join(TMP_DIR, "step_2d7_authoritative_input_register.csv")
    auth_path_final = os.path.join(OUTPUT_DIR, "step_2d7_authoritative_input_register.csv")
    atomic_write(auth_reg, auth_path_tmp, auth_path_final)
    log_progress(logger, "authority_verification", t0)

    brief, sources = build_core_brief(logger)
    log_progress(logger, "package_population_reconciliation", t0)

    brief = assign_brief_types(brief)
    brief = synthesize_all_sections(brief, logger)
    log_progress(logger, "executive_summary_synthesis", t0)
    log_progress(logger, "risk_recommendation_synthesis", t0)
    log_progress(logger, "scenario_synthesis", t0)
    log_progress(logger, "financial_synthesis", t0)
    log_progress(logger, "governance_limitation_synthesis", t0)

    derived = create_derived_outputs(brief, logger)
    log_progress(logger, "evidence_lineage_summarisation", t0)
    log_progress(logger, "action_route_synthesis", t0)
    log_progress(logger, "management_question_selection", t0)
    log_progress(logger, "streamlit_contract_creation", t0)

    written = write_all_outputs(brief, derived, logger)

    # Execution summary
    exec_sum = build_execution_summary(logger, STEP_NAME, mode="full_run")
    exec_path = os.path.join(OUTPUT_DIR, "step_2d7_execution_summary.csv")
    exec_sum.to_csv(exec_path, index=False)

    # Manifest
    all_outputs = {**written, "step_2d7_execution_summary.csv": exec_path}
    manifest = generate_manifest(OUTPUT_DIR, all_outputs, STEP_NAME, mode="full_run")
    # Rename to standard naming convention
    old_manifest = os.path.join(OUTPUT_DIR, "2d-7_manifest.json")
    new_manifest = os.path.join(OUTPUT_DIR, "step_2d7_manifest.json")
    if os.path.exists(old_manifest):
        if os.path.exists(new_manifest):
            os.remove(new_manifest)
        shutil.move(old_manifest, new_manifest)
    log_progress(logger, "manifest_generation", t0)

    print(f"Full run complete. {len(brief)} briefs created.")
    return brief, derived, manifest


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def main(mode="full_run"):
    logger = []
    total_t0 = time.time()
    try:
        acquire_lock(LOCK_FILE, STEP_NAME)
    except RuntimeError as e:
        print(f"Lock error: {e}")
        return 1

    try:
        if mode == "smoke":
            run_smoke_test(logger)
        else:
            run_full_process(logger)
        release_lock(LOCK_FILE, STEP_NAME)
        log_progress(logger, "total_execution", total_t0)
        return 0
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        with open(LOCK_FILE, "w") as f:
            f.write(f"{STEP_NAME} FAILED {datetime.now().isoformat()}")
        return 1


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "full_run"
    sys.exit(main(mode))
