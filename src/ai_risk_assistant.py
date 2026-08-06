"""Sentinel360 Risk AI Assistant service.

Uses Tencent Hy3 (via the shared TokenHub transport) to answer
management questions about the governed Risk & Alert evidence.

Contract:
  * The assistant only explains and interprets governed evidence.
  * It never calculates new risk values, infers missing KPIs, or
    modifies warning classifications.
  * If a question cannot be answered from the supplied evidence, it
    responds with the deterministic refusal message.
  * Causality is never claimed unless explicitly present in the evidence.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple

from src._ai_tokenhub_transport import call_tokenhub_chat_completion
from src.genai_provenance_badge import is_hy3_live

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------

SCHEMA_VERSION = "risk_ai_v1"

_DEFAULT_SYSTEM_PROMPT = (
    "You are the Sentinel360 Risk Briefing Assistant for hospital management.\n"
    "\n"
    "Answer ONLY from the governed Risk & Alert evidence supplied.\n"
    "Do NOT calculate, estimate, infer missing values, or alter risk "
    "classifications.\n"
    "Explain the evidence in concise management language.\n"
    "Never claim causality unless explicitly supplied as confirmed evidence.\n"
    "If the evidence does not answer the question, say so.\n"
    "\n"
    "Response rules:\n"
    "- 30 to 70 words preferred. Never exceed 100 words.\n"
    "- Plain management language only.\n"
    "- No JSON, no KPI IDs, no raw field names, no Spearman, no MAE, "
    "no internal schemas, no methodology notes.\n"
    "- No causal claims such as 'caused', 'drove', 'led to', 'resulted in'.\n"
    "- Refer to KPIs by their display names only.\n"
    "- Use cautious language: 'at risk', 'deteriorating', 'below target', "
    "'warrants attention', 'should be monitored'.\n"
)

_UNSUPPORTED_MSG = (
    "The current governed Risk & Alert evidence does not support that question."
)

_FALLBACK_UNAVAILABLE = (
    "The AI Risk Brief is currently unavailable. "
    "Please use the governed Risk & Alert evidence shown on this page."
)

# ---------------------------------------------------------------------------
# Suggested questions (public so the UI and tests can share them)
# ---------------------------------------------------------------------------

SUGGESTED_QUESTIONS: List[str] = [
    "What is the biggest risk this month?",
    "Why is it a risk?",
    "Which KPIs have escalating risk?",
    "Which KPI is starting to build risk?",
    "What should management watch first?",
]

# Map question text → deterministic fallback answer template key
_QUESTION_TEMPLATE_KEY: Dict[str, str] = {
    "What is the biggest risk this month?": "biggest_risk",
    "Why is it a risk?": "why_risk",
    "Which KPIs have escalating risk?": "escalating_kpis",
    "Which KPI is starting to build risk?": "emerging_kpis",
    "What should management watch first?": "watch_first",
}


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------

class AIRiskAssistantService:
    """Hy3-powered Risk & Alert conversational assistant.

    Public surface
    --------------
    ask(question, evidence, *, previous_context=None)
        -> AIRiskAssistantResult
    """

    def __init__(self, *, api_key: Optional[str] = None) -> None:
        self._api_key = api_key
        # The existing AI environment variable convention (mirrors KPI graph).
        if self._api_key is None:
            self._api_key = _load_api_key()

    def ask(
        self,
        question: str,
        evidence: Dict[str, Any],
        *,
        previous_context: Optional[Dict[str, Any]] = None,
    ) -> "AIRiskAssistantResult":
        """Answer a management question from the governed evidence.

        If Hy3 is live (status == OK) the answer comes from the model.
        Otherwise, for one of the five standard questions, a deterministic
        fallback sentence is generated directly from the evidence. For
        unsupported questions in fallback mode, a polite refusal is
        returned.

        Parameters
        ----------
        question
            The management question (e.g. one of the suggested questions).
        evidence
            The governed evidence dict built by ``build_risk_ai_evidence``.
        previous_context
            Optional previous turn context (keys: ``question``, ``answer``,
            ``referenced_kpi``). Used to resolve follow-up pronouns like
            "Why?" or "What about it?".

        Returns
        -------
        AIRiskAssistantResult
        """
        if not question or not question.strip():
            return AIRiskAssistantResult(
                status="EMPTY_QUESTION",
                message="Please enter a question.",
            )

        # Resolve follow-up "Why?" / "it" references if previous context exists
        resolved_question = _resolve_follow_up(question, previous_context)

        # Build messages
        system_prompt = _build_system_prompt(evidence)
        user_prompt = _build_user_prompt(resolved_question, evidence)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Live Hy3 call via shared transport
        if self._api_key:
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
                return AIRiskAssistantResult(
                    status="OK",
                    message=raw_response.get("message", ""),
                    raw_response=raw_response,
                )

        # Deterministic fallback for the five standard questions
        template_key = _QUESTION_TEMPLATE_KEY.get(resolved_question)
        if template_key:
            fallback = _deterministic_answer(template_key, evidence)
            return AIRiskAssistantResult(
                status="FALLBACK",
                message=fallback,
            )

        # Unsupported custom question in fallback mode
        return AIRiskAssistantResult(
            status="FALLBACK",
            message=_UNSUPPORTED_MSG,
        )


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

class AIRiskAssistantResult:
    """Lightweight result container (dict-compatible for provenance gate)."""

    def __init__(
        self,
        *,
        status: str,
        message: str,
        raw_response: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.status = status
        self.message = message
        self.raw_response = raw_response

    def __repr__(self) -> str:
        return f"AIRiskAssistantResult(status={self.status!r}, message=...{len(self.message)} chars)"


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def _build_system_prompt(evidence: Dict[str, Any]) -> str:
    """Return a system prompt that embeds the governed evidence summary."""
    ctx = evidence.get("context", {})
    summary = evidence.get("summary", {})
    priority = evidence.get("priority_risks", [])
    emerging = evidence.get("emerging_risks", [])
    escalating = evidence.get("escalating_risks", [])

    lines: List[str] = []
    lines.append(_DEFAULT_SYSTEM_PROMPT)
    lines.append("")
    lines.append("GOVERNED CONTEXT:")
    lines.append(f"- Hospital: {ctx.get('hospital_display', ctx.get('hospital_id', ''))}")
    lines.append(f"- Department: {ctx.get('department_name', '')}")
    lines.append(f"- Period: {ctx.get('month_name', '')} {ctx.get('year', '')}")
    lines.append("")
    lines.append("SUMMARY:")
    lines.append(f"- KPIs at risk: {summary.get('kpis_at_risk_count', 0)}")
    lines.append(f"- Emerging forecast risks: {summary.get('emerging_forecast_risk_count', 0)}")
    lines.append(f"- High/escalating warnings: {summary.get('high_escalating_warning_count', 0)}")
    lines.append(f"- Highest warning level: {summary.get('highest_warning_level', '')}")
    lines.append("")
    if priority:
        lines.append("PRIORITY RISKS (ranked by severity):")
        for r in priority[:10]:
            lines.append(
                f"  {r.get('risk_rank', '')}. {r['kpi_name']} ({r['department_name']}) "
                f"— actual: {r['actual_status']}, warning: {r['warning_level']}, "
                f"forecast: {r['forecast_value'] or 'N/A'}"
            )
    if emerging:
        lines.append("")
        lines.append("EMERGING RISKS:")
        for r in emerging[:10]:
            lines.append(
                f"  - {r['kpi_name']} ({r['department_name']}) "
                f"— actual status: {r['actual_status']}, warning: {r['warning_level']}"
            )
    if escalating:
        lines.append("")
        lines.append("ESCALATING RISKS:")
        for r in escalating[:10]:
            lines.append(
                f"  - {r['kpi_name']} ({r['department_name']}) "
                f"— warning: {r['warning_level']}, actual: {r['actual_status']}"
            )
    lines.append("")
    lines.append(
        "GOVERNANCE FLAGS:\n"
        "- evidence_is_governed: true\n"
        "- ai_may_calculate: false\n"
        "- ai_may_modify_values: false\n"
        "- ai_may_infer_missing_values: false\n"
        "- causality_confirmed: false\n"
    )
    return "\n".join(lines).strip()


def _build_user_prompt(question: str, evidence: Dict[str, Any]) -> str:
    """Return the user-turn prompt containing the question and period."""
    ctx = evidence.get("context", {})
    return (
        f"Question: {question}\n"
        f"Period: {ctx.get('month_name', '')} {ctx.get('year', '')}\n\n"
        "Answer ONLY from the governed evidence above."
    )


# ---------------------------------------------------------------------------
# Follow-up resolution
# ---------------------------------------------------------------------------

def _resolve_follow_up(
    question: str, previous_context: Optional[Dict[str, Any]]
) -> str:
    """Resolve vague follow-up questions ("Why?", "Why is it?") using context.

    If the previous turn referenced a specific KPI, the follow-up is
    expanded to refer to that KPI explicitly so the prompt stays
    unambiguous.
    """
    if not previous_context:
        return question
    q = question.strip()
    low = q.lower().rstrip("?")
    if low in ("why", "why is it", "why is it a risk"):
        prev_kpi = previous_context.get("referenced_kpi")
        if prev_kpi:
            return f"Why is {prev_kpi} a risk?"
        return "Why is it a risk?"
    return question


# ---------------------------------------------------------------------------
# Deterministic fallback answers
# ---------------------------------------------------------------------------

def _deterministic_answer(template_key: str, evidence: Dict[str, Any]) -> str:
    """Return a deterministic answer sentence from the governed evidence."""
    summary = evidence.get("summary", {})
    priority = evidence.get("priority_risks", [])
    emerging = evidence.get("emerging_risks", [])
    escalating = evidence.get("escalating_risks", [])
    ctx = evidence.get("context", {})
    month_name = ctx.get("month_name", "this month")
    year = ctx.get("year", "")

    if template_key == "biggest_risk":
        if priority:
            top = priority[0]
            return (
                f"{top['kpi_name']} is the highest-priority risk for "
                f"{month_name} {year}, with a {top['warning_level']} and "
                f"{top['actual_status'].lower()}. Its projected performance "
                f"remains below the governed acceptable range, making it the "
                f"most immediate issue for management attention."
            )
        return (
            f"No priority risks are detected for {month_name} {year}."
        )

    if template_key == "why_risk":
        # If the previous context referenced a KPI, answer about that KPI.
        # Otherwise, answer about the top priority risk.
        if priority:
            target = priority[0]
            return (
                f"{target['kpi_name']} carries a {target['warning_level']} "
                f"because its actual status is {target['actual_status'].lower()} "
                f"and the forecast indicates continued deterioration. "
                f"Management should monitor the gap against target."
            )
        return (
            f"No priority risks are detected for {month_name} {year}."
        )

    if template_key == "escalating_kpis":
        if not escalating:
            return (
                f"No KPIs currently carry an escalating or high warning for "
                f"{month_name} {year}."
            )
        names = [r["kpi_name"] for r in escalating]
        if len(names) == 1:
            return (
                f"{names[0]} currently carries an escalating or high warning."
            )
        return (
            f"The KPIs with escalating or high warnings are "
            f"{', '.join(names[:-1])} and {names[-1]}."
        )

    if template_key == "emerging_kpis":
        if not emerging:
            return (
                f"No KPIs are currently flagged as emerging risks for "
                f"{month_name} {year}."
            )
        names = [r["kpi_name"] for r in emerging]
        if len(names) == 1:
            return (
                f"{names[0]} is beginning to show emerging risk indicators."
            )
        return (
            f"The KPIs beginning to show emerging risk indicators are "
            f"{', '.join(names[:-1])} and {names[-1]}."
        )

    if template_key == "watch_first":
        if priority:
            top = priority[0]
            return (
                f"Management should watch {top['kpi_name']} first. It is "
                f"ranked as the highest-priority risk with a "
                f"{top['warning_level']} and {top['actual_status'].lower()}."
            )
        return (
            f"No priority risks require management attention for "
            f"{month_name} {year}."
        )

    return _UNSUPPORTED_MSG


# ---------------------------------------------------------------------------
# Cache key helper
# ---------------------------------------------------------------------------

def build_cache_key(
    evidence: Dict[str, Any],
    question: str,
) -> str:
    """Deterministic cache key for a given evidence + question.

    The key never contains the API key. It uses the evidence content hash
    (which changes when any governed value changes) combined with the
    question text.
    """
    evidence_hash = evidence.get("_evidence_hash", "")
    canonical_question = question.strip().lower()
    base = f"risk_ai_v1:{evidence_hash}:{canonical_question}"
    return hashlib.md5(base.encode("utf-8")).hexdigest()[:24]


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _load_api_key() -> Optional[str]:
    """Read API key from environment (SENTINEL360_AI_API_KEY)."""
    import os

    key = os.getenv("SENTINEL360_AI_API_KEY", "").strip()
    return key if key else None
