"""
streamlit_executive_financial_engine.py
Financial impact summary engine.
"""

from typing import Dict, List, Optional
import pandas as pd

from .streamlit_executive_logging import log_event


def _safe_sum(series: pd.Series) -> Optional[float]:
    nums = pd.to_numeric(series, errors="coerce")
    valid = nums.dropna()
    if valid.empty:
        return None
    return float(valid.sum())


def build_financial_summary(fin_df: pd.DataFrame) -> Dict[str, Dict]:
    if fin_df.empty:
        return {}
    central = _safe_sum(fin_df["central_estimate"]) if "central_estimate" in fin_df.columns else None
    upper = _safe_sum(fin_df["upper_estimate"]) if "upper_estimate" in fin_df.columns else None
    net = _safe_sum(fin_df["net_financial_impact"]) if "net_financial_impact" in fin_df.columns else None
    missing_count = 0
    if "missing_input_warning" in fin_df.columns:
        missing_count = int(fin_df["missing_input_warning"].astype(str).str.strip().ne("").sum())
    lower = _safe_sum(fin_df["lower_estimate"]) if "lower_estimate" in fin_df.columns else None
    summary = {
        "Estimated Intervention Cost": {
            "value": central,
            "display": f"RM {central:,.0f}" if central is not None else "Requires Financial Input",
        },
        "Estimated Financial Benefit": {
            "value": upper,
            "display": f"RM {upper:,.0f}" if upper is not None else "Requires Financial Input",
        },
        "Estimated Net Financial Impact": {
            "value": net,
            "display": f"RM {net:,.0f}" if net is not None else "Not Assessable",
        },
        "Packages Requiring Financial Input": {
            "value": missing_count,
            "display": str(missing_count),
        },
    }
    if lower is not None and central is not None and upper is not None:
        summary["range"] = {
            "lower": lower,
            "central": central,
            "upper": upper,
        }
    log_event("FINANCIAL_SUMMARY_BUILT", f"records={len(fin_df)}")
    return summary


def build_financial_priority_cases(
    fin_df: pd.DataFrame,
    risk_df: pd.DataFrame,
    top_n: int = 5,
) -> List[Dict]:
    if fin_df.empty:
        return []
    merged = fin_df.copy()
    if not risk_df.empty and "decision_package_id" in risk_df.columns:
        merged = merged.merge(
            risk_df[["decision_package_id", "risk_tier", "urgency", "dominant_kpi_name", "affected_department"]],
            on="decision_package_id",
            how="left",
        )
    # Sort by risk desc then urgency then financial completeness
    if "risk_tier" in merged.columns:
        merged["risk_tier_num"] = pd.to_numeric(merged["risk_tier"], errors="coerce").fillna(0)
    else:
        merged["risk_tier_num"] = 0
    urgency_order = {"Immediate Review": 1, "Prompt Review": 2, "Standard Management Review": 3, "Routine": 4}
    if "urgency" in merged.columns:
        merged["urgency_order"] = merged["urgency"].map(urgency_order).fillna(99)
    else:
        merged["urgency_order"] = 99
    if "missing_input_warning" in merged.columns:
        merged["has_missing"] = merged["missing_input_warning"].astype(str).str.strip().ne("").astype(int)
    else:
        merged["has_missing"] = 0
    if "net_financial_impact" in merged.columns:
        merged["net_num"] = pd.to_numeric(merged["net_financial_impact"], errors="coerce").fillna(0).abs()
    else:
        merged["net_num"] = 0
    merged = merged.sort_values(
        by=["risk_tier_num", "urgency_order", "has_missing", "net_num"],
        ascending=[False, True, True, False],
    )
    top = merged.head(top_n)
    records: List[Dict] = []
    for _, row in top.iterrows():
        net = row.get("net_financial_impact")
        net_display = f"RM {float(net):,.0f}" if pd.notna(net) else "Not Assessable"
        records.append(
            {
                "department": str(row.get("affected_department", "")),
                "dominant_kpi": str(row.get("dominant_kpi_name", "")),
                "risk_tier": str(row.get("risk_tier", "")),
                "readiness": "",
                "estimated_cost": str(row.get("central_estimate", "")),
                "estimated_benefit": str(row.get("upper_estimate", "")),
                "estimated_net": net_display,
                "financial_confidence": str(row.get("financial_confidence", "")),
                "missing_input": str(row.get("missing_input_warning", "")),
                "primary_queue": "",
            }
        )
    log_event("FINANCIAL_PRIORITY_BUILT", f"top_n={top_n}")
    return records
