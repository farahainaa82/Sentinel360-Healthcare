"""
Safe runner for Step 2A-5 Six-KPI Integration and Status Layer.

Executes the integration engine without recalculating KPIs.
Verifies immutability of all prior accepted outputs.
"""

import argparse
import hashlib
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

# Ensure project root on path
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.six_kpi_integration_engine import SixKPIIntegrationEngine, GOVERNED_KPI_IDS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_immutability(project_root: Path) -> Dict[str, Any]:
    """Verify all accepted prior outputs remain unchanged."""
    # We record current checksums and return them; the caller decides pass/fail.
    checks = {}
    phases = {
        "phase1": [
            "data/processed/processed_staff_roster.csv",
            "data/processed/processed_staff_attendance.csv",
            "data/processed/processed_staffing_requirement.csv",
            "data/processed/processed_workforce_daily.csv",
            "data/processed/processed_patient_encounters.csv",
            "data/processed/processed_patient_queue.csv",
            "data/processed/processed_bed_capacity.csv",
            "data/processed/processed_service_schedule.csv",
            "data/processed/processed_patient_flow_daily.csv",
            "data/processed/processed_hospital_master.csv",
            "data/processed/processed_department_master.csv",
            "data/processed/processed_operational_daily.csv",
        ],
        "step_2a1": [
            "outputs/analytical_governance/kpi_governance_registry.csv",
            "outputs/analytical_governance/kpi_readiness_summary.csv",
            "outputs/analytical_governance/kpi_source_field_mapping.csv",
            "outputs/analytical_governance/kpi_configuration_validation.csv",
            "outputs/analytical_governance/kpi_threshold_validation.csv",
        ],
        "step_2a2": [
            "data/analytical/analytical_workforce_kpi_daily.csv",
            "data/analytical/analytical_workforce_kpi_evidence.csv",
            "data/analytical/analytical_workforce_kpi_exclusions.csv",
            "data/analytical/analytical_workforce_kpi_lineage.csv",
            "data/analytical/analytical_workforce_kpi_issues.csv",
            "data/analytical/analytical_workforce_kpi_audit.csv",
        ],
        "step_2a3": [
            "data/analytical/analytical_patient_flow_kpi_daily.csv",
            "data/analytical/analytical_patient_flow_kpi_evidence.csv",
            "data/analytical/analytical_patient_flow_kpi_exclusions.csv",
            "data/analytical/analytical_patient_flow_kpi_lineage.csv",
            "data/analytical/analytical_patient_flow_kpi_issues.csv",
            "data/analytical/analytical_patient_flow_kpi_audit.csv",
        ],
        "step_2a4": [
            "data/analytical/analytical_patient_experience_kpi_daily.csv",
            "data/analytical/analytical_patient_experience_kpi_evidence.csv",
            "data/analytical/analytical_patient_experience_kpi_exclusions.csv",
            "data/analytical/analytical_patient_experience_kpi_lineage.csv",
            "data/analytical/analytical_patient_experience_kpi_issues.csv",
            "data/analytical/analytical_patient_experience_kpi_audit.csv",
        ],
    }
    for phase, files in phases.items():
        checks[phase] = {}
        for f in files:
            p = project_root / f
            if p.exists():
                checks[phase][f] = _sha256_file(p)
            else:
                checks[phase][f] = "MISSING"
    return checks


