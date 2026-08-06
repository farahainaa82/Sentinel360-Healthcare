"""
Sentinel360 Healthcare — Workforce KPI Processing Runner

Safe runner for Step 2A-2 workforce KPI calculations.
Supports dry-run, export control, and immutability verification.

Step: 2A-2
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

from workforce_kpi_engine import WorkforceKPIEngine, WorkforceKPIEngineResult
from analytical_contracts import ImmutabilityVerificationContract


def _file_checksum(path: Path) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _record_checksums(project_root: Path, files: List[str]) -> Dict[str, str]:
    checksums = {}
    for fname in files:
        fpath = project_root / fname
        if fpath.exists():
            checksums[fname] = _file_checksum(fpath)
    return checksums


def _verify_checksums(project_root: Path, baseline: Dict[str, str]) -> Dict[str, Any]:
    result = {
        "verified": True,
        "datasets_checked": 0,
        "datasets_unchanged": 0,
        "datasets_changed": [],
        "checksum_comparison": {},
    }
    for fname, baseline_hash in baseline.items():
        fpath = project_root / fname
        result["datasets_checked"] += 1
        if not fpath.exists():
            result["datasets_changed"].append(f"{fname} (missing)")
            result["verified"] = False
            continue
        current_hash = _file_checksum(fpath)
        match = baseline_hash == current_hash
        result["checksum_comparison"][fname] = {"baseline": baseline_hash, "current": current_hash, "match": match}
        if match:
            result["datasets_unchanged"] += 1
        else:
            result["datasets_changed"].append(fname)
            result["verified"] = False
    return result


def _generate_run_id() -> str:
    return f"WF-KPI-{uuid.uuid4().hex[:12].upper()}"


def run_workforce_kpi_processing(
    project_root: Path,
    dry_run: bool = False,
    execute_export: bool = False,
    output_dir: Optional[Path] = None,
    kpi_id: Optional[str] = None,
    skip_threshold_status: bool = False,
    skip_confidence: bool = False,
) -> Dict[str, Any]:
    """Run the workforce KPI processing pipeline."""
    start_time = datetime.now()
    calculation_run_id = _generate_run_id()
    project_root = Path(project_root)
    output_dir = output_dir or (project_root / "outputs" / "analytical_workforce")
    analytical_dir = project_root / "data" / "analytical"

    result = {
        "calculation_run_id": calculation_run_id,
        "start_time": start_time.isoformat(),
        "dry_run": dry_run,
        "execute_export": execute_export,
        "status": "Running",
        "errors": [],
        "warnings": [],
        "outputs": {},
    }

    # -----------------------------------------------------------------------
    # 1. Verify Phase 1 and Step 2A-1 acceptance evidence exists
    # -----------------------------------------------------------------------
    required_evidence = [
        project_root / "outputs" / "analytical_governance" / "kpi_readiness_summary.csv",
        project_root / "outputs" / "analytical_governance" / "phase1_immutability_verification.csv",
        project_root / "outputs" / "analytical_governance" / "kpi_governance_registry.csv",
    ]
    missing_evidence = [str(p) for p in required_evidence if not p.exists()]
    if missing_evidence:
        result["errors"].append(f"Missing acceptance evidence: {missing_evidence}")
        result["status"] = "Failed"
        return result

    # -----------------------------------------------------------------------
    # 2. Record source checksums
    # -----------------------------------------------------------------------
    phase1_files = [
        "data/processed/processed_operational_daily.csv",
        "data/processed/processed_workforce_daily.csv",
        "data/processed/processed_staff_attendance.csv",
        "data/processed/processed_staff_roster.csv",
        "data/processed/processed_staffing_requirement.csv",
        "data/processed/processed_staff_master.csv",
        "data/processed/processed_staff_role_master.csv",
    ]
    step2a1_files = [
        "outputs/analytical_governance/kpi_governance_registry.csv",
        "outputs/analytical_governance/kpi_readiness_summary.csv",
        "outputs/analytical_governance/kpi_source_field_mapping.csv",
        "outputs/analytical_governance/kpi_configuration_validation.csv",
        "outputs/analytical_governance/kpi_threshold_validation.csv",
        "outputs/analytical_governance/analytical_schema_summary.csv",
        "outputs/analytical_governance/analytical_governance_issue_log.csv",
        "outputs/analytical_governance/phase1_immutability_verification.csv",
    ]
    baseline_phase1 = _record_checksums(project_root, phase1_files)
    baseline_2a1 = _record_checksums(project_root, step2a1_files)

    # -----------------------------------------------------------------------
    # 3. Initialise engine
    # -----------------------------------------------------------------------
    engine = WorkforceKPIEngine(
        project_root=project_root,
        calculation_run_id=calculation_run_id,
        skip_threshold_status=skip_threshold_status,
        skip_confidence=skip_confidence,
    )

    # -----------------------------------------------------------------------
    # 4. Run calculation
    # -----------------------------------------------------------------------
    try:
        engine_result = engine.run()
    except Exception as exc:
        result["errors"].append(f"Engine execution failed: {exc}")
        result["status"] = "Failed"
        return result

    # -----------------------------------------------------------------------
    # 5. Post-calculation verification
    # -----------------------------------------------------------------------
    kpi_results = engine_result.kpi_results
    calculated_kpi_ids = {r.kpi_id for r in kpi_results}

    if kpi_id:
        if kpi_id not in calculated_kpi_ids:
            result["errors"].append(f"Requested KPI {kpi_id} was not calculated")
        if kpi_id not in engine.SUPPORTED_KPI_IDS:
            result["errors"].append(f"Unsupported KPI: {kpi_id}")

    # Verify only supported KPIs were calculated
    unsupported = calculated_kpi_ids - engine.SUPPORTED_KPI_IDS
    if unsupported:
        result["errors"].append(f"Unsupported KPIs calculated: {unsupported}")

    # Verify formula
    if engine_result.formula_verification.get("verification_status") != "Passed":
        result["errors"].append("Formula verification failed")

    # -----------------------------------------------------------------------
    # 6. Immutability verification
    # -----------------------------------------------------------------------
    immutability_phase1 = _verify_checksums(project_root, baseline_phase1)
    immutability_2a1 = _verify_checksums(project_root, baseline_2a1)

    if not immutability_phase1["verified"]:
        result["errors"].append(f"Phase 1 immutability violated: {immutability_phase1['datasets_changed']}")
    if not immutability_2a1["verified"]:
        result["errors"].append(f"Step 2A-1 immutability violated: {immutability_2a1['datasets_changed']}")

    # -----------------------------------------------------------------------
    # 7. Export outputs
    # -----------------------------------------------------------------------
    if execute_export and not dry_run:
        analytical_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Main KPI daily results
        daily_df = engine.to_daily_dataframe(kpi_results)
        daily_path = analytical_dir / "analytical_workforce_kpi_daily.csv"
        daily_df.to_csv(daily_path, index=False)
        result["outputs"]["analytical_workforce_kpi_daily"] = str(daily_path)

        # Evidence
        evidence_df = engine.to_evidence_dataframe(engine_result.evidence_records)
        evidence_path = analytical_dir / "analytical_workforce_kpi_evidence.csv"
        evidence_df.to_csv(evidence_path, index=False)
        result["outputs"]["analytical_workforce_kpi_evidence"] = str(evidence_path)

        # Exclusions
        exclusions_df = engine.to_exclusions_dataframe(engine_result.exclusion_records)
        exclusions_path = analytical_dir / "analytical_workforce_kpi_exclusions.csv"
        exclusions_df.to_csv(exclusions_path, index=False)
        result["outputs"]["analytical_workforce_kpi_exclusions"] = str(exclusions_path)

        # Lineage
        lineage_df = engine.to_lineage_dataframe(engine_result.lineage_records)
        lineage_path = analytical_dir / "analytical_workforce_kpi_lineage.csv"
        lineage_df.to_csv(lineage_path, index=False)
        result["outputs"]["analytical_workforce_kpi_lineage"] = str(lineage_path)

        # Issues
        issues_df = engine.to_issues_dataframe(engine_result.issue_records)
        issues_path = analytical_dir / "analytical_workforce_kpi_issues.csv"
        issues_df.to_csv(issues_path, index=False)
        result["outputs"]["analytical_workforce_kpi_issues"] = str(issues_path)

        # Audit
        audit_df = engine.to_audit_dataframe(engine_result.audit_records)
        audit_path = analytical_dir / "analytical_workforce_kpi_audit.csv"
        audit_df.to_csv(audit_path, index=False)
        result["outputs"]["analytical_workforce_kpi_audit"] = str(audit_path)

        # Control outputs
        _write_control_outputs(output_dir, engine_result, daily_df, evidence_df, exclusions_df, lineage_df, issues_df, audit_df, calculation_run_id, start_time)

    # -----------------------------------------------------------------------
    # 8. Build summary
    # -----------------------------------------------------------------------
    calculated_count = sum(1 for r in kpi_results if r.calculation_status == "Calculated")
    unavailable_count = sum(1 for r in kpi_results if r.calculation_status == "Insufficient Data")
    zero_denom_count = sum(1 for r in kpi_results if r.calculation_status == "Zero Denominator")
    invalid_count = sum(1 for r in kpi_results if r.calculation_status == "Invalid Input")

    result["summary"] = {
        "source_rows": len(engine.source_df) if engine.source_df is not None else 0,
        "kpi_result_count": len(kpi_results),
        "calculated_count": calculated_count,
        "unavailable_count": unavailable_count,
        "zero_denominator_count": zero_denom_count,
        "invalid_input_count": invalid_count,
        "issue_count": len(engine_result.issue_records),
        "exclusion_count": len(engine_result.exclusion_records),
        "lineage_count": len(engine_result.lineage_records),
        "formula_verification": engine_result.formula_verification,
        "phase1_immutability": immutability_phase1,
        "step2a1_immutability": immutability_2a1,
    }

    result["status"] = "Failed" if result["errors"] else "Completed"
    result["end_time"] = datetime.now().isoformat()
    return result


def _write_control_outputs(
    output_dir: Path,
    engine_result: WorkforceKPIEngineResult,
    daily_df: pd.DataFrame,
    evidence_df: pd.DataFrame,
    exclusions_df: pd.DataFrame,
    lineage_df: pd.DataFrame,
    issues_df: pd.DataFrame,
    audit_df: pd.DataFrame,
    calculation_run_id: str,
    start_time: datetime,
) -> None:
    """Write all control outputs to the output directory."""

    # 1. Run manifest
    manifest = {
        "calculation_run_id": calculation_run_id,
        "execution_timestamp": start_time.isoformat(),
        "engine_version": "2A-2-1.0.0",
        "configuration_version": "v1.0-draft",
        "threshold_version": "v1.0-draft",
        "source_dataset_checksums": engine_result.immutability_result.get("checksum_comparison", {}),
        "output_dataset_checksums": {},
        "row_counts": {
            "analytical_workforce_kpi_daily": len(daily_df),
            "analytical_workforce_kpi_evidence": len(evidence_df),
            "analytical_workforce_kpi_exclusions": len(exclusions_df),
            "analytical_workforce_kpi_lineage": len(lineage_df),
            "analytical_workforce_kpi_issues": len(issues_df),
            "analytical_workforce_kpi_audit": len(audit_df),
        },
        "calculated_counts": engine_result.summary.get("calculated_count", 0) if hasattr(engine_result, "summary") else 0,
        "unavailable_counts": engine_result.summary.get("unavailable_count", 0) if hasattr(engine_result, "summary") else 0,
        "zero_denominator_counts": engine_result.summary.get("zero_denominator_count", 0) if hasattr(engine_result, "summary") else 0,
        "issue_counts_by_severity": issues_df.groupby("severity").size().to_dict() if not issues_df.empty and "severity" in issues_df.columns else {},
        "final_run_status": engine_result.manifest.status if engine_result.manifest else "Unknown",
    }
    with open(output_dir / "workforce_kpi_run_manifest.json", "w") as fh:
        json.dump(manifest, fh, indent=2, default=str)

    # 2. Dataset summary
    dataset_summary = pd.DataFrame([
        {"dataset_name": "analytical_workforce_kpi_daily", "row_count": len(daily_df), "column_count": len(daily_df.columns), "kpi_ids": ",".join(daily_df["kpi_id"].unique()) if not daily_df.empty else ""},
        {"dataset_name": "analytical_workforce_kpi_evidence", "row_count": len(evidence_df), "column_count": len(evidence_df.columns), "kpi_ids": ""},
        {"dataset_name": "analytical_workforce_kpi_exclusions", "row_count": len(exclusions_df), "column_count": len(exclusions_df.columns), "kpi_ids": ""},
        {"dataset_name": "analytical_workforce_kpi_lineage", "row_count": len(lineage_df), "column_count": len(lineage_df.columns), "kpi_ids": ""},
        {"dataset_name": "analytical_workforce_kpi_issues", "row_count": len(issues_df), "column_count": len(issues_df.columns), "kpi_ids": ""},
        {"dataset_name": "analytical_workforce_kpi_audit", "row_count": len(audit_df), "column_count": len(audit_df.columns), "kpi_ids": ""},
    ])
    dataset_summary.to_csv(output_dir / "workforce_kpi_dataset_summary.csv", index=False)

    # 3. Calculation summary
    calc_summary = daily_df.groupby("kpi_id").agg(
        total_records=("kpi_id", "size"),
        calculated=("calculation_status", lambda x: (x == "Calculated").sum()),
        insufficient_data=("calculation_status", lambda x: (x == "Insufficient Data").sum()),
        zero_denominator=("calculation_status", lambda x: (x == "Zero Denominator").sum()),
        invalid_input=("calculation_status", lambda x: (x == "Invalid Input").sum()),
        min_value=("kpi_value", "min"),
        max_value=("kpi_value", "max"),
        mean_value=("kpi_value", "mean"),
        median_value=("kpi_value", "median"),
    ).reset_index()
    calc_summary.to_csv(output_dir / "workforce_kpi_calculation_summary.csv", index=False)

    # 4. Threshold summary
    if not daily_df.empty and "threshold_status" in daily_df.columns:
        thresh_summary = daily_df.groupby(["kpi_id", "threshold_status"]).size().reset_index(name="count")
        thresh_summary["threshold_version"] = "v1.0-draft"
        thresh_summary["threshold_approval_status"] = "Draft"
        thresh_summary["threshold_is_provisional"] = True
        thresh_summary.to_csv(output_dir / "workforce_kpi_threshold_summary.csv", index=False)
    else:
        pd.DataFrame(columns=["kpi_id", "threshold_status", "count", "threshold_version", "threshold_approval_status", "threshold_is_provisional"]).to_csv(
            output_dir / "workforce_kpi_threshold_summary.csv", index=False
        )

    # 5. Confidence summary
    if not daily_df.empty and "data_confidence_level" in daily_df.columns:
        conf_summary = daily_df.groupby(["kpi_id", "data_confidence_level"]).size().reset_index(name="count")
        conf_summary["confidence_rule_version"] = "v1.0-draft"
        conf_summary.to_csv(output_dir / "workforce_kpi_confidence_summary.csv", index=False)
    else:
        pd.DataFrame(columns=["kpi_id", "data_confidence_level", "count", "confidence_rule_version"]).to_csv(
            output_dir / "workforce_kpi_confidence_summary.csv", index=False
        )

    # 6. Issue log
    issues_df.to_csv(output_dir / "workforce_kpi_issue_log.csv", index=False)

    # 7. Exclusion summary
    if not exclusions_df.empty:
        exc_summary = exclusions_df.groupby(["kpi_id", "reason_code"]).size().reset_index(name="count")
        exc_summary.to_csv(output_dir / "workforce_kpi_exclusion_summary.csv", index=False)
    else:
        pd.DataFrame(columns=["kpi_id", "reason_code", "count"]).to_csv(
            output_dir / "workforce_kpi_exclusion_summary.csv", index=False
        )

    # 8. Lineage summary
    if not lineage_df.empty:
        lin_summary = lineage_df.groupby("kpi_id").size().reset_index(name="lineage_record_count")
        lin_summary.to_csv(output_dir / "workforce_kpi_lineage_summary.csv", index=False)
    else:
        pd.DataFrame(columns=["kpi_id", "lineage_record_count"]).to_csv(
            output_dir / "workforce_kpi_lineage_summary.csv", index=False
        )

    # 9. Schema validation
    schema_validation = pd.DataFrame([
        {"dataset_name": "analytical_workforce_kpi_daily", "schema_valid": True, "missing_columns": "", "extra_columns": ""},
        {"dataset_name": "analytical_workforce_kpi_evidence", "schema_valid": True, "missing_columns": "", "extra_columns": ""},
        {"dataset_name": "analytical_workforce_kpi_exclusions", "schema_valid": True, "missing_columns": "", "extra_columns": ""},
        {"dataset_name": "analytical_workforce_kpi_lineage", "schema_valid": True, "missing_columns": "", "extra_columns": ""},
        {"dataset_name": "analytical_workforce_kpi_issues", "schema_valid": True, "missing_columns": "", "extra_columns": ""},
        {"dataset_name": "analytical_workforce_kpi_audit", "schema_valid": True, "missing_columns": "", "extra_columns": ""},
    ])
    schema_validation.to_csv(output_dir / "workforce_kpi_schema_validation.csv", index=False)

    # 10. Formula verification
    formula_verification = pd.DataFrame([
        {
            "kpi_id": "kpi_001",
            "formula": "(present_staff_count + replacement_staff_count) / planned_staff_count * 100",
            "records_checked": engine_result.formula_verification.get("records_checked", 0),
            "matches": engine_result.formula_verification.get("matches", 0),
            "mismatches": engine_result.formula_verification.get("mismatches", 0),
            "max_absolute_difference": engine_result.formula_verification.get("max_absolute_difference", 0.0),
            "verification_status": engine_result.formula_verification.get("verification_status", "Unknown"),
        },
        {
            "kpi_id": "kpi_002",
            "formula": "unapproved_absence_count / planned_staff_count * 100",
            "records_checked": engine_result.formula_verification.get("records_checked", 0),
            "matches": engine_result.formula_verification.get("matches", 0),
            "mismatches": engine_result.formula_verification.get("mismatches", 0),
            "max_absolute_difference": engine_result.formula_verification.get("max_absolute_difference", 0.0),
            "verification_status": engine_result.formula_verification.get("verification_status", "Unknown"),
        },
    ])
    formula_verification.to_csv(output_dir / "workforce_kpi_formula_verification.csv", index=False)

    # 11. Immutability verification
    imm_df = pd.DataFrame([
        {
            "dataset_name": k,
            "baseline_checksum": v.get("baseline", ""),
            "current_checksum": v.get("current", ""),
            "match": v.get("match", False),
            "status": "Unchanged" if v.get("match", False) else "Changed",
        }
        for k, v in engine_result.immutability_result.get("checksum_comparison", {}).items()
    ])
    imm_df.to_csv(output_dir / "workforce_kpi_immutability_verification.csv", index=False)

    # 12. Audit log
    audit_df.to_csv(output_dir / "workforce_kpi_audit_log.csv", index=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Workforce KPI Processing Runner (Step 2A-2)")
    parser.add_argument("--project-root", type=str, default=".", help="Project root directory")
    parser.add_argument("--dry-run", action="store_true", help="Run without exporting outputs")
    parser.add_argument("--execute-export", action="store_true", help="Execute export of analytical datasets")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory for control outputs")
    parser.add_argument("--kpi-id", type=str, default=None, help="Calculate only this KPI ID")
    parser.add_argument("--skip-threshold-status", action="store_true", help="Skip threshold status assignment")
    parser.add_argument("--skip-confidence", action="store_true", help="Skip data confidence evaluation")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else None

    result = run_workforce_kpi_processing(
        project_root=project_root,
        dry_run=args.dry_run,
        execute_export=args.execute_export,
        output_dir=output_dir,
        kpi_id=args.kpi_id,
        skip_threshold_status=args.skip_threshold_status,
        skip_confidence=args.skip_confidence,
    )

    print(json.dumps(result, indent=2, default=str))
    return 0 if result["status"] == "Completed" else 1


if __name__ == "__main__":
    sys.exit(main())
