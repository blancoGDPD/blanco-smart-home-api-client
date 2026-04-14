# blanco-smart-home-api-client

Async Python client library for the BLANCO Smart Home Cloud API.

- **PyPI package name:** `blanco-smart-home-api-client`
- **Import name:** `blanco_smart_home_api_client`
- **Requires:** Python ≥ 3.13, aiohttp ≥ 3.9
- **License:** MIT

---

## Installation

```bash
pip install blanco-smart-home-api-client
```

---

## Usage

### Basic setup

```python
import aiohttp
from blanco_smart_home_api_client import BlancoApiClient

async def main() -> None:
    async with aiohttp.ClientSession() as session:
        client = BlancoApiClient(
            session,
            app_version="1.0.0",   # your application version
            app_build="1",         # your application build number
            os_version="3.13.0",   # host OS / platform version string
        )

        # Register the app and obtain an app_id.
        reg = await client.register_app("en")
        print("app_id:", reg["app_id"])

        # Authenticate the device.
        auth = await client.authenticate(dev_id="<sha256-derived-device-id>")
        print("token:", auth["token"])

        # Poll device data.
        status, system = await client.get_device_system("<dev_id>")
        print("system params:", system["params"])
```

### Error handling

All exceptions are subclasses of `BlancoApiError`:

```python
from blanco_smart_home_api_client import (
    BlancoApiClient,
    BlancoAuthError,
    BlancoConnectionError,
    BlancoDeviceTypeError,
    BlancoTokenExpiredError,
)

try:
    auth = await client.authenticate(dev_id)
except BlancoAuthError:
    print("Access not yet granted — open the BLANCO UNIT App")
except BlancoDeviceTypeError:
    print("Device type not supported for Smart Home")
except BlancoConnectionError as err:
    print("Network error:", err)
```

### Token renewal

A `BlancoTokenExpiredError` is raised when any device endpoint returns HTTP 401.
Call `renew_token()` and then retry:

```python
from blanco_smart_home_api_client import BlancoTokenExpiredError

try:
    status, result = await client.get_device_status(dev_id)
except BlancoTokenExpiredError:
    await client.renew_token(dev_id)
    status, result = await client.get_device_status(dev_id)
```

---

## Package Structure

```
blanco_smart_home_api_client/
├── __init__.py       # Public API — re-exports all key types
├── client.py         # BlancoApiClient — all HTTP methods
├── config.py         # API stage config, endpoint constants, API keys
├── errors.py         # ApiErrorCode enum + exception hierarchy
├── http_status.py    # HttpStatus enum
├── log.py            # BlancoLogLevel enum, LOG_LEVEL constant, blanco_log()
├── mask.py           # mask_headers(), mask_dev_id(), mask_response_body()
├── models.py         # BlancoErrorType, BlancoActionType, BlancoWaterType enums
└── results.py        # TypedDict result types and response-parsing helpers
```

---

## Available Endpoints

| Method | HTTP | Endpoint |
|--------|------|----------|
| `register_app(locale)` | POST | `/apps/registrations` |
| `update_app_locale(locale)` | PUT | `/apps/registrations` |
| `deregister_app()` | DELETE | `/apps/registrations` |
| `authenticate(dev_id)` | POST | `/auth/token` |
| `renew_token(dev_id)` | POST | `/auth/token` |
| `get_device_system(dev_id)` | GET | `/devices/{dev_id}/system` |
| `get_device_status(dev_id)` | GET | `/devices/{dev_id}/status` |
| `get_device_settings(dev_id)` | GET | `/devices/{dev_id}/settings` |
| `get_device_errors(dev_id)` | GET | `/devices/{dev_id}/errors` |
| `get_device_actions(dev_id, from_ts, count, asc)` | GET | `/devices/{dev_id}/actions` |
| `get_device_stats(dev_id, ranges)` | POST | `/devices/{dev_id}/stats` |

---

## Home Assistant Integration

This library is used as the HTTP communication layer by the
[BLANCO Home Assistant integration](https://github.com/blancoGDPD/blanco-smart-home-api-client).
All network I/O and response parsing is handled here; the integration only
orchestrates polling, state management, and HA-specific entity registration.

---

## Authors

| Name | Role |
|---|---|
| Michael Weiss | Conception, implementation, and documentation |
