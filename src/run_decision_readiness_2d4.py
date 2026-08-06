"""
Main runner for Phase 2D-4 Decision-Readiness Classification.

Orchestrates authority validation, readiness classification, gate evaluation,
condition analysis, transition rules, queue mapping, role assignment,
escalation, explanations, data contracts, evidence/lineage reconciliation,
governance validation, output writing, smoke test, and manifest generation.
"""

import os
import sys
import json
import time
import shutil
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(PROJECT_ROOT, "outputs", "decision_intelligence")
OUTPUT_DIR = INPUT_DIR
TMP_DIR = os.path.join(OUTPUT_DIR, "_tmp_2d4")
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
sys.path.insert(0, SRC_DIR)

from decision_readiness_authority_validator import validate_authority
from decision_readiness_population_validator import validate_population
from decision_readiness_rule_engine import build_readiness_register
from decision_readiness_precedence_engine import apply_precedence
from decision_readiness_gate_engine import build_gates
from decision_readiness_blocking_condition_engine import build_blocking_conditions
from decision_readiness_secondary_condition_engine import build_secondary_conditions
from decision_readiness_transition_engine import build_transitions
from decision_readiness_queue_engine import build_queues
from decision_readiness_role_engine import build_roles
from decision_readiness_escalation_engine import build_escalation
from decision_readiness_explanation_engine import build_explanations
from decision_readiness_data_contract_engine import build_streamlit_contracts
from decision_readiness_evidence_lineage_engine import build_evidence, build_lineage
from decision_readiness_governance_validator import validate_readiness

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
LOG = logging.getLogger("run_decision_readiness_2d4")


def compute_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_csv(fname: str) -> pd.DataFrame:
    path = os.path.join(INPUT_DIR, fname)
    if not os.path.exists(path) or os.path.getsize(path) <= 2:
        return pd.DataFrame()
    return pd.read_csv(path)


def save_csv(df: pd.DataFrame, fname: str) -> str:
    path = os.path.join(TMP_DIR, fname)
    df.to_csv(path, index=False)
    return path


def run_smoke_test() -> bool:
    LOG.info("=" * 60)
    LOG.info("SMOKE TEST START")
    LOG.info("=" * 60)

    scorecard_df = load_csv("step_2d3_decision_scorecard_register.csv")
    dimension_df = load_csv("step_2d3_scorecard_dimension_register.csv")

    if scorecard_df.empty or dimension_df.empty:
        LOG.error("Smoke test failed: missing required inputs")
        return False

    # Pick one of each package type
    sample_pkg = scorecard_df[
        scorecard_df["package_status"].isin([
            "Ready with Conditions",
            "Monitoring Only",
            "Requires Assumption Validation",
            "Non-Quantitative",
        ])
    ].groupby("package_status").head(1)

    if len(sample_pkg) < 4:
        LOG.error("Smoke test failed: could not find all 4 required package types")
        return False

    # Build readiness for sample
    sample_ready = build_readiness_register(sample_pkg, dimension_df, logger=LOG)
    sample_ready = apply_precedence(sample_ready, logger=LOG)

    # Validate exactly one status per package
    status_counts = sample_ready.groupby("decision_package_id").size()
    if (status_counts > 1).any():
        LOG.error("Smoke test failed: multiple statuses assigned")
        return False

    # Validate required package statuses are preserved in readiness
    expected_pkg_statuses = {"Ready with Conditions", "Monitoring Only", "Requires Assumption Validation", "Non-Quantitative"}
    actual_pkg_statuses = set(sample_ready["package_status"].unique())
    if not expected_pkg_statuses.issubset(actual_pkg_statuses):
        LOG.error("Smoke test failed: not all expected package statuses present. Got: %s", actual_pkg_statuses)
        return False

    # Validate that readiness classification produced valid statuses
    valid_statuses = {
        "Ready for Integrated Management Review", "Ready with Conditions",
        "Requires Assumption Validation", "Requires Baseline Validation",
        "Requires Financial Input", "Requires Benefit Validation",
        "Requires Budget Data", "Requires Stakeholder Validation",
        "Requires Additional Scenario Analysis", "Requires Evidence Completion",
        "Requires Lineage Completion", "Monitoring Only",
        "Non-Quantitative", "Not Suitable for Decision Use", "Rejected"
    }
    actual_statuses = set(sample_ready["final_readiness_status"].unique())
    if not actual_statuses.issubset(valid_statuses):
        LOG.error("Smoke test failed: invalid readiness statuses found. Got: %s", actual_statuses)
        return False

    # Validate no transitions executed
    sample_trans = build_transitions(sample_ready, logger=LOG)
    if sample_trans["transition_executed"].any():
        LOG.error("Smoke test failed: transitions were executed")
        return False

    # Validate approval status
    if (sample_ready["approval_status"] != "Pending Management Review").any():
        LOG.error("Smoke test failed: approval status not pending")
        return False

    # Validate causality status
    if (sample_ready["causality_status"] != "Not Confirmed").any():
        LOG.error("Smoke test failed: causality status not Not Confirmed")
        return False

    LOG.info("SMOKE TEST PASSED")
    return True


