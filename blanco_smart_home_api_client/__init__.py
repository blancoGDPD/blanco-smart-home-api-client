"""BLANCO Smart Home API client library.

Provides BlancoApiClient and all supporting types for integrating with the
BLANCO Smart Home Cloud API.  Typical usage::

    from blanco_smart_home_api_client import BlancoApiClient
    from blanco_smart_home_api_client.errors import BlancoAuthError

    client = BlancoApiClient(
        session,
        app_version="1.0.0",
        app_build="1",
        os_version="2026.1.0",
    )
"""

from __future__ import annotations

from .client import BlancoApiClient
from .errors import (
    ApiErrorCode,
    BlancoApiError,
    BlancoAuthError,
    BlancoConnectionError,
    BlancoDeviceTypeError,
    BlancoInvalidTokenError,
    BlancoTokenExpiredError,
)
from .http_status import HttpStatus
from .log import BlancoLogLevel, blanco_log
from .models import BlancoActionType, BlancoErrorType, BlancoWaterType
from .results import (
    AppRegistrationResult,
    AuthResult,
    DeviceActionItem,
    DeviceActionsResult,
    DeviceErrorItem,
    DeviceErrorsResult,
    DeviceEventResult,
    DeviceStatsResult,
    StatRangeResult,
    StatTotalItem,
)

__all__ = [
    # Client
    "BlancoApiClient",
    # Errors
    "ApiErrorCode",
    "BlancoApiError",
    "BlancoAuthError",
    "BlancoConnectionError",
    "BlancoDeviceTypeError",
    "BlancoInvalidTokenError",
    "BlancoTokenExpiredError",
    # HTTP utilities
    "HttpStatus",
    # Logging
    "BlancoLogLevel",
    "blanco_log",
    # Models
    "BlancoActionType",
    "BlancoErrorType",
    "BlancoWaterType",
    # Results
    "AppRegistrationResult",
    "AuthResult",
    "DeviceActionItem",
    "DeviceActionsResult",
    "DeviceErrorItem",
    "DeviceErrorsResult",
    "DeviceEventResult",
    "DeviceStatsResult",
    "StatRangeResult",
    "StatTotalItem",
]
