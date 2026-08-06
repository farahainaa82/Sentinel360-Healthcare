"""
Step AI-1: Governed management evidence pack builder.

This module assembles a small, structured, JSON-serialisable fact object from
EXISTING Sentinel360 analytical outputs (the state dict produced by
``build_executive_page_state`` in ``src.streamlit_executive_page_controller``,
plus the governed threshold config and governed period constants).

Hard rules:

* NO analytical value is recomputed. Every field is read from a governed,
  already-evaluated authoritative source and merely projected to JSON-safe
  primitives.
* If a value is unavailable, the corresponding field is set to ``None``.
  The module NEVER substitutes zeros, neighbouring-month values, generic
  "Moderate", or any fabricated wording.
* No LLM is called. No UI is wired. This step is fact assembly only.
* Period type, hospital, department, year, month, data cut-off, dominant
  KPI value, unit, governed target, gap-to-target, status, warning level,
  forecast status, and (when cleanly available) forecast method / quality /
  horizon are all consumed verbatim from governing Sentinel360 objects.
* The dominant KPI's value is selected to match what the page actually
  displays:
    - period_type == "ACTUAL"     -> card["latest_value"] / latest_value_raw
    - period_type == "FORECAST"   -> card["point_forecast"] (fallback latest_value)
* The eventual AI payload is a dict of primitives; ``json.dumps`` must
  succeed without a default encoder.
"""

from __future__ import annotations

import calendar
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd

from src.streamlit_executive_data_loader import (
    FORECAST_HORIZON_END_MONTH,
    FORECAST_HORIZON_START_MONTH,
    GOVERNED_ACTUAL_MONTH_CUTOFF,
    GOVERNED_ACTUAL_YEAR,
    get_period_type,
)
from src.streamlit_executive_page_controller import load_kpi_threshold_config


_MONTH_ABBR = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


