"""
decision_action_catalogue_engine.py
Phase 2D-5 — Action catalogue management.
"""

import pandas as pd
from typing import List, Dict


def load_action_catalogue(config_path: str = "config/decision_action_catalogue.csv") -> pd.DataFrame:
    """Load the governed action catalogue."""
    return pd.read_csv(config_path)


def get_allowed_actions() -> List[str]:
    """Return the list of governed action names."""
    return [
        "Review Integrated Decision Package",
        "Compare Scenario Options",
        "Validate Assumptions",
        "Validate Baseline",
        "Validate Financial Inputs",
        "Validate Benefit Assumptions",
        "Provide Budget Information",
        "Request Additional Scenario",
        "Request Stakeholder Review",
        "Proceed to Limited-Trial Consideration",
        "Continue Monitoring",
        "Escalate for Immediate Management Attention",
        "Defer Decision",
        "Reject Decision Use",
        "Request Evidence Completion",
        "Request Lineage Completion",
        "Route to Non-Quantitative Review",
        "No Action - Monitoring Continues",
    ]


def get_prohibited_actions() -> List[str]:
    """Return actions that must never appear."""
    return [
        "Approve Scenario",
        "Approve Recommendation",
        "Approve Budget",
        "Implement Intervention",
        "Select Best Scenario",
        "Accept AI Recommendation",
    ]


def validate_no_prohibited_actions(action_names: List[str]) -> bool:
    """Check that no prohibited action names are present."""
    prohibited = set(get_prohibited_actions())
    found = prohibited.intersection(set(action_names))
    return len(found) == 0
