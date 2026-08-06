"""Simulation Lab Controller — lightweight helper for pages/04_Simulation_Lab.py.

Reuses ONLY existing governed engines, configs, and data.  No new models.
No new assumptions.  No frozen output modification.
"""
from __future__ import annotations

import calendar
import json
import math
import os
import sys
import warnings
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# Ensure src/ is on path so existing financial engines with relative imports work
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

# ---------------------------------------------------------------------------
# Sentinel360 project imports
# ---------------------------------------------------------------------------
from src.financial_base_engine import FinancialBaseEngine
from src.financial_benefit_engine import FinancialBenefitEngine
from src.financial_cost_engine import FinancialCostEngine
from src.financial_net_impact_engine import FinancialNetImpactEngine
from src.financial_roi_engine import FinancialROIEngine
from src.scenario_baseline_engine import ScenarioBaselineEngine
from src.scenario_config_loader import ScenarioConfigLoader
from src.scenario_models import (
    BaselineStatus,
    ScenarioBaseline,
    ScenarioResult,
)
from src.staffing_scenario_engine import StaffingScenarioEngine
from src.absenteeism_scenario_engine import AbsenteeismScenarioEngine
from src.patient_flow_scenario_engine import PatientFlowScenarioEngine
from src.scenario_tradeoff_engine import ScenarioTradeoffEngine
from src.scenario_displacement_engine import ScenarioDisplacementEngine
from src.scenario_governance_validator import ScenarioGovernanceValidator

from src.streamlit_executive_data_loader import (
    load_kpi_daily,
    load_kpi_monthly_forecast,
    get_kpi_annual_forecast_series,
    GOVERNED_ACTUAL_YEAR,
    GOVERNED_ACTUAL_MONTH_CUTOFF,
    FORECAST_HORIZON_START_MONTH,
    get_filter_options as _get_data_filter_options,
)
from src.streamlit_executive_page_controller import (
    format_unit_value,
    evaluate_kpi_status,
    load_kpi_threshold_config,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_KPI_ID_TO_NAME: Dict[str, str] = {
    "kpi_001": "Staffing Level",
    "kpi_002": "Staff Absenteeism Rate",
    "kpi_003": "Bed Occupancy Rate",
    "kpi_004": "Average Patient Waiting Time",
    "kpi_005": "Patient Complaint Rate",
    "kpi_006": "Patient Satisfaction Score",
}

_SUPPORTED_KPI_IDS: Tuple[str, ...] = ("kpi_001", "kpi_002", "kpi_003", "kpi_004")

_KPI_ENGINE_MAP: Dict[str, Any] = {
    "kpi_001": StaffingScenarioEngine,
    "kpi_002": AbsenteeismScenarioEngine,
    "kpi_003": PatientFlowScenarioEngine,
    "kpi_004": PatientFlowScenarioEngine,
}

_KPI_TO_SCENARIO_FAMILY: Dict[str, str] = {
    "kpi_001": "Staffing Coverage Adjustment",
    "kpi_002": "Absenteeism Contingency",
    "kpi_003": "Patient Flow",
    "kpi_004": "Patient Flow",
}

_KPI_TO_SCENARIO_TEMPLATE: Dict[str, str] = {
    "kpi_001": "SCEN-STAFF-001",
    "kpi_002": "SCEN-ABS-001",
    "kpi_003": "SCEN-FLOW-001",
    "kpi_004": "SCEN-FLOW-001",
}

_KPI_TO_ACTION_STRATEGY: Dict[str, str] = {
    "kpi_001": "Staffing Coverage Adjustment",
    "kpi_002": "Absenteeism Contingency Response",
    "kpi_003": "Patient Flow Capacity Adjustment",
    "kpi_004": "Patient Flow Capacity Adjustment",
}

_COMPARATOR_ORDER: Tuple[str, ...] = ("Conservative", "Expected", "Higher Intensity")

_DISPLAY_LABEL_FOR_COMPARATOR_ID: Dict[str, str] = {
    "Conservative": "Minimum Action",
    "Expected": "Recommended Action",
    "Higher Intensity": "Intensive Action",
}

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "analytical")
_CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")

# Financial display governance (from financial_display_governance.csv)
_FINANCIAL_DISPLAY_RULES: Dict[str, str] = {
    "cost_label": "Estimated Intervention Cost",
    "benefit_label": "Estimated Financial Benefit",
    "net_label": "Estimated Net Financial Impact",
    "roi_label": "Estimated ROI (%)",
    "confidence": "Moderate",
    "causality": "Not Confirmed",
    "decision_status": "Pending Management Review",
    "exposure": "Estimated Operational Financial Exposure",
    "assumption_label": "Governed Analytical Assumption",
    "approval_status": "Ready with Financial Conditions",
}

