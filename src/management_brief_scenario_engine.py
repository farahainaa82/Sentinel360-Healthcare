"""Scenario summary engine for Step 2D-7."""


def _safe(val, default=""):
    if val is None or (isinstance(val, float) and str(val) == "nan"):
        return default
    return str(val)


def _comparator_val(val):
    if val is None or (isinstance(val, float) and str(val) == "nan"):
        return "Unavailable"
    v = str(val).strip()
    if v == "" or v.lower() == "nan":
        return "Unavailable"
    return v


def synthesize_scenario(row):
    """Synthesize scenario summary fields from source data."""
    result = {}
    result["scenario_readiness"] = _safe(row.get("scenario_readiness", ""))
    result["baseline_summary"] = _safe(row.get("baseline_summary", "Unavailable"))
    result["conservative_summary"] = _safe(row.get("conservative_summary", "Unavailable"))
    result["expected_summary"] = _safe(row.get("expected_summary", "Unavailable"))
    result["higher_intensity_summary"] = _safe(row.get("higher_intensity_summary", "Unavailable"))
    result["comparator_completeness"] = _safe(row.get("comparator_completeness", ""))
    result["comparator_consistency"] = _safe(row.get("comparator_consistency", ""))
    result["scenario_validation_status"] = _safe(row.get("scenario_validation_status", ""))
    result["scenario_confidence"] = _safe(row.get("scenario_confidence", ""))
    return result
