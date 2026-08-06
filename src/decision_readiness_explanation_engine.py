"""
Decision Readiness Explanation Engine for Phase 2D-4.

Creates one concise explanation per package with required structure.
"""

import logging
import pandas as pd
from typing import Dict, Any, List

LOG = logging.getLogger("decision_readiness_explanation_engine")


def _build_explanation(row: pd.Series) -> str:
    status = row["final_readiness_status"]
    pkg_status = row.get("package_status", "")

    explanations = {
        "Ready for Integrated Management Review": (
            "This package has passed all mandatory gates and is ready for management review. "
            "Core risk, recommendation, scenario, and financial information is available. "
            "No absolute exclusion applies. "
            "Management can review the options and confirm specified matters."
        ),
        "Ready with Conditions": (
            "This package is complete enough for management review with non-blocking conditions remaining. "
            "Core information is available but some warnings or provisional matters require attention. "
            "Management can review the options but must confirm specified matters."
        ),
        "Requires Assumption Validation": (
            "Scenario or recommendation assumptions remain materially unconfirmed. "
            "Management review would be misleading without confirmation of key assumptions. "
            "Comparator assumptions require validation before proceeding."
        ),
        "Requires Baseline Validation": (
            "The baseline is missing, stale, inconsistent, or not representative. "
            "Baseline validation status is blocking further progression. "
            "A valid baseline must be established before management review."
        ),
        "Requires Financial Input": (
            "A mandatory financial input is missing or incomplete. "
            "Financial comparison would be materially misleading without complete data. "
            "Required cost or benefit information must be provided."
        ),
        "Requires Benefit Validation": (
            "Financial benefit is used but benefit eligibility is unresolved. "
            "The avoided-cost relationship requires validation before it can be relied upon."
        ),
        "Requires Budget Data": (
            "Affordability or budget sufficiency is required but no authoritative budget is available. "
            "Budget data must be supplied before financial readiness can be confirmed."
        ),
        "Requires Stakeholder Validation": (
            "A material input or assumption requires responsible-owner confirmation. "
            "Stakeholder confirmation is blocking and cannot be safely resolved analytically."
        ),
        "Requires Additional Scenario Analysis": (
            "The comparator set is incomplete or existing scenario results are insufficient. "
            "Additional modelling is required before comparison can be completed."
        ),
        "Requires Evidence Completion": (
            "Required evidence references are missing or applicable analytical phases are not covered. "
            "Evidence completeness is insufficient for management review."
        ),
        "Requires Lineage Completion": (
            "Source-to-decision lineage is incomplete or orphan references exist. "
            "The decision record cannot be fully traced without completing lineage."
        ),
        "Monitoring Only": (
            "This case does not currently require active intervention review. "
            "The analytical route calls for continued observation. "
            "Monitoring requirements are present and escalation triggers are defined."
        ),
        "Non-Quantitative": (
            "Scenario or financial comparison cannot be quantified for this case. "
            "Narrative review or monitoring remains possible. "
            "No fabricated quantitative value has been introduced."
        ),
        "Not Suitable for Decision Use": (
            "The package is materially incomplete or the analysis is incompatible with the intended decision. "
            "Evidence or lineage defects are severe. "
            "Governance restrictions prevent use in current form."
        ),
        "Rejected": (
            "An authoritative prior phase rejected this package and the rejection reason remains valid. "
            "The package is excluded from management-ready queues."
        ),
    }

    why = explanations.get(status, f"Status assigned based on governed classification rules for package status: {pkg_status}.")

    blocking = ""
    if "Requires" in status:
        blocking = f" Main blocking condition: {status}."
    elif status in ("Not Suitable for Decision Use", "Rejected"):
        blocking = f" Main blocking condition: {status}."

    next_action = ""
    if status == "Ready for Integrated Management Review":
        next_action = " Management review may proceed."
    elif status == "Monitoring Only":
        next_action = " Continue monitoring until escalation trigger is met."
    else:
        next_action = f" Resolve {status} before readiness can advance."

    responsible = " Responsible party varies by condition; see responsible role register."
    permitted = " Permitted action: review and validate; no automatic decision."

    conclusion = " This classification supports management routing and does not constitute approval."

    return f"Current readiness: {status}. {why}{blocking}{next_action}{responsible}{permitted}{conclusion}"


def build_explanations(
    readiness_df: pd.DataFrame,
    logger: logging.Logger = None,
) -> pd.DataFrame:
    logger = logger or LOG
    logger.info("Building readiness explanations")

    rows: List[Dict[str, Any]] = []
    for _, rec in readiness_df.iterrows():
        explanation = _build_explanation(rec)

        rows.append({
            "explanation_id": f"EXP-{rec['decision_readiness_id']}",
            "decision_readiness_id": rec["decision_readiness_id"],
            "decision_scorecard_id": rec["decision_scorecard_id"],
            "decision_package_id": rec["decision_package_id"],
            "current_readiness": rec["final_readiness_status"],
            "why_assigned": explanation.split(".")[1] + "." if "." in explanation else "",
            "main_blocking_condition": rec["final_readiness_status"] if "Requires" in rec["final_readiness_status"] or rec["final_readiness_status"] in ("Not Suitable for Decision Use", "Rejected") else "None",
            "secondary_conditions": "See secondary condition register",
            "what_must_happen_next": "See transition register",
            "who_is_responsible": "See responsible role register",
            "permitted_management_action": "Review and validate; no automatic decision",
            "what_status_does_not_mean": "This is not an approval or recommendation",
            "full_explanation": explanation,
            "governance_note": "Explanation supports routing only",
        })

    result = pd.DataFrame(rows)
    logger.info("Explanations built: %s records", len(result))
    return result
