"""API error codes and exception hierarchy for the BLANCO Smart Home API.

ApiErrorCode enumerates every numeric error code the API can return in the
errors[].code field of a response.  The exception classes below are raised
by BlancoApiClient and can be imported by callers without pulling in the
full HTTP client.
"""

from __future__ import annotations

from enum import IntEnum


class ApiErrorCode(IntEnum):
    """API error codes returned in the errors[].code field of every response."""

    # Fallback
    UNDEFINED = 0
    """Undefined error code — used as a safe fallback for unrecognised values."""
    UNKNOWN = 1
    """Unknown error as fallback for all non-specified errors."""
    EXCEPTION = 2
    """An exception occurred on the server side."""

    # Common request (1000..1999)
    BAD_REQUEST = 1000
    """Generic bad-request error."""
    BAD_REQUEST_MISSING_PARAM = 1001
    """Bad request due to missing parameter(s)."""
    BAD_REQUEST_INVALID_PARAM = 1002
    """Bad request due to invalid parameter(s)."""
    BAD_REQUEST_VALIDATION_FAILED = 1003
    """Bad request due to failed validation."""
    ACCESS_DENIED = 1100
    """Access denied for the requested resource."""
    FORBIDDEN = 1200
    """Caller is authenticated but not permitted to access the resource."""

    # Auth (2000..2999)
    UNAUTHORIZED = 2000
    """Generic unauthorised error."""
    UNAUTHORIZED_NO_ACCESS = 2001
    """Unauthorized because requesting account or access key does not exist."""
    UNAUTHORIZED_MISSING_PERMISSION = 2002
    """Unauthorized due to missing permission(s)."""
    UNAUTHORIZED_ACCESS_BLOCKED = 2003
    """Unauthorized because account or access key is blocked."""
    UNAUTHORIZED_ACCESS_EXPIRED = 2004
    """Unauthorized because account or access key is expired."""
    UNAUTHORIZED_TOKEN_EXPIRED = 2005
    """Unauthorized because access token (JWT) is expired."""

    # App (3000..3999)
    APP_ID_MISSING = 3000
    """Required app identifier is missing."""
    APP_ID_NOT_EXISTING = 3001
    """App identifier does not exist."""
    APP_ID_BLOCKED = 3002
    """App identifier is blocked."""
    APP_ID_EXPIRED = 3003
    """App identifier is expired."""
    APP_ACCESS_DENIED = 3100
    """App access denied."""

    # Device (4000..4999)
    DEVICE_ID_MISSING = 4000
    """Required device identifier is missing."""
    DEVICE_ID_NOT_EXISTING = 4001
    """Device with given identifier does not exist."""
    DEVICE_ID_BLOCKED = 4002
    """Device with identifier is blocked."""
    DEVICE_ID_EXPIRED = 4003
    """Device identifier is expired."""
    DEVICE_ACCESS_DENIED = 4100
    """Device access denied."""
    DEVICE_TYPE_NOT_SUPPORTED = 4200
    """Device type not supported."""

    # Functions (6000..6999)
    FUNCTION_MISSING = 6000
    """Required function is missing."""
    FUNCTION_NOT_SUPPORTED = 6001
    """Requested function is not supported."""

    # Development (9000..9999)
    NOT_IMPLEMENTED = 9000
    """Function or endpoint not implemented (yet)."""


class BlancoApiError(Exception):
    """Base exception for all BLANCO API errors."""


class BlancoConnectionError(BlancoApiError):
    """Network or transport error when contacting the BLANCO API."""


class BlancoAuthError(BlancoApiError):
    """HTTP 401 returned by the auth endpoint — access not yet granted."""


class BlancoInvalidTokenError(BlancoApiError):
    """Auth call succeeded (HTTP 200) but the response contained no token."""


class BlancoDeviceTypeError(BlancoApiError):
    """Device type not supported by the BLANCO Smart Home API."""


class BlancoTokenExpiredError(BlancoApiError):
    """HTTP 401 returned by a device data endpoint — auth token has expired."""
