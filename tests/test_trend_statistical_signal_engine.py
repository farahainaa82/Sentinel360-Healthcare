"""
Sentinel360 Healthcare — Trend and Statistical Signal Engine Tests

Focused tests for Phase 2B-1.
Do not run nested pytest inside tests.

Step: 2B-1
"""

import os
import sys
import json
import tempfile
import shutil
import pytest
from datetime import datetime, date, timedelta

import pandas as pd
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from trend_statistical_signal_engine import TrendStatisticalSignalEngine
from trend_analytical_models import (
    PeriodComparisonResult,
    RollingStatisticResult,
    StatisticalSignalResult,
    SustainedMovementResult,
)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def engine():
    return TrendStatisticalSignalEngine(project_root=PROJECT_ROOT)


@pytest.fixture
def sample_df():
    rows = []
    base_date = date(2026, 1, 1)
    for i in range(20):
        d = base_date + timedelta(days=i)
        rows.append({
            "integration_record_id": f"IKPI-kpi_001-HOSP-001-DEPT-ADM-{d.strftime('%Y%m%d')}",
            "analytical_record_id": f"AKPI-kpi_001-HOSP-001-DEPT-ADM-{d.strftime('%Y%m%d')}",
            "hospital_id": "HOSP-001",
            "department_id": "DEPT-ADM",
            "reporting_date": d,
            "reporting_month": d.month,
            "reporting_year": d.year,
            "kpi_id": "kpi_001",
            "kpi_name": "Staffing Level",
            "domain": "Workforce",
            "numerator_value": 20.0,
            "denominator_value": 25.0,
            "kpi_value": 80.0 + i * 0.5,
            "unit": "Percent",
            "calculation_status": "Calculated",
            "readiness_status": "Conditionally Ready",
            "threshold_status": "Not Assessed",
            "threshold_version": "v1.0-draft",
            "threshold_approval_status": "Draft",
            "threshold_is_provisional": True,
            "data_confidence_level": "High",
            "confidence_rule_version": "v1.0-draft",
            "confidence_is_provisional": True,
            "integration_status": "Integrated with Warning",
            "evidence_status": "Complete",
            "lineage_status": "Complete",
            "source_analytical_dataset": "analytical_workforce_kpi_daily.csv",
            "source_analytical_record_id": f"AKPI-kpi_001-HOSP-001-DEPT-ADM-{d.strftime('%Y%m%d')}",
            "source_calculation_run_id": "WF-KPI-TEST",
            "integration_run_id": "SIX-KPI-TEST",
            "integrated_at": datetime.now().isoformat(),
        })
    # Add some unavailable rows
    for i in range(20, 25):
        d = base_date + timedelta(days=i)
        rows.append({
            "integration_record_id": f"IKPI-kpi_003-HOSP-001-DEPT-ADM-{d.strftime('%Y%m%d')}",
            "analytical_record_id": f"AKPI-kpi_003-HOSP-001-DEPT-ADM-{d.strftime('%Y%m%d')}",
            "hospital_id": "HOSP-001",
            "department_id": "DEPT-ADM",
            "reporting_date": d,
            "reporting_month": d.month,
            "reporting_year": d.year,
            "kpi_id": "kpi_003",
            "kpi_name": "Bed Occupancy Rate",
            "domain": "Patient Flow",
            "numerator_value": None,
            "denominator_value": None,
            "kpi_value": None,
            "unit": "Percent",
            "calculation_status": "Insufficient Data",
            "readiness_status": "Conditionally Ready",
            "threshold_status": "Not Assessed",
            "threshold_version": "v1.0-draft",
            "threshold_approval_status": "Draft",
            "threshold_is_provisional": True,
            "data_confidence_level": "Unavailable",
            "confidence_rule_version": "v1.0-draft",
            "confidence_is_provisional": True,
            "integration_status": "Integrated with Warning",
            "evidence_status": "Unavailable",
            "lineage_status": "Complete",
            "source_analytical_dataset": "analytical_patient_flow_kpi_daily.csv",
            "source_analytical_record_id": f"AKPI-kpi_003-HOSP-001-DEPT-ADM-{d.strftime('%Y%m%d')}",
            "source_calculation_run_id": "PF-KPI-TEST",
            "integration_run_id": "SIX-KPI-TEST",
            "integrated_at": datetime.now().isoformat(),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Architecture
# ---------------------------------------------------------------------------

def test_safe_import():
    from trend_statistical_signal_engine import TrendStatisticalSignalEngine
    assert TrendStatisticalSignalEngine is not None


def test_no_automatic_execution():
    import run_trend_statistical_signal_processing
    assert hasattr(run_trend_statistical_signal_processing, "run_trend_processing")


def test_exactly_six_kpis_supported(engine):
    assert len(engine.SIX_KPIS) == 6
    assert set(engine.SIX_KPIS) == {"kpi_001", "kpi_002", "kpi_003", "kpi_004", "kpi_005", "kpi_006"}


def test_no_kpi_recalculation(engine, sample_df):
    # Engine should not modify kpi_value
    pre_vals = sample_df["kpi_value"].copy()
    engine.run_all(sample_df)
    pd.testing.assert_series_equal(pre_vals, sample_df["kpi_value"])


# ---------------------------------------------------------------------------
# Input handling
# ---------------------------------------------------------------------------

def test_calculated_observations_included(engine, sample_df):
    engine.run_all(sample_df)
    calc_comps = [c for c in engine.period_comparisons if c.calculation_status == "Calculated"]
    assert len(calc_comps) > 0


def test_unavailable_observations_preserved(engine, sample_df):
    engine.run_all(sample_df)
    unavail = [c for c in engine.period_comparisons if c.calculation_status == "Current Value Unavailable"]
    assert len(unavail) > 0


def test_records_sorted_by_date(engine, sample_df):
    engine.run_all(sample_df)
    for (h, d, k), group in engine._data_cache.items():
        continue
    # Verify via grain
    series = engine.prepare_time_series(sample_df)
    for key, sub in series.items():
        assert sub["reporting_date"].is_monotonic_increasing


# ---------------------------------------------------------------------------
# Period comparison
# ---------------------------------------------------------------------------

def test_previous_available_day(engine, sample_df):
    engine.build_period_comparisons(sample_df)
    comps = [c for c in engine.period_comparisons if c.comparison_type == "Previous Available Day"]
    assert len(comps) > 0
    calc = [c for c in comps if c.calculation_status == "Calculated"]
    assert len(calc) > 0
    c = calc[0]
    assert c.absolute_change is not None


def test_zero_comparison_value(engine):
    rows = []
    for i in range(5):
        d = date(2026, 1, 1) + timedelta(days=i)
        rows.append({
            "integration_record_id": f"IKPI-kpi_001-HOSP-001-DEPT-ADM-{d.strftime('%Y%m%d')}",
            "analytical_record_id": f"AKPI-kpi_001-HOSP-001-DEPT-ADM-{d.strftime('%Y%m%d')}",
            "hospital_id": "HOSP-001",
            "department_id": "DEPT-ADM",
            "reporting_date": d,
            "reporting_month": d.month,
            "reporting_year": d.year,
            "kpi_id": "kpi_001",
            "kpi_name": "Staffing Level",
            "domain": "Workforce",
            "numerator_value": 0.0,
            "denominator_value": 25.0,
            "kpi_value": 0.0 if i == 0 else 10.0,
            "unit": "Percent",
            "calculation_status": "Calculated",
            "data_confidence_level": "High",
            "source_analytical_dataset": "test.csv",
            "source_analytical_record_id": f"AKPI-{d.strftime('%Y%m%d')}",
            "source_calculation_run_id": "TEST",
            "integration_run_id": "TEST",
        })
    df = pd.DataFrame(rows)
    engine.build_period_comparisons(df)
    comps = [c for c in engine.period_comparisons if c.comparison_type == "Previous Available Day"]
    zero_comp = [c for c in comps if c.percentage_change_status == "Zero Comparison Value"]
    assert len(zero_comp) > 0
    for z in zero_comp:
        assert z.percentage_change is None


def test_no_zero_filling(engine, sample_df):
    engine.run_all(sample_df)
    # Unavailable values should remain null, not zero
    for c in engine.period_comparisons:
        if c.calculation_status == "Current Value Unavailable":
            assert c.current_value is None


# ---------------------------------------------------------------------------
# Rolling statistics
# ---------------------------------------------------------------------------

def test_rolling_mean(engine, sample_df):
    engine.calculate_rolling_statistics(sample_df)
    rolls = [r for r in engine.rolling_statistics if r.rolling_window == 7]
    assert len(rolls) > 0
    calc = [r for r in rolls if r.calculation_status == "Calculated"]
    assert len(calc) > 0
    assert calc[0].rolling_mean is not None


def test_rolling_std(engine, sample_df):
    engine.calculate_rolling_statistics(sample_df)
    rolls = [r for r in engine.rolling_statistics if r.rolling_window == 7]
    calc = [r for r in rolls if r.calculation_status == "Calculated"]
    assert len(calc) > 0
    assert calc[0].rolling_standard_deviation is not None


def test_unavailable_values_not_converted_to_zero(engine, sample_df):
    engine.calculate_rolling_statistics(sample_df)
    # Rolling stats should only use calculated values
    for r in engine.rolling_statistics:
        if r.calculation_status == "Calculated":
            assert r.rolling_valid_observation_count > 0


# ---------------------------------------------------------------------------
# Trend direction
# ---------------------------------------------------------------------------

def test_mathematical_direction_separate_from_business(engine, sample_df):
    engine.build_period_comparisons(sample_df)
    calc = [c for c in engine.period_comparisons if c.calculation_status == "Calculated"]
    assert len(calc) > 0
    c = calc[0]
    assert c.mathematical_trend_direction in ["Increasing", "Decreasing", "Stable"]
    assert c.business_movement_interpretation in ["Improvement", "Deterioration", "Stable", "Context Review", "Insufficient History", "Unavailable", "Provisional"]


def test_higher_is_better_improvement(engine):
    rows = []
    for i in range(5):
        d = date(2026, 1, 1) + timedelta(days=i)
        rows.append({
            "integration_record_id": f"IKPI-kpi_001-HOSP-001-DEPT-ADM-{d.strftime('%Y%m%d')}",
            "analytical_record_id": f"AKPI-kpi_001-HOSP-001-DEPT-ADM-{d.strftime('%Y%m%d')}",
            "hospital_id": "HOSP-001",
            "department_id": "DEPT-ADM",
            "reporting_date": d,
            "reporting_month": d.month,
            "reporting_year": d.year,
            "kpi_id": "kpi_001",
            "kpi_name": "Staffing Level",
            "domain": "Workforce",
            "numerator_value": 20.0,
            "denominator_value": 25.0,
            "kpi_value": 80.0 + i * 2.0,
            "unit": "Percent",
            "calculation_status": "Calculated",
            "data_confidence_level": "High",
            "source_analytical_dataset": "test.csv",
            "source_analytical_record_id": f"AKPI-{d.strftime('%Y%m%d')}",
            "source_calculation_run_id": "TEST",
            "integration_run_id": "TEST",
        })
    df = pd.DataFrame(rows)
    engine.build_period_comparisons(df)
    comps = [c for c in engine.period_comparisons if c.comparison_type == "Previous Available Day" and c.calculation_status == "Calculated"]
    assert len(comps) > 0
    c = comps[0]
    assert c.mathematical_trend_direction == "Increasing"
    assert c.business_movement_interpretation == "Improvement"


def test_lower_is_better_deterioration(engine):
    rows = []
    for i in range(5):
        d = date(2026, 1, 1) + timedelta(days=i)
        rows.append({
            "integration_record_id": f"IKPI-kpi_002-HOSP-001-DEPT-ADM-{d.strftime('%Y%m%d')}",
            "analytical_record_id": f"AKPI-kpi_002-HOSP-001-DEPT-ADM-{d.strftime('%Y%m%d')}",
            "hospital_id": "HOSP-001",
            "department_id": "DEPT-ADM",
            "reporting_date": d,
            "reporting_month": d.month,
            "reporting_year": d.year,
            "kpi_id": "kpi_002",
            "kpi_name": "Staff Absenteeism Rate",
            "domain": "Workforce",
            "numerator_value": 2.0,
            "denominator_value": 25.0,
            "kpi_value": 8.0 + i * 1.0,
            "unit": "Percent",
            "calculation_status": "Calculated",
            "data_confidence_level": "High",
            "source_analytical_dataset": "test.csv",
            "source_analytical_record_id": f"AKPI-{d.strftime('%Y%m%d')}",
            "source_calculation_run_id": "TEST",
            "integration_run_id": "TEST",
        })
    df = pd.DataFrame(rows)
    engine.build_period_comparisons(df)
    comps = [c for c in engine.period_comparisons if c.comparison_type == "Previous Available Day" and c.calculation_status == "Calculated"]
    assert len(comps) > 0
    c = comps[0]
    assert c.mathematical_trend_direction == "Increasing"
    assert c.business_movement_interpretation == "Deterioration"


def test_occupancy_context_review(engine):
    rows = []
    for i in range(5):
        d = date(2026, 1, 1) + timedelta(days=i)
        rows.append({
            "integration_record_id": f"IKPI-kpi_003-HOSP-001-DEPT-ADM-{d.strftime('%Y%m%d')}",
            "analytical_record_id": f"AKPI-kpi_003-HOSP-001-DEPT-ADM-{d.strftime('%Y%m%d')}",
            "hospital_id": "HOSP-001",
            "department_id": "DEPT-ADM",
            "reporting_date": d,
            "reporting_month": d.month,
            "reporting_year": d.year,
            "kpi_id": "kpi_003",
            "kpi_name": "Bed Occupancy Rate",
            "domain": "Patient Flow",
            "numerator_value": 80.0,
            "denominator_value": 100.0,
            "kpi_value": 80.0 + i * 1.0,
            "unit": "Percent",
            "calculation_status": "Calculated",
            "data_confidence_level": "High",
            "source_analytical_dataset": "test.csv",
            "source_analytical_record_id": f"AKPI-{d.strftime('%Y%m%d')}",
            "source_calculation_run_id": "TEST",
            "integration_run_id": "TEST",
        })
    df = pd.DataFrame(rows)
    engine.build_period_comparisons(df)
    comps = [c for c in engine.period_comparisons if c.comparison_type == "Previous Available Day" and c.calculation_status == "Calculated"]
    assert len(comps) > 0
    c = comps[0]
    assert c.business_movement_interpretation == "Context Review"


# ---------------------------------------------------------------------------
# Sustained movement
# ---------------------------------------------------------------------------

def test_sustained_increase(engine):
    rows = []
    for i in range(5):
        d = date(2026, 1, 1) + timedelta(days=i)
        rows.append({
            "integration_record_id": f"IKPI-kpi_001-HOSP-001-DEPT-ADM-{d.strftime('%Y%m%d')}",
            "analytical_record_id": f"AKPI-kpi_001-HOSP-001-DEPT-ADM-{d.strftime('%Y%m%d')}",
            "hospital_id": "HOSP-001",
            "department_id": "DEPT-ADM",
            "reporting_date": d,
            "reporting_month": d.month,
            "reporting_year": d.year,
            "kpi_id": "kpi_001",
            "kpi_name": "Staffing Level",
            "domain": "Workforce",
            "numerator_value": 20.0,
            "denominator_value": 25.0,
            "kpi_value": 80.0 + i * 5.0,
            "unit": "Percent",
            "calculation_status": "Calculated",
            "data_confidence_level": "High",
            "source_analytical_dataset": "test.csv",
            "source_analytical_record_id": f"AKPI-{d.strftime('%Y%m%d')}",
            "source_calculation_run_id": "TEST",
            "integration_run_id": "TEST",
        })
    df = pd.DataFrame(rows)
    engine.detect_sustained_movements(df)
    inc = [m for m in engine.sustained_movements if m.movement_type == "Sustained Increase"]
    assert len(inc) > 0


def test_insufficient_history_no_movement(engine):
    rows = []
    for i in range(2):
        d = date(2026, 1, 1) + timedelta(days=i)
        rows.append({
            "integration_record_id": f"IKPI-kpi_001-HOSP-001-DEPT-ADM-{d.strftime('%Y%m%d')}",
            "analytical_record_id": f"AKPI-kpi_001-HOSP-001-DEPT-ADM-{d.strftime('%Y%m%d')}",
            "hospital_id": "HOSP-001",
            "department_id": "DEPT-ADM",
            "reporting_date": d,
            "reporting_month": d.month,
            "reporting_year": d.year,
            "kpi_id": "kpi_001",
            "kpi_name": "Staffing Level",
            "domain": "Workforce",
            "numerator_value": 20.0,
            "denominator_value": 25.0,
            "kpi_value": 80.0 + i * 5.0,
            "unit": "Percent",
            "calculation_status": "Calculated",
            "data_confidence_level": "High",
            "source_analytical_dataset": "test.csv",
            "source_analytical_record_id": f"AKPI-{d.strftime('%Y%m%d')}",
            "source_calculation_run_id": "TEST",
            "integration_run_id": "TEST",
        })
    df = pd.DataFrame(rows)
    engine.detect_sustained_movements(df)
    assert len(engine.sustained_movements) == 0


# ---------------------------------------------------------------------------
# Statistical signals
# ---------------------------------------------------------------------------

def test_zscore_valid(engine, sample_df):
    engine.generate_signal_candidates(sample_df)
    z = [s for s in engine.signals if s.signal_method == "z_score"]
    assert len(z) > 0


def test_zero_historical_variance(engine):
    rows = []
    for i in range(15):
        d = date(2026, 1, 1) + timedelta(days=i)
        rows.append({
            "integration_record_id": f"IKPI-kpi_001-HOSP-001-DEPT-ADM-{d.strftime('%Y%m%d')}",
            "analytical_record_id": f"AKPI-kpi_001-HOSP-001-DEPT-ADM-{d.strftime('%Y%m%d')}",
            "hospital_id": "HOSP-001",
            "department_id": "DEPT-ADM",
            "reporting_date": d,
            "reporting_month": d.month,
            "reporting_year": d.year,
            "kpi_id": "kpi_001",
            "kpi_name": "Staffing Level",
            "domain": "Workforce",
            "numerator_value": 20.0,
            "denominator_value": 25.0,
            "kpi_value": 80.0,
            "unit": "Percent",
            "calculation_status": "Calculated",
            "data_confidence_level": "High",
            "source_analytical_dataset": "test.csv",
            "source_analytical_record_id": f"AKPI-{d.strftime('%Y%m%d')}",
            "source_calculation_run_id": "TEST",
            "integration_run_id": "TEST",
        })
    df = pd.DataFrame(rows)
    engine.generate_signal_candidates(df)
    zero_var = [s for s in engine.signals if s.signal_method == "z_score" and s.signal_type == "Zero Historical Variance"]
    assert len(zero_var) > 0


def test_mad_signal(engine, sample_df):
    engine.generate_signal_candidates(sample_df)
    mad = [s for s in engine.signals if s.signal_method == "mad_signal"]
    assert len(mad) > 0


def test_slope_valid(engine, sample_df):
    engine.generate_signal_candidates(sample_df)
    slope = [s for s in engine.signals if s.signal_method == "trend_slope"]
    assert len(slope) > 0
    calc = [s for s in slope if s.signal_status == "Calculated"]
    assert len(calc) > 0


def test_volatility_signal(engine, sample_df):
    engine.generate_signal_candidates(sample_df)
    vol = [s for s in engine.signals if s.signal_method == "volatility_change"]
    assert len(vol) > 0


# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------

def test_high_confidence(engine, sample_df):
    engine.build_period_comparisons(sample_df)
    high = [c for c in engine.period_comparisons if c.trend_confidence_level == "High"]
    assert len(high) > 0


def test_unavailable_confidence_for_unavailable(engine, sample_df):
    engine.build_period_comparisons(sample_df)
    unavail = [c for c in engine.period_comparisons if c.calculation_status == "Current Value Unavailable"]
    assert len(unavail) > 0
    assert unavail[0].trend_confidence_level == "Unavailable"


# ---------------------------------------------------------------------------
# Evidence and lineage
# ---------------------------------------------------------------------------

def test_calculated_result_has_evidence(engine, sample_df):
    engine.run_all(sample_df)
    assert len(engine.evidence) > 0


def test_lineage_present(engine, sample_df):
    engine.run_all(sample_df)
    assert len(engine.lineage) > 0


# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------

def test_unique_ids(engine, sample_df):
    engine.run_all(sample_df)
    ids = [c.comparison_record_id for c in engine.period_comparisons]
    assert len(ids) == len(set(ids))


def test_no_green_amber_red(engine, sample_df):
    engine.run_all(sample_df)
    for c in engine.period_comparisons:
        assert c.business_movement_interpretation not in ["Green", "Amber", "Red"]
    for s in engine.signals:
        assert s.signal_type not in ["Green", "Amber", "Red"]


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------

def test_phase_2a_unchanged(engine, sample_df):
    import hashlib
    path = os.path.join(PROJECT_ROOT, "data/analytical/analytical_six_kpi_daily.csv")
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    pre = h.hexdigest()
    engine.run_all(sample_df)
    h2 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h2.update(chunk)
    post = h2.hexdigest()
    assert pre == post
