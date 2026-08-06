"""Recommendation summary engine for Step 2D-7."""


def _safe(val, default=""):
    if val is None or (isinstance(val, float) and str(val) == "nan"):
        return default
    return str(val)


def synthesize_recommendation(row):
    """Synthesize recommendation summary fields from source data."""
    result = {}
    result["representative_recommendation"] = _safe(row.get("representative_recommendation", ""))
    result["immediate_action_option"] = _safe(row.get("immediate_action", ""))
    result["near_term_action_option"] = _safe(row.get("near_term_action", ""))
    result["preventive_action_option"] = _safe(row.get("preventive_action", ""))
    result["recommendation_readiness"] = _safe(row.get("recommendation_readiness", ""))
    result["recommendation_validation_status"] = _safe(row.get("recommendation_validation_status", ""))
    result["recommendation_confirmation_required"] = _safe(row.get("recommendation_confirmation_required", ""))
    result["recommendation_limitations"] = _safe(row.get("recommendation_limitations", ""))
    return result
