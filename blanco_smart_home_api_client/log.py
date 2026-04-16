"""Logging utilities for the BLANCO Smart Home API client."""

from __future__ import annotations

import logging
from enum import IntEnum


class BlancoLogLevel(IntEnum):
    """Log verbosity levels for the BLANCO API client."""

    NONE = 0
    """Suppress all log output from the client."""
    ERROR = 1
    """Log only unrecoverable errors."""
    WARNING = 2
    """Log errors and recoverable warnings."""
    INFO = 3
    """Log errors, warnings, and key request/response events."""
    DEBUG = 4
    """Log request and response lines (method, URL, status code)."""
    TRACE = 5
    """Log everything including full headers, payloads, and response bodies."""


# ---------------------------------------------------------------
# Central log-level setting — raise to TRACE during development
# to see request headers, payloads, and response bodies.
# ---------------------------------------------------------------
LOG_LEVEL: BlancoLogLevel = BlancoLogLevel.DEBUG
"""Active log verbosity level for the BLANCO API client.

At the default level (DEBUG), all request/response lines (method, URL, status
code) are emitted via Python's standard logging infrastructure.  The caller
controls what actually appears by configuring the ``blanco_smart_home_api_client``
logger (e.g. setting its level to WARNING suppresses DEBUG output).

Raise to TRACE to also log full request headers, payloads, and response bodies —
useful during development but not recommended in production as it exposes
sensitive values such as API keys and bearer tokens.
"""


def blanco_log(
    logger: logging.Logger, level: BlancoLogLevel, msg: str, *args: object
) -> None:
    """Emit *msg* only when LOG_LEVEL >= *level*, using the matching Python level."""
    if LOG_LEVEL < level:
        return
    if level <= BlancoLogLevel.ERROR:
        logger.error(msg, *args)
    elif level == BlancoLogLevel.WARNING:
        logger.warning(msg, *args)
    elif level == BlancoLogLevel.INFO:
        logger.info(msg, *args)
    elif level == BlancoLogLevel.DEBUG:
        logger.debug(msg, *args)
    else:
        logger.log(5, msg, *args)  # 5 = TRACE level
