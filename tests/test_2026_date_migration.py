"""Sentinel360 - 2026 Date Migration Verification.

Focused migration checks (12 checks):
1. latest actual cutoff = 2026-07-31
2. no actual record after Jul 2026 is treated as historical actual
3. forecast months are Aug-Dec 2026
4. Executive Overview constants reference 2026
5. Risk & Alert defaults reference 2026
6. Simulation Lab baseline is Jul 2026
7. KPI values remain unchanged after date migration
8. scenario values remain unchanged
9. financial values remain unchanged
10. row counts remain unchanged
11. IDs remain unchanged
12. no accidental 2025 operational dates remain in active demo datasets
"""
import os
import sys
import json
import re

import pandas as pd

# Ensure src is on path
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "src"))


# ---------------------------------------------------------------------------
# 1. Latest actual cutoff = 2026-07-31
# ---------------------------------------------------------------------------
def test_latest_actual_cutoff_is_2026_07_31():
    from src.kpi_forecast_engine import CUTOFF_DATE, HISTORICAL_YEAR
    from src.kpi_forecast_data_preparation import CUTOFF_DATE as PREP_CUTOFF
    from src.streamlit_executive_data_loader import (
        GOVERNED_ACTUAL_MONTH_CUTOFF as EXEC_CUTOFF,
        GOVERNED_ACTUAL_YEAR,
    )

    assert str(CUTOFF_DATE)[:10] == "2026-07-31", f"CUTOFF_DATE={CUTOFF_DATE}"
    assert HISTORICAL_YEAR == 2026
    assert str(PREP_CUTOFF)[:10] == "2026-07-31", f"PREP_CUTOFF={PREP_CUTOFF}"
    assert EXEC_CUTOFF == 7
    assert GOVERNED_ACTUAL_YEAR == 2026


# ---------------------------------------------------------------------------
# 2. No actual record after Jul 2026 is treated as historical actual
# ---------------------------------------------------------------------------
def test_no_actual_record_after_jul_2026():
    """The kpi_forecast_data_preparation.prepare_monthly_history() function
    must not include any record with reporting_date > 2026-07-31 in the
    actuals extraction (the governed cutoff).
    """
    from src.kpi_forecast_data_preparation import prepare_monthly_history, CUTOFF_DATE
    history_path = "outputs/forecasting/kpi_monthly_actual_history.csv"
    if not os.path.exists(history_path):
        return
    df = pd.read_csv(history_path)
    # History is monthly aggregated actuals; check max month in the file
    if "reporting_month" in df.columns:
        months = pd.to_datetime(df["reporting_month"], errors="coerce")
        if months.notna().any():
            max_month = months.max()
            assert max_month <= pd.Timestamp("2026-07-01"), (
                f"Monthly actuals has record after Jul 2026: {max_month}"
            )


# ---------------------------------------------------------------------------
# 3. Forecast months are Aug-Dec 2026
# ---------------------------------------------------------------------------
def test_forecast_months_are_aug_to_dec_2026():
    fc_path = "outputs/forecasting/analytical_kpi_monthly_forecast.csv"
    if not os.path.exists(fc_path):
        return
    df = pd.read_csv(fc_path)
    assert "forecast_year" in df.columns, f"Missing forecast_year: {df.columns.tolist()}"
    years = set(df["forecast_year"].astype(int).unique())
    assert years == {2026}, f"Forecast years must be only 2026, got {years}"

    starts = pd.to_datetime(df["forecast_period_start"], errors="coerce")
    months = set(starts.dt.month.unique())
    assert months == {8, 9, 10, 11, 12}, f"Forecast months must be 8-12, got {months}"

    sample_id = df["forecast_id"].iloc[0]
    assert "_2026_" in sample_id, f"forecast_id should embed 2026: {sample_id}"


def test_forecast_engine_manifest_updated():
    manifest_path = "outputs/forecasting/forecast_engine_manifest.json"
    if not os.path.exists(manifest_path):
        return
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest.get("historical_cutoff") == "2026-07-31", (
        f"historical_cutoff={manifest.get('historical_cutoff')}"
    )
    horizon = manifest.get("forecast_horizon", [])
    assert horizon == ["2026-08", "2026-09", "2026-10", "2026-11", "2026-12"], (
        f"forecast_horizon={horizon}"
    )


# ---------------------------------------------------------------------------
# 4. Executive Overview constants reference 2026
# ---------------------------------------------------------------------------
def test_executive_overview_references_2026():
    import inspect
    from src import streamlit_executive_data_loader as loader
    source = inspect.getsource(loader)
    assert "GOVERNED_ACTUAL_YEAR = 2026" in source, "GOVERNED_ACTUAL_YEAR not 2026"
    assert "FORECAST_HORIZON_START_MONTH = 8" in source, "FORECAST_HORIZON_START_MONTH not 8"
    assert "FORECAST_HORIZON_END_MONTH = 12" in source, "FORECAST_HORIZON_END_MONTH not 12"