# Forbidden financial wording
_FORBIDDEN_WORDS: Tuple[str, ...] = (
    "Actual Cost",
    "Guaranteed Savings",
    "Profit",
    "Proven ROI",
    "High Confidence",
    "Confirmed Causality",
    "Approved",
    "Definite Cost",
    "Fact",
    "Strong",  # must use Higher Intensity
)


# ---------------------------------------------------------------------------
# Config loaders
# ---------------------------------------------------------------------------

def _read_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def _load_intervention_catalogue() -> pd.DataFrame:
    return _read_csv(os.path.join(_CONFIG_DIR, "intervention_catalogue.csv"))


def _load_scenario_assumption_profile_config() -> pd.DataFrame:
    return _read_csv(os.path.join(_CONFIG_DIR, "scenario_assumption_profile_config.csv"))


def _load_scenario_comparator_config() -> pd.DataFrame:
    return _read_csv(os.path.join(_CONFIG_DIR, "scenario_comparator_config.csv"))


def _load_financial_cost_driver_mapping() -> pd.DataFrame:
    return _read_csv(os.path.join(_CONFIG_DIR, "financial_cost_driver_mapping.csv"))


def _load_financial_display_governance() -> pd.DataFrame:
    return _read_csv(os.path.join(_CONFIG_DIR, "financial_display_governance.csv"))


def _load_analytical_workforce() -> pd.DataFrame:
    return _read_csv(os.path.join(_DATA_DIR, "analytical_workforce_kpi_daily.csv"))


def _load_analytical_six_kpi() -> pd.DataFrame:
    return _read_csv(os.path.join(_DATA_DIR, "analytical_six_kpi_daily.csv"))


# ---------------------------------------------------------------------------
# Filter options
# ---------------------------------------------------------------------------

def get_filter_options() -> Dict[str, Any]:
    """Return hospital, department, month, and KPI options for the Simulation Lab."""
    raw = _get_data_filter_options(load_kpi_daily())

    # Hospitals from actual data
    hospital_options = sorted(
        [h for h, _ in raw.get("hospital", [])]
    ) if raw.get("hospital") else []

    # Departments — exclude ALL and DEPT-PEX (same logic as Risk & Alert)
    dept_options = sorted(
        [
            d for d, _ in raw.get("department", [])
            if d not in ("ALL", "DEPT-PEX")
        ]
    ) if raw.get("department") else []

    # Supported forecast months only
    month_options = list(range(FORECAST_HORIZON_START_MONTH, 13))

    kpi_options = [
        {"id": kpi_id, "name": _KPI_ID_TO_NAME[kpi_id]}
        for kpi_id in _SUPPORTED_KPI_IDS
    ]

    return {
        "hospitals": hospital_options,
        "departments": dept_options,
        "months": month_options,
        "kpis": kpi_options,
    }


# ---------------------------------------------------------------------------
# Interventions
# ---------------------------------------------------------------------------

def load_interventions_for_kpi(kpi_id: str) -> pd.DataFrame:
    """Filter intervention catalogue to active interventions for the given KPI."""
    df = _load_intervention_catalogue()
    if df.empty:
        return df
    # applicable_kpi_id may contain semicolon-separated values like "kpi_001;kpi_002"
    mask = df["applicable_kpi_id"].apply(
        lambda v: kpi_id in str(v).split(";") if pd.notna(v) else False
    ) & (df["active_flag"].str.strip().str.lower() == "true")
    return df[mask].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Baseline construction
# ---------------------------------------------------------------------------

def _to_float(val: Any, default: float = 0.0) -> float:
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _apply_governed_cutoff(df: pd.DataFrame) -> pd.DataFrame:
    """Return rows with reporting_date <= JUL 2025 governed cutoff."""
    if df is None or df.empty or "reporting_date" not in df.columns:
        return df
    df = df.copy()
    df["_date"] = pd.to_datetime(df["reporting_date"], errors="coerce")
    cutoff = pd.Timestamp(f"{GOVERNED_ACTUAL_YEAR}-{GOVERNED_ACTUAL_MONTH_CUTOFF:02d}-31")
    filtered = df[df["_date"] <= cutoff].drop(columns=["_date"], errors="ignore")
    return filtered


def _latest_actual_value(
    df: pd.DataFrame,
    hospital_id: str,
    department_id: str,
    kpi_id: str,
) -> Optional[Tuple[float, str, str]]:
    """Return (latest_kpi_value, unit, latest_date) for the given hospital/dept/kpi."""
    if df is None or df.empty:
        return None
    df = _apply_governed_cutoff(df)
    mask = (
        (df["hospital_id"] == hospital_id)
        & (df["department_id"] == department_id)
        & (df["kpi_id"] == kpi_id)
        & (df["calculation_status"].str.strip() == "Calculated")
    )
    subset = df[mask]
    if subset.empty:
        return None

    # Sort by date descending, take latest
    subset = subset.copy()
    subset["_date"] = pd.to_datetime(subset["reporting_date"], errors="coerce")
    subset = subset.sort_values("_date", ascending=False)
    latest = subset.iloc[0]
    val = _to_float(latest.get("kpi_value"), None)
    unit = str(latest.get("unit", "")).strip()
    date_str = str(latest.get("reporting_date", "")).strip()
    return val, unit, date_str


