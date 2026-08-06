"""
Base engine for Step 2C-2E validation.
Provides shared utilities for loading inputs, applying config rules,
and writing governed outputs with lineage.
"""

import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any


class ValidationEngineBase:
    """Base class for all Step 2C-2E validation engines."""

    def __init__(
        self,
        data_dir: str = None,
        config_dir: str = None,
        output_dir: str = None,
        engine_name: str = "base",
        engine_version: str = "2C-2E-1.0",
    ):
        self.data_dir = data_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "analytical"
        )
        self.config_dir = config_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "config"
        )
        self.output_dir = output_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "outputs", "scenario_modelling", "_temp_2c2e"
        )
        os.makedirs(self.output_dir, exist_ok=True)
        self.engine_name = engine_name
        self.engine_version = engine_version
        self.run_timestamp = datetime.now().isoformat()
        self.lineage_records: List[Dict[str, Any]] = []
        self.evidence_records: List[Dict[str, Any]] = []
        self.governance_records: List[Dict[str, Any]] = []
        self.issue_records: List[Dict[str, Any]] = []

    def load_csv(self, filename: str) -> pd.DataFrame:
        """Load a CSV from the data directory."""
        path = os.path.join(self.data_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Input file not found: {path}")
        return pd.read_csv(path)

    def load_config(self, filename: str) -> pd.DataFrame:
        """Load a configuration CSV from the config directory."""
        path = os.path.join(self.config_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file not found: {path}")
        return pd.read_csv(path)

    def write_output(self, df: pd.DataFrame, filename: str) -> str:
        """Write a DataFrame to the temporary output directory."""
        path = os.path.join(self.output_dir, filename)
        df.to_csv(path, index=False)
        return path

    def add_lineage(
        self,
        source_scenario_run_id: Optional[str],
        source_type: str,
        source_id: str,
        source_file: str,
        link_type: str = "derived",
    ) -> None:
        """Record a lineage entry."""
        self.lineage_records.append({
            "lineage_id": f"LIN-{self.engine_name}-{len(self.lineage_records)+1:06d}",
            "scenario_run_id": source_scenario_run_id,
            "source_type": source_type,
            "source_id": source_id,
            "source_file": source_file,
            "link_type": link_type,
            "recorded_at": self.run_timestamp,
        })

    def add_evidence(
        self,
        source_scenario_run_id: Optional[str],
        evidence_type: str,
        source_type: str,
        source_id: str,
        source_file: str,
        link_type: str = "validation",
        metadata_json: Optional[str] = None,
    ) -> None:
        """Record an evidence entry."""
        self.evidence_records.append({
            "evidence_id": f"EV-{self.engine_name}-{len(self.evidence_records)+1:06d}",
            "scenario_run_id": source_scenario_run_id,
            "evidence_type": evidence_type,
            "source_type": source_type,
            "source_id": source_id,
            "source_file": source_file,
            "link_type": link_type,
            "recorded_at": self.run_timestamp,
            "metadata_json": metadata_json or "{}",
        })

    def add_governance(
        self,
        source_scenario_run_id: Optional[str],
        rule_id: str,
        rule_name: str,
        rule_applied: bool,
        rule_outcome: str,
        message: str,
    ) -> None:
        """Record a governance entry."""
        self.governance_records.append({
            "governance_id": f"GOV-{self.engine_name}-{len(self.governance_records)+1:06d}",
            "scenario_run_id": source_scenario_run_id,
            "rule_id": rule_id,
            "rule_name": rule_name,
            "rule_applied": rule_applied,
            "rule_outcome": rule_outcome,
            "message": message,
            "applied_at": self.run_timestamp,
        })

    def add_issue(
        self,
        source_scenario_run_id: Optional[str],
        approval_package_id: Optional[str],
        issue_type: str,
        issue_severity: str,
        issue_description: str,
        recommended_action: str,
    ) -> None:
        """Record an issue entry."""
        self.issue_records.append({
            "issue_id": f"ISS-{self.engine_name}-{len(self.issue_records)+1:06d}",
            "scenario_run_id": source_scenario_run_id,
            "approval_package_id": approval_package_id,
            "issue_type": issue_type,
            "issue_severity": issue_severity,
            "issue_description": issue_description,
            "recommended_action": recommended_action,
            "recorded_at": self.run_timestamp,
        })

    def get_lineage_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.lineage_records)

    def get_evidence_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.evidence_records)

    def get_governance_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.governance_records)

    def get_issues_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.issue_records)

    def safe_merge(
        self,
        left: pd.DataFrame,
        right: pd.DataFrame,
        on: List[str],
        how: str = "left",
        suffixes: tuple = ("_x", "_y"),
    ) -> pd.DataFrame:
        """Governed merge that validates join keys exist and warns on cardinality."""
        for key in on:
            if key not in left.columns:
                raise KeyError(f"Left DataFrame missing join key: {key}")
            if key not in right.columns:
                raise KeyError(f"Right DataFrame missing join key: {key}")
        merged = left.merge(right, on=on, how=how, suffixes=suffixes)
        # Detect potential Cartesian product
        if len(merged) > max(len(left), len(right)) * 10:
            self.issue_records.append({
                "issue_id": f"ISS-{self.engine_name}-CARTESIAN-{len(self.issue_records)+1:06d}",
                "scenario_run_id": None,
                "approval_package_id": None,
                "issue_type": "Cartesian Risk",
                "issue_severity": "Warning",
                "issue_description": f"Merge on {on} produced {len(merged)} rows from {len(left)} x {len(right)}",
                "recommended_action": "Review join keys for duplicates",
                "recorded_at": self.run_timestamp,
            })
        return merged
