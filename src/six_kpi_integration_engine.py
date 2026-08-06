"""
Six-KPI Integration and Status Layer (Step 2A-5).

Consolidates all six accepted analytical KPI datasets without recalculation.
Preserves original KPI values, evidence, and governance metadata.
"""

import hashlib
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

GOVERNED_KPI_IDS = {"kpi_001", "kpi_002", "kpi_003", "kpi_004", "kpi_005", "kpi_006"}

ACCEPTED_CALCULATION_STATUSES = {
    "calculated", "insufficient data", "zero denominator",
    "configuration missing", "rule pending", "invalid input", "not calculated",
}

ACCEPTED_THRESHOLD_STATUSES = {
    "green", "amber", "red", "not assessed", "unavailable", "configuration missing",
}

ACCEPTED_CONFIDENCE_LEVELS = {
    "high", "medium", "low", "unavailable", "not assessed",
}


@dataclass
class IntegrationIssueRecord:
    integration_issue_id: str
    source_issue_id: Optional[str]
    severity: str
    issue_origin: str
    issue_type: str
    kpi_id: Optional[str]
    hospital_id: Optional[str]
    department_id: Optional[str]
    reporting_date: Optional[str]
    message: str
    integration_record_id: Optional[str]
    source_record_id: Optional[str]
    integration_run_id: str


@dataclass
class IntegrationAuditRecord:
    audit_id: str
    event_type: str
    event_status: str
    integration_run_id: str
    kpi_id: Optional[str]
    configuration_version: str
    threshold_version: str
    event_time: str
    details: str


@dataclass
class IntegrationResult:
    integrated_daily_df: pd.DataFrame
    integrated_evidence_df: pd.DataFrame
    integrated_exclusions_df: pd.DataFrame
    integrated_lineage_df: pd.DataFrame
    integrated_issues_df: pd.DataFrame
    integrated_audit_df: pd.DataFrame
    coverage_df: pd.DataFrame
    reconciliation_df: pd.DataFrame
    status_summary_df: pd.DataFrame
    integration_manifest: Dict[str, Any]
    issue_records: List[IntegrationIssueRecord]
    audit_records: List[IntegrationAuditRecord]