def _extract_staffing_components(
    df: pd.DataFrame,
    hospital_id: str,
    department_id: str,
) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[str]]:
    """Extract required_staff, available_staff, coverage_pct for kpi_001."""
    if df is None or df.empty:
        return None, None, None, None
    df = _apply_governed_cutoff(df)
    mask = (
        (df["hospital_id"] == hospital_id)
        & (df["department_id"] == department_id)
        & (df["kpi_id"] == "kpi_001")
        & (df["calculation_status"].str.strip() == "Calculated")
    )
    subset = df[mask].copy()
    if subset.empty:
        return None, None, None, None
    subset["_date"] = pd.to_datetime(subset["reporting_date"], errors="coerce")
    subset = subset.sort_values("_date", ascending=False)

    req_vals = subset["denominator_value"].apply(_to_float).dropna()
    avail_vals = subset["numerator_value"].apply(_to_float).dropna()
    kpi_vals = subset["kpi_value"].apply(_to_float).dropna()

    latest_date = str(subset.iloc[0]["reporting_date"]).strip() if len(subset) > 0 else None

    req = float(req_vals.mean()) if not req_vals.empty else None
    avail = float(avail_vals.mean()) if not avail_vals.empty else None
    cov = float(kpi_vals.mean()) if not kpi_vals.empty else None
    return req, avail, cov, latest_date


def _extract_patient_flow_components(
    df: pd.DataFrame,
    hospital_id: str,
    department_id: str,
) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[str]]:
    """Extract avg_wait_min, arrivals, service_capacity for kpi_004."""
    if df is None or df.empty:
        return None, None, None, None
    df = _apply_governed_cutoff(df)
    mask = (
        (df["hospital_id"] == hospital_id)
        & (df["department_id"] == department_id)
        & (df["kpi_id"] == "kpi_004")
        & (df["calculation_status"].str.strip() == "Calculated")
    )
    subset = df[mask].copy()
    if subset.empty:
        return None, None, None, None
    subset["_date"] = pd.to_datetime(subset["reporting_date"], errors="coerce")
    subset = subset.sort_values("_date", ascending=False)

    kpi_vals = subset["kpi_value"].apply(_to_float).dropna()
    num_vals = subset["numerator_value"].apply(_to_float).dropna()
    den_vals = subset["denominator_value"].apply(_to_float).dropna()

    avg_wait = float(kpi_vals.mean()) if not kpi_vals.empty else None
    arrivals = float(den_vals.mean()) if not den_vals.empty else None
    # capacity approx = total patients / observation days
    total_patients = float(den_vals.sum()) if not den_vals.empty else 0.0
    obs_days = max(1, len(den_vals))
    capacity = total_patients / obs_days if total_patients > 0 else None

    latest_date = str(subset.iloc[0]["reporting_date"]).strip() if len(subset) > 0 else None
    return avg_wait, arrivals, capacity, latest_date


