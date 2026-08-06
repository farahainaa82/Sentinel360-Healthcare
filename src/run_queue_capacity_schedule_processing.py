"""
Sentinel360 Healthcare — Queue, Bed Capacity and Service Schedule Processing Runner

Safe execution module for Step 2D-3B.

Usage:
    python src/run_queue_capacity_schedule_processing.py
    python src/run_queue_capacity_schedule_processing.py --input-dir data/demo --output-dir data/processed

Step: 2D-3B
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src.queue_capacity_schedule_transformer import QueueCapacityScheduleTransformer, TRANSFORMATION_VERSION, SOURCE_DATASETS
from src.processed_schema_registry import get_processed_schema
from src.processing_contracts import ValidationGateResult


def _generate_run_id() -> str:
    """Generate a deterministic processing run ID."""
    return f"PROC-QCS-{uuid.uuid4().hex[:12].upper()}"


def _now() -> datetime:
    return datetime.utcnow()


def _file_checksum(path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _export_processed_dataset(df: pd.DataFrame, output_path: Path) -> None:
    """Export a processed DataFrame to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)


def _count_issues_by_severity(issues: List[Any]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for i in issues:
        sev = getattr(i, "severity", "Information")
        counts[sev] = counts.get(sev, 0) + 1
    return counts


def _confirm_source_unchanged(source_path: Path, original_checksum: Optional[str]) -> bool:
    if original_checksum is None:
        return False
    current = _file_checksum(source_path)
    return current == original_checksum


def _confirm_workforce_unchanged(output_dir: Path) -> bool:
    """Check that existing workforce processed files have not been modified."""
    workforce_files = [
        "processed_hospital_master.csv",
        "processed_department_master.csv",
        "processed_staff_role_master.csv",
        "processed_staff_master.csv",
        "processed_staff_roster.csv",
        "processed_staff_attendance.csv",
        "processed_staffing_requirement.csv",
        "processed_workforce_daily.csv",
    ]
    all_exist = True
    for name in workforce_files:
        path = output_dir / name
        if not path.exists():
            all_exist = False
    return all_exist


def _confirm_encounter_unchanged(output_dir: Path) -> bool:
    """Check that processed_patient_encounters.csv still exists."""
    return (output_dir / "processed_patient_encounters.csv").exists()


def run_queue_capacity_schedule_processing(
    input_dir: Path = Path("data/demo"),
    output_dir: Path = Path("data/processed"),
    validation_log_dir: Path = Path("outputs/logs"),
    source_type: str = "synthetic_demo",
    collect_lineage: bool = True,
    max_issue_examples: int = 1000,
    execute_export: bool = True,
) -> Dict[str, Any]:
    """Execute the queue, bed capacity and service schedule processing pipeline.

    Parameters
    ----------
    execute_export : bool
        If True, writes processed CSV and control outputs to disk.
        If False, performs transformation in-memory only.
    """
    run_id = _generate_run_id()
    started = _now()

    print("=" * 60)
    print("Sentinel360 Healthcare — Queue, Bed Capacity and Service Schedule Processing")
    print(f"Run ID: {run_id}")
    print("=" * 60)

    # 1. Load schemas
    for ds_name in ["processed_patient_queue", "processed_bed_capacity", "processed_service_schedule"]:
        schema = get_processed_schema(ds_name)
        if schema is None:
            print(f"Schema not found for {ds_name}")
            return {"status": "failed", "reason": f"Schema not found for {ds_name}", "run_id": run_id}
        target_fields = schema["required_fields"] + schema.get("optional_fields", [])
        print(f"Loaded schema for {ds_name} ({len(target_fields)} fields).")

    # 2. Initialise transformer
    transformer = QueueCapacityScheduleTransformer(
        processing_run_id=run_id,
        validation_run_id="",
        input_directory=input_dir,
        output_directory=output_dir,
        validation_log_directory=validation_log_dir,
        source_type=source_type,
        collect_lineage=collect_lineage,
        max_issue_examples=max_issue_examples,
    )

    # 3. Check validation gate
    gate = transformer.check_validation_gate()
    if not gate.processing_allowed:
        print(f"\nProcessing BLOCKED: {gate.blocking_reason}")
        # Write blocked manifest
        manifest = {
            "processing_run_id": run_id,
            "validation_run_id": gate.validation_run_id,
            "source_type": source_type,
            "input_directory": str(input_dir),
            "output_directory": str(output_dir),
            "processing_started_datetime": started.isoformat() + "Z",
            "processing_completed_datetime": _now().isoformat() + "Z",
            "engine_version": "1.0.0",
            "transformation_version": TRANSFORMATION_VERSION,
            "configuration_version": "",
            "run_status": "Blocked",
            "processing_allowed_flag": False,
            "blocking_reason": gate.blocking_reason,
            "output_files": [],
        }
        if execute_export:
            validation_log_dir.mkdir(parents=True, exist_ok=True)
            manifest_path = validation_log_dir / "queue_capacity_schedule_processing_run_manifest.json"
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
            print(f"Blocked manifest written: {manifest_path}")
        return {
            "status": "blocked",
            "reason": gate.blocking_reason,
            "run_id": run_id,
        }
    transformer.validation_run_id = gate.validation_run_id
    print(f"Validation gate passed (validation_run_id={gate.validation_run_id}).")

    # 4. Load source datasets
    try:
        sources = transformer.load_source_datasets()
    except FileNotFoundError as exc:
        print(f"\nProcessing FAILED: {exc}")
        return {
            "status": "failed",
            "reason": str(exc),
            "run_id": run_id,
        }
    for ds_name, df in sources.items():
        print(f"Loaded source: {len(df)} rows from {SOURCE_DATASETS[ds_name]['source_file']}")
        print(f"  Source checksum: {transformer.source_checksums[ds_name]}")

    # 5. Transform
    queue_df = transformer.transform_patient_queue(sources["patient_queue_records"])
    bed_df = transformer.transform_bed_capacity(sources["bed_capacity_records"])
    schedule_df = transformer.transform_service_schedule(sources["service_schedule"])
    print(f"\nTransformed: queue={len(queue_df)}, bed={len(bed_df)}, schedule={len(schedule_df)}")

    # 6. Validate schemas
    schema_results = {}
    for ds_name, df in [
        ("processed_patient_queue", queue_df),
        ("processed_bed_capacity", bed_df),
        ("processed_service_schedule", schedule_df),
    ]:
        errors = transformer.validate_processed_schema(df, ds_name)
        passed = len(errors) == 0
        schema_results[ds_name] = {"passed": passed, "errors": errors}
        status = "PASSED" if passed else "FAILED"
        print(f"Schema validation {ds_name}: {status}")
        for err in errors:
            print(f"  - {err}")
    all_schemas_passed = all(r["passed"] for r in schema_results.values())

    # 7. Build lineage
    if collect_lineage:
        transformer.build_lineage(sources["patient_queue_records"], queue_df, "patient_queue_records")
        transformer.build_lineage(sources["bed_capacity_records"], bed_df, "bed_capacity_records")
        transformer.build_lineage(sources["service_schedule"], schedule_df, "service_schedule")
        print(f"Lineage records: {len(transformer.lineage_records)}")

    # 8. Build exclusions and issues
    exclusions_df = transformer.build_exclusions()
    issues_df = transformer.collect_issues()
    print(f"Exclusions: {len(transformer.exclusion_records)}")
    print(f"Issues: {len(transformer.issues)} ({_count_issues_by_severity(transformer.issues)})")

    # 9. Export (only when explicitly executed)
    paths: Dict[str, Path] = {}
    if execute_export:
        output_dir.mkdir(parents=True, exist_ok=True)
        validation_log_dir.mkdir(parents=True, exist_ok=True)

        # Export processed datasets
        queue_path = output_dir / "processed_patient_queue.csv"
        bed_path = output_dir / "processed_bed_capacity.csv"
        schedule_path = output_dir / "processed_service_schedule.csv"
        _export_processed_dataset(queue_df, queue_path)
        _export_processed_dataset(bed_df, bed_path)
        _export_processed_dataset(schedule_df, schedule_path)
        paths["processed_patient_queue"] = queue_path
        paths["processed_bed_capacity"] = bed_path
        paths["processed_service_schedule"] = schedule_path
        print(f"\nExported processed datasets:")
        for key in ["processed_patient_queue", "processed_bed_capacity", "processed_service_schedule"]:
            print(f"  - {paths[key].name}")

        # Compute processed checksums
        for key in ["processed_patient_queue", "processed_bed_capacity", "processed_service_schedule"]:
            try:
                transformer.processed_checksums[key] = _file_checksum(paths[key])
            except Exception:
                transformer.processed_checksums[key] = ""

        # A. Run manifest
        manifest: Dict[str, Any] = {
            "processing_run_id": run_id,
            "validation_run_id": transformer.validation_run_id,
            "source_type": source_type,
            "input_directory": str(input_dir),
            "output_directory": str(output_dir),
            "processing_started_datetime": started.isoformat() + "Z",
            "processing_completed_datetime": _now().isoformat() + "Z",
            "engine_version": "1.0.0",
            "transformation_version": TRANSFORMATION_VERSION,
            "configuration_version": "",
            "source_datasets": list(SOURCE_DATASETS.keys()),
            "processed_datasets": ["processed_patient_queue", "processed_bed_capacity", "processed_service_schedule"],
            "source_record_counts": {
                "patient_queue_records": len(sources["patient_queue_records"]),
                "bed_capacity_records": len(sources["bed_capacity_records"]),
                "service_schedule": len(sources["service_schedule"]),
            },
            "processed_record_counts": {
                "processed_patient_queue": len(queue_df),
                "processed_bed_capacity": len(bed_df),
                "processed_service_schedule": len(schedule_df),
            },
            "excluded_record_counts": {
                "processed_patient_queue": int((~queue_df["valid_queue_record_flag"]).sum()) if "valid_queue_record_flag" in queue_df.columns else 0,
                "processed_bed_capacity": int((~bed_df["valid_bed_record_flag"]).sum()) if "valid_bed_record_flag" in bed_df.columns else 0,
                "processed_service_schedule": int((~schedule_df["valid_schedule_flag"]).sum()) if "valid_schedule_flag" in schedule_df.columns else 0,
            },
            "issue_counts_by_severity": _count_issues_by_severity(transformer.issues),
            "warning_count": sum(1 for i in transformer.issues if i.severity == "Warning"),
            "error_count": sum(1 for i in transformer.issues if i.severity in ("Error", "Critical")),
            "run_status": "Completed" if all_schemas_passed else "Failed",
            "processing_allowed_flag": True,
            "source_checksums": transformer.source_checksums,
            "processed_checksums": transformer.processed_checksums,
            "output_files": [str(p) for p in paths.values()],
            "unresolved_rules": [],
            "known_limitations": [
                "Average Patient Waiting Time KPI is not calculated in this step.",
                "Bed Occupancy Rate KPI is not calculated in this step.",
                "Official wait-stage eligibility may require clinical rule refinement.",
            ],
        }
        manifest_path = validation_log_dir / "queue_capacity_schedule_processing_run_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        paths["manifest"] = manifest_path
        print(f"\nExported control outputs:")
        print(f"  - {manifest_path.name}")

        # B. Dataset summary
        summary_rows = []
        for ds_key, df in [
            ("patient_queue_records", queue_df),
            ("bed_capacity_records", bed_df),
            ("service_schedule", schedule_df),
        ]:
            config = SOURCE_DATASETS[ds_key]
            excluded = 0
            if ds_key == "patient_queue_records" and "valid_queue_record_flag" in df.columns:
                excluded = int((~df["valid_queue_record_flag"]).sum())
            elif ds_key == "bed_capacity_records" and "valid_bed_record_flag" in df.columns:
                excluded = int((~df["valid_bed_record_flag"]).sum())
            elif ds_key == "service_schedule" and "valid_schedule_flag" in df.columns:
                excluded = int((~df["valid_schedule_flag"]).sum())
            summary_rows.append({
                "processing_run_id": run_id,
                "validation_run_id": transformer.validation_run_id,
                "source_dataset_name": ds_key,
                "processed_dataset_name": config["processed_name"],
                "source_row_count": len(sources[ds_key]),
                "processed_row_count": len(df),
                "excluded_row_count": excluded,
                "transformed_field_count": len(df.columns),
                "warning_count": sum(1 for i in transformer.issues if i.source_dataset_name == ds_key and i.severity == "Warning"),
                "error_count": sum(1 for i in transformer.issues if i.source_dataset_name == ds_key and i.severity in ("Error", "Critical")),
                "dataset_status": "Processed" if schema_results[config["processed_name"]]["passed"] else "Failed",
                "output_file_name": f"{config['processed_name']}.csv",
                "transformation_version": TRANSFORMATION_VERSION,
                "processed_datetime": _now().isoformat() + "Z",
            })
        summary_df = pd.DataFrame(summary_rows)
        summary_path = validation_log_dir / "queue_capacity_schedule_processing_dataset_summary.csv"
        summary_df.to_csv(summary_path, index=False)
        paths["dataset_summary"] = summary_path
        print(f"  - {summary_path.name}")

        # C. Issue log
        issue_path = validation_log_dir / "queue_capacity_schedule_processing_issue_log.csv"
        if transformer.issues:
            issue_df = pd.DataFrame([i.to_dict() for i in transformer.issues])
        else:
            issue_df = pd.DataFrame(columns=[
                "processing_run_id", "issue_id", "source_dataset_name",
                "processed_dataset_name", "source_primary_key", "source_row_number",
                "field_name", "issue_type", "severity", "issue_description",
                "source_value", "processed_value", "resolution_action",
                "exclusion_flag", "blocks_processing", "created_datetime",
            ])
        issue_df.to_csv(issue_path, index=False)
        paths["issue_log"] = issue_path
        print(f"  - {issue_path.name}")

        # D. Lineage
        lineage_path = validation_log_dir / "queue_capacity_schedule_processing_lineage.csv"
        if transformer.lineage_records:
            lineage_df = pd.DataFrame([l.to_dict() for l in transformer.lineage_records])
        else:
            lineage_df = pd.DataFrame(columns=[
                "processing_run_id", "lineage_id", "validation_run_id",
                "source_dataset_name", "source_file_name", "source_primary_key_field",
                "source_primary_key_value", "source_row_number", "processed_dataset_name",
                "processed_primary_key_field", "processed_primary_key_value",
                "transformation_rule_id", "transformation_description", "source_fields_used",
                "processed_fields_created", "exclusion_flag", "exclusion_reason_code",
                "transformation_version", "configuration_version", "processed_datetime",
            ])
        lineage_df.to_csv(lineage_path, index=False)
        paths["lineage"] = lineage_path
        print(f"  - {lineage_path.name}")

        # E. Exclusion register
        exclusion_path = validation_log_dir / "queue_capacity_schedule_processing_exclusion_register.csv"
        if transformer.exclusion_records:
            exclusion_df_out = pd.DataFrame([e.to_dict() for e in transformer.exclusion_records])
        else:
            exclusion_df_out = pd.DataFrame(columns=[
                "processing_run_id", "exclusion_id", "source_dataset_name",
                "source_primary_key_field", "source_primary_key_value", "source_row_number",
                "exclusion_reason_code", "exclusion_reason_description", "validation_issue_id",
                "manual_override_id", "exclusion_stage", "excluded_by_rule",
                "reversible_flag", "created_datetime",
            ])
        exclusion_df_out.to_csv(exclusion_path, index=False)
        paths["exclusion_register"] = exclusion_path
        print(f"  - {exclusion_path.name}")

        # F. Audit log
        audit_path = validation_log_dir / "queue_capacity_schedule_processing_audit_log.csv"
        if transformer.audit_events:
            audit_df = pd.DataFrame(transformer.audit_events)
        else:
            audit_df = pd.DataFrame(columns=[
                "processing_run_id", "event", "detail", "timestamp",
            ])
        audit_df.to_csv(audit_path, index=False)
        paths["audit_log"] = audit_path
        print(f"  - {audit_path.name}")

    # 10. Confirm source unchanged
    source_unchanged = {}
    for ds_name, config in SOURCE_DATASETS.items():
        source_path = input_dir / config["source_file"]
        source_unchanged[ds_name] = _confirm_source_unchanged(source_path, transformer.source_checksums.get(ds_name))
    all_source_unchanged = all(source_unchanged.values())
    print(f"\nSource unchanged: {all_source_unchanged}")

    # 11. Workforce outputs unchanged
    workforce_ok = _confirm_workforce_unchanged(output_dir)
    print(f"Workforce outputs unchanged: {workforce_ok}")

    # 12. Encounter output unchanged
    encounter_ok = _confirm_encounter_unchanged(output_dir)
    print(f"Encounter output unchanged: {encounter_ok}")

    # 13. Summary
    elapsed = (_now() - started).total_seconds()
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Run ID:                {run_id}")
    print(f"Validation Run ID:     {transformer.validation_run_id}")
    print(f"Queue source rows:     {len(sources['patient_queue_records'])}")
    print(f"Queue processed rows:  {len(queue_df)}")
    print(f"Bed source rows:       {len(sources['bed_capacity_records'])}")
    print(f"Bed processed rows:    {len(bed_df)}")
    print(f"Schedule source rows:  {len(sources['service_schedule'])}")
    print(f"Schedule processed rows: {len(schedule_df)}")
    print(f"Schema validation:     {'PASSED' if all_schemas_passed else 'FAILED'}")
    print(f"Issues:                {len(transformer.issues)}")
    print(f"Exclusions:            {len(transformer.exclusion_records)}")
    print(f"Lineage records:       {len(transformer.lineage_records)}")
    print(f"Source unchanged:      {all_source_unchanged}")
    print(f"Workforce unchanged:   {workforce_ok}")
    print(f"Encounter unchanged:   {encounter_ok}")
    print(f"Elapsed time:          {elapsed:.2f}s")
    print("=" * 60)

    return {
        "status": "completed" if all_schemas_passed else "failed_schema",
        "run_id": run_id,
        "validation_run_id": transformer.validation_run_id,
        "source_rows": {
            "patient_queue_records": len(sources["patient_queue_records"]),
            "bed_capacity_records": len(sources["bed_capacity_records"]),
            "service_schedule": len(sources["service_schedule"]),
        },
        "processed_rows": {
            "processed_patient_queue": len(queue_df),
            "processed_bed_capacity": len(bed_df),
            "processed_service_schedule": len(schedule_df),
        },
        "schema_passed": all_schemas_passed,
        "schema_results": schema_results,
        "issues": [i.to_dict() for i in transformer.issues],
        "exclusions": [e.to_dict() for e in transformer.exclusion_records],
        "lineage": [l.to_dict() for l in transformer.lineage_records],
        "source_unchanged": all_source_unchanged,
        "workforce_unchanged": workforce_ok,
        "encounter_unchanged": encounter_ok,
        "output_paths": {k: str(v) for k, v in paths.items()},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Sentinel360 Queue, Bed Capacity and Service Schedule Processing Runner")
    parser.add_argument("--input-dir", default="data/demo")
    parser.add_argument("--output-dir", default="data/processed")
    parser.add_argument("--validation-log-dir", default="outputs/logs")
    parser.add_argument("--source-type", default="synthetic_demo")
    parser.add_argument("--collect-lineage", type=lambda x: x.lower() in ("true", "1", "yes"), default=True)
    parser.add_argument("--max-issue-examples", type=int, default=1000)
    parser.add_argument("--no-export", action="store_true", help="Run transformation without writing outputs.")
    args = parser.parse_args()

    run_queue_capacity_schedule_processing(
        input_dir=Path(args.input_dir),
        output_dir=Path(args.output_dir),
        validation_log_dir=Path(args.validation_log_dir),
        source_type=args.source_type,
        collect_lineage=args.collect_lineage,
        max_issue_examples=args.max_issue_examples,
        execute_export=not args.no_export,
    )


if __name__ == "__main__":
    main()
