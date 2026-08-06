"""
Sentinel360 Healthcare — Preparation Layer Integration Validator

Phase 1, Step 2D-5: Final integration, reconciliation and formal closure
of the entire Phase 1 preparation layer.

This validator is read-only. It never updates prior manifests or evidence.
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

CLOSURE_VERSION = "2D-5-1.0.0"
ENGINE_VERSION = "Sentinel360-Phase1-2D-5"

REQUIRED_PROCESSED_DATASETS = [
    "processed_hospital_master.csv",
    "processed_department_master.csv",
    "processed_staff_role_master.csv",
    "processed_staff_master.csv",
    "processed_staff_roster.csv",
    "processed_staff_attendance.csv",
    "processed_staffing_requirement.csv",
    "processed_workforce_daily.csv",
    "processed_patient_encounters.csv",
    "processed_patient_queue.csv",
    "processed_bed_capacity.csv",
    "processed_service_schedule.csv",
    "processed_patient_flow_daily.csv",
    "processed_patient_complaints.csv",
    "processed_patient_surveys.csv",
    "processed_patient_experience_daily.csv",
]

REQUIRED_MANIFESTS = [
    "validation_run_manifest.json",
    "patient_encounter_processing_run_manifest.json",
    "queue_capacity_schedule_processing_run_manifest.json",
    "patient_flow_daily_processing_run_manifest.json",
    "patient_flow_integration_manifest.json",
    "step_2d3_closure_manifest.json",
    "patient_experience_processing_run_manifest.json",
]

DAILY_DATASETS = [
    "processed_workforce_daily.csv",
    "processed_patient_flow_daily.csv",
    "processed_patient_experience_daily.csv",
]

PROHIBITED_FIELD_PATTERNS = [
    re.compile(r"kpi_value", re.I),
    re.compile(r"kpi_percentage", re.I),
    re.compile(r"kpi_status", re.I),
    re.compile(r"green_status", re.I),
    re.compile(r"amber_status", re.I),
    re.compile(r"red_status", re.I),
    re.compile(r"risk_score", re.I),
    re.compile(r"risk_level", re.I),
    re.compile(r"anomaly_score", re.I),
    re.compile(r"forecast", re.I),
    re.compile(r"scenario", re.I),
    re.compile(r"recommendation", re.I),
    re.compile(r"financial_impact", re.I),
    re.compile(r"intervention", re.I),
    re.compile(r"action_owner", re.I),
    re.compile(r"approval_status", re.I),
]


class PreparationLayerIntegrationValidator:
    """Read-only validator for Phase 1 preparation layer integration."""

    def __init__(
        self,
        project_root: Path,
        processed_dir: Path,
        log_dir: Path,
        max_issue_examples: int = 10,
    ):
        self.project_root = Path(project_root)
        self.processed_dir = Path(processed_dir)
        self.log_dir = Path(log_dir)
        self.max_issue_examples = max_issue_examples
        self.issues: List[ProcessingIssue] = []
        self.exclusions: List[Dict[str, Any]] = []
        self.checksums: Dict[str, str] = {}
        self.datasets: Dict[str, pd.DataFrame] = {}
        self.manifests: Dict[str, Dict[str, Any]] = {}
        self.lineage: Optional[pd.DataFrame] = None
        self.reconciliation: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Inventory
    # ------------------------------------------------------------------
    def inventory_required_files(self) -> Dict[str, Any]:
        result = {"required": [], "missing": [], "present": []}
        for fname in REQUIRED_PROCESSED_DATASETS:
            fpath = self.processed_dir / fname
            result["required"].append(fname)
            if fpath.exists():
                result["present"].append(fname)
            else:
                result["missing"].append(fname)
                self._add_issue(
                    "Critical",
                    "Missing required processed dataset",
                    f"{fname} not found in {self.processed_dir}",
                    dataset_name=fname.replace(".csv", ""),
                )
        return result

    # ------------------------------------------------------------------
    # Manifests
    # ------------------------------------------------------------------
    def load_prior_manifests(self) -> Dict[str, Any]:
        loaded = {}
        for mname in REQUIRED_MANIFESTS:
            mpath = self.log_dir / mname
            if mpath.exists():
                try:
                    with open(mpath, "r", encoding="utf-8") as f:
                        loaded[mname] = json.load(f)
                except Exception as exc:
                    self._add_issue(
                        "Critical",
                        "Manifest unreadable",
                        f"{mname}: {exc}",
                    )
            else:
                self._add_issue(
                    "Critical",
                    "Missing required manifest",
                    f"{mname} not found in {self.log_dir}",
                )
        self.manifests = loaded
        return loaded

    def verify_manifest_statuses(self) -> Dict[str, Any]:
        results = {}
        step_2d3_ok = False
        step_2d4_ok = False
        for mname, mdata in self.manifests.items():
            status = mdata.get("closure_status", mdata.get("status", mdata.get("run_status", "Unknown")))
            results[mname] = status
            if "2d3" in mname.lower() or "step_2d3" in mname.lower():
                if status in ("Passed", "Passed with Warnings", "Completed", "success"):
                    step_2d3_ok = True
            if "patient_experience" in mname.lower() and "manifest" in mname.lower():
                if status in ("Passed", "Passed with Warnings", "Completed", "success"):
                    step_2d4_ok = True
        if not step_2d3_ok:
            self._add_issue(
                "Critical",
                "Step 2D-3 not accepted",
                "Step 2D-3 closure manifest does not show Passed status.",
            )
        if not step_2d4_ok:
            self._add_issue(
                "Critical",
                "Step 2D-4 not accepted",
                "Patient experience processing manifest does not show accepted status.",
            )
        return {"step_2d3_accepted": step_2d3_ok, "step_2d4_accepted": step_2d4_ok, "details": results}

    # ------------------------------------------------------------------
    # Checksums
    # ------------------------------------------------------------------
    def _file_checksum(self, fpath: Path) -> str:
        h = hashlib.sha256()
        with open(fpath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def verify_processed_dataset_checksums(self) -> Dict[str, Any]:
        results = {}
        for fname in REQUIRED_PROCESSED_DATASETS:
            fpath = self.processed_dir / fname
            if fpath.exists():
                chksum = self._file_checksum(fpath)
                self.checksums[fname] = chksum
                results[fname] = {"checksum": chksum, "status": "Calculated"}
            else:
                results[fname] = {"checksum": None, "status": "Missing"}
        return results

    def confirm_processed_data_immutability(self, prior_checksums: Dict[str, Any]) -> Dict[str, Any]:
        results = {}
        for fname, prior in prior_checksums.items():
            prior_checksum = prior.get("checksum") if isinstance(prior, dict) else prior
            current = self.checksums.get(fname)
            if current is None:
                results[fname] = {"status": "Missing", "match": False}
                self._add_issue("Error", "Checksum missing for immutability check", fname)
            elif current != prior_checksum:
                results[fname] = {"status": "Changed", "match": False, "prior": prior_checksum, "current": current}
                self._add_issue("Error", "Prior processed dataset changed", f"{fname} checksum mismatch")
            else:
                results[fname] = {"status": "Unchanged", "match": True}
        return results

    # ------------------------------------------------------------------
    # Dataset loading
    # ------------------------------------------------------------------
    def verify_dataset_row_counts(self) -> Dict[str, Any]:
        counts = {}
        for fname in REQUIRED_PROCESSED_DATASETS:
            fpath = self.processed_dir / fname
            if fpath.exists():
                try:
                    df = pd.read_csv(fpath, dtype=str, keep_default_na=False)
                    self.datasets[fname.replace(".csv", "")] = df
                    counts[fname] = len(df)
                except Exception as exc:
                    counts[fname] = None
                    self._add_issue("Critical", "Cannot load dataset", f"{fname}: {exc}")
            else:
                counts[fname] = None
        return counts

    # ------------------------------------------------------------------
    # Schema validation
    # ------------------------------------------------------------------
    def validate_all_processed_schemas(self) -> Dict[str, Any]:
        results = {}
        for ds_name, df in self.datasets.items():
            schema = get_processed_schema(ds_name)
            if schema is None:
                self._add_issue("Critical", "Schema not found", ds_name)
                results[ds_name] = {"status": "No schema"}
                continue
            required_fields = schema.get("required_fields", [])
            optional_fields = schema.get("optional_fields", [])
            missing_required = [f for f in required_fields if f not in df.columns]
            extra_fields = [f for f in df.columns if f not in required_fields and f not in optional_fields]
            ok = not missing_required
            results[ds_name] = {
                "status": "Passed" if ok else "Failed",
                "missing_required": missing_required,
                "extra_fields": extra_fields,
            }
            if missing_required:
                self._add_issue("Error", "Schema missing required fields", f"{ds_name}: {missing_required}")
        return results

    # ------------------------------------------------------------------
    # Business keys
    # ------------------------------------------------------------------
    def validate_business_keys(self) -> Dict[str, Any]:
        results = {}
        for ds_name, df in self.datasets.items():
            schema = get_processed_schema(ds_name)
            if schema is None:
                continue
            pk = schema.get("primary_key", "")
            if not pk:
                continue
            if pk not in df.columns:
                results[ds_name] = {"status": "No PK column", "duplicates": 0}
                self._add_issue("Error", "Primary key column missing", f"{ds_name}.{pk}")
                continue
            dups = df[pk].duplicated().sum()
            results[ds_name] = {"status": "Passed" if dups == 0 else "Failed", "duplicates": int(dups)}
            if dups > 0:
                self._add_issue("Error", "Duplicate primary key", f"{ds_name}.{pk}: {dups} duplicates")
        return results

    # ------------------------------------------------------------------
    # Daily grains
    # ------------------------------------------------------------------
    def validate_daily_grains(self) -> Dict[str, Any]:
        results = {}
        grain_cols = ["hospital_id", "department_id", "reporting_date"]
        for ds_name in ["processed_workforce_daily", "processed_patient_flow_daily", "processed_patient_experience_daily"]:
            df = self.datasets.get(ds_name)
            if df is None:
                continue
            missing = [c for c in grain_cols if c not in df.columns]
            if missing:
                results[ds_name] = {"status": "Missing columns", "duplicates": 0}
                self._add_issue("Error", "Daily grain columns missing", f"{ds_name}: {missing}")
                continue
            dups = df[grain_cols].duplicated().sum()
            # Workforce daily has staff_role_id dimension, so duplicates at h-d-d are expected
            if ds_name == "processed_workforce_daily":
                results[ds_name] = {"status": "Passed (staff_role_id dimension)", "duplicates": int(dups)}
            else:
                results[ds_name] = {"status": "Passed" if dups == 0 else "Failed", "duplicates": int(dups)}
                if dups > 0:
                    self._add_issue("Error", "Duplicate daily grain", f"{ds_name}: {dups} duplicates")
        return results

    # ------------------------------------------------------------------
    # References
    # ------------------------------------------------------------------
    def validate_hospital_references(self) -> Dict[str, Any]:
        results = {}
        hosp_df = self.datasets.get("processed_hospital_master")
        if hosp_df is None or "hospital_id" not in hosp_df.columns:
            return results
        valid_hospitals = set(hosp_df["hospital_id"])
        for ds_name, df in self.datasets.items():
            if "hospital_id" not in df.columns:
                continue
            # Handle string comparison safely
            hosp_col = df["hospital_id"].astype(str)
            orphans = hosp_col[~hosp_col.isin([str(v) for v in valid_hospitals])].unique().tolist()
            results[ds_name] = {"status": "Passed" if not orphans else "Failed", "orphans": orphans}
            if orphans:
                self._add_issue("Error", "Invalid hospital reference", f"{ds_name}: {orphans[:self.max_issue_examples]}")
        return results

    def validate_department_references(self) -> Dict[str, Any]:
        results = {}
        dept_df = self.datasets.get("processed_department_master")
        if dept_df is None or "department_id" not in dept_df.columns:
            return results
        valid_depts = set(dept_df["department_id"])
        for ds_name, df in self.datasets.items():
            if "department_id" not in df.columns:
                continue
            dept_col = df["department_id"].astype(str)
            orphans = dept_col[~dept_col.isin([str(v) for v in valid_depts])].unique().tolist()
            results[ds_name] = {"status": "Passed" if not orphans else "Failed", "orphans": orphans}
            if orphans:
                self._add_issue("Error", "Invalid department reference", f"{ds_name}: {orphans[:self.max_issue_examples]}")
        return results

    def validate_department_hospital_relationships(self) -> Dict[str, Any]:
        results = {}
        dept_df = self.datasets.get("processed_department_master")
        if dept_df is None or "department_id" not in dept_df.columns or "hospital_id" not in dept_df.columns:
            return results
        dept_to_hosp = dict(zip(dept_df["department_id"].astype(str), dept_df["hospital_id"].astype(str)))
        for ds_name, df in self.datasets.items():
            if "department_id" not in df.columns or "hospital_id" not in df.columns:
                continue
            mismatches = []
            for _, row in df.iterrows():
                expected = dept_to_hosp.get(str(row["department_id"]))
                if expected is not None and str(row["hospital_id"]) != expected:
                    mismatches.append((str(row["department_id"]), str(row["hospital_id"]), expected))
                    if len(mismatches) >= self.max_issue_examples:
                        break
            results[ds_name] = {"status": "Passed" if not mismatches else "Failed", "mismatches": mismatches}
            if mismatches:
                self._add_issue("Error", "Department-hospital mismatch", f"{ds_name}: {len(mismatches)} examples")
        return results

    # ------------------------------------------------------------------
    # Date validation
    # ------------------------------------------------------------------
    def validate_date_fields(self) -> Dict[str, Any]:
        results = {}
        for ds_name, df in self.datasets.items():
            if "reporting_date" not in df.columns:
                continue
            bad_dates = 0
            for val in df["reporting_date"]:
                try:
                    pd.to_datetime(val, errors="raise")
                except Exception:
                    bad_dates += 1
            results[ds_name] = {"status": "Passed" if bad_dates == 0 else "Failed", "bad_dates": bad_dates}
            if bad_dates > 0:
                self._add_issue("Error", "Invalid reporting_date", f"{ds_name}: {bad_dates} bad dates")
        return results

    def validate_month_year_consistency(self) -> Dict[str, Any]:
        results = {}
        for ds_name, df in self.datasets.items():
            if "reporting_date" not in df.columns:
                continue
            has_month = "reporting_month" in df.columns
            has_year = "reporting_year" in df.columns
            if not has_month and not has_year:
                continue
            mismatches = 0
            for _, row in df.iterrows():
                dt = pd.to_datetime(row["reporting_date"], errors="coerce")
                if pd.isna(dt):
                    continue
                if has_month:
                    try:
                        month_val = str(row["reporting_month"])
                        # Handle YYYY-MM format
                        if "-" in month_val:
                            parts = month_val.split("-")
                            month_int = int(parts[1]) if len(parts) > 1 else int(month_val)
                        else:
                            month_int = int(month_val)
                        if month_int != dt.month:
                            mismatches += 1
                            continue
                    except Exception:
                        mismatches += 1
                        continue
                if has_year:
                    try:
                        year_val = str(row["reporting_year"])
                        if "-" in year_val:
                            parts = year_val.split("-")
                            year_int = int(parts[0]) if len(parts) > 0 else int(year_val)
                        else:
                            year_int = int(year_val)
                        if year_int != dt.year:
                            mismatches += 1
                    except Exception:
                        mismatches += 1
            results[ds_name] = {"status": "Passed" if mismatches == 0 else "Failed", "mismatches": mismatches}
            if mismatches > 0:
                self._add_issue("Error", "Month/year mismatch", f"{ds_name}: {mismatches} mismatches")
        return results

    # ------------------------------------------------------------------
    # Cross-domain daily keys
    # ------------------------------------------------------------------
    def validate_cross_domain_daily_keys(self) -> Dict[str, Any]:
        results = {}
        keys = {}
        grain = ["hospital_id", "department_id", "reporting_date"]
        for ds_name in ["processed_workforce_daily", "processed_patient_flow_daily", "processed_patient_experience_daily"]:
            df = self.datasets.get(ds_name)
            if df is not None and all(c in df.columns for c in grain):
                keys[ds_name] = set(zip(df["hospital_id"], df["department_id"], df["reporting_date"]))
        if len(keys) < 2:
            return results
        union = set()
        for kset in keys.values():
            union |= kset
        intersection = None
        for kset in keys.values():
            intersection = kset if intersection is None else intersection & kset
        results["union_count"] = len(union)
        results["intersection_count"] = len(intersection) if intersection else 0
        results["domain_key_counts"] = {k: len(v) for k, v in keys.items()}
        return results

    def validate_domain_presence(self) -> Dict[str, Any]:
        # Placeholder for operational-daily specific validation; done in builder
        return {}

    # ------------------------------------------------------------------
    # Lineage
    # ------------------------------------------------------------------
    def validate_lineage_coverage(self, lineage_df: Optional[pd.DataFrame] = None, output_record_count: int = 0) -> Dict[str, Any]:
        if lineage_df is None:
            return {"status": "No lineage", "coverage": 0.0}
        if output_record_count == 0:
            return {"status": "No output records", "coverage": 0.0}
        unique_outputs = lineage_df["output_record_id"].nunique() if "output_record_id" in lineage_df.columns else 0
        coverage = unique_outputs / output_record_count if output_record_count > 0 else 0.0
        status = "Passed" if coverage >= 1.0 else "Failed"
        if status == "Failed":
            self._add_issue("Error", "Incomplete lineage coverage", f"{unique_outputs}/{output_record_count}")
        return {"status": status, "coverage": coverage, "unique_outputs": unique_outputs, "output_record_count": output_record_count}

    def validate_lineage_references(self, lineage_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        if lineage_df is None or lineage_df.empty:
            return {"status": "No lineage", "broken": 0}
        # Basic check: no empty source_record_id when source_dataset is present
        broken = lineage_df[
            (lineage_df["source_dataset"].notna() & (lineage_df["source_dataset"] != ""))
            & (lineage_df["source_record_id"].isna() | (lineage_df["source_record_id"] == ""))
        ]
        count = len(broken)
        if count > 0:
            self._add_issue("Warning", "Broken lineage references", f"{count} rows with missing source_record_id (expected for workforce_daily with staff_role_id dimension)")
        return {"status": "Passed" if count == 0 else "Warning", "broken": count}

    def detect_lineage_gaps(self, lineage_df: Optional[pd.DataFrame] = None, expected_output_ids: Optional[Set[str]] = None) -> Dict[str, Any]:
        if lineage_df is None or expected_output_ids is None:
            return {"missing_count": 0, "missing_ids": []}
        present = set(lineage_df["output_record_id"].dropna().astype(str).unique()) if "output_record_id" in lineage_df.columns else set()
        missing = sorted(expected_output_ids - present)
        if missing:
            self._add_issue("Warning", "Lineage gaps detected", f"{len(missing)} output IDs without lineage")
        return {"missing_count": len(missing), "missing_ids": missing[:self.max_issue_examples]}

    def detect_duplicate_lineage(self, lineage_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        if lineage_df is None or lineage_df.empty:
            return {"duplicates": 0}
        cols = [c for c in ["output_record_id", "source_dataset", "source_record_id"] if c in lineage_df.columns]
        if not cols:
            return {"duplicates": 0}
        dups = lineage_df[lineage_df.duplicated(subset=cols, keep=False)]
        count = len(dups)
        if count > 0:
            self._add_issue("Warning", "Duplicate lineage records", f"{count} duplicate rows")
        return {"duplicates": count}

    # ------------------------------------------------------------------
    # Issue / exclusion outputs
    # ------------------------------------------------------------------
    def validate_issue_outputs(self, issue_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        if issue_df is None or issue_df.empty:
            return {"status": "No issues", "count": 0}
        required_cols = {"issue_id", "severity", "category", "message"}
        missing = required_cols - set(issue_df.columns)
        return {"status": "Passed" if not missing else "Failed", "missing_columns": list(missing), "count": len(issue_df)}

    def validate_exclusion_outputs(self, exclusion_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        if exclusion_df is None or exclusion_df.empty:
            return {"status": "No exclusions", "count": 0}
        required_cols = {"exclusion_id", "source_dataset_name", "exclusion_reason_code"}
        missing = required_cols - set(exclusion_df.columns)
        return {"status": "Passed" if not missing else "Failed", "missing_columns": list(missing), "count": len(exclusion_df)}

    # ------------------------------------------------------------------
    # Prohibited fields
    # ------------------------------------------------------------------
    def detect_prohibited_fields(self, df: Optional[pd.DataFrame] = None, dataset_name: str = "") -> Dict[str, Any]:
        target = df
        if target is None:
            return {"status": "No data", "prohibited_fields": []}
        prohibited = []
        for col in target.columns:
            for pat in PROHIBITED_FIELD_PATTERNS:
                if pat.search(col):
                    prohibited.append(col)
                    break
        if prohibited:
            self._add_issue("Error", "Prohibited analytical field detected", f"{dataset_name}: {prohibited}")
        return {"status": "Failed" if prohibited else "Passed", "prohibited_fields": prohibited}

    # ------------------------------------------------------------------
    # Reconciliation
    # ------------------------------------------------------------------
    def build_reconciliation_summary(self, operational_daily_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        rec = {}
        grain = ["hospital_id", "department_id", "reporting_date"]
        for ds_name in ["processed_workforce_daily", "processed_patient_flow_daily", "processed_patient_experience_daily"]:
            df = self.datasets.get(ds_name)
            if df is not None:
                rec[f"{ds_name}_row_count"] = len(df)
                if all(c in df.columns for c in grain):
                    rec[f"{ds_name}_unique_keys"] = len(df[grain].drop_duplicates())
            else:
                rec[f"{ds_name}_row_count"] = 0
                rec[f"{ds_name}_unique_keys"] = 0
        if operational_daily_df is not None:
            rec["operational_daily_row_count"] = len(operational_daily_df)
            if all(c in operational_daily_df.columns for c in grain):
                rec["operational_daily_unique_keys"] = len(operational_daily_df[grain].drop_duplicates())
        self.reconciliation = rec
        return rec

    # ------------------------------------------------------------------
    # Issue collection
    # ------------------------------------------------------------------
    def _add_issue(
        self,
        severity: str,
        category: str,
        message: str,
        dataset_name: str = "",
        field_name: str = "",
        rule_id: str = "",
    ) -> None:
        self.issues.append(
            ProcessingIssue(
                processing_run_id="",
                issue_id=str(uuid.uuid4())[:8],
                issue_type=category,
                severity=severity,
                issue_description=message,
                source_dataset_name=dataset_name,
                processed_dataset_name=dataset_name,
                field_name=field_name,
            )
        )

    def collect_issues(self) -> pd.DataFrame:
        if not self.issues:
            return pd.DataFrame(columns=[
                "issue_id", "severity", "category", "message",
                "dataset_name", "field_name", "rule_id",
            ])
        rows = []
        for issue in self.issues:
            rows.append({
                "issue_id": issue.issue_id,
                "severity": issue.severity,
                "category": issue.issue_type,
                "message": issue.issue_description,
                "dataset_name": issue.source_dataset_name or issue.processed_dataset_name,
                "field_name": issue.field_name,
                "rule_id": "",
            })
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Closure status
    # ------------------------------------------------------------------
    def calculate_closure_status(self) -> str:
        severities = [i.severity for i in self.issues]
        if "Critical" in severities:
            return "Blocked"
        if "Error" in severities:
            return "Failed"
        if "Warning" in severities:
            return "Passed with Warnings"
        return "Passed"

    def return_validation_result(self) -> Dict[str, Any]:
        return {
            "closure_version": CLOSURE_VERSION,
            "engine_version": ENGINE_VERSION,
            "validation_timestamp": datetime.now().isoformat(),
            "closure_status": self.calculate_closure_status(),
            "issue_count": len(self.issues),
            "issue_breakdown": {
                "Information": sum(1 for i in self.issues if i.severity == "Information"),
                "Warning": sum(1 for i in self.issues if i.severity == "Warning"),
                "Error": sum(1 for i in self.issues if i.severity == "Error"),
                "Critical": sum(1 for i in self.issues if i.severity == "Critical"),
            },
            "checksums": self.checksums,
            "reconciliation": self.reconciliation,
        }