def build_baseline(
    hospital_id: str,
    department_id: str,
    kpi_id: str,
) -> Optional[ScenarioBaseline]:
    """Build a ScenarioBaseline from the latest governed actual data.

    Does NOT create new data — only aggregates existing analytical records.
    """
    workforce_df = _load_analytical_workforce()
    six_kpi_df = _load_analytical_six_kpi()

    if kpi_id in ("kpi_001", "kpi_002"):
        result = _latest_actual_value(workforce_df, hospital_id, department_id, kpi_id)
    else:
        result = _latest_actual_value(six_kpi_df, hospital_id, department_id, kpi_id)

    if result is None:
        return None

    kpi_val, unit, latest_date = result

    baseline_id = f"BASE-{hospital_id}-{department_id}-{kpi_id}"
    now = datetime.utcnow().isoformat()

    kwargs: Dict[str, Any] = {
        "baseline_id": baseline_id,
        "approval_package_id": "SIM-LAB-PKG-001",
        "episode_id": "SIM-LAB-EPI-001",
        "scenario_template_id": _KPI_TO_SCENARIO_TEMPLATE.get(kpi_id, ""),
        "hospital_id": hospital_id,
        "department_id": department_id,
        "episode_start_date": f"{GOVERNED_ACTUAL_YEAR}-01-01",
        "episode_end_date": latest_date or f"{GOVERNED_ACTUAL_YEAR}-{GOVERNED_ACTUAL_MONTH_CUTOFF:02d}-31",
        "dominant_kpi_id": kpi_id,
        "dominant_kpi_name": _KPI_ID_TO_NAME.get(kpi_id, ""),
        "baseline_kpi_value": kpi_val,
        "baseline_kpi_unit": unit,
        "baseline_reference_date": latest_date,
        "baseline_status": BaselineStatus.AVAILABLE,
        "baseline_data_completeness": 100.0,
        "baseline_confidence": "Moderate",
        "source_file_list": ["analytical_workforce_kpi_daily.csv" if kpi_id in ("kpi_001", "kpi_002") else "analytical_six_kpi_daily.csv"],
    }

    # Add KPI-specific components
    if kpi_id == "kpi_001":
        req, avail, cov, _ = _extract_staffing_components(workforce_df, hospital_id, department_id)
        kwargs["baseline_required_staff"] = req
        kwargs["baseline_available_staff"] = avail
        kwargs["baseline_staffing_coverage_pct"] = cov

    elif kpi_id == "kpi_002":
        kwargs["baseline_absenteeism_rate"] = kpi_val

    elif kpi_id in ("kpi_003", "kpi_004"):
        wait, arrivals, capacity, _ = _extract_patient_flow_components(six_kpi_df, hospital_id, department_id)
        kwargs["baseline_avg_wait_min"] = wait
        kwargs["baseline_arrivals"] = arrivals
        kwargs["baseline_service_capacity"] = capacity
        if kpi_id == "kpi_003":
            kwargs["baseline_kpi_unit"] = "Percent"

    return ScenarioBaseline(**kwargs)


# ---------------------------------------------------------------------------
# Forecast retrieval
# ---------------------------------------------------------------------------

def get_forecast_for_kpi(
    hospital_id: str,
    department_id: str,
    kpi_id: str,
    month: int,
    year: int = GOVERNED_ACTUAL_YEAR,
) -> Optional[Dict[str, Any]]:
    """Return the governed forecast value for the selected month."""
    forecast_df = get_kpi_annual_forecast_series(
        load_kpi_monthly_forecast(), hospital_id, department_id, kpi_id, year
    )
    if forecast_df is None or forecast_df.empty:
        return None

    # forecast_df has columns: month, monthly_value, lower_value, upper_value, eligibility_status, unit
    mask = forecast_df["month"] == month
    row = forecast_df[mask]
    if row.empty:
        return None

    r = row.iloc[0]
    val = _to_float(r.get("monthly_value"), None)
    lower = _to_float(r.get("lower_value"), None)
    upper = _to_float(r.get("upper_value"), None)
    eligibility = str(r.get("eligibility_status", "INELIGIBLE")).strip()
    unit = str(r.get("unit", "")).strip()

    # Get warning from forecast signals
    from src.streamlit_executive_data_loader import load_kpi_forecast_warning_signals
    signals = load_kpi_forecast_warning_signals()
    warning = "Monitoring"
    if signals is not None and not signals.empty:
        wmask = (
            (signals["hospital"] == hospital_id)
            & (signals["department_code"] == department_id)
            & (signals["kpi_id"] == kpi_id)
            & (signals["forecast_month"] == month)
        )
        wrow = signals[wmask]
        if not wrow.empty:
            warning = str(wrow.iloc[0].get("warning_level", "Monitoring")).strip()

    return {
        "value": val,
        "lower": lower,
        "upper": upper,
        "unit": unit,
        "eligibility": eligibility,
        "warning": warning,
    }


# ---------------------------------------------------------------------------
# Comparator profiles
# ---------------------------------------------------------------------------

def get_comparator_profiles(scenario_template_id: str) -> List[Dict[str, Any]]:
    """Return Conservative, Expected, Higher Intensity profiles for a template."""
    profile_df = _load_scenario_assumption_profile_config()
    comparator_df = _load_scenario_comparator_config()

    if profile_df.empty or comparator_df.empty:
        return []

    profiles = []
    for comp_type in _COMPARATOR_ORDER:
        # Find comparator row for this template + type
        cmask = (
            (comparator_df["scenario_template_id"] == scenario_template_id)
            & (comparator_df["comparator_type"] == comp_type)
        )
        crows = comparator_df[cmask]
        if crows.empty:
            continue
        comparator_id = str(crows.iloc[0]["comparator_id"]).strip()
        profile_id = str(crows.iloc[0]["assumption_profile"]).strip()

        # Get profile assumptions
        pmask = (
            (profile_df["profile_id"] == profile_id)
            & (profile_df["scenario_template_id"] == scenario_template_id)
            & (profile_df["comparator_type"] == comp_type)
        )
        prows = profile_df[pmask]
        if prows.empty:
            continue

        assumptions: Dict[str, Any] = {}
        for _, r in prows.iterrows():
            field = str(r.get("assumption_name", "")).strip()
            val = r.get("assumption_value", "")
            if field:
                try:
                    # Try int first, then float, then string
                    if "." not in str(val):
                        assumptions[field] = int(val)
                    else:
                        assumptions[field] = float(val)
                except (ValueError, TypeError):
                    assumptions[field] = str(val).strip()

        profiles.append({
            "comparator_type": comp_type,
            "comparator_id": comparator_id,
            "profile_id": profile_id,
            "assumptions": assumptions,
        })

    return profiles


