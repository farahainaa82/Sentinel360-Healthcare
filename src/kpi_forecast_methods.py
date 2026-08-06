"""Simple, explainable forecasting methods for Sentinel360 KPIs.

Methods: Naive, 3-Month Moving Average, Linear Trend, Simple Exponential
Smoothing, and Holt Linear Trend.
"""

from typing import List
import numpy as np
from statsmodels.tsa.holtwinters import SimpleExpSmoothing, Holt


def _ensure_float(value):
    if np.isscalar(value) and not isinstance(value, (np.ndarray, list)):
        return float(value)
    return value


def naive_last_value(series: np.ndarray, steps: int = 1) -> List[float]:
    """Forecast = latest valid monthly value."""
    if len(series) == 0:
        return [np.nan] * steps
    val = float(series[-1])
    return [val] * steps


def three_month_moving_average(series: np.ndarray, steps: int = 1) -> List[float]:
    """Forecast = mean of latest three valid monthly observations."""
    if len(series) < 3:
        return [np.nan] * steps
    val = float(np.mean(series[-3:]))
    return [val] * steps


def linear_trend(series: np.ndarray, steps: int = 1) -> List[float]:
    """Simple OLS linear trend extrapolation."""
    n = len(series)
    if n < 2:
        return [np.nan] * steps
    x = np.arange(n, dtype=float)
    y = np.array(series, dtype=float)
    x_mean = np.mean(x)
    y_mean = np.mean(y)
    denom = np.sum((x - x_mean) ** 2)
    if denom == 0:
        return [np.nan] * steps
    slope = np.sum((x - x_mean) * (y - y_mean)) / denom
    intercept = y_mean - slope * x_mean
    forecasts = []
    for s in range(1, steps + 1):
        forecasts.append(float(intercept + slope * (n - 1 + s)))
    return forecasts


def simple_exponential_smoothing(series: np.ndarray, steps: int = 1) -> List[float]:
    """Statsmodels SimpleExpSmoothing."""
    if len(series) < 2:
        return [np.nan] * steps
    try:
        model = SimpleExpSmoothing(series, initialization_method="estimated")
        fit = model.fit(optimized=True)
        fc = fit.forecast(steps)
        return [float(v) for v in fc]
    except Exception:
        return [np.nan] * steps


def holt_linear_trend(series: np.ndarray, steps: int = 1) -> List[float]:
    """Statsmodels Holt linear trend."""
    if len(series) < 3:
        return [np.nan] * steps
    try:
        model = Holt(series, initialization_method="estimated")
        fit = model.fit(optimized=True)
        fc = fit.forecast(steps)
        return [float(v) for v in fc]
    except Exception:
        return [np.nan] * steps


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
