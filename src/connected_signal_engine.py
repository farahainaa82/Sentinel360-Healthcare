"""
Connected Signal Engine — Governed Historical KPI Association + Forecast Continuation.

Responsibilities:
  1. Load governed monthly actual KPI history.
  2. Filter strictly to actual periods (Jan–Jul 2025) for historical association.
  3. Compute Spearman rank correlation on aligned monthly series per config pair.
  4. Compare observed sign with expected_direction from config.
  5. Apply strict small-sample guardrails (n=7, |r| >= 0.80).
  6. Mark supported relationships and build directed chains.
  7. Evaluate forecast continuation for selected forecast month (Aug–Dec).
  8. Return JSON-safe structured result.

Governance:
  - No causality is claimed.
  - Forecast values are NEVER used to strengthen historical association.
  - Only actual data establishes the historical relationship.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import pandas as pd
from scipy.stats import spearmanr  # type: ignore[import-untyped]


# ---------------------------------------------------------------------------
# Governed paths & constants
# ---------------------------------------------------------------------------
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ACTUAL_HISTORY_PATH = os.path.join(
    _BASE_DIR, "outputs", "forecasting", "kpi_monthly_actual_history.csv"
)
_FORECAST_PATH = os.path.join(
    _BASE_DIR, "outputs", "forecasting", "analytical_kpi_monthly_forecast.csv"
)
_CONFIG_PATH = os.path.join(_BASE_DIR, "config", "connected_signal_config.csv")
_KPI_DEF_PATH = os.path.join(_BASE_DIR, "config", "kpi_definition_config.csv")

GOVERNED_ACTUAL_YEAR = 2025
GOVERNED_ACTUAL_MONTH_CUTOFF = 7

_MIN_OBSERVATIONS = 5
_STRICT_THRESHOLD = 0.80


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _load_csv(path: str) -> pd.DataFrame:
    if not os.path.isfile(path):
        return pd.DataFrame()
    return pd.read_csv(path, keep_default_na=False, na_values=[""])


def _load_config(path: Optional[str] = None) -> pd.DataFrame:
    cfg = _load_csv(path or _CONFIG_PATH)
    if cfg.empty:
        return cfg
    enabled = cfg.get("enabled", "True")
    if isinstance(enabled, pd.Series):
        enabled = enabled.astype(str).str.upper() == "TRUE"
    else:
        enabled = pd.Series([True] * len(cfg), index=cfg.index)
    return cfg[enabled].copy()


def _load_kpi_definitions(path: Optional[str] = None) -> pd.DataFrame:
    df = _load_csv(path or _KPI_DEF_PATH)
    if df.empty:
        return df
    return df[["kpi_id", "kpi_name", "performance_direction"]].drop_duplicates()


def _load_actual_history(
    hospital_id: str,
    department_id: str,
    year: int,
    end_month: int,
    path: Optional[str] = None,
) -> pd.DataFrame:
    df = _load_csv(path or _ACTUAL_HISTORY_PATH)
    if df.empty:
        return df
    for col in ["year", "month"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "monthly_actual_value" in df.columns:
        df["monthly_actual_value"] = pd.to_numeric(df["monthly_actual_value"], errors="coerce")
    mask = (
        (df["hospital"] == hospital_id)
        & (df["department"] == department_id)
        & (df["year"] == year)
        & (df["month"] <= end_month)
        & (df["month"] >= 1)
    )
    return df[mask].copy()


def _load_forecast(
    hospital_id: str,
    department_id: str,
    year: int,
    month: int,
    path: Optional[str] = None,
) -> pd.DataFrame:
    df = _load_csv(path or _FORECAST_PATH)
    if df.empty:
        return df
    for col in ["forecast_year", "forecast_month"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "point_forecast" in df.columns:
        df["point_forecast"] = pd.to_numeric(df["point_forecast"], errors="coerce")
    mask = (
        (df["hospital"] == hospital_id)
        & (df["department_code"] == department_id)
        & (df["forecast_year"] == year)
        & (df["forecast_month"] == month)
    )
    return df[mask].copy()


def _get_series(df: pd.DataFrame, kpi_id: str) -> pd.Series:
    sub = df[df["kpi_id"] == kpi_id].sort_values("month")
    return sub.set_index("month")["monthly_actual_value"].dropna()


def _compute_spearman(s1: pd.Series, s2: pd.Series) -> Optional[float]:
    aligned = pd.concat([s1, s2], axis=1).dropna()
    if aligned.empty or len(aligned) < _MIN_OBSERVATIONS:
        return None
    try:
        r, _ = spearmanr(aligned.iloc[:, 0], aligned.iloc[:, 1])
        return float(r) if r is not None else None
    except Exception:
        return None


def _observed_direction(r: float) -> str:
    return "POSITIVE" if r >= 0 else "INVERSE"


def _direction_matches(expected: str, observed: str) -> bool:
    return expected.upper() == observed.upper()


def _strength_label(r: float, n: int) -> str:
    if n < _MIN_OBSERVATIONS:
        return "INSUFFICIENT EVIDENCE"
    ar = abs(r)
    if ar >= _STRICT_THRESHOLD:
        return "STRONG OBSERVED PATTERN"
    return "NOT_SUPPORTED"


def _supported(r: Optional[float], expected: str, n: int) -> bool:
    if r is None or n < _MIN_OBSERVATIONS:
        return False
    if abs(r) < _STRICT_THRESHOLD:
        return False
    return _direction_matches(expected, _observed_direction(r))


def _historical_trend_direction(series: pd.Series) -> str:
    """Return UP, DOWN, or FLAT based on first vs last actual value in the series."""
    if series.empty or len(series) < 2:
        return "FLAT"
    first = series.iloc[0]
    last = series.iloc[-1]
    if pd.isna(first) or pd.isna(last):
        return "FLAT"
    if last > first:
        return "UP"
    if last < first:
        return "DOWN"
    return "FLAT"


def _forecast_direction(latest_actual: float, forecast_value: float) -> str:
    if pd.isna(latest_actual) or pd.isna(forecast_value):
        return "FLAT"
    if forecast_value > latest_actual:
        return "UP"
    if forecast_value < latest_actual:
        return "DOWN"
    return "FLAT"


def _arrow(direction: str) -> str:
    """KPI trend icon -- large, crisp, inline SVG.

    Renders a 20 x 20 px geometric shape inside a 22 x 22 px flex
    container so the icon is visually strong (≥ 20 px) yet still
    executive-grade.  Three semantic variants:

      * ``s360-cs-trend-up``   -- UP   : green solid triangle (increase)
      * ``s360-cs-trend-down`` -- DOWN : red   solid triangle (decrease)
      * ``s360-cs-trend-flat`` -- FLAT : slate rounded bar    (stable)

    The icon is right-aligned against the KPI label by the row layout.
    It must remain visually distinct from the vertical flow connector
    arrow used between KPI rows in the chain (which uses its own inline
    SVG with classes ``s360-cs-flow-arrow`` / ``s360-cs-flow-arrow-svg``).
    """
    _common = (
        'display:inline-flex;align-items:center;justify-content:center;'
        'width:22px;height:22px;flex-shrink:0;vertical-align:middle;'
    )
    if direction == "UP":
        svg = (
            '<svg width="20" height="20" viewBox="0 0 20 20" '
            'xmlns="http://www.w3.org/2000/svg" focusable="false" '
            'aria-hidden="true">'
            '<polygon points="10,3 17.2,15.6 2.8,15.6" fill="#2F855A"/>'
            '</svg>'
        )
        return (
            f'<span class="s360-cs-trend-icon s360-cs-trend-up" '
            f'style="{_common}" aria-label="increase" '
            f'title="increasing">{svg}</span>'
        )
    if direction == "DOWN":
        svg = (
            '<svg width="20" height="20" viewBox="0 0 20 20" '
            'xmlns="http://www.w3.org/2000/svg" focusable="false" '
            'aria-hidden="true">'
            '<polygon points="2.8,4.4 17.2,4.4 10,17" fill="#C53030"/>'
            '</svg>'
        )
        return (
            f'<span class="s360-cs-trend-icon s360-cs-trend-down" '
            f'style="{_common}" aria-label="decrease" '
            f'title="decreasing">{svg}</span>'
        )
    svg = (
        '<svg width="20" height="20" viewBox="0 0 20 20" '
        'xmlns="http://www.w3.org/2000/svg" focusable="false" '
        'aria-hidden="true">'
        '<rect x="3" y="8.5" width="14" height="3" rx="1.5" '
        'fill="#4A6A99"/>'
        '</svg>'
    )
    return (
        f'<span class="s360-cs-trend-icon s360-cs-trend-flat" '
        f'style="{_common}" aria-label="unchanged" '
        f'title="stable">{svg}</span>'
    )


# ---------------------------------------------------------------------------
# Chain building
# ---------------------------------------------------------------------------
def _build_chains(
    supported_edges: List[Dict[str, Any]],
    actual_series: Dict[str, pd.Series],
    kpi_name_map: Dict[str, str],
) -> List[Dict[str, Any]]:
    """Build all simple directed paths of length >= 2 edges (>= 3 nodes).
    Only include paths where every consecutive edge is individually supported.
    """
    if not supported_edges:
        return []

    # Build adjacency list
    adj: Dict[str, List[str]] = {}
    edge_map: Dict[tuple, Dict[str, Any]] = {}
    for e in supported_edges:
        src = e["from_kpi_id"]
        tgt = e["to_kpi_id"]
        adj.setdefault(src, []).append(tgt)
        edge_map[(src, tgt)] = e

    chains: List[List[str]] = []

    def _dfs(node: str, path: List[str]) -> None:
        if len(path) >= 3:
            chains.append(path.copy())
        if node not in adj:
            return
        for nxt in adj[node]:
            if nxt in path:
                continue
            path.append(nxt)
            _dfs(nxt, path)
            path.pop()

    for start in adj:
        _dfs(start, [start])

    # Remove duplicate chains (same node sequence)
    seen: set = set()
    unique_chains: List[List[str]] = []
    for c in chains:
        key = tuple(c)
        if key not in seen:
            seen.add(key)
            unique_chains.append(c)

    # Build chain objects with trend directions
    result: List[Dict[str, Any]] = []
    for chain in unique_chains:
        edges_in_chain: List[Dict[str, Any]] = []
        total_abs_r = 0.0
        edge_count = 0
        for i in range(len(chain) - 1):
            e = edge_map[(chain[i], chain[i + 1])]
            edges_in_chain.append(e)
            r = e.get("association_value")
            if r is not None:
                total_abs_r += abs(r)
                edge_count += 1
        avg_abs_r = total_abs_r / edge_count if edge_count else 0.0

        # Compute trend direction for each KPI in the chain
        trend_directions = {}
        for kpi_id in chain:
            s = actual_series.get(kpi_id)
            trend_directions[kpi_id] = _historical_trend_direction(s) if s is not None else "FLAT"

        result.append(
            {
                "chain_kpi_ids": chain,
                "chain_kpi_names": [kpi_name_map.get(k, k) for k in chain],
                "trend_directions": trend_directions,
                "edges": edges_in_chain,
                "average_abs_r": avg_abs_r,
                "depth": len(chain) - 1,
            }
        )

    # Sort by depth desc, then avg_abs_r desc, then config order implicitly via edge order
    result.sort(key=lambda x: (-x["depth"], -x["average_abs_r"]))
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def run_connected_signal(
    hospital_id: str,
    department_id: str,
    selected_year: int,
    selected_month: int,
    *,
    actual_history_path: Optional[str] = None,
    forecast_path: Optional[str] = None,
    config_path: Optional[str] = None,
    kpi_definition_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the full Connected Signal pipeline.

    Returns a JSON-safe dict with relationships, chains, and forecast continuation.
    """
    # Determine historical window
    is_forecast_period = selected_month > GOVERNED_ACTUAL_MONTH_CUTOFF
    if is_forecast_period:
        hist_end_month = GOVERNED_ACTUAL_MONTH_CUTOFF
    else:
        hist_end_month = selected_month

    # Load data
    cfg = _load_config(config_path)
    kpi_defs = _load_kpi_definitions(kpi_definition_path)
    actual_df = _load_actual_history(
        hospital_id, department_id, selected_year, hist_end_month, actual_history_path
    )
    forecast_df = _load_forecast(
        hospital_id, department_id, selected_year, selected_month, forecast_path
    )

    # Build KPI name lookup
    kpi_name_map: Dict[str, str] = {}
    perf_dir_map: Dict[str, str] = {}
    if not kpi_defs.empty:
        kpi_name_map = dict(zip(kpi_defs["kpi_id"], kpi_defs["kpi_name"]))
        perf_dir_map = dict(zip(kpi_defs["kpi_id"], kpi_defs["performance_direction"]))

    # Build actual series per KPI
    actual_series: Dict[str, pd.Series] = {}
    if not actual_df.empty:
        for kpi_id in actual_df["kpi_id"].unique():
            actual_series[kpi_id] = _get_series(actual_df, kpi_id)

    relationships: List[Dict[str, Any]] = []
    supported_edges: List[Dict[str, Any]] = []

    for _, row in cfg.iterrows():
        rel_id = row["relationship_id"]
        from_id = row["from_kpi_id"]
        to_id = row["to_kpi_id"]
        expected = row["expected_direction"]

        s1 = actual_series.get(from_id)
        s2 = actual_series.get(to_id)
        if s1 is None or s2 is None:
            continue

        aligned = pd.concat([s1, s2], axis=1).dropna()
        n = len(aligned)
        r = _compute_spearman(s1, s2)
        obs_dir = _observed_direction(r) if r is not None else "UNKNOWN"
        sup = _supported(r, expected, n)
        strength = _strength_label(r if r is not None else 0.0, n)

        rel = {
            "relationship_id": rel_id,
            "from_kpi_id": from_id,
            "from_kpi_name": kpi_name_map.get(from_id, from_id),
            "to_kpi_id": to_id,
            "to_kpi_name": kpi_name_map.get(to_id, to_id),
            "expected_direction": expected,
            "observed_direction": obs_dir,
            "association_value": round(r, 4) if r is not None else None,
            "observation_count": n,
            "strength_label": strength,
            "supported": sup,
        }
        relationships.append(rel)
        if sup:
            supported_edges.append(rel)

    chains = _build_chains(supported_edges, actual_series, kpi_name_map)
    primary_chain = chains[0] if chains else None

    # Forecast continuation
    forecast_continuation = None
    if is_forecast_period and primary_chain:
        latest_actual_df = _load_actual_history(
            hospital_id, department_id, selected_year, GOVERNED_ACTUAL_MONTH_CUTOFF, actual_history_path
        )
        latest_series: Dict[str, pd.Series] = {}
        if not latest_actual_df.empty:
            for kpi_id in latest_actual_df["kpi_id"].unique():
                latest_series[kpi_id] = _get_series(latest_actual_df, kpi_id)

        fc_lookup: Dict[str, float] = {}
        if not forecast_df.empty:
            for _, frow in forecast_df.iterrows():
                fc_lookup[frow["kpi_id"]] = frow["point_forecast"]

        chain_directions: Dict[str, str] = {}
        fc_directions: Dict[str, str] = {}
        continuing = 0
        total = 0

        for kpi_id in primary_chain["chain_kpi_ids"]:
            hist_series = latest_series.get(kpi_id)
            hist_dir = _historical_trend_direction(hist_series) if hist_series is not None else "FLAT"
            latest_actual = hist_series.iloc[-1] if hist_series is not None and not hist_series.empty else None
            fc_val = fc_lookup.get(kpi_id)
            fc_dir = _forecast_direction(latest_actual, fc_val) if latest_actual is not None and fc_val is not None else "FLAT"

            chain_directions[kpi_id] = hist_dir
            fc_directions[kpi_id] = fc_dir
            if hist_dir != "FLAT" and fc_dir == hist_dir:
                continuing += 1
            if hist_dir != "FLAT":
                total += 1

        if total == 0:
            cont_status = "NOT_APPLICABLE"
        elif continuing == total:
            cont_status = "CONTINUES"
        elif continuing == 0:
            cont_status = "NOT_CONTINUING"
        else:
            cont_status = "PARTIAL"

        forecast_continuation = {
            "selected_forecast_year": selected_year,
            "selected_forecast_month": selected_month,
            "chain_directions": chain_directions,
            "forecast_directions": fc_directions,
            "continuation_status": cont_status,
        }

    result = {
        "status": "OK" if not actual_df.empty else "INSUFFICIENT_DATA",
        "hospital_id": hospital_id,
        "department_id": department_id,
        "actual_period_start": f"{selected_year}-01-01" if not actual_df.empty else None,
        "actual_period_end": f"{selected_year}-{hist_end_month:02d}-28" if not actual_df.empty else None,
        "selected_forecast_year": selected_year if is_forecast_period else None,
        "selected_forecast_month": selected_month if is_forecast_period else None,
        "is_forecast_period": is_forecast_period,
        "relationships": relationships,
        "connected_chains": chains,
        "primary_chain": primary_chain,
        "forecast_continuation": forecast_continuation,
        "governance": {
            "causality_confirmed": False,
            "actual_data_only": True,
            "relationship_type": "exploratory historical association",
            "min_observations": _MIN_OBSERVATIONS,
            "strict_threshold": _STRICT_THRESHOLD,
            "prototype_disclaimer": (
                "Results based on limited monthly observations. "
                "Not statistically significant at conventional levels for all pairs. "
                "Interpreted as an exploratory prototype signal only."
            ),
        },
    }
    return result


