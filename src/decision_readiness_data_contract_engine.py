"""
Decision Readiness Data Contract Engine for Phase 2D-4.

Creates Streamlit-ready contracts for readiness display.
"""

import logging
import pandas as pd
from typing import Dict, Any, List

LOG = logging.getLogger("decision_readiness_data_contract_engine")


def build_streamlit_contracts(
    readiness_df: pd.DataFrame,
    gate_df: pd.DataFrame,
    blocking_df: pd.DataFrame,
    transition_df: pd.DataFrame,
    escalation_df: pd.DataFrame,
    logger: logging.Logger = None,
) -> pd.DataFrame:
    logger = logger or LOG
    logger.info("Building Streamlit readiness contracts")

    rows: List[Dict[str, Any]] = []

    for _, rec in readiness_df.iterrows():
        readiness_id = rec["decision_readiness_id"]
        pkg_id = rec["decision_package_id"]

        # Get related records
        gates = gate_df[gate_df["decision_readiness_id"] == readiness_id]
        blocking = blocking_df[blocking_df["decision_readiness_id"] == readiness_id]
        transitions = transition_df[transition_df["decision_readiness_id"] == readiness_id]
        escalation = escalation_df[escalation_df["decision_readiness_id"] == readiness_id]

        main_blocking = blocking.iloc[0]["condition_type"] if not blocking.empty else "None"
        next_action = transitions.iloc[0]["transition_requirements"] if not transitions.empty else "See transition register"
        esc_status = escalation.iloc[0]["operational_escalation_status"] if not escalation.empty else "Not Assessable"
        attention = escalation.iloc[0]["management_attention_required"] if not escalation.empty else False

        # Contract A: Readiness summary
        rows.append({
            "contract_type": "A. Readiness Summary",
            "decision_readiness_id": readiness_id,
            "decision_package_id": pkg_id,
            "hospital": rec.get("hospital_name", ""),
            "department": rec.get("department_name", ""),
            "dominant_kpi": rec.get("dominant_kpi_name", ""),
            "risk_tier": "",
            "urgency": "",
            "final_readiness_status": rec["final_readiness_status"],
            "primary_queue": "",
            "main_blocking_condition": main_blocking,
            "next_required_action": next_action,
            "responsible_role": "",
            "approval_status": rec["approval_status"],
            "contract_field": "summary",
        })

        # Contract B: Readiness gates
        for _, g in gates.iterrows():
            rows.append({
                "contract_type": "B. Readiness Gates",
                "decision_readiness_id": readiness_id,
                "decision_package_id": pkg_id,
                "hospital": "",
                "department": "",
                "dominant_kpi": "",
                "risk_tier": "",
                "urgency": "",
                "final_readiness_status": "",
                "primary_queue": "",
                "main_blocking_condition": "",
                "next_required_action": "",
                "responsible_role": "",
                "approval_status": "",
                "contract_field": f"{g['gate_name']}={g['gate_status']}",
            })

        # Contract C: Conditions
        for _, b in blocking.iterrows():
            rows.append({
                "contract_type": "C. Conditions",
                "decision_readiness_id": readiness_id,
                "decision_package_id": pkg_id,
                "hospital": "",
                "department": "",
                "dominant_kpi": "",
                "risk_tier": "",
                "urgency": "",
                "final_readiness_status": "",
                "primary_queue": "",
                "main_blocking_condition": b["condition_type"],
                "next_required_action": b["required_resolution"],
                "responsible_role": b["responsible_role"],
                "approval_status": "",
                "contract_field": f"severity={b['severity']},blocking={b['blocking_flag']}",
            })

        # Contract D: Transition guidance
        for _, t in transitions.iterrows():
            rows.append({
                "contract_type": "D. Transition Guidance",
                "decision_readiness_id": readiness_id,
                "decision_package_id": pkg_id,
                "hospital": "",
                "department": "",
                "dominant_kpi": "",
                "risk_tier": "",
                "urgency": "",
                "final_readiness_status": t["current_state"],
                "primary_queue": "",
                "main_blocking_condition": "",
                "next_required_action": t["transition_requirements"],
                "responsible_role": "",
                "approval_status": "",
                "contract_field": f"next={t['eligible_next_state']},not_executed={t['transition_not_executed_flag']}",
            })

        # Contract E: Escalation
        rows.append({
            "contract_type": "E. Escalation",
            "decision_readiness_id": readiness_id,
            "decision_package_id": pkg_id,
            "hospital": "",
            "department": "",
            "dominant_kpi": "",
            "risk_tier": "",
            "urgency": "",
            "final_readiness_status": rec["final_readiness_status"],
            "primary_queue": "",
            "main_blocking_condition": "",
            "next_required_action": "",
            "responsible_role": "",
            "approval_status": "",
            "contract_field": f"escalation={esc_status},attention={attention}",
        })

    result = pd.DataFrame(rows)
    logger.info("Streamlit contracts built: %s records", len(result))
    return result
