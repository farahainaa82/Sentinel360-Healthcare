"""
Sentinel360 Healthcare
Demo Decision Confidence Lookup

This module performs a read-only lookup against
config/decision_confidence_demo_config.csv.

The confidence mapping is indicative demo governance only.
It is not a statistical confidence model, forecast probability,
or confidence interval.

Lookup keys: forecast_year + forecast_month + kpi_id (active_flag = TRUE).

This helper contains no business logic. It does not infer confidence
from KPI values, forecast outputs, or any other analytical signal.
If no active mapping is configured for the requested context,
the helper returns a structured unavailable result.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd


# ---------------------------------------------------------------------------
# 1. Path resolution
# ---------------------------------------------------------------------------

DEFAULT_BASE_DIR = Path(__file__).parent.parent
DEFAULT_CONFIG_RELATIVE_PATH = Path("config") / "decision_confidence_demo_config.csv"

REQUIRED_COLUMNS = (
    "forecast_year",
    "forecast_month",
    "kpi_id",
    "confidence_level",
    "decision_posture",
    "decision_implication",
    "evidence_action",
    "source_type",
    "active_flag",
)


# ---------------------------------------------------------------------------
# 2. Result data model
# ---------------------------------------------------------------------------

@dataclass
class DecisionConfidenceResult:
    """Structured result of a demo decision confidence lookup."""

    forecast_year: Optional[int]
    forecast_month: Optional[int]
    kpi_id: Optional[str]
    confidence_level: Optional[str]
    decision_posture: Optional[str]
    decision_implication: Optional[str]
    evidence_action: Optional[str]
    source_type: Optional[str]
    status: str
    message: Optional[str] = None


# ---------------------------------------------------------------------------
# 3. Status constants
# ---------------------------------------------------------------------------

STATUS_OK = "OK"
STATUS_NOT_CONFIGURED = "NOT_CONFIGURED"
STATUS_DUPLICATE_CONFIG = "DUPLICATE_CONFIG"
STATUS_INVALID_INPUT = "INVALID_INPUT"
STATUS_CONFIG_NOT_FOUND = "CONFIG_NOT_FOUND"
STATUS_CONFIG_ERROR = "CONFIG_ERROR"


# ---------------------------------------------------------------------------
# 4. Lookup class
# ---------------------------------------------------------------------------

class DecisionConfidenceDemoLookup:
    """Read-only lookup for demo decision confidence mappings.

    The class performs a pure lookup against the governed demo config
    file. It does not compute, infer, or default confidence values.
    """

    def __init__(
        self,
        base_dir: Optional[Path] = None,
        config_path: Optional[Path] = None,
    ) -> None:
        if config_path is not None:
            self._config_path = Path(config_path)
            return
        base = Path(base_dir) if base_dir is not None else DEFAULT_BASE_DIR
        self._config_path = base / DEFAULT_CONFIG_RELATIVE_PATH

    # ---- Public API -----------------------------------------------------

    def get(
        self,
        forecast_year,
        forecast_month,
        kpi_id,
    ) -> DecisionConfidenceResult:
        """Return the active demo confidence row for the given context.

        Parameters
        ----------
        forecast_year : int | str | None
            Selected forecast year (e.g. 2025).
        forecast_month : int | str | None
            Selected forecast month (1-12).
        kpi_id : str | None
            Selected KPI identifier (e.g. "kpi_001").

        Returns
        -------
        DecisionConfidenceResult
            Structured result. ``status`` is one of:
            OK, NOT_CONFIGURED, DUPLICATE_CONFIG,
            INVALID_INPUT, CONFIG_NOT_FOUND, CONFIG_ERROR.
        """
        # 1. Input validation (context fields left as None on invalid input)
        year, year_ok = self._coerce_year(forecast_year)
        month, month_ok = self._coerce_month(forecast_month)
        kpi_norm = self._normalize_kpi_id(kpi_id)

        if not (year_ok and month_ok and kpi_norm):
            return DecisionConfidenceResult(
                forecast_year=year if year_ok else None,
                forecast_month=month if month_ok else None,
                kpi_id=kpi_norm if kpi_norm else None,
                confidence_level=None,
                decision_posture=None,
                decision_implication=None,
                evidence_action=None,
                source_type=None,
                status=STATUS_INVALID_INPUT,
                message=(
                    "Invalid lookup inputs. Provide an integer year, a month "
                    "between 1 and 12, and a non-empty KPI ID."
                ),
            )

        # 2. Load config
        df, load_status = self._load_dataframe()
        if load_status is not None:
            return DecisionConfidenceResult(
                forecast_year=year,
                forecast_month=month,
                kpi_id=kpi_norm,
                confidence_level=None,
                decision_posture=None,
                decision_implication=None,
                evidence_action=None,
                source_type=None,
                status=load_status,
                message=self._status_message(load_status),
            )

        # 3. Filter active rows for the requested key
        try:
            active_mask = (
                df["active_flag"].astype(str).str.strip().str.upper() == "TRUE"
            )
            year_series = pd.to_numeric(df["forecast_year"], errors="coerce")
            month_series = pd.to_numeric(df["forecast_month"], errors="coerce")
            kpi_series = df["kpi_id"].astype(str).str.strip()

            matches = df[
                active_mask
                & (year_series == year)
                & (month_series == month)
                & (kpi_series == kpi_norm)
            ]
        except Exception as exc:  # pragma: no cover - defensive
            return DecisionConfidenceResult(
                forecast_year=year,
                forecast_month=month,
                kpi_id=kpi_norm,
                confidence_level=None,
                decision_posture=None,
                decision_implication=None,
                evidence_action=None,
                source_type=None,
                status=STATUS_CONFIG_ERROR,
                message=f"Unable to evaluate demo confidence lookup: {exc}",
            )

        if len(matches) == 0:
            return DecisionConfidenceResult(
                forecast_year=year,
                forecast_month=month,
                kpi_id=kpi_norm,
                confidence_level=None,
                decision_posture=None,
                decision_implication=None,
                evidence_action=None,
                source_type=None,
                status=STATUS_NOT_CONFIGURED,
                message=(
                    "No demo decision-confidence mapping is configured for the "
                    "selected context."
                ),
            )

        if len(matches) > 1:
            return DecisionConfidenceResult(
                forecast_year=year,
                forecast_month=month,
                kpi_id=kpi_norm,
                confidence_level=None,
                decision_posture=None,
                decision_implication=None,
                evidence_action=None,
                source_type=None,
                status=STATUS_DUPLICATE_CONFIG,
                message=(
                    f"Multiple active demo decision-confidence mappings exist "
                    f"for the selected context ({len(matches)} rows)."
                ),
            )

        # 4. Single active row found
        row = matches.iloc[0]
        return DecisionConfidenceResult(
            forecast_year=year,
            forecast_month=month,
            kpi_id=kpi_norm,
            confidence_level=self._safe_str(row.get("confidence_level")),
            decision_posture=self._safe_str(row.get("decision_posture")),
            decision_implication=self._safe_str(row.get("decision_implication")),
            evidence_action=self._safe_str(row.get("evidence_action")),
            source_type=self._safe_str(row.get("source_type")),
            status=STATUS_OK,
            message=None,
        )

    @property
    def config_path(self) -> Path:
        """Return the resolved config file path used by this lookup."""
        return self._config_path

    # ---- Internals ------------------------------------------------------

    def _load_dataframe(self) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """Load and validate the demo confidence config CSV.

        Returns
        -------
        (df, error_status)
            ``df`` is the loaded DataFrame on success, else None.
            ``error_status`` is one of CONFIG_NOT_FOUND / CONFIG_ERROR
            on failure, else None.
        """
        if not self._config_path.exists():
            return None, STATUS_CONFIG_NOT_FOUND

        try:
            df = pd.read_csv(
                self._config_path,
                dtype=str,
                keep_default_na=False,
                na_values=[""],
            )
        except Exception as exc:
            return None, STATUS_CONFIG_ERROR

        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            return None, STATUS_CONFIG_ERROR

        return df, None

    @staticmethod
    def _coerce_year(value) -> Tuple[Optional[int], bool]:
        if value is None:
            return None, False
        try:
            year = int(str(value).strip())
        except (TypeError, ValueError):
            return None, False
        if year < 1900 or year > 2999:
            return None, False
        return year, True

    @staticmethod
    def _coerce_month(value) -> Tuple[Optional[int], bool]:
        if value is None:
            return None, False
        try:
            month = int(str(value).strip())
        except (TypeError, ValueError):
            return None, False
        if month < 1 or month > 12:
            return None, False
        return month, True

    @staticmethod
    def _normalize_kpi_id(value) -> Optional[str]:
        if value is None:
            return None
        if not isinstance(value, str):
            try:
                value = str(value)
            except Exception:
                return None
        norm = value.strip()
        return norm if norm else None

    @staticmethod
    def _safe_str(value) -> Optional[str]:
        if value is None:
            return None
        try:
            if pd.isna(value):
                return None
        except (TypeError, ValueError):
            pass
        s = str(value).strip()
        return s if s else None

    @staticmethod
    def _status_message(status: str) -> str:
        if status == STATUS_CONFIG_NOT_FOUND:
            return (
                "Demo decision confidence configuration file was not found."
            )
        if status == STATUS_CONFIG_ERROR:
            return (
                "Demo decision confidence configuration file is malformed or "
                "missing required columns."
            )
        return None


# ---------------------------------------------------------------------------
# 5. Module-level convenience
# ---------------------------------------------------------------------------

def get_decision_confidence(
    forecast_year,
    forecast_month,
    kpi_id,
    base_dir: Optional[Path] = None,
) -> DecisionConfidenceResult:
    """Convenience function for a one-shot demo confidence lookup."""
    return DecisionConfidenceDemoLookup(base_dir=base_dir).get(
        forecast_year=forecast_year,
        forecast_month=forecast_month,
        kpi_id=kpi_id,
    )
