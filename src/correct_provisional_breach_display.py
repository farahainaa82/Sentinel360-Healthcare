"""
Sentinel360 Step 2B-3 Correction — Provisional Breach Display Governance

Refreshes department-risk daily output with governed display fields that
correctly distinguish dominant-driver provisional status from department-wide
provisional-KPI presence.

Does NOT modify:
- accepted risk scores
- department risk scores
- rankings, tiers, urgency
- dominant-driver selection
"""

import pandas as pd
import os
from datetime import datetime


def correct_provisional_breach_display(
    dept_risk_path: str = "data/analytical/analytical_department_risk_daily.csv",
    kpi_scores_path: str = "data/analytical/analytical_kpi_risk_scores_daily.csv",
    output_path: str = "data/analytical/analytical_department_risk_daily.csv",
):
    dept = pd.read_csv(dept_risk_path)
    kpi = pd.read_csv(kpi_scores_path)

    # ------------------------------------------------------------------
    # 1. Join dominant KPI threshold_state from KPI scores
    # ------------------------------------------------------------------
    dominant_kpi = kpi[[
        "hospital_id", "department_id", "reporting_date",
        "kpi_id", "threshold_state", "threshold_is_provisional",
    ]].copy()

    merged = dept.merge(
        dominant_kpi,
        left_on=["hospital_id", "department_id", "reporting_date", "dominant_kpi_id"],
        right_on=["hospital_id", "department_id", "reporting_date", "kpi_id"],
        how="left",
        suffixes=("", "_dom"),
    )

    # ------------------------------------------------------------------
    # 2. Build dominant_threshold_is_provisional
    # ------------------------------------------------------------------
    # Use the already-correct dominant_driver_is_provisional
    merged["dominant_threshold_is_provisional"] = merged["dominant_driver_is_provisional"].fillna(False)

    # ------------------------------------------------------------------
    # 3. Build dominant_breach_type_governed
    # ------------------------------------------------------------------
    def _governed_breach(row):
        state = row.get("threshold_state")
        is_prov = row.get("dominant_threshold_is_provisional", False)

        if pd.isna(state) or state in ("Green", "Normal Operating Band", "Unavailable", "Not Assessed"):
            return "No Breach"

        if is_prov:
            return "Provisional Breach"

        if state in ("Amber", "Lower Amber", "Upper Amber"):
            return "Amber Condition"
        if state == "Red":
            return "Red Breach"
        if state == "Critical Capacity Pressure":
            return "Critical Capacity Breach"
        if state == "Low Utilisation":
            return "Low Utilisation Condition"
        return "No Breach"

    merged["dominant_breach_type_governed"] = merged.apply(_governed_breach, axis=1)

    # ------------------------------------------------------------------
    # 4. Build dominant_driver_governance_warning
    # ------------------------------------------------------------------
    def _governed_warning(row):
        is_prov = row.get("dominant_threshold_is_provisional", False)
        if is_prov:
            return "Dominant risk driver uses provisional threshold"
        return "Dominant risk driver uses approved threshold"

    merged["dominant_driver_governance_warning"] = merged.apply(_governed_warning, axis=1)

    # ------------------------------------------------------------------
    # 5. Build dominant_driver_reason_governed
    # ------------------------------------------------------------------
    def _governed_reason(row):
        parts = []
        state = row.get("threshold_state")
        if pd.notna(state) and state not in ("Green", "Normal Operating Band", "Unavailable", "Not Assessed"):
            parts.append(f"threshold={state}")

        breach = row.get("dominant_breach_type_governed")
        if breach and breach != "No Breach":
            parts.append(f"breach={breach}")

        watch = row.get("watch_condition_type")
        if pd.notna(watch) and watch not in ("None", "No Watch"):
            parts.append(f"watch={watch}")

        if not parts:
            return "No current adverse indicators"
        return "; ".join(parts)

    merged["dominant_driver_reason_governed"] = merged.apply(_governed_reason, axis=1)

    # ------------------------------------------------------------------
    # 6. Clean up merge artifacts
    # ------------------------------------------------------------------
    drop_cols = [c for c in merged.columns if c.endswith("_dom") or c == "kpi_id_dom"]
    for c in drop_cols:
        if c in merged.columns:
            merged = merged.drop(columns=[c])

    # Remove any duplicated columns from merge
    merged = merged.loc[:, ~merged.columns.duplicated()]

    # ------------------------------------------------------------------
    # 7. Preserve column order: new columns appended
    # ------------------------------------------------------------------
    new_cols = [
        "dominant_threshold_is_provisional",
        "dominant_breach_type_governed",
        "dominant_driver_governance_warning",
        "dominant_driver_reason_governed",
    ]
    for c in new_cols:
        if c not in merged.columns:
            raise RuntimeError(f"Expected column {c} missing after merge")

    # ------------------------------------------------------------------
    # 8. Write
    # ------------------------------------------------------------------
    merged.to_csv(output_path, index=False)
    print(f"[{datetime.now().isoformat()}] Wrote {len(merged)} rows with {len(new_cols)} new governed fields to {output_path}")

    # Validation summary
    print("\n--- Validation Summary ---")
    for kpi_id in ["kpi_001", "kpi_002", "kpi_004", "kpi_006"]:
        sub = merged[merged["dominant_kpi_id"] == kpi_id]
        prov_count = sub["dominant_breach_type_governed"].eq("Provisional Breach").sum()
        print(f"  {kpi_id} dominant: {len(sub)} rows, Provisional Breach count = {prov_count}")
    for kpi_id in ["kpi_003", "kpi_005"]:
        sub = merged[merged["dominant_kpi_id"] == kpi_id]
        prov_count = sub["dominant_breach_type_governed"].eq("Provisional Breach").sum()
        print(f"  {kpi_id} dominant: {len(sub)} rows, Provisional Breach count = {prov_count}")

    return merged


if __name__ == "__main__":
    correct_provisional_breach_display()
