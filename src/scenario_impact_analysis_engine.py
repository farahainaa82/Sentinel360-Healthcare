"""Scenario impact analysis engine.

Phase 2C-2D — Primary and supporting KPI impact classification.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


class ScenarioImpactAnalysisEngine:
    """Classifies primary and supporting KPI impacts using configuration-driven bands."""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.impact_bands = self._load_impact_bands()

    def _load_impact_bands(self) -> pd.DataFrame:
        path = os.path.join(self.config_dir, "scenario_impact_band_config.csv")
        if os.path.exists(path):
            return pd.read_csv(path, keep_default_na=False)
        return pd.DataFrame()

    def classify_primary_impact(
        self,
        primary_kpi_id: str,
        percentage_change: float,
        direction_of_change: str,
    ) -> Dict[str, Any]:
        """Classify a primary KPI impact using configured bands."""
        if self.impact_bands.empty:
            return {
                "impact_classification": "Insufficient Evidence",
                "effect_direction": "Unknown",
                "evidence_language": "insufficient evidence for classification",
            }

        # Filter to ALL or specific KPI bands
        bands = self.impact_bands[
            (self.impact_bands["primary_kpi_id"] == "ALL") |
            (self.impact_bands["primary_kpi_id"] == primary_kpi_id)
        ].copy()

        # Convert thresholds to numeric
        bands["lower"] = pd.to_numeric(bands["percentage_change_threshold_lower"], errors="coerce")
        bands["upper"] = pd.to_numeric(bands["percentage_change_threshold_upper"], errors="coerce")

        # Find matching band
        for _, band in bands.iterrows():
            lower = band["lower"]
            upper = band["upper"]
            if pd.notna(lower) and pd.notna(upper):
                if lower <= percentage_change <= upper:
                    return {
                        "impact_classification": band["impact_classification"],
                        "effect_direction": band["effect_direction"],
                        "evidence_language": band["evidence_language"],
                    }

        # Default to insufficient evidence
        return {
            "impact_classification": "Insufficient Evidence",
            "effect_direction": "Unknown",
            "evidence_language": "insufficient evidence for classification",
        }

    def analyse_supporting_kpis(
        self,
        supporting_kpi_status: str,
        affected_supporting_kpis: List[str],
    ) -> Dict[str, Any]:
        """Determine supporting KPI impact status."""
        if not affected_supporting_kpis or affected_supporting_kpis == [""] or affected_supporting_kpis == []:
            return {
                "supporting_kpi_status": "Unavailable",
                "expected_direction_if_any": "Unknown",
                "evidence_basis": "No supporting KPIs identified",
                "uncertainty": "High",
                "monitoring_requirement": "Review supporting KPI coverage",
            }

        unsupported = {"kpi_003", "kpi_005", "kpi_006"}
        has_unsupported = any(k in unsupported for k in affected_supporting_kpis)

        if has_unsupported:
            return {
                "supporting_kpi_status": "Monitoring Only",
                "expected_direction_if_any": "Unknown",
                "evidence_basis": "Unsupported KPIs present; no quantitative modelling",
                "uncertainty": "High",
                "monitoring_requirement": "Validate unsupported KPI data before use",
            }

        if supporting_kpi_status in ("Quantified", "Calculated"):
            return {
                "supporting_kpi_status": "Quantified",
                "expected_direction_if_any": "See individual KPI results",
                "evidence_basis": "Step 2C-2C governed calculation",
                "uncertainty": "Moderate",
                "monitoring_requirement": "Monitor supporting KPI trends",
            }

        return {
            "supporting_kpi_status": "Directional Only",
            "expected_direction_if_any": "Unknown",
            "evidence_basis": "Limited supporting KPI data",
            "uncertainty": "Moderate",
            "monitoring_requirement": "Collect additional supporting KPI data",
        }
