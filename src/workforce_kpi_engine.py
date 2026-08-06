"""
Sentinel360 Healthcare — Workforce KPI Engine

Calculates only:
  - kpi_001 — Staffing Level
  - kpi_002 — Staff Absenteeism Rate

Uses accepted Phase 1 processed data and Step 2A-1 governance.
Preserves numerator/denominator evidence, applies draft thresholds,
evaluates data confidence, and generates lineage/audit records.

Step: 2A-2
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from analytical_models import (
    KPIDefinition,
    KPICalculationRequest,
    KPICalculationResult,
    KPINumeratorEvidence,
    KPIDenominatorEvidence,
    KPIExclusionRecord,
    DataConfidenceResult,
    AnalyticalIssue,
    AnalyticalLineageRecord,
    AnalyticalAuditRecord,
    ConfigurationProvenance,
    CalculationRunManifest,
    SchemaValidationResult,
)
from analytical_contracts import (
    CalculationGateResult,
    ImmutabilityVerificationContract,
)
from kpi_registry import build_registry_from_config
from analytical_config_loader import AnalyticalConfigLoader


# ---------------------------------------------------------------------------
# 1. Engine Result Container
# ---------------------------------------------------------------------------

@dataclass
class WorkforceKPIEngineResult:
    """Complete result from a workforce KPI engine run."""

    manifest: CalculationRunManifest = field(default_factory=CalculationRunManifest)
    kpi_results: List[KPICalculationResult] = field(default_factory=list)
    evidence_records: List[Dict[str, Any]] = field(default_factory=list)
    exclusion_records: List[Dict[str, Any]] = field(default_factory=list)
    lineage_records: List[Dict[str, Any]] = field(default_factory=list)
    issue_records: List[Dict[str, Any]] = field(default_factory=list)
    audit_records: List[Dict[str, Any]] = field(default_factory=list)
    formula_verification: Dict[str, Any] = field(default_factory=dict)
    immutability_result: Dict[str, Any] = field(default_factory=dict)
    configuration_provenance: List[ConfigurationProvenance] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 2. Workforce KPI Engine
# ---------------------------------------------------------------------------

class WorkforceKPIEngine:
    """Governed engine for calculating workforce KPIs."""

    SUPPORTED_KPI_IDS = {"kpi_001", "kpi_002"}

    # Source field mapping from governed definitions
    KPI_SOURCE_FIELDS = {
        "kpi_001": {
            "numerator_fields": ["present_staff_count", "replacement_staff_count"],
            "denominator_field": "planned_staff_count",
            "required_fields": [
                "hospital_id",
                "department_id",
                "reporting_date",
                "reporting_month",
                "reporting_year",
                "planned_staff_count",
                "present_staff_count",
                "replacement_staff_count",
                "reassigned_staff_count",
            ],
            "source_dataset": "processed_operational_daily",
        },
        "kpi_002": {
            "numerator_fields": ["unapproved_absence_count"],
            "denominator_field": "planned_staff_count",
            "required_fields": [
                "hospital_id",
                "department_id",
                "reporting_date",
                "reporting_month",
                "reporting_year",
                "planned_staff_count",
                "unapproved_absence_count",
            ],
            "source_dataset": "processed_operational_daily",
        },
    }

    def __init__(
        self,
        project_root: Path,
        calculation_run_id: Optional[str] = None,
        skip_threshold_status: bool = False,
        skip_confidence: bool = False,
    ):
        self.project_root = Path(project_root)
        self.calculation_run_id = calculation_run_id or self._generate_run_id()
        self.skip_threshold_status = skip_threshold_status
        self.skip_confidence = skip_confidence
        self.config_loader = AnalyticalConfigLoader(self.project_root / "config")
        self.kpi_registry: Optional[Dict[str, KPIDefinition]] = None
        self.thresholds_df: Optional[pd.DataFrame] = None
        self.confidence_rules_df: Optional[pd.DataFrame] = None
        self.source_df: Optional[pd.DataFrame] = None
        self.issues: List[AnalyticalIssue] = []
        self.audit_records: List[AnalyticalAuditRecord] = []
        self._baseline_checksums: Dict[str, str] = {}

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _generate_run_id() -> str:
        return f"WF-KPI-{uuid.uuid4().hex[:12].upper()}"

    @staticmethod
    def _generate_analytical_record_id(kpi_id: str, hospital_id: str, department_id: str, reporting_date: date) -> str:
        date_str = reporting_date.strftime("%Y%m%d") if isinstance(reporting_date, date) else str(reporting_date).replace("-", "")
        return f"AKPI-{kpi_id}-{hospital_id}-{department_id}-{date_str}"

    @staticmethod
    def _file_checksum(path: Path) -> str:
        with open(path, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()

    # -----------------------------------------------------------------------
    # 2.1 Load Inputs
    # -----------------------------------------------------------------------

    def load_inputs(self) -> Dict[str, Any]:
        """Load the authoritative processed dataset."""
        source_path = self.project_root / "data" / "processed" / "processed_operational_daily.csv"
        if not source_path.exists():
            raise FileNotFoundError(f"Source dataset not found: {source_path}")
        self.source_df = pd.read_csv(source_path)
        self.source_df["reporting_date"] = pd.to_datetime(self.source_df["reporting_date"]).dt.date
        return {"source_rows": len(self.source_df), "source_path": str(source_path)}

    # -----------------------------------------------------------------------
    # 2.2 Validate Inputs
    # -----------------------------------------------------------------------

    def validate_inputs(self) -> Dict[str, Any]:
        """Validate source schema, grain, and required fields."""
        if self.source_df is None:
            raise RuntimeError("Inputs not loaded. Call load_inputs() first.")

        results = {"valid": True, "errors": [], "warnings": []}

        # Required base fields
        base_fields = ["hospital_id", "department_id", "reporting_date", "reporting_month", "reporting_year"]
        for col in base_fields:
            if col not in self.source_df.columns:
                results["errors"].append(f"Missing base field: {col}")
                results["valid"] = False

        # Check grain uniqueness
        grain_cols = ["hospital_id", "department_id", "reporting_date"]
        if all(c in self.source_df.columns for c in grain_cols):
            dupes = self.source_df.duplicated(subset=grain_cols).sum()
            if dupes > 0:
                results["warnings"].append(f"Grain duplicates detected: {dupes}")

        # Date validity
        if "reporting_date" in self.source_df.columns:
            try:
                months = self.source_df["reporting_month"].astype(int)
                years = self.source_df["reporting_year"].astype(int)
                dates = pd.to_datetime(self.source_df["reporting_date"])
                match = (dates.dt.month == months) & (dates.dt.year == years)
                if not match.all():
                    mismatches = (~match).sum()
                    results["warnings"].append(f"Date mismatches: {mismatches}")
            except Exception as e:
                results["warnings"].append(f"Date validation error: {e}")

        return results

    # -----------------------------------------------------------------------
    # 2.3 Load Governed Definitions
    # -----------------------------------------------------------------------

    def load_governed_definitions(self) -> Dict[str, Any]:
        """Load KPI definitions from registry and configuration."""
        self.kpi_registry = build_registry_from_config(self.project_root / "config")
        self.thresholds_df = self.config_loader.load_kpi_thresholds()
        self.confidence_rules_df = self.config_loader.load_data_confidence_rules()

        loaded = {}
        for kpi_id in self.SUPPORTED_KPI_IDS:
            definition = self.kpi_registry.get(kpi_id)
            if definition is None:
                self.issues.append(
                    AnalyticalIssue(
                        issue_id=f"ISS-{kpi_id}-MISSING",
                        issue_type="Error",
                        severity="Critical",
                        issue_description=f"KPI definition not found for {kpi_id}",
                        kpi_id=kpi_id,
                        created_at=datetime.now(),
                    )
                )
                loaded[kpi_id] = "missing"
            else:
                loaded[kpi_id] = "loaded"
        return {"loaded": loaded, "threshold_rows": len(self.thresholds_df), "confidence_rows": len(self.confidence_rules_df)}

    # -----------------------------------------------------------------------
    # 2.4 Eligibility
    # -----------------------------------------------------------------------

    def determine_eligibility(self, row: pd.Series, kpi_id: str) -> Tuple[bool, Optional[str]]:
        """Determine if a source row is eligible for a given KPI."""
        mapping = self.KPI_SOURCE_FIELDS.get(kpi_id)
        if not mapping:
            return False, "Unknown KPI"

        required = mapping["required_fields"]
        for field in required:
            if field not in row.index:
                return False, f"Missing field: {field}"

        # planned_staff_count must be > 0 for both KPIs
        planned = row.get("planned_staff_count")
        if pd.isna(planned) or planned is None:
            return False, "planned_staff_count is null"
        if planned <= 0:
            return False, "planned_staff_count must be > 0"

        # For kpi_001, numerator fields must be available
        if kpi_id == "kpi_001":
            present = row.get("present_staff_count")
            replacement = row.get("replacement_staff_count")
            if pd.isna(present) and pd.isna(replacement):
                return False, "Both present_staff_count and replacement_staff_count are null"

        # For kpi_002, unapproved_absence_count must be available
        if kpi_id == "kpi_002":
            absence = row.get("unapproved_absence_count")
            if pd.isna(absence):
                return False, "unapproved_absence_count is null"

        return True, None

    # -----------------------------------------------------------------------
    # 2.5 Calculations
    # -----------------------------------------------------------------------

    def calculate_staffing_level(self, row: pd.Series) -> KPICalculationResult:
        """Calculate kpi_001 — Staffing Level."""
        kpi_id = "kpi_001"
        result = self._base_result(row, kpi_id)

        eligible, reason = self.determine_eligibility(row, kpi_id)
        if not eligible:
            result.calculation_status = self._map_eligibility_to_status(reason)
            result.kpi_value = None
            return result

        planned = float(row["planned_staff_count"])
        present = row.get("present_staff_count")
        replacement = row.get("replacement_staff_count")

        present_val = 0.0 if pd.isna(present) else float(present)
        replacement_val = 0.0 if pd.isna(replacement) else float(replacement)

        numerator = present_val + replacement_val
        denominator = planned

        result.numerator_value = numerator
        result.denominator_value = denominator
        result.kpi_value = (numerator / denominator) * 100.0
        result.calculation_status = "Calculated"
        result.unit = "Percent"

        result.numerator_evidence = KPINumeratorEvidence(
            source_field="present_staff_count + replacement_staff_count",
            source_value=numerator,
            source_record_count=1,
            aggregation_method="sum",
            eligibility_applied=True,
        )
        result.denominator_evidence = KPIDenominatorEvidence(
            source_field="planned_staff_count",
            source_value=denominator,
            source_record_count=1,
            aggregation_method="direct",
            eligibility_applied=True,
        )

        return result

    def calculate_absenteeism_rate(self, row: pd.Series) -> KPICalculationResult:
        """Calculate kpi_002 — Staff Absenteeism Rate."""
        kpi_id = "kpi_002"
        result = self._base_result(row, kpi_id)

        eligible, reason = self.determine_eligibility(row, kpi_id)
        if not eligible:
            result.calculation_status = self._map_eligibility_to_status(reason)
            result.kpi_value = None
            return result

        planned = float(row["planned_staff_count"])
        absence = row.get("unapproved_absence_count")

        absence_val = 0.0 if pd.isna(absence) else float(absence)

        numerator = absence_val
        denominator = planned

        result.numerator_value = numerator
        result.denominator_value = denominator
        result.kpi_value = (numerator / denominator) * 100.0
        result.calculation_status = "Calculated"
        result.unit = "Percent"

        result.numerator_evidence = KPINumeratorEvidence(
            source_field="unapproved_absence_count",
            source_value=numerator,
            source_record_count=1,
            aggregation_method="direct",
            eligibility_applied=True,
        )
        result.denominator_evidence = KPIDenominatorEvidence(
            source_field="planned_staff_count",
            source_value=denominator,
            source_record_count=1,
            aggregation_method="direct",
            eligibility_applied=True,
        )

        return result

    def _base_result(self, row: pd.Series, kpi_id: str) -> KPICalculationResult:
        definition = self.kpi_registry.get(kpi_id) if self.kpi_registry else None
        reporting_date = row.get("reporting_date")
        if isinstance(reporting_date, str):
            reporting_date = datetime.strptime(reporting_date, "%Y-%m-%d").date()
        return KPICalculationResult(
            kpi_id=kpi_id,
            kpi_name=definition.kpi_name if definition else "",
            hospital_id=str(row.get("hospital_id", "")),
            department_id=str(row.get("department_id", "")),
            reporting_date=reporting_date,
            unit="Percent",
            calculation_run_id=self.calculation_run_id,
            calculated_at=datetime.now(),
        )

    @staticmethod
    def _map_eligibility_to_status(reason: str) -> str:
        if "null" in reason.lower():
            return "Insufficient Data"
        if "must be > 0" in reason.lower():
            return "Zero Denominator"
        if "Missing field" in reason:
            return "Invalid Input"
        return "Not Calculated"

    # -----------------------------------------------------------------------
    # 2.6 Threshold Status
    # -----------------------------------------------------------------------

    def assign_threshold_status(self, result: KPICalculationResult) -> Dict[str, Any]:
        """Assign threshold status using configured thresholds."""
        if self.skip_threshold_status or self.thresholds_df is None or self.thresholds_df.empty:
            return {
                "threshold_status": "Not Assessed",
                "threshold_version": "",
                "threshold_approval_status": "",
                "threshold_effective_date": "",
                "threshold_is_provisional": True,
            }

        kpi_id = result.kpi_id
        kpi_thresholds = self.thresholds_df[self.thresholds_df["kpi_id"] == kpi_id]

        if kpi_thresholds.empty:
            return {
                "threshold_status": "Not Assessed",
                "threshold_version": "",
                "threshold_approval_status": "",
                "threshold_effective_date": "",
                "threshold_is_provisional": True,
            }

        # Use the first active threshold row (placeholder logic for draft thresholds)
        row = kpi_thresholds.iloc[0]
        version = str(row.get("configuration_version", "v1.0-draft"))
        approval = str(row.get("approval_status", "Draft"))
        is_provisional = approval.lower() != "approved"

        # Draft thresholds have no bound values — mark as Not Assessed
        if is_provisional:
            return {
                "threshold_status": "Not Assessed",
                "threshold_version": version,
                "threshold_approval_status": approval,
                "threshold_effective_date": str(row.get("effective_start_date", "")),
                "threshold_is_provisional": True,
            }

        # If bounds exist, evaluate (not expected for draft)
        return {
            "threshold_status": "Not Assessed",
            "threshold_version": version,
            "threshold_approval_status": approval,
            "threshold_effective_date": str(row.get("effective_start_date", "")),
            "threshold_is_provisional": is_provisional,
        }

    # -----------------------------------------------------------------------
    # 2.7 Data Confidence
    # -----------------------------------------------------------------------

    def evaluate_data_confidence(self, result: KPICalculationResult) -> DataConfidenceResult:
        """Evaluate data confidence for a KPI result."""
        if self.skip_confidence:
            return DataConfidenceResult(
                kpi_id=result.kpi_id,
                confidence_level="Unavailable",
                confidence_score=None,
                issues=["Confidence evaluation skipped"],
            )

        issues = []
        score = 100

        if result.calculation_status != "Calculated":
            return DataConfidenceResult(
                kpi_id=result.kpi_id,
                confidence_level="Unavailable",
                confidence_score=None,
                issues=[f"Calculation status: {result.calculation_status}"],
            )

        # Numerator completeness
        if result.numerator_value is None:
            score -= 30
            issues.append("Numerator is null")

        # Denominator completeness
        if result.denominator_value is None or result.denominator_value <= 0:
            score -= 40
            issues.append("Denominator invalid")

        # Source lineage
        if not result.calculation_run_id:
            score -= 10
            issues.append("Missing calculation run ID")

        if score >= 90:
            level = "High"
        elif score >= 70:
            level = "Medium"
        elif score >= 40:
            level = "Low"
        else:
            level = "Unavailable"

        return DataConfidenceResult(
            kpi_id=result.kpi_id,
            confidence_level=level,
            confidence_score=score,
            issues=issues,
        )

    # -----------------------------------------------------------------------
    # 2.8 Build Evidence / Exclusions / Lineage / Issues / Audit
    # -----------------------------------------------------------------------

    def build_evidence(self, result: KPICalculationResult) -> List[Dict[str, Any]]:
        records = []
        base = {
            "analytical_record_id": self._generate_analytical_record_id(
                result.kpi_id, result.hospital_id, result.department_id, result.reporting_date
            ),
            "kpi_id": result.kpi_id,
            "source_dataset": "processed_operational_daily",
            "source_record_id": "",
            "calculation_run_id": self.calculation_run_id,
        }

        if result.numerator_evidence:
            rec = base.copy()
            rec["evidence_type"] = "numerator"
            rec["source_field"] = result.numerator_evidence.source_field
            rec["source_value"] = result.numerator_evidence.source_value
            rec["evidence_role"] = "numerator"
            records.append(rec)

        if result.denominator_evidence:
            rec = base.copy()
            rec["evidence_type"] = "denominator"
            rec["source_field"] = result.denominator_evidence.source_field
            rec["source_value"] = result.denominator_evidence.source_value
            rec["evidence_role"] = "denominator"
            records.append(rec)

        return records

    def build_exclusions(self, row: pd.Series, kpi_id: str, reason: str) -> List[Dict[str, Any]]:
        return [
            {
                "exclusion_id": f"EXC-{uuid.uuid4().hex[:8].upper()}",
                "kpi_id": kpi_id,
                "hospital_id": str(row.get("hospital_id", "")),
                "department_id": str(row.get("department_id", "")),
                "reporting_date": str(row.get("reporting_date", "")),
                "reason_code": "ELIGIBILITY",
                "reason_description": reason,
                "source_record_id": str(row.get("operational_daily_id", "")),
                "calculation_run_id": self.calculation_run_id,
            }
        ]

    def build_lineage(self, result: KPICalculationResult, source_record_id: str) -> List[Dict[str, Any]]:
        return [
            {
                "lineage_id": f"LIN-{uuid.uuid4().hex[:8].upper()}",
                "analytical_record_id": self._generate_analytical_record_id(
                    result.kpi_id, result.hospital_id, result.department_id, result.reporting_date
                ),
                "kpi_id": result.kpi_id,
                "source_dataset": "processed_operational_daily",
                "source_record_id": source_record_id,
                "transformation_name": f"calculate_{result.kpi_id}",
                "calculation_run_id": self.calculation_run_id,
                "created_at": datetime.now().isoformat(),
            }
        ]

    def collect_issues(self) -> List[Dict[str, Any]]:
        records = []
        for issue in self.issues:
            records.append({
                "issue_id": issue.issue_id or f"ISS-{uuid.uuid4().hex[:8].upper()}",
                "severity": issue.severity,
                "issue_type": issue.issue_type,
                "kpi_id": issue.kpi_id,
                "hospital_id": "",
                "department_id": "",
                "reporting_date": "",
                "message": issue.issue_description,
                "source_dataset": issue.source_dataset,
                "source_record_id": "",
                "calculation_run_id": self.calculation_run_id,
            })
        return records

    def build_audit(self, event_type: str, event_status: str, kpi_id: str = "", details: str = "") -> Dict[str, Any]:
        return {
            "audit_id": f"AUD-{uuid.uuid4().hex[:8].upper()}",
            "event_type": event_type,
            "event_status": event_status,
            "kpi_id": kpi_id,
            "calculation_run_id": self.calculation_run_id,
            "configuration_version": "v1.0-draft",
            "threshold_version": "v1.0-draft",
            "event_time": datetime.now().isoformat(),
            "details": details,
        }

    # -----------------------------------------------------------------------
    # 2.9 Output Schema Validation
    # -----------------------------------------------------------------------

    def validate_output_schema(self, df: pd.DataFrame, schema_name: str) -> SchemaValidationResult:
        """Validate that an output DataFrame conforms to the expected schema."""
        schemas = {
            "analytical_workforce_kpi_daily": [
                "analytical_record_id", "hospital_id", "department_id", "reporting_date",
                "reporting_month", "reporting_year", "kpi_id", "kpi_name", "domain",
                "numerator_value", "denominator_value", "kpi_value", "unit",
                "calculation_status", "readiness_status", "threshold_status",
                "threshold_version", "threshold_approval_status", "threshold_is_provisional",
                "configuration_version", "data_confidence_level", "confidence_rule_version",
                "source_dataset", "source_record_id", "calculation_run_id", "calculated_at",
            ],
        }
        required = schemas.get(schema_name, [])
        present = [c for c in required if c in df.columns]
        missing = [c for c in required if c not in df.columns]
        extra = [c for c in df.columns if c not in required]
        return SchemaValidationResult(
            schema_name=schema_name,
            required_fields_present=present,
            required_fields_missing=missing,
            optional_fields_present=[],
            extra_fields=extra,
            valid=len(missing) == 0,
        )

    # -----------------------------------------------------------------------
    # 2.10 Main Execution
    # -----------------------------------------------------------------------

    def run(self) -> WorkforceKPIEngineResult:
        """Execute the full workforce KPI calculation pipeline."""
        result = WorkforceKPIEngineResult()
        manifest = CalculationRunManifest(
            calculation_run_id=self.calculation_run_id,
            run_type="calculation",
            start_time=datetime.now(),
            status="Running",
            kpi_ids=list(self.SUPPORTED_KPI_IDS),
        )

        # Record baseline checksums
        self._record_baseline_checksums()

        # Load inputs
        load_info = self.load_inputs()
        self.audit_records.append(
            AnalyticalAuditRecord(
                audit_id=f"AUD-LOAD-{uuid.uuid4().hex[:8].upper()}",
                operation="load_inputs",
                dataset_name="processed_operational_daily",
                record_count=load_info["source_rows"],
                calculation_run_id=self.calculation_run_id,
                performed_by="WorkforceKPIEngine",
                performed_at=datetime.now(),
                notes=json.dumps(load_info),
            )
        )

        # Validate inputs
        validation = self.validate_inputs()
        if not validation["valid"]:
            manifest.status = "Failed"
            manifest.end_time = datetime.now()
            result.manifest = manifest
            self.issues.append(
                AnalyticalIssue(
                    issue_id="ISS-INPUT-001",
                    issue_type="Error",
                    severity="Critical",
                    issue_description=f"Input validation failed: {validation['errors']}",
                    created_at=datetime.now(),
                )
            )
            result.issue_records = self.collect_issues()
            return result

        # Load governed definitions
        gov_info = self.load_governed_definitions()
        if any(v == "missing" for v in gov_info["loaded"].values()):
            manifest.status = "Failed"
            manifest.end_time = datetime.now()
            result.manifest = manifest
            result.issue_records = self.collect_issues()
            return result

        # Calculate KPIs row by row
        kpi_results: List[KPICalculationResult] = []
        evidence_records: List[Dict[str, Any]] = []
        exclusion_records: List[Dict[str, Any]] = []
        lineage_records: List[Dict[str, Any]] = []

        for _, row in self.source_df.iterrows():
            source_record_id = str(row.get("operational_daily_id", ""))

            # kpi_001
            res001 = self.calculate_staffing_level(row)
            threshold_meta001 = self.assign_threshold_status(res001)
            confidence001 = self.evaluate_data_confidence(res001)
            res001 = self._enrich_result(res001, threshold_meta001, confidence001)
            kpi_results.append(res001)
            evidence_records.extend(self.build_evidence(res001))
            lineage_records.extend(self.build_lineage(res001, source_record_id))
            if res001.calculation_status != "Calculated":
                eligible, reason = self.determine_eligibility(row, "kpi_001")
                if not eligible:
                    exclusion_records.extend(self.build_exclusions(row, "kpi_001", reason))

            # kpi_002
            res002 = self.calculate_absenteeism_rate(row)
            threshold_meta002 = self.assign_threshold_status(res002)
            confidence002 = self.evaluate_data_confidence(res002)
            res002 = self._enrich_result(res002, threshold_meta002, confidence002)
            kpi_results.append(res002)
            evidence_records.extend(self.build_evidence(res002))
            lineage_records.extend(self.build_lineage(res002, source_record_id))
            if res002.calculation_status != "Calculated":
                eligible, reason = self.determine_eligibility(row, "kpi_002")
                if not eligible:
                    exclusion_records.extend(self.build_exclusions(row, "kpi_002", reason))

        result.kpi_results = kpi_results
        result.evidence_records = evidence_records
        result.exclusion_records = exclusion_records
        result.lineage_records = lineage_records
        result.issue_records = self.collect_issues()

        # Build audit trail
        result.audit_records = [
            self.build_audit("calculation", "Success", kpi_id="", details=f"Calculated {len(kpi_results)} results")
        ]

        # Update manifest
        calculated_count = sum(1 for r in kpi_results if r.calculation_status == "Calculated")
        unavailable_count = sum(1 for r in kpi_results if r.calculation_status == "Insufficient Data")
        zero_denom_count = sum(1 for r in kpi_results if r.calculation_status == "Zero Denominator")
        invalid_count = sum(1 for r in kpi_results if r.calculation_status == "Invalid Input")

        manifest.issue_count = len(result.issue_records)
        manifest.exclusion_count = len(result.exclusion_records)
        manifest.status = "Completed"
        manifest.end_time = datetime.now()
        result.manifest = manifest

        # Formula verification
        result.formula_verification = self._verify_formulas(kpi_results)

        # Immutability check
        result.immutability_result = self._verify_immutability()

        return result

    def _enrich_result(
        self,
        result: KPICalculationResult,
        threshold_meta: Dict[str, Any],
        confidence: DataConfidenceResult,
    ) -> KPICalculationResult:
        result.readiness_status = "Conditionally Ready"
        result.threshold_status = threshold_meta.get("threshold_status", "Not Assessed")
        # Attach threshold metadata as custom attributes (not in dataclass — store in a dict or extend)
        # We use object.__setattr__ to bypass frozen if needed, but dataclass is not frozen.
        # Since KPICalculationResult is not frozen, we can add attributes dynamically.
        result.threshold_version = threshold_meta.get("threshold_version", "")
        result.threshold_approval_status = threshold_meta.get("threshold_approval_status", "")
        result.threshold_effective_date = threshold_meta.get("threshold_effective_date", "")
        result.threshold_is_provisional = threshold_meta.get("threshold_is_provisional", True)
        result.data_confidence_level = confidence.confidence_level
        result.confidence_score = confidence.confidence_score
        result.confidence_rule_version = "v1.0-draft"
        result.confidence_reason = "; ".join(confidence.issues) if confidence.issues else ""
        result.configuration_version = "v1.0-draft"
        result.source_dataset = "processed_operational_daily"
        result.source_record_id = ""
        return result

    # -----------------------------------------------------------------------
    # 2.11 Formula Verification
    # -----------------------------------------------------------------------

    def _verify_formulas(self, kpi_results: List[KPICalculationResult]) -> Dict[str, Any]:
        checked = 0
        matches = 0
        mismatches = 0
        max_diff = 0.0
        mismatch_details: List[Dict[str, Any]] = []

        for res in kpi_results:
            if res.calculation_status != "Calculated":
                continue
            checked += 1
            expected = None
            if res.kpi_id == "kpi_001" and res.numerator_value is not None and res.denominator_value is not None:
                expected = (res.numerator_value / res.denominator_value) * 100.0
            elif res.kpi_id == "kpi_002" and res.numerator_value is not None and res.denominator_value is not None:
                expected = (res.numerator_value / res.denominator_value) * 100.0

            if expected is not None:
                diff = abs(res.kpi_value - expected) if res.kpi_value is not None else float("inf")
                if diff < 1e-9:
                    matches += 1
                else:
                    mismatches += 1
                    max_diff = max(max_diff, diff)
                    mismatch_details.append({
                        "kpi_id": res.kpi_id,
                        "hospital_id": res.hospital_id,
                        "department_id": res.department_id,
                        "reporting_date": str(res.reporting_date),
                        "expected": expected,
                        "actual": res.kpi_value,
                        "diff": diff,
                    })

        return {
            "records_checked": checked,
            "matches": matches,
            "mismatches": mismatches,
            "max_absolute_difference": max_diff,
            "verification_status": "Passed" if mismatches == 0 else "Failed",
            "mismatch_details": mismatch_details,
        }

    # -----------------------------------------------------------------------
    # 2.12 Immutability
    # -----------------------------------------------------------------------

    def _record_baseline_checksums(self) -> None:
        processed_dir = self.project_root / "data" / "processed"
        for fname in [
            "processed_operational_daily.csv",
            "processed_workforce_daily.csv",
            "processed_staff_attendance.csv",
            "processed_staff_roster.csv",
            "processed_staffing_requirement.csv",
            "processed_staff_master.csv",
            "processed_staff_role_master.csv",
        ]:
            fpath = processed_dir / fname
            if fpath.exists():
                self._baseline_checksums[fname] = self._file_checksum(fpath)

    def _verify_immutability(self) -> Dict[str, Any]:
        result = {
            "verified": True,
            "datasets_checked": 0,
            "datasets_unchanged": 0,
            "datasets_changed": [],
            "checksum_comparison": {},
        }
        processed_dir = self.project_root / "data" / "processed"
        for fname, baseline in self._baseline_checksums.items():
            fpath = processed_dir / fname
            result["datasets_checked"] += 1
            if not fpath.exists():
                result["datasets_changed"].append(f"{fname} (missing)")
                result["verified"] = False
                continue
            current = self._file_checksum(fpath)
            match = baseline == current
            result["checksum_comparison"][fname] = {"baseline": baseline, "current": current, "match": match}
            if match:
                result["datasets_unchanged"] += 1
            else:
                result["datasets_changed"].append(fname)
                result["verified"] = False
        return result

    # -----------------------------------------------------------------------
    # 2.13 Export Helpers
    # -----------------------------------------------------------------------

    def to_daily_dataframe(self, kpi_results: List[KPICalculationResult]) -> pd.DataFrame:
        rows = []
        for res in kpi_results:
            rows.append({
                "analytical_record_id": self._generate_analytical_record_id(
                    res.kpi_id, res.hospital_id, res.department_id, res.reporting_date
                ),
                "hospital_id": res.hospital_id,
                "department_id": res.department_id,
                "reporting_date": res.reporting_date,
                "reporting_month": res.reporting_date.month if res.reporting_date else None,
                "reporting_year": res.reporting_date.year if res.reporting_date else None,
                "kpi_id": res.kpi_id,
                "kpi_name": res.kpi_name,
                "domain": "Workforce",
                "numerator_value": res.numerator_value,
                "denominator_value": res.denominator_value,
                "kpi_value": res.kpi_value,
                "unit": res.unit,
                "calculation_status": res.calculation_status,
                "readiness_status": res.readiness_status,
                "threshold_status": getattr(res, "threshold_status", "Not Assessed"),
                "threshold_version": getattr(res, "threshold_version", ""),
                "threshold_approval_status": getattr(res, "threshold_approval_status", ""),
                "threshold_is_provisional": getattr(res, "threshold_is_provisional", True),
                "configuration_version": getattr(res, "configuration_version", "v1.0-draft"),
                "data_confidence_level": getattr(res, "data_confidence_level", "Unavailable"),
                "confidence_rule_version": getattr(res, "confidence_rule_version", "v1.0-draft"),
                "source_dataset": getattr(res, "source_dataset", "processed_operational_daily"),
                "source_record_id": getattr(res, "source_record_id", ""),
                "calculation_run_id": res.calculation_run_id,
                "calculated_at": res.calculated_at.isoformat() if res.calculated_at else None,
            })
        return pd.DataFrame(rows)

    def to_evidence_dataframe(self, evidence_records: List[Dict[str, Any]]) -> pd.DataFrame:
        return pd.DataFrame(evidence_records)

    def to_exclusions_dataframe(self, exclusion_records: List[Dict[str, Any]]) -> pd.DataFrame:
        return pd.DataFrame(exclusion_records)

    def to_lineage_dataframe(self, lineage_records: List[Dict[str, Any]]) -> pd.DataFrame:
        return pd.DataFrame(lineage_records)

    def to_issues_dataframe(self, issue_records: List[Dict[str, Any]]) -> pd.DataFrame:
        return pd.DataFrame(issue_records)

    def to_audit_dataframe(self, audit_records: List[Dict[str, Any]]) -> pd.DataFrame:
        return pd.DataFrame(audit_records)
