"""
Smoke test: manually exercise the Tencent TokenHub (hy3) live synthesis path.

Do NOT run this in automated CI - it requires real credentials.
Usage (from project root):

    python scripts/test_hunyuan_synthesis.py

Expected environment variables:
    SENTINEL360_AI_PROVIDER=tencent_hunyuan
    SENTINEL360_AI_MODEL=hy3
    SENTINEL360_AI_API_KEY=<TokenHub Bearer token>

DEBUG MODE (TEMPORARY — TokenHub response shape inspection)
-----------------------------------------------------------
This script installs a thin wrapper around
``src.ai_management_synthesis.requests.post`` so that, when a real
``requests.post`` returns from TokenHub, the raw response is inspected
and a sanitized diagnostic block is printed BEFORE the service processes
it. The wrapper delegates the actual HTTP call to the real
``requests.post``; the service's parsing logic, evidence pack, and
governance prompt are NOT modified in any way.

The diagnostic block prints ONLY:
    * HTTP status code
    * a *safe* subset of response headers (Authorization and any
      credential-like header values are redacted to ``<REDACTED>``)
    * top-level JSON keys of the response body
    * whether ``choices`` exists and its length
    * whether common TokenHub fields exist
      (``output``, ``response``, ``data``, ``message``, ``error``,
      ``request_id``)
    * sanitized error / code / message fields
    * a sanitized representation of the raw response body, with any
      credential-like fields replaced by ``<REDACTED>``

The diagnostic block NEVER prints:
    * the API key
    * the ``Authorization`` header value
    * full request headers
    * secrets
    * the request evidence payload
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict

import requests  # type: ignore[import-untyped]

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import src.ai_management_synthesis as _ai_mod  # for monkey-patching requests.post
from src.ai_management_synthesis import AIManagementSynthesisService
from src.management_evidence_pack import ManagementEvidencePack


# ---------------------------------------------------------------------------
# Sanitization helpers
# ---------------------------------------------------------------------------
# Header / field names treated as credential-like. Compared case-insensitively.
_CREDENTIAL_FIELDS = {
    "api_key", "apikey", "api-key",
    "authorization", "auth",
    "token", "access_token", "bearer_token", "session_token", "id_token",
    "secret", "secret_id", "secret_key", "secretid", "secretkey",
    "password", "passwd",
    "credential", "credentials",
    "x-api-key", "x-api-token", "x-auth-token", "x-secret",
    "cookie", "set-cookie",
}
# Substrings that, if present anywhere in a lowercased key, mark it as a credential.
_CREDENTIAL_SUBSTRINGS = (
    "api_key", "apikey", "secret", "token", "password",
    "authorization", "passwd",
)


def _is_credential_field(name: str) -> bool:
    kl = str(name).lower()
    if kl in _CREDENTIAL_FIELDS:
        return True
    return any(sub in kl for sub in _CREDENTIAL_SUBSTRINGS)


def _safe_header_subset(headers: Dict[str, str]) -> Dict[str, str]:
    """Return only non-sensitive headers, redacting anything credential-like."""
    safe: Dict[str, str] = {}
    for k, v in (headers or {}).items():
        if _is_credential_field(k):
            safe[k] = "<REDACTED>"
        else:
            safe[k] = v
    return safe


def _redact_credential_fields(obj: Any, _depth: int = 0) -> Any:
    """Recursively walk a JSON-like object and redact credential-like fields.

    - Dict keys matching credential patterns are replaced with ``<REDACTED>``.
    - String values that look like Bearer tokens or ``sk-*`` keys are masked.
    - Lists are walked element-by-element.
    """
    if _depth > 8:
        return "..."
    if isinstance(obj, dict):
        out: Dict[str, Any] = {}
        for k, v in obj.items():
            if _is_credential_field(k):
                out[k] = "<REDACTED>"
            else:
                out[k] = _redact_credential_fields(v, _depth + 1)
        return out
    if isinstance(obj, list):
        return [_redact_credential_fields(v, _depth + 1) for v in obj]
    if isinstance(obj, str):
        if obj.startswith("Bearer "):
            return "Bearer <REDACTED>"
        # Common API-key prefixes
        if obj.startswith("sk-") or obj.startswith("sk_") or obj.startswith("AKID"):
            return "<REDACTED_KEY>"
        return obj
    return obj


# ---------------------------------------------------------------------------
# Debug wrapper around requests.post
# ---------------------------------------------------------------------------
def _install_debug_wrapper() -> None:
    """Wrap ``src.ai_management_synthesis.requests.post`` for diagnostics.

    The wrapper delegates the actual HTTP call to the real
    ``requests.post``, then inspects the returned response and prints a
    sanitized diagnostic block. The original response object is returned
    unchanged so the service's parser sees the same bytes.
    """
    real_post = requests.post

    def debug_post(url, *args, **kwargs):
        resp = real_post(url, *args, **kwargs)

        # --- Request-side diagnostics (sanitized) ---
        req_method = "POST"  # this wrapper only wraps POST
        req_model = None
        req_msg_count = None
        json_body = kwargs.get("json")
        if isinstance(json_body, dict):
            req_model = json_body.get("model")
            msgs = json_body.get("messages")
            if isinstance(msgs, list):
                req_msg_count = len(msgs)

        print("")
        print("=" * 70)
        print("DEBUG: TokenHub raw response inspection (sanitized)")
        print("=" * 70)
        try:
            print(f"endpoint        : {url}")
        except Exception:
            pass
        print(f"HTTP method     : {req_method}")
        print(f"request model   : {req_model!r}")
        print(f"messages count  : {req_msg_count}")
        print(f"HTTP status code: {resp.status_code}")

        # ---- Response headers: only safe subset ----
        try:
            resp_headers = dict(resp.headers) if resp.headers else {}
        except Exception:
            resp_headers = {}
        print(
            "response headers: "
            + json.dumps(
                _safe_header_subset(resp_headers),
                ensure_ascii=False,
                indent=2,
            )
        )

        # ---- Body ----
        try:
            body_text = resp.text or ""
        except Exception as exc:
            print(f"(could not read response body: {type(exc).__name__}: {exc})")
            print("=" * 70)
            print("")
            return resp

        # Try JSON
        try:
            data = json.loads(body_text)
        except ValueError:
            preview = body_text[:500]
            print("raw body (truncated to 500 chars, sanitized):")
            print(_redact_credential_fields(preview))
            print("(body is not valid JSON)")
            print("=" * 70)
            print("")
            return resp

        if isinstance(data, dict):
            top_keys = list(data.keys())
            print(f"top-level keys  : {top_keys}")

            # choices
            choices = data.get("choices")
            if "choices" in data:
                if isinstance(choices, list):
                    print(f"'choices' present: yes (length={len(choices)})")
                    if choices:
                        try:
                            first_keys = list(choices[0].keys()) if isinstance(choices[0], dict) else []
                            print(f"choices[0] keys : {first_keys}")
                        except Exception:
                            pass
                else:
                    print(f"'choices' present: yes (type={type(choices).__name__})")
            else:
                print(f"'choices' present: no")

            # common TokenHub fields
            for field in ("output", "response", "data", "message", "error", "request_id", "usage", "model"):
                present = field in data
                print(f"  has '{field}': {present}")

            # Sanitized error / code / message
            err = data.get("error")
            if err is not None:
                print("sanitized 'error' object:")
                print(json.dumps(_redact_credential_fields(err), ensure_ascii=False, indent=2))
            else:
                code = data.get("code")
                msg = data.get("message")
                if code is not None or msg is not None:
                    print(f"sanitized top-level code/message: code={code!r}, message={msg!r}")

            # Sanitized raw body
            print("sanitized raw response body (credentials redacted):")
            print(json.dumps(_redact_credential_fields(data), ensure_ascii=False, indent=2))
        else:
            print(f"top-level type  : {type(data).__name__}")
            print("sanitized raw body:")
            print(json.dumps(_redact_credential_fields(data), ensure_ascii=False, indent=2))

        print("=" * 70)
        print("")
        return resp

    # Replace the `post` attribute on the `requests` module object that the
    # service module imported. This affects only the in-process `requests`
    # module — fine for this single-shot smoke test.
    _ai_mod.requests.post = debug_post


# ---------------------------------------------------------------------------
# Standard evidence pack (unchanged from previous version)
# ---------------------------------------------------------------------------
def _build_pack() -> ManagementEvidencePack:
    return ManagementEvidencePack(
        context={
            "hospital_id": "HOSP-001",
            "hospital_name": "St. Mary's",
            "department_id": "DEPT-ED",
            "department_name": "Emergency Department",
            "year": 2025,
            "month": 8,
            "month_label": "AUG 2025",
            "period_type": "FORECAST",
            "data_cutoff": "31 JUL 2025",
            "forecast_horizon": "AUG-DEC 2025",
        },
        priority_signal={
            "kpi_id": "kpi_001",
            "kpi_name": "Staffing Level",
            "value": 70.0,
            "value_display": "70.0%",
            "unit": "percent",
            "target_label": ">= 84.2%",
            "gap_to_target": "14.2 percentage points below target",
            "status": "Amber",
            "border_colour": "amber",
            "directionality": "HIGHER_IS_BETTER",
            "warning_level": "Escalating Warning",
            "forecast_quality": "MODERATE INDICATIVE CONFIDENCE",
            "horizon_months_ahead": 1,
            "forecast_value": 70.0,
            "forecast_indicative_range": "68.5% - 72.5%",
            "forecast_status": "Forecast deterioration",
            "risk_tier": "High",
            "operational_status": "PRIORITY MANAGEMENT REVIEW",
            "has_priority_signal": True,
        },
        forecast_provenance={
            "selected_method": "Holt-Winters",
            "forecast_quality": "MODERATE INDICATIVE CONFIDENCE",
            "horizon": "1 month ahead",
            "horizon_months_ahead": 1,
            "dominant_warning_level": "Escalating Warning",
            "forecast_capability_text": "Moderate confidence",
            "validation_mae": 2.4,
        },
        availability={
            "has_priority_signal": True,
            "has_forecast": True,
            "period_type_available": True,
            "kpi_value_available": True,
            "target_available": True,
            "warning_available": True,
            "forecast_method_available": True,
        },
        governance={
            "evidence_source": "Sentinel360 governed analytical outputs",
            "evidence_is_governed": True,
            "ai_may_calculate": False,
            "ai_may_modify_values": False,
            "ai_may_infer_missing_values": False,
            "causality_confirmed": False,
            "module": "src.management_evidence_pack",
            "schema_version": "ai1_v1",
            "scope": "executive_overview",
        },
        source_references={
            "page_state": "build_executive_page_state",
            "kpi_cards": "_build_all_kpi_cards",
            "threshold_config": "config/kpi_threshold_config.csv",
            "period_governance": "GOVERNED_ACTUAL_*",
            "forecast_method": "outputs/forecasting/...",
        },
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    provider = os.getenv("SENTINEL360_AI_PROVIDER", "")
    model = os.getenv("SENTINEL360_AI_MODEL", "")
    api_key = os.getenv("SENTINEL360_AI_API_KEY", "")

    missing = []
    if not provider:
        missing.append("SENTINEL360_AI_PROVIDER")
    if not model:
        missing.append("SENTINEL360_AI_MODEL")
    if not api_key:
        missing.append("SENTINEL360_AI_API_KEY")

    if missing:
        print(f"SKIP - live credentials not configured. Missing: {', '.join(missing)}")
        return 0

    # Install debug wrapper BEFORE constructing the service so that the
    # wrapper is in place when the service makes its first `requests.post`.
    _install_debug_wrapper()

    pack = _build_pack()
    svc = AIManagementSynthesisService(
        provider=provider,
        model=model,
        api_key=api_key,
        timeout=10,
        temperature=0.2,
    )

    result = svc.synthesize(pack)
    print(f"status        : {result.status}")
    print(f"model_provider: {result.model_provider}")
    print(f"model_name    : {result.model_name}")
    print(f"duration_sec  : {result.response_duration_seconds}")
    if result.status == "OK":
        print(f"headline              : {result.headline}")
        print(f"situation             : {result.situation}")
        print(f"management_significance: {result.management_significance}")
        print(f"next_step             : {result.next_step}")
        print(f"governance_note       : {result.governance_note}")
    else:
        print(f"message       : {result.message}")
    return 0 if result.status == "OK" else 1


if __name__ == "__main__":
    sys.exit(main())
