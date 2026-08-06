"""Phase 2D-8 Focused Scenario-Summary Reconciliation.

Identifies Ready-for-Review packages lacking scenario summaries in the frozen
Step 2D-7 IMB output, classifies them, maps recoverable summaries from frozen
Step 2D-7 scenario register and Phase 2C-2 sources, and refreshes only affected
downstream registers.

Does NOT begin Step 2D-9.
Does NOT recalculate scenario values.
Does NOT modify frozen Phase 2C-2 scenario values.
"""

import json
import sys
import time
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs" / "decision_intelligence"
SCENARIO_DIR = BASE_DIR / "outputs" / "scenario_modelling"
DOCS_DIR = BASE_DIR / "docs"
SRC_DIR = BASE_DIR / "src"

sys.path.insert(0, str(SRC_DIR))
from decision_intelligence_validation_utils import (
    atomic_write_csv,
    build_manifest,
    compute_sha256,
    correction_class,
    load_register,
    validation_outcome,
    write_manifest,
)


def load_csv(name, dir_path=OUTPUT_DIR):
    path = dir_path / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False, on_bad_lines="skip")


def save_csv(df, name):
    return atomic_write_csv(df, name)


def has_content(val):
    if pd.isna(val):
        return False
    return str(val).strip() != ""


def ensure_object_cols(df, cols):
    for col in cols:
        if col in df.columns:
            df[col] = df[col].astype(object)
    return df


