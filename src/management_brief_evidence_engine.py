"""Evidence summary engine for Step 2D-7."""


def _safe(val, default=""):
    if val is None or (isinstance(val, float) and str(val) == "nan"):
        return default
    return str(val)


def synthesize_evidence(row):
    """Synthesize evidence summary fields from source data."""
    result = {}
    result["evidence_completeness_status"] = _safe(row.get("evidence_completeness_status", ""))
    result["evidence_coverage_pct"] = _safe(row.get("evidence_coverage_pct", ""))
    result["critical_missing_evidence_count"] = _safe(row.get("critical_missing_evidence_count", "0"))
    result["key_evidence_summary"] = _safe(row.get("key_evidence_summary", ""))
    result["evidence_conditions"] = _safe(row.get("evidence_conditions", ""))
    result["evidence_warning"] = _safe(row.get("evidence_warning", ""))
    result["source_to_decision_trace_status"] = _safe(row.get("source_to_decision_trace_status", ""))
    return result
