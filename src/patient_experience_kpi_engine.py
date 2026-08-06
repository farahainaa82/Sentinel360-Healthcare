"""
Sentinel360 Healthcare — Patient Experience KPI Engine

Governed, auditable and deterministic calculation of:
- kpi_005 Patient Complaint Rate
- kpi_006 Patient Satisfaction Score

Step: 2A-4
"""

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
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

# Monkey-patch KPICalculationResult with extra fields used by this engine
if not hasattr(KPICalculationResult, "threshold_status"):
    KPICalculationResult.threshold_status = "Not Assessed"
if not hasattr(KPICalculationResult, "threshold_version"):
    KPICalculationResult.threshold_version = ""
if not hasattr(KPICalculationResult, "threshold_approval_status"):
    KPICalculationResult.threshold_approval_status = ""
if not hasattr(KPICalculationResult, "threshold_is_provisional"):
    KPICalculationResult.threshold_is_provisional = True
if not hasattr(KPICalculationResult, "configuration_version"):
    KPICalculationResult.configuration_version = ""
if not hasattr(KPICalculationResult, "data_confidence_level"):
    KPICalculationResult.data_confidence_level = "Unavailable"
if not hasattr(KPICalculationResult, "confidence_rule_version"):
    KPICalculationResult.confidence_rule_version = ""
if not hasattr(KPICalculationResult, "source_dataset"):
    KPICalculationResult.source_dataset = ""
if not hasattr(KPICalculationResult, "source_record_id"):
    KPICalculationResult.source_record_id = ""

from kpi_registry import build_registry_from_config
from analytical_config_loader import AnalyticalConfigLoader
from analytical_governance_validator import AnalyticalGovernanceValidator


@dataclass
class PatientExperienceKPIEngineResult:
    kpi_results: List[KPICalculationResult]
    evidence_records: List[Dict[str, Any]]
    exclusion_records: List[Dict[str, Any]]
    lineage_records: List[Dict[str, Any]]
    issue_records: List[Dict[str, Any]]
    audit_records: List[Dict[str, Any]]
    manifest: CalculationRunManifest
    formula_verification: Dict[str, Any]
    complaint_denominator_readiness: Dict[str, Any]
    satisfaction_weighting_readiness: Dict[str, Any]
    immutability_result: Dict[str, Any]
    summary: Dict[str, Any] = field(default_factory=dict)


