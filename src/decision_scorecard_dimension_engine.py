"""
Decision Scorecard Dimension Engine for Phase 2D-3.

Builds all nine scorecard dimensions from the decision package register.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List

LOG = logging.getLogger("decision_scorecard_dimension_engine")

RISK_BANDS = ["Critical", "High", "Elevated", "Moderate", "Low", "Monitoring", "Not Assessable"]
EVIDENCE_STATUSES = ["Complete", "Complete with Conditions", "Partial", "Limited", "Not Available"]
LINEAGE_STATUSES = ["Complete", "Complete with Conditions", "Partial", "Incomplete", "Not Available"]
REC_READINESS = ["Ready with Conditions", "Requires Confirmation", "Requires Validation", "Monitoring Recommendation Only", "Non-Quantitative", "Not Suitable", "Not Available"]
SCENARIO_READINESS = ["Ready with Conditions", "Requires Assumption Validation", "Requires Baseline Validation", "Requires Additional Scenario Analysis", "Monitoring Only", "Non-Quantitative", "Not Suitable", "Not Available"]
FINANCIAL_READINESS = ["Ready for Financial Comparison", "Ready with Financial Conditions", "Requires Cost Input", "Requires Benefit Validation", "Requires Budget Data", "Requires Stakeholder Validation", "Partial Financial Estimate Only", "Financial Analysis Not Assessable", "Financial Analysis Not Applicable"]
UNCERTAINTY_STATUSES = ["Governed Range Available", "Available with Conditions", "Limited", "Not Assessable", "Not Applicable"]
GOVERNANCE_BURDEN = ["Low", "Moderate", "High", "Blocking", "Monitoring Only", "Not Assessable"]
DISPLAY_LEVELS = ["Strong", "Adequate", "Conditional", "Limited", "Blocking", "Not Applicable", "Not Assessable"]


def _safe_str(val):
    if pd.isna(val):
        return ""
    return str(val)


def _map_display(level: str) -> str:
    mapping = {
        "Ready with Conditions": "Conditional",
        "Monitoring Only": "Limited",
        "Requires Assumption Validation": "Blocking",
        "Non-Quantitative": "Not Assessable",
        "Ready for Integrated Management Review": "Strong",
        "Requires Baseline Validation": "Blocking",
        "Requires Financial Input": "Blocking",
        "Requires Stakeholder Validation": "Blocking",
        "Requires Additional Scenario Analysis": "Blocking",
        "Not Suitable for Decision Use": "Not Applicable",
        "Rejected": "Not Applicable",
    }
    return mapping.get(level, "Not Assessable")


def build_dimensions(pkg_df: pd.DataFrame, logger: logging.Logger = None) -> pd.DataFrame:
    logger = logger or LOG
    logger.info("Building scorecard dimensions")

    rows: List[Dict[str, Any]] = []
    for _, rec in pkg_df.iterrows():
        pkg_id = rec["decision_package_id"]
        apid = rec["approval_package_id"]
        status = rec.get("decision_status", "Unknown")

        # Dimension 1: Operational Risk
        risk_tier = _safe_str(rec.get("risk_tier", "Not Assessable"))
        if not risk_tier or risk_tier.lower() in ("nan", "none", ""):
            risk_tier = "Not Assessable"
        op_risk_band = risk_tier if risk_tier in RISK_BANDS else "Not Assessable"

        # Dimension 2: Evidence Strength
        ev_count = rec.get("evidence_count", 0)
        if pd.isna(ev_count):
            ev_count = 0
        ev_complete = rec.get("evidence_completeness", False)
        if pd.isna(ev_complete):
            ev_complete = False
        ev_status = "Complete" if ev_complete else ("Partial" if ev_count > 0 else "Not Available")

        # Dimension 3: Lineage Strength
        ln_complete = rec.get("lineage_completeness", False)
        if pd.isna(ln_complete):
            ln_complete = False
        ln_status = "Complete" if ln_complete else "Partial"

        # Dimension 4: Recommendation Readiness
        rec_ready = _safe_str(rec.get("recommendation_readiness", "Not Available"))
        if not rec_ready or rec_ready.lower() in ("nan", "none", ""):
            rec_ready = "Not Available"

        # Dimension 5: Scenario Readiness
        scen_ready = _safe_str(rec.get("scenario_readiness", "Not Available"))
        if not scen_ready or scen_ready.lower() in ("nan", "none", ""):
            scen_ready = "Not Available"

        # Dimension 6: Financial Readiness
        fin_ready = _safe_str(rec.get("financial_readiness", "Financial Analysis Not Assessable"))
        if not fin_ready or fin_ready.lower() in ("nan", "none", ""):
            fin_ready = "Financial Analysis Not Assessable"

        # Dimension 7: Uncertainty
        lower = rec.get("lower_financial_estimate", np.nan)
        central = rec.get("central_financial_estimate", np.nan)
        upper = rec.get("upper_financial_estimate", np.nan)
        has_range = pd.notna(lower) and pd.notna(upper)
        unc_status = "Governed Range Available" if has_range else "Not Assessable"

        # Dimension 8: Governance Burden
        gov_issues = rec.get("governance_issue_count", 0)
        if pd.isna(gov_issues):
            gov_issues = 0
        prov_warn = rec.get("provisional_warning", False)
        if pd.isna(prov_warn):
            prov_warn = False
        contr_warn = rec.get("contradiction_warning", False)
        if pd.isna(contr_warn):
            contr_warn = False
        if gov_issues > 0 or contr_warn:
            gov_burden = "High"
        elif prov_warn:
            gov_burden = "Moderate"
        else:
            gov_burden = "Low"
        if status == "Monitoring Only":
            gov_burden = "Monitoring Only"

        # Dimension 9: Management Readiness
        mgmt_ready = _safe_str(rec.get("package_readiness", status))
        if not mgmt_ready or mgmt_ready.lower() in ("nan", "none", ""):
            mgmt_ready = status

        rows.append({
            "dimension_record_id": f"{pkg_id}-DIM",
            "decision_package_id": pkg_id,
            "approval_package_id": apid,
            "operational_risk_score": rec.get("maximum_risk_score", np.nan),
            "risk_tier": op_risk_band,
            "priority_tier": _safe_str(rec.get("priority_tier", "")),
            "urgency": _safe_str(rec.get("urgency", "")),
            "breach_status": _safe_str(rec.get("breach_status", "")),
            "watch_status": _safe_str(rec.get("watch_status", "")),
            "trend_direction": _safe_str(rec.get("trend_direction", "")),
            "sustained_movement_flag": rec.get("sustained_movement_flag", False),
            "dominant_breach_type": _safe_str(rec.get("dominant_breach_type", "")),
            "provisional_threshold_flag": rec.get("provisional_threshold_flag", False),
            "evidence_reference_count": int(ev_count),
            "evidence_phase_coverage": "Phase 2B|Phase 2C-1|Phase 2C-2|Phase 2C-3|Phase 2D-1|Phase 2D-2",
            "evidence_completeness": ev_complete,
            "evidence_status": ev_status,
            "missing_evidence_flag": not ev_complete,
            "lineage_reference_count": 1 if ln_complete else 0,
            "lineage_stage_coverage": "Phase 2B|Phase 2C-1|Phase 2C-2|Phase 2C-3|Phase 2D-1|Phase 2D-2",
            "lineage_completeness": ln_complete,
            "lineage_status": ln_status,
            "orphan_lineage_flag": not ln_complete,
            "representative_recommendation_available": pd.notna(rec.get("representative_recommendation")),
            "recommendation_validation_status": _safe_str(rec.get("recommendation_validation_status", "")),
            "recommendation_confirmation_required": rec.get("recommendation_confirmation_required", False),
            "recommendation_limitation_count": 0,
            "recommendation_governance_warning": _safe_str(rec.get("recommendation_governance_warning", "")),
            "recommendation_readiness": rec_ready,
            "scenario_required_status": _safe_str(rec.get("scenario_required_status", "")),
            "scenario_readiness": scen_ready,
            "baseline_available": rec.get("baseline_available", False),
            "comparator_completeness": _safe_str(rec.get("comparator_completeness", "")),
            "comparator_consistency": _safe_str(rec.get("comparator_consistency", "")),
            "scenario_validation_status": _safe_str(rec.get("scenario_validation_status", "")),
            "scenario_confidence": _safe_str(rec.get("scenario_confidence", "")),
            "tradeoff_status": _safe_str(rec.get("tradeoff_summary", "")),
            "displacement_status": _safe_str(rec.get("displacement_summary", "")),
            "sensitivity_status": _safe_str(rec.get("sensitivity_summary", "")),
            "dominance_status": _safe_str(rec.get("dominance_summary", "")),
            "financial_review_required": rec.get("financial_review_required", False),
            "financial_readiness": fin_ready,
            "cost_completeness": _safe_str(rec.get("cost_completeness", "")),
            "benefit_completeness": _safe_str(rec.get("benefit_completeness", "")),
            "net_impact_available": pd.notna(rec.get("estimated_net_financial_impact")),
            "roi_status": _safe_str(rec.get("roi_status", "")),
            "payback_status": _safe_str(rec.get("payback_status", "")),
            "affordability_status": _safe_str(rec.get("affordability_status", "")),
            "financial_confidence": _safe_str(rec.get("financial_confidence", "")),
            "missing_financial_input_flag": rec.get("missing_financial_input_flag", False),
            "uncertainty_available": has_range,
            "lower_financial_estimate": lower,
            "central_financial_estimate": central,
            "upper_financial_estimate": upper,
            "financial_range_width": (upper - lower) if has_range else np.nan,
            "primary_uncertainty_driver": _safe_str(rec.get("primary_financial_driver", "")),
            "uncertainty_status": unc_status,
            "scenario_sensitivity_status": _safe_str(rec.get("sensitivity_summary", "")),
            "financial_sensitivity_status": _safe_str(rec.get("primary_financial_risk", "")),
            "break_even_status": "Not Assessable",
            "contradiction_warning": contr_warn,
            "contradiction_severity": _safe_str(rec.get("contradiction_severity", "")),
            "provisional_warning": prov_warn,
            "stakeholder_validation_required": rec.get("stakeholder_validation_required", False),
            "assumption_validation_required": rec.get("assumption_validation_required", False),
            "baseline_validation_required": rec.get("baseline_validation_required", False),
            "financial_validation_required": rec.get("financial_validation_required", False),
            "governance_issue_count": int(gov_issues),
            "governance_burden_status": gov_burden,
            "package_readiness": mgmt_ready,
            "package_completeness": _safe_str(rec.get("completeness_status", "")),
            "decision_readiness": _safe_str(rec.get("decision_readiness", "")),
            "permitted_management_actions": _safe_str(rec.get("permitted_management_actions", "")),
            "blocking_condition_count": 0,
            "management_review_required": rec.get("management_review_required", False),
            "approval_status": "Pending Management Review",
            "display_level": _map_display(status),
        })

    df = pd.DataFrame(rows)
    logger.info(f"Dimensions built: {len(df)} records")
    return df
