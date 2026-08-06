"""
Decision Package Confirmation Engine for Phase 2D-2.

Generates required confirmations per package. No confirmation is marked completed.
"""

import logging
import pandas as pd
from typing import List, Dict, Any

LOG = logging.getLogger("decision_package_confirmation_engine")

CONFIRMATION_TEMPLATES: List[Dict[str, Any]] = [
    {
        "confirmation_id": "CF-001",
        "type": "Risk Acknowledgement",
        "description": "Operational risk has been reviewed and acknowledged.",
        "role": "Operations Manager",
        "required_before_action": True,
        "evidence_required": "Risk review log",
    },
    {
        "confirmation_id": "CF-002",
        "type": "Assumption Acceptance",
        "description": "Key assumptions underlying recommendations have been accepted.",
        "role": "Clinical Lead",
        "required_before_action": True,
        "evidence_required": "Assumption sign-off record",
    },
    {
        "confirmation_id": "CF-003",
        "type": "Financial Validation",
        "description": "Financial estimates have been reviewed for completeness.",
        "role": "Finance Lead",
        "required_before_action": False,
        "evidence_required": "Financial review checklist",
    },
    {
        "confirmation_id": "CF-004",
        "type": "Stakeholder Alignment",
        "description": "Relevant stakeholders have been consulted.",
        "role": "Executive Sponsor",
        "required_before_action": False,
        "evidence_required": "Stakeholder consultation record",
    },
    {
        "confirmation_id": "CF-005",
        "type": "Governance Review",
        "description": "Governance warnings and limitations have been reviewed.",
        "role": "Governance Officer",
        "required_before_action": True,
        "evidence_required": "Governance review log",
    },
]


def build_confirmations(integrated_df: pd.DataFrame, logger: logging.Logger = None) -> pd.DataFrame:
    logger = logger or LOG
    logger.info("Building required confirmations")

    rows: List[Dict[str, Any]] = []
    for _, rec in integrated_df.iterrows():
        pkg_id = f"DPKG-{rec['approval_package_id']}"
        status = rec["decision_status"]

        if status == "Monitoring Only":
            selected = [c for c in CONFIRMATION_TEMPLATES if c["confirmation_id"] == "CF-001"]
        elif status == "Requires Assumption Validation":
            selected = [c for c in CONFIRMATION_TEMPLATES if c["confirmation_id"] in ("CF-002", "CF-003")]
        elif status == "Non-Quantitative":
            selected = [c for c in CONFIRMATION_TEMPLATES if c["confirmation_id"] == "CF-004"]
        elif status == "Ready with Conditions":
            selected = [c for c in CONFIRMATION_TEMPLATES if c["required_before_action"]]
        else:
            selected = CONFIRMATION_TEMPLATES[:2]

        for c in selected:
            rows.append({
                "confirmation_id": f"{pkg_id}-{c['confirmation_id']}",
                "decision_package_id": pkg_id,
                "approval_package_id": rec["approval_package_id"],
                "confirmation_type": c["type"],
                "confirmation_description": c["description"],
                "responsible_role": c["role"],
                "required_before_action": c["required_before_action"],
                "current_status": "Pending",
                "evidence_required": c["evidence_required"],
                "governance_warning": "Do not mark as completed without evidence.",
            })

    df = pd.DataFrame(rows)
    logger.info(f"Confirmations built: {len(df)} total")
    return df