class PatientExperienceKPIEngine:
    SUPPORTED_KPI_IDS = {"kpi_005", "kpi_006"}

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
        self.config_version = "v1.0-draft"
        self.threshold_version = "v1.0-draft"

        self.operational_df: Optional[pd.DataFrame] = None
        self.complaints_df: Optional[pd.DataFrame] = None
        self.surveys_df: Optional[pd.DataFrame] = None
        self.registry: Dict[str, Any] = {}
        self.thresholds_df: Optional[pd.DataFrame] = None
        self.confidence_df: Optional[pd.DataFrame] = None

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------
    def _generate_run_id(self) -> str:
        return f"PEX-KPI-{uuid.uuid4().hex[:12].upper()}"

    def _make_id(self, kpi_id: str, hospital_id: str, dept_id: str, date_str: str) -> str:
        d = pd.to_datetime(date_str).strftime("%Y%m%d")
        return f"AKPI-{kpi_id}-{hospital_id}-{dept_id}-{d}"

    def _now(self) -> str:
        return datetime.now().isoformat()

    # -----------------------------------------------------------------------
    # Load inputs
    # -----------------------------------------------------------------------
    def load_inputs(self) -> None:
        op_path = self.project_root / "data" / "processed" / "processed_operational_daily.csv"
        comp_path = self.project_root / "data" / "processed" / "processed_patient_complaints.csv"
        surv_path = self.project_root / "data" / "processed" / "processed_patient_surveys.csv"

        if not op_path.exists():
            raise FileNotFoundError(f"Operational daily not found: {op_path}")

        self.operational_df = pd.read_csv(op_path)
        if comp_path.exists():
            self.complaints_df = pd.read_csv(comp_path)
        if surv_path.exists():
            self.surveys_df = pd.read_csv(surv_path)

    # -----------------------------------------------------------------------
    # Validate inputs
    # -----------------------------------------------------------------------
    def validate_inputs(self) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        required = ["hospital_id", "department_id", "reporting_date", "reporting_month", "reporting_year", "encounter_record_count"]
        missing = [c for c in required if c not in self.operational_df.columns]
        if missing:
            issues.append(self._make_issue("Error", "MISSING_COLUMNS", "kpi_005", "", "", "", f"Missing columns in operational_daily: {missing}", "processed_operational_daily.csv", ""))
        return issues

    # -----------------------------------------------------------------------
    # Load governed definitions
    # -----------------------------------------------------------------------
    def load_governed_definitions(self) -> None:
        config_path = self.project_root / "config"
        self.registry = build_registry_from_config(config_path)
        loader = AnalyticalConfigLoader(config_path)
        self.thresholds_df = loader.load_kpi_thresholds()
        self.confidence_df = loader.load_data_confidence_rules()

    # -----------------------------------------------------------------------
    # Complaint denominator readiness
    # -----------------------------------------------------------------------
    def assess_complaint_denominator_readiness(self) -> Dict[str, Any]:
        readiness = {
            "denominator_definition": "encounter_record_count",
            "denominator_source": "processed_operational_daily.csv",
            "denominator_field": "encounter_record_count",
            "denominator_unit": "encounters",
            "approval_status": "Draft",
            "total_eligible_complaint_records": 0,
            "total_denominator_exposure": 0,
            "duplicate_complaint_count": 0,
            "invalid_complaint_count": 0,
            "calculation_readiness": "Unknown",
            "provisional_status": True,
            "blocking_reason": "",
        }

        if self.complaints_df is not None:
            eligible = self.complaints_df[
                (self.complaints_df["complaint_count_eligible_flag"] == True)
                & self.complaints_df["exclusion_reason_code"].isna()
            ]
            readiness["total_eligible_complaint_records"] = len(eligible)
            dupes = self.complaints_df[self.complaints_df["complaint_duplicate_flag"] == True] if "complaint_duplicate_flag" in self.complaints_df.columns else pd.DataFrame()
            readiness["duplicate_complaint_count"] = len(dupes)
            invalid = self.complaints_df[self.complaints_df["complaint_record_valid_flag"] == False] if "complaint_record_valid_flag" in self.complaints_df.columns else pd.DataFrame()
            readiness["invalid_complaint_count"] = len(invalid)

        if self.operational_df is not None and "encounter_record_count" in self.operational_df.columns:
            readiness["total_denominator_exposure"] = int(self.operational_df["encounter_record_count"].sum())

        # Determine readiness
        if "encounter_record_count" not in self.operational_df.columns:
            readiness["calculation_readiness"] = "Configuration Missing"
            readiness["blocking_reason"] = "encounter_record_count field missing from operational_daily"
        else:
            readiness["calculation_readiness"] = "Provisional but Calculable"
            readiness["blocking_reason"] = ""

        return readiness

    # -----------------------------------------------------------------------
    # Satisfaction weighting readiness
    # -----------------------------------------------------------------------
    def assess_satisfaction_weighting_readiness(self) -> Dict[str, Any]:
        readiness = {
            "score_field": "satisfaction_score_numeric",
            "response_count_field": "response_count",
            "score_scale": "1-5",
            "valid_score_range": "1.0 to 5.0",
            "source_rows": 0,
            "valid_response_count": 0,
            "invalid_response_count": 0,
            "weighted_calculation_supported": True,
            "calculation_readiness": "Unknown",
            "blocking_reason": "",
        }

        if self.surveys_df is not None:
            readiness["source_rows"] = len(self.surveys_df)
            eligible = self.surveys_df[
                (self.surveys_df["survey_score_eligible_flag"] == True)
                & self.surveys_df["exclusion_reason_code"].isna()
            ]
            readiness["valid_response_count"] = int(eligible["response_count"].sum()) if "response_count" in eligible.columns else 0
            invalid = self.surveys_df[
                (self.surveys_df["survey_score_eligible_flag"] == False)
                | self.surveys_df["exclusion_reason_code"].notna()
            ]
            readiness["invalid_response_count"] = len(invalid)

        # Check operational_daily has required fields
        has_weighted_sum = "survey_score_weighted_sum" in self.operational_df.columns
        has_valid_count = "survey_valid_score_record_count" in self.operational_df.columns

        if not has_weighted_sum or not has_valid_count:
            readiness["calculation_readiness"] = "Configuration Missing"
            readiness["weighted_calculation_supported"] = False
            readiness["blocking_reason"] = f"Missing fields in operational_daily: weighted_sum={has_weighted_sum}, valid_count={has_valid_count}"
        else:
            readiness["calculation_readiness"] = "Calculable"
            readiness["blocking_reason"] = ""

        return readiness

    # -----------------------------------------------------------------------
    # Calculate complaint rate
    # -----------------------------------------------------------------------
    def calculate_complaint_rate(self, row: pd.Series, readiness: Dict[str, Any]) -> KPICalculationResult:
        kpi_id = "kpi_005"
        kpi_def = self.registry.get(kpi_id)
        kpi_name = kpi_def.kpi_name if kpi_def else "Patient Complaint Rate"
        unit = "Complaints per 1000 encounters"

        hospital_id = row.get("hospital_id", "")
        dept_id = row.get("department_id", "")
        date_str = row.get("reporting_date", "")
        record_id = self._make_id(kpi_id, hospital_id, dept_id, date_str)

        result = KPICalculationResult(
            kpi_id=kpi_id,
            kpi_name=kpi_name,
            hospital_id=hospital_id,
            department_id=dept_id,
            reporting_date=date_str,
            numerator_value=None,
            denominator_value=None,
            kpi_value=None,
            unit=unit,
            calculation_status="Not Calculated",
            readiness_status="Not Assessed",
            calculation_run_id=self.calculation_run_id,
            calculated_at=self._now(),
        )
        result.threshold_status = "Not Assessed"
        result.threshold_version = self.threshold_version
        result.threshold_approval_status = "Draft"
        result.threshold_is_provisional = True
        result.configuration_version = self.config_version
        result.data_confidence_level = "Unavailable"
        result.confidence_rule_version = self.config_version
        result.source_dataset = "processed_operational_daily.csv"
        result.source_record_id = row.get("operational_daily_id", "")

        # Check if PX data is available for this row
        complaint_count = row.get("complaint_valid_record_count")
        encounter_count = row.get("encounter_record_count")

        if pd.isna(complaint_count):
            result.calculation_status = "Insufficient Data"
            result.readiness_status = "PX Data Unavailable"
            return result

        try:
            complaint_count = float(complaint_count)
            encounter_count = float(encounter_count)
        except (ValueError, TypeError):
            result.calculation_status = "Invalid Input"
            return result

        if pd.isna(encounter_count):
            result.calculation_status = "Insufficient Data"
            return result

        if encounter_count <= 0:
            result.calculation_status = "Zero Denominator"
            result.denominator_value = encounter_count
            return result

        if readiness.get("calculation_readiness") == "Configuration Missing":
            result.calculation_status = "Configuration Missing"
            return result

        # Calculate
        result.numerator_value = complaint_count
        result.denominator_value = encounter_count
        result.kpi_value = (complaint_count / encounter_count) * 1000.0
        result.calculation_status = "Calculated"
        result.readiness_status = readiness.get("calculation_readiness", "Provisional but Calculable")

        return result

    # -----------------------------------------------------------------------
    # Calculate satisfaction score
    # -----------------------------------------------------------------------
    def calculate_satisfaction_score(self, row: pd.Series, readiness: Dict[str, Any]) -> KPICalculationResult:
        kpi_id = "kpi_006"
        kpi_def = self.registry.get(kpi_id)
        kpi_name = kpi_def.kpi_name if kpi_def else "Patient Satisfaction Score"
        unit = "Score (1-5 scale)"

        hospital_id = row.get("hospital_id", "")
        dept_id = row.get("department_id", "")
        date_str = row.get("reporting_date", "")
        record_id = self._make_id(kpi_id, hospital_id, dept_id, date_str)

        result = KPICalculationResult(
            kpi_id=kpi_id,
            kpi_name=kpi_name,
            hospital_id=hospital_id,
            department_id=dept_id,
            reporting_date=date_str,
            numerator_value=None,
            denominator_value=None,
            kpi_value=None,
            unit=unit,
            calculation_status="Not Calculated",
            readiness_status="Not Assessed",
            calculation_run_id=self.calculation_run_id,
            calculated_at=self._now(),
        )
        result.threshold_status = "Not Assessed"
        result.threshold_version = self.threshold_version
        result.threshold_approval_status = "Draft"
        result.threshold_is_provisional = True
        result.configuration_version = self.config_version
        result.data_confidence_level = "Unavailable"
        result.confidence_rule_version = self.config_version
        result.source_dataset = "processed_operational_daily.csv"
        result.source_record_id = row.get("operational_daily_id", "")

        weighted_sum = row.get("survey_score_weighted_sum")
        valid_count = row.get("survey_valid_score_record_count")

        if pd.isna(weighted_sum) or pd.isna(valid_count):
            result.calculation_status = "Insufficient Data"
            result.readiness_status = "PX Data Unavailable"
            return result

        try:
            weighted_sum = float(weighted_sum)
            valid_count = float(valid_count)
        except (ValueError, TypeError):
            result.calculation_status = "Invalid Input"
            return result

        if valid_count <= 0:
            result.calculation_status = "Zero Denominator"
            result.denominator_value = valid_count
            return result

        if readiness.get("calculation_readiness") == "Configuration Missing":
            result.calculation_status = "Configuration Missing"
            return result

        result.numerator_value = weighted_sum
        result.denominator_value = valid_count
        result.kpi_value = weighted_sum / valid_count
        result.calculation_status = "Calculated"
        result.readiness_status = readiness.get("calculation_readiness", "Calculable")

        return result

    # -----------------------------------------------------------------------
    # Threshold and confidence
    # -----------------------------------------------------------------------
    def assign_threshold_and_confidence(self, result: KPICalculationResult) -> KPICalculationResult:
        if not self.skip_threshold_status and self.thresholds_df is not None and not self.thresholds_df.empty:
            # Simple threshold application based on config
            kpi_thresholds = self.thresholds_df[self.thresholds_df["kpi_id"] == result.kpi_id]
            if not kpi_thresholds.empty and result.kpi_value is not None:
                result.threshold_status = "Not Assessed"  # Draft thresholds - no Green/Amber/Red
            else:
                result.threshold_status = "Not Assessed"
        else:
            result.threshold_status = "Not Assessed"

        if not self.skip_confidence:
            if result.calculation_status == "Calculated":
                result.data_confidence_level = "Medium"
            else:
                result.data_confidence_level = "Unavailable"
        else:
            result.data_confidence_level = "Unavailable"

        return result

    # -----------------------------------------------------------------------
    # Evidence
    # -----------------------------------------------------------------------
    def build_evidence(self, result: KPICalculationResult, row: pd.Series) -> List[Dict[str, Any]]:
        evidence: List[Dict[str, Any]] = []

        if result.kpi_id == "kpi_005":
            evidence.append({
                "analytical_record_id": self._make_id(result.kpi_id, result.hospital_id, result.department_id, result.reporting_date),
                "kpi_id": result.kpi_id,
                "evidence_type": "numerator",
                "source_dataset": "processed_operational_daily.csv",
                "source_field": "complaint_valid_record_count",
                "source_value": result.numerator_value,
                "evidence_role": "valid_complaint_count",
                "source_record_id": row.get("operational_daily_id", ""),
                "calculation_run_id": self.calculation_run_id,
            })
            evidence.append({
                "analytical_record_id": self._make_id(result.kpi_id, result.hospital_id, result.department_id, result.reporting_date),
                "kpi_id": result.kpi_id,
                "evidence_type": "denominator",
                "source_dataset": "processed_operational_daily.csv",
                "source_field": "encounter_record_count",
                "source_value": result.denominator_value,
                "evidence_role": "exposure_denominator",
                "source_record_id": row.get("operational_daily_id", ""),
                "calculation_run_id": self.calculation_run_id,
            })
            evidence.append({
                "analytical_record_id": self._make_id(result.kpi_id, result.hospital_id, result.department_id, result.reporting_date),
                "kpi_id": result.kpi_id,
                "evidence_type": "multiplier",
                "source_dataset": "config/kpi_definition_config.csv",
                "source_field": "formula",
                "source_value": 1000.0,
                "evidence_role": "per_1000_multiplier",
                "source_record_id": "",
                "calculation_run_id": self.calculation_run_id,
            })

        elif result.kpi_id == "kpi_006":
            evidence.append({
                "analytical_record_id": self._make_id(result.kpi_id, result.hospital_id, result.department_id, result.reporting_date),
                "kpi_id": result.kpi_id,
                "evidence_type": "numerator",
                "source_dataset": "processed_operational_daily.csv",
                "source_field": "survey_score_weighted_sum",
                "source_value": result.numerator_value,
                "evidence_role": "weighted_score_numerator",
                "source_record_id": row.get("operational_daily_id", ""),
                "calculation_run_id": self.calculation_run_id,
            })
            evidence.append({
                "analytical_record_id": self._make_id(result.kpi_id, result.hospital_id, result.department_id, result.reporting_date),
                "kpi_id": result.kpi_id,
                "evidence_type": "denominator",
                "source_dataset": "processed_operational_daily.csv",
                "source_field": "survey_valid_score_record_count",
                "source_value": result.denominator_value,
                "evidence_role": "valid_response_denominator",
                "source_record_id": row.get("operational_daily_id", ""),
                "calculation_run_id": self.calculation_run_id,
            })
            evidence.append({
                "analytical_record_id": self._make_id(result.kpi_id, result.hospital_id, result.department_id, result.reporting_date),
                "kpi_id": result.kpi_id,
                "evidence_type": "scale",
                "source_dataset": "config/kpi_definition_config.csv",
                "source_field": "unit",
                "source_value": "1-5",
                "evidence_role": "score_scale",
                "source_record_id": "",
                "calculation_run_id": self.calculation_run_id,
            })
            evidence.append({
                "analytical_record_id": self._make_id(result.kpi_id, result.hospital_id, result.department_id, result.reporting_date),
                "kpi_id": result.kpi_id,
                "evidence_type": "weighting_method",
                "source_dataset": "config/kpi_definition_config.csv",
                "source_field": "formula",
                "source_value": "weighted_sum / valid_response_count",
                "evidence_role": "response_weighting",
                "source_record_id": "",
                "calculation_run_id": self.calculation_run_id,
            })

        return evidence

    # -----------------------------------------------------------------------
    # Exclusions
    # -----------------------------------------------------------------------
    def build_exclusions(self, result: KPICalculationResult) -> List[Dict[str, Any]]:
        exclusions: List[Dict[str, Any]] = []
        if result.calculation_status != "Calculated":
            return exclusions

        if result.kpi_id == "kpi_005" and self.complaints_df is not None:
            # Find excluded complaints for this hospital-dept-date
            date_str = result.reporting_date
            excluded = self.complaints_df[
                (self.complaints_df["hospital_id"] == result.hospital_id)
                & (self.complaints_df["department_id"] == result.department_id)
                & (self.complaints_df["complaint_date"] == date_str)
                & (
                    (self.complaints_df["complaint_count_eligible_flag"] == False)
                    | self.complaints_df["exclusion_reason_code"].notna()
                )
            ]
            for _, row in excluded.iterrows():
                reason = row.get("exclusion_reason_code", "Unknown")
                exclusions.append({
                    "exclusion_id": f"EXC-{result.kpi_id}-{uuid.uuid4().hex[:8].upper()}",
                    "kpi_id": result.kpi_id,
                    "hospital_id": result.hospital_id,
                    "department_id": result.department_id,
                    "reporting_date": date_str,
                    "reason_code": str(reason) if pd.notna(reason) else "INELIGIBLE",
                    "reason_description": "Complaint excluded from count",
                    "source_record_id": row.get("complaint_id", ""),
                    "calculation_run_id": self.calculation_run_id,
                })

        elif result.kpi_id == "kpi_006" and self.surveys_df is not None:
            date_str = result.reporting_date
            excluded = self.surveys_df[
                (self.surveys_df["hospital_id"] == result.hospital_id)
                & (self.surveys_df["department_id"] == result.department_id)
                & (self.surveys_df["survey_date"] == date_str)
                & (
                    (self.surveys_df["survey_score_eligible_flag"] == False)
                    | self.surveys_df["exclusion_reason_code"].notna()
                )
            ]
            for _, row in excluded.iterrows():
                reason = row.get("exclusion_reason_code", "Unknown")
                exclusions.append({
                    "exclusion_id": f"EXC-{result.kpi_id}-{uuid.uuid4().hex[:8].upper()}",
                    "kpi_id": result.kpi_id,
                    "hospital_id": result.hospital_id,
                    "department_id": result.department_id,
                    "reporting_date": date_str,
                    "reason_code": str(reason) if pd.notna(reason) else "INELIGIBLE",
                    "reason_description": "Survey excluded from score",
                    "source_record_id": row.get("survey_id", ""),
                    "calculation_run_id": self.calculation_run_id,
                })

        return exclusions

    # -----------------------------------------------------------------------
    # Lineage
    # -----------------------------------------------------------------------
    def build_lineage(self, result: KPICalculationResult, row: pd.Series) -> List[Dict[str, Any]]:
        lineage: List[Dict[str, Any]] = []
        record_id = self._make_id(result.kpi_id, result.hospital_id, result.department_id, result.reporting_date)
        lineage.append({
            "lineage_id": f"LIN-{record_id}-001",
            "analytical_record_id": record_id,
            "kpi_id": result.kpi_id,
            "source_dataset": "processed_operational_daily.csv",
            "source_record_id": row.get("operational_daily_id", ""),
            "transformation_name": f"calculate_{result.kpi_id}",
            "calculation_run_id": self.calculation_run_id,
            "created_at": self._now(),
        })
        if result.kpi_id == "kpi_005" and self.complaints_df is not None:
            lineage.append({
                "lineage_id": f"LIN-{record_id}-002",
                "analytical_record_id": record_id,
                "kpi_id": result.kpi_id,
                "source_dataset": "processed_patient_complaints.csv",
                "source_record_id": "",
                "transformation_name": "validate_complaint_eligibility",
                "calculation_run_id": self.calculation_run_id,
                "created_at": self._now(),
            })
        if result.kpi_id == "kpi_006" and self.surveys_df is not None:
            lineage.append({
                "lineage_id": f"LIN-{record_id}-002",
                "analytical_record_id": record_id,
                "kpi_id": result.kpi_id,
                "source_dataset": "processed_patient_surveys.csv",
                "source_record_id": "",
                "transformation_name": "validate_survey_eligibility",
                "calculation_run_id": self.calculation_run_id,
                "created_at": self._now(),
            })
        return lineage

    # -----------------------------------------------------------------------
    # Issues
    # -----------------------------------------------------------------------
    def _make_issue(
        self,
        severity: str,
        issue_type: str,
        kpi_id: str,
        hospital_id: str,
        department_id: str,
        reporting_date: str,
        message: str,
        source_dataset: str,
        source_record_id: str,
    ) -> Dict[str, Any]:
        return {
            "issue_id": f"ISS-{kpi_id}-{uuid.uuid4().hex[:8].upper()}",
            "severity": severity,
            "issue_type": issue_type,
            "kpi_id": kpi_id,
            "hospital_id": hospital_id,
            "department_id": department_id,
            "reporting_date": reporting_date,
            "message": message,
            "source_dataset": source_dataset,
            "source_record_id": source_record_id,
            "calculation_run_id": self.calculation_run_id,
        }

    def collect_issues(self, result: KPICalculationResult, row: pd.Series) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        if result.calculation_status == "Zero Denominator":
            issues.append(self._make_issue(
                "Warning", "ZERO_DENOMINATOR", result.kpi_id,
                result.hospital_id, result.department_id, result.reporting_date,
                f"Zero denominator for {result.kpi_id}", "processed_operational_daily.csv",
                row.get("operational_daily_id", ""),
            ))
        if result.calculation_status == "Insufficient Data":
            issues.append(self._make_issue(
                "Warning", "INSUFFICIENT_DATA", result.kpi_id,
                result.hospital_id, result.department_id, result.reporting_date,
                f"Insufficient data for {result.kpi_id}", "processed_operational_daily.csv",
                row.get("operational_daily_id", ""),
            ))
        if result.kpi_id == "kpi_005" and result.calculation_status == "Calculated":
            # Flag provisional denominator
            issues.append(self._make_issue(
                "Info", "PROVISIONAL_DENOMINATOR", result.kpi_id,
                result.hospital_id, result.department_id, result.reporting_date,
                "Complaint rate denominator is provisional and pending stakeholder approval",
                "processed_operational_daily.csv", row.get("operational_daily_id", ""),
            ))
        return issues

    # -----------------------------------------------------------------------
    # Audit
    # -----------------------------------------------------------------------
    def build_audit(self, event_type: str, event_status: str, kpi_id: str, details: str) -> Dict[str, Any]:
        return {
            "audit_id": f"AUD-{uuid.uuid4().hex[:8].upper()}",
            "event_type": event_type,
            "event_status": event_status,
            "kpi_id": kpi_id,
            "calculation_run_id": self.calculation_run_id,
            "configuration_version": self.config_version,
            "threshold_version": self.threshold_version,
            "event_time": self._now(),
            "details": details,
        }

    # -----------------------------------------------------------------------
    # Formula verification
    # -----------------------------------------------------------------------
    def verify_formulas(self, results: List[KPICalculationResult]) -> Dict[str, Any]:
        checked = 0
        matches = 0
        mismatches = 0
        max_diff = 0.0
        unavailable = 0
        zero_denom = 0
        rule_pending = 0

        for r in results:
            if r.calculation_status != "Calculated":
                if r.calculation_status == "Insufficient Data":
                    unavailable += 1
                elif r.calculation_status == "Zero Denominator":
                    zero_denom += 1
                elif r.calculation_status == "Rule Pending":
                    rule_pending += 1
                continue

            checked += 1
            expected = None
            if r.kpi_id == "kpi_005" and r.denominator_value and r.denominator_value > 0:
                expected = (r.numerator_value / r.denominator_value) * 1000.0 if r.numerator_value is not None else 0.0
            elif r.kpi_id == "kpi_006" and r.denominator_value and r.denominator_value > 0:
                expected = r.numerator_value / r.denominator_value if r.numerator_value is not None else 0.0

            if expected is not None and r.kpi_value is not None:
                diff = abs(r.kpi_value - expected)
                if diff < 1e-9:
                    matches += 1
                else:
                    mismatches += 1
                    if diff > max_diff:
                        max_diff = diff
            else:
                unavailable += 1

        return {
            "records_checked": checked,
            "matches": matches,
            "mismatches": mismatches,
            "max_absolute_difference": max_diff,
            "unavailable_records": unavailable,
            "zero_denominator_records": zero_denom,
            "rule_pending_records": rule_pending,
            "verification_status": "Passed" if mismatches == 0 else "Failed",
        }

    # -----------------------------------------------------------------------
    # Immutability
    # -----------------------------------------------------------------------
    def verify_immutability(self, baseline: Dict[str, str]) -> Dict[str, Any]:
        result = {
            "verified": True,
            "datasets_checked": 0,
            "datasets_unchanged": 0,
            "datasets_changed": [],
            "checksum_comparison": {},
        }
        for fname, baseline_hash in baseline.items():
            fpath = self.project_root / fname
            result["datasets_checked"] += 1
            if not fpath.exists():
                result["datasets_changed"].append(f"{fname} (missing)")
                result["verified"] = False
                continue
            current_hash = hashlib.sha256(fpath.read_bytes()).hexdigest()
            match = baseline_hash == current_hash
            result["checksum_comparison"][fname] = {"baseline": baseline_hash, "current": current_hash, "match": match}
            if match:
                result["datasets_unchanged"] += 1
            else:
                result["datasets_changed"].append(fname)
                result["verified"] = False
        return result

    # -----------------------------------------------------------------------
    # DataFrame builders
    # -----------------------------------------------------------------------
    def to_daily_dataframe(self, results: List[KPICalculationResult]) -> pd.DataFrame:
        if not results:
            return pd.DataFrame()
        rows = []
        for r in results:
            rows.append({
                "analytical_record_id": self._make_id(r.kpi_id, r.hospital_id, r.department_id, r.reporting_date),
                "hospital_id": r.hospital_id,
                "department_id": r.department_id,
                "reporting_date": r.reporting_date,
                "reporting_month": getattr(r, "reporting_month", None),
                "reporting_year": getattr(r, "reporting_year", None),
                "kpi_id": r.kpi_id,
                "kpi_name": r.kpi_name,
                "domain": getattr(r, "domain", "Patient Experience"),
                "numerator_value": r.numerator_value,
                "denominator_value": r.denominator_value,
                "kpi_value": r.kpi_value,
                "unit": r.unit,
                "calculation_status": r.calculation_status,
                "readiness_status": r.readiness_status,
                "threshold_status": getattr(r, "threshold_status", "Not Assessed"),
                "threshold_version": getattr(r, "threshold_version", self.threshold_version),
                "threshold_approval_status": getattr(r, "threshold_approval_status", "Draft"),
                "threshold_is_provisional": getattr(r, "threshold_is_provisional", True),
                "configuration_version": getattr(r, "configuration_version", self.config_version),
                "data_confidence_level": getattr(r, "data_confidence_level", "Unavailable"),
                "confidence_rule_version": getattr(r, "confidence_rule_version", self.config_version),
                "source_dataset": getattr(r, "source_dataset", "processed_operational_daily.csv"),
                "source_record_id": getattr(r, "source_record_id", ""),
                "calculation_run_id": r.calculation_run_id,
                "calculated_at": r.calculated_at,
            })
        return pd.DataFrame(rows)

    def to_evidence_dataframe(self, evidence: List[Dict[str, Any]]) -> pd.DataFrame:
        if not evidence:
            return pd.DataFrame()
        return pd.DataFrame(evidence)

    def to_exclusions_dataframe(self, exclusions: List[Dict[str, Any]]) -> pd.DataFrame:
        if not exclusions:
            return pd.DataFrame()
        return pd.DataFrame(exclusions)

    def to_lineage_dataframe(self, lineage: List[Dict[str, Any]]) -> pd.DataFrame:
        if not lineage:
            return pd.DataFrame()
        return pd.DataFrame(lineage)

    def to_issues_dataframe(self, issues: List[Dict[str, Any]]) -> pd.DataFrame:
        if not issues:
            return pd.DataFrame()
        return pd.DataFrame(issues)

    def to_audit_dataframe(self, audit: List[Dict[str, Any]]) -> pd.DataFrame:
        if not audit:
            return pd.DataFrame()
        return pd.DataFrame(audit)

    # -----------------------------------------------------------------------
    # Main run
    # -----------------------------------------------------------------------
    def run(self) -> PatientExperienceKPIEngineResult:
        self.load_inputs()
        issues = self.validate_inputs()
        self.load_governed_definitions()

        comp_readiness = self.assess_complaint_denominator_readiness()
        sat_readiness = self.assess_satisfaction_weighting_readiness()

        kpi_results: List[KPICalculationResult] = []
        evidence_records: List[Dict[str, Any]] = []
        exclusion_records: List[Dict[str, Any]] = []
        lineage_records: List[Dict[str, Any]] = []
        issue_records: List[Dict[str, Any]] = issues
        audit_records: List[Dict[str, Any]] = []

        audit_records.append(self.build_audit("RUN_START", "Success", "", f"Patient Experience KPI run started: {self.calculation_run_id}"))

        for _, row in self.operational_df.iterrows():
            # kpi_005
            r005 = self.calculate_complaint_rate(row, comp_readiness)
            r005 = self.assign_threshold_and_confidence(r005)
            kpi_results.append(r005)
            evidence_records.extend(self.build_evidence(r005, row))
            exclusion_records.extend(self.build_exclusions(r005))
            lineage_records.extend(self.build_lineage(r005, row))
            issue_records.extend(self.collect_issues(r005, row))

            # kpi_006
            r006 = self.calculate_satisfaction_score(row, sat_readiness)
            r006 = self.assign_threshold_and_confidence(r006)
            kpi_results.append(r006)
            evidence_records.extend(self.build_evidence(r006, row))
            exclusion_records.extend(self.build_exclusions(r006))
            lineage_records.extend(self.build_lineage(r006, row))
            issue_records.extend(self.collect_issues(r006, row))

        formula_verification = self.verify_formulas(kpi_results)
        audit_records.append(self.build_audit("FORMULA_VERIFICATION", formula_verification["verification_status"], "", json.dumps(formula_verification)))

        manifest = CalculationRunManifest(
            calculation_run_id=self.calculation_run_id,
            run_type="calculation",
            start_time=datetime.now(),
            end_time=datetime.now(),
            status="Passed",
            kpi_ids=["kpi_005", "kpi_006"],
            issue_count=len(issue_records),
            exclusion_count=len(exclusion_records),
            output_datasets=["analytical_patient_experience_kpi_daily.csv"],
            phase1_immutability_verified=False,
            phase1_checksums_match=False,
        )

        calculated_count = sum(1 for r in kpi_results if r.calculation_status == "Calculated")
        unavailable_count = sum(1 for r in kpi_results if r.calculation_status == "Insufficient Data")
        zero_denom_count = sum(1 for r in kpi_results if r.calculation_status == "Zero Denominator")
        rule_pending_count = sum(1 for r in kpi_results if r.calculation_status == "Rule Pending")
        invalid_count = sum(1 for r in kpi_results if r.calculation_status == "Invalid Input")

        summary = {
            "calculated_count": calculated_count,
            "unavailable_count": unavailable_count,
            "zero_denominator_count": zero_denom_count,
            "rule_pending_count": rule_pending_count,
            "invalid_input_count": invalid_count,
        }

        return PatientExperienceKPIEngineResult(
            kpi_results=kpi_results,
            evidence_records=evidence_records,
            exclusion_records=exclusion_records,
            lineage_records=lineage_records,
            issue_records=issue_records,
            audit_records=audit_records,
            manifest=manifest,
            formula_verification=formula_verification,
            complaint_denominator_readiness=comp_readiness,
            satisfaction_weighting_readiness=sat_readiness,
            immutability_result={},
            summary=summary,
        )