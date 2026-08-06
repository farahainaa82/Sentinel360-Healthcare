"""Phase 2D handover issue engine."""
from phase2d_closure_utils import load_csv
import pandas as pd

def build_handover_issues():
    mv = load_csv("step_2d8_master_validation_register.csv")
    if mv.empty:
        return pd.DataFrame()
    records = []
    for _, row in mv.iterrows():
        if row["validation_outcome"] != "Validated for Streamlit Handover":
            records.append({
                "decision_package_id": row["decision_package_id"],
                "issue_type": "Validation Condition",
                "issue_description": row["validation_outcome"],
            })
    return pd.DataFrame(records)

if __name__ == "__main__":
    print(build_handover_issues())
