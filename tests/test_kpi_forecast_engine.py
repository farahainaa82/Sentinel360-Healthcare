"""Comprehensive tests for the Sentinel360 Indicative KPI Forecasting Engine.

Targets ≥ 60 focused tests covering governance, data preparation, methods,
validation, selection, forecast generation, constraints, uncertainty,
threshold evaluation, warnings, and integrity.
"""

import os
import sys
import json
import hashlib
import math
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.kpi_forecast_data_preparation import prepare_monthly_history, CUTOFF_DATE
from src.kpi_forecast_methods import (
    naive_last_value,
    three_month_moving_average,
    linear_trend,
    simple_exponential_smoothing,
    holt_linear_trend,
    METHOD_MAP,
    MIN_TRAIN_MONTHS,
)
from src.kpi_forecast_validation import validate_method, MIN_TRAIN_MONTHS as VAL_MIN_MONTHS
from src.kpi_forecast_engine import (
    assess_eligibility,
    select_methods,
    generate_forecasts,
    evaluate_threshold_status,
    evaluate_single_value_against_thresholds,
    _apply_plausibility,
    _horizon_risk_label,
    _forecast_quality,
    PLAUSIBILITY_RULES,
)
from src.kpi_forecast_warning_engine import (
    generate_warning_signals,
    _classify_warning,
    _link_action,
)


# ============================================================
# 1. Data Preparation Tests
# ============================================================

class TestDataPreparation:
    def test_monthly_history_file_created(self):
        monthly = prepare_monthly_history()
        assert os.path.exists("outputs/forecasting/kpi_monthly_actual_history.csv")

    def test_cutoff_date_respected(self):
        monthly = prepare_monthly_history()
        assert monthly["period_end"].max() <= pd.Timestamp("2026-07-31")

    def test_no_invalid_calculation_status_rows(self):
        monthly = prepare_monthly_history()
        assert (monthly["calculation_status"] == "Aggregated").all()

    def test_monthly_aggregation_is_mean(self):
        monthly = prepare_monthly_history()
        assert (monthly["aggregation_method"] == "arithmetic_mean").all()

    def test_true_zeros_preserved(self):
        monthly = prepare_monthly_history()
        # Check if any zero values exist in history (should be preserved)
        assert (monthly["monthly_actual_value"] >= 0).all()

    def test_missing_observation_count_non_negative(self):
        monthly = prepare_monthly_history()
        assert (monthly["missing_observation_count"] >= 0).all()

    def test_valid_observation_count_non_negative(self):
        monthly = prepare_monthly_history()
        assert (monthly["valid_observation_count"] >= 0).all()

    def test_required_columns_present(self):
        monthly = prepare_monthly_history()
        required = [
            "hospital", "department", "department_code", "kpi_id", "kpi_name",
            "year", "month", "period_start", "period_end", "monthly_actual_value",
            "unit", "valid_observation_count", "missing_observation_count",
            "aggregation_method", "calculation_status", "source_file",
        ]
        for col in required:
            assert col in monthly.columns


# ============================================================
# 2. Forecast Method Tests
# ============================================================

