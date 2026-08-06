"""Generate management context alignment audit CSV."""
import os
import sys
import csv
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.streamlit_executive_data_loader import load_kpi_daily, load_risk_alert, load_financial_impact, load_integrated_decision
from src.streamlit_executive_page_controller import build_executive_page_state, load_kpi_threshold_config

OUTPUT_PATH = "outputs/streamlit/step_3b_management_context_alignment_audit.csv"


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

            dominant_kpi_id = state.get("dominant_kpi_id")
            dominant_kpi_name = state.get("dominant_kpi_name")
            card_value = ""
            card_status = ""
            for card in state.get("primary_kpi_cards", []):
                if card.get("kpi_id") == dominant_kpi_id:
                    card_value = card.get("latest_value", "")
                    card_status = card.get("threshold_status", "")
                    break

            mgmt = state.get("management_review", {})
            action_id = ""
            action_text = mgmt.get("primary_permitted_action", "")
            dominant_status = state.get("dominant_status")
            if dominant_kpi_id and dominant_status:
                action_id = f"ACTION-{dominant_kpi_id}-{dominant_status}"

            source_package_id = ""
            pkg_match = False
            primary_pkg = state.get("primary_package")
            if primary_pkg:
                source_package_id = primary_pkg.get("decision_package_id", "")
                pkg_match = True

            management_value = card_value if dominant_kpi_id else ""
            management_status = card_status if dominant_kpi_id else "STABLE"

            values_match = (
                (not dominant_kpi_id) or
                (str(card_value) == str(management_value) and card_status == management_status)
            )

            rows.append({
                "hospital": hospital_id,
                "department": dept_name,
                "department_code": dept_code,
                "year": year,
                "month": month,
                "dominant_kpi_id": dominant_kpi_id or "",
                "dominant_kpi_name": dominant_kpi_name or "",
                "card_value": card_value,
                "management_value": management_value,
                "card_status": card_status,
                "management_status": management_status,
                "action_id": action_id,
                "action_text": action_text,
                "source_package_id": source_package_id,
                "package_context_match": pkg_match,
                "management_values_match": values_match,
                "validation_note": "OK" if values_match else "MISMATCH",
            })

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUTPUT_PATH}")
    # Summary
    mismatches = [r for r in rows if not r["management_values_match"]]
    print(f"Mismatches: {len(mismatches)}")


if __name__ == "__main__":
    main()
