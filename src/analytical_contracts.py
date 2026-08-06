"""
Sentinel360 Healthcare — Analytical Contracts

Defines contracts, interfaces and validation gates for the analytical layer.
No actual KPI calculation is performed in Step 2A-1.

Step: 2A-1
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


# ---------------------------------------------------------------------------
# 1. KPI Registry Contract
# ---------------------------------------------------------------------------

class KPIRegistryContract(ABC):
    """Contract for KPI registry implementations."""

    @abstractmethod
    def get_kpi_definition(self, kpi_id: str) -> Optional[Dict[str, Any]]:
        """Return the governed definition for a KPI ID."""
        ...

    @abstractmethod
    def list_kpi_ids(self) -> List[str]:
        """Return all registered KPI IDs."""
        ...

    @abstractmethod
    def validate_kpi_completeness(self) -> Dict[str, Any]:
        """Validate that all required KPI definitions are present."""
        ...


# ---------------------------------------------------------------------------
# 2. Configuration Loader Contract
# ---------------------------------------------------------------------------

class ConfigurationLoaderContract(ABC):
    """Contract for analytical configuration loaders."""

    @abstractmethod
    def load_kpi_definitions(self) -> pd.DataFrame:
        """Load KPI definition configuration."""
        ...

    @abstractmethod
    def load_kpi_thresholds(self) -> pd.DataFrame:
        """Load KPI threshold configuration."""
        ...

    @abstractmethod
    def load_data_confidence_rules(self) -> pd.DataFrame:
        """Load data-confidence rules."""
        ...

    @abstractmethod
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate loaded configuration and return issues."""
        ...


# ---------------------------------------------------------------------------
# 3. Governance Validator Contract
# ---------------------------------------------------------------------------

class GovernanceValidatorContract(ABC):
    """Contract for analytical governance validators."""

    @abstractmethod
    def validate_source_field_availability(self) -> Dict[str, Any]:
        """Validate that required source fields exist in processed datasets."""
        ...

    @abstractmethod
    def validate_threshold_configuration(self) -> Dict[str, Any]:
        """Validate threshold configuration for all KPIs."""
        ...

    @abstractmethod
    def determine_kpi_readiness(self) -> Dict[str, str]:
        """Determine readiness status for each KPI."""
        ...

    @abstractmethod
    def validate_no_calculations_performed(self) -> bool:
        """Confirm no KPI calculations occurred during this step."""
        ...


# ---------------------------------------------------------------------------
# 4. Calculation Gate Contract
# ---------------------------------------------------------------------------

@dataclass
class CalculationGateResult:
    """Result of evaluating the calculation gate."""

    calculation_allowed: bool = False
    blocking_reason: str = ""
    allowed_kpi_ids: List[str] = field(default_factory=list)
    blocked_kpi_ids: List[str] = field(default_factory=list)
    calculation_run_id: str = ""
    readiness_summary: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "calculation_allowed": self.calculation_allowed,
            "blocking_reason": self.blocking_reason,
            "allowed_kpi_ids": self.allowed_kpi_ids,
            "blocked_kpi_ids": self.blocked_kpi_ids,
            "calculation_run_id": self.calculation_run_id,
            "readiness_summary": self.readiness_summary,
        }


class CalculationGateContract:
    """Contract that determines whether KPI calculation is permitted.

    Calculation is allowed only when:
      - all governance checks pass, AND
      - no KPI is marked Blocked, AND
      - Phase 1 immutability is confirmed.
    """

    @staticmethod
    def check_calculation_gate(
        governance_results: Dict[str, Any],
        readiness_summary: Dict[str, str],
        phase1_immutable: bool = False,
    ) -> CalculationGateResult:
        result = CalculationGateResult()
        result.readiness_summary = readiness_summary

        if not phase1_immutable:
            result.blocking_reason = "Phase 1 processed datasets are not confirmed immutable."
            result.blocked_kpi_ids = list(readiness_summary.keys())
            return result

        blocked = [kpi for kpi, status in readiness_summary.items() if status == "Blocked"]
        if blocked:
            result.blocking_reason = f"Blocked KPIs: {', '.join(blocked)}"
            result.blocked_kpi_ids = blocked
            result.allowed_kpi_ids = [kpi for kpi, status in readiness_summary.items() if status != "Blocked"]
            return result

        result.calculation_allowed = True
        result.allowed_kpi_ids = list(readiness_summary.keys())
        return result


# ---------------------------------------------------------------------------
# 5. Immutability Verification Contract
# ---------------------------------------------------------------------------

@dataclass
class ImmutabilityVerificationResult:
    """Result of verifying Phase 1 dataset immutability."""

    verified: bool = False
    datasets_checked: int = 0
    datasets_unchanged: int = 0
    datasets_changed: List[str] = field(default_factory=list)
    checksum_comparison: Dict[str, Dict[str, str]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verified": self.verified,
            "datasets_checked": self.datasets_checked,
            "datasets_unchanged": self.datasets_unchanged,
            "datasets_changed": self.datasets_changed,
        }


class ImmutabilityVerificationContract:
    """Contract for verifying that Phase 1 processed datasets remain unchanged."""

    @staticmethod
    def verify_immutability(
        baseline_checksums: Dict[str, str],
        processed_dir: Path,
    ) -> ImmutabilityVerificationResult:
        import hashlib

        result = ImmutabilityVerificationResult()
        result.datasets_checked = len(baseline_checksums)

        for fname, baseline_hash in baseline_checksums.items():
            fpath = processed_dir / fname
            if not fpath.exists():
                result.datasets_changed.append(f"{fname} (missing)")
                continue
            with open(fpath, "rb") as fh:
                current_hash = hashlib.sha256(fh.read()).hexdigest()
            result.checksum_comparison[fname] = {
                "baseline": baseline_hash,
                "current": current_hash,
                "match": baseline_hash == current_hash,
            }
            if baseline_hash == current_hash:
                result.datasets_unchanged += 1
            else:
                result.datasets_changed.append(fname)

        result.verified = len(result.datasets_changed) == 0
        return result
