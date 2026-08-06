"""Main runner for Phase 2D-8 — Decision Intelligence Validation.

Validates 646 integrated management briefs end-to-end using frozen 2D-7 outputs.
No upstream values are recalculated, modified, or approved.
"""

import json
import sys
import time
from pathlib import Path

import pandas as pd

from decision_intelligence_validation_utils import (
    BASE_DIR,
    OUTPUT_DIR,
    atomic_write_csv,
    build_manifest,
    compute_sha256,
    correction_class,
    load_register,
    validation_outcome,
    write_manifest,
)

# Import all 26 validation engines
from decision_intelligence_validation_authority_engine import build_register as build_authority
from decision_intelligence_validation_population_engine import build_register as build_population
from decision_intelligence_validation_identity_engine import build_register as build_identity
from decision_intelligence_validation_kpi_risk_engine import build_register as build_kpi_risk
from decision_intelligence_validation_scenario_engine import build_register as build_scenario
from decision_intelligence_validation_financial_engine import build_register as build_financial
from decision_intelligence_validation_readiness_engine import build_register as build_readiness
from decision_intelligence_validation_action_routing_engine import build_register as build_action_routing
from decision_intelligence_validation_evidence_engine import build_register as build_evidence
from decision_intelligence_validation_lineage_engine import build_register as build_lineage
from decision_intelligence_validation_audit_engine import build_register as build_audit
from decision_intelligence_validation_narrative_engine import build_register as build_narrative
from decision_intelligence_validation_wording_engine import build_register as build_wording
from decision_intelligence_validation_contradiction_engine import build_register as build_contradiction
from decision_intelligence_validation_cross_layer_engine import build_register as build_cross_layer
from decision_intelligence_validation_streamlit_engine import build_register as build_streamlit
from decision_intelligence_validation_question_engine import build_register as build_question
from decision_intelligence_validation_confirmation_engine import build_register as build_confirmation
from decision_intelligence_validation_monitoring_engine import build_register as build_monitoring
from decision_intelligence_validation_governance_engine import build_register as build_governance
from decision_intelligence_validation_recommendation_engine import build_register as build_recommendation
from decision_intelligence_validation_tradeoff_engine import build_register as build_tradeoff
from decision_intelligence_validation_export_contract_engine import build_register as build_export_contract
from decision_intelligence_validation_priority_queue_engine import build_register as build_priority_queue
from decision_intelligence_validation_section_engine import build_register as build_section
from decision_intelligence_validation_type_engine import build_register as build_type

EXPECTED_PACKAGES = 646


