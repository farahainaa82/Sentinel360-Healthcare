"""
Shared TokenHub / Hy3 HTTP transport for Sentinel360.

Single, authoritative implementation of the live TokenHub chat-completions
call so that synthesis services (management, connected signal, and any
future Hy3 consumer) all use the same wire format, error mapping, and
response normalisation.

Public surface:

    call_tokenhub_chat_completion(
        messages,
        *,
        provider,
        model,
        api_key,
        timeout,
        temperature,
        max_tokens,
        tokenhub_url=DEFAULT_TOKENHUB_URL,
    ) -> dict

    Returns one of:

      {
        "status": "OK",
        "message": "<concatenated assistant message>",
        "raw": <full decoded response body>,
      }

      {
        "status": "TIMEOUT",
        "message": "TokenHub request timed out.",
        "raw": None,
      }

      {
        "status": "API_UNAVAILABLE",
        "message": "TokenHub endpoint returned HTTP <status>.",
        "raw": None | <decoded body>,
      }

      {
        "status": "PROVIDER_ERROR",
        "message": "<TokenHub-provided error message>",
        "raw": <decoded body>,
      }

      {
        "status": "INVALID_RESPONSE",
        "message": "<reason>",
        "raw": <decoded body>,
      }

      {
        "status": "NOT_CONFIGURED",
        "message": "TokenHub API key is not configured.",
        "raw": None,
      }

Notes
-----
* This module uses the standard library only (urllib). It does not pull in
  any new third-party dependency.
* If a different SDK / proxy / agent runner is wired in by future work,
  it should replace only this module. Higher-level synthesis services
  should continue to import :func:`call_tokenhub_chat_completion`.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

DEFAULT_TOKENHUB_URL = (
    "https://tokenhub-intl.tencentcloudmaas.com/v1/chat/completions"
)


def _safe_read_body(http_error):
    """Best-effort decode of an HTTP error body (JSON if possible)."""
    try:
        body = http_error.read()
    except Exception:
        return None
    try:
        text = body.decode("utf-8")
    except Exception:
        return None
    try:
        return json.loads(text)
    except Exception:
        return text


def _format_message(text):
    """Return *text* with stripped outer whitespace."""
    if not isinstance(text, str):
        return ""
    return text.strip()


def call_tokenhub_chat_completion(
    messages: List[Dict[str, str]],
    *,
    provider: str,
    model: str,
    api_key: Optional[str],
    timeout: float,
    temperature: float,
    max_tokens: int,
    tokenhub_url: str = DEFAULT_TOKENHUB_URL,
) -> Dict[str, Any]:
    """Single authoritative TokenHub chat-completions call.

    ``provider`` is the Sentinel360 internal provider name
    (e.g. ``SENTINEL360_AI_PROVIDER``); it is accepted for symmetry with
    the rest of the AI config but does not change the wire format -- the
    TokenHub endpoint URL is fixed.

    The function never raises. Errors are mapped into the documented
    ``status`` codes so synthesis services can decide how to fall back
    without having to handle HTTP exceptions themselves.
    """

    if not api_key:
        return {
            "status": "NOT_CONFIGURED",
            "message": "TokenHub API key is not configured.",
            "raw": None,
        }

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + str(api_key),
    }

    request = urllib.request.Request(
        tokenhub_url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status_code = getattr(response, "status", None) or response.getcode()
            raw_bytes = response.read()
    except urllib.error.HTTPError as exc:
        raw_body = _safe_read_body(exc)
        return {
            "status": "API_UNAVAILABLE",
            "message": "TokenHub endpoint returned HTTP " + str(exc.code) + ".",
            "raw": raw_body,
        }
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", None)
        reason_text = str(reason or "").lower()
        if "timed out" in reason_text or "timeout" in reason_text:
            return {
                "status": "TIMEOUT",
                "message": "TokenHub request timed out.",
                "raw": None,
            }
        return {
            "status": "API_UNAVAILABLE",
            "message": "TokenHub endpoint is not reachable: " + str(reason) + ".",
            "raw": None,
        }
    except Exception as exc:  # defensive guard -- never raise
        return {
            "status": "PROVIDER_ERROR",
            "message": "Unexpected TokenHub transport error: " + str(exc) + ".",
            "raw": None,
        }

    try:
        decoded = json.loads(raw_bytes.decode("utf-8"))
    except Exception:
        return {
            "status": "INVALID_RESPONSE",
            "message": "TokenHub returned a non-JSON response.",
            "raw": None,
        }

    if status_code >= 400:
        return {
            "status": "API_UNAVAILABLE",
            "message": "TokenHub endpoint returned HTTP " + str(status_code) + ".",
            "raw": decoded,
        }

    if not isinstance(decoded, dict):
        return {
            "status": "INVALID_RESPONSE",
            "message": "TokenHub returned a non-object response.",
            "raw": decoded,
        }

    provider_error = decoded.get("error")
    if provider_error:
        if isinstance(provider_error, dict):
            err_msg = (
                provider_error.get("message")
                or provider_error.get("type")
                or "TokenHub provider error."
            )
        else:
            err_msg = str(provider_error)
        return {
            "status": "PROVIDER_ERROR",
            "message": _format_message(err_msg),
            "raw": decoded,
        }

    choices = decoded.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict):
            message_obj = first.get("message")
            if isinstance(message_obj, dict):
                content = message_obj.get("content")
                if isinstance(content, str) and content.strip():
                    return {
                        "status": "OK",
                        "message": _format_message(content),
                        "raw": decoded,
                    }

    return {
        "status": "INVALID_RESPONSE",
        "message": "TokenHub response did not contain a chat message.",
        "raw": decoded,
    }
