"""Sentinel360 Decision Impact Interpretation service.

Uses Tencent Hy3 (via the shared TokenHub transport) to produce a concise
two-sentence management interpretation of the expected impact from a selected
scenario.

Contract:
  * AI only explains governed evidence.
  * AI never recalculates, modifies, or infers scenario values.
  * Causality is never claimed.
  * Output is always two fields: what_it_means, decision_implication.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Optional

from src._ai_tokenhub_transport import call_tokenhub_chat_completion
from src.genai_provenance_badge import is_hy3_live

_SCHEMA_VERSION = "decision_impact_v1"

_SYSTEM_PROMPT = (
    "You are the Sentinel360 Decision Impact Interpretation Assistant for "
    "hospital executives.\n\n"
    "Answer ONLY from the governed scenario evidence supplied.\n"
    "Do NOT recalculate, estimate, infer missing values, or alter scenario "
    "outcomes.\n"
    "Explain the evidence in concise management language.\n"
    "Never claim causality unless explicitly supplied as confirmed evidence.\n"
    "\n"
    "Response rules:\n"
    "- Produce exactly two fields: what_it_means and decision_implication.\n"
    "- Each field must be ONE sentence, 20 to 35 words.\n"
    "- Plain management language only.\n"
    "- No JSON, no KPI IDs, no raw field names, no methodology notes.\n"
    "- No causal claims such as 'caused', 'drove', 'led to', 'resulted in'.\n"
    "- Refer to KPIs by their display names only.\n"
    "- Use cautious language: 'suggests', 'indicates', 'may be sufficient', "
    "'may warrant', 'should be weighed', 'supports consideration'.\n"
    "- Never make autonomous decisions: do NOT say 'Management should approve "
    "this action' or 'This is the best decision'.\n"
    "\n"
    "Decision implication guidance:\n"
    "- If governed_ceiling_reached is true, suggest that additional action "
    "intensity may provide limited KPI benefit and should be weighed against "
    "extra resources.\n"
    "- If target_met is true but governed_ceiling_reached is false, indicate "
    "that the current intervention may be sufficient without escalating.\n"
    "- If target_met is false, suggest that management may need to consider a "
    "stronger intervention or further review.\n"
    "\n"
    "Output format (exact JSON):\n"
    '{"what_it_means": "...", "decision_implication": "..."}\n'
)


def _build_prompt(evidence: Dict[str, Any]) -> str:
    """Build the prompt containing the governed evidence and the request."""
    kpi = evidence.get("kpi", {})
    baseline = evidence.get("baseline", {})
    scenario = evidence.get("scenario", {})
    ctx = evidence.get("context", {})
    gov = evidence.get("governance", {})

    lines: list[str] = []
    lines.append("GOVERNED SCENARIO EVIDENCE:")
    lines.append(f"- KPI: {kpi.get('kpi_name', '')} ({kpi.get('unit', '')})")
    lines.append(f"- Target: {kpi.get('target_display', 'Not configured')}")
    lines.append(f"- Department: {ctx.get('department_name', '')}")
    lines.append(f"- Forecast month: {ctx.get('forecast_month', '')}")
    lines.append("")
    lines.append(
        f"Do-nothing forecast: {baseline.get('do_nothing_forecast_display', 'Not available')}"
    )
    lines.append(
        f"Selected scenario ({scenario.get('selected_action_level', '')}): "
        f"{scenario.get('selected_scenario_display', 'Not available')}"
    )
    lines.append(
        f"Expected KPI change: {scenario.get('expected_kpi_change_display', 'Not available')}"
    )
    lines.append(
        f"Relative change: {scenario.get('relative_change_display', 'Not available')}"
    )
    lines.append(f"Action strategy: {scenario.get('action_strategy', '')}")
    lines.append(f"Resource commitment: {scenario.get('resource_commitment', '')}")
    lines.append("")
    lines.append("Governed state flags:")
    lines.append(
        f"- Target met: {'yes' if scenario.get('target_met') else 'no'}"
    )
    lines.append(
        f"- Governed ceiling reached: "
        f"{'yes' if scenario.get('governed_ceiling_reached') else 'no'}"
    )
    lines.append("")
    lines.append("Governance constraints:")
    lines.append(
        f"- evidence_is_governed: {gov.get('evidence_is_governed', False)}"
    )
    lines.append(f"- ai_may_calculate: {gov.get('ai_may_calculate', False)}")
    lines.append(
        f"- ai_may_modify_values: {gov.get('ai_may_modify_values', False)}"
    )
    lines.append(
        f"- ai_may_infer_missing_values: {gov.get('ai_may_infer_missing_values', False)}"
    )
    lines.append(
        f"- causality_confirmed: {gov.get('causality_confirmed', False)}"
    )
    lines.append("")
    lines.append(
        "Interpretation request:\n"
        "Provide a concise two-sentence management interpretation:\n"
        "1. WHAT DOES THIS MEAN FOR THE DECISION? (one sentence, 20–35 words)\n"
        "2. DECISION IMPLICATION (one sentence, 20–35 words)\n"
        "Use the governed state flags to guide the tone.  Do NOT fabricate numbers."
    )

    return "\n".join(lines)


class AIDecisionImpactResult:
    """Structured result returned by the decision impact interpretation."""

    def __init__(
        self,
        *,
        status: str,
        what_it_means: str = "",
        decision_implication: str = "",
        raw_response: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.status = status
        self.what_it_means = what_it_means
        self.decision_implication = decision_implication
        self.raw_response = raw_response

    def __repr__(self) -> str:
        return (
            f"AIDecisionImpactResult(status={self.status!r}, "
            f"what_it_means={len(self.what_it_means)} chars, "
            f"decision_implication={len(self.decision_implication)} chars)"
        )


class AIDecisionImpactSynthesisService:
    """Hy3-powered decision impact interpretation service."""

    def __init__(self, *, api_key: Optional[str] = None) -> None:
        self._api_key = api_key
        if self._api_key is None:
            self._api_key = _load_api_key()

    def interpret(self, evidence: Dict[str, Any]) -> AIDecisionImpactResult:
        """Return a two-sentence interpretation for the governed scenario evidence."""
        if not evidence:
            return AIDecisionImpactResult(
                status="EMPTY_EVIDENCE",
                what_it_means="",
                decision_implication="",
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
                if parsed.get("what_it_means") or parsed.get(
                    "decision_implication"
                ):
                    return AIDecisionImpactResult(
                        status="OK",
                        what_it_means=parsed["what_it_means"],
                        decision_implication=parsed["decision_implication"],
                        raw_response=raw_response,
                    )
                # Parsing succeeded but fields are empty → fall through to fallback

        # Deterministic fallback (also used when Hy3 unavailable or unparseable)
        fallback = _build_fallback(evidence)
        return AIDecisionImpactResult(
            status="FALLBACK",
            what_it_means=fallback["what_it_means"],
            decision_implication=fallback["decision_implication"],
        )


def _build_fallback(evidence: Dict[str, Any]) -> Dict[str, str]:
    """Build a deterministic fallback from the governed evidence."""
    kpi = evidence.get("kpi", {})
    baseline = evidence.get("baseline", {})
    scenario = evidence.get("scenario", {})

    kpi_name = kpi.get("kpi_name", "the selected KPI")
    do_nothing = baseline.get("do_nothing_forecast_display", "Not available")
    scenario_val = scenario.get("selected_scenario_display", "Not available")
    action_level = scenario.get("selected_action_level", "Selected scenario")
    change_display = scenario.get("expected_kpi_change_display", "")
    ceiling_reached = scenario.get("governed_ceiling_reached", False)
    target_met = scenario.get("target_met", False)

    # WHAT DOES THIS MEAN FOR THE DECISION?
    if change_display and change_display != "Not available":
        what = (
            f"The selected {action_level} is expected to improve {kpi_name} "
            f"from the do-nothing forecast of {do_nothing} to {scenario_val}, "
            f"representing a {change_display} improvement under the current "
            f"governed scenario assumptions."
        )
    else:
        what = (
            f"The selected {action_level} is expected to change {kpi_name} "
            f"from {do_nothing} to {scenario_val} under the current governed "
            f"scenario assumptions."
        )

    # DECISION IMPLICATION
    if ceiling_reached:
        why = (
            "The selected scenario reaches the governed performance ceiling; "
            "compare additional resource intensity before considering a stronger "
            "action."
        )
    elif target_met:
        why = (
            "The selected scenario moves the KPI above its governed target, "
            "indicating that the current intervention may be sufficient without "
            "immediately escalating to a more resource-intensive option."
        )
    else:
        why = (
            "The selected scenario improves the KPI but remains below the governed "
            "target, so management may need to consider a stronger intervention or "
            "further review."
        )

    return {
        "what_it_means": what,
        "decision_implication": why,
    }


def _parse_json_fields(text: str) -> Dict[str, str]:
    """Extract what_it_means and decision_implication from a JSON string."""
    text = text.strip()

    code_block = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if code_block:
        text = code_block.group(1).strip()

    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return {
                "what_it_means": str(obj.get("what_it_means", "")),
                "decision_implication": str(obj.get("decision_implication", "")),
            }
    except (json.JSONDecodeError, ValueError):
        pass

    wc_match = re.search(
        r'what_it_means["\']?\s*[:=]\s*["\']?(.*?)(?:(?:["\']?\s*[,}])|$)',
        text,
        re.IGNORECASE | re.DOTALL,
    )
    wm_match = re.search(
        r'decision_implication["\']?\s*[:=]\s*["\']?(.*?)(?:(?:["\']?\s*[,}])|$)',
        text,
        re.IGNORECASE | re.DOTALL,
    )

    result: Dict[str, str] = {}
    if wc_match:
        result["what_it_means"] = (
            wc_match.group(1).strip().strip('"').strip("'")
        )
    if wm_match:
        result["decision_implication"] = (
            wm_match.group(1).strip().strip('"').strip("'")
        )
    return result


def _load_api_key() -> Optional[str]:
    key = os.getenv("SENTINEL360_AI_API_KEY", "").strip()
    return key if key else None
