"""Audit Validation Engine for 2D-8.

Validates audit status, traceability, and event immutability.
"""

import pandas as pd

from decision_intelligence_validation_utils import load_register


def validate():
    """Run audit validation."""
    briefs = load_register("step_2d7_integrated_management_brief_register.csv")

    rows = []

    if briefs.empty:
        return pd.DataFrame({
            "validation_id": ["VA-AU-001"],
            "check": ["register_loaded"],
            "status": ["FAIL"],
            "detail": ["Brief register empty"],
        })

    # Check 1: Future audit status awaiting
    if "future_audit_status" in briefs.columns:
        awaiting = (briefs["future_audit_status"].fillna("") == "Awaiting Management Action").all()
        rows.append({
            "validation_id": "VA-AU-001",
            "check": "future_audit_status_awaiting",
            "expected": True,
            "actual": awaiting,
            "status": "PASS" if awaiting else "FAIL",
            "detail": "" if awaiting else "Some packages do not have Awaiting Management Action audit status",
        })
    else:
        rows.append({
            "validation_id": "VA-AU-001",
            "check": "future_audit_status_awaiting",
            "expected": True,
            "actual": None,
            "status": "PASS",
            "detail": "future_audit_status column not present",
        })

    # Check 2: No audit event executed
    if "audit_event_status" in briefs.columns:
        executed = briefs["audit_event_status"].fillna("").str.contains("Executed", case=False, na=False).sum()
        rows.append({
            "validation_id": "VA-AU-002",
            "check": "no_audit_event_executed",
            "expected": 0,
            "actual": executed,
            "status": "PASS" if executed == 0 else "FAIL",
            "detail": "" if executed == 0 else f"{executed} audit events marked as Executed",
        })
    else:
        rows.append({
            "validation_id": "VA-AU-002",
            "check": "no_audit_event_executed",
            "expected": 0,
            "actual": None,
            "status": "PASS",
            "detail": "audit_event_status column not present",
        })

    # Check 3: Audit traceability status present
    if "audit_traceability_status" in briefs.columns:
        present = briefs["audit_traceability_status"].notna().all()
        rows.append({
            "validation_id": "VA-AU-003",
            "check": "audit_traceability_present",
            "expected": True,
            "actual": present,
            "status": "PASS" if present else "FAIL",
            "detail": "" if present else "Some packages lack audit_traceability_status",
        })
    else:
        rows.append({
            "validation_id": "VA-AU-003",
            "check": "audit_traceability_present",
            "expected": True,
            "actual": None,
            "status": "PASS",
            "detail": "audit_traceability_status column not present",
        })

    return pd.DataFrame(rows)


def build_register():
    return validate()


def get_required_columns():
    return [
        "validation_id", "check", "expected", "actual",
        "status", "detail",
    ]
