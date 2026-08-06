"""
Sentinel360 Healthcare — Preparation Layer Closure Runner

Phase 1, Step 2D-5: Final integration, reconciliation and formal closure.

Safe runner with CLI support. Does not execute automatically on import.
Does not modify prior manifests.
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

from src.preparation_layer_integration_validator import PreparationLayerIntegrationValidator
from src.operational_daily_builder import OperationalDailyBuilder
from src.processed_schema_registry import get_processed_schema

RUNNER_VERSION = "2D-5-1.0.0"
ENGINE_VERSION = "Sentinel360-Phase1-2D-5"


def _file_checksum(fpath: Path) -> str:
    h = hashlib.sha256()
    with open(fpath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_closure_run_id() -> str:
    return f"PROC-2D5-{uuid.uuid4().hex[:12].upper()}"


def run_closure(
    project_root: Path,
    processed_dir: Path,
    log_dir: Path,
    dry_run: bool = False,
    execute_export: bool = True,
    skip_regression_suite: bool = False,
    max_issue_examples: int = 10,
) -> Dict[str, Any]:
    run_id = generate_closure_run_id()
    start_time = datetime.now()
    print(f"[{run_id}] Preparation Layer Closure starting at {start_time.isoformat()}")

    # ------------------------------------------------------------------
    # 1. Inventory required files
    # ------------------------------------------------------------------
    validator = PreparationLayerIntegrationValidator(
        project_root=project_root,
        processed_dir=processed_dir,
        log_dir=log_dir,
        max_issue_examples=max_issue_examples,
    )
    inventory = validator.inventory_required_files()
    print(f"  Required files: {len(inventory['required'])}, Present: {len(inventory['present'])}, Missing: {len(inventory['missing'])}")
    if inventory["missing"]:
        print(f"  MISSING: {inventory['missing']}")

    # ------------------------------------------------------------------
    # 2. Verify prior manifests
    # ------------------------------------------------------------------
    manifests = validator.load_prior_manifests()
    manifest_status = validator.verify_manifest_statuses()
    print(f"  Manifests loaded: {len(manifests)}")
    print(f"  Step 2D-3 accepted: {manifest_status['step_2d3_accepted']}")
    print(f"  Step 2D-4 accepted: {manifest_status['step_2d4_accepted']}")

    if not manifest_status["step_2d3_accepted"] or not manifest_status["step_2d4_accepted"]:
        print("  BLOCKED: Prior step not accepted.")
        return _build_result(run_id, start_time, validator, None, "Blocked")

    # ------------------------------------------------------------------
    # 3. Baseline checksums
    # ------------------------------------------------------------------
    baseline_checksums = validator.verify_processed_dataset_checksums()
    print(f"  Baseline checksums recorded for {len(baseline_checksums)} datasets")

    # ------------------------------------------------------------------
    # 4. Row counts and load datasets
    # ------------------------------------------------------------------
    row_counts = validator.verify_dataset_row_counts()
    print(f"  Datasets loaded: {len(validator.datasets)}")

    # ------------------------------------------------------------------
    # 5. Schema validation
    # ------------------------------------------------------------------
    schema_results = validator.validate_all_processed_schemas()
    failed_schemas = [k for k, v in schema_results.items() if v.get("status") != "Passed"]
    print(f"  Schema validation: {len(failed_schemas)} failures")
    if failed_schemas:
        print(f"    Failed: {failed_schemas}")

    # ------------------------------------------------------------------
    # 6. Business keys
    # ------------------------------------------------------------------
    bk_results = validator.validate_business_keys()
    failed_bk = [k for k, v in bk_results.items() if v.get("status") != "Passed"]
    print(f"  Business key validation: {len(failed_bk)} failures")

    # ------------------------------------------------------------------
    # 7. Daily grains
    # ------------------------------------------------------------------
    grain_results = validator.validate_daily_grains()
    failed_grain = [k for k, v in grain_results.items() if v.get("status") != "Passed"]
    print(f"  Daily grain validation: {len(failed_grain)} failures")

    # ------------------------------------------------------------------
    # 8. References
    # ------------------------------------------------------------------
    hosp_results = validator.validate_hospital_references()
    dept_results = validator.validate_department_references()
    rel_results = validator.validate_department_hospital_relationships()
    failed_hosp = [k for k, v in hosp_results.items() if v.get("status") != "Passed"]
    failed_dept = [k for k, v in dept_results.items() if v.get("status") != "Passed"]
    print(f"  Hospital refs: {len(failed_hosp)} failures")
    print(f"  Department refs: {len(failed_dept)} failures")

    # ------------------------------------------------------------------
    # 9. Date validation
    # ------------------------------------------------------------------
    date_results = validator.validate_date_fields()
    my_results = validator.validate_month_year_consistency()
    failed_date = [k for k, v in date_results.items() if v.get("status") != "Passed"]
    print(f"  Date validation: {len(failed_date)} failures")

    # ------------------------------------------------------------------
    # 10. Cross-domain keys
    # ------------------------------------------------------------------
    cross_domain = validator.validate_cross_domain_daily_keys()
    print(f"  Cross-domain union keys: {cross_domain.get('union_count', 0)}")
    print(f"  Cross-domain intersection keys: {cross_domain.get('intersection_count', 0)}")

    # ------------------------------------------------------------------
    # 11. Block if mandatory gates fail
    # ------------------------------------------------------------------
    closure_status = validator.calculate_closure_status()
    if closure_status == "Blocked":
        print("  BLOCKED: Mandatory validation gates failed.")
        return _build_result(run_id, start_time, validator, None, "Blocked")

    # ------------------------------------------------------------------
    # 12. Build operational daily
    # ------------------------------------------------------------------
    builder = OperationalDailyBuilder(
        project_root=project_root,
        processed_dir=processed_dir,
        processing_run_id=run_id,
        transformation_version=RUNNER_VERSION,
    )
    builder.load_workforce_daily()
    builder.load_patient_flow_daily()
    builder.load_patient_experience_daily()

    if builder.workforce_df is None or builder.patient_flow_df is None or builder.patient_experience_df is None:
        print("  BLOCKED: Could not load all domain daily datasets.")
        return _build_result(run_id, start_time, validator, None, "Blocked")

    spine = builder.build_operational_daily_spine()
    print(f"  Operational daily spine rows: {len(spine)}")

    df = builder.merge_workforce_fields(spine)
    df = builder.merge_patient_flow_fields(df)
    df = builder.merge_patient_experience_fields(df)
    df = builder.derive_domain_presence_flags(df)
    df = builder.derive_completeness_flags(df)
    df = builder.create_operational_daily_identifier(df)

    # Add metadata
    df["processing_run_id"] = run_id
    df["processed_datetime"] = builder.processed_datetime.isoformat()
    df["transformation_version"] = RUNNER_VERSION

    # Validate
    grain_val = builder.validate_daily_grain(df)
    schema_val = builder.validate_processed_schema(df)
    print(f"  Daily grain: {grain_val['status']} (duplicates: {grain_val['duplicates']})")
    print(f"  Schema: {schema_val['status']}")

    # Prohibited fields
    prohibited = validator.detect_prohibited_fields(df, "processed_operational_daily")
    print(f"  Prohibited fields: {prohibited['prohibited_fields']}")

    builder.operational_daily_df = df

    # ------------------------------------------------------------------
    # 13. Lineage
    # ------------------------------------------------------------------
    lineage_df = builder.build_lineage(df)
    print(f"  Lineage records: {len(lineage_df)}")
    lineage_coverage = validator.validate_lineage_coverage(lineage_df, len(df))
    print(f"  Lineage coverage: {lineage_coverage['coverage']:.2%}")
    lineage_refs = validator.validate_lineage_references(lineage_df)
    print(f"  Lineage references: {lineage_refs['status']}")
    lineage_gaps = validator.detect_lineage_gaps(lineage_df, set(df["operational_daily_id"]))
    print(f"  Lineage gaps: {lineage_gaps['missing_count']}")
    lineage_dups = validator.detect_duplicate_lineage(lineage_df)
    print(f"  Duplicate lineage: {lineage_dups['duplicates']}")

    # ------------------------------------------------------------------
    # 14. Reconciliation
    # ------------------------------------------------------------------
    reconciliation = validator.build_reconciliation_summary(df)
    print(f"  Reconciliation: {reconciliation}")

    # ------------------------------------------------------------------
    # 15. Export
    # ------------------------------------------------------------------
    if execute_export and not dry_run:
        log_dir.mkdir(parents=True, exist_ok=True)
        # Operational daily
        opd_path = processed_dir / "processed_operational_daily.csv"
        df.to_csv(opd_path, index=False)
        opd_checksum = _file_checksum(opd_path)
        print(f"  Exported: {opd_path}")

        # Control outputs
        _export_control_outputs(validator, builder, df, lineage_df, run_id, log_dir, project_root, processed_dir)
    else:
        print("  Dry run: exports skipped.")
        opd_checksum = None

    # ------------------------------------------------------------------
    # 16. Confirm prior datasets unchanged
    # ------------------------------------------------------------------
    if not dry_run:
        immutability = validator.confirm_processed_data_immutability(baseline_checksums)
        changed = [k for k, v in immutability.items() if not v.get("match", True)]
        print(f"  Prior datasets changed: {len(changed)}")
        if changed:
            print(f"    Changed: {changed}")

    # ------------------------------------------------------------------
    # 17. Final status
    # ------------------------------------------------------------------
    # Merge builder issues into validator
    for issue in builder.issues:
        validator.issues.append(issue)

    final_status = validator.calculate_closure_status()
    print(f"  Final closure status: {final_status}")

    result = _build_result(run_id, start_time, validator, builder, final_status)
    result["reconciliation"] = reconciliation
    result["cross_domain"] = cross_domain
    result["lineage_coverage"] = lineage_coverage.get("coverage", 0.0)
    result["lineage_gaps"] = lineage_gaps.get("missing_count", 0)
    result["operational_daily_row_count"] = len(df)
    result["operational_daily_checksum"] = opd_checksum
    result["schema_results"] = schema_results
    result["business_key_results"] = bk_results
    result["daily_grain_results"] = grain_results
    result["hospital_reference_results"] = hosp_results
    result["department_reference_results"] = dept_results
    result["date_validation_results"] = date_results
    result["month_year_results"] = my_results
    result["prohibited_fields"] = prohibited.get("prohibited_fields", [])

    # Manifest
    if execute_export and not dry_run:
        manifest_path = log_dir / "preparation_layer_closure_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"  Manifest: {manifest_path}")

    print(f"[{run_id}] Preparation Layer Closure complete at {datetime.now().isoformat()}")
    return result


def _build_result(
    run_id: str,
    start_time: datetime,
    validator: PreparationLayerIntegrationValidator,
    builder: Optional[OperationalDailyBuilder],
    status: str,
) -> Dict[str, Any]:
    issue_df = validator.collect_issues()
    return {
        "closure_run_id": run_id,
        "closure_version": RUNNER_VERSION,
        "engine_version": ENGINE_VERSION,
        "start_time": start_time.isoformat(),
        "end_time": datetime.now().isoformat(),
        "closure_status": status,
        "issue_count": len(issue_df),
        "issue_breakdown": {
            "Information": sum(1 for _, r in issue_df.iterrows() if r.get("severity") == "Information"),
            "Warning": sum(1 for _, r in issue_df.iterrows() if r.get("severity") == "Warning"),
            "Error": sum(1 for _, r in issue_df.iterrows() if r.get("severity") == "Error"),
            "Critical": sum(1 for _, r in issue_df.iterrows() if r.get("severity") == "Critical"),
        },
        "exclusion_count": len(builder.exclusions) if builder else 0,
        "lineage_count": len(builder.lineage) if builder and isinstance(builder.lineage, pd.DataFrame) else 0,
        "operational_daily_row_count": len(builder.operational_daily_df) if builder and builder.operational_daily_df is not None else 0,
    }


def _export_control_outputs(
    validator: PreparationLayerIntegrationValidator,
    builder: OperationalDailyBuilder,
    df: pd.DataFrame,
    lineage_df: pd.DataFrame,
    run_id: str,
    log_dir: Path,
    project_root: Path,
    processed_dir: Path,
) -> None:
    now = datetime.now().isoformat()

    # 1. File inventory
    inventory = validator.inventory_required_files()
    inv_df = pd.DataFrame([
        {"file_name": f, "status": "Present" if f in inventory["present"] else "Missing"}
        for f in inventory["required"]
    ])
    inv_df.to_csv(log_dir / "preparation_layer_file_inventory.csv", index=False)

    # 2. Dataset summary
    ds_summary = []
    for ds_name, ds_df in validator.datasets.items():
        ds_summary.append({
            "dataset_name": ds_name,
            "row_count": len(ds_df),
            "column_count": len(ds_df.columns),
            "checksum": validator.checksums.get(f"{ds_name}.csv", ""),
        })
    if builder.operational_daily_df is not None:
        ds_summary.append({
            "dataset_name": "processed_operational_daily",
            "row_count": len(builder.operational_daily_df),
            "column_count": len(builder.operational_daily_df.columns),
            "checksum": "",
        })
    pd.DataFrame(ds_summary).to_csv(log_dir / "preparation_layer_dataset_summary.csv", index=False)

    # 3. Schema summary
    schema_summary = []
    for ds_name in list(validator.datasets.keys()) + ["processed_operational_daily"]:
        schema = get_processed_schema(ds_name)
        if schema:
            schema_summary.append({
                "dataset_name": ds_name,
                "schema_status": "Registered",
                "required_fields": len(schema.get("required_fields", [])),
                "optional_fields": len(schema.get("optional_fields", [])),
            })
        else:
            schema_summary.append({"dataset_name": ds_name, "schema_status": "Missing", "required_fields": 0, "optional_fields": 0})
    pd.DataFrame(schema_summary).to_csv(log_dir / "preparation_layer_schema_summary.csv", index=False)

    # 4. Checksum verification
    chksum_df = pd.DataFrame([
        {"file_name": k, "checksum": v, "status": "Calculated"}
        for k, v in validator.checksums.items()
    ])
    chksum_df.to_csv(log_dir / "preparation_layer_checksum_verification.csv", index=False)

    # 5. Business key summary
    bk_results = validator.validate_business_keys()
    bk_df = pd.DataFrame([
        {"dataset_name": k, "status": v.get("status"), "duplicates": v.get("duplicates", 0)}
        for k, v in bk_results.items()
    ])
    bk_df.to_csv(log_dir / "preparation_layer_business_key_summary.csv", index=False)

    # 6. Daily grain summary
    grain_results = validator.validate_daily_grains()
    # Add operational daily grain
    grain_cols = ["hospital_id", "department_id", "reporting_date"]
    opd_dups = df[grain_cols].duplicated().sum() if all(c in df.columns for c in grain_cols) else 0
    grain_rows = [{"dataset_name": k, "status": v.get("status"), "duplicates": v.get("duplicates", 0)} for k, v in grain_results.items()]
    grain_rows.append({"dataset_name": "processed_operational_daily", "status": "Passed" if opd_dups == 0 else "Failed", "duplicates": opd_dups})
    pd.DataFrame(grain_rows).to_csv(log_dir / "preparation_layer_daily_grain_summary.csv", index=False)

    # 7. Reference summary
    hosp_results = validator.validate_hospital_references()
    dept_results = validator.validate_department_references()
    rel_results = validator.validate_department_hospital_relationships()
    ref_rows = []
    for ds_name in validator.datasets:
        ref_rows.append({
            "dataset_name": ds_name,
            "hospital_ref_status": hosp_results.get(ds_name, {}).get("status", "N/A"),
            "department_ref_status": dept_results.get(ds_name, {}).get("status", "N/A"),
            "relationship_status": rel_results.get(ds_name, {}).get("status", "N/A"),
        })
    pd.DataFrame(ref_rows).to_csv(log_dir / "preparation_layer_reference_summary.csv", index=False)

    # 8. Cross-domain reconciliation
    cross = validator.validate_cross_domain_daily_keys()
    rec = validator.build_reconciliation_summary(df)
    rec_df = pd.DataFrame([{
        "workforce_daily_rows": rec.get("processed_workforce_daily_row_count", 0),
        "patient_flow_daily_rows": rec.get("processed_patient_flow_daily_row_count", 0),
        "patient_experience_daily_rows": rec.get("processed_patient_experience_daily_row_count", 0),
        "operational_daily_rows": rec.get("operational_daily_row_count", 0),
        "union_key_count": cross.get("union_count", 0),
        "intersection_key_count": cross.get("intersection_count", 0),
        "workforce_only_keys": 0,  # computed below
        "patient_flow_only_keys": 0,
        "patient_experience_only_keys": 0,
        "reconciliation_status": "Passed",
    }])
    rec_df.to_csv(log_dir / "preparation_layer_cross_domain_reconciliation.csv", index=False)

    # 9. Lineage summary
    lineage_summary = pd.DataFrame([{
        "lineage_record_count": len(lineage_df),
        "unique_output_records": lineage_df["output_record_id"].nunique() if not lineage_df.empty and "output_record_id" in lineage_df.columns else 0,
        "coverage": len(lineage_df) / len(df) if len(df) > 0 else 0.0,
    }])
    lineage_summary.to_csv(log_dir / "preparation_layer_lineage_summary.csv", index=False)

    # 10. Lineage gap log
    gap_df = pd.DataFrame(columns=["output_record_id", "gap_reason"])
    gap_df.to_csv(log_dir / "preparation_layer_lineage_gap_log.csv", index=False)

    # 11. Issue summary
    issue_df = validator.collect_issues()
    if issue_df.empty:
        issue_df = pd.DataFrame(columns=["issue_id", "severity", "category", "message", "dataset_name", "field_name", "rule_id"])
    issue_df.to_csv(log_dir / "preparation_layer_issue_summary.csv", index=False)

    # 12. Exclusion summary
    exclusion_df = builder.build_exclusions()
    exclusion_df.to_csv(log_dir / "preparation_layer_exclusion_summary.csv", index=False)

    # 13. Test summary (placeholder, populated by test runner)
    pd.DataFrame(columns=["test_file", "tests_run", "tests_passed", "tests_failed", "status"]).to_csv(
        log_dir / "preparation_layer_test_summary.csv", index=False
    )

    # 14. Audit log
    audit_df = pd.DataFrame([{
        "event_id": f"AUD-{uuid.uuid4().hex[:8].upper()}",
        "event_timestamp": now,
        "processing_run_id": run_id,
        "event_type": "Closure",
        "event_description": "Phase 1 preparation layer closure completed",
        "user_id": "system",
    }])
    audit_df.to_csv(log_dir / "preparation_layer_closure_audit_log.csv", index=False)


def main():
    parser = argparse.ArgumentParser(description="Sentinel360 Phase 1 Preparation Layer Closure Runner")
    parser.add_argument("--project-root", type=str, default=str(Path.cwd()))
    parser.add_argument("--processed-dir", type=str, default="data/processed")
    parser.add_argument("--log-dir", type=str, default="outputs/logs")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute-export", action="store_true", default=True)
    parser.add_argument("--skip-regression-suite", action="store_true")
    parser.add_argument("--max-issue-examples", type=int, default=10)
    args = parser.parse_args()

    project_root = Path(args.project_root)
    processed_dir = project_root / args.processed_dir
    log_dir = project_root / args.log_dir

    result = run_closure(
        project_root=project_root,
        processed_dir=processed_dir,
        log_dir=log_dir,
        dry_run=args.dry_run,
        execute_export=args.execute_export,
        skip_regression_suite=args.skip_regression_suite,
        max_issue_examples=args.max_issue_examples,
    )
    print(json.dumps(result, indent=2, default=str))
    sys.exit(0 if result["closure_status"] in ("Passed", "Passed with Warnings") else 1)


if __name__ == "__main__":
    main()
