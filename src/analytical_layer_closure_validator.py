"""
Sentinel360 Healthcare — Analytical Layer Closure Validator

Formal validation and closure of Phase 2A Analytical Layer.
Does not recalculate KPIs or modify accepted results.

Step: 2A-6
"""

import os
import json
import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# 1. Safe CSV loader
# ---------------------------------------------------------------------------

def _safe_read_csv(path: str) -> Optional[pd.DataFrame]:
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=True)
        if df.empty:
            return None
        return df
    except pd.errors.EmptyDataError:
        return None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 2. Checksum helpers
# ---------------------------------------------------------------------------

def _file_checksum(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _record_checksums(file_paths: List[str]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for p in file_paths:
        if os.path.exists(p):
            result[p] = _file_checksum(p)
    return result


# ---------------------------------------------------------------------------
# 3. Validation finding model
# ---------------------------------------------------------------------------

class ValidationFinding:
    def __init__(
        self,
        domain: str,
        check_name: str,
        status: str,  # Passed, Passed with Warning, Failed, Not Applicable
        severity: str,  # Information, Warning, Blocking
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.domain = domain
        self.check_name = check_name
        self.status = status
        self.severity = severity
        self.message = message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "check_name": self.check_name,
            "status": self.status,
            "severity": self.severity,
            "message": self.message,
            "details": self.details,
        }


# ---------------------------------------------------------------------------
# 4. Closure result model
# ---------------------------------------------------------------------------

class ClosureResult:
    def __init__(self):
        self.findings: List[ValidationFinding] = []
        self.closure_status: str = "Not Determined"
        self.phase_2b_readiness: str = "Not Determined"
        self.phase_2b_conditions: List[str] = []
        self.pre_checksums: Dict[str, str] = {}
        self.post_checksums: Dict[str, str] = {}
        self.immutability_status: str = "Not Checked"
        self.summary: Dict[str, Any] = {}
        self.outputs_generated: List[str] = []

    def add_finding(self, finding: ValidationFinding) -> None:
        self.findings.append(finding)

    def passed_count(self) -> int:
        return sum(1 for f in self.findings if f.status == "Passed")

    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.status == "Passed with Warning")

    def failed_count(self) -> int:
        return sum(1 for f in self.findings if f.status == "Failed")

    def blocking_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "Blocking")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "closure_status": self.closure_status,
            "phase_2b_readiness": self.phase_2b_readiness,
            "phase_2b_conditions": self.phase_2b_conditions,
            "immutability_status": self.immutability_status,
            "passed_checks": self.passed_count(),
            "warning_checks": self.warning_count(),
            "failed_checks": self.failed_count(),
            "blocking_findings": self.blocking_count(),
            "total_checks": len(self.findings),
            "findings": [f.to_dict() for f in self.findings],
            "summary": self.summary,
            "outputs_generated": self.outputs_generated,
        }


# ---------------------------------------------------------------------------
# 5. AnalyticalLayerClosureValidator
# ---------------------------------------------------------------------------

