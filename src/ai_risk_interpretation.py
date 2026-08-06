"""Sentinel360 Risk Management Interpretation service.

Uses Tencent Hy3 (via the shared TokenHub transport) to produce a concise
two-sentence management interpretation for a single selected KPI.

Contract:
  * AI only explains governed evidence.
  * AI never calculates, modifies, or infers values.
  * Causality is never claimed.
  * Output is always two fields: what_is_changing, why_it_matters.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Optional

from src._ai_tokenhub_transport import call_tokenhub_chat_completion
from src.genai_provenance_badge import is_hy3_live

_SCHEMA_VERSION = "risk_interp_v1"

_SYSTEM_PROMPT = (
    "You are the Sentinel360 Risk Management Interpretation Assistant for "
    "hospital executives.\n\n"
    "Answer ONLY from the governed KPI evidence supplied.\n"
    "Do NOT calculate, estimate, infer missing values, or alter risk "
    "classifications.\n"
    "Explain the evidence in concise management language.\n"
    "Never claim causality unless explicitly supplied as confirmed evidence.\n"
    "\n"
    "Response rules:\n"
    "- Produce exactly two fields: what_is_changing and why_it_matters.\n"
    "- Each field must be ONE sentence, 20 to 35 words.\n"
    "- Plain management language only.\n"
    "- No JSON, no KPI IDs, no raw field names, no methodology notes.\n"
    "- No causal claims such as 'caused', 'drove', 'led to', 'resulted in'.\n"
    "- Refer to KPIs by their display names only.\n"
    "- Use cautious language: 'at risk', 'deteriorating', 'below target', "
    "'warrants attention', 'should be monitored'.\n"
    "\n"
    "Output format (exact JSON):\n"
    '{"what_is_changing": "...", "why_it_matters": "..."}\n'
)


def _build_prompt(evidence: Dict[str, Any]) -> str:
    """Build the prompt containing the governed evidence and the request."""
    kpi = evidence.get("kpi", {})
    hist = evidence.get("historical", {})
    fc = evidence.get("forecast", {})
    ctx = evidence.get("context", {})

    lines: list[str] = []
    lines.append("GOVERNED KPI EVIDENCE:")
    lines.append(
        f"- KPI: {kpi.get('kpi_name', '')} ({kpi.get('unit', '')})"
    )
    lines.append(f"- Department: {ctx.get('department_name', '')}")
    lines.append(
        f"- Period: {ctx.get('year', '')}-{ctx.get('selected_month', '')}"
    )
    lines.append("")

    if hist.get("start_month"):
        lines.append(
            f"Historical: {kpi['kpi_name']} moved from "
            f"{hist['start_value_display']} in {hist['start_month']} to "
            f"{hist['latest_actual_value_display']} in "
            f"{hist['latest_actual_month']}. Latest actual status: "
            f"{hist['latest_actual_status']}."
        )
    elif hist.get("latest_actual_month"):
        lines.append(
            f"Historical: {kpi['kpi_name']} latest actual is "
            f"{hist['latest_actual_value_display']} in "
            f"{hist['latest_actual_month']}. Latest actual status: "
            f"{hist['latest_actual_status']}."
        )
    else:
        lines.append(
            f"Historical: No supported actual data available for "
            f"{kpi['kpi_name']}."
        )

    lines.append("")
    if (
        fc.get("forecast_value_display")
        and fc.get("forecast_value_display") != "Not available"
    ):
        lines.append(
            f"Forecast: {kpi['kpi_name']} is projected at "
            f"{fc['forecast_value_display']} by {fc['forecast_month']}, "
            f"classified as {fc['warning_level']}."
        )
    else:
        lines.append(f"Forecast: Not available for {kpi['kpi_name']}.")

    lines.append("")
    lines.append(
        "GOVERNANCE FLAGS:\n"
        "- evidence_is_governed: true\n"
        "- ai_may_calculate: false\n"
        "- ai_may_modify_values: false\n"
        "- ai_may_infer_missing_values: false\n"
        "- causality_confirmed: false\n"
    )
    lines.append("")
    lines.append("INSTRUCTION:")
    lines.append(
        "In one sentence, state WHAT IS CHANGING for this KPI "
        "(historical movement + forecast direction)."
    )
    lines.append(
        "In one second sentence, state WHY IT MATTERS "
        "(warning escalation + management significance)."
    )
    lines.append(
        "Return valid JSON with exactly two keys: "
        "what_is_changing, why_it_matters."
    )
    return "\n".join(lines).strip()


class AIRiskInterpretationResult:
    """Result container for the Risk Interpretation service."""

    def __init__(
        self,
        *,
        status: str,
        what_is_changing: str,
        why_it_matters: str,
        raw_response: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.status = status
        self.what_is_changing = what_is_changing
        self.why_it_matters = why_it_matters
        self.raw_response = raw_response

    def __repr__(self) -> str:
        return (
            f"AIRiskInterpretationResult(status={self.status!r}, "
            f"what_is_changing={len(self.what_is_changing)} chars, "
            f"why_it_matters={len(self.why_it_matters)} chars)"
        )


class AIRiskInterpretationService:
    """Hy3-powered single-KPI management interpretation service."""

    def __init__(self, *, api_key: Optional[str] = None) -> None:
        self._api_key = api_key
        if self._api_key is None:
            self._api_key = _load_api_key()

    def interpret(self, evidence: Dict[str, Any]) -> AIRiskInterpretationResult:
        """Return a two-sentence interpretation for the governed KPI evidence."""
        if not evidence:
            return AIRiskInterpretationResult(
                status="EMPTY_EVIDENCE",
                what_is_changing="",
                why_it_matters="",
            )

        # Live Hy3 call via shared transport
        if self._api_key:
            prompt = _build_prompt(evidence)
            messages = [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]
            raw_response = call_tokenhub_chat_completion(
                messages,
                provider="SENTINEL360_AI_PROVIDER",
                model="hy3",
                api_key=self._api_key,
                timeout=30.0,
                temperature=0.1,
                max_tokens=200,
            )
            if is_hy3_live(raw_response):
                message = raw_response.get("message", "")
                parsed = _parse_json_fields(message)
                if parsed.get("what_is_changing") or parsed.get(
                    "why_it_matters"
                ):
                    return AIRiskInterpretationResult(
                        status="OK",
                        what_is_changing=parsed["what_is_changing"],
                        why_it_matters=parsed["why_it_matters"],
                        raw_response=raw_response,
                    )
                # Parsing succeeded but fields are empty → fall through to fallback

        # Deterministic fallback (also used when Hy3 unavailable or unparseable)
        fallback = _build_fallback(evidence)
        return AIRiskInterpretationResult(
            status="FALLBACK",
            what_is_changing=fallback["what_is_changing"],
            why_it_matters=fallback["why_it_matters"],
        )


def _build_fallback(evidence: Dict[str, Any]) -> Dict[str, str]:
    """Build a deterministic fallback from the governed evidence."""
    kpi = evidence.get("kpi", {})
    hist = evidence.get("historical", {})
    fc = evidence.get("forecast", {})

    kpi_name = kpi.get("kpi_name", "this KPI")
    start_val = (
        hist.get("start_value_display")
        or hist.get("latest_actual_value_display")
        or "not available"
    )
    start_month = hist.get("start_month") or hist.get(
        "latest_actual_month"
    ) or "the period"
    latest_val = hist.get("latest_actual_value_display") or "not available"
    latest_month = hist.get("latest_actual_month") or "the latest period"
    forecast_val = fc.get("forecast_value_display") or "not available"
    forecast_month = fc.get("forecast_month") or "the forecast period"
    warning_level = fc.get("warning_level") or "a warning level"

    # WHAT IS CHANGING
    if hist.get("start_month"):
        what = (
            f"{kpi_name} moved from {start_val} in {start_month} to "
            f"{latest_val} in {latest_month} and is forecast at "
            f"{forecast_val} by {forecast_month}."
        )
    else:
        what = (
            f"{kpi_name} latest actual is {latest_val} in "
            f"{latest_month} and is forecast at {forecast_val} by "
            f"{forecast_month}."
        )

    # WHY DOES IT MATTER
    if (
        fc.get("forecast_value_display")
        and fc.get("forecast_value_display") != "Not available"
    ):
        why = (
            f"The {forecast_month} forecast is classified as {warning_level} "
            f"and warrants management attention."
        )
    else:
        why = (
            f"Insufficient data is available for a full forecast assessment, "
            f"but management should monitor {kpi_name} closely."
        )

    return {
        "what_is_changing": what,
        "why_it_matters": why,
    }


def _parse_json_fields(text: str) -> Dict[str, str]:
    """Extract what_is_changing and why_it_matters from a JSON string."""
    text = text.strip()

    # Try to find JSON block in ```json ... ``` or just raw JSON
    code_block = re.search(
        r"```(?:json)?\s*([\s\S]*?)```", text
    )
    if code_block:
        text = code_block.group(1).strip()

    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return {
                "what_is_changing": str(obj.get("what_is_changing", "")),
                "why_it_matters": str(obj.get("why_it_matters", "")),
            }
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback: regex extraction
    wc_match = re.search(
        r'what_is_changing["\']?\s*[:=]\s*["\']?(.*?)(?:(?:["\']?\s*[,}])|$)',
        text,
        re.IGNORECASE | re.DOTALL,
    )
    wm_match = re.search(
        r'why_it_matters["\']?\s*[:=]\s*["\']?(.*?)(?:(?:["\']?\s*[,}])|$)',
        text,
        re.IGNORECASE | re.DOTALL,
    )

    result: Dict[str, str] = {}
    if wc_match:
        result["what_is_changing"] = (
            wc_match.group(1).strip().strip('"').strip("'")
        )
    if wm_match:
        result["why_it_matters"] = (
            wm_match.group(1).strip().strip('"').strip("'")
        )
    return result


def _load_api_key() -> Optional[str]:
    key = os.getenv("SENTINEL360_AI_API_KEY", "").strip()
    return key if key else None


def build_risk_interpretation_cache_key(evidence: Dict[str, Any]) -> str:
    """Build a deterministic cache key for the interpretation.

    The key never contains the API key. It uses the evidence content hash
    (which changes when any governed value changes).
    """
    evidence_hash = evidence.get("_evidence_hash", "")
    return f"s360_risk_interp_cache_v1:{evidence_hash}"
