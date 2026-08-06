"""
Sentinel360 Healthcare — Analytical Architecture Validation Runner

Orchestrates Step 2A-1 governance validation.
No actual KPI calculation is performed.

Step: 2A-1
"""

import argparse
import hashlib
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from analytical_config_loader import AnalyticalConfigLoader
from analytical_contracts import CalculationGateContract, ImmutabilityVerificationContract
from analytical_governance_validator import AnalyticalGovernanceValidator
from analytical_models import CalculationRunManifest
from analytical_schema_registry import list_analytical_schemas, validate_schema_completeness
from kpi_registry import KPIRegistry, build_registry_from_config


# ---------------------------------------------------------------------------
# 1. Runner
# ---------------------------------------------------------------------------

class AnalyticalArchitectureRunner:
    """Runs the Step 2A-1 analytical architecture validation."""

    def __init__(
        self,
        project_root: Path,
        processed_dir: Path,
        config_dir: Path,
        output_dir: Path,
        log_dir: Path,
    ):
        self.project_root = Path(project_root)
        self.processed_dir = Path(processed_dir)
        self.config_dir = Path(config_dir)
        self.output_dir = Path(output_dir)
        self.log_dir = Path(log_dir)
        self.calculation_run_id = f"ARCH-2A1-{uuid.uuid4().hex[:12].upper()}"
        self.baseline_checksums: Dict[str, str] = {}
        self.manifest = CalculationRunManifest(
            calculation_run_id=self.calculation_run_id,
            run_type="governance_check",
            start_time=datetime.now(),
        )
        self.results: Dict[str, Any] = {}

    # -- Execution ---------------------------------------------------------

    def run(self, dry_run: bool = False, execute_export: bool = False) -> Dict[str, Any]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 1. Record Phase 1 checksums
        self._record_phase1_checksums()

        # 2. Load configurations
        config_loader = AnalyticalConfigLoader(self.config_dir)
        config_loader.load_kpi_definitions()
        config_loader.load_kpi_thresholds()
        config_loader.load_data_confidence_rules()
        config_validation = config_loader.validate_configuration()

        # 3. Build KPI registry
        registry = KPIRegistry(build_registry_from_config(config_loader.kpi_definitions))

        # 4. Validate governance
        validator = AnalyticalGovernanceValidator(registry, self.processed_dir, self.config_dir)
        governance_results = validator.validate_all()

        # 5. Verify Phase 1 immutability
        immutability = ImmutabilityVerificationContract.verify_immutability(
            self.baseline_checksums, self.processed_dir
        )

        # 6. Check calculation gate
        readiness = validator.get_readiness()
        gate = CalculationGateContract.check_calculation_gate(
            governance_results, readiness, phase1_immutable=immutability.verified
        )

        # 7. Compile results
        self.results = {
            "calculation_run_id": self.calculation_run_id,
            "run_type": "governance_check",
            "start_time": str(self.manifest.start_time),
            "end_time": str(datetime.now()),
            "status": "Passed" if governance_results.get("overall_valid") else "Failed",
            "phase1_immutability_verified": immutability.verified,
            "phase1_datasets_unchanged": immutability.datasets_unchanged,
            "phase1_datasets_changed": immutability.datasets_changed,
            "kpi_count": len(registry.list_kpi_ids()),
            "kpi_ids": registry.list_kpi_ids(),
            "readiness_summary": readiness,
            "calculation_gate": gate.to_dict(),
            "config_validation": config_validation,
            "governance_validation": governance_results,
            "issue_count": len(validator.get_issues()),
            "issues": [i.to_dict() for i in validator.get_issues()],
            "source_field_mapping": validator.get_source_field_mapping(),
        }

        # 8. Export if requested
        if execute_export and not dry_run:
            self._export_outputs(registry, validator, config_loader, immutability)

        self.manifest.end_time = datetime.now()
        self.manifest.status = self.results["status"]
        self.manifest.issue_count = self.results["issue_count"]
        self.manifest.phase1_immutability_verified = immutability.verified
        self.manifest.phase1_checksums_match = immutability.verified

        return self.results

    # -- Phase 1 Checksums -------------------------------------------------

    def _record_phase1_checksums(self) -> None:
        for fname in sorted(os.listdir(self.processed_dir)):
            if fname.endswith(".csv"):
                fpath = self.processed_dir / fname
                with open(fpath, "rb") as fh:
                    self.baseline_checksums[fname] = hashlib.sha256(fh.read()).hexdigest()

    # -- Export ------------------------------------------------------------

    def _export_outputs(
        self,
        registry: KPIRegistry,
        validator: AnalyticalGovernanceValidator,
        config_loader: AnalyticalConfigLoader,
        immutability: Any,
    ) -> None:
        out = self.output_dir

        # 1. Manifest
        with open(out / "analytical_architecture_manifest.json", "w") as f:
            json.dump(self.results, f, indent=2, default=str)

        # 2. KPI Governance Registry
        kpi_records = []
        for kpi in registry.list_kpis():
            mapping = validator.get_source_field_mapping().get(kpi.kpi_id, {})
            kpi_records.append({
                "kpi_id": kpi.kpi_id,
                "kpi_name": kpi.kpi_name,
                "domain": kpi.domain,
                "description": kpi.description,
                "numerator_definition": kpi.numerator_definition,
                "denominator_definition": kpi.denominator_definition,
                "formula_text": kpi.formula_text,
                "unit": kpi.unit,
                "directionality": kpi.directionality,
                "grain": kpi.grain,
                "calculation_frequency": kpi.calculation_frequency,
                "authoritative_input_dataset": kpi.authoritative_input_dataset,
                "required_fields": ", ".join(kpi.required_fields),
                "eligibility_rules": ", ".join(kpi.eligibility_rules),
                "exclusion_rules": ", ".join(kpi.exclusion_rules),
                "null_treatment": kpi.null_treatment,
                "zero_denominator_treatment": kpi.zero_denominator_treatment,
                "minimum_denominator": kpi.minimum_denominator,
                "threshold_config_reference": kpi.threshold_config_reference,
                "data_confidence_rule_reference": kpi.data_confidence_rule_reference,
                "config_version": kpi.config_version,
                "approval_requirement": kpi.approval_requirement,
                "readiness_status": validator.get_readiness().get(kpi.kpi_id, "Not Applicable"),
                "unresolved_rules": "; ".join(kpi.unresolved_rules),
                "effective_date": str(kpi.effective_date) if kpi.effective_date else None,
                "approval_status": kpi.approval_status,
            })
        pd.DataFrame(kpi_records).to_csv(out / "kpi_governance_registry.csv", index=False)

        # 3. KPI Readiness Summary
        readiness_records = []
        for kpi_id, status in validator.get_readiness().items():
            kpi = registry.get_kpi(kpi_id)
            mapping = validator.get_source_field_mapping().get(kpi_id, {})
            readiness_records.append({
                "kpi_id": kpi_id,
                "kpi_name": kpi.kpi_name if kpi else "",
                "readiness_status": status,
                "blocking_reason": "",
                "source_dataset_available": bool(mapping.get("dataset")),
                "required_fields_available": len(mapping.get("required_fields", [])) > 0,
                "threshold_config_available": bool(kpi.threshold_config_reference) if kpi else False,
                "approval_status": kpi.approval_status if kpi else "",
                "assessed_at": datetime.now(),
                "calculation_run_id": self.calculation_run_id,
                "unresolved_rules": "; ".join(kpi.unresolved_rules) if kpi else "",
            })
        pd.DataFrame(readiness_records).to_csv(out / "kpi_readiness_summary.csv", index=False)

        # 4. KPI Source Field Mapping
        mapping_records = []
        for kpi_id, mapping in validator.get_source_field_mapping().items():
            kpi = registry.get_kpi(kpi_id)
            mapping_records.append({
                "kpi_id": kpi_id,
                "kpi_name": kpi.kpi_name if kpi else "",
                "source_dataset": mapping.get("dataset", ""),
                "numerator_field": mapping.get("numerator_field", ""),
                "denominator_field": mapping.get("denominator_field", ""),
                "required_fields": ", ".join(mapping.get("required_fields", [])),
                "notes": mapping.get("notes", ""),
            })
        pd.DataFrame(mapping_records).to_csv(out / "kpi_source_field_mapping.csv", index=False)

        # 5. KPI Configuration Validation
        config_issues = []
        for issue in config_loader.get_issues():
            config_issues.append({
                "issue_id": issue.issue_id,
                "issue_type": issue.issue_type,
                "issue_description": issue.issue_description,
                "config_file": issue.source_dataset,
            })
        if not config_issues:
            config_issues.append({"issue_id": "", "issue_type": "Information", "issue_description": "No configuration issues", "config_file": ""})
        pd.DataFrame(config_issues).to_csv(out / "kpi_configuration_validation.csv", index=False)

        # 6. KPI Threshold Validation
        threshold_path = self.config_dir / "kpi_threshold_config.csv"
        if threshold_path.exists():
            pd.read_csv(threshold_path).to_csv(out / "kpi_threshold_validation.csv", index=False)
        else:
            pd.DataFrame({"issue": ["Threshold config missing"]}).to_csv(out / "kpi_threshold_validation.csv", index=False)

        # 7. Analytical Schema Summary
        schema_result = validate_schema_completeness()
        schema_records = []
        for schema_name in list_analytical_schemas():
            schema_records.append({
                "schema_name": schema_name,
                "defined": True,
                "required_field_count": len(validate_schema_completeness()),
            })
        pd.DataFrame(schema_records).to_csv(out / "analytical_schema_summary.csv", index=False)

        # 8. Governance Issue Log
        issue_records = []
        for issue in validator.get_issues():
            issue_records.append({
                "issue_id": issue.issue_id,
                "issue_type": issue.issue_type,
                "severity": issue.severity,
                "issue_description": issue.issue_description,
                "source_dataset": issue.source_dataset,
                "kpi_id": issue.kpi_id,
                "field_name": issue.field_name,
                "resolution_status": issue.resolution_status,
                "created_at": issue.created_at,
            })
        if not issue_records:
            issue_records.append({
                "issue_id": "", "issue_type": "Information", "severity": "Information",
                "issue_description": "No governance issues", "source_dataset": "", "kpi_id": "",
                "field_name": "", "resolution_status": "N/A", "created_at": datetime.now(),
            })
        pd.DataFrame(issue_records).to_csv(out / "analytical_governance_issue_log.csv", index=False)

        # 9. Governance Audit Log
        audit_records = [{
            "audit_id": str(uuid.uuid4())[:8],
            "operation": "governance_validation",
            "dataset_name": "analytical_architecture",
            "record_count": len(registry.list_kpi_ids()),
            "calculation_run_id": self.calculation_run_id,
            "performed_by": "run_analytical_architecture_validation",
            "performed_at": datetime.now(),
            "notes": f"KPIs validated: {len(registry.list_kpi_ids())}, Issues: {len(validator.get_issues())}",
        }]
        pd.DataFrame(audit_records).to_csv(out / "analytical_governance_audit_log.csv", index=False)

        # 10. Phase 1 Immutability Verification
        immutability_records = []
        for fname, baseline_hash in self.baseline_checksums.items():
            current_hash = immutability.checksum_comparison.get(fname, {}).get("current", "")
            match = baseline_hash == current_hash
            immutability_records.append({
                "dataset_name": fname,
                "baseline_checksum": baseline_hash,
                "current_checksum": current_hash,
                "match": match,
                "status": "Unchanged" if match else "Changed",
            })
        pd.DataFrame(immutability_records).to_csv(out / "phase1_immutability_verification.csv", index=False)


