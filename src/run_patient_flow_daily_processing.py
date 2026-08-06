"""
Sentinel360 Healthcare — Patient Flow Daily Processing Runner

Safe runner for Step 2D-3C.
Orchestrates loading, aggregation, validation and export of
processed_patient_flow_daily.csv.
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

from src.patient_flow_daily_builder import PatientFlowDailyBuilder, TRANSFORMATION_VERSION, ENGINE_VERSION, INPUT_DATASETS
from src.processed_schema_registry import get_processed_schema
from src.processing_models import ProcessingDatasetResult


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Patient Flow Daily Processing Runner (Step 2D-3C)")
    parser.add_argument("--input-dir", default="data/processed", help="Directory containing processed inputs")
    parser.add_argument("--output-dir", default="data/processed", help="Directory for processed output")
    parser.add_argument("--log-dir", default="outputs/logs", help="Directory for control outputs")
    parser.add_argument("--source-type", default="processed_synthetic_demo", help="Source type label")
    parser.add_argument("--collect-lineage", default="true", help="Collect lineage (true/false)")
    parser.add_argument("--max-issue-examples", type=int, default=1000, help="Max issue examples")
    return parser.parse_args()


def _build_blocked_manifest(
    builder: PatientFlowDailyBuilder,
    started: datetime,
    blocking_reason: str,
) -> Dict[str, Any]:
    completed = datetime.now()
    return {
        "processing_run_id": builder.processing_run_id,
        "validation_run_id": builder.validation_run_id,
        "input_processing_run_ids": builder.prior_run_ids,
        "source_type": builder.source_type,
        "input_directory": str(builder.input_directory),
        "output_directory": str(builder.output_directory),
        "processing_started_datetime": started.isoformat(),
        "processing_completed_datetime": completed.isoformat(),
        "engine_version": ENGINE_VERSION,
        "transformation_version": TRANSFORMATION_VERSION,
        "configuration_version": ENGINE_VERSION,
        "input_datasets": list(INPUT_DATASETS.keys()),
        "output_dataset": "processed_patient_flow_daily.csv",
        "input_record_counts": builder.input_record_counts,
        "output_record_count": 0,
        "exclusion_count": 0,
        "issue_counts_by_severity": {},
        "warning_count": 0,
        "error_count": 0,
        "run_status": "blocked",
        "processing_allowed_flag": False,
        "input_checksums": builder.input_checksums,
        "output_checksum": "",
        "output_files": [],
        "unresolved_rules": ["Pending Review"],
        "known_limitations": ["Processing blocked by gate."],
        "blocking_reason": blocking_reason,
    }


def _build_success_manifest(
    builder: PatientFlowDailyBuilder,
    started: datetime,
    completed: datetime,
    daily: pd.DataFrame,
    output_file: Path,
    inputs_unchanged: bool,
) -> Dict[str, Any]:
    output_checksum = _file_checksum(output_file)
    issue_counts = {}
    for i in builder.issues:
        issue_counts[i.severity] = issue_counts.get(i.severity, 0) + 1
    return {
        "processing_run_id": builder.processing_run_id,
        "validation_run_id": builder.validation_run_id,
        "input_processing_run_ids": builder.prior_run_ids,
        "source_type": builder.source_type,
        "input_directory": str(builder.input_directory),
        "output_directory": str(builder.output_directory),
        "processing_started_datetime": started.isoformat(),
        "processing_completed_datetime": completed.isoformat(),
        "engine_version": ENGINE_VERSION,
        "transformation_version": TRANSFORMATION_VERSION,
        "configuration_version": ENGINE_VERSION,
        "input_datasets": list(INPUT_DATASETS.keys()),
        "output_dataset": "processed_patient_flow_daily.csv",
        "input_record_counts": builder.input_record_counts,
        "output_record_count": len(daily),
        "exclusion_count": len(builder.exclusion_records),
        "issue_counts_by_severity": issue_counts,
        "warning_count": issue_counts.get("Warning", 0),
        "error_count": issue_counts.get("Error", 0),
        "run_status": "success",
        "processing_allowed_flag": True,
        "input_checksums": builder.input_checksums,
        "output_checksum": output_checksum,
        "output_files": [
            "processed_patient_flow_daily.csv",
            "patient_flow_daily_processing_run_manifest.json",
            "patient_flow_daily_processing_dataset_summary.csv",
            "patient_flow_daily_processing_issue_log.csv",
            "patient_flow_daily_processing_lineage.csv",
            "patient_flow_daily_processing_exclusion_register.csv",
            "patient_flow_daily_processing_audit_log.csv",
        ],
        "unresolved_rules": ["Pending Review"],
        "known_limitations": ["Queue aggregation uses explicit summary flag only."],
        "inputs_unchanged": inputs_unchanged,
    }


def _write_manifest(log_path: Path, manifest: Dict[str, Any]) -> None:
    manifest_path = log_path / "patient_flow_daily_processing_run_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, default=str)


def _file_checksum(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main(
    input_dir: str = "data/processed",
    output_dir: str = "data/processed",
    log_dir: str = "outputs/logs",
    source_type: str = "processed_synthetic_demo",
    collect_lineage: bool = True,
    max_issue_examples: int = 1000,
) -> Dict[str, Any]:
    """Main processing orchestration."""
    started = datetime.now()
    processing_run_id = f"PROC-PFD-{uuid.uuid4().hex[:12].upper()}"
    validation_run_id = "VAL-C62B370EC6C3"  # Accepted validation run from prior steps

    input_path = Path(input_dir)
    output_path = Path(output_dir)
    log_path = Path(log_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    log_path.mkdir(parents=True, exist_ok=True)

    builder = PatientFlowDailyBuilder(
        processing_run_id=processing_run_id,
        validation_run_id=validation_run_id,
        input_directory=input_path,
        output_directory=output_path,
        log_directory=log_path,
        source_type=source_type,
        collect_lineage=collect_lineage,
        max_issue_examples=max_issue_examples,
    )

    # 1. Load schema
    schema = get_processed_schema("processed_patient_flow_daily")
    if schema is None:
        raise ValueError("Schema not found for processed_patient_flow_daily")

    # 2. Check prior manifests (processing gate)
    gate = builder.check_input_manifests()
    if not gate.processing_allowed:
        manifest = _build_blocked_manifest(builder, started, gate.blocking_reason)
        _write_manifest(log_path, manifest)
        print(f"Processing blocked: {gate.blocking_reason}")
        return {"success": False, "blocking_reason": gate.blocking_reason}

    # 3. Load inputs
    try:
        inputs = builder.load_processed_inputs()
    except FileNotFoundError as e:
        manifest = _build_blocked_manifest(builder, started, str(e))
        _write_manifest(log_path, manifest)
        print(f"Processing blocked: {e}")
        return {"success": False, "blocking_reason": str(e)}

    # 4. Verify checksums after load
    if not builder.verify_input_checksums():
        manifest = _build_blocked_manifest(builder, started, "Input checksum mismatch after loading.")
        _write_manifest(log_path, manifest)
        print("Processing blocked: input checksum mismatch")
        return {"success": False, "blocking_reason": "Input checksum mismatch"}

    # 5. Validate input schemas
    input_schema_errors = builder.validate_input_schemas(inputs)
    if input_schema_errors:
        manifest = _build_blocked_manifest(builder, started, f"Input schema failures: {input_schema_errors}")
        _write_manifest(log_path, manifest)
        print("Processing blocked: input schema failures")
        return {"success": False, "blocking_reason": "Input schema failures"}

    # 6. Build daily spine
    spine = builder.build_daily_spine(inputs)

    # 7. Aggregate encounters
    encounters = builder.aggregate_encounters(inputs["processed_patient_encounters"])

    # 8. Aggregate queue
    queue = builder.aggregate_queue(inputs["processed_patient_queue"])

    # 9. Aggregate bed capacity
    bed = builder.aggregate_bed_capacity(inputs["processed_bed_capacity"])

    # 10. Aggregate service schedule
    service = builder.aggregate_service_schedule(inputs["processed_service_schedule"])

    # 11. Combine
    daily = builder.combine_daily_components(spine, encounters, queue, bed, service)

    # 12. Create deterministic IDs
    daily = builder.create_daily_identifier(daily)

    # 13. Validate daily grain uniqueness
    dup_count = daily["patient_flow_daily_id"].duplicated().sum()
    if dup_count > 0:
        builder._add_issue(
            source_dataset_name="",
            processed_dataset_name="processed_patient_flow_daily",
            source_primary_key="",
            source_row_number=0,
            field_name="patient_flow_daily_id",
            issue_type="Duplicate Daily Identifier",
            severity="Critical",
            issue_description=f"{dup_count} duplicate patient_flow_daily_id values found.",
            source_value="",
            exclusion_flag=False,
            blocks_processing=True,
        )
        manifest = _build_blocked_manifest(builder, started, f"Duplicate daily identifiers: {dup_count}")
        _write_manifest(log_path, manifest)
        print(f"Processing blocked: {dup_count} duplicate daily identifiers")
        return {"success": False, "blocking_reason": f"Duplicate daily identifiers: {dup_count}"}
    builder._audit("Daily Grain Validated", f"Unique: {len(daily)} rows")

    # 14. Add metadata
    daily["processing_run_id"] = processing_run_id
    daily["validation_run_id"] = validation_run_id
    daily["transformation_version"] = TRANSFORMATION_VERSION
    daily["processed_datetime"] = datetime.now()

    # Reorder to schema
    all_fields = schema["required_fields"] + schema.get("optional_fields", [])
    for col in all_fields:
        if col not in daily.columns:
            daily[col] = np.nan
    daily = daily[[c for c in all_fields if c in daily.columns]]

    # 15. Validate final schema
    schema_errors = builder.validate_daily_schema(daily)
    if schema_errors:
        manifest = _build_blocked_manifest(builder, started, f"Processed schema failures: {schema_errors}")
        _write_manifest(log_path, manifest)
        print("Processing blocked: processed schema failures")
        return {"success": False, "blocking_reason": "Processed schema failures"}

    # 16. Generate lineage
    lineage_df = builder.build_lineage(inputs, daily)

    # 17. Generate exclusions
    exclusions_df = builder.build_exclusions()

    # 18. Generate issues
    issues_df = builder.collect_issues()

    # 19. Export processed CSV
    output_file = output_path / "processed_patient_flow_daily.csv"
    daily.to_csv(output_file, index=False)
    builder._audit("Output Exported", f"{len(daily)} rows to {output_file.name}")

    # 20. Confirm inputs unchanged
    inputs_unchanged = builder.verify_input_checksums()
    if not inputs_unchanged:
        print("Warning: input files changed during processing")

    # 21. Build and export control outputs
    result = builder.return_build_result(daily)
    completed = datetime.now()

    # Run manifest
    manifest = _build_success_manifest(
        builder=builder,
        started=started,
        completed=completed,
        daily=daily,
        output_file=output_file,
        inputs_unchanged=inputs_unchanged,
    )
    _write_manifest(log_path, manifest)

    # Dataset summary
    summary_df = pd.DataFrame([result["dataset_result"].to_dict()])
    summary_df.to_csv(log_path / "patient_flow_daily_processing_dataset_summary.csv", index=False)

    # Issue log
    issues_df.to_csv(log_path / "patient_flow_daily_processing_issue_log.csv", index=False)

    # Lineage
    lineage_df.to_csv(log_path / "patient_flow_daily_processing_lineage.csv", index=False)

    # Exclusion register
    exclusions_df.to_csv(log_path / "patient_flow_daily_processing_exclusion_register.csv", index=False)

    # Audit log
    audit_df = pd.DataFrame(builder.audit_events)
    audit_df.to_csv(log_path / "patient_flow_daily_processing_audit_log.csv", index=False)

    # Print summary
    print("=" * 60)
    print("Patient Flow Daily Processing Complete (Step 2D-3C)")
    print("=" * 60)
    print(f"Processing run ID: {processing_run_id}")
    print(f"Input counts: encounters={builder.input_record_counts.get('processed_patient_encounters', 0)}, "
          f"queue={builder.input_record_counts.get('processed_patient_queue', 0)}, "
          f"bed={builder.input_record_counts.get('processed_bed_capacity', 0)}, "
          f"schedule={builder.input_record_counts.get('processed_service_schedule', 0)}")
    print(f"Output rows: {len(daily)}")
    print(f"Daily grain unique: {daily['patient_flow_daily_id'].nunique() == len(daily)}")
    print(f"Issues: {len(builder.issues)} (Warnings: {sum(1 for i in builder.issues if i.severity == 'Warning')}, "
          f"Errors: {sum(1 for i in builder.issues if i.severity == 'Error')})")
    print(f"Exclusions: {len(builder.exclusion_records)}")
    print(f"Lineage records: {len(builder.lineage_records)}")
    print(f"Inputs unchanged: {inputs_unchanged}")
    print("=" * 60)

    return {
        "success": True,
        "processing_run_id": processing_run_id,
        "daily_dataframe": daily,
        "builder": builder,
    }


if __name__ == "__main__":
    args = parse_args()
    collect_lineage = args.collect_lineage.lower() in ("true", "1", "yes")
    main(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        log_dir=args.log_dir,
        source_type=args.source_type,
        collect_lineage=collect_lineage,
        max_issue_examples=args.max_issue_examples,
    )
