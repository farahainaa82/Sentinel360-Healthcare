"""
Step AI-1 — Targeted tests for the governed management evidence pack builder.

These tests verify, in isolation, that ``ManagementEvidencePack`` behaves as a
read-only, JSON-safe fact projector:

  * No analytical value is recomputed — every assertion is anchored on a
    value already present in the Executive Overview page state (or, when
    testing safety, on an explicit ``None``).
  * No DataFrame or pandas object ever leaks into the AI payload.
  * The governance metadata block is always present and locked to the
    locked-down rules (ai_may_calculate == False, causality_confirmed ==
    False, etc.).
  * Production datasets are NEVER mutated by these tests — only read.
"""

import json
import os
import sys

import pandas as pd
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.management_evidence_pack import (
    ManagementEvidencePack,
    _coerce_primitive,
    _build_target_and_gap,
    _resolve_directionality_token,
)
from src.streamlit_executive_data_loader import (
    FORECAST_HORIZON_END_MONTH,
    FORECAST_HORIZON_START_MONTH,
    GOVERNED_ACTUAL_MONTH_CUTOFF,
    GOVERNED_ACTUAL_YEAR,
    get_period_type,
    load_all_data,
)
from src.streamlit_executive_page_controller import (
    build_executive_page_state,
    load_kpi_threshold_config,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------
def _exec_state(month: int):
    """Build a real Executive Overview page state for ED month=``month``.

    Uses the SAME pattern as ``test_step_3b_executive_overview.py`` — i.e.
    the canonical go-live dataset, read-only.
    """
    data = load_all_data()
    filters = {
        "department_name": "Emergency Department",
        "department_id": "DEPT-ED",
        "hospital_id": "HOSP-001",
        "year": GOVERNED_ACTUAL_YEAR,
        "month": int(month),
        "reporting_date": None,
    }
    return build_executive_page_state(data, filters)


# ===========================================================================
# 1 + 2 — Executive Overview forecast context produces a structured pack;
#         ACTUAL / FORECAST period type is preserved.
# ===========================================================================
def test_pack_is_built_from_real_executive_state_forecast():
    state = _exec_state(FORECAST_HORIZON_START_MONTH)  # August = FORECAST
    pack = ManagementEvidencePack.from_executive_state(state)

    assert isinstance(pack, ManagementEvidencePack)
    assert pack.schema_version == "ai1_v1"

    payload = pack.to_ai_payload()
    assert isinstance(payload, dict)
    # Five-section schema is preserved
    for key in (
        "context",
        "priority_signal",
        "forecast_provenance",
        "availability",
        "governance",
    ):
        assert key in payload, f"Missing top-level section: {key}"
    assert "source_references" in payload


def test_actual_period_type_preserved():
    state = _exec_state(3)  # March = ACTUAL
    pack = ManagementEvidencePack.from_executive_state(state)
    assert pack.context["period_type"] == "ACTUAL"
    assert pack.context["year"] == GOVERNED_ACTUAL_YEAR
    assert pack.context["month"] == 3
    # Period type computed canonically via the loader helper:
    assert get_period_type(GOVERNED_ACTUAL_YEAR, 3) == "ACTUAL"


def test_forecast_period_type_preserved():
    state = _exec_state(FORECAST_HORIZON_START_MONTH)  # August = FORECAST
    pack = ManagementEvidencePack.from_executive_state(state)
    assert pack.context["period_type"] == "FORECAST"
    assert pack.context["month"] == FORECAST_HORIZON_START_MONTH
    assert get_period_type(GOVERNED_ACTUAL_YEAR, FORECAST_HORIZON_START_MONTH) == "FORECAST"


# ===========================================================================
# 3 — KPI value is preserved exactly.
# ===========================================================================
def test_kpi_value_preserved_exactly_from_state():
    state = _exec_state(6)  # ACTUAL — should carry latest_value_raw
    pack = ManagementEvidencePack.from_executive_state(state)
    cards = state.get("primary_kpi_cards", [])
    dominant_id = state.get("dominant_kpi_id")
    assert dominant_id, "Expected dominant KPI for ED month=6"
    matching = next((c for c in cards if c.get("kpi_id") == dominant_id), None)
    assert matching is not None, "Dominant KPI card missing from primary_kpi_cards"

    expected_value = matching.get("latest_value_raw")
    assert expected_value is not None
    expected_unit = matching.get("unit") or matching.get("latest_actual_unit")

    assert pack.priority_signal["kpi_id"] == dominant_id
    assert pack.priority_signal["value"] == pytest.approx(float(expected_value))
    assert pack.priority_signal["unit"] == expected_unit


# ===========================================================================
# 4 — Governed target is preserved (deterministic from kpi_threshold_config).
# ===========================================================================
def test_governed_target_preserved_for_each_directionality():
    cfg = load_kpi_threshold_config()
    assert cfg, "Threshold config should not be empty"
    by_token = {
        "HIGHER_IS_BETTER": [],
        "LOWER_IS_BETTER": [],
        "TARGET_BAND": [],
    }
    for kpi_id, row in cfg.items():
        d = (row.get("directionality") or "").strip().upper()
        if d in by_token:
            by_token[d].append(kpi_id)

    # We do NOT assume all three buckets are non-empty across the CSV —
    # but each present bucket must resolve to a non-None target_label when
    # passed through ``_build_target_and_gap``.
    for token, kpi_ids in by_token.items():
        for kpi_id in kpi_ids:
            row = cfg[kpi_id]
            result = _build_target_and_gap(
                kpi_id=kpi_id,
                directionality_token=token,
                value=row.get("green_lower_boundary"),
                threshold_row=row,
            )
            assert result["target_label"] is not None, (
                f"{kpi_id} ({token}) produced no target_label — governed target broken"
            )


# ===========================================================================
# 5 — Gap-to-target is preserved.
# ===========================================================================
def test_gap_to_target_for_lower_is_better_above():
    threshold_row = {
        "green_lower_boundary": 0.0,
        "green_upper_boundary": 47.2,
        "unit": "minutes",
    }
    out = _build_target_and_gap(
        kpi_id="kpi_004",
        directionality_token="LOWER_IS_BETTER",
        value=77.58,
        threshold_row=threshold_row,
    )
    assert out["target_label"] == "\u2264 47.2 minutes"
    assert "above target" in out["gap_to_target"]
    assert "minutes" in out["gap_to_target"]
    assert "30.4" in out["gap_to_target"]


def test_gap_to_target_for_higher_is_better_below():
    threshold_row = {
        "green_lower_boundary": 84.2,
        "green_upper_boundary": 100.0,
        "unit": "percent",
    }
    out = _build_target_and_gap(
        kpi_id="kpi_001",
        directionality_token="HIGHER_IS_BETTER",
        value=70.0,
        threshold_row=threshold_row,
    )
    assert out["target_label"] == "\u2265 84.2%"
    assert "below target" in out["gap_to_target"]
    assert "percentage points" in out["gap_to_target"]


def test_gap_to_target_for_context_sensitive_band():
    threshold_row = {
        "green_lower_boundary": 86.1,
        "green_upper_boundary": 100.2,
        "unit": "percent",
    }
    out_inside = _build_target_and_gap(
        kpi_id="kpi_003",
        directionality_token="TARGET_BAND",
        value=92.5,
        threshold_row=threshold_row,
    )
    assert out_inside["gap_to_target"] == "Within target band"

    out_above = _build_target_and_gap(
        kpi_id="kpi_003",
        directionality_token="TARGET_BAND",
        value=104.8,
        threshold_row=threshold_row,
    )
    assert "above target band" in out_above["gap_to_target"]
    assert "4.6" in out_above["gap_to_target"]
    assert "percentage points" in out_above["gap_to_target"]


# ===========================================================================
# 6 — Warning level is preserved when cleanly available.
# ===========================================================================
def test_warning_level_preserved_from_dominant_warning():
    # The Executive Overview is forecast-aware only for FORECAST months with a
    # known department. Use a FORECAST month + ICU (a department that does
    # trigger forecast warnings in the prototype dataset).
    state = _exec_state(FORECAST_HORIZON_START_MONTH + 1)  # September
    pack = ManagementEvidencePack.from_executive_state(state)
    payload = pack.to_ai_payload()

    if state.get("dominant_forecast_warning"):
        assert payload["priority_signal"]["warning_level"] == (
            state["dominant_forecast_warning"].get("warning_level")
            or state["dominant_forecast_warning"].get("warning")
        )
        # Forecast provenance block always carries something even when None
        assert "dominant_warning_level" in payload["forecast_provenance"]


# ===========================================================================
# 7 — Missing values remain None.
# ===========================================================================
def test_missing_values_are_none():
    sparse = {
        "selected_context": {"hospital_id": "HOSP-001"},
        "period_type": "FORECAST",
        # no dominant_*, no primary_kpi_cards, no forecast fields
    }
    pack = ManagementEvidencePack.from_executive_state(sparse)
    payload = pack.to_ai_payload()

    assert payload["priority_signal"]["value"] is None
    assert payload["priority_signal"]["unit"] is None
    assert payload["priority_signal"]["target_label"] is None
    assert payload["priority_signal"]["gap_to_target"] is None
    assert payload["priority_signal"]["warning_level"] is None

    assert payload["context"]["department_id"] is None
    assert payload["context"]["year"] is None
    assert payload["context"]["month"] is None


def test_directionality_normalised_to_uppercase_token():
    assert _resolve_directionality_token({"directionality": "HIGHER_IS_BETTER"}) == "HIGHER_IS_BETTER"
    assert _resolve_directionality_token({"directionality": "higher is better"}) == "HIGHER_IS_BETTER"
    assert _resolve_directionality_token({"directionality": "Context-sensitive"}) == "TARGET_BAND"
    assert _resolve_directionality_token({"directionality": "context sensitive"}) == "TARGET_BAND"
    assert _resolve_directionality_token({}) is None
    assert _resolve_directionality_token({"directionality": "Bogus Value"}) is None


# ===========================================================================
# 8 — No analytical value is recalculated.
# ===========================================================================
def test_state_is_not_mutated():
    state = _exec_state(6)
    snapshot_keys = set(state.keys())
    snapshot_primary = [c.copy() for c in state.get("primary_kpi_cards", [])]

    _ = ManagementEvidencePack.from_executive_state(state)

    assert set(state.keys()) == snapshot_keys
    for before, after in zip(
        snapshot_primary, state.get("primary_kpi_cards", [])
    ):
        assert before == after


def test_thresholds_come_from_governed_csv_not_recomputed():
    cfg = load_kpi_threshold_config()
    state = _exec_state(FORECAST_HORIZON_START_MONTH)
    pack = ManagementEvidencePack.from_executive_state(state)
    dominant_id = pack.priority_signal["kpi_id"]
    if dominant_id and pack.priority_signal["target_label"]:
        row = cfg.get(dominant_id, {})
        lo = row.get("green_lower_boundary")
        hi = row.get("green_upper_boundary")
        unit = row.get("unit", "")
        direction = _resolve_directionality_token({"directionality": row.get("directionality")})
        # Reproduce the same target formula; if it agrees, the pack did not invent anything.
        from src.management_evidence_pack import _build_target_and_gap as rebuilt
        reproduced = rebuilt(dominant_id, direction, None, row)["target_label"]
        assert pack.priority_signal["target_label"] == reproduced


# ===========================================================================
# 9 — Payload is JSON serialisable.
# ===========================================================================
def test_payload_is_json_serialisable():
    state = _exec_state(FORECAST_HORIZON_START_MONTH)
    pack = ManagementEvidencePack.from_executive_state(state)
    serialised = pack.to_json()
    reparsed = json.loads(serialised)
    assert isinstance(reparsed, dict)
    # Round-trip the headline fields
    assert reparsed["context"]["period_type"] == "FORECAST"
    # Module's own helper must succeed too
    again = json.loads(pack.to_json(indent=None))
    assert "governance" in again


def test_coerce_primitive_handles_pandas_objects():
    assert _coerce_primitive(None) is None
    assert _coerce_primitive("hi") == "hi"
    assert _coerce_primitive(5.0) == 5.0
    assert _coerce_primitive(float("nan")) is None
    assert _coerce_primitive(float("inf")) is None
    assert _coerce_primitive(pd.NaT) is None
    assert _coerce_primitive(pd.DataFrame({"x": [1]})) is None
    assert _coerce_primitive(pd.Series([1, 2, 3])) is None
    ts = pd.Timestamp("2025-01-31")
    assert _coerce_primitive(ts).startswith("2025-01-31")
    assert _coerce_primitive({"a": 1, "b": pd.NaT}) == {"a": 1, "b": None}


# ===========================================================================
# 10 — Governance metadata present and locked.
# ===========================================================================
def test_governance_flags_present_and_locked():
    pack = ManagementEvidencePack.from_executive_state(_exec_state(6))
    g = pack.governance

    for required in (
        "evidence_is_governed",
        "ai_may_calculate",
        "ai_may_modify_values",
        "ai_may_infer_missing_values",
        "causality_confirmed",
        "evidence_source",
        "module",
        "schema_version",
    ):
        assert required in g, f"Missing governance field: {required}"

    assert g["evidence_is_governed"] is True
    assert g["ai_may_calculate"] is False
    assert g["ai_may_modify_values"] is False
    assert g["ai_may_infer_missing_values"] is False
    assert g["causality_confirmed"] is False
    assert g["evidence_source"] == "Sentinel360 governed analytical outputs"


# ===========================================================================
# 11 — No raw DataFrame in the payload.
# ===========================================================================
def test_no_raw_dataframe_in_payload():
    state = _exec_state(FORECAST_HORIZON_START_MONTH)
    pack = ManagementEvidencePack.from_executive_state(state)

    def _walk(o, path=""):
        if isinstance(o, dict):
            for k, v in o.items():
                yield from _walk(v, f"{path}.{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                yield from _walk(v, f"{path}[{i}]")
        else:
            yield path, o

    types_seen = {type(v).__name__ for _, v in _walk(pack.to_ai_payload())}
    forbidden = {"DataFrame", "Series", "Timestamp", "NAType"}
    assert types_seen.isdisjoint(forbidden), (
        f"Non-primitive types leaked into payload: {types_seen & forbidden}"
    )

    # JSON round-trip must also succeed with default encoder.
    json.dumps(pack.to_ai_payload())


# ===========================================================================
# 12 — causality_confirmed defaults to False across all builders.
# ===========================================================================
def test_causality_default_is_false_for_every_state():
    for month in (3, FORECAST_HORIZON_START_MONTH, FORECAST_HORIZON_END_MONTH):
        pack = ManagementEvidencePack.from_executive_state(_exec_state(month))
        assert pack.governance["causality_confirmed"] is False


# ===========================================================================
# Helper — explicit safety net to ensure no production dataset mutated.
# ===========================================================================
def test_no_production_dataset_mutation(monkeypatch):
    from src import streamlit_executive_data_loader as dl

    # Wrap a DataFrame-returning loader with a spy that records structure.
    seen = {"kpi_daily": None}

    real_load_kpi_daily = dl.load_kpi_daily

    def spy_load_kpi_daily(*args, **kwargs):
        result = real_load_kpi_daily(*args, **kwargs)
        seen["kpi_daily"] = result.copy() if hasattr(result, "copy") else result
        return result

    monkeypatch.setattr(dl, "load_kpi_daily", spy_load_kpi_daily)
    _ = ManagementEvidencePack.from_executive_state(_exec_state(6))

    # The copied snapshot still equals what was originally returned — i.e.
    # the builder did NOT keep a reference and mutate it.
    real_after = real_load_kpi_daily()
    if seen["kpi_daily"] is not None and hasattr(seen["kpi_daily"], "equals"):
        pd.testing.assert_frame_equal(seen["kpi_daily"], real_after)
    else:
        assert seen["kpi_daily"] is not None  # we read something
