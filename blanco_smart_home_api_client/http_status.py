"""HTTP status codes relevant to the BLANCO Smart Home API."""

from __future__ import annotations

from enum import IntEnum


class HttpStatus(IntEnum):
    """Relevant HTTP status codes used by the BLANCO API client."""

    OK = 200
    """Request completed successfully."""
    BAD_REQUEST = 400
    """Malformed or invalid request."""
    UNAUTHORIZED = 401
    """Authentication required or token expired."""
    FORBIDDEN = 403
    """Authenticated but not permitted to perform the operation."""
    NOT_FOUND = 404
    """Requested resource does not exist."""
    INTERNAL_SERVER_ERROR = 500
    """Unexpected server-side error."""
    BAD_GATEWAY = 502
    """Upstream service returned an invalid response."""
    SERVICE_UNAVAILABLE = 503
    """Service is temporarily unavailable."""
    GATEWAY_TIMEOUT = 504
    """Upstream service did not respond within the gateway timeout window."""
