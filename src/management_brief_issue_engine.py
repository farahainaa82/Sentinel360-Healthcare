"""Issue and risk summary engine for Step 2D-7."""


def _safe(val, default=""):
    if val is None or (isinstance(val, float) and str(val) == "nan"):
        return default
    return str(val)


def synthesize_issue_risk(row):
    """Synthesize issue and risk summary fields from source data."""
    result = {}
    result["current_issue_summary"] = _safe(row.get("what_is_happening", ""))
    result["current_kpi_status"] = _safe(row.get("current_kpi_value", ""))
    result["breach_status"] = _safe(row.get("breach_status", ""))
    result["watch_status"] = _safe(row.get("watch_status", ""))
    result["trend_direction"] = _safe(row.get("trend_direction", ""))
    result["sustained_movement_flag"] = _safe(row.get("sustained_movement_flag", "False"))
    result["operational_risk_score"] = _safe(row.get("operational_risk_score", ""))
    result["risk_tier"] = _safe(row.get("risk_tier", ""))
    result["urgency"] = _safe(row.get("urgency", ""))
    result["priority_tier"] = _safe(row.get("priority_tier", ""))
    result["dominant_breach_type"] = _safe(row.get("dominant_breach_type", ""))
    result["operational_significance"] = (
        f"The {_safe(row.get('risk_tier','')).lower()} risk tier and "
        f"{_safe(row.get('priority_tier','')).lower()} priority indicate this package requires management attention."
    )
    result["likely_service_consequence"] = "Requires validation before estimating service impact."
    result["likely_workforce_consequence"] = "Requires validation before estimating workforce impact."
    result["likely_patient_experience_consequence"] = "Requires validation before estimating patient experience impact."
    result["likely_financial_exposure"] = _safe(row.get("estimated_net_financial_impact", "Not Assessable"))
    result["management_attention_reason"] = (
        f"Operational conditions in {_safe(row.get('department_name',''))} "
        f"related to {_safe(row.get('dominant_kpi_name',''))} require management review."
    )
    return result
