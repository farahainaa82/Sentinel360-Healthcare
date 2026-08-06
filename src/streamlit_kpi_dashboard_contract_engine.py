"""Streamlit KPI dashboard contract engine."""
from phase2d_closure_utils import load_csv
import pandas as pd

def build_kpi_dashboard():
    sc = load_csv("step_2d3_decision_scorecard_register.csv")
    if sc.empty:
        return pd.DataFrame()
    kpis = ["kpi_001","kpi_002","kpi_003","kpi_004","kpi_005","kpi_006"]
    records = []
    for _, row in sc.iterrows():
        dpkg = row.get("decision_package_id","")
        for kpi in kpis:
            if f"{kpi}_value" in row and pd.notna(row[f"{kpi}_value"]):
                records.append({
                    "decision_package_id": dpkg,
                    "kpi_id": kpi,
                    "current_value": row[f"{kpi}_value"],
                    "threshold_status": row.get(f"{kpi}_status",""),
                    "trend": row.get(f"{kpi}_trend",""),
                })
    return pd.DataFrame(records)

if __name__ == "__main__":
    print(build_kpi_dashboard())