# ---------------------------------------------------------------------------
# Scenario engine routing
# ---------------------------------------------------------------------------

def run_scenario(
    baseline: ScenarioBaseline,
    kpi_id: str,
    comparator_profile: Dict[str, Any],
) -> Optional[ScenarioResult]:
    """Run the correct scenario engine for the KPI + comparator.

    Returns ScenarioResult or None if engine unavailable.
    """
    engine_cls = _KPI_ENGINE_MAP.get(kpi_id)
    if engine_cls is None:
        return None

    loader = ScenarioConfigLoader()
    validator = ScenarioGovernanceValidator(loader)
    engine = engine_cls(validator)
    comparator = {
        "comparator_id": comparator_profile["comparator_id"],
        "comparator_type": comparator_profile["comparator_type"],
        "scenario_mode": "Single Intervention",
        "profile_id": comparator_profile["profile_id"],
    }
    assumptions = comparator_profile["assumptions"]

    try:
        result, validations = engine.run(baseline, comparator, assumptions)
        return result
    except Exception as exc:
        warnings.warn(f"Scenario engine failed for {kpi_id}/{comparator_profile['comparator_type']}: {exc}")
        return None


# ---------------------------------------------------------------------------
# Financial impact — use existing engines only
# ---------------------------------------------------------------------------

def _has_financial_mapping(scenario_family: str, comparator_type: str) -> bool:
    """Check if cost driver mapping exists for this family + comparator.

    The actual financial_cost_driver_mapping.csv uses
    ``applicable_comparator_types`` which may be comma- or semicolon-separated
    inside a quoted CSV field. We parse both separators.
    """
    df = _load_financial_cost_driver_mapping()
    if df.empty:
        return False
    family_mask = df["scenario_family"] == scenario_family
    if not family_mask.any():
        return False
    for _, row in df[family_mask].iterrows():
        raw = str(row.get("applicable_comparator_types", ""))
        # Handle both comma and semicolon separators
        types = [t.strip() for t in raw.replace(";", ",").split(",") if t.strip()]
        if comparator_type in types:
            return True
    return False


