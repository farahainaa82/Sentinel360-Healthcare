"""
Sentinel360 Healthcare — Validation Runner

Safe execution module for the data-validation engine.
Does not execute automatically when imported.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from src.data_validation_engine import DataValidationEngine, ENGINE_VERSION, CONFIG_VERSION
from src.validation_models import (
    DatasetValidationResult,
    ManualOverrideRecord,
    RecordValidationIssue,
    RelationshipValidationResult,
    ValidationAuditEvent,
    ValidationIssue,
    ValidationRun,
)
from src import validation_config_loader as vcl


def parse_args(argv: List[str] = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Sentinel360 Healthcare Data Validation Runner"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/demo",
        help="Input directory containing source CSV files (default: data/demo)",
    )
    parser.add_argument(
        "--source-type",
        type=str,
        default="synthetic_demo",
        help="Source type descriptor (default: synthetic_demo)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs/logs",
        help="Output directory for validation logs (default: outputs/logs)",
    )
    parser.add_argument(
        "--collect-record-issues",
        type=lambda x: x.lower() in ("true", "1", "yes"),
        default=True,
        help="Collect representative record-level issues (default: true)",
    )
    parser.add_argument(
        "--max-record-examples",
        type=int,
        default=100,
        help="Maximum record-level examples per issue type per dataset (default: 100). This is a technical display limit, not a business threshold.",
    )
    return parser.parse_args(argv)


def export_validation_outputs(result: Any, output_dir: Path) -> Dict[str, Path]:
    """Export all validation outputs to the specified directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    files: Dict[str, Path] = {}

    manifest_path = output_dir / "validation_run_manifest.json"

    # 2. dataset_validation_summary.csv
    ds_rows = [r.to_dict() for r in result.dataset_results.values()]
    ds_df = pd.DataFrame(ds_rows)
    if ds_df.empty:
        ds_df = pd.DataFrame(columns=DatasetValidationResult.__dataclass_fields__.keys())
    ds_path = output_dir / "dataset_validation_summary.csv"
    ds_df.to_csv(ds_path, index=False)
    files["dataset_validation_summary.csv"] = ds_path

    # 3. validation_issue_log.csv
    issue_rows = [i.to_dict() for i in result.issues]
    issue_df = pd.DataFrame(issue_rows)
    if issue_df.empty:
        issue_df = pd.DataFrame(columns=ValidationIssue.__dataclass_fields__.keys())
    issue_path = output_dir / "validation_issue_log.csv"
    issue_df.to_csv(issue_path, index=False)
    files["validation_issue_log.csv"] = issue_path

    # 4. record_validation_issue_log.csv
    rec_rows = [r.to_dict() for r in result.record_issues]
    rec_df = pd.DataFrame(rec_rows)
    if rec_df.empty:
        rec_df = pd.DataFrame(columns=RecordValidationIssue.__dataclass_fields__.keys())
    rec_path = output_dir / "record_validation_issue_log.csv"
    rec_df.to_csv(rec_path, index=False)
    files["record_validation_issue_log.csv"] = rec_path

    # 5. relationship_validation_summary.csv
    rel_rows = [r.to_dict() for r in result.relationship_results]
    rel_df = pd.DataFrame(rel_rows)
    if rel_df.empty:
        rel_df = pd.DataFrame(columns=RelationshipValidationResult.__dataclass_fields__.keys())
    rel_path = output_dir / "relationship_validation_summary.csv"
    rel_df.to_csv(rel_path, index=False)
    files["relationship_validation_summary.csv"] = rel_path

    # 6. manual_override_register.csv
    override_rows = [o.to_dict() for o in result.manual_overrides]
    override_df = pd.DataFrame(override_rows)
    if override_df.empty:
        override_df = pd.DataFrame(columns=ManualOverrideRecord.__dataclass_fields__.keys())
    override_path = output_dir / "manual_override_register.csv"
    override_df.to_csv(override_path, index=False)
    files["manual_override_register.csv"] = override_path

    # 7. validation_audit_log.csv
    audit_rows = [a.to_dict() for a in result.audit_events]
    audit_df = pd.DataFrame(audit_rows)
    if audit_df.empty:
        audit_df = pd.DataFrame(columns=ValidationAuditEvent.__dataclass_fields__.keys())
    audit_path = output_dir / "validation_audit_log.csv"
    audit_df.to_csv(audit_path, index=False)
    files["validation_audit_log.csv"] = audit_path

    # Write manifest last so output_file_names is complete
    manifest = {
        "validation_run_id": result.validation_run.validation_run_id,
        "source_type": result.validation_run.source_type,
        "input_directory": result.validation_run.input_directory,
        "validation_started_datetime": result.validation_run.validation_started_datetime.isoformat(),
        "validation_completed_datetime": result.validation_run.validation_completed_datetime.isoformat() if result.validation_run.validation_completed_datetime else None,
        "engine_version": result.validation_run.validation_engine_version,
        "configuration_version": result.validation_run.configuration_version,
        "expected_dataset_count": result.validation_run.dataset_count_expected,
        "discovered_dataset_count": result.validation_run.dataset_count_found,
        "validated_dataset_count": len(result.dataset_results),
        "run_status": result.validation_run.run_status,
        "processing_allowed_flag": result.validation_run.run_status in ("Passed", "Passed with Warnings"),
        "issue_counts_by_severity": {
            "Information": result.validation_run.information_issue_count,
            "Warning": result.validation_run.warning_issue_count,
            "Error": result.validation_run.error_issue_count,
            "Critical": result.validation_run.critical_issue_count,
        },
        "issue_counts_by_outcome": {
            "Observed": len([i for i in result.issues if i.issue_outcome == "Observed"]),
            "Passed": len([i for i in result.issues if i.issue_outcome == "Passed"]),
            "Failed": len([i for i in result.issues if i.issue_outcome == "Failed"]),
        },
        "blocking_issue_count": result.validation_run.blocking_issue_count,
        "manual_override_count": result.validation_run.manual_override_count,
        "output_file_names": list(files.keys()),
        "source_file_checksums": result.source_checksums,
        "known_limitations": [
            "Validation does not prove business meaning of source records.",
            "Manual overrides require explicit approval workflow outside this engine.",
            "Record-level examples are limited by technical display limit.",
        ],
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    files["validation_run_manifest.json"] = manifest_path

    return files


def print_summary(result: Any) -> None:
    """Print a concise English completion summary."""
    run = result.validation_run
    print("=" * 60)
    print("Sentinel360 Healthcare — Data Validation Complete")
    print("=" * 60)
    print(f"Run ID:        {run.validation_run_id}")
    print(f"Status:        {run.run_status}")
    print(f"Input:         {run.input_directory}")
    print(f"Datasets:      {run.dataset_count_found} found / {run.dataset_count_expected} expected")
    print(f"Blocking:      {run.blocking_issue_count}")
    print(f"Critical:      {run.critical_issue_count}")
    print(f"Error:         {run.error_issue_count}")
    print(f"Warning:       {run.warning_issue_count}")
    print(f"Information:   {run.information_issue_count}")
    print("-" * 60)
    print("Dataset Statuses:")
    for ds_name, ds_result in result.dataset_results.items():
        flag = "OK" if ds_result.processing_allowed_flag else "BLOCK"
        print(f"  {ds_name:30s} {ds_result.dataset_status:20s} [{flag}]")
    print("-" * 60)
    print("Relationship Results:")
    for rel in result.relationship_results:
        status = rel.relationship_status
        blocks = "BLOCKS" if rel.blocks_processing else "OK"
        print(f"  {rel.child_dataset}.{rel.child_field} -> {rel.parent_dataset}.{rel.parent_field}: {status} [{blocks}]")
    print("=" * 60)


def main(argv: List[str] = None) -> int:
    """Main entry point for the validation runner."""
    args = parse_args(argv)
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    # Load registries
    schema_registry = vcl.load_dataset_schema_registry()
    relationship_registry = vcl.load_relationship_registry()
    validation_rules = vcl.load_validation_rule_registry()

    # Validate registry integrity
    ok, messages = vcl.validate_registry_integrity()
    if not ok:
        print("Registry integrity errors:")
        for m in messages:
            print(f"  - {m}")
        return 1

    # Run engine
    engine = DataValidationEngine(
        input_directory=input_dir,
        schema_registry=schema_registry,
        relationship_registry=relationship_registry,
        validation_rules=validation_rules,
        source_type=args.source_type,
        collect_record_level_issues=args.collect_record_issues,
        maximum_record_level_examples=args.max_record_examples,
    )
    result = engine.run_validation()

    # Export outputs
    files = export_validation_outputs(result, output_dir)
    result.validation_run.notes = f"Exported {len(files)} output files."

    # Print summary
    print_summary(result)

    # Exit code
    if result.validation_run.run_status in ("Passed", "Passed with Warnings"):
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
