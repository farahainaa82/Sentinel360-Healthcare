"""Streamlit integrated decision contract engine."""
from phase2d_closure_utils import load_csv
import pandas as pd

def build_integrated_decision():
    imb = load_csv("step_2d7_integrated_management_brief_register.csv")
    if imb.empty:
        return pd.DataFrame()
    records = []
    for _, row in imb.iterrows():
        records.append({
            "decision_package_id": row.get("decision_package_id",""),
            "executive_headline": row.get("executive_headline",""),
            "issue_summary": row.get("current_issue_summary",""),
            "readiness": row.get("final_readiness_status",""),
            "blocking_conditions": row.get("main_blocking_condition",""),
            "management_boundary": "This view supports management review and does not constitute action selection, scenario selection, recommendation approval, budget approval, or a final management decision.",
        })
    return pd.DataFrame(records)

if __name__ == "__main__":
    print(build_integrated_decision())
