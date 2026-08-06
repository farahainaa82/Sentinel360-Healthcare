"""Streamlit executive overview contract engine."""
from phase2d_closure_utils import load_csv, has_content
import pandas as pd

def build_executive_overview():
    imb = load_csv("step_2d7_integrated_management_brief_register.csv")
    if imb.empty:
        return pd.DataFrame()
    records = []
    for _, row in imb.iterrows():
        records.append({
            "decision_package_id": row.get("decision_package_id", ""),
            "hospital_name": row.get("hospital_name", ""),
            "department_name": row.get("department_name", ""),
            "risk_tier": row.get("maximum_risk_score", ""),
            "readiness_status": row.get("final_readiness_status", ""),
            "management_attention_level": row.get("management_attention_level", ""),
        })
    return pd.DataFrame(records)

if __name__ == "__main__":
    print(build_executive_overview())
