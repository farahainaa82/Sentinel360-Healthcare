"""Streamlit scenario lab contract engine."""
from phase2d_closure_utils import load_csv
import pandas as pd

def build_scenario_lab():
    imb = load_csv("step_2d7_integrated_management_brief_register.csv")
    if imb.empty:
        return pd.DataFrame()
    records = []
    for _, row in imb.iterrows():
        records.append({
            "decision_package_id": row.get("decision_package_id",""),
            "baseline": row.get("baseline_summary",""),
            "conservative": row.get("conservative_summary",""),
            "expected": row.get("expected_summary",""),
            "higher_intensity": row.get("higher_intensity_summary",""),
            "tradeoffs": row.get("tradeoff_summary",""),
            "displacement_risk": row.get("displacement_summary",""),
            "confidence": row.get("scenario_confidence",""),
            "validation_warning": row.get("scenario_governance_warning",""),
        })
    return pd.DataFrame(records)

if __name__ == "__main__":
    print(build_scenario_lab())
