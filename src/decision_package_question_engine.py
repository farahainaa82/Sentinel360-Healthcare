"""
Decision Package Question Engine for Phase 2D-2.

Generates structured management questions per package based on decision status
and available evidence gaps.
"""

import logging
import pandas as pd
from typing import List, Dict, Any

LOG = logging.getLogger("decision_package_question_engine")

QUESTION_TEMPLATES: List[Dict[str, Any]] = [
    {
        "question_id": "MQ-001",
        "text": "Is the current operational risk accurately represented?",
        "category": "Risk Validation",
        "response_type": "Yes/No/Partial",
        "mandatory": True,
        "role": "Operations Manager",
        "blocking": True,
    },
    {
        "question_id": "MQ-002",
        "text": "Are the recommendation assumptions acceptable?",
        "category": "Assumption Validation",
        "response_type": "Yes/No/Partial",
        "mandatory": True,
        "role": "Clinical Lead",
        "blocking": True,
    },
    {
        "question_id": "MQ-003",
        "text": "Is the baseline valid for the current department?",
        "category": "Baseline Validation",
        "response_type": "Yes/No/Partial",
        "mandatory": False,
        "role": "Data Steward",
        "blocking": False,
    },
    {
        "question_id": "MQ-004",
        "text": "Are the comparator assumptions operationally realistic?",
        "category": "Scenario Validation",
        "response_type": "Yes/No/Partial",
        "mandatory": False,
        "role": "Operations Manager",
        "blocking": False,
    },
    {
        "question_id": "MQ-005",
        "text": "Are the required financial inputs sufficiently validated?",
        "category": "Financial Validation",
        "response_type": "Yes/No/Partial",
        "mandatory": False,
        "role": "Finance Lead",
        "blocking": False,
    },
    {
        "question_id": "MQ-006",
        "text": "Are the trade-offs acceptable?",
        "category": "Trade-off Assessment",
        "response_type": "Yes/No/Partial",
        "mandatory": True,
        "role": "Executive Sponsor",
        "blocking": True,
    },
    {
        "question_id": "MQ-007",
        "text": "Is a limited trial appropriate?",
        "category": "Trial Assessment",
        "response_type": "Yes/No/Partial",
        "mandatory": False,
        "role": "Clinical Lead",
        "blocking": False,
    },
    {
        "question_id": "MQ-008",
        "text": "Should the case remain under monitoring?",
        "category": "Monitoring Assessment",
        "response_type": "Yes/No/Partial",
        "mandatory": False,
        "role": "Operations Manager",
        "blocking": False,
    },
    {
        "question_id": "MQ-009",
        "text": "Is stakeholder review required?",
        "category": "Stakeholder Engagement",
        "response_type": "Yes/No/Partial",
        "mandatory": False,
        "role": "Executive Sponsor",
        "blocking": False,
    },
]


def build_questions(integrated_df: pd.DataFrame, logger: logging.Logger = None) -> pd.DataFrame:
    logger = logger or LOG
    logger.info("Building management questions")

    rows: List[Dict[str, Any]] = []
    for _, rec in integrated_df.iterrows():
        pkg_id = f"DPKG-{rec['approval_package_id']}"
        status = rec["decision_status"]

        # Select relevant questions based on status
        if status == "Monitoring Only":
            selected = [q for q in QUESTION_TEMPLATES if q["category"] in ("Risk Validation", "Monitoring Assessment")]
        elif status == "Requires Assumption Validation":
            selected = [q for q in QUESTION_TEMPLATES if q["category"] in (
                "Assumption Validation", "Baseline Validation", "Scenario Validation", "Financial Validation"
            )]
        elif status == "Non-Quantitative":
            selected = [q for q in QUESTION_TEMPLATES if q["category"] in (
                "Risk Validation", "Stakeholder Engagement"
            )]
        elif status == "Ready with Conditions":
            selected = [q for q in QUESTION_TEMPLATES if q["mandatory"]]
        else:
            selected = QUESTION_TEMPLATES[:3]

        for q in selected:
            rows.append({
                "management_question_id": f"{pkg_id}-{q['question_id']}",
                "decision_package_id": pkg_id,
                "approval_package_id": rec["approval_package_id"],
                "question_text": q["text"],
                "question_category": q["category"],
                "required_response_type": q["response_type"],
                "mandatory_flag": q["mandatory"],
                "responsible_role": q["role"],
                "blocking_flag": q["blocking"],
                "source_reference": "Step 2D-1 integrated decision model",
            })

    df = pd.DataFrame(rows)
    logger.info(f"Questions built: {len(df)} total across {len(integrated_df)} packages")
    return df
