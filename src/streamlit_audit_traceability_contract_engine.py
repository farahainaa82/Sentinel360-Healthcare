"""Streamlit audit traceability contract engine."""
from phase2d_closure_utils import load_csv
import pandas as pd

def build_audit_traceability():
    imb = load_csv("step_2d7_integrated_management_brief_register.csv")
    if imb.empty:
        return pd.DataFrame()
    records = []
    for _, row in imb.iterrows():
        records.append({
            "decision_package_id": row.get("decision_package_id",""),
            "package_version": row.get("current_package_version","1.0"),
            "audit_event_status": "Not Executed",
            "actor": "",
            "timestamp": "",
            "approval_reference": "",
            "integrity_status": row.get("integrity_status","Verified"),
        })
    return pd.DataFrame(records)

if __name__ == "__main__":
    print(build_audit_traceability())
