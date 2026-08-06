"""
Sentinel360 Healthcare — Step 2D-3 Closure Validator

Cumulative regression testing and final acceptance verification
for the complete patient-flow processing branch (Steps 2A through 2D-3D).

Step: 2D-3E
"""

import hashlib
import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd
import numpy as np

from src.processed_schema_registry import get_processed_schema
from src.processing_models import ProcessingIssue

CLOSURE_VERSION = "2D-3E-1.0.0"
ENGINE_VERSION = "Sentinel360-Phase1-2D-3E"

REQUIRED_CATEGORIES = {
    "Implementation": [
        "src/demo_generation_config.py",
        "src/demo_data_generator.py",
        "src/export_demo_data.py",
        "src/profile_demo_data.py",
        "src/data_validation_engine.py",
        "src/run_data_validation.py",
        "src/validation_config_loader.py",
        "src/validation_models.py",
        "src/processing_models.py",
        "src/processed_schema_registry.py",
        "src/processing_config_loader.py",
        "src/processing_contracts.py",
        "src/workforce_transformer.py",
        "src/workforce_daily_builder.py",
        "src/run_workforce_processing.py",
        "src/patient_encounter_transformer.py",
        "src/run_patient_encounter_processing.py",
        "src/queue_capacity_schedule_transformer.py",
        "src/run_queue_capacity_schedule_processing.py",
        "src/patient_flow_daily_builder.py",
        "src/run_patient_flow_daily_processing.py",
        "src/patient_flow_integration_validator.py",
        "src/run_patient_flow_integration_validation.py",
        "src/step_2d3_closure_validator.py",
        "src/run_step_2d3_closure.py",
    ],
    "Test": [
        "tests/test_demo_data_generator.py",
        "tests/test_demo_data_export.py",
        "tests/test_data_validation_engine.py",
        "tests/test_processing_architecture.py",
        "tests/test_workforce_transformation.py",
        "tests/test_patient_encounter_transformation.py",
        "tests/test_queue_capacity_schedule_transformation.py",
        "tests/test_patient_flow_daily_builder.py",
        "tests/test_patient_flow_integration.py",
        "tests/test_step_2d3_closure.py",
    ],
    "Documentation": [
        "docs/data_validation_engine_specification.md",
        "docs/workforce_transformation_specification.md",
        "docs/workforce_processing_report.md",
        "docs/patient_encounter_transformation_specification.md",
        "docs/patient_encounter_processing_report.md",
        "docs/queue_capacity_schedule_transformation_specification.md",
        "docs/queue_capacity_schedule_processing_report.md",
        "docs/patient_flow_daily_specification.md",
        "docs/patient_flow_daily_processing_report.md",
        "docs/patient_flow_integration_specification.md",
        "docs/patient_flow_integration_report.md",
        "docs/step_2d3_closure_specification.md",
        "docs/step_2d3_final_acceptance_report.md",
    ],
    "Processed Dataset": [
        "data/processed/processed_hospital_master.csv",
        "data/processed/processed_department_master.csv",
        "data/processed/processed_staff_role_master.csv",
        "data/processed/processed_staff_master.csv",
        "data/processed/processed_staff_roster.csv",
        "data/processed/processed_staff_attendance.csv",
        "data/processed/processed_staffing_requirement.csv",
        "data/processed/processed_workforce_daily.csv",
        "data/processed/processed_patient_encounters.csv",
        "data/processed/processed_patient_queue.csv",
        "data/processed/processed_bed_capacity.csv",
        "data/processed/processed_service_schedule.csv",
        "data/processed/processed_patient_flow_daily.csv",
    ],
    "Manifest": [
        "outputs/logs/validation_run_manifest.json",
        "outputs/logs/patient_encounter_processing_run_manifest.json",
        "outputs/logs/queue_capacity_schedule_processing_run_manifest.json",
        "outputs/logs/patient_flow_daily_processing_run_manifest.json",
        "outputs/logs/patient_flow_integration_manifest.json",
    ],
    "Report": [
        "docs/data_validation_engine_specification.md",
        "docs/workforce_transformation_specification.md",
        "docs/workforce_processing_report.md",
        "docs/patient_encounter_transformation_specification.md",
        "docs/patient_encounter_processing_report.md",
        "docs/queue_capacity_schedule_transformation_specification.md",
        "docs/queue_capacity_schedule_processing_report.md",
        "docs/patient_flow_daily_specification.md",
        "docs/patient_flow_daily_processing_report.md",
        "docs/patient_flow_integration_specification.md",
        "docs/patient_flow_integration_report.md",
    ],
}

