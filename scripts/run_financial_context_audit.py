"""Generate financial context alignment audit CSV."""
import os
import sys
import csv
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.streamlit_executive_data_loader import load_kpi_daily, load_risk_alert, load_financial_impact, load_integrated_decision
from src.streamlit_executive_page_controller import build_executive_page_state, load_kpi_threshold_config

OUTPUT_PATH = "outputs/streamlit/step_3b_financial_context_alignment_audit.csv"


def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    kpi_daily = load_kpi_daily()
    threshold_cfg = load_kpi_threshold_config()
    risk_alert = load_risk_alert()
    financial = load_financial_impact()
    integrated = load_integrated_decision()

    departments = [
        ("ALL", "All Departments"),
        ("DEPT-ED", "Emergency Department"),
        ("DEPT-ICU", "Intensive Care Unit"),
        ("DEPT-MED", "Medical Ward"),
        ("DEPT-ADM", "Admissions"),
        ("DEPT-DIAG", "Diagnostics"),
        ("DEPT-OPC", "Outpatient Clinic"),
        ("DEPT-SUR", "Surgery"),
        ("DEPT-PE", "Patient Experience"),
    ]
    months = list(range(1, 8))
    year = 2025
    hospital_id = "HOSP-001"

    rows = []
    for dept_code, dept_name in departments:
        for month in months:
            data = {
                "kpi_daily": kpi_daily,
                "risk_alert": risk_alert,
                "financial": financial,
                "integrated_decision": integrated,
            }
            filters = {
                "department_name": dept_name,
                "department_id": dept_code,
                "hospital_id": hospital_id,
                "year": year,
                "month": month,
                "reporting_date": None,
            }
            state = build_executive_page_state(data, filters)

            fin_block = state.get("financial_impact_block", {})
            dominant_kpi_id = state.get("dominant_kpi_id", "")
            action_text = state.get("management_action", "")
            action_id = f"ACTION-{dominant_kpi_id}" if dominant_kpi_id else ""

            # Find matching risk_alert package for context
            pkg_id = ""
            primary_pkg = state.get("primary_package")
            if primary_pkg:
                pkg_id = primary_pkg.get("decision_package_id", "")

            # Find matching financial record
            fin_rec_id = ""
            fin_pkg_id = ""
            intervention_cost = ""
            benefit = ""
            governed_net = ""
            calculated_net = ""
            context_match = False
            reconciliation_status = ""
            fallback_used = False

            if financial is not None and not financial.empty and pkg_id:
                fin_match = financial[financial["decision_package_id"] == pkg_id]
                if not fin_match.empty:
                    fin_rec = fin_match.iloc[0]
                    fin_rec_id = str(fin_rec.name)
                    fin_pkg_id = pkg_id
                    intervention_cost = str(fin_rec.get("cost_completeness", ""))
                    benefit = str(fin_rec.get("benefit_components", ""))
                    governed_net = str(fin_rec.get("net_financial_impact", ""))
                    calculated_net = str(fin_rec.get("net_financial_impact_num", ""))
                    context_match = True
                    # Reconciliation check
                    net_str = fin_rec.get("net_financial_impact", "")
                    net_num = fin_rec.get("net_financial_impact_num")
                    if pd.isna(net_num) or net_str == "":
                        reconciliation_status = "UNRECONCILED"
                    elif str(net_num) in str(net_str):
                        reconciliation_status = "RECONCILED"
                    else:
                        reconciliation_status = "RECONCILIATION_WARNING"

            # Determine if fallback was used
            if not context_match and fin_block.get("display_state") == "QUANTIFIED":
                fallback_used = True

            note = "OK"
            if not context_match and fin_block.get("display_state") == "QUANTIFIED":
                note = "FALLBACK_USED"
            elif context_match and fin_block.get("display_state") == "READINESS":
                note = "CONTEXT_MATCH_BUT_READINESS"
            elif not context_match and fin_block.get("display_state") == "READINESS":
                note = "NO_FINANCIAL_RECORD_FOR_CONTEXT"

            rows.append({
                "hospital": hospital_id,
                "department": dept_name,
                "department_code": dept_code,
                "year": year,
                "month": month,
                "dominant_kpi_id": dominant_kpi_id,
                "action_id": action_id,
                "financial_record_id": fin_rec_id,
                "decision_package_id": fin_pkg_id,
                "scenario_id": "",
                "intervention_cost": intervention_cost,
                "benefit": benefit,
                "governed_net": governed_net,
                "calculated_net": calculated_net,
                "context_match": context_match,
                "reconciliation_status": reconciliation_status,
                "fallback_used": fallback_used,
                "validation_note": note,
            })

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUTPUT_PATH}")
    fallbacks = [r for r in rows if r["fallback_used"]]
    print(f"Fallbacks used: {len(fallbacks)}")


if __name__ == "__main__":
    main()