def run_validation(mode="full_run", sample_packages=None):
    """Execute the full 2D-8 validation pipeline.

    Args:
        mode: 'full_run' or 'smoke_test'
        sample_packages: list of decision_package_ids for smoke test, or None for full run
    """
    print(f"=== Phase 2D-8 Decision Intelligence Validation ===")
    print(f"Mode: {mode}")
    print(f"Timestamp: {pd.Timestamp.now()}")
    print()

    # Step 0: Load brief register (frozen upstream)
    briefs = load_register("step_2d7_integrated_management_brief_register.csv")
    if briefs.empty:
        print("FATAL: 2D-7 brief register not found or empty.")
        sys.exit(1)

    if sample_packages:
        briefs = briefs[briefs["decision_package_id"].isin(sample_packages)]
        print(f"Smoke test mode: {len(briefs)} packages selected.")
    else:
        if len(briefs) != EXPECTED_PACKAGES:
            print(f"WARNING: Expected {EXPECTED_PACKAGES} packages, found {len(briefs)}")

    # ------------------------------------------------------------------
    # Execute all 26 validation engines
    # ------------------------------------------------------------------
    engines = [
        ("authority", build_authority),
        ("population", build_population),
        ("identity", build_identity),
        ("kpi_risk", build_kpi_risk),
        ("scenario", build_scenario),
        ("financial", build_financial),
        ("readiness", build_readiness),
        ("action_routing", build_action_routing),
        ("evidence", build_evidence),
        ("lineage", build_lineage),
        ("audit", build_audit),
        ("narrative", build_narrative),
        ("wording", build_wording),
        ("contradiction", build_contradiction),
        ("cross_layer", build_cross_layer),
        ("streamlit", build_streamlit),
        ("question", build_question),
        ("confirmation", build_confirmation),
        ("monitoring", build_monitoring),
        ("governance", build_governance),
        ("recommendation", build_recommendation),
        ("tradeoff", build_tradeoff),
        ("export_contract", build_export_contract),
        ("priority_queue", build_priority_queue),
        ("section", build_section),
        ("type", build_type),
    ]

    all_registers = {}
    execution_summary = []

    for name, engine_fn in engines:
        start = time.time()
        try:
            df = engine_fn()
            elapsed = time.time() - start
            all_registers[name] = df
            pass_count = (df["status"] == "PASS").sum() if "status" in df.columns else 0
            fail_count = (df["status"] == "FAIL").sum() if "status" in df.columns else 0
            execution_summary.append({
                "engine": name,
                "status": "COMPLETE",
                "rows": len(df),
                "pass_count": pass_count,
                "fail_count": fail_count,
                "elapsed_seconds": round(elapsed, 3),
                "error": "",
            })
            print(f"  [{name:20s}] {len(df):4d} rows | PASS {pass_count:3d} | FAIL {fail_count:3d} | {elapsed:.3f}s")
        except Exception as e:
            elapsed = time.time() - start
            execution_summary.append({
                "engine": name,
                "status": "ERROR",
                "rows": 0,
                "pass_count": 0,
                "fail_count": 0,
                "elapsed_seconds": round(elapsed, 3),
                "error": str(e),
            })
            print(f"  [{name:20s}] ERROR: {e}")

    # ------------------------------------------------------------------
    # Build per-package validation summary (master register)
    # ------------------------------------------------------------------
    print("\nBuilding per-package validation summary...")
    pkg_summary = []
    for _, row in briefs.iterrows():
        pkg_id = row["decision_package_id"]
        brief_id = row["integrated_management_brief_id"]

        severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        failed_checks = []

        for name, df in all_registers.items():
            if "status" not in df.columns:
                continue
            fails = df[df["status"] == "FAIL"]
            for _, f in fails.iterrows():
                # Map check severity based on engine and config
                sev = _infer_severity(name, f.get("check", ""))
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
                failed_checks.append(f"{name}:{f.get('check','')}")

        outcome = validation_outcome(severity_counts)
        correction = correction_class(outcome)

        pkg_summary.append({
            "decision_package_id": pkg_id,
            "integrated_management_brief_id": brief_id,
            "validation_engine_count": len(engines),
            "checks_executed": sum(len(df) for df in all_registers.values()),
            "checks_passed": sum((df["status"] == "PASS").sum() for df in all_registers.values() if "status" in df.columns),
            "checks_failed": sum((df["status"] == "FAIL").sum() for df in all_registers.values() if "status" in df.columns),
            "critical_failures": severity_counts["Critical"],
            "high_failures": severity_counts["High"],
            "medium_failures": severity_counts["Medium"],
            "low_failures": severity_counts["Low"],
            "validation_outcome": outcome,
            "correction_classification": correction,
            "failed_check_list": "; ".join(failed_checks[:10]),
            "streamlit_ready": outcome in ["Validated for Streamlit Handover", "Validated with Conditions"],
        })

    pkg_summary_df = pd.DataFrame(pkg_summary)

    # ------------------------------------------------------------------
    # Write all outputs
    # ------------------------------------------------------------------
    print("\nWriting outputs...")
    outputs = {}

    # A. Master validation register
    fname = "step_2d8_master_validation_register.csv"
    path = atomic_write_csv(pkg_summary_df, fname)
    outputs[fname] = {
        "path": str(path),
        "checksum": compute_sha256(path),
        "rows": len(pkg_summary_df),
        "columns": len(pkg_summary_df.columns),
    }

    # B-AD. Individual engine registers
    register_map = {
        "step_2d8_authority_validation_register.csv": all_registers["authority"],
        "step_2d8_population_validation_register.csv": all_registers["population"],
        "step_2d8_identity_validation_register.csv": all_registers["identity"],
        "step_2d8_kpi_risk_validation_register.csv": all_registers["kpi_risk"],
        "step_2d8_scenario_validation_register.csv": all_registers["scenario"],
        "step_2d8_financial_validation_register.csv": all_registers["financial"],
        "step_2d8_readiness_validation_register.csv": all_registers["readiness"],
        "step_2d8_action_routing_validation_register.csv": all_registers["action_routing"],
        "step_2d8_evidence_validation_register.csv": all_registers["evidence"],
        "step_2d8_lineage_validation_register.csv": all_registers["lineage"],
        "step_2d8_audit_validation_register.csv": all_registers["audit"],
        "step_2d8_narrative_validation_register.csv": all_registers["narrative"],
        "step_2d8_wording_validation_register.csv": all_registers["wording"],
        "step_2d8_contradiction_validation_register.csv": all_registers["contradiction"],
        "step_2d8_cross_layer_validation_register.csv": all_registers["cross_layer"],
        "step_2d8_streamlit_validation_register.csv": all_registers["streamlit"],
        "step_2d8_question_validation_register.csv": all_registers["question"],
        "step_2d8_confirmation_validation_register.csv": all_registers["confirmation"],
        "step_2d8_monitoring_validation_register.csv": all_registers["monitoring"],
        "step_2d8_governance_validation_register.csv": all_registers["governance"],
        "step_2d8_recommendation_validation_register.csv": all_registers["recommendation"],
        "step_2d8_tradeoff_validation_register.csv": all_registers["tradeoff"],
        "step_2d8_export_contract_validation_register.csv": all_registers["export_contract"],
        "step_2d8_priority_queue_validation_register.csv": all_registers["priority_queue"],
        "step_2d8_section_validation_register.csv": all_registers["section"],
        "step_2d8_type_validation_register.csv": all_registers["type"],
    }

    for fname, df in register_map.items():
        path = atomic_write_csv(df, fname)
        outputs[fname] = {
            "path": str(path),
            "checksum": compute_sha256(path),
            "rows": len(df),
            "columns": len(df.columns),
        }

    # AE. Execution summary
    exec_df = pd.DataFrame(execution_summary)
    fname = "step_2d8_execution_summary.csv"
    path = atomic_write_csv(exec_df, fname)
    outputs[fname] = {
        "path": str(path),
        "checksum": compute_sha256(path),
        "rows": len(exec_df),
        "columns": len(exec_df.columns),
    }

    # AF. Outcome distribution
    outcome_dist = pkg_summary_df["validation_outcome"].value_counts().reset_index()
    outcome_dist.columns = ["validation_outcome", "package_count"]
    fname = "step_2d8_outcome_distribution.csv"
    path = atomic_write_csv(outcome_dist, fname)
    outputs[fname] = {
        "path": str(path),
        "checksum": compute_sha256(path),
        "rows": len(outcome_dist),
        "columns": len(outcome_dist.columns),
    }

    # Manifest
    manifest = build_manifest("2D-8", mode, outputs)
    manifest["packages_validated"] = len(briefs)
    manifest["engines_executed"] = len(engines)
    manifest["total_checks"] = sum(len(df) for df in all_registers.values())
    manifest["total_passes"] = sum(
        (df["status"] == "PASS").sum() for df in all_registers.values() if "status" in df.columns
    )
    manifest["total_fails"] = sum(
        (df["status"] == "FAIL").sum() for df in all_registers.values() if "status" in df.columns
    )
    manifest["outcome_distribution"] = pkg_summary_df["validation_outcome"].value_counts().to_dict()
    manifest["streamlit_ready_count"] = int(pkg_summary_df["streamlit_ready"].sum())

    write_manifest(manifest, "step_2d8_manifest.json")
    outputs["step_2d8_manifest.json"] = {"path": str(OUTPUT_DIR / "step_2d8_manifest.json")}

    print(f"\n=== 2D-8 Validation Complete ===")
    print(f"Packages validated: {len(briefs)}")
    print(f"Engines executed: {len(engines)}")
    print(f"Total checks: {manifest['total_checks']}")
    print(f"Total passes: {manifest['total_passes']}")
    print(f"Total fails: {manifest['total_fails']}")
    print(f"Streamlit ready: {manifest['streamlit_ready_count']}")
    print(f"Outcome distribution:")
    for outcome, count in manifest["outcome_distribution"].items():
        print(f"  {outcome}: {count}")
    print(f"\nManifest written to: {OUTPUT_DIR / 'step_2d8_manifest.json'}")

    return manifest