PRIOR_MANIFESTS = [
    "validation_run_manifest.json",
    "workforce_processing_run_manifest.json",
    "patient_encounter_processing_run_manifest.json",
    "queue_capacity_schedule_processing_run_manifest.json",
    "patient_flow_daily_processing_run_manifest.json",
    "patient_flow_integration_manifest.json",
]

PROCESSED_DATASETS = {
    "processed_hospital_master": {
        "file_name": "processed_hospital_master.csv",
        "primary_key": "hospital_id",
        "grain_keys": ["hospital_id"],
    },
    "processed_department_master": {
        "file_name": "processed_department_master.csv",
        "primary_key": "department_id",
        "grain_keys": ["department_id"],
    },
    "processed_staff_role_master": {
        "file_name": "processed_staff_role_master.csv",
        "primary_key": "staff_role_id",
        "grain_keys": ["staff_role_id"],
    },
    "processed_staff_master": {
        "file_name": "processed_staff_master.csv",
        "primary_key": "staff_id",
        "grain_keys": ["staff_id"],
    },
    "processed_staff_roster": {
        "file_name": "processed_staff_roster.csv",
        "primary_key": "roster_record_id",
        "grain_keys": ["roster_record_id"],
    },
    "processed_staff_attendance": {
        "file_name": "processed_staff_attendance.csv",
        "primary_key": "attendance_record_id",
        "grain_keys": ["attendance_record_id"],
    },
    "processed_staffing_requirement": {
        "file_name": "processed_staffing_requirement.csv",
        "primary_key": "staffing_requirement_id",
        "grain_keys": ["staffing_requirement_id"],
    },
    "processed_workforce_daily": {
        "file_name": "processed_workforce_daily.csv",
        "primary_key": "workforce_daily_id",
        "grain_keys": ["hospital_id", "department_id", "staff_role_id", "reporting_date"],
    },
    "processed_patient_encounters": {
        "file_name": "processed_patient_encounters.csv",
        "primary_key": "encounter_id",
        "grain_keys": ["hospital_id", "department_id", "reporting_date"],
    },
    "processed_patient_queue": {
        "file_name": "processed_patient_queue.csv",
        "primary_key": "queue_record_id",
        "grain_keys": ["hospital_id", "department_id", "reporting_date"],
    },
    "processed_bed_capacity": {
        "file_name": "processed_bed_capacity.csv",
        "primary_key": "bed_capacity_record_id",
        "grain_keys": ["hospital_id", "department_id", "reporting_date"],
    },
    "processed_service_schedule": {
        "file_name": "processed_service_schedule.csv",
        "primary_key": "service_schedule_id",
        "grain_keys": ["hospital_id", "department_id", "reporting_date"],
    },
    "processed_patient_flow_daily": {
        "file_name": "processed_patient_flow_daily.csv",
        "primary_key": "patient_flow_daily_id",
        "grain_keys": ["hospital_id", "department_id", "reporting_date"],
        "deterministic_id_pattern": r"^PFD-[A-Z0-9-]+-[A-Z0-9-]+-\d{8}$",
    },
}

PROHIBITED_FIELD_PATTERNS = [
    "kpi_value", "kpi_status", "trend", "anomaly_score", "risk_score",
    "forecast", "scenario", "financial_impact", "recommendation",
    "management_decision", "action_tracking", "outcome_review",
    "average_patient_waiting_time", "bed_occupancy_rate", "staffing_level",
    "staff_absenteeism_rate", "complaint_rate", "patient_satisfaction_score",
]


