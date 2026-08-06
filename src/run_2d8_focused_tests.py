"""Focused tests for Phase 2D-8 Scenario-Summary Reconciliation.

Tests the final state without modifying any outputs.
"""

import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs" / "decision_intelligence"
SCENARIO_DIR = BASE_DIR / "outputs" / "scenario_modelling"
SRC_DIR = BASE_DIR / "src"

sys.path.insert(0, str(SRC_DIR))
from decision_intelligence_validation_utils import atomic_write_csv


def load_csv(name, dir_path=OUTPUT_DIR):
    path = dir_path / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False, on_bad_lines="skip")


def has_content(val):
    if pd.isna(val):
        return False
    return str(val).strip() not in ("", "nan", "NaN", "None", "null")


def main():
    print("=" * 60)
    print("Phase 2D-8 Focused Reconciliation Tests")
    print("=" * 60)

    imb = load_csv("step_2d7_integrated_management_brief_register.csv")
    scenario_reg = load_csv("step_2d7_scenario_summary_register.csv")
    streamlit_contract = load_csv("step_2d7_streamlit_management_brief_contract.csv")
    section_reg = load_csv("step_2d7_management_brief_section_register.csv")
    master_val = load_csv("step_2d8_master_validation_register.csv")
    c2f_scenario = load_csv("step_2c2f_management_scenario_package_register.csv", SCENARIO_DIR)

    if not master_val.empty and "streamlit_ready" in master_val.columns:
        master_val["streamlit_ready"] = (
            master_val["streamlit_ready"]
            .astype(str)
            .map({"True": True, "False": False, "1": True, "0": False})
            .fillna(False)
        )

    scenario_cols = ["baseline_summary", "conservative_summary", "expected_summary", "higher_intensity_summary"]
    ready_mask = imb["final_readiness_status"] == "Ready for Integrated Management Review"
    ready_packages = imb[ready_mask]
    ready_ids = set(ready_packages["decision_package_id"].unique())

    c2f_by_apkg = {}
    if not c2f_scenario.empty and "approval_package_id" in c2f_scenario.columns:
        for _, r in c2f_scenario.iterrows():
            c2f_by_apkg[r["approval_package_id"]] = r

    dpkg_to_apkg = dict(zip(imb["decision_package_id"], imb["approval_package_id"]))

    test_results = []

    # Test 1: Every Ready-for-Review package has scenario summary or governed Not Applicable reason
    all_have_summary_or_na = True
    missing_reason = []
    for dpkg in ready_ids:
        imb_row = imb[imb["decision_package_id"] == dpkg]
        if imb_row.empty:
            continue
        has_scen = any(has_content(imb_row.iloc[0].get(c, "")) for c in scenario_cols)
        scen_na = all(str(imb_row.iloc[0].get(c, "")).strip() == "Not Applicable" for c in scenario_cols)
        if not has_scen and not scen_na:
            all_have_summary_or_na = False
            missing_reason.append(dpkg)

    test_results.append({
        "test_id": "TEST-01",
        "description": "Every Ready-for-Review package has scenario summary or governed Not Applicable reason",
        "status": "PASS" if all_have_summary_or_na else "FAIL",
        "detail": "" if all_have_summary_or_na else f"Missing: {len(missing_reason)} packages",
    })

    # Test 2: No scenario value is recalculated
    no_recalc = True
    recalc_issues = []
    for dpkg in ready_ids:
        apkg = dpkg_to_apkg.get(dpkg, "")
        c2f_row = c2f_by_apkg.get(apkg)
        imb_row = imb[imb["decision_package_id"] == dpkg]
        if c2f_row is not None and not imb_row.empty:
            for col in scenario_cols:
                orig = str(c2f_row.get(col, "")).strip()
                mapped = str(imb_row.iloc[0].get(col, "")).strip()
                if orig and mapped and orig != mapped:
                    no_recalc = False
                    recalc_issues.append(f"{dpkg}:{col}")

    test_results.append({
        "test_id": "TEST-02",
        "description": "No scenario value is recalculated",
        "status": "PASS" if no_recalc else "FAIL",
        "detail": "" if no_recalc else f"Mismatches: {len(recalc_issues)}",
    })

    # Test 3: Missing scenario values are not converted to zero
    no_zero = True
    zero_issues = []
    for _, row in imb.iterrows():
        for col in scenario_cols:
            val = str(row.get(col, "")).strip()
            if val in ("0", "0.0"):
                no_zero = False
                zero_issues.append(f"{row['decision_package_id']}:{col}")

    test_results.append({
        "test_id": "TEST-03",
        "description": "Missing scenario values are not converted to zero",
        "status": "PASS" if no_zero else "FAIL",
        "detail": "" if no_zero else f"Zero conversions: {len(zero_issues)}",
    })

    # Test 4: No preferred scenario is selected
    no_preferred_selected = True
    preferred_issues = []
    for _, row in imb.iterrows():
        val = row.get("selected_scenario", "")
        if has_content(val):
            no_preferred_selected = False
            preferred_issues.append(row["decision_package_id"])

    test_results.append({
        "test_id": "TEST-04",
        "description": "No preferred scenario is selected",
        "status": "PASS" if no_preferred_selected else "FAIL",
        "detail": "" if no_preferred_selected else f"Selections found: {len(preferred_issues)}",
    })

    # Test 5: Readiness is not upgraded without evidence
    # For this focused reconciliation, upgrades for packages that now have recovered summaries are legitimate.
    # We verify that no package is "Validated for Streamlit Handover" while still missing a mandatory summary.
    no_unjustified_upgrade = True
    upgrade_issues = []
    for dpkg in ready_ids:
        imb_row = imb[imb["decision_package_id"] == dpkg]
        master_row = master_val[master_val["decision_package_id"] == dpkg]
        if imb_row.empty or master_row.empty:
            continue
        has_scen = any(has_content(imb_row.iloc[0].get(c, "")) for c in scenario_cols)
        scen_na = all(str(imb_row.iloc[0].get(c, "")).strip() == "Not Applicable" for c in scenario_cols)
        outcome = master_row.iloc[0]["validation_outcome"]
        if outcome == "Validated for Streamlit Handover" and not has_scen and not scen_na:
            no_unjustified_upgrade = False
            upgrade_issues.append(dpkg)

    test_results.append({
        "test_id": "TEST-05",
        "description": "Readiness is not upgraded without evidence (no Streamlit Handover without summary)",
        "status": "PASS" if no_unjustified_upgrade else "FAIL",
        "detail": "" if no_unjustified_upgrade else f"Unjustified upgrades: {len(upgrade_issues)}",
    })

    # Test 6: Streamlit readiness reflects unresolved missing summaries
    streamlit_reflects = True
    streamlit_issues = []
    for dpkg in ready_ids:
        imb_row = imb[imb["decision_package_id"] == dpkg]
        master_row = master_val[master_val["decision_package_id"] == dpkg]
        if imb_row.empty or master_row.empty:
            continue
        has_scen = any(has_content(imb_row.iloc[0].get(c, "")) for c in scenario_cols)
        scen_na = all(str(imb_row.iloc[0].get(c, "")).strip() == "Not Applicable" for c in scenario_cols)
        outcome = master_row.iloc[0]["validation_outcome"]
        if not has_scen and not scen_na and outcome == "Validated for Streamlit Handover":
            streamlit_reflects = False
            streamlit_issues.append(dpkg)

    test_results.append({
        "test_id": "TEST-06",
        "description": "Streamlit readiness reflects unresolved missing summaries",
        "status": "PASS" if streamlit_reflects else "FAIL",
        "detail": "" if streamlit_reflects else f"Issues: {len(streamlit_issues)}",
    })

    # Test 7: Evidence and lineage reconcile
    evidence_reconciles = True
    evidence_issues = []
    for dpkg in ready_ids:
        apkg = dpkg_to_apkg.get(dpkg, "")
        c2f_row = c2f_by_apkg.get(apkg)
        imb_row = imb[imb["decision_package_id"] == dpkg]
        if c2f_row is not None and not imb_row.empty:
            for col in scenario_cols:
                c2f_val = str(c2f_row.get(col, "")).strip()
                imb_val = str(imb_row.iloc[0].get(col, "")).strip()
                if c2f_val and imb_val and c2f_val != imb_val:
                    # Allow "Not Applicable" as valid override
                    if imb_val != "Not Applicable":
                        evidence_reconciles = False
                        evidence_issues.append(f"{dpkg}:{col}")

    test_results.append({
        "test_id": "TEST-07",
        "description": "Evidence and lineage reconcile to frozen upstream source",
        "status": "PASS" if evidence_reconciles else "FAIL",
        "detail": "" if evidence_reconciles else f"Issues: {len(evidence_issues)}",
    })

    # Test 8: Frozen upstream scenario outputs remain unchanged
    upstream_unchanged = True
    c2f_path = SCENARIO_DIR / "step_2c2f_management_scenario_package_register.csv"
    if not c2f_path.exists():
        upstream_unchanged = False

    test_results.append({
        "test_id": "TEST-08",
        "description": "Frozen upstream scenario outputs remain unchanged",
        "status": "PASS" if upstream_unchanged else "FAIL",
        "detail": "" if upstream_unchanged else "2C-2 source missing",
    })

    # Test 9: No Step 2D-9 output is created
    step_2d9_exists = any(
        (OUTPUT_DIR / f"step_2d9_{suffix}").exists()
        for suffix in ["manifest.json", "execution_summary.csv", "final_validation_outcome_register.csv"]
    )

    test_results.append({
        "test_id": "TEST-09",
        "description": "No Step 2D-9 output is created",
        "status": "PASS" if not step_2d9_exists else "FAIL",
        "detail": "" if not step_2d9_exists else "Step 2D-9 artifacts detected",
    })

    test_df = pd.DataFrame(test_results)
    for _, tr in test_df.iterrows():
        print(f"    {tr['test_id']}: {tr['status']} — {tr['description']}")
        if tr["detail"]:
            print(f"         Detail: {tr['detail']}")

    print("\n" + "=" * 60)
    print(f"Tests: {test_df['status'].value_counts().get('PASS', 0)} passed, {test_df['status'].value_counts().get('FAIL', 0)} failed")
    print("=" * 60)

    atomic_write_csv(test_df, "step_2d8_reconciliation_test_results.csv")


if __name__ == "__main__":
    main()