def run_full_process() -> Dict[str, Any]:
    LOG.info("=" * 60)
    LOG.info("STEP 2D-4 FULL PROCESS START")
    LOG.info("=" * 60)

    start_time = time.time()
    summary: Dict[str, Any] = {"step": "2D-4", "start_time": datetime.now().isoformat()}

    # Clean and create temp dir
    if os.path.exists(TMP_DIR):
        shutil.rmtree(TMP_DIR)
    os.makedirs(TMP_DIR, exist_ok=True)

    # 1. Authority validation
    t0 = time.time()
    LOG.info("[1/15] Authority validation")
    auth_df, auth_pass = validate_authority(logger=LOG)
    if not auth_pass:
        LOG.error("Authority validation failed. Stopping.")
        summary["status"] = "FAILED"
        summary["failure_reason"] = "Authority validation failed"
        return summary
    save_csv(auth_df, "step_2d4_authoritative_input_register.csv")
    summary["authority_validation_time"] = round(time.time() - t0, 2)

    # 2. Load inputs
    t0 = time.time()
    LOG.info("[2/15] Loading Step 2D-3 inputs")
    scorecard_df = load_csv("step_2d3_decision_scorecard_register.csv")
    dimension_df = load_csv("step_2d3_scorecard_dimension_register.csv")
    display_df = load_csv("step_2d3_scorecard_display_level_register.csv")
    condition_df = load_csv("step_2d3_scorecard_condition_flag_register.csv")
    evidence_df = load_csv("step_2d3_scorecard_evidence_register.csv")
    lineage_df = load_csv("step_2d3_scorecard_lineage_register.csv")
    LOG.info("Loaded: scorecards=%s, dimensions=%s, conditions=%s", len(scorecard_df), len(dimension_df), len(condition_df))
    summary["input_loading_time"] = round(time.time() - t0, 2)

    # 3. Build readiness register
    t0 = time.time()
    LOG.info("[3/15] Building readiness register")
    readiness_df = build_readiness_register(scorecard_df, dimension_df, logger=LOG)
    readiness_df = apply_precedence(readiness_df, logger=LOG)
    save_csv(readiness_df, "step_2d4_decision_readiness_register.csv")
    summary["readiness_build_time"] = round(time.time() - t0, 2)

    # 4. Population validation
    t0 = time.time()
    LOG.info("[4/15] Population validation")
    pop_ok, pop_msg = validate_population(scorecard_df, readiness_df, logger=LOG)
    if not pop_ok:
        LOG.error("Population validation failed: %s", pop_msg)
        summary["status"] = "FAILED"
        summary["failure_reason"] = pop_msg
        return summary
    summary["population_validation_time"] = round(time.time() - t0, 2)

    # 5. Build gates
    t0 = time.time()
    LOG.info("[5/15] Building readiness gates")
    gate_df = build_gates(readiness_df, dimension_df, logger=LOG)
    save_csv(gate_df, "step_2d4_readiness_gate_register.csv")
    summary["gate_build_time"] = round(time.time() - t0, 2)

    # 6. Build blocking conditions
    t0 = time.time()
    LOG.info("[6/15] Building blocking conditions")
    blocking_df = build_blocking_conditions(readiness_df, condition_df, logger=LOG)
    save_csv(blocking_df, "step_2d4_blocking_condition_register.csv")
    summary["blocking_build_time"] = round(time.time() - t0, 2)

    # 7. Build secondary conditions
    t0 = time.time()
    LOG.info("[7/15] Building secondary conditions")
    secondary_df = build_secondary_conditions(readiness_df, condition_df, logger=LOG)
    save_csv(secondary_df, "step_2d4_secondary_condition_register.csv")
    summary["secondary_build_time"] = round(time.time() - t0, 2)

    # 8. Build transitions
    t0 = time.time()
    LOG.info("[8/15] Building transition rules")
    transition_df = build_transitions(readiness_df, logger=LOG)
    save_csv(transition_df, "step_2d4_readiness_transition_register.csv")
    summary["transition_build_time"] = round(time.time() - t0, 2)

    # 9. Build queues
    t0 = time.time()
    LOG.info("[9/15] Building queue assignments")
    queue_df = build_queues(readiness_df, logger=LOG)
    save_csv(queue_df, "step_2d4_readiness_queue_register.csv")
    summary["queue_build_time"] = round(time.time() - t0, 2)

    # 10. Build roles
    t0 = time.time()
    LOG.info("[10/15] Building responsible roles")
    role_df = build_roles(readiness_df, logger=LOG)
    save_csv(role_df, "step_2d4_responsible_role_register.csv")
    summary["role_build_time"] = round(time.time() - t0, 2)

    # 11. Build escalation
    t0 = time.time()
    LOG.info("[11/15] Building escalation assignments")
    escalation_df = build_escalation(readiness_df, dimension_df, logger=LOG)
    save_csv(escalation_df, "step_2d4_operational_escalation_register.csv")
    summary["escalation_build_time"] = round(time.time() - t0, 2)

    # 12. Build explanations
    t0 = time.time()
    LOG.info("[12/15] Building readiness explanations")
    explanation_df = build_explanations(readiness_df, logger=LOG)
    save_csv(explanation_df, "step_2d4_readiness_explanation_register.csv")
    summary["explanation_build_time"] = round(time.time() - t0, 2)

    # 13. Build Streamlit contracts
    t0 = time.time()
    LOG.info("[13/15] Building Streamlit data contracts")
    contract_df = build_streamlit_contracts(
        readiness_df, gate_df, blocking_df, transition_df, escalation_df, logger=LOG
    )
    save_csv(contract_df, "step_2d4_streamlit_readiness_data_contract.csv")
    summary["contract_build_time"] = round(time.time() - t0, 2)

    # 14. Build evidence and lineage
    t0 = time.time()
    LOG.info("[14/15] Building evidence and lineage")
    rev_evidence_df = build_evidence(readiness_df, evidence_df, logger=LOG)
    rev_lineage_df = build_lineage(readiness_df, lineage_df, logger=LOG)
    save_csv(rev_evidence_df, "step_2d4_readiness_evidence_register.csv")
    save_csv(rev_lineage_df, "step_2d4_readiness_lineage_register.csv")
    summary["evidence_lineage_time"] = round(time.time() - t0, 2)

    # 15. Governance validation
    t0 = time.time()
    LOG.info("[15/15] Governance validation")
    gov_df, gov_pass = validate_readiness(readiness_df, explanation_df, logger=LOG)
    if not gov_pass:
        LOG.error("Governance validation failed")
        summary["status"] = "FAILED"
        summary["failure_reason"] = "Governance validation failed"
        return summary

    # Build governance and issue registers
    gov_register = pd.DataFrame({
        "governance_check_id": ["GOV-001"],
        "check_type": ["Readiness Governance"],
        "check_result": ["Passed"],
        "issue_count": [len(gov_df)],
        "governance_note": ["All readiness records comply with governance rules"],
    })
    save_csv(gov_register, "step_2d4_readiness_governance_register.csv")

    issue_register = gov_df.copy()
    if issue_register.empty:
        issue_register = pd.DataFrame({
            "issue_id": ["NO-ISSUES"],
            "decision_package_id": ["ALL"],
            "issue_type": ["No Issues"],
            "severity": ["None"],
            "governance_warning": ["No governance issues detected"],
            "resolution_required": [False],
        })
    save_csv(issue_register, "step_2d4_readiness_issue_register.csv")
    summary["governance_time"] = round(time.time() - t0, 2)

    # Build deferred/non-ready register
    deferred = readiness_df[readiness_df["final_readiness_status"].isin([
        "Monitoring Only", "Non-Quantitative", "Not Suitable for Decision Use", "Rejected"
    ])].copy()
    deferred["deferral_reason"] = deferred["final_readiness_status"]
    save_csv(deferred, "step_2d4_deferred_and_non_ready_register.csv")

    # Build execution summary
    status_counts = readiness_df["final_readiness_status"].value_counts().to_dict()
    gate_counts = gate_df["gate_status"].value_counts().to_dict()

    summary.update({
        "status": "SUCCESS",
        "end_time": datetime.now().isoformat(),
        "total_time_seconds": round(time.time() - start_time, 2),
        "scorecards_processed": len(scorecard_df),
        "readiness_records_created": len(readiness_df),
        "ready_for_integrated_management_review": status_counts.get("Ready for Integrated Management Review", 0),
        "ready_with_conditions": status_counts.get("Ready with Conditions", 0),
        "requires_assumption_validation": status_counts.get("Requires Assumption Validation", 0),
        "requires_baseline_validation": status_counts.get("Requires Baseline Validation", 0),
        "requires_financial_input": status_counts.get("Requires Financial Input", 0),
        "requires_benefit_validation": status_counts.get("Requires Benefit Validation", 0),
        "requires_budget_data": status_counts.get("Requires Budget Data", 0),
        "requires_stakeholder_validation": status_counts.get("Requires Stakeholder Validation", 0),
        "requires_additional_scenario_analysis": status_counts.get("Requires Additional Scenario Analysis", 0),
        "requires_evidence_completion": status_counts.get("Requires Evidence Completion", 0),
        "requires_lineage_completion": status_counts.get("Requires Lineage Completion", 0),
        "monitoring_only": status_counts.get("Monitoring Only", 0),
        "non_quantitative": status_counts.get("Non-Quantitative", 0),
        "not_suitable": status_counts.get("Not Suitable for Decision Use", 0),
        "rejected": status_counts.get("Rejected", 0),
        "gates_created": len(gate_df),
        "gate_passes": gate_counts.get("Pass", 0),
        "gate_pass_with_conditions": gate_counts.get("Pass with Conditions", 0),
        "gate_failures": gate_counts.get("Fail", 0),
        "blocking_conditions_created": len(blocking_df),
        "secondary_conditions_created": len(secondary_df),
        "transition_rules_created": len(transition_df),
        "primary_queues_assigned": len(queue_df),
        "role_assignments": len(role_df),
        "escalation_assignments": len(escalation_df),
        "explanations_created": len(explanation_df),
        "streamlit_contract_records": len(contract_df),
        "evidence_records_created": len(rev_evidence_df),
        "lineage_records_created": len(rev_lineage_df),
        "governance_issues": len(gov_df),
        "no_preferred_scenario_selected": True,
        "no_approved_recommendation": True,
        "no_management_action_selected": True,
        "no_management_approval_recorded": True,
        "causality_status": "Not Confirmed",
        "upstream_immutable": True,
    })

    exec_summary = pd.DataFrame([{
        "metric": k,
        "value": str(v),
    } for k, v in summary.items()])
    save_csv(exec_summary, "step_2d4_execution_summary.csv")

    # Move outputs atomically
    LOG.info("Moving outputs to final paths")
    for fname in os.listdir(TMP_DIR):
        src = os.path.join(TMP_DIR, fname)
        dst = os.path.join(OUTPUT_DIR, fname)
        shutil.move(src, dst)

    # Generate manifest
    manifest = {
        "step": "2D-4",
        "timestamp": datetime.now().isoformat(),
        "summary": summary,
        "outputs": {},
    }
    for fname in os.listdir(OUTPUT_DIR):
        if fname.startswith("step_2d4_"):
            fpath = os.path.join(OUTPUT_DIR, fname)
            manifest["outputs"][fname] = {
                "checksum": compute_sha256(fpath),
                "size_bytes": os.path.getsize(fpath),
            }

    manifest_path = os.path.join(OUTPUT_DIR, "step_2d4_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    LOG.info("=" * 60)
    LOG.info("STEP 2D-4 COMPLETE")
    LOG.info("Readiness records: %s", summary["readiness_records_created"])
    LOG.info("Total time: %s seconds", summary["total_time_seconds"])
    LOG.info("=" * 60)

    return summary


if __name__ == "__main__":
    if not run_smoke_test():
        LOG.error("Smoke test failed. Aborting full process.")
        sys.exit(1)

    result = run_full_process()
    if result.get("status") != "SUCCESS":
        sys.exit(1)
    sys.exit(0)
