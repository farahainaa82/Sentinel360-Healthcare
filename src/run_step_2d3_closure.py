"""
Sentinel360 Healthcare — Step 2D-3 Closure Runner

Cumulative regression testing and final acceptance verification runner.
Step: 2D-3E
"""

import argparse
import csv
import json
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src.step_2d3_closure_validator import (
    Step2D3ClosureValidator,
    CLOSURE_VERSION,
    ENGINE_VERSION,
    PROCESSED_DATASETS,
)


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Step 2D-3 Closure Runner (2D-3E)")
    parser.add_argument("--project-root", default=str(Path.cwd()), help="Project root directory")
    parser.add_argument("--processed-dir", default="data/processed", help="Processed data directory")
    parser.add_argument("--log-dir", default="outputs/logs", help="Logs directory")
    parser.add_argument("--tests-dir", default="tests", help="Tests directory")
    parser.add_argument("--skip-cumulative-suite", action="store_true", help="Skip final cumulative pytest suite")
    parser.add_argument("--max-issue-examples", type=int, default=1000, help="Max issue examples")
    return parser.parse_args(argv)


def _run_pytest_tests(tests_dir: Path, skip_cumulative: bool) -> List[Dict[str, Any]]:
    """Run individual test files sequentially, then optional cumulative suite."""
    test_files = [
        "test_demo_data_generator.py",
        "test_demo_data_export.py",
        "test_data_validation_engine.py",
        "test_processing_architecture.py",
        "test_workforce_transformation.py",
        "test_patient_encounter_transformation.py",
        "test_queue_capacity_schedule_transformation.py",
        "test_patient_flow_daily_builder.py",
        "test_patient_flow_integration.py",
        "test_step_2d3_closure.py",
    ]
    results = []
    all_passed = True
    for tf in test_files:
        path = tests_dir / tf
        if not path.exists():
            results.append({
                "test_file": tf,
                "tests_collected": 0,
                "passed": 0,
                "failed": 0,
                "errors": 0,
                "skipped": 0,
                "warnings": 0,
                "duration_seconds": 0.0,
                "final_status": "Missing",
            })
            all_passed = False
            continue
        cmd = [sys.executable, "-m", "pytest", str(path), "-q", "--tb=short"]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=300)
            out = proc.stdout + proc.stderr
            status = "Passed" if proc.returncode == 0 else "Failed"
            if proc.returncode != 0:
                all_passed = False
            # Parse summary line like "10 passed, 1 failed in 2.34s"
            collected, passed, failed, errors, skipped, warnings, duration = _parse_pytest_summary(out)
        except Exception as e:
            status = "Error"
            all_passed = False
            out = str(e)
            collected = passed = failed = errors = skipped = warnings = 0
            duration = 0.0
        results.append({
            "test_file": tf,
            "tests_collected": collected,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
            "warnings": warnings,
            "duration_seconds": duration,
            "final_status": status,
        })

    if not skip_cumulative and all_passed:
        cmd = [sys.executable, "-m", "pytest", str(tests_dir), "-q", "--tb=short"]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=600)
            out = proc.stdout + proc.stderr
            status = "Passed" if proc.returncode == 0 else "Failed"
            collected, passed, failed, errors, skipped, warnings, duration = _parse_pytest_summary(out)
        except Exception as e:
            status = "Error"
            out = str(e)
            collected = passed = failed = errors = skipped = warnings = 0
            duration = 0.0
        results.append({
            "test_file": "cumulative_suite",
            "tests_collected": collected,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
            "warnings": warnings,
            "duration_seconds": duration,
            "final_status": status,
        })
    return results


def _parse_pytest_summary(output: str):
    """Parse pytest summary lines for counts and duration."""
    collected = 0
    passed = 0
    failed = 0
    errors = 0
    skipped = 0
    warnings = 0
    duration = 0.0
    for line in output.splitlines():
        line = line.strip()
        if " collected" in line and "items" in line:
            # e.g. "10 items"
            parts = line.split()
            for i, p in enumerate(parts):
                if p == "collected":
                    try:
                        collected = int(parts[i-1])
                    except Exception:
                        pass
        if " passed" in line or " failed" in line or " error" in line or " skipped" in line:
            parts = line.split(",")
            for part in parts:
                part = part.strip()
                if " passed" in part:
                    try:
                        passed = int(part.split()[0])
                    except Exception:
                        pass
                elif " failed" in part:
                    try:
                        failed = int(part.split()[0])
                    except Exception:
                        pass
                elif " error" in part:
                    try:
                        errors = int(part.split()[0])
                    except Exception:
                        pass
                elif " skipped" in part:
                    try:
                        skipped = int(part.split()[0])
                    except Exception:
                        pass
            # duration at end like "in 2.34s"
            if " in " in line:
                try:
                    dur_str = line.split(" in ")[-1].replace("s", "").strip()
                    duration = float(dur_str)
                except Exception:
                    pass
        if "warnings" in line.lower():
            try:
                warnings = int(line.split()[0])
            except Exception:
                pass
    return collected, passed, failed, errors, skipped, warnings, duration