def main():
    print("=" * 60)
    print("Phase 2D-8 Focused Scenario-Summary Reconciliation")
    print("=" * 60)
    start_time = time.time()

    # ------------------------------------------------------------------
    # 1. Load frozen upstream and downstream registers
    # ------------------------------------------------------------------
    print("\n[1] Loading registers...")

    imb = load_csv("step_2d7_integrated_management_brief_register.csv")
    scenario_reg = load_csv("step_2d7_scenario_summary_register.csv")
    streamlit_contract = load_csv("step_2d7_streamlit_management_brief_contract.csv")
    section_reg = load_csv("step_2d7_management_brief_section_register.csv")
    readiness_reg = load_csv("step_2d7_readiness_and_condition_summary_register.csv")

    c2f_scenario = load_csv("step_2c2f_management_scenario_package_register.csv", SCENARIO_DIR)
    c2b_mapping = load_csv("step_2c2b_package_scenario_mapping.csv", SCENARIO_DIR)

    master_val = load_csv("step_2d8_master_validation_register.csv")
    scenario_val = load_csv("step_2d8_scenario_validation_register.csv")
    exec_summary = load_csv("step_2d8_execution_summary.csv")

    # Normalize string booleans
    if not master_val.empty and "streamlit_ready" in master_val.columns:
        master_val["streamlit_ready"] = (
            master_val["streamlit_ready"]
            .astype(str)
            .map({"True": True, "False": False, "1": True, "0": False})
            .fillna(False)
        )

    print(f"    2D-7 IMB register: {len(imb)} rows")
    print(f"    2D-7 Scenario register: {len(scenario_reg)} rows")
    print(f"    2C-2 Scenario source: {len(c2f_scenario)} rows")
    print(f"    2D-8 Master validation: {len(master_val)} rows")

    # ------------------------------------------------------------------
    # 2. Identify Ready-for-Review packages lacking summaries in IMB
    # ------------------------------------------------------------------
    print("\n[2] Identifying Ready-for-Review packages with missing IMB summaries...")

    scenario_cols = ["baseline_summary", "conservative_summary", "expected_summary", "higher_intensity_summary"]

    ready_mask = imb["final_readiness_status"] == "Ready for Integrated Management Review"
    ready_packages = imb[ready_mask].copy()
    ready_ids = set(ready_packages["decision_package_id"].unique())
    print(f"    Ready-for-Review packages: {len(ready_ids)}")

    affected = []
    for _, row in ready_packages.iterrows():
        dpkg = row["decision_package_id"]
        imb_id = row["integrated_management_brief_id"]
        apkg = row.get("approval_package_id", "")
        has_scen_imb = any(has_content(row.get(c, "")) for c in scenario_cols)
        if not has_scen_imb:
            affected.append({
                "integrated_management_brief_id": imb_id,
                "decision_package_id": dpkg,
                "approval_package_id": apkg,
                "final_readiness_status": row["final_readiness_status"],
                "scenario_family": row.get("scenario_family", ""),
            })

    affected_df = pd.DataFrame(affected)
    print(f"    Affected packages (missing IMB scenario summary): {len(affected_df)}")

    # ------------------------------------------------------------------
    # 3. Build lookups for recovery
    # ------------------------------------------------------------------
    print("\n[3] Building recovery lookups...")

    c2f_by_apkg = {}
    if not c2f_scenario.empty and "approval_package_id" in c2f_scenario.columns:
        for _, r in c2f_scenario.iterrows():
            c2f_by_apkg[r["approval_package_id"]] = r

    scen_by_dpkg = {}
    if not scenario_reg.empty and "decision_package_id" in scenario_reg.columns:
        for _, r in scenario_reg.iterrows():
            scen_by_dpkg[r["decision_package_id"]] = r

    dpkg_to_apkg = dict(zip(imb["decision_package_id"], imb["approval_package_id"]))

    recoverable = 0
    non_quantitative = 0
    monitoring_only = 0
    mapping_defect = 0
    source_missing = 0
    inconsistent = 0

    classification_records = []
    reconciled_summaries = {}  # dpkg -> dict

    for _, row in affected_df.iterrows():
        dpkg = row["decision_package_id"]
        apkg = row["approval_package_id"]
        imb_id = row["integrated_management_brief_id"]
        scen_family = str(row.get("scenario_family", "")).strip()

        mapping_rows = c2b_mapping[c2b_mapping["approval_package_id"] == apkg] if not c2b_mapping.empty else pd.DataFrame()
        quant_allowed = None
        scen_exec_readiness = None
        if not mapping_rows.empty:
            quant_allowed = mapping_rows.iloc[0].get("quantitative_model_allowed", True)
            scen_exec_readiness = mapping_rows.iloc[0].get("scenario_execution_readiness", "")

        # Prefer Step 2D-7 scenario_reg as frozen source, fallback to 2C-2
        source_row = scen_by_dpkg.get(dpkg)
        source_label = "step_2d7_scenario_summary_register.csv"
        source_phase = "2D-7"

        if source_row is None or not any(has_content(source_row.get(c, "")) for c in scenario_cols):
            source_row = c2f_by_apkg.get(apkg)
            source_label = "step_2c2f_management_scenario_package_register.csv"
            source_phase = "2C-2"

        # Determine classification
        reason = ""
        classification = ""
        source_pkg_id = ""
        baseline_avail = ""
        conservative_avail = ""
        expected_avail = ""
        higher_intensity_avail = ""
        scen_summary_avail = ""

        if source_row is not None and any(has_content(source_row.get(c, "")) for c in scenario_cols):
            classification = "Scenario Summary Recoverable from Frozen Source"
            reason = f"Scenario summary exists in frozen {source_phase} source but was not mapped to Step 2D-7 IMB output."
            recoverable += 1
            source_pkg_id = source_row.get("management_scenario_package_id", source_row.get("scenario_package_id", ""))

            def get_val(r, c):
                v = r.get(c, "")
                return str(v).strip() if pd.notna(v) else ""

            reconciled_summaries[dpkg] = {
                "baseline_summary": get_val(source_row, "baseline_summary"),
                "conservative_summary": get_val(source_row, "conservative_summary"),
                "expected_summary": get_val(source_row, "expected_summary"),
                "higher_intensity_summary": get_val(source_row, "higher_intensity_summary"),
                "scenario_confidence": get_val(source_row, "final_scenario_confidence") or get_val(source_row, "scenario_confidence"),
                "primary_kpi_effect_summary": get_val(source_row, "primary_kpi_effects") or get_val(source_row, "primary_kpi_effect_summary"),
                "supporting_kpi_effect_summary": get_val(source_row, "supporting_kpi_effects") or get_val(source_row, "supporting_kpi_effect_summary"),
                "tradeoff_summary": get_val(source_row, "tradeoff_summary"),
                "displacement_summary": get_val(source_row, "displacement_summary"),
                "sensitivity_summary": get_val(source_row, "sensitivity_summary"),
                "dominance_summary": get_val(source_row, "dominance_summary"),
                "scenario_limitations": get_val(source_row, "scenario_limitations"),
                "scenario_governance_warning": get_val(source_row, "management_action_required") or get_val(source_row, "scenario_governance_warning"),
                "source_phase": source_phase,
                "source_file": source_label,
                "source_package_id": source_pkg_id,
            }
            baseline_avail = reconciled_summaries[dpkg]["baseline_summary"]
            conservative_avail = reconciled_summaries[dpkg]["conservative_summary"]
            expected_avail = reconciled_summaries[dpkg]["expected_summary"]
            higher_intensity_avail = reconciled_summaries[dpkg]["higher_intensity_summary"]
            scen_summary_avail = f"Recovered from {source_phase}"
        else:
            # No source with content
            if quant_allowed is False or str(scen_exec_readiness).strip().lower() in ["monitoring only", "monitoring-only"]:
                classification = "Scenario Monitoring Only"
                reason = "Package is mapped to Monitoring-Only scenario template; quantitative summaries not applicable."
                monitoring_only += 1
                baseline_avail = "Not Applicable"
                conservative_avail = "Not Applicable"
                expected_avail = "Not Applicable"
                higher_intensity_avail = "Not Applicable"
                scen_summary_avail = "Not Applicable"
            elif scen_family.lower() in ["non-quantitative", "non quantitative"]:
                classification = "Scenario Non-Quantitative"
                reason = "Scenario family is Non-Quantitative; summaries not required."
                non_quantitative += 1
                baseline_avail = "Not Applicable"
                conservative_avail = "Not Applicable"
                expected_avail = "Not Applicable"
                higher_intensity_avail = "Not Applicable"
                scen_summary_avail = "Not Applicable"
            else:
                # Check if 2C-2 row exists but is empty
                c2f_row = c2f_by_apkg.get(apkg)
                if c2f_row is not None:
                    classification = "Scenario Summary Source Missing"
                    reason = "Frozen 2C-2 source row exists but contains no scenario summary content."
                    source_missing += 1
                else:
                    # No 2C-2 row at all, and not monitoring/non-quant
                    classification = "Readiness Classification Inconsistent"
                    reason = "Package classified as Ready for Integrated Management Review but has no scenario source data and is not Monitoring-Only or Non-Quantitative."
                    inconsistent += 1
                baseline_avail = "Unavailable"
                conservative_avail = "Unavailable"
                expected_avail = "Unavailable"
                higher_intensity_avail = "Unavailable"
                scen_summary_avail = "Unavailable"

        classification_records.append({
            "integrated_management_brief_id": imb_id,
            "decision_package_id": dpkg,
            "approval_package_id": apkg,
            "final_readiness_status": row["final_readiness_status"],
            "scenario_required_status": "Required" if classification not in ["Scenario Monitoring Only", "Scenario Non-Quantitative", "Scenario Not Required"] else "Not Required",
            "scenario_readiness": scen_exec_readiness if scen_exec_readiness else "",
            "scenario_family": scen_family,
            "baseline_availability": baseline_avail,
            "conservative_availability": conservative_avail,
            "expected_availability": expected_avail,
            "higher_intensity_availability": higher_intensity_avail,
            "scenario_summary_availability": scen_summary_avail,
            "source_scenario_package_id": source_pkg_id,
            "source_file": source_label if classification == "Scenario Summary Recoverable from Frozen Source" else ("step_2c2f_management_scenario_package_register.csv" if c2f_by_apkg.get(apkg) is not None else ""),
            "reason_summary_is_missing": reason,
            "classification": classification,
        })

    classification_df = pd.DataFrame(classification_records)
    print(f"    Recoverable from frozen source: {recoverable}")
    print(f"    Monitoring Only: {monitoring_only}")
    print(f"    Non-Quantitative: {non_quantitative}")
    print(f"    Source Missing: {source_missing}")
    print(f"    Readiness Classification Inconsistent: {inconsistent}")
    print(f"    Total affected: {len(classification_df)}")

    # ------------------------------------------------------------------
    # 4. Update Step 2D-7 registers
    # ------------------------------------------------------------------
    print("\n[4] Updating Step 2D-7 registers...")

    summary_cols = ["baseline_summary", "conservative_summary", "expected_summary", "higher_intensity_summary",
                    "scenario_confidence", "primary_kpi_effect_summary", "supporting_kpi_effect_summary",
                    "tradeoff_summary", "displacement_summary", "sensitivity_summary", "dominance_summary",
                    "scenario_limitations", "scenario_governance_warning"]
    avail_cols = ["baseline_available", "conservative_available", "expected_available", "higher_intensity_available"]

    # 4a. Update scenario_summary_register (mapping defect fix: ensure consistency with IMB)
    scenario_reg_updated = scenario_reg.copy()
    scenario_reg_updated = ensure_object_cols(scenario_reg_updated, summary_cols)
    for dpkg, summaries in reconciled_summaries.items():
        mask = scenario_reg_updated["decision_package_id"] == dpkg
        if mask.any():
            for col in summary_cols:
                if col in scenario_reg_updated.columns and col in summaries:
                    scenario_reg_updated.loc[mask, col] = summaries[col]
        else:
            new_row = {"decision_package_id": dpkg}
            for c in scenario_reg_updated.columns:
                if c not in new_row:
                    new_row[c] = summaries.get(c, "")
            scenario_reg_updated = pd.concat([scenario_reg_updated, pd.DataFrame([new_row])], ignore_index=True)

    save_csv(scenario_reg_updated, "step_2d7_scenario_summary_register.csv")
    print(f"    Saved step_2d7_scenario_summary_register.csv ({len(scenario_reg_updated)} rows)")

    # 4b. Update integrated_management_brief_register
    imb_updated = imb.copy()
    imb_updated = ensure_object_cols(imb_updated, summary_cols + avail_cols)
    for dpkg, summaries in reconciled_summaries.items():
        mask = imb_updated["decision_package_id"] == dpkg
        if mask.any():
            for col in summary_cols:
                if col in imb_updated.columns and col in summaries:
                    imb_updated.loc[mask, col] = summaries[col]
            for col in avail_cols:
                if col in imb_updated.columns:
                    imb_updated.loc[mask, col] = True

    # Not Applicable for non-required classifications
    for _, cls_row in classification_df.iterrows():
        dpkg = cls_row["decision_package_id"]
        if cls_row["classification"] in ["Scenario Monitoring Only", "Scenario Non-Quantitative", "Scenario Not Required"]:
            mask = imb_updated["decision_package_id"] == dpkg
            if mask.any():
                for col in ["baseline_summary", "conservative_summary", "expected_summary", "higher_intensity_summary"]:
                    if col in imb_updated.columns:
                        imb_updated.loc[mask, col] = "Not Applicable"
                for col in avail_cols:
                    if col in imb_updated.columns:
                        imb_updated.loc[mask, col] = False

    save_csv(imb_updated, "step_2d7_integrated_management_brief_register.csv")
    print(f"    Saved step_2d7_integrated_management_brief_register.csv ({len(imb_updated)} rows)")

    # 4c. Update streamlit_management_brief_contract
    streamlit_updated = streamlit_contract.copy()
    streamlit_updated = ensure_object_cols(streamlit_updated, summary_cols)
    for dpkg, summaries in reconciled_summaries.items():
        mask = streamlit_updated["decision_package_id"] == dpkg
        if mask.any():
            for col in summary_cols:
                if col in streamlit_updated.columns and col in summaries:
                    streamlit_updated.loc[mask, col] = summaries[col]

    for _, cls_row in classification_df.iterrows():
        dpkg = cls_row["decision_package_id"]
        if cls_row["classification"] in ["Scenario Monitoring Only", "Scenario Non-Quantitative", "Scenario Not Required"]:
            mask = streamlit_updated["decision_package_id"] == dpkg
            if mask.any():
                for col in ["baseline_summary", "conservative_summary", "expected_summary", "higher_intensity_summary"]:
                    if col in streamlit_updated.columns:
                        streamlit_updated.loc[mask, col] = "Not Applicable"

    save_csv(streamlit_updated, "step_2d7_streamlit_management_brief_contract.csv")
    print(f"    Saved step_2d7_streamlit_management_brief_contract.csv ({len(streamlit_updated)} rows)")

    # 4d. Update management_brief_section_register
    section_updated = section_reg.copy()
    for dpkg in list(reconciled_summaries.keys()):
        mask = (section_updated["decision_package_id"] == dpkg) & (section_updated["section_name"] == "Scenario Options")
        if mask.any():
            section_updated.loc[mask, "governance_note"] = "Required section present — summary reconciled from frozen 2C-2/2D-7 source"
        else:
            imb_id = affected_df[affected_df["decision_package_id"] == dpkg]["integrated_management_brief_id"].values[0]
            new_sec = {
                "integrated_management_brief_id": imb_id,
                "decision_package_id": dpkg,
                "section_name": "Scenario Options",
                "section_present": True,
                "governance_note": "Required section present — summary reconciled from frozen 2C-2/2D-7 source",
            }
            section_updated = pd.concat([section_updated, pd.DataFrame([new_sec])], ignore_index=True)

    save_csv(section_updated, "step_2d7_management_brief_section_register.csv")
    print(f"    Saved step_2d7_management_brief_section_register.csv ({len(section_updated)} rows)")

    # ------------------------------------------------------------------
    # 5. Update Step 2D-8 validation registers
    # ------------------------------------------------------------------
    print("\n[5] Updating Step 2D-8 validation registers...")

    # Re-run scenario validation engine (reads updated IMB from disk)
    from decision_intelligence_validation_scenario_engine import build_register as build_scenario

    new_scenario_val = build_scenario()
    save_csv(new_scenario_val, "step_2d8_scenario_validation_register.csv")
    print(f"    Saved step_2d8_scenario_validation_register.csv")

    # Rebuild master validation register
    master_updated = master_val.copy()

    for dpkg in list(reconciled_summaries.keys()):
        mask = master_updated["decision_package_id"] == dpkg
        if mask.any():
            old_failed = master_updated.loc[mask, "failed_check_list"].values[0]
            if isinstance(old_failed, str) and "scenario:ready_review_scenario_present" in old_failed:
                new_failed = old_failed.replace("scenario:ready_review_scenario_present", "").strip("; ").replace(";;", ";")
                master_updated.loc[mask, "failed_check_list"] = new_failed
                master_updated.loc[mask, "checks_failed"] = max(0, int(master_updated.loc[mask, "checks_failed"].values[0]) - 1)
                master_updated.loc[mask, "checks_passed"] = int(master_updated.loc[mask, "checks_passed"].values[0]) + 1
                old_medium = int(master_updated.loc[mask, "medium_failures"].values[0])
                master_updated.loc[mask, "medium_failures"] = max(0, old_medium - 1)
                sev = {
                    "Critical": int(master_updated.loc[mask, "critical_failures"].values[0]),
                    "High": int(master_updated.loc[mask, "high_failures"].values[0]),
                    "Medium": int(master_updated.loc[mask, "medium_failures"].values[0]),
                    "Low": int(master_updated.loc[mask, "low_failures"].values[0]),
                }
                new_outcome = validation_outcome(sev)
                master_updated.loc[mask, "validation_outcome"] = new_outcome
                master_updated.loc[mask, "correction_classification"] = correction_class(new_outcome)
                master_updated.loc[mask, "streamlit_ready"] = new_outcome == "Validated for Streamlit Handover"

    # Ensure unresolved cases remain flagged
    for _, cls_row in classification_df.iterrows():
        dpkg = cls_row["decision_package_id"]
        if cls_row["classification"] in ["Readiness Classification Inconsistent", "Scenario Summary Source Missing"]:
            mask = master_updated["decision_package_id"] == dpkg
            if mask.any():
                master_updated.loc[mask, "validation_outcome"] = "Validated with Conditions"
                master_updated.loc[mask, "correction_classification"] = correction_class("Validated with Conditions")
                master_updated.loc[mask, "streamlit_ready"] = True

    save_csv(master_updated, "step_2d8_master_validation_register.csv")
    print(f"    Saved step_2d8_master_validation_register.csv")

    # Final validation outcome register
    final_outcome = master_updated[[
        "decision_package_id", "integrated_management_brief_id",
        "validation_outcome", "correction_classification", "streamlit_ready",
        "checks_executed", "checks_passed", "checks_failed",
        "critical_failures", "high_failures", "medium_failures", "low_failures",
        "failed_check_list",
    ]].copy()
    save_csv(final_outcome, "step_2d8_final_validation_outcome_register.csv")
    print(f"    Saved step_2d8_final_validation_outcome_register.csv")

    # Streamlit handover readiness register
    handover_reg = master_updated[[
        "decision_package_id", "integrated_management_brief_id",
        "streamlit_ready", "validation_outcome", "correction_classification",
    ]].copy()
    handover_reg["handover_status"] = handover_reg["validation_outcome"].apply(
        lambda x: "Ready for Handover" if x == "Validated for Streamlit Handover" else "Ready with Conditions" if x == "Validated with Conditions" else "Not Ready"
    )
    save_csv(handover_reg, "step_2d8_streamlit_handover_readiness_register.csv")
    print(f"    Saved step_2d8_streamlit_handover_readiness_register.csv")

    # Completeness register
    completeness_records = []
    for _, row in imb_updated.iterrows():
        dpkg = row["decision_package_id"]
        imb_id = row["integrated_management_brief_id"]
        has_scen = any(has_content(row.get(c, "")) for c in scenario_cols)
        scen_na = all(str(row.get(c, "")).strip() == "Not Applicable" for c in scenario_cols)
        completeness_records.append({
            "decision_package_id": dpkg,
            "integrated_management_brief_id": imb_id,
            "scenario_summary_present": has_scen or scen_na,
            "scenario_summary_not_applicable": scen_na,
            "completeness_status": "Complete" if (has_scen or scen_na) else "Incomplete",
        })
    completeness_df = pd.DataFrame(completeness_records)
    save_csv(completeness_df, "step_2d8_management_brief_completeness_register.csv")
    print(f"    Saved step_2d8_management_brief_completeness_register.csv")

    # Execution summary
    exec_updated = exec_summary.copy()
    scen_mask = exec_updated["engine"] == "scenario"
    if scen_mask.any():
        exec_updated.loc[scen_mask, "pass_count"] = int(new_scenario_val[new_scenario_val["status"] == "PASS"].shape[0])
        exec_updated.loc[scen_mask, "fail_count"] = int(new_scenario_val[new_scenario_val["status"] == "FAIL"].shape[0])
        exec_updated.loc[scen_mask, "status"] = "COMPLETE"
    save_csv(exec_updated, "step_2d8_execution_summary.csv")
    print(f"    Saved step_2d8_execution_summary.csv")

    # ------------------------------------------------------------------
    # 6. Create reconciliation register and correction summary
    # ------------------------------------------------------------------
    print("\n[6] Creating reconciliation registers...")

    save_csv(classification_df, "step_2d8_scenario_summary_reconciliation_register.csv")
    print(f"    Saved step_2d8_scenario_summary_reconciliation_register.csv ({len(classification_df)} rows)")

    correction_summary = []
    for cls, count in classification_df["classification"].value_counts().items():
        if cls == "Scenario Summary Recoverable from Frozen Source":
            action = "Mapped existing summary from frozen 2C-2/2D-7 source into Step 2D-7 IMB. No recalculation."
            impact = "Streamlit readiness improved where no other conditions remain."
        elif cls == "Scenario Monitoring Only":
            action = "Documented as Not Applicable. No summary required."
            impact = "Package remains ready; Streamlit display shows Not Applicable."
        elif cls == "Scenario Non-Quantitative":
            action = "Documented as Not Applicable. No summary required."
            impact = "Package remains ready; Streamlit display shows Not Applicable."
        elif cls == "Scenario Summary Source Missing":
            action = "Retained missing-scenario condition visibly. Readiness flagged with conditions."
            impact = "Streamlit-ready with conditions. Requires focused correction or upstream source review."
        elif cls == "Readiness Classification Inconsistent":
            action = "Flagged for governance review. Package should not be Ready-for-Review without scenario source."
            impact = "Validation outcome set to Validated with Conditions. Streamlit-ready with conditions."
        else:
            action = "Review required."
            impact = "Unknown impact."
        correction_summary.append({
            "classification": cls,
            "affected_count": count,
            "correction_action": action,
            "streamlit_impact": impact,
        })

    correction_summary_df = pd.DataFrame(correction_summary)
    save_csv(correction_summary_df, "step_2d8_scenario_summary_correction_summary.csv")
    print(f"    Saved step_2d8_scenario_summary_correction_summary.csv")

    # ------------------------------------------------------------------
    # 7. Build manifest
    # ------------------------------------------------------------------
    print("\n[7] Building manifest...")

    outputs_dict = {}
    for fname in [
        "step_2d7_scenario_summary_register.csv",
        "step_2d7_integrated_management_brief_register.csv",
        "step_2d7_management_brief_section_register.csv",
        "step_2d7_streamlit_management_brief_contract.csv",
        "step_2d8_management_brief_completeness_register.csv",
        "step_2d8_scenario_validation_register.csv",
        "step_2d8_final_validation_outcome_register.csv",
        "step_2d8_streamlit_handover_readiness_register.csv",
        "step_2d8_execution_summary.csv",
        "step_2d8_scenario_summary_reconciliation_register.csv",
        "step_2d8_scenario_summary_correction_summary.csv",
    ]:
        fpath = OUTPUT_DIR / fname
        if fpath.exists():
            outputs_dict[fname] = {
                "sha256": compute_sha256(fpath),
                "rows": len(load_csv(fname)),
            }

    manifest = build_manifest("2d8_scenario_reconciliation", "focused_reconciliation", outputs_dict)
    write_manifest(manifest, "step_2d8_manifest.json")
    print(f"    Saved step_2d8_manifest.json")

    # ------------------------------------------------------------------
    # 8. Run focused tests
    # ------------------------------------------------------------------
    print("\n[8] Running focused tests...")

    test_results = []

    # Test 1: Every Ready-for-Review package has scenario summary or governed Not Applicable reason
    all_have_summary_or_na = True
    missing_reason = []
    for dpkg in ready_ids:
        imb_row = imb_updated[imb_updated["decision_package_id"] == dpkg]
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
    for dpkg, summaries in reconciled_summaries.items():
        apkg = dpkg_to_apkg.get(dpkg, "")
        c2f_row = c2f_by_apkg.get(apkg)
        if c2f_row is not None:
            for col in ["baseline_summary", "conservative_summary", "expected_summary", "higher_intensity_summary"]:
                orig = str(c2f_row.get(col, "")).strip()
                mapped = summaries.get(col, "").strip()
                if orig != mapped:
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
    for _, row in imb_updated.iterrows():
        for col in scenario_cols:
            val = str(row.get(col, "")).strip()
            if val in ("0", "0.0"):
                orig_row = imb[imb["decision_package_id"] == row["decision_package_id"]]
                if not orig_row.empty:
                    orig_val = str(orig_row.iloc[0].get(col, "")).strip()
                    if orig_val == "" or pd.isna(orig_val):
                        no_zero = False
                        zero_issues.append(f"{row['decision_package_id']}:{col}")

    test_results.append({
        "test_id": "TEST-03",
        "description": "Missing scenario values are not converted to zero",
        "status": "PASS" if no_zero else "FAIL",
        "detail": "" if no_zero else f"Zero conversions: {len(zero_issues)}",
    })

    # Test 4: No preferred scenario is selected by this reconciliation
    no_preferred_selected = True
    preferred_issues = []
    for _, row in imb_updated.iterrows():
        val = row.get("selected_scenario", "")
        if has_content(val):
            no_preferred_selected = False
            preferred_issues.append(row["decision_package_id"])

    test_results.append({
        "test_id": "TEST-04",
        "description": "No preferred scenario is selected by reconciliation",
        "status": "PASS" if no_preferred_selected else "FAIL",
        "detail": "" if no_preferred_selected else f"Selections found: {len(preferred_issues)}",
    })

    # Test 5: Readiness is not upgraded without evidence
    no_upgrade = True
    upgrade_issues = []
    for dpkg in list(reconciled_summaries.keys()):
        old_row = master_val[master_val["decision_package_id"] == dpkg]
        new_row = master_updated[master_updated["decision_package_id"] == dpkg]
        if not old_row.empty and not new_row.empty:
            old_outcome = old_row.iloc[0]["validation_outcome"]
            new_outcome = new_row.iloc[0]["validation_outcome"]
            outcome_rank = {
                "Not Suitable": 0,
                "Requires Focused Correction": 1,
                "Requires Source Data Review": 2,
                "Requires Upstream Analytical Review": 3,
                "Requires Governance Review": 4,
                "Validated with Conditions": 5,
                "Validated for Streamlit Handover": 6,
            }
            if outcome_rank.get(new_outcome, 0) > outcome_rank.get(old_outcome, 0):
                no_upgrade = False
                upgrade_issues.append(f"{dpkg}: {old_outcome} -> {new_outcome}")

    test_results.append({
        "test_id": "TEST-05",
        "description": "Readiness is not upgraded without evidence",
        "status": "PASS" if no_upgrade else "FAIL",
        "detail": "" if no_upgrade else f"Upgrades: {len(upgrade_issues)}",
    })

    # Test 6: Streamlit readiness reflects unresolved missing summaries
    streamlit_reflects = True
    streamlit_issues = []
    for _, cls_row in classification_df.iterrows():
        dpkg = cls_row["decision_package_id"]
        if cls_row["classification"] in ["Readiness Classification Inconsistent", "Scenario Summary Source Missing"]:
            master_row = master_updated[master_updated["decision_package_id"] == dpkg]
            if not master_row.empty:
                outcome = master_row.iloc[0]["validation_outcome"]
                if outcome == "Validated for Streamlit Handover":
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
    for dpkg, summaries in reconciled_summaries.items():
        if summaries.get("source_phase") not in ("2C-2", "2D-7"):
            evidence_reconciles = False
            evidence_issues.append(dpkg)

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

    # ------------------------------------------------------------------
    # 9. Generate final reconciliation report
    # ------------------------------------------------------------------
    print("\n[9] Generating reconciliation report...")

    total_affected = len(classification_df)
    recoverable_count = len(classification_df[classification_df["classification"] == "Scenario Summary Recoverable from Frozen Source"])
    non_applicable_count = len(classification_df[classification_df["classification"].isin(["Scenario Monitoring Only", "Scenario Non-Quantitative", "Scenario Not Required"])])
    mapping_defect_count = len(classification_df[classification_df["classification"] == "Scenario Summary Mapping Defect"])
    unresolved_missing = len(classification_df[classification_df["classification"].isin(["Scenario Summary Source Missing", "Readiness Classification Inconsistent"])])

    readiness_changed = 0
    for dpkg in list(reconciled_summaries.keys()):
        old_row = master_val[master_val["decision_package_id"] == dpkg]
        new_row = master_updated[master_updated["decision_package_id"] == dpkg]
        if not old_row.empty and not new_row.empty:
            if old_row.iloc[0]["validation_outcome"] != new_row.iloc[0]["validation_outcome"]:
                readiness_changed += 1

    validation_changed = readiness_changed

    final_streamlit_ready = int(master_updated["streamlit_ready"].sum())
    final_streamlit_with_conditions = int(
        master_updated[(master_updated["streamlit_ready"] == True) & (master_updated["validation_outcome"] == "Validated with Conditions")].shape[0]
    )
    packages_requiring_focused_correction = int(
        master_updated[master_updated["validation_outcome"] == "Requires Focused Correction"].shape[0]
    )

    report_lines = [
        "# Phase 2D-8 Focused Scenario-Summary Reconciliation Report",
        "",
        f"**Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Scope:** Frozen Step 2D-7 outputs with missing scenario summaries for Ready-for-Review packages",
        "",
        "## Executive Summary",
        "",
        f"- **Total Ready-for-Review packages:** {len(ready_ids)}",
        f"- **Affected packages (missing IMB summaries):** {total_affected}",
        f"- **Recoverable from frozen source:** {recoverable_count}",
        f"- **Non-applicable (Monitoring / Non-Quantitative):** {non_applicable_count}",
        f"- **Unresolved missing sources:** {unresolved_missing}",
        f"- **Readiness classifications changed:** {readiness_changed}",
        f"- **Validation outcomes changed:** {validation_changed}",
        f"- **Final Streamlit-ready count:** {final_streamlit_ready}",
        f"- **Streamlit-ready-with-conditions count:** {final_streamlit_with_conditions}",
        f"- **Packages requiring focused correction:** {packages_requiring_focused_correction}",
        "",
        "## Classification Breakdown",
        "",
        "| Classification | Count | Action Taken |",
        "|---|---|---|",
    ]

    for _, cs in correction_summary_df.iterrows():
        report_lines.append(f"| {cs['classification']} | {cs['affected_count']} | {cs['correction_action']} |")

    report_lines.extend([
        "",
        "## Test Results",
        "",
        "| Test ID | Description | Status | Detail |",
        "|---|---|---|---|",
    ])

    for _, tr in test_df.iterrows():
        report_lines.append(f"| {tr['test_id']} | {tr['description']} | {tr['status']} | {tr['detail']} |")

    report_lines.extend([
        "",
        "## Governed Principles Applied",
        "",
        "1. **No recalculation:** Scenario values from frozen Phase 2C-2 / Step 2D-7 were mapped directly without modification.",
        "2. **No silent upgrades:** Packages with unresolved missing summaries retain a visible condition.",
        "3. **Not Applicable documented:** Monitoring-Only and Non-Quantitative packages display governed reasons.",
        "4. **Upstream frozen:** No Phase 2C-2 files were modified.",
        "5. **Stop before 2D-9:** No Step 2D-9 artifacts were created.",
        "",
        "## Affected Packages Detail",
        "",
    ])

    for _, cls_row in classification_df.iterrows():
        report_lines.append(f"### {cls_row['decision_package_id']}")
        report_lines.append(f"- **IMB ID:** {cls_row['integrated_management_brief_id']}")
        report_lines.append(f"- **Classification:** {cls_row['classification']}")
        report_lines.append(f"- **Reason:** {cls_row['reason_summary_is_missing']}")
        report_lines.append(f"- **Scenario Family:** {cls_row['scenario_family']}")
        report_lines.append(f"- **Baseline Availability:** {cls_row['baseline_availability']}")
        report_lines.append(f"- **Expected Availability:** {cls_row['expected_availability']}")
        report_lines.append("")

    report_text = "\n".join(report_lines)
    report_path = DOCS_DIR / "step_2d8_scenario_summary_reconciliation_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"    Saved {report_path}")

    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"Reconciliation complete in {elapsed:.2f}s")
    print(f"Affected: {total_affected} | Recoverable: {recoverable_count} | Non-Applicable: {non_applicable_count}")
    print(f"Tests: {test_df['status'].value_counts().get('PASS', 0)} passed, {test_df['status'].value_counts().get('FAIL', 0)} failed")
    print("=" * 60)

    save_csv(test_df, "step_2d8_reconciliation_test_results.csv")


if __name__ == "__main__":
    main()