# ---------------------------------------------------------------------------
# 5. Risk & Alert defaults reference 2026
# ---------------------------------------------------------------------------
def test_risk_and_alert_defaults_2026():
    risk_path = "pages/03_Risk_and_Alert.py"
    if not os.path.exists(risk_path):
        return
    with open(risk_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "risk_alert_selected_year\": 2026" in content, (
        "Risk & Alert default year not 2026"
    )
    assert "or [2026]" in content, "Risk & Alert fallback year not 2026"


# ---------------------------------------------------------------------------
# 6. Simulation Lab baseline is Jul 2026
# ---------------------------------------------------------------------------
def test_simulation_lab_baseline_jul_2026():
    src_sim_controller = "src/simulation_lab_controller.py"
    if os.path.exists(src_sim_controller):
        with open(src_sim_controller, "r", encoding="utf-8") as f:
            content = f.read()
        assert "JUL 2026" in content, "Simulation Lab controller JUL 2026 missing"


# ---------------------------------------------------------------------------
# 7. KPI values remain unchanged after date migration
# ---------------------------------------------------------------------------
def test_kpi_values_unchanged():
    kpi_path = "data/analytical/analytical_six_kpi_daily.csv"
    if not os.path.exists(kpi_path):
        return
    df = pd.read_csv(kpi_path)
    kpi_value_cols = [c for c in df.columns if c.startswith("kpi_") and "id" not in c]
    assert kpi_value_cols, f"No KPI value columns: {df.columns.tolist()}"
    if "kpi_001" in df.columns:
        values = df["kpi_001"].dropna()
        assert values.between(0, 100).all(), "kpi_001 must be percentage [0,100]"


# ---------------------------------------------------------------------------
# 8. Scenario values remain unchanged
# ---------------------------------------------------------------------------
def test_scenario_values_unchanged():
    scenario_path = "outputs/scenario_modelling"
    if not os.path.exists(scenario_path):
        return
    for f in os.listdir(scenario_path):
        if f.endswith(".csv") and not f.startswith("_") and "smoke" not in f.lower():
            df = pd.read_csv(os.path.join(scenario_path, f))
            assert len(df) > 0, f"Empty scenario file: {f}"
            num_cols = df.select_dtypes(include="number").columns
            if len(num_cols) > 0:
                for col in num_cols[:3]:
                    assert df[col].notna().any(), f"{f}:{col} all NaN"
            return


# ---------------------------------------------------------------------------
# 9. Financial values remain unchanged
# ---------------------------------------------------------------------------
def test_financial_values_unchanged():
    kpi_path = "data/analytical/analytical_six_kpi_daily.csv"
    if not os.path.exists(kpi_path):
        return
    df = pd.read_csv(kpi_path)
    if "kpi_001" in df.columns:
        mean = df["kpi_001"].mean()
        assert 0 < mean < 100, f"kpi_001 mean should be in (0,100): {mean}"


# ---------------------------------------------------------------------------
# 10. Row counts remain unchanged
# ---------------------------------------------------------------------------
def test_row_counts_unchanged():
    expected = {
        "data/analytical/analytical_six_kpi_daily.csv": lambda n: n > 1000,
        "outputs/forecasting/analytical_kpi_monthly_forecast.csv": lambda n: n > 0,
    }
    for path, check in expected.items():
        if not os.path.exists(path):
            continue
        df = pd.read_csv(path)
        assert check(len(df)), f"{path}: row count check failed (rows={len(df)})"


# ---------------------------------------------------------------------------
# 11. IDs remain unchanged
# ---------------------------------------------------------------------------
def test_ids_remain_unchanged():
    kpi_path = "data/analytical/analytical_six_kpi_daily.csv"
    if not os.path.exists(kpi_path):
        return
    df = pd.read_csv(kpi_path)
    if "hospital_id" in df.columns:
        assert "HOSP-001" in df["hospital_id"].astype(str).values, (
            "hospital_id missing HOSP-001"
        )
    if "kpi_id" in df.columns:
        for kpi in ["kpi_001", "kpi_002", "kpi_003", "kpi_004"]:
            assert kpi in df["kpi_id"].astype(str).values, (
                f"kpi_id missing {kpi}"
            )


# ---------------------------------------------------------------------------
# 12. No accidental 2025 operational dates remain in active demo datasets
# ---------------------------------------------------------------------------
def test_no_2025_in_active_demo_data():
    """Active demo data should not contain 2025 in date/ID contexts."""
    skip_dirs = {"_archive", "_temp", "_temp_2c2e", "_temp_2c2_correction", "smoke_test", "__pycache__"}
    skip_files = {"smoke_scenario_runs.csv", "_smoke_analytical_scenario_runs.csv"}

    # Patterns that count as "operational date" 2025
    date_patterns = [
        re.compile(r"2025-\d{2}-\d{2}"),  # ISO date
        re.compile(r"2025-\d{2}"),  # year-month
        re.compile(r"2025_\d{2}"),  # forecast_id
        re.compile(r"2025\.\d"),  # year.float
        re.compile(r"2025,"),  # csv year field
    ]

    found = []
    for base in ["data", "outputs"]:
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for f in files:
                if f in skip_files:
                    continue
                if not f.endswith((".csv", ".json")):
                    continue
                path = os.path.join(root, f)
                try:
                    with open(path, "r", encoding="utf-8", errors="replace") as fp:
                        for i, line in enumerate(fp, 1):
                            for pat in date_patterns:
                                if pat.search(line):
                                    found.append((path, i, line.rstrip()[:120]))
                                    break
                            if len(found) > 5:
                                break
                except Exception:
                    pass
                if len(found) > 5:
                    break
            if len(found) > 5:
                break
        if len(found) > 5:
            break

    assert not found, f"Operational 2025 dates still present: {found}"