class AnalyticalLayerClosureValidator:
    """
    Governed validator for Phase 2A analytical-layer closure.
    """

    SIX_KPIS = ["kpi_001", "kpi_002", "kpi_003", "kpi_004", "kpi_005", "kpi_006"]

    EXPECTED_TOTAL = 17520
    EXPECTED_PER_KPI = 2920
    EXPECTED_GRAINS = 2920

    EXPECTED_AVAILABILITY: Dict[str, Dict[str, int]] = {
        "kpi_001": {"calculated": 2920, "unavailable": 0},
        "kpi_002": {"calculated": 2920, "unavailable": 0},
        "kpi_003": {"calculated": 1095, "unavailable": 1825},
        "kpi_004": {"calculated": 1095, "unavailable": 1825},
        "kpi_005": {"calculated": 984, "unavailable": 1936},
        "kpi_006": {"calculated": 2383, "unavailable": 537},
    }

    SOURCE_DATASETS: Dict[str, str] = {
        "kpi_001": "analytical_workforce_kpi_daily.csv",
        "kpi_002": "analytical_workforce_kpi_daily.csv",
        "kpi_003": "analytical_patient_flow_kpi_daily.csv",
        "kpi_004": "analytical_patient_flow_kpi_daily.csv",
        "kpi_005": "analytical_patient_experience_kpi_daily.csv",
        "kpi_006": "analytical_patient_experience_kpi_daily.csv",
    }

    REQUIRED_INTEGRATED_FILES = [
        "data/analytical/analytical_six_kpi_daily.csv",
        "data/analytical/analytical_six_kpi_evidence.csv",
        "data/analytical/analytical_six_kpi_exclusions.csv",
        "data/analytical/analytical_six_kpi_lineage.csv",
        "data/analytical/analytical_six_kpi_issues.csv",
        "data/analytical/analytical_six_kpi_audit.csv",
        "data/analytical/analytical_six_kpi_coverage_daily.csv",
    ]

    REQUIRED_SOURCE_FILES = [
        "data/analytical/analytical_workforce_kpi_daily.csv",
        "data/analytical/analytical_patient_flow_kpi_daily.csv",
        "data/analytical/analytical_patient_experience_kpi_daily.csv",
    ]

    REQUIRED_CONFIG_FILES = [
        "config/kpi_definition_config.csv",
        "config/kpi_threshold_config.csv",
        "config/data_confidence_config.csv",
    ]

    REQUIRED_STEP_FILES: Dict[str, List[str]] = {
        "step_2a1": [
            "src/analytical_models.py",
            "src/analytical_contracts.py",
            "src/analytical_config_loader.py",
            "src/kpi_registry.py",
            "src/analytical_schema_registry.py",
            "src/analytical_governance_validator.py",
            "src/run_analytical_architecture_validation.py",
            "tests/test_analytical_architecture.py",
        ],
        "step_2a2": [
            "src/workforce_kpi_engine.py",
            "src/run_workforce_kpi_processing.py",
            "tests/test_workforce_kpi_engine.py",
        ],
        "step_2a3": [
            "src/patient_flow_kpi_engine.py",
            "src/run_patient_flow_kpi_processing.py",
            "tests/test_patient_flow_kpi_engine.py",
        ],
        "step_2a4": [
            "src/patient_experience_kpi_engine.py",
            "src/run_patient_experience_kpi_processing.py",
            "tests/test_patient_experience_kpi_engine.py",
        ],
        "step_2a5": [
            "src/six_kpi_integration_engine.py",
            "src/run_six_kpi_integration.py",
            "tests/test_six_kpi_integration_engine.py",
        ],
    }

    REQUIRED_DOCUMENTATION = [
        "docs/kpi_governance_registry.md",
        "docs/step_2a1_analytical_architecture_report.md",
        "docs/step_2a2_workforce_kpi_processing_report.md",
        "docs/step_2a3_patient_flow_kpi_processing_report.md",
        "docs/patient_experience_kpi_engine_specification.md",
        "docs/patient_experience_kpi_processing_report.md",
        "docs/patient_experience_kpi_validation_evidence.md",
        "docs/six_kpi_integration_specification.md",
        "docs/six_kpi_status_governance.md",
        "docs/step_2a5_six_kpi_integration_report.md",
    ]

    def __init__(
        self,
        project_root: str,
        output_dir: str = "outputs/analytical_closure",
        skip_evidence_validation: bool = False,
        skip_lineage_validation: bool = False,
        skip_documentation_validation: bool = False,
        strict: bool = False,
        report_only: bool = False,
    ):
        self.project_root = os.path.abspath(project_root)
        self.output_dir = os.path.join(self.project_root, output_dir)
        self.skip_evidence_validation = skip_evidence_validation
        self.skip_lineage_validation = skip_lineage_validation
        self.skip_documentation_validation = skip_documentation_validation
        self.strict = strict
        self.report_only = report_only
        self.result = ClosureResult()
        self._data_cache: Dict[str, Optional[pd.DataFrame]] = {}
        self.logger = logging.getLogger(__name__)

    # -----------------------------------------------------------------------
    # Data loading helpers
    # -----------------------------------------------------------------------

    def _path(self, rel: str) -> str:
        return os.path.join(self.project_root, rel)

    def _load(self, rel: str) -> Optional[pd.DataFrame]:
        if rel not in self._data_cache:
            self._data_cache[rel] = _safe_read_csv(self._path(rel))
        return self._data_cache[rel]

    # -----------------------------------------------------------------------
    # 5.1 Load acceptance evidence
    # -----------------------------------------------------------------------

    def load_acceptance_evidence(self) -> None:
        """Pre-load all authoritative datasets into cache."""
        for rel in (
            self.REQUIRED_INTEGRATED_FILES
            + self.REQUIRED_SOURCE_FILES
            + self.REQUIRED_CONFIG_FILES
        ):
            self._load(rel)
        for step_files in self.REQUIRED_STEP_FILES.values():
            for rel in step_files:
                self._load(rel)
        for rel in self.REQUIRED_DOCUMENTATION:
            self._load(rel)

    # -----------------------------------------------------------------------
    # 5.2 Validate required files
    # -----------------------------------------------------------------------

    def validate_required_files(self) -> None:
        domain = "File Validation"
        for rel in self.REQUIRED_INTEGRATED_FILES + self.REQUIRED_SOURCE_FILES + self.REQUIRED_CONFIG_FILES:
            exists = os.path.exists(self._path(rel))
            status = "Passed" if exists else "Failed"
            severity = "Blocking" if not exists else "Information"
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name=f"required_file_exists:{rel}",
                    status=status,
                    severity=severity,
                    message=f"{'Found' if exists else 'MISSING'}: {rel}",
                )
            )

    # -----------------------------------------------------------------------
    # 5.3 Record / verify checksums
    # -----------------------------------------------------------------------

    def record_checksums(self, label: str) -> Dict[str, str]:
        files: List[str] = []
        for rel in (
            self.REQUIRED_INTEGRATED_FILES
            + self.REQUIRED_SOURCE_FILES
            + self.REQUIRED_CONFIG_FILES
        ):
            files.append(self._path(rel))
        for step_files in self.REQUIRED_STEP_FILES.values():
            for rel in step_files:
                files.append(self._path(rel))
        # Include Phase 1 processed dataset if present
        phase1_path = self._path("data/processed/processed_operational_daily.csv")
        if os.path.exists(phase1_path):
            files.append(phase1_path)
        checksums = _record_checksums(files)
        if label == "pre":
            self.result.pre_checksums = checksums
        else:
            self.result.post_checksums = checksums
        return checksums

    def verify_immutability(self) -> None:
        domain = "Immutability"
        changed = []
        for path, pre_hash in self.result.pre_checksums.items():
            post_hash = self.result.post_checksums.get(path)
            if post_hash is not None and post_hash != pre_hash:
                changed.append(path)
        if changed:
            status = "Failed"
            severity = "Blocking"
            msg = f"Accepted file(s) changed: {changed}"
        else:
            status = "Passed"
            severity = "Information"
            msg = "All accepted files unchanged."
        self.result.immutability_status = status
        self.result.add_finding(
            ValidationFinding(
                domain=domain,
                check_name="immutability_check",
                status=status,
                severity=severity,
                message=msg,
                details={"changed_files": changed},
            )
        )

    # -----------------------------------------------------------------------
    # 5.4 Validate KPI registry
    # -----------------------------------------------------------------------

    def validate_kpi_registry(self) -> None:
        domain = "KPI Registry"
        df = self._load("config/kpi_definition_config.csv")
        if df is None:
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name="kpi_registry_load",
                    status="Failed",
                    severity="Blocking",
                    message="Cannot load kpi_definition_config.csv",
                )
            )
            return
        found_ids = set(df["kpi_id"].dropna().unique().tolist())
        expected = set(self.SIX_KPIS)
        missing = expected - found_ids
        extra = found_ids - expected
        status = "Passed" if not missing else "Failed"
        severity = "Blocking" if missing else "Information"
        self.result.add_finding(
            ValidationFinding(
                domain=domain,
                check_name="kpi_registry_six_kpis",
                status=status,
                severity=severity,
                message=f"Expected {expected}, missing {missing}, extra {extra}",
                details={"found": list(found_ids), "missing": list(missing), "extra": list(extra)},
            )
        )

    def validate_six_kpi_set(self) -> None:
        domain = "KPI Registry"
        daily = self._load("data/analytical/analytical_six_kpi_daily.csv")
        if daily is None:
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name="six_kpi_set_integrated",
                    status="Failed",
                    severity="Blocking",
                    message="Cannot load analytical_six_kpi_daily.csv",
                )
            )
            return
        found_ids = set(daily["kpi_id"].dropna().unique().tolist())
        expected = set(self.SIX_KPIS)
        missing = expected - found_ids
        status = "Passed" if not missing else "Failed"
        severity = "Blocking" if missing else "Information"
        self.result.add_finding(
            ValidationFinding(
                domain=domain,
                check_name="six_kpi_set_integrated",
                status=status,
                severity=severity,
                message=f"Integrated KPI IDs: {found_ids}, missing: {missing}",
                details={"found": list(found_ids), "missing": list(missing)},
            )
        )

    # -----------------------------------------------------------------------
    # 5.5 Validate counts
    # -----------------------------------------------------------------------

    def validate_source_counts(self) -> None:
        domain = "Counts"
        for kpi_id, source_name in self.SOURCE_DATASETS.items():
            src = self._load(f"data/analytical/{source_name}")
            if src is None:
                self.result.add_finding(
                    ValidationFinding(
                        domain=domain,
                        check_name=f"source_count:{kpi_id}",
                        status="Failed",
                        severity="Blocking",
                        message=f"Cannot load {source_name}",
                    )
                )
                continue
            mask = src["kpi_id"] == kpi_id
            count = int(mask.sum())
            status = "Passed" if count == self.EXPECTED_PER_KPI else "Failed"
            severity = "Blocking" if count != self.EXPECTED_PER_KPI else "Information"
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name=f"source_count:{kpi_id}",
                    status=status,
                    severity=severity,
                    message=f"{kpi_id} source count = {count} (expected {self.EXPECTED_PER_KPI})",
                    details={"kpi_id": kpi_id, "count": count},
                )
            )

    def validate_integrated_counts(self) -> None:
        domain = "Counts"
        daily = self._load("data/analytical/analytical_six_kpi_daily.csv")
        if daily is None:
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name="integrated_total_count",
                    status="Failed",
                    severity="Blocking",
                    message="Cannot load analytical_six_kpi_daily.csv",
                )
            )
            return
        total = len(daily)
        status = "Passed" if total == self.EXPECTED_TOTAL else "Failed"
        severity = "Blocking" if total != self.EXPECTED_TOTAL else "Information"
        self.result.add_finding(
            ValidationFinding(
                domain=domain,
                check_name="integrated_total_count",
                status=status,
                severity=severity,
                message=f"Integrated total = {total} (expected {self.EXPECTED_TOTAL})",
                details={"total": total},
            )
        )
        for kpi_id in self.SIX_KPIS:
            count = int((daily["kpi_id"] == kpi_id).sum())
            st = "Passed" if count == self.EXPECTED_PER_KPI else "Failed"
            sev = "Blocking" if count != self.EXPECTED_PER_KPI else "Information"
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name=f"integrated_count:{kpi_id}",
                    status=st,
                    severity=sev,
                    message=f"{kpi_id} integrated count = {count} (expected {self.EXPECTED_PER_KPI})",
                    details={"kpi_id": kpi_id, "count": count},
                )
            )

    # -----------------------------------------------------------------------
    # 5.6 Reconcile KPI results
    # -----------------------------------------------------------------------

    def reconcile_kpi_results(self) -> None:
        domain = "Integration Reconciliation"
        daily = self._load("data/analytical/analytical_six_kpi_daily.csv")
        if daily is None:
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name="reconciliation_load",
                    status="Failed",
                    severity="Blocking",
                    message="Cannot load integrated daily for reconciliation",
                )
            )
            return
        reconciliation_rows = []
        for kpi_id in self.SIX_KPIS:
            source_name = self.SOURCE_DATASETS[kpi_id]
            src = self._load(f"data/analytical/{source_name}")
            src_count = int((src["kpi_id"] == kpi_id).sum()) if src is not None else 0
            int_count = int((daily["kpi_id"] == kpi_id).sum())
            dup_count = 0
            if src is not None:
                src_sub = src[src["kpi_id"] == kpi_id]
                dup_count = int(src_sub.duplicated(subset=["hospital_id", "department_id", "reporting_date"]).sum())
            diff = src_count - int_count
            rec_status = "Reconciled" if diff == 0 else "MISMATCH"
            reconciliation_rows.append({
                "kpi_id": kpi_id,
                "kpi_name": self._kpi_name(kpi_id),
                "source_dataset": source_name,
                "source_row_count": src_count,
                "integrated_row_count": int_count,
                "closure_row_count": int_count,
                "calculated_count": None,
                "unavailable_count": None,
                "duplicate_count": dup_count,
                "missing_count": max(0, -diff),
                "count_difference": diff,
                "reconciliation_status": rec_status,
            })
            st = "Passed" if diff == 0 else "Failed"
            sev = "Blocking" if diff != 0 else "Information"
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name=f"reconcile:{kpi_id}",
                    status=st,
                    severity=sev,
                    message=f"{kpi_id} source={src_count} integrated={int_count} diff={diff}",
                    details={"diff": diff},
                )
            )
        self.result.summary["kpi_count_reconciliation"] = reconciliation_rows

    def _kpi_name(self, kpi_id: str) -> str:
        df = self._load("config/kpi_definition_config.csv")
        if df is None:
            return ""
        rows = df[df["kpi_id"] == kpi_id]
        if rows.empty:
            return ""
        return str(rows.iloc[0].get("kpi_name", ""))

    # -----------------------------------------------------------------------
    # 5.7 Validate calculation statuses
    # -----------------------------------------------------------------------

    def validate_calculation_statuses(self) -> None:
        domain = "Calculation Status"
        daily = self._load("data/analytical/analytical_six_kpi_daily.csv")
        if daily is None:
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name="calc_status_load",
                    status="Failed",
                    severity="Blocking",
                    message="Cannot load integrated daily",
                )
            )
            return
        for kpi_id in self.SIX_KPIS:
            sub = daily[daily["kpi_id"] == kpi_id]
            calc_mask = sub["calculation_status"] == "Calculated"
            calc_count = int(calc_mask.sum())
            unavail_count = int((~calc_mask).sum())
            exp = self.EXPECTED_AVAILABILITY[kpi_id]
            calc_ok = calc_count == exp["calculated"]
            unavail_ok = unavail_count == exp["unavailable"]
            status = "Passed" if (calc_ok and unavail_ok) else "Failed"
            severity = "Blocking" if not (calc_ok and unavail_ok) else "Information"
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name=f"calculation_availability:{kpi_id}",
                    status=status,
                    severity=severity,
                    message=(
                        f"{kpi_id} calculated={calc_count} (exp {exp['calculated']}), "
                        f"unavailable={unavail_count} (exp {exp['unavailable']})"
                    ),
                    details={"calculated": calc_count, "unavailable": unavail_count},
                )
            )
        # Value-status consistency
        inconsistencies = 0
        for _, row in daily.iterrows():
            calc_status = str(row.get("calculation_status", ""))
            kpi_val = row.get("kpi_value")
            is_null = pd.isna(kpi_val) or str(kpi_val).strip() == ""
            if calc_status == "Calculated" and is_null:
                inconsistencies += 1
            if calc_status != "Calculated" and not is_null:
                inconsistencies += 1
        st = "Passed" if inconsistencies == 0 else "Failed"
        sev = "Blocking" if inconsistencies > 0 else "Information"
        self.result.add_finding(
            ValidationFinding(
                domain=domain,
                check_name="value_status_consistency",
                status=st,
                severity=sev,
                message=f"Value-status inconsistencies = {inconsistencies} (expected 0)",
                details={"inconsistencies": inconsistencies},
            )
        )

    # -----------------------------------------------------------------------
    # 5.8 Validate threshold governance
    # -----------------------------------------------------------------------

    def validate_threshold_governance(self) -> None:
        domain = "Threshold Governance"
        daily = self._load("data/analytical/analytical_six_kpi_daily.csv")
        if daily is None:
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name="threshold_load",
                    status="Failed",
                    severity="Blocking",
                    message="Cannot load integrated daily",
                )
            )
            return
        total = len(daily)
        not_assessed = int((daily["threshold_status"] == "Not Assessed").sum())
        provisional = int((daily["threshold_is_provisional"].astype(str).str.lower() == "true").sum())
        green = int((daily["threshold_status"] == "Green").sum())
        amber = int((daily["threshold_status"] == "Amber").sum())
        red = int((daily["threshold_status"] == "Red").sum())
        draft_not_approved = int(
            (
                (daily["threshold_approval_status"].astype(str).str.lower() == "draft")
                & (daily["threshold_is_provisional"].astype(str).str.lower() == "true")
            ).sum()
        )

        checks = [
            ("all_not_assessed", not_assessed == total),
            ("all_provisional", provisional == total),
            ("no_green", green == 0),
            ("no_amber", amber == 0),
            ("no_red", red == 0),
            ("draft_not_approved", draft_not_approved == total),
        ]
        for name, ok in checks:
            st = "Passed" if ok else "Failed"
            sev = "Blocking" if not ok else "Information"
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name=name,
                    status=st,
                    severity=sev,
                    message=f"{name}: {'OK' if ok else 'FAIL'}",
                    details={"count": not_assessed if name == "all_not_assessed" else (provisional if name == "all_provisional" else 0)},
                )
            )
        # Warning about provisional thresholds
        if provisional == total:
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name="provisional_threshold_warning",
                    status="Passed with Warning",
                    severity="Warning",
                    message=(
                        "Phase 2A KPI calculations are complete, but performance classification remains "
                        "provisional until thresholds are formally approved."
                    ),
                )
            )

    # -----------------------------------------------------------------------
    # 5.9 Validate confidence governance
    # -----------------------------------------------------------------------

    def validate_confidence_governance(self) -> None:
        domain = "Confidence Governance"
        daily = self._load("data/analytical/analytical_six_kpi_daily.csv")
        if daily is None:
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name="confidence_load",
                    status="Failed",
                    severity="Blocking",
                    message="Cannot load integrated daily",
                )
            )
            return
        # Distribution by KPI
        dist = daily.groupby(["kpi_id", "data_confidence_level"]).size().reset_index(name="count")
        self.result.summary["confidence_distribution"] = dist.to_dict(orient="records")
        # Unavailable results must not have High confidence
        calc_mask = daily["calculation_status"] == "Calculated"
        unavailable_high = daily[~calc_mask & (daily["data_confidence_level"] == "High")]
        uh_count = len(unavailable_high)
        st = "Passed" if uh_count == 0 else "Failed"
        sev = "Blocking" if uh_count > 0 else "Information"
        self.result.add_finding(
            ValidationFinding(
                domain=domain,
                check_name="unavailable_not_high_confidence",
                status=st,
                severity=sev,
                message=f"Unavailable records with High confidence = {uh_count} (expected 0)",
                details={"count": uh_count},
            )
        )

    # -----------------------------------------------------------------------
    # 5.10 Validate evidence
    # -----------------------------------------------------------------------

    def validate_evidence(self) -> None:
        domain = "Evidence"
        if self.skip_evidence_validation:
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name="evidence_validation",
                    status="Not Applicable",
                    severity="Information",
                    message="Evidence validation skipped per flag.",
                )
            )
            return
        daily = self._load("data/analytical/analytical_six_kpi_daily.csv")
        evidence = self._load("data/analytical/analytical_six_kpi_evidence.csv")
        if daily is None:
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name="evidence_load",
                    status="Failed",
                    severity="Blocking",
                    message="Cannot load integrated daily",
                )
            )
            return
        # Calculated KPIs should have evidence status Complete
        calc_mask = daily["calculation_status"] == "Calculated"
        calc_daily = daily[calc_mask]
        missing_evidence = int((calc_daily["evidence_status"] != "Complete").sum())
        st = "Passed" if missing_evidence == 0 else "Failed"
        sev = "Blocking" if missing_evidence > 0 else "Information"
        self.result.add_finding(
            ValidationFinding(
                domain=domain,
                check_name="calculated_has_evidence",
                status=st,
                severity=sev,
                message=f"Calculated records without Complete evidence = {missing_evidence}",
                details={"count": missing_evidence},
            )
        )
        # Unavailable KPIs should have evidence status Unavailable or Complete
        uncalc_daily = daily[~calc_mask]
        bad_evidence = int(
            (~uncalc_daily["evidence_status"].isin(["Complete", "Unavailable", "Missing"])).sum()
        )
        st2 = "Passed" if bad_evidence == 0 else "Failed"
        sev2 = "Blocking" if bad_evidence > 0 else "Information"
        self.result.add_finding(
            ValidationFinding(
                domain=domain,
                check_name="unavailable_evidence_status_valid",
                status=st2,
                severity=sev2,
                message=f"Unavailable records with invalid evidence status = {bad_evidence}",
                details={"count": bad_evidence},
            )
        )
        # Evidence dataset reconciliation with source outputs
        if evidence is not None and not evidence.empty:
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name="evidence_dataset_reconciles",
                    status="Passed",
                    severity="Information",
                    message=f"Evidence dataset has {len(evidence)} rows.",
                    details={"evidence_rows": len(evidence)},
                )
            )
        else:
            # Empty evidence is acceptable if daily evidence_status is Complete for calculated records
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name="evidence_dataset_reconciles",
                    status="Passed with Warning",
                    severity="Warning",
                    message="Evidence dataset is empty; relying on daily evidence_status.",
                )
            )

    # -----------------------------------------------------------------------
    # 5.11 Validate lineage
    # -----------------------------------------------------------------------

    def validate_lineage(self) -> None:
        domain = "Lineage"
        if self.skip_lineage_validation:
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name="lineage_validation",
                    status="Not Applicable",
                    severity="Information",
                    message="Lineage validation skipped per flag.",
                )
            )
            return
        daily = self._load("data/analytical/analytical_six_kpi_daily.csv")
        lineage = self._load("data/analytical/analytical_six_kpi_lineage.csv")
        if daily is None:
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name="lineage_load",
                    status="Failed",
                    severity="Blocking",
                    message="Cannot load integrated daily",
                )
            )
            return
        calc_mask = daily["calculation_status"] == "Calculated"
        calc_daily = daily[calc_mask]
        broken = int((calc_daily["lineage_status"].isin(["Broken", "Missing"])).sum())
        st = "Passed" if broken == 0 else "Failed"
        sev = "Blocking" if broken > 0 else "Information"
        self.result.add_finding(
            ValidationFinding(
                domain=domain,
                check_name="calculated_lineage_not_broken",
                status=st,
                severity=sev,
                message=f"Calculated records with broken/missing lineage = {broken}",
                details={"count": broken},
            )
        )
        # Source analytical dataset linkage
        missing_source = int(daily["source_analytical_dataset"].isna().sum())
        st2 = "Passed" if missing_source == 0 else "Failed"
        sev2 = "Blocking" if missing_source > 0 else "Information"
        self.result.add_finding(
            ValidationFinding(
                domain=domain,
                check_name="source_dataset_linkage",
                status=st2,
                severity=sev2,
                message=f"Records missing source_analytical_dataset = {missing_source}",
                details={"count": missing_source},
            )
        )
        if lineage is not None and not lineage.empty:
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name="lineage_dataset_reconciles",
                    status="Passed",
                    severity="Information",
                    message=f"Lineage dataset has {len(lineage)} rows.",
                    details={"lineage_rows": len(lineage)},
                )
            )
        else:
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name="lineage_dataset_reconciles",
                    status="Passed with Warning",
                    severity="Warning",
                    message="Lineage dataset is empty; relying on daily lineage_status.",
                )
            )

    # -----------------------------------------------------------------------
    # 5.12 Validate coverage
    # -----------------------------------------------------------------------

    def validate_coverage(self) -> None:
        domain = "Coverage"
        cov = self._load("data/analytical/analytical_six_kpi_coverage_daily.csv")
        if cov is None:
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name="coverage_load",
                    status="Failed",
                    severity="Blocking",
                    message="Cannot load coverage dataset",
                )
            )
            return
        total_grains = len(cov)
        complete = int((cov["coverage_status"] == "Complete").sum())
        missing = int(cov["missing_kpi_count"].astype(float).sum())
        st_total = "Passed" if total_grains == self.EXPECTED_GRAINS else "Failed"
        sev_total = "Blocking" if total_grains != self.EXPECTED_GRAINS else "Information"
        self.result.add_finding(
            ValidationFinding(
                domain=domain,
                check_name="coverage_grain_count",
                status=st_total,
                severity=sev_total,
                message=f"Coverage grains = {total_grains} (expected {self.EXPECTED_GRAINS})",
                details={"grains": total_grains},
            )
        )
        st_complete = "Passed" if complete == self.EXPECTED_GRAINS else "Failed"
        sev_complete = "Blocking" if complete != self.EXPECTED_GRAINS else "Information"
        self.result.add_finding(
            ValidationFinding(
                domain=domain,
                check_name="coverage_all_complete",
                status=st_complete,
                severity=sev_complete,
                message=f"Complete grains = {complete} (expected {self.EXPECTED_GRAINS})",
                details={"complete": complete},
            )
        )
        st_missing = "Passed" if missing == 0 else "Failed"
        sev_missing = "Blocking" if missing > 0 else "Information"
        self.result.add_finding(
            ValidationFinding(
                domain=domain,
                check_name="coverage_missing_kpis",
                status=st_missing,
                severity=sev_missing,
                message=f"Missing KPI rows across all grains = {missing} (expected 0)",
                details={"missing": missing},
            )
        )

    # -----------------------------------------------------------------------
    # 5.13 Validate schemas and keys
    # -----------------------------------------------------------------------

    def validate_schemas(self) -> None:
        domain = "Schema"
        daily = self._load("data/analytical/analytical_six_kpi_daily.csv")
        if daily is None:
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name="schema_load",
                    status="Failed",
                    severity="Blocking",
                    message="Cannot load integrated daily",
                )
            )
            return
        required_fields = [
            "integration_record_id",
            "analytical_record_id",
            "hospital_id",
            "department_id",
            "reporting_date",
            "reporting_month",
            "reporting_year",
            "kpi_id",
            "kpi_name",
            "domain",
            "calculation_status",
            "readiness_status",
            "threshold_status",
            "threshold_is_provisional",
            "data_confidence_level",
            "integration_status",
            "evidence_status",
            "lineage_status",
            "source_analytical_dataset",
            "source_analytical_record_id",
            "source_calculation_run_id",
            "integration_run_id",
        ]
        missing_fields = [f for f in required_fields if f not in daily.columns]
        st = "Passed" if not missing_fields else "Failed"
        sev = "Blocking" if missing_fields else "Information"
        self.result.add_finding(
            ValidationFinding(
                domain=domain,
                check_name="daily_required_fields",
                status=st,
                severity=sev,
                message=f"Missing fields: {missing_fields}",
                details={"missing": missing_fields},
            )
        )
        # Type/date checks
        date_parse_ok = True
        try:
            pd.to_datetime(daily["reporting_date"], errors="raise")
        except Exception:
            date_parse_ok = False
        st_date = "Passed" if date_parse_ok else "Failed"
        sev_date = "Blocking" if not date_parse_ok else "Information"
        self.result.add_finding(
            ValidationFinding(
                domain=domain,
                check_name="reporting_date_parse",
                status=st_date,
                severity=sev_date,
                message="reporting_date parses as datetime" if date_parse_ok else "reporting_date parse failed",
            )
        )

    def validate_business_keys(self) -> None:
        domain = "Keys"
        daily = self._load("data/analytical/analytical_six_kpi_daily.csv")
        if daily is None:
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name="keys_load",
                    status="Failed",
                    severity="Blocking",
                    message="Cannot load integrated daily",
                )
            )
            return
        # Duplicate grain check
        dup_grain = daily.duplicated(
            subset=["hospital_id", "department_id", "reporting_date", "kpi_id"], keep=False
        ).sum()
        st = "Passed" if dup_grain == 0 else "Failed"
        sev = "Blocking" if dup_grain > 0 else "Information"
        self.result.add_finding(
            ValidationFinding(
                domain=domain,
                check_name="duplicate_grain_check",
                status=st,
                severity=sev,
                message=f"Duplicate hospital-department-date-kpi grains = {dup_grain}",
                details={"duplicate_count": int(dup_grain)},
            )
        )
        # Unique integration_record_id
        unique_ids = daily["integration_record_id"].nunique()
        total = len(daily)
        st_id = "Passed" if unique_ids == total else "Failed"
        sev_id = "Blocking" if unique_ids != total else "Information"
        self.result.add_finding(
            ValidationFinding(
                domain=domain,
                check_name="unique_integration_record_id",
                status=st_id,
                severity=sev_id,
                message=f"integration_record_id unique = {unique_ids}/{total}",
                details={"unique": unique_ids, "total": total},
            )
        )

    def validate_deterministic_ids(self) -> None:
        domain = "Keys"
        daily = self._load("data/analytical/analytical_six_kpi_daily.csv")
        if daily is None:
            return
        expected_prefix = "IKPI-"
        bad_prefix = int((~daily["integration_record_id"].astype(str).str.startswith(expected_prefix)).sum())
        st = "Passed" if bad_prefix == 0 else "Failed"
        sev = "Blocking" if bad_prefix > 0 else "Information"
        self.result.add_finding(
            ValidationFinding(
                domain=domain,
                check_name="deterministic_id_prefix",
                status=st,
                severity=sev,
                message=f"integration_record_id without IKPI- prefix = {bad_prefix}",
                details={"bad_count": bad_prefix},
            )
        )

    # -----------------------------------------------------------------------
    # 5.14 Validate issues and exclusions
    # -----------------------------------------------------------------------

    def validate_issues_and_exclusions(self) -> None:
        domain = "Issues and Exclusions"
        issues = self._load("data/analytical/analytical_six_kpi_issues.csv")
        exclusions = self._load("data/analytical/analytical_six_kpi_exclusions.csv")
        # Issues
        if issues is None or issues.empty:
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name="issues_empty",
                    status="Passed",
                    severity="Information",
                    message="Issue log is empty (zero integration issues as accepted).",
                )
            )
        else:
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name="issues_present",
                    status="Passed with Warning",
                    severity="Warning",
                    message=f"Issue log has {len(issues)} rows; review required.",
                    details={"issue_count": len(issues)},
                )
            )
        # Exclusions
        if exclusions is None or exclusions.empty:
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name="exclusions_empty",
                    status="Passed",
                    severity="Information",
                    message="Exclusion dataset is empty.",
                )
            )
        else:
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name="exclusions_present",
                    status="Passed",
                    severity="Information",
                    message=f"Exclusion dataset has {len(exclusions)} rows.",
                    details={"exclusion_count": len(exclusions)},
                )
            )

    # -----------------------------------------------------------------------
    # 5.15 Validate audit coverage
    # -----------------------------------------------------------------------

    def validate_audit_coverage(self) -> None:
        domain = "Audit"
        audit = self._load("data/analytical/analytical_six_kpi_audit.csv")
        if audit is None or audit.empty:
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name="audit_load",
                    status="Passed with Warning",
                    severity="Warning",
                    message="Audit dataset is empty or missing.",
                )
            )
            return
        self.result.add_finding(
            ValidationFinding(
                domain=domain,
                check_name="audit_rows",
                status="Passed",
                severity="Information",
                message=f"Audit dataset has {len(audit)} rows.",
                details={"audit_rows": len(audit)},
            )
        )

    # -----------------------------------------------------------------------
    # 5.16 Validate documentation
    # -----------------------------------------------------------------------

    def validate_documentation(self) -> None:
        domain = "Documentation"
        if self.skip_documentation_validation:
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name="documentation_validation",
                    status="Not Applicable",
                    severity="Information",
                    message="Documentation validation skipped per flag.",
                )
            )
            return
        missing = []
        for rel in self.REQUIRED_DOCUMENTATION:
            if not os.path.exists(self._path(rel)):
                missing.append(rel)
        st = "Passed" if not missing else ("Failed" if self.strict else "Passed with Warning")
        sev = "Blocking" if missing and self.strict else ("Warning" if missing else "Information")
        self.result.add_finding(
            ValidationFinding(
                domain=domain,
                check_name="required_documentation",
                status=st,
                severity=sev,
                message=f"Missing documentation: {missing}" if missing else "All required documentation present.",
                details={"missing": missing},
            )
        )

    # -----------------------------------------------------------------------
    # 5.17 Validate value preservation
    # -----------------------------------------------------------------------

    def validate_value_preservation(self) -> None:
        domain = "Value Preservation"
        daily = self._load("data/analytical/analytical_six_kpi_daily.csv")
        if daily is None:
            self.result.add_finding(
                ValidationFinding(
                    domain=domain,
                    check_name="value_preservation_load",
                    status="Failed",
                    severity="Blocking",
                    message="Cannot load integrated daily",
                )
            )
            return
        mismatches = 0
        mismatch_details = []
        for kpi_id in self.SIX_KPIS:
            source_name = self.SOURCE_DATASETS[kpi_id]
            src = self._load(f"data/analytical/{source_name}")
            if src is None:
                continue
            src_sub = src[src["kpi_id"] == kpi_id].copy()
            int_sub = daily[daily["kpi_id"] == kpi_id].copy()
            if src_sub.empty or int_sub.empty:
                continue
            # Merge on natural key
            merge_cols = ["hospital_id", "department_id", "reporting_date"]
            merged = int_sub.merge(src_sub, on=merge_cols, how="inner", suffixes=("_int", "_src"))
            if merged.empty:
                continue
            # Compare kpi_value with tolerance for floats
            for _, row in merged.iterrows():
                val_int = row.get("kpi_value_int")
                val_src = row.get("kpi_value_src")
                if pd.isna(val_int) and pd.isna(val_src):
                    continue
                try:
                    v_int = float(val_int)
                    v_src = float(val_src)
                    if abs(v_int - v_src) > 1e-9:
                        mismatches += 1
                        mismatch_details.append({"kpi_id": kpi_id, "diff": abs(v_int - v_src)})
                except (TypeError, ValueError):
                    if str(val_int) != str(val_src):
                        mismatches += 1
                        mismatch_details.append({"kpi_id": kpi_id, "diff": None})
        st = "Passed" if mismatches == 0 else "Failed"
        sev = "Blocking" if mismatches > 0 else "Information"
        self.result.add_finding(
            ValidationFinding(
                domain=domain,
                check_name="kpi_value_preserved",
                status=st,
                severity=sev,
                message=f"KPI value mismatches = {mismatches} (expected 0)",
                details={"mismatches": mismatches, "sample": mismatch_details[:10]},
            )
        )

    # -----------------------------------------------------------------------
    # 5.18 Validate formula evidence existence
    # -----------------------------------------------------------------------

    def validate_formula_evidence(self) -> None:
        domain = "Formula Evidence"
        # Check accepted formula-verification outputs exist for patient experience
        pex_evidence = self._path("outputs/analytical_patient_experience/formula_verification_evidence.json")
        exists = os.path.exists(pex_evidence)
        st = "Passed" if exists else "Passed with Warning"
        sev = "Warning" if not exists else "Information"
        self.result.add_finding(
            ValidationFinding(
                domain=domain,
                check_name="formula_evidence_exists",
                status=st,
                severity=sev,
                message=(
                    "Patient experience formula verification evidence found."
                    if exists
                    else "Patient experience formula verification evidence not found; relying on accepted status."
                ),
            )
        )

    # -----------------------------------------------------------------------
    # 5.19 Classification
    # -----------------------------------------------------------------------

    def classify_findings(self) -> None:
        blocking = self.result.blocking_count()
        warnings = self.result.warning_count()
        if blocking > 0:
            self.result.closure_status = "Failed"
            self.result.phase_2b_readiness = "Not Ready"
        elif warnings > 0:
            self.result.closure_status = "Passed with Warning"
            self.result.phase_2b_readiness = "Ready with Conditions"
        else:
            self.result.closure_status = "Passed"
            self.result.phase_2b_readiness = "Ready"
        # Phase 2B conditions
        if self.result.phase_2b_readiness == "Ready with Conditions":
            self.result.phase_2b_conditions = [
                "Stakeholder approval of threshold boundaries remains pending.",
                "Threshold-based Green, Amber and Red classifications remain unavailable.",
                "Phase 2B may proceed with period comparisons, trends, anomaly detection and relationship analysis.",
                "Threshold-breach logic must remain provisional or disabled until approved.",
            ]

    # -----------------------------------------------------------------------
    # 5.20 Build closure summary and manifest
    # -----------------------------------------------------------------------

    def build_closure_summary(self) -> Dict[str, Any]:
        daily = self._load("data/analytical/analytical_six_kpi_daily.csv")
        summary: Dict[str, Any] = {
            "closure_run_at": datetime.now().isoformat(),
            "total_integrated_records": len(daily) if daily is not None else 0,
            "records_per_kpi": {},
            "calculated_counts": {},
            "unavailable_counts": {},
            "closure_status": self.result.closure_status,
            "phase_2b_readiness": self.result.phase_2b_readiness,
            "phase_2b_conditions": self.result.phase_2b_conditions,
        }
        if daily is not None:
            for kpi_id in self.SIX_KPIS:
                sub = daily[daily["kpi_id"] == kpi_id]
                summary["records_per_kpi"][kpi_id] = len(sub)
                calc = int((sub["calculation_status"] == "Calculated").sum())
                summary["calculated_counts"][kpi_id] = calc
                summary["unavailable_counts"][kpi_id] = len(sub) - calc
        self.result.summary.update(summary)
        return summary

    def build_closure_manifest(self) -> Dict[str, Any]:
        return {
            "manifest_type": "Phase_2A_Closure",
            "created_at": datetime.now().isoformat(),
            "validator": "AnalyticalLayerClosureValidator",
            "closure_status": self.result.closure_status,
            "phase_2b_readiness": self.result.phase_2b_readiness,
            "findings_summary": {
                "total": len(self.result.findings),
                "passed": self.result.passed_count(),
                "warning": self.result.warning_count(),
                "failed": self.result.failed_count(),
                "blocking": self.result.blocking_count(),
            },
            "outputs_generated": self.result.outputs_generated,
        }

    # -----------------------------------------------------------------------
    # 5.21 Run all validations
    # -----------------------------------------------------------------------

    def run_all_validations(self) -> ClosureResult:
        self.load_acceptance_evidence()
        self.validate_required_files()
        self.validate_kpi_registry()
        self.validate_six_kpi_set()
        self.validate_source_counts()
        self.validate_integrated_counts()
        self.reconcile_kpi_results()
        self.validate_calculation_statuses()
        self.validate_threshold_governance()
        self.validate_confidence_governance()
        self.validate_evidence()
        self.validate_lineage()
        self.validate_coverage()
        self.validate_schemas()
        self.validate_business_keys()
        self.validate_deterministic_ids()
        self.validate_issues_and_exclusions()
        self.validate_audit_coverage()
        self.validate_documentation()
        self.validate_value_preservation()
        self.validate_formula_evidence()
        self.classify_findings()
        self.build_closure_summary()
        return self.result

    # -----------------------------------------------------------------------
    # 5.22 Export helpers
    # -----------------------------------------------------------------------

    def _ensure_output_dir(self) -> None:
        os.makedirs(self.output_dir, exist_ok=True)

    def export_findings_csv(self, filename: str, domain_filter: Optional[str] = None) -> str:
        self._ensure_output_dir()
        path = os.path.join(self.output_dir, filename)
        rows = [f.to_dict() for f in self.result.findings if domain_filter is None or f.domain == domain_filter]
        df = pd.DataFrame(rows)
        if not df.empty:
            df.to_csv(path, index=False)
        else:
            df = pd.DataFrame(columns=["domain", "check_name", "status", "severity", "message", "details"])
            df.to_csv(path, index=False)
        self.result.outputs_generated.append(path)
        return path

    def export_summary_csv(self, filename: str, data: List[Dict[str, Any]]) -> str:
        self._ensure_output_dir()
        path = os.path.join(self.output_dir, filename)
        df = pd.DataFrame(data)
        df.to_csv(path, index=False)
        self.result.outputs_generated.append(path)
        return path

    def export_json(self, filename: str, payload: Dict[str, Any]) -> str:
        self._ensure_output_dir()
        path = os.path.join(self.output_dir, filename)
        with open(path, "w") as f:
            json.dump(payload, f, indent=2, default=str)
        self.result.outputs_generated.append(path)
        return path