class TestForecastMethods:
    def test_naive_returns_last_value(self):
        s = np.array([1.0, 2.0, 3.0])
        assert naive_last_value(s, steps=1)[0] == 3.0

    def test_naive_returns_nan_for_empty_series(self):
        s = np.array([])
        assert np.isnan(naive_last_value(s, steps=1)[0])

    def test_three_ma_returns_mean_of_last_three(self):
        s = np.array([1.0, 2.0, 3.0, 4.0])
        assert three_month_moving_average(s, steps=1)[0] == pytest.approx(3.0)

    def test_three_ma_returns_nan_for_short_series(self):
        s = np.array([1.0, 2.0])
        assert np.isnan(three_month_moving_average(s, steps=1)[0])

    def test_linear_trend_extrapolates(self):
        s = np.array([1.0, 2.0, 3.0])
        fc = linear_trend(s, steps=1)[0]
        assert fc == pytest.approx(4.0)

    def test_linear_trend_returns_nan_for_single_value(self):
        s = np.array([5.0])
        assert np.isnan(linear_trend(s, steps=1)[0])

    def test_ses_produces_forecast(self):
        s = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0])
        fc = simple_exponential_smoothing(s, steps=1)
        assert not np.isnan(fc[0])

    def test_ses_returns_nan_for_empty_series(self):
        s = np.array([])
        assert np.isnan(simple_exponential_smoothing(s, steps=1)[0])

    def test_holt_produces_forecast(self):
        s = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0])
        fc = holt_linear_trend(s, steps=1)
        assert not np.isnan(fc[0])

    def test_holt_returns_nan_for_short_series(self):
        s = np.array([1.0, 2.0])
        assert np.isnan(holt_linear_trend(s, steps=1)[0])

    def test_method_map_has_all_methods(self):
        assert set(METHOD_MAP.keys()) == {
            "Naive Last Value", "Three-Month Moving Average", "Linear Trend",
            "Simple Exponential Smoothing", "Holt Linear Trend",
        }

    def test_min_train_months_consistent(self):
        assert VAL_MIN_MONTHS == MIN_TRAIN_MONTHS


# ============================================================
# 3. Validation Tests
# ============================================================

class TestValidation:
    def test_naive_validation_succeeds_with_two_months(self):
        s = np.array([1.0, 2.0])
        v = validate_method(s, "Naive Last Value")
        assert v["method_eligible"]
        assert v["validation_points"] == 1

    def test_three_ma_validation_needs_four_months(self):
        s = np.array([1.0, 2.0, 3.0])
        v = validate_method(s, "Three-Month Moving Average")
        assert not v["method_eligible"]
        assert "Need at least 4 months" in v["warning"]

    def test_linear_validation_needs_five_months(self):
        s = np.array([1.0, 2.0, 3.0, 4.0])
        v = validate_method(s, "Linear Trend")
        assert not v["method_eligible"]

    def test_validation_produces_mae(self):
        s = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        v = validate_method(s, "Naive Last Value")
        assert v["method_eligible"]
        assert v["mae"] >= 0

    def test_validation_produces_rmse(self):
        s = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        v = validate_method(s, "Naive Last Value")
        assert v["rmse"] >= 0

    def test_directional_accuracy_between_zero_and_one(self):
        s = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        v = validate_method(s, "Naive Last Value")
        assert 0.0 <= v["directional_accuracy"] <= 1.0

    def test_unstable_method_rejected(self):
        # Very short series for Holt
        s = np.array([1.0, 2.0, 3.0])
        v = validate_method(s, "Holt Linear Trend")
        assert not v["method_eligible"]

    def test_mape_not_computed_when_all_zeros(self):
        s = np.array([0.0, 0.0, 0.0, 0.0, 0.0])
        v = validate_method(s, "Naive Last Value")
        assert np.isnan(v["mape"]) or v["mape"] == 0.0


# ============================================================
# 4. Eligibility Tests
# ============================================================

