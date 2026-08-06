"""Patient Experience KPI audit for Phase 3B.

Iterates every department × Jan–Jul 2025 for Patient Complaint Rate (kpi_005)
and Patient Satisfaction Score (kpi_006), compares the canonical monthly value
against the card value built by _build_all_kpi_cards, and records coverage.

Output: outputs/streamlit/step_3b_patient_experience_kpi_audit.csv
"""
import os
import sys
import csv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pandas as pd

from src.streamlit_executive_data_loader import (
    load_kpi_daily,
    get_kpi_monthly_actual_table,
)
from src.streamlit_executive_page_controller import _build_all_kpi_cards, load_kpi_threshold_config

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "outputs", "streamlit")
os.makedirs(OUTPUT_DIR, exist_ok=True)

DEPARTMENTS = [
    ("DEPT-ADM", "Admissions"),
    ("DEPT-ICU", "Intensive Care Unit"),
    ("DEPT-MED", "Medical Ward"),
    ("DEPT-ED", "Emergency Department"),
    ("DEPT-DIAG", "Diagnostics"),
    ("DEPT-OPC", "Outpatient Clinic"),
    ("DEPT-SURG", "Surgery"),
    ("DEPT-PEX", "Patient Experience"),
]

MONTHS = list(range(1, 8))  # Jan–Jul
HOSPITAL = "HOSP-001"
YEAR = 2025


def main():
    kpi_daily = load_kpi_daily()
    threshold_cfg = load_kpi_threshold_config()
    monthly_table = get_kpi_monthly_actual_table(kpi_daily)
    rows = []

    for dept_code, dept_name in DEPARTMENTS:
        for month in MONTHS:
            for kpi_id, kpi_name in [
                ("kpi_005", "Patient Complaint Rate"),
                ("kpi_006", "Patient Satisfaction Score"),
            ]:
                # Canonical value lookup
                canonical_value = None
                canonical_unit = ""
                canonical_status = ""
                valid_obs = 0
                if not monthly_table.empty:
                    mask = (
                        (monthly_table["kpi_id"] == kpi_id)
                        & (monthly_table["hospital"] == HOSPITAL)
                        & (monthly_table["year"] == YEAR)
                        & (monthly_table["month"] == month)
                        & (monthly_table["department_code"] == dept_code)
                    )
                    sub = monthly_table[mask]
                    if not sub.empty:
                        canonical_value = sub.iloc[0]["monthly_actual_value"]
                        canonical_unit = sub.iloc[0].get("unit", "")
                        canonical_status = sub.iloc[0].get("calculation_status", "")
                        valid_obs = sub.iloc[0].get("valid_observation_count", 0)

                # Card value lookup
                cards = _build_all_kpi_cards(
                    kpi_daily=kpi_daily,
                    kpi_dept=dept_code,
                    selected_date=None,
                    pkg_date=None,
                    primary_pkg=None,
                    threshold_cfg=threshold_cfg,
                    hospital_id=HOSPITAL,
                    year=YEAR,
                    month=month,
                )
                card = next((c for c in cards if c["kpi_id"] == kpi_id), None)
                card_value = card["latest_value"] if card else "N/A"
                card_unit = card["unit"] if card else ""
                card_status = card["threshold_status"] if card else ""

                # Match logic
                if canonical_value is None or pd.isna(canonical_value):
                    value_expected = "N/A"
                    value_displayed = card_value
                    values_match = card_value in ("Insufficient Data", "N/A")
                    missing_reason = "No valid monthly data in canonical table"
                else:
                    # Card value is formatted to 1 decimal place; compare rounded values
                    value_expected = f"{canonical_value:.4f}"
                    value_displayed = str(card_value)
                    try:
                        card_float = float(card_value)
                        canonical_rounded = round(float(canonical_value), 1)
                        values_match = abs(card_float - canonical_rounded) < 0.001
                    except (ValueError, TypeError):
                        values_match = False
                    missing_reason = ""

                row = {
                    "hospital": HOSPITAL,
                    "department": dept_name,
                    "department_code": dept_code,
                    "year": YEAR,
                    "month": month,
                    "kpi_id": kpi_id,
                    "kpi_name": kpi_name,
                    "valid_observation_count": valid_obs,
                    "canonical_monthly_value": canonical_value if canonical_value is not None and pd.notna(canonical_value) else "N/A",
                    "card_value": card_value,
                    "unit": canonical_unit or card_unit,
                    "calculation_status": canonical_status,
                    "value_expected": value_expected,
                    "value_displayed": value_displayed,
                    "values_match": values_match,
                    "missing_reason": missing_reason,
                    "validation_note": "",
                }
                rows.append(row)

    out_path = os.path.join(OUTPUT_DIR, "step_3b_patient_experience_kpi_audit.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out_path}")

    # Summary
    for kpi_id, kpi_name in [("kpi_005", "Patient Complaint Rate"), ("kpi_006", "Patient Satisfaction Score")]:
        sub = [r for r in rows if r["kpi_id"] == kpi_id]
        with_data = [r for r in sub if r["missing_reason"] == ""]
        matches = [r for r in with_data if r["values_match"]]
        mismatches = [r for r in with_data if not r["values_match"]]
        print(f"\n{kpi_name}:")
        print(f"  Total rows: {len(sub)}")
        print(f"  With canonical data: {len(with_data)}")
        print(f"  Card matches canonical: {len(matches)}")
        print(f"  Card mismatches canonical: {len(mismatches)}")
        if mismatches:
            for m in mismatches:
                print(f"    MISMATCH: {m['department']} {m['year']}-{m['month']:02d} expected={m['value_expected']} got={m['value_displayed']}")


if __name__ == "__main__":
    main()
