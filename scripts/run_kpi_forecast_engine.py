"""Runner script for the Sentinel360 Indicative KPI Forecasting Engine.

Orchestrates data preparation, eligibility, validation, method selection,
forecast generation, threshold evaluation, warning signals, manifest, and
frozen-file integrity checks.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, List

import pandas as pd

from src.kpi_forecast_data_preparation import prepare_monthly_history
from src.kpi_forecast_engine import (
    assess_eligibility,
    select_methods,
    generate_forecasts,
    evaluate_threshold_status,
    _load_monthly_history,
    _load_threshold_config,
    OUTPUT_DIR,
)
from src.kpi_forecast_warning_engine import generate_warning_signals, _load_interventions

FROZEN_PATHS = ["data/analytical", "outputs"]


def _hash_file(path: str) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def _collect_hashes(paths: List[str]) -> Dict[str, str]:
    result = {}
    for base in paths:
        if not os.path.exists(base):
            continue
        for root, _dirs, files in os.walk(base):
            for fname in files:
                fpath = os.path.join(root, fname)
                # Exclude newly generated forecasting outputs from frozen check
                if "forecasting" in fpath:
                    continue
                result[fpath] = _hash_file(fpath)
    return result


def _write_integrity(before: Dict[str, str], after: Dict[str, str], path: str):
    records = []
    all_keys = sorted(set(before.keys()) | set(after.keys()))
    for k in all_keys:
        h_before = before.get(k, "")
        h_after = after.get(k, "")
        records.append({
            "file_path": k,
            "hash_before": h_before,
            "hash_after": h_after,
            "unchanged": h_before == h_after and h_before != "",
            "validation_note": "New file" if k not in before else ("Unchanged" if h_before == h_after else "MODIFIED"),
        })
    df = pd.DataFrame(records)
    df.to_csv(path, index=False)
    return df


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Step 1 — Frozen-file integrity before
    logging.info("Computing frozen-file integrity hashes (before)...")
    hashes_before = _collect_hashes(FROZEN_PATHS)

    # Step 2 — Data preparation
    logging.info("Preparing monthly historical data...")
    monthly = prepare_monthly_history()

    # Step 3 — Eligibility assessment
    logging.info("Assessing eligibility...")
    eligibility = assess_eligibility(monthly)
    eligibility_path = os.path.join(OUTPUT_DIR, "kpi_forecast_eligibility_audit.csv")
    eligibility.to_csv(eligibility_path, index=False)
    logging.info("Eligibility written to %s", eligibility_path)

    # Step 4 — Method selection (validation built-in)
    logging.info("Validating candidate methods and selecting best...")
    selection = select_methods(monthly, eligibility)
    selection_path = os.path.join(OUTPUT_DIR, "kpi_forecast_method_selection.csv")
    selection.to_csv(selection_path, index=False)
    logging.info("Method selection written to %s", selection_path)

    # Validation details (explode per method for audit)
    validation_records = []
    for _, sel in selection.iterrows():
        hospital = sel["hospital"]
        dept_code = sel["department_code"]
        kpi_id = sel["kpi_id"]
        g = monthly[
            (monthly["hospital"] == hospital)
            & (monthly["department_code"] == dept_code)
            & (monthly["kpi_id"] == kpi_id)
        ].sort_values(["year", "month"]).reset_index(drop=True)
        if len(g) == 0:
            continue
        series = g["monthly_actual_value"].values
        from src.kpi_forecast_validation import validate_method, MIN_TRAIN_MONTHS
        for method_name, min_train in MIN_TRAIN_MONTHS.items():
            if len(series) < min_train + 1:
                continue
            v = validate_method(series, method_name)
            validation_records.append({
                "hospital": hospital,
                "department": sel["department"],
                "department_code": dept_code,
                "kpi_id": kpi_id,
                "kpi_name": sel["kpi_name"],
                "candidate_method": method_name,
                "validation_points": v["validation_points"],
                "mae": v["mae"],
                "rmse": v["rmse"],
                "mape": v["mape"],
                "directional_accuracy": v["directional_accuracy"],
                "fit_status": v["fit_status"],
                "stability_status": v["stability_status"],
                "method_eligible": v["method_eligible"],
                "warning": v["warning"],
            })
    if validation_records:
        pd.DataFrame(validation_records).to_csv(
            os.path.join(OUTPUT_DIR, "kpi_forecast_method_validation.csv"), index=False
        )

    # Step 5 — Generate forecasts
    logging.info("Generating August–December 2025 forecasts...")
    forecasts = generate_forecasts(monthly, selection)
    forecasts_path = os.path.join(OUTPUT_DIR, "analytical_kpi_monthly_forecast.csv")
    forecasts.to_csv(forecasts_path, index=False)
    logging.info("Forecasts written to %s", forecasts_path)

    # Step 6 — Threshold evaluation
    logging.info("Evaluating forecast threshold status...")
    threshold_cfg = _load_threshold_config()
    forecasts_status = evaluate_threshold_status(forecasts, threshold_cfg)
    status_path = os.path.join(OUTPUT_DIR, "analytical_kpi_forecast_status.csv")
    forecasts_status.to_csv(status_path, index=False)
    logging.info("Forecast status written to %s", status_path)

    # Step 7 — Warning signals
    logging.info("Generating early-warning signals...")
    interventions = _load_interventions()
    warnings = generate_warning_signals(forecasts_status, monthly, interventions, threshold_cfg=threshold_cfg)
    warnings_path = os.path.join(OUTPUT_DIR, "analytical_kpi_forecast_warning_signals.csv")
    warnings.to_csv(warnings_path, index=False)
    logging.info("Warning signals written to %s", warnings_path)

    # Step 8 — Frozen-file integrity after
    logging.info("Computing frozen-file integrity hashes (after)...")
    hashes_after = _collect_hashes(FROZEN_PATHS)
    integrity_path = os.path.join(OUTPUT_DIR, "forecast_frozen_file_integrity_check.csv")
    integrity_df = _write_integrity(hashes_before, hashes_after, integrity_path)
    any_changed = (integrity_df["validation_note"] == "MODIFIED").any()
    if any_changed:
        logging.warning("Frozen-file integrity check detected modifications!")
    else:
        logging.info("Frozen-file integrity confirmed: no modifications.")

    # Step 9 — Manifest
    manifest = {
        "engine_name": "Sentinel360 Indicative KPI Forecasting Engine",
        "engine_version": "1.0.0-indicative",
        "generation_timestamp": datetime.now().isoformat(),
        "input_files": ["data/analytical/analytical_six_kpi_daily.csv", "config/kpi_threshold_config.csv", "config/intervention_catalogue.csv"],
        "output_files": {
            "monthly_history": str(os.path.join(OUTPUT_DIR, "kpi_monthly_actual_history.csv")),
            "eligibility_audit": str(eligibility_path),
            "method_selection": str(selection_path),
            "method_validation": str(os.path.join(OUTPUT_DIR, "kpi_forecast_method_validation.csv")),
            "forecasts": str(forecasts_path),
            "forecast_status": str(status_path),
            "warning_signals": str(warnings_path),
            "integrity_check": str(integrity_path),
        },
        "historical_cutoff": "2025-07-31",
        "forecast_horizon": ["2025-08", "2025-09", "2025-10", "2025-11", "2025-12"],
        "candidate_methods": ["Naive Last Value", "Three-Month Moving Average", "Linear Trend", "Simple Exponential Smoothing", "Holt Linear Trend"],
        "validation_approach": "Rolling-origin one-step-ahead validation",
        "KPI_coverage": list(eligibility["kpi_name"].unique()),
        "department_coverage": list(eligibility["department"].unique()),
        "eligible_combinations": int(eligibility["eligibility_status"].isin(["ELIGIBLE", "ELIGIBLE WITH LIMITATIONS"]).sum()),
        "ineligible_combinations": int((~eligibility["eligibility_status"].isin(["ELIGIBLE", "ELIGIBLE WITH LIMITATIONS"])).sum()),
        "selected_method_counts": selection["selected_method"].value_counts().to_dict() if not selection.empty else {},
        "warning_signal_counts": warnings["warning_level"].value_counts().to_dict() if not warnings.empty else {},
        "known_limitations": [
            "Seven months of history are insufficient for reliable seasonal modelling.",
            "Forecasts are indicative operational estimates only.",
            "No causal inference is performed.",
        ],
        "disclaimer": "These forecasts are indicative operational estimates generated from available synthetic historical data. They support early-warning demonstration and require further validation before operational deployment.",
        "approval_status": "Indicative Prototype",
        "frozen_file_integrity": "No modifications detected" if not any_changed else "MODIFICATIONS DETECTED",
    }

    manifest_path = os.path.join(OUTPUT_DIR, "forecast_engine_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, default=str)
    logging.info("Manifest written to %s", manifest_path)

    logging.info("Forecast engine run complete.")
    return 0 if not any_changed else 1


if __name__ == "__main__":
    sys.exit(main())
