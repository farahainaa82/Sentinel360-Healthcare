"""Phase 2D handover dataset engine."""
from phase2d_closure_utils import load_csv
import pandas as pd

def build_handover_datasets():
    imb = load_csv("step_2d7_integrated_management_brief_register.csv")
    mv = load_csv("step_2d8_master_validation_register.csv")
    if imb.empty:
        return pd.DataFrame()
    records = []
    for _, row in imb.iterrows():
        dpkg = row["decision_package_id"]
        mv_row = mv[mv["decision_package_id"] == dpkg]
        val = mv_row.iloc[0]["validation_outcome"] if not mv_row.empty else "Unknown"
        records.append({
            "decision_package_id": dpkg,
            "final_readiness_status": row.get("final_readiness_status",""),
            "validation_outcome": val,
            "streamlit_ready": val in ("Validated for Streamlit Handover", "Validated with Conditions"),
        })
    return pd.DataFrame(records)

if __name__ == "__main__":
    print(build_handover_datasets())