def export_outputs(result, project_root: Path, output_dir: Path) -> Dict[str, str]:
    """Export integrated analytical datasets and control outputs."""
    # Analytical outputs
    analytical_dir = project_root / "data" / "analytical"
    analytical_dir.mkdir(parents=True, exist_ok=True)

    paths = {}
    daily_path = analytical_dir / "analytical_six_kpi_daily.csv"
    result.integrated_daily_df.to_csv(daily_path, index=False)
    paths["analytical_six_kpi_daily"] = str(daily_path)

    if not result.integrated_evidence_df.empty:
        ev_path = analytical_dir / "analytical_six_kpi_evidence.csv"
        result.integrated_evidence_df.to_csv(ev_path, index=False)
        paths["analytical_six_kpi_evidence"] = str(ev_path)

    if not result.integrated_exclusions_df.empty:
        ex_path = analytical_dir / "analytical_six_kpi_exclusions.csv"
        result.integrated_exclusions_df.to_csv(ex_path, index=False)
        paths["analytical_six_kpi_exclusions"] = str(ex_path)

    if not result.integrated_lineage_df.empty:
        lin_path = analytical_dir / "analytical_six_kpi_lineage.csv"
        result.integrated_lineage_df.to_csv(lin_path, index=False)
        paths["analytical_six_kpi_lineage"] = str(lin_path)

    if not result.integrated_issues_df.empty:
        iss_path = analytical_dir / "analytical_six_kpi_issues.csv"
        result.integrated_issues_df.to_csv(iss_path, index=False)
        paths["analytical_six_kpi_issues"] = str(iss_path)

    if not result.integrated_audit_df.empty:
        aud_path = analytical_dir / "analytical_six_kpi_audit.csv"
        result.integrated_audit_df.to_csv(aud_path, index=False)
        paths["analytical_six_kpi_audit"] = str(aud_path)

    coverage_path = analytical_dir / "analytical_six_kpi_coverage_daily.csv"
    result.coverage_df.to_csv(coverage_path, index=False)
    paths["analytical_six_kpi_coverage_daily"] = str(coverage_path)

    # Control outputs
    control_dir = output_dir
    control_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = control_dir / "six_kpi_integration_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(result.integration_manifest, f, indent=2, default=str)
    paths["six_kpi_integration_manifest"] = str(manifest_path)

    result.reconciliation_df.to_csv(control_dir / "six_kpi_kpi_count_reconciliation.csv", index=False)
    paths["six_kpi_kpi_count_reconciliation"] = str(control_dir / "six_kpi_kpi_count_reconciliation.csv")

    result.status_summary_df.to_csv(control_dir / "six_kpi_status_distribution.csv", index=False)
    paths["six_kpi_status_distribution"] = str(control_dir / "six_kpi_status_distribution.csv")

    # Additional control summaries
    calc_summary = result.integrated_daily_df.groupby(["kpi_id", "calculation_status"]).size().reset_index(name="count")
    calc_summary.to_csv(control_dir / "six_kpi_calculation_status_summary.csv", index=False)
    paths["six_kpi_calculation_status_summary"] = str(control_dir / "six_kpi_calculation_status_summary.csv")

    thresh_summary = result.integrated_daily_df.groupby(["kpi_id", "threshold_status"]).size().reset_index(name="count")
    thresh_summary.to_csv(control_dir / "six_kpi_threshold_status_summary.csv", index=False)
    paths["six_kpi_threshold_status_summary"] = str(control_dir / "six_kpi_threshold_status_summary.csv")

    conf_summary = result.integrated_daily_df.groupby(["kpi_id", "data_confidence_level"]).size().reset_index(name="count")
    conf_summary.to_csv(control_dir / "six_kpi_confidence_summary.csv", index=False)
    paths["six_kpi_confidence_summary"] = str(control_dir / "six_kpi_confidence_summary.csv")

    int_summary = result.integrated_daily_df.groupby(["kpi_id", "integration_status"]).size().reset_index(name="count")
    int_summary.to_csv(control_dir / "six_kpi_integration_status_summary.csv", index=False)
    paths["six_kpi_integration_status_summary"] = str(control_dir / "six_kpi_integration_status_summary.csv")

    ev_summary = result.integrated_daily_df.groupby(["kpi_id", "evidence_status"]).size().reset_index(name="count")
    ev_summary.to_csv(control_dir / "six_kpi_evidence_status_summary.csv", index=False)
    paths["six_kpi_evidence_status_summary"] = str(control_dir / "six_kpi_evidence_status_summary.csv")

    lin_summary = result.integrated_daily_df.groupby(["kpi_id", "lineage_status"]).size().reset_index(name="count")
    lin_summary.to_csv(control_dir / "six_kpi_lineage_status_summary.csv", index=False)
    paths["six_kpi_lineage_status_summary"] = str(control_dir / "six_kpi_lineage_status_summary.csv")

    result.coverage_df.groupby("coverage_status").size().reset_index(name="count").to_csv(
        control_dir / "six_kpi_coverage_summary.csv", index=False
    )
    paths["six_kpi_coverage_summary"] = str(control_dir / "six_kpi_coverage_summary.csv")

    dup_check = result.integrated_daily_df.groupby("integration_record_id").size().reset_index(name="count")
    dup_check[dup_check["count"] > 1].to_csv(control_dir / "six_kpi_duplicate_check.csv", index=False)
    paths["six_kpi_duplicate_check"] = str(control_dir / "six_kpi_duplicate_check.csv")

    # Value-status consistency
    consistency = []
    for _, row in result.integrated_daily_df.iterrows():
        issues = []
        if row["calculation_status"] == "Calculated" and pd.isna(row["kpi_value"]):
            issues.append("calculated_null")
        if row["threshold_status"] in ("Green", "Amber", "Red") and pd.isna(row["kpi_value"]):
            issues.append("threshold_color_null")
        if row["threshold_status"] in ("Green", "Amber", "Red") and row["calculation_status"] != "Calculated":
            issues.append("threshold_color_non_calculated")
        if row["data_confidence_level"] == "High" and pd.isna(row["kpi_value"]):
            issues.append("high_confidence_unavailable")
        consistency.append({
            "integration_record_id": row["integration_record_id"],
            "kpi_id": row["kpi_id"],
            "kpi_value": row["kpi_value"],
            "calculation_status": row["calculation_status"],
            "threshold_status": row["threshold_status"],
            "data_confidence_level": row["data_confidence_level"],
            "inconsistencies": ";".join(issues) if issues else "none",
        })
    pd.DataFrame(consistency).to_csv(control_dir / "six_kpi_value_status_consistency.csv", index=False)
    paths["six_kpi_value_status_consistency"] = str(control_dir / "six_kpi_value_status_consistency.csv")

    # Governance consistency
    gov = []
    for _, row in result.integrated_daily_df.iterrows():
        issues = []
        if row["threshold_is_provisional"] and row["threshold_approval_status"].lower() not in ("draft", "pending"):
            issues.append("provisional_without_draft_status")
        gov.append({
            "integration_record_id": row["integration_record_id"],
            "kpi_id": row["kpi_id"],
            "threshold_is_provisional": row["threshold_is_provisional"],
            "threshold_approval_status": row["threshold_approval_status"],
            "configuration_version": row.get("configuration_version", ""),
            "issues": ";".join(issues) if issues else "none",
        })
    pd.DataFrame(gov).to_csv(control_dir / "six_kpi_governance_consistency.csv", index=False)
    paths["six_kpi_governance_consistency"] = str(control_dir / "six_kpi_governance_consistency.csv")

    # Schema validation
    schema_results = []
    required_daily = [
        "integration_record_id", "analytical_record_id", "hospital_id", "department_id",
        "reporting_date", "kpi_id", "kpi_name", "domain", "kpi_value",
        "calculation_status", "threshold_status", "data_confidence_level",
        "integration_status", "evidence_status", "lineage_status",
    ]
    for col in required_daily:
        schema_results.append({
            "dataset": "analytical_six_kpi_daily",
            "field": col,
            "present": col in result.integrated_daily_df.columns,
        })
    pd.DataFrame(schema_results).to_csv(control_dir / "six_kpi_schema_validation.csv", index=False)
    paths["six_kpi_schema_validation"] = str(control_dir / "six_kpi_schema_validation.csv")

    # Issue log
    if result.issue_records:
        issue_df = pd.DataFrame([
            {
                "integration_issue_id": i.integration_issue_id,
                "severity": i.severity,
                "issue_type": i.issue_type,
                "kpi_id": i.kpi_id,
                "message": i.message,
                "integration_record_id": i.integration_record_id,
            }
            for i in result.issue_records
        ])
    else:
        issue_df = pd.DataFrame(columns=["integration_issue_id", "severity", "issue_type", "kpi_id", "message", "integration_record_id"])
    issue_df.to_csv(control_dir / "six_kpi_issue_log.csv", index=False)
    paths["six_kpi_issue_log"] = str(control_dir / "six_kpi_issue_log.csv")

    # Exclusion summary
    if not result.integrated_exclusions_df.empty:
        ex_sum = result.integrated_exclusions_df.groupby(["kpi_id", "reason_code"]).size().reset_index(name="count")
    else:
        ex_sum = pd.DataFrame(columns=["kpi_id", "reason_code", "count"])
    ex_sum.to_csv(control_dir / "six_kpi_exclusion_summary.csv", index=False)
    paths["six_kpi_exclusion_summary"] = str(control_dir / "six_kpi_exclusion_summary.csv")

    # Lineage summary
    if not result.integrated_lineage_df.empty:
        lin_sum = result.integrated_lineage_df.groupby(["kpi_id", "transformation_name"]).size().reset_index(name="count")
    else:
        lin_sum = pd.DataFrame(columns=["kpi_id", "transformation_name", "count"])
    lin_sum.to_csv(control_dir / "six_kpi_lineage_summary.csv", index=False)
    paths["six_kpi_lineage_summary"] = str(control_dir / "six_kpi_lineage_summary.csv")

    # Dataset summary
    ds_summary = pd.DataFrame([
        {"dataset": k, "record_count": len(result.integrated_daily_df) if "daily" in k else (len(getattr(result, f"integrated_{k.split('_')[-1]}_df")) if hasattr(result, f"integrated_{k.split('_')[-1]}_df") else 0), "exported": True}
        for k in paths.keys()
    ])
    ds_summary.to_csv(control_dir / "six_kpi_dataset_summary.csv", index=False)
    paths["six_kpi_dataset_summary"] = str(control_dir / "six_kpi_dataset_summary.csv")

    # Audit log
    if not result.integrated_audit_df.empty:
        result.integrated_audit_df.to_csv(control_dir / "six_kpi_audit_log.csv", index=False)
    else:
        pd.DataFrame(columns=["audit_id", "event_type", "event_status", "integration_run_id"]).to_csv(control_dir / "six_kpi_audit_log.csv", index=False)
    paths["six_kpi_audit_log"] = str(control_dir / "six_kpi_audit_log.csv")

    return paths


