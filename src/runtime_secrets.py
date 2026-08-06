"""Central cloud-safe secret resolution for Sentinel360.

This helper exists so that the same configuration value can be obtained
from **two** different runtime sources without duplication at every
call site:

  1. ``streamlit`` (Community Cloud ``st.secrets`` map), and
  2. OS environment variables (``os.getenv``).

Resolution order is **secrets first, then env**. This matches the
canonical Streamlit Community Cloud deployment pattern: credentials
live in the cloud's Secrets manager and the running app reads them
via ``st.secrets``.

On plain localhost -- where ``st.secrets`` is unavailable, no
``secrets.toml`` exists, or Streamlit isn't even importable -- the
helper transparently falls back to ``os.getenv`` and ultimately the
caller-supplied default. Existing localhost flows that set
``SENTINEL360_AI_*`` as OS environment variables continue to work
unchanged.

The helper is deliberately minimal so it can be unit-tested in
isolation and used from any module that needs cloud-portable
configuration without leaking Streamlit imports into code paths that
must otherwise remain UI-framework-agnostic (e.g. background jobs,
test runners, smoke scripts).
"""

from __future__ import annotations

import os
from typing import Any, Optional


__all__ = ["get_runtime_secret"]


def _read_streamlit_secret(name: str) -> Optional[str]:
    """Try to read ``name`` from ``st.secrets`` if Streamlit is importable.

    Returns the string value if found, otherwise ``None``. Never raises:
    any failure -- import error, attribute error, missing key, file not
    found, no script run context -- is swallowed and treated as "no
    secret available", so the caller can cleanly fall back to ``os.getenv``.
    """
    try:
        import streamlit as _st  # type: ignore  # noqa: F401
    except Exception:
        return None

    try:
        secrets_obj = getattr(_st, "secrets", None)
    except Exception:
        return None
    if secrets_obj is None:
        return None

    val: Any = None
    try:
        # ``StreamlitSecret`` supports ``__contains__`` + ``__getitem__``;
        # using ``in`` first avoids raising on missing keys.
        if name in secrets_obj:
            val = secrets_obj[name]
    except Exception:
        return None

    if val is None:
        return None
    try:
        sval = str(val).strip()
    except Exception:
        return None
    return sval or None


def get_runtime_secret(
    name: str,
    default: Optional[str] = None,
) -> Optional[str]:
    """Resolve a runtime configuration value portably.

    Lookup order:
      1. ``st.secrets[name]`` if Streamlit is available and the key is set.
      2. ``os.getenv(name)`` (works on localhost + any CI shell).
      3. The supplied ``default``.

    Empty strings and whitespace-only values from either source are
    treated as "not set" so the next source / default is consulted.
    The function always returns a ``str`` or the original ``default``
    object untouched.
    """
    if not isinstance(name, str) or not name:
        return default

    st_val = _read_streamlit_secret(name)
    if st_val is not None:
        return st_val

    try:
        env_val = os.getenv(name, default)
    except Exception:
        return default
    if env_val is None:
        return default
    if isinstance(env_val, str):
        stripped = env_val.strip()
        return stripped if stripped else default
    return env_val