# ---------------------------------------------------------------------------
# Display-only mappings (do NOT change analytical logic)
# ---------------------------------------------------------------------------
_ENGLISH_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
_ENGLISH_MONTHS_SHORT = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

# Manager-friendly display wording for forecast continuation status.
# Internal status values are NOT changed; only the card / prompt mapping
# is. This is purely a display concern.
_CONTINUATION_DISPLAY = {
    "CONTINUES": (
        "Connected pattern continues into the forecast",
        "The {month} forecast reflects the same broad KPI movements observed historically.",
    ),
    "PARTIAL": (
        "Part of the connected pattern continues",
        "Some, but not all, of the historical KPI movements remain visible in the {month} forecast.",
    ),
    "NOT_CONTINUING": (
        "Pattern not evident in the {month} forecast",
        "The connected KPI movements seen historically are not consistently reflected in the {month} forecast.",
    ),
    "NOT_CONTINUE": (
        "Pattern not evident in the {month} forecast",
        "The connected KPI movements seen historically are not consistently reflected in the {month} forecast.",
    ),
    "NOT_CONTINUES": (
        "Pattern not evident in the {month} forecast",
        "The connected KPI movements seen historically are not consistently reflected in the {month} forecast.",
    ),
    "NOT_APPLICABLE": (
        "Forward signal not applicable",
        "No forecast month is currently selected for this connected signal.",
    ),
}


