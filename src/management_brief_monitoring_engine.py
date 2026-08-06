"""Monitoring and escalation summary engine for Step 2D-7."""


def _safe(val, default=""):
    if val is None or (isinstance(val, float) and str(val) == "nan"):
        return default
    return str(val)


def synthesize_monitoring(row):
    """Synthesize monitoring and escalation summary fields from source data."""
    result = {}
    result["monitoring_required"] = _safe(row.get("monitoring_required", "False"))
    result["monitoring_kpis"] = _safe(row.get("monitoring_kpis", ""))
    result["monitoring_frequency"] = _safe(row.get("monitoring_frequency", ""))
    result["trigger_condition"] = _safe(row.get("trigger_condition", ""))
    result["escalation_condition"] = _safe(row.get("escalation_condition", ""))
    result["reassessment_condition"] = _safe(row.get("reassessment_condition", ""))
    result["monitoring_responsible_role"] = _safe(row.get("monitoring_responsible_role", ""))
    result["management_attention_required"] = _safe(row.get("management_attention_required", "False"))
    return result
