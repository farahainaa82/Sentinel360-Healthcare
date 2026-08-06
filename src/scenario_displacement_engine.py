"""Scenario risk displacement engine.

Phase 2C-2D — Identifies possible risk displacement across KPIs and departments.
"""

from __future__ import annotations

import os
import uuid
from typing import Any, Dict, List, Optional

import pandas as pd


class ScenarioDisplacementEngine:
    """Analyses possible risk displacement for scenario runs."""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.rules = self._load_rules()

    def _load_rules(self) -> pd.DataFrame:
        path = os.path.join(self.config_dir, "scenario_displacement_rule_config.csv")
        if os.path.exists(path):
            return pd.read_csv(path, keep_default_na=False)
        return pd.DataFrame()

    def analyse_displacement(
        self,
        scenario_run: Dict[str, Any],
        baseline: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Analyse displacement for a single scenario run."""
        records = []
        family = scenario_run.get("scenario_family", "")
        comparator_type = scenario_run.get("comparator_type", "Baseline")

        if comparator_type == "Baseline":
            # Baseline comparator has no displacement risk
            records.append(self._create_no_displacement_record(scenario_run))
            return records

        # Parse assumption values
        assumptions = self._parse_assumptions(scenario_run.get("assumption_values_json", "{}"))

        # Apply rules based on family and assumptions
        if family == "Staffing Coverage Adjustment":
            records.extend(self._check_staffing_displacement(scenario_run, baseline, assumptions))
        elif family == "Absenteeism Contingency":
            records.extend(self._check_absenteeism_displacement(scenario_run, baseline, assumptions))
        elif family == "Patient-Flow and Waiting-Time Adjustment":
            records.extend(self._check_flow_displacement(scenario_run, baseline, assumptions))
        elif family == "Combined Workforce and Flow Intervention":
            records.extend(self._check_combined_displacement(scenario_run, baseline, assumptions))

        if not records:
            records.append(self._create_no_displacement_record(scenario_run))

        return records

    def _parse_assumptions(self, json_str: str) -> Dict[str, float]:
        import json
        try:
            return json.loads(json_str) if json_str else {}
        except json.JSONDecodeError:
            return {}

    def _create_no_displacement_record(self, scenario_run: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "displacement_id": f"DISP-{uuid.uuid4().hex[:16].upper()}",
            "scenario_run_id": scenario_run.get("scenario_run_id", ""),
            "approval_package_id": scenario_run.get("approval_package_id", ""),
            "episode_id": scenario_run.get("episode_id", ""),
            "source_kpi_id": scenario_run.get("primary_kpi_id", ""),
            "improved_kpi_id": scenario_run.get("primary_kpi_id", ""),
            "potentially_affected_kpi_id": "",
            "source_department_id": "",
            "potentially_affected_department_id": "",
            "displacement_type": "None",
            "displacement_classification": "No Displacement Identified",
            "evidence_basis": "Baseline comparator or no displacement conditions met",
            "confidence": scenario_run.get("final_scenario_confidence", ""),
            "required_monitoring": "None",
            "management_confirmation_required": False,
        }

    def _check_staffing_displacement(
        self,
        scenario_run: Dict[str, Any],
        baseline: Dict[str, Any],
        assumptions: Dict[str, float],
    ) -> List[Dict[str, Any]]:
        records = []
        additional = assumptions.get("additional_staff_count", 0)
        temp = assumptions.get("temporary_staff_count", 0)
        uncovered_reduction = assumptions.get("uncovered_shift_reduction_pct", 0)

        # Cross-KPI: staffing increase may affect wait times
        if (additional + temp) > 0:
            records.append({
                "displacement_id": f"DISP-{uuid.uuid4().hex[:16].upper()}",
                "scenario_run_id": scenario_run.get("scenario_run_id", ""),
                "approval_package_id": scenario_run.get("approval_package_id", ""),
                "episode_id": scenario_run.get("episode_id", ""),
                "source_kpi_id": scenario_run.get("primary_kpi_id", ""),
                "improved_kpi_id": scenario_run.get("primary_kpi_id", ""),
                "potentially_affected_kpi_id": "kpi_004",
                "source_department_id": "",
                "potentially_affected_department_id": "",
                "displacement_type": "Cross-KPI Displacement",
                "displacement_classification": "Possible Cross-KPI Displacement",
                "evidence_basis": "Staffing increase may reduce patient waiting times indirectly",
                "confidence": scenario_run.get("final_scenario_confidence", ""),
                "required_monitoring": "Monitor patient waiting time trends",
                "management_confirmation_required": False,
            })

        # Within-department: temporary staff without uncovered shift reduction
        if temp > 0 and uncovered_reduction == 0:
            records.append({
                "displacement_id": f"DISP-{uuid.uuid4().hex[:16].upper()}",
                "scenario_run_id": scenario_run.get("scenario_run_id", ""),
                "approval_package_id": scenario_run.get("approval_package_id", ""),
                "episode_id": scenario_run.get("episode_id", ""),
                "source_kpi_id": scenario_run.get("primary_kpi_id", ""),
                "improved_kpi_id": scenario_run.get("primary_kpi_id", ""),
                "potentially_affected_kpi_id": scenario_run.get("primary_kpi_id", ""),
                "source_department_id": "",
                "potentially_affected_department_id": "",
                "displacement_type": "Within-Department Displacement",
                "displacement_classification": "Possible Within-Department Displacement",
                "evidence_basis": "Temporary staff added but uncovered shift reduction is zero",
                "confidence": scenario_run.get("final_scenario_confidence", ""),
                "required_monitoring": "Monitor shift coverage and temporary staff effectiveness",
                "management_confirmation_required": False,
            })

        return records

    def _check_absenteeism_displacement(
        self,
        scenario_run: Dict[str, Any],
        baseline: Dict[str, Any],
        assumptions: Dict[str, float],
    ) -> List[Dict[str, Any]]:
        records = []
        reduction = assumptions.get("assumed_absenteeism_reduction_pct", 0)
        replacement = assumptions.get("replacement_coverage_pct", 0)

        # Cross-department: absenteeism reduction may pressure staffing elsewhere
        if reduction > 15:
            records.append({
                "displacement_id": f"DISP-{uuid.uuid4().hex[:16].upper()}",
                "scenario_run_id": scenario_run.get("scenario_run_id", ""),
                "approval_package_id": scenario_run.get("approval_package_id", ""),
                "episode_id": scenario_run.get("episode_id", ""),
                "source_kpi_id": scenario_run.get("primary_kpi_id", ""),
                "improved_kpi_id": scenario_run.get("primary_kpi_id", ""),
                "potentially_affected_kpi_id": "kpi_001",
                "source_department_id": "",
                "potentially_affected_department_id": "",
                "displacement_type": "Cross-Department Displacement",
                "displacement_classification": "Possible Cross-Department Displacement",
                "evidence_basis": "High absenteeism reduction may create staffing pressure in other departments",
                "confidence": scenario_run.get("final_scenario_confidence", ""),
                "required_monitoring": "Monitor staffing coverage across departments",
                "management_confirmation_required": False,
            })

        # Within-department: low replacement coverage with high reduction
        if replacement < 50 and reduction > 10:
            records.append({
                "displacement_id": f"DISP-{uuid.uuid4().hex[:16].upper()}",
                "scenario_run_id": scenario_run.get("scenario_run_id", ""),
                "approval_package_id": scenario_run.get("approval_package_id", ""),
                "episode_id": scenario_run.get("episode_id", ""),
                "source_kpi_id": scenario_run.get("primary_kpi_id", ""),
                "improved_kpi_id": scenario_run.get("primary_kpi_id", ""),
                "potentially_affected_kpi_id": scenario_run.get("primary_kpi_id", ""),
                "source_department_id": "",
                "potentially_affected_department_id": "",
                "displacement_type": "Within-Department Displacement",
                "displacement_classification": "Possible Within-Department Displacement",
                "evidence_basis": "Replacement coverage is low despite high absenteeism reduction target",
                "confidence": scenario_run.get("final_scenario_confidence", ""),
                "required_monitoring": "Monitor actual replacement coverage and workload distribution",
                "management_confirmation_required": True,
            })

        return records

    def _check_flow_displacement(
        self,
        scenario_run: Dict[str, Any],
        baseline: Dict[str, Any],
        assumptions: Dict[str, float],
    ) -> List[Dict[str, Any]]:
        records = []
        arrival_change = assumptions.get("arrival_change_pct", 0)
        capacity_change = assumptions.get("service_capacity_change_pct", 0)

        # Cross-department: arrival increase may pressure staffing
        if arrival_change > 10:
            records.append({
                "displacement_id": f"DISP-{uuid.uuid4().hex[:16].upper()}",
                "scenario_run_id": scenario_run.get("scenario_run_id", ""),
                "approval_package_id": scenario_run.get("approval_package_id", ""),
                "episode_id": scenario_run.get("episode_id", ""),
                "source_kpi_id": scenario_run.get("primary_kpi_id", ""),
                "improved_kpi_id": scenario_run.get("primary_kpi_id", ""),
                "potentially_affected_kpi_id": "kpi_001",
                "source_department_id": "",
                "potentially_affected_department_id": "",
                "displacement_type": "Cross-Department Displacement",
                "displacement_classification": "Possible Cross-Department Displacement",
                "evidence_basis": "Increased patient arrivals may create staffing pressure",
                "confidence": scenario_run.get("final_scenario_confidence", ""),
                "required_monitoring": "Monitor staffing levels relative to arrival volumes",
                "management_confirmation_required": False,
            })

        return records

    def _check_combined_displacement(
        self,
        scenario_run: Dict[str, Any],
        baseline: Dict[str, Any],
        assumptions: Dict[str, float],
    ) -> List[Dict[str, Any]]:
        records = []
        interaction = assumptions.get("interaction_adjustment_factor", 1.0)

        if interaction != 1.0:
            records.append({
                "displacement_id": f"DISP-{uuid.uuid4().hex[:16].upper()}",
                "scenario_run_id": scenario_run.get("scenario_run_id", ""),
                "approval_package_id": scenario_run.get("approval_package_id", ""),
                "episode_id": scenario_run.get("episode_id", ""),
                "source_kpi_id": scenario_run.get("primary_kpi_id", ""),
                "improved_kpi_id": scenario_run.get("primary_kpi_id", ""),
                "potentially_affected_kpi_id": "",
                "source_department_id": "",
                "potentially_affected_department_id": "",
                "displacement_type": "Cross-KPI Displacement",
                "displacement_classification": "Possible Cross-KPI Displacement",
                "evidence_basis": "Combined scenario interaction factor indicates possible cross-effect displacement",
                "confidence": scenario_run.get("final_scenario_confidence", ""),
                "required_monitoring": "Monitor all primary and supporting KPIs in combined intervention",
                "management_confirmation_required": True,
            })

        return records
