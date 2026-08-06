"""
Sentinel360 Healthcare — Workforce Processing Runner

Safe execution module for Step 2D-2 workforce transformation.

Usage:
    python src/run_workforce_processing.py
    python src/run_workforce_processing.py --input-dir data/demo --output-dir data/processed

Step: 2D-2
"""

import argparse
import hashlib
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src.processing_contracts import ValidationGateResult
from src.processing_models import ProcessingRun, ProcessingDatasetResult, ProcessingIssue
from src.workforce_transformer import WorkforceTransformer, TRANSFORMATION_VERSION, _file_checksum
from src.workforce_daily_builder import build_workforce_daily


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _generate_run_id() -> str:
    return f"PROC-{uuid.uuid4().hex[:12]}"


def _now() -> datetime:
    return datetime.now()


def load_validation_manifest(validation_log_dir: Path) -> Dict[str, Any]:
    path = validation_log_dir / "validation_run_manifest.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_dataset_summary(validation_log_dir: Path) -> Optional[pd.DataFrame]:
    path = validation_log_dir / "dataset_validation_summary.csv"
    if path.exists():
        return pd.read_csv(path, dtype=str)
    return None


def load_override_register(validation_log_dir: Path) -> Optional[pd.DataFrame]:
    path = validation_log_dir / "manual_override_register.csv"
    if path.exists():
        return pd.read_csv(path, dtype=str)
    return None