def _export_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    if not rows:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def _build_dataset_acceptance_rows(validator: Step2D3ClosureValidator, row_counts: Dict[str, Any], schemas: Dict[str, Any], checksums: Dict[str, Any], keys: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    for ds_name, meta in PROCESSED_DATASETS.items():
        rc = row_counts.get(ds_name, {})
        sc = schemas.get(ds_name, {})
        ch = checksums.get(ds_name, {})
        k = keys.get(ds_name, {})
        rows.append({
            "dataset_name": ds_name,
            "file_path": f"data/processed/{meta['file_name']}",
            "expected_row_count": rc.get("expected"),
            "actual_row_count": rc.get("actual"),
            "expected_primary_key": meta["primary_key"],
            "duplicate_key_count": k.get("duplicate_key_count"),
            "required_columns_present": sc.get("schema_status") == "Passed",
            "schema_status": sc.get("schema_status", "Unchecked"),
            "checksum_status": ch.get("status", "Unchecked"),
            "immutability_status": ch.get("status", "Unchecked"),
            "acceptance_status": "Passed" if all([
                rc.get("status") == "Passed",
                sc.get("schema_status") == "Passed",
                ch.get("status") == "Passed",
                k.get("status") == "Passed",
            ]) else "Failed",
            "notes": "",
        })
    return rows


def _build_schema_acceptance_rows(schemas: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    for ds_name, sc in schemas.items():
        rows.append({
            "dataset_name": ds_name,
            "registry_schema_name": sc.get("registry_schema_name", ds_name),
            "required_field_count": sc.get("required_field_count", 0),
            "actual_field_count": sc.get("actual_field_count", 0),
            "missing_fields": ", ".join(sc.get("missing_fields", [])),
            "unexpected_fields": ", ".join(sc.get("unexpected_fields", [])),
            "data_type_issue_count": sc.get("data_type_issue_count", 0),
            "schema_status": sc.get("schema_status", "Unchecked"),
            "notes": sc.get("notes", ""),
        })
    return rows


def _build_checksum_rows(checksums: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    for ds_name, ch in checksums.items():
        rows.append({
            "dataset_name": ds_name,
            "file_path": f"data/processed/{PROCESSED_DATASETS[ds_name]['file_name']}",
            "evidence_manifest": "prior_manifest",
            "expected_checksum": ch.get("expected"),
            "actual_checksum": ch.get("actual"),
            "checksum_status": ch.get("status", "Unchecked"),
            "checked_datetime": datetime.now().isoformat(),
        })
    return rows


def run_closure(args: argparse.Namespace) -> Dict[str, Any]:
    started = datetime.now()
    closure_run_id = f"CLOSURE-2D3E-{uuid.uuid4().hex[:12].upper()}"
    project_root = Path(args.project_root)
    processed_dir = project_root / args.processed_dir
    log_dir = project_root / args.log_dir
    tests_dir = project_root / args.tests_dir

    validator = Step2D3ClosureValidator(
        closure_run_id=closure_run_id,
        project_root=project_root,
        processed_directory=processed_dir,
        log_directory=log_dir,
        tests_directory=tests_dir,
        max_issue_examples=args.max_issue_examples,
    )

    print(f"[Closure] Run ID: {closure_run_id}")
    print(f"[Closure] Started: {started.isoformat()}")

    # 1. Inventory
    inventory_result = validator.inventory_required_files()
    print(f"[Closure] File inventory: {len(validator.file_inventory)} items, missing required: {len(inventory_result['missing_required'])}")

    # 2. Prior manifests
    validator.load_prior_manifests()
    print(f"[Closure] Prior manifests loaded: {len(validator.prior_manifests)}")

    # 3. Verify statuses
    statuses = validator.verify_prior_run_statuses()
    print(f"[Closure] Prior manifest statuses: {statuses}")

    # 4. Dataset presence
    presence = validator.verify_processed_dataset_presence()
    print(f"[Closure] Dataset presence: {sum(presence.values())}/{len(presence)} present")

    # 5. Row counts
    row_counts = validator.verify_processed_dataset_row_counts()
    print(f"[Closure] Row count checks complete")

    # 6. Checksums
    checksums = validator.verify_processed_dataset_checksums()
    print(f"[Closure] Checksum checks complete")

    # 7. Schemas
    schemas = validator.validate_all_processed_schemas()
    print(f"[Closure] Schema checks complete")

    # 8. Business keys
    keys = validator.validate_business_keys()
    print(f"[Closure] Business key checks complete")

    # 9. Daily grain
    grain = validator.validate_daily_grain()
    print(f"[Closure] Daily grain: {grain['status']}")

    # 10. Deterministic IDs
    ids_check = validator.validate_deterministic_daily_ids()
    print(f"[Closure] Deterministic IDs: {ids_check['status']}")

    # 11. Integration evidence
    integration = validator.verify_integration_results()
    print(f"[Closure] Integration evidence verified")

    # 12. Lineage
    lineage = validator.verify_lineage_acceptance()
    print(f"[Closure] Lineage acceptance: {lineage['status']}")

    # 13. Reconciliation
    recon = validator.verify_reconciliation_acceptance()
    print(f"[Closure] Reconciliation acceptance: {recon['status']}")

    # 14. Prohibited outputs
    prohibited = validator.detect_prohibited_outputs()
    print(f"[Closure] Prohibited output check complete")

    # 15. Immutability
    immutability = validator.confirm_dataset_immutability()
    print(f"[Closure] Immutability check complete")

    # 16. Documentation
    docs = validator.verify_documentation_presence()
    print(f"[Closure] Documentation presence: {docs['status']}")

    # 17. Test execution
    print("[Closure] Running regression tests...")
    test_results = _run_pytest_tests(tests_dir, args.skip_cumulative_suite)
    validator.consolidate_test_results(test_results)
    for tr in test_results:
        print(f"[Closure] {tr['test_file']}: {tr['final_status']} ({tr['passed']}/{tr['tests_collected']} passed)")

    # Build acceptance structures
    validator.dataset_acceptance = _build_dataset_acceptance_rows(validator, row_counts, schemas, checksums, keys)
    validator.schema_acceptance = _build_schema_acceptance_rows(schemas)
    validator.checksum_verification = _build_checksum_rows(checksums)

    # Build manifest
    manifest = validator.build_closure_manifest()
    print(f"[Closure] Manifest status: {manifest['run_status']}")

    # Export outputs
    log_dir.mkdir(parents=True, exist_ok=True)

    # Manifest JSON
    with open(log_dir / "step_2d3_closure_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Test summary
    _export_csv(
        log_dir / "step_2d3_test_summary.csv",
        validator.test_summary,
        ["test_file", "tests_collected", "passed", "failed", "errors", "skipped", "warnings", "duration_seconds", "final_status"],
    )

    # File inventory
    _export_csv(
        log_dir / "step_2d3_file_inventory.csv",
        validator.file_inventory,
        ["file_category", "step_reference", "file_path", "required_flag", "exists_flag", "file_size_bytes", "checksum", "acceptance_status", "notes", "checked_datetime"],
    )

    # Dataset acceptance
    _export_csv(
        log_dir / "step_2d3_dataset_acceptance_summary.csv",
        validator.dataset_acceptance,
        ["dataset_name", "file_path", "expected_row_count", "actual_row_count", "expected_primary_key", "duplicate_key_count", "required_columns_present", "schema_status", "checksum_status", "immutability_status", "acceptance_status", "notes"],
    )

    # Schema acceptance
    _export_csv(
        log_dir / "step_2d3_schema_acceptance_summary.csv",
        validator.schema_acceptance,
        ["dataset_name", "registry_schema_name", "required_field_count", "actual_field_count", "missing_fields", "unexpected_fields", "data_type_issue_count", "schema_status", "notes"],
    )

    # Checksum verification
    _export_csv(
        log_dir / "step_2d3_checksum_verification.csv",
        validator.checksum_verification,
        ["dataset_name", "file_path", "evidence_manifest", "expected_checksum", "actual_checksum", "checksum_status", "checked_datetime"],
    )

    # Acceptance checks
    _export_csv(
        log_dir / "step_2d3_acceptance_check_results.csv",
        validator.check_results,
        ["closure_run_id", "check_name", "status", "details", "checked_datetime"],
    )

    # Issue log
    issues = validator.collect_closure_issues()
    _export_csv(
        log_dir / "step_2d3_closure_issue_log.csv",
        issues,
        ["issue_id", "processing_run_id", "issue_type", "severity", "issue_description", "field_name", "blocks_processing"],
    )

    # Audit log
    _export_csv(
        log_dir / "step_2d3_closure_audit_log.csv",
        validator.audit_events,
        ["closure_run_id", "event", "details", "timestamp"],
    )

    print(f"[Closure] Outputs exported to {log_dir}")
    print(f"[Closure] Completed: {datetime.now().isoformat()}")
    print(f"[Closure] Final status: {manifest['run_status']}")

    return validator.return_closure_result()


def main() -> None:
    args = parse_args()
    run_closure(args)


if __name__ == "__main__":
    main()
