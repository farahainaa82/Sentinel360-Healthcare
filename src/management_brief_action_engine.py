"""Management action summary engine for Step 2D-7."""


def _safe(val, default=""):
    if val is None or (isinstance(val, float) and str(val) == "nan"):
        return default
    return str(val)


def synthesize_actions(row):
    """Synthesize permitted management action summary fields from source data."""
    result = {}
    result["primary_permitted_action"] = _safe(row.get("primary_permitted_action", ""))
    result["secondary_permitted_actions"] = _safe(row.get("secondary_permitted_actions", ""))
    result["blocked_action_summary"] = _safe(row.get("blocked_action_summary", ""))
    result["primary_queue"] = _safe(row.get("primary_queue", ""))
    result["secondary_queues"] = _safe(row.get("secondary_queues", ""))
    result["responsible_role"] = _safe(row.get("responsible_role", ""))
    result["escalation_required"] = _safe(row.get("escalation_required", "False"))
    result["escalation_status"] = _safe(row.get("escalation_status", ""))
    result["escalation_reason"] = _safe(row.get("escalation_reason", ""))
    return result