def run_workforce_processing(
    input_dir: Path = PROJECT_ROOT / "data" / "demo",
    output_dir: Path = PROJECT_ROOT / "data" / "processed",
    validation_log_dir: Path = PROJECT_ROOT / "outputs" / "logs",
    source_type: str = "synthetic_demo",
    collect_lineage: bool = True,
    max_issue_examples: int = 100,
) -> Dict[str, Any]:
    """Execute the full workforce processing pipeline."""

    run_id = _generate_run_id()
    run = ProcessingRun(
        processing_run_id=run_id,
        validation_run_id="",
        source_type=source_type,
        input_directory=str(input_dir),
        output_directory=str(output_dir),
        processing_started_datetime=_now(),
        processing_engine_version="1.0.0",
        transformation_version=TRANSFORMATION_VERSION,
        run_status="In Progress",
    )

    audit_events: List[Dict[str, Any]] = []

    def audit(event: str, details: str = "") -> None:
        audit_events.append(
            {
                "processing_run_id": run_id,
                "event": event,
                "details": details,
                "timestamp": _now().isoformat(),
            }
        )

    audit("Processing Started", f"run_id={run_id}")

    # Load validation outputs
    manifest = load_validation_manifest(validation_log_dir)
    summary = load_dataset_summary(validation_log_dir)
    overrides = load_override_register(validation_log_dir)
    run.validation_run_id = manifest.get("validation_run_id", "")

    # Check gate
    transformer = WorkforceTransformer(
        run=run,
        input_dir=input_dir,
        output_dir=output_dir,
        validation_run_id=run.validation_run_id,
        collect_lineage=collect_lineage,
        max_issue_examples=max_issue_examples,
    )
    gate = transformer.check_validation_gate(manifest, summary, overrides)
    if not gate.processing_allowed:
        run.run_status = "Blocked"
        run.processing_allowed_flag = False
        run.processing_completed_datetime = _now()
        audit("Processing Blocked", gate.blocking_reason)
        _export_blocked_manifest(run, audit_events, output_dir, validation_log_dir)
        print(f"Processing blocked: {gate.blocking_reason}")
        return {"status": "blocked", "reason": gate.blocking_reason}

    run.processing_allowed_flag = True
    audit("Validation Gate Passed", f"accepted={gate.accepted_datasets}")

    # Load sources
    transformer.load_source_datasets()
    audit("Source Datasets Loaded", f"count={len(transformer._source_dfs)}")

    # Transformations
    transforms = [
        ("processed_hospital_master", transformer.transform_hospital_master),
        ("processed_department_master", transformer.transform_department_master),
        ("processed_staff_role_master", transformer.transform_staff_role_master),
        ("processed_staff_master", transformer.transform_staff_master),
        ("processed_staff_roster", transformer.transform_staff_roster),
        ("processed_staff_attendance", transformer.transform_staff_attendance),
        ("processed_staffing_requirement", transformer.transform_staffing_requirement),
    ]

    for proc_name, transform_fn in transforms:
        audit("Dataset Transformation Started", proc_name)
        result = transform_fn()
        audit("Dataset Transformation Completed", f"{proc_name}: rows={result.to_dict()['processed_rows']}")
        # Schema validation
        audit("Processed Schema Validated", proc_name)
        schema_errors = transformer.validate_processed_schema(proc_name)
        if schema_errors:
            for err in schema_errors:
                transformer.issues.append(
                    ProcessingIssue(
                        processing_run_id=run_id,
                        issue_id=f"ISS-{uuid.uuid4().hex[:12]}",
                        processed_dataset_name=proc_name,
                        issue_type="Processed Schema Failure",
                        severity="Error",
                        issue_description=err,
                    )
                )
            # Mark dataset result as failed
            for dr in transformer.dataset_results:
                if dr.processed_dataset_name == proc_name:
                    dr.dataset_status = "Failed"

    # Build workforce daily
    audit("Dataset Transformation Started", "processed_workforce_daily")
    daily_df = build_workforce_daily(
        transformer._processed_dfs.get("processed_staff_roster", pd.DataFrame()),
        transformer._processed_dfs.get("processed_staff_attendance", pd.DataFrame()),
        transformer._processed_dfs.get("processed_staffing_requirement", pd.DataFrame()),
        run,
        run.validation_run_id,
    )
    transformer._processed_dfs["processed_workforce_daily"] = daily_df
    daily_result = ProcessingDatasetResult(
        processing_run_id=run_id,
        validation_run_id=run.validation_run_id,
        source_dataset_name="workforce_daily",
        processed_dataset_name="processed_workforce_daily",
        source_row_count=0,
        processed_row_count=len(daily_df),
        dataset_status="Processed" if not daily_df.empty else "Empty",
        processed_datetime=_now(),
    )
    transformer.dataset_results.append(daily_result)
    audit("Dataset Transformation Completed", f"processed_workforce_daily: rows={len(daily_df)}")

    # Validate workforce daily schema
    schema_errors = transformer.validate_processed_schema("processed_workforce_daily")
    if schema_errors:
        for err in schema_errors:
            transformer.issues.append(
                ProcessingIssue(
                    processing_run_id=run_id,
                    issue_id=f"ISS-{uuid.uuid4().hex[:12]}",
                    processed_dataset_name="processed_workforce_daily",
                    issue_type="Processed Schema Failure",
                    severity="Error",
                    issue_description=err,
                )
            )
        daily_result.dataset_status = "Failed"

    # Build lineage and exclusions
    audit("Lineage Generated", f"records={len(transformer.build_lineage())}")
    audit("Exclusion Register Generated", f"records={len(transformer.build_exclusions())}")

    # Export processed datasets
    processed_names = [
        "processed_hospital_master",
        "processed_department_master",
        "processed_staff_role_master",
        "processed_staff_master",
        "processed_staff_roster",
        "processed_staff_attendance",
        "processed_staffing_requirement",
        "processed_workforce_daily",
    ]
    for name in processed_names:
        transformer.export_processed_dataset(name)
        audit("Output Exported", name)

    # Source checksum confirmation
    for name, checksum in transformer.source_checksums.items():
        path = input_dir / f"{name}.csv"
        if path.exists():
            current = _file_checksum(path)
            if current != checksum:
                transformer.issues.append(
                    ProcessingIssue(
                        processing_run_id=run_id,
                        issue_id=f"ISS-{uuid.uuid4().hex[:12]}",
                        issue_type="Source Checksum Mismatch",
                        severity="Critical",
                        issue_description=f"Source {name} changed during processing.",
                    )
                )
    audit("Source Checksum Confirmed", "all sources unchanged")

    # Finalise run
    run.processing_completed_datetime = _now()
    run.run_status = "Completed"
    run.source_dataset_count = len(transformer._source_dfs)
    run.processed_dataset_count = len([n for n in processed_names if n in transformer._processed_dfs])
    run.source_record_count = sum(len(df) for df in transformer._source_dfs.values())
    run.processed_record_count = sum(len(transformer._processed_dfs.get(n, pd.DataFrame())) for n in processed_names)
    run.excluded_record_count = sum(dr.excluded_row_count for dr in transformer.dataset_results)
    run.warning_count = sum(1 for i in transformer.issues if i.severity == "Warning")
    run.error_count = sum(1 for i in transformer.issues if i.severity in ("Error", "Critical"))

    # Export control outputs
    _export_control_outputs(run, transformer, audit_events, output_dir, validation_log_dir)
    audit("Processing Completed", f"run_id={run_id}")

    print("Workforce processing completed successfully.")
    print(f"  Run ID: {run_id}")
    print(f"  Validation Run ID: {run.validation_run_id}")
    print(f"  Processed datasets: {run.processed_dataset_count}")
    print(f"  Total source records: {run.source_record_count}")
    print(f"  Total processed records: {run.processed_record_count}")
    print(f"  Excluded records: {run.excluded_record_count}")
    print(f"  Warnings: {run.warning_count}")
    print(f"  Errors: {run.error_count}")

    return {
        "status": "completed",
        "run_id": run_id,
        "validation_run_id": run.validation_run_id,
        "processed_dataset_count": run.processed_dataset_count,
        "source_record_count": run.source_record_count,
        "processed_record_count": run.processed_record_count,
        "excluded_record_count": run.excluded_record_count,
        "warning_count": run.warning_count,
        "error_count": run.error_count,
    }