def main():
    parser = argparse.ArgumentParser(description="Step 2A-5 Six-KPI Integration Runner")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute-export", action="store_true")
    parser.add_argument("--output-dir", default=str(PROJECT_ROOT / "outputs" / "analytical_six_kpi"))
    parser.add_argument("--kpi-id", default=None)
    parser.add_argument("--hospital-id", default=None)
    parser.add_argument("--department-id", default=None)
    parser.add_argument("--reporting-date", default=None)
    parser.add_argument("--skip-evidence-validation", action="store_true")
    parser.add_argument("--skip-lineage-validation", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root)
    output_dir = Path(args.output_dir)

    logger.info("Step 2A-5 Six-KPI Integration starting")
    logger.info("Project root: %s", project_root)

    # Immutability check before
    logger.info("Recording pre-run checksums...")
    pre_checksums = verify_immutability(project_root)

    engine = SixKPIIntegrationEngine(
        project_root=str(project_root),
        skip_evidence_validation=args.skip_evidence_validation,
        skip_lineage_validation=args.skip_lineage_validation,
    )

    result = engine.run()

    logger.info("Integration run %s complete. Integrated %d records.", engine.integration_run_id, len(result.integrated_daily_df))
    logger.info("Issues: %d, Audit events: %d", len(result.issue_records), len(result.audit_records))

    # Reconciliation
    logger.info("Reconciliation:\n%s", result.reconciliation_df.to_string(index=False))

    # Coverage
    logger.info("Coverage: %s", result.coverage_df["coverage_status"].value_counts().to_dict())

    # Duplicate check
    dup_count = result.integrated_daily_df["integration_record_id"].duplicated().sum()
    logger.info("Duplicate integration_record_id: %d", dup_count)

    # Value-status consistency
    inconsistency_count = result.integrated_daily_df.apply(lambda r: (
        (r["calculation_status"] == "Calculated" and pd.isna(r["kpi_value"])) or
        (r["threshold_status"] in ("Green", "Amber", "Red") and pd.isna(r["kpi_value"])) or
        (r["threshold_status"] in ("Green", "Amber", "Red") and r["calculation_status"] != "Calculated") or
        (r["data_confidence_level"] == "High" and pd.isna(r["kpi_value"]))
    ), axis=1).sum()
    logger.info("Value-status inconsistencies: %d", inconsistency_count)

    # Filter if requested
    df = result.integrated_daily_df
    if args.kpi_id:
        df = df[df["kpi_id"] == args.kpi_id]
    if args.hospital_id:
        df = df[df["hospital_id"] == args.hospital_id]
    if args.department_id:
        df = df[df["department_id"] == args.department_id]
    if args.reporting_date:
        df = df[df["reporting_date"] == args.reporting_date]

    if args.dry_run:
        logger.info("Dry run complete. No files exported.")
        print(json.dumps({
            "integration_run_id": engine.integration_run_id,
            "integrated_records": len(df),
            "issues": len(result.issue_records),
            "duplicates": int(dup_count),
            "inconsistencies": int(inconsistency_count),
        }, indent=2))
        return

    if not args.execute_export:
        logger.info("Pass --execute-export to write outputs.")
        return

    # Export
    paths = export_outputs(result, project_root, output_dir)
    logger.info("Exported %d files.", len(paths))

    # Post-run immutability
    logger.info("Verifying post-run immutability...")
    post_checksums = verify_immutability(project_root)
    immutability_result = {}
    for phase in pre_checksums:
        changed = []
        for f, pre in pre_checksums[phase].items():
            post = post_checksums[phase].get(f, "MISSING")
            if pre != post:
                changed.append(f)
        immutability_result[phase] = {
            "changed_files": changed,
            "status": "Passed" if not changed else "Failed",
        }

    # Write immutability verification
    imm_path = output_dir / "six_kpi_immutability_verification.json"
    with open(imm_path, "w") as f:
        json.dump(immutability_result, f, indent=2)
    logger.info("Immutability: %s", {k: v["status"] for k, v in immutability_result.items()})

    # Write end-to-end test results
    test_results = {
        "integration_run_id": engine.integration_run_id,
        "timestamp": datetime.now().isoformat(),
        "total_integrated": len(result.integrated_daily_df),
        "duplicate_count": int(dup_count),
        "inconsistency_count": int(inconsistency_count),
        "issue_count": len(result.issue_records),
        "coverage_complete": int(result.coverage_df["coverage_status"].eq("Complete").sum()),
        "coverage_partial": int(result.coverage_df["coverage_status"].eq("Partial").sum()),
        "immutability": immutability_result,
    }
    with open(output_dir / "six_kpi_end_to_end_test_results.json", "w") as f:
        json.dump(test_results, f, indent=2, default=str)

    # Acceptance evidence
    acceptance = {
        "step": "2A-5",
        "status": "Completed",
        "integration_run_id": engine.integration_run_id,
        "kpi_ids": sorted(GOVERNED_KPI_IDS),
        "record_count": len(result.integrated_daily_df),
        "issue_count": len(result.issue_records),
        "duplicate_count": int(dup_count),
        "inconsistency_count": int(inconsistency_count),
        "immutability_status": "Passed" if all(v["status"] == "Passed" for v in immutability_result.values()) else "Failed",
        "timestamp": datetime.now().isoformat(),
    }
    with open(output_dir / "six_kpi_acceptance_evidence.json", "w") as f:
        json.dump(acceptance, f, indent=2, default=str)

    logger.info("Step 2A-5 complete.")


if __name__ == "__main__":
    main()
