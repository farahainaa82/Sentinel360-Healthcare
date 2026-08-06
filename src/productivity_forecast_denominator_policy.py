"""
Sentinel360 Healthcare — Productivity Forecast Denominator Policy

Governed helper for estimating forecast required staff-hours using only
observed actual data. No forecast-generated denominators are invented.

Reads the governed policy from config/productivity_forecast_assumption_config.csv
and applies it to analytical_six_kpi_daily.csv.

Step: Governance configuration for Phase 3B productivity estimation.
"""

from __future__ import annotations

import os
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


# ---------------------------------------------------------------------------
# 1. Config path resolution (mirrors ScenarioConfigLoader pattern)
# ---------------------------------------------------------------------------

DEFAULT_BASE_DIR = Path(__file__).parent.parent


def _read_csv(path: Path) -> pd.DataFrame:
    """Read CSV with safe defaults; return empty DataFrame if missing."""
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, keep_default_na=False, na_values=[""])


# ---------------------------------------------------------------------------
# 2. Policy data model
# ---------------------------------------------------------------------------

@dataclass
class ForecastDenominatorPolicy:
    """Typed representation of a productivity forecast denominator policy."""

    policy_id: str
    policy_name: str
    metric_scope: str
    method: str
    lookback_months: int
    aggregation_method: str
    forecast_horizon_usage: str
    minimum_complete_months_required: int
    fallback_behavior: str
    source_dataset: str
    source_field: str
    kpi_id: str
    unit: str
    configuration_version: str
    effective_start_date: str
    effective_end_date: str
    approval_status: str
    validation_status: str
    created_datetime: str
    updated_datetime: str
    governance_note: str


# ---------------------------------------------------------------------------
# 3. Policy loader
# ---------------------------------------------------------------------------

class PolicyConfigLoader:
    """Loads and validates productivity forecast assumption config."""

    _VALID_AGGREGATION_METHODS = {"ARITHMETIC_MEAN", "MEDIAN", "WEIGHTED_MEAN"}
    _VALID_FALLBACK_BEHAVIORS = {"NOT_AVAILABLE", "ZERO", "LAST_KNOWN"}

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or DEFAULT_BASE_DIR
        self.config_dir = self.base_dir / "config"
        self._policy: Optional[ForecastDenominatorPolicy] = None

    def _config_path(self) -> Path:
        return self.config_dir / "productivity_forecast_assumption_config.csv"

    def load(self, *, force_reload: bool = False) -> ForecastDenominatorPolicy:
        """Load the single governed policy row from config."""
        if self._policy is not None and not force_reload:
            return self._policy

        df = _read_csv(self._config_path())
        if df.empty:
            raise FileNotFoundError(
                f"Productivity forecast assumption config not found: {self._config_path()}"
            )

        row = df.iloc[0].to_dict()
        policy = ForecastDenominatorPolicy(
            policy_id=str(row["policy_id"]),
            policy_name=str(row["policy_name"]),
            metric_scope=str(row["metric_scope"]),
            method=str(row["method"]),
            lookback_months=int(row["lookback_months"]),
            aggregation_method=str(row["aggregation_method"]).upper(),
            forecast_horizon_usage=str(row["forecast_horizon_usage"]),
            minimum_complete_months_required=int(row["minimum_complete_months_required"]),
            fallback_behavior=str(row["fallback_behavior"]).upper(),
            source_dataset=str(row["source_dataset"]),
            source_field=str(row["source_field"]),
            kpi_id=str(row["kpi_id"]),
            unit=str(row["unit"]),
            configuration_version=str(row.get("configuration_version", "")),
            effective_start_date=str(row.get("effective_start_date", "")),
            effective_end_date=str(row.get("effective_end_date", "")),
            approval_status=str(row.get("approval_status", "")),
            validation_status=str(row.get("validation_status", "")),
            created_datetime=str(row.get("created_datetime", "")),
            updated_datetime=str(row.get("updated_datetime", "")),
            governance_note=str(row.get("governance_note", "")),
        )
        self._validate(policy)
        self._policy = policy
        return policy

    def _validate(self, policy: ForecastDenominatorPolicy) -> None:
        """Validate policy fields against supported values."""
        if policy.lookback_months < 1:
            raise ValueError(
                f"lookback_months must be >= 1, got {policy.lookback_months}"
            )
        if policy.aggregation_method not in self._VALID_AGGREGATION_METHODS:
            raise ValueError(
                f"aggregation_method '{policy.aggregation_method}' not supported. "
                f"Expected one of: {self._VALID_AGGREGATION_METHODS}"
            )
        if policy.fallback_behavior not in self._VALID_FALLBACK_BEHAVIORS:
            raise ValueError(
                f"fallback_behavior '{policy.fallback_behavior}' not recognised. "
                f"Expected one of: {self._VALID_FALLBACK_BEHAVIORS}"
            )
        if policy.minimum_complete_months_required < 1:
            raise ValueError(
                f"minimum_complete_months_required must be >= 1, got "
                f"{policy.minimum_complete_months_required}"
            )
        if policy.kpi_id != "kpi_001":
            raise ValueError(
                f"Policy currently supports only kpi_001, got {policy.kpi_id}"
            )
        if policy.source_field != "denominator_value":
            raise ValueError(
                f"Policy currently supports only source_field='denominator_value', "
                f"got '{policy.source_field}'"
            )