def _continuation_display(continuation_status: str, month_label: str) -> tuple:
    """Map internal continuation status -> (display_title, display_subtext).

    Returns English manager-friendly wording. The internal status value is
    NEVER rendered to the Executive Overview.
    """
    if not continuation_status:
        return ("", "")
    key = str(continuation_status).strip().upper()
    template = _CONTINUATION_DISPLAY.get(key)
    if not template:
        # Unknown status: keep card honest with a neutral phrase.
        return ("Forward signal under review", "The forward signal for {month} is being evaluated.".replace("{month}", month_label))
    title, subtext = template
    return (title.format(month=month_label), subtext.format(month=month_label))


def _forecast_month_label(month_value: Any, year_value: Any = None) -> str:
    """Render a forecast month value as 'August' (short) or 'August 2025'.

    Used for both the period badge and the management wording.
    """
    month = _parse_month(month_value)
    if month and 1 <= month <= 12:
        return _ENGLISH_MONTHS_SHORT[month - 1]
    return str(month_value or "the selected forecast")


def _forecast_period_label(month_value: Any, year_value: Any) -> str:
    """Render a forecast month as 'August 2025' (long)."""
    month = _parse_month(month_value)
    if month and 1 <= month <= 12 and year_value:
        return f"{_ENGLISH_MONTHS[month - 1]} {year_value}"
    if month and 1 <= month <= 12:
        return _ENGLISH_MONTHS[month - 1]
    return str(month_value or "the selected forecast")


