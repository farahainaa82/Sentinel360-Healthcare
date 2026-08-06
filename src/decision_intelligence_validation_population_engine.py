"""Population Validation Engine for 2D-8.

Reconciles expected vs actual population counts across all 2D-7 registers.
"""

import pandas as pd

from decision_intelligence_validation_utils import (
    EXPECTED_PACKAGES,
    load_register,
)


def validate():
    """Run population validation across all 2D-7 registers."""
    registers = {
        "integrated_management_brief_register": "step_2d7_integrated_management_brief_register.csv",
        "executive_one_line_summary_register": "step_2d7_executive_one_line_summary_register.csv",
        "executive_short_summary_register": "step_2d7_executive_short_summary_register.csv",
        "issue_and_risk_summary_register": "step_2d7_issue_and_risk_summary_register.csv",
        "evidence_summary_register": "step_2d7_evidence_summary_register.csv",
        "recommendation_summary_register": "step_2d7_recommendation_summary_register.csv",
        "scenario_summary_register": "step_2d7_scenario_summary_register.csv",
        "tradeoff_and_impact_summary_register": "step_2d7_tradeoff_and_impact_summary_register.csv",
        "financial_summary_register": "step_2d7_financial_summary_register.csv",
        "readiness_and_condition_summary_register": "step_2d7_readiness_and_condition_summary_register.csv",
        "management_action_summary_register": "step_2d7_management_action_summary_register.csv",
        "management_question_summary_register": "step_2d7_management_question_summary_register.csv",
        "confirmation_summary_register": "step_2d7_confirmation_summary_register.csv",
        "monitoring_and_escalation_summary_register": "step_2d7_monitoring_and_escalation_summary_register.csv",
        "governance_and_limitation_summary_register": "step_2d7_governance_and_limitation_summary_register.csv",
        "audit_and_traceability_summary_register": "step_2d7_audit_and_traceability_summary_register.csv",
        "management_priority_view_register": "step_2d7_management_priority_view_register.csv",
        "management_queue_brief_register": "step_2d7_management_queue_brief_register.csv",
        "streamlit_management_brief_contract": "step_2d7_streamlit_management_brief_contract.csv",
        "brief_evidence_register": "step_2d7_brief_evidence_register.csv",
        "brief_lineage_register": "step_2d7_brief_lineage_register.csv",
        "brief_governance_register": "step_2d7_brief_governance_register.csv",
    }

    rows = []
    for reg_name, file_name in registers.items():
        df = load_register(file_name)
        actual = len(df)
        # Some registers are 1:1 (646), sections are 1:17 (10982), export is 1:8 (5168)
        if reg_name == "management_brief_section_register":
            expected = EXPECTED_PACKAGES * 17
        elif reg_name == "export_contract_register":
            expected = EXPECTED_PACKAGES * 8
        else:
            expected = EXPECTED_PACKAGES

        rows.append({
            "validation_id": f"VA-POP-{len(rows)+1:03d}",
            "register_name": reg_name,
            "file_name": file_name,
            "expected_count": expected,
            "actual_count": actual,
            "status": "PASS" if actual == expected else "FAIL",
        })

    return pd.DataFrame(rows)


def build_register():
    return validate()


def get_required_columns():
    return [
        "validation_id", "register_name", "file_name",
        "expected_count", "actual_count", "status",
    ]
