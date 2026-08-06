"""
decision_audit_event_catalogue_engine.py
Phase 2D-6 — Audit event catalogue definitions.
"""

import pandas as pd


def build_audit_event_catalogue(config_path: str = "config/decision_audit_event_catalogue.csv") -> pd.DataFrame:
    return pd.read_csv(config_path)
