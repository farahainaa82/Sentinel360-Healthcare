"""
Step 2C-2E Focused Comparator Assumption Correction Runner.

This script:
1. Loads the current scenario runs
2. Applies governed assumption profiles from config/scenario_assumption_profile_config.csv
3. Regenerates scenario_runs with distinct comparator assumptions
4. Preserves all baselines and observed data
5. Does not calculate financial impact
6. Does not select preferred scenarios
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
from typing import Dict, List, Any

import pandas as pd

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"


def setup_logging(log_dir: str) -> logging.Logger:
    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger("comparator_correction")
    logger.setLevel(logging.INFO)
    if logger.handlers:
        logger.handlers.clear()
    fh = logging.FileHandler(os.path.join(log_dir, "step_2c2_comparator_correction.log"), encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(fh)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(ch)
    return logger


class ComparatorCorrectionRunner:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.data_dir = str(self.project_root / "data" / "analytical")
        self.config_dir = str(self.project_root / "config")
        self.output_dir = str(self.project_root / "outputs" / "scenario_modelling")
        self.temp_dir = os.path.join(self.output_dir, "_temp_2c2_correction")
        os.makedirs(self.temp_dir, exist_ok=True)
        self.logger = setup_logging(self.output_dir)
        self.revision_log: List[Dict[str, Any]] = []
        self.run_timestamp = datetime.now().isoformat()

    def log(self, msg: str) -> None:
        self.logger.info(msg)

    def load_csv(self, filename: str) -> pd.DataFrame:
        return pd.read_csv(os.path.join(self.data_dir, filename))

    def load_config(self, filename: str) -> pd.DataFrame:
        return pd.read_csv(os.path.join(self.config_dir, filename))

    def run(self) -> Dict[str, Any]:
        self.log("=" * 60)
        self.log("Comparator Assumption Correction Started")
        self.log("=" * 60)

        # Load inputs
        runs = self.load_csv("analytical_scenario_runs.csv")
        profiles = self.load_config("scenario_assumption_profile_config.csv")
        baselines = self.load_csv("analytical_scenario_baselines.csv")

        self.log(f"Loaded {len(runs)} scenario runs")
        self.log(f"Loaded {len(profiles)} profile rows")

        # Build profile lookup: (scenario_template_id, comparator_type, assumption_name) -> value
        profile_lookup = {}
        for _, row in profiles.iterrows():
            key = (row["scenario_template_id"], row["comparator_type"], row["assumption_name"])
            profile_lookup[key] = {
                "value": row["assumption_value"],
                "unit": row["unit"],
                "version": row["version"],
            }

        # Build baseline lookup for staffing scale
        baseline_lookup = {}
        for _, row in baselines.iterrows():
            baseline_lookup[row["baseline_id"]] = {
                "required_staff": row.get("baseline_required_staff", 0),
                "available_staff": row.get("baseline_available_staff", 0),
                "staffing_coverage_pct": row.get("baseline_staffing_coverage_pct", 0),
            }

        corrected_rows = []
        changes_made = 0
        identical_before = 0
        identical_after = 0

        for _, row in runs.iterrows():
            new_row = row.to_dict()
            ctype = row["comparator_type"]
            stid = row["scenario_template_id"]
            family = row["scenario_family"]

            if ctype not in ("Conservative", "Expected", "Higher Intensity"):
                corrected_rows.append(new_row)
                continue

            # Get current assumption values
            try:
                current_vals = json.loads(row["assumption_values_json"]) if pd.notna(row["assumption_values_json"]) else {}
            except:
                current_vals = {}

            # Build new assumption values from profile
            new_vals = {}
            profile_keys = [k for k in profile_lookup.keys() if k[0] == stid and k[1] == ctype]
            for pk in profile_keys:
                assumption_name = pk[2]
                new_vals[assumption_name] = profile_lookup[pk]["value"]

            if not new_vals:
                corrected_rows.append(new_row)
                continue

            # Check if values changed
            changed = False
            for k, v in new_vals.items():
                old_v = current_vals.get(k)
                if old_v != v:
                    changed = True
                    self.revision_log.append({
                        "scenario_run_id": row["scenario_run_id"],
                        "approval_package_id": row["approval_package_id"],
                        "scenario_template_id": stid,
                        "scenario_family": family,
                        "comparator_type": ctype,
                        "assumption_name": k,
                        "old_value": old_v,
                        "new_value": v,
                        "unit": profile_lookup.get((stid, ctype, k), {}).get("unit", ""),
                        "reason": "Governed comparator profile correction",
                        "version": "2C-2E-CORR-1.0",
                        "timestamp": self.run_timestamp,
                    })

            if changed:
                changes_made += 1
                new_row["assumption_values_json"] = json.dumps(new_vals)
                new_row["assumption_config_version"] = "2C-2E-CORR-1.0"

            corrected_rows.append(new_row)

        # Check identical profiles before and after
        df_corrected = pd.DataFrame(corrected_rows)
        comparable = df_corrected[df_corrected["comparator_type"].isin(["Conservative", "Expected", "Higher Intensity"])]

        for pkg in comparable["approval_package_id"].unique():
            pkg_runs = comparable[comparable["approval_package_id"] == pkg]
            vectors = []
            for _, pr in pkg_runs.iterrows():
                try:
                    v = json.dumps(json.loads(pr["assumption_values_json"]), sort_keys=True)
                except:
                    v = ""
                vectors.append(v)
            if len(set(vectors)) <= 1 and len(vectors) > 1:
                identical_after += 1

        self.log(f"Changes made to {changes_made} scenario runs")
        self.log(f"Identical profiles after correction: {identical_after} packages")

        # Write corrected runs to temp
        temp_runs_path = os.path.join(self.temp_dir, "analytical_scenario_runs.csv")
        df_corrected.to_csv(temp_runs_path, index=False)

        # Write revision log
        revision_df = pd.DataFrame(self.revision_log)
        revision_path = os.path.join(self.output_dir, "step_2c2_comparator_profile_revision_log.csv")
        revision_df.to_csv(revision_path, index=False)
        self.log(f"Revision log: {len(revision_df)} entries -> {revision_path}")

        # Move corrected runs to final (overwrite)
        final_runs_path = os.path.join(self.data_dir, "analytical_scenario_runs.csv")
        shutil.copy2(final_runs_path, os.path.join(self.temp_dir, "analytical_scenario_runs_backup.csv"))
        shutil.move(temp_runs_path, final_runs_path)
        self.log(f"Corrected scenario runs moved to {final_runs_path}")

        return {
            "status": "success",
            "changes_made": changes_made,
            "identical_profiles_after": identical_after,
            "revision_log_entries": len(revision_df),
            "timestamp": self.run_timestamp,
        }


def main():
    runner = ComparatorCorrectionRunner()
    result = runner.run()
    print(json.dumps(result, indent=2, default=str))
    sys.exit(0 if result.get("status") == "success" else 1)


if __name__ == "__main__":
    main()
