"""
Sentinel360 Healthcare — Patient Flow Integration Validation Runner

Safe runner for Step 2D-3D.
Orchestrates integration checks across all five processed datasets.
"""

import argparse
import hashlib
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import numpy as np

from src.patient_flow_integration_validator import PatientFlowIntegrationValidator, INTEGRATION_VERSION, ENGINE_VERSION, PROCESSED_DATASETS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Patient Flow Integration Validation Runner (Step 2D-3D)")
    parser.add_argument("--processed-dir", default="data/processed", help="Directory containing processed datasets")
    parser.add_argument("--log-dir", default="outputs/logs", help="Directory for control outputs")
    parser.add_argument("--max-issue-examples", type=int, default=1000, help="Max issue examples")
    parser.add_argument("--reconciliation-tolerance", type=float, default=0.001, help="Reconciliation tolerance")
    return parser.parse_args()


def _build_blocked_manifest(
    validator: PatientFlowIntegrationValidator,
    started: datetime,
    blocking_reason: str,
) -> Dict[str, Any]:
    completed = datetime.now()
    return {
        "integration_run_id": validator.integration_run_id,
        "integration_started_datetime": started.isoformat(),
        "integration_completed_datetime": completed.isoformat(),
        "engine_version": ENGINE_VERSION,
        "integration_version": INTEGRATION_VERSION,
        "prior_processing_run_ids": {},
        "validation_run_ids": {},
        "processed_datasets_checked": list(PROCESSED_DATASETS.keys()),
        "processed_dataset_row_counts": {},
        "manifest_verification_results": "Failed",
        "checksum_verification_results": "Failed",
        "schema_results": "Failed",
        "business_key_results": "Failed",
        "daily_grain_result": "Failed",
        "reconciliation_results": "Failed",
        "lineage_results": "Failed",
        "issue_counts_by_severity": {},
        "exclusion_counts": 0,
        "prohibited_field_check": "Failed",
        "run_status": "Blocked",
        "integration_passed_flag": False,
        "output_files": [],
        "unresolved_rules": ["Pending Review"],
        "known_limitations": ["Integration blocked by gate."],
        "blocking_reason": blocking_reason,
    }


def _build_success_manifest(validator: PatientFlowIntegrationValidator, started: datetime) -> Dict[str, Any]:
    completed = datetime.now()
    issue_counts = {}
    for i in validator.issues:
        issue_counts[i.severity] = issue_counts.get(i.severity, 0) + 1
    summary = validator.build_integration_summary()
    summary["integration_started_datetime"] = started.isoformat()
    summary["integration_completed_datetime"] = completed.isoformat()
    summary["output_files"] = [
        "patient_flow_integration_manifest.json",
        "patient_flow_integration_dataset_summary.csv",
        "patient_flow_integration_check_results.csv",
        "patient_flow_integration_issue_log.csv",
        "patient_flow_integration_lineage_summary.csv",
        "patient_flow_integration_lineage_gap_log.csv",
        "patient_flow_integration_exclusion_summary.csv",
        "patient_flow_integration_audit_log.csv",
        "patient_flow_cross_step_reconciliation.csv",
    ]
    return summary


