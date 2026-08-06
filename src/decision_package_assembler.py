"""
Decision Package Assembler for Phase 2D-2.

Assembles the main decision package register by merging all 2D-1 inputs
and enriching with package-specific fields.
"""

import os
import logging
import pandas as pd
from typing import Dict, Any, Tuple

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(PROJECT_ROOT, "outputs", "decision_intelligence")

LOG = logging.getLogger("decision_package_assembler")


def load_input(fname: str) -> pd.DataFrame:
    path = os.path.join(INPUT_DIR, fname)
    if not os.path.exists(path) or os.path.getsize(path) <= 2:
        return pd.DataFrame()
    return pd.read_csv(path)


def assemble_packages(logger: logging.Logger = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    logger = logger or LOG
    logger.info("Starting package assembly")

    base = load_input("step_2d1_integrated_decision_register.csv")
    if base.empty:
        raise ValueError("Integrated decision register is empty")

    expected = len(base)
    logger.info(f"Base records: {expected}")

    # Merge with status
    status = load_input("step_2d1_integrated_decision_status_register.csv")
    if not status.empty:
        base = base.merge(
            status, on=["integrated_decision_id", "approval_package_id"], how="left", suffixes=("", "_status")
        )
        if len(base) != expected:
            raise ValueError(f"Status merge expanded rows: {len(base)} vs {expected}")

    # Merge with readiness
    readiness = load_input("step_2d1_decision_readiness_register.csv")
    if not readiness.empty:
        base = base.merge(
            readiness, on=["integrated_decision_id", "approval_package_id"], how="left", suffixes=("", "_readiness")
        )
        if len(base) != expected:
            raise ValueError(f"Readiness merge expanded rows: {len(base)} vs {expected}")

    # Merge with action routing
    actions = load_input("step_2d1_management_action_routing_register.csv")
    if not actions.empty:
        base = base.merge(
            actions, on=["integrated_decision_id", "approval_package_id"], how="left", suffixes=("", "_actions")
        )
        if len(base) != expected:
            raise ValueError(f"Action routing merge expanded rows: {len(base)} vs {expected}")

    # Merge with scorecard
    scorecard = load_input("step_2d1_decision_scorecard_input_register.csv")
    if not scorecard.empty:
        base = base.merge(
            scorecard, on=["integrated_decision_id", "approval_package_id"], how="left", suffixes=("", "_scorecard")
        )
        if len(base) != expected:
            raise ValueError(f"Scorecard merge expanded rows: {len(base)} vs {expected}")

    # Merge with summary
    summary = load_input("step_2d1_management_summary_register.csv")
    if not summary.empty:
        base = base.merge(
            summary, on=["integrated_decision_id", "approval_package_id"], how="left", suffixes=("", "_summary")
        )
        if len(base) != expected:
            raise ValueError(f"Summary merge expanded rows: {len(base)} vs {expected}")

    # Merge with evidence
    evidence = load_input("step_2d1_decision_evidence_register.csv")
    if not evidence.empty:
        base = base.merge(
            evidence, on=["integrated_decision_id", "approval_package_id"], how="left", suffixes=("", "_evidence")
        )
        if len(base) != expected:
            raise ValueError(f"Evidence merge expanded rows: {len(base)} vs {expected}")

    # Merge with lineage
    lineage = load_input("step_2d1_decision_lineage_register.csv")
    if not lineage.empty:
        base = base.merge(
            lineage, on=["integrated_decision_id", "approval_package_id"], how="left", suffixes=("", "_lineage")
        )
        if len(base) != expected:
            raise ValueError(f"Lineage merge expanded rows: {len(base)} vs {expected}")

    # Build package ID
    base["decision_package_id"] = "DPKG-" + base["approval_package_id"]
    base["package_version"] = "1.0"
    base["package_status"] = base["decision_status"]
    base["approval_status"] = "Pending Management Review"

    # Ensure required fields exist
    for col in ["issue_title", "issue_summary", "what_is_happening", "why_it_matters",
                "current_operational_risk", "urgency", "priority_tier", "current_status",
                "management_attention_reason"]:
        if col not in base.columns:
            base[col] = None

    for col in ["current_kpi_value", "threshold_status", "breach_status", "watch_status",
                "trend_direction", "sustained_movement_flag", "risk_score", "risk_tier",
                "dominant_breach_type", "contributing_factor_summary", "contradiction_severity",
                "provisional_threshold_flag", "operational_evidence_summary"]:
        if col not in base.columns:
            base[col] = None

    for col in ["representative_recommendation", "recommendation_type", "recommendation_horizon",
                "immediate_action", "near_term_action", "preventive_action",
                "recommendation_validation_status", "recommendation_confirmation_required",
                "recommendation_limitations", "recommendation_governance_warning"]:
        if col not in base.columns:
            base[col] = None

    for col in ["scenario_required_status", "scenario_readiness", "baseline_available",
                "conservative_available", "expected_available", "higher_intensity_available",
                "baseline_summary", "conservative_summary", "expected_summary",
                "higher_intensity_summary", "comparator_completeness", "comparator_consistency",
                "scenario_validation_status", "scenario_confidence"]:
        if col not in base.columns:
            base[col] = None

    for col in ["primary_kpi_effect_summary", "supporting_kpi_effect_summary", "tradeoff_summary",
                "displacement_summary", "sensitivity_summary", "dominance_summary",
                "diminishing_return_summary", "scenario_limitations", "scenario_governance_warning"]:
        if col not in base.columns:
            base[col] = None

    for col in ["financial_review_required", "financial_readiness", "cost_completeness",
                "estimated_scenario_cost", "estimated_financial_benefit", "estimated_net_financial_impact",
                "roi_status", "payback_status", "affordability_status", "lower_financial_estimate",
                "central_financial_estimate", "upper_financial_estimate", "financial_confidence",
                "missing_financial_input_flag", "financial_limitations", "financial_governance_warning"]:
        if col not in base.columns:
            base[col] = None

    for col in ["causality_status", "contradiction_warning", "provisional_warning",
                "stakeholder_validation_required", "assumption_validation_required",
                "baseline_validation_required", "financial_validation_required",
                "evidence_completeness", "lineage_completeness", "governance_issue_count",
                "package_limitations"]:
        if col not in base.columns:
            base[col] = None

    logger.info(f"Package assembly complete: {len(base)} records")
    return base