# ---------------------------------------------------------------------------
# 2. CLI Entry Point
# ---------------------------------------------------------------------------

def run_closure(
    project_root: Optional[Path] = None,
    processed_dir: Optional[Path] = None,
    config_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    log_dir: Optional[Path] = None,
    dry_run: bool = False,
    execute_export: bool = False,
) -> Dict[str, Any]:
    root = Path(project_root) if project_root else Path.cwd()
    runner = AnalyticalArchitectureRunner(
        project_root=root,
        processed_dir=Path(processed_dir) if processed_dir else root / "data" / "processed",
        config_dir=Path(config_dir) if config_dir else root / "config",
        output_dir=Path(output_dir) if output_dir else root / "outputs" / "analytical_governance",
        log_dir=Path(log_dir) if log_dir else root / "outputs" / "logs",
    )
    return runner.run(dry_run=dry_run, execute_export=execute_export)


def main():
    parser = argparse.ArgumentParser(description="Sentinel360 Analytical Architecture Validation (Step 2A-1)")
    parser.add_argument("--project-root", type=str, default=".")
    parser.add_argument("--processed-dir", type=str, default=None)
    parser.add_argument("--config-dir", type=str, default=None)
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--log-dir", type=str, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute-export", action="store_true")
    args = parser.parse_args()

    root = Path(args.project_root)
    result = run_closure(
        project_root=root,
        processed_dir=Path(args.processed_dir) if args.processed_dir else root / "data" / "processed",
        config_dir=Path(args.config_dir) if args.config_dir else root / "config",
        output_dir=Path(args.output_dir) if args.output_dir else root / "outputs" / "analytical_governance",
        log_dir=Path(args.log_dir) if args.log_dir else root / "outputs" / "logs",
        dry_run=args.dry_run,
        execute_export=args.execute_export,
    )
    print(f"Step 2A-1 Status: {result['status']}")
    print(f"KPIs Registered: {result['kpi_count']}")
    print(f"Phase 1 Immutability: {'Verified' if result['phase1_immutability_verified'] else 'Failed'}")
    print(f"Issues: {result['issue_count']}")
    print(f"Readiness: {result['readiness_summary']}")


if __name__ == "__main__":
    main()