def main(
    processed_dir: str = "data/processed",
    log_dir: str = "outputs/logs",
    max_issue_examples: int = 1000,
    reconciliation_tolerance: float = 0.001,
) -> Dict[str, Any]:
    """Main integration orchestration."""
    started = datetime.now()
    integration_run_id = f"INT-PFD-{uuid.uuid4().hex[:12].upper()}"

    processed_path = Path(processed_dir)
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    validator = PatientFlowIntegrationValidator(
        integration_run_id=integration_run_id,
        processed_directory=processed_path,
        log_directory=log_path,
        max_issue_examples=max_issue_examples,
        reconciliation_tolerance=reconciliation_tolerance,
    )

    # 1. Load prior manifests (integration gate)
    gate = validator.load_prior_manifests()
    if not gate.processing_allowed:
        manifest = _build_blocked_manifest(validator, started, gate.blocking_reason)
        _write_manifest(log_path, manifest)
        print(f"Integration blocked: {gate.blocking_reason}")
        return {"success": False, "blocking_reason": gate.blocking_reason}

    # 2. Verify prior run statuses
    status_errors = validator.verify_prior_run_statuses()
    if status_errors:
        manifest = _build_blocked_manifest(validator, started, f"Prior run status failures: {status_errors}")
        _write_manifest(log_path, manifest)
        print("Integration blocked: prior run status failures")
        return {"success": False, "blocking_reason": "Prior run status failures"}

    # 3. Load processed datasets
    try:
        datasets = validator.load_processed_datasets()
    except FileNotFoundError as e:
        manifest = _build_blocked_manifest(validator, started, str(e))
        _write_manifest(log_path, manifest)
        print(f"Integration blocked: {e}")
        return {"success": False, "blocking_reason": str(e)}

    # 4. Verify manifest checksums
    checksum_ok = validator.verify_manifest_checksums()
    if not checksum_ok:
        manifest = _build_blocked_manifest(validator, started, "Checksum mismatch detected")
        _write_manifest(log_path, manifest)
        print("Integration blocked: checksum mismatch")
        return {"success": False, "blocking_reason": "Checksum mismatch"}

    # 5. Validate processed schemas
    schema_errors = validator.validate_processed_schemas()
    if schema_errors:
        manifest = _build_blocked_manifest(validator, started, f"Schema failures: {schema_errors}")
        _write_manifest(log_path, manifest)
        print("Integration blocked: schema failures")
        return {"success": False, "blocking_reason": "Schema failures"}

    # 6. Validate business keys
    bk_errors = validator.validate_business_keys()

    # 7. Validate cross-dataset references
    ref_errors = validator.validate_cross_dataset_references()

    # 8. Validate date alignment
    date_errors = validator.validate_date_alignment()

    # 9. Validate daily grain
    grain_errors = validator.validate_daily_grain()

    # 10. Reconcile encounters
    validator.reconcile_daily_encounters()

    # 11. Reconcile queue
    validator.reconcile_daily_queue()

    # 12. Reconcile bed capacity
    validator.reconcile_daily_bed_capacity()

    # 13. Reconcile service schedule
    validator.reconcile_daily_service_schedule()

    # 14. Validate cross-step lineage
    validator.validate_cross_step_lineage()

    # 15. Detect lineage gaps
    validator.detect_lineage_gaps()

    # 16. Consolidate issues
    consolidated_issues = validator.consolidate_issues()

    # 17. Consolidate exclusions
    consolidated_exclusions = validator.consolidate_exclusions()

    # 18. Check prohibited fields
    validator.check_prohibited_fields()

    # 19. Build integration summary
    manifest = _build_success_manifest(validator, started)
    manifest["exclusion_counts"] = len(consolidated_exclusions)
    _write_manifest(log_path, manifest)

    # 20. Export all integration outputs
    # Dataset summary
    summary_rows = []
    for ds_name, df in datasets.items():
        summary_rows.append({
            "integration_run_id": integration_run_id,
            "dataset_name": ds_name,
            "row_count": len(df),
            "column_count": len(df.columns),
            "checksum": validator.dataset_checksums.get(ds_name, ""),
            "checked_datetime": datetime.now(),
        })
    pd.DataFrame(summary_rows).to_csv(log_path / "patient_flow_integration_dataset_summary.csv", index=False)

    # Check results
    pd.DataFrame(validator.check_results).to_csv(log_path / "patient_flow_integration_check_results.csv", index=False)

    # Issue log (integration-specific + consolidated)
    integration_issues = pd.DataFrame([i.to_dict() for i in validator.issues])
    if not consolidated_issues.empty:
        all_issues = pd.concat([consolidated_issues, integration_issues], ignore_index=True)
    else:
        all_issues = integration_issues
    all_issues.to_csv(log_path / "patient_flow_integration_issue_log.csv", index=False)

    # Lineage summary
    pd.DataFrame(validator.lineage_summary).to_csv(log_path / "patient_flow_integration_lineage_summary.csv", index=False)

    # Lineage gap log
    pd.DataFrame(validator.lineage_gaps).to_csv(log_path / "patient_flow_integration_lineage_gap_log.csv", index=False)

    # Exclusion summary
    consolidated_exclusions.to_csv(log_path / "patient_flow_integration_exclusion_summary.csv", index=False)

    # Audit log
    pd.DataFrame(validator.audit_events).to_csv(log_path / "patient_flow_integration_audit_log.csv", index=False)

    # Cross-step reconciliation
    pd.DataFrame(validator.reconciliation_records).to_csv(log_path / "patient_flow_cross_step_reconciliation.csv", index=False)

    # 21. Confirm datasets unchanged
    unchanged = True
    for ds_name, config in PROCESSED_DATASETS.items():
        file_path = processed_path / config["file_name"]
        current = validator._file_checksum(file_path)
        if current != validator.dataset_checksums.get(ds_name, current):
            unchanged = False
            print(f"Warning: {ds_name} changed during integration")

    # Print summary
    print("=" * 60)
    print("Patient Flow Integration Validation Complete (Step 2D-3D)")
    print("=" * 60)
    print(f"Integration run ID: {integration_run_id}")
    print(f"Datasets checked: {len(datasets)}")
    print(f"Row counts: encounters={len(datasets.get('processed_patient_encounters', pd.DataFrame()))}, "
          f"queue={len(datasets.get('processed_patient_queue', pd.DataFrame()))}, "
          f"bed={len(datasets.get('processed_bed_capacity', pd.DataFrame()))}, "
          f"schedule={len(datasets.get('processed_service_schedule', pd.DataFrame()))}, "
          f"daily={len(datasets.get('processed_patient_flow_daily', pd.DataFrame()))}")
    print(f"Integration issues: {len(validator.issues)} (Warnings: {sum(1 for i in validator.issues if i.severity == 'Warning')}, "
          f"Errors: {sum(1 for i in validator.issues if i.severity == 'Error')}, "
          f"Critical: {sum(1 for i in validator.issues if i.severity == 'Critical')})")
    print(f"Consolidated prior issues: {len(consolidated_issues)}")
    print(f"Consolidated prior exclusions: {len(consolidated_exclusions)}")
    print(f"Reconciliation checks: {len(validator.reconciliation_records)}")
    print(f"Lineage coverage: {validator.lineage_summary[0]['lineage_coverage_percentage'] if validator.lineage_summary else 'N/A'}%")
    print(f"Lineage gaps: {len(validator.lineage_gaps)}")
    print(f"Datasets unchanged: {unchanged}")
    print(f"Integration status: {manifest['run_status']}")
    print("=" * 60)

    return {
        "success": True,
        "integration_run_id": integration_run_id,
        "manifest": manifest,
        "validator": validator,
    }


def _write_manifest(log_path: Path, manifest: Dict[str, Any]) -> None:
    manifest_path = log_path / "patient_flow_integration_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, default=str)


if __name__ == "__main__":
    args = parse_args()
    main(
        processed_dir=args.processed_dir,
        log_dir=args.log_dir,
        max_issue_examples=args.max_issue_examples,
        reconciliation_tolerance=args.reconciliation_tolerance,
    )
