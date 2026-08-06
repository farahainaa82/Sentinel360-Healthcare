"""Readiness and conditions summary engine for Step 2D-7."""


def _safe(val, default=""):
    if val is None or (isinstance(val, float) and str(val) == "nan"):
        return default
    return str(val)


def synthesize_readiness(row):
    """Synthesize readiness and condition summary fields from source data."""
    result = {}
    result["final_readiness_status"] = _safe(row.get("final_readiness_status", ""))
    result["readiness_explanation"] = _safe(row.get("readiness_explanation", ""))
    result["main_blocking_condition"] = _safe(row.get("main_blocking_condition", "None"))
    result["blocking_condition_count"] = _safe(row.get("blocking_condition_count", "0"))
    result["secondary_condition_count"] = _safe(row.get("secondary_condition_count", "0"))
    result["top_secondary_conditions"] = _safe(row.get("top_secondary_conditions", ""))
    result["failed_gates"] = _safe(row.get("failed_gates", ""))
    result["pass_with_condition_gates"] = _safe(row.get("pass_with_condition_gates", ""))
    result["required_resolution"] = _safe(row.get("required_resolution", ""))
    result["responsible_role"] = _safe(row.get("responsible_role", ""))
    return result