def _infer_severity(engine_name, check_name):
    """Infer severity from engine name and check."""
    critical_engines = ["authority", "identity", "action_routing", "governance"]
    high_engines = ["kpi_risk", "financial", "readiness", "evidence", "lineage", "wording"]
    if engine_name in critical_engines:
        return "Critical"
    if engine_name in high_engines:
        return "High"
    if engine_name in ["scenario", "narrative", "contradiction", "cross_layer", "streamlit"]:
        return "Medium"
    return "Low"


def run_smoke_test():
    """Run smoke test on 5 representative packages."""
    briefs = load_register("step_2d7_integrated_management_brief_register.csv")
    if briefs.empty:
        print("FATAL: Cannot run smoke test — brief register empty.")
        sys.exit(1)

    # Select 5 representative packages covering different readiness statuses
    samples = []
    for status in ["Ready for Integrated Management Review", "Ready with Conditions",
                   "Monitoring Only", "Requires Assumption Validation", "Non-Quantitative"]:
        subset = briefs[briefs["final_readiness_status"] == status]
        if not subset.empty:
            samples.append(subset.iloc[0]["decision_package_id"])
        if len(samples) >= 5:
            break

    if len(samples) < 5:
        # Fill remaining with first rows
        remaining = 5 - len(samples)
        samples.extend(briefs["decision_package_id"].iloc[:remaining].tolist())
        samples = list(dict.fromkeys(samples))[:5]

    print(f"Smoke test sample packages: {samples}")
    return run_validation(mode="smoke_test", sample_packages=samples)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Phase 2D-8 Decision Intelligence Validation")
    parser.add_argument("--smoke", action="store_true", help="Run smoke test on 5 packages")
    parser.add_argument("--full", action="store_true", help="Run full validation on all 646 packages")
    args = parser.parse_args()

    if args.smoke:
        run_smoke_test()
    elif args.full:
        run_validation(mode="full_run")
    else:
        # Default to smoke test first, then prompt for full
        print("No mode specified. Run with --smoke or --full.")
        print("Defaulting to smoke test...")
        run_smoke_test()