# ---------------------------------------------------------------------------
# Primitive coercion — guarantees JSON-serialisability without leaking
# pandas / numpy objects into the AI payload.
# ---------------------------------------------------------------------------
def _coerce_primitive(value: Any) -> Any:
    """Project an arbitrary value to a JSON-safe primitive.

    * ``None``  -> ``None``
    * ``str / int / float / bool`` -> as-is (NaN / inf coerced to None)
    * ``pandas.Timestamp``          -> ISO 8601 string or None
    * ``pandas.NaT`` / NaN values   -> ``None``
    * ``dict`` / ``list`` / ``tuple`` -> recursive coercion
    * anything else                  -> ``str(value)`` as last-resort
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (str, int)):
        return value
    if isinstance(value, float):
        if pd.isna(value) or value != value or value in (float("inf"), float("-inf")):
            return None
        return value
    # pandas.Timestamp / datetime
    if isinstance(value, pd.Timestamp):
        try:
            if pd.isna(value):
                return None
            return value.isoformat()
        except Exception:
            return None
    # dict / list / tuple — recurse
    if isinstance(value, dict):
        return {str(_coerce_primitive(k)): _coerce_primitive(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_coerce_primitive(v) for v in value]
    # dataframe / series / numpy scalars — never leak into the AI payload
    if isinstance(value, (pd.DataFrame, pd.Series)):
        return None
    # last resort — string form, never raw object
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return str(value)


# ---------------------------------------------------------------------------
# Target / gap helpers — use the SAME Green-band rule the page already uses.
# These are facts-of-config (the target numbers come from governed CSV),
# so reporting them here does NOT constitute analytical inference.
# ---------------------------------------------------------------------------
def _gap_unit_word(unit: str) -> str:
    u = (unit or "").strip().lower()
    if u == "percent":
        return "percentage points"
    if u == "minutes":
        return "minutes"
    if u == "likert":
        return "Likert points"
    if u in ("complaint", "encounter"):
        return "per 1,000 encounters"
    return ""


def _build_target_and_gap(
    kpi_id: Optional[str],
    directionality_token: str,
    value: Optional[float],
    threshold_row: Optional[Dict[str, Any]],
) -> Dict[str, Optional[str]]:
    """Return ``{target_label, gap_to_target}`` from governed threshold row.

    ``directionality_token`` is the loader-normalised uppercase token —
    ``HIGHER_IS_BETTER``, ``LOWER_IS_BETTER``, or ``TARGET_BAND``.
    """
    if not kpi_id or not isinstance(threshold_row, dict):
        return {"target_label": None, "gap_to_target": None}

    lo = threshold_row.get("green_lower_boundary")
    hi = threshold_row.get("green_upper_boundary")
    unit = (threshold_row.get("unit") or "").strip()

    target_label: Optional[str] = None
    if directionality_token == "HIGHER_IS_BETTER":
        if lo is None:
            return {"target_label": None, "gap_to_target": None}
        try:
            target_label = f"\u2265 {_format_value(lo, unit)}"
        except (TypeError, ValueError):
            return {"target_label": None, "gap_to_target": None}
    elif directionality_token == "LOWER_IS_BETTER":
        if hi is None:
            return {"target_label": None, "gap_to_target": None}
        try:
            target_label = f"\u2264 {_format_value(hi, unit)}"
        except (TypeError, ValueError):
            return {"target_label": None, "gap_to_target": None}
    elif directionality_token == "TARGET_BAND":
        if lo is None or hi is None:
            return {"target_label": None, "gap_to_target": None}
        try:
            target_label = f"{_format_value(lo, unit)} \u2013 {_format_value(hi, unit)}"
        except (TypeError, ValueError):
            return {"target_label": None, "gap_to_target": None}
    else:
        return {"target_label": None, "gap_to_target": None}

    if value is None:
        return {"target_label": target_label, "gap_to_target": None}

    try:
        fv = float(value)
    except (TypeError, ValueError):
        return {"target_label": target_label, "gap_to_target": None}

    unit_word = _gap_unit_word(unit)
    gap_unit = unit_word if unit_word else "points"

    gap_to_target: Optional[str] = None
    if directionality_token == "HIGHER_IS_BETTER":
        try:
            lo_f = float(lo)
        except (TypeError, ValueError):
            lo_f = None
        if lo_f is None:
            gap_to_target = None
        elif fv < lo_f:
            gap_to_target = f"{_format_value(lo_f - fv, unit)} {gap_unit} below target"
        else:
            gap_to_target = "On target"
    elif directionality_token == "LOWER_IS_BETTER":
        try:
            hi_f = float(hi)
        except (TypeError, ValueError):
            hi_f = None
        if hi_f is None:
            gap_to_target = None
        elif fv > hi_f:
            gap_to_target = f"{_format_value(fv - hi_f, unit)} {gap_unit} above target"
        else:
            gap_to_target = "On target"
    elif directionality_token == "TARGET_BAND":
        try:
            lo_f = float(lo)
            hi_f = float(hi)
        except (TypeError, ValueError):
            gap_to_target = None
        else:
            # Inclusive lower, exclusive upper — same rule the page uses
            if fv >= lo_f and fv < hi_f:
                gap_to_target = "Within target band"
            elif fv < lo_f:
                gap_to_target = f"{_format_value(lo_f - fv, unit)} {gap_unit} below target band"
            else:
                gap_to_target = f"{_format_value(fv - hi_f, unit)} {gap_unit} above target band"

    return {"target_label": target_label, "gap_to_target": gap_to_target}


def _format_value(value: Any, unit: str) -> str:
    """Format a numeric threshold value with its unit suffix.

    Delegates to ``format_unit_value`` from the page controller for the
    canonical unit-aware formatting already used by the Executive Overview,
    Decision & Call for Action, Risk & Alert, and Simulation Lab pages. This
    means the evidence pack's target strings are literally identical to
    what the page renders, by construction.
    """
    from src.streamlit_executive_page_controller import format_unit_value
    return format_unit_value(value, unit)


# ---------------------------------------------------------------------------
# Data cut-off label — derived only from existing governed constants.
# ---------------------------------------------------------------------------
def _data_cutoff_label() -> str:
    last_day = calendar.monthrange(GOVERNED_ACTUAL_YEAR, GOVERNED_ACTUAL_MONTH_CUTOFF)[1]
    month_abbr = _MONTH_ABBR[int(GOVERNED_ACTUAL_MONTH_CUTOFF) - 1].upper()
    return f"{last_day:02d} {month_abbr} {GOVERNED_ACTUAL_YEAR}"


# ---------------------------------------------------------------------------
# Main evidence pack dataclass
# ---------------------------------------------------------------------------
@dataclass
class ManagementEvidencePack:
    """Structured, read-only evidence object for the AI synthesis layer.

    All values are either consumed verbatim from existing Sentinel360
    analytical outputs or left as ``None`` when not exposed cleanly. No
    value is invented, inferred, or recomputed.
    """

    context: Dict[str, Any]
    priority_signal: Dict[str, Any]
    forecast_provenance: Dict[str, Any]
    availability: Dict[str, Any]
    governance: Dict[str, Any]
    source_references: Dict[str, str] = field(default_factory=dict)
    schema_version: str = "ai1_v1"

    # ------------------------------------------------------------------
    # Builders
    # ------------------------------------------------------------------
    @staticmethod
    def from_executive_state(state: Dict[str, Any]) -> "ManagementEvidencePack":
        """Build an Executive Overview evidence pack from a page state dict.

        ``state`` is the exact object returned by
        ``build_executive_page_state`` from
        ``src.streamlit_executive_page_controller``. The builder never
        mutates ``state``.
        """
        if not isinstance(state, dict):
            state = {}

        ctx_obj = state.get("selected_context") or {}
        if not isinstance(ctx_obj, dict):
            ctx_obj = {}

        hospital_id = ctx_obj.get("hospital_id")
        department_id = ctx_obj.get("department_id")
        year_raw = ctx_obj.get("selected_year")
        month_raw = ctx_obj.get("selected_month")

        try:
            year_val = int(year_raw) if year_raw is not None else None
        except (TypeError, ValueError):
            year_val = None
        try:
            month_val = int(month_raw) if month_raw is not None else None
        except (TypeError, ValueError):
            month_val = None

        # Period type — prefer the one the controller has already computed.
        period_type_raw = state.get("period_type")
        if isinstance(period_type_raw, str) and period_type_raw in ("ACTUAL", "FORECAST"):
            period_type: Optional[str] = period_type_raw
        elif year_val is not None and month_val is not None:
            try:
                period_type = get_period_type(year_val, month_val)
            except Exception:
                period_type = None
        else:
            period_type = None

        context = {
            "hospital_id": _coerce_primitive(hospital_id),
            "hospital_name": _coerce_primitive(ctx_obj.get("hospital_name")),
            "department_id": _coerce_primitive(department_id),
            "department_name": _coerce_primitive(ctx_obj.get("department_name")),
            "year": _coerce_primitive(year_val),
            "month": _coerce_primitive(month_val),
            "month_label": (
                f"{_MONTH_ABBR[month_val - 1].upper()} {year_val}"
                if month_val is not None and year_val is not None
                else None
            ),
            "period_type": _coerce_primitive(period_type),
            "data_cutoff": _data_cutoff_label(),
            "forecast_horizon": (
                f"{_MONTH_ABBR[FORECAST_HORIZON_START_MONTH - 1].upper()}"
                f"\u2013{_MONTH_ABBR[FORECAST_HORIZON_END_MONTH - 1].upper()}"
                f" {GOVERNED_ACTUAL_YEAR}"
            ),
        }

        # ---- Priority signal (dominant KPI on the page) ----
        dominant_kpi_id = state.get("dominant_kpi_id")
        dominant_kpi_name = state.get("dominant_kpi_name")
        dominant_status = state.get("dominant_status")
        risk_tier = state.get("risk_tier")
        operational_status = state.get("operational_status")

        # Find the dominant card to harvest the values the page actually renders.
        priority_card = _find_dominant_card(state, dominant_kpi_id)

        priority_signal: Dict[str, Any] = {
            "kpi_id": _coerce_primitive(dominant_kpi_id),
            "kpi_name": _coerce_primitive(dominant_kpi_name),
            "value": None,
            "unit": None,
            "target_label": None,
            "gap_to_target": None,
            "status": _coerce_primitive(dominant_status),
            "warning_level": None,
            "forecast_status": None,
            "has_priority_signal": bool(dominant_kpi_id),
        }

        if isinstance(priority_card, dict):
            unit_raw = priority_card.get("unit") or priority_card.get("latest_actual_unit")
            threshold_status_text = priority_card.get("threshold_status")
            directionality_token = _resolve_directionality_token(priority_card)

            # Pick the numeric value to compare to target — exactly the one
            # the page renders for the selected period.
            if period_type == "FORECAST":
                raw_value = priority_card.get("point_forecast")
                if raw_value is None or (isinstance(raw_value, float) and pd.isna(raw_value)):
                    raw_value = priority_card.get("latest_value_raw")
                forecast_unavailable = bool(priority_card.get("forecast_unavailable")) or raw_value is None
            else:
                raw_value = priority_card.get("latest_value_raw")
                if raw_value is None or (isinstance(raw_value, float) and pd.isna(raw_value)):
                    raw_value = priority_card.get("point_forecast")
                forecast_unavailable = False

            try:
                raw_value_float = float(raw_value) if raw_value is not None else None
            except (TypeError, ValueError):
                raw_value_float = None
            if raw_value_float is not None and pd.isna(raw_value_float):
                raw_value_float = None

            threshold_row = _get_threshold_row(dominant_kpi_id)
            target_gap = _build_target_and_gap(
                kpi_id=dominant_kpi_id,
                directionality_token=directionality_token,
                value=raw_value_float,
                threshold_row=threshold_row,
            )

            priority_signal.update(
                {
                    "kpi_id": _coerce_primitive(priority_card.get("kpi_id") or dominant_kpi_id),
                    "kpi_name": _coerce_primitive(
                        priority_card.get("kpi_name") or dominant_kpi_name
                    ),
                    "value": raw_value_float if period_type == "ACTUAL" or forecast_unavailable is False else None,
                    "value_display": _coerce_primitive(priority_card.get("latest_value")),
                    "unit": _coerce_primitive(unit_raw),
                    "target_label": _coerce_primitive(target_gap.get("target_label")),
                    "gap_to_target": _coerce_primitive(target_gap.get("gap_to_target")),
                    "threshold_status": _coerce_primitive(threshold_status_text),
                    "border_colour": _coerce_primitive(priority_card.get("border_colour")),
                    "directionality": _coerce_primitive(directionality_token),
                    "has_priority_signal": True,
                }
            )

            # Forecast-context fields — only when cleanly available.
            warning_level = priority_card.get("warning_level")
            forecast_status = (
                priority_card.get("expected_status_change")
                or priority_card.get("forecast_status")
            )

            if period_type == "FORECAST" and not forecast_unavailable:
                priority_signal["warning_level"] = _coerce_primitive(warning_level)
                priority_signal["forecast_quality"] = _coerce_primitive(
                    priority_card.get("forecast_quality")
                )
                priority_signal["horizon_months_ahead"] = _coerce_primitive(
                    priority_card.get("horizon_months_ahead")
                )
                priority_signal["forecast_value"] = (
                    raw_value_float if raw_value_float is not None else None
                )
                priority_signal["forecast_indicative_range"] = (
                    _build_indicative_range(priority_card)
                    if priority_card.get("lower_bound") is not None
                    and priority_card.get("upper_bound") is not None
                    else None
                )
            elif period_type == "FORECAST" and forecast_unavailable:
                priority_signal["forecast_status"] = "Forecast not available for this combination"

            priority_signal["forecast_status"] = _coerce_primitive(forecast_status)

        # If no priority card found, leave priority_signal values at None.
        # Also propagate risk_tier / operational_status as supplementary facts.
        priority_signal["risk_tier"] = _coerce_primitive(risk_tier)
        priority_signal["operational_status"] = _coerce_primitive(operational_status)

        # ---- Forecast provenance ----
        forecast_capability = state.get("forecast_capability") or {}
        if not isinstance(forecast_capability, dict):
            forecast_capability = {}

        dominant_warning = state.get("dominant_forecast_warning") or {}
        if not isinstance(dominant_warning, dict):
            dominant_warning = {}

        method_df = state.get("forecast_method")
        method_row = _extract_method_row(
            method_df,
            kpi_id=dominant_kpi_id,
            hospital_id=hospital_id,
            department_id=department_id,
            year=year_val,
            month=month_val,
        )

        forecast_provenance = {
            "selected_method": _coerce_primitive(method_row.get("selected_method")),
            "forecast_quality": _coerce_primitive(method_row.get("forecast_quality"))
            or _coerce_primitive(forecast_capability.get("quality")),
            "horizon": _coerce_primitive(method_row.get("horizon"))
            or _coerce_primitive(forecast_capability.get("horizon")),
            "horizon_months_ahead": _coerce_primitive(
                priority_card.get("horizon_months_ahead") if isinstance(priority_card, dict) else None
            ),
            "dominant_warning_level": _coerce_primitive(
                dominant_warning.get("warning_level") or dominant_warning.get("warning")
            ),
            "forecast_capability_text": _coerce_primitive(
                forecast_capability.get("notice") or forecast_capability.get("text")
            ),
            "validation_mae": _coerce_primitive(method_row.get("validation_mae")),
        }

        # ---- Availability ----
        has_priority = bool(
            priority_signal.get("has_priority_signal") and priority_signal.get("kpi_id")
        )
        has_forecast = bool(
            period_type == "FORECAST"
            and priority_signal.get("forecast_value") is not None
        )
        availability = {
            "has_priority_signal": has_priority,
            "has_forecast": has_forecast,
            "period_type_available": _coerce_primitive(period_type) is not None,
            "kpi_value_available": _coerce_primitive(priority_signal.get("value")) is not None,
            "target_available": _coerce_primitive(priority_signal.get("target_label")) is not None,
            "warning_available": _coerce_primitive(priority_signal.get("warning_level")) is not None,
            "forecast_method_available": (
                forecast_provenance["selected_method"] is not None
            ),
        }

        # ---- Governance metadata ----
        governance = {
            "evidence_source": "Sentinel360 governed analytical outputs",
            "evidence_is_governed": True,
            "ai_may_calculate": False,
            "ai_may_modify_values": False,
            "ai_may_infer_missing_values": False,
            "causality_confirmed": False,
            "module": "src.management_evidence_pack",
            "schema_version": "ai1_v1",
            "scope": "executive_overview",
        }

        # ---- Source references (traceability only — no file paths) ----
        source_references = {
            "page_state": "build_executive_page_state (src.streamlit_executive_page_controller)",
            "kpi_cards": "_build_all_kpi_cards (src.streamlit_executive_page_controller)",
            "threshold_config": "config/kpi_threshold_config.csv (governed Green band only)",
            "period_governance": "GOVERNED_ACTUAL_* / FORECAST_HORIZON_* (src.streamlit_executive_data_loader)",
            "forecast_method": "outputs/forecasting/kpi_forecast_method_selection.csv",
        }

        return ManagementEvidencePack(
            context=context,
            priority_signal=priority_signal,
            forecast_provenance=forecast_provenance,
            availability=availability,
            governance=governance,
            source_references=source_references,
        )

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        """Project the evidence pack to a JSON-safe dictionary.

        This is the canonical payload shape for the future AI synthesis
        layer. The output must be directly serialisable by ``json.dumps``
        without any custom encoder.
        """
        raw = asdict(self)
        return _coerce_primitive(raw)  # type: ignore[arg-type]

    def to_ai_payload(self) -> Dict[str, Any]:
        """Convenience alias for ``to_dict()`` — the eventual LLM payload."""
        return self.to_dict()

    def to_json(self, indent: Optional[int] = 2) -> str:
        """Serialise the evidence pack to a JSON string.

        ``json.dumps`` will fail with a ``TypeError`` if any non-primitive
        value slips through. That failure is treated as a regression — the
        governance of this module is that no pandas / numpy / dataframe
        object can ever reach the AI payload.
        """
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _find_dominant_card(
    state: Dict[str, Any], dominant_kpi_id: Optional[str]
) -> Optional[Dict[str, Any]]:
    """Locate the page's card for the dominant KPI, in either card list."""
    if not dominant_kpi_id:
        return None
    for key in ("primary_kpi_cards", "all_kpi_cards"):
        cards = state.get(key)
        if isinstance(cards, list):
            for card in cards:
                if isinstance(card, dict) and card.get("kpi_id") == dominant_kpi_id:
                    return card
    return None