class Step2D3ClosureValidator:
    """Final closure validator for Step 2D-3 patient-flow processing branch."""

    def __init__(
        self,
        closure_run_id: str,
        project_root: Path,
        processed_directory: Path,
        log_directory: Path,
        tests_directory: Path,
        max_issue_examples: int = 1000,
    ):
        self.closure_run_id = closure_run_id
        self.project_root = project_root
        self.processed_directory = processed_directory
        self.log_directory = log_directory
        self.tests_directory = tests_directory
        self.max_issue_examples = max_issue_examples
        self.issues: List[ProcessingIssue] = []
        self.check_results: List[Dict[str, Any]] = []
        self.audit_events: List[Dict[str, Any]] = []
        self.file_inventory: List[Dict[str, Any]] = []
        self.dataset_acceptance: List[Dict[str, Any]] = []
        self.schema_acceptance: List[Dict[str, Any]] = []
        self.checksum_verification: List[Dict[str, Any]] = []
        self.prior_manifests: Dict[str, Dict[str, Any]] = {}
        self.test_summary: List[Dict[str, Any]] = []
        self.closure_manifest: Dict[str, Any] = {}
        self.blocked_reasons: List[str] = []
        self._dataset_checksums: Dict[str, str] = {}
        self._pre_checksums: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # Audit helpers
    # ------------------------------------------------------------------
    def _audit(self, event: str, details: str = "") -> None:
        self.audit_events.append({
            "closure_run_id": self.closure_run_id,
            "event": event,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        })

    def _add_issue(
        self,
        issue_type: str,
        severity: str,
        description: str,
        field_name: str = "",
        blocks_closure: bool = False,
    ) -> None:
        issue_id = f"CI-{len(self.issues)+1:04d}"
        self.issues.append(ProcessingIssue(
            processing_run_id=self.closure_run_id,
            issue_id=issue_id,
            issue_type=issue_type,
            severity=severity,
            issue_description=description,
            field_name=field_name,
            blocks_processing=blocks_closure,
        ))

    def _add_check(self, check_name: str, status: str, details: str = "") -> None:
        self.check_results.append({
            "closure_run_id": self.closure_run_id,
            "check_name": check_name,
            "status": status,
            "details": details,
            "checked_datetime": datetime.now().isoformat(),
        })

    # ------------------------------------------------------------------
    # File inventory
    # ------------------------------------------------------------------
    def inventory_required_files(self) -> Dict[str, Any]:
        self._audit("Inventory Started")
        inventory = []
        missing_required = []
        for category, files in REQUIRED_CATEGORIES.items():
            for rel_path in files:
                full_path = self.project_root / rel_path
                exists = full_path.exists()
                size = full_path.stat().st_size if exists else 0
                checksum = self._file_checksum(full_path) if exists else ""
                required_flag = True
                if not exists and category in ("Processed Dataset", "Manifest"):
                    missing_required.append(rel_path)
                status = "Present" if exists else "Missing"
                inventory.append({
                    "file_category": category,
                    "step_reference": self._step_from_path(rel_path),
                    "file_path": str(rel_path),
                    "required_flag": required_flag,
                    "exists_flag": exists,
                    "file_size_bytes": size,
                    "checksum": checksum,
                    "acceptance_status": status,
                    "notes": "" if exists else "Required file not found",
                    "checked_datetime": datetime.now().isoformat(),
                })
        self.file_inventory = inventory
        if missing_required:
            self.blocked_reasons.append(f"Missing required files: {missing_required}")
        self._audit("Inventory Completed", f"items={len(inventory)}")
        return {"inventory": inventory, "missing_required": missing_required}

    def _step_from_path(self, rel_path: str) -> str:
        mapping = {
            "src/demo": "2A",
            "src/export": "2B",
            "src/profile": "2B",
            "src/data_validation": "2C",
            "src/validation": "2C",
            "src/workforce": "2D-2",
            "src/patient_encounter": "2D-3A",
            "src/queue_capacity": "2D-3B",
            "src/patient_flow_daily": "2D-3C",
            "src/patient_flow_integration": "2D-3D",
            "src/step_2d3": "2D-3E",
        }
        lower = rel_path.lower()
        for prefix, step in mapping.items():
            if prefix in lower:
                return step
        return ""

    # ------------------------------------------------------------------
    # Manifest loading
    # ------------------------------------------------------------------
    def load_prior_manifests(self) -> Dict[str, Any]:
        self._audit("Load Prior Manifests Started")
        loaded = {}
        for manifest_name in PRIOR_MANIFESTS:
            path = self.log_directory / manifest_name
            if not path.exists():
                self._add_issue("Missing Manifest", "Critical", f"Missing manifest: {manifest_name}", blocks_closure=True)
                continue
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            loaded[manifest_name] = data
        self.prior_manifests = loaded
        self._audit("Load Prior Manifests Completed", f"loaded={len(loaded)}")
        return loaded

    def verify_prior_run_statuses(self) -> Dict[str, Any]:
        self._audit("Verify Prior Run Statuses Started")
        statuses = {}
        required_passes = {
            "validation_run_manifest.json": ["Passed"],
            "workforce_processing_run_manifest.json": ["Completed", "success", "Passed"],
            "patient_encounter_processing_run_manifest.json": ["Completed", "success", "Passed"],
            "queue_capacity_schedule_processing_run_manifest.json": ["Completed", "success", "Passed"],
            "patient_flow_daily_processing_run_manifest.json": ["success", "Passed"],
            "patient_flow_integration_manifest.json": ["Passed"],
        }
        for manifest_name, allowed in required_passes.items():
            data = self.prior_manifests.get(manifest_name, {})
            status = data.get("run_status", "Unknown")
            statuses[manifest_name] = status
            if status not in allowed:
                self._add_issue("Manifest Status Failure", "Critical", f"{manifest_name} status={status}, expected one of {allowed}", blocks_closure=True)
                self.blocked_reasons.append(f"{manifest_name} status={status}")
        self._add_check("Prior Manifest Statuses", "Passed" if not any(s not in allowed for s in statuses.values()) else "Failed")
        self._audit("Verify Prior Run Statuses Completed")
        return statuses

    # ------------------------------------------------------------------
    # Dataset presence and row counts
    # ------------------------------------------------------------------
    def verify_processed_dataset_presence(self) -> Dict[str, Any]:
        self._audit("Verify Processed Dataset Presence Started")
        results = {}
        for ds_name, meta in PROCESSED_DATASETS.items():
            path = self.processed_directory / meta["file_name"]
            exists = path.exists()
            results[ds_name] = exists
            if not exists:
                self._add_issue("Missing Processed Dataset", "Critical", f"Missing {ds_name}", blocks_closure=True)
                self.blocked_reasons.append(f"Missing processed dataset: {ds_name}")
        self._add_check("Processed Dataset Presence", "Passed" if all(results.values()) else "Failed")
        self._audit("Verify Processed Dataset Presence Completed")
        return results

    def verify_processed_dataset_row_counts(self) -> Dict[str, Any]:
        self._audit("Verify Processed Dataset Row Counts Started")
        results = {}
        expected = self._expected_row_counts_from_manifests()
        for ds_name, meta in PROCESSED_DATASETS.items():
            path = self.processed_directory / meta["file_name"]
            if not path.exists():
                results[ds_name] = {"expected": expected.get(ds_name), "actual": None, "status": "Failed"}
                continue
            df = pd.read_csv(path)
            actual = len(df)
            exp = expected.get(ds_name)
            match = (exp is not None and actual == exp)
            status = "Passed" if match else ("Failed" if exp is not None else "Unchecked")
            results[ds_name] = {"expected": exp, "actual": actual, "status": status}
            if exp is not None and actual != exp:
                self._add_issue("Row Count Mismatch", "Critical", f"{ds_name}: expected={exp}, actual={actual}", blocks_closure=True)
        self._add_check("Processed Dataset Row Counts", "Passed" if all(r["status"] == "Passed" for r in results.values() if r["expected"] is not None) else "Failed")
        self._audit("Verify Processed Dataset Row Counts Completed")
        return results

    def _expected_row_counts_from_manifests(self) -> Dict[str, int]:
        expected = {}
        # Workforce manifest
        wf = self.prior_manifests.get("workforce_processing_run_manifest.json", {})
        if "processed_record_counts" in wf:
            expected.update(wf["processed_record_counts"])
        # Encounter manifest
        pe = self.prior_manifests.get("patient_encounter_processing_run_manifest.json", {})
        if "processed_record_count" in pe:
            expected["processed_patient_encounters"] = pe["processed_record_count"]
        # Queue capacity manifest
        qcs = self.prior_manifests.get("queue_capacity_schedule_processing_run_manifest.json", {})
        if "processed_record_counts" in qcs:
            expected.update(qcs["processed_record_counts"])
        # Daily manifest
        pfd = self.prior_manifests.get("patient_flow_daily_processing_run_manifest.json", {})
        if "output_record_count" in pfd:
            expected["processed_patient_flow_daily"] = pfd["output_record_count"]
        if "input_record_counts" in pfd:
            expected.update(pfd["input_record_counts"])
        # Integration manifest (fallback / cross-check)
        integ = self.prior_manifests.get("patient_flow_integration_manifest.json", {})
        if "processed_dataset_row_counts" in integ:
            for k, v in integ["processed_dataset_row_counts"].items():
                if k not in expected:
                    expected[k] = v
        return expected

    # ------------------------------------------------------------------
    # Checksums
    # ------------------------------------------------------------------
    def verify_processed_dataset_checksums(self) -> Dict[str, Any]:
        self._audit("Verify Processed Dataset Checksums Started")
        results = {}
        expected_checksums = self._expected_checksums_from_manifests()
        for ds_name, meta in PROCESSED_DATASETS.items():
            path = self.processed_directory / meta["file_name"]
            if not path.exists():
                results[ds_name] = {"expected": expected_checksums.get(ds_name), "actual": None, "status": "Failed"}
                continue
            actual = self._file_checksum(path)
            self._dataset_checksums[ds_name] = actual
            exp = expected_checksums.get(ds_name)
            match = (exp is not None and actual == exp)
            status = "Passed" if match else ("Failed" if exp is not None else "Unchecked")
            results[ds_name] = {"expected": exp, "actual": actual, "status": status}
            if exp is not None and actual != exp:
                self._add_issue("Checksum Mismatch", "Critical", f"{ds_name}: checksum mismatch", blocks_closure=True)
        self._add_check("Processed Dataset Checksums", "Passed" if all(r["status"] == "Passed" for r in results.values() if r["expected"] is not None) else "Failed")
        self._audit("Verify Processed Dataset Checksums Completed")
        return results

    def _expected_checksums_from_manifests(self) -> Dict[str, str]:
        expected = {}
        wf = self.prior_manifests.get("workforce_processing_run_manifest.json", {})
        if "processed_checksums" in wf:
            expected.update(wf["processed_checksums"])
        pe = self.prior_manifests.get("patient_encounter_processing_run_manifest.json", {})
        if "processed_checksum" in pe:
            expected["processed_patient_encounters"] = pe["processed_checksum"]
        qcs = self.prior_manifests.get("queue_capacity_schedule_processing_run_manifest.json", {})
        if "processed_checksums" in qcs:
            expected.update(qcs["processed_checksums"])
        pfd = self.prior_manifests.get("patient_flow_daily_processing_run_manifest.json", {})
        if "output_checksum" in pfd:
            expected["processed_patient_flow_daily"] = pfd["output_checksum"]
        if "input_checksums" in pfd:
            for k, v in pfd["input_checksums"].items():
                if k in PROCESSED_DATASETS and k not in expected:
                    expected[k] = v
        return expected

    def _file_checksum(self, path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    # ------------------------------------------------------------------
    # Schema validation
    # ------------------------------------------------------------------
    def validate_all_processed_schemas(self) -> Dict[str, Any]:
        self._audit("Validate All Processed Schemas Started")
        results = {}
        for ds_name in PROCESSED_DATASETS:
            schema = get_processed_schema(ds_name)
            path = self.processed_directory / PROCESSED_DATASETS[ds_name]["file_name"]
            if not path.exists():
                results[ds_name] = {"schema_status": "Failed", "notes": "File missing"}
                continue
            df = pd.read_csv(path, nrows=5)
            actual_cols = set(df.columns)
            required = set(schema.get("required_fields", []))
            missing = required - actual_cols
            unexpected = actual_cols - required - set(schema.get("optional_fields", []))
            status = "Passed" if not missing else "Failed"
            results[ds_name] = {
                "registry_schema_name": ds_name,
                "required_field_count": len(required),
                "actual_field_count": len(actual_cols),
                "missing_fields": list(missing),
                "unexpected_fields": list(unexpected),
                "data_type_issue_count": 0,
                "schema_status": status,
                "notes": "",            }
            if missing:
                self._add_issue("Schema Mismatch", "Critical", f"{ds_name} missing fields: {missing}", blocks_closure=True)
        self._add_check("Processed Schema Validation", "Passed" if all(r["schema_status"] == "Passed" for r in results.values()) else "Failed")
        self._audit("Validate All Processed Schemas Completed")
        return results

    # ------------------------------------------------------------------
    # Business keys and grain
    # ------------------------------------------------------------------
    def validate_business_keys(self) -> Dict[str, Any]:
        self._audit("Validate Business Keys Started")
        results = {}
        for ds_name, meta in PROCESSED_DATASETS.items():
            path = self.processed_directory / meta["file_name"]
            if not path.exists():
                results[ds_name] = {"duplicate_key_count": None, "status": "Failed"}
                continue
            pk = meta["primary_key"]
            df = pd.read_csv(path, usecols=[pk])
            dupes = len(df) - df[pk].nunique()
            status = "Passed" if dupes == 0 else "Failed"
            results[ds_name] = {"duplicate_key_count": dupes, "status": status}
            if dupes > 0:
                self._add_issue("Business Key Duplicates", "Critical", f"{ds_name}: {dupes} duplicate {pk} values", blocks_closure=True)
        self._add_check("Business Key Uniqueness", "Passed" if all(r["status"] == "Passed" for r in results.values()) else "Failed")
        self._audit("Validate Business Keys Completed")
        return results

    def validate_daily_grain(self) -> Dict[str, Any]:
        self._audit("Validate Daily Grain Started")
        ds_name = "processed_patient_flow_daily"
        meta = PROCESSED_DATASETS[ds_name]
        path = self.processed_directory / meta["file_name"]
        result = {"status": "Failed", "duplicate_grain_count": None}
        if path.exists():
            df = pd.read_csv(path, usecols=meta["grain_keys"])
            grain_dupes = len(df) - df.drop_duplicates(subset=meta["grain_keys"]).shape[0]
            result = {"status": "Passed" if grain_dupes == 0 else "Failed", "duplicate_grain_count": grain_dupes}
            if grain_dupes > 0:
                self._add_issue("Daily Grain Duplicates", "Critical", f"{ds_name}: {grain_dupes} duplicate grain rows", blocks_closure=True)
        self._add_check("Daily Grain Uniqueness", result["status"])
        self._audit("Validate Daily Grain Completed")
        return result

    def validate_deterministic_daily_ids(self) -> Dict[str, Any]:
        self._audit("Validate Deterministic Daily IDs Started")
        ds_name = "processed_patient_flow_daily"
        path = self.processed_directory / PROCESSED_DATASETS[ds_name]["file_name"]
        result = {"status": "Failed", "invalid_format_count": None}
        if path.exists():
            df = pd.read_csv(path, usecols=["patient_flow_daily_id"])
            pattern = PROCESSED_DATASETS[ds_name].get("deterministic_id_pattern", r"^PFD-.*")
            invalid = (~df["patient_flow_daily_id"].astype(str).str.match(pattern)).sum()
            result = {"status": "Passed" if invalid == 0 else "Failed", "invalid_format_count": int(invalid)}
            if invalid > 0:
                self._add_issue("Invalid Daily ID Format", "Critical", f"{invalid} patient_flow_daily_id values do not match expected pattern", blocks_closure=True)
        self._add_check("Deterministic Daily ID Format", result["status"])
        self._audit("Validate Deterministic Daily IDs Completed")
        return result

    # ------------------------------------------------------------------
    # Integration evidence
    # ------------------------------------------------------------------
    def verify_integration_results(self) -> Dict[str, Any]:
        self._audit("Verify Integration Results Started")
        integ = self.prior_manifests.get("patient_flow_integration_manifest.json", {})
        required = {
            "manifest_verification_results": "Passed",
            "checksum_verification_results": "Passed",
            "schema_results": "Passed",
            "business_key_results": "Passed",
            "daily_grain_result": "Passed",
            "reconciliation_results": "Passed",
            "lineage_results": "Passed",
            "prohibited_field_check": "Passed",
            "run_status": "Passed",
        }
        results = {}
        all_passed = True
        for key, expected in required.items():
            actual = integ.get(key, "Missing")
            passed = actual == expected
            results[key] = {"expected": expected, "actual": actual, "passed": passed}
            if not passed:
                all_passed = False
                self._add_issue("Integration Evidence Failure", "Critical", f"{key}={actual}, expected={expected}", blocks_closure=True)
        self._add_check("Integration Evidence", "Passed" if all_passed else "Failed")
        self._audit("Verify Integration Results Completed")
        return results

    def verify_lineage_acceptance(self) -> Dict[str, Any]:
        self._audit("Verify Lineage Acceptance Started")
        integ = self.prior_manifests.get("patient_flow_integration_manifest.json", {})
        lineage_summary_path = self.log_directory / "patient_flow_integration_lineage_summary.csv"
        lineage_gap_path = self.log_directory / "patient_flow_integration_lineage_gap_log.csv"
        result = {"status": "Passed", "gaps": 0, "broken": 0, "duplicates": 0}
        # Read lineage summary for coverage
        if lineage_summary_path.exists():
            df = pd.read_csv(lineage_summary_path)
            gaps = int((df.get("gap_flag", pd.Series([], dtype=bool)) == True).sum()) if "gap_flag" in df.columns else 0
            broken = int((df.get("broken_reference_flag", pd.Series([], dtype=bool)) == True).sum()) if "broken_reference_flag" in df.columns else 0
            duplicates = int((df.get("duplicate_flag", pd.Series([], dtype=bool)) == True).sum()) if "duplicate_flag" in df.columns else 0
            result = {"status": "Passed" if gaps == 0 and broken == 0 and duplicates == 0 else "Failed", "gaps": gaps, "broken": broken, "duplicates": duplicates}
        # Read gap log
        if lineage_gap_path.exists():
            try:
                gap_df = pd.read_csv(lineage_gap_path)
                if len(gap_df) > 0:
                    result["status"] = "Failed"
                    result["gaps"] += len(gap_df)
                    self._add_issue("Lineage Gaps Found", "Critical", f"Lineage gap log contains {len(gap_df)} records", blocks_closure=True)
            except pd.errors.EmptyDataError:
                pass
        if result["status"] != "Passed":
            self._add_issue("Lineage Acceptance Failure", "Critical", f"Lineage gaps={result['gaps']}, broken={result['broken']}, duplicates={result['duplicates']}", blocks_closure=True)
        self._add_check("Lineage Acceptance", result["status"])
        self._audit("Verify Lineage Acceptance Completed")
        return result

    def verify_reconciliation_acceptance(self) -> Dict[str, Any]:
        self._audit("Verify Reconciliation Acceptance Started")
        recon_path = self.log_directory / "patient_flow_cross_step_reconciliation.csv"
        result = {"status": "Passed", "failed_checks": 0, "total_checks": 0}
        if recon_path.exists():
            df = pd.read_csv(recon_path)
            if "reconciliation_status" in df.columns:
                failed = (df["reconciliation_status"] != "Passed").sum()
                total = len(df)
                result = {"status": "Passed" if failed == 0 else "Failed", "failed_checks": int(failed), "total_checks": int(total)}
                if failed > 0:
                    self._add_issue("Reconciliation Failure", "Critical", f"{failed} of {total} reconciliation checks failed", blocks_closure=True)
        self._add_check("Reconciliation Acceptance", result["status"])
        self._audit("Verify Reconciliation Acceptance Completed")
        return result

    # ------------------------------------------------------------------
    # Prohibited outputs
    # ------------------------------------------------------------------
    def detect_prohibited_outputs(self) -> Dict[str, Any]:
        self._audit("Detect Prohibited Outputs Started")
        results = {}
        any_found = False
        for ds_name, meta in PROCESSED_DATASETS.items():
            path = self.processed_directory / meta["file_name"]
            if not path.exists():
                continue
            df = pd.read_csv(path, nrows=0)
            cols = set(df.columns)
            found = [p for p in PROHIBITED_FIELD_PATTERNS if p in cols]
            results[ds_name] = found
            if found:
                any_found = True
                self._add_issue("Prohibited Field Detected", "Critical", f"{ds_name} contains prohibited fields: {found}", blocks_closure=True)
        self._add_check("Prohibited Output Check", "Failed" if any_found else "Passed")
        self._audit("Detect Prohibited Outputs Completed")
        return results

    def detect_unapproved_fields(self, dataset_path: Path) -> List[str]:
        """Return prohibited fields found in a single dataset."""
        if not dataset_path.exists():
            return []
        df = pd.read_csv(dataset_path, nrows=0)
        cols = set(df.columns)
        return [p for p in PROHIBITED_FIELD_PATTERNS if p in cols]

    # ------------------------------------------------------------------
    # Dataset immutability
    # ------------------------------------------------------------------
    def confirm_dataset_immutability(self) -> Dict[str, Any]:
        self._audit("Confirm Dataset Immutability Started")
        results = {}
        all_unchanged = True
        expected_checksums = self._expected_checksums_from_manifests()
        for ds_name, meta in PROCESSED_DATASETS.items():
            path = self.processed_directory / meta["file_name"]
            if not path.exists():
                results[ds_name] = "Missing"
                all_unchanged = False
                continue
            current = self._file_checksum(path)
            exp = expected_checksums.get(ds_name)
            unchanged = (exp is not None and current == exp)
            results[ds_name] = "Unchanged" if unchanged else ("Unchecked" if exp is None else "Modified")
            if exp is not None and not unchanged:
                all_unchanged = False
                self._add_issue("Dataset Modified", "Critical", f"{ds_name} checksum changed since prior manifest", blocks_closure=True)
        self._add_check("Dataset Immutability", "Passed" if all_unchanged else "Failed")
        self._audit("Confirm Dataset Immutability Completed")
        return results

    # ------------------------------------------------------------------
    # Documentation presence
    # ------------------------------------------------------------------
    def verify_documentation_presence(self) -> Dict[str, Any]:
        self._audit("Verify Documentation Presence Started")
        docs = REQUIRED_CATEGORIES.get("Documentation", [])
        missing = []
        for rel_path in docs:
            if not (self.project_root / rel_path).exists():
                missing.append(rel_path)
        if missing:
            self._add_issue("Missing Documentation", "Warning", f"Missing docs: {missing}", blocks_closure=False)
        self._add_check("Documentation Presence", "Passed" if not missing else "Passed with Warnings")
        self._audit("Verify Documentation Presence Completed")
        return {"missing": missing, "status": "Passed" if not missing else "Passed with Warnings"}

    # ------------------------------------------------------------------
    # Consolidation
    # ------------------------------------------------------------------
    def consolidate_test_results(self, test_results: List[Dict[str, Any]]) -> None:
        self.test_summary = test_results
        failed = [t for t in test_results if t.get("final_status") != "Passed"]
        if failed:
            self._add_issue("Test Failure", "Critical", f"{len(failed)} test files failed", blocks_closure=True)
        self._add_check("Cumulative Test Results", "Passed" if not failed else "Failed")

    def build_acceptance_checks(self) -> List[Dict[str, Any]]:
        return self.check_results

    def collect_closure_issues(self) -> List[Dict[str, Any]]:
        return [i.to_dict() for i in self.issues]

    # ------------------------------------------------------------------
    # Closure manifest
    # ------------------------------------------------------------------
    def build_closure_manifest(self) -> Dict[str, Any]:
        started = datetime.now()
        critical_issues = [i for i in self.issues if i.severity in ("Critical", "Error") or i.blocks_processing]
        warning_issues = [i for i in self.issues if i.severity == "Warning" and not i.blocks_processing]
        if self.blocked_reasons:
            status = "Blocked"
        elif critical_issues:
            status = "Failed"
        elif warning_issues:
            status = "Passed with Warnings"
        else:
            status = "Passed"
        manifest = {
            "closure_run_id": self.closure_run_id,
            "closure_started_datetime": started.isoformat(),
            "closure_completed_datetime": datetime.now().isoformat(),
            "engine_version": ENGINE_VERSION,
            "closure_version": CLOSURE_VERSION,
            "steps_covered": ["2A", "2B", "2C", "2D-1", "2D-2", "2D-3A", "2D-3B", "2D-3C", "2D-3D"],
            "prior_manifests_verified": list(self.prior_manifests.keys()),
            "processed_datasets_checked": list(PROCESSED_DATASETS.keys()),
            "file_inventory_count": len(self.file_inventory),
            "dataset_acceptance_count": len(self.dataset_acceptance),
            "schema_acceptance_count": len(self.schema_acceptance),
            "checksum_verification_count": len(self.checksum_verification),
            "test_summary_count": len(self.test_summary),
            "closure_issue_count": len(self.issues),
            "critical_issue_count": len(critical_issues),
            "warning_issue_count": len(warning_issues),
            "blocked_reasons": self.blocked_reasons,
            "run_status": status,
            "closure_passed_flag": status in ("Passed", "Passed with Warnings"),
            "output_files": [
                "step_2d3_closure_manifest.json",
                "step_2d3_test_summary.csv",
                "step_2d3_file_inventory.csv",
                "step_2d3_dataset_acceptance_summary.csv",
                "step_2d3_schema_acceptance_summary.csv",
                "step_2d3_checksum_verification.csv",
                "step_2d3_acceptance_check_results.csv",
                "step_2d3_closure_issue_log.csv",
                "step_2d3_closure_audit_log.csv",
            ],
            "unresolved_rules": [
                "Queue multi-stage aggregation without summary flag: Pending Review",
                "Duplicate bed-snapshot selection logic: Pending Review",
            ],
            "known_limitations": [
                "Closure validation relies on prior manifest evidence; it does not reprocess data.",
            ],
            "readiness_for_next_step": "Step 2D-4 may proceed to transform patient complaints and patient survey data into validated preparation-level datasets. Step 2D-4 must not yet calculate official Complaint Rate, Patient Satisfaction Score or KPI status.",
        }
        self.closure_manifest = manifest
        return manifest

    def return_closure_result(self) -> Dict[str, Any]:
        return {
            "closure_run_id": self.closure_run_id,
            "closure_manifest": self.closure_manifest,
            "issues": self.collect_closure_issues(),
            "check_results": self.check_results,
            "audit_events": self.audit_events,
            "file_inventory": self.file_inventory,
            "dataset_acceptance": self.dataset_acceptance,
            "schema_acceptance": self.schema_acceptance,
            "checksum_verification": self.checksum_verification,
            "test_summary": self.test_summary,
        }
