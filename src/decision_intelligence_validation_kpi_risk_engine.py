"""KPI/Risk Validation Engine for 2D-8.

Validates KPI and risk tier consistency, escalation alignment, and attention levels.
"""

import pandas as pd

from decision_intelligence_validation_utils import load_register


def validate():
    """Run KPI/Risk validation."""
    briefs = load_register("step_2d7_integrated_management_brief_register.csv")
    if briefs.empty:
        return pd.DataFrame({
            "validation_id": ["VA-KR-001"],
            "check": ["register_loaded"],
            "status": ["FAIL"],
            "detail": ["Brief register empty"],
        })

    rows = []

    # Check 1: High/Critical risk not downgraded without attention
    high_critical = briefs[briefs["risk_tier"].isin(["Critical", "High"])]
    if not high_critical.empty:
        blocked = high_critical[high_critical["final_readiness_status"].isin([
            "Requires Assumption Validation", "Requires Baseline Validation",
            "Requires Evidence Completion", "Requires Lineage Completion"
        ])]
        if not blocked.empty:
            attention_ok = blocked["management_attention_level"].isin([
                "Immediate Management Attention", "Priority Management Review"
            ]).all()
            rows.append({
                "validation_id": "VA-KR-001",
                "check": "high_risk_not_downgraded",
                "expected": True,
                "actual": attention_ok,
                "status": "PASS" if attention_ok else "FAIL",
                "detail": "" if attention_ok else "High/Critical risk blocked without proper attention level",
            })
        else:
            rows.append({
                "validation_id": "VA-KR-001",
                "check": "high_risk_not_downgraded",
                "expected": True,
                "actual": True,
                "status": "PASS",
                "detail": "No high/critical risk packages in blocked status",
            })
    else:
        rows.append({
            "validation_id": "VA-KR-001",
            "check": "high_risk_not_downgraded",
            "expected": True,
            "actual": None,
            "status": "PASS",
            "detail": "No Critical or High risk tiers in dataset",
        })

    # Check 2: Operational escalation aligns with attention level
    escalated = briefs[briefs["operational_escalation_status"].fillna("").str.lower() == "operational escalation"]
    if not escalated.empty:
        attention_ok = escalated["management_attention_level"].isin([
            "Immediate Management Attention", "Priority Management Review"
        ]).all()
        rows.append({
            "validation_id": "VA-KR-002",
            "check": "escalation_attention_alignment",
            "expected": True,
            "actual": attention_ok,
            "status": "PASS" if attention_ok else "FAIL",
            "detail": "" if attention_ok else "Escalated package lacks required attention level",
        })
    else:
        rows.append({
            "validation_id": "VA-KR-002",
            "check": "escalation_attention_alignment",
            "expected": True,
            "actual": None,
            "status": "PASS",
            "detail": "No operational escalation rows",
        })

    # Check 3: Urgency alignment
    immediate = briefs[briefs["urgency"].fillna("").str.lower() == "immediate review"]
    if not immediate.empty:
        attention_ok = immediate["management_attention_level"].isin([
            "Immediate Management Attention"
        ]).all()
        rows.append({
            "validation_id": "VA-KR-003",
            "check": "urgency_attention_alignment",
            "expected": True,
            "actual": attention_ok,
            "status": "PASS" if attention_ok else "FAIL",
            "detail": "" if attention_ok else "Immediate urgency without Immediate Management Attention",
        })
    else:
        rows.append({
            "validation_id": "VA-KR-003",
            "check": "urgency_attention_alignment",
            "expected": True,
            "actual": None,
            "status": "PASS",
            "detail": "No Immediate Review urgency rows",
        })

    return pd.DataFrame(rows)


def build_register():
    return validate()


def get_required_columns():
    return [
        "validation_id", "check", "expected", "actual",
        "status", "detail",
    ]
