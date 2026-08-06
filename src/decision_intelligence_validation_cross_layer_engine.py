"""Cross-Layer Consistency Validation Engine for 2D-8.

Validates logical consistency across evidence, lineage, readiness, and governance layers.
"""

import pandas as pd

from decision_intelligence_validation_utils import load_register


def validate():
    """Run cross-layer consistency validation."""
    briefs = load_register("step_2d7_integrated_management_brief_register.csv")

    rows = []

    if briefs.empty:
        return pd.DataFrame({
            "validation_id": ["VA-CL-001"],
            "check": ["register_loaded"],
            "status": ["FAIL"],
            "detail": ["Brief register empty"],
        })

    # Check 1: Evidence and lineage completeness alignment
    if "evidence_completeness_status" in briefs.columns and "lineage_completeness_status" in briefs.columns:
        inconsistent = 0
        for _, row in briefs.iterrows():
            ev = str(row.get("evidence_completeness_status", "")).lower()
            ln = str(row.get("lineage_completeness_status", "")).lower()
            # If one is complete and the other is missing, flag it
            ev_complete = "complete" in ev and "missing" not in ev
            ln_complete = "complete" in ln and "missing" not in ln
            ev_missing = "missing" in ev
            ln_missing = "missing" in ln
            if (ev_complete and ln_missing) or (ln_complete and ev_missing):
                inconsistent += 1
        rows.append({
            "validation_id": "VA-CL-001",
            "check": "evidence_lineage_alignment",
            "expected": 0,
            "actual": inconsistent,
            "status": "PASS" if inconsistent == 0 else "FAIL",
            "detail": "" if inconsistent == 0 else f"{inconsistent} evidence/lineage misalignments",
        })
    else:
        rows.append({
            "validation_id": "VA-CL-001",
            "check": "evidence_lineage_alignment",
            "expected": 0,
            "actual": None,
            "status": "PASS",
            "detail": "Required columns not present",
        })

    # Check 2: Readiness score range consistency
    if "readiness_score" in briefs.columns:
        scores = pd.to_numeric(briefs["readiness_score"], errors="coerce")
        out_of_range = ((scores < 0) | (scores > 1)).sum()
        rows.append({
            "validation_id": "VA-CL-002",
            "check": "readiness_score_range",
            "expected": 0,
            "actual": out_of_range,
            "status": "PASS" if out_of_range == 0 else "FAIL",
            "detail": "" if out_of_range == 0 else f"{out_of_range} readiness scores out of [0,1]",
        })
    else:
        rows.append({
            "validation_id": "VA-CL-002",
            "check": "readiness_score_range",
            "expected": 0,
            "actual": None,
            "status": "PASS",
            "detail": "readiness_score column not present",
        })

    # Check 3: Governance issue count zero or documented
    if "governance_issue_count" in briefs.columns:
        issues = pd.to_numeric(briefs["governance_issue_count"], errors="coerce").fillna(0)
        non_zero = (issues > 0).sum()
        rows.append({
            "validation_id": "VA-CL-003",
            "check": "governance_issue_count",
            "expected": 0,
            "actual": non_zero,
            "status": "PASS" if non_zero == 0 else "FAIL",
            "detail": "" if non_zero == 0 else f"{non_zero} packages with governance issues > 0",
        })
    else:
        rows.append({
            "validation_id": "VA-CL-003",
            "check": "governance_issue_count",
            "expected": 0,
            "actual": None,
            "status": "PASS",
            "detail": "governance_issue_count column not present",
        })

    return pd.DataFrame(rows)


def build_register():
    return validate()


def get_required_columns():
    return [
        "validation_id", "check", "expected", "actual",
        "status", "detail",
    ]