class SixKPIIntegrationEngine:
    """Governed integration engine for six accepted KPI domains."""

    def __init__(
        self,
        project_root: str,
        integration_run_id: Optional[str] = None,
        skip_evidence_validation: bool = False,
        skip_lineage_validation: bool = False,
    ):
        self.project_root = Path(project_root)
        self.integration_run_id = integration_run_id or f"SIX-KPI-{uuid.uuid4().hex[:12].upper()}"
        self.skip_evidence_validation = skip_evidence_validation
        self.skip_lineage_validation = skip_lineage_validation
        self.issue_records: List[IntegrationIssueRecord] = []
        self.audit_records: List[IntegrationAuditRecord] = []
        self.input_checksums: Dict[str, str] = {}
        self.source_counts: Dict[str, int] = {}

    def _checksum_file(self, path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def _record_audit(
        self,
        event_type: str,
        event_status: str,
        kpi_id: Optional[str] = None,
        details: str = "",
    ) -> None:
        self.audit_records.append(
            IntegrationAuditRecord(
                audit_id=str(uuid.uuid4()),
                event_type=event_type,
                event_status=event_status,
                integration_run_id=self.integration_run_id,
                kpi_id=kpi_id,
                configuration_version="v1.0-draft",
                threshold_version="v1.0-draft",
                event_time=datetime.now().isoformat(),
                details=details,
            )
        )

    def _record_issue(
        self,
        severity: str,
        issue_type: str,
        message: str,
        kpi_id: Optional[str] = None,
        hospital_id: Optional[str] = None,
        department_id: Optional[str] = None,
        reporting_date: Optional[str] = None,
        integration_record_id: Optional[str] = None,
        source_record_id: Optional[str] = None,
        issue_origin: str = "integration",
        source_issue_id: Optional[str] = None,
    ) -> None:
        self.issue_records.append(
            IntegrationIssueRecord(
                integration_issue_id=str(uuid.uuid4()),
                source_issue_id=source_issue_id,
                severity=severity,
                issue_origin=issue_origin,
                issue_type=issue_type,
                kpi_id=kpi_id,
                hospital_id=hospital_id,
                department_id=department_id,
                reporting_date=reporting_date,
                message=message,
                integration_record_id=integration_record_id,
                source_record_id=source_record_id,
                integration_run_id=self.integration_run_id,
            )
        )

    def _safe_read_csv(self, path: Path) -> Optional[pd.DataFrame]:
        """Safely read CSV, returning None if empty or unreadable."""
        if not path.exists() or path.stat().st_size == 0:
            return None
        try:
            return pd.read_csv(path)
        except pd.errors.EmptyDataError:
            return None

    def load_accepted_inputs(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Load all accepted analytical KPI datasets."""
        domains = {
            "workforce": ["kpi_001", "kpi_002"],
            "patient_flow": ["kpi_003", "kpi_004"],
            "patient_experience": ["kpi_005", "kpi_006"],
        }

        daily_frames = []
        evidence_frames = []
        exclusion_frames = []
        lineage_frames = []
        issue_frames = []
        audit_frames = []

        for domain, kpi_ids in domains.items():
            base = self.project_root / "data" / "analytical"
            daily_path = base / f"analytical_{domain}_kpi_daily.csv"
            evidence_path = base / f"analytical_{domain}_kpi_evidence.csv"
            exclusion_path = base / f"analytical_{domain}_kpi_exclusions.csv"
            lineage_path = base / f"analytical_{domain}_kpi_lineage.csv"
            issue_path = base / f"analytical_{domain}_kpi_issues.csv"
            audit_path = base / f"analytical_{domain}_kpi_audit.csv"

            for p in [daily_path, evidence_path, exclusion_path, lineage_path, issue_path, audit_path]:
                if p.exists() and p.stat().st_size > 0:
                    self.input_checksums[str(p.relative_to(self.project_root))] = self._checksum_file(p)
                else:
                    self.input_checksums[str(p.relative_to(self.project_root))] = "EMPTY_OR_MISSING"

            daily_df = self._safe_read_csv(daily_path)
            if daily_df is None:
                raise ValueError(f"Required daily file missing or empty: {daily_path}")
            daily_df["_source_domain"] = domain
            daily_df["_source_kpi_ids"] = ",".join(kpi_ids)
            daily_frames.append(daily_df)
            self.source_counts[f"{domain}_daily"] = len(daily_df)
            self._record_audit("load", "success", details=f"Loaded {domain} daily: {len(daily_df)} rows")

            evidence_df = self._safe_read_csv(evidence_path)
            if evidence_df is not None:
                evidence_df["_source_domain"] = domain
                evidence_frames.append(evidence_df)
                self.source_counts[f"{domain}_evidence"] = len(evidence_df)
            else:
                self.source_counts[f"{domain}_evidence"] = 0

            exclusion_df = self._safe_read_csv(exclusion_path)
            if exclusion_df is not None:
                exclusion_df["_source_domain"] = domain
                exclusion_frames.append(exclusion_df)
                self.source_counts[f"{domain}_exclusions"] = len(exclusion_df)
            else:
                self.source_counts[f"{domain}_exclusions"] = 0

            lineage_df = self._safe_read_csv(lineage_path)
            if lineage_df is not None:
                lineage_df["_source_domain"] = domain
                lineage_frames.append(lineage_df)
                self.source_counts[f"{domain}_lineage"] = len(lineage_df)
            else:
                self.source_counts[f"{domain}_lineage"] = 0

            issue_df = self._safe_read_csv(issue_path)
            if issue_df is not None:
                issue_df["_source_domain"] = domain
                issue_frames.append(issue_df)
                self.source_counts[f"{domain}_issues"] = len(issue_df)
            else:
                self.source_counts[f"{domain}_issues"] = 0

            audit_df = self._safe_read_csv(audit_path)
            if audit_df is not None:
                audit_df["_source_domain"] = domain
                audit_frames.append(audit_df)
                self.source_counts[f"{domain}_audit"] = len(audit_df)
            else:
                self.source_counts[f"{domain}_audit"] = 0

        daily = pd.concat(daily_frames, ignore_index=True)
        evidence = pd.concat(evidence_frames, ignore_index=True) if evidence_frames else pd.DataFrame()
        exclusions = pd.concat(exclusion_frames, ignore_index=True) if exclusion_frames else pd.DataFrame()
        lineage = pd.concat(lineage_frames, ignore_index=True) if lineage_frames else pd.DataFrame()
        issues = pd.concat(issue_frames, ignore_index=True) if issue_frames else pd.DataFrame()
        audit = pd.concat(audit_frames, ignore_index=True) if audit_frames else pd.DataFrame()

        return daily, evidence, exclusions, lineage, issues, audit

    def validate_kpi_registry(self, daily_df: pd.DataFrame) -> pd.DataFrame:
        """Validate KPI IDs and detect unknowns."""
        unknown = daily_df[~daily_df["kpi_id"].isin(GOVERNED_KPI_IDS)]
        if not unknown.empty:
            for _, row in unknown.iterrows():
                self._record_issue(
                    severity="Error",
                    issue_type="Unknown KPI ID",
                    message=f"Unknown KPI ID {row['kpi_id']} encountered in accepted data.",
                    kpi_id=row.get("kpi_id"),
                    integration_record_id=row.get("analytical_record_id"),
                )
        return daily_df[daily_df["kpi_id"].isin(GOVERNED_KPI_IDS)].copy()

    def normalize_calculation_status(self, daily_df: pd.DataFrame) -> pd.DataFrame:
        """Normalize calculation status spelling and capitalization."""
        df = daily_df.copy()
        df["calculation_status"] = df["calculation_status"].astype(str).str.strip().str.title()
        # Standardize known variants
        mapping = {
            "Insufficient Data": "Insufficient Data",
            "Zero Denominator": "Zero Denominator",
            "Configuration Missing": "Configuration Missing",
            "Rule Pending": "Rule Pending",
            "Invalid Input": "Invalid Input",
            "Not Calculated": "Not Calculated",
            "Calculated": "Calculated",
        }
        df["calculation_status"] = df["calculation_status"].replace(mapping)
        return df

    def normalize_threshold_status(self, daily_df: pd.DataFrame) -> pd.DataFrame:
        """Normalize threshold status."""
        df = daily_df.copy()
        df["threshold_status"] = df["threshold_status"].astype(str).str.strip().str.title()
        mapping = {
            "Not Assessed": "Not Assessed",
            "Unavailable": "Unavailable",
            "Configuration Missing": "Configuration Missing",
            "Green": "Green",
            "Amber": "Amber",
            "Red": "Red",
        }
        df["threshold_status"] = df["threshold_status"].replace(mapping)
        return df

    def normalize_confidence_status(self, daily_df: pd.DataFrame) -> pd.DataFrame:
        """Normalize confidence level."""
        df = daily_df.copy()
        df["data_confidence_level"] = df["data_confidence_level"].astype(str).str.strip().str.title()
        mapping = {
            "High": "High",
            "Medium": "Medium",
            "Low": "Low",
            "Unavailable": "Unavailable",
            "Not Assessed": "Not Assessed",
        }
        df["data_confidence_level"] = df["data_confidence_level"].replace(mapping)
        return df

    def _make_integration_id(self, row: pd.Series) -> str:
        date_str = str(row["reporting_date"]).replace("-", "")
        return f"IKPI-{row['kpi_id']}-{row['hospital_id']}-{row['department_id']}-{date_str}"

    def assign_integration_status(self, daily_df: pd.DataFrame) -> pd.DataFrame:
        """Assign integration status per record."""
        df = daily_df.copy()
        statuses = []
        for _, row in df.iterrows():
            status = "Integrated"
            warnings = []

            if row["threshold_is_provisional"]:
                warnings.append("provisional_threshold")

            # Blocking validations first
            if pd.isna(row["kpi_value"]) and row["calculation_status"] == "Calculated":
                status = "Failed Validation"
                warnings.append("calculated_but_null")
            elif row["threshold_status"] in ("Green", "Amber", "Red"):
                if pd.isna(row["kpi_value"]):
                    status = "Failed Validation"
                    warnings.append("threshold_color_with_null")
                elif row["calculation_status"] != "Calculated":
                    status = "Failed Validation"
                    warnings.append("threshold_color_with_non_calculated")
            elif pd.notna(row["kpi_value"]) and row["calculation_status"] != "Calculated":
                status = "Integrated with Warning"
                warnings.append("non_calculated_with_value")
            elif row["data_confidence_level"] == "High" and pd.isna(row["kpi_value"]):
                status = "Integrated with Warning"
                warnings.append("high_confidence_unavailable")

            if row["calculation_status"] in ("Insufficient Data", "Zero Denominator", "Configuration Missing", "Rule Pending", "Invalid Input", "Not Calculated"):
                if pd.notna(row["kpi_value"]):
                    if status not in ("Failed Validation",):
                        status = "Integrated with Warning"
                    warnings.append("unavailable_status_with_value")

            if status == "Integrated" and warnings:
                status = "Integrated with Warning"

            statuses.append(status)
        df["integration_status"] = statuses
        return df

    def assign_evidence_status(self, daily_df: pd.DataFrame, evidence_df: pd.DataFrame) -> pd.DataFrame:
        """Assign evidence status per integrated record."""
        df = daily_df.copy()
        has_evidence = pd.DataFrame(columns=["analytical_record_id", "evidence_count"])
        if not evidence_df.empty and "analytical_record_id" in evidence_df.columns:
            has_evidence = evidence_df.groupby("analytical_record_id").size().reset_index(name="evidence_count")
        df = df.merge(has_evidence, on="analytical_record_id", how="left")
        df["evidence_count"] = df["evidence_count"].fillna(0).astype(int)

        def _evidence_status(row: pd.Series) -> str:
            if row["calculation_status"] != "Calculated":
                return "Unavailable"
            if row["evidence_count"] > 0:
                return "Complete"
            return "Missing"

        df["evidence_status"] = df.apply(_evidence_status, axis=1)
        return df

    def assign_lineage_status(self, daily_df: pd.DataFrame, lineage_df: pd.DataFrame) -> pd.DataFrame:
        """Assign lineage status per integrated record."""
        df = daily_df.copy()
        has_lineage = pd.DataFrame(columns=["analytical_record_id", "lineage_count"])
        if not lineage_df.empty and "analytical_record_id" in lineage_df.columns:
            has_lineage = lineage_df.groupby("analytical_record_id").size().reset_index(name="lineage_count")
        df = df.merge(has_lineage, on="analytical_record_id", how="left")
        df["lineage_count"] = df["lineage_count"].fillna(0).astype(int)

        def _lineage_status(row: pd.Series) -> str:
            if row["calculation_status"] != "Calculated":
                return "Unavailable"
            if row["lineage_count"] > 0:
                return "Complete"
            return "Broken"

        df["lineage_status"] = df.apply(_lineage_status, axis=1)
        return df

    def validate_value_status_consistency(self, daily_df: pd.DataFrame) -> pd.DataFrame:
        """Flag inconsistencies between KPI value and statuses."""
        df = daily_df.copy()
        for _, row in df.iterrows():
            if row["calculation_status"] == "Calculated" and pd.isna(row["kpi_value"]):
                self._record_issue(
                    severity="Error",
                    issue_type="Value Status Inconsistency",
                    message="Calculated status but kpi_value is null.",
                    kpi_id=row.get("kpi_id"),
                    hospital_id=row.get("hospital_id"),
                    department_id=row.get("department_id"),
                    reporting_date=row.get("reporting_date"),
                    integration_record_id=row.get("integration_record_id"),
                )
            if row["threshold_status"] in ("Green", "Amber", "Red"):
                if pd.isna(row["kpi_value"]):
                    self._record_issue(
                        severity="Error",
                        issue_type="Threshold Status Inconsistency",
                        message="Threshold color assigned but kpi_value is null.",
                        kpi_id=row.get("kpi_id"),
                        integration_record_id=row.get("integration_record_id"),
                    )
                if row["calculation_status"] != "Calculated":
                    self._record_issue(
                        severity="Error",
                        issue_type="Threshold Status Inconsistency",
                        message="Threshold color assigned but calculation_status is not Calculated.",
                        kpi_id=row.get("kpi_id"),
                        integration_record_id=row.get("integration_record_id"),
                    )
            if row["data_confidence_level"] == "High" and pd.isna(row["kpi_value"]):
                self._record_issue(
                    severity="Warning",
                    issue_type="Confidence Inconsistency",
                    message="High confidence assigned to unavailable KPI result.",
                    kpi_id=row.get("kpi_id"),
                    integration_record_id=row.get("integration_record_id"),
                )
        return df

    def detect_duplicates(self, daily_df: pd.DataFrame) -> pd.DataFrame:
        """Detect duplicate integration keys."""
        dups = daily_df[daily_df.duplicated(subset=["integration_record_id"], keep=False)]
        if not dups.empty:
            for _, row in dups.iterrows():
                self._record_issue(
                    severity="Error",
                    issue_type="Duplicate Integration Key",
                    message=f"Duplicate integration_record_id: {row['integration_record_id']}",
                    kpi_id=row.get("kpi_id"),
                    integration_record_id=row.get("integration_record_id"),
                )
        return daily_df

    def build_coverage_matrix(self, daily_df: pd.DataFrame) -> pd.DataFrame:
        """Build six-KPI coverage matrix per grain."""
        df = daily_df.copy()
        grp = df.groupby(["hospital_id", "department_id", "reporting_date"]).agg(
            present_kpi_count=("kpi_id", "nunique"),
            calculated_kpi_count=("kpi_value", lambda x: x.notna().sum()),
            unavailable_kpi_count=("kpi_value", lambda x: x.isna().sum()),
        ).reset_index()

        grp["expected_kpi_count"] = len(GOVERNED_KPI_IDS)
        grp["missing_kpi_count"] = grp["expected_kpi_count"] - grp["present_kpi_count"]
        grp["missing_kpi_count"] = grp["missing_kpi_count"].clip(lower=0)
        grp["coverage_percentage"] = (grp["present_kpi_count"] / grp["expected_kpi_count"] * 100).round(2)

        def _coverage_status(row: pd.Series) -> str:
            if row["present_kpi_count"] == row["expected_kpi_count"]:
                return "Complete"
            elif row["present_kpi_count"] > 0:
                return "Partial"
            return "No Applicable Data"

        grp["coverage_status"] = grp.apply(_coverage_status, axis=1)
        grp["reporting_month"] = pd.to_datetime(grp["reporting_date"]).dt.month
        grp["reporting_year"] = pd.to_datetime(grp["reporting_date"]).dt.year
        grp["coverage_record_id"] = grp.apply(
            lambda r: f"COV-{r['hospital_id']}-{r['department_id']}-{str(r['reporting_date']).replace('-','')}", axis=1
        )
        grp["integration_run_id"] = self.integration_run_id
        grp["created_at"] = datetime.now().isoformat()
        return grp

    def integrate_evidence(self, evidence_df: pd.DataFrame) -> pd.DataFrame:
        """Consolidate evidence with integration metadata."""
        if evidence_df.empty:
            return pd.DataFrame()
        df = evidence_df.copy()
        df["integration_record_id"] = df["analytical_record_id"].apply(
            lambda x: f"IKPI-{x.split('-', 1)[1]}" if isinstance(x, str) and x.startswith("AKPI-") else x
        )
        df["source_analytical_dataset"] = df.get("source_dataset", "")
        df["integration_run_id"] = self.integration_run_id
        # Ensure required columns exist
        for col in ["evidence_type", "evidence_role", "source_field", "source_value", "source_record_id"]:
            if col not in df.columns:
                df[col] = ""
        return df

    def integrate_exclusions(self, exclusion_df: pd.DataFrame) -> pd.DataFrame:
        """Consolidate exclusions with integration metadata."""
        if exclusion_df.empty:
            return pd.DataFrame()
        df = exclusion_df.copy()
        df["integration_exclusion_id"] = df.apply(lambda _: f"IEXC-{uuid.uuid4().hex[:8].upper()}", axis=1)
        df["source_exclusion_id"] = df.get("exclusion_id", "")
        df["exclusion_origin"] = "source_engine"
        df["integration_run_id"] = self.integration_run_id
        return df

    def integrate_lineage(self, lineage_df: pd.DataFrame) -> pd.DataFrame:
        """Consolidate lineage with integration metadata."""
        if lineage_df.empty:
            return pd.DataFrame()
        df = lineage_df.copy()
        df["integration_lineage_id"] = df.apply(lambda _: f"ILIN-{uuid.uuid4().hex[:8].upper()}", axis=1)
        df["integration_record_id"] = df["analytical_record_id"].apply(
            lambda x: f"IKPI-{x.split('-', 1)[1]}" if isinstance(x, str) and x.startswith("AKPI-") else x
        )
        df["source_analytical_dataset"] = df.get("source_dataset", "")
        df["source_analytical_record_id"] = df.get("analytical_record_id", "")
        df["upstream_source_dataset"] = df.get("source_dataset", "")
        df["upstream_source_record_id"] = df.get("source_record_id", "")
        df["integration_run_id"] = self.integration_run_id
        df["created_at"] = datetime.now().isoformat()
        return df

    def integrate_issues(self, issue_df: pd.DataFrame) -> pd.DataFrame:
        """Consolidate source issues with integration metadata."""
        if issue_df.empty:
            return pd.DataFrame()
        df = issue_df.copy()
        df["integration_issue_id"] = df.apply(lambda _: f"IISS-{uuid.uuid4().hex[:8].upper()}", axis=1)
        df["source_issue_id"] = df.get("issue_id", "")
        df["issue_origin"] = "source_engine"
        df["integration_run_id"] = self.integration_run_id
        return df

    def integrate_audit(self, audit_df: pd.DataFrame) -> pd.DataFrame:
        """Consolidate source audit with integration metadata."""
        if audit_df.empty:
            return pd.DataFrame()
        df = audit_df.copy()
        df["integration_run_id"] = self.integration_run_id
        return df

    def build_reconciliation(self, daily_df: pd.DataFrame) -> pd.DataFrame:
        """Build source-to-integrated reconciliation by KPI."""
        recs = []
        for kpi_id in sorted(GOVERNED_KPI_IDS):
            src_count = self.source_counts.get(f"{self._kpi_domain(kpi_id)}_daily", 0)
            int_count = len(daily_df[daily_df["kpi_id"] == kpi_id])
            calc_count = len(daily_df[(daily_df["kpi_id"] == kpi_id) & (daily_df["calculation_status"] == "Calculated")])
            unavail_count = len(daily_df[(daily_df["kpi_id"] == kpi_id) & (daily_df["kpi_value"].isna())])
            dup_count = daily_df[daily_df["kpi_id"] == kpi_id]["integration_record_id"].duplicated().sum()
            recs.append({
                "kpi_id": kpi_id,
                "source_analytical_dataset": f"analytical_{self._kpi_domain(kpi_id)}_kpi_daily.csv",
                "source_row_count": src_count // 2,  # each domain has 2 kpis
                "integrated_row_count": int_count,
                "calculated_count": calc_count,
                "unavailable_count": unavail_count,
                "duplicate_count": dup_count,
                "count_difference": int_count - (src_count // 2),
                "reconciliation_status": "Reconciled" if int_count == (src_count // 2) else "Mismatch",
            })
        return pd.DataFrame(recs)

    def _kpi_domain(self, kpi_id: str) -> str:
        mapping = {
            "kpi_001": "workforce",
            "kpi_002": "workforce",
            "kpi_003": "patient_flow",
            "kpi_004": "patient_flow",
            "kpi_005": "patient_experience",
            "kpi_006": "patient_experience",
        }
        return mapping.get(kpi_id, "unknown")

    def build_status_summary(self, daily_df: pd.DataFrame) -> pd.DataFrame:
        """Build overall status summary."""
        summary = []
        for kpi_id in sorted(GOVERNED_KPI_IDS):
            sub = daily_df[daily_df["kpi_id"] == kpi_id]
            summary.append({
                "kpi_id": kpi_id,
                "total_records": len(sub),
                "calculated": len(sub[sub["calculation_status"] == "Calculated"]),
                "insufficient_data": len(sub[sub["calculation_status"] == "Insufficient Data"]),
                "zero_denominator": len(sub[sub["calculation_status"] == "Zero Denominator"]),
                "other_status": len(sub[~sub["calculation_status"].isin(["Calculated", "Insufficient Data", "Zero Denominator"])]),
                "not_assessed_threshold": len(sub[sub["threshold_status"] == "Not Assessed"]),
                "high_confidence": len(sub[sub["data_confidence_level"] == "High"]),
                "medium_confidence": len(sub[sub["data_confidence_level"] == "Medium"]),
                "unavailable_confidence": len(sub[sub["data_confidence_level"] == "Unavailable"]),
                "integrated": len(sub[sub["integration_status"] == "Integrated"]),
                "integrated_with_warning": len(sub[sub["integration_status"] == "Integrated with Warning"]),
                "failed_validation": len(sub[sub["integration_status"] == "Failed Validation"]),
            })
        return pd.DataFrame(summary)

    def run(self) -> IntegrationResult:
        """Execute the full integration pipeline."""
        self._record_audit("integration_start", "started", details="Six-KPI integration started")

        daily, evidence, exclusions, lineage, issues, audit = self.load_accepted_inputs()

        # Validate KPI registry
        daily = self.validate_kpi_registry(daily)

        # Normalize statuses
        daily = self.normalize_calculation_status(daily)
        daily = self.normalize_threshold_status(daily)
        daily = self.normalize_confidence_status(daily)

        # Create integration record ID
        daily["integration_record_id"] = daily.apply(self._make_integration_id, axis=1)

        # Detect duplicates
        daily = self.detect_duplicates(daily)

        # Assign statuses
        daily = self.assign_integration_status(daily)
        if not self.skip_evidence_validation:
            daily = self.assign_evidence_status(daily, evidence)
        else:
            daily["evidence_status"] = "Unavailable"
        if not self.skip_lineage_validation:
            daily = self.assign_lineage_status(daily, lineage)
        else:
            daily["lineage_status"] = "Unavailable"

        # Validate consistency
        daily = self.validate_value_status_consistency(daily)

        # Coverage
        coverage = self.build_coverage_matrix(daily)

        # Reconciliation
        reconciliation = self.build_reconciliation(daily)

        # Status summary
        status_summary = self.build_status_summary(daily)

        # Integrate supporting datasets
        integrated_evidence = self.integrate_evidence(evidence)
        integrated_exclusions = self.integrate_exclusions(exclusions)
        integrated_lineage = self.integrate_lineage(lineage)
        integrated_issues = self.integrate_issues(issues)
        integrated_audit = self.integrate_audit(audit)

        # Add integration issues and audit
        if self.issue_records:
            issue_rows = []
            for iss in self.issue_records:
                issue_rows.append({
                    "integration_issue_id": iss.integration_issue_id,
                    "source_issue_id": iss.source_issue_id,
                    "severity": iss.severity,
                    "issue_origin": iss.issue_origin,
                    "issue_type": iss.issue_type,
                    "kpi_id": iss.kpi_id,
                    "hospital_id": iss.hospital_id,
                    "department_id": iss.department_id,
                    "reporting_date": iss.reporting_date,
                    "message": iss.message,
                    "integration_record_id": iss.integration_record_id,
                    "source_record_id": iss.source_record_id,
                    "integration_run_id": iss.integration_run_id,
                })
            integration_issues_df = pd.DataFrame(issue_rows)
            if not integrated_issues.empty:
                integrated_issues = pd.concat([integrated_issues, integration_issues_df], ignore_index=True)
            else:
                integrated_issues = integration_issues_df

        if self.audit_records:
            audit_rows = []
            for a in self.audit_records:
                audit_rows.append({
                    "audit_id": a.audit_id,
                    "event_type": a.event_type,
                    "event_status": a.event_status,
                    "integration_run_id": a.integration_run_id,
                    "kpi_id": a.kpi_id,
                    "configuration_version": a.configuration_version,
                    "threshold_version": a.threshold_version,
                    "event_time": a.event_time,
                    "details": a.details,
                })
            integration_audit_df = pd.DataFrame(audit_rows)
            if not integrated_audit.empty:
                integrated_audit = pd.concat([integrated_audit, integration_audit_df], ignore_index=True)
            else:
                integrated_audit = integration_audit_df

        # Build manifest
        manifest = {
            "integration_run_id": self.integration_run_id,
            "integration_timestamp": datetime.now().isoformat(),
            "source_checksums": self.input_checksums,
            "source_counts": self.source_counts,
            "integrated_record_count": len(daily),
            "kpi_ids": sorted(GOVERNED_KPI_IDS),
            "issue_count": len(self.issue_records),
            "audit_count": len(self.audit_records),
        }

        self._record_audit("integration_complete", "completed", details=f"Integrated {len(daily)} records")

        # Final audit append
        if self.audit_records:
            audit_rows = []
            for a in self.audit_records:
                audit_rows.append({
                    "audit_id": a.audit_id,
                    "event_type": a.event_type,
                    "event_status": a.event_status,
                    "integration_run_id": a.integration_run_id,
                    "kpi_id": a.kpi_id,
                    "configuration_version": a.configuration_version,
                    "threshold_version": a.threshold_version,
                    "event_time": a.event_time,
                    "details": a.details,
                })
            final_audit_df = pd.DataFrame(audit_rows)
            if not integrated_audit.empty:
                integrated_audit = pd.concat([integrated_audit, final_audit_df], ignore_index=True)
            else:
                integrated_audit = final_audit_df

        # Prepare final daily output columns
        output_cols = [
            "integration_record_id", "analytical_record_id", "hospital_id", "department_id",
            "reporting_date", "reporting_month", "reporting_year", "kpi_id", "kpi_name",
            "domain", "numerator_value", "denominator_value", "kpi_value", "unit",
            "calculation_status", "readiness_status", "threshold_status", "threshold_version",
            "threshold_approval_status", "threshold_is_provisional", "data_confidence_level",
            "confidence_rule_version", "source_dataset", "source_record_id",
            "calculation_run_id", "calculated_at",
        ]
        # Add confidence_is_provisional if not present
        if "confidence_is_provisional" not in daily.columns:
            daily["confidence_is_provisional"] = True
        if "integration_status" not in daily.columns:
            daily["integration_status"] = "Integrated"
        if "evidence_status" not in daily.columns:
            daily["evidence_status"] = "Unavailable"
        if "lineage_status" not in daily.columns:
            daily["lineage_status"] = "Unavailable"

        daily["source_analytical_dataset"] = daily["_source_domain"].apply(lambda d: f"analytical_{d}_kpi_daily.csv")
        daily["source_analytical_record_id"] = daily["analytical_record_id"]
        daily["source_calculation_run_id"] = daily["calculation_run_id"]
        daily["integration_run_id"] = self.integration_run_id
        daily["integrated_at"] = datetime.now().isoformat()

        final_cols = [
            "integration_record_id", "analytical_record_id", "hospital_id", "department_id",
            "reporting_date", "reporting_month", "reporting_year", "kpi_id", "kpi_name",
            "domain", "numerator_value", "denominator_value", "kpi_value", "unit",
            "calculation_status", "readiness_status", "threshold_status", "threshold_version",
            "threshold_approval_status", "threshold_is_provisional", "data_confidence_level",
            "confidence_rule_version", "confidence_is_provisional", "integration_status",
            "evidence_status", "lineage_status", "source_analytical_dataset",
            "source_analytical_record_id", "source_calculation_run_id", "integration_run_id",
            "integrated_at",
        ]
        for c in final_cols:
            if c not in daily.columns:
                daily[c] = ""
        daily_out = daily[final_cols].copy()

        return IntegrationResult(
            integrated_daily_df=daily_out,
            integrated_evidence_df=integrated_evidence,
            integrated_exclusions_df=integrated_exclusions,
            integrated_lineage_df=integrated_lineage,
            integrated_issues_df=integrated_issues,
            integrated_audit_df=integrated_audit,
            coverage_df=coverage,
            reconciliation_df=reconciliation,
            status_summary_df=status_summary,
            integration_manifest=manifest,
            issue_records=self.issue_records,
            audit_records=self.audit_records,
        )