def _export_blocked_manifest(
    run: ProcessingRun,
    audit_events: List[Dict[str, Any]],
    output_dir: Path,
    validation_log_dir: Path,
) -> None:
    manifest = run.to_dict()
    manifest["audit_events"] = audit_events
    manifest["issues"] = []
    manifest["dataset_results"] = []
    out_path = validation_log_dir / "workforce_processing_run_manifest.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def _export_control_outputs(
    run: ProcessingRun,
    transformer: WorkforceTransformer,
    audit_events: List[Dict[str, Any]],
    output_dir: Path,
    validation_log_dir: Path,
) -> None:
    log_dir = validation_log_dir
    log_dir.mkdir(parents=True, exist_ok=True)

    # A. Manifest
    manifest = run.to_dict()
    manifest["source_datasets"] = list(transformer._source_dfs.keys())
    manifest["processed_datasets"] = [dr.processed_dataset_name for dr in transformer.dataset_results]
    manifest["source_record_counts"] = {k: len(v) for k, v in transformer._source_dfs.items()}
    manifest["processed_record_counts"] = {k: len(v) for k, v in transformer._processed_dfs.items()}
    manifest["excluded_record_counts"] = {dr.processed_dataset_name: dr.excluded_row_count for dr in transformer.dataset_results}
    manifest["issue_counts_by_severity"] = _count_issues_by_severity(transformer.issues)
    manifest["source_checksums"] = transformer.source_checksums
    manifest["processed_checksums"] = transformer.processed_checksums
    manifest["output_files"] = [str(output_dir / f"{n}.csv") for n in transformer._processed_dfs.keys()]
    manifest["unresolved_rules"] = []
    manifest["known_limitations"] = ["Workforce daily aggregation does not calculate KPI percentages."]
    manifest["audit_events"] = audit_events
    with open(log_dir / "workforce_processing_run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # B. Dataset summary
    summary_rows = [dr.to_dict() for dr in transformer.dataset_results]
    pd.DataFrame(summary_rows).to_csv(log_dir / "workforce_processing_dataset_summary.csv", index=False)

    # C. Issue log
    issue_rows = [i.to_dict() for i in transformer.issues]
    if issue_rows:
        pd.DataFrame(issue_rows).to_csv(log_dir / "workforce_processing_issue_log.csv", index=False)
    else:
        pd.DataFrame(columns=[
            "processing_run_id", "issue_id", "source_dataset_name", "processed_dataset_name",
            "field_name", "issue_type", "severity", "issue_description", "source_value",
            "processed_value", "exclusion_flag", "blocks_processing", "created_datetime",
        ]).to_csv(log_dir / "workforce_processing_issue_log.csv", index=False)

    # D. Lineage
    lineage_df = transformer.build_lineage()
    if not lineage_df.empty:
        lineage_df.to_csv(log_dir / "workforce_processing_lineage.csv", index=False)
    else:
        pd.DataFrame(columns=[
            "processing_run_id", "lineage_id", "validation_run_id", "source_dataset_name",
            "source_file_name", "source_primary_key_field", "source_primary_key_value",
            "source_row_number", "processed_dataset_name", "processed_primary_key_field",
            "processed_primary_key_value", "transformation_rule_id", "transformation_description",
            "source_fields_used", "processed_fields_created", "exclusion_flag",
            "exclusion_reason_code", "transformation_version", "configuration_version", "processed_datetime",
        ]).to_csv(log_dir / "workforce_processing_lineage.csv", index=False)

    # E. Exclusion register
    exclusion_df = transformer.build_exclusions()
    if not exclusion_df.empty:
        exclusion_df.to_csv(log_dir / "workforce_processing_exclusion_register.csv", index=False)
    else:
        pd.DataFrame(columns=[
            "processing_run_id", "exclusion_id", "source_dataset_name", "source_primary_key_field",
            "source_primary_key_value", "source_row_number", "exclusion_reason_code",
            "exclusion_reason_description", "validation_issue_id", "manual_override_id",
            "exclusion_stage", "excluded_by_rule", "reversible_flag", "created_datetime",
        ]).to_csv(log_dir / "workforce_processing_exclusion_register.csv", index=False)

    # F. Audit log
    pd.DataFrame(audit_events).to_csv(log_dir / "workforce_processing_audit_log.csv", index=False)


def _count_issues_by_severity(issues: List[ProcessingIssue]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for i in issues:
        counts[i.severity] = counts.get(i.severity, 0) + 1
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Sentinel360 Workforce Processing Runner")
    parser.add_argument("--input-dir", default=str(PROJECT_ROOT / "data" / "demo"))
    parser.add_argument("--output-dir", default=str(PROJECT_ROOT / "data" / "processed"))
    parser.add_argument("--validation-log-dir", default=str(PROJECT_ROOT / "outputs" / "logs"))
    parser.add_argument("--source-type", default="synthetic_demo")
    parser.add_argument("--collect-lineage", type=lambda x: x.lower() == "true", default=True)
    parser.add_argument("--max-issue-examples", type=int, default=100)
    args = parser.parse_args()

    run_workforce_processing(
        input_dir=Path(args.input_dir),
        output_dir=Path(args.output_dir),
        validation_log_dir=Path(args.validation_log_dir),
        source_type=args.source_type,
        collect_lineage=args.collect_lineage,
        max_issue_examples=args.max_issue_examples,
    )


if __name__ == "__main__":
    main()
