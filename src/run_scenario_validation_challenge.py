"""
Step 2C-2E Main Runner — Scenario Validation and Challenge.

Features:
- Execution lock (prevents concurrent runs)
- Smoke-test mode (3 packages)
- Progress logging
- Batch output writing (temp -> final atomic move)
- Temporary output directory
- Manifest generation after outputs complete
- Governed engine orchestration
"""

import os
import sys
import json
import time
import shutil
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd

# Import all Task 3 engines
from scenario_validation_base_engine import ValidationEngineBase
from scenario_assumption_challenge_engine import AssumptionChallengeEngine
from scenario_baseline_validation_engine import BaselineValidationEngine
from scenario_numerical_validation_engine import NumericalValidationEngine
from scenario_comparator_validation_engine import ComparatorValidationEngine
from scenario_dominance_validation_engine import DominanceValidationEngine
from scenario_sensitivity_validation_engine import SensitivityValidationEngine
from scenario_diminishing_returns_validation_engine import DiminishingReturnsValidationEngine
from scenario_displacement_validation_engine import DisplacementValidationEngine
from scenario_management_interpretation_validator import ManagementInterpretationValidator
from scenario_validation_scorecard_engine import ValidationScorecardEngine
from scenario_validation_evidence_engine import ValidationEvidenceEngine
from scenario_validation_governance_validator import ValidationGovernanceValidator


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"


