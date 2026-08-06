"""Streamlit management action contract engine."""
from phase2d_closure_utils import load_csv
import pandas as pd

def build_management_action():
    imb = load_csv("step_2d7_integrated_management_brief_register.csv")
    if imb.empty:
        return pd.DataFrame()
    records = []
    for _, row in imb.iterrows():
        records.append({
            "decision_package_id": row.get("decision_package_id",""),
            "selected_action": "",
            "selected_scenario": "",
            "review_outcome": "Pending",
            "management_comment": "",
            "reviewer_role": row.get("primary_reviewer",""),
            "approval_reference": "",
            "confirmation_checkbox": False,
        })
    return pd.DataFrame(records)

if __name__ == "__main__":
    print(build_management_action())