def _resolve_directionality_token(card: Dict[str, Any]) -> Optional[str]:
    """Map a card's directionality field to the loader-normalised uppercase
    token (``HIGHER_IS_BETTER`` / ``LOWER_IS_BETTER`` / ``TARGET_BAND``).

    Falls back to ``None`` when the field is missing or non-recognisable.
    Never returns a human-readable raw string as a "fact".
    """
    raw = card.get("directionality")
    if raw is None:
        raw = card.get("directionality_label")
    if not isinstance(raw, str):
        return None
    token = raw.strip().upper()
    if token in ("HIGHER_IS_BETTER", "LOWER_IS_BETTER", "TARGET_BAND"):
        return token
    # Tolerate the human-readable spellings the page sometimes passes.
    legacy_map = {
        "HIGHER IS BETTER": "HIGHER_IS_BETTER",
        "LOWER IS BETTER": "LOWER_IS_BETTER",
        "CONTEXT-SENSITIVE": "TARGET_BAND",
        "CONTEXT SENSITIVE": "TARGET_BAND",
    }
    return legacy_map.get(token)


def _get_threshold_row(kpi_id: Optional[str]) -> Optional[Dict[str, Any]]:
    """Return the threshold row dict for ``kpi_id`` from the governed CSV."""
    if not kpi_id:
        return None
    try:
        cfg = load_kpi_threshold_config()
    except Exception:
        return None
    if not isinstance(cfg, dict):
        return None
    row = cfg.get(kpi_id)
    return row if isinstance(row, dict) else None