def _safe_financial_compute(
    scenario_family: str,
    comparator_type: str,
    assumptions: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Smallest possible financial adapter using governed config only.

    Reads financial_cost_driver_mapping.csv and financial_input_definition.csv.
    For each matching cost driver:
      cost = assumption_value * default_rate * intervention_duration_days
    Returns total cost dict or None if exact linkage is not possible.
    """
    try:
        mapping = _load_financial_cost_driver_mapping()
        if mapping.empty:
            return None
        family_rows = mapping[mapping["scenario_family"] == scenario_family]
        if family_rows.empty:
            return None
        # Filter by comparator type
        matched = []
        for _, row in family_rows.iterrows():
            raw = str(row.get("applicable_comparator_types", ""))
            types = [t.strip() for t in raw.replace(";", ",").split(",") if t.strip()]
            if comparator_type in types:
                matched.append(row)
        if not matched:
            return None

        # Load input definitions for default rates
        input_def_path = os.path.join(_CONFIG_DIR, "financial_input_definition.csv")
        if not os.path.exists(input_def_path):
            return None
        input_def = pd.read_csv(input_def_path, keep_default_na=False)

        duration = float(assumptions.get("intervention_duration_days", 1) or 1)
        total_cost = 0.0
        details = []
        currency = "MYR"
        for row in matched:
            assumption_name = str(row.get("assumption_name", "")).strip()
            financial_input_id = str(row.get("financial_input_id", "")).strip()
            component_name = str(row.get("cost_component_name", "")).strip()
            if not assumption_name or not financial_input_id:
                continue
            assumption_value = float(assumptions.get(assumption_name, 0) or 0)
            if assumption_value <= 0:
                continue
            rate_rows = input_def[input_def["financial_input_id"] == financial_input_id]
            if rate_rows.empty:
                continue
            rate_str = str(rate_rows.iloc[0].get("default_value", "0"))
            try:
                rate = float(rate_str)
            except (ValueError, TypeError):
                continue
            if rate <= 0:
                continue
            cost = assumption_value * rate * duration
            total_cost += cost
            details.append(component_name)
        if total_cost <= 0:
            return None
        return {
            "total_cost": total_cost,
            "currency": currency,
            "cost_drivers": details,
            "duration_days": int(duration),
            "causality": "Estimated",
            "confidence": "Moderate",
            "engine_version": "phase3d-adapter-v1",
        }
    except Exception:
        return None


def calculate_financial_impact(
    scenario_result: ScenarioResult,
    assumptions: Dict[str, Any],
    scenario_family: str,
    comparator_type: str,
) -> Optional[Dict[str, Any]]:
    """Calculate financial impact using existing engines where supported.

    Returns dict with total_cost + governance fields if computable.
    Returns None if no mapping exists or engines fail.
    """
    if not _has_financial_mapping(scenario_family, comparator_type):
        return None
    result = _safe_financial_compute(scenario_family, comparator_type, assumptions)
    if result is not None:
        return result
    # Exact linkage not possible — keep None so UI shows governed "Not Available".
    return None


# ---------------------------------------------------------------------------
# Trade-off & displacement
# ---------------------------------------------------------------------------

def build_tradeoff_and_displacement(
    results: List[ScenarioResult],
) -> Tuple[str, str]:
    """Use existing tradeoff and displacement engines where APIs are available.

    Returns (tradeoff_text, displacement_text) using only public methods.
    Never exposes Python errors or engine method names.
    """
    if not results:
        return (
            "Trade-off assessment will be available after a scenario is run.",
            "Displacement risk will be available after a scenario is run.",
        )

    tradeoff_text = (
        "Higher intensity scenarios assume more staff/time/throughput changes "
        "and typically yield larger KPI movement but at higher operational cost."
    )
    displacement_text = (
        "Higher intensity interventions may temporarily shift workload to "
        "adjacent teams or shifts; monitor operational signals after launch."
    )

    try:
        engine = ScenarioTradeoffEngine()
        # Use only documented public methods
        if hasattr(engine, "compare_comparators"):
            profile = engine.compare_comparators(results)
            if isinstance(profile, dict) and profile.get("summary"):
                tradeoff_text = str(profile["summary"])
    except Exception:
        pass

    try:
        engine = ScenarioDisplacementEngine()
        if hasattr(engine, "analyse_displacement"):
            analysis = engine.analyse_displacement(results)
            if isinstance(analysis, dict) and analysis.get("summary"):
                displacement_text = str(analysis["summary"])
    except Exception:
        pass

    return tradeoff_text, displacement_text


# ---------------------------------------------------------------------------
# Status evaluation
# ---------------------------------------------------------------------------

def _get_status_for_value(kpi_id: str, value: float) -> Tuple[str, str]:
    """Return (status_text, status_code) for a KPI value."""
    if value is None or math.isnan(value):
        return "Not Assessable", "NOT_ASSESSABLE"

    config = load_kpi_threshold_config()
    if not config or kpi_id not in config:
        return "Not Assessable", "NOT_ASSESSABLE"

    cfg = config[kpi_id]
    direction = str(cfg.get("directionality", "")).strip().upper()

    # Use amber/red boundaries if available
    lower_red = cfg.get("lower_red_boundary")
    lower_amber = cfg.get("lower_amber_boundary")
    upper_amber = cfg.get("upper_amber_boundary")
    upper_red = cfg.get("upper_red_boundary")

    if direction == "HIGHER_IS_BETTER":
        if upper_red is not None and value >= upper_red:
            return "Above Target", "ABOVE_TARGET"
        if upper_amber is not None and value >= upper_amber:
            return "Target Met", "TARGET_MET"
        if lower_amber is not None and value >= lower_amber:
            return "Below Target", "BELOW_TARGET"
        return "Not Assessable", "NOT_ASSESSABLE"
    elif direction == "LOWER_IS_BETTER":
        if lower_red is not None and value <= lower_red:
            return "Above Target", "ABOVE_TARGET"
        if lower_amber is not None and value <= lower_amber:
            return "Target Met", "TARGET_MET"
        if upper_amber is not None and value <= upper_amber:
            return "Below Target", "BELOW_TARGET"
        return "Not Assessable", "NOT_ASSESSABLE"
    else:
        # Context-sensitive / target band
        if lower_amber is not None and upper_amber is not None:
            if lower_amber <= value <= upper_amber:
                return "Target Met", "TARGET_MET"
            elif value < lower_amber or value > upper_amber:
                return "Above Target", "ABOVE_TARGET"
        return "Not Assessable", "NOT_ASSESSABLE"


# ---------------------------------------------------------------------------
# Management takeaway
# ---------------------------------------------------------------------------

def build_management_takeaway(
    kpi_id: str,
    kpi_name: str,
    baseline_value: Optional[float],
    baseline_unit: str,
    forecast_value: Optional[float],
    forecast_unit: str,
    scenario_result: Optional[ScenarioResult],
    comparator_type: str,
    intervention_name: str,
    financial: Optional[Dict[str, Any]],
) -> str:
    """Build a deterministic management takeaway using governed language.

    Structure:
      RECOMMENDED ACTION
      EXPECTED OPERATIONAL IMPACT
      WHY ACT NOW
      RESOURCE LEVEL
      FINANCIAL VIEW
      DECISION REQUIRED
    """
    label = _DISPLAY_LABEL_FOR_COMPARATOR_ID.get(comparator_type, comparator_type)

    baseline_str = format_unit_value(baseline_value, baseline_unit) if baseline_value is not None else "Not available"
    forecast_str = format_unit_value(forecast_value, forecast_unit) if forecast_value is not None else "Not available"

    lines: List[str] = []

    # RECOMMENDED ACTION
    lines.append(f"**RECOMMENDED ACTION**")
    lines.append(f"{intervention_name} — {label}")

    # EXPECTED OPERATIONAL IMPACT
    lines.append("")
    lines.append("**EXPECTED OPERATIONAL IMPACT**")
    if scenario_result is not None and scenario_result.scenario_primary_kpi_value is not None:
        scenario_val = scenario_result.scenario_primary_kpi_value
        scenario_str = format_unit_value(scenario_val, baseline_unit)
        lines.append(
            f"{kpi_name} changes from {forecast_str} (do-nothing forecast) to {scenario_str} under the selected intervention."
        )
    else:
        lines.append(f"{kpi_name} impact is indicative under governed analytical assumptions.")

    # WHY ACT NOW
    lines.append("")
    lines.append("**WHY ACT NOW**")
    if scenario_result is not None:
        status_code = ""
        try:
            sv = scenario_result.scenario_primary_kpi_value
            if sv is not None:
                _txt, status_code = _get_status_for_value(kpi_id, sv)
        except Exception:
            status_code = ""
        status_msg = {
            "ABOVE_TARGET": "current KPI exceeds target",
            "TARGET_MET": "current KPI meets target",
            "BELOW_TARGET": "current KPI is below target",
            "NEEDS_REVIEW": "current KPI needs review",
            "CAUTION": "current KPI is in caution",
            "ALERT": "current KPI is in alert",
        }.get(status_code, "current forecast signals operational pressure")
        lines.append(f"Under the {label} scenario, {status_msg}.")

    # RESOURCE LEVEL
    lines.append("")
    lines.append("**RESOURCE LEVEL**")
    lines.append(label)

    # FINANCIAL VIEW
    lines.append("")
    lines.append("**FINANCIAL VIEW**")
    if financial and isinstance(financial, dict) and financial.get("total_cost") is not None:
        cost = float(financial.get("total_cost", 0))
        currency = financial.get("currency", "MYR")
        days = int(financial.get("duration_days", 0) or 0)
        lines.append(
            f"Estimated Intervention Cost: {currency} {cost:,.0f} over {days} days. "
            f"Causality: Estimated. Confidence: Moderate."
        )
    else:
        lines.append("Financial impact is not available under the current governed mapping.")

    # DECISION REQUIRED
    lines.append("")
    lines.append("**DECISION REQUIRED**")
    lines.append("Review this intervention for management approval.")
    lines.append(f"Decision Status: {_FINANCIAL_DISPLAY_RULES.get('decision_status', 'Pending Management Review')}")

    return "\n\n".join(lines)


# ---------------------------------------------------------------------------
# Full state builder
# ---------------------------------------------------------------------------

def build_simulation_state(
    hospital_id: str,
    department_id: str,
    kpi_id: str,
    forecast_month: int,
    intervention_id: str,
) -> Dict[str, Any]:
    """Build the complete simulation state for the page.

    Returns a dict with baseline, forecast, interventions, comparators,
    scenario results, financial impact, trade-off, and management takeaway.
    """
    state: Dict[str, Any] = {
        "hospital_id": hospital_id,
        "department_id": department_id,
        "kpi_id": kpi_id,
        "kpi_name": _KPI_ID_TO_NAME.get(kpi_id, ""),
        "forecast_month": forecast_month,
        "intervention_id": intervention_id,
    }

    # Baseline
    baseline = build_baseline(hospital_id, department_id, kpi_id)
    state["baseline"] = baseline
    state["baseline_value"] = baseline.baseline_kpi_value if baseline else None
    state["baseline_unit"] = baseline.baseline_kpi_unit if baseline else ""
    state["baseline_date"] = baseline.baseline_reference_date if baseline else None

    # Forecast
    forecast = get_forecast_for_kpi(hospital_id, department_id, kpi_id, forecast_month)
    state["forecast"] = forecast
    state["forecast_value"] = forecast["value"] if forecast else None
    state["forecast_unit"] = forecast["unit"] if forecast else state["baseline_unit"]
    state["forecast_warning"] = forecast["warning"] if forecast else "Monitoring"

    # -----------------------------------------------------------------------
    # Staffing scenario baseline correction (governed model v2)
    # For kpi_001, the scenario baseline must be the selected-month forecast,
    # not the Jan–Jul historical mean.  The required-staff denominator is
    # retained from governed workforce data.
    # -----------------------------------------------------------------------
    if kpi_id == "kpi_001" and baseline is not None and forecast is not None:
        forecast_pct = forecast["value"]
        if forecast_pct is not None and baseline.baseline_required_staff is not None:
            # Derive forecast-consistent available staff
            forecast_available = (forecast_pct / 100.0) * baseline.baseline_required_staff
            baseline.baseline_staffing_coverage_pct = forecast_pct
            baseline.baseline_available_staff = forecast_available
            baseline.baseline_kpi_value = forecast_pct
            baseline.baseline_reference_date = f"{GOVERNED_ACTUAL_YEAR}-{forecast_month:02d}-01"
            # Update state so UI and handoff are consistent
            state["baseline_value"] = forecast_pct
            state["baseline_date"] = baseline.baseline_reference_date

    # Interventions
    interventions = load_interventions_for_kpi(kpi_id)
    state["interventions"] = interventions
    selected_intervention = interventions[interventions["intervention_id"] == intervention_id]
    state["intervention_name"] = (
        str(selected_intervention.iloc[0]["intervention_name"]).strip()
        if not selected_intervention.empty else "Unknown"
    )

    # Comparator profiles
    template_id = _KPI_TO_SCENARIO_TEMPLATE.get(kpi_id, "")
    profiles = get_comparator_profiles(template_id)
    state["comparator_profiles"] = profiles

    # Run scenarios for each comparator
    scenario_results: List[Optional[ScenarioResult]] = []
    financial_results: List[Optional[Dict[str, Any]]] = []
    scenario_family = _KPI_TO_SCENARIO_FAMILY.get(kpi_id, "")

    for profile in profiles:
        # Inject selected-month calendar days for staffing duration scaling
        if kpi_id == "kpi_001":
            try:
                days_in_month = calendar.monthrange(GOVERNED_ACTUAL_YEAR, forecast_month)[1]
            except (ValueError, TypeError):
                days_in_month = 30
            profile["assumptions"]["days_in_selected_month"] = days_in_month

        result = run_scenario(baseline, kpi_id, profile) if baseline else None
        scenario_results.append(result)

        if result is not None:
            fin = calculate_financial_impact(
                result, profile["assumptions"], scenario_family, profile["comparator_type"]
            )
            financial_results.append(fin)
        else:
            financial_results.append(None)

    state["scenario_results"] = scenario_results
    state["financial_results"] = financial_results

    # Default selected comparator = Expected (index 1 if available, else 0)
    expected_idx = next(
        (i for i, p in enumerate(profiles) if p["comparator_type"] == "Expected"), 0
    )
    state["selected_comparator_index"] = expected_idx

    # Trade-off & displacement
    valid_results = [r for r in scenario_results if r is not None]
    tradeoff_text, displacement_text = build_tradeoff_and_displacement(valid_results)
    state["tradeoff_text"] = tradeoff_text
    state["displacement_text"] = displacement_text

    # Management takeaway (for default selected comparator)
    selected_result = scenario_results[expected_idx] if expected_idx < len(scenario_results) else None
    selected_financial = financial_results[expected_idx] if expected_idx < len(financial_results) else None
    selected_profile = profiles[expected_idx] if expected_idx < len(profiles) else None
    comparator_type = selected_profile["comparator_type"] if selected_profile else "Expected"

    state["management_takeaway"] = build_management_takeaway(
        kpi_id=kpi_id,
        kpi_name=state["kpi_name"],
        baseline_value=state["baseline_value"],
        baseline_unit=state["baseline_unit"],
        forecast_value=state["forecast_value"],
        forecast_unit=state["forecast_unit"],
        scenario_result=selected_result,
        comparator_type=comparator_type,
        intervention_name=state["intervention_name"],
        financial=selected_financial,
    )

    # Status for baseline and forecast
    if baseline and baseline.baseline_kpi_value is not None:
        status_text, _ = _get_status_for_value(kpi_id, baseline.baseline_kpi_value)
        state["baseline_status"] = status_text
    else:
        state["baseline_status"] = "Not Assessable"

    if forecast and forecast["value"] is not None:
        status_text, _ = _get_status_for_value(kpi_id, forecast["value"])
        state["forecast_status"] = status_text
    else:
        state["forecast_status"] = "Not Assessable"

    return state
