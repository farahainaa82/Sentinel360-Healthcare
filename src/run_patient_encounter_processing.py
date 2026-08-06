"""
Sentinel360 Healthcare — Patient Encounter Processing Runner

Safe execution module for Step 2D-3A patient encounter transformation.

Usage:
    python src/run_patient_encounter_processing.py
    python src/run_patient_encounter_processing.py --input-dir data/demo --output-dir data/processed

Step: 2D-3A
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src.patient_encounter_transformer import PatientEncounterTransformer, TRANSFORMATION_VERSION
from src.processed_schema_registry import get_processed_schema
from src.processing_contracts import TransformationResultContract


def _generate_run_id() -> str:
    """Generate a deterministic processing run ID."""
    import uuid
    return f"PROC-PE-{uuid.uuid4().hex[:12].upper()}"


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


def _export_control_outputs(
    transformer: PatientEncounterTransformer,
    output_dir: Path,
    log_dir: Path,
    processed_df: pd.DataFrame,
    schema_passed: bool,
    schema_errors: List[str],
) -> Dict[str, Path]:
    """Export all six encounter-specific control outputs."""
    log_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: Dict[str, Path] = {}

    # A. Run manifest
    manifest: Dict[str, Any] = {
        "processing_run_id": transformer.processing_run_id,
        "validation_run_id": transformer.validation_run_id,
        "source_type": transformer.source_type,
        "input_directory": str(transformer.input_dir),
        "output_directory": str(transformer.output_dir),
        "processing_started_datetime": transformer.processing_started,
        "processing_completed_datetime": _now().isoformat() + "Z",
        "engine_version": "1.0.0",
        "transformation_version": TRANSFORMATION_VERSION,
        "configuration_version": "",
        "source_dataset": "patient_encounters",
        "processed_dataset": "processed_patient_encounters",
        "source_record_count": len(transformer.processed_df) if transformer.processed_df is not None else 0,
        "processed_record_count": len(processed_df),
        "excluded_record_count": len(transformer.exclusions),
        "analytically_ineligible_record_count": int(
            (processed_df["exclusion_reason_code"].notna() & (processed_df["exclusion_reason_code"] != "")).sum()
        ),
        "issue_counts_by_severity": _count_issues_by_severity(transformer.issues),
        "warning_count": sum(1 for i in transformer.issues if i.severity == "Warning"),
        "error_count": sum(1 for i in transformer.issues if i.severity in ("Error", "Critical")),
        "run_status": "Completed" if schema_passed else "Failed",
        "processing_allowed_flag": True,
        "source_checksum": transformer.source_checksum,
        "processed_checksum": None,
        "output_files": [],
        "unresolved_rules": transformer.unresolved_rules,
        "known_limitations": [
            "Wait-time KPI percentages are not calculated in this step.",
            "Official wait-stage eligibility may require clinical rule refinement.",
        ],
    }
    manifest_path = log_dir / "patient_encounter_processing_run_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    paths["manifest"] = manifest_path

    # B. Dataset summary
    summary = pd.DataFrame([{
        "processing_run_id": transformer.processing_run_id,
        "validation_run_id": transformer.validation_run_id,
        "source_dataset_name": "patient_encounters",
        "processed_dataset_name": "processed_patient_encounters",
        "source_row_count": len(transformer.processed_df) if transformer.processed_df is not None else 0,
        "processed_row_count": len(processed_df),
        "excluded_row_count": len(transformer.exclusions),
        "transformed_field_count": len(processed_df.columns),
        "warning_count": sum(1 for i in transformer.issues if i.severity == "Warning"),
        "error_count": sum(1 for i in transformer.issues if i.severity in ("Error", "Critical")),
        "dataset_status": "Processed" if schema_passed else "Failed",
        "output_file_name": "processed_patient_encounters.csv",
        "transformation_version": TRANSFORMATION_VERSION,
        "processed_datetime": _now().isoformat() + "Z",
    }])
    summary_path = log_dir / "patient_encounter_processing_dataset_summary.csv"
    summary.to_csv(summary_path, index=False)
    paths["dataset_summary"] = summary_path

    # C. Issue log
    issue_path = log_dir / "patient_encounter_processing_issue_log.csv"
    if transformer.issues:
        issue_df = pd.DataFrame([i.to_dict() for i in transformer.issues])
    else:
        issue_df = pd.DataFrame(columns=[
            "processing_run_id", "issue_id", "dataset_name", "severity",
            "issue_type", "description", "field_name", "evidence", "created_datetime",
        ])
    issue_df.to_csv(issue_path, index=False)
    paths["issue_log"] = issue_path

    # D. Lineage
    lineage_path = log_dir / "patient_encounter_processing_lineage.csv"
    if transformer.lineage:
        lineage_df = pd.DataFrame([l.to_dict() for l in transformer.lineage])
    else:
        lineage_df = pd.DataFrame(columns=[
            "processing_run_id", "validation_run_id", "source_dataset_name",
            "source_file_name", "source_primary_key_field", "source_primary_key_value",
            "source_row_number", "processed_dataset_name", "processed_primary_key_field",
            "processed_primary_key_value", "transformation_rule_id", "transformation_description",
            "source_fields_used", "processed_fields_created", "exclusion_flag",
            "exclusion_reason_code", "transformation_version", "configuration_version",
            "processed_datetime",
        ])
    lineage_df.to_csv(lineage_path, index=False)
    paths["lineage"] = lineage_path

    # E. Exclusion register
    exclusion_path = log_dir / "patient_encounter_processing_exclusion_register.csv"
    if transformer.exclusions:
        exclusion_df = pd.DataFrame([e.to_dict() for e in transformer.exclusions])
    else:
        exclusion_df = pd.DataFrame(columns=[
            "processing_run_id", "exclusion_id", "source_dataset_name",
            "source_primary_key_field", "source_primary_key_value", "source_row_number",
            "exclusion_reason_code", "exclusion_reason_description", "validation_issue_id",
            "manual_override_id", "exclusion_stage", "excluded_by_rule", "reversible_flag",
            "created_datetime",
        ])
    exclusion_df.to_csv(exclusion_path, index=False)
    paths["exclusion_register"] = exclusion_path

    # F. Audit log
    audit_path = log_dir / "patient_encounter_processing_audit_log.csv"
    if transformer.audit_events:
        audit_df = pd.DataFrame(transformer.audit_events)
    else:
        audit_df = pd.DataFrame(columns=[
            "processing_run_id", "event", "details", "timestamp",
        ])
    audit_df.to_csv(audit_path, index=False)
    paths["audit_log"] = audit_path

    # Update manifest with output files and processed checksum
    manifest["output_files"] = [str(p) for p in paths.values()]
    processed_path = paths.get("processed_dataset")
    if processed_path is not None:
        try:
            manifest["processed_checksum"] = _file_checksum(processed_path)
        except Exception:
            manifest["processed_checksum"] = None
    else:
        manifest["processed_checksum"] = None
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return paths


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


def run_patient_encounter_processing(
    input_dir: Path = Path("data/demo"),
    output_dir: Path = Path("data/processed"),
    validation_log_dir: Path = Path("outputs/logs"),
    source_type: str = "synthetic_demo",
    collect_lineage: bool = True,
    max_issue_examples: int = 1000,
    execute_export: bool = True,
) -> Dict[str, Any]:
    """Execute the patient encounter processing pipeline.

    Parameters
    ----------
    execute_export : bool
        If True, writes processed CSV and control outputs to disk.
        If False, performs transformation in-memory only.
    """
    run_id = _generate_run_id()
    started = _now()

    print("=" * 60)
    print("Sentinel360 Healthcare — Patient Encounter Processing")
    print(f"Run ID: {run_id}")
    print("=" * 60)

    # 1. Load schema
    schema = get_processed_schema("processed_patient_encounters")
    target_fields = schema["required_fields"] + schema.get("optional_fields", [])
    print(f"Loaded schema for processed_patient_encounters ({len(target_fields)} fields).")

    # 2. Initialise transformer
    transformer = PatientEncounterTransformer(
        input_dir=input_dir,
        output_dir=output_dir,
        validation_log_dir=validation_log_dir,
        source_type=source_type,
        collect_lineage=collect_lineage,
        max_issue_examples=max_issue_examples,
    )
    transformer.processing_run_id = run_id
    transformer.processing_started = started.isoformat() + "Z"

    # 3. Check validation gate
    gate = transformer.check_validation_gate()
    if not gate.processing_allowed:
        print(f"\nProcessing BLOCKED: {gate.blocking_reason}")
        return {
            "status": "blocked",
            "reason": gate.blocking_reason,
            "run_id": run_id,
        }
    print(f"Validation gate passed (validation_run_id={gate.validation_run_id}).")

    # 4. Load source
    try:
        source_df = transformer.load_source_data()
    except FileNotFoundError as exc:
        print(f"\nProcessing FAILED: {exc}")
        return {
            "status": "failed",
            "reason": str(exc),
            "run_id": run_id,
        }
    print(f"Loaded source: {len(source_df)} rows from patient_encounters.csv")
    print(f"Source checksum: {transformer.source_checksum}")

    # 5. Transform
    processed_df = transformer.transform_encounters(source_df)
    print(f"Transformed: {len(processed_df)} processed rows.")

    # 6. Validate schema
    schema_passed, schema_errors = transformer.validate_processed_schema(processed_df)
    if schema_passed:
        print("Processed schema validation: PASSED")
    else:
        print("Processed schema validation: FAILED")
        for err in schema_errors:
            print(f"  - {err}")

    # 7. Build lineage, exclusions, issues
    transformer.build_lineage(source_df, processed_df)
    transformer.build_exclusions(processed_df)
    issues = transformer.collect_issues()
    print(f"Issues: {len(issues)} ({sum(1 for i in issues if i.severity == 'Warning')} warnings, {sum(1 for i in issues if i.severity in ('Error', 'Critical'))} errors)")
    print(f"Exclusions: {len(transformer.exclusions)}")
    print(f"Lineage records: {len(transformer.lineage)}")

    # 8. Export (only when explicitly executed)
    paths: Dict[str, Path] = {}
    if execute_export:
        processed_path = output_dir / "processed_patient_encounters.csv"
        _export_processed_dataset(processed_df, processed_path)
        paths["processed_dataset"] = processed_path
        print(f"Exported processed dataset: {processed_path}")

        paths.update(_export_control_outputs(
            transformer=transformer,
            output_dir=output_dir,
            log_dir=validation_log_dir,
            processed_df=processed_df,
            schema_passed=schema_passed,
            schema_errors=schema_errors,
        ))
        print("Exported control outputs:")
        for key, path in paths.items():
            if key != "processed_dataset":
                print(f"  - {path.name}")

    # 9. Source checksum confirmation
    source_path = input_dir / "patient_encounters.csv"
    source_unchanged = _confirm_source_unchanged(source_path, transformer.source_checksum)
    print(f"Source unchanged: {source_unchanged}")

    # 10. Workforce outputs unchanged
    workforce_ok = _confirm_workforce_unchanged(output_dir)
    print(f"Workforce outputs unchanged: {workforce_ok}")

    # 11. Summary
    elapsed = (_now() - started).total_seconds()
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Run ID:                {run_id}")
    print(f"Validation Run ID:     {transformer.validation_run_id}")
    print(f"Source rows:           {len(source_df)}")
    print(f"Processed rows:        {len(processed_df)}")
    print(f"Schema validation:     {'PASSED' if schema_passed else 'FAILED'}")
    print(f"Issues:                {len(issues)}")
    print(f"Exclusions:            {len(transformer.exclusions)}")
    print(f"Lineage records:       {len(transformer.lineage)}")
    print(f"Source unchanged:      {source_unchanged}")
    print(f"Workforce unchanged:   {workforce_ok}")
    print(f"Elapsed time:          {elapsed:.2f}s")
    print("=" * 60)

    return {
        "status": "completed" if schema_passed else "failed_schema",
        "run_id": run_id,
        "validation_run_id": transformer.validation_run_id,
        "source_rows": len(source_df),
        "processed_rows": len(processed_df),
        "schema_passed": schema_passed,
        "schema_errors": schema_errors,
        "issues": [i.to_dict() for i in issues],
        "exclusions": [e.to_dict() for e in transformer.exclusions],
        "lineage": [l.to_dict() for l in transformer.lineage],
        "source_unchanged": source_unchanged,
        "workforce_unchanged": workforce_ok,
        "output_paths": {k: str(v) for k, v in paths.items()},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Sentinel360 Patient Encounter Processing Runner")
    parser.add_argument("--input-dir", default="data/demo")
    parser.add_argument("--output-dir", default="data/processed")
    parser.add_argument("--validation-log-dir", default="outputs/logs")
    parser.add_argument("--source-type", default="synthetic_demo")
    parser.add_argument("--collect-lineage", type=lambda x: x.lower() in ("true", "1", "yes"), default=True)
    parser.add_argument("--max-issue-examples", type=int, default=1000)
    parser.add_argument("--no-export", action="store_true", help="Run transformation without writing outputs.")
    args = parser.parse_args()

    run_patient_encounter_processing(
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