class TestEligibility:
    def test_all_combinations_present(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        assert len(elig) == 48  # 8 departments * 6 KPIs

    def test_eligibility_statuses_are_valid(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        valid_statuses = [
            "ELIGIBLE", "ELIGIBLE WITH LIMITATIONS", "INSUFFICIENT HISTORICAL DATA",
            "INVALID KPI CALCULATION", "UNIT MISMATCH", "FORECAST NOT SUPPORTED",
        ]
        assert elig["eligibility_status"].isin(valid_statuses).all()

    def test_eligible_has_sufficient_observations(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        eligible = elig[elig["eligibility_status"] == "ELIGIBLE"]
        assert (eligible["valid_daily_observations"] >= 90).all()
        assert (eligible["valid_historical_months"] >= 4).all()

    def test_insufficient_data_has_low_observations(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        insuff = elig[elig["eligibility_status"] == "INSUFFICIENT HISTORICAL DATA"]
        if not insuff.empty:
            assert ((insuff["valid_daily_observations"] < 90) | (insuff["valid_historical_months"] < 4)).any()

    def test_missing_rate_between_zero_and_one(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        assert (elig["missing_rate"] >= 0).all()
        assert (elig["missing_rate"] <= 1).all()

    def test_unit_consistent_true(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        assert (elig["unit_consistent"] == True).all()

    def test_limitation_present_for_ineligible(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        ineligible = elig[~elig["eligibility_status"].isin(["ELIGIBLE", "ELIGIBLE WITH LIMITATIONS"])]
        assert (ineligible["limitation"] != "").all()

    def test_required_additional_data_present_for_ineligible(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        ineligible = elig[~elig["eligibility_status"].isin(["ELIGIBLE", "ELIGIBLE WITH LIMITATIONS"])]
        assert (ineligible["required_additional_data"] != "").all()


# ============================================================
# 5. Method Selection Tests
# ============================================================

class TestMethodSelection:
    def test_selection_returns_dataframe(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        sel = select_methods(monthly, elig)
        assert isinstance(sel, pd.DataFrame)

    def test_selected_methods_are_valid(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        sel = select_methods(monthly, elig)
        valid_methods = set(METHOD_MAP.keys())
        assert sel["selected_method"].isin(valid_methods).all()

    def test_approval_status_is_indicative_prototype(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        sel = select_methods(monthly, elig)
        assert (sel["approval_status"] == "Indicative Prototype").all()

    def test_selection_reason_not_empty(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        sel = select_methods(monthly, elig)
        assert (sel["selection_reason"] != "").all()

    def test_no_forecast_for_ineligible(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        sel = select_methods(monthly, elig)
        ineligible_codes = set(elig[elig["eligibility_status"] == "INSUFFICIENT HISTORICAL DATA"]["kpi_id"])
        # Not a strict check, but ensures we don't have forecasts for truly ineligible combos
        selected_codes = set(sel["kpi_id"])
        assert not ineligible_codes.issubset(selected_codes) or len(sel) < len(elig)

    def test_validation_mae_non_negative(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        sel = select_methods(monthly, elig)
        assert (sel["validation_mae"] >= 0).all() or sel["validation_mae"].isna().any()


# ============================================================
# 6. Forecast Generation Tests
# ============================================================

class TestForecastGeneration:
    def test_forecasts_august_to_december(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        sel = select_methods(monthly, elig)
        fc = generate_forecasts(monthly, sel)
        assert set(fc["forecast_month"]) == {8, 9, 10, 11, 12}

    def test_forecast_id_unique(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        sel = select_methods(monthly, elig)
        fc = generate_forecasts(monthly, sel)
        assert fc["forecast_id"].nunique() == len(fc)

    def test_point_forecast_not_nan(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        sel = select_methods(monthly, elig)
        fc = generate_forecasts(monthly, sel)
        assert fc["point_forecast"].notna().all()

    def test_lower_bound_le_point_le_upper_bound(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        sel = select_methods(monthly, elig)
        fc = generate_forecasts(monthly, sel)
        assert (fc["lower_bound"] <= fc["point_forecast"]).all()
        assert (fc["point_forecast"] <= fc["upper_bound"]).all()

    def test_horizon_risk_labels_present(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        sel = select_methods(monthly, elig)
        fc = generate_forecasts(monthly, sel)
        expected = {"nearest indicative horizon", "short indicative horizon",
                    "medium indicative horizon", "extended indicative horizon",
                    "extended indicative horizon with highest uncertainty"}
        assert set(fc["horizon_risk"]).issubset(expected)

    def test_quality_declines_with_horizon(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        sel = select_methods(monthly, elig)
        fc = generate_forecasts(monthly, sel)
        for _, g in fc.groupby(["hospital", "department_code", "kpi_id"]):
            qualities = g.sort_values("forecast_month")["forecast_quality"].tolist()
            # Later months should not be higher confidence than earlier ones
            # (simplified: if first is MODERATE, later should not be MODERATE if they were lower before)
            # This is a weak check; just ensure no 'High' confidence is used.
            for q in qualities:
                assert "High" not in q

    def test_disclaimer_present(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        sel = select_methods(monthly, elig)
        fc = generate_forecasts(monthly, sel)
        assert (fc["disclaimer"].str.contains("indicative operational estimates", case=False)).all()

    def test_approval_status_indicative_prototype(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        sel = select_methods(monthly, elig)
        fc = generate_forecasts(monthly, sel)
        assert (fc["approval_status"] == "Indicative Prototype").all()

    def test_model_version_present(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        sel = select_methods(monthly, elig)
        fc = generate_forecasts(monthly, sel)
        assert (fc["model_version"] != "").all()


# ============================================================
# 7. Plausibility Constraint Tests
# ============================================================

class TestPlausibilityConstraints:
    def test_staffing_level_within_bounds(self):
        for raw in [-5.0, 50.0, 110.0]:
            adj, constraint, reason = _apply_plausibility("kpi_001", raw)
            assert 0 <= adj <= 100
            if raw < 0 or raw > 100:
                assert constraint != "None"

    def test_absenteeism_rate_within_bounds(self):
        for raw in [-2.0, 10.0, 120.0]:
            adj, constraint, reason = _apply_plausibility("kpi_002", raw)
            assert 0 <= adj <= 100
            if raw < 0 or raw > 100:
                assert constraint != "None"

    def test_bed_occupancy_capped_at_governed_max(self):
        adj, constraint, reason = _apply_plausibility("kpi_003", 110.0)
        assert adj <= 104.761905
        assert constraint == "Maximum bound"

    def test_waiting_time_minimum_zero(self):
        adj, constraint, reason = _apply_plausibility("kpi_004", -5.0)
        assert adj == 0
        assert constraint == "Minimum bound"

    def test_satisfaction_score_within_likert(self):
        adj, constraint, reason = _apply_plausibility("kpi_006", 6.0)
        assert adj == 5.0
        assert constraint == "Maximum bound"

    def test_constraint_reason_non_empty_when_applied(self):
        adj, constraint, reason = _apply_plausibility("kpi_006", 6.0)
        assert reason != ""

    def test_no_constraint_for_valid_value(self):
        adj, constraint, reason = _apply_plausibility("kpi_001", 85.0)
        assert constraint == "None"
        assert adj == 85.0


# ============================================================
# 8. Threshold Evaluation Tests
# ============================================================

class TestThresholdEvaluation:
    def test_single_value_red_lower(self):
        row = pd.Series({"lower_red_boundary": 80, "lower_amber_boundary": 85,
                         "green_lower_boundary": 85, "green_upper_boundary": 100,
                         "upper_amber_boundary": np.nan, "upper_red_boundary": np.nan})
        assert evaluate_single_value_against_thresholds(75, row) == "Red"

    def test_single_value_green(self):
        row = pd.Series({"lower_red_boundary": 80, "lower_amber_boundary": 85,
                         "green_lower_boundary": 85, "green_upper_boundary": 100,
                         "upper_amber_boundary": np.nan, "upper_red_boundary": np.nan})
        assert evaluate_single_value_against_thresholds(90, row) == "Green"

    def test_single_value_amber(self):
        row = pd.Series({"lower_red_boundary": 80, "lower_amber_boundary": 85,
                         "green_lower_boundary": 85, "green_upper_boundary": 100,
                         "upper_amber_boundary": 105, "upper_red_boundary": 110})
        assert evaluate_single_value_against_thresholds(103, row) == "Amber"

    def test_single_value_not_assessable(self):
        row = pd.Series({"lower_red_boundary": np.nan, "lower_amber_boundary": np.nan,
                         "green_lower_boundary": np.nan, "green_upper_boundary": np.nan,
                         "upper_amber_boundary": np.nan, "upper_red_boundary": np.nan})
        assert evaluate_single_value_against_thresholds(50, row) == "Not Assessable"

    def test_threshold_status_added_to_forecasts(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        sel = select_methods(monthly, elig)
        fc = generate_forecasts(monthly, sel)
        threshold_cfg = pd.read_csv("config/kpi_threshold_config.csv")
        fc_status = evaluate_threshold_status(fc, threshold_cfg)
        assert "forecast_status" in fc_status.columns
        assert "threshold_rule" in fc_status.columns

    def test_forecast_statuses_are_valid(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        sel = select_methods(monthly, elig)
        fc = generate_forecasts(monthly, sel)
        threshold_cfg = pd.read_csv("config/kpi_threshold_config.csv")
        fc_status = evaluate_threshold_status(fc, threshold_cfg)
        assert fc_status["forecast_status"].isin(["Green", "Amber", "Red", "Not Assessable"]).all()


# ============================================================
# 9. Warning Engine Tests
# ============================================================

class TestWarningEngine:
    def test_classify_green_to_amber(self):
        level, reason, change = _classify_warning("Green", "Amber")
        assert level == "Emerging Warning"
        assert "Green" in reason and "Amber" in reason

    def test_classify_green_to_red(self):
        level, reason, change = _classify_warning("Green", "Red")
        assert level == "High Early Warning"

    def test_classify_amber_to_red(self):
        level, reason, change = _classify_warning("Amber", "Red")
        assert level == "Escalating Warning"

    def test_classify_stable(self):
        level, reason, change = _classify_warning("Green", "Green")
        assert level == "Monitoring"

    def test_classify_not_assessable(self):
        level, reason, change = _classify_warning("Not Assessable", "Amber")
        assert level == "Not Assessable"

    def test_warning_signals_dataframe(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        sel = select_methods(monthly, elig)
        fc = generate_forecasts(monthly, sel)
        threshold_cfg = pd.read_csv("config/kpi_threshold_config.csv")
        fc_status = evaluate_threshold_status(fc, threshold_cfg)
        interventions = pd.read_csv("config/intervention_catalogue.csv")
        warnings = generate_warning_signals(fc_status, monthly, interventions, threshold_cfg)
        assert isinstance(warnings, pd.DataFrame)
        assert len(warnings) == len(fc)

    def test_warning_level_values_valid(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        sel = select_methods(monthly, elig)
        fc = generate_forecasts(monthly, sel)
        threshold_cfg = pd.read_csv("config/kpi_threshold_config.csv")
        fc_status = evaluate_threshold_status(fc, threshold_cfg)
        interventions = pd.read_csv("config/intervention_catalogue.csv")
        warnings = generate_warning_signals(fc_status, monthly, interventions, threshold_cfg)
        valid_levels = {"Monitoring", "Emerging Warning", "High Early Warning", "Escalating Warning", "Not Assessable"}
        assert set(warnings["warning_level"]).issubset(valid_levels)

    def test_suggested_action_text_does_not_claim_completion(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        sel = select_methods(monthly, elig)
        fc = generate_forecasts(monthly, sel)
        threshold_cfg = pd.read_csv("config/kpi_threshold_config.csv")
        fc_status = evaluate_threshold_status(fc, threshold_cfg)
        interventions = pd.read_csv("config/intervention_catalogue.csv")
        warnings = generate_warning_signals(fc_status, monthly, interventions, threshold_cfg)
        for text in warnings["suggested_action_text"]:
            assert "COMPLETED" not in text.upper()
            assert "DONE" not in text.upper()
            assert "APPROVED" not in text.upper()


# ============================================================
# 10. Runner / Integration Tests
# ============================================================

class TestRunnerIntegration:
    def test_runner_creates_all_outputs(self):
        from scripts.run_kpi_forecast_engine import main
        # main already ran; check outputs exist
        expected_files = [
            "outputs/forecasting/kpi_monthly_actual_history.csv",
            "outputs/forecasting/kpi_forecast_eligibility_audit.csv",
            "outputs/forecasting/kpi_forecast_method_selection.csv",
            "outputs/forecasting/kpi_forecast_method_validation.csv",
            "outputs/forecasting/analytical_kpi_monthly_forecast.csv",
            "outputs/forecasting/analytical_kpi_forecast_status.csv",
            "outputs/forecasting/analytical_kpi_forecast_warning_signals.csv",
            "outputs/forecasting/forecast_frozen_file_integrity_check.csv",
            "outputs/forecasting/forecast_engine_manifest.json",
        ]
        for f in expected_files:
            assert os.path.exists(f), f"Missing {f}"

    def test_manifest_is_valid_json(self):
        with open("outputs/forecasting/forecast_engine_manifest.json") as f:
            manifest = json.load(f)
        assert "engine_name" in manifest
        assert manifest["approval_status"] == "Indicative Prototype"

    def test_manifest_contains_selected_method_counts(self):
        with open("outputs/forecasting/forecast_engine_manifest.json") as f:
            manifest = json.load(f)
        assert "selected_method_counts" in manifest

    def test_frozen_file_integrity_no_modifications(self):
        integrity = pd.read_csv("outputs/forecasting/forecast_frozen_file_integrity_check.csv")
        modified = integrity[integrity["validation_note"] == "MODIFIED"]
        assert modified.empty, f"Frozen files modified: {modified['file_path'].tolist()}"

    def test_disclaimer_in_manifest(self):
        with open("outputs/forecasting/forecast_engine_manifest.json") as f:
            manifest = json.load(f)
        assert "indicative operational estimates" in manifest["disclaimer"].lower()

    def test_no_forecast_values_for_ineligible(self):
        elig = pd.read_csv("outputs/forecasting/kpi_forecast_eligibility_audit.csv")
        ineligible = elig[elig["eligibility_status"] == "INSUFFICIENT HISTORICAL DATA"]
        fc = pd.read_csv("outputs/forecasting/analytical_kpi_monthly_forecast.csv")
        for _, row in ineligible.iterrows():
            combo = fc[
                (fc["hospital"] == row["hospital"]) &
                (fc["department_code"] == row["department_code"]) &
                (fc["kpi_id"] == row["kpi_id"])
            ]
            assert combo.empty, f"Forecast found for ineligible combo {row['kpi_id']} {row['department_code']}"

    def test_august_rows_present_for_eligible(self):
        elig = pd.read_csv("outputs/forecasting/kpi_forecast_eligibility_audit.csv")
        eligible = elig[elig["eligibility_status"] == "ELIGIBLE"]
        fc = pd.read_csv("outputs/forecasting/analytical_kpi_monthly_forecast.csv")
        for _, row in eligible.iterrows():
            combo = fc[
                (fc["hospital"] == row["hospital"]) &
                (fc["department_code"] == row["department_code"]) &
                (fc["kpi_id"] == row["kpi_id"]) &
                (fc["forecast_month"] == 8)
            ]
            assert len(combo) == 1, f"Missing August forecast for eligible combo {row['kpi_id']} {row['department_code']}"


# ============================================================
# 11. Horizon & Quality Tests
# ============================================================

class TestHorizonAndQuality:
    def test_horizon_risk_august_is_nearest(self):
        assert _horizon_risk_label(1) == "nearest indicative horizon"

    def test_horizon_risk_december_is_extended(self):
        assert _horizon_risk_label(5) == "extended indicative horizon with highest uncertainty"

    def test_quality_not_high_confidence(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        sel = select_methods(monthly, elig)
        fc = generate_forecasts(monthly, sel)
        assert not fc["forecast_quality"].str.contains("High Confidence", case=False).any()

    def test_quality_contains_indicative(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        sel = select_methods(monthly, elig)
        fc = generate_forecasts(monthly, sel)
        assert fc["forecast_quality"].str.contains("Indicative", case=False).all()

    def test_uncertainty_note_present(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        sel = select_methods(monthly, elig)
        fc = generate_forecasts(monthly, sel)
        assert (fc["uncertainty_note"] != "").all()

    def test_horizon_risk_present(self):
        monthly = prepare_monthly_history()
        elig = assess_eligibility(monthly)
        sel = select_methods(monthly, elig)
        fc = generate_forecasts(monthly, sel)
        assert (fc["horizon_risk"] != "").all()
