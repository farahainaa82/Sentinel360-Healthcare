"""Financial summary engine for Step 2D-7."""


def _safe(val, default=""):
    if val is None or (isinstance(val, float) and str(val) == "nan"):
        return default
    return str(val)


def synthesize_financial(row):
    """Synthesize financial summary fields from source data."""
    result = {}
    result["financial_readiness"] = _safe(row.get("financial_readiness", ""))
    result["cost_completeness"] = _safe(row.get("cost_completeness", ""))
    result["estimated_scenario_cost"] = _safe(row.get("estimated_scenario_cost", "Not Available"))
    result["estimated_financial_benefit"] = _safe(row.get("estimated_financial_benefit", "Not Available"))
    result["estimated_net_financial_impact"] = _safe(row.get("estimated_net_financial_impact", "Not Available"))
    result["roi_status"] = _safe(row.get("roi_status", "Not Assessable"))
    result["payback_status"] = _safe(row.get("payback_status", "Not Assessable"))
    result["affordability_status"] = _safe(row.get("affordability_status", "Budget Data Required"))
    result["lower_financial_estimate"] = _safe(row.get("lower_financial_estimate", "Not Available"))
    result["central_financial_estimate"] = _safe(row.get("central_financial_estimate", "Not Available"))
    result["upper_financial_estimate"] = _safe(row.get("upper_financial_estimate", "Not Available"))
    result["financial_confidence"] = _safe(row.get("financial_confidence", ""))
    result["missing_financial_input_flag"] = _safe(row.get("missing_financial_input_flag", "False"))
    result["financial_limitations"] = _safe(row.get("financial_limitations", ""))
    return result
