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
# Central log-level setting — change this value during development
# ---------------------------------------------------------------
LOG_LEVEL: BlancoLogLevel = BlancoLogLevel.DEBUG
"""Active log verbosity level. Set to NONE in production to silence all client logs."""


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
