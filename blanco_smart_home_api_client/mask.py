"""Masking utilities for the BLANCO Smart Home API client.

All functions that truncate or redact sensitive values before they appear in
log output, diagnostics, or any other externally visible string live here.
"""

from __future__ import annotations

import copy
from typing import Any

# ── HTTP headers ───────────────────────────────────────────────────────────────

_SENSITIVE_HEADERS: frozenset[str] = frozenset(
    {"Authorization", "X-Api-Key", "X-App-Id"}
)
# Header names whose values are truncated before logging.

_HEADER_MASK_LENGTH = 20
# Maximum number of characters shown for sensitive header values.


def mask_headers(headers: dict[str, str]) -> dict[str, str]:
    """Return a copy of *headers* with sensitive values truncated to 20 chars.

    The keys listed in ``_SENSITIVE_HEADERS`` (Authorization, X-Api-Key,
    X-App-Id) are truncated to ``_HEADER_MASK_LENGTH`` characters followed by
    ``...`` when their value exceeds that length.
    """
    return {
        k: (v[:_HEADER_MASK_LENGTH] + "...")
        if k in _SENSITIVE_HEADERS and len(v) > _HEADER_MASK_LENGTH
        else v
        for k, v in headers.items()
    }


# ── Device / App IDs ───────────────────────────────────────────────────────────

_DEV_ID_VISIBLE = 8
# Number of leading characters of a dev_id kept visible for log correlation.


def mask_dev_id(value: str | None) -> str:
    """Return *value* with all but the first 8 characters replaced by '...'.

    Used when logging dev_id values to avoid leaking the full SHA-256 hash
    while still providing enough context for log correlation.
    """
    if not value:
        return ""
    return value[:_DEV_ID_VISIBLE] + "..." if len(value) > _DEV_ID_VISIBLE else value


# ── Response bodies ────────────────────────────────────────────────────────────

_SENSITIVE_BODY_KEYS: frozenset[str] = frozenset({"token"})
# Response body keys whose values are truncated in log output.

_BODY_MASK_LENGTH = 20
# Maximum number of characters shown for sensitive body field values.


def mask_response_body(body: dict[str, Any] | None) -> dict[str, Any] | None:
    """Return a deep copy of *body* with sensitive result fields truncated to 20 chars.

    Any ``token`` field inside the ``results`` list is truncated to
    ``_BODY_MASK_LENGTH`` characters followed by ``...``.  All other fields
    are left unchanged.  Returns *body* unchanged when it is falsy.
    """
    if not body:
        return body
    masked: dict[str, Any] = copy.deepcopy(body)
    for result in masked.get("results") or []:
        if not isinstance(result, dict):
            continue
        for key in _SENSITIVE_BODY_KEYS:
            value = result.get(key)
            if isinstance(value, str) and len(value) > _BODY_MASK_LENGTH:
                result[key] = value[:_BODY_MASK_LENGTH] + "..."
    return masked
