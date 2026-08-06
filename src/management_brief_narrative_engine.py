"""Narrative generation engine for Step 2D-7 headlines and summaries."""

import textwrap


def _safe(val, default=""):
    if val is None or (isinstance(val, float) and str(val) == "nan"):
        return default
    return str(val)


def generate_issue_title(row):
    """Generate concise issue title from hospital, department, KPI, and risk."""
    dept = _safe(row.get("department_name", ""))
    kpi = _safe(row.get("dominant_kpi_name", ""))
    risk = _safe(row.get("risk_tier", ""))
    if not dept:
        dept = _safe(row.get("department_id", "Unknown Department"))
    if not kpi:
        kpi = _safe(row.get("dominant_kpi_id", "Unknown KPI"))
    if risk.lower() in ("critical", "high"):
        condition = "Pressure"
    elif risk.lower() == "moderate":
        condition = "Warning"
    else:
        condition = "Attention"
    return f"{dept} {kpi} {condition}"


def generate_brief_title(row):
    """Generate brief title."""
    return f"Integrated Management Brief: {generate_issue_title(row)}"


def generate_brief_subtitle(row):
    """Generate brief subtitle."""
    readiness = _safe(row.get("final_readiness_status", ""))
    return f"Status: {readiness} — Pending Management Review"


def generate_executive_headline(row):
    """Generate executive headline describing issue, location, and attention need."""
    dept = _safe(row.get("department_name", row.get("department_id", "Unknown")))
    kpi = _safe(row.get("dominant_kpi_name", row.get("dominant_kpi_id", "Unknown")))
    risk = _safe(row.get("risk_tier", ""))
    urgency = _safe(row.get("urgency", ""))
    parts = [dept, "is experiencing", kpi, "related operational conditions."]
    if risk:
        parts.extend(["Risk tier:", risk + "."])
    if urgency:
        parts.extend(["Urgency:", urgency + "."])
    parts.append("Management attention required.")
    return " ".join(parts)


def generate_one_line_summary(row):
    """Generate one-line summary, max 35 words target."""
    dept = _safe(row.get("department_name", row.get("department_id", "Unknown")))
    kpi = _safe(row.get("dominant_kpi_name", ""))
    risk = _safe(row.get("risk_tier", ""))
    readiness = _safe(row.get("final_readiness_status", ""))
    text = f"{dept}: {kpi} shows {risk.lower() if risk else 'elevated'} risk; readiness {readiness}; awaiting management review."
    words = text.split()
    if len(words) > 35:
        text = " ".join(words[:35]) + "."
    return text


def generate_short_summary(row):
    """Generate short summary, max 120 words target."""
    dept = _safe(row.get("department_name", row.get("department_id", "Unknown")))
    kpi = _safe(row.get("dominant_kpi_name", ""))
    risk = _safe(row.get("risk_tier", ""))
    readiness = _safe(row.get("final_readiness_status", ""))
    action = _safe(row.get("primary_permitted_action", ""))
    text = (
        f"{dept} is experiencing operational conditions related to {kpi}. "
        f"The current risk tier is {risk if risk else 'under assessment'}. "
        f"Analytical readiness status: {readiness}. "
        f"Primary permitted action: {action if action else 'under review'}. "
        f"No scenario or action has been selected. No recommendation has been approved. "
        f"Management review is required before any decision."
    )
    words = text.split()
    if len(words) > 120:
        text = " ".join(words[:120]) + "."
    return text