def _parse_month(value: Any) -> Optional[int]:
    """Parse a value into a 1-12 month number.

    Accepts int, numeric string, ``"YYYY-MM"``, or ``"YYYY-MM-DD"``.
    Returns None when the value cannot be interpreted.
    """
    if value is None:
        return None
    if isinstance(value, int):
        return value if 1 <= value <= 12 else None
    s = str(value).strip()
    if not s:
        return None
    if s.isdigit():
        try:
            m = int(s)
            return m if 1 <= m <= 12 else None
        except ValueError:
            return None
    parts = s.split("-")
    if len(parts) >= 2:
        try:
            m = int(parts[1])
            return m if 1 <= m <= 12 else None
        except (ValueError, TypeError):
            return None
    return None


def _actual_period_label(start_value: Any, end_value: Any) -> str:
    """Render the actual-history period label from engine values.

    The engine emits full ISO dates (``"2025-01-01"`` / ``"2025-07-28"``)
    or month-precision values (``"2025-01"`` / ``"2025-07"``). This
    helper normalizes both into a human-friendly phrase such as
    ``"Jan to Jul 2025"``, falling back to the raw tokens if the format
    is unrecognised.
    """
    if not start_value or not end_value:
        return ""

    def _try_label(token: str) -> Optional[str]:
        parts = str(token).split("-")
        if len(parts) < 2:
            return None
        try:
            y = int(parts[0])
            m = int(parts[1])
        except (ValueError, TypeError):
            return None
        if 1 <= m <= 12:
            return f"{_ENGLISH_MONTHS_SHORT[m-1]} {y}"
        return None

    s_short = _try_label(start_value)
    e_short = _try_label(end_value)
    if s_short and e_short:
        return f"{s_short} to {e_short}"
    return f"{start_value} to {end_value}"


