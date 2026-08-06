import pandas as pd
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.streamlit_executive_data_loader import load_all_data, get_kpi_monthly_actual_table, _display_department
from src.streamlit_executive_page_controller import _build_all_kpi_cards, load_kpi_threshold_config

def run_audit():
    data = load_all_data()
    kpi_daily = data.get("kpi_daily", pd.DataFrame())
    threshold_cfg = load_kpi_threshold_config()
    monthly_table = get_kpi_monthly_actual_table(kpi_daily)

    departments = ["DEPT-ADM", "DEPT-ICU", "DEPT-MED", "DEPT-SURG", "DEPT-ED", "DEPT-PAED", "DEPT-ORTHO", "DEPT-ADMIN"]
    kpi_ids = ["kpi_001", "kpi_002", "kpi_003", "kpi_004", "kpi_005", "kpi_006"]
    months = list(range(1, 8))  # Jan-Jul

    rows = []
    for dept in departments:
        for kpi_id in kpi_ids:
            for month in months:
                row = {
                    "hospital": "HOSP-001",
                    "department": _display_department(dept),
                    "department_code": dept,
                    "kpi_id": kpi_id,
                    "kpi_name": threshold_cfg.get(kpi_id, {}).get("kpi_name", kpi_id),
                    "year": 2025,
                    "month": month,
                    "monthly_actual_value": None,
                    "card_value": None,
                    "chart_value": None,
                    "status_input_value": None,
                    "interpretation_input_value": None,
                    "card_matches_month": False,
                    "chart_matches_month": False,
                    "all_values_match": False,
                    "valid_observation_count": None,
                    "source_date_start": None,
                    "source_date_end": None,
                    "mismatch_reason": None,
                }

                # Monthly actual from canonical table
                if not monthly_table.empty:
                    mask = (
                        (monthly_table["hospital"] == "HOSP-001")
                        & (monthly_table["department_code"] == dept)
                        & (monthly_table["kpi_id"] == kpi_id)
                        & (monthly_table["year"] == 2025)
                        & (monthly_table["month"] == month)
                    )
                    m_rows = monthly_table[mask]
                    if not m_rows.empty:
                        row["monthly_actual_value"] = round(m_rows.iloc[0]["monthly_actual_value"], 4)
                        row["valid_observation_count"] = m_rows.iloc[0]["valid_observation_count"]
                        row["source_date_start"] = m_rows.iloc[0]["first_date"]
                        row["source_date_end"] = m_rows.iloc[0]["last_date"]

                # Card value from _build_all_kpi_cards
                cards = _build_all_kpi_cards(
                    kpi_daily, dept, None, None, None, threshold_cfg,
                    hospital_id="HOSP-001", year=2025, month=month,
                )
                card = [c for c in cards if c["kpi_id"] == kpi_id]
                if card:
                    c = card[0]
                    row["card_value"] = c.get("latest_value_raw")
                    row["status_input_value"] = c.get("threshold_status")
                    row["interpretation_input_value"] = c.get("threshold_status")
                    # Chart value from annual_df
                    annual_df = c.get("annual_df", pd.DataFrame())
                    if not annual_df.empty and "month" in annual_df.columns:
                        chart_rows = annual_df[annual_df["month"] == month]
                        if not chart_rows.empty:
                            row["chart_value"] = chart_rows.iloc[0].get("monthly_value")

                # Match checks
                if pd.notna(row["monthly_actual_value"]):
                    if pd.notna(row["card_value"]):
                        row["card_matches_month"] = abs(row["monthly_actual_value"] - float(row["card_value"])) < 0.001
                    else:
                        row["card_matches_month"] = False
                    if pd.notna(row["chart_value"]):
                        row["chart_matches_month"] = abs(row["monthly_actual_value"] - float(row["chart_value"])) < 0.001
                    else:
                        row["chart_matches_month"] = False
                    row["all_values_match"] = row["card_matches_month"] and row["chart_matches_month"]
                    if not row["all_values_match"]:
                        reasons = []
                        if not row["card_matches_month"]:
                            reasons.append("Card value differs from monthly actual")
                        if not row["chart_matches_month"]:
                            reasons.append("Chart value differs from monthly actual")
                        row["mismatch_reason"] = "; ".join(reasons) if reasons else "Missing card or chart value"
                else:
                    row["card_matches_month"] = False
                    row["chart_matches_month"] = False
                    row["all_values_match"] = False
                    row["mismatch_reason"] = "No valid monthly data for this department-KPI-month combination"

                rows.append(row)

    df = pd.DataFrame(rows)
    out_path = PROJECT_ROOT / "outputs" / "streamlit" / "step_3b_month_filter_alignment_audit.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Audit written to {out_path}")
    print(f"Total rows: {len(df)}")
    match_count = df["all_values_match"].sum()
    print(f"All values match: {match_count} / {len(df)}")

if __name__ == "__main__":
    run_audit()
