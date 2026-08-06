"""Management question summary engine for Step 2D-7."""


def _safe(val, default=""):
    if val is None or (isinstance(val, float) and str(val) == "nan"):
        return default
    return str(val)


def select_questions(row, questions_df=None):
    """Select top management questions for the brief."""
    result = {}
    result["top_management_questions"] = _safe(row.get("top_management_questions", ""))
    result["blocking_question_count"] = _safe(row.get("blocking_question_count", "0"))
    result["mandatory_question_count"] = _safe(row.get("mandatory_question_count", "0"))
    result["responsible_roles"] = _safe(row.get("responsible_roles", ""))
    result["required_response_types"] = _safe(row.get("required_response_types", ""))
    return result