def build_connected_signal_card_html(
    result: Dict[str, Any],
    period_badge_html: str,
    ai_interpretation: Optional[str] = None,
) -> str:
    """Build a compact Connected Signal HTML card for the Executive Overview.

    Display-only:
      * No correlation coefficients, p-values, or model names appear.
      * Internal continuation status values (CONTINUES / PARTIAL /
        NOT_CONTINUING) are NEVER rendered; manager-friendly wording is
        used instead.
      * Small KPI trend icons vs. wide flowchart connector arrows.
    """
    primary = result.get("primary_chain")
    continuation = result.get("forecast_continuation")
    is_forecast = result.get("is_forecast_period", False)
    hist_start = result.get("actual_period_start", "")
    hist_end = result.get("actual_period_end", "")
    forecast_year = result.get("selected_forecast_year")
    forecast_month_num = result.get("selected_forecast_month")

    # ---- No-chain state: clean fallback, no chain sections ----
    if not primary:
        return (
            f'<div class="s360-kpi-card grey" style="padding:14px 16px;">'
            f'<div style="font-size:13px;font-weight:700;color:#1A2B47;margin-bottom:6px;">'
            f'Connected Signal {period_badge_html}'
            f'</div>'
            f'<div style="font-size:0.96rem;color:#4A5568;line-height:1.4;">'
            f'No sufficiently strong connected signal detected from the available actual history.'
            f'</div>'
            f'<div style="font-size:0.65rem;color:#718096;margin-top:8px;">'
            f'Based on governed actual KPI history. Causality is not inferred.'
            f'</div>'
            f'</div>'
        )

    # ---- Chain KPI rows with wide flowchart connectors ----
    chain_rows = []
    kpi_ids = primary["chain_kpi_ids"]
    kpi_names = primary.get("chain_kpi_names", kpi_ids)
    trend_dirs = primary.get("trend_directions", {})

    for i, kpi_id in enumerate(kpi_ids):
        name = kpi_names[i] if i < len(kpi_names) else kpi_id
        direction = trend_dirs.get(kpi_id, "FLAT")
        arrow = _arrow(direction)  # small KPI trend icon
        # KPI name uses an inline <span> so the row can lay out as
        # `display: inline-flex` (intrinsic width -- no full-card stretch).
        kpi_name_html = (
            f'<span class="s360-cs-kpi-name" '
            f'style="font-size:0.95rem;font-weight:600;color:#1A2B47;'
            f'line-height:1.25;">{name}</span>'
        )
        # KPI row uses inline-flex with a fixed 12px gap between the name
        # and the trend icon.  No margin-left:auto, no justify-content
        # space-between -- the icon sits directly beside the label and
        # the row only takes the width it actually needs.
        kpi_row_html = (
            f'<div class="s360-cs-kpi-row" '
            f'style="display:inline-flex;align-items:center;'
            f'gap:12px;padding:4px 8px;">'
            f'{kpi_name_html}'
            f'{arrow}'
            f'</div>'
        )

        node_inner = [kpi_row_html]

        if i < len(kpi_ids) - 1:
            # Polished, centered vertical flow connector -- rendered as a
            # single inline SVG so it is crisp at any zoom and clearly
            # larger than the per-KPI trend icons (20 x 36 vs 20 x 20).
            # Visually distinct from the small ▲/▼/▬ trend icons.
            node_inner.append(
                f'<div class="s360-cs-flow-connector" '
                f'style="display:flex;justify-content:center;'
                f'align-items:center;padding:6px 0;">'
                f'<span class="s360-cs-flow-arrow" aria-hidden="true">'
                f'<svg class="s360-cs-flow-arrow-svg" '
                f'width="20" height="36" viewBox="0 0 20 36" '
                f'xmlns="http://www.w3.org/2000/svg" focusable="false">'
                f'<line x1="10" y1="2" x2="10" y2="24" '
                f'stroke="#4A6A99" stroke-width="3" '
                f'stroke-linecap="round" opacity="0.9"/>'
                f'<polygon points="10,33 3,24 17,24" fill="#4A6A99"/>'
                f'</svg>'
                f'</span>'
                f'</div>'
            )

        # chain-node is the unit of horizontal centering: it is
        # `inline-flex` (intrinsic width = max child width) and column-
        # flex (children stacked vertically).  The flow connector is a
        # child of this same node, so it centers directly beneath the
        # KPI row above it -- relative to that block, NOT relative to
        # the wider Connected Signal card.
        chain_rows.append(
            f'<div class="s360-cs-chain-node" '
            f'style="display:inline-flex;flex-direction:column;'
            f'align-items:center;padding:2px 0;">'
            f'{"".join(node_inner)}'
            f'</div>'
        )

    chain_html = "".join(chain_rows)

    # ---- Strength label (STRONG / MODERATE) ----
    strength = ""
    if primary.get("edges"):
        avg_r = primary.get("average_abs_r", 0.0)
        strength = "STRONG" if avg_r >= _STRICT_THRESHOLD else "MODERATE"

    actual_period = _actual_period_label(hist_start, hist_end)

    # ---- Forward Signal: manager-friendly continuation ----
    forward_html = ""
    if is_forecast and continuation:
        cont_status = str(continuation.get("continuation_status", "") or "").strip()
        month_long = _forecast_period_label(forecast_month_num, forecast_year)
        display_title, display_subtext = _continuation_display(cont_status, month_long)
        forward_html = (
            f'<div style="margin-top:10px;padding:6px 0;border-top:1px solid #EDF2F7;">'
            f'<div style="font-size:0.62rem;color:#4A6A99;text-transform:uppercase;'
            f'letter-spacing:0.5px;font-weight:600;">'
            f'Forward Signal &mdash; {month_long}'
            f'</div>'
            f'<div style="font-size:0.92rem;font-weight:600;color:#1A2B47;margin-top:3px;">'
            f'{display_title}'
            f'</div>'
            f'<div style="font-size:0.78rem;color:#4A5568;line-height:1.4;margin-top:2px;">'
            f'{display_subtext}'
            f'</div>'
            f'</div>'
        )

    # ---- Management Interpretation (Hy3 sentence) ----
    interp_html = ""
    if ai_interpretation:
        interp_html = (
            f'<div style="margin-top:10px;padding:6px 0;border-top:1px solid #EDF2F7;">'
            f'<div style="font-size:0.62rem;color:#4A6A99;text-transform:uppercase;'
            f'letter-spacing:0.5px;font-weight:600;">'
            f'Management Interpretation'
            f'</div>'
            f'<div style="font-size:0.88rem;color:#2D3748;line-height:1.45;margin-top:3px;">'
            f'{ai_interpretation}'
            f'</div>'
            f'</div>'
        )

    # ---- Final card ----
    return (
        f'<div class="s360-kpi-card grey" style="padding:14px 16px;">'
        f'<div style="font-size:13px;font-weight:700;color:#1A2B47;margin-bottom:6px;">'
        f'Connected Signal {period_badge_html}'
        f'</div>'
        f'<div style="font-size:0.62rem;color:#4A6A99;text-transform:uppercase;'
        f'letter-spacing:0.5px;font-weight:600;margin-bottom:2px;">'
        f'Historical Connection &mdash; {actual_period or "governed actual KPI history"}'
        f'</div>'
        f'<div class="s360-cs-chain" '
        f'style="display:flex;flex-direction:column;align-items:center;'
        f'margin-top:4px;">'
        f'{chain_html}'
        f'</div>'
        f'<div style="margin-top:10px;padding:6px 0;border-top:1px solid #EDF2F7;">'
        f'<div style="font-size:0.62rem;color:#4A6A99;text-transform:uppercase;'
        f'letter-spacing:0.5px;font-weight:600;">'
        f'Historical Signal'
        f'</div>'
        f'<div style="font-size:0.95rem;font-weight:600;color:#1A2B47;margin-top:3px;">'
        f'Strong connected pattern'
        f'</div>'
        f'<div style="font-size:0.78rem;color:#4A5568;line-height:1.4;margin-top:2px;">'
        f'Observed across {actual_period} actual performance.'
        f'</div>'
        f'</div>'
        f'{forward_html}'
        f'{interp_html}'
        f'<div style="font-size:0.62rem;color:#718096;margin-top:8px;line-height:1.35;">'
        f'Association observed from governed actual KPI history. '
        f'Forecast assessment reflects directional consistency only. '
        f'Causality is not confirmed.'
        f'</div>'
        f'</div>'
    )
