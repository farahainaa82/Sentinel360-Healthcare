"""Scenario modelling execution runner.

Phase 2C-2C — Baseline and Intervention Calculation Engine orchestrator.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.scenario_config_loader import ScenarioConfigLoader
from src.scenario_baseline_engine import ScenarioBaselineEngine
from src.scenario_governance_validator import ScenarioGovernanceValidator
from src.scenario_confidence_engine import ScenarioConfidenceEngine
from src.scenario_evidence_engine import ScenarioEvidenceEngine
from src.staffing_scenario_engine import StaffingScenarioEngine
from src.absenteeism_scenario_engine import AbsenteeismScenarioEngine
from src.patient_flow_scenario_engine import PatientFlowScenarioEngine
from src.combined_scenario_engine import CombinedScenarioEngine
from src.scenario_models import (
    AssumptionValidation,
    BaselineStatus,
    ComparatorType,
    DirectionOfChange,
    EvidenceRecord,
    parse_comparator_type,
    GovernanceRecord,
    IssueRecord,
    ScenarioBaseline,
    ScenarioConfidence,
    ScenarioExecutionStatus,
    ScenarioResult,
)


LOCK_FILE = "outputs/scenario_modelling/.engine_lock"


def _acquire_lock() -> bool:
    """Try to acquire a single-instance execution lock."""
    try:
        os.makedirs(os.path.dirname(LOCK_FILE), exist_ok=True)
        # Use O_EXCL to atomically create the lock file
        fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "w") as f:
            f.write(f"pid={os.getpid()}\nstarted={datetime.now(timezone.utc).isoformat()}\n")
        return True
    except FileExistsError:
        return False


def _release_lock():
    """Release the execution lock."""
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except OSError:
        pass


def _log_progress(step: int, total: int, label: str, start_ts: float):
    elapsed = time.perf_counter() - start_ts
    print(f"[{step}/{total}] {label}... elapsed={elapsed:.2f}s")


def _log_complete(step: int, total: int, label: str, rows: int, size_bytes: int, start_ts: float):
    elapsed = time.perf_counter() - start_ts
    print(f"[{step}/{total}] Complete — {label}: rows={rows}, size={size_bytes}B, elapsed={elapsed:.2f}s")


class ScenarioModellingEngineRunner:
    """Orchestrates the entire scenario modelling pipeline."""

    SUPPORTED_QUANTITATIVE_FAMILIES = {
        "Staffing Coverage Adjustment",
        "Absenteeism Contingency",
        "Patient-Flow and Waiting-Time Adjustment",
        "Combined Workforce and Flow Intervention",
    }
    UNSUPPORTED_KPIS = {"kpi_003", "kpi_005", "kpi_006"}
    MONITORING_ONLY_FAMILIES = {
        "Monitoring Only",
        "Validation Required",
    }

    def __init__(self, base_dir: str = "."):
        self.base_dir = base_dir
        self.loader = ScenarioConfigLoader(base_dir)
        self.baseline_engine = ScenarioBaselineEngine(self.loader)
        self.validator = ScenarioGovernanceValidator(self.loader)
        self.confidence_engine = ScenarioConfidenceEngine(self.loader)
        self.evidence_engine = ScenarioEvidenceEngine(self.loader)
        self.staffing_engine = StaffingScenarioEngine(self.validator)
        self.absenteeism_engine = AbsenteeismScenarioEngine(self.validator)
        self.flow_engine = PatientFlowScenarioEngine(self.validator)
        self.combined_engine = CombinedScenarioEngine(self.validator, self.staffing_engine, self.flow_engine)

        self.baselines: List[ScenarioBaseline] = []
        self.results: List[ScenarioResult] = []
        self.evidence_records: List[EvidenceRecord] = []
        self.governance_records: List[GovernanceRecord] = []
        self.issue_records: List[IssueRecord] = []
        self.validation_records: List[AssumptionValidation] = []

        self.run_timestamp = datetime.now(timezone.utc).isoformat()
        self.engine_version = "2C-2C-1.0"
        self.timing: Dict[str, float] = {}

    def run(self) -> Dict[str, Any]:
        """Execute the full scenario modelling pipeline."""
        if not _acquire_lock():
            print("ERROR: Another engine instance is already running. Lock file exists:", LOCK_FILE)
            return {"status": "blocked", "reason": "Another engine instance is already running."}

        try:
            return self._run_locked()
        finally:
            _release_lock()

    def _run_locked(self) -> Dict[str, Any]:
        t0 = time.perf_counter()
        print("Phase 2C-2C: Baseline and Intervention Calculation Engine")
        print("=" * 60)

        t_load = time.perf_counter()
        configs = self.loader.get_all_configs()
        mapping_df = configs["package_scenario_mapping"]
        episode_df = configs["episode_register"]
        catalogue_df = configs["catalogue"]
        comparator_df = configs["comparator_config"]
        approval_df = configs["episode_approval_package"]
        linkage_df = configs["recommendation_linkage"]
        recommendation_df = configs["validated_recommendation"]
        self.timing["input_loading"] = time.perf_counter() - t_load

        print(f"Loaded {len(mapping_df)} package-scenario mappings")
        print(f"Loaded {len(episode_df)} episodes")
        print(f"Loaded {len(catalogue_df)} scenario templates")
        print(f"Loaded {len(comparator_df)} comparators")
        print(f"  [timing] input_loading={self.timing['input_loading']:.2f}s")

        t_bl = time.perf_counter()
        print("\nBuilding baselines...")
        self.baselines = self.baseline_engine.build_all_baselines_for_all_mappings(mapping_df, episode_df)
        self.timing["baseline_construction"] = time.perf_counter() - t_bl
        print(f"Built {len(self.baselines)} baselines")
        print(f"  [timing] baseline_construction={self.timing['baseline_construction']:.2f}s")

        t_sc = time.perf_counter()
        print("\nRunning scenario calculations...")
        self._run_all_scenarios(mapping_df, episode_df, catalogue_df, comparator_df, approval_df, linkage_df, recommendation_df)
        self.timing["scenario_calculations"] = time.perf_counter() - t_sc
        print(f"Completed {len(self.results)} scenario results")
        print(f"  [timing] scenario_calculations={self.timing['scenario_calculations']:.2f}s")

        t_out = time.perf_counter()
        print("\nWriting outputs...")
        self._write_all_outputs()
        self.timing["output_writing"] = time.perf_counter() - t_out
        print(f"  [timing] output_writing={self.timing['output_writing']:.2f}s")

        self.timing["total_execution"] = time.perf_counter() - t0
        print(f"  [timing] total_execution={self.timing['total_execution']:.2f}s")

        summary = self._build_summary()
        return summary

    def _run_all_scenarios(self, mapping_df, episode_df, catalogue_df, comparator_df, approval_df, linkage_df, recommendation_df):
        if mapping_df.empty:
            return

        baseline_lookup: Dict[str, ScenarioBaseline] = {}
        for bl in self.baselines:
            key = f"{bl.approval_package_id}|{bl.episode_id}|{bl.scenario_template_id}"
            baseline_lookup[key] = bl

        rec_lookup: Dict[str, List[str]] = {}
        if not linkage_df.empty and "approval_package_id" in linkage_df.columns and "recommendation_id" in linkage_df.columns:
            for _, row in linkage_df.iterrows():
                pkg = str(row.get("approval_package_id", ""))
                rec = str(row.get("recommendation_id", ""))
                if pkg and rec:
                    rec_lookup.setdefault(pkg, []).append(rec)

        for _, row in mapping_df.iterrows():
            package_id = str(row.get("approval_package_id", ""))
            template_id = str(row.get("scenario_template_id", ""))
            episode_id = str(row.get("episode_id", ""))
            review_status = str(row.get("scenario_review_priority", ""))

            if not package_id or not template_id or not episode_id:
                continue

            template_info = catalogue_df[catalogue_df["scenario_template_id"] == template_id]
            if template_info.empty:
                continue

            template = template_info.iloc[0].to_dict()
            family = str(template.get("scenario_family", ""))
            mode = str(template.get("scenario_mode", ""))

            baseline_key = f"{package_id}|{episode_id}|{template_id}"
            baseline = baseline_lookup.get(baseline_key)
            if baseline is None:
                continue

            if family in self.MONITORING_ONLY_FAMILIES or baseline.dominant_kpi_id in self.UNSUPPORTED_KPIS:
                self._create_non_quantitative_result(baseline, template, family, mode)
                continue

            if family not in self.SUPPORTED_QUANTITATIVE_FAMILIES and family not in self.MONITORING_ONLY_FAMILIES:
                result = self._create_blocked_result(baseline, template, "", "Unsupported family")
                result.scenario_execution_status = ScenarioExecutionStatus.BLOCKED_UNSUPPORTED_FAMILY
                result.governance_warning = f"Scenario family '{family}' is not supported for quantitative modelling."
                self.results.append(result)
                continue

            comparators = self.loader.get_comparators_for_template(template_id)
            if not comparators:
                comparators = [{
                    "comparator_id": f"{template_id}-BL",
                    "comparator_type": "Baseline",
                    "scenario_mode": mode,
                    "assumption_profile_id": "baseline",
                }]

            rec_ids = rec_lookup.get(package_id, [])

            for comp in comparators:
                result, validations = self._run_comparator(baseline, template, comp, family, rec_ids)
                self.results.append(result)
                self.validation_records.extend(validations)

                evidence = self.evidence_engine.create_evidence_for_result(
                    result, baseline.source_file_list, baseline.source_record_id_list, rec_ids, comp
                )
                self.evidence_records.extend(evidence)

                gov_checks = self.validator.check_governance_rules(baseline, {}, template_id)
                gov_records = self.evidence_engine.create_governance_records(result, gov_checks)
                self.governance_records.extend(gov_records)

                if result.scenario_execution_status in (
                    ScenarioExecutionStatus.BLOCKED_MISSING_BASELINE,
                    ScenarioExecutionStatus.BLOCKED_INVALID_ASSUMPTION,
                    ScenarioExecutionStatus.BLOCKED_MISSING_ASSUMPTION,
                    ScenarioExecutionStatus.BLOCKED_UNSUPPORTED_FAMILY,
                    ScenarioExecutionStatus.BLOCKED_GOVERNANCE_RULE,
                ):
                    issues = [result.governance_warning or f"Scenario blocked: {result.scenario_execution_status.value}"]
                    issue_records = self.evidence_engine.create_issue_records(result, issues)
                    self.issue_records.extend(issue_records)

    def _run_comparator(self, baseline, template, comparator, family, recommendation_ids):
        comparator_type = comparator.get("comparator_type", "Baseline")
        comparator_id = comparator.get("comparator_id", f"{template.get('scenario_template_id', '')}-{comparator_type}")
        profile_id = comparator.get("assumption_profile_id", "baseline")
        template_id = template.get("scenario_template_id", "")
        mode = template.get("scenario_mode", "")

        assumptions = self._build_assumptions(comparator, family)

        if family == "Staffing Coverage Adjustment":
            result, validations = self.staffing_engine.run(baseline, comparator, assumptions)
        elif family == "Absenteeism Contingency":
            result, validations = self.absenteeism_engine.run(baseline, comparator, assumptions)
        elif family == "Patient-Flow and Waiting-Time Adjustment":
            result, validations = self.flow_engine.run(baseline, comparator, assumptions)
        elif family == "Combined Workforce and Flow Intervention":
            result, validations = self.combined_engine.run(baseline, baseline, comparator, assumptions)
        else:
            result = self._create_baseline_comparator_result(baseline, comparator, template)
            validations = []

        provisional = baseline.baseline_provisional_flag
        partial_flow = family == "Patient-Flow and Waiting-Time Adjustment" and baseline.baseline_avg_wait_min is None
        combined_penalty = family == "Combined Workforce and Flow Intervention"

        confidence = self.confidence_engine.calculate_confidence(
            baseline=baseline,
            execution_status=result.scenario_execution_status,
            assumption_warning_count=result.assumption_warning_count,
            contradiction_severity=result.contradiction_severity,
            provisional_kpi_involved=provisional,
            partial_flow_coverage=partial_flow,
            combined_scenario_penalty=combined_penalty,
        )
        result.final_scenario_confidence = confidence
        result.recommendation_ids = recommendation_ids
        result.comparator_id = comparator_id
        result.comparator_config_version = "2C-2B-1.0"
        result.assumption_config_version = "2C-2B-1.0"

        return result, validations

    def _build_assumptions(self, comparator, family):
        assumptions = {}
        comparator_type = comparator.get("comparator_type", "Baseline")
        if comparator_type == "Baseline":
            return assumptions

        # Try assumption_profile_id first, then assumption_profile
        profile_id = comparator.get("assumption_profile_id", "") or comparator.get("assumption_profile", "")
        if profile_id:
            profile = self.loader.get_assumption_profile(profile_id)
            if profile:
                for key in profile:
                    if key.startswith("assumption_") or key in (
                        "additional_staff_count", "temporary_staff_count", "staff_reassignment_count",
                        "uncovered_shift_reduction_pct", "assumed_absenteeism_reduction_pct",
                        "replacement_coverage_pct", "contingency_roster_activation_pct", "absence_duration_reduction_days",
                        "arrival_change_pct", "service_capacity_change_pct",
                        "throughput_change_pct", "routing_efficiency_change_pct", "temporary_resource_change",
                        "interaction_adjustment_factor", "combined_scenario_confidence_penalty",
                        "max_coverage_pct", "max_wait_time_reduction_pct", "intervention_duration_days",
                    ):
                        assumptions[key] = profile.get(key)

        if not assumptions and comparator_type != "Baseline":
            if family == "Staffing Coverage Adjustment":
                assumptions = {
                    "additional_staff_count": 2.0,
                    "temporary_staff_count": 1.0,
                    "staff_reassignment_count": 0.0,
                    "uncovered_shift_reduction_pct": 0.0,
                    "max_coverage_pct": 100.0,
                }
            elif family == "Absenteeism Contingency":
                assumptions = {
                    "assumed_absenteeism_reduction_pct": 20.0,
                    "replacement_coverage_pct": 50.0,
                }
            elif family == "Patient-Flow and Waiting-Time Adjustment":
                assumptions = {
                    "arrival_change_pct": 0.0,
                    "service_capacity_change_pct": 10.0,
                    "throughput_change_pct": 5.0,
                    "routing_efficiency_change_pct": 0.0,
                    "max_wait_time_reduction_pct": 50.0,
                }
            elif family == "Combined Workforce and Flow Intervention":
                assumptions = {
                    "additional_staff_count": 2.0,
                    "temporary_staff_count": 1.0,
                    "arrival_change_pct": 0.0,
                    "service_capacity_change_pct": 10.0,
                    "throughput_change_pct": 5.0,
                    "interaction_adjustment_factor": 1.0,
                    "combined_scenario_confidence_penalty": 0.0,
                }

        return assumptions

    def _create_non_quantitative_result(self, baseline, template, family, mode):
        template_id = template.get("template_id", "")
        comparator_id = f"{template_id}-MON"

        result = ScenarioResult(
            scenario_run_id=f"SR-{baseline.baseline_id}-{comparator_id}",
            approval_package_id=baseline.approval_package_id,
            episode_id=baseline.episode_id,
            scenario_template_id=template_id,
            comparator_id=comparator_id,
            comparator_type=ComparatorType.BASELINE,
            scenario_family=family,
            scenario_mode=mode,
            scenario_run_timestamp=self.run_timestamp,
            engine_version=self.engine_version,
            baseline_id=baseline.baseline_id,
            baseline_status=baseline.baseline_status.value,
            baseline_value=baseline.baseline_kpi_value,
            baseline_unit=baseline.baseline_kpi_unit,
            baseline_reference_date=baseline.baseline_reference_date,
            baseline_data_completeness=baseline.baseline_data_completeness,
            primary_kpi_id=baseline.dominant_kpi_id,
            baseline_primary_kpi_value=baseline.baseline_kpi_value,
            scenario_execution_status=ScenarioExecutionStatus.MONITORING_ONLY,
            governance_warning=f"Non-quantitative family: {family}. Dominant KPI {baseline.dominant_kpi_id} is excluded from scenario calculations.",
            operational_interpretation=f"Monitoring Only: {baseline.dominant_kpi_id} is not supported for quantitative intervention modelling.",
            causality_status="Not Confirmed",
            source_file_list=baseline.source_file_list,
            source_record_id_list=baseline.source_record_id_list,
        )

        confidence = self.confidence_engine.calculate_confidence(
            baseline=baseline,
            execution_status=result.scenario_execution_status,
            assumption_warning_count=0,
            contradiction_severity=baseline.baseline_contradiction_severity,
            provisional_kpi_involved=baseline.baseline_provisional_flag,
        )
        result.final_scenario_confidence = confidence
        self.results.append(result)

        evidence = self.evidence_engine.create_evidence_for_result(
            result, baseline.source_file_list, baseline.source_record_id_list, [], {}
        )
        self.evidence_records.extend(evidence)

    def _create_blocked_result(self, baseline, template, comparator_id, reason):
        template_id = template.get("template_id", "")
        return ScenarioResult(
            scenario_run_id=f"SR-{baseline.baseline_id}-{comparator_id}",
            approval_package_id=baseline.approval_package_id,
            episode_id=baseline.episode_id,
            scenario_template_id=template_id,
            comparator_id=comparator_id or f"{template_id}-BLOCKED",
            comparator_type=ComparatorType.BASELINE,
            scenario_family=template.get("scenario_family", ""),
            scenario_mode=template.get("scenario_mode", ""),
            scenario_run_timestamp=self.run_timestamp,
            engine_version=self.engine_version,
            baseline_id=baseline.baseline_id,
            baseline_status=baseline.baseline_status.value,
            baseline_value=baseline.baseline_kpi_value,
            baseline_unit=baseline.baseline_kpi_unit,
            baseline_reference_date=baseline.baseline_reference_date,
            baseline_data_completeness=baseline.baseline_data_completeness,
            primary_kpi_id=baseline.dominant_kpi_id,
            baseline_primary_kpi_value=baseline.baseline_kpi_value,
            scenario_execution_status=ScenarioExecutionStatus.BLOCKED_UNSUPPORTED_FAMILY,
            governance_warning=reason,
            causality_status="Not Confirmed",
            source_file_list=baseline.source_file_list,
            source_record_id_list=baseline.source_record_id_list,
        )

    def _create_baseline_comparator_result(self, baseline, comparator, template):
        comparator_type = comparator.get("comparator_type", "Baseline")
        comparator_id = comparator.get("comparator_id", f"{template['template_id']}-{comparator_type}")
        template_id = template.get("template_id", "")
        family = template.get("scenario_family", "")
        mode = template.get("scenario_mode", "")

        return ScenarioResult(
            scenario_run_id=f"SR-{baseline.baseline_id}-{comparator_id}",
            approval_package_id=baseline.approval_package_id,
            episode_id=baseline.episode_id,
            scenario_template_id=template_id,
            comparator_id=comparator_id,
            comparator_type=parse_comparator_type(comparator_type),
            scenario_family=family,
            scenario_mode=mode,
            scenario_run_timestamp=self.run_timestamp,
            engine_version=self.engine_version,
            baseline_id=baseline.baseline_id,
            baseline_status=baseline.baseline_status.value,
            baseline_value=baseline.baseline_kpi_value,
            baseline_unit=baseline.baseline_kpi_unit,
            baseline_reference_date=baseline.baseline_reference_date,
            baseline_data_completeness=baseline.baseline_data_completeness,
            assumption_set_id="baseline",
            assumption_profile="baseline",
            assumption_values_json="{}",
            assumption_validation_status="Valid",
            assumption_warning_count=0,
            primary_kpi_id=baseline.dominant_kpi_id,
            baseline_primary_kpi_value=baseline.baseline_kpi_value,
            scenario_primary_kpi_value=baseline.baseline_kpi_value,
            absolute_change=0.0,
            percentage_change=0.0,
            direction_of_change=DirectionOfChange.NO_CHANGE,
            operational_interpretation="Baseline / No-Action comparator. No intervention assumptions applied.",
            scenario_execution_status=ScenarioExecutionStatus.COMPLETED,
            calculation_rule_id="baseline-no-action",
            comparator_config_version="2C-2B-1.0",
            assumption_config_version="2C-2B-1.0",
            causality_status="Not Confirmed",
            source_file_list=baseline.source_file_list,
            source_record_id_list=baseline.source_record_id_list,
        )

    def _write_all_outputs(self):
        out_dir = os.path.join(self.base_dir, "data", "analytical")
        os.makedirs(out_dir, exist_ok=True)
        scenario_dir = os.path.join(self.base_dir, "outputs", "scenario_modelling")
        os.makedirs(scenario_dir, exist_ok=True)
        docs_dir = os.path.join(self.base_dir, "docs")
        os.makedirs(docs_dir, exist_ok=True)

        total_steps = 12
        step = 0

        # A. Baselines
        step += 1
        t = time.perf_counter()
        _log_progress(step, total_steps, "Writing analytical_scenario_baselines.csv", t)
        bl_df = self.baseline_engine.baselines_to_dataframe(self.baselines)
        bl_path = os.path.join(out_dir, "analytical_scenario_baselines.csv")
        bl_df.to_csv(bl_path, index=False)
        _log_complete(step, total_steps, "analytical_scenario_baselines.csv", len(bl_df), os.path.getsize(bl_path), t)

        # B. Scenario runs
        step += 1
        t = time.perf_counter()
        _log_progress(step, total_steps, "Writing analytical_scenario_runs.csv", t)
        runs_path = os.path.join(out_dir, "analytical_scenario_runs.csv")
        if self.results:
            runs_df = pd.DataFrame([r.to_dict() for r in self.results])
            runs_df.to_csv(runs_path, index=False)
            _log_complete(step, total_steps, "analytical_scenario_runs.csv", len(runs_df), os.path.getsize(runs_path), t)
        else:
            pd.DataFrame().to_csv(runs_path, index=False)
            _log_complete(step, total_steps, "analytical_scenario_runs.csv", 0, os.path.getsize(runs_path), t)

        # C. KPI impacts
        step += 1
        t = time.perf_counter()
        _log_progress(step, total_steps, "Writing analytical_scenario_kpi_impacts.csv", t)
        impacts = []
        for r in self.results:
            impacts.append({
                "scenario_run_id": r.scenario_run_id,
                "primary_kpi_id": r.primary_kpi_id,
                "baseline_value": r.baseline_primary_kpi_value,
                "scenario_value": r.scenario_primary_kpi_value,
                "absolute_change": r.absolute_change,
                "percentage_change": r.percentage_change,
                "direction_of_change": r.direction_of_change.value,
                "affected_supporting_kpis": r.affected_supporting_kpis,
                "supporting_kpi_result_status": r.supporting_kpi_result_status,
            })
        impacts_path = os.path.join(out_dir, "analytical_scenario_kpi_impacts.csv")
        pd.DataFrame(impacts).to_csv(impacts_path, index=False)
        _log_complete(step, total_steps, "analytical_scenario_kpi_impacts.csv", len(impacts), os.path.getsize(impacts_path), t)

        # D. Assumption validation
        step += 1
        t = time.perf_counter()
        _log_progress(step, total_steps, "Writing analytical_scenario_assumption_validation.csv", t)
        val_path = os.path.join(out_dir, "analytical_scenario_assumption_validation.csv")
        if self.validation_records:
            val_df = pd.DataFrame([{
                "validation_id": f"VAL-{i}",
                "assumption_id": v.assumption_id,
                "original_value": v.original_value,
                "validated_value": v.validated_value,
                "validation_outcome": v.validation_outcome.value,
                "validation_message": v.validation_message,
                "adjustment_applied": v.adjustment_applied,
                "hard_limit_violated": v.hard_limit_violated,
                "soft_limit_violated": v.soft_limit_violated,
            } for i, v in enumerate(self.validation_records)])
            val_df.to_csv(val_path, index=False)
            _log_complete(step, total_steps, "analytical_scenario_assumption_validation.csv", len(val_df), os.path.getsize(val_path), t)
        else:
            pd.DataFrame().to_csv(val_path, index=False)
            _log_complete(step, total_steps, "analytical_scenario_assumption_validation.csv", 0, os.path.getsize(val_path), t)

        # E. Confidence
        step += 1
        t = time.perf_counter()
        _log_progress(step, total_steps, "Writing analytical_scenario_confidence.csv", t)
        confs = []
        for r in self.results:
            bl = next((b for b in self.baselines if b.baseline_id == r.baseline_id), None)
            rationale = self.confidence_engine.confidence_rationale(
                baseline=bl,
                execution_status=r.scenario_execution_status,
                assumption_warning_count=r.assumption_warning_count,
                contradiction_severity=r.contradiction_severity,
                provisional_kpi_involved=r.provisional_warning,
            )
            confs.append({
                "scenario_run_id": r.scenario_run_id,
                "confidence_base": rationale.get("confidence_base", 0) if rationale else 0,
                "confidence_adjustments": json.dumps(rationale.get("confidence_adjustments", [])) if rationale else "[]",
                "confidence_score_internal": rationale.get("confidence_score_internal", "") if rationale else "",
                "final_scenario_confidence": r.final_scenario_confidence.value,
                "confidence_rationale": rationale.get("confidence_rationale", "") if rationale else "",
            })
        conf_path = os.path.join(out_dir, "analytical_scenario_confidence.csv")
        pd.DataFrame(confs).to_csv(conf_path, index=False)
        _log_complete(step, total_steps, "analytical_scenario_confidence.csv", len(confs), os.path.getsize(conf_path), t)

        # F. Non-quantitative register
        step += 1
        t = time.perf_counter()
        _log_progress(step, total_steps, "Writing analytical_scenario_non_quantitative_register.csv", t)
        nonq = [r.to_dict() for r in self.results if r.scenario_execution_status in (
            ScenarioExecutionStatus.MONITORING_ONLY,
            ScenarioExecutionStatus.VALIDATION_REQUIRED,
            ScenarioExecutionStatus.BLOCKED_UNSUPPORTED_FAMILY,
        )]
        nonq_path = os.path.join(out_dir, "analytical_scenario_non_quantitative_register.csv")
        pd.DataFrame(nonq).to_csv(nonq_path, index=False)
        _log_complete(step, total_steps, "analytical_scenario_non_quantitative_register.csv", len(nonq), os.path.getsize(nonq_path), t)

        # G. Evidence
        step += 1
        t = time.perf_counter()
        _log_progress(step, total_steps, "Writing analytical_scenario_evidence.csv", t)
        ev_path = os.path.join(out_dir, "analytical_scenario_evidence.csv")
        if self.evidence_records:
            ev_df = pd.DataFrame(self.evidence_engine.evidence_to_dict(self.evidence_records))
            ev_df.to_csv(ev_path, index=False)
            _log_complete(step, total_steps, "analytical_scenario_evidence.csv", len(ev_df), os.path.getsize(ev_path), t)
        else:
            pd.DataFrame().to_csv(ev_path, index=False)
            _log_complete(step, total_steps, "analytical_scenario_evidence.csv", 0, os.path.getsize(ev_path), t)

        # H. Lineage
        step += 1
        t = time.perf_counter()
        _log_progress(step, total_steps, "Writing analytical_scenario_lineage.csv", t)
        lin_path = os.path.join(out_dir, "analytical_scenario_lineage.csv")
        if self.evidence_records:
            lineage = [{
                "lineage_id": f"LIN-{e.evidence_id}",
                "scenario_run_id": e.scenario_run_id,
                "source_type": e.source_type,
                "source_id": e.source_id,
                "source_file": e.source_file,
                "link_type": e.link_type,
                "recorded_at": e.recorded_at,
            } for e in self.evidence_records]
            pd.DataFrame(lineage).to_csv(lin_path, index=False)
            _log_complete(step, total_steps, "analytical_scenario_lineage.csv", len(lineage), os.path.getsize(lin_path), t)
        else:
            pd.DataFrame().to_csv(lin_path, index=False)
            _log_complete(step, total_steps, "analytical_scenario_lineage.csv", 0, os.path.getsize(lin_path), t)

        # I. Governance
        step += 1
        t = time.perf_counter()
        _log_progress(step, total_steps, "Writing analytical_scenario_governance.csv", t)
        gov_path = os.path.join(out_dir, "analytical_scenario_governance.csv")
        if self.governance_records:
            gov_df = pd.DataFrame(self.evidence_engine.governance_to_dict(self.governance_records))
            gov_df.to_csv(gov_path, index=False)
            _log_complete(step, total_steps, "analytical_scenario_governance.csv", len(gov_df), os.path.getsize(gov_path), t)
        else:
            pd.DataFrame().to_csv(gov_path, index=False)
            _log_complete(step, total_steps, "analytical_scenario_governance.csv", 0, os.path.getsize(gov_path), t)

        # J. Issues
        step += 1
        t = time.perf_counter()
        _log_progress(step, total_steps, "Writing analytical_scenario_issues.csv", t)
        iss_path = os.path.join(out_dir, "analytical_scenario_issues.csv")
        if self.issue_records:
            iss_df = pd.DataFrame(self.evidence_engine.issues_to_dict(self.issue_records))
            iss_df.to_csv(iss_path, index=False)
            _log_complete(step, total_steps, "analytical_scenario_issues.csv", len(iss_df), os.path.getsize(iss_path), t)
        else:
            pd.DataFrame().to_csv(iss_path, index=False)
            _log_complete(step, total_steps, "analytical_scenario_issues.csv", 0, os.path.getsize(iss_path), t)

        # K. Run manifest JSON
        step += 1
        t = time.perf_counter()
        _log_progress(step, total_steps, "Writing step_2c2c_run_manifest.json", t)
        manifest_path = os.path.join(scenario_dir, "step_2c2c_run_manifest.json")
        summary = self._build_summary()
        with open(manifest_path, "w") as f:
            json.dump(summary, f, indent=2, default=str)
        _log_complete(step, total_steps, "step_2c2c_run_manifest.json", len(summary), os.path.getsize(manifest_path), t)

        # L. Execution summary CSV
        step += 1
        t = time.perf_counter()
        _log_progress(step, total_steps, "Writing step_2c2c_execution_summary.csv", t)
        summary_for_csv = self._build_summary()
        exec_summary = pd.DataFrame([{
            "metric": k,
            "value": v,
        } for k, v in summary_for_csv.items()])
        summary_path = os.path.join(scenario_dir, "step_2c2c_execution_summary.csv")
        exec_summary.to_csv(summary_path, index=False)
        _log_complete(step, total_steps, "step_2c2c_execution_summary.csv", len(exec_summary), os.path.getsize(summary_path), t)

    def _build_summary(self) -> Dict[str, Any]:
        total = len(self.results)
        completed = sum(1 for r in self.results if r.scenario_execution_status == ScenarioExecutionStatus.COMPLETED)
        completed_warn = sum(1 for r in self.results if r.scenario_execution_status == ScenarioExecutionStatus.COMPLETED_WITH_WARNINGS)
        blocked_baseline = sum(1 for r in self.results if r.scenario_execution_status == ScenarioExecutionStatus.BLOCKED_MISSING_BASELINE)
        blocked_assumption = sum(1 for r in self.results if r.scenario_execution_status == ScenarioExecutionStatus.BLOCKED_MISSING_ASSUMPTION)
        blocked_invalid = sum(1 for r in self.results if r.scenario_execution_status == ScenarioExecutionStatus.BLOCKED_INVALID_ASSUMPTION)
        blocked_unsupported = sum(1 for r in self.results if r.scenario_execution_status == ScenarioExecutionStatus.BLOCKED_UNSUPPORTED_FAMILY)
        blocked_gov = sum(1 for r in self.results if r.scenario_execution_status == ScenarioExecutionStatus.BLOCKED_GOVERNANCE_RULE)
        monitoring = sum(1 for r in self.results if r.scenario_execution_status == ScenarioExecutionStatus.MONITORING_ONLY)
        validation_req = sum(1 for r in self.results if r.scenario_execution_status == ScenarioExecutionStatus.VALIDATION_REQUIRED)
        not_selected = sum(1 for r in self.results if r.scenario_execution_status == ScenarioExecutionStatus.NOT_SELECTED)

        staffing = sum(1 for r in self.results if r.scenario_family == "Staffing Coverage Adjustment" and r.scenario_execution_status in (ScenarioExecutionStatus.COMPLETED, ScenarioExecutionStatus.COMPLETED_WITH_WARNINGS))
        absenteeism = sum(1 for r in self.results if r.scenario_family == "Absenteeism Contingency" and r.scenario_execution_status in (ScenarioExecutionStatus.COMPLETED, ScenarioExecutionStatus.COMPLETED_WITH_WARNINGS))
        flow = sum(1 for r in self.results if r.scenario_family == "Patient-Flow and Waiting-Time Adjustment" and r.scenario_execution_status in (ScenarioExecutionStatus.COMPLETED, ScenarioExecutionStatus.COMPLETED_WITH_WARNINGS))
        combined = sum(1 for r in self.results if r.scenario_family == "Combined Workforce and Flow Intervention" and r.scenario_execution_status in (ScenarioExecutionStatus.COMPLETED, ScenarioExecutionStatus.COMPLETED_WITH_WARNINGS))
        baseline_comp = sum(1 for r in self.results if r.comparator_type == ComparatorType.BASELINE and r.scenario_execution_status in (ScenarioExecutionStatus.COMPLETED, ScenarioExecutionStatus.COMPLETED_WITH_WARNINGS))
        conservative = sum(1 for r in self.results if r.comparator_type == ComparatorType.CONSERVATIVE and r.scenario_execution_status in (ScenarioExecutionStatus.COMPLETED, ScenarioExecutionStatus.COMPLETED_WITH_WARNINGS))
        expected = sum(1 for r in self.results if r.comparator_type == ComparatorType.EXPECTED and r.scenario_execution_status in (ScenarioExecutionStatus.COMPLETED, ScenarioExecutionStatus.COMPLETED_WITH_WARNINGS))
        higher = sum(1 for r in self.results if r.comparator_type == ComparatorType.HIGHER_INTENSITY and r.scenario_execution_status in (ScenarioExecutionStatus.COMPLETED, ScenarioExecutionStatus.COMPLETED_WITH_WARNINGS))

        moderate = sum(1 for r in self.results if r.final_scenario_confidence == ScenarioConfidence.MODERATE)
        low = sum(1 for r in self.results if r.final_scenario_confidence == ScenarioConfidence.LOW)
        insufficient = sum(1 for r in self.results if r.final_scenario_confidence == ScenarioConfidence.INSUFFICIENT_EVIDENCE)
        material_contra = sum(1 for r in self.results if r.contradiction_severity == "Material")
        provisional_warn = sum(1 for r in self.results if r.provisional_warning)
        evidence_linked = sum(1 for r in self.results if any(e.scenario_run_id == r.scenario_run_id for e in self.evidence_records))
        lineage_linked = sum(1 for r in self.results if any(e.scenario_run_id == r.scenario_run_id and e.evidence_type == "Episode" for e in self.evidence_records))

        baselines_available = sum(1 for b in self.baselines if b.baseline_status == BaselineStatus.AVAILABLE)
        baselines_cond = sum(1 for b in self.baselines if b.baseline_status == BaselineStatus.AVAILABLE_WITH_CONDITIONS)
        baselines_partial = sum(1 for b in self.baselines if b.baseline_status == BaselineStatus.PARTIAL)
        baselines_unavailable = sum(1 for b in self.baselines if b.baseline_status == BaselineStatus.UNAVAILABLE)
        baselines_blocked = sum(1 for b in self.baselines if b.baseline_status == BaselineStatus.BLOCKED)

        return {
            "packages_assessed": len(self.baselines),
            "baselines_created": len(self.baselines),
            "baselines_available": baselines_available,
            "baselines_available_with_conditions": baselines_cond,
            "baselines_partial": baselines_partial,
            "baselines_missing": baselines_unavailable + baselines_blocked,
            "scenario_runs_attempted": total,
            "scenario_runs_completed": completed,
            "scenario_runs_completed_with_warnings": completed_warn,
            "scenarios_blocked_by_missing_baseline": blocked_baseline,
            "scenarios_blocked_by_missing_assumption": blocked_assumption,
            "scenarios_blocked_by_invalid_assumption": blocked_invalid,
            "monitoring_only_records": monitoring,
            "validation_required_records": validation_req,
            "staffing_scenarios_completed": staffing,
            "absenteeism_scenarios_completed": absenteeism,
            "patient_flow_scenarios_completed": flow,
            "combined_scenarios_completed": combined,
            "baseline_comparators_completed": baseline_comp,
            "conservative_comparators_completed": conservative,
            "expected_comparators_completed": expected,
            "higher_intensity_comparators_completed": higher,
            "moderate_confidence_results": moderate,
            "low_confidence_results": low,
            "insufficient_evidence_results": insufficient,
            "material_contradiction_results": material_contra,
            "provisional_warning_results": provisional_warn,
            "evidence_linkage_result": evidence_linked,
            "lineage_result": lineage_linked,
            "test_results": "Pending",
            "upstream_immutability_result": "Not Verified",
            "no_financial_calculations": True,
            "readiness_for_2c2d": "Ready for Step 2C-2D Multi-KPI Impact and Trade-Off Analysis",
            "engine_version": self.engine_version,
            "run_timestamp": self.run_timestamp,
            "timing_seconds": self.timing,
        }


if __name__ == "__main__":
    runner = ScenarioModellingEngineRunner()
    summary = runner.run()
    print("\n" + "=" * 60)
    print("Execution Summary")
    print("=" * 60)
    for k, v in summary.items():
        if k == "timing_seconds":
            print(f"  {k}:")
            for tk, tv in v.items():
                print(f"    {tk}: {tv:.2f}s")
        else:
            print(f"  {k}: {v}")
