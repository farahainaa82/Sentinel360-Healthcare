"""Scenario trade-off analysis runner.

Phase 2C-2D — Multi-KPI Impact and Trade-Off Analysis orchestrator.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.scenario_impact_analysis_engine import ScenarioImpactAnalysisEngine
from src.scenario_displacement_engine import ScenarioDisplacementEngine
from src.scenario_dominance_engine import ScenarioDominanceEngine
from src.scenario_sensitivity_engine import ScenarioSensitivityEngine
from src.scenario_tradeoff_engine import ScenarioTradeoffEngine

LOCK_FILE = "outputs/scenario_modelling/.tradeoff_lock"


def _acquire_lock() -> bool:
    try:
        os.makedirs(os.path.dirname(LOCK_FILE), exist_ok=True)
        fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "w") as f:
            f.write(f"pid={os.getpid()}\nstarted={datetime.now(timezone.utc).isoformat()}\n")
        return True
    except FileExistsError:
        return False


def _release_lock():
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


class ScenarioTradeoffAnalysisRunner:
    """Orchestrates the Phase 2C-2D trade-off analysis pipeline."""

    SUPPORTED_FAMILIES = {
        "Staffing Coverage Adjustment",
        "Absenteeism Contingency",
        "Patient-Flow and Waiting-Time Adjustment",
        "Combined Workforce and Flow Intervention",
        "No-Action or Baseline Comparator",
    }
    QUANTITATIVE_STATUSES = {"Completed", "Completed with Warnings"}

    def __init__(self, base_dir: str = "."):
        self.base_dir = base_dir
        self.impact_engine = ScenarioImpactAnalysisEngine(os.path.join(base_dir, "config"))
        self.displacement_engine = ScenarioDisplacementEngine(os.path.join(base_dir, "config"))
        self.dominance_engine = ScenarioDominanceEngine(os.path.join(base_dir, "config"))
        self.sensitivity_engine = ScenarioSensitivityEngine(os.path.join(base_dir, "config"))
        self.tradeoff_engine = ScenarioTradeoffEngine(os.path.join(base_dir, "config"))

        self.run_timestamp = datetime.now(timezone.utc).isoformat()
        self.engine_version = "2C-2D-1.0"
        self.timing: Dict[str, float] = {}

        # Output collections
        self.primary_impacts: List[Dict[str, Any]] = []
        self.supporting_kpi_impacts: List[Dict[str, Any]] = []
        self.effect_classifications: List[Dict[str, Any]] = []
        self.tradeoffs: List[Dict[str, Any]] = []
        self.displacements: List[Dict[str, Any]] = []
        self.comparator_analyses: List[Dict[str, Any]] = []
        self.diminishing_returns: List[Dict[str, Any]] = []
        self.dominance_records: List[Dict[str, Any]] = []
        self.sensitivity_records: List[Dict[str, Any]] = []
        self.tradeoff_profiles: List[Dict[str, Any]] = []
        self.management_interpretations: List[Dict[str, Any]] = []
        self.evidence_records: List[Dict[str, Any]] = []
        self.lineage_records: List[Dict[str, Any]] = []
        self.governance_records: List[Dict[str, Any]] = []
        self.issue_records: List[Dict[str, Any]] = []
        self.non_comparable: List[Dict[str, Any]] = []

    def run(self) -> Dict[str, Any]:
        if not _acquire_lock():
            print("ERROR: Another trade-off analysis is already running.")
            return {"status": "blocked", "reason": "Another trade-off analysis is already running."}

        try:
            return self._run_locked()
        finally:
            _release_lock()

    def _run_locked(self) -> Dict[str, Any]:
        t0 = time.perf_counter()
        print("Phase 2C-2D: Multi-KPI Impact and Trade-Off Analysis")
        print("=" * 60)

        # Load inputs
        t_load = time.perf_counter()
        runs_df = pd.read_csv(os.path.join(self.base_dir, "data", "analytical", "analytical_scenario_runs.csv"), keep_default_na=False)
        baselines_df = pd.read_csv(os.path.join(self.base_dir, "data", "analytical", "analytical_scenario_baselines.csv"), keep_default_na=False)
        self.timing["input_loading"] = time.perf_counter() - t_load

        print(f"Loaded {len(runs_df)} scenario runs")
        print(f"Loaded {len(baselines_df)} baselines")
        print(f"  [timing] input_loading={self.timing['input_loading']:.2f}s")

        # Separate quantitative vs non-comparable
        quant_mask = runs_df["scenario_execution_status"].isin(self.QUANTITATIVE_STATUSES)
        quant_runs = runs_df[quant_mask].copy()
        non_quant_runs = runs_df[~quant_mask].copy()

        print(f"Quantitative runs: {len(quant_runs)}")
        print(f"Non-comparable runs: {len(non_quant_runs)}")

        # Build baseline lookup
        baseline_lookup = {}
        for _, row in baselines_df.iterrows():
            key = row.get("baseline_id", "")
            if key:
                baseline_lookup[key] = row.to_dict()

        # Process non-comparable register
        for _, row in non_quant_runs.iterrows():
            self.non_comparable.append(row.to_dict())

        # Process quantitative runs
        t_calc = time.perf_counter()
        self._process_quantitative_runs(quant_runs, baseline_lookup)
        self.timing["tradeoff_calculations"] = time.perf_counter() - t_calc
        print(f"  [timing] tradeoff_calculations={self.timing['tradeoff_calculations']:.2f}s")

        # Write outputs
        t_out = time.perf_counter()
        self._write_all_outputs()
        self.timing["output_writing"] = time.perf_counter() - t_out
        print(f"  [timing] output_writing={self.timing['output_writing']:.2f}s")

        self.timing["total_execution"] = time.perf_counter() - t0
        print(f"  [timing] total_execution={self.timing['total_execution']:.2f}s")

        summary = self._build_summary()
        return summary

    def _process_quantitative_runs(self, quant_runs: pd.DataFrame, baseline_lookup: Dict[str, Any]):
        # Group by package + template for comparator comparisons
        grouped = quant_runs.groupby(["approval_package_id", "scenario_template_id"])

        for (pkg_id, template_id), group in grouped:
            runs = [row.to_dict() for _, row in group.iterrows()]
            self._process_package_template(pkg_id, template_id, runs, baseline_lookup)

    def _process_package_template(
        self,
        pkg_id: str,
        template_id: str,
        runs: List[Dict[str, Any]],
        baseline_lookup: Dict[str, Any],
    ):
        # Sort comparators
        comparator_order = {"Baseline": 0, "Conservative": 1, "Expected": 2, "Higher Intensity": 3}
        runs = sorted(runs, key=lambda r: comparator_order.get(r.get("comparator_type", "Baseline"), 0))

        # Get baseline, conservative, expected, higher
        baseline = next((r for r in runs if r.get("comparator_type") == "Baseline"), None)
        conservative = next((r for r in runs if r.get("comparator_type") == "Conservative"), None)
        expected = next((r for r in runs if r.get("comparator_type") == "Expected"), None)
        higher = next((r for r in runs if r.get("comparator_type") == "Higher Intensity"), None)

        # Process each run
        for run in runs:
            bl = baseline_lookup.get(run.get("baseline_id", ""), {})
            self._process_single_run(run, bl, baseline, conservative, expected, higher)

        # Comparator trade-off analysis
        if baseline and (conservative or expected or higher):
            comparisons = self.tradeoff_engine.compare_comparators(baseline, conservative, expected, higher)
            self.comparator_analyses.extend(comparisons)

        # Diminishing returns
        dr = self.tradeoff_engine.assess_diminishing_returns(baseline, conservative, expected, higher)
        if dr:
            dr_record = {
                "diminishing_return_id": f"DR-{pkg_id}-{template_id}",
                "approval_package_id": pkg_id,
                "scenario_template_id": template_id,
                "diminishing_return_classification": dr.get("diminishing_return_classification", ""),
                "diminishing_return_rationale": dr.get("diminishing_return_rationale", ""),
                "incremental_effect_ratios_json": json.dumps(dr.get("incremental_effect_ratios", [])),
            }
            self.diminishing_returns.append(dr_record)

        # Sensitivity analysis
        sens = self.sensitivity_engine.analyse_sensitivity(runs)
        if sens:
            sens_record = {
                "sensitivity_id": f"SENS-{pkg_id}-{template_id}",
                "approval_package_id": pkg_id,
                "scenario_template_id": template_id,
                "sensitivity_classification": sens.get("sensitivity_classification", ""),
                "sensitivity_rationale": sens.get("sensitivity_rationale", ""),
                "direction_stable": sens.get("direction_stable", False),
                "magnitude_variation": sens.get("magnitude_variation", 0),
                "warning_increase": sens.get("warning_increase", False),
                "confidence_change": sens.get("confidence_change", False),
                "direction_reversal": sens.get("direction_reversal", False),
                "comparator_count": sens.get("comparator_count", 0),
            }
            self.sensitivity_records.append(sens_record)

        # Dominance analysis (pairwise)
        for i, run_a in enumerate(runs):
            for run_b in runs[i + 1:]:
                dom = self.dominance_engine.compare_pairwise(run_a, run_b)
                dom_record = {
                    "dominance_id": f"DOM-{run_a.get('scenario_run_id', '')}-{run_b.get('scenario_run_id', '')}",
                    "scenario_run_id_a": run_a.get("scenario_run_id", ""),
                    "scenario_run_id_b": run_b.get("scenario_run_id", ""),
                    "approval_package_id": pkg_id,
                    "scenario_template_id": template_id,
                    "dominance_classification": dom.get("dominance_classification", ""),
                    "dominance_rationale": dom.get("dominance_rationale", ""),
                    "conditions_met_json": json.dumps(dom.get("dominance_conditions_met", [])),
                    "conditions_failed_json": json.dumps(dom.get("dominance_conditions_failed", [])),
                }
                self.dominance_records.append(dom_record)

        # Management interpretation
        interp = self._build_management_interpretation(pkg_id, template_id, runs, baseline, conservative, expected, higher)
        self.management_interpretations.append(interp)

    def _process_single_run(
        self,
        run: Dict[str, Any],
        baseline: Dict[str, Any],
        baseline_comp: Optional[Dict[str, Any]],
        conservative: Optional[Dict[str, Any]],
        expected: Optional[Dict[str, Any]],
        higher: Optional[Dict[str, Any]],
    ):
        # Primary impact
        pct_change = self._to_float(run.get("percentage_change", 0))
        direction = run.get("direction_of_change", "")
        primary_kpi = run.get("primary_kpi_id", "")

        impact = self.impact_engine.classify_primary_impact(primary_kpi, pct_change, direction)
        primary_record = {
            "primary_impact_id": f"PI-{run.get('scenario_run_id', '')}",
            "scenario_run_id": run.get("scenario_run_id", ""),
            "approval_package_id": run.get("approval_package_id", ""),
            "episode_id": run.get("episode_id", ""),
            "primary_kpi_id": primary_kpi,
            "baseline_primary_kpi_value": run.get("baseline_primary_kpi_value", ""),
            "scenario_primary_kpi_value": run.get("scenario_primary_kpi_value", ""),
            "absolute_change": run.get("absolute_change", ""),
            "percentage_change": pct_change,
            "direction_of_change": direction,
            "comparator_type": run.get("comparator_type", ""),
            "scenario_family": run.get("scenario_family", ""),
            "final_scenario_confidence": run.get("final_scenario_confidence", ""),
            "impact_classification": impact.get("impact_classification", ""),
            "effect_direction": impact.get("effect_direction", ""),
            "evidence_language": impact.get("evidence_language", ""),
        }
        self.primary_impacts.append(primary_record)

        # Supporting KPI
        supporting = self.impact_engine.analyse_supporting_kpis(
            run.get("supporting_kpi_result_status", ""),
            self._parse_list(run.get("affected_supporting_kpis", "")),
        )
        supporting_record = {
            "supporting_impact_id": f"SK-{run.get('scenario_run_id', '')}",
            "scenario_run_id": run.get("scenario_run_id", ""),
            "approval_package_id": run.get("approval_package_id", ""),
            "episode_id": run.get("episode_id", ""),
            "supporting_kpi_status": supporting.get("supporting_kpi_status", ""),
            "expected_direction_if_any": supporting.get("expected_direction_if_any", ""),
            "evidence_basis": supporting.get("evidence_basis", ""),
            "uncertainty": supporting.get("uncertainty", ""),
            "monitoring_requirement": supporting.get("monitoring_requirement", ""),
        }
        self.supporting_kpi_impacts.append(supporting_record)

        # Effect classification
        effect = self._classify_effect(run, impact)
        self.effect_classifications.append(effect)

        # Displacement
        displacements = self.displacement_engine.analyse_displacement(run, baseline)
        self.displacements.extend(displacements)

        # Trade-off profile
        displacement_risk = displacements[0].get("displacement_classification", "No Displacement Identified") if displacements else "No Displacement Identified"
        profile = self.tradeoff_engine.build_tradeoff_profile(run, supporting.get("supporting_kpi_status", ""), displacement_risk)
        profile_record = {
            "profile_id": f"TP-{run.get('scenario_run_id', '')}",
            "scenario_run_id": run.get("scenario_run_id", ""),
            "approval_package_id": run.get("approval_package_id", ""),
            "episode_id": run.get("episode_id", ""),
            "analytical_trade_off_index": profile.get("analytical_trade_off_index", 0),
            "index_components_json": json.dumps(profile.get("index_components", {})),
            "index_weights_json": json.dumps(profile.get("index_weights", {})),
            "trade_off_band": profile.get("trade_off_band", ""),
            "trade_off_rationale": profile.get("trade_off_rationale", ""),
        }
        self.tradeoff_profiles.append(profile_record)

        # Evidence and lineage
        self._create_evidence_and_lineage(run)

    def _classify_effect(self, run: Dict[str, Any], impact: Dict[str, Any]) -> Dict[str, Any]:
        direction = impact.get("effect_direction", "")
        classification = impact.get("impact_classification", "")

        if "Improvement" in classification:
            effect_class = "Benefit"
        elif "Adverse" in classification:
            effect_class = "Adverse Effect"
        elif "No Material" in classification or "No Change" in direction:
            effect_class = "Neutral"
        elif "Insufficient" in classification:
            effect_class = "Uncertain"
        else:
            effect_class = "Not Quantified"

        magnitude_band = "Unknown"
        if "Strong" in classification:
            magnitude_band = "Strong"
        elif "Moderate" in classification:
            magnitude_band = "Moderate"
        elif "Small" in classification:
            magnitude_band = "Small"
        elif "No Material" in classification:
            magnitude_band = "None"

        return {
            "effect_id": f"EFF-{run.get('scenario_run_id', '')}",
            "scenario_run_id": run.get("scenario_run_id", ""),
            "approval_package_id": run.get("approval_package_id", ""),
            "episode_id": run.get("episode_id", ""),
            "affected_kpi_id": run.get("primary_kpi_id", ""),
            "effect_classification": effect_class,
            "effect_direction": direction,
            "effect_magnitude_band": magnitude_band,
            "evidence_basis": impact.get("evidence_language", ""),
            "confidence": run.get("final_scenario_confidence", ""),
            "contradiction_severity": run.get("contradiction_severity", ""),
            "provisional_warning": run.get("provisional_warning", False),
            "monitoring_requirement": "Monitor primary KPI trends" if effect_class in ("Benefit", "Adverse Effect") else "None",
        }

    def _build_management_interpretation(
        self,
        pkg_id: str,
        template_id: str,
        runs: List[Dict[str, Any]],
        baseline: Optional[Dict[str, Any]],
        conservative: Optional[Dict[str, Any]],
        expected: Optional[Dict[str, Any]],
        higher: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        # Build comparator summary
        comp_summaries = []
        for comp_name, comp in [("Baseline", baseline), ("Conservative", conservative), ("Expected", expected), ("Higher Intensity", higher)]:
            if comp:
                comp_summaries.append(f"{comp_name}: {comp.get('direction_of_change', '')} ({comp.get('percentage_change', 0)}%)")

        # Determine sensitivity
        sens = self.sensitivity_engine.analyse_sensitivity(runs)

        # Determine diminishing returns
        dr = self.tradeoff_engine.assess_diminishing_returns(baseline, conservative, expected, higher)

        # Determine overall readiness
        has_completed = any(r.get("scenario_execution_status") in self.QUANTITATIVE_STATUSES for r in runs)
        has_warnings = any(r.get("assumption_warning_count", 0) > 0 for r in runs)
        has_contra = any(r.get("contradiction_severity", "") not in ("", "No Contradiction") for r in runs)

        if has_completed and not has_warnings and not has_contra:
            readiness = "Suitable for Management Comparison"
        elif has_completed and has_warnings and not has_contra:
            readiness = "Suitable for Limited-Trial Consideration"
        elif has_completed and has_contra:
            readiness = "Requires Additional Validation"
        else:
            readiness = "Requires Monitoring-Only Approach"

        interpretation_text = (
            f"Package {pkg_id} ({template_id}): "
            f"Comparators show {'; '.join(comp_summaries)}. "
            f"Sensitivity: {sens.get('sensitivity_classification', 'Unknown')}. "
            f"Diminishing returns: {dr.get('diminishing_return_classification', 'Unknown')}. "
            f"Management validation required for assumption accuracy and operational feasibility."
        )

        return {
            "interpretation_id": f"INT-{pkg_id}-{template_id}",
            "approval_package_id": pkg_id,
            "scenario_template_id": template_id,
            "episode_id": runs[0].get("episode_id", "") if runs else "",
            "scenario_family": runs[0].get("scenario_family", "") if runs else "",
            "comparator_summary": "; ".join(comp_summaries),
            "primary_kpi_effect": expected.get("operational_interpretation", "") if expected else (conservative.get("operational_interpretation", "") if conservative else ""),
            "supporting_kpi_effects": "See supporting KPI impact records",
            "adverse_effects": "See effect classification records",
            "displacement_risk": "See displacement records",
            "assumption_drivers": "See assumption validation records",
            "management_validation_required": has_warnings or has_contra,
            "sensitivity_classification": sens.get("sensitivity_classification", ""),
            "diminishing_return_classification": dr.get("diminishing_return_classification", ""),
            "trade_off_band": "See trade-off profile records",
            "management_readiness": readiness,
            "interpretation_text": interpretation_text,
        }

    def _create_evidence_and_lineage(self, run: Dict[str, Any]):
        evidence = {
            "evidence_id": f"EV-{uuid.uuid4().hex[:16].upper()}",
            "scenario_run_id": run.get("scenario_run_id", ""),
            "evidence_type": "Trade-Off Analysis",
            "source_type": "Step 2C-2C Scenario Run",
            "source_id": run.get("scenario_run_id", ""),
            "source_file": "analytical_scenario_runs.csv",
            "link_type": "Derived",
            "recorded_at": self.run_timestamp,
        }
        self.evidence_records.append(evidence)

        lineage = {
            "lineage_id": f"LIN-{evidence['evidence_id']}",
            "scenario_run_id": run.get("scenario_run_id", ""),
            "source_type": "Trade-Off Analysis",
            "source_id": run.get("scenario_run_id", ""),
            "source_file": "analytical_scenario_runs.csv",
            "link_type": "Derived",
            "recorded_at": self.run_timestamp,
        }
        self.lineage_records.append(lineage)

    def _write_all_outputs(self):
        out_dir = os.path.join(self.base_dir, "data", "analytical")
        os.makedirs(out_dir, exist_ok=True)
        scenario_dir = os.path.join(self.base_dir, "outputs", "scenario_modelling")
        os.makedirs(scenario_dir, exist_ok=True)

        total_steps = 18
        step = 0

        def write_csv(data: List[Dict[str, Any]], filename: str):
            nonlocal step
            step += 1
            t = time.perf_counter()
            _log_progress(step, total_steps, f"Writing {filename}", t)
            path = os.path.join(out_dir, filename)
            if data:
                pd.DataFrame(data).to_csv(path, index=False)
            else:
                pd.DataFrame().to_csv(path, index=False)
            _log_complete(step, total_steps, filename, len(data), os.path.getsize(path), t)

        write_csv(self.primary_impacts, "analytical_scenario_primary_impacts.csv")
        write_csv(self.supporting_kpi_impacts, "analytical_scenario_supporting_kpi_impacts.csv")
        write_csv(self.effect_classifications, "analytical_scenario_effect_classification.csv")
        write_csv(self.tradeoffs, "analytical_scenario_tradeoffs.csv")
        write_csv(self.displacements, "analytical_scenario_risk_displacement.csv")
        write_csv(self.comparator_analyses, "analytical_scenario_comparator_analysis.csv")
        write_csv(self.diminishing_returns, "analytical_scenario_diminishing_returns.csv")
        write_csv(self.dominance_records, "analytical_scenario_dominance.csv")
        write_csv(self.sensitivity_records, "analytical_scenario_sensitivity.csv")
        write_csv(self.tradeoff_profiles, "analytical_scenario_tradeoff_profiles.csv")
        write_csv(self.management_interpretations, "analytical_scenario_management_interpretation.csv")
        write_csv(self.evidence_records, "analytical_scenario_tradeoff_evidence.csv")
        write_csv(self.lineage_records, "analytical_scenario_tradeoff_lineage.csv")
        write_csv(self.governance_records, "analytical_scenario_tradeoff_governance.csv")
        write_csv(self.issue_records, "analytical_scenario_tradeoff_issues.csv")
        write_csv(self.non_comparable, "analytical_scenario_non_comparable_register.csv")

        # Manifest
        step += 1
        t = time.perf_counter()
        _log_progress(step, total_steps, "Writing step_2c2d_run_manifest.json", t)
        manifest_path = os.path.join(scenario_dir, "step_2c2d_run_manifest.json")
        summary = self._build_summary()
        with open(manifest_path, "w") as f:
            json.dump(summary, f, indent=2, default=str)
        _log_complete(step, total_steps, "step_2c2d_run_manifest.json", len(summary), os.path.getsize(manifest_path), t)

        # Execution summary
        step += 1
        t = time.perf_counter()
        _log_progress(step, total_steps, "Writing step_2c2d_execution_summary.csv", t)
        summary_path = os.path.join(scenario_dir, "step_2c2d_execution_summary.csv")
        pd.DataFrame([{"metric": k, "value": v} for k, v in summary.items()]).to_csv(summary_path, index=False)
        _log_complete(step, total_steps, "step_2c2d_execution_summary.csv", len(summary), os.path.getsize(summary_path), t)

    def _build_summary(self) -> Dict[str, Any]:
        quant_runs = len(self.primary_impacts)
        non_quant = len(self.non_comparable)

        strong_improve = sum(1 for r in self.primary_impacts if "Strong" in r.get("impact_classification", "") and "Improvement" in r.get("impact_classification", ""))
        moderate_improve = sum(1 for r in self.primary_impacts if "Moderate" in r.get("impact_classification", "") and "Improvement" in r.get("impact_classification", ""))
        small_improve = sum(1 for r in self.primary_impacts if "Small" in r.get("impact_classification", "") and "Improvement" in r.get("impact_classification", ""))
        no_change = sum(1 for r in self.primary_impacts if "No Material" in r.get("impact_classification", ""))
        adverse = sum(1 for r in self.primary_impacts if "Adverse" in r.get("impact_classification", ""))

        benefits = sum(1 for r in self.effect_classifications if r.get("effect_classification") == "Benefit")
        adverse_effects = sum(1 for r in self.effect_classifications if r.get("effect_classification") == "Adverse Effect")
        uncertain = sum(1 for r in self.effect_classifications if r.get("effect_classification") == "Uncertain")

        within_dept = sum(1 for r in self.displacements if "Within-Department" in r.get("displacement_classification", ""))
        cross_dept = sum(1 for r in self.displacements if "Cross-Department" in r.get("displacement_classification", ""))
        cross_kpi = sum(1 for r in self.displacements if "Cross-KPI" in r.get("displacement_classification", ""))
        material_disp = sum(1 for r in self.displacements if "Material" in r.get("displacement_classification", ""))

        dominates = sum(1 for r in self.dominance_records if r.get("dominance_classification") == "Dominates")
        weakly_dominates = sum(1 for r in self.dominance_records if r.get("dominance_classification") == "Weakly Dominates")
        non_dominated = sum(1 for r in self.dominance_records if r.get("dominance_classification") == "Non-Dominated")
        dominated = sum(1 for r in self.dominance_records if r.get("dominance_classification") == "Dominated")
        incomparable = sum(1 for r in self.dominance_records if r.get("dominance_classification") == "Incomparable")

        favourable = sum(1 for r in self.tradeoff_profiles if r.get("trade_off_band") == "Favourable but Conditional")
        balanced = sum(1 for r in self.tradeoff_profiles if r.get("trade_off_band") == "Balanced Trade-Off")
        mixed = sum(1 for r in self.tradeoff_profiles if r.get("trade_off_band") == "Mixed Trade-Off")
        unfavourable = sum(1 for r in self.tradeoff_profiles if r.get("trade_off_band") == "Unfavourable Trade-Off")

        stable_dir = sum(1 for r in self.sensitivity_records if r.get("sensitivity_classification") == "Stable Direction")
        sens_assumption = sum(1 for r in self.sensitivity_records if r.get("sensitivity_classification") == "Sensitive to Assumption Intensity")
        reversal = sum(1 for r in self.sensitivity_records if r.get("sensitivity_classification") == "Direction Reversal")

        moderate_conf = sum(1 for r in self.primary_impacts if r.get("final_scenario_confidence") == "Moderate")
        low_conf = sum(1 for r in self.primary_impacts if r.get("final_scenario_confidence") == "Low")
        insufficient_conf = sum(1 for r in self.primary_impacts if r.get("final_scenario_confidence") == "Insufficient Evidence")

        material_contra = sum(1 for r in self.primary_impacts if r.get("contradiction_severity") == "Material")
        provisional_warn = sum(1 for r in self.primary_impacts if r.get("provisional_warning", False))

        management_ready = sum(1 for r in self.management_interpretations if "Suitable" in r.get("management_readiness", ""))
        validation_required = sum(1 for r in self.management_interpretations if "Requires" in r.get("management_readiness", ""))

        return {
            "scenario_runs_reviewed": quant_runs + non_quant,
            "quantitatively_comparable_runs": quant_runs,
            "non_comparable_runs": non_quant,
            "approval_packages_reviewed": len(set(r.get("approval_package_id", "") for r in self.primary_impacts)),
            "episodes_reviewed": len(set(r.get("episode_id", "") for r in self.primary_impacts)),
            "strong_directional_improvements": strong_improve,
            "moderate_directional_improvements": moderate_improve,
            "small_directional_improvements": small_improve,
            "no_material_change_results": no_change,
            "adverse_change_results": adverse,
            "benefits_identified": benefits,
            "adverse_effects_identified": adverse_effects,
            "uncertain_effects_identified": uncertain,
            "possible_within_department_displacement": within_dept,
            "possible_cross_department_displacement": cross_dept,
            "possible_cross_kpi_displacement": cross_kpi,
            "material_displacement_risks": material_disp,
            "comparator_pairs_analysed": len(self.comparator_analyses),
            "diminishing_improvement_findings": sum(1 for r in self.diminishing_returns if "Diminishing" in r.get("diminishing_return_classification", "")),
            "direction_reversal_findings": reversal,
            "dominant_scenarios": dominates,
            "weakly_dominant_scenarios": weakly_dominates,
            "non_dominated_scenarios": non_dominated,
            "dominated_scenarios": dominated,
            "incomparable_scenarios": incomparable,
            "favourable_but_conditional_profiles": favourable,
            "balanced_trade_offs": balanced,
            "mixed_trade_offs": mixed,
            "unfavourable_trade_offs": unfavourable,
            "stable_direction_sensitivity": stable_dir,
            "assumption_sensitive_results": sens_assumption,
            "moderate_confidence_results": moderate_conf,
            "low_confidence_results": low_conf,
            "insufficient_evidence_results": insufficient_conf,
            "material_contradiction_results": material_contra,
            "provisional_warning_results": provisional_warn,
            "management_comparison_ready": management_ready,
            "additional_validation_required": validation_required,
            "evidence_linkage_result": len(self.evidence_records),
            "lineage_result": len(self.lineage_records),
            "test_results": "Pending",
            "upstream_immutability_result": "Not Verified",
            "no_preferred_scenario_selected": True,
            "no_financial_calculations": True,
            "readiness_for_2c2e": "Ready for Step 2C-2E Scenario Validation and Challenge",
            "engine_version": self.engine_version,
            "run_timestamp": self.run_timestamp,
            "timing_seconds": self.timing,
        }

    @staticmethod
    def _to_float(value) -> float:
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def _parse_list(value) -> List[str]:
        if not value or value == "[]" or value == "":
            return []
        if isinstance(value, str):
            # Try JSON parse first
            import json
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            # Fallback: comma-separated
            return [v.strip() for v in value.split(",") if v.strip()]
        return []


if __name__ == "__main__":
    runner = ScenarioTradeoffAnalysisRunner()
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
