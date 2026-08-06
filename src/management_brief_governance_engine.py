"""Governance and limitation summary engine for Step 2D-7."""


def _safe(val, default=""):
    if val is None or (isinstance(val, float) and str(val) == "nan"):
        return default
    return str(val)


def synthesize_governance(row):
    """Synthesize governance and limitation summary fields from source data."""
    result = {}
    result["provisional_warning"] = _safe(row.get("provisional_warning", ""))
    result["contradiction_warning"] = _safe(row.get("contradiction_warning", ""))
    result["stakeholder_validation_required"] = _safe(row.get("stakeholder_validation_required", "False"))
    result["assumption_validation_required"] = _safe(row.get("assumption_validation_required", "False"))
    result["baseline_validation_required"] = _safe(row.get("baseline_validation_required", "False"))
    result["financial_validation_required"] = _safe(row.get("financial_validation_required", "False"))
    result["governance_burden_status"] = _safe(row.get("governance_burden_status", ""))
    result["evidence_limitation"] = _safe(row.get("evidence_limitation", ""))
    result["lineage_limitation"] = _safe(row.get("lineage_limitation", ""))
    result["audit_limitation"] = _safe(row.get("audit_limitation", ""))
    result["overall_management_limitation"] = (
        "This brief supports management review and does not constitute action selection, "
        "scenario selection, recommendation approval, budget approval, or a final management decision."
    )
    return result
