"""Streamlit financial impact contract engine."""
from phase2d_closure_utils import load_csv
import pandas as pd

def build_financial_impact():
    imb = load_csv("step_2d7_integrated_management_brief_register.csv")
    if imb.empty:
        return pd.DataFrame()
    records = []
    for _, row in imb.iterrows():
        records.append({
            "decision_package_id": row.get("decision_package_id",""),
            "net_financial_impact": row.get("net_financial_impact",""),
            "lower_estimate": row.get("Baseline",""),
            "central_estimate": row.get("Expected",""),
            "upper_estimate": row.get("Higher Intensity",""),
            "financial_confidence": row.get("financial_readiness",""),
            "roi_status": row.get("roi_status",""),
            "payback_status": row.get("payback_status",""),
        })
    return pd.DataFrame(records)

if __name__ == "__main__":
    print(build_financial_impact())