def setup_logging(log_dir: str) -> logging.Logger:
    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger("step_2c2e")
    logger.setLevel(logging.INFO)
    if logger.handlers:
        logger.handlers.clear()
    fh = logging.FileHandler(os.path.join(log_dir, "step_2c2e_runner.log"), encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(fh)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(ch)
    return logger


# ---------------------------------------------------------------------------
# Execution lock
# ---------------------------------------------------------------------------
class ExecutionLock:
    def __init__(self, lock_path: str):
        self.lock_path = lock_path
        self.acquired = False

    def acquire(self) -> bool:
        if os.path.exists(self.lock_path):
            return False
        with open(self.lock_path, "w", encoding="utf-8") as f:
            f.write(f"pid={os.getpid()}\nstarted={datetime.now().isoformat()}\n")
        self.acquired = True
        return True

    def release(self) -> None:
        if self.acquired and os.path.exists(self.lock_path):
            os.remove(self.lock_path)
            self.acquired = False


# ---------------------------------------------------------------------------
# Checksum helper
# ---------------------------------------------------------------------------
def file_checksum(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------
class ValidationRunner:
    def __init__(
        self,
        data_dir: str = None,
        config_dir: str = None,
        temp_dir: str = None,
        final_dir: str = None,
        log_dir: str = None,
        smoke_test: bool = False,
        smoke_packages: int = 3,
    ):
        self.project_root = Path(__file__).parent.parent
        self.data_dir = data_dir or str(self.project_root / "data" / "analytical")
        self.config_dir = config_dir or str(self.project_root / "config")
        self.temp_dir = temp_dir or str(self.project_root / "outputs" / "scenario_modelling" / "_temp_2c2e")
        self.final_dir = final_dir or str(self.project_root / "data" / "analytical")
        self.log_dir = log_dir or str(self.project_root / "outputs" / "scenario_modelling")
        self.smoke_test = smoke_test
        self.smoke_packages = smoke_packages
        self.logger = setup_logging(self.log_dir)
        self.stage_timings: Dict[str, float] = {}
        self.engines: List[ValidationEngineBase] = []
        self.manifest: Dict[str, Any] = {}

        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.final_dir, exist_ok=True)

    def log(self, msg: str) -> None:
        self.logger.info(msg)

    def _stage(self, name: str):
        class _StageCtx:
            def __init__(ctx_self, runner, stage_name):
                ctx_self.runner = runner
                ctx_self.stage_name = stage_name
                ctx_self.start = time.time()
                runner.log(f"[STAGE START] {stage_name}")

            def __enter__(ctx_self):
                return ctx_self

            def __exit__(ctx_self, *args):
                elapsed = time.time() - ctx_self.start
                ctx_self.runner.stage_timings[ctx_self.stage_name] = elapsed
                ctx_self.runner.log(f"[STAGE END] {ctx_self.stage_name} — {elapsed:.2f}s")
        return _StageCtx(self, name)

    def _filter_smoke(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self.smoke_test or df.empty:
            return df
        if "approval_package_id" in df.columns:
            pkgs = df["approval_package_id"].unique()[: self.smoke_packages]
            return df[df["approval_package_id"].isin(pkgs)].copy()
        return df

    def run(self) -> Dict[str, Any]:
        lock_path = os.path.join(self.temp_dir, "execution.lock")
        lock = ExecutionLock(lock_path)
        if not lock.acquire():
            self.log("ERROR: Another Step 2C-2E run is already in progress. Exiting.")
            return {"status": "locked", "message": "Execution lock in place"}

        try:
            self.log("=" * 60)
            self.log(f"Step 2C-2E Runner started — smoke_test={self.smoke_test}")
            self.log("=" * 60)

            # -----------------------------------------------------------------
            # Stage 1: Load inputs
            # -----------------------------------------------------------------
            with self._stage("load_inputs"):
                runs = pd.read_csv(os.path.join(self.data_dir, "analytical_scenario_runs.csv"))
                if self.smoke_test:
                    smoke_pkg_ids = runs["approval_package_id"].unique()[: self.smoke_packages]
                    runs = runs[runs["approval_package_id"].isin(smoke_pkg_ids)].copy()
                    self.log(f"Smoke test mode: filtered to {len(smoke_pkg_ids)} packages, {len(runs)} runs")

                # Save smoke-filtered inputs to temp for engine consistency
                smoke_runs_path = os.path.join(self.temp_dir, "_smoke_analytical_scenario_runs.csv")
                runs.to_csv(smoke_runs_path, index=False)
                self.log(f"Loaded {len(runs)} scenario runs")

            # -----------------------------------------------------------------
            # Stage 2: Run individual validation engines
            # -----------------------------------------------------------------
            engine_outputs = {}

            with self._stage("assumption_challenge"):
                e = AssumptionChallengeEngine(data_dir=self.data_dir, config_dir=self.config_dir, output_dir=self.temp_dir)
                engine_outputs["assumption_challenge"] = e.run()
                self.engines.append(e)
                self.log(f"Assumption challenge: {len(engine_outputs['assumption_challenge'])} records")

            with self._stage("baseline_validation"):
                e = BaselineValidationEngine(data_dir=self.data_dir, config_dir=self.config_dir, output_dir=self.temp_dir)
                engine_outputs["baseline_validation"] = e.run()
                self.engines.append(e)
                self.log(f"Baseline validation: {len(engine_outputs['baseline_validation'])} records")

            with self._stage("numerical_validation"):
                e = NumericalValidationEngine(data_dir=self.data_dir, config_dir=self.config_dir, output_dir=self.temp_dir)
                engine_outputs["numerical_validation"] = e.run()
                self.engines.append(e)
                self.log(f"Numerical validation: {len(engine_outputs['numerical_validation'])} records")

            with self._stage("comparator_validation"):
                e = ComparatorValidationEngine(data_dir=self.data_dir, config_dir=self.config_dir, output_dir=self.temp_dir)
                engine_outputs["comparator_validation"] = e.run()
                self.engines.append(e)
                self.log(f"Comparator validation: {len(engine_outputs['comparator_validation'])} records")

            with self._stage("dominance_validation"):
                e = DominanceValidationEngine(data_dir=self.data_dir, config_dir=self.config_dir, output_dir=self.temp_dir)
                engine_outputs["dominance_validation"] = e.run(comparator_validation_df=engine_outputs["comparator_validation"])
                self.engines.append(e)
                self.log(f"Dominance validation: {len(engine_outputs['dominance_validation'])} records")

            with self._stage("sensitivity_validation"):
                e = SensitivityValidationEngine(data_dir=self.data_dir, config_dir=self.config_dir, output_dir=self.temp_dir)
                engine_outputs["sensitivity_validation"] = e.run(comparator_validation_df=engine_outputs["comparator_validation"])
                self.engines.append(e)
                self.log(f"Sensitivity validation: {len(engine_outputs['sensitivity_validation'])} records")

            with self._stage("diminishing_returns_validation"):
                e = DiminishingReturnsValidationEngine(data_dir=self.data_dir, config_dir=self.config_dir, output_dir=self.temp_dir)
                engine_outputs["diminishing_returns_validation"] = e.run(
                    comparator_validation_df=engine_outputs["comparator_validation"],
                    runs_df=runs,
                )
                self.engines.append(e)
                self.log(f"Diminishing returns validation: {len(engine_outputs['diminishing_returns_validation'])} records")

            with self._stage("displacement_validation"):
                e = DisplacementValidationEngine(data_dir=self.data_dir, config_dir=self.config_dir, output_dir=self.temp_dir)
                engine_outputs["displacement_validation"] = e.run()
                self.engines.append(e)
                self.log(f"Displacement validation: {len(engine_outputs['displacement_validation'])} records")

            with self._stage("management_interpretation"):
                e = ManagementInterpretationValidator(data_dir=self.data_dir, config_dir=self.config_dir, output_dir=self.temp_dir)
                engine_outputs["management_interpretation"] = e.run()
                self.engines.append(e)
                self.log(f"Management interpretation: {len(engine_outputs['management_interpretation'])} records")

            with self._stage("governance_validator"):
                e = ValidationGovernanceValidator(data_dir=self.data_dir, config_dir=self.config_dir, output_dir=self.temp_dir)
                engine_outputs["governance"] = e.run()
                self.engines.append(e)
                self.log(f"Governance validation: {len(engine_outputs['governance'])} records")

            # -----------------------------------------------------------------
            # Stage 3: Scorecard (depends on prior engines)
            # -----------------------------------------------------------------
            with self._stage("scorecard"):
                e = ValidationScorecardEngine(data_dir=self.data_dir, config_dir=self.config_dir, output_dir=self.temp_dir)
                engine_outputs["scorecard"] = e.run(
                    baseline_validation=engine_outputs["baseline_validation"],
                    assumption_challenge=engine_outputs["assumption_challenge"],
                    numerical_validation=engine_outputs["numerical_validation"],
                    comparator_validation=engine_outputs["comparator_validation"],
                    dominance_validation=engine_outputs["dominance_validation"],
                    sensitivity_validation=engine_outputs["sensitivity_validation"],
                    displacement_validation=engine_outputs["displacement_validation"],
                    diminishing_returns_validation=engine_outputs["diminishing_returns_validation"],
                    interpretation_validation=engine_outputs["management_interpretation"],
                    runs=runs,
                )
                self.engines.append(e)
                self.log(f"Scorecard: {len(engine_outputs['scorecard'])} packages")

            # -----------------------------------------------------------------
            # Stage 4: Evidence / Lineage / Governance / Issues aggregation
            # -----------------------------------------------------------------
            with self._stage("evidence_aggregation"):
                e = ValidationEvidenceEngine(data_dir=self.data_dir, config_dir=self.config_dir, output_dir=self.temp_dir)
                engine_outputs["evidence_bundle"] = e.run(self.engines)
                self.engines.append(e)
                self.log("Evidence aggregation complete")

            # -----------------------------------------------------------------
            # Stage 5: Package readiness
            # -----------------------------------------------------------------
            with self._stage("package_readiness"):
                readiness = self._compute_package_readiness(engine_outputs, runs)
                readiness_path = os.path.join(self.temp_dir, "analytical_scenario_package_readiness.csv")
                readiness.to_csv(readiness_path, index=False)
                engine_outputs["package_readiness"] = readiness
                self.log(f"Package readiness: {len(readiness)} packages")

            # -----------------------------------------------------------------
            # Stage 6: Validation register
            # -----------------------------------------------------------------
            with self._stage("validation_register"):
                reg = self._compute_validation_register(engine_outputs, runs)
                reg_path = os.path.join(self.temp_dir, "analytical_scenario_validation_register.csv")
                reg.to_csv(reg_path, index=False)
                engine_outputs["validation_register"] = reg
                self.log(f"Validation register: {len(reg)} records")

            # -----------------------------------------------------------------
            # Stage 7: Rejected register & revision log
            # -----------------------------------------------------------------
            with self._stage("rejected_and_revision"):
                rejected, revision = self._compute_rejected_and_revision(engine_outputs, runs)
                rejected.to_csv(os.path.join(self.temp_dir, "analytical_scenario_rejected_register.csv"), index=False)
                revision.to_csv(os.path.join(self.temp_dir, "analytical_scenario_revision_log.csv"), index=False)
                engine_outputs["rejected_register"] = rejected
                engine_outputs["revision_log"] = revision
                self.log(f"Rejected register: {len(rejected)} records")
                self.log(f"Revision log: {len(revision)} records")

            # -----------------------------------------------------------------
            # Stage 8: Atomic move temp -> final
            # -----------------------------------------------------------------
            with self._stage("atomic_move"):
                moved_files = self._atomic_move_to_final()
                self.log(f"Atomic move complete: {len(moved_files)} files")

            # -----------------------------------------------------------------
            # Stage 9: Manifest generation
            # -----------------------------------------------------------------
            with self._stage("manifest"):
                self._generate_manifest(engine_outputs, moved_files)
                self.log("Manifest generated")

            self.log("=" * 60)
            self.log("Step 2C-2E Runner completed successfully")
            self.log("=" * 60)

            return {
                "status": "success",
                "smoke_test": self.smoke_test,
                "stage_timings": self.stage_timings,
                "outputs": {k: len(v) if hasattr(v, "__len__") else 1 for k, v in engine_outputs.items()},
            }

        except Exception as exc:
            self.log(f"FATAL ERROR: {exc}")
            import traceback
            self.log(traceback.format_exc())
            return {"status": "error", "error": str(exc)}

        finally:
            lock.release()
            self.log("Execution lock released")

    # -----------------------------------------------------------------
    # Package readiness computation
    # -----------------------------------------------------------------
    def _compute_package_readiness(self, outputs: Dict[str, pd.DataFrame], runs: pd.DataFrame) -> pd.DataFrame:
        scorecard = outputs["scorecard"]
        comp = outputs["comparator_validation"]
        baseline = outputs["baseline_validation"]
        assumption = outputs["assumption_challenge"]

        merged = scorecard.copy()
        merged = merged.merge(comp[["approval_package_id", "validation_status"]].rename(columns={"validation_status": "comparator_status"}), on="approval_package_id", how="left")
        merged = merged.merge(baseline.groupby("approval_package_id")["validation_status"].first().reset_index().rename(columns={"validation_status": "baseline_status"}), on="approval_package_id", how="left")
        merged = merged.merge(assumption.groupby("approval_package_id")["challenge_status"].first().reset_index().rename(columns={"challenge_status": "assumption_status"}), on="approval_package_id", how="left")

        def classify(row):
            if row["validation_classification"] == "Strong Validation":
                return "Ready"
            if row["validation_classification"] == "Acceptable with Conditions":
                return "Ready with Conditions"
            if row["validation_classification"] == "Weak Validation":
                return "Not Ready"
            return "Rejected"

        merged["package_readiness"] = merged.apply(classify, axis=1)
        merged["readiness_rationale"] = merged["validation_classification"]
        return merged[["approval_package_id", "package_readiness", "readiness_rationale",
                       "scenario_validation_index", "comparator_status", "baseline_status", "assumption_status",
                       "engine_name", "engine_version", "run_timestamp"]]

    # -----------------------------------------------------------------
    # Validation register computation
    # -----------------------------------------------------------------
    def _compute_validation_register(self, outputs: Dict[str, pd.DataFrame], runs: pd.DataFrame) -> pd.DataFrame:
        # Start with runs and attach validation statuses
        reg = runs[["scenario_run_id", "approval_package_id", "episode_id", "scenario_template_id",
                    "comparator_id", "comparator_type", "scenario_family", "final_scenario_confidence",
                    "causality_status", "baseline_status"]].copy()

        bl = outputs["baseline_validation"][["scenario_run_id", "validation_status"]].rename(columns={"validation_status": "baseline_validation_status"}).drop_duplicates("scenario_run_id")
        num = outputs["numerical_validation"][["scenario_run_id", "validation_status"]].rename(columns={"validation_status": "numerical_validation_status"}).drop_duplicates("scenario_run_id")
        ass = outputs["assumption_challenge"][["scenario_run_id", "challenge_status"]].rename(columns={"challenge_status": "assumption_challenge_status"}).drop_duplicates("scenario_run_id")
        gov = outputs["governance"][["scenario_run_id", "governance_status"]].rename(columns={"governance_status": "governance_compliance_status"}).drop_duplicates("scenario_run_id")

        reg = reg.merge(bl, on="scenario_run_id", how="left")
        reg = reg.merge(num, on="scenario_run_id", how="left")
        reg = reg.merge(ass, on="scenario_run_id", how="left")
        reg = reg.merge(gov, on="scenario_run_id", how="left")

        def overall_status(row):
            if row.get("baseline_validation_status") == "Invalid":
                return "Invalid Baseline"
            if row.get("assumption_challenge_status") == "Failed":
                return "Failed Assumption Challenge"
            if row.get("governance_compliance_status") == "Non-Compliant":
                return "Non-Compliant"
            if any(pd.isna(row[c]) or str(row[c]).startswith("Valid") or str(row[c]).startswith("Passed") or str(row[c]).startswith("Compliant") for c in ["baseline_validation_status", "numerical_validation_status", "assumption_challenge_status", "governance_compliance_status"]):
                return "Valid with Conditions"
            return "Valid"

        reg["overall_validation_status"] = reg.apply(overall_status, axis=1)
        reg["validation_timestamp"] = datetime.now().isoformat()
        return reg

    # -----------------------------------------------------------------
    # Rejected register & revision log
    # -----------------------------------------------------------------
    def _compute_rejected_and_revision(self, outputs: Dict[str, pd.DataFrame], runs: pd.DataFrame) -> tuple:
        reg = outputs["validation_register"]
        rejected = reg[reg["overall_validation_status"].isin(["Invalid Baseline", "Failed Assumption Challenge", "Non-Compliant", "Rejected"])].copy()
        rejected["rejection_reason"] = rejected["overall_validation_status"]
        rejected["rejection_timestamp"] = datetime.now().isoformat()

        revision = reg[reg["overall_validation_status"] == "Valid with Conditions"].copy()
        revision["revision_required"] = True
        revision["revision_type"] = "Validation Flags"
        revision["revision_timestamp"] = datetime.now().isoformat()

        return rejected, revision

    # -----------------------------------------------------------------
    # Atomic move
    # -----------------------------------------------------------------
    def _atomic_move_to_final(self) -> List[str]:
        moved = []
        for fname in os.listdir(self.temp_dir):
            if not fname.endswith(".csv"):
                continue
            if fname.startswith("_smoke_") or fname == "execution.lock":
                continue
            src = os.path.join(self.temp_dir, fname)
            dst = os.path.join(self.final_dir, fname)
            shutil.move(src, dst)
            moved.append(fname)
            self.log(f"Moved {fname} -> final")
        return moved

    # -----------------------------------------------------------------
    # Manifest generation
    # -----------------------------------------------------------------
    def _generate_manifest(self, outputs: Dict[str, pd.DataFrame], moved_files: List[str]) -> None:
        manifest = {
            "step": "2C-2E",
            "run_timestamp": datetime.now().isoformat(),
            "smoke_test": self.smoke_test,
            "engine_version": "2C-2E-1.0",
            "stage_timings_seconds": self.stage_timings,
            "outputs": {},
        }
        for fname in moved_files:
            fpath = os.path.join(self.final_dir, fname)
            if os.path.exists(fpath):
                manifest["outputs"][fname] = {
                    "checksum_sha256": file_checksum(fpath),
                    "size_bytes": os.path.getsize(fpath),
                }
        manifest_path = os.path.join(self.project_root, "outputs", "scenario_modelling", "step_2c2e_run_manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        self.manifest = manifest


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------
def main():
    smoke = "--smoke" in sys.argv or "--smoke-test" in sys.argv
    runner = ValidationRunner(smoke_test=smoke)
    result = runner.run()
    print(json.dumps(result, indent=2, default=str))
    sys.exit(0 if result.get("status") == "success" else 1)


if __name__ == "__main__":
    main()
