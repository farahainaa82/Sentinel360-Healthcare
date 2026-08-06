"""Scenario configuration loader.

Reads all authoritative configuration files for Phase 2C-2C scenario modelling.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import pandas as pd


def read_csv(path: str, **kwargs) -> pd.DataFrame:
    """Read CSV with safe defaults."""
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path, keep_default_na=False, na_values=[""], **kwargs)


class ScenarioConfigLoader:
    """Loads and caches all scenario configuration files."""

    def __init__(self, base_dir: str = "."):
        self.base_dir = base_dir
        self.config_dir = os.path.join(base_dir, "config")
        self.data_dir = os.path.join(base_dir, "data")
        self.output_dir = os.path.join(base_dir, "outputs")

    def load_catalogue(self) -> pd.DataFrame:
        path = os.path.join(self.config_dir, "scenario_catalogue.csv")
        return read_csv(path)

    def load_assumption_definition(self) -> pd.DataFrame:
        path = os.path.join(self.config_dir, "scenario_assumption_definition.csv")
        return read_csv(path)

    def load_assumption_range_config(self) -> pd.DataFrame:
        path = os.path.join(self.config_dir, "scenario_assumption_range_config.csv")
        return read_csv(path)

    def load_comparator_config(self) -> pd.DataFrame:
        path = os.path.join(self.config_dir, "scenario_comparator_config.csv")
        return read_csv(path)

    def load_confidence_rule_config(self) -> pd.DataFrame:
        path = os.path.join(self.config_dir, "scenario_confidence_rule_config.csv")
        return read_csv(path)

    def load_governance_rule_config(self) -> pd.DataFrame:
        path = os.path.join(self.config_dir, "scenario_governance_rule_config.csv")
        return read_csv(path)

    def load_assumption_config(self) -> pd.DataFrame:
        path = os.path.join(self.config_dir, "scenario_assumption_config.csv")
        return read_csv(path)

    def load_package_scenario_mapping(self) -> pd.DataFrame:
        path = os.path.join(self.output_dir, "scenario_modelling", "step_2c2b_package_scenario_mapping.csv")
        return read_csv(path)

    def load_baseline_requirement_register(self) -> pd.DataFrame:
        path = os.path.join(self.output_dir, "scenario_modelling", "step_2c2b_scenario_baseline_requirement_register.csv")
        return read_csv(path)

    def load_assumption_gap_register(self) -> pd.DataFrame:
        path = os.path.join(self.output_dir, "scenario_modelling", "step_2c2b_assumption_gap_register.csv")
        return read_csv(path)

    def load_episode_register(self) -> pd.DataFrame:
        path = os.path.join(self.data_dir, "scenario_inputs", "step_2c1c_corrected_episode_register.csv")
        return read_csv(path)

    def load_episode_approval_package_register(self) -> pd.DataFrame:
        path = os.path.join(self.data_dir, "scenario_inputs", "step_2c1d_episode_approval_package_register.csv")
        return read_csv(path)

    def load_recommendation_linkage_register(self) -> pd.DataFrame:
        path = os.path.join(self.data_dir, "scenario_inputs", "step_2c1d_recommendation_approval_linkage_register.csv")
        return read_csv(path)

    def load_validated_recommendation_register(self) -> pd.DataFrame:
        path = os.path.join(self.data_dir, "scenario_inputs", "step_2c1c_validated_recommendation_register.csv")
        return read_csv(path)

    def load_workforce_kpi_daily(self) -> pd.DataFrame:
        path = os.path.join(self.data_dir, "analytical", "analytical_workforce_kpi_daily.csv")
        return read_csv(path)

    def load_patient_flow_kpi_daily(self) -> pd.DataFrame:
        path = os.path.join(self.data_dir, "analytical", "analytical_patient_flow_kpi_daily.csv")
        return read_csv(path)

    def load_six_kpi_daily(self) -> pd.DataFrame:
        path = os.path.join(self.data_dir, "analytical", "analytical_six_kpi_daily.csv")
        return read_csv(path)

    def get_all_configs(self) -> Dict[str, pd.DataFrame]:
        return {
            "catalogue": self.load_catalogue(),
            "assumption_definition": self.load_assumption_definition(),
            "assumption_range_config": self.load_assumption_range_config(),
            "comparator_config": self.load_comparator_config(),
            "confidence_rule_config": self.load_confidence_rule_config(),
            "governance_rule_config": self.load_governance_rule_config(),
            "assumption_config": self.load_assumption_config(),
            "package_scenario_mapping": self.load_package_scenario_mapping(),
            "baseline_requirement_register": self.load_baseline_requirement_register(),
            "assumption_gap_register": self.load_assumption_gap_register(),
            "episode_register": self.load_episode_register(),
            "episode_approval_package": self.load_episode_approval_package_register(),
            "recommendation_linkage": self.load_recommendation_linkage_register(),
            "validated_recommendation": self.load_validated_recommendation_register(),
            "workforce_kpi_daily": self.load_workforce_kpi_daily(),
            "patient_flow_kpi_daily": self.load_patient_flow_kpi_daily(),
            "six_kpi_daily": self.load_six_kpi_daily(),
        }

    def get_comparators_for_template(self, template_id: str) -> List[Dict[str, Any]]:
        """Return active comparator definitions for a template."""
        df = self.load_comparator_config()
        if df.empty:
            return []
        mask = (df["scenario_template_id"] == template_id)
        rows = df[mask].to_dict("records")
        return rows

    def get_assumption_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Return assumption profile by ID from scenario_assumption_profile_config.csv."""
        df = self.load_assumption_profile_config()
        if df.empty:
            return None
        mask = df["profile_id"] == profile_id
        rows = df[mask].to_dict("records")
        if not rows:
            return None
        # Aggregate all assumption_name/assumption_value pairs for this profile
        profile = {}
        for row in rows:
            key = row.get("assumption_name", "")
            val = row.get("assumption_value", "")
            if key:
                try:
                    profile[key] = float(val) if "." in str(val) else int(val)
                except (ValueError, TypeError):
                    profile[key] = val
        return profile if profile else None

    def load_assumption_profile_config(self) -> pd.DataFrame:
        path = os.path.join(self.config_dir, "scenario_assumption_profile_config.csv")
        return read_csv(path)

    def get_assumption_ranges(self, assumption_id: str) -> Optional[Dict[str, Any]]:
        """Return range config for an assumption."""
        df = self.load_assumption_range_config()
        if df.empty:
            return None
        # Match by assumption_name column (not assumption_id)
        mask = df["assumption_name"] == assumption_id
        rows = df[mask].to_dict("records")
        return rows[0] if rows else None

    def get_catalogue_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Return catalogue template by ID."""
        df = self.load_catalogue()
        if df.empty:
            return None
        mask = df["template_id"] == template_id
        rows = df[mask].to_dict("records")
        return rows[0] if rows else None

    def get_governance_rules_for_template(self, template_id: str) -> List[Dict[str, Any]]:
        """Return active governance rules for a template."""
        df = self.load_governance_rule_config()
        if df.empty:
            return []
        return df.to_dict("records")

    def get_confidence_rules(self) -> List[Dict[str, Any]]:
        """Return all active confidence rules."""
        df = self.load_confidence_rule_config()
        if df.empty:
            return []
        return df.to_dict("records")
