"""Streamlit risk and alert contract engine."""
from phase2d_closure_utils import load_csv
import pandas as pd

def build_risk_alert():
    imb = load_csv("step_2d7_integrated_management_brief_register.csv")
    if imb.empty:
        return pd.DataFrame()
    records = []
    for _, row in imb.iterrows():
        records.append({
            "decision_package_id": row.get("decision_package_id",""),
            "risk_tier": row.get("maximum_risk_score",""),
            "urgency": row.get("maximum_urgency",""),
            "dominant_kpi": row.get("dominant_kpi_name",""),
            "contributing_factors": row.get("contributing_factor",""),
            "contradiction_warning": row.get("contradiction_severity",""),
        })
    return pd.DataFrame(records)

if __name__ == "__main__":
    print(build_risk_alert())
