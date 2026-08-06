"""Streamlit recommendation contract engine."""
from phase2d_closure_utils import load_csv
import pandas as pd

def build_recommendation():
    imb = load_csv("step_2d7_integrated_management_brief_register.csv")
    if imb.empty:
        return pd.DataFrame()
    records = []
    for _, row in imb.iterrows():
        records.append({
            "decision_package_id": row.get("decision_package_id",""),
            "representative_recommendation": row.get("representative_recommendation",""),
            "immediate_option": row.get("immediate_action_option",""),
            "near_term_option": row.get("near_term_action_option",""),
            "preventive_option": row.get("preventive_action_option",""),
            "validation_status": row.get("recommendation_review_outcome",""),
            "provisional_warning": row.get("provisional_warning",""),
        })
    return pd.DataFrame(records)

if __name__ == "__main__":
    print(build_recommendation())