# ---------------------------------------------------------------------------
# 4. Denominator calculator (pure; no UI)
# ---------------------------------------------------------------------------

@dataclass
class DenominatorResult:
    """Result of a forecast denominator calculation."""

    hospital_id: str
    department_id: str
    target_year: int
    kpi_id: str
    value: Optional[float]
    unit: str
    months_used: List[int] = field(default_factory=list)
    months_available: List[int] = field(default_factory=list)
    status: str = ""  # "OK", "NOT_AVAILABLE", "INSUFFICIENT_MONTHS"
    message: str = ""


class ForecastDenominatorCalculator:
    """Calculates forecast required staff-hours using the governed policy."""

    def __init__(
        self,
        policy: Optional[ForecastDenominatorPolicy] = None,
        base_dir: Optional[Path] = None,
    ):
        self.base_dir = base_dir or DEFAULT_BASE_DIR
        self.data_dir = self.base_dir / "data" / "analytical"
        self._policy = policy

    def _load_policy(self) -> ForecastDenominatorPolicy:
        if self._policy is not None:
            return self._policy
        self._policy = PolicyConfigLoader(base_dir=self.base_dir).load()
        return self._policy

    def _read_source(self, policy: ForecastDenominatorPolicy) -> pd.DataFrame:
        """Read the governed source dataset."""
        dataset_name = Path(policy.source_dataset).name
        path = self.data_dir / dataset_name
        if not path.exists():
            raise FileNotFoundError(f"Source dataset not found: {path}")
        return _read_csv(path)

    def calculate(
        self,
        hospital_id: str,
        department_id: str,
        target_year: int,
    ) -> DenominatorResult:
        """
        Compute the forecast required staff-hours denominator.

        Returns the arithmetic mean of the latest `lookback_months` complete
        actual months, derived dynamically from available actual data.
        """
        policy = self._load_policy()
        df = self._read_source(policy)

        # Filter to hospital / department / year / kpi
        df["reporting_year"] = pd.to_numeric(df["reporting_year"], errors="coerce")
        df["reporting_month"] = pd.to_numeric(df["reporting_month"], errors="coerce")
        df = df[
            (df["hospital_id"] == hospital_id)
            & (df["department_id"] == department_id)
            & (df["reporting_year"] == target_year)
            & (df["kpi_id"] == policy.kpi_id)
        ].copy()

        if df.empty:
            return DenominatorResult(
                hospital_id=hospital_id,
                department_id=department_id,
                target_year=target_year,
                kpi_id=policy.kpi_id,
                value=None,
                unit=policy.unit,
                status="NOT_AVAILABLE",
                message="No actual data found for the specified scope.",
            )

        # Aggregate denominator by month (sum of daily values)
        df[policy.source_field] = pd.to_numeric(
            df[policy.source_field], errors="coerce"
        )
        monthly = (
            df.groupby("reporting_month")[policy.source_field]
            .sum()
            .dropna()
            .reset_index()
        )
        monthly = monthly.sort_values("reporting_month", ascending=False)
        available_months = monthly["reporting_month"].astype(int).tolist()

        if len(available_months) < policy.minimum_complete_months_required:
            return DenominatorResult(
                hospital_id=hospital_id,
                department_id=department_id,
                target_year=target_year,
                kpi_id=policy.kpi_id,
                value=None,
                unit=policy.unit,
                months_available=available_months,
                status="INSUFFICIENT_MONTHS",
                message=(
                    f"Only {len(available_months)} complete month(s) available; "
                    f"minimum required is {policy.minimum_complete_months_required}."
                ),
            )

        # Select latest N months (dynamically derived — no hardcoded month numbers)
        selected_months = available_months[: policy.lookback_months]
        selected_values = monthly[
            monthly["reporting_month"].isin(selected_months)
        ][policy.source_field].tolist()

        if policy.aggregation_method == "ARITHMETIC_MEAN":
            aggregated = statistics.mean(selected_values)
        elif policy.aggregation_method == "MEDIAN":
            aggregated = statistics.median(selected_values)
        elif policy.aggregation_method == "WEIGHTED_MEAN":
            # Not currently used; equal weights as default
            aggregated = statistics.mean(selected_values)
        else:
            raise ValueError(
                f"Unsupported aggregation_method: {policy.aggregation_method}"
            )

        return DenominatorResult(
            hospital_id=hospital_id,
            department_id=department_id,
            target_year=target_year,
            kpi_id=policy.kpi_id,
            value=round(aggregated, 2),
            unit=policy.unit,
            months_used=sorted(selected_months),
            months_available=sorted(available_months),
            status="OK",
            message="Derived from latest complete actual months.",
        )

    def calculate_all_departments(
        self,
        hospital_id: str,
        target_year: int,
        excluded_departments: Optional[List[str]] = None,
    ) -> Dict[str, DenominatorResult]:
        """Calculate denominator for all departments found in actual data."""
        policy = self._load_policy()
        df = self._read_source(policy)
        df = df[
            (df["hospital_id"] == hospital_id)
            & (df["reporting_year"] == target_year)
            & (df["kpi_id"] == policy.kpi_id)
        ]
        excluded = set(excluded_departments or [])
        depts = sorted(
            {d for d in df["department_id"].dropna().unique() if d not in excluded}
        )
        return {
            dept: self.calculate(hospital_id, dept, target_year) for dept in depts
        }
