"""Time-aware validation for candidate forecast methods.

Rolling-origin one-step-ahead validation with MAE, RMSE, MAPE and
directional accuracy.
"""

from typing import Dict, List
import numpy as np
from src.kpi_forecast_methods import (
    naive_last_value,
    three_month_moving_average,
    linear_trend,
    simple_exponential_smoothing,
    holt_linear_trend,
)

METHOD_MAP = {
    "Naive Last Value": naive_last_value,
    "Three-Month Moving Average": three_month_moving_average,
    "Linear Trend": linear_trend,
    "Simple Exponential Smoothing": simple_exponential_smoothing,
    "Holt Linear Trend": holt_linear_trend,
}

MIN_TRAIN_MONTHS = {
    "Naive Last Value": 1,
    "Three-Month Moving Average": 3,
    "Linear Trend": 4,
    "Simple Exponential Smoothing": 4,
    "Holt Linear Trend": 6,
}


def validate_method(series: np.ndarray, method_name: str) -> Dict:
    """Rolling-origin one-step-ahead validation for a single method.

    Parameters
    ----------
    series : np.ndarray
        Chronological monthly actual values.
    method_name : str
        Key from METHOD_MAP.

    Returns
    -------
    dict
        Validation metrics and eligibility flags.
    """
    method = METHOD_MAP[method_name]
    min_train = MIN_TRAIN_MONTHS[method_name]
    n = len(series)

    if n < min_train + 1:
        return {
            "validation_points": 0,
            "mae": np.nan,
            "rmse": np.nan,
            "mape": np.nan,
            "directional_accuracy": np.nan,
            "fit_status": "Insufficient history",
            "stability_status": "Not tested",
            "method_eligible": False,
            "warning": f"Need at least {min_train + 1} months for validation, got {n}",
        }

    predictions: List[float] = []
    actuals: List[float] = []
    directions: List[int] = []

    for train_end in range(min_train, n):
        train = series[:train_end]
        actual = float(series[train_end])
        preds = method(train, steps=1)
        pred = preds[0]
        if np.isnan(pred):
            continue
        predictions.append(pred)
        actuals.append(actual)
        if len(train) >= 1:
            last_train = float(train[-1])
            actual_dir = np.sign(actual - last_train)
            pred_dir = np.sign(pred - last_train)
            directions.append(1 if actual_dir == pred_dir else 0)

    validation_points = len(predictions)
    if validation_points == 0:
        return {
            "validation_points": 0,
            "mae": np.nan,
            "rmse": np.nan,
            "mape": np.nan,
            "directional_accuracy": np.nan,
            "fit_status": "Failed to produce predictions",
            "stability_status": "Unstable",
            "method_eligible": False,
            "warning": "No valid predictions during validation",
        }

    preds_arr = np.array(predictions, dtype=float)
    acts_arr = np.array(actuals, dtype=float)

    mae = float(np.mean(np.abs(preds_arr - acts_arr)))
    rmse = float(np.sqrt(np.mean((preds_arr - acts_arr) ** 2)))

    non_zero_mask = acts_arr != 0
    if np.any(non_zero_mask):
        mape = float(np.mean(np.abs((acts_arr[non_zero_mask] - preds_arr[non_zero_mask]) / acts_arr[non_zero_mask])))
    else:
        mape = np.nan

    directional_accuracy = float(np.mean(directions)) if directions else np.nan

    implausible = bool(np.any(np.isinf(preds_arr)) or np.any(np.isnan(preds_arr)))
    warning = "Implausible predictions encountered" if implausible else ""
    stability = "Unstable" if implausible else "Stable"

    return {
        "validation_points": validation_points,
        "mae": mae,
        "rmse": rmse,
        "mape": mape,
        "directional_accuracy": directional_accuracy,
        "fit_status": "Fitted" if stability == "Stable" else "Failed",
        "stability_status": stability,
        "method_eligible": stability == "Stable",
        "warning": warning,
    }
