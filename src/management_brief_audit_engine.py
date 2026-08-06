"""Audit and traceability summary engine for Step 2D-7."""


def _safe(val, default=""):
    if val is None or (isinstance(val, float) and str(val) == "nan"):
        return default
    return str(val)


def synthesize_audit(row):
    """Synthesize audit and traceability summary fields from source data."""
    result = {}
    result["evidence_completeness_status"] = _safe(row.get("evidence_completeness_status", ""))
    result["lineage_completeness_status"] = _safe(row.get("lineage_completeness_status", ""))
    result["audit_traceability_status"] = _safe(row.get("audit_traceability_status", "Awaiting Management Action"))
    result["integrity_status"] = _safe(row.get("integrity_status", "Verified"))
    result["current_package_version"] = _safe(row.get("current_package_version", "1.0"))
    result["source_manifest"] = _safe(row.get("source_manifest", ""))
    result["audit_requirements_pending"] = _safe(row.get("audit_requirements_pending", ""))
    result["future_audit_status"] = "Awaiting Management Action"
    return result
