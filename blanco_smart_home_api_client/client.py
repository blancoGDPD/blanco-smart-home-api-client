"""HTTP API client for the BLANCO Smart Home API."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .config import (
    API_APP_REGISTRATIONS_ENDPOINT,
    API_AUTH_ENDPOINT,
    API_BASE_URL,
    API_DEVICES_ENDPOINT,
    API_KEY,
)
from .errors import (
    ApiErrorCode,
    BlancoApiError,
    BlancoAuthError,
    BlancoConnectionError,
    BlancoDeviceTypeError,
    BlancoInvalidTokenError,
    BlancoTokenExpiredError,
)
from .results import (
    AppRegistrationResult,
    AuthResult,
    DeviceActionsResult,
    DeviceErrorsResult,
    DeviceEventResult,
    DeviceStatsResult,
    _parse_actions,
    _parse_errors,
    _parse_event,
    _parse_stats,
)
from .http_status import HttpStatus
from .log import BlancoLogLevel, blanco_log
from .mask import mask_dev_id, mask_headers, mask_response_body

_LOGGER = logging.getLogger(__name__)

# ── Re-exports (allow callers to import errors from this module) ───────────────

__all__ = [
    "BlancoApiClient",
    "BlancoApiError",
    "BlancoAuthError",
    "BlancoConnectionError",
    "BlancoDeviceTypeError",
    "BlancoInvalidTokenError",
    "BlancoTokenExpiredError",
    "AppRegistrationResult",
    "AuthResult",
    "DeviceActionsResult",
    "DeviceErrorsResult",
    "DeviceEventResult",
    "DeviceStatsResult",
]

# ── API client ────────────────────────────────────────────────────────────────


class BlancoApiClient:
    """HTTP client for the BLANCO Smart Home API.

    Encapsulates every HTTP interaction: app registration, authentication,
    token renewal, and device data polling.  Callers receive typed result
    objects and handle the ``BlancoApiError`` subclass exceptions raised here.

    All requests include the static headers built from the constructor
    parameters automatically.  Sensitive values (Authorization, X-Api-Key,
    X-App-Id, dev_id) are masked in log output.

    Args:
        session: Shared aiohttp client session managed by the caller.
        app_id: App identifier issued by POST /apps/registrations.
        token: Bearer token issued by POST /auth/token.
        token_type: Token type string (default: ``"Bearer"``).
        app_version: Integration or application version string sent in
            ``X-App-Version`` (e.g. ``"1.0.0"``).
        app_build: Integration or application build number sent in
            ``X-App-Build`` (e.g. ``"1"``).
        os_version: Host OS / platform version sent in ``X-OS-Version``
            (e.g. the Home Assistant version string).
    """

    def __init__(
        self,
        session: aiohttp.ClientSession,
        *,
        app_id: str = "",
        token: str = "",
        token_type: str = "Bearer",
        app_version: str = "",
        app_build: str = "",
        os_version: str = "",
    ) -> None:
        """Initialise the client with a shared aiohttp session and optional credentials."""
        self._session = session
        self._app_id = app_id
        self._token = token
        self._token_type = token_type
        # Build static headers once per instance from the provided metadata.
        self._static_headers: dict[str, str] = {
            "User-Agent": "ha-blanco",
            "X-App-Version": app_version,
            "X-App-Build": app_build,
            "X-OS-Type": "HomeAssistant",
            "X-OS-Version": os_version,
        }

    def update_authorization(self, token: str, token_type: str) -> None:
        """Update the stored auth token (called after a successful token renewal)."""
        self._token = token
        self._token_type = token_type

    def update_app_id(self, app_id: str) -> None:
        """Update the stored app ID (called after successful app registration)."""
        self._app_id = app_id

    # ── Internal header builders ──────────────────────────────────────────────

    def _api_key_headers(self) -> dict[str, str]:
        """Build minimal headers: API key + static headers (no auth token)."""
        return {"X-Api-Key": API_KEY, **self._static_headers}

    def _app_headers(self) -> dict[str, str]:
        """Build headers with API key + app ID + static headers (no auth token)."""
        return {"X-Api-Key": API_KEY, "X-App-Id": self._app_id, **self._static_headers}

    def _auth_headers(self) -> dict[str, str]:
        """Build fully-authenticated headers including Bearer token."""
        return {
            "Authorization": f"{self._token_type} {self._token}",
            "X-Api-Key": API_KEY,
            "X-App-Id": self._app_id,
            **self._static_headers,
        }

    # ── App registration ──────────────────────────────────────────────────────

    async def register_app(self, locale: str) -> AppRegistrationResult:
        """POST /apps/registrations — register a new app instance.

        Stores the returned app_id on the client for use in subsequent calls.

        Raises:
            BlancoConnectionError: Network failure or non-2xx response.
        """
        url = f"{API_BASE_URL}{API_APP_REGISTRATIONS_ENDPOINT}"
        headers = self._api_key_headers()
        payload: dict[str, Any] = {"app_locale": locale}
        blanco_log(_LOGGER, BlancoLogLevel.DEBUG, "POST %s", url)
        blanco_log(_LOGGER, BlancoLogLevel.TRACE, "  headers=%s", mask_headers(headers))
        blanco_log(_LOGGER, BlancoLogLevel.TRACE, "  payload=%s", payload)
        try:
            async with self._session.post(
                url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                body = await resp.json(content_type=None)
                blanco_log(
                    _LOGGER, BlancoLogLevel.DEBUG, "POST %s → %s", url, resp.status
                )
                blanco_log(_LOGGER, BlancoLogLevel.TRACE, "  response=%s", body)
                if resp.status != HttpStatus.OK:
                    blanco_log(
                        _LOGGER,
                        BlancoLogLevel.WARNING,
                        "App registration failed: HTTP %s",
                        resp.status,
                    )
                    raise BlancoConnectionError(
                        f"App registration failed: HTTP {resp.status}"
                    )
        except BlancoConnectionError:
            raise
        except aiohttp.ClientError as err:
            blanco_log(
                _LOGGER, BlancoLogLevel.WARNING, "POST %s → ClientError: %s", url, err
            )
            raise BlancoConnectionError(f"App registration failed: {err}") from err

        app_id = (body.get("results") or [{}])[0].get("app_id")
        if not app_id:
            raise BlancoConnectionError("App registration response contained no app_id")
        self.update_app_id(str(app_id))
        return AppRegistrationResult(app_id=str(app_id))

    async def update_app_locale(self, new_locale: str) -> bool:
        """PUT /apps/registrations — update the locale for the registered app.

        Returns True on HTTP 200 (success), False on any non-2xx status
        (warning is logged).

        Raises:
            BlancoConnectionError: Network failure.
        """
        url = f"{API_BASE_URL}{API_APP_REGISTRATIONS_ENDPOINT}"
        headers = self._app_headers()
        payload: dict[str, Any] = {"app_locale": new_locale}
        blanco_log(_LOGGER, BlancoLogLevel.DEBUG, "PUT %s", url)
        blanco_log(_LOGGER, BlancoLogLevel.TRACE, "  headers=%s", mask_headers(headers))
        blanco_log(_LOGGER, BlancoLogLevel.TRACE, "  payload=%s", payload)
        try:
            async with self._session.put(
                url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                blanco_log(
                    _LOGGER, BlancoLogLevel.DEBUG, "PUT %s → %s", url, resp.status
                )
                if resp.status != HttpStatus.OK:
                    blanco_log(
                        _LOGGER,
                        BlancoLogLevel.WARNING,
                        "Failed to update app locale: HTTP %s",
                        resp.status,
                    )
                    return False
        except aiohttp.ClientError as err:
            blanco_log(
                _LOGGER, BlancoLogLevel.WARNING, "PUT %s → ClientError: %s", url, err
            )
            raise BlancoConnectionError(f"Locale update failed: {err}") from err
        return True

    async def deregister_app(self) -> None:
        """DELETE /apps/registrations — deregister the app from the BLANCO API.

        Non-2xx responses are logged as warnings but do not raise.

        Raises:
            BlancoConnectionError: Network failure.
        """
        url = f"{API_BASE_URL}{API_APP_REGISTRATIONS_ENDPOINT}"
        headers = self._auth_headers()
        blanco_log(_LOGGER, BlancoLogLevel.DEBUG, "DELETE %s", url)
        blanco_log(_LOGGER, BlancoLogLevel.TRACE, "  headers=%s", mask_headers(headers))
        try:
            async with self._session.delete(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                blanco_log(
                    _LOGGER, BlancoLogLevel.DEBUG, "DELETE %s → %s", url, resp.status
                )
                if resp.status != HttpStatus.OK:
                    blanco_log(
                        _LOGGER,
                        BlancoLogLevel.WARNING,
                        "App deregistration failed: HTTP %s",
                        resp.status,
                    )
        except aiohttp.ClientError as err:
            blanco_log(
                _LOGGER, BlancoLogLevel.WARNING, "DELETE %s → ClientError: %s", url, err
            )
            raise BlancoConnectionError(f"App deregistration failed: {err}") from err

    # ── Authentication ────────────────────────────────────────────────────────

    async def authenticate(self, dev_id: str) -> AuthResult:
        """POST /auth/token — authenticate a device and return token details.

        Stores the returned token on the client via update_authorization().

        Raises:
            BlancoConnectionError: Network failure or unexpected non-2xx status.
            BlancoAuthError: HTTP 401 (access not yet granted via BLANCO UNIT App).
            BlancoInvalidTokenError: HTTP 200 response contained no token field.
            BlancoDeviceTypeError: API error code indicates unsupported device type.
        """
        url = f"{API_BASE_URL}{API_AUTH_ENDPOINT}"
        headers = self._app_headers()
        payload: dict[str, Any] = {"dev_id": dev_id, "service": 1}
        masked_payload = {**payload, "dev_id": mask_dev_id(dev_id)}
        blanco_log(_LOGGER, BlancoLogLevel.DEBUG, "POST %s", url)
        blanco_log(_LOGGER, BlancoLogLevel.TRACE, "  headers=%s", mask_headers(headers))
        blanco_log(_LOGGER, BlancoLogLevel.TRACE, "  payload=%s", masked_payload)
        try:
            async with self._session.post(
                url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                body = await resp.json(content_type=None)
                blanco_log(
                    _LOGGER, BlancoLogLevel.DEBUG, "POST %s → %s", url, resp.status
                )
                blanco_log(
                    _LOGGER,
                    BlancoLogLevel.TRACE,
                    "  response=%s",
                    mask_response_body(body),
                )
                if resp.status != HttpStatus.OK:
                    error_codes = [
                        e.get("code") for e in (body or {}).get("errors", [])
                    ]
                    if ApiErrorCode.DEVICE_TYPE_NOT_SUPPORTED in error_codes:
                        raise BlancoDeviceTypeError("Device type not supported")
                    if resp.status == HttpStatus.UNAUTHORIZED:
                        raise BlancoAuthError(
                            f"Authentication failed: HTTP {resp.status}"
                        )
                    raise BlancoConnectionError(
                        f"Authentication failed: HTTP {resp.status}"
                    )
        except BlancoApiError:
            raise
        except aiohttp.ClientError as err:
            blanco_log(
                _LOGGER, BlancoLogLevel.WARNING, "POST %s → ClientError: %s", url, err
            )
            raise BlancoConnectionError(f"Authentication failed: {err}") from err

        result = (body.get("results") or [{}])[0]
        token = result.get("token")
        if not token:
            raise BlancoInvalidTokenError("Authentication response contained no token")
        self.update_authorization(str(token), str(result.get("token_type", "Bearer")))
        return AuthResult(
            token=str(token),
            token_type=str(result.get("token_type", "Bearer")),
            dev_type=result.get("dev_type"),
        )

    async def renew_token(self, dev_id: str) -> AuthResult:
        """POST /auth/token for token renewal — identical to authenticate().

        Provided as a named alias so call sites clearly express their intent.

        Raises:
            BlancoApiError: Any subclass raised by authenticate().
        """
        return await self.authenticate(dev_id)

    # ── Device data ───────────────────────────────────────────────────────────

    async def _get_device_endpoint(
        self, url: str, dev_id: str
    ) -> tuple[int, dict[str, Any]]:
        """GET *url* using full auth headers; return (status_code, body).

        Raises:
            BlancoTokenExpiredError: HTTP 401 response (token needs renewal).
            BlancoConnectionError: Network failure.
        """
        masked_url = url.replace(dev_id, mask_dev_id(dev_id)) if dev_id else url
        headers = self._auth_headers()
        blanco_log(_LOGGER, BlancoLogLevel.DEBUG, "GET %s", masked_url)
        blanco_log(_LOGGER, BlancoLogLevel.TRACE, "  headers=%s", mask_headers(headers))
        try:
            async with self._session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                body = await resp.json(content_type=None)
                blanco_log(
                    _LOGGER,
                    BlancoLogLevel.DEBUG,
                    "GET %s → %s",
                    masked_url,
                    resp.status,
                )
                blanco_log(_LOGGER, BlancoLogLevel.TRACE, "  response=%s", body)
                if resp.status == HttpStatus.UNAUTHORIZED:
                    raise BlancoTokenExpiredError(
                        f"Token expired: HTTP 401 on {masked_url}"
                    )
                return resp.status, body
        except BlancoTokenExpiredError:
            raise
        except aiohttp.ClientError as err:
            blanco_log(
                _LOGGER,
                BlancoLogLevel.WARNING,
                "GET %s → ClientError: %s",
                masked_url,
                err,
            )
            raise BlancoConnectionError(f"GET {masked_url} failed: {err}") from err

    async def get_device_system(self, dev_id: str) -> tuple[int, DeviceEventResult]:
        """GET /devices/{dev_id}/system — return (status_code, DeviceEventResult)."""
        url = f"{API_BASE_URL}{API_DEVICES_ENDPOINT}/{dev_id}/system"
        status, body = await self._get_device_endpoint(url, dev_id)
        return status, _parse_event(body)

    async def get_device_status(self, dev_id: str) -> tuple[int, DeviceEventResult]:
        """GET /devices/{dev_id}/status — return (status_code, DeviceEventResult)."""
        url = f"{API_BASE_URL}{API_DEVICES_ENDPOINT}/{dev_id}/status"
        status, body = await self._get_device_endpoint(url, dev_id)
        return status, _parse_event(body)

    async def get_device_settings(self, dev_id: str) -> tuple[int, DeviceEventResult]:
        """GET /devices/{dev_id}/settings — return (status_code, DeviceEventResult)."""
        url = f"{API_BASE_URL}{API_DEVICES_ENDPOINT}/{dev_id}/settings"
        status, body = await self._get_device_endpoint(url, dev_id)
        return status, _parse_event(body)

    async def get_device_errors(self, dev_id: str) -> tuple[int, DeviceErrorsResult]:
        """GET /devices/{dev_id}/errors — return (status_code, DeviceErrorsResult)."""
        url = f"{API_BASE_URL}{API_DEVICES_ENDPOINT}/{dev_id}/errors"
        status, body = await self._get_device_endpoint(url, dev_id)
        return status, _parse_errors(body)

    async def get_device_actions(
        self,
        dev_id: str,
        from_ts: int = 0,
        count: int = 300,
        asc: bool = True,
    ) -> tuple[int, DeviceActionsResult]:
        """GET /devices/{dev_id}/actions — return (status_code, DeviceActionsResult).

        Args:
            dev_id: Device identifier.
            from_ts: Include only actions with evt_ts >= this value (milliseconds).
            count: Maximum number of actions to return per page.
            asc: When True, results are sorted oldest-first (ascending evt_ts).
        """
        asc_param = 1 if asc else 0
        url = (
            f"{API_BASE_URL}{API_DEVICES_ENDPOINT}/{dev_id}"
            f"/actions?from={from_ts}&cnt={count}&asc={asc_param}"
        )
        status, body = await self._get_device_endpoint(url, dev_id)
        return status, _parse_actions(body)

    async def get_device_stats(
        self,
        dev_id: str,
        ranges: list[dict[str, Any]],
    ) -> tuple[int, DeviceStatsResult]:
        """POST /devices/{dev_id}/stats — fetch aggregated water statistics.

        Args:
            dev_id: Device identifier.
            ranges: List of time-range descriptors specifying the periods to aggregate.

        Raises:
            BlancoTokenExpiredError: HTTP 401 response (token needs renewal).
            BlancoConnectionError: Network failure.
        """
        url = f"{API_BASE_URL}{API_DEVICES_ENDPOINT}/{dev_id}/stats"
        masked_url = url.replace(dev_id, mask_dev_id(dev_id)) if dev_id else url
        headers = self._auth_headers()
        payload: dict[str, Any] = {"ranges": ranges}
        blanco_log(_LOGGER, BlancoLogLevel.DEBUG, "POST %s", masked_url)
        blanco_log(_LOGGER, BlancoLogLevel.TRACE, "  headers=%s", mask_headers(headers))
        blanco_log(_LOGGER, BlancoLogLevel.TRACE, "  payload=%s", payload)
        try:
            async with self._session.post(
                url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                body = await resp.json(content_type=None)
                blanco_log(
                    _LOGGER,
                    BlancoLogLevel.DEBUG,
                    "POST %s → %s",
                    masked_url,
                    resp.status,
                )
                blanco_log(_LOGGER, BlancoLogLevel.TRACE, "  response=%s", body)
                if resp.status == HttpStatus.UNAUTHORIZED:
                    raise BlancoTokenExpiredError(
                        f"Token expired: HTTP 401 on {masked_url}"
                    )
                return resp.status, _parse_stats(body)
        except BlancoTokenExpiredError:
            raise
        except aiohttp.ClientError as err:
            blanco_log(
                _LOGGER,
                BlancoLogLevel.WARNING,
                "POST %s → ClientError: %s",
                masked_url,
                err,
            )
            raise BlancoConnectionError(f"POST {masked_url} failed: {err}") from err