def _build_indicative_range(card: Dict[str, Any]) -> Optional[str]:
    lo = card.get("lower_bound")
    hi = card.get("upper_bound")
    if lo is None or hi is None:
        return None
    unit = card.get("unit") or ""
    try:
        lo_f = float(lo)
        hi_f = float(hi)
    except (TypeError, ValueError):
        return None
    return f"{_format_value(lo_f, unit)} \u2013 {_format_value(hi_f, unit)}"


def _extract_method_row(
    method_df: Any,
    *,
    kpi_id: Optional[str],
    hospital_id: Optional[str],
    department_id: Optional[str],
    year: Optional[int],
    month: Optional[int],
) -> Dict[str, Any]:
    """Best-effort row extraction from the forecast method selection table.

    Returns ``{}`` if the table is unavailable or no matching row exists.
    No fabrication: if the row does not exist, fields are simply ``None``
    and the availability flag is set accordingly by the caller.
    """
    if not isinstance(method_df, pd.DataFrame) or method_df.empty:
        return {}
    if not kpi_id or "kpi_id" not in method_df.columns:
        return {}
    sub = method_df[method_df["kpi_id"] == kpi_id]
    if sub.empty:
        return {}

    # Try progressively looser filters to maximise hit rate.
    for scope in (
        _scope_kwargs(hospital_id, department_id, year, month),
        _scope_kwargs(department_id=department_id, year=year, month=month),
        _scope_kwargs(year=year, month=month),
        {},
    ):
        if "hospital" in sub.columns and "hospital" in scope:
            cand = sub[sub["hospital"] == scope["hospital"]]
            if not cand.empty:
                sub = cand
        if (
            "department_code" in sub.columns
            and "department_code" in scope
            and scope["department_code"] is not None
        ):
            cand = sub[sub["department_code"] == scope["department_code"]]
            if not cand.empty:
                sub = cand
        elif (
            "affected_department" in sub.columns
            and "department_code" in scope
            and scope["department_code"] is not None
        ):
            cand = sub[sub["affected_department"] == scope["department_code"]]
            if not cand.empty:
                sub = cand
        if "year" in sub.columns and "year" in scope:
            cand = sub[sub["year"] == scope["year"]]
            if not cand.empty:
                sub = cand
        if "month" in sub.columns and "month" in scope:
            cand = sub[sub["month"] == scope["month"]]
            if not cand.empty:
                sub = cand
        # If sub still has rows after scoping, use the first.
        if not sub.empty:
            row = sub.iloc[0].to_dict()
            return {
                "selected_method": row.get("selected_method"),
                "forecast_quality": row.get("forecast_quality"),
                "horizon": row.get("horizon"),
                "validation_mae": row.get("validation_mae"),
            }
    return {}


def _scope_kwargs(
    hospital_id: Optional[str] = None,
    department_id: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if hospital_id is not None:
        out["hospital"] = hospital_id
    if department_id is not None:
        out["department_code"] = department_id
    if year is not None:
        out["year"] = year
    if month is not None:
        out["month"] = month
    return out


__all__ = [
    "ManagementEvidencePack",
    "_coerce_primitive",
    "_build_target_and_gap",
    "_resolve_directionality_token",
]
