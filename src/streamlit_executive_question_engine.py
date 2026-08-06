"""
streamlit_executive_question_engine.py
Top management questions engine.
"""

from typing import Dict, List
import pandas as pd

from .streamlit_executive_logging import log_event


def build_top_questions(
    question_df: pd.DataFrame,
    risk_df: pd.DataFrame,
    top_n: int = 5,
) -> List[Dict]:
    if question_df.empty:
        return []
    merged = question_df.copy()
    if not risk_df.empty and "decision_package_id" in risk_df.columns:
        merged = merged.merge(
            risk_df[
                [
                    "decision_package_id",
                    "urgency",
                    "affected_department",
                    "management_attention",
                ]
            ],
            on="decision_package_id",
            how="left",
        )
    # Blocking questions first
    if "blocking_question_count" in merged.columns:
        merged["blocking_num"] = pd.to_numeric(
            merged["blocking_question_count"], errors="coerce"
        ).fillna(0)
    else:
        merged["blocking_num"] = 0
    if "mandatory_question_count" in merged.columns:
        merged["mandatory_num"] = pd.to_numeric(
            merged["mandatory_question_count"], errors="coerce"
        ).fillna(0)
    else:
        merged["mandatory_num"] = 0
    urgency_order = {
        "Immediate Review": 1,
        "Prompt Review": 2,
        "Standard Management Review": 3,
        "Routine": 4,
    }
    if "urgency" in merged.columns:
        merged["urgency_order"] = merged["urgency"].map(urgency_order).fillna(99)
    else:
        merged["urgency_order"] = 99
    merged = merged.sort_values(
        by=["blocking_num", "mandatory_num", "urgency_order"],
        ascending=[False, False, True],
    )
    top = merged.head(top_n)
    records: List[Dict] = []
    for _, row in top.iterrows():
        records.append(
            {
                "question": str(row.get("management_questions", "")),
                "department": str(row.get("affected_department", "")),
                "readiness": "",
                "blocking": int(row.get("blocking_num", 0)) > 0,
                "responsible_role": str(row.get("responsible_roles", "")),
                "required_response_type": str(row.get("required_response_types", "")),
            }
        )
    log_event("TOP_QUESTIONS_BUILT", f"top_n={top_n}")
    return records
